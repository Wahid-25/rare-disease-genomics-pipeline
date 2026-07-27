#!/usr/bin/env bash

set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage:"
    echo "bash pipeline/case_workflow/08_add_spliceai.sh CASE_ID"
    exit 1
fi

CASE_ID="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CORE_REL="containers/core_tools.sif"
SPLICEAI_REL="containers/spliceai.sif"
REFERENCE_REL="resources/reference/hg38.fa"

INPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep.snpeff.clinvar.vcf.gz"
OUTPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep.snpeff.clinvar.spliceai.vcf.gz"

TEMP_INPUT_REL="results/cases/$CASE_ID/work/${CASE_ID}.spliceai.input.vcf"
TEMP_OUTPUT_REL="results/cases/$CASE_ID/work/${CASE_ID}.spliceai.output.vcf"

CORE_SIF="$PROJECT_ROOT/$CORE_REL"
SPLICEAI_SIF="$PROJECT_ROOT/$SPLICEAI_REL"
REFERENCE="$PROJECT_ROOT/$REFERENCE_REL"

INPUT_VCF="$PROJECT_ROOT/$INPUT_REL"
OUTPUT_VCF="$PROJECT_ROOT/$OUTPUT_REL"

TEMP_INPUT="$PROJECT_ROOT/$TEMP_INPUT_REL"
TEMP_OUTPUT="$PROJECT_ROOT/$TEMP_OUTPUT_REL"

RESULT_DIR="$PROJECT_ROOT/results/cases/$CASE_ID"
WORK_DIR="$RESULT_DIR/work"
LOG_DIR="$RESULT_DIR/logs"
FINAL_DIR="$RESULT_DIR/final"

ROUTING_QC="$FINAL_DIR/${CASE_ID}.variant_routing_qc.tsv"
QC_FILE="$FINAL_DIR/${CASE_ID}.spliceai_qc.tsv"
LOG_FILE="$LOG_DIR/${CASE_ID}.spliceai.log"
HEADER_FILE="$WORK_DIR/${CASE_ID}.spliceai.header.txt"

mkdir -p "$WORK_DIR" "$LOG_DIR" "$FINAL_DIR"

exec > >(tee "$LOG_FILE") 2>&1

echo "========================================"
echo "SPLICEAI ANNOTATION"
echo "========================================"
echo "Case ID:    $CASE_ID"
echo "Input VCF:  $INPUT_REL"
echo "Reference:  $REFERENCE_REL"
echo "Output VCF: $OUTPUT_REL"
echo

# ---------------------------------------
# Check routing decision
# ---------------------------------------
if [[ -f "$ROUTING_QC" ]]; then
    SMALL_BRANCH="$(
        awk -F $'\t' '
            $1 == "small_variant_branch_required" {
                gsub(/\r/, "", $2)
                print $2
            }
        ' "$ROUTING_QC"
    )"

    if [[ "$SMALL_BRANCH" == "no" ]]; then
        {
            printf "metric\tvalue\n"
            printf "case_id\t%s\n" "$CASE_ID"
            printf "status\tskipped\n"
            printf "reason\tno_small_variants_detected\n"
        } > "$QC_FILE"

        echo "No small variants were detected."
        echo "SpliceAI branch skipped safely."
        exit 0
    fi
fi

# ---------------------------------------
# Validate resources
# ---------------------------------------
for required_file in \
    "$CORE_SIF" \
    "$SPLICEAI_SIF" \
    "$REFERENCE" \
    "${REFERENCE}.fai" \
    "$INPUT_VCF" \
    "${INPUT_VCF}.tbi"
do
    if [[ ! -s "$required_file" ]]; then
        echo "ERROR: Required file is missing or empty:"
        echo "$required_file"
        exit 1
    fi
done

command -v apptainer >/dev/null 2>&1 || {
    echo "ERROR: Apptainer is not available."
    exit 1
}

CORE=(
    apptainer exec
    --bind "$PROJECT_ROOT:/project"
    "$CORE_SIF"
)

SPLICEAI=(
    apptainer exec
    --bind "$PROJECT_ROOT:/project"
    "$SPLICEAI_SIF"
)

echo "[1/6] Checking the SpliceAI container"

if ! "${SPLICEAI[@]}" sh -lc \
    'command -v spliceai >/dev/null 2>&1'
then
    echo "ERROR: The spliceai command was not found inside the container."
    exit 1
fi

INPUT_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$INPUT_REL" |
    wc -l
)"

echo "Input records: $INPUT_COUNT"

if [[ "$INPUT_COUNT" -eq 0 ]]; then
    echo "ERROR: Input VCF contains no records."
    exit 1
fi

# ---------------------------------------
# Prepare plain VCF
# ---------------------------------------
echo
echo "[2/6] Preparing the VCF for SpliceAI"

rm -f \
    "$TEMP_INPUT" \
    "$TEMP_OUTPUT" \
    "$OUTPUT_VCF" \
    "${OUTPUT_VCF}.tbi"

"${CORE[@]}" bcftools view \
    --output-type v \
    --output "/project/$TEMP_INPUT_REL" \
    "/project/$INPUT_REL"

# ---------------------------------------
# Run SpliceAI
# ---------------------------------------
echo
echo "[3/6] Running SpliceAI"

"${SPLICEAI[@]}" spliceai \
    -I "/project/$TEMP_INPUT_REL" \
    -O "/project/$TEMP_OUTPUT_REL" \
    -R "/project/$REFERENCE_REL" \
    -A grch38

if [[ ! -s "$TEMP_OUTPUT" ]]; then
    echo "ERROR: SpliceAI did not create its output VCF."
    exit 1
fi

# ---------------------------------------
# Compress and index
# ---------------------------------------
echo
echo "[4/6] Compressing and indexing the SpliceAI VCF"

"${CORE[@]}" bgzip \
    -c \
    "/project/$TEMP_OUTPUT_REL" \
    > "$OUTPUT_VCF"

"${CORE[@]}" tabix \
    -f \
    -p vcf \
    "/project/$OUTPUT_REL"

# ---------------------------------------
# Validate annotations
# ---------------------------------------
echo
echo "[5/6] Validating cumulative annotations"

OUTPUT_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$OUTPUT_REL" |
    wc -l
)"

if [[ "$OUTPUT_COUNT" -ne "$INPUT_COUNT" ]]; then
    echo "ERROR: Record count changed during SpliceAI annotation."
    echo "Input records:  $INPUT_COUNT"
    echo "Output records: $OUTPUT_COUNT"
    exit 1
fi

"${CORE[@]}" bcftools view -h \
    "/project/$OUTPUT_REL" \
    > "$HEADER_FILE"

for required_tag in CSQ ANN CLNSIG SpliceAI; do
    if ! grep -q "^##INFO=<ID=${required_tag}," "$HEADER_FILE"; then
        echo "ERROR: INFO/${required_tag} is missing from the output."
        exit 1
    fi
done

SPLICEAI_COUNT="$(
    "${CORE[@]}" bcftools query \
        -f '%INFO/SpliceAI\n' \
        "/project/$OUTPUT_REL" |
    awk '
        $0 != "." && $0 != "" {
            count++
        }
        END {
            print count + 0
        }
    '
)"

# ---------------------------------------
# Create QC
# ---------------------------------------
echo
echo "[6/6] Creating SpliceAI QC summary"

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "status\tcompleted\n"
    printf "input_records\t%s\n" "$INPUT_COUNT"
    printf "output_records\t%s\n" "$OUTPUT_COUNT"
    printf "records_with_SpliceAI\t%s\n" "$SPLICEAI_COUNT"
    printf "VEP_CSQ_preserved\tyes\n"
    printf "SnpEff_ANN_preserved\tyes\n"
    printf "ClinVar_CLNSIG_preserved\tyes\n"
    printf "reference_build\tGRCh38\n"
    printf "input_vcf\t%s\n" "$INPUT_REL"
    printf "output_vcf\t%s\n" "$OUTPUT_REL"
} > "$QC_FILE"

rm -f "$TEMP_INPUT" "$TEMP_OUTPUT"

echo
echo "Input records:             $INPUT_COUNT"
echo "Output records:            $OUTPUT_COUNT"
echo "Records with SpliceAI:     $SPLICEAI_COUNT"
echo "VEP CSQ preserved:         yes"
echo "SnpEff ANN preserved:      yes"
echo "ClinVar CLNSIG preserved:  yes"

echo
echo "Output:"
echo "$OUTPUT_VCF"

echo
echo "QC:"
echo "$QC_FILE"

echo
echo "SPLICEAI ANNOTATION COMPLETED SUCCESSFULLY"

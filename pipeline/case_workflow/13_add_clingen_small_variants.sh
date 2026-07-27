#!/usr/bin/env bash

set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage:"
    echo "bash pipeline/case_workflow/13_add_clingen_small_variants.sh CASE_ID"
    exit 1
fi

CASE_ID="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CORE_REL="containers/core_tools.sif"
CLINGEN_REL="resources/clingen/clingen_dosage.hg38.bed.gz"

INPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep.snpeff.clinvar.spliceai.vcf.gz"
OUTPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.final.small_variants.annotated.vcf.gz"

ROUTING_QC_REL="results/cases/$CASE_ID/final/${CASE_ID}.variant_routing_qc.tsv"
HEADER_REL="results/cases/$CASE_ID/work/${CASE_ID}.clingen.header.txt"
QC_REL="results/cases/$CASE_ID/final/${CASE_ID}.clingen_qc.tsv"
LOG_REL="results/cases/$CASE_ID/logs/${CASE_ID}.clingen.log"

CORE_SIF="$PROJECT_ROOT/$CORE_REL"
CLINGEN_BED="$PROJECT_ROOT/$CLINGEN_REL"
INPUT_VCF="$PROJECT_ROOT/$INPUT_REL"
OUTPUT_VCF="$PROJECT_ROOT/$OUTPUT_REL"
ROUTING_QC="$PROJECT_ROOT/$ROUTING_QC_REL"
HEADER_FILE="$PROJECT_ROOT/$HEADER_REL"
QC_FILE="$PROJECT_ROOT/$QC_REL"
LOG_FILE="$PROJECT_ROOT/$LOG_REL"

mkdir -p \
    "$(dirname "$HEADER_FILE")" \
    "$(dirname "$QC_FILE")" \
    "$(dirname "$LOG_FILE")" \
    "$(dirname "$OUTPUT_VCF")"

exec > >(tee "$LOG_FILE") 2>&1

echo "========================================"
echo "CLINGEN SMALL-VARIANT ANNOTATION"
echo "========================================"
echo "Case ID:        $CASE_ID"
echo "Input VCF:      $INPUT_REL"
echo "ClinGen source: $CLINGEN_REL"
echo

# ---------------------------------------
# Check automatic routing decision
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

    if [[ "$SMALL_BRANCH" != "yes" ]]; then
        {
            printf "metric\tvalue\n"
            printf "case_id\t%s\n" "$CASE_ID"
            printf "status\tskipped\n"
            printf "reason\tno_small_variants_detected\n"
        } > "$QC_FILE"

        echo "No small variants were detected."
        echo "ClinGen small-variant annotation skipped safely."
        exit 0
    fi
fi

# ---------------------------------------
# Validate files
# ---------------------------------------

for required_file in \
    "$CORE_SIF" \
    "$CLINGEN_BED" \
    "${CLINGEN_BED}.tbi" \
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

# ---------------------------------------
# Create ClinGen VCF header definitions
# ---------------------------------------

echo "[1/5] Creating ClinGen INFO definitions"

cat > "$HEADER_FILE" <<'HDR'
##INFO=<ID=CLINGEN_REGION,Number=.,Type=String,Description="ClinGen dosage sensitivity region or gene overlapping the variant">
##INFO=<ID=CLINGEN_HAPLO,Number=.,Type=String,Description="ClinGen haploinsufficiency score">
##INFO=<ID=CLINGEN_TRIPLO,Number=.,Type=String,Description="ClinGen triplosensitivity score">
HDR

INPUT_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$INPUT_REL" |
    wc -l
)"

if [[ "$INPUT_COUNT" -eq 0 ]]; then
    echo "ERROR: Input VCF contains no records."
    exit 1
fi

echo "Input records: $INPUT_COUNT"

# ---------------------------------------
# Add ClinGen overlap annotations
# ---------------------------------------

echo
echo "[2/5] Adding ClinGen dosage overlaps"

rm -f "$OUTPUT_VCF" "${OUTPUT_VCF}.tbi"

"${CORE[@]}" bcftools annotate \
    --annotations "/project/$CLINGEN_REL" \
    --header-lines "/project/$HEADER_REL" \
    --columns \
"CHROM,FROM,TO,INFO/CLINGEN_REGION,INFO/CLINGEN_HAPLO,INFO/CLINGEN_TRIPLO" \
    --output-type z \
    --output "/project/$OUTPUT_REL" \
    "/project/$INPUT_REL"

# ---------------------------------------
# Index
# ---------------------------------------

echo
echo "[3/5] Indexing final small-variant VCF"

"${CORE[@]}" bcftools index \
    --force \
    --tbi \
    "/project/$OUTPUT_REL"

# ---------------------------------------
# Validate cumulative fields
# ---------------------------------------

echo
echo "[4/5] Validating cumulative annotations"

OUTPUT_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$OUTPUT_REL" |
    wc -l
)"

if [[ "$OUTPUT_COUNT" -ne "$INPUT_COUNT" ]]; then
    echo "ERROR: Record count changed during ClinGen annotation."
    echo "Input:  $INPUT_COUNT"
    echo "Output: $OUTPUT_COUNT"
    exit 1
fi

OUTPUT_HEADER="$(
    "${CORE[@]}" bcftools view -h \
        "/project/$OUTPUT_REL"
)"

for required_tag in \
    CSQ \
    ANN \
    CLNSIG \
    SpliceAI \
    CLINGEN_REGION \
    CLINGEN_HAPLO \
    CLINGEN_TRIPLO
do
    if ! grep -q "^##INFO=<ID=${required_tag}," <<< "$OUTPUT_HEADER"; then
        echo "ERROR: INFO/${required_tag} is missing."
        exit 1
    fi
done

CLINGEN_MATCH_COUNT="$(
    "${CORE[@]}" bcftools query \
        -f '%INFO/CLINGEN_REGION\n' \
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
# QC summary
# ---------------------------------------

echo
echo "[5/5] Creating ClinGen QC table"

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "status\tcompleted\n"
    printf "input_records\t%s\n" "$INPUT_COUNT"
    printf "output_records\t%s\n" "$OUTPUT_COUNT"
    printf "records_with_clingen_overlap\t%s\n" "$CLINGEN_MATCH_COUNT"
    printf "VEP_CSQ_preserved\tyes\n"
    printf "SnpEff_ANN_preserved\tyes\n"
    printf "ClinVar_CLNSIG_preserved\tyes\n"
    printf "SpliceAI_preserved\tyes\n"
    printf "clingen_points_added\t0\n"
    printf "clingen_source\t%s\n" "$CLINGEN_REL"
    printf "input_vcf\t%s\n" "$INPUT_REL"
    printf "output_vcf\t%s\n" "$OUTPUT_REL"
} > "$QC_FILE"

echo
echo "Input records:                 $INPUT_COUNT"
echo "Output records:                $OUTPUT_COUNT"
echo "Records with ClinGen overlap:  $CLINGEN_MATCH_COUNT"
echo
echo "Final cumulative small-variant VCF:"
echo "$OUTPUT_VCF"
echo
echo "QC:"
echo "$QC_FILE"
echo
echo "CLINGEN ANNOTATION COMPLETED SUCCESSFULLY"

#!/usr/bin/env bash

set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage:"
    echo "bash pipeline/case_workflow/04_add_clinvar_to_snpeff.sh CASE_ID"
    echo
    echo "Example:"
    echo "bash pipeline/case_workflow/04_add_clinvar_to_snpeff.sh case001"
    exit 1
fi

CASE_ID="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CORE_REL="containers/core_tools.sif"
CLINVAR_REL="resources/clinvar/clinvar.chr.vcf.gz"

INPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep.snpeff.vcf.gz"
OUTPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep.snpeff.clinvar.vcf.gz"

CORE_SIF="$PROJECT_ROOT/$CORE_REL"
CLINVAR_VCF="$PROJECT_ROOT/$CLINVAR_REL"
CLINVAR_INDEX="${CLINVAR_VCF}.tbi"
INPUT_VCF="$PROJECT_ROOT/$INPUT_REL"
OUTPUT_VCF="$PROJECT_ROOT/$OUTPUT_REL"

RESULT_DIR="$PROJECT_ROOT/results/cases/$CASE_ID"
WORK_DIR="$RESULT_DIR/work"
LOG_DIR="$RESULT_DIR/logs"
FINAL_DIR="$RESULT_DIR/final"

HEADER_FILE="$WORK_DIR/${CASE_ID}.cumulative_clinvar.header.txt"
LOG_FILE="$LOG_DIR/${CASE_ID}.cumulative_clinvar.log"
QC_FILE="$FINAL_DIR/${CASE_ID}.cumulative_clinvar_qc.tsv"

mkdir -p "$WORK_DIR" "$LOG_DIR" "$FINAL_DIR"

exec > >(tee "$LOG_FILE") 2>&1

echo "========================================"
echo "CUMULATIVE CLINVAR ANNOTATION"
echo "========================================"
echo "Case ID:        $CASE_ID"
echo "Input VCF:      $INPUT_REL"
echo "ClinVar source: $CLINVAR_REL"
echo "Output VCF:     $OUTPUT_REL"
echo

for required_file in \
    "$CORE_SIF" \
    "$CLINVAR_VCF" \
    "$CLINVAR_INDEX" \
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

echo "[1/5] Detecting available ClinVar fields"

"${CORE[@]}" bcftools view -h \
    "/project/$CLINVAR_REL" \
    > "$HEADER_FILE"

DESIRED_TAGS=(
    CLNSIG
    CLNDN
    CLNREVSTAT
    CLNDISDB
    CLNHGVS
    CLNVC
    CLNVCSO
    GENEINFO
)

AVAILABLE_TAGS=()
ANNOTATE_COLUMNS=()

for tag in "${DESIRED_TAGS[@]}"; do
    if grep -q "^##INFO=<ID=${tag}," "$HEADER_FILE"; then
        AVAILABLE_TAGS+=("$tag")
        ANNOTATE_COLUMNS+=("INFO/$tag")
        echo "  FOUND   $tag"
    else
        echo "  MISSING $tag"
    fi
done

if [[ ! " ${AVAILABLE_TAGS[*]} " =~ " CLNSIG " ]]; then
    echo "ERROR: CLNSIG was not found in the ClinVar header."
    exit 1
fi

COLUMN_STRING="$(
    IFS=,
    echo "${ANNOTATE_COLUMNS[*]}"
)"

TAG_STRING="$(
    IFS=,
    echo "${AVAILABLE_TAGS[*]}"
)"

INPUT_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$INPUT_REL" |
    wc -l
)"

echo
echo "Input records: $INPUT_COUNT"

if [[ "$INPUT_COUNT" -eq 0 ]]; then
    echo "ERROR: Input VCF contains no records."
    exit 1
fi

echo
echo "[2/5] Adding ClinVar annotations"

rm -f "$OUTPUT_VCF" "${OUTPUT_VCF}.tbi"

"${CORE[@]}" bcftools annotate \
    --annotations "/project/$CLINVAR_REL" \
    --columns "$COLUMN_STRING" \
    --output-type z \
    --output "/project/$OUTPUT_REL" \
    "/project/$INPUT_REL"

echo
echo "[3/5] Indexing cumulative VCF"

"${CORE[@]}" bcftools index \
    --force \
    --tbi \
    "/project/$OUTPUT_REL"

echo
echo "[4/5] Validating cumulative annotations"

OUTPUT_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$OUTPUT_REL" |
    wc -l
)"

if [[ "$OUTPUT_COUNT" -ne "$INPUT_COUNT" ]]; then
    echo "ERROR: Record count changed during ClinVar annotation."
    echo "Input records:  $INPUT_COUNT"
    echo "Output records: $OUTPUT_COUNT"
    exit 1
fi

OUTPUT_HEADER="$(
    "${CORE[@]}" bcftools view -h \
        "/project/$OUTPUT_REL"
)"

CSQ_PRESENT="no"
ANN_PRESENT="no"
CLNSIG_PRESENT="no"

if grep -q '^##INFO=<ID=CSQ,' <<< "$OUTPUT_HEADER"; then
    CSQ_PRESENT="yes"
fi

if grep -q '^##INFO=<ID=ANN,' <<< "$OUTPUT_HEADER"; then
    ANN_PRESENT="yes"
fi

if grep -q '^##INFO=<ID=CLNSIG,' <<< "$OUTPUT_HEADER"; then
    CLNSIG_PRESENT="yes"
fi

if [[ "$CSQ_PRESENT" != "yes" ]]; then
    echo "ERROR: VEP CSQ was not preserved."
    exit 1
fi

if [[ "$ANN_PRESENT" != "yes" ]]; then
    echo "ERROR: SnpEff ANN was not preserved."
    exit 1
fi

if [[ "$CLNSIG_PRESENT" != "yes" ]]; then
    echo "ERROR: ClinVar CLNSIG was not added."
    exit 1
fi

CLINVAR_MATCH_COUNT="$(
    "${CORE[@]}" bcftools query \
        -f '%INFO/CLNSIG\n' \
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

ANN_COUNT="$(
    "${CORE[@]}" bcftools query \
        -f '%INFO/ANN\n' \
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

echo
echo "[5/5] Creating cumulative ClinVar QC"

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "input_records\t%s\n" "$INPUT_COUNT"
    printf "output_records\t%s\n" "$OUTPUT_COUNT"
    printf "records_with_snpeff_ANN\t%s\n" "$ANN_COUNT"
    printf "records_with_clinvar_match\t%s\n" "$CLINVAR_MATCH_COUNT"
    printf "VEP_CSQ_preserved\t%s\n" "$CSQ_PRESENT"
    printf "SnpEff_ANN_preserved\t%s\n" "$ANN_PRESENT"
    printf "ClinVar_CLNSIG_added\t%s\n" "$CLNSIG_PRESENT"
    printf "clinvar_fields_copied\t%s\n" "$TAG_STRING"
    printf "input_vcf\t%s\n" "$INPUT_REL"
    printf "output_vcf\t%s\n" "$OUTPUT_REL"
} > "$QC_FILE"

echo
echo "Input records:                $INPUT_COUNT"
echo "Output records:               $OUTPUT_COUNT"
echo "Records with SnpEff ANN:      $ANN_COUNT"
echo "Records with ClinVar match:   $CLINVAR_MATCH_COUNT"
echo "VEP CSQ preserved:            $CSQ_PRESENT"
echo "SnpEff ANN preserved:         $ANN_PRESENT"
echo "ClinVar CLNSIG added:         $CLNSIG_PRESENT"

echo
echo "Cumulative VCF:"
echo "$OUTPUT_VCF"

echo
echo "QC table:"
echo "$QC_FILE"

echo
echo "CUMULATIVE CLINVAR ANNOTATION COMPLETED SUCCESSFULLY"

#!/usr/bin/env bash

set -euo pipefail

# ---------------------------------------
# Check arguments
# ---------------------------------------
if [[ $# -ne 1 ]]; then
    echo "Usage:"
    echo "bash pipeline/case_workflow/06_add_clinvar.sh CASE_ID"
    echo
    echo "Example:"
    echo "bash pipeline/case_workflow/06_add_clinvar.sh case001"
    exit 1
fi

CASE_ID="$1"

# ---------------------------------------
# Detect project root
# ---------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CORE_CONTAINER="$PROJECT_ROOT/containers/core_tools.sif"

CLINVAR_REL="resources/clinvar/clinvar.chr.vcf.gz"
CLINVAR_INDEX_REL="${CLINVAR_REL}.tbi"

INPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep.vcf.gz"
OUTPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep.clinvar.vcf.gz"

CLINVAR_HOST="$PROJECT_ROOT/$CLINVAR_REL"
CLINVAR_INDEX_HOST="$PROJECT_ROOT/$CLINVAR_INDEX_REL"
INPUT_HOST="$PROJECT_ROOT/$INPUT_REL"
OUTPUT_HOST="$PROJECT_ROOT/$OUTPUT_REL"

RESULT_ROOT="$PROJECT_ROOT/results/cases/$CASE_ID"
WORK_DIR="$RESULT_ROOT/work"
LOG_DIR="$RESULT_ROOT/logs"
FINAL_DIR="$RESULT_ROOT/final"

mkdir -p "$WORK_DIR" "$LOG_DIR" "$FINAL_DIR"

HEADER_FILE="$WORK_DIR/${CASE_ID}.clinvar.header.txt"
LOG_FILE="$LOG_DIR/${CASE_ID}.clinvar.log"
QC_FILE="$FINAL_DIR/${CASE_ID}.clinvar_qc.tsv"

# ---------------------------------------
# Validate required files
# ---------------------------------------
for required_file in \
    "$CORE_CONTAINER" \
    "$CLINVAR_HOST" \
    "$CLINVAR_INDEX_HOST" \
    "$INPUT_HOST"
do
    if [[ ! -f "$required_file" ]]; then
        echo "ERROR: Required file was not found:"
        echo "$required_file"
        exit 1
    fi
done

exec > >(tee "$LOG_FILE") 2>&1

echo "========================================"
echo "CLINVAR ANNOTATION"
echo "========================================"
echo "Case ID:        $CASE_ID"
echo "Input VCF:      $INPUT_REL"
echo "ClinVar source: $CLINVAR_REL"
echo

# ---------------------------------------
# Read ClinVar header
# ---------------------------------------
echo "[1/5] Reading available ClinVar fields"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools view -h "/project/$CLINVAR_REL" \
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
    echo "ERROR: CLNSIG was not found in the ClinVar VCF header."
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

# ---------------------------------------
# Count input variants
# ---------------------------------------
INPUT_COUNT=$(
    apptainer exec \
        --bind "$PROJECT_ROOT:/project" \
        "$CORE_CONTAINER" \
        bcftools view -H "/project/$INPUT_REL" |
    wc -l
)

echo
echo "Input records: $INPUT_COUNT"

# ---------------------------------------
# Add ClinVar fields
# ---------------------------------------
echo
echo "[2/5] Adding ClinVar annotations"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools annotate \
    --annotations "/project/$CLINVAR_REL" \
    --columns "$COLUMN_STRING" \
    --output-type z \
    --output "/project/$OUTPUT_REL" \
    "/project/$INPUT_REL"

# ---------------------------------------
# Index output
# ---------------------------------------
echo
echo "[3/5] Indexing ClinVar-annotated VCF"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools index \
    --force \
    --tbi \
    "/project/$OUTPUT_REL"

# ---------------------------------------
# Validate output
# ---------------------------------------
echo
echo "[4/5] Validating annotation output"

OUTPUT_COUNT=$(
    apptainer exec \
        --bind "$PROJECT_ROOT:/project" \
        "$CORE_CONTAINER" \
        bcftools view -H "/project/$OUTPUT_REL" |
    wc -l
)

if [[ "$OUTPUT_COUNT" -ne "$INPUT_COUNT" ]]; then
    echo "ERROR: ClinVar output count differs from input count."
    echo "Input:  $INPUT_COUNT"
    echo "Output: $OUTPUT_COUNT"
    exit 1
fi

CLINVAR_MATCH_COUNT=$(
    apptainer exec \
        --bind "$PROJECT_ROOT:/project" \
        "$CORE_CONTAINER" \
        bcftools query \
        -f '%INFO/CLNSIG\n' \
        "/project/$OUTPUT_REL" |
    awk '$0 != "." && $0 != "" {count++} END {print count+0}'
)

# ---------------------------------------
# Create QC table
# ---------------------------------------
echo
echo "[5/5] Creating ClinVar QC summary"

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "input_records\t%s\n" "$INPUT_COUNT"
    printf "output_records\t%s\n" "$OUTPUT_COUNT"
    printf "records_with_clinvar_match\t%s\n" "$CLINVAR_MATCH_COUNT"
    printf "clinvar_fields_copied\t%s\n" "$TAG_STRING"
    printf "clinvar_source\t%s\n" "$CLINVAR_REL"
    printf "output_vcf\t%s\n" "$OUTPUT_REL"
} > "$QC_FILE"

echo
echo "Input records:               $INPUT_COUNT"
echo "Output records:              $OUTPUT_COUNT"
echo "Records with ClinVar match:  $CLINVAR_MATCH_COUNT"
echo "Fields copied:               $TAG_STRING"

echo
echo "ClinVar-annotated VCF:"
echo "$OUTPUT_HOST"

echo
echo "QC table:"
echo "$QC_FILE"

echo
echo "CLINVAR ANNOTATION COMPLETED SUCCESSFULLY"

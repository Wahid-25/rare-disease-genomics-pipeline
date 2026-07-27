#!/usr/bin/env bash

set -euo pipefail

# -----------------------------
# Check command-line arguments
# -----------------------------
if [[ $# -ne 2 ]]; then
    echo "Usage:"
    echo "bash pipeline/case_workflow/01_prepare_and_normalize.sh CASE_ID INPUT_VCF"
    echo
    echo "Example:"
    echo "bash pipeline/case_workflow/01_prepare_and_normalize.sh \\"
    echo "  case001 \\"
    echo "  input/cases/case001/case001.raw.vcf"
    exit 1
fi

CASE_ID="$1"
INPUT_REL="$2"

# -----------------------------
# Detect project root
# -----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CORE_CONTAINER="$PROJECT_ROOT/containers/core_tools.sif"
REFERENCE="$PROJECT_ROOT/resources/reference/hg38.fa"
INPUT_HOST="$PROJECT_ROOT/$INPUT_REL"

RESULT_ROOT="$PROJECT_ROOT/results/cases/$CASE_ID"
WORK_DIR="$RESULT_ROOT/work"
LOG_DIR="$RESULT_ROOT/logs"
FINAL_DIR="$RESULT_ROOT/final"

mkdir -p "$WORK_DIR" "$LOG_DIR" "$FINAL_DIR"

LOG_FILE="$LOG_DIR/${CASE_ID}.prepare_and_normalize.log"

INPUT_GZ_REL="results/cases/$CASE_ID/work/${CASE_ID}.input.vcf.gz"
SORTED_GZ_REL="results/cases/$CASE_ID/work/${CASE_ID}.sorted.vcf.gz"
NORMALIZED_GZ_REL="results/cases/$CASE_ID/work/${CASE_ID}.normalized.vcf.gz"

INPUT_GZ="$PROJECT_ROOT/$INPUT_GZ_REL"
SORTED_GZ="$PROJECT_ROOT/$SORTED_GZ_REL"
NORMALIZED_GZ="$PROJECT_ROOT/$NORMALIZED_GZ_REL"

QC_FILE="$FINAL_DIR/${CASE_ID}.normalization_qc.tsv"

# -----------------------------
# Check required files
# -----------------------------
if [[ ! -f "$INPUT_HOST" ]]; then
    echo "ERROR: Input VCF was not found:"
    echo "$INPUT_HOST"
    exit 1
fi

if [[ ! -f "$CORE_CONTAINER" ]]; then
    echo "ERROR: core_tools.sif was not found:"
    echo "$CORE_CONTAINER"
    exit 1
fi

if [[ ! -f "$REFERENCE" ]]; then
    echo "ERROR: GRCh38 reference was not found:"
    echo "$REFERENCE"
    exit 1
fi

# Send terminal output into the log file as well
exec > >(tee "$LOG_FILE") 2>&1

echo "========================================"
echo "CASE PREPARATION AND NORMALIZATION"
echo "========================================"
echo "Case ID:       $CASE_ID"
echo "Input VCF:     $INPUT_REL"
echo "Reference:     resources/reference/hg38.fa"
echo "Project root:  $PROJECT_ROOT"
echo

# -----------------------------
# Count original records
# -----------------------------
INPUT_COUNT=$(
    apptainer exec \
        --bind "$PROJECT_ROOT:/project" \
        "$CORE_CONTAINER" \
        bcftools view -H "/project/$INPUT_REL" |
    wc -l
)

echo "Input variant count: $INPUT_COUNT"

# -----------------------------
# Validate and compress
# -----------------------------
echo
echo "[1/5] Validating and compressing input VCF"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools view \
    -Oz \
    -o "/project/$INPUT_GZ_REL" \
    "/project/$INPUT_REL"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools index \
    -f \
    -t \
    "/project/$INPUT_GZ_REL"

# -----------------------------
# Sort variants
# -----------------------------
echo
echo "[2/5] Sorting variants"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools sort \
    -Oz \
    -o "/project/$SORTED_GZ_REL" \
    "/project/$INPUT_GZ_REL"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools index \
    -f \
    -t \
    "/project/$SORTED_GZ_REL"

# -----------------------------
# Normalize against GRCh38
# -----------------------------
echo
echo "[3/5] Normalizing against GRCh38"

# AUTO_SYNTHETIC_REFERENCE_POLICY
#
# Synthetic educational files:
#     exclude incompatible background records
#
# Real patient files:
#     stop on any GRCh38 REF mismatch

HEADER_TEXT="$(
    apptainer exec \
        --bind "$PROJECT_ROOT:/project" \
        "$CORE_CONTAINER" \
        bcftools view \
        -h \
        "/project/$SORTED_GZ_REL"
)"

REF_CHECK_MODE="e"
REFERENCE_POLICY="strict_fail_on_reference_mismatch"

if grep -Eiq \
    '^##source=.*synthetic|^##dataset_note=.*(synthetic|toy|not a real patient)|SyntheticWGSGenerator|SIMULATED DATA FOR EDUCATIONAL' \
    <<< "$HEADER_TEXT"
then
    REF_CHECK_MODE="x"
    REFERENCE_POLICY="synthetic_exclude_reference_mismatches"
fi

REFERENCE_POLICY_FILE="$FINAL_DIR/${CASE_ID}.reference_policy.tsv"

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "reference_policy\t%s\n" "$REFERENCE_POLICY"
    printf "bcftools_check_ref_mode\t%s\n" "$REF_CHECK_MODE"
} > "$REFERENCE_POLICY_FILE"

echo "Reference policy: $REFERENCE_POLICY"
echo "bcftools -c mode:  $REF_CHECK_MODE"


apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools norm \
    -f /project/resources/reference/hg38.fa \
    -m -any \
    -c "$REF_CHECK_MODE" \
    -Oz \
    -o "/project/$NORMALIZED_GZ_REL" \
    "/project/$SORTED_GZ_REL"

# -----------------------------
# Index normalized VCF
# -----------------------------
echo
echo "[4/5] Indexing normalized VCF"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools index \
    -f \
    -t \
    "/project/$NORMALIZED_GZ_REL"

# -----------------------------
# Collect QC information
# -----------------------------
echo
echo "[5/5] Creating QC summary"

NORMALIZED_COUNT=$(
    apptainer exec \
        --bind "$PROJECT_ROOT:/project" \
        "$CORE_CONTAINER" \
        bcftools view -H "/project/$NORMALIZED_GZ_REL" |
    wc -l
)

REMOVED_COUNT=$((INPUT_COUNT - NORMALIZED_COUNT))

SAMPLES=$(
    apptainer exec \
        --bind "$PROJECT_ROOT:/project" \
        "$CORE_CONTAINER" \
        bcftools query -l "/project/$NORMALIZED_GZ_REL" |
    paste -sd ',' -
)

if [[ -z "$SAMPLES" ]]; then
    SAMPLES="No sample columns"
fi

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "genome_build\tGRCh38\n"
    printf "input_file\t%s\n" "$INPUT_REL"
    printf "input_records\t%s\n" "$INPUT_COUNT"
    printf "normalized_records\t%s\n" "$NORMALIZED_COUNT"
    printf "excluded_or_removed_records\t%s\n" "$REMOVED_COUNT"
    printf "samples\t%s\n" "$SAMPLES"
    printf "normalized_vcf\t%s\n" "$NORMALIZED_GZ_REL"
} > "$QC_FILE"

echo
echo "Input records:       $INPUT_COUNT"
echo "Normalized records:  $NORMALIZED_COUNT"
echo "Removed records:     $REMOVED_COUNT"
echo "Samples:             $SAMPLES"

echo
echo "Normalized VCF:"
echo "$NORMALIZED_GZ"

echo
echo "QC summary:"
echo "$QC_FILE"

echo
echo "NORMALIZATION COMPLETED SUCCESSFULLY"

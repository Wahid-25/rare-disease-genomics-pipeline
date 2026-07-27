#!/usr/bin/env bash

set -euo pipefail

# ---------------------------------------
# Check command-line arguments
# ---------------------------------------
if [[ $# -ne 1 ]]; then
    echo "Usage:"
    echo "bash pipeline/case_workflow/02_annotate_vep.sh CASE_ID"
    echo
    echo "Example:"
    echo "bash pipeline/case_workflow/02_annotate_vep.sh case001"
    exit 1
fi

CASE_ID="$1"
THREADS="${THREADS:-4}"

# ---------------------------------------
# Detect project root
# ---------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ---------------------------------------
# Required containers and resources
# ---------------------------------------
VEP_CONTAINER="$PROJECT_ROOT/containers/vep_release115.sif"
CORE_CONTAINER="$PROJECT_ROOT/containers/core_tools.sif"

REFERENCE="$PROJECT_ROOT/resources/reference/hg38.fa"
VEP_CACHE="$PROJECT_ROOT/resources/vep_cache/homo_sapiens/115_GRCh38"

# ---------------------------------------
# Input and output locations
# ---------------------------------------
NORMALIZED_REL="results/cases/$CASE_ID/work/${CASE_ID}.normalized.vcf.gz"
NORMALIZED_HOST="$PROJECT_ROOT/$NORMALIZED_REL"

RESULT_ROOT="$PROJECT_ROOT/results/cases/$CASE_ID"
ANNOTATED_DIR="$RESULT_ROOT/annotated"
LOG_DIR="$RESULT_ROOT/logs"
FINAL_DIR="$RESULT_ROOT/final"
WORK_DIR="$RESULT_ROOT/work"

mkdir -p \
    "$ANNOTATED_DIR" \
    "$LOG_DIR" \
    "$FINAL_DIR" \
    "$WORK_DIR"

VEP_OUTPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep.vcf.gz"
VEP_OUTPUT_HOST="$PROJECT_ROOT/$VEP_OUTPUT_REL"

VEP_STATS_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep_summary.html"
VEP_WARNING_REL="results/cases/$CASE_ID/logs/${CASE_ID}.vep_warnings.txt"

LOG_FILE="$LOG_DIR/${CASE_ID}.vep.log"
HEADER_FILE="$WORK_DIR/${CASE_ID}.vep.header.txt"
QC_FILE="$FINAL_DIR/${CASE_ID}.vep_qc.tsv"

# ---------------------------------------
# Check required files
# ---------------------------------------
for required_file in \
    "$NORMALIZED_HOST" \
    "$VEP_CONTAINER" \
    "$CORE_CONTAINER" \
    "$REFERENCE"
do
    if [[ ! -f "$required_file" ]]; then
        echo "ERROR: Required file was not found:"
        echo "$required_file"
        exit 1
    fi
done

if [[ ! -d "$VEP_CACHE" ]]; then
    echo "ERROR: VEP release 115 GRCh38 cache was not found:"
    echo "$VEP_CACHE"
    exit 1
fi

# Save terminal output in the log as well
exec > >(tee "$LOG_FILE") 2>&1

echo "========================================"
echo "VEP ANNOTATION"
echo "========================================"
echo "Case ID:        $CASE_ID"
echo "Threads:        $THREADS"
echo "Input VCF:      $NORMALIZED_REL"
echo "VEP release:    115"
echo "Genome build:   GRCh38"
echo "Project root:   $PROJECT_ROOT"
echo

INPUT_COUNT=$(
    apptainer exec \
        --bind "$PROJECT_ROOT:/project" \
        "$CORE_CONTAINER" \
        bcftools view -H "/project/$NORMALIZED_REL" |
    wc -l
)

echo "Normalized input records: $INPUT_COUNT"

echo
echo "[1/3] Running VEP annotation"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$VEP_CONTAINER" \
    vep \
    --input_file "/project/$NORMALIZED_REL" \
    --output_file "/project/$VEP_OUTPUT_REL" \
    --format vcf \
    --vcf \
    --compress_output bgzip \
    --force_overwrite \
    --offline \
    --cache \
    --cache_version 115 \
    --dir_cache /project/resources/vep_cache \
    --species homo_sapiens \
    --assembly GRCh38 \
    --fasta /project/resources/reference/hg38.fa \
    --fork "$THREADS" \
    --everything \
    --symbol \
    --canonical \
    --mane \
    --hgvs \
    --protein \
    --biotype \
    --af_gnomade \
    --af_gnomadg \
    --max_af \
    --flag_pick \
    --stats_file "/project/$VEP_STATS_REL" \
    --warning_file "/project/$VEP_WARNING_REL"

echo
echo "[2/3] Indexing VEP output"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools index \
    -f \
    -t \
    "/project/$VEP_OUTPUT_REL"

echo
echo "[3/3] Checking VEP annotations"

OUTPUT_COUNT=$(
    apptainer exec \
        --bind "$PROJECT_ROOT:/project" \
        "$CORE_CONTAINER" \
        bcftools view -H "/project/$VEP_OUTPUT_REL" |
    wc -l
)

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_CONTAINER" \
    bcftools view -h "/project/$VEP_OUTPUT_REL" \
    > "$HEADER_FILE"

if grep -q '^##INFO=<ID=CSQ' "$HEADER_FILE"; then
    CSQ_PRESENT="yes"
else
    CSQ_PRESENT="no"
fi

if [[ "$OUTPUT_COUNT" -ne "$INPUT_COUNT" ]]; then
    echo "ERROR: VEP output record count does not match its input."
    echo "Input:  $INPUT_COUNT"
    echo "Output: $OUTPUT_COUNT"
    exit 1
fi

if [[ "$CSQ_PRESENT" != "yes" ]]; then
    echo "ERROR: VEP completed, but the CSQ annotation header was not found."
    exit 1
fi

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "genome_build\tGRCh38\n"
    printf "vep_release\t115\n"
    printf "normalized_input_records\t%s\n" "$INPUT_COUNT"
    printf "vep_output_records\t%s\n" "$OUTPUT_COUNT"
    printf "csq_annotation_present\t%s\n" "$CSQ_PRESENT"
    printf "vep_output\t%s\n" "$VEP_OUTPUT_REL"
    printf "vep_statistics\t%s\n" "$VEP_STATS_REL"
    printf "vep_warning_file\t%s\n" "$VEP_WARNING_REL"
} > "$QC_FILE"

echo
echo "Input records:          $INPUT_COUNT"
echo "VEP output records:     $OUTPUT_COUNT"
echo "CSQ annotation present: $CSQ_PRESENT"

echo
echo "VEP-annotated VCF:"
echo "$VEP_OUTPUT_HOST"

echo
echo "VEP QC table:"
echo "$QC_FILE"

echo
echo "VEP ANNOTATION COMPLETED SUCCESSFULLY"

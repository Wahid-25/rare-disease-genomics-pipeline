#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage:"
    echo "bash pipeline/case_workflow/01_normalize_routed_small_variants.sh CASE_ID"
    echo
    echo "Example:"
    echo "bash pipeline/case_workflow/01_normalize_routed_small_variants.sh case001"
    exit 1
fi

CASE_ID="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ROUTING_QC="$PROJECT_ROOT/results/cases/$CASE_ID/final/${CASE_ID}.variant_routing_qc.tsv"

ROUTED_VCF_REL="results/cases/$CASE_ID/work/${CASE_ID}.small_variants.raw.vcf"
ROUTED_VCF="$PROJECT_ROOT/$ROUTED_VCF_REL"

NORMALIZATION_SCRIPT="$PROJECT_ROOT/pipeline/case_workflow/01_prepare_and_normalize.sh"

WRAPPER_QC="$PROJECT_ROOT/results/cases/$CASE_ID/final/${CASE_ID}.normalization_router_qc.tsv"

mkdir -p "$(dirname "$WRAPPER_QC")"

echo "========================================"
echo "ROUTED SMALL-VARIANT NORMALIZATION"
echo "========================================"
echo "Case ID: $CASE_ID"
echo

if [[ ! -f "$ROUTING_QC" ]]; then
    echo "ERROR: Routing QC file was not found:"
    echo "$ROUTING_QC"
    echo
    echo "Run the variant-routing stage first."
    exit 1
fi

if [[ ! -f "$NORMALIZATION_SCRIPT" ]]; then
    echo "ERROR: Existing normalization script was not found:"
    echo "$NORMALIZATION_SCRIPT"
    exit 1
fi

SMALL_BRANCH="$(
    awk -F $'\t' \
        '$1 == "small_variant_branch_required" {
            gsub(/\r/, "", $2)
            print $2
        }' \
        "$ROUTING_QC"
)"

SMALL_COUNT="$(
    awk -F $'\t' \
        '$1 == "small_variant_records" {
            gsub(/\r/, "", $2)
            print $2
        }' \
        "$ROUTING_QC"
)"

if [[ -z "$SMALL_BRANCH" ]]; then
    echo "ERROR: Could not read the small-variant routing decision."
    exit 1
fi

echo "Small-variant records: $SMALL_COUNT"
echo "Branch required:       $SMALL_BRANCH"
echo

if [[ "$SMALL_BRANCH" != "yes" ]]; then
    {
        printf "metric\tvalue\n"
        printf "case_id\t%s\n" "$CASE_ID"
        printf "status\tskipped\n"
        printf "reason\tno_small_variants_detected\n"
        printf "small_variant_records\t%s\n" "${SMALL_COUNT:-0}"
    } > "$WRAPPER_QC"

    echo "No small variants were detected."
    echo "Normalization branch skipped safely."
    echo
    echo "QC:"
    echo "$WRAPPER_QC"
    exit 0
fi

if [[ ! -s "$ROUTED_VCF" ]]; then
    echo "ERROR: Routed small-variant VCF is missing or empty:"
    echo "$ROUTED_VCF"
    exit 1
fi

RECORD_COUNT="$(
    awk '!/^#/ && NF > 0 {count++} END {print count+0}' \
        "$ROUTED_VCF"
)"

if [[ "$RECORD_COUNT" -eq 0 ]]; then
    echo "ERROR: Routed VCF contains no variant records."
    exit 1
fi

echo "[1/2] Running the existing normalization workflow"
echo "Input: $ROUTED_VCF_REL"
echo

cd "$PROJECT_ROOT"

bash "$NORMALIZATION_SCRIPT" \
    "$CASE_ID" \
    "$ROUTED_VCF_REL"

NORMALIZED_VCF="$PROJECT_ROOT/results/cases/$CASE_ID/work/${CASE_ID}.normalized.vcf.gz"

if [[ ! -s "$NORMALIZED_VCF" ]]; then
    echo "ERROR: Expected normalized VCF was not created:"
    echo "$NORMALIZED_VCF"
    exit 1
fi

echo
echo "[2/2] Creating routing-normalization QC"

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "status\tcompleted\n"
    printf "small_variant_records_received\t%s\n" "$RECORD_COUNT"
    printf "input_vcf\t%s\n" "$ROUTED_VCF_REL"
    printf "normalized_vcf\t%s\n" \
        "results/cases/$CASE_ID/work/${CASE_ID}.normalized.vcf.gz"
} > "$WRAPPER_QC"

echo
echo "Routing-normalization QC:"
echo "$WRAPPER_QC"

echo
echo "ROUTED NORMALIZATION COMPLETED SUCCESSFULLY"

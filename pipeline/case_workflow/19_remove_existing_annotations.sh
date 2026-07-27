#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
    cat <<'USAGE'
Usage:
  bash pipeline/case_workflow/19_remove_existing_annotations.sh \
    CASE_ID INPUT_VCF [--force]
USAGE
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ $# -ge 2 ]] || {
    usage
    exit 1
}

CASE_ID="$1"
INPUT_ARGUMENT="$2"
shift 2

FORCE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force)
            FORCE=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

[[ "$CASE_ID" =~ ^[A-Za-z0-9._-]+$ ]] \
    || die "Invalid CASE_ID."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

[[ -f "$INPUT_ARGUMENT" ]] \
    || die "Input VCF not found: $INPUT_ARGUMENT"

INPUT_VCF="$(readlink -f "$INPUT_ARGUMENT")"

case "$INPUT_VCF" in
    "$PROJECT_ROOT"/*)
        ;;
    *)
        die "Input VCF must be stored inside the project directory."
        ;;
esac

CORE_SIF="$PROJECT_ROOT/containers/core_tools.sif"

[[ -s "$CORE_SIF" ]] \
    || die "Core tools container is missing."

command -v apptainer >/dev/null 2>&1 \
    || die "Apptainer is unavailable."

OUTPUT_DIR="$PROJECT_ROOT/input/cases/$CASE_ID/prepared"

OUTPUT_VCF="$OUTPUT_DIR/${CASE_ID}.reannotation_ready.vcf.gz"
REPORT="$OUTPUT_DIR/${CASE_ID}.annotation_cleanup_report.tsv"

if [[ -e "$OUTPUT_VCF" || -e "$REPORT" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
        rm -f \
            "$OUTPUT_VCF" \
            "${OUTPUT_VCF}.tbi" \
            "${OUTPUT_VCF}.csi" \
            "$REPORT"
    else
        die "Cleanup outputs already exist. Use --force to replace them."
    fi
fi

mkdir -p "$OUTPUT_DIR"

INPUT_REL="${INPUT_VCF#"$PROJECT_ROOT/"}"
OUTPUT_REL="${OUTPUT_VCF#"$PROJECT_ROOT/"}"

CORE=(
    apptainer exec
    --bind "$PROJECT_ROOT:/project"
    "$CORE_SIF"
)

echo "========================================"
echo "EXISTING ANNOTATION CLEANUP"
echo "========================================"
echo "Case ID: $CASE_ID"
echo

HEADER="$(
    "${CORE[@]}" bcftools view -h \
        "/project/$INPUT_REL"
)"

ANNOTATION_TAGS=(
    CSQ
    ANN
    CLNSIG
    CLNDN
    CLNREVSTAT
    CLNDISDB
    CADD
    SpliceAI
    CLINGEN_REGION
    CLINGEN_HAPLO
    CLINGEN_TRIPLO
    GNOMADAF
    GNOMADAF_popmax
    most_severe_consequence
    most_severe_pli
    Annotation
    GeneticModels
    ModelScore
    Compounds
)

PRESENT_TAGS=()

for tag in "${ANNOTATION_TAGS[@]}"; do
    if grep -qE "^##INFO=<ID=${tag}," <<< "$HEADER"; then
        PRESENT_TAGS+=("$tag")
    fi
done

SOURCE_RECORDS="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$INPUT_REL" |
    wc -l
)"

if [[ "${#PRESENT_TAGS[@]}" -gt 0 ]]; then
    REMOVE_EXPRESSION=""

    for tag in "${PRESENT_TAGS[@]}"; do
        if [[ -n "$REMOVE_EXPRESSION" ]]; then
            REMOVE_EXPRESSION+=","
        fi

        REMOVE_EXPRESSION+="INFO/$tag"
    done

    echo "Removing existing annotation tags:"
    printf '  %s\n' "${PRESENT_TAGS[@]}"

    "${CORE[@]}" bcftools annotate \
        -x "$REMOVE_EXPRESSION" \
        -Oz \
        -o "/project/$OUTPUT_REL" \
        "/project/$INPUT_REL"
else
    echo "No known conflicting annotation tags were detected."

    "${CORE[@]}" bcftools view \
        -Oz \
        -o "/project/$OUTPUT_REL" \
        "/project/$INPUT_REL"
fi

"${CORE[@]}" bcftools index \
    --force \
    --tbi \
    "/project/$OUTPUT_REL"

OUTPUT_RECORDS="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$OUTPUT_REL" |
    wc -l
)"

[[ "$SOURCE_RECORDS" -eq "$OUTPUT_RECORDS" ]] \
    || die "Record count changed during annotation cleanup."

REMOVED_TAG_LIST="none"

if [[ "${#PRESENT_TAGS[@]}" -gt 0 ]]; then
    REMOVED_TAG_LIST="$(
        IFS=';'
        echo "${PRESENT_TAGS[*]}"
    )"
fi

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "cleanup_status\tcompleted\n"
    printf "source_records\t%s\n" "$SOURCE_RECORDS"
    printf "output_records\t%s\n" "$OUTPUT_RECORDS"
    printf "removed_annotation_count\t%s\n" "${#PRESENT_TAGS[@]}"
    printf "removed_annotation_tags\t%s\n" "$REMOVED_TAG_LIST"
    printf "source_vcf_sha256\t%s\n" \
        "$(sha256sum "$INPUT_VCF" | awk '{print $1}')"
    printf "output_vcf_sha256\t%s\n" \
        "$(sha256sum "$OUTPUT_VCF" | awk '{print $1}')"
    printf "original_source_modified\tno\n"
    printf "reannotation_ready_vcf\t%s\n" \
        "${OUTPUT_VCF#"$PROJECT_ROOT/"}"
} > "$REPORT"

echo
echo "Annotation cleanup completed."
echo "Records retained: $OUTPUT_RECORDS"
echo "Annotations removed: ${#PRESENT_TAGS[@]}"
echo
echo "Output:"
echo "$OUTPUT_VCF"
echo
echo "Report:"
echo "$REPORT"

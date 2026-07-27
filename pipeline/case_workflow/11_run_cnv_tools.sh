#!/usr/bin/env bash

set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage:"
    echo "bash pipeline/case_workflow/11_run_cnv_tools.sh CASE_ID"
    echo
    echo "Example:"
    echo "bash pipeline/case_workflow/11_run_cnv_tools.sh case_cnv001"
    exit 1
fi

CASE_ID="$1"
THREADS="${THREADS:-4}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# --------------------------------------------------
# Relative project paths
# --------------------------------------------------

CNV_INPUT_REL="results/cases/$CASE_ID/work/${CASE_ID}.cnvs.bed"
ROUTING_QC_REL="results/cases/$CASE_ID/final/${CASE_ID}.variant_routing_qc.tsv"

ANNOTSV_ANNOTATIONS_REL="resources/annotsv_annotations/AnnotSV_annotations"
CLASSIFYCNV_REL="tools/ClassifyCNV"

ANNOTSV_CONTAINER_REL="containers/annotsv.sif"
ISV_CONTAINER_REL="containers/isv.sif"
CORE_CONTAINER_REL="containers/core_tools.sif"

CNV_OUTPUT_DIR_REL="results/cases/$CASE_ID/cnv"
WORK_DIR_REL="results/cases/$CASE_ID/work"
LOG_DIR_REL="results/cases/$CASE_ID/logs"
FINAL_DIR_REL="results/cases/$CASE_ID/final"

ANNOTSV_OUTPUT_REL="$CNV_OUTPUT_DIR_REL/${CASE_ID}.AnnotSV.tsv"
CLASSIFY_OUTPUT_REL="$CNV_OUTPUT_DIR_REL/${CASE_ID}.ClassifyCNV"
ISV_INPUT_REL="$WORK_DIR_REL/${CASE_ID}.isv.headered.bed"
ISV_OUTPUT_REL="$CNV_OUTPUT_DIR_REL/${CASE_ID}.ISV_with_SHAP.tsv"

QC_FILE_REL="$FINAL_DIR_REL/${CASE_ID}.cnv_tools_qc.tsv"
SUMMARY_FILE_REL="$FINAL_DIR_REL/${CASE_ID}.cnv_tool_outputs.tsv"

# --------------------------------------------------
# Absolute paths
# --------------------------------------------------

CNV_INPUT="$PROJECT_ROOT/$CNV_INPUT_REL"
ROUTING_QC="$PROJECT_ROOT/$ROUTING_QC_REL"

ANNOTSV_ANNOTATIONS="$PROJECT_ROOT/$ANNOTSV_ANNOTATIONS_REL"
CLASSIFYCNV_DIR="$PROJECT_ROOT/$CLASSIFYCNV_REL"

ANNOTSV_CONTAINER="$PROJECT_ROOT/$ANNOTSV_CONTAINER_REL"
ISV_CONTAINER="$PROJECT_ROOT/$ISV_CONTAINER_REL"
CORE_CONTAINER="$PROJECT_ROOT/$CORE_CONTAINER_REL"

CNV_OUTPUT_DIR="$PROJECT_ROOT/$CNV_OUTPUT_DIR_REL"
WORK_DIR="$PROJECT_ROOT/$WORK_DIR_REL"
LOG_DIR="$PROJECT_ROOT/$LOG_DIR_REL"
FINAL_DIR="$PROJECT_ROOT/$FINAL_DIR_REL"

ANNOTSV_OUTPUT="$PROJECT_ROOT/$ANNOTSV_OUTPUT_REL"
CLASSIFY_OUTPUT="$PROJECT_ROOT/$CLASSIFY_OUTPUT_REL"
ISV_INPUT="$PROJECT_ROOT/$ISV_INPUT_REL"
ISV_OUTPUT="$PROJECT_ROOT/$ISV_OUTPUT_REL"

QC_FILE="$PROJECT_ROOT/$QC_FILE_REL"
SUMMARY_FILE="$PROJECT_ROOT/$SUMMARY_FILE_REL"

ANNOTSV_STDOUT="$LOG_DIR/${CASE_ID}.AnnotSV.stdout.log"
ANNOTSV_STDERR="$LOG_DIR/${CASE_ID}.AnnotSV.stderr.log"
PIPELINE_LOG="$LOG_DIR/${CASE_ID}.cnv_tools.log"

mkdir -p \
    "$CNV_OUTPUT_DIR" \
    "$WORK_DIR" \
    "$LOG_DIR" \
    "$FINAL_DIR"

exec > >(tee "$PIPELINE_LOG") 2>&1

echo "========================================"
echo "AUTOMATIC CNV TOOL WORKFLOW"
echo "========================================"
echo "Case ID:     $CASE_ID"
echo "Threads:     $THREADS"
echo "CNV input:   $CNV_INPUT_REL"
echo

# --------------------------------------------------
# Check routing decision
# --------------------------------------------------

if [[ ! -f "$ROUTING_QC" ]]; then
    echo "ERROR: Variant-routing QC file was not found:"
    echo "$ROUTING_QC"
    exit 1
fi

CNV_BRANCH="$(
    awk -F $'\t' '
        $1 == "cnv_branch_required" {
            gsub(/\r/, "", $2)
            print $2
        }
    ' "$ROUTING_QC"
)"

CNV_COUNT="$(
    awk -F $'\t' '
        $1 == "supported_DEL_DUP_records" {
            gsub(/\r/, "", $2)
            print $2
        }
    ' "$ROUTING_QC"
)"

echo "Detected DEL/DUP records: ${CNV_COUNT:-0}"
echo "CNV branch required:      ${CNV_BRANCH:-unknown}"
echo

if [[ "$CNV_BRANCH" != "yes" ]]; then
    {
        printf "metric\tvalue\n"
        printf "case_id\t%s\n" "$CASE_ID"
        printf "status\tskipped\n"
        printf "reason\tno_supported_DEL_DUP_records\n"
        printf "cnv_records\t%s\n" "${CNV_COUNT:-0}"
    } > "$QC_FILE"

    echo "No supported DEL/DUP records were detected."
    echo "CNV tools skipped safely."
    echo
    echo "QC:"
    echo "$QC_FILE"

    exit 0
fi

# --------------------------------------------------
# Validate resources
# --------------------------------------------------

for required_file in \
    "$CNV_INPUT" \
    "$ANNOTSV_CONTAINER" \
    "$ISV_CONTAINER" \
    "$CORE_CONTAINER" \
    "$CLASSIFYCNV_DIR/ClassifyCNV.py"
do
    if [[ ! -s "$required_file" ]]; then
        echo "ERROR: Required file is missing or empty:"
        echo "$required_file"
        exit 1
    fi
done

if [[ ! -d "$ANNOTSV_ANNOTATIONS" ]]; then
    echo "ERROR: AnnotSV annotation directory was not found:"
    echo "$ANNOTSV_ANNOTATIONS"
    exit 1
fi

command -v apptainer >/dev/null 2>&1 || {
    echo "ERROR: Apptainer is not available."
    exit 1
}

# --------------------------------------------------
# Validate the four-column BED
# --------------------------------------------------

echo "[1/7] Validating routed CNV BED"

awk '
BEGIN {
    errors = 0
    rows = 0
}
{
    rows++

    if (NF != 4) {
        print "Invalid column count on row", rows > "/dev/stderr"
        errors++
    }

    if ($1 !~ /^chr/) {
        print "Chromosome lacks chr prefix on row", rows > "/dev/stderr"
        errors++
    }

    if ($2 !~ /^[0-9]+$/ || $3 !~ /^[0-9]+$/) {
        print "Invalid coordinates on row", rows > "/dev/stderr"
        errors++
    }

    if ($2 ~ /^[0-9]+$/ && $3 ~ /^[0-9]+$/ && $3 <= $2) {
        print "End is not greater than start on row", rows > "/dev/stderr"
        errors++
    }

    if ($4 != "DEL" && $4 != "DUP") {
        print "Unsupported CNV type on row", rows > "/dev/stderr"
        errors++
    }
}
END {
    if (rows == 0 || errors > 0) {
        exit 1
    }
}
' "$CNV_INPUT"

BED_RECORDS="$(
    awk 'NF > 0 {count++} END {print count+0}' "$CNV_INPUT"
)"

echo "Validated CNV records: $BED_RECORDS"

CORE=(
    apptainer exec
    --bind "$PROJECT_ROOT:/project"
    "$CORE_CONTAINER"
)

ANNOTSV=(
    apptainer exec
    --bind "$PROJECT_ROOT:/project"
    "$ANNOTSV_CONTAINER"
)

ISV=(
    apptainer exec
    --bind "$PROJECT_ROOT:/project"
    "$ISV_CONTAINER"
)

# --------------------------------------------------
# AnnotSV
# --------------------------------------------------

echo
echo "[2/7] Running AnnotSV"

rm -f \
    "$ANNOTSV_OUTPUT" \
    "$ANNOTSV_STDOUT" \
    "$ANNOTSV_STDERR"

"${ANNOTSV[@]}" AnnotSV \
    -SVinputFile "/project/$CNV_INPUT_REL" \
    -outputFile "/project/$ANNOTSV_OUTPUT_REL" \
    -genomeBuild GRCh38 \
    -svtBEDcol 4 \
    -annotationsDir "/project/$ANNOTSV_ANNOTATIONS_REL" \
    > "$ANNOTSV_STDOUT" \
    2> "$ANNOTSV_STDERR"

if [[ ! -s "$ANNOTSV_OUTPUT" ]]; then
    echo "ERROR: AnnotSV output was not created."
    echo
    echo "AnnotSV stderr:"
    tail -n 30 "$ANNOTSV_STDERR" || true
    exit 1
fi

ANNOTSV_ROWS="$(
    awk 'NR > 1 && NF > 0 {count++} END {print count+0}' \
        "$ANNOTSV_OUTPUT"
)"

echo "AnnotSV data rows: $ANNOTSV_ROWS"

# --------------------------------------------------
# ClassifyCNV
# --------------------------------------------------

echo
echo "[3/7] Running ClassifyCNV"

rm -rf "$CLASSIFY_OUTPUT"

CLASSIFY_METHOD="core_tools_container"

if ! "${CORE[@]}" bash -lc "
    cd '/project/$CLASSIFYCNV_REL'

    python3 ClassifyCNV.py \
        --infile '/project/$CNV_INPUT_REL' \
        --GenomeBuild hg38 \
        --cores '$THREADS' \
        --precise \
        --outdir '/project/$CLASSIFY_OUTPUT_REL'
"; then
    echo "ClassifyCNV did not run inside core_tools.sif."
    echo "Trying the tested host installation."

    CLASSIFY_METHOD="host_python"

    (
        cd "$CLASSIFYCNV_DIR"

        python3 ClassifyCNV.py \
            --infile "$CNV_INPUT" \
            --GenomeBuild hg38 \
            --cores "$THREADS" \
            --precise \
            --outdir "$CLASSIFY_OUTPUT"
    )
fi

if [[ ! -d "$CLASSIFY_OUTPUT" ]]; then
    echo "ERROR: ClassifyCNV output directory was not created:"
    echo "$CLASSIFY_OUTPUT"
    exit 1
fi

CLASSIFY_FILE_COUNT="$(
    find "$CLASSIFY_OUTPUT" \
        -type f \
        | wc -l
)"

if [[ "$CLASSIFY_FILE_COUNT" -eq 0 ]]; then
    echo "ERROR: ClassifyCNV output directory contains no files."
    exit 1
fi

CLASSIFY_SCORESHEET="$(
    find "$CLASSIFY_OUTPUT" \
        -type f \
        \( \
            -iname '*scoresheet*' \
            -o -iname 'Scoresheet.txt' \
        \) \
        | head -n 1
)"

echo "ClassifyCNV method:       $CLASSIFY_METHOD"
echo "ClassifyCNV output files: $CLASSIFY_FILE_COUNT"

if [[ -n "$CLASSIFY_SCORESHEET" ]]; then
    echo "ClassifyCNV scoresheet:   $CLASSIFY_SCORESHEET"
else
    echo "ClassifyCNV scoresheet:   not located by filename"
fi

# --------------------------------------------------
# ISV-CNV
# --------------------------------------------------

echo
echo "[4/7] Preparing ISV-CNV input"

{
    printf "chromosome\tstart\tend\tcnv_type\n"
    cat "$CNV_INPUT"
} > "$ISV_INPUT"

echo
echo "[5/7] Running ISV-CNV"

rm -f "$ISV_OUTPUT"

"${ISV[@]}" python3 - \
    "/project/$ISV_INPUT_REL" \
    "/project/$ISV_OUTPUT_REL" <<'PY'
import sys

import pandas as pd
from isv import isv


input_bed = sys.argv[1]
output_tsv = sys.argv[2]

cnvs = pd.read_csv(input_bed, sep="\t")

result = isv(
    cnvs=cnvs,
    proba=True,
    shap=True,
    threshold=0.95,
)

result.to_csv(
    output_tsv,
    sep="\t",
    index=False,
)

print(f"ISV-CNV output: {output_tsv}")
PY

if [[ ! -s "$ISV_OUTPUT" ]]; then
    echo "ERROR: ISV-CNV output was not created."
    exit 1
fi

ISV_ROWS="$(
    awk 'NR > 1 && NF > 0 {count++} END {print count+0}' \
        "$ISV_OUTPUT"
)"

echo "ISV-CNV data rows: $ISV_ROWS"

# --------------------------------------------------
# Create compact output manifest
# --------------------------------------------------

echo
echo "[6/7] Creating CNV output manifest"

{
    printf "case_id\tchromosome\tstart\tend\tcnv_type\tAnnotSV_output\tClassifyCNV_directory\tISV_output\n"

    awk \
        -v case_id="$CASE_ID" \
        -v annotsv="$ANNOTSV_OUTPUT_REL" \
        -v classify="$CLASSIFY_OUTPUT_REL" \
        -v isv="$ISV_OUTPUT_REL" \
        '
        BEGIN {
            OFS = "\t"
        }
        {
            print case_id, $1, $2, $3, $4, annotsv, classify, isv
        }
        ' "$CNV_INPUT"
} > "$SUMMARY_FILE"

# --------------------------------------------------
# Create QC table
# --------------------------------------------------

echo
echo "[7/7] Creating CNV tools QC table"

CLASSIFY_SCORESHEET_REL=""

if [[ -n "$CLASSIFY_SCORESHEET" ]]; then
    CLASSIFY_SCORESHEET_REL="${CLASSIFY_SCORESHEET#$PROJECT_ROOT/}"
fi

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "status\tcompleted\n"
    printf "input_cnv_records\t%s\n" "$BED_RECORDS"
    printf "annotsv_data_rows\t%s\n" "$ANNOTSV_ROWS"
    printf "classifycnv_method\t%s\n" "$CLASSIFY_METHOD"
    printf "classifycnv_output_files\t%s\n" "$CLASSIFY_FILE_COUNT"
    printf "classifycnv_scoresheet\t%s\n" "$CLASSIFY_SCORESHEET_REL"
    printf "isv_data_rows\t%s\n" "$ISV_ROWS"
    printf "isv_threshold\t0.95\n"
    printf "cnv_input\t%s\n" "$CNV_INPUT_REL"
    printf "annotsv_output\t%s\n" "$ANNOTSV_OUTPUT_REL"
    printf "classifycnv_output_directory\t%s\n" "$CLASSIFY_OUTPUT_REL"
    printf "isv_output\t%s\n" "$ISV_OUTPUT_REL"
    printf "output_manifest\t%s\n" "$SUMMARY_FILE_REL"
} > "$QC_FILE"

echo
echo "CNV tool workflow summary"
echo "-------------------------"
echo "Input CNVs:             $BED_RECORDS"
echo "AnnotSV rows:           $ANNOTSV_ROWS"
echo "ClassifyCNV files:      $CLASSIFY_FILE_COUNT"
echo "ISV-CNV rows:           $ISV_ROWS"
echo
echo "AnnotSV:"
echo "$ANNOTSV_OUTPUT"
echo
echo "ClassifyCNV:"
echo "$CLASSIFY_OUTPUT"
echo
echo "ISV-CNV:"
echo "$ISV_OUTPUT"
echo
echo "QC:"
echo "$QC_FILE"
echo
echo "AUTOMATIC CNV TOOL WORKFLOW COMPLETED SUCCESSFULLY"

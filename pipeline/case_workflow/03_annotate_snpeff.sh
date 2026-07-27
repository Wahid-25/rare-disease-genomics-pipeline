#!/usr/bin/env bash

set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage:"
    echo "bash pipeline/case_workflow/03_annotate_snpeff.sh CASE_ID"
    echo
    echo "Example:"
    echo "bash pipeline/case_workflow/03_annotate_snpeff.sh case001"
    exit 1
fi

CASE_ID="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

JAVA_MEM="${JAVA_MEM:-8g}"

SNPEFF_DB="GRCh38.mane.1.2.ensembl"

CORE_REL="containers/core_tools.sif"
SNPEFF_REL="containers/snpeff.sif"
SNPEFF_DATA_REL="resources/snpeff_data/data"

INPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep.vcf.gz"
OUTPUT_REL="results/cases/$CASE_ID/annotated/${CASE_ID}.vep.snpeff.vcf.gz"

CORE_SIF="$PROJECT_ROOT/$CORE_REL"
SNPEFF_SIF="$PROJECT_ROOT/$SNPEFF_REL"
SNPEFF_DATA="$PROJECT_ROOT/$SNPEFF_DATA_REL"

INPUT_VCF="$PROJECT_ROOT/$INPUT_REL"
OUTPUT_VCF="$PROJECT_ROOT/$OUTPUT_REL"

RESULT_DIR="$PROJECT_ROOT/results/cases/$CASE_ID"
LOG_DIR="$RESULT_DIR/logs"
FINAL_DIR="$RESULT_DIR/final"
WORK_DIR="$RESULT_DIR/work"

LOG_FILE="$LOG_DIR/${CASE_ID}.snpeff.log"
QC_FILE="$FINAL_DIR/${CASE_ID}.snpeff_qc.tsv"
HEADER_FILE="$WORK_DIR/${CASE_ID}.snpeff.header.txt"

mkdir -p "$LOG_DIR" "$FINAL_DIR" "$WORK_DIR"

exec > >(tee "$LOG_FILE") 2>&1

echo "========================================"
echo "SNPEFF ANNOTATION"
echo "========================================"
echo "Case ID:       $CASE_ID"
echo "Input VCF:     $INPUT_REL"
echo "Database:      $SNPEFF_DB"
echo "Java memory:   $JAVA_MEM"
echo

for required_file in \
    "$CORE_SIF" \
    "$SNPEFF_SIF" \
    "$INPUT_VCF"
do
    if [[ ! -s "$required_file" ]]; then
        echo "ERROR: Required file is missing or empty:"
        echo "$required_file"
        exit 1
    fi
done

if [[ ! -d "$SNPEFF_DATA" ]]; then
    echo "ERROR: SnpEff data directory was not found:"
    echo "$SNPEFF_DATA"
    exit 1
fi

if [[ ! -d "$SNPEFF_DATA/$SNPEFF_DB" ]]; then
    echo "ERROR: SnpEff database directory was not found:"
    echo "$SNPEFF_DATA/$SNPEFF_DB"
    exit 1
fi

command -v apptainer >/dev/null 2>&1 || {
    echo "ERROR: Apptainer is not available."
    exit 1
}

CORE=(
    apptainer exec
    --bind "$PROJECT_ROOT:/project"
    "$CORE_SIF"
)

SNPEFF=(
    apptainer exec
    --bind "$PROJECT_ROOT:/project"
    "$SNPEFF_SIF"
)

echo "[1/5] Checking the SnpEff container"

"${SNPEFF[@]}" test -s /opt/snpEff/snpEff.jar || {
    echo "ERROR: /opt/snpEff/snpEff.jar is missing inside the container."
    exit 1
}

"${CORE[@]}" bcftools view -h \
    "/project/$INPUT_REL" >/dev/null

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

echo
echo "[2/5] Running SnpEff"

rm -f "$OUTPUT_VCF" "${OUTPUT_VCF}.tbi"

"${SNPEFF[@]}" java \
    -Xmx"$JAVA_MEM" \
    -jar /opt/snpEff/snpEff.jar \
    ann \
    -noStats \
    -canon \
    -hgvs \
    -dataDir "/project/$SNPEFF_DATA_REL" \
    "$SNPEFF_DB" \
    "/project/$INPUT_REL" \
| "${CORE[@]}" bgzip -c \
> "$OUTPUT_VCF"

echo
echo "[3/5] Indexing the SnpEff VCF"

"${CORE[@]}" tabix \
    -f \
    -p vcf \
    "/project/$OUTPUT_REL"

echo
echo "[4/5] Validating SnpEff annotations"

OUTPUT_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$OUTPUT_REL" |
    wc -l
)"

if [[ "$OUTPUT_COUNT" -ne "$INPUT_COUNT" ]]; then
    echo "ERROR: Record count changed during SnpEff annotation."
    echo "Input records:  $INPUT_COUNT"
    echo "Output records: $OUTPUT_COUNT"
    exit 1
fi

"${CORE[@]}" bcftools view -h \
    "/project/$OUTPUT_REL" \
    > "$HEADER_FILE"

if ! grep -q '^##INFO=<ID=ANN,' "$HEADER_FILE"; then
    echo "ERROR: SnpEff ANN field was not found in the output header."
    exit 1
fi

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

CSQ_PRESENT="no"

if grep -q '^##INFO=<ID=CSQ,' "$HEADER_FILE"; then
    CSQ_PRESENT="yes"
fi

echo
echo "[5/5] Creating SnpEff QC summary"

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "input_records\t%s\n" "$INPUT_COUNT"
    printf "output_records\t%s\n" "$OUTPUT_COUNT"
    printf "records_with_ANN\t%s\n" "$ANN_COUNT"
    printf "VEP_CSQ_preserved\t%s\n" "$CSQ_PRESENT"
    printf "snpeff_database\t%s\n" "$SNPEFF_DB"
    printf "snpeff_data_directory\t%s\n" "$SNPEFF_DATA_REL"
    printf "input_vcf\t%s\n" "$INPUT_REL"
    printf "output_vcf\t%s\n" "$OUTPUT_REL"
} > "$QC_FILE"

echo
echo "Input records:       $INPUT_COUNT"
echo "Output records:      $OUTPUT_COUNT"
echo "Records with ANN:    $ANN_COUNT"
echo "VEP CSQ preserved:   $CSQ_PRESENT"

echo
echo "SnpEff output:"
echo "$OUTPUT_VCF"

echo
echo "QC:"
echo "$QC_FILE"

echo
echo "SNPEFF ANNOTATION COMPLETED SUCCESSFULLY"

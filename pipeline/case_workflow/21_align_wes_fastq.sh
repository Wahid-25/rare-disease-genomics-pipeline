#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
    cat <<'USAGE'
Usage:
  THREADS=8 SORT_THREADS=4 \
  bash pipeline/case_workflow/21_align_wes_fastq.sh \
    CASE_ID READ1.fastq.gz READ2.fastq.gz [--force]
USAGE
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ $# -ge 3 ]] || {
    usage
    exit 1
}

CASE_ID="$1"
READ1_ARGUMENT="$2"
READ2_ARGUMENT="$3"
shift 3

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

THREADS="${THREADS:-8}"
SORT_THREADS="${SORT_THREADS:-4}"
SORT_MEM="${SORT_MEM:-1G}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

[[ -f "$READ1_ARGUMENT" ]] \
    || die "Read 1 not found: $READ1_ARGUMENT"

[[ -f "$READ2_ARGUMENT" ]] \
    || die "Read 2 not found: $READ2_ARGUMENT"

READ1="$(readlink -f "$READ1_ARGUMENT")"
READ2="$(readlink -f "$READ2_ARGUMENT")"

REFERENCE="$PROJECT_ROOT/resources/reference/hg38.fa"
CONTAINER="$PROJECT_ROOT/containers/read_processing.sif"

for required_file in \
    "$REFERENCE" \
    "${REFERENCE}.fai" \
    "${REFERENCE}.amb" \
    "${REFERENCE}.ann" \
    "${REFERENCE}.bwt" \
    "${REFERENCE}.pac" \
    "${REFERENCE}.sa" \
    "$CONTAINER"
do
    [[ -s "$required_file" ]] \
        || die "Required file missing or empty: $required_file"
done

case "$READ1" in
    "$PROJECT_ROOT"/*) ;;
    *) die "Read 1 must be stored inside the project directory." ;;
esac

case "$READ2" in
    "$PROJECT_ROOT"/*) ;;
    *) die "Read 2 must be stored inside the project directory." ;;
esac

CASE_DIR="$PROJECT_ROOT/validation/external_real_cases/$CASE_ID"
ALIGNMENT_DIR="$CASE_DIR/read_processing/alignment"
LOG_DIR="$CASE_DIR/read_processing/logs"
QC_DIR="$CASE_DIR/read_processing/qc"
TMP_DIR="$CASE_DIR/read_processing/tmp"
METADATA_DIR="$CASE_DIR/metadata"

BAM="$ALIGNMENT_DIR/${CASE_ID}.sorted.bam"
BAM_INDEX="${BAM}.bai"

BWA_LOG="$LOG_DIR/${CASE_ID}.bwa_mem.log"
SORT_LOG="$LOG_DIR/${CASE_ID}.samtools_sort.log"
FLAGSTAT="$QC_DIR/${CASE_ID}.flagstat.txt"
IDXSTATS="$QC_DIR/${CASE_ID}.idxstats.tsv"
STATS="$QC_DIR/${CASE_ID}.samtools_stats.txt"
REPORT="$METADATA_DIR/${CASE_ID}.alignment_report.tsv"

if [[ -e "$BAM" || -e "$REPORT" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
        rm -f \
            "$BAM" \
            "$BAM_INDEX" \
            "$BWA_LOG" \
            "$SORT_LOG" \
            "$FLAGSTAT" \
            "$IDXSTATS" \
            "$STATS" \
            "$REPORT"

        rm -rf "$TMP_DIR"
    else
        die "Alignment outputs already exist. Use --force to replace them."
    fi
fi

mkdir -p \
    "$ALIGNMENT_DIR" \
    "$LOG_DIR" \
    "$QC_DIR" \
    "$TMP_DIR" \
    "$METADATA_DIR"

python3 - "$READ1" "$READ2" <<'PY'
import gzip
import sys
from pathlib import Path

for filename in sys.argv[1:]:
    path = Path(filename)

    if path.stat().st_size < 1_000_000:
        raise SystemExit(
            f"ERROR: FASTQ appears unexpectedly small: {path}"
        )

    try:
        with gzip.open(
            path,
            "rt",
            encoding="utf-8",
            errors="replace",
        ) as handle:
            record = [handle.readline().rstrip() for _ in range(4)]
    except Exception as error:
        raise SystemExit(
            f"ERROR: Cannot read compressed FASTQ {path}: {error}"
        )

    if (
        len(record) != 4
        or not record[0].startswith("@")
        or not record[2].startswith("+")
    ):
        raise SystemExit(
            f"ERROR: Invalid FASTQ structure at start of {path}"
        )

print("FASTQ structure check passed.")
PY

READ1_REL="${READ1#"$PROJECT_ROOT/"}"
READ2_REL="${READ2#"$PROJECT_ROOT/"}"
REFERENCE_REL="${REFERENCE#"$PROJECT_ROOT/"}"
BAM_REL="${BAM#"$PROJECT_ROOT/"}"
TMP_REL="${TMP_DIR#"$PROJECT_ROOT/"}"

RUN_ID="$(basename "$READ1" | sed -E 's/_1\.fastq\.gz$//')"

READ_GROUP="@RG\tID:${RUN_ID}\tSM:${CASE_ID}\tLB:WES\tPL:ILLUMINA\tPU:${RUN_ID}"

RUN=(
    apptainer exec
    --bind "$PROJECT_ROOT:/project"
    "$CONTAINER"
)

START_EPOCH="$(date +%s)"
START_UTC="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

echo "========================================"
echo "WES ALIGNMENT TO GRCh38"
echo "========================================"
echo "Case ID:       $CASE_ID"
echo "Read 1:        $READ1"
echo "Read 2:        $READ2"
echo "BWA threads:   $THREADS"
echo "Sort threads:  $SORT_THREADS"
echo "Sort memory:   $SORT_MEM per thread"
echo
echo "Streaming BWA output directly into samtools sort."
echo "No intermediate SAM file will be created."
echo

"${RUN[@]}" bwa mem \
    -t "$THREADS" \
    -R "$READ_GROUP" \
    "/project/$REFERENCE_REL" \
    "/project/$READ1_REL" \
    "/project/$READ2_REL" \
    2> "$BWA_LOG" \
| "${RUN[@]}" samtools sort \
    -@ "$SORT_THREADS" \
    -m "$SORT_MEM" \
    -l 1 \
    -T "/project/$TMP_REL/${CASE_ID}" \
    -o "/project/$BAM_REL" \
    - \
    2> "$SORT_LOG"

"${RUN[@]}" samtools quickcheck \
    -v \
    "/project/$BAM_REL"

"${RUN[@]}" samtools index \
    -@ "$SORT_THREADS" \
    "/project/$BAM_REL"

"${RUN[@]}" samtools flagstat \
    -@ "$SORT_THREADS" \
    "/project/$BAM_REL" \
    > "$FLAGSTAT"

"${RUN[@]}" samtools idxstats \
    "/project/$BAM_REL" \
    > "$IDXSTATS"

"${RUN[@]}" samtools stats \
    -@ "$SORT_THREADS" \
    "/project/$BAM_REL" \
    > "$STATS"

END_EPOCH="$(date +%s)"
END_UTC="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
ELAPSED_SECONDS="$((END_EPOCH - START_EPOCH))"

TOTAL_READS="$(
    awk '/ in total / {print $1; exit}' "$FLAGSTAT"
)"

MAPPED_READS="$(
    awk '/ mapped \(/ {print $1; exit}' "$FLAGSTAT"
)"

PROPERLY_PAIRED="$(
    awk '/ properly paired / {print $1; exit}' "$FLAGSTAT"
)"

BAM_BYTES="$(stat -c '%s' "$BAM")"

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "alignment_status\tcompleted\n"
    printf "reference\tGRCh38\n"
    printf "aligner\tbwa mem\n"
    printf "output_format\tcoordinate-sorted BAM\n"
    printf "intermediate_SAM_created\tno\n"
    printf "read_trimming_performed\tno\n"
    printf "duplicate_marking_performed\tno\n"
    printf "BWA_threads\t%s\n" "$THREADS"
    printf "sort_threads\t%s\n" "$SORT_THREADS"
    printf "sort_memory_per_thread\t%s\n" "$SORT_MEM"
    printf "start_utc\t%s\n" "$START_UTC"
    printf "end_utc\t%s\n" "$END_UTC"
    printf "elapsed_seconds\t%s\n" "$ELAPSED_SECONDS"
    printf "total_reads\t%s\n" "${TOTAL_READS:-unknown}"
    printf "mapped_reads\t%s\n" "${MAPPED_READS:-unknown}"
    printf "properly_paired_reads\t%s\n" "${PROPERLY_PAIRED:-unknown}"
    printf "BAM_size_bytes\t%s\n" "$BAM_BYTES"
    printf "sorted_BAM\t%s\n" "${BAM#"$PROJECT_ROOT/"}"
    printf "BAM_index\t%s\n" "${BAM_INDEX#"$PROJECT_ROOT/"}"
    printf "flagstat_report\t%s\n" "${FLAGSTAT#"$PROJECT_ROOT/"}"
    printf "idxstats_report\t%s\n" "${IDXSTATS#"$PROJECT_ROOT/"}"
    printf "samtools_stats_report\t%s\n" "${STATS#"$PROJECT_ROOT/"}"
    printf "bwa_log\t%s\n" "${BWA_LOG#"$PROJECT_ROOT/"}"
    printf "sort_log\t%s\n" "${SORT_LOG#"$PROJECT_ROOT/"}"
} > "$REPORT"

rm -rf "$TMP_DIR"

echo
echo "========================================"
echo "ALIGNMENT COMPLETED"
echo "========================================"
echo "Sorted BAM:"
echo "$BAM"
echo
echo "Alignment QC:"
echo "$FLAGSTAT"
echo
echo "Report:"
echo "$REPORT"

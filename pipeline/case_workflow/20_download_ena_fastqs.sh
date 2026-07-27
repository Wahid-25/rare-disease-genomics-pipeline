#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
    cat <<'USAGE'
Usage:
  bash pipeline/case_workflow/20_download_ena_fastqs.sh \
    CASE_ID ENA_FASTQ_MANIFEST

The ENA manifest must contain:
  fastq_ftp
  fastq_bytes
  fastq_md5
USAGE
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ $# -eq 2 ]] || {
    usage
    exit 1
}

CASE_ID="$1"
MANIFEST_ARGUMENT="$2"

[[ "$CASE_ID" =~ ^[A-Za-z0-9._-]+$ ]] \
    || die "Invalid CASE_ID."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

[[ -f "$MANIFEST_ARGUMENT" ]] \
    || die "ENA manifest not found: $MANIFEST_ARGUMENT"

command -v curl >/dev/null 2>&1 \
    || die "curl is not installed."

command -v md5sum >/dev/null 2>&1 \
    || die "md5sum is not installed."

MANIFEST="$(readlink -f "$MANIFEST_ARGUMENT")"

CASE_DIR="$PROJECT_ROOT/validation/external_real_cases/$CASE_ID"
RAW_DIR="$CASE_DIR/raw_reads"
METADATA_DIR="$CASE_DIR/metadata"
LOG_DIR="$CASE_DIR/read_processing/logs"

PLAN_FILE="$METADATA_DIR/FASTQ_download_plan.tsv"
CHECKSUM_FILE="$METADATA_DIR/FASTQ_checksums.md5"
REPORT_FILE="$METADATA_DIR/FASTQ_download_report.tsv"

mkdir -p \
    "$RAW_DIR" \
    "$METADATA_DIR" \
    "$LOG_DIR"

python3 - \
    "$MANIFEST" \
    "$PLAN_FILE" <<'PY'
import csv
import sys
from pathlib import Path
from urllib.parse import urlparse

manifest = Path(sys.argv[1])
output = Path(sys.argv[2])

with manifest.open(
    encoding="utf-8-sig",
    newline="",
) as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))

if not rows:
    raise SystemExit("ERROR: ENA manifest contains no data rows.")

row = rows[0]

required = {
    "fastq_ftp",
    "fastq_bytes",
    "fastq_md5",
}

missing = required - set(row)

if missing:
    raise SystemExit(
        "ERROR: Missing manifest columns: "
        + ", ".join(sorted(missing))
    )

urls = [
    value.strip()
    for value in row["fastq_ftp"].split(";")
    if value.strip()
]

sizes = [
    value.strip()
    for value in row["fastq_bytes"].split(";")
    if value.strip()
]

md5s = [
    value.strip().lower()
    for value in row["fastq_md5"].split(";")
    if value.strip()
]

if not urls:
    raise SystemExit("ERROR: No FASTQ URLs found.")

if not (
    len(urls) == len(sizes) == len(md5s)
):
    raise SystemExit(
        "ERROR: FASTQ URL, size and MD5 counts differ."
    )

with output.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:
    writer = csv.writer(
        handle,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writerow(
        [
            "url",
            "expected_bytes",
            "expected_md5",
            "filename",
        ]
    )

    for url, size, md5 in zip(urls, sizes, md5s):
        path_component = urlparse(
            url if "://" in url else f"https://{url}"
        ).path

        filename = Path(path_component).name

        if not filename:
            raise SystemExit(
                f"ERROR: Could not determine filename: {url}"
            )

        if not size.isdigit():
            raise SystemExit(
                f"ERROR: Invalid expected size: {size}"
            )

        if len(md5) != 32:
            raise SystemExit(
                f"ERROR: Invalid MD5 value: {md5}"
            )

        writer.writerow(
            [url, size, md5, filename]
        )

print(f"FASTQ files planned: {len(urls)}")
PY

download_one() {
    local url="$1"
    local expected_bytes="$2"
    local expected_md5="$3"
    local filename="$4"

    local source_url
    local final_file
    local partial_file
    local actual_bytes
    local actual_md5

    case "$url" in
        https://*|http://*)
            source_url="$url"
            ;;

        ftp://*)
            source_url="https://${url#ftp://}"
            ;;

        *)
            source_url="https://$url"
            ;;
    esac

    final_file="$RAW_DIR/$filename"
    partial_file="${final_file}.part"

    echo "FASTQ: $filename"
    echo "URL:   $source_url"

    if [[ -f "$final_file" ]]; then
        actual_bytes="$(stat -c '%s' "$final_file")"
        actual_md5="$(
            md5sum "$final_file" |
            awk '{print $1}'
        )"

        if [[ "$actual_bytes" == "$expected_bytes" \
           && "$actual_md5" == "$expected_md5" ]]
        then
            echo "Already downloaded and verified."
            return 0
        fi

        mv \
            "$final_file" \
            "${final_file}.invalid.$(date +%s)"
    fi

    curl \
        --fail \
        --location \
        --continue-at - \
        --retry 10 \
        --retry-all-errors \
        --retry-delay 5 \
        --connect-timeout 30 \
        --output "$partial_file" \
        "$source_url"

    actual_bytes="$(stat -c '%s' "$partial_file")"

    if [[ "$actual_bytes" != "$expected_bytes" ]]; then
        echo "ERROR: Size mismatch for $filename" >&2
        echo "Expected: $expected_bytes" >&2
        echo "Observed: $actual_bytes" >&2
        return 1
    fi

    actual_md5="$(
        md5sum "$partial_file" |
        awk '{print $1}'
    )"

    if [[ "$actual_md5" != "$expected_md5" ]]; then
        echo "ERROR: MD5 mismatch for $filename" >&2
        echo "Expected: $expected_md5" >&2
        echo "Observed: $actual_md5" >&2
        return 1
    fi

    mv "$partial_file" "$final_file"

    echo "Download and checksum verification passed."
}

export -f download_one
export RAW_DIR

echo "========================================"
echo "ENA FASTQ PARALLEL DOWNLOAD"
echo "========================================"
echo "Case ID: $CASE_ID"
echo

PIDS=()
FILES=()

while IFS=$'\t' read -r \
    url \
    expected_bytes \
    expected_md5 \
    filename
do
    url="${url%$'\r'}"
    expected_bytes="${expected_bytes%$'\r'}"
    expected_md5="${expected_md5%$'\r'}"
    filename="${filename%$'\r'}"

    [[ "$url" == "url" ]] && continue

    (
        download_one \
            "$url" \
            "$expected_bytes" \
            "$expected_md5" \
            "$filename"
    ) > "$LOG_DIR/${filename}.download.log" 2>&1 &

    PIDS+=("$!")
    FILES+=("$filename")

    echo "Started: $filename"
done < "$PLAN_FILE"

FAILED=0

for index in "${!PIDS[@]}"; do
    pid="${PIDS[$index]}"
    filename="${FILES[$index]}"

    if wait "$pid"; then
        echo "Completed: $filename"
    else
        echo "FAILED: $filename" >&2
        echo "Log: $LOG_DIR/${filename}.download.log" >&2
        FAILED=1
    fi
done

[[ "$FAILED" -eq 0 ]] \
    || die "One or more FASTQ downloads failed."

: > "$CHECKSUM_FILE"

TOTAL_BYTES=0
FILE_COUNT=0

while IFS=$'\t' read -r \
    url \
    expected_bytes \
    expected_md5 \
    filename
do
    url="${url%$'\r'}"
    expected_bytes="${expected_bytes%$'\r'}"
    expected_md5="${expected_md5%$'\r'}"
    filename="${filename%$'\r'}"

    [[ "$url" == "url" ]] && continue

    final_file="$RAW_DIR/$filename"

    [[ -s "$final_file" ]] \
        || die "Downloaded FASTQ is missing: $final_file"

    printf "%s  %s\n" \
        "$expected_md5" \
        "$final_file" \
        >> "$CHECKSUM_FILE"

    TOTAL_BYTES=$((TOTAL_BYTES + expected_bytes))
    FILE_COUNT=$((FILE_COUNT + 1))
done < "$PLAN_FILE"

md5sum --check "$CHECKSUM_FILE"

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "download_status\tcompleted\n"
    printf "download_method\tparallel_https_with_resume\n"
    printf "FASTQ_file_count\t%s\n" "$FILE_COUNT"
    printf "total_bytes\t%s\n" "$TOTAL_BYTES"
    printf "total_GiB\t%.2f\n" \
        "$(awk -v value="$TOTAL_BYTES" \
            'BEGIN {print value/(1024^3)}')"
    printf "size_verification\tpassed\n"
    printf "MD5_verification\tpassed\n"
    printf "source_manifest_sha256\t%s\n" \
        "$(sha256sum "$MANIFEST" | awk '{print $1}')"
    printf "download_plan\t%s\n" \
        "${PLAN_FILE#"$PROJECT_ROOT/"}"
    printf "checksum_file\t%s\n" \
        "${CHECKSUM_FILE#"$PROJECT_ROOT/"}"
    printf "raw_reads_directory\t%s\n" \
        "${RAW_DIR#"$PROJECT_ROOT/"}"
} > "$REPORT_FILE"

echo
echo "========================================"
echo "FASTQ DOWNLOAD COMPLETED"
echo "========================================"
echo "Files:       $FILE_COUNT"
echo "Total size:  $(du -sh "$RAW_DIR" | cut -f1)"
echo "Checksums:   passed"
echo
echo "Raw reads:"
echo "$RAW_DIR"
echo
echo "Report:"
echo "$REPORT_FILE"

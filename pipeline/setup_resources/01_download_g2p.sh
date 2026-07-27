#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RESOURCE_DIR="$PROJECT_ROOT/resources/gene_disease/g2p"

SOURCE_URL="https://www.ebi.ac.uk/gene2phenotype/api/panel/all/download"
DOWNLOAD_DATE="$(date -u +%F)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

DATED_FILE="$RESOURCE_DIR/AllG2P.official.${DOWNLOAD_DATE}.${STAMP}.csv"
OFFICIAL_FILE="$RESOURCE_DIR/AllG2P.official.csv"
LATEST_FILE="$RESOURCE_DIR/AllG2P.latest.csv"
TEMP_FILE="$RESOURCE_DIR/.AllG2P.download.${STAMP}.tmp"
OFFICIAL_TEMP="$RESOURCE_DIR/.AllG2P.official.${STAMP}.tmp"
LATEST_TEMP="$RESOURCE_DIR/.AllG2P.latest.${STAMP}.tmp"
METADATA_FILE="$RESOURCE_DIR/AllG2P.metadata.tsv"
METADATA_TEMP="$RESOURCE_DIR/.AllG2P.metadata.${STAMP}.tmp"

cleanup() {
    rm -f \
        "$TEMP_FILE" \
        "$OFFICIAL_TEMP" \
        "$LATEST_TEMP" \
        "$METADATA_TEMP"
}
trap cleanup EXIT

mkdir -p "$RESOURCE_DIR"

echo "========================================"
echo "OFFICIAL G2P RESOURCE DOWNLOAD"
echo "========================================"
echo "Source:      $SOURCE_URL"
echo "Destination: $RESOURCE_DIR"
echo "Date:        $DOWNLOAD_DATE"
echo

echo "[1/5] Downloading the complete G2P dataset"

curl \
    --location \
    --fail \
    --retry 3 \
    --retry-delay 3 \
    --output "$TEMP_FILE" \
    "$SOURCE_URL"

echo
echo "[2/5] Validating the downloaded file"

[[ -s "$TEMP_FILE" ]] \
    || { echo "ERROR: Downloaded G2P file is empty."; exit 1; }

LINE_COUNT="$(wc -l < "$TEMP_FILE")"

if [[ "$LINE_COUNT" -lt 10 ]]; then
    echo "ERROR: Downloaded file contains too few lines: $LINE_COUNT"
    exit 1
fi

if grep -qi '<html' "$TEMP_FILE"; then
    echo "ERROR: Downloaded file appears to be HTML."
    exit 1
fi

FIRST_LINE="$(head -n 1 "$TEMP_FILE")"

for required_column in \
    "gene symbol" \
    "disease name" \
    "allelic requirement" \
    "confidence"
do
    if [[ "$FIRST_LINE" != *"$required_column"* ]]; then
        echo "ERROR: Required G2P column is missing: $required_column"
        exit 1
    fi
done

echo "Downloaded lines: $LINE_COUNT"
echo "Header: $FIRST_LINE"

echo
echo "[3/5] Creating immutable dated official snapshot"

mv -f "$TEMP_FILE" "$DATED_FILE"

SHA256="$(sha256sum "$DATED_FILE" | awk '{print $1}')"
DATA_ROWS="$((LINE_COUNT - 1))"

echo
echo "[4/5] Atomically refreshing production and compatibility copies"

cp -f "$DATED_FILE" "$OFFICIAL_TEMP"
mv -f "$OFFICIAL_TEMP" "$OFFICIAL_FILE"

cp -f "$OFFICIAL_FILE" "$LATEST_TEMP"
mv -f "$LATEST_TEMP" "$LATEST_FILE"

{
    printf "field\tvalue\n"
    printf "resource\tGene2Phenotype_All_Panels\n"
    printf "resource_role\tofficial_production_baseline\n"
    printf "download_date_utc\t%s\n" "$DOWNLOAD_DATE"
    printf "download_timestamp_utc\t%s\n" "$STAMP"
    printf "source_url\t%s\n" "$SOURCE_URL"
    printf "versioned_official_file\t%s\n" "$(basename "$DATED_FILE")"
    printf "official_production_file\t%s\n" "$(basename "$OFFICIAL_FILE")"
    printf "compatibility_latest_file\t%s\n" "$(basename "$LATEST_FILE")"
    printf "validation_file\tAllG2P.validation.csv\n"
    printf "data_rows\t%s\n" "$DATA_ROWS"
    printf "sha256\t%s\n" "$SHA256"
} > "$METADATA_TEMP"

mv -f "$METADATA_TEMP" "$METADATA_FILE"

echo
echo "[5/5] Resource setup completed"
echo
echo "Official production file:"
echo "$OFFICIAL_FILE"
echo
echo "Dated official snapshot:"
echo "$DATED_FILE"
echo
echo "Compatibility copy:"
echo "$LATEST_FILE"
echo
echo "Metadata:"
echo "$METADATA_FILE"
echo
echo "NOTE: Validation mode rebuilds AllG2P.validation.csv separately."
echo "G2P DOWNLOAD COMPLETED SUCCESSFULLY"

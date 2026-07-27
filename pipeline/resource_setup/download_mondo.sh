#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." \
    && pwd
)"

BASE_DIR="$PROJECT_ROOT/resources/disease_ontology/mondo"
TEMP_DIR="$BASE_DIR/.download_tmp"
SOURCE_URL="https://purl.obolibrary.org/obo/mondo/mondo.obo"

mkdir -p "$TEMP_DIR"

TEMP_FILE="$TEMP_DIR/mondo.obo"

echo "Downloading the official stable Mondo OBO release..."

curl \
    --fail \
    --location \
    --retry 3 \
    --retry-delay 5 \
    --connect-timeout 30 \
    --output "$TEMP_FILE" \
    "$SOURCE_URL"

if [[ ! -s "$TEMP_FILE" ]]; then
    echo "ERROR: Downloaded Mondo file is empty." >&2
    exit 1
fi

if ! grep -q '^ontology: mondo' "$TEMP_FILE"; then
    echo "ERROR: Downloaded file is not a Mondo OBO ontology." >&2
    exit 1
fi

if ! grep -q '^id: MONDO:' "$TEMP_FILE"; then
    echo "ERROR: No MONDO terms were found." >&2
    exit 1
fi

DATA_VERSION="$(
    awk -F ': ' '
        /^data-version:/ {
            print $2
            exit
        }
    ' "$TEMP_FILE"
)"

RELEASE_DATE="$(
    grep -Eo \
        '[0-9]{4}-[0-9]{2}-[0-9]{2}' \
        <<< "$DATA_VERSION" \
    | head -n 1
)"

if [[ -z "$RELEASE_DATE" ]]; then
    echo "ERROR: Could not determine the Mondo release date." >&2
    echo "data-version: $DATA_VERSION" >&2
    exit 1
fi

RELEASE_NAME="v${RELEASE_DATE}"
RELEASE_DIR="$BASE_DIR/$RELEASE_NAME"

mkdir -p "$RELEASE_DIR"

mv -f \
    "$TEMP_FILE" \
    "$RELEASE_DIR/mondo.obo"

SHA256="$(
    sha256sum "$RELEASE_DIR/mondo.obo" \
    | awk '{print $1}'
)"

SIZE_BYTES="$(
    stat -c '%s' "$RELEASE_DIR/mondo.obo"
)"

TERM_COUNT="$(
    grep -c '^id: MONDO:' \
    "$RELEASE_DIR/mondo.obo"
)"

XREF_COUNT="$(
    grep -c '^xref:' \
    "$RELEASE_DIR/mondo.obo"
)"

{
    printf "field\tvalue\n"
    printf "resource\tMondo Disease Ontology\n"
    printf "release\t%s\n" "$RELEASE_NAME"
    printf "release_date\t%s\n" "$RELEASE_DATE"
    printf "data_version\t%s\n" "$DATA_VERSION"
    printf "source_url\t%s\n" "$SOURCE_URL"
    printf "file\tmondo.obo\n"
    printf "size_bytes\t%s\n" "$SIZE_BYTES"
    printf "sha256\t%s\n" "$SHA256"
    printf "mondo_terms\t%s\n" "$TERM_COUNT"
    printf "xref_lines\t%s\n" "$XREF_COUNT"
    printf "license\tCC-BY-4.0\n"
} > "$RELEASE_DIR/release_manifest.tsv"

CURRENT_LINK="$BASE_DIR/current"

rm -f "$CURRENT_LINK"

ln -s \
    "$RELEASE_NAME" \
    "$CURRENT_LINK"

rm -rf "$TEMP_DIR"

echo
echo "Mondo installation completed."
echo "Release:       $RELEASE_NAME"
echo "Data version:  $DATA_VERSION"
echo "Terms:         $TERM_COUNT"
echo "Xrefs:         $XREF_COUNT"
echo "Directory:     $RELEASE_DIR"
echo "Current link:  $CURRENT_LINK"

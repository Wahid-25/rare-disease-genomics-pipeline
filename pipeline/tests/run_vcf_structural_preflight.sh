#!/usr/bin/env bash
set -Eeuo pipefail

cd "${1:-$HOME/rare_disease_project}"

BASE="validation/universal_pipeline_testing"
VCF_DIR="$BASE/inputs/vcfs"
MANIFEST_DIR="$BASE/manifests"
REPORT="$MANIFEST_DIR/vcf_preflight.tsv"
CONTAINER="containers/core_tools.sif"

mkdir -p "$MANIFEST_DIR"

[[ -d "$VCF_DIR" ]] || {
    echo "ERROR: VCF directory not found: $VCF_DIR" >&2
    exit 1
}

[[ -s "$CONTAINER" ]] || {
    echo "ERROR: Container not found: $CONTAINER" >&2
    exit 1
}

mapfile -t VCFS < <(
    find "$VCF_DIR" -maxdepth 1 -type f -name '*.vcf' -print | sort
)

[[ "${#VCFS[@]}" -eq 13 ]] || {
    echo "ERROR: Expected 13 VCF files but found ${#VCFS[@]}." >&2
    exit 1
}

printf 'file\trecords\tsample_count\tsamples\tfirst_contig\tcolumn_mismatches\tbcftools_read\n' > "$REPORT"

echo "=== VCF STRUCTURAL PREFLIGHT ==="

failures=0

for VCF in "${VCFS[@]}"
do
    NAME="$(basename "$VCF")"

    RECORDS="$(awk '!/^#/ {count++} END {print count + 0}' "$VCF")"

    SAMPLE_LIST="$(
        apptainer exec "$CONTAINER" bcftools query -l "$VCF" 2>/dev/null |
        paste -sd ',' -
    )"

    if [[ -n "$SAMPLE_LIST" ]]; then
        SAMPLE_COUNT="$(
            tr ',' '\n' <<<"$SAMPLE_LIST" |
            awk 'NF {count++} END {print count + 0}'
        )"
    else
        SAMPLE_COUNT=0
        SAMPLE_LIST="none"
    fi

    FIRST_CONTIG="$(
        apptainer exec "$CONTAINER" bcftools query -f '%CHROM\n' "$VCF" 2>/dev/null |
        awk 'NR == 1 {first = $0} END {print first}'
    )"
    [[ -n "$FIRST_CONTIG" ]] || FIRST_CONTIG="none"

    COLUMN_MISMATCHES="$(
        awk -F $'\t' '
        /^#CHROM/ {
            expected = NF
            next
        }
        !/^#/ && NF != expected {
            mismatches++
        }
        END {
            print mismatches + 0
        }
        ' "$VCF"
    )"

    if apptainer exec "$CONTAINER" bcftools view -Ou "$VCF" >/dev/null 2>&1
    then
        READ_STATUS="PASS"
    else
        READ_STATUS="FAIL"
        failures=$((failures + 1))
    fi

    if [[ "$COLUMN_MISMATCHES" -ne 0 ]]; then
        failures=$((failures + 1))
    fi

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n'         "$NAME" "$RECORDS" "$SAMPLE_COUNT" "$SAMPLE_LIST"         "$FIRST_CONTIG" "$COLUMN_MISMATCHES" "$READ_STATUS"         >> "$REPORT"

    printf '%-52s records=%-6s samples=%-2s mismatches=%-2s read=%s\n'         "$NAME" "$RECORDS" "$SAMPLE_COUNT"         "$COLUMN_MISMATCHES" "$READ_STATUS"
done

echo
echo "=== PREFLIGHT TABLE ==="
column -t -s $'\t' "$REPORT"

echo
if [[ "$failures" -eq 0 ]]; then
    echo "PASS: All 13 VCFs are structurally readable with zero column mismatches."
else
    echo "FAIL: Structural preflight found $failures problem(s)." >&2
    exit 1
fi

echo
echo "Report: $REPORT"

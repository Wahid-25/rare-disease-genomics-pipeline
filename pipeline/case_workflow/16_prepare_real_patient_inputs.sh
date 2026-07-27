#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
    cat <<'USAGE'
Usage:
  bash pipeline/case_workflow/16_prepare_real_patient_inputs.sh \
    CASE_ID INPUT_VCF PHENOTYPE_FILE \
    [--sample SAMPLE_NAME] \
    [--confirm-grch38] \
    [--force]

Options:
  --sample NAME       Select one patient from a multisample VCF.
  --confirm-grch38    Confirm GRCh38 when the VCF header does not declare
                      its genome build.
  --force             Replace previously prepared files for this case.

Examples:
  bash pipeline/case_workflow/16_prepare_real_patient_inputs.sh \
    patient001 patient.vcf.gz phenotypes.txt \
    --sample PATIENT_01 \
    --confirm-grch38

  bash pipeline/case_workflow/16_prepare_real_patient_inputs.sh \
    case_prepare_test \
    input/cases/case_mixed001/case_mixed001.raw.vcf \
    input/cases/case_mixed001/phenotypes.txt \
    --force
USAGE
}


die() {
    echo "ERROR: $*" >&2
    exit 1
}


if [[ $# -lt 3 ]]; then
    usage
    exit 1
fi

CASE_ID="$1"
INPUT_VCF_ARGUMENT="$2"
PHENOTYPE_ARGUMENT="$3"
shift 3

SELECTED_SAMPLE_ARGUMENT=""
CONFIRM_GRCH38=0
FORCE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample)
            [[ $# -ge 2 ]] || die "--sample requires a sample name."
            SELECTED_SAMPLE_ARGUMENT="$2"
            shift 2
            ;;

        --confirm-grch38)
            CONFIRM_GRCH38=1
            shift
            ;;

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

if [[ ! "$CASE_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
    die "CASE_ID may contain only letters, numbers, dots, underscores and hyphens."
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

[[ -f "$INPUT_VCF_ARGUMENT" ]] \
    || die "Input VCF was not found: $INPUT_VCF_ARGUMENT"

[[ -f "$PHENOTYPE_ARGUMENT" ]] \
    || die "Phenotype file was not found: $PHENOTYPE_ARGUMENT"

INPUT_VCF_SOURCE="$(readlink -f "$INPUT_VCF_ARGUMENT")"
PHENOTYPE_SOURCE="$(readlink -f "$PHENOTYPE_ARGUMENT")"

case "$INPUT_VCF_SOURCE" in
    *.vcf|*.vcf.gz)
        ;;
    *)
        die "Input filename must end with .vcf or .vcf.gz"
        ;;
esac

CASE_INPUT_DIR="$PROJECT_ROOT/input/cases/$CASE_ID"
PREPARED_DIR="$CASE_INPUT_DIR/prepared"

CASE_RESULT_DIR="$PROJECT_ROOT/results/cases/$CASE_ID"
WORK_DIR_REL="results/cases/$CASE_ID/preparation_work"
WORK_DIR="$PROJECT_ROOT/$WORK_DIR_REL"
LOG_DIR="$CASE_RESULT_DIR/logs"
FINAL_DIR="$CASE_RESULT_DIR/final"

READY_VCF="$PREPARED_DIR/${CASE_ID}.ready.vcf.gz"
READY_HPO="$PREPARED_DIR/phenotypes.ready.txt"
PREPARATION_REPORT="$PREPARED_DIR/${CASE_ID}.preparation_report.tsv"
COPIED_READINESS_REPORT="$PREPARED_DIR/${CASE_ID}.readiness.tsv"

PIPELINE_LOG="$LOG_DIR/${CASE_ID}.input_preparation.log"
NORMALIZATION_LOG="$LOG_DIR/${CASE_ID}.normalization.stderr.log"

CORE_SIF="$PROJECT_ROOT/containers/core_tools.sif"
REFERENCE="$PROJECT_ROOT/resources/reference/hg38.fa"
READINESS_SCRIPT="$PROJECT_ROOT/pipeline/case_workflow/15_check_real_patient_readiness.py"

if [[ -e "$READY_VCF" || -e "$PREPARATION_REPORT" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
        rm -rf "$PREPARED_DIR" "$WORK_DIR"
    else
        die "Prepared files already exist. Use --force to replace them."
    fi
fi

mkdir -p \
    "$PREPARED_DIR" \
    "$WORK_DIR" \
    "$LOG_DIR" \
    "$FINAL_DIR"

exec > >(tee "$PIPELINE_LOG") 2>&1

trap '
    status=$?
    echo
    echo "PATIENT INPUT PREPARATION FAILED"
    echo "Line: $LINENO"
    echo "Exit status: $status"
    echo "Log: '"$PIPELINE_LOG"'"
    exit $status
' ERR

for required_file in \
    "$CORE_SIF" \
    "$REFERENCE" \
    "${REFERENCE}.fai" \
    "$READINESS_SCRIPT"
do
    [[ -s "$required_file" ]] \
        || die "Required file is missing or empty: $required_file"
done

command -v apptainer >/dev/null 2>&1 \
    || die "Apptainer is not available."

CORE=(
    apptainer exec
    --bind "$PROJECT_ROOT:/project"
    "$CORE_SIF"
)

# --------------------------------------------------
# Stage the external source with a neutral filename
# --------------------------------------------------

if [[ "$INPUT_VCF_SOURCE" == *.vcf.gz ]]; then
    STAGED_SOURCE="$WORK_DIR/source.vcf.gz"
else
    STAGED_SOURCE="$WORK_DIR/source.vcf"
fi

cp -f "$INPUT_VCF_SOURCE" "$STAGED_SOURCE"
cp -f "$PHENOTYPE_SOURCE" "$WORK_DIR/phenotypes.source.txt"

SOURCE_REL="${STAGED_SOURCE#"$PROJECT_ROOT/"}"

SOURCE_SHA256="$(sha256sum "$STAGED_SOURCE" | awk '{print $1}')"
SOURCE_SIZE="$(stat -c '%s' "$STAGED_SOURCE")"

echo "========================================"
echo "REAL-PATIENT INPUT PREPARATION"
echo "========================================"
echo "Case ID:             $CASE_ID"
echo "Assembly required:   GRCh38"
echo "Prepared sample ID:  $CASE_ID"
echo

# --------------------------------------------------
# Validate the source VCF
# --------------------------------------------------

echo "[1/10] Validating source VCF"

"${CORE[@]}" bcftools view -h \
    "/project/$SOURCE_REL" \
    >/dev/null

SOURCE_HEADER="$(
    "${CORE[@]}" bcftools view -h \
        "/project/$SOURCE_REL"
)"

if grep -qiE '^##reference=.*(GRCh37|hg19)' <<< "$SOURCE_HEADER"; then
    die "The VCF declares GRCh37/hg19. Do not relabel it as GRCh38. Obtain a GRCh38 VCF or use a separately validated liftover workflow."
fi

if grep -qiE '^##reference=.*(GRCh38|hg38)' <<< "$SOURCE_HEADER"; then
    ASSEMBLY_CONFIRMATION="declared_in_vcf_header"
else
    if [[ "$CONFIRM_GRCH38" -ne 1 ]]; then
        die "Genome build is not declared. Confirm it independently and rerun with --confirm-grch38."
    fi

    ASSEMBLY_CONFIRMATION="confirmed_by_user"
fi

SOURCE_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$SOURCE_REL" |
    wc -l
)"

[[ "$SOURCE_COUNT" -gt 0 ]] \
    || die "The source VCF contains no variant records."

echo "Source records:       $SOURCE_COUNT"
echo "Assembly confirmation: $ASSEMBLY_CONFIRMATION"

# --------------------------------------------------
# Detect sample structure and select a sample when needed
# --------------------------------------------------

echo
echo "[2/10] Inspecting sample structure"

mapfile -t SAMPLE_NAMES < <(
    "${CORE[@]}" bcftools query -l \
        "/project/$SOURCE_REL"
)

SAMPLE_COUNT="${#SAMPLE_NAMES[@]}"
SELECTED_SAMPLE_HASH="not_applicable"

if [[ "$SAMPLE_COUNT" -eq 0 ]]; then
    [[ -z "$SELECTED_SAMPLE_ARGUMENT" ]] \
        || die "--sample cannot be used because the VCF has no samples."

    echo "Source sample count:  0"
    echo "Sample selection:     not applicable"

else
    if [[ -n "$SELECTED_SAMPLE_ARGUMENT" ]]; then
        SAMPLE_FOUND=0

        for sample_name in "${SAMPLE_NAMES[@]}"; do
            if [[ "$sample_name" == "$SELECTED_SAMPLE_ARGUMENT" ]]; then
                SAMPLE_FOUND=1
                break
            fi
        done

        [[ "$SAMPLE_FOUND" -eq 1 ]] \
            || die "Requested sample was not found in the VCF."

    else
        if [[ "$SAMPLE_COUNT" -ne 1 ]]; then
            echo "The VCF contains $SAMPLE_COUNT samples."
            echo "Available sample names:"
            printf '  %s
' "${SAMPLE_NAMES[@]}"
            die "Rerun with --sample SAMPLE_NAME."
        fi

        SELECTED_SAMPLE_ARGUMENT="${SAMPLE_NAMES[0]}"
    fi

    SELECTED_SAMPLE_HASH="$(
        printf '%s' "$SELECTED_SAMPLE_ARGUMENT" |
        sha256sum |
        awk '{print $1}'
    )"

    echo "Source sample count:  $SAMPLE_COUNT"
    echo "Selected one sample:  yes"
    echo "Output sample name:    $CASE_ID"
fi

# --------------------------------------------------
# Inspect and standardize chromosome names
# --------------------------------------------------

echo
echo "[3/10] Preparing chromosome-name mapping"

CHROMOSOME_FILE="$WORK_DIR/source.chromosomes.txt"
RENAME_MAP="$WORK_DIR/rename_chromosomes.tsv"
UNSUPPORTED_CONTIGS="$WORK_DIR/unsupported_nonprefixed_contigs.txt"
COLLISIONS_FILE="$WORK_DIR/chromosome_name_collisions.txt"

"${CORE[@]}" bcftools query \
    -f '%CHROM\n' \
    "/project/$SOURCE_REL" |
sort -u > "$CHROMOSOME_FILE"

python3 - \
    "$CHROMOSOME_FILE" \
    "$RENAME_MAP" \
    "$UNSUPPORTED_CONTIGS" \
    "$COLLISIONS_FILE" <<'PY'
import sys
from pathlib import Path

chromosome_file = Path(sys.argv[1])
mapping_file = Path(sys.argv[2])
unsupported_file = Path(sys.argv[3])
collisions_file = Path(sys.argv[4])

chromosomes = {
    line.strip()
    for line in chromosome_file.read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip()
}

mapping = {}
unsupported = []

primary = {
    *(str(number) for number in range(1, 23)),
    "X",
    "Y",
    "M",
    "MT",
}

for chromosome in sorted(chromosomes):
    upper = chromosome.upper()

    if chromosome.startswith("chr"):
        if upper == "CHRMT":
            mapping[chromosome] = "chrM"
        continue

    if upper in primary:
        target = "chrM" if upper in {"M", "MT"} else f"chr{upper}"
        mapping[chromosome] = target
    else:
        unsupported.append(chromosome)

collisions = []

for source, target in mapping.items():
    if target in chromosomes and target != source:
        collisions.append(f"{source}\t{target}")

mapping_file.write_text(
    "".join(
        f"{source}\t{target}\n"
        for source, target in sorted(mapping.items())
    ),
    encoding="utf-8",
)

unsupported_file.write_text(
    "".join(f"{item}\n" for item in unsupported),
    encoding="utf-8",
)

collisions_file.write_text(
    "".join(f"{item}\n" for item in collisions),
    encoding="utf-8",
)
PY

if [[ -s "$UNSUPPORTED_CONTIGS" ]]; then
    echo "These non-prefixed alternate contigs cannot be renamed safely:"
    cat "$UNSUPPORTED_CONTIGS"
    die "Manual contig review is required."
fi

if [[ -s "$COLLISIONS_FILE" ]]; then
    echo "Conflicting chromosome names were found:"
    cat "$COLLISIONS_FILE"
    die "The VCF contains duplicate prefixed and non-prefixed chromosome namespaces."
fi

CHROMOSOME_RENAME_COUNT="$(
    awk 'NF == 2 {count++} END {print count+0}' \
        "$RENAME_MAP"
)"

echo "Chromosome names requiring conversion: $CHROMOSOME_RENAME_COUNT"

# --------------------------------------------------
# Select a sample when present and determine analysis mode
# --------------------------------------------------

echo
echo "[4/10] Preparing sample columns and determining mode"

SELECTED_BCF_REL="$WORK_DIR_REL/selected_sample.bcf"

if [[ "$SAMPLE_COUNT" -eq 0 ]]; then
    "${CORE[@]}" bcftools view \
        --output-type b \
        --output "/project/$SELECTED_BCF_REL" \
        "/project/$SOURCE_REL"
else
    "${CORE[@]}" bcftools view \
        --samples "$SELECTED_SAMPLE_ARGUMENT" \
        --output-type b \
        --output "/project/$SELECTED_BCF_REL" \
        "/project/$SOURCE_REL"
fi

SELECTED_HEADER="$(
    "${CORE[@]}" bcftools view -h \
        "/project/$SELECTED_BCF_REL"
)"

GT_CELL_COUNT=0
ALT_GT_CELL_COUNT=0

if grep -q '^##FORMAT=<ID=GT,' <<< "$SELECTED_HEADER"; then
    GT_LIST="$WORK_DIR/selected_genotypes.txt"

    "${CORE[@]}" bcftools query \
        -f '[%GT\n]' \
        "/project/$SELECTED_BCF_REL" \
        > "$GT_LIST"

    read -r GT_CELL_COUNT ALT_GT_CELL_COUNT < <(
        python3 - "$GT_LIST" <<'PYGT'
import sys
from pathlib import Path

path = Path(sys.argv[1])

total = 0
alternate = 0

for line in path.read_text(
    encoding="utf-8"
).splitlines():
    genotype = line.strip().replace("|", "/")

    if not genotype:
        continue

    total += 1

    alleles = genotype.split("/")

    if any(
        allele not in {"", ".", "0"}
        for allele in alleles
    ):
        alternate += 1

print(total, alternate)
PYGT
    )
fi

if [[ "$SAMPLE_COUNT" -eq 0 ]]; then
    ANALYSIS_MODE="site_annotation"
    GENOTYPE_AVAILABLE="no"
    INHERITANCE_EVALUATED="no"
    PATIENT_VARIANT_INTERPRETATION="no"
    CONFIDENCE_LEVEL="site_only_contextual"

elif [[ "$ALT_GT_CELL_COUNT" -gt 0 ]]; then
    ANALYSIS_MODE="genotype_aware"
    GENOTYPE_AVAILABLE="yes"
    INHERITANCE_EVALUATED="yes"
    PATIENT_VARIANT_INTERPRETATION="yes"
    CONFIDENCE_LEVEL="standard"

else
    ANALYSIS_MODE="annotation_only"
    GENOTYPE_AVAILABLE="no"
    INHERITANCE_EVALUATED="no"
    PATIENT_VARIANT_INTERPRETATION="conditional"
    CONFIDENCE_LEVEL="reduced"
fi

echo "Analysis mode:          $ANALYSIS_MODE"
echo "GT cells inspected:     $GT_CELL_COUNT"
echo "Alternate GT cells:     $ALT_GT_CELL_COUNT"
echo "Genotype available:     $GENOTYPE_AVAILABLE"
echo "Inheritance evaluated:  $INHERITANCE_EVALUATED"

# --------------------------------------------------
# Apply chromosome-name conversion
# --------------------------------------------------

echo
echo "[5/10] Standardizing chromosome names"

RENAMED_BCF_REL="$WORK_DIR_REL/renamed_chromosomes.bcf"

if [[ -s "$RENAME_MAP" ]]; then
    RENAME_MAP_REL="${RENAME_MAP#"$PROJECT_ROOT/"}"

    "${CORE[@]}" bcftools annotate \
        --rename-chrs "/project/$RENAME_MAP_REL" \
        --output-type b \
        --output "/project/$RENAMED_BCF_REL" \
        "/project/$SELECTED_BCF_REL"
else
    "${CORE[@]}" bcftools view \
        --output-type b \
        --output "/project/$RENAMED_BCF_REL" \
        "/project/$SELECTED_BCF_REL"
fi

# --------------------------------------------------
# Sort, split and normalize
# --------------------------------------------------

echo
echo "[6/10] Sorting and normalizing variants"

SORTED_BCF_REL="$WORK_DIR_REL/sorted.bcf"

NORMALIZED_VCF_REL="$WORK_DIR_REL/normalized.vcf.gz"

FILTERED_VCF_REL="$WORK_DIR_REL/nonreference.vcf.gz"

REFERENCE_REL="${REFERENCE#"$PROJECT_ROOT/"}"

"${CORE[@]}" bcftools sort \
    --output-type b \
    --output "/project/$SORTED_BCF_REL" \
    "/project/$RENAMED_BCF_REL"

"${CORE[@]}" bcftools norm \
    --fasta-ref "/project/$REFERENCE_REL" \
    --multiallelics -any \
    --check-ref w \
    --output-type z \
    --output "/project/$NORMALIZED_VCF_REL" \
    "/project/$SORTED_BCF_REL" \
    2> "$NORMALIZATION_LOG"

NORMALIZED_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$NORMALIZED_VCF_REL" |
    wc -l
)"

echo "Normalized records: $NORMALIZED_COUNT"

if [[ "$ANALYSIS_MODE" == "genotype_aware" ]]; then
    RETENTION_POLICY="retain_nonreference_genotype_records"

    "${CORE[@]}" bcftools view \
        --include 'GT="alt"' \
        --output-type z \
        --output "/project/$FILTERED_VCF_REL" \
        "/project/$NORMALIZED_VCF_REL"

else
    RETENTION_POLICY="retain_all_normalized_listed_variants"

    "${CORE[@]}" bcftools view \
        --output-type z \
        --output "/project/$FILTERED_VCF_REL" \
        "/project/$NORMALIZED_VCF_REL"
fi

FILTERED_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$FILTERED_VCF_REL" |
    wc -l
)"

[[ "$FILTERED_COUNT" -gt 0 ]] \
    || die "No variants remained after preparation."

REMOVED_REFERENCE_OR_NOCALL="$(
    awk -v before="$NORMALIZED_COUNT" -v after="$FILTERED_COUNT" \
        'BEGIN {print before-after}'
)"

echo "Retention policy:          $RETENTION_POLICY"
echo "Prepared records retained: $FILTERED_COUNT"
echo "Records removed by mode:   $REMOVED_REFERENCE_OR_NOCALL"

# --------------------------------------------------
# Sanitize metadata and rename the sample
# --------------------------------------------------

echo
echo "[7/10] Removing obvious identifying metadata"

RAW_HEADER="$WORK_DIR/raw_header.txt"
SANITIZED_HEADER="$WORK_DIR/sanitized_header.txt"
REMOVED_HEADER_COUNT_FILE="$WORK_DIR/removed_header_count.txt"

"${CORE[@]}" bcftools view -h \
    "/project/$FILTERED_VCF_REL" \
    > "$RAW_HEADER"

python3 - \
    "$RAW_HEADER" \
    "$SANITIZED_HEADER" \
    "$REMOVED_HEADER_COUNT_FILE" \
    "$CASE_ID" \
    "$ANALYSIS_MODE" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1])
destination = Path(sys.argv[2])
count_file = Path(sys.argv[3])
case_id = sys.argv[4]
analysis_mode = sys.argv[5]

remove_patterns = [
    re.compile(
        r"^##(?:SAMPLE|PEDIGREE|Individual|Patient)=",
        re.IGNORECASE,
    ),
    re.compile(
        r"^##(?:bcftools_|GATKCommandLine)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:MRN|medical.record|patient.id|subject.id)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:DOB|date.of.birth|birth.date)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    ),
]

output_lines = []
removed = 0
reference_added = False

for line in source.read_text(
    encoding="utf-8"
).splitlines():
    if line.startswith("##reference="):
        if not reference_added:
            output_lines.append("##reference=GRCh38")
            reference_added = True
        continue

    if any(pattern.search(line) for pattern in remove_patterns):
        removed += 1
        continue

    if line.startswith("#CHROM"):
        fields = line.split("\t")

        if analysis_mode == "site_annotation":
            if len(fields) != 8:
                raise SystemExit(
                    "ERROR: Site-only VCF must contain exactly "
                    "the eight fixed VCF columns."
                )
        else:
            if len(fields) < 10:
                raise SystemExit(
                    "ERROR: Patient-mode VCF has no sample column."
                )

            fields = fields[:9] + [case_id]
            line = "\t".join(fields)

    output_lines.append(line)

if not reference_added:
    insertion_index = 1 if output_lines else 0
    output_lines.insert(
        insertion_index,
        "##reference=GRCh38",
    )

destination.write_text(
    "\n".join(output_lines) + "\n",
    encoding="utf-8",
)

count_file.write_text(
    f"{removed}\n",
    encoding="utf-8",
)
PY

SANITIZED_HEADER_REL="${SANITIZED_HEADER#"$PROJECT_ROOT/"}"
READY_VCF_REL="${READY_VCF#"$PROJECT_ROOT/"}"

"${CORE[@]}" bcftools reheader \
    --header "/project/$SANITIZED_HEADER_REL" \
    --output "/project/$READY_VCF_REL" \
    "/project/$FILTERED_VCF_REL"

"${CORE[@]}" bcftools index \
    --force \
    --tbi \
    "/project/$READY_VCF_REL"

PRIVACY_HEADERS_REMOVED="$(
    cat "$REMOVED_HEADER_COUNT_FILE"
)"

# --------------------------------------------------
# Prepare the phenotype file
# --------------------------------------------------

echo
echo "[8/10] Cleaning and deduplicating HPO terms"

python3 - \
    "$PHENOTYPE_SOURCE" \
    "$READY_HPO" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1])
destination = Path(sys.argv[2])

pattern = re.compile(r"\bHP:\d{7}\b", re.IGNORECASE)

terms = set()

for line in source.read_text(
    encoding="utf-8"
).splitlines():
    terms.update(
        term.upper()
        for term in pattern.findall(line)
    )

if not terms:
    raise SystemExit(
        "ERROR: No valid HP:####### terms were found."
    )

destination.write_text(
    "# Prepared unique patient HPO terms\n"
    + "\n".join(sorted(terms))
    + "\n",
    encoding="utf-8",
)

print(f"Prepared HPO terms: {len(terms)}")
PY

HPO_COUNT="$(
    grep -Ec '^HP:[0-9]{7}$' "$READY_HPO"
)"

# --------------------------------------------------
# Validate prepared output
# --------------------------------------------------

echo
echo "[9/10] Validating prepared VCF"

"${CORE[@]}" bcftools view -h \
    "/project/$READY_VCF_REL" \
    >/dev/null

READY_COUNT="$(
    "${CORE[@]}" bcftools view -H \
        "/project/$READY_VCF_REL" |
    wc -l
)"

READY_SAMPLE="$(
    "${CORE[@]}" bcftools query -l \
        "/project/$READY_VCF_REL" |
    paste -sd ',' -
)"

if [[ "$ANALYSIS_MODE" == "site_annotation" ]]; then
    [[ -z "$READY_SAMPLE" ]] \
        || die "Site-annotation output unexpectedly contains a sample."

    READY_SAMPLE_REPORT="none"
else
    [[ "$READY_SAMPLE" == "$CASE_ID" ]] \
        || die "Prepared sample name was not changed to the case ID."

    READY_SAMPLE_REPORT="$READY_SAMPLE"
fi

[[ -s "${READY_VCF}.tbi" ]] \
    || die "Prepared VCF index was not created."

echo "Prepared VCF records: $READY_COUNT"
echo "Prepared sample ID:    $READY_SAMPLE_REPORT"
echo "Prepared HPO terms:    $HPO_COUNT"
echo "Analysis mode:         $ANALYSIS_MODE"

# --------------------------------------------------
# Run the independent readiness checker
# --------------------------------------------------

echo
echo "[10/10] Running the readiness checker again"

python3 \
    "$READINESS_SCRIPT" \
    "$CASE_ID" \
    "$READY_VCF" \
    "$READY_HPO"

READINESS_REPORT="$FINAL_DIR/${CASE_ID}.real_patient_readiness.tsv"

[[ -s "$READINESS_REPORT" ]] \
    || die "Readiness report was not created."

READINESS_STATUS="$(
    awk -F $'\t' '
        $1 == "readiness_status" {
            gsub(/\r/, "", $2)
            print $2
        }
    ' "$READINESS_REPORT"
)"

cp -f "$READINESS_REPORT" "$COPIED_READINESS_REPORT"

# --------------------------------------------------
# Preparation report
# --------------------------------------------------

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "preparation_status\tcompleted\n"
    printf "readiness_status\t%s\n" "$READINESS_STATUS"
    printf "analysis_mode\t%s\n" "$ANALYSIS_MODE"
    printf "genotype_available\t%s\n" "$GENOTYPE_AVAILABLE"
    printf "inheritance_evaluated\t%s\n" "$INHERITANCE_EVALUATED"
    printf "patient_variant_interpretation_allowed\t%s\n" "$PATIENT_VARIANT_INTERPRETATION"
    printf "confidence_level\t%s\n" "$CONFIDENCE_LEVEL"
    printf "retention_policy\t%s\n" "$RETENTION_POLICY"
    printf "assembly\tGRCh38\n"
    printf "assembly_confirmation\t%s\n" "$ASSEMBLY_CONFIRMATION"
    printf "source_vcf_sha256\t%s\n" "$SOURCE_SHA256"
    printf "source_vcf_size_bytes\t%s\n" "$SOURCE_SIZE"
    printf "source_sample_count\t%s\n" "$SAMPLE_COUNT"
    printf "selected_sample_sha256\t%s\n" "$SELECTED_SAMPLE_HASH"
    printf "prepared_sample_name\t%s\n" "$CASE_ID"
    printf "source_records\t%s\n" "$SOURCE_COUNT"
    printf "normalized_records\t%s\n" "$NORMALIZED_COUNT"
    printf "prepared_records\t%s\n" "$READY_COUNT"
    printf "prepared_nonreference_records\t%s\n" "$READY_COUNT"
    printf "reference_or_nocall_records_removed\t%s\n" "$REMOVED_REFERENCE_OR_NOCALL"
    printf "chromosome_names_renamed\t%s\n" "$CHROMOSOME_RENAME_COUNT"
    printf "privacy_header_lines_removed\t%s\n" "$PRIVACY_HEADERS_REMOVED"
    printf "prepared_HPO_terms\t%s\n" "$HPO_COUNT"
    printf "prepared_vcf\t%s\n" "${READY_VCF#"$PROJECT_ROOT/"}"
    printf "prepared_vcf_index\t%s\n" "${READY_VCF#"$PROJECT_ROOT/"}.tbi"
    printf "prepared_phenotypes\t%s\n" "${READY_HPO#"$PROJECT_ROOT/"}"
    printf "readiness_report\t%s\n" "${COPIED_READINESS_REPORT#"$PROJECT_ROOT/"}"
    printf "preparation_log\t%s\n" "${PIPELINE_LOG#"$PROJECT_ROOT/"}"
    printf "normalization_log\t%s\n" "${NORMALIZATION_LOG#"$PROJECT_ROOT/"}"
    printf "liftover_performed\tno\n"
    printf "missing_genotypes_invented\tno\n"
    printf "manual_privacy_review_required\tyes\n"
} > "$PREPARATION_REPORT"

# Remove temporary copies and intermediate variant files.
rm -rf "$WORK_DIR"

echo
echo "========================================"
echo "PATIENT INPUT PREPARATION COMPLETED"
echo "========================================"
echo "Readiness status: $READINESS_STATUS"
echo "Analysis mode:    $ANALYSIS_MODE"
echo "Retention policy: $RETENTION_POLICY"
echo
echo "Prepared VCF:"
echo "$READY_VCF"
echo
echo "Prepared phenotype file:"
echo "$READY_HPO"
echo
echo "Preparation report:"
echo "$PREPARATION_REPORT"
echo
echo "Important:"
echo "The script removes common obvious identifiers, but a manual"
echo "privacy review is still required before sharing patient data."

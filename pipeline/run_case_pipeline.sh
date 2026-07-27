#!/usr/bin/env bash
# UNIVERSAL_RESOURCE_MODE_V1: production default; validation requires explicit mode

set -Eeuo pipefail

usage() {
    cat <<'USAGE'
Usage:
  bash pipeline/run_case_pipeline.sh \
    CASE_ID \
    INPUT_VCF \
    PHENOTYPE_FILE \
    [--mode production|validation] [--force]

Example:
  THREADS=4 JAVA_MEM=8g \
  bash pipeline/run_case_pipeline.sh \
    case_auto001 \
    input/cases/case001/case001.raw.vcf \
    input/cases/case001/phenotypes.txt \
    --force

Arguments:
  CASE_ID          Unique case identifier
  INPUT_VCF        GRCh38 VCF or VCF.GZ file
  PHENOTYPE_FILE   Text file containing HP:####### terms
  --mode MODE      Resource mode: production (default) or validation
  --force          Remove existing results for the case and rerun
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

PIPELINE_MODE="${PIPELINE_MODE:-production}"
FORCE=0

THREADS="${THREADS:-4}"
JAVA_MEM="${JAVA_MEM:-8g}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            [[ $# -ge 2 ]]                 || die "--mode requires production or validation."

            PIPELINE_MODE="$2"
            shift 2
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

case "$PIPELINE_MODE" in
    production|validation)
        ;;

    *)
        die "Invalid mode: $PIPELINE_MODE. Use production or validation."
        ;;
esac

export PIPELINE_MODE

if [[ ! "$CASE_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
    die "CASE_ID may contain only letters, numbers, dots, underscores and hyphens."
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

if [[ ! -f "$INPUT_VCF_ARGUMENT" ]]; then
    die "Input VCF was not found: $INPUT_VCF_ARGUMENT"
fi

if [[ ! -f "$PHENOTYPE_ARGUMENT" ]]; then
    die "Phenotype file was not found: $PHENOTYPE_ARGUMENT"
fi

INPUT_VCF_SOURCE="$(readlink -f "$INPUT_VCF_ARGUMENT")"
PHENOTYPE_SOURCE="$(readlink -f "$PHENOTYPE_ARGUMENT")"

CASE_INPUT_DIR="$PROJECT_ROOT/input/cases/$CASE_ID"
CASE_RESULT_DIR="$PROJECT_ROOT/results/cases/$CASE_ID"
STAGING_DIR="$CASE_INPUT_DIR/staged"

mkdir -p "$CASE_INPUT_DIR" "$STAGING_DIR"

case "$INPUT_VCF_SOURCE" in
    *.vcf.gz)
        STAGED_VCF="$STAGING_DIR/${CASE_ID}.pipeline_input.vcf.gz"
        ;;
    *.vcf)
        STAGED_VCF="$STAGING_DIR/${CASE_ID}.pipeline_input.vcf"
        ;;
    *)
        die "Input must end in .vcf or .vcf.gz"
        ;;
esac

STAGED_PHENOTYPES="$STAGING_DIR/${CASE_ID}.pipeline_phenotypes.txt"

copy_if_different() {
    local source_file="$1"
    local destination_file="$2"

    local source_resolved
    local destination_resolved
    local temporary_file

    source_resolved="$(readlink -f "$source_file")"
    destination_resolved="$(readlink -m "$destination_file")"

    if [[ "$source_resolved" == "$destination_resolved" ]]; then
        return 0
    fi

    temporary_file="${destination_file}.tmp.$$"

    cp -f -- "$source_file" "$temporary_file"
    mv -f -- "$temporary_file" "$destination_file"
}

copy_if_different "$INPUT_VCF_SOURCE" "$STAGED_VCF"
copy_if_different "$PHENOTYPE_SOURCE" "$STAGED_PHENOTYPES"

if [[ -d "$CASE_RESULT_DIR" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
        rm -rf "$CASE_RESULT_DIR"
    else
        die "Results already exist for $CASE_ID. Use --force to rerun."
    fi
fi

mkdir -p \
    "$CASE_RESULT_DIR/work" \
    "$CASE_RESULT_DIR/annotated" \
    "$CASE_RESULT_DIR/clinpgx" \
    "$CASE_RESULT_DIR/cnv" \
    "$CASE_RESULT_DIR/logs" \
    "$CASE_RESULT_DIR/final"

PIPELINE_LOG="$CASE_RESULT_DIR/logs/${CASE_ID}.case_pipeline.log"
SUMMARY_FILE="$CASE_RESULT_DIR/final/${CASE_ID}.pipeline_summary.tsv"
RESOURCE_MODE_FILE="$CASE_RESULT_DIR/final/${CASE_ID}.resource_mode.tsv"

exec > >(tee "$PIPELINE_LOG") 2>&1

trap '
    status=$?
    echo
    echo "CASE PIPELINE FAILED"
    echo "Line: $LINENO"
    echo "Exit status: $status"
    echo "Log: '"$PIPELINE_LOG"'"
    exit $status
' ERR

echo "========================================"
echo "UNIVERSAL GENETIC CASE PIPELINE"
echo "========================================"
echo "Case ID:        $CASE_ID"
echo "Input VCF:      $STAGED_VCF"
echo "Phenotypes:     $STAGED_PHENOTYPES"
echo "Threads:        $THREADS"
echo "Java memory:    $JAVA_MEM"
echo "Resource mode:  $PIPELINE_MODE"
echo "Assembly:       GRCh38"
echo

# --------------------------------------------------
# Validate required scripts
# --------------------------------------------------

REQUIRED_SCRIPTS=(
    pipeline/case_workflow/00_detect_and_split_variants.py
    pipeline/case_workflow/inheritance_utils.py
    pipeline/case_workflow/00b_refresh_combined_g2p.py
    pipeline/case_workflow/01_normalize_routed_small_variants.sh
    pipeline/case_workflow/02_annotate_vep.sh
    pipeline/case_workflow/03_extract_vep_table.py
    pipeline/case_workflow/04_map_genes_to_diseases.py
    pipeline/case_workflow/05_add_clinpgx_matches.py
    pipeline/case_workflow/05b_add_local_pgx_reference.py
    pipeline/case_workflow/05c_write_disabled_local_pgx.py
    pipeline/case_workflow/06_add_clinvar.sh
    pipeline/case_workflow/07_score_disease_candidates.py
    pipeline/case_workflow/03_annotate_snpeff.sh
    pipeline/case_workflow/04_add_clinvar_to_snpeff.sh
    pipeline/case_workflow/08_add_spliceai.sh
    pipeline/case_workflow/09_merge_snpeff_spliceai.py
    pipeline/case_workflow/10_add_phenotype_scores.py
    pipeline/case_workflow/10b_add_compound_heterozygous_evidence.py
    pipeline/case_workflow/11_run_cnv_tools.sh
    pipeline/case_workflow/12_score_cnv_candidates.py
    pipeline/case_workflow/13_add_clingen_small_variants.sh
    pipeline/case_workflow/14_build_master_candidate_table.py
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ ! -s "$PROJECT_ROOT/$script" ]]; then
        die "Required workflow script is missing: $script"
    fi
done

if ! grep -Eq 'HP:[0-9]{7}' "$STAGED_PHENOTYPES"; then
    die "No valid HP:####### terms were found in the phenotype file."
fi

CORE_SIF="$PROJECT_ROOT/containers/core_tools.sif"

if [[ ! -s "$CORE_SIF" ]]; then
    die "Missing container: $CORE_SIF"
fi

echo "[1] Validating staged VCF"

apptainer exec \
    --bind "$PROJECT_ROOT:/project" \
    "$CORE_SIF" \
    bcftools view -h \
    "/project/${STAGED_VCF#"$PROJECT_ROOT/"}" \
    >/dev/null

echo "VCF validation passed."

# --------------------------------------------------
# Resolve G2P resource once for every active branch
# --------------------------------------------------

if [[ "$PIPELINE_MODE" == "validation" ]]; then
    echo
    echo "[RESOURCE] Build validation-only G2P resource"

    python3 \
        pipeline/case_workflow/00b_refresh_combined_g2p.py

    G2P_RESOURCE="$PROJECT_ROOT/resources/gene_disease/g2p/AllG2P.validation.csv"
    LOCAL_G2P_VALIDATION_ENABLED="yes"
else
    G2P_RESOURCE="$PROJECT_ROOT/resources/gene_disease/g2p/AllG2P.official.csv"
    LOCAL_G2P_VALIDATION_ENABLED="no"
fi

[[ -s "$G2P_RESOURCE" ]] \
    || die "Selected G2P resource is missing or empty: $G2P_RESOURCE"

G2P_RESOURCE_RELATIVE="${G2P_RESOURCE#"$PROJECT_ROOT/"}"

{
    printf "metric\tvalue\n"
    printf "pipeline_mode\t%s\n" "$PIPELINE_MODE"
    printf "g2p_resource\t%s\n" "$G2P_RESOURCE_RELATIVE"
    printf "official_g2p_only\t%s\n" \
        "$([[ "$PIPELINE_MODE" == "production" ]] && echo yes || echo no)"
    printf "local_g2p_validation_enabled\t%s\n" \
        "$LOCAL_G2P_VALIDATION_ENABLED"
    printf "local_pgx_validation_enabled\t%s\n" \
        "$([[ "$PIPELINE_MODE" == "validation" ]] && echo yes || echo no)"
} > "$RESOURCE_MODE_FILE"

echo "Selected G2P resource: $G2P_RESOURCE_RELATIVE"

# --------------------------------------------------
# Automatic routing
# --------------------------------------------------

echo
echo "[2] Detecting and separating variant classes"

python3 \
    pipeline/case_workflow/00_detect_and_split_variants.py \
    "$CASE_ID" \
    "$STAGED_VCF"

ROUTING_QC="$CASE_RESULT_DIR/final/${CASE_ID}.variant_routing_qc.tsv"

read_qc_value() {
    local key="$1"

    awk -F $'\t' -v requested_key="$key" '
        $1 == requested_key {
            gsub(/\r/, "", $2)
            print $2
        }
    ' "$ROUTING_QC"
}

SMALL_BRANCH="$(read_qc_value small_variant_branch_required)"
CNV_BRANCH="$(read_qc_value cnv_branch_required)"
SMALL_COUNT="$(read_qc_value small_variant_records)"
CNV_COUNT="$(read_qc_value supported_DEL_DUP_records)"
OTHER_SV_COUNT="$(read_qc_value other_structural_variant_records)"

echo
echo "Routing decision"
echo "----------------"
echo "Small variants:        ${SMALL_COUNT:-0}"
echo "DEL/DUP CNVs:          ${CNV_COUNT:-0}"
echo "Other SVs:             ${OTHER_SV_COUNT:-0}"
echo "Small-variant branch:  ${SMALL_BRANCH:-no}"
echo "CNV branch:            ${CNV_BRANCH:-no}"

UNSUPPORTED_ONLY=0

if [[ "$SMALL_BRANCH" != "yes" && "$CNV_BRANCH" != "yes" ]]; then
    if [[ "${OTHER_SV_COUNT:-0}" =~ ^[0-9]+$ ]] \
        && (( OTHER_SV_COUNT > 0 ))
    then
        UNSUPPORTED_ONLY=1

        echo
        echo "No currently supported small variants or DEL/DUP CNVs."
        echo "Unsupported structural records were detected and preserved."
        echo "Returning to the universal reporting layer."
    else
        die "No supported or reportable variant records were detected."
    fi
fi

SMALL_STATUS="not_required"
CNV_STATUS="not_required"
CLINPGX_STATUS="not_required"

if [[ "$UNSUPPORTED_ONLY" -eq 1 ]]; then
    echo
    echo "========================================"
    echo "CORE PIPELINE ROUTING COMPLETE"
    echo "========================================"
    echo "Case ID:              $CASE_ID"
    echo "Small variants:       ${SMALL_COUNT:-0}"
    echo "DEL/DUP CNVs:         ${CNV_COUNT:-0}"
    echo "Unsupported records:  ${OTHER_SV_COUNT:-0}"
    echo
    echo "Interpretation branches were not run."
    echo "Unsupported records remain available for dedicated reporting."

    exit 0
fi

# --------------------------------------------------
# Small-variant branch
# --------------------------------------------------

if [[ "$SMALL_BRANCH" == "yes" ]]; then
    SMALL_STATUS="running"

    echo
    echo "========================================"
    echo "SMALL-VARIANT BRANCH"
    echo "========================================"

    echo
    echo "[3A.1] Normalization"

    bash \
        pipeline/case_workflow/01_normalize_routed_small_variants.sh \
        "$CASE_ID"

    echo
    echo "[3A.2] VEP annotation"

    THREADS="$THREADS" \
    bash \
        pipeline/case_workflow/02_annotate_vep.sh \
        "$CASE_ID"

    echo
    echo "[3A.3] Extracting preferred VEP transcripts"

    python3 \
        pipeline/case_workflow/03_extract_vep_table.py \
        "$CASE_ID"

    echo
    echo "[3A.4] G2P gene-to-disease mapping"

    python3 \
        pipeline/case_workflow/04_map_genes_to_diseases.py \
        "$CASE_ID" \
        "$G2P_RESOURCE"

    echo
    echo "[3A.5] ClinPGx contextual matching"

    CLINPGX_STATUS="completed"

    if ! python3 \
        pipeline/case_workflow/05_add_clinpgx_matches.py \
        "$CASE_ID"
    then
        CLINPGX_STATUS="warning_api_or_matching_failure"

        echo
        echo "WARNING: ClinPGx matching failed."
        echo "Disease prioritization will continue because ClinPGx"
        echo "is contextual and does not determine disease causality."
    fi

    echo
    echo "[3A.5b] Local PGx validation layer"

    if [[ "$PIPELINE_MODE" == "validation" ]]; then
        LOCAL_PGX_VALIDATION_STATUS="completed"

        if ! python3 \
            pipeline/case_workflow/05b_add_local_pgx_reference.py \
            "$CASE_ID"
        then
            LOCAL_PGX_VALIDATION_STATUS="warning_validation_failure"

            echo
            echo "WARNING: Local PGx validation did not complete cleanly."
            echo "Official ClinPGx processing remains separate."
        fi
    else
        LOCAL_PGX_VALIDATION_STATUS="disabled_by_production_mode"

        python3 \
            pipeline/case_workflow/05c_write_disabled_local_pgx.py \
            "$CASE_ID"
    fi

    printf "local_pgx_validation_status\t%s\n" \
        "$LOCAL_PGX_VALIDATION_STATUS" \
        >> "$RESOURCE_MODE_FILE"

    echo
    echo "[3A.6] ClinVar evidence for disease scoring"

    bash \
        pipeline/case_workflow/06_add_clinvar.sh \
        "$CASE_ID"

    echo
    echo "[3A.7] Initial transparent disease score"

    python3 \
        pipeline/case_workflow/07_score_disease_candidates.py \
        "$CASE_ID"

    echo
    echo "[3A.8] SnpEff annotation"

    JAVA_MEM="$JAVA_MEM" \
    bash \
        pipeline/case_workflow/03_annotate_snpeff.sh \
        "$CASE_ID"

    echo
    echo "[3A.9] Cumulative ClinVar annotation"

    bash \
        pipeline/case_workflow/04_add_clinvar_to_snpeff.sh \
        "$CASE_ID"

    echo
    echo "[3A.10] SpliceAI annotation"

    bash \
        pipeline/case_workflow/08_add_spliceai.sh \
        "$CASE_ID"

    echo
    echo "[3A.11] Merging SnpEff and SpliceAI evidence"

    python3 \
        pipeline/case_workflow/09_merge_snpeff_spliceai.py \
        "$CASE_ID"

    echo
    echo "[3A.12] Phenotype-aware ranking"

    python3 \
        pipeline/case_workflow/10_add_phenotype_scores.py \
        "$CASE_ID" \
        "$STAGED_PHENOTYPES" \
        "$G2P_RESOURCE"

    echo
    echo "[3A.12b] Gene-level recessive and compound-heterozygous evidence"

    python3 \
        pipeline/case_workflow/10b_add_compound_heterozygous_evidence.py \
        "$CASE_ID"

    echo
    echo "[3A.13] ClinGen dosage context"

    bash \
        pipeline/case_workflow/13_add_clingen_small_variants.sh \
        "$CASE_ID"

    # The former ClinVar score-floor calibration was removed.
    # Universal evidence ranking is applied after all annotations.
    SMALL_STATUS="completed"
else
    echo
    echo "Small-variant branch skipped: no small variants detected."
fi

# --------------------------------------------------
# CNV branch
# --------------------------------------------------

if [[ "$CNV_BRANCH" == "yes" ]]; then
    CNV_STATUS="running"

    echo
    echo "========================================"
    echo "CNV BRANCH"
    echo "========================================"

    echo
    echo "[3B.1] AnnotSV, ClassifyCNV and ISV-CNV"

    THREADS="$THREADS" \
    bash \
        pipeline/case_workflow/11_run_cnv_tools.sh \
        "$CASE_ID"

    echo
    echo "[3B.2] CNV gene-disease and phenotype scoring"

    python3 \
        pipeline/case_workflow/12_score_cnv_candidates.py \
        "$CASE_ID" \
        "$G2P_RESOURCE"

    CNV_STATUS="completed"
else
    echo
    echo "CNV branch skipped: no DEL/DUP records detected."
fi

# --------------------------------------------------
# Master ranking
# --------------------------------------------------

echo
echo "========================================"
echo "MASTER RESULT"
echo "========================================"

echo
echo "[4] Building combined candidate table"

python3 \
    pipeline/case_workflow/14_build_master_candidate_table.py \
    "$CASE_ID"

MASTER_TABLE="$CASE_RESULT_DIR/final/${CASE_ID}.master_candidate_ranking.tsv"

if [[ ! -s "$MASTER_TABLE" ]]; then
    die "Master candidate table was not created."
fi

TOP_RESULT="$(
    python3 - "$MASTER_TABLE" <<'PY'
import csv
import sys
from pathlib import Path

path = Path(sys.argv[1])

with path.open(encoding="utf-8", newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")
    row = next(reader, {})

values = [
    row.get("candidate_type", ""),
    row.get("gene", ""),
    row.get("candidate_disease", ""),
    row.get("variant", ""),
    row.get("normalized_score_100", ""),
    row.get("priority", ""),
]

print("\t".join(values))
PY
)"

IFS=$'\t' read -r \
    TOP_TYPE \
    TOP_GENE \
    TOP_DISEASE \
    TOP_VARIANT \
    TOP_SCORE \
    TOP_PRIORITY \
    <<< "$TOP_RESULT"

INPUT_SHA256="$(sha256sum "$STAGED_VCF" | awk '{print $1}')"
PHENOTYPE_SHA256="$(sha256sum "$STAGED_PHENOTYPES" | awk '{print $1}')"

{
    printf "field\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "assembly\tGRCh38\n"
    printf "input_vcf\t%s\n" "${STAGED_VCF#"$PROJECT_ROOT/"}"
    printf "input_vcf_sha256\t%s\n" "$INPUT_SHA256"
    printf "phenotype_file\t%s\n" "${STAGED_PHENOTYPES#"$PROJECT_ROOT/"}"
    printf "phenotype_sha256\t%s\n" "$PHENOTYPE_SHA256"
    printf "small_variant_records\t%s\n" "${SMALL_COUNT:-0}"
    printf "cnv_records\t%s\n" "${CNV_COUNT:-0}"
    printf "other_structural_variants\t%s\n" "${OTHER_SV_COUNT:-0}"
    printf "small_variant_branch_status\t%s\n" "$SMALL_STATUS"
    printf "cnv_branch_status\t%s\n" "$CNV_STATUS"
    printf "clinpgx_status\t%s\n" "$CLINPGX_STATUS"
    printf "top_candidate_type\t%s\n" "$TOP_TYPE"
    printf "top_gene\t%s\n" "$TOP_GENE"
    printf "top_disease\t%s\n" "$TOP_DISEASE"
    printf "top_variant\t%s\n" "$TOP_VARIANT"
    printf "top_normalized_score\t%s\n" "$TOP_SCORE"
    printf "top_priority\t%s\n" "$TOP_PRIORITY"
    printf "master_table\t%s\n" "${MASTER_TABLE#"$PROJECT_ROOT/"}"
    printf "pipeline_log\t%s\n" "${PIPELINE_LOG#"$PROJECT_ROOT/"}"
} > "$SUMMARY_FILE"

echo
echo "========================================"
echo "CASE PIPELINE COMPLETED SUCCESSFULLY"
echo "========================================"
echo "Case ID:              $CASE_ID"
echo "Top candidate type:   $TOP_TYPE"
echo "Top gene:             $TOP_GENE"
echo "Top disease:          $TOP_DISEASE"
echo "Top variant:          $TOP_VARIANT"
echo "Normalized score:     $TOP_SCORE"
echo "Priority:             $TOP_PRIORITY"
echo
echo "Master ranking:"
echo "$MASTER_TABLE"
echo
echo "Pipeline summary:"
echo "$SUMMARY_FILE"
echo
echo "Pipeline log:"
echo "$PIPELINE_LOG"

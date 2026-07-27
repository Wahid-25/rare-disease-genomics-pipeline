#!/usr/bin/env bash
set -Eeuo pipefail

die() {
    echo "ERROR: $*" >&2
    exit 1
}

if [[ $# -lt 4 || $# -gt 5 ]]; then
    cat <<'EOF'
Usage:
  bash pipeline/run_universal_case.sh \
    CASE_ID INPUT_VCF PHENOTYPE_FILE_OR_- CONTEXT_FILE_OR_- [--force]
EOF
    exit 1
fi

CASE_ID="$1"
INPUT_VCF="$2"
PHENOTYPE="$3"
CONTEXT="$4"
OPTION="${5:-}"

[[ "$CASE_ID" =~ ^[A-Za-z0-9._-]+$ ]] \
    || die "Invalid case ID"

[[ -f "$INPUT_VCF" ]] \
    || die "Input VCF missing: $INPUT_VCF"

[[ "$PHENOTYPE" == "-" || -f "$PHENOTYPE" ]] \
    || die "Phenotype file missing: $PHENOTYPE"

[[ "$CONTEXT" == "-" || -f "$CONTEXT" ]] \
    || die "Context file missing: $CONTEXT"

[[ "$OPTION" == "" || "$OPTION" == "--force" ]] \
    || die "Unknown option: $OPTION"

if [[ "$PHENOTYPE" == "-" && "$CONTEXT" == "-" ]]; then
    die "Provide a phenotype file or context file"
fi

ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

cd "$ROOT"

export THREADS="${THREADS:-1}"
export JAVA_MEM="${JAVA_MEM:-768m}"
export CLINPGX_MODE="${CLINPGX_MODE:-cache_only}"
export PYTHONUNBUFFERED=1

PREPARED_DIR="$ROOT/input/cases/$CASE_ID/prepared"
PREPARED_VCF="$PREPARED_DIR/$CASE_ID.chr.vcf"
CHR_MAP="$ROOT/resources/reference/grch38_chr_rename.tsv"

mkdir -p "$PREPARED_DIR"

if [[ ! -s "$CHR_MAP" ]]; then
    {
        for chromosome in $(seq 1 22); do
            printf "%s\tchr%s\n" \
                "$chromosome" \
                "$chromosome"
        done

        printf "X\tchrX\n"
        printf "Y\tchrY\n"
        printf "M\tchrM\n"
        printf "MT\tchrM\n"
    } > "$CHR_MAP"
fi

echo "============================================================"
echo "UNIVERSAL CASE PIPELINE"
echo "============================================================"
echo "Case:        $CASE_ID"
echo "Input VCF:   $INPUT_VCF"
echo "Phenotypes:  $PHENOTYPE"
echo "Context:     $CONTEXT"
echo

echo "[1/4] Preparing chromosome names"

apptainer exec containers/core_tools.sif \
    bcftools annotate \
    --rename-chrs "$CHR_MAP" \
    -Ov \
    -o "$PREPARED_VCF" \
    "$INPUT_VCF"

if [[ "$PHENOTYPE" == "-" ]]; then
    ANNOTATION_HPO="$PREPARED_DIR/technical_placeholder.hpo.txt"

    cat > "$ANNOTATION_HPO" <<'EOF'
# Internal placeholder required by the legacy annotation stage.
# It is never used for final context-aware phenotype scoring.
HP:0000001
EOF

    RANKING_HPO="-"
else
    ANNOTATION_HPO="$(readlink -f "$PHENOTYPE")"
    RANKING_HPO="$ANNOTATION_HPO"
fi

if [[ "$CONTEXT" == "-" ]]; then
    RANKING_CONTEXT="-"
else
    RANKING_CONTEXT="$(readlink -f "$CONTEXT")"
fi

# SAFE REUSE MANIFEST
FINAL_DIR="$ROOT/results/cases/$CASE_ID/final"
mkdir -p "$FINAL_DIR"

CURRENT_MANIFEST="$PREPARED_DIR/"
CURRENT_MANIFEST+="${CASE_ID}.reproducibility_manifest.current.tsv"

SAVED_MANIFEST="$FINAL_DIR/"
SAVED_MANIFEST+="${CASE_ID}.reproducibility_manifest.tsv"

python3 \
    "$ROOT/pipeline/case_workflow/00c_build_reproducibility_manifest.py" \
    "$CASE_ID" \
    "$INPUT_VCF" \
    "$PHENOTYPE" \
    "$CONTEXT" \
    "$PREPARED_VCF" \
    "$CURRENT_MANIFEST"

echo "[2/4] Running variant annotation"

ANNOTATION_TABLE="$FINAL_DIR/"
ANNOTATION_TABLE+="$CASE_ID.variant_gene_disease.tsv"

REUSE_ANNOTATION=0
REUSE_REASON=""

if [[ "$OPTION" == "--force" ]]; then
    REUSE_REASON="forced_rebuild"
elif [[ ! -s "$ANNOTATION_TABLE" ]]; then
    REUSE_REASON="annotation_missing"
elif [[ ! -s "$SAVED_MANIFEST" ]]; then
    REUSE_REASON="saved_manifest_missing"
elif cmp -s "$CURRENT_MANIFEST" "$SAVED_MANIFEST"; then
    REUSE_ANNOTATION=1
    REUSE_REASON="exact_manifest_match"
else
    REUSE_REASON="input_pipeline_or_resource_change"
fi

echo "Reuse decision: $REUSE_REASON"

if [[ "$REUSE_ANNOTATION" -eq 1 ]]; then
    echo "Existing annotation is reproducibly compatible."
    echo "Reusing: $ANNOTATION_TABLE"
else
    ANNOTATION_ARGS=(
        "$CASE_ID"
        "$PREPARED_VCF"
        "$ANNOTATION_HPO"
    )

    # Existing results must be replaced whenever the manifest
    # differs or the user explicitly requests a rebuild.
    if [[ "$OPTION" == "--force" || -s "$ANNOTATION_TABLE" ]]; then
        ANNOTATION_ARGS+=("--force")
    fi

    bash pipeline/run_case_pipeline.sh \
        "${ANNOTATION_ARGS[@]}"
fi

echo "[3/6] Resolving universal case context"

python3 \
    pipeline/case_workflow/00_resolve_case_context.py \
    "$CASE_ID" \
    "$RANKING_HPO" \
    "$RANKING_CONTEXT"

SMALL_INPUT="$ROOT/results/cases/$CASE_ID/final/"
SMALL_INPUT+="$CASE_ID.variant_gene_disease.tsv"

CNV_INPUT="$ROOT/results/cases/$CASE_ID/final/"
CNV_INPUT+="$CASE_ID.cnv_gene_disease_scores.final.tsv"

SMALL_AVAILABLE=0
CNV_AVAILABLE=0

echo "[4/6] Checking small-variant branch"

if [[ -s "$SMALL_INPUT" ]]; then
    SMALL_AVAILABLE=1

    python3 \
        pipeline/case_workflow/04b_expand_hpo_disease_candidates.py \
        "$CASE_ID"

    python3 \
        pipeline/case_workflow/10a_add_semantic_phenotype_evidence.py \
        "$CASE_ID"

    python3 \
        pipeline/case_workflow/10b_resolve_disease_identities.py \
        "$CASE_ID"

    python3 \
        pipeline/case_workflow/11_score_universal_evidence.py \
        "$CASE_ID"
else
    echo "No small-variant candidate table found."
    echo "Small-variant universal scoring skipped."
fi

echo "[5/6] Checking CNV branch"

if [[ -s "$CNV_INPUT" ]]; then
    CNV_AVAILABLE=1

    python3 \
        "$ROOT/pipeline/case_workflow/10c_prepare_cnv_semantic_input.py" \
        "$CASE_ID"

    python3 \
        "$ROOT/pipeline/case_workflow/10d_add_cnv_semantic_phenotype_evidence.py" \
        "$CASE_ID"

    python3 \
        "$ROOT/pipeline/case_workflow/11b_score_universal_cnv.py" \
        "$CASE_ID"

    python3 \
        "$ROOT/pipeline/case_workflow/11c_add_cnv_clinpgx.py" \
        "$CASE_ID"
else
    echo "No supported DEL/DUP candidate table found."
    echo "Universal CNV scoring skipped."
fi

FINAL_DIR="$ROOT/results/cases/$CASE_ID/final"
WORK_DIR="$ROOT/results/cases/$CASE_ID/work"

ROUTING_MANIFEST="$FINAL_DIR/${CASE_ID}.variant_routing_manifest.tsv"
UNSUPPORTED_VCF="$WORK_DIR/${CASE_ID}.other_structural_variants.vcf"
REPEAT_REPORT="$FINAL_DIR/${CASE_ID}.repeat_expansions.detected.tsv"
STATUS_FILE="$FINAL_DIR/${CASE_ID}.case_completion_status.tsv"

mkdir -p "$FINAL_DIR"

UNSUPPORTED_COUNT=0

if [[ -s "$ROUTING_MANIFEST" ]]; then
    UNSUPPORTED_COUNT="$(
        grep -c $'\tother_or_unsupported_report\t' \
            "$ROUTING_MANIFEST" \
        || true
    )"

    UNSUPPORTED_COUNT="${UNSUPPORTED_COUNT:-0}"

    if grep -q $'\trepeat_expansion\t' \
        "$ROUTING_MANIFEST"
    then
        echo "Creating repeat-expansion report."

        python3 \
            "$ROOT/pipeline/case_workflow/00b_report_repeat_expansions.py" \
            "$CASE_ID"
    fi
fi

if [[ "$SMALL_AVAILABLE" -eq 0 && "$CNV_AVAILABLE" -eq 0 ]]; then
    if [[ "$UNSUPPORTED_COUNT" -gt 0 ]]; then
        cp -f "$CURRENT_MANIFEST" "$SAVED_MANIFEST"

        {
            printf "metric\tvalue\n"
            printf "case_id\t%s\n" "$CASE_ID"
            printf "completion_status\t%s\n" \
                "COMPLETED_WITH_UNSUPPORTED_VARIANTS"
            printf "small_variant_branch\tabsent\n"
            printf "cnv_branch\tabsent\n"
            printf "unsupported_records\t%s\n" \
                "$UNSUPPORTED_COUNT"
            printf "master_table\t%s\n" \
                "not_created_no_supported_candidates"
            printf "routing_manifest\t%s\n" \
                "$ROUTING_MANIFEST"
            printf "unsupported_vcf\t%s\n" \
                "$UNSUPPORTED_VCF"
            printf "reproducibility_manifest\t%s\n" \
                "$SAVED_MANIFEST"

            if [[ -s "$REPEAT_REPORT" ]]; then
                printf "repeat_expansion_report\t%s\n" \
                    "$REPEAT_REPORT"
            fi
        } > "$STATUS_FILE"

        echo
        echo "============================================================"
        echo "CASE COMPLETED WITH UNSUPPORTED VARIANTS"
        echo "============================================================"
        echo "Supported candidates: none"
        echo "Unsupported records:  $UNSUPPORTED_COUNT"
        echo "No misleading master ranking was created."
        echo "Completion status:"
        echo "$STATUS_FILE"

        exit 0
    fi

    die "No supported or reportable variant records were produced."
fi

echo "[6/6] Building master candidate table"

python3 \
    "$ROOT/pipeline/case_workflow/12_build_universal_master.py" \
    "$CASE_ID"

MASTER="$FINAL_DIR/${CASE_ID}.master_candidate_table.tsv"

COMPLETION_STATUS="COMPLETED"

if [[ "$UNSUPPORTED_COUNT" -gt 0 ]]; then
    COMPLETION_STATUS="COMPLETED_WITH_SUPPORTED_AND_UNSUPPORTED_VARIANTS"
fi

cp -f "$CURRENT_MANIFEST" "$SAVED_MANIFEST"

{
    printf "metric\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "completion_status\t%s\n" \
        "$COMPLETION_STATUS"
    printf "small_variant_branch\t%s\n" \
        "$SMALL_AVAILABLE"
    printf "cnv_branch\t%s\n" \
        "$CNV_AVAILABLE"
    printf "unsupported_records\t%s\n" \
        "$UNSUPPORTED_COUNT"
    printf "master_table\t%s\n" "$MASTER"
    printf "reproducibility_manifest\t%s\n" \
        "$SAVED_MANIFEST"
    printf "annotation_reuse_reason\t%s\n" \
        "$REUSE_REASON"

    if [[ -s "$REPEAT_REPORT" ]]; then
        printf "repeat_expansion_report\t%s\n" \
            "$REPEAT_REPORT"
    fi
} > "$STATUS_FILE"

echo
echo "============================================================"
echo "CASE COMPLETED"
echo "============================================================"
echo "Status: $COMPLETION_STATUS"
echo "Master table:"
echo "$MASTER"
echo "Completion status:"
echo "$STATUS_FILE"

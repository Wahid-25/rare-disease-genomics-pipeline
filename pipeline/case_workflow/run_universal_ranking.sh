#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
    cat <<'EOF'
Usage:
  run_universal_ranking.sh CASE_ID PHENOTYPE_FILE|- [CONTEXT_TSV|-]

Examples:

  Standard affected diagnostic case:
    run_universal_ranking.sh \
      patient_01_cf \
      validation/patient_vcfs/patient_01_cf.hpo.txt

  Unaffected carrier or other special context:
    run_universal_ranking.sh \
      patient_04_brca1 \
      - \
      validation/patient_vcfs/patient_04_brca1.context.tsv
EOF
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
    usage
    exit 1
fi

CASE_ID="$1"
PHENOTYPE_FILE="$2"
CONTEXT_FILE="${3:--}"

PROJECT_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." \
    && pwd
)"

WORKFLOW_DIR="$PROJECT_ROOT/pipeline/case_workflow"

FINAL_DIR="$PROJECT_ROOT/results/cases/$CASE_ID/final"

MAPPING_INPUT="$FINAL_DIR/$CASE_ID.variant_gene_disease.tsv"

if [[ ! -s "$MAPPING_INPUT" ]]; then
    echo "ERROR: Initial variant–gene–disease table missing:" >&2
    echo "  $MAPPING_INPUT" >&2
    echo >&2
    echo "Run the main annotation pipeline first." >&2
    exit 1
fi

echo "========================================================================"
echo "UNIVERSAL POST-ANNOTATION RANKING"
echo "========================================================================"
echo "Case ID:          $CASE_ID"
echo "Phenotype file:   $PHENOTYPE_FILE"
echo "Context file:     $CONTEXT_FILE"
echo

python3 \
    "$WORKFLOW_DIR/00_resolve_case_context.py" \
    "$CASE_ID" \
    "$PHENOTYPE_FILE" \
    "$CONTEXT_FILE"

echo
echo "[1/4] Expanding universal gene–disease candidates..."

python3 \
    "$WORKFLOW_DIR/04b_expand_hpo_disease_candidates.py" \
    "$CASE_ID"

echo
echo "[2/4] Calculating semantic phenotype evidence..."

python3 \
    "$WORKFLOW_DIR/10a_add_semantic_phenotype_evidence.py" \
    "$CASE_ID"

echo
echo "[3/4] Resolving equivalent disease identities..."

python3 \
    "$WORKFLOW_DIR/10b_resolve_disease_identities.py" \
    "$CASE_ID"

echo
echo "[4/4] Calculating universal evidence scores..."

python3 \
    "$WORKFLOW_DIR/11_score_universal_evidence.py" \
    "$CASE_ID"

OUTPUT="$FINAL_DIR/$CASE_ID.universal_evidence_scores.tsv"
QC="$FINAL_DIR/$CASE_ID.universal_evidence_scoring_qc.tsv"

if [[ ! -s "$OUTPUT" ]]; then
    echo "ERROR: Universal scoring output was not created." >&2
    exit 1
fi

echo
echo "========================================================================"
echo "UNIVERSAL RANKING COMPLETED"
echo "========================================================================"
echo "Candidate table: $OUTPUT"
echo "Scoring QC:      $QC"

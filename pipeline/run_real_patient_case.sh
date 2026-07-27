#!/usr/bin/env bash
# UNIVERSAL_RESOURCE_MODE_V1: production default; validation requires explicit mode

set -Eeuo pipefail

usage() {
    cat <<'USAGE'
Usage:
  bash pipeline/run_real_patient_case.sh \
    CASE_ID INPUT_VCF PHENOTYPE_FILE \
    [--sample SAMPLE_NAME] \
    [--confirm-grch38] \
    [--mode production|validation] \
    [--sex male|female|unknown] \
    [--force]

Options:
  --sample NAME
      Select the patient sample from a multisample VCF.

  --confirm-grch38
      Confirm that the VCF uses GRCh38 when its header does not
      declare the genome build.

  --mode MODE
      Resource mode: production (default) or validation.

  --sex SEX
      Optional reported sex: male, female, or unknown.
      Production defaults to unknown. Validation mode can
      resolve sex from the synthetic sample sheet.
      Use production (default) or validation resources.

  --force
      Replace existing prepared files and case results.

Environment variables:
  THREADS       Number of processing threads. Default: 4
  JAVA_MEM      Java memory for SnpEff. Default: 8g

Example:
  THREADS=4 JAVA_MEM=8g \
  bash pipeline/run_real_patient_case.sh \
    patient_case001 \
    patient.vcf.gz \
    patient_phenotypes.txt \
    --sample PATIENT_01 \
    --confirm-grch38 \
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

SELECTED_SAMPLE=""
CONFIRM_GRCH38=0
FORCE=0
PIPELINE_MODE="${PIPELINE_MODE:-production}"
REQUESTED_SEX="${PATIENT_SEX:-unknown}"

THREADS="${THREADS:-4}"
JAVA_MEM="${JAVA_MEM:-8g}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample)
            [[ $# -ge 2 ]] \
                || die "--sample requires a sample name."

            SELECTED_SAMPLE="$2"
            shift 2
            ;;

        --confirm-grch38)
            CONFIRM_GRCH38=1
            shift
            ;;

        --mode)
            [[ $# -ge 2 ]]                 || die "--mode requires production or validation."

            PIPELINE_MODE="$2"
            shift 2
            ;;

        --sex)
            [[ $# -ge 2 ]] \
                || die "--sex requires male, female, or unknown."

            REQUESTED_SEX="$2"
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

[[ -f "$INPUT_VCF_ARGUMENT" ]] \
    || die "Input VCF was not found: $INPUT_VCF_ARGUMENT"

[[ -f "$PHENOTYPE_ARGUMENT" ]] \
    || die "Phenotype file was not found: $PHENOTYPE_ARGUMENT"

INTAKE_SCRIPT="$PROJECT_ROOT/pipeline/case_workflow/18_external_case_intake.py"
SEX_RESOLVER="$PROJECT_ROOT/pipeline/case_workflow/21_resolve_case_sex.py"
SEX_PLOIDY_PREFLIGHT="$PROJECT_ROOT/pipeline/case_workflow/20_sex_ploidy_preflight.py"
PREPARATION_SCRIPT="$PROJECT_ROOT/pipeline/case_workflow/16_prepare_real_patient_inputs.sh"
CLEANUP_SCRIPT="$PROJECT_ROOT/pipeline/case_workflow/19_remove_existing_annotations.sh"
CASE_PIPELINE="$PROJECT_ROOT/pipeline/run_case_pipeline.sh"

[[ -s "$INTAKE_SCRIPT" ]] \
    || die "Universal intake script was not found: $INTAKE_SCRIPT"

[[ -s "$SEX_RESOLVER" ]] \
    || die "Sex resolver was not found: $SEX_RESOLVER"

[[ -s "$SEX_PLOIDY_PREFLIGHT" ]] \
    || die "Sex/ploidy preflight was not found: $SEX_PLOIDY_PREFLIGHT"

[[ -s "$PREPARATION_SCRIPT" ]] \
    || die "Preparation script was not found: $PREPARATION_SCRIPT"

[[ -s "$CLEANUP_SCRIPT" ]] \
    || die "Annotation cleanup script was not found: $CLEANUP_SCRIPT"

[[ -s "$CASE_PIPELINE" ]] \
    || die "Universal case pipeline was not found: $CASE_PIPELINE"

CASE_INPUT_DIR="$PROJECT_ROOT/input/cases/$CASE_ID"
PREPARED_DIR="$CASE_INPUT_DIR/prepared"

READY_VCF="$PREPARED_DIR/${CASE_ID}.ready.vcf.gz"
READY_HPO="$PREPARED_DIR/phenotypes.ready.txt"
PREPARATION_REPORT="$PREPARED_DIR/${CASE_ID}.preparation_report.tsv"
PREPARED_READINESS="$PREPARED_DIR/${CASE_ID}.readiness.tsv"

INTAKE_EVIDENCE_DIR="$CASE_INPUT_DIR/intake"
PRESERVED_INTAKE_REPORT="$INTAKE_EVIDENCE_DIR/${CASE_ID}.external_vcf_intake.tsv"

REANNOTATION_READY_VCF="$PREPARED_DIR/${CASE_ID}.reannotation_ready.vcf.gz"
ANNOTATION_CLEANUP_REPORT="$PREPARED_DIR/${CASE_ID}.annotation_cleanup_report.tsv"

WRAPPER_LOG="$PREPARED_DIR/${CASE_ID}.real_patient_launcher.log"

mkdir -p "$PREPARED_DIR" "$INTAKE_EVIDENCE_DIR"

SEX_CONTEXT_FILE="$CASE_INPUT_DIR/case_sex.resolved.tsv"

RESOLVED_SEX="$(
    python3 "$SEX_RESOLVER" \
        "$CASE_ID" \
        --mode "$PIPELINE_MODE" \
        --requested-sex "$REQUESTED_SEX" \
        --selected-sample "$SELECTED_SAMPLE" \
        --project-root "$PROJECT_ROOT" \
        --output "$SEX_CONTEXT_FILE"
)"

export PATIENT_SEX="$RESOLVED_SEX"

exec > >(tee -a "$WRAPPER_LOG") 2>&1

trap '
    status=$?
    echo
    echo "REAL-PATIENT PIPELINE FAILED"
    echo "Line: $LINENO"
    echo "Exit status: $status"
    echo "Launcher log: '"$WRAPPER_LOG"'"
    exit $status
' ERR

echo "========================================"
echo "REAL-PATIENT GENOMIC ANALYSIS PIPELINE"
echo "========================================"
echo "Case ID:       $CASE_ID"
echo "Assembly:      GRCh38"
echo "Threads:       $THREADS"
echo "Java memory:   $JAVA_MEM"
echo "Resource mode: $PIPELINE_MODE"
echo "Reported sex:  $RESOLVED_SEX"
echo


# --------------------------------------------------
# Stage 1: Universal VCF intake
# --------------------------------------------------

echo "[STAGE 1/6] Inspecting and classifying the input VCF"

python3 \
    "$INTAKE_SCRIPT" \
    "$CASE_ID" \
    "$INPUT_VCF_ARGUMENT"

INTAKE_REPORT="$PROJECT_ROOT/results/cases/$CASE_ID/final/${CASE_ID}.external_vcf_intake.tsv"

[[ -s "$INTAKE_REPORT" ]] \
    || die "Universal VCF intake report was not created."

cp -f \
    "$INTAKE_REPORT" \
    "$PRESERVED_INTAKE_REPORT"

intake_metric() {
    local key="$1"

    awk -F $'\t' -v requested_key="$key" '
        $1 == requested_key {
            gsub(/\r/, "", $2)
            print $2
            exit
        }
    ' "$PRESERVED_INTAKE_REPORT"
}

INTAKE_STATUS="$(intake_metric intake_status)"
INTAKE_SAMPLE_COUNT="$(intake_metric sample_count)"
INTAKE_BUILD="$(intake_metric genome_build)"
INTAKE_GENOTYPES="$(intake_metric usable_patient_genotypes)"
INTAKE_ANNOTATIONS="$(intake_metric existing_annotation_tags)"

echo
echo "Intake status:         $INTAKE_STATUS"
echo "Detected build:        $INTAKE_BUILD"
echo "Sample count:          $INTAKE_SAMPLE_COUNT"
echo "Usable genotypes:      $INTAKE_GENOTYPES"
echo "Existing annotations:  ${INTAKE_ANNOTATIONS:-none}"

case "$INTAKE_STATUS" in
    READY_FOR_PREPARATION_AND_FULL_PIPELINE)
        ;;

    READY_AFTER_EXISTING_ANNOTATION_CLEANUP)
        ;;

    NEEDS_EXPLICIT_SAMPLE_SELECTION)
        [[ -n "$SELECTED_SAMPLE" ]] \
            || die "The VCF contains multiple samples. Rerun with --sample SAMPLE_NAME."
        ;;

    NEEDS_GENOME_BUILD_CONFIRMATION)
        [[ "$CONFIRM_GRCH38" -eq 1 ]] \
            || die "Genome build is unknown. Confirm it independently and rerun with --confirm-grch38."
        ;;

    ANNOTATION_ONLY_NO_USABLE_GENOTYPES)
        die "The VCF has no usable alternate genotypes. Full patient analysis cannot run. It is suitable only for annotation-only processing."

        ;;

    NOT_A_PATIENT_VCF_NO_SAMPLES)
        die "This is a site-only database VCF, not a patient VCF."

        ;;

    NOT_READY_WRONG_GENOME_BUILD)
        die "The VCF is not GRCh38. Silent liftover is not permitted."

        ;;

    NOT_READY_EMPTY_VCF)
        die "The VCF contains no usable records."

        ;;

    NOT_READY_INCONSISTENT_SAMPLE_COLUMNS)
        die "The VCF contains records that do not match the sample columns declared by the #CHROM header. Preparation and annotation were not started."

        ;;

    MULTISAMPLE_WITHOUT_USABLE_GENOTYPES)
        die "The multisample VCF contains no usable alternate genotypes."

        ;;

    *)
        die "Input VCF is not eligible for the full pipeline: $INTAKE_STATUS"
        ;;
esac

if [[ "${INTAKE_SAMPLE_COUNT:-0}" -gt 1 && -z "$SELECTED_SAMPLE" ]]; then
    die "The VCF contains $INTAKE_SAMPLE_COUNT samples. Rerun with --sample SAMPLE_NAME."
fi

echo
echo "Universal intake gate passed."

# --------------------------------------------------
# Stage 2: Prepare the patient inputs
# --------------------------------------------------

echo "[STAGE 2/6] Preparing patient inputs"

PREPARATION_COMMAND=(
    bash
    "$PREPARATION_SCRIPT"
    "$CASE_ID"
    "$INPUT_VCF_ARGUMENT"
    "$PHENOTYPE_ARGUMENT"
)

if [[ -n "$SELECTED_SAMPLE" ]]; then
    PREPARATION_COMMAND+=(
        --sample
        "$SELECTED_SAMPLE"
    )
fi

if [[ "$CONFIRM_GRCH38" -eq 1 ]]; then
    PREPARATION_COMMAND+=(
        --confirm-grch38
    )
fi

if [[ "$FORCE" -eq 1 ]]; then
    PREPARATION_COMMAND+=(
        --force
    )
fi

"${PREPARATION_COMMAND[@]}"

for required_file in \
    "$READY_VCF" \
    "${READY_VCF}.tbi" \
    "$READY_HPO" \
    "$PREPARATION_REPORT" \
    "$PREPARED_READINESS"
do
    [[ -s "$required_file" ]] \
        || die "Preparation output is missing or empty: $required_file"
done


echo
echo "[STAGE 2b/6] Running sex-chromosome and ploidy preflight"

python3 "$SEX_PLOIDY_PREFLIGHT" \
    "$CASE_ID" \
    "$READY_VCF" \
    --sex "$RESOLVED_SEX" \
    --output-dir "$PREPARED_DIR"

SEX_PLOIDY_QC="$PREPARED_DIR/${CASE_ID}.sex_ploidy_qc.tsv"
SEX_PLOIDY_RECORDS="$PREPARED_DIR/${CASE_ID}.sex_ploidy_records.tsv"

[[ -s "$SEX_PLOIDY_QC" ]] \
    || die "Sex/ploidy QC report was not created."

[[ -s "$SEX_PLOIDY_RECORDS" ]] \
    || die "Sex/ploidy detail table was not created."

read_metric() {
    local table_file="$1"
    local requested_key="$2"

    awk -F $'\t' -v key="$requested_key" '
        $1 == key {
            gsub(/\r/, "", $2)
            print $2
            exit
        }
    ' "$table_file"
}

READINESS_STATUS="$(
    read_metric \
        "$PREPARATION_REPORT" \
        readiness_status
)"

if [[ "$READINESS_STATUS" == "NOT_READY" || -z "$READINESS_STATUS" ]]; then
    die "Prepared patient inputs did not pass readiness checking."
fi

echo
echo "Prepared-input readiness: $READINESS_STATUS"

# --------------------------------------------------
# Stage 3: Remove existing external annotations
# --------------------------------------------------

echo
echo "[STAGE 3/6] Creating an independent reannotation copy"

CLEANUP_COMMAND=(
    bash
    "$CLEANUP_SCRIPT"
    "$CASE_ID"
    "$READY_VCF"
)

if [[ "$FORCE" -eq 1 ]]; then
    CLEANUP_COMMAND+=(--force)
fi

"${CLEANUP_COMMAND[@]}"

for required_file in \
    "$REANNOTATION_READY_VCF" \
    "${REANNOTATION_READY_VCF}.tbi" \
    "$ANNOTATION_CLEANUP_REPORT"
do
    [[ -s "$required_file" ]] \
        || die "Annotation cleanup output is missing: $required_file"
done

# --------------------------------------------------
# Preserve preparation logs before annotation results
# are replaced by the universal launcher
# --------------------------------------------------

PREPARATION_LOG_SOURCE="$PROJECT_ROOT/results/cases/$CASE_ID/logs/${CASE_ID}.input_preparation.log"
NORMALIZATION_LOG_SOURCE="$PROJECT_ROOT/results/cases/$CASE_ID/logs/${CASE_ID}.normalization.stderr.log"

PRESERVED_PREPARATION_LOG="$PREPARED_DIR/${CASE_ID}.input_preparation.log"
PRESERVED_NORMALIZATION_LOG="$PREPARED_DIR/${CASE_ID}.normalization.stderr.log"

if [[ -s "$PREPARATION_LOG_SOURCE" ]]; then
    cp -f \
        "$PREPARATION_LOG_SOURCE" \
        "$PRESERVED_PREPARATION_LOG"
fi

if [[ -s "$NORMALIZATION_LOG_SOURCE" ]]; then
    cp -f \
        "$NORMALIZATION_LOG_SOURCE" \
        "$PRESERVED_NORMALIZATION_LOG"
fi

# --------------------------------------------------
# Stage 2: Run the complete annotation pipeline
# --------------------------------------------------

echo
echo "[STAGE 4/6] Running annotation and disease prioritization"

THREADS="$THREADS" \
JAVA_MEM="$JAVA_MEM" \
bash "$CASE_PIPELINE" \
    "$CASE_ID" \
    "$REANNOTATION_READY_VCF" \
    "$READY_HPO" \
    --force

CASE_RESULT_DIR="$PROJECT_ROOT/results/cases/$CASE_ID"
FINAL_DIR="$CASE_RESULT_DIR/final"
RESULT_LOG_DIR="$CASE_RESULT_DIR/logs"

PIPELINE_SUMMARY="$FINAL_DIR/${CASE_ID}.pipeline_summary.tsv"
MASTER_TABLE="$FINAL_DIR/${CASE_ID}.master_candidate_ranking.tsv"

[[ -s "$PIPELINE_SUMMARY" ]] \
    || die "Pipeline summary was not created."

[[ -s "$MASTER_TABLE" ]] \
    || die "Master candidate table was not created."

# --------------------------------------------------
# Stage 3: Restore preparation evidence into final
# results
# --------------------------------------------------

echo
echo "[STAGE 5/6] Preserving intake, preparation and readiness reports"

mkdir -p "$FINAL_DIR" "$RESULT_LOG_DIR"

FINAL_INTAKE_REPORT="$FINAL_DIR/${CASE_ID}.external_vcf_intake.tsv"
FINAL_PREPARATION_REPORT="$FINAL_DIR/${CASE_ID}.input_preparation_report.tsv"
FINAL_CLEANUP_REPORT="$FINAL_DIR/${CASE_ID}.annotation_cleanup_report.tsv"
FINAL_READINESS_REPORT="$FINAL_DIR/${CASE_ID}.real_patient_readiness.tsv"

cp -f \
    "$PRESERVED_INTAKE_REPORT" \
    "$FINAL_INTAKE_REPORT"

cp -f \
    "$PREPARATION_REPORT" \
    "$FINAL_PREPARATION_REPORT"

cp -f \
    "$ANNOTATION_CLEANUP_REPORT" \
    "$FINAL_CLEANUP_REPORT"

cp -f \
    "$PREPARED_READINESS" \
    "$FINAL_READINESS_REPORT"

if [[ -s "$PRESERVED_PREPARATION_LOG" ]]; then
    cp -f \
        "$PRESERVED_PREPARATION_LOG" \
        "$RESULT_LOG_DIR/${CASE_ID}.input_preparation.log"
fi

if [[ -s "$PRESERVED_NORMALIZATION_LOG" ]]; then
    cp -f \
        "$PRESERVED_NORMALIZATION_LOG" \
        "$RESULT_LOG_DIR/${CASE_ID}.input_normalization.stderr.log"
fi

# --------------------------------------------------
# Stage 4: Build a combined patient-run summary
# --------------------------------------------------

echo
echo "[STAGE 6/6] Building combined patient-run summary"

FINAL_RUN_SUMMARY="$FINAL_DIR/${CASE_ID}.real_patient_run_summary.tsv"

ASSEMBLY_CONFIRMATION="$(
    read_metric \
        "$PREPARATION_REPORT" \
        assembly_confirmation
)"

SOURCE_SHA256="$(
    read_metric \
        "$PREPARATION_REPORT" \
        source_vcf_sha256
)"

SOURCE_RECORDS="$(
    read_metric \
        "$PREPARATION_REPORT" \
        source_records
)"

PREPARED_RECORDS="$(
    read_metric \
        "$PREPARATION_REPORT" \
        prepared_nonreference_records
)"

PREPARED_HPO_COUNT="$(
    read_metric \
        "$PREPARATION_REPORT" \
        prepared_HPO_terms
)"

SMALL_VARIANT_COUNT="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        small_variant_records
)"

CNV_COUNT="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        cnv_records
)"

OTHER_SV_COUNT="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        other_structural_variants
)"

SMALL_BRANCH_STATUS="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        small_variant_branch_status
)"

CNV_BRANCH_STATUS="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        cnv_branch_status
)"

TOP_CANDIDATE_TYPE="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        top_candidate_type
)"

TOP_GENE="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        top_gene
)"

TOP_DISEASE="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        top_disease
)"

TOP_VARIANT="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        top_variant
)"

TOP_SCORE="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        top_normalized_score
)"

TOP_PRIORITY="$(
    read_metric \
        "$PIPELINE_SUMMARY" \
        top_priority
)"

{
    printf "field\tvalue\n"
    printf "case_id\t%s\n" "$CASE_ID"
    printf "run_status\tcompleted\n"
    printf "intake_status\t%s\n" "$INTAKE_STATUS"
    printf "assembly\tGRCh38\n"
    printf "assembly_confirmation\t%s\n" "$ASSEMBLY_CONFIRMATION"
    printf "readiness_status\t%s\n" "$READINESS_STATUS"
    printf "source_vcf_sha256\t%s\n" "$SOURCE_SHA256"
    printf "source_records\t%s\n" "$SOURCE_RECORDS"
    printf "prepared_nonreference_records\t%s\n" "$PREPARED_RECORDS"
    printf "prepared_HPO_terms\t%s\n" "$PREPARED_HPO_COUNT"
    printf "small_variant_records\t%s\n" "$SMALL_VARIANT_COUNT"
    printf "cnv_records\t%s\n" "$CNV_COUNT"
    printf "other_structural_variants\t%s\n" "$OTHER_SV_COUNT"
    printf "small_variant_branch_status\t%s\n" "$SMALL_BRANCH_STATUS"
    printf "cnv_branch_status\t%s\n" "$CNV_BRANCH_STATUS"
    printf "top_candidate_type\t%s\n" "$TOP_CANDIDATE_TYPE"
    printf "top_gene\t%s\n" "$TOP_GENE"
    printf "top_disease\t%s\n" "$TOP_DISEASE"
    printf "top_variant\t%s\n" "$TOP_VARIANT"
    printf "top_normalized_score\t%s\n" "$TOP_SCORE"
    printf "top_priority\t%s\n" "$TOP_PRIORITY"
    printf "prepared_vcf\t%s\n" "${READY_VCF#"$PROJECT_ROOT/"}"
    printf "reported_sex\t%s\n" "$RESOLVED_SEX"
    printf "sex_context\t%s\n" "${SEX_CONTEXT_FILE#"$PROJECT_ROOT/"}"
    printf "sex_ploidy_qc\t%s\n" "${SEX_PLOIDY_QC#"$PROJECT_ROOT/"}"
    printf "sex_ploidy_records\t%s\n" "${SEX_PLOIDY_RECORDS#"$PROJECT_ROOT/"}"
    printf "pipeline_input_vcf\t%s\n" "${REANNOTATION_READY_VCF#"$PROJECT_ROOT/"}"
    printf "prepared_phenotypes\t%s\n" "${READY_HPO#"$PROJECT_ROOT/"}"
    printf "intake_report\t%s\n" "${FINAL_INTAKE_REPORT#"$PROJECT_ROOT/"}"
    printf "annotation_cleanup_report\t%s\n" "${FINAL_CLEANUP_REPORT#"$PROJECT_ROOT/"}"
    printf "preparation_report\t%s\n" "${FINAL_PREPARATION_REPORT#"$PROJECT_ROOT/"}"
    printf "readiness_report\t%s\n" "${FINAL_READINESS_REPORT#"$PROJECT_ROOT/"}"
    printf "pipeline_summary\t%s\n" "${PIPELINE_SUMMARY#"$PROJECT_ROOT/"}"
    printf "master_candidate_table\t%s\n" "${MASTER_TABLE#"$PROJECT_ROOT/"}"
    printf "launcher_log\t%s\n" "${WRAPPER_LOG#"$PROJECT_ROOT/"}"
    printf "manual_clinical_review_required\tyes\n"
    printf "manual_privacy_review_required\tyes\n"
} > "$FINAL_RUN_SUMMARY"

echo
echo "========================================"
echo "REAL-PATIENT PIPELINE COMPLETED"
echo "========================================"
echo "Case ID:             $CASE_ID"
echo "Intake status:       $INTAKE_STATUS"
echo "Readiness:           $READINESS_STATUS"
echo "Small-variant branch:$SMALL_BRANCH_STATUS"
echo "CNV branch:          $CNV_BRANCH_STATUS"
echo "Top candidate type:  $TOP_CANDIDATE_TYPE"
echo "Top gene:            $TOP_GENE"
echo "Top disease:         $TOP_DISEASE"
echo "Top variant:         $TOP_VARIANT"
echo "Normalized score:    $TOP_SCORE"
echo "Priority:            $TOP_PRIORITY"
echo
echo "Master candidate table:"
echo "$MASTER_TABLE"
echo
echo "Combined run summary:"
echo "$FINAL_RUN_SUMMARY"
echo
echo "This output is a prioritization result and requires"
echo "manual clinical and molecular interpretation."

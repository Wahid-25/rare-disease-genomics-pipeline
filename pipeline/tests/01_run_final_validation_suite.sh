#!/usr/bin/env bash

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT" || exit 1

TEST_ROOT="$PROJECT_ROOT/results/final_validation_suite"
WORK_DIR="$TEST_ROOT/work"
LOG_DIR="$TEST_ROOT/logs"

REPORT="$TEST_ROOT/final_validation_report.tsv"
SOFTWARE_REPORT="$TEST_ROOT/software_versions.tsv"
HASH_REPORT="$TEST_ROOT/pipeline_script_sha256.tsv"

CORE_SIF="$PROJECT_ROOT/containers/core_tools.sif"

READINESS_SCRIPT="$PROJECT_ROOT/pipeline/case_workflow/15_check_real_patient_readiness.py"
PREPARATION_SCRIPT="$PROJECT_ROOT/pipeline/case_workflow/16_prepare_real_patient_inputs.sh"

PASS_COUNT=0
FAIL_COUNT=0

rm -rf "$TEST_ROOT"

mkdir -p \
    "$WORK_DIR" \
    "$LOG_DIR"

printf "test_id\tstatus\tdescription\n" > "$REPORT"


record_pass() {
    local test_id="$1"
    local description="$2"

    PASS_COUNT=$((PASS_COUNT + 1))

    printf "%s\tPASS\t%s\n" \
        "$test_id" \
        "$description" \
        >> "$REPORT"

    printf "PASS  %-38s %s\n" \
        "$test_id" \
        "$description"
}


record_fail() {
    local test_id="$1"
    local description="$2"

    FAIL_COUNT=$((FAIL_COUNT + 1))

    printf "%s\tFAIL\t%s\n" \
        "$test_id" \
        "$description" \
        >> "$REPORT"

    printf "FAIL  %-38s %s\n" \
        "$test_id" \
        "$description"
}


check_file() {
    local test_id="$1"
    local path="$2"

    if [[ -s "$path" ]]; then
        record_pass \
            "$test_id" \
            "Required file exists: ${path#"$PROJECT_ROOT/"}"
    else
        record_fail \
            "$test_id" \
            "Missing or empty file: ${path#"$PROJECT_ROOT/"}"
    fi
}


read_metric() {
    local table="$1"
    local key="$2"

    awk -F $'\t' -v requested_key="$key" '
        $1 == requested_key {
            gsub(/\r/, "", $2)
            print $2
            exit
        }
    ' "$table" 2>/dev/null
}


check_metric() {
    local test_id="$1"
    local table="$2"
    local key="$3"
    local expected="$4"

    if [[ ! -s "$table" ]]; then
        record_fail \
            "$test_id" \
            "Metric table is missing: ${table#"$PROJECT_ROOT/"}"
        return
    fi

    local observed

    observed="$(read_metric "$table" "$key")"

    if [[ "$observed" == "$expected" ]]; then
        record_pass \
            "$test_id" \
            "$key=$observed"
    else
        record_fail \
            "$test_id" \
            "$key expected '$expected' but observed '$observed'"
    fi
}


check_candidate_type() {
    local test_id="$1"
    local table="$2"
    local candidate_type="$3"

    if [[ ! -s "$table" ]]; then
        record_fail \
            "$test_id" \
            "Master table is missing: ${table#"$PROJECT_ROOT/"}"
        return
    fi

    if awk -F $'\t' -v expected="$candidate_type" '
        NR == 1 {
            for (column = 1; column <= NF; column++) {
                if ($column == "candidate_type") {
                    type_column = column
                }
            }

            next
        }

        type_column > 0 && $type_column == expected {
            found = 1
        }

        END {
            exit(found ? 0 : 1)
        }
    ' "$table"
    then
        record_pass \
            "$test_id" \
            "Candidate type present: $candidate_type"
    else
        record_fail \
            "$test_id" \
            "Candidate type missing: $candidate_type"
    fi
}


expect_failure() {
    local test_id="$1"
    local expected_pattern="$2"
    local log_file="$3"

    shift 3

    if "$@" > "$log_file" 2>&1; then
        record_fail \
            "$test_id" \
            "Command unexpectedly succeeded"
        return
    fi

    if grep -qiE "$expected_pattern" "$log_file"; then
        record_pass \
            "$test_id" \
            "Unsafe input was rejected for the expected reason"
    else
        record_fail \
            "$test_id" \
            "Command failed, but not for the expected reason; inspect ${log_file#"$PROJECT_ROOT/"}"
    fi
}


expect_success() {
    local test_id="$1"
    local log_file="$2"

    shift 2

    if "$@" > "$log_file" 2>&1; then
        record_pass \
            "$test_id" \
            "Command completed successfully"
    else
        record_fail \
            "$test_id" \
            "Command failed; inspect ${log_file#"$PROJECT_ROOT/"}"
    fi
}


echo "========================================"
echo "FINAL REPRODUCIBILITY AND FAILURE TESTS"
echo "========================================"
echo

# ==================================================
# Section 1: Script syntax
# ==================================================

echo "[1/7] Checking workflow script syntax"

while IFS= read -r script
do
    script_name="$(basename "$script")"

    if bash -n "$script" \
        > "$LOG_DIR/${script_name}.syntax.log" \
        2>&1
    then
        record_pass \
            "bash_syntax_${script_name}" \
            "Valid Bash syntax"
    else
        record_fail \
            "bash_syntax_${script_name}" \
            "Invalid Bash syntax"
    fi
done < <(
    find pipeline \
        -type f \
        -name '*.sh' \
        | sort
)

while IFS= read -r script
do
    script_name="$(basename "$script")"

    if python3 -m py_compile "$script" \
        > "$LOG_DIR/${script_name}.syntax.log" \
        2>&1
    then
        record_pass \
            "python_syntax_${script_name}" \
            "Valid Python syntax"
    else
        record_fail \
            "python_syntax_${script_name}" \
            "Invalid Python syntax"
    fi
done < <(
    find pipeline \
        -type f \
        -name '*.py' \
        | sort
)

# ==================================================
# Section 2: Required resources
# ==================================================

echo
echo "[2/7] Checking containers and resources"

check_file \
    "resource_core_container" \
    "$PROJECT_ROOT/containers/core_tools.sif"

check_file \
    "resource_vep_container" \
    "$PROJECT_ROOT/containers/vep_release115.sif"

check_file \
    "resource_snpeff_container" \
    "$PROJECT_ROOT/containers/snpeff.sif"

check_file \
    "resource_spliceai_container" \
    "$PROJECT_ROOT/containers/spliceai.sif"

check_file \
    "resource_annotsv_container" \
    "$PROJECT_ROOT/containers/annotsv.sif"

check_file \
    "resource_isv_container" \
    "$PROJECT_ROOT/containers/isv.sif"

check_file \
    "resource_reference" \
    "$PROJECT_ROOT/resources/reference/hg38.fa"

check_file \
    "resource_reference_index" \
    "$PROJECT_ROOT/resources/reference/hg38.fa.fai"

check_file \
    "resource_clinvar" \
    "$PROJECT_ROOT/resources/clinvar/clinvar.chr.vcf.gz"

check_file \
    "resource_clinvar_index" \
    "$PROJECT_ROOT/resources/clinvar/clinvar.chr.vcf.gz.tbi"

check_file \
    "resource_clingen" \
    "$PROJECT_ROOT/resources/clingen/clingen_dosage.hg38.bed.gz"

check_file \
    "resource_clingen_index" \
    "$PROJECT_ROOT/resources/clingen/clingen_dosage.hg38.bed.gz.tbi"

check_file \
    "resource_g2p_official" \
    "$PROJECT_ROOT/resources/gene_disease/g2p/AllG2P.official.csv"

check_file \
    "resource_classifycnv" \
    "$PROJECT_ROOT/tools/ClassifyCNV/ClassifyCNV.py"

if [[ -d "$PROJECT_ROOT/resources/annotsv_annotations/AnnotSV_annotations" ]]; then
    record_pass \
        "resource_annotsv_annotations" \
        "AnnotSV annotation directory exists"
else
    record_fail \
        "resource_annotsv_annotations" \
        "AnnotSV annotation directory is missing"
fi

# ==================================================
# Section 3: Completed synthetic cases
# ==================================================

echo
echo "[3/7] Checking completed synthetic cases"

SMALL_SUMMARY="$PROJECT_ROOT/results/cases/case_auto001/final/case_auto001.pipeline_summary.tsv"
SMALL_MASTER="$PROJECT_ROOT/results/cases/case_auto001/final/case_auto001.master_candidate_ranking.tsv"

check_metric \
    "small_branch_completed" \
    "$SMALL_SUMMARY" \
    "small_variant_branch_status" \
    "completed"

check_metric \
    "small_top_gene" \
    "$SMALL_SUMMARY" \
    "top_gene" \
    "HEXA"

check_metric \
    "small_top_disease" \
    "$SMALL_SUMMARY" \
    "top_disease" \
    "Tay-Sachs disease"

check_candidate_type \
    "small_candidate_type" \
    "$SMALL_MASTER" \
    "small_variant"


CNV_SUMMARY="$PROJECT_ROOT/results/cases/case_auto_cnv001/final/case_auto_cnv001.pipeline_summary.tsv"
CNV_MASTER="$PROJECT_ROOT/results/cases/case_auto_cnv001/final/case_auto_cnv001.master_candidate_ranking.tsv"

check_metric \
    "cnv_branch_completed" \
    "$CNV_SUMMARY" \
    "cnv_branch_status" \
    "completed"

check_metric \
    "cnv_top_gene" \
    "$CNV_SUMMARY" \
    "top_gene" \
    "HEXA"

check_metric \
    "cnv_top_disease" \
    "$CNV_SUMMARY" \
    "top_disease" \
    "Tay-Sachs disease"

check_candidate_type \
    "cnv_candidate_type" \
    "$CNV_MASTER" \
    "cnv"


MIXED_SUMMARY="$PROJECT_ROOT/results/cases/case_real_launcher_test/final/case_real_launcher_test.real_patient_run_summary.tsv"
MIXED_MASTER="$PROJECT_ROOT/results/cases/case_real_launcher_test/final/case_real_launcher_test.master_candidate_ranking.tsv"

check_metric \
    "mixed_small_branch_completed" \
    "$MIXED_SUMMARY" \
    "small_variant_branch_status" \
    "completed"

check_metric \
    "mixed_cnv_branch_completed" \
    "$MIXED_SUMMARY" \
    "cnv_branch_status" \
    "completed"

check_metric \
    "mixed_top_gene" \
    "$MIXED_SUMMARY" \
    "top_gene" \
    "HEXA"

check_metric \
    "mixed_top_disease" \
    "$MIXED_SUMMARY" \
    "top_disease" \
    "Tay-Sachs disease"

check_candidate_type \
    "mixed_small_candidate_present" \
    "$MIXED_MASTER" \
    "small_variant"

check_candidate_type \
    "mixed_cnv_candidate_present" \
    "$MIXED_MASTER" \
    "cnv"

VALIDATION_SUMMARY="$PROJECT_ROOT/results/cases/case_real_launcher_test/final/case_real_launcher_test.blinded_validation_summary.tsv"

check_metric \
    "blinded_validation_pass" \
    "$VALIDATION_SUMMARY" \
    "validation_status" \
    "PASS"

check_metric \
    "truth_not_used_in_pipeline" \
    "$VALIDATION_SUMMARY" \
    "truth_used_during_pipeline" \
    "no"

# ==================================================
# Section 4: Create controlled invalid inputs
# ==================================================

echo
echo "[4/7] Creating controlled invalid inputs"

VALID_HPO="$WORK_DIR/valid_hpo.txt"
EMPTY_HPO="$WORK_DIR/empty_hpo.txt"

cat > "$VALID_HPO" <<'HPO'
HP:0001250
HP:0001252
HPO

cat > "$EMPTY_HPO" <<'HPO'
# No valid HPO identifiers in this file
seizures
developmental regression
HPO

GRCH38_VCF="$WORK_DIR/grch38_valid.vcf"

cat > "$GRCH38_VCF" <<'VCF'
##fileformat=VCFv4.2
##reference=GRCh38
##contig=<ID=chr15>
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	PATIENT
chr15	72346579	TEST_VARIANT	G	GGATA	.	PASS	.	GT	1/1
VCF

GRCH37_VCF="$WORK_DIR/grch37.vcf"

cat > "$GRCH37_VCF" <<'VCF'
##fileformat=VCFv4.2
##reference=GRCh37
##contig=<ID=chr15>
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	PATIENT
chr15	72600000	TEST_VARIANT	G	A	.	PASS	.	GT	0/1
VCF

NO_GT_VCF="$WORK_DIR/no_gt.vcf"

cat > "$NO_GT_VCF" <<'VCF'
##fileformat=VCFv4.2
##reference=GRCh38
##contig=<ID=chr15>
##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read depth">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	PATIENT
chr15	72346579	TEST_VARIANT	G	A	.	PASS	.	DP	30
VCF

MISSING_END_VCF="$WORK_DIR/missing_end_cnv.vcf"

cat > "$MISSING_END_VCF" <<'VCF'
##fileformat=VCFv4.2
##reference=GRCh38
##contig=<ID=chr15>
##ALT=<ID=DEL,Description="Deletion">
##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Structural variant type">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	PATIENT
chr15	72340923	TEST_DEL	N	<DEL>	.	PASS	SVTYPE=DEL	GT	1/1
VCF

MIXED_CHROM_VCF="$WORK_DIR/mixed_chromosomes.vcf"

cat > "$MIXED_CHROM_VCF" <<'VCF'
##fileformat=VCFv4.2
##reference=GRCh38
##contig=<ID=chr15>
##contig=<ID=15>
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	PATIENT
chr15	72346579	TEST_ONE	G	A	.	PASS	.	GT	0/1
15	72346580	TEST_TWO	A	G	.	PASS	.	GT	0/1
VCF

MULTISAMPLE_VCF="$WORK_DIR/multisample_nonprefixed.vcf"

cat > "$MULTISAMPLE_VCF" <<'VCF'
##fileformat=VCFv4.2
##reference=GRCh38
##contig=<ID=15>
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	PATIENT_A	PATIENT_B
15	72346579	TEST_VARIANT	G	GGATA	.	PASS	.	GT	1/1	0/0
VCF

record_pass \
    "controlled_inputs_created" \
    "Synthetic failure-mode inputs were created"

# ==================================================
# Section 5: Readiness checker behavior
# ==================================================

echo
echo "[5/7] Testing readiness-checker decisions"

expect_failure \
    "reject_missing_hpo" \
    "No valid HP:[#0-9]+|No valid HP" \
    "$LOG_DIR/reject_missing_hpo.log" \
    python3 \
    "$READINESS_SCRIPT" \
    qa_readiness_missing_hpo \
    "$GRCH38_VCF" \
    "$EMPTY_HPO"

expect_failure \
    "reject_grch37" \
    "GRCh37|hg19" \
    "$LOG_DIR/reject_grch37.log" \
    python3 \
    "$READINESS_SCRIPT" \
    qa_readiness_grch37 \
    "$GRCH37_VCF" \
    "$VALID_HPO"

expect_success \
    "accept_missing_gt_annotation_only" \
    "$LOG_DIR/accept_missing_gt_annotation_only.log" \
    python3 \
    "$READINESS_SCRIPT" \
    qa_readiness_no_gt \
    "$NO_GT_VCF" \
    "$VALID_HPO"

NO_GT_REPORT="$PROJECT_ROOT/results/cases/qa_readiness_no_gt/final/qa_readiness_no_gt.real_patient_readiness.tsv"

check_metric \
    "missing_gt_readiness_warning" \
    "$NO_GT_REPORT" \
    "readiness_status" \
    "READY_WITH_WARNINGS"

check_metric \
    "missing_gt_annotation_mode" \
    "$NO_GT_REPORT" \
    "analysis_mode" \
    "annotation_only"

check_metric \
    "missing_gt_genotype_unavailable" \
    "$NO_GT_REPORT" \
    "genotype_available" \
    "no"

check_metric \
    "missing_gt_inheritance_disabled" \
    "$NO_GT_REPORT" \
    "inheritance_evaluated" \
    "no"

expect_failure \
    "reject_cnv_missing_end" \
    "lack INFO/END|lacks INFO/END" \
    "$LOG_DIR/reject_cnv_missing_end.log" \
    python3 \
    "$READINESS_SCRIPT" \
    qa_readiness_missing_end \
    "$MISSING_END_VCF" \
    "$VALID_HPO"

expect_failure \
    "reject_mixed_chromosomes" \
    "Mixed chromosome naming" \
    "$LOG_DIR/reject_mixed_chromosomes.log" \
    python3 \
    "$READINESS_SCRIPT" \
    qa_readiness_mixed_chrom \
    "$MIXED_CHROM_VCF" \
    "$VALID_HPO"

# ==================================================
# Section 5b: Universal intake column consistency
# ==================================================

echo
echo "[5b/7] Testing universal intake column consistency"

COLUMN_TEST_VCF="$WORK_DIR/inconsistent_sample_columns.vcf"
COLUMN_TEST_HPO="$WORK_DIR/inconsistent_sample_columns.hpo.txt"

INTAKE_SCRIPT="$PROJECT_ROOT/pipeline/case_workflow/18_external_case_intake.py"
LAUNCHER_SCRIPT="$PROJECT_ROOT/pipeline/run_real_patient_case.sh"

python3 - "$COLUMN_TEST_VCF" <<'PYTEST'
from pathlib import Path
import sys

output = Path(sys.argv[1])

records = [
    "##fileformat=VCFv4.2",
    "##reference=GRCh38",
    "##contig=<ID=chr9,length=138394717>",
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
    "\t".join([
        "#CHROM",
        "POS",
        "ID",
        "REF",
        "ALT",
        "QUAL",
        "FILTER",
        "INFO",
        "FORMAT",
        "PATIENT",
    ]),
    "\t".join([
        "chr9",
        "100000",
        "VALID",
        "A",
        "G",
        ".",
        "PASS",
        ".",
        "GT",
        "0/1",
    ]),
    "\t".join([
        "chr9",
        "100100",
        "INVALID",
        "C",
        "T",
        ".",
        "PASS",
        ".",
    ]),
]

output.write_text(
    "\n".join(records) + "\n",
    encoding="utf-8",
)
PYTEST

cat > "$COLUMN_TEST_HPO" <<'HPO'
HP:0001250
HPO

INTAKE_COLUMN_CASE="qa_intake_inconsistent_columns"

INTAKE_COLUMN_REPORT="$PROJECT_ROOT/results/cases/$INTAKE_COLUMN_CASE/final/${INTAKE_COLUMN_CASE}.external_vcf_intake.tsv"

expect_success \
    "intake_column_validation_runs" \
    "$LOG_DIR/intake_column_validation_runs.log" \
    python3 \
    "$INTAKE_SCRIPT" \
    "$INTAKE_COLUMN_CASE" \
    "$COLUMN_TEST_VCF"

check_metric \
    "intake_rejects_inconsistent_columns" \
    "$INTAKE_COLUMN_REPORT" \
    "intake_status" \
    "NOT_READY_INCONSISTENT_SAMPLE_COLUMNS"

check_metric \
    "intake_counts_inconsistent_columns" \
    "$INTAKE_COLUMN_REPORT" \
    "inconsistent_sample_column_records" \
    "1"

check_metric \
    "intake_expected_column_count" \
    "$INTAKE_COLUMN_REPORT" \
    "expected_columns_per_record" \
    "10"

check_metric \
    "intake_disables_pipeline_processing" \
    "$INTAKE_COLUMN_REPORT" \
    "pipeline_processing_allowed" \
    "no"

check_metric \
    "intake_disables_genotype_analysis" \
    "$INTAKE_COLUMN_REPORT" \
    "analysis_mode" \
    "not_applicable"

LAUNCHER_COLUMN_CASE="qa_launcher_inconsistent_columns"
LAUNCHER_COLUMN_LOG="$LOG_DIR/launcher_rejects_inconsistent_columns.log"

expect_failure \
    "launcher_rejects_inconsistent_columns" \
    "NOT_READY_INCONSISTENT_SAMPLE_COLUMNS|do not match the sample columns" \
    "$LAUNCHER_COLUMN_LOG" \
    bash \
    "$LAUNCHER_SCRIPT" \
    "$LAUNCHER_COLUMN_CASE" \
    "$COLUMN_TEST_VCF" \
    "$COLUMN_TEST_HPO" \
    --confirm-grch38

if grep -q '\[STAGE 2/6\]' "$LAUNCHER_COLUMN_LOG"; then
    record_fail \
        "launcher_blocks_stage2_after_column_failure" \
        "Launcher entered input preparation after intake rejection"
else
    record_pass \
        "launcher_blocks_stage2_after_column_failure" \
        "Launcher stopped before input preparation"
fi

rm -rf \
    "$PROJECT_ROOT/results/cases/$INTAKE_COLUMN_CASE" \
    "$PROJECT_ROOT/results/cases/$LAUNCHER_COLUMN_CASE" \
    "$PROJECT_ROOT/input/cases/$LAUNCHER_COLUMN_CASE"


# ==================================================
# Section 6: Preparation safety and repair tests
# ==================================================

echo
echo "[6/7] Testing patient-input preparation"

expect_failure \
    "multisample_requires_selection" \
    "contains 2 samples|--sample" \
    "$LOG_DIR/multisample_requires_selection.log" \
    bash \
    "$PREPARATION_SCRIPT" \
    qa_prepare_refusal \
    "$MULTISAMPLE_VCF" \
    "$VALID_HPO" \
    --force

expect_success \
    "multisample_explicit_selection" \
    "$LOG_DIR/multisample_explicit_selection.log" \
    bash \
    "$PREPARATION_SCRIPT" \
    qa_prepare_success \
    "$MULTISAMPLE_VCF" \
    "$VALID_HPO" \
    --sample PATIENT_A \
    --force

PREPARED_VCF="$PROJECT_ROOT/input/cases/qa_prepare_success/prepared/qa_prepare_success.ready.vcf.gz"
PREPARATION_REPORT="$PROJECT_ROOT/input/cases/qa_prepare_success/prepared/qa_prepare_success.preparation_report.tsv"

check_file \
    "prepared_vcf_created" \
    "$PREPARED_VCF"

check_file \
    "prepared_vcf_index_created" \
    "${PREPARED_VCF}.tbi"

check_metric \
    "prepared_readiness_status" \
    "$PREPARATION_REPORT" \
    "readiness_status" \
    "READY"

check_metric \
    "prepared_sample_anonymized" \
    "$PREPARATION_REPORT" \
    "prepared_sample_name" \
    "qa_prepare_success"

check_metric \
    "chromosome_prefix_repaired" \
    "$PREPARATION_REPORT" \
    "chromosome_names_renamed" \
    "1"

if [[ -s "$PREPARED_VCF" ]]; then
    PREPARED_SAMPLE="$(
        apptainer exec \
            --bind "$PROJECT_ROOT:/project" \
            "$CORE_SIF" \
            bcftools query -l \
            /project/input/cases/qa_prepare_success/prepared/qa_prepare_success.ready.vcf.gz \
            2>/dev/null
    )"

    if [[ "$PREPARED_SAMPLE" == "qa_prepare_success" ]]; then
        record_pass \
            "prepared_vcf_sample_name" \
            "Prepared VCF sample was renamed to the neutral case ID"
    else
        record_fail \
            "prepared_vcf_sample_name" \
            "Unexpected prepared sample name: $PREPARED_SAMPLE"
    fi

    if apptainer exec \
        --bind "$PROJECT_ROOT:/project" \
        "$CORE_SIF" \
        bcftools query \
        -f '%CHROM\n' \
        /project/input/cases/qa_prepare_success/prepared/qa_prepare_success.ready.vcf.gz \
        2>/dev/null \
        | awk '
            $0 !~ /^chr/ {
                invalid = 1
            }

            END {
                exit(invalid ? 1 : 0)
            }
        '
    then
        record_pass \
            "prepared_vcf_chr_prefix" \
            "All prepared records use the chr prefix"
    else
        record_fail \
            "prepared_vcf_chr_prefix" \
            "A prepared record lacks the chr prefix"
    fi
fi

# ==================================================
# Section 7: Reproducibility records
# ==================================================

echo
echo "[7/7] Recording versions and script checksums"

{
    printf "item\tvalue\n"

    printf "test_date_utc\t%s\n" \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

    printf "python\t%s\n" \
        "$(python3 --version 2>&1)"

    printf "apptainer\t%s\n" \
        "$(apptainer --version 2>&1)"

    printf "bcftools\t%s\n" \
        "$(
            apptainer exec \
                --bind "$PROJECT_ROOT:/project" \
                "$CORE_SIF" \
                bcftools --version \
                2>/dev/null \
                | head -n 1
        )"

    if git rev-parse --is-inside-work-tree \
        >/dev/null 2>&1
    then
        printf "git_commit\t%s\n" \
            "$(git rev-parse HEAD 2>/dev/null)"
    else
        printf "git_commit\tnot_a_git_repository\n"
    fi
} > "$SOFTWARE_REPORT"

{
    printf "sha256\tpath\n"

    find pipeline \
        -type f \
        \( \
            -name '*.sh' \
            -o -name '*.py' \
        \) \
        -print0 \
        | sort -z \
        | while IFS= read -r -d '' file
        do
            hash="$(sha256sum "$file" | awk '{print $1}')"

            printf "%s\t%s\n" \
                "$hash" \
                "$file"
        done
} > "$HASH_REPORT"

check_file \
    "software_versions_recorded" \
    "$SOFTWARE_REPORT"

check_file \
    "script_hashes_recorded" \
    "$HASH_REPORT"

# Clean temporary QA case folders while retaining the suite reports.
rm -rf \
    "$PROJECT_ROOT/results/cases/qa_readiness_missing_hpo" \
    "$PROJECT_ROOT/results/cases/qa_readiness_grch37" \
    "$PROJECT_ROOT/results/cases/qa_readiness_no_gt" \
    "$PROJECT_ROOT/results/cases/qa_readiness_missing_end" \
    "$PROJECT_ROOT/results/cases/qa_readiness_mixed_chrom" \
    "$PROJECT_ROOT/results/cases/qa_prepare_refusal" \
    "$PROJECT_ROOT/results/cases/qa_prepare_success" \
    "$PROJECT_ROOT/input/cases/qa_prepare_refusal" \
    "$PROJECT_ROOT/input/cases/qa_prepare_success"

echo
echo "========================================"
echo "FINAL VALIDATION SUMMARY"
echo "========================================"
echo "Passed tests: $PASS_COUNT"
echo "Failed tests: $FAIL_COUNT"
echo
echo "Validation report:"
echo "$REPORT"
echo
echo "Software versions:"
echo "$SOFTWARE_REPORT"
echo
echo "Pipeline script hashes:"
echo "$HASH_REPORT"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
    echo
    echo "FINAL VALIDATION SUITE FAILED"
    exit 1
fi

echo
echo "ALL FINAL VALIDATION TESTS PASSED"

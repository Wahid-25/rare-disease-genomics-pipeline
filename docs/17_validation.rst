.. _17-validation-strategy-unit-tests-regression-testing-and-final-audit-procedure:

17. Validation Strategy, Unit Tests, Regression Testing and Final Audit Procedure
=================================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


Validation confirms that the pipeline continues to process the same inputs in the same way after changes to source code, containers, reference resources or analytical rules.

The project uses several validation layers:

Source-code syntax validation

│

▼

VCF structural preflight

│

▼

Targeted unit and regression tests

│

▼

Controlled synthetic case execution

│

▼

Canonical candidate comparison

│

▼

Source, resource and output checksum verification

│

▼

Final Patients 01–12 audit

These layers answer different questions:

Syntax tests:

Can the source files be parsed?

Structural preflight:

Are the prepared VCF inputs valid and routable?

Unit tests:

Does one specific rule behave correctly?

Regression tests:

Did a previously corrected behaviour remain correct?

Case validation:

Does the complete workflow recover the expected candidate?

Checksum audit:

Did the validated source, resources or outputs change?

A single successful case is not sufficient to validate the complete workflow.

.. _17-1-validation-objectives:

17.1 Validation objectives
--------------------------

The validation system is designed to confirm that:

✓ Supported VCF structures are accepted

✓ Malformed or unsupported records are reported

✓ Production and validation resources remain isolated

✓ Pharmacogenomic matching is allele-aware

✓ Inheritance models are applied consistently

✓ Sex and ploidy are evaluated before X-linked interpretation

✓ Compound-heterozygous phase logic remains correct

✓ HPO files are associated with the exact patient

✓ G2P disease labels retain the intended precedence

✓ Intake reports are preserved

✓ Repeat expansions follow the dedicated route

✓ Expected principal candidates remain correctly ranked

✓ Source, resource and result changes are traceable

The validation suite uses synthetic educational cases. It demonstrates software behaviour and reproducibility, not clinical performance in a patient population.

.. _17-2-validation-directory-structure:

17.2 Validation directory structure
-----------------------------------

The principal validation directory is:

validation/

Important components include:

validation/

├── universal_pipeline_testing/

│ ├── inputs/

│ │ ├── vcfs/

│ │ ├── hpo/

│ │ └── reference/

│ ├── manifests/

│ │ ├── vcf_preflight.tsv

│ │ └── input_sha256.tsv

│ └── expected or generated validation outputs

│

├── final_audit_20260727/

│ ├── canonical_cases.tsv

│ ├── canonical_final_outputs.sha256

│ ├── key_resources.sha256

│ ├── pipeline_source.sha256

│ ├── FINAL_VALIDATION_STATUS.md

│ └── scripts/

│ └── audit_patients_01_12_final.py

│

└── additional development and historical validation material

The final audit directory should be treated as a fixed record of the accepted project state.

.. _17-3-validation-inputs:

17.3 Validation inputs
----------------------

The controlled validation suite includes prepared GRCh38 VCF files, HPO files and reference metadata.

The VCF inputs are stored under:

.. code:: bash

   validation/universal_pipeline_testing/inputs/vcfs/

The HPO inputs are stored under:

.. code:: bash

   validation/universal_pipeline_testing/inputs/hpo/

The validation sample sheet is stored under:

.. code:: bash

   validation/universal_pipeline_testing/inputs/reference/sample_sheet.csv

These inputs should remain synthetic and non-identifying.

.. _17-3-1-inventory-the-validation-inputs:

17.3.1 Inventory the validation inputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   echo "=== Validation VCFs ==="
   find \
   validation/universal_pipeline_testing/inputs/vcfs \
   -maxdepth 1 \
   -type f \
   \( -name '*.vcf' -o -name '*.vcf.gz' \) \
   -printf '%f\n' |

sort

.. code:: bash

   echo
   echo "=== Validation HPO files ==="
   find \
   validation/universal_pipeline_testing/inputs/hpo \
   -maxdepth 1 \
   -type f \
   -printf '%f\n' |

sort

.. code:: bash

   echo
   echo "=== Validation reference files ==="
   find \
   validation/universal_pipeline_testing/inputs/reference \
   -maxdepth 1 \
   -type f \
   -printf '%f\n' |

sort

.. _17-3-2-count-the-prepared-vcf-files:

17.3.2 Count the prepared VCF files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF_COUNT="$(
   find \
   validation/universal_pipeline_testing/inputs/vcfs \
   -maxdepth 1 \
   -type f \
   \( -name '*.vcf' -o -name '*.vcf.gz' \) \
   | wc -l
   )"
   echo "Prepared validation VCFs: $VCF_COUNT"

The project prepared thirteen validation VCFs. Patient 13 passed structural preflight but was intentionally not processed through the full final workflow because of the project timeframe.

.. _17-4-validation-environment-preparation:

17.4 Validation environment preparation
---------------------------------------

Validation should be performed from the project root:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail

Activate the project virtual environment:

.. code:: bash

   if [[ ! -x .venv/bin/python ]]; then
   echo "ERROR: Project virtual environment is unavailable."
   exit 1
   fi
   source .venv/bin/activate
   python --version

Confirm essential commands:

.. code:: bash

   REQUIRED_COMMANDS=(
   python
   bash
   bcftools
   bgzip
   tabix
   sha256sum
   git
   )
   FAILURES=0
   for command_name in "${REQUIRED_COMMANDS[@]}"; do
   if command -v "$command_name" >/dev/null 2>&1; then
   printf "PASS %-12s %s\n" \
   "$command_name" \
   "$(command -v "$command_name")"
   else
   printf "FAIL %s\n" "$command_name"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo
   echo "ERROR: $FAILURES required command(s) are missing."
   exit 1
   fi

Validation should not proceed in an incomplete environment.

.. _17-5-preserve-the-repository-state-before-testing:

17.5 Preserve the repository state before testing
-------------------------------------------------

Record the Git state before executing tests:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git status --short \
   > /tmp/rare_disease_git_status_before_validation.txt
   git rev-parse HEAD \
   > /tmp/rare_disease_commit_before_validation.txt
   echo "Commit:"
   cat /tmp/rare_disease_commit_before_validation.txt
   echo
   echo "Working-tree status:"
   cat /tmp/rare_disease_git_status_before_validation.txt

An existing modified file does not necessarily prevent testing, but it makes the results harder to compare with the validated source state.

For a strict canonical audit, the relevant source files must match:

.. code:: bash

   validation/final_audit_20260727/pipeline_source.sha256

.. _17-6-source-code-syntax-validation:

17.6 Source-code syntax validation
----------------------------------

Syntax validation detects malformed Python and Bash files before case execution.

It does not confirm biological correctness, but it catches problems such as:

-  

   .. container::

      Missing brackets

-  

   .. container::

      Incorrect indentation

-  

   .. container::

      Invalid Python syntax

-  

   .. container::

      Broken shell quoting

-  

   .. container::

      Malformed conditional blocks

-  

   .. container::

      Truncated source files

.. _17-6-1-validate-all-pipeline-bash-files:

17.6.1 Validate all pipeline Bash files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   BASH_FAILURES=0
   BASH_COUNT=0
   while IFS= read -r -d '' script; do
   BASH_COUNT=$((BASH_COUNT + 1))
   if bash -n "$script"; then
   printf "PASS %s\n" "$script"
   else
   printf "FAIL %s\n" "$script"
   BASH_FAILURES=$((BASH_FAILURES + 1))
   fi
   done < <(
   find pipeline \
   -type f \
   -name '*.sh' \
   -print0 |
   sort -z
   )
   echo
   echo "Bash files checked: $BASH_COUNT"
   echo "Bash syntax failures: $BASH_FAILURES"
   if (( BASH_FAILURES > 0 )); then
   exit 1
   fi

.. _17-6-2-validate-all-pipeline-python-files:

17.6.2 Validate all pipeline Python files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   PYTHON_FAILURES=0
   PYTHON_COUNT=0
   while IFS= read -r -d '' script; do
   PYTHON_COUNT=$((PYTHON_COUNT + 1))
   if python -m py_compile "$script"; then
   printf "PASS %s\n" "$script"
   else
   printf "FAIL %s\n" "$script"
   PYTHON_FAILURES=$((PYTHON_FAILURES + 1))
   fi
   done < <(
   find pipeline validation \
   -type f \
   -name '*.py' \
   -print0 |
   sort -z
   )
   echo
   echo "Python files checked: $PYTHON_COUNT"
   echo "Python syntax failures: $PYTHON_FAILURES"
   if (( PYTHON_FAILURES > 0 )); then
   exit 1
   fi

This command may create \__pycache\_\_ directories. They are ignored by Git and may be removed after testing.

.. _17-7-vcf-structural-preflight:

17.7 VCF structural preflight
-----------------------------

The structural-preflight launcher is:

.. code:: bash

   pipeline/tests/run_vcf_structural_preflight.sh

The preflight checks whether each validation VCF is structurally usable before the complete workflow is run.

The checks may include:

-  

   .. container::

      VCF fileformat declaration

-  

   .. container::

      #CHROM header

-  

   .. container::

      Sample column

-  

   .. container::

      INFO and FORMAT definitions

-  

   .. container::

      Chromosome convention

-  

   .. container::

      Record structure

-  

   .. container::

      Symbolic ALT representation

-  

   .. container::

      Structural endpoint information

-  

   .. container::

      Repeat-expansion representation

-  

   .. container::

      Variant-route compatibility

The output manifest is:

.. code:: bash

   validation/universal_pipeline_testing/manifests/vcf_preflight.tsv

.. _17-7-1-run-structural-preflight:

17.7.1 Run structural preflight
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PREFLIGHT_SCRIPT="pipeline/tests/run_vcf_structural_preflight.sh"
   if [[ ! -s "$PREFLIGHT_SCRIPT" ]]; then
   echo "ERROR: Structural-preflight script is missing."
   exit 1
   fi

bash -n "$PREFLIGHT_SCRIPT"

bash "$PREFLIGHT_SCRIPT"

.. _17-7-2-inspect-the-preflight-manifest:

17.7.2 Inspect the preflight manifest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PREFLIGHT_MANIFEST="validation/universal_pipeline_testing/manifests/vcf_preflight.tsv"
   if [[ ! -s "$PREFLIGHT_MANIFEST" ]]; then
   echo "ERROR: Structural-preflight manifest is missing."
   exit 1
   fi
   column \
   --separator $'\t' \
   --table \
   "$PREFLIGHT_MANIFEST"

The validated project recorded structural-preflight success for all thirteen prepared VCFs.

.. _17-7-3-summarise-preflight-statuses-without-assuming-column-names:

17.7.3 Summarise preflight statuses without assuming column names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   python3 - \
   validation/universal_pipeline_testing/manifests/vcf_preflight.tsv <<'PY'
   from __future__ import annotations
   import csv
   import re
   import sys
   from collections import Counter
   from pathlib import Path
   path = Path(sys.argv[1])
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.DictReader(
   handle,
   delimiter="\t",
   )
   if not reader.fieldnames:
   raise SystemExit("ERROR: Preflight header missing.")
   normalised = {
   re.sub(
   r"[^a-z0-9]+",
   "_",
   column.lower(),
   ).strip("_"): column
   for column in reader.fieldnames
   }
   status_column = None
   for candidate in (
   "status",
   "result",
   "preflight_status",
   "validation_status",
   ):
   if candidate in normalised:
   status_column = normalised[candidate]
   break
   if status_column is None:
   print("Available columns:")
   for column in reader.fieldnames:
   print(f" {column}")
   raise SystemExit(
   "ERROR: No recognisable status column found."
   )
   statuses = Counter(
   row.get(status_column, "").strip() or "<blank>"
   for row in reader
   )
   print(f"Status column: {status_column}")
   for status, count in sorted(statuses.items()):
   print(f"{status}: {count}")
   PY

.. _17-8-targeted-unit-and-regression-tests:

17.8 Targeted unit and regression tests
---------------------------------------

The project uses focused tests for individual behaviours.

+-----------------------------------------+----------------------------------------------+
| **Test**                                | **Behaviour validated**                      |
+=========================================+==============================================+
| 03_test_resource_modes.py               | Production and validation mode selection     |
+-----------------------------------------+----------------------------------------------+
| 04_test_allele_aware_local_pgx.py       | Exact ClinPGx allele matching                |
+-----------------------------------------+----------------------------------------------+
| 05_test_inheritance_models.py           | Inheritance-model compatibility              |
+-----------------------------------------+----------------------------------------------+
| 06_test_sex_ploidy_preflight.py         | Sex-chromosome and ploidy safeguards         |
+-----------------------------------------+----------------------------------------------+
| 07_test_g2p_resource_isolation.py       | Official and validation G2P separation       |
+-----------------------------------------+----------------------------------------------+
| 08_test_compound_heterozygous.py        | Trans, cis, unphased and homozygous handling |
+-----------------------------------------+----------------------------------------------+
| 09_test_exact_hpo_patient_matching.py   | Exact patient-to-HPO association             |
+-----------------------------------------+----------------------------------------------+
| 10_test_g2p_disease_label_precedence.py | G2P disease-label precedence                 |
+-----------------------------------------+----------------------------------------------+
| 11_test_intake_report_preservation.py   | Preservation of intake evidence              |
+-----------------------------------------+----------------------------------------------+

The numbering reflects the committed project test organisation. A test should not be renamed merely for cosmetic consistency because its path may be referenced by documentation or validation procedures.

.. _17-9-production-and-validation-mode-test:

17.9 Production and validation mode test
----------------------------------------

The test is:

.. code:: bash

   pipeline/tests/03_test_resource_modes.py

It confirms that the pipeline recognises the intended analysis modes and selects the corresponding resources.

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/03_test_resource_modes.py

The test must exit with status code zero.

.. _17-10-allele-aware-clinpgx-test:

17.10 Allele-aware ClinPGx test
-------------------------------

The test is:

pipeline/tests/04_test_allele_aware_local_pgx.py

It confirms that:

✓ Exact CHROM-POS-REF-ALT matches are accepted

✓ A different ALT allele is rejected

✓ A shared rsID is not sufficient by itself

✓ Patient genotype is retained

✓ Unmatched variants remain unmatched

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/04_test_allele_aware_local_pgx.py

.. _17-11-inheritance-model-test:

17.11 Inheritance-model test
----------------------------

The test is:

.. code:: bash

   pipeline/tests/05_test_inheritance_models.py

It validates the shared inheritance logic used by later pipeline stages.

The test may cover conceptual cases such as:

-  

   .. container::

      Monoallelic autosomal compatibility

-  

   .. container::

      Biallelic autosomal compatibility

-  

   .. container::

      Single recessive heterozygous candidate

-  

   .. container::

      X-linked hemizygous interpretation

-  

   .. container::

      Mitochondrial handling

-  

   .. container::

      Missing genotype handling

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/05_test_inheritance_models.py

The exact assertions remain authoritative in the test source.

.. _17-12-sex-and-ploidy-preflight-test:

17.12 Sex and ploidy preflight test
-----------------------------------

The test is:

.. code:: bash

   pipeline/tests/06_test_sex_ploidy_preflight.py

It confirms that sex-chromosome records are not interpreted using unrestricted autosomal assumptions.

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/06_test_sex_ploidy_preflight.py

Potential conditions covered include:

-  

   .. container::

      Compatible X-linked genotype

-  

   .. container::

      Unresolved sex

-  

   .. container::

      Unexpected Y-chromosome record

-  

   .. container::

      Haploid or diploid representation

-  

   .. container::

      Mitochondrial ploidy

.. _17-13-g2p-resource-isolation-test:

17.13 G2P resource-isolation test
---------------------------------

The test is:

.. code:: bash

   pipeline/tests/07_test_g2p_resource_isolation.py

It confirms that controlled validation relationships cannot enter production analysis.

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/07_test_g2p_resource_isolation.py

A failure should stop production analysis until the active G2P path is corrected.

.. _17-14-compound-heterozygous-test:

17.14 Compound-heterozygous test
--------------------------------

The test is:

.. code:: bash

   pipeline/tests/08_test_compound_heterozygous.py

It validates:

-  

   .. container::

      Shared phase set

-  

   .. container::

      Opposite haplotypes

-  

   .. container::

      Same-haplotype cis variants

-  

   .. container::

      Unphased possible pairs

-  

   .. container::

      Different phase sets

-  

   .. container::

      Homozygous non-duplication

-  

   .. container::

      Same-gene requirement

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/08_test_compound_heterozygous.py

The test protects against a major inheritance error: incorrectly treating two heterozygous variants as confirmed trans without suitable phase evidence.

.. _17-15-exact-hpo-patient-matching-test:

17.15 Exact HPO patient-matching test
-------------------------------------

The test is:

.. code:: bash

   pipeline/tests/09_test_exact_hpo_patient_matching.py

It confirms that:

patient_01

does not accidentally match:

patient_010

patient_011

patient_012

patient_013

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/09_test_exact_hpo_patient_matching.py

Incorrect HPO association can change candidate ranking without changing any genomic variant, making this a critical regression test.

.. _17-16-g2p-disease-label-precedence-test:

17.16 G2P disease-label precedence test
---------------------------------------

The test is:

.. code:: bash

   pipeline/tests/10_test_g2p_disease_label_precedence.py

It verifies that the controlled G2P disease model remains the principal resolved disease identity where appropriate, while ClinVar condition names remain available as supporting evidence.

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/10_test_g2p_disease_label_precedence.py

This prevents broad or multi-condition ClinVar labels from replacing the intended gene–disease model.

.. _17-17-intake-report-preservation-test:

17.17 Intake-report preservation test
-------------------------------------

The test is:

.. code:: bash

   pipeline/tests/11_test_intake_report_preservation.py

It confirms that the original intake report remains available after case files are copied, routed or prepared.

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/11_test_intake_report_preservation.py

The intake report is part of the provenance record and must not be overwritten by a later report.

.. _17-18-run-the-complete-targeted-python-test-suite:

17.18 Run the complete targeted Python test suite
-------------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   TESTS=(
   pipeline/tests/03_test_resource_modes.py
   pipeline/tests/04_test_allele_aware_local_pgx.py
   pipeline/tests/05_test_inheritance_models.py
   pipeline/tests/06_test_sex_ploidy_preflight.py
   pipeline/tests/07_test_g2p_resource_isolation.py
   pipeline/tests/08_test_compound_heterozygous.py
   pipeline/tests/09_test_exact_hpo_patient_matching.py
   pipeline/tests/10_test_g2p_disease_label_precedence.py
   pipeline/tests/11_test_intake_report_preservation.py
   )
   PASSED=0
   FAILED=0
   for test_script in "${TESTS[@]}"; do
   echo
   echo "============================================================"
   echo "RUNNING: $test_script"
   echo "============================================================"
   if [[ ! -s "$test_script" ]]; then
   echo "FAIL: Test file is missing."
   FAILED=$((FAILED + 1))
   continue
   fi
   if python "$test_script"; then
   echo "PASS: $test_script"
   PASSED=$((PASSED + 1))
   else
   echo "FAIL: $test_script"
   FAILED=$((FAILED + 1))
   fi
   done
   echo
   echo "Tests passed: $PASSED"
   echo "Tests failed: $FAILED"
   if (( FAILED > 0 )); then
   exit 1
   fi
   echo
   echo "PASS: All targeted Python tests completed successfully."

This runner continues through the full list so that all failing tests can be identified in one execution.

.. _17-19-create-a-validation-log:

17.19 Create a validation log
-----------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   VALIDATION_LOG_DIR="validation/logs"
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   VALIDATION_LOG="$VALIDATION_LOG_DIR/targeted_tests_${TIMESTAMP}.log"
   mkdir -p "$VALIDATION_LOG_DIR"
   {
   echo "Validation started UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
   echo "Project root: $(pwd)"
   echo "Git commit: $(git rev-parse HEAD)"
   echo
   TESTS=(
   pipeline/tests/03_test_resource_modes.py
   pipeline/tests/04_test_allele_aware_local_pgx.py
   pipeline/tests/05_test_inheritance_models.py
   pipeline/tests/06_test_sex_ploidy_preflight.py
   pipeline/tests/07_test_g2p_resource_isolation.py
   pipeline/tests/08_test_compound_heterozygous.py
   pipeline/tests/09_test_exact_hpo_patient_matching.py
   pipeline/tests/10_test_g2p_disease_label_precedence.py
   pipeline/tests/11_test_intake_report_preservation.py
   )
   for test_script in "${TESTS[@]}"; do
   echo
   echo "=== $test_script ==="
   python "$test_script"
   done
   echo
   echo "Validation completed UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
   } 2>&1 |

tee "$VALIDATION_LOG"

.. code:: bash

   echo
   echo "Validation log:"
   echo "$VALIDATION_LOG"

Because set -o pipefail is active, a failed Python test causes the complete command to fail even though the output is passed through tee.

.. _17-20-verify-that-testing-did-not-alter-tracked-files:

17.20 Verify that testing did not alter tracked files
-----------------------------------------------------

Compare the working-tree status with the earlier snapshot:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git status --short \
   > /tmp/rare_disease_git_status_after_validation.txt
   if diff -u \
   /tmp/rare_disease_git_status_before_validation.txt \
   /tmp/rare_disease_git_status_after_validation.txt
   then
   echo "PASS: Validation did not change the tracked repository state."
   else
   echo "WARNING: Repository status changed during validation."
   echo "Review every changed file before continuing."
   fi

Inspect changed files:

.. code:: bash

   git status --short

Temporary logs and ignored outputs may be created locally without affecting tracked source files.

.. _17-21-canonical-validation-cases:

17.21 Canonical validation cases
--------------------------------

The final audit records the accepted output for each completed validation case.

The manifest is:

.. code:: bash

   validation/final_audit_20260727/canonical_cases.tsv

The project recognises three output categories:

-  

   .. container::

      CURRENT

-  

   .. container::

      LEGACY

-  

   .. container::

      ROUTED_REPEAT

**CURRENT**

The canonical result was produced through the current universal workflow.

**LEGACY**

The accepted result came from an earlier compatible workflow and remains the canonical output for that case.

**ROUTED_REPEAT**

The case followed the dedicated repeat-expansion route and did not receive ordinary small-variant ranking.

These categories describe output provenance, not clinical classification.

.. _17-22-canonical-patients-01-12-results:

17.22 Canonical Patients 01–12 results
--------------------------------------

The accepted audit targets are:

+-------------+----------------+--------------------------------------------------+
| **Patient** | **Category**   | **Principal result**                             |
+=============+================+==================================================+
| 01          | LEGACY         | CFTR, chr7:117559590:ATCT>A, score 62.96         |
+-------------+----------------+--------------------------------------------------+
| 02          | LEGACY         | HBB, chr11:5227002:T>A, score 29.63              |
+-------------+----------------+--------------------------------------------------+
| 03          | ROUTED_REPEAT  | HTT, CAG repeat record, detected_not_interpreted |
+-------------+----------------+--------------------------------------------------+
| 04          | LEGACY         | BRCA1, chr17:43124027:ACT>A, score 81.48         |
+-------------+----------------+--------------------------------------------------+
| 05          | CURRENT        | HEXA, chr15:72346579:G>GGATA, score 85.19        |
+-------------+----------------+--------------------------------------------------+
| 06          | CURRENT        | PAH, chr12:102840493:G>A, score 66.67            |
+-------------+----------------+--------------------------------------------------+
| 07          | CURRENT        | ATP7B, chr13:51958333:C>A, score 48.15           |
+-------------+----------------+--------------------------------------------------+
| 08          | CURRENT        | APOB, chr2:21006288:C>T, score 70.37             |
+-------------+----------------+--------------------------------------------------+
| 09          | CURRENT        | G6PD, chrX:154536002:C>T, score 59.26            |
+-------------+----------------+--------------------------------------------------+
| 10          | CURRENT        | MEFV, chr16:3243407:T>C, score 77.78             |
+-------------+----------------+--------------------------------------------------+
| 11          | CURRENT        | HFE, chr6:26092913:G>A, score 62.96              |
+-------------+----------------+--------------------------------------------------+
| 12          | CURRENT        | MLH1, chr3:37028902:C>T, score 74.07             |
+-------------+----------------+--------------------------------------------------+

The controlled PGx validation results include:

+-------------+------------------------------------------------------------+
| **Patient** | **PGx result**                                             |
+=============+============================================================+
| 10          | TPMT rs1142345, \*1/\*3C, intermediate metaboliser         |
+-------------+------------------------------------------------------------+
| 11          | CYP2D6 rs3892097, \*1/\*4, intermediate metaboliser        |
+-------------+------------------------------------------------------------+
| 12          | DPYD rs3918290, \*1/\*2A, intermediate metaboliser         |
+-------------+------------------------------------------------------------+

Patient 09’s final audit records the PGx branch as not applicable.

.. _17-23-patient-03-repeat-expansion-validation:

17.23 Patient 03 repeat-expansion validation
--------------------------------------------

Patient 03 validates routing rather than ordinary candidate scoring.

The accepted result includes:

Canonical case:

patient_03_huntington_disease

Gene:

HTT

Variant:

chr4:3074877:N><CAG_EXPANSION>

Reported count:

45

Controlled threshold:

40

Genotype:

0/1

Status:

detected_not_interpreted

The audit confirms that the record:

✓ Was detected

✓ Was preserved

✓ Was routed to a repeat report

✓ Was excluded from ordinary ranking

✓ Requires specialist repeat analysis

The audit does not claim independent read-level confirmation.

.. _17-24-patient-13-status:

17.24 Patient 13 status
-----------------------

Patient 13:

✓ Had a prepared validation VCF

✓ Passed structural preflight

✗ Was not executed through the complete final workflow

The reason was the project timeframe, not a structural-input failure.

.. _17-25-final-audit-files:

17.25 Final audit files
-----------------------

The final audit directory contains four main evidence types.

.. _17-25-1-canonical-case-definitions:

17.25.1 Canonical case definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

canonical_cases.tsv

Defines the accepted candidate, score or route for each audited case.

.. _17-25-2-canonical-output-checksums:

17.25.2 Canonical output checksums
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

canonical_final_outputs.sha256

Confirms that the accepted output files have not changed.

.. _17-25-3-key-resource-checksums:

17.25.3 Key-resource checksums
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

key_resources.sha256

Confirms that the compact resources used by the validated project remain unchanged.

.. _17-25-4-pipeline-source-checksums:

17.25.4 Pipeline-source checksums
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pipeline_source.sha256

Confirms that the source files responsible for the validated behaviour remain unchanged.

.. _17-26-verify-the-final-audit-files-exist:

17.26 Verify the final audit files exist
----------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   AUDIT_DIR="validation/final_audit_20260727"
   REQUIRED_FILES=(
   "$AUDIT_DIR/canonical_cases.tsv"
   "$AUDIT_DIR/canonical_final_outputs.sha256"
   "$AUDIT_DIR/key_resources.sha256"
   "$AUDIT_DIR/pipeline_source.sha256"
   "$AUDIT_DIR/FINAL_VALIDATION_STATUS.md"
   "$AUDIT_DIR/scripts/audit_patients_01_12_final.py"
   )
   FAILURES=0
   for path in "${REQUIRED_FILES[@]}"; do
   if [[ -s "$path" ]]; then
   printf "PASS %s\n" "$path"
   else
   printf "FAIL %s\n" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo
   echo "ERROR: $FAILURES final-audit file(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: Final-audit files are present."

.. _17-27-inspect-the-canonical-case-manifest:

17.27 Inspect the canonical case manifest
-----------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   column \
   --separator $'\t' \
   --table \
   validation/final_audit_20260727/canonical_cases.tsv

The table should be treated as the authoritative mapping between each patient and its accepted output.

.. _17-28-verify-the-canonical-output-checksums:

17.28 Verify the canonical output checksums
-------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sha256sum \
   --check \
   validation/final_audit_20260727/canonical_final_outputs.sha256

A failure means that at least one accepted output has changed, moved or become unavailable.

Do not regenerate the checksum immediately. First determine why the file differs.

.. _17-29-verify-the-key-resource-checksums:

17.29 Verify the key-resource checksums
---------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sha256sum \
   --check \
   validation/final_audit_20260727/key_resources.sha256

A resource-checksum failure may result from:

-  

   .. container::

      Intentional resource update

-  

   .. container::

      Accidental file modification

-  

   .. container::

      Line-ending conversion

-  

   .. container::

      File corruption

-  

   .. container::

      Incorrect project root

-  

   .. container::

      Different file path

Any intentional resource update requires a complete regression rerun before new checksums are accepted.

.. _17-30-verify-the-pipeline-source-checksums:

17.30 Verify the pipeline-source checksums
------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sha256sum \
   --check \
   validation/final_audit_20260727/pipeline_source.sha256

A source-checksum failure means that the previous final audit no longer proves the behaviour of the current source tree.

Even a small source edit can change:

-  matching;

-  routing;

-  scoring;

-  output columns;

-  sorting;

-  status labels;

-  resource selection.

.. _17-31-run-the-final-audit-script:

17.31 Run the final audit script
--------------------------------

The final audit script is:

.. code:: bash

   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   AUDIT_SCRIPT="validation/final_audit_20260727/scripts/audit_patients_01_12_final.py"
   python -m py_compile "$AUDIT_SCRIPT"
   python "$AUDIT_SCRIPT"

The script checks the canonical Patients 01–12 results according to the accepted output category for each case.

.. _17-32-inspect-the-final-validation-status:

17.32 Inspect the final validation status
-----------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   STATUS_FILE="validation/final_audit_20260727/FINAL_VALIDATION_STATUS.md"
   if [[ ! -s "$STATUS_FILE" ]]; then
   echo "ERROR: Final validation status file is missing."
   exit 1
   fi
   cat "$STATUS_FILE"

The accepted final audit recorded:

Audited cases: 12

Passed cases: 12

Failed cases: 0

This result applies to the source, resources and outputs represented by the associated checksum manifests.

.. _17-33-complete-final-audit-command:

17.33 Complete final-audit command
----------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   AUDIT_DIR="validation/final_audit_20260727"
   echo "=== 1. Source syntax ==="
   python -m py_compile \
   "$AUDIT_DIR/scripts/audit_patients_01_12_final.py"
   echo
   echo "=== 2. Canonical output checksums ==="
   sha256sum \
   --check \
   "$AUDIT_DIR/canonical_final_outputs.sha256"
   echo
   echo "=== 3. Key-resource checksums ==="
   sha256sum \
   --check \
   "$AUDIT_DIR/key_resources.sha256"
   echo
   echo "=== 4. Pipeline-source checksums ==="
   sha256sum \
   --check \
   "$AUDIT_DIR/pipeline_source.sha256"
   echo
   echo "=== 5. Patient audit ==="
   python \
   "$AUDIT_DIR/scripts/audit_patients_01_12_final.py"
   echo
   echo "=== 6. Final validation status ==="
   cat \
   "$AUDIT_DIR/FINAL_VALIDATION_STATUS.md"
   echo
   echo "PASS: Complete final audit finished successfully."

This is the principal final validation command for the accepted project state.

.. _17-34-what-constitutes-a-passing-case:

17.34 What constitutes a passing case
-------------------------------------

A case passes the final audit when the required canonical conditions are satisfied.

For a scored small-variant case, this may include:

-  

   .. container::

      Expected candidate exists

-  

   .. container::

      Expected CHROM-POS-REF-ALT key matches

-  

   .. container::

      Expected gene matches

-  

   .. container::

      Expected score matches

-  

   .. container::

      Expected output category matches

-  

   .. container::

      Required output file is readable

-  

   .. container::

      For a repeat case, this may include:

-  

   .. container::

      Repeat record exists

-  

   .. container::

      Expected locus or gene matches

-  

   .. container::

      Expected route status matches

-  

   .. container::

      Record is excluded from ordinary ranking

-  

   .. container::

      Specialist follow-up status is preserved

-  

   .. container::

      For a PGx validation case, additional checks may include:

-  

   .. container::

      Expected PGx variant exists

-  

   .. container::

      Exact allele matches

-  

   .. container::

      Expected genotype is retained

-  

   .. container::

      Expected project diplotype matches

-  

   .. container::

      Expected functional phenotype matches

The exact assertions are defined in the final audit script and canonical case manifest.

.. _17-35-what-does-not-constitute-a-pass:

17.35 What does not constitute a pass
-------------------------------------

A case should not be marked as passed merely because:

-  

   .. container::

      The pipeline exited with status zero

-  

   .. container::

      A result directory exists

-  

   .. container::

      The expected gene appears somewhere

-  

   .. container::

      The expected rsID appears somewhere

-  

   .. container::

      A high score was produced

-  

   .. container::

      One annotation tool matched

-  

   .. container::

      A previous output file is still present

The audit must verify the expected candidate and relevant evidence fields.

A successful process can still produce an incorrect result.

.. _17-36-regression-testing-after-a-source-code-change:

17.36 Regression testing after a source-code change
---------------------------------------------------

After modifying source code:

1.  Record the changed files.

2.  Run Python and Bash syntax checks.

3.  Run the targeted test related to the change.

4.  Run the complete targeted test suite.

5.  Run VCF structural preflight.

6.  Rerun affected synthetic cases.

7.  Compare the new outputs with canonical results.

8.  Run the final audit.

9.  Investigate every difference.

10. Update canonical outputs only after deliberate review.

Inspect changed source files:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git diff \
   --name-only \
   -- pipeline validation

Inspect the actual changes:

.. code:: bash

   git diff \
   -- pipeline validation

Do not accept a source change solely because it corrects one case. It must not break other supported cases.

.. _17-37-regression-testing-after-a-resource-update:

17.37 Regression testing after a resource update
------------------------------------------------

A resource update may include:

-  

   .. container::

      New ClinVar release

-  

   .. container::

      Updated G2P file

-  

   .. container::

      New HPO release

-  

   .. container::

      New MONDO release

-  

   .. container::

      Updated ClinGen dosage data

-  

   .. container::

      Changed local ClinPGx reference

-  

   .. container::

      New VEP cache

-  

   .. container::

      Changed SnpEff database

After a resource update:

1. Preserve the previous resource.

2. Record the previous checksum.

3. Install the new resource separately.

4. Record the new release and checksum.

5. Validate the resource structure.

6. Run targeted unit tests.

7. Rerun Patients 01–12.

8. Compare candidate identities and scores.

9. Explain all changed evidence.

10. Create a new dated audit only after approval.

A resource update can legitimately change results without a source-code change.

.. _17-38-regression-testing-after-a-scoring-change:

17.38 Regression testing after a scoring change
-----------------------------------------------

Scoring changes require especially careful review because they may reorder candidates without changing their annotations.

After changing scoring logic:

✓ Compile the scoring scripts

✓ Record their new checksums

✓ Run inheritance and phenotype tests

✓ Run ClinVar calibration checks

✓ Run CNV scoring checks

✓ Rerun every completed validation case

✓ Compare top candidate and rank

✓ Compare individual score components

✓ Confirm deterministic ordering

✓ Review all score changes

Do not simply change the expected canonical scores to match new output.

The reason for each changed score must be documented.

.. _17-39-structured-comparison-of-old-and-new-outputs:

17.39 Structured comparison of old and new outputs
--------------------------------------------------

A byte-level checksum comparison is useful, but it may detect harmless changes such as timestamps.

A structured comparison should examine fields including:

-  

   .. container::

      candidate key

-  

   .. container::

      gene

-  

   .. container::

      resolved disease

-  

   .. container::

      score

-  

   .. container::

      rank

-  

   .. container::

      ClinVar classification

-  

   .. container::

      phenotype score

-  

   .. container::

      inheritance status

-  

   .. container::

      compound-heterozygous status

-  

   .. container::

      route status

-  

   .. container::

      ClinPGx match

A generic TSV comparison can begin with:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   OLD_OUTPUT="path/to/canonical_output.tsv"
   NEW_OUTPUT="path/to/new_output.tsv"
   for path in "$OLD_OUTPUT" "$NEW_OUTPUT"; do
   if [[ ! -s "$path" ]]; then
   echo "ERROR: Missing comparison file: $path"
   exit 1
   fi
   done
   diff -u \
   "$OLD_OUTPUT" \
   "$NEW_OUTPUT" \
   || true

The placeholder paths must be replaced with the actual outputs being compared.

.. _17-40-compare-checksums-before-field-level-review:

17.40 Compare checksums before field-level review
-------------------------------------------------

.. code:: bash

   OLD_SHA256="$(
   sha256sum "$OLD_OUTPUT" |
   awk '{print $1}'
   )"
   NEW_SHA256="$(
   sha256sum "$NEW_OUTPUT" |
   awk '{print $1}'
   )"
   echo "Old: $OLD_SHA256"
   echo "New: $NEW_SHA256"
   if [[ "$OLD_SHA256" == "$NEW_SHA256" ]]; then
   echo "PASS: Outputs are byte-for-byte identical."
   else
   echo "NOTICE: Output files differ."
   echo "Proceed to field-level comparison."
   fi

A checksum difference should not be ignored even when the top candidate remains unchanged.

.. _17-41-validation-failure-investigation:

17.41 Validation failure investigation
--------------------------------------

When a test or audit fails, investigate in this order:

1. Confirm that the correct project root is active.

2. Confirm the input checksum.

3. Confirm the source-code checksum.

4. Confirm the resource mode.

5. Confirm the resource checksums.

6. Confirm tool and container versions.

7. Read the failing test message.

8. Inspect the affected intermediate file.

9. Compare with the canonical output.

10. Determine whether the change is intentional.

Do not immediately modify:

-  

   .. container::

      Expected test values

-  

   .. container::

      Canonical scores

-  

   .. container::

      Checksums

-  

   .. container::

      Validation relationships

to remove the failure.

A failing test is evidence that the current state differs from the validated state.

.. _17-42-preserve-failed-run-evidence:

17.42 Preserve failed-run evidence
----------------------------------

A failed run should preserve:

-  

   .. container::

      Case identifier

-  

   .. container::

      Input checksum

-  

   .. container::

      Pipeline commit

-  

   .. container::

      Resource mode

-  

   .. container::

      Tool versions

-  

   .. container::

      Stage name

-  

   .. container::

      Exit status

-  

   .. container::

      Standard output

-  

   .. container::

      Standard error

-  

   .. container::

      Partial outputs

-  

   .. container::

      Failure timestamp

A useful local structure is:

results/failed_runs/

└── <case_id>\_<timestamp>/

├── context/

├── logs/

├── partial_outputs/

└── failure_manifest.tsv

Failed outputs must not replace the last successful canonical output.

.. _17-43-distinguish-expected-failure-from-regression-failure:

17.43 Distinguish expected failure from regression failure
----------------------------------------------------------

Some tests may deliberately supply invalid data to verify that the pipeline rejects it.

An expected failure means:

-  

   .. container::

      The test supplied invalid or incompatible input

.. container::

   and the pipeline rejected it correctly.

A regression failure means:

The software no longer behaves according

to the expected rule.

A test script may therefore pass when an internal command correctly fails.

The final success criterion is the test script’s exit status, not whether every command inside the test succeeded.

.. _17-44-validation-mode-isolation:

17.44 Validation-mode isolation
-------------------------------

Controlled validation relationships are useful for synthetic cases, but they must never enter production analysis.

The audit should confirm:

-  

   .. container::

      Production mode uses AllG2P.official.csv

-  

   .. container::

      Validation mode uses the controlled validation resource

-  

   .. container::

      The active mode is recorded

-  

   .. container::

      Local validation entries remain labelled

Production outputs do not depend on validation-only records

Run both resource tests together:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python pipeline/tests/03_test_resource_modes.py
   python pipeline/tests/07_test_g2p_resource_isolation.py
   echo "PASS: Resource-mode isolation confirmed."

.. _17-45-validation-of-exact-allele-matching:

17.45 Validation of exact allele matching
-----------------------------------------

A correct allele-aware test should include at least:

-  

   .. container::

      Positive control:

Exact chromosome, position, REF and ALT

-  

   .. container::

      Negative control:

Same rsID but different ALT

-  

   .. container::

      Negative control:

Same position but different REF

-  

   .. container::

      Negative control:

Different genome coordinate

-  

   .. container::

      Genotype control:

Locus present but alternate allele not carried

The committed test remains authoritative for the implemented controls.

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/04_test_allele_aware_local_pgx.py

.. _17-46-validation-of-phase-logic:

17.46 Validation of phase logic
-------------------------------

A complete compound-heterozygous regression test should distinguish:

``0|1`` and ``1|0`` with shared PS:

phased trans

``0|1`` and ``0|1`` with shared PS:

cis

0/1 and 0/1:

possible unphased pair

``0|1`` and ``1|0`` with different PS values:

phase unresolved

1/1:

homozygous biallelic, not compound heterozygous

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \

pipeline/tests/08_test_compound_heterozygous.py

.. _17-47-validation-of-repeat-routing:

17.47 Validation of repeat routing
----------------------------------

Repeat routing can be checked through:

-  

   .. container::

      Patient 03 validation VCF

-  

   .. container::

      Repeat-report output

-  

   .. container::

      Canonical case manifest

-  

   .. container::

      Final validation status

Search the audit files:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   grep -RInE \
   'patient.?03|HTT|CAG|detected_not_interpreted|ROUTED_REPEAT' \
   validation/final_audit_20260727 \
   || true

Confirm that the repeat record is not treated as an ordinary scored SNV.

.. _17-48-validate-the-final-audit-script-itself:

17.48 Validate the final audit script itself
--------------------------------------------

The audit script is part of the validated source and should be reviewed like any other program.

Compile it:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python -m py_compile \
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py

Inspect its candidate and score checks:

.. code:: bash

   grep -nE \
   'patient|candidate|gene|score|PASS|FAIL|ROUTED_REPEAT|LEGACY|CURRENT' \
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py \
   | head -n 200

The script should not be modified after a failure unless the expected validation design itself has been deliberately revised.

.. _17-49-create-a-dated-validation-snapshot:

17.49 Create a dated validation snapshot
----------------------------------------

After a fully successful new validation cycle, create a separate dated directory instead of overwriting the previous final audit.

Example:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   DATE_TAG="$(
   date -u '+%Y%m%d'
   )"
   NEW_AUDIT_DIR="validation/final_audit_${DATE_TAG}"
   if [[ -e "$NEW_AUDIT_DIR" ]]; then
   echo "ERROR: Audit directory already exists:"
   echo "$NEW_AUDIT_DIR"
   exit 1
   fi
   mkdir -p \
   "$NEW_AUDIT_DIR/scripts"

Copy only deliberately approved audit materials.

The previous audit should remain unchanged for historical comparison.

.. _17-50-validation-report-contents:

17.50 Validation report contents
--------------------------------

A final validation report should document:

-  

   .. container::

      Validation date

-  

   .. container::

      Pipeline commit

-  

   .. container::

      Test environment

-  

   .. container::

      Input cases

-  

   .. container::

      Input checksums

-  

   .. container::

      Resource mode

-  

   .. container::

      Resource versions

-  

   .. container::

      Container checksums

-  

   .. container::

      Tests executed

-  

   .. container::

      Structural-preflight result

-  

   .. container::

      Case-level expected results

-  

   .. container::

      Case-level observed results

-  

   .. container::

      Failures

-  

   .. container::

      Warnings

-  

   .. container::

      Skipped cases

-  

   .. container::

      Repeat-route result

-  

   .. container::

      ClinPGx controls

-  

   .. container::

      Final pass count

-  

   .. container::

      Limitations

The report should state clearly that:

Patient 13 was not run through the complete pipeline.

It should not be silently omitted.

.. _17-51-validation-limitations:

17.51 Validation limitations
----------------------------

The completed validation demonstrates that the pipeline behaves correctly for the implemented synthetic scenarios.

It does not establish:

-  

   .. container::

      Clinical sensitivity

-  

   .. container::

      Clinical specificity

-  

   .. container::

      Diagnostic yield

-  

   .. container::

      Performance across all variant classes

-  

   .. container::

      Performance across all ancestries

-  

   .. container::

      Complete star-allele resolution

-  

   .. container::

      Complete repeat-expansion detection

-  

   .. container::

      Complete mitochondrial interpretation

-  

   .. container::

      Complete mosaicism detection

-  

   .. container::

      Complete complex-SV interpretation

-  

   .. container::

      Regulatory approval

The validation data were deliberately constructed to test known pipeline functions.

Real-world validation would require:

-  larger reference datasets;

-  independently characterised variants;

-  blinded analysis;

-  orthogonal confirmation;

-  clinical review;

-  defined performance metrics.

.. _17-52-remove-python-cache-files-after-validation:

17.52 Remove Python cache files after validation
------------------------------------------------

Display cache files:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find \
   pipeline \
   validation \
   -type d \
   -name '__pycache__' \
   -print
   find \
   pipeline \
   validation \
   -type f \
   -name '*.pyc' \
   -print

Remove them:

.. code:: bash

   find \
   pipeline \
   validation \
   -type d \
   -name '__pycache__' \
   -prune \
   -exec rm -rf {} +
   find \
   pipeline \
   validation \
   -type f \
   -name '*.pyc' \
   -delete

These generated cache files are not part of the validated source.

.. _17-53-clean-temporary-validation-snapshots:

17.53 Clean temporary validation snapshots
------------------------------------------

Remove the temporary Git-status files:

.. code:: bash

   rm -f \
   /tmp/rare_disease_git_status_before_validation.txt \
   /tmp/rare_disease_git_status_after_validation.txt \
   /tmp/rare_disease_commit_before_validation.txt

Do not remove:

-  

   .. container::

      canonical case files

-  

   .. container::

      audit checksums

-  

   .. container::

      validation logs

-  

   .. container::

      expected outputs

-  

   .. container::

      final status documents

.. _17-54-complete-validation-readiness-command:

17.54 Complete validation readiness command
-------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   echo "=== Structural preflight ==="
   bash \
   pipeline/tests/run_vcf_structural_preflight.sh
   echo
   echo "=== Targeted regression tests ==="
   TESTS=(
   pipeline/tests/03_test_resource_modes.py
   pipeline/tests/04_test_allele_aware_local_pgx.py
   pipeline/tests/05_test_inheritance_models.py
   pipeline/tests/06_test_sex_ploidy_preflight.py
   pipeline/tests/07_test_g2p_resource_isolation.py
   pipeline/tests/08_test_compound_heterozygous.py
   pipeline/tests/09_test_exact_hpo_patient_matching.py
   pipeline/tests/10_test_g2p_disease_label_precedence.py
   pipeline/tests/11_test_intake_report_preservation.py
   )
   for test_script in "${TESTS[@]}"; do
   echo
   echo "Running: $test_script"
   python "$test_script"
   done
   echo
   echo "=== Canonical-output checksums ==="
   sha256sum \
   --check \
   validation/final_audit_20260727/canonical_final_outputs.sha256
   echo
   echo "=== Key-resource checksums ==="
   sha256sum \
   --check \
   validation/final_audit_20260727/key_resources.sha256
   echo
   echo "=== Pipeline-source checksums ==="
   sha256sum \
   --check \
   validation/final_audit_20260727/pipeline_source.sha256
   echo
   echo "=== Final Patients 01–12 audit ==="
   python \
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py
   echo
   echo "=== Final status ==="
   cat \
   validation/final_audit_20260727/FINAL_VALIDATION_STATUS.md
   echo
   echo "PASS: Complete validation and final audit succeeded."

This command verifies the accepted project state without rerunning every annotation tool.

A full reproducibility rerun would additionally execute the complete universal pipeline for the validation cases.

.. _17-55-final-validation-checklist:

17.55 Final validation checklist
--------------------------------

The validation process is complete when:

✓ Pipeline Bash files pass syntax validation

✓ Pipeline Python files pass syntax validation

✓ All thirteen prepared VCFs pass structural preflight

✓ Production and validation modes remain distinct

✓ Validation-only G2P relationships cannot enter production

✓ Local ClinPGx matching remains allele-aware

✓ rsID-only false matches are rejected

✓ Inheritance models are interpreted consistently

✓ Sex and ploidy preflight passes

✓ X-linked and mitochondrial contexts remain distinct

✓ Compound-heterozygous trans, cis and unphased states are distinguished

✓ Homozygous variants are not duplicated into pairs

✓ HPO files use exact patient matching

✓ G2P disease-label precedence is preserved

✓ Original intake reports remain preserved

✓ Repeat expansions follow the routed-repeat branch

✓ Patient 03 retains detected_not_interpreted status

✓ PGx validation cases produce the expected project results

✓ Canonical output checksums pass

✓ Key-resource checksums pass

✓ Pipeline-source checksums pass

✓ Patients 01–12 pass the final audit

✓ Patient 13 remains explicitly documented as not executed

✓ Validation failures are investigated rather than hidden

✓ Old audit snapshots remain preserved

✓ Validation limitations are reported honestly

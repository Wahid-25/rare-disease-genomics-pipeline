.. _18-end-to-end-case-execution-command-line-usage-and-safe-processing-of-a-new-cas:

18. End-to-End Case Execution, Command-Line Usage and Safe Processing of a New Case
===================================================================================


This section describes how to submit a new GRCh38 VCF and phenotype file to the complete universal pipeline.

The project provides two main case launchers:

.. code:: bash

   pipeline/run_real_patient_case.sh
   pipeline/run_case_pipeline.sh

Their purposes are different:

+--------------------------+-------------------------------------------------------------------------------------------------------+
| **Launcher**             | **Intended use**                                                                                      |
+==========================+=======================================================================================================+
| run_real_patient_case.sh | External or newly received VCF requiring intake, sample selection, build confirmation and preparation |
+--------------------------+-------------------------------------------------------------------------------------------------------+
| run_case_pipeline.sh     | Already prepared GRCh38 case containing a known patient sample and valid phenotype file               |
+--------------------------+-------------------------------------------------------------------------------------------------------+

The external-case wrapper is the safer entry point for a newly received VCF. It performs intake checks before allowing the annotation workflow to begin.

The committed wrapper accepts a case identifier, VCF and phenotype file, with optional --sample, --confirm-grch38 and --force arguments. It also recognises the THREADS and JAVA_MEM environment variables.

.. _18-1-overall-end-to-end-execution:

18.1 Overall end-to-end execution
---------------------------------

A newly received case follows this sequence:

External GRCh38 VCF

+

Patient HPO file

│

▼

Universal external-case intake

│

▼

Sample-count and genotype evaluation

│

▼

Genome-build confirmation

│

▼

Patient-input preparation

│

▼

Removal of incompatible existing annotations

│

▼

Universal case pipeline

│

├── Small-variant branch

├── CNV branch

├── Repeat-expansion route

├── Unsupported-SV route

└── ClinPGx branch

│

▼

Candidate scoring and master-table generation

│

▼

Readiness and completion summaries

│

▼

Case-level interpretation and manual review

The wrapper stops before annotation when the VCF is unsuitable for full patient analysis.

.. _18-2-selecting-the-correct-launcher:

18.2 Selecting the correct launcher
-----------------------------------

.. _18-2-1-use-run-real-patient-case-sh-when:

18.2.1 Use run_real_patient_case.sh when
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the external-case wrapper when:

-  

   .. container::

      The VCF has just been received

-  

   .. container::

      The VCF may contain several samples

-  

   .. container::

      The genome build may not be declared

-  

   .. container::

      The VCF may already contain annotations

-  

   .. container::

      The input has not yet been placed in the project

-  

   .. container::

      The VCF structure has not been assessed

-  

   .. container::

      The case requires a permanent intake report

The command interface is:

.. code:: bash

   bash pipeline/run_real_patient_case.sh \
   CASE_ID INPUT_VCF PHENOTYPE_FILE \
   [--sample SAMPLE_NAME] \
   [--confirm-grch38] \
   [--force]

.. _18-2-2-use-run-case-pipeline-sh-when:

18.2.2 Use run_case_pipeline.sh when
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the direct case launcher only when:

-  

   .. container::

      The VCF is already known to use GRCh38

-  

   .. container::

      The intended patient sample has already been selected

-  

   .. container::

      The VCF contains usable patient genotypes

-  

   .. container::

      The phenotype file is valid

-  

   .. container::

      No external-intake gate is needed

Its interface is:

.. code:: bash

   bash pipeline/run_case_pipeline.sh \
   CASE_ID \
   INPUT_VCF \
   PHENOTYPE_FILE \
   [--force]

The launcher stages the VCF and phenotype file, accepts only .vcf or .vcf.gz, creates the case result directories and refuses to replace existing results unless --force is supplied.

.. _18-2-3-do-not-use-the-legacy-launcher-for-a-new-universal-case:

18.2.3 Do not use the legacy launcher for a new universal case
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The older script:

.. code:: bash

   pipeline/run_rare_disease_pipeline.sh

belongs to the earlier disease-specific workflow.

It should not be used as the main entry point for a newly received universal case.

.. _18-3-inspect-the-current-launcher-interfaces:

18.3 Inspect the current launcher interfaces
--------------------------------------------

Before the first execution on a newly installed system, display the current usage text:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail

bash pipeline/run_real_patient_case.sh --help

.. code:: bash

   echo
   echo "============================================================"
   echo

bash pipeline/run_case_pipeline.sh

run_case_pipeline.sh prints its usage when the required arguments are absent.

Validate both scripts:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail

bash -n pipeline/run_real_patient_case.sh

bash -n pipeline/run_case_pipeline.sh

.. code:: bash

   echo "PASS: Main case launchers passed Bash syntax validation."

.. _18-4-pre-run-project-checks:

18.4 Pre-run project checks
---------------------------

Move to the project root:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail

Activate the Python environment:

.. code:: bash

   if [[ ! -x .venv/bin/python ]]; then
   echo "ERROR: Project Python environment is missing."
   exit 1
   fi
   source .venv/bin/activate
   python --version

Confirm the main commands:

.. code:: bash

   REQUIRED_COMMANDS=(
   bash
   python
   apptainer
   bcftools
   bgzip
   tabix
   sha256sum
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
   echo "ERROR: $FAILURES required command(s) are unavailable."
   exit 1
   fi

.. _18-5-confirm-essential-containers-and-resources:

18.5 Confirm essential containers and resources
-----------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   REQUIRED_PATHS=(
   containers/core_tools.sif
   containers/vep.sif
   containers/snpeff.sif
   containers/spliceai.sif
   containers/isv.sif
   resources/reference/hg38.fa
   resources/reference/hg38.fa.fai
   resources/vep_cache
   resources/snpeff_data
   resources/clinvar/clinvar.vcf.gz
   resources/clinvar/clinvar.vcf.gz.tbi
   resources/clingen/clingen_dosage_genes_regions.csv
   resources/gene_disease/g2p
   resources/phenotype/hpo
   resources/disease_ontology/mondo
   resources/clinpgx/local_curated_pgx_reference.csv
   tools/ClassifyCNV/ClassifyCNV.py
   )
   FAILURES=0
   for path in "${REQUIRED_PATHS[@]}"; do
   if [[ -e "$path" ]]; then
   printf "PASS %s\n" "$path"
   else
   printf "FAIL %s\n" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo
   echo "ERROR: $FAILURES required component(s) are missing."
   exit 1
   fi

.. _18-6-confirm-production-resource-isolation:

18.6 Confirm production-resource isolation
------------------------------------------

Before processing an external case, confirm that validation-only resources cannot enter production analysis:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python pipeline/tests/03_test_resource_modes.py
   python pipeline/tests/07_test_g2p_resource_isolation.py
   echo
   echo "PASS: Production and validation resource isolation confirmed."

A production case must not be used to test synthetic local disease relationships.

.. _18-7-choose-a-safe-case-identifier:

18.7 Choose a safe case identifier
----------------------------------

The case identifier may contain:

-  

   .. container::

      Letters

-  

   .. container::

      Numbers

-  

   .. container::

      Dots

-  

   .. container::

      Underscores

-  

   .. container::

      Hyphens

-  

   .. container::

      A safe example is:

-  

   .. container::

      case_001

-  

   .. container::

      Do not include:

-  

   .. container::

      Patient name

-  

   .. container::

      Hospital number

-  

   .. container::

      Date of birth

-  

   .. container::

      National identity number

-  

   .. container::

      Telephone number

-  

   .. container::

      Email address

Set the identifier:

CASE_ID="case_001"

Validate it:

.. code:: bash

   if [[ ! "$CASE_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
   echo "ERROR: Invalid case identifier: $CASE_ID"
   exit 1
   fi
   echo "PASS: Safe case identifier: $CASE_ID"

The launcher applies the same character restriction.

.. _18-8-define-the-source-vcf-and-phenotype-file:

18.8 Define the source VCF and phenotype file
---------------------------------------------

Use absolute paths to the files received from the source:

.. code:: bash

   SOURCE_VCF="/absolute/path/to/case_001.raw.vcf.gz"
   HPO_FILE="/absolute/path/to/case_001.phenotypes.txt"

Check both:

.. code:: bash

   for path in \
   "$SOURCE_VCF" \
   "$HPO_FILE"
   do
   if [[ ! -s "$path" ]]; then
   echo "ERROR: Missing or empty input file:"
   echo "$path"
   exit 1
   fi
   done
   echo "PASS: Source VCF and phenotype file are present."

The external source files should remain outside the generated result directory so that they cannot be removed by a forced rerun.

.. _18-9-record-source-file-checksums-before-execution:

18.9 Record source-file checksums before execution
--------------------------------------------------

.. code:: bash

   SOURCE_MANIFEST="/tmp/${CASE_ID}.source_inputs.sha256"
   sha256sum \
   "$SOURCE_VCF" \
   "$HPO_FILE" \
   > "$SOURCE_MANIFEST"
   cat "$SOURCE_MANIFEST"

Store a permanent copy in a secure local location after the case directory is created.

The checksum proves exactly which files were supplied to the pipeline.

.. _18-10-validate-the-phenotype-file:

18.10 Validate the phenotype file
---------------------------------

The phenotype file should contain one HPO identifier per line:

-  

   .. container::

      HP:0001250

-  

   .. container::

      HP:0001263

-  

   .. container::

      HP:0004322

Validate it:

.. code:: bash

   python3 - "$HPO_FILE" <<'PY'
   from __future__ import annotations
   import re
   import sys
   from pathlib import Path
   path = Path(sys.argv[1])
   pattern = re.compile(r"^HP:\d{7}$")
   if not path.is_file() or path.stat().st_size == 0:
   raise SystemExit(f"ERROR: Missing or empty HPO file: {path}")
   valid_terms: list[str] = []
   invalid_lines: list[tuple[int, str]] = []
   for line_number, raw_line in enumerate(
   path.read_text(
   encoding="utf-8-sig"
   ).splitlines(),
   start=1,
   ):
   line = raw_line.strip()
   if not line or line.startswith("#"):
   continue
   if pattern.fullmatch(line):
   valid_terms.append(line)
   else:
   invalid_lines.append(
   (
   line_number,
   line,
   )
   )
   if invalid_lines:
   print("ERROR: Invalid phenotype entries:")
   for line_number, value in invalid_lines:
   print(
   f" line {line_number}: {value!r}"
   )
   raise SystemExit(1)
   if not valid_terms:
   raise SystemExit(
   "ERROR: No valid HP:####### terms were found."
   )
   print(f"PASS: {len(valid_terms)} HPO term(s) validated.")
   print(f"Unique terms: {len(set(valid_terms))}")
   PY

The HPO file should describe observed clinical features, not a suspected diagnosis written as free text.

.. _18-11-inspect-the-vcf-before-execution:

18.11 Inspect the VCF before execution
--------------------------------------

Confirm that bcftools can parse it:

.. code:: bash

   bcftools view \
   --output-type v \
   --output /dev/null \
   "$SOURCE_VCF"
   echo "PASS: VCF is structurally readable by bcftools."

Display the file-format line:

.. code:: bash

   bcftools view \
   --header-only \
   "$SOURCE_VCF" |
   head -n 1

Display sample names:

.. code:: bash

   bcftools query \
   --list-samples \
   "$SOURCE_VCF"

Count samples:

.. code:: bash

   SAMPLE_COUNT="$(
   bcftools query \
   --list-samples \
   "$SOURCE_VCF" |
   sed '/^$/d' |
   wc -l
   )"
   echo "Sample count: $SAMPLE_COUNT"

Count records:

.. code:: bash

   RECORD_COUNT="$(
   bcftools view \
   --no-header \
   "$SOURCE_VCF" |
   wc -l
   )"
   echo "VCF records: $RECORD_COUNT"
   if (( RECORD_COUNT == 0 )); then
   echo "ERROR: The VCF contains no variant records."
   exit 1
   fi

.. _18-12-inspect-available-genotype-information:

18.12 Inspect available genotype information
--------------------------------------------

.. code:: bash

   echo "=== FORMAT fields ==="
   bcftools view \
   --header-only \
   "$SOURCE_VCF" |
   grep '^##FORMAT=' \
   || true
   echo
   echo "=== First genotype records ==="
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT[\t%SAMPLE=%GT]\n' \
   "$SOURCE_VCF" |
   head -n 20

A sites-only VCF without samples cannot support full patient-level inheritance or ClinPGx interpretation.

The external wrapper explicitly rejects a site-only database VCF and an annotation-only VCF without usable alternate genotypes. It also blocks wrong-build, empty and malformed sample-column inputs.

.. _18-13-inspect-genome-build-evidence:

18.13 Inspect genome-build evidence
-----------------------------------

Search the header:

.. code:: bash

   bcftools view \
   --header-only \
   "$SOURCE_VCF" |
   grep -Ei \
   'reference=|assembly=|GRCh38|hg38|GRCh37|hg19' \
   || true

The build should be confirmed from:

-  

   .. container::

      VCF header

-  

   .. container::

      Variant-caller report

-  

   .. container::

      Sequencing provider

-  

   .. container::

      Known coordinates

-  

   .. container::

      Reference-allele compatibility

-  

   .. container::

      Source metadata

Do not use --confirm-grch38 merely because the chromosome names begin with chr.

That option records an independent confirmation. It does not convert GRCh37 to GRCh38.

The wrapper rejects a known non-GRCh38 file and explicitly states that silent liftover is not permitted.

.. _18-14-run-a-single-sample-case-with-declared-grch38:

18.14 Run a single-sample case with declared GRCh38
---------------------------------------------------

When the VCF contains one patient sample and its GRCh38 build is declared:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   SOURCE_VCF="/absolute/path/to/case_001.raw.vcf.gz"
   HPO_FILE="/absolute/path/to/case_001.phenotypes.txt"
   THREADS=4 \
   JAVA_MEM=8g \
   bash pipeline/run_real_patient_case.sh \
   "$CASE_ID" \
   "$SOURCE_VCF" \
   "$HPO_FILE"

The default values are:

.. code:: bash

   THREADS=4
   JAVA_MEM=8g

They may be changed according to the system’s available resources.

.. _18-15-run-a-case-whose-header-does-not-declare-grch38:

18.15 Run a case whose header does not declare GRCh38
-----------------------------------------------------

First confirm the build independently.

Then run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   SOURCE_VCF="/absolute/path/to/case_001.raw.vcf.gz"
   HPO_FILE="/absolute/path/to/case_001.phenotypes.txt"
   THREADS=4 \
   JAVA_MEM=8g \
   bash pipeline/run_real_patient_case.sh \
   "$CASE_ID" \
   "$SOURCE_VCF" \
   "$HPO_FILE" \
   --confirm-grch38
   --confirm-grch38 means:

The analyst independently confirmed that

the submitted coordinates use GRCh38.

It does not mean:

The pipeline guessed the build

or automatically performed liftover.

.. _18-16-run-a-multisample-vcf:

18.16 Run a multisample VCF
---------------------------

List the available samples:

.. code:: bash

   bcftools query \
   --list-samples \
   "$SOURCE_VCF"

Set the exact patient sample:

.. code:: bash

   SAMPLE_NAME="PATIENT_SAMPLE"

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   SOURCE_VCF="/absolute/path/to/case_001.multisample.vcf.gz"
   HPO_FILE="/absolute/path/to/case_001.phenotypes.txt"
   SAMPLE_NAME="PATIENT_SAMPLE"
   THREADS=4 \
   JAVA_MEM=8g \
   bash pipeline/run_real_patient_case.sh \
   "$CASE_ID" \
   "$SOURCE_VCF" \
   "$HPO_FILE" \
   --sample "$SAMPLE_NAME"

When the build also requires independent confirmation:

.. code:: bash

   THREADS=4 \
   JAVA_MEM=8g \
   bash pipeline/run_real_patient_case.sh \
   "$CASE_ID" \
   "$SOURCE_VCF" \
   "$HPO_FILE" \
   --sample "$SAMPLE_NAME" \
   --confirm-grch38

The wrapper stops a multisample VCF when no sample has been selected.

.. _18-17-what-the-external-case-wrapper-performs:

18.17 What the external-case wrapper performs
---------------------------------------------

The external wrapper begins by creating a permanent intake report and classifying the input VCF.

It checks states including:

-  

   .. container::

      READY_FOR_PREPARATION_AND_FULL_PIPELINE

-  

   .. container::

      READY_AFTER_EXISTING_ANNOTATION_CLEANUP

-  

   .. container::

      NEEDS_EXPLICIT_SAMPLE_SELECTION

-  

   .. container::

      NEEDS_GENOME_BUILD_CONFIRMATION

-  

   .. container::

      ANNOTATION_ONLY_NO_USABLE_GENOTYPES

-  

   .. container::

      NOT_A_PATIENT_VCF_NO_SAMPLES

-  

   .. container::

      NOT_READY_WRONG_GENOME_BUILD

-  

   .. container::

      NOT_READY_EMPTY_VCF

-  

   .. container::

      NOT_READY_INCONSISTENT_SAMPLE_COLUMNS

-  

   .. container::

      MULTISAMPLE_WITHOUT_USABLE_GENOTYPES

Only an eligible input passes the intake gate.

The wrapper then performs controlled preparation and calls the universal case pipeline. Its first stage records the input status, detected build, sample count, usable genotypes and existing annotation tags before annotation begins.

.. _18-18-prepared-external-case-files:

18.18 Prepared external-case files
----------------------------------

After successful preparation, files are stored under:

input/cases/<case_id>/

Important prepared files may include:

-  

   .. container::

      prepared/<case_id>.ready.vcf.gz

-  

   .. container::

      prepared/<case_id>.ready.vcf.gz.tbi

-  

   .. container::

      prepared/phenotypes.ready.txt

-  

   .. container::

      prepared/<case_id>.preparation_report.tsv

-  

   .. container::

      prepared/<case_id>.readiness.tsv

-  

   .. container::

      prepared/<case_id>.reannotation_ready.vcf.gz

-  

   .. container::

      prepared/<case_id>.annotation_cleanup_report.tsv

The intake evidence should remain in a separate intake location so that preparation with --force cannot delete it. The project’s regression test checks that the wrapper uses:

.. code:: bash

   input/cases/<case_id>/intake/

for the preserved external VCF intake report.

Locate the files:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   find \
   "input/cases/$CASE_ID" \
   -maxdepth 3 \
   -type f \
   -printf '%s\t%p\n' |
   sort -k2,2

.. _18-19-direct-execution-of-an-already-prepared-case:

18.19 Direct execution of an already prepared case
--------------------------------------------------

For a controlled case that is already known to contain:

-  

   .. container::

      GRCh38 coordinates

-  

   .. container::

      One intended patient sample

-  

   .. container::

      Usable genotypes

-  

   .. container::

      Valid HPO terms

-  

   .. container::

      No unresolved intake problem

run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   INPUT_VCF="/absolute/path/to/prepared.case.vcf.gz"
   HPO_FILE="/absolute/path/to/phenotypes.txt"
   THREADS=4 \
   JAVA_MEM=8g \
   bash pipeline/run_case_pipeline.sh \
   "$CASE_ID" \
   "$INPUT_VCF" \
   "$HPO_FILE"

The direct launcher stages its own copies under:

.. code:: bash

   input/cases/<case_id>/staged/

and creates:

-  

   .. container::

      results/cases/<case_id>/work/

-  

   .. container::

      results/cases/<case_id>/annotated/

-  

   .. container::

      results/cases/<case_id>/clinpgx/

-  

   .. container::

      results/cases/<case_id>/cnv/

-  

   .. container::

      results/cases/<case_id>/logs/

-  

   .. container::

      results/cases/<case_id>/final/

It also writes a case pipeline log and summary.

.. _18-20-result-overwrite-protection:

18.20 Result overwrite protection
---------------------------------

Both principal launchers protect existing results.

Without --force, a repeated case identifier causes execution to stop.

This prevents accidental deletion of:

-  

   .. container::

      Previous annotations

-  

   .. container::

      Master candidate tables

-  

   .. container::

      CNV outputs

-  

   .. container::

      ClinPGx results

-  

   .. container::

      Logs

-  

   .. container::

      Manifests

-  

   .. container::

      Final reports

Before a forced rerun, inspect the existing case:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   find \
   "input/cases/$CASE_ID" \
   "results/cases/$CASE_ID" \
   -type f \
   -printf '%s\t%p\n' \
   2>/dev/null |
   sort -k2,2

.. _18-21-create-a-backup-before-force:

18.21 Create a backup before --force
------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   BACKUP_ROOT="$PWD/local_case_archives"
   BACKUP_FILE="$BACKUP_ROOT/${CASE_ID}_${TIMESTAMP}.tar.gz"
   mkdir -p "$BACKUP_ROOT"
   ARCHIVE_PATHS=()
   if [[ -d "input/cases/$CASE_ID" ]]; then
   ARCHIVE_PATHS+=(
   "input/cases/$CASE_ID"
   )
   fi
   if [[ -d "results/cases/$CASE_ID" ]]; then
   ARCHIVE_PATHS+=(
   "results/cases/$CASE_ID"
   )
   fi
   if (( ${#ARCHIVE_PATHS[@]} == 0 )); then
   echo "ERROR: No existing case files were found."
   exit 1
   fi
   tar \
   --create \
   --gzip \
   --file "$BACKUP_FILE" \
   "${ARCHIVE_PATHS[@]}"
   sha256sum \
   "$BACKUP_FILE" \
   > "${BACKUP_FILE}.sha256"
   sha256sum \
   --check \
   "${BACKUP_FILE}.sha256"
   echo
   echo "Backup:"
   echo "$BACKUP_FILE"

Keep this archive local. It may contain sensitive genomic data.

.. _18-22-perform-a-forced-rerun:

18.22 Perform a forced rerun
----------------------------

For an external case:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   SOURCE_VCF="/absolute/path/to/case_001.raw.vcf.gz"
   HPO_FILE="/absolute/path/to/case_001.phenotypes.txt"
   THREADS=4 \
   JAVA_MEM=8g \
   bash pipeline/run_real_patient_case.sh \
   "$CASE_ID" \
   "$SOURCE_VCF" \
   "$HPO_FILE" \
   --force

For a multisample case:

.. code:: bash

   THREADS=4 \
   JAVA_MEM=8g \
   bash pipeline/run_real_patient_case.sh \
   "$CASE_ID" \
   "$SOURCE_VCF" \
   "$HPO_FILE" \
   --sample "$SAMPLE_NAME" \
   --force

For the direct case launcher:

.. code:: bash

   THREADS=4 \
   JAVA_MEM=8g \
   bash pipeline/run_case_pipeline.sh \
   "$CASE_ID" \
   "$INPUT_VCF" \
   "$HPO_FILE" \
   --force

--force should be used only after a backup and deliberate review.

.. _18-23-monitoring-an-active-execution:

18.23 Monitoring an active execution
------------------------------------

The launchers write logs automatically.

Locate the current logs:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   find \
   "input/cases/$CASE_ID" \
   "results/cases/$CASE_ID/logs" \
   -type f \
   \( -name '*.log' -o -name '*.txt' \) \
   -printf '%T@\t%p\n' \
   2>/dev/null |
   sort -nr |
   head -n 20

Follow the main case-pipeline log:

.. code:: bash

   CASE_LOG="results/cases/$CASE_ID/logs/${CASE_ID}.case_pipeline.log"
   if [[ -f "$CASE_LOG" ]]; then
   tail -f "$CASE_LOG"
   else
   echo "Case pipeline log has not been created yet."
   fi

Press:

Ctrl+C

to stop following the log. This does not stop the pipeline itself when the pipeline is running in another terminal.

.. _18-24-monitor-resource-consumption:

18.24 Monitor resource consumption
----------------------------------

In another terminal:

.. code:: bash

   watch -n 5 '
   echo "=== MEMORY ==="
   free -h
   echo
   echo "=== DISK ==="
   df -h ~/rare_disease_project
   echo
   echo "=== PROCESSES ==="
   ps -eo pid,etimes,%cpu,%mem,cmd \
   --sort=-%cpu |
   head -n 15
   '

A long VEP, SpliceAI, AnnotSV or ISV-CNV step may remain active without printing frequent terminal output.

.. _18-25-expected-result-directory:

18.25 Expected result directory
-------------------------------

The main case result root is:

.. code:: bash

   results/cases/<case_id>/

The direct case launcher creates:

-  

   .. container::

      work/

-  

   .. container::

      annotated/

-  

   .. container::

      clinpgx/

-  

   .. container::

      cnv/

-  

   .. container::

      logs/

-  

   .. container::

      final/

Inspect the completed case:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   find \
   "results/cases/$CASE_ID" \
   -maxdepth 3 \
   -type f \
   -printf '%s\t%p\n' |
   sort -k2,2

.. _18-26-pipeline-summary:

18.26 Pipeline summary
----------------------

The direct launcher writes:

.. code:: bash

   results/cases/<case_id>/final/<case_id>.pipeline_summary.tsv

The summary records fields including:

-  

   .. container::

      case_id

-  

   .. container::

      assembly

-  

   .. container::

      input_vcf

-  

   .. container::

      input_vcf_sha256

-  

   .. container::

      phenotype_file

-  

   .. container::

      phenotype_sha256

-  

   .. container::

      small_variant_records

-  

   .. container::

      cnv_records

-  

   .. container::

      other_structural_variants

-  

   .. container::

      small_variant_branch_status

-  

   .. container::

      cnv_branch_status

-  

   .. container::

      clinpgx_status

-  

   .. container::

      top_candidate_type

-  

   .. container::

      top_gene

-  

   .. container::

      top_disease

-  

   .. container::

      top_variant

-  

   .. container::

      top_normalized_score

-  

   .. container::

      top_priority

-  

   .. container::

      master_table

-  

   .. container::

      pipeline_log

The launcher prints the top candidate, master table, summary file and log after successful completion.

Inspect:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   SUMMARY="results/cases/$CASE_ID/final/${CASE_ID}.pipeline_summary.tsv"
   if [[ ! -s "$SUMMARY" ]]; then
   echo "ERROR: Pipeline summary is missing."
   exit 1
   fi
   column \
   --separator $'\t' \
   --table \
   "$SUMMARY"

.. _18-27-read-selected-summary-values:

18.27 Read selected summary values
----------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   SUMMARY="results/cases/$CASE_ID/final/${CASE_ID}.pipeline_summary.tsv"

summary_value() {

local key="$1"

.. code:: bash

   awk \
   -F '\t' \
   -v requested="$key" \
   '
   $1 == requested {
   gsub(/\r/, "", $2)
   print $2
   exit
   }
   ' \
   "$SUMMARY"
   }
   echo "Case: $(summary_value case_id)"
   echo "Assembly: $(summary_value assembly)"
   echo "Small variants: $(summary_value small_variant_records)"
   echo "CNVs: $(summary_value cnv_records)"
   echo "Other SVs: $(summary_value other_structural_variants)"
   echo "Small branch: $(summary_value small_variant_branch_status)"
   echo "CNV branch: $(summary_value cnv_branch_status)"
   echo "ClinPGx: $(summary_value clinpgx_status)"
   echo "Top type: $(summary_value top_candidate_type)"
   echo "Top gene: $(summary_value top_gene)"
   echo "Top disease: $(summary_value top_disease)"
   echo "Top variant: $(summary_value top_variant)"
   echo "Top score: $(summary_value top_normalized_score)"
   echo "Priority: $(summary_value top_priority)"
   echo "Master table: $(summary_value master_table)"
   echo "Pipeline log: $(summary_value pipeline_log)"

.. _18-28-locate-and-inspect-the-master-table:

18.28 Locate and inspect the master table
-----------------------------------------

Read the path from the pipeline summary:

.. code:: bash

   MASTER_REL="$(
   awk \
   -F '\t' \
   '$1 == "master_table" {
   gsub(/\r/, "", $2)
   print $2
   exit
   }' \
   "$SUMMARY"
   )"
   if [[ -z "$MASTER_REL" ]]; then
   echo "ERROR: Master-table path is absent from the summary."
   exit 1
   fi
   case "$MASTER_REL" in
   /*)
   MASTER_TABLE="$MASTER_REL"
   ;;
   *)
   MASTER_TABLE="$PWD/$MASTER_REL"
   ;;
   esac
   if [[ ! -s "$MASTER_TABLE" ]]; then
   echo "ERROR: Master table is missing:"
   echo "$MASTER_TABLE"
   exit 1
   fi
   echo "Master table:"
   echo "$MASTER_TABLE"

Display its first rows:

.. code:: bash

   column \
   --separator $'\t' \
   --table \
   "$MASTER_TABLE" |
   head -n 20

The first row is the highest-priority supported candidate, not an automatically confirmed diagnosis.

.. _18-29-confirm-branch-routing-outputs:

18.29 Confirm branch-routing outputs
------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   FINAL_DIR="results/cases/$CASE_ID/final"
   WORK_DIR="results/cases/$CASE_ID/work"
   echo "=== Routing reports ==="
   find \
   "$FINAL_DIR" \
   -maxdepth 1 \
   -type f \
   \( \
   -iname '*routing*' \
   -o -iname '*repeat*' \
   -o -iname '*unsupported*' \
   \) \
   -print |

sort

.. code:: bash

   echo
   echo "=== Routed working files ==="
   find \
   "$WORK_DIR" \
   -maxdepth 1 \
   -type f \
   \( \
   -iname '*small*' \
   -o -iname '*cnv*' \
   -o -iname '*structural*' \
   \) \
   -print |

sort

Review all routes, even when the small-variant branch produced a strong top candidate.

.. _18-30-confirm-annotation-outputs:

18.30 Confirm annotation outputs
--------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   ANNOTATED_DIR="results/cases/$CASE_ID/annotated"
   find \
   "$ANNOTATED_DIR" \
   -type f \
   -printf '%s\t%p\n' |
   sort -k2,2

Search for the main annotations:

.. code:: bash

   find \
   "$ANNOTATED_DIR" \
   -type f \
   \( \
   -iname '*vep*' \
   -o -iname '*snpeff*' \
   -o -iname '*clinvar*' \
   -o -iname '*spliceai*' \
   \) \
   -print |

sort

.. _18-31-confirm-cnv-output-conditionally:

18.31 Confirm CNV output conditionally
--------------------------------------

Read the CNV branch status:

.. code:: bash

   CNV_STATUS="$(
   awk \
   -F '\t' \
   '$1 == "cnv_branch_status" {
   gsub(/\r/, "", $2)
   print $2
   exit
   }' \
   "$SUMMARY"
   )"
   echo "CNV branch status: $CNV_STATUS"

When the branch was required, inspect:

.. code:: bash

   find \
   "results/cases/$CASE_ID/cnv" \
   -type f \
   -printf '%s\t%p\n' |
   sort -k2,2

A case with no supported DEL or DUP records should not be failed merely because AnnotSV, ClassifyCNV and ISV-CNV were not applicable.

.. _18-32-confirm-clinpgx-output:

18.32 Confirm ClinPGx output
----------------------------

.. code:: bash

   find \
   "results/cases/$CASE_ID/clinpgx" \
   -type f \
   -printf '%s\t%p\n' \
   2>/dev/null |
   sort -k2,2

A missing or warning ClinPGx stage should not invalidate the rare-disease ranking automatically. The launcher treats ClinPGx as contextual and allows disease prioritisation to continue while recording a warning when matching fails.

.. _18-33-verify-important-output-files-are-not-empty:

18.33 Verify important output files are not empty
-------------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   CASE_RESULTS="results/cases/$CASE_ID"
   EMPTY_FILES="$(
   find \
   "$CASE_RESULTS" \
   -type f \
   -size 0 \
   -print
   )"
   if [[ -n "$EMPTY_FILES" ]]; then
   echo "WARNING: Zero-byte files detected:"
   echo "$EMPTY_FILES"
   else
   echo "PASS: No zero-byte case output files detected."
   fi

Some explicit zero-record branch outputs may contain only a header, but they should not be completely empty.

.. _18-34-search-logs-for-failure-indicators:

18.34 Search logs for failure indicators
----------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   LOG_DIR="results/cases/$CASE_ID/logs"
   FAILURE_TEXT="$(
   grep -RInE \
   --include='*.log' \
   --include='*.txt' \
   'Traceback|FATAL|CASE PIPELINE FAILED|REAL-PATIENT PIPELINE FAILED|command not found|No such file' \
   "$LOG_DIR" \
   "input/cases/$CASE_ID" \
   2>/dev/null \
   || true
   )"
   if [[ -n "$FAILURE_TEXT" ]]; then
   echo "Potential failure indicators:"
   echo "$FAILURE_TEXT"
   else
   echo "No obvious fatal failure indicators were found."
   fi

The launchers use error traps that report:

-  

   .. container::

      Failed line

-  

   .. container::

      Exit status

-  

   .. container::

      Relevant log path

A failed stage should not be represented as a completed case.

.. _18-35-generate-a-post-run-case-checksum-manifest:

18.35 Generate a post-run case checksum manifest
------------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   CASE_RESULTS="results/cases/$CASE_ID"
   MANIFEST_DIR="$CASE_RESULTS/manifests"
   OUTPUT_HASHES="$MANIFEST_DIR/generated_outputs.sha256"
   mkdir -p "$MANIFEST_DIR"
   find \
   "$CASE_RESULTS" \
   -type f \
   ! -path "$OUTPUT_HASHES" \
   ! -name '*.tmp' \
   ! -name '*.lock' \
   -print0 |
   sort -z |
   xargs -0 sha256sum \
   > "$OUTPUT_HASHES"
   sha256sum \
   --check \
   "$OUTPUT_HASHES"

This manifest allows later verification that the case results have not changed.

.. _18-36-preserve-a-case-completion-record:

18.36 Preserve a case-completion record
---------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   CASE_RESULTS="results/cases/$CASE_ID"
   COMPLETION_RECORD="$CASE_RESULTS/final/${CASE_ID}.completion_record.tsv"
   SUMMARY="$CASE_RESULTS/final/${CASE_ID}.pipeline_summary.tsv"
   {
   printf 'field\tvalue\n'
   printf 'case_id\t%s\n' "$CASE_ID"
   printf 'completion_record_created_utc\t%s\n' \
   "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
   printf 'pipeline_commit\t%s\n' \
   "$(git rev-parse HEAD 2>/dev/null || echo unavailable)"
   printf 'pipeline_summary\t%s\n' "$SUMMARY"
   printf 'pipeline_summary_sha256\t%s\n' \
   "$(sha256sum "$SUMMARY" | awk '{print $1}')"
   printf 'source_vcf\t%s\n' "$SOURCE_VCF"
   printf 'source_vcf_sha256\t%s\n' \
   "$(sha256sum "$SOURCE_VCF" | awk '{print $1}')"
   printf 'phenotype_file\t%s\n' "$HPO_FILE"
   printf 'phenotype_sha256\t%s\n' \
   "$(sha256sum "$HPO_FILE" | awk '{print $1}')"
   } > "$COMPLETION_RECORD"
   column \
   --separator $'\t' \
   --table \
   "$COMPLETION_RECORD"

This record should remain local when it contains absolute paths to sensitive source files.

.. _18-37-safe-failure-recovery:

18.37 Safe failure recovery
---------------------------

When the workflow fails:

-  

   .. container::

      Do not run --force immediately

-  

   .. container::

      Do not delete the result directory

-  

   .. container::

      Do not edit the original VCF

-  

   .. container::

      Do not alter expected resource files

-  

   .. container::

      Do not suppress the error message

First inspect:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   find \
   "input/cases/$CASE_ID" \
   "results/cases/$CASE_ID" \
   -type f \
   -printf '%T@\t%s\t%p\n' \
   2>/dev/null |
   sort -nr |
   head -n 50

Display the end of all recent logs:

.. code:: bash

   find \
   "input/cases/$CASE_ID" \
   "results/cases/$CASE_ID/logs" \
   -type f \
   -name '*.log' \
   -print0 \
   2>/dev/null |
   while IFS= read -r -d '' log_file; do
   echo
   echo "============================================================"
   echo "$log_file"
   echo "============================================================"
   tail -n 50 "$log_file"
   done

Identify the first failed stage before rerunning.

.. _18-38-common-intake-failures:

18.38 Common intake failures
----------------------------

+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+
| **Intake status or error**             | **Meaning**                                                | **Required response**                                 |
+========================================+============================================================+=======================================================+
| NEEDS_EXPLICIT_SAMPLE_SELECTION        | More than one sample is present                            | Rerun with --sample                                   |
+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+
| NEEDS_GENOME_BUILD_CONFIRMATION        | Build could not be established                             | Confirm independently, then use --confirm-grch38      |
+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+
| ANNOTATION_ONLY_NO_USABLE_GENOTYPES    | No usable alternate sample genotypes                       | Do not perform full inheritance analysis              |
+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+
| NOT_A_PATIENT_VCF_NO_SAMPLES           | Sites-only VCF                                             | Obtain a patient-level VCF                            |
+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+
| NOT_READY_WRONG_GENOME_BUILD           | File is not GRCh38                                         | Do not silently process it                            |
+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+
| NOT_READY_EMPTY_VCF                    | No usable records                                          | Recover a valid source file                           |
+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+
| NOT_READY_INCONSISTENT_SAMPLE_COLUMNS  | Body columns do not match the VCF header                   | Repair or re-export the VCF                           |
+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+
| MULTISAMPLE_WITHOUT_USABLE_GENOTYPES   | Samples exist but none provide a usable alternate genotype | Review the caller output                              |
+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+
| Existing results                       | Case identifier already used                               | Inspect the existing result or back up before --force |
+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+
| Invalid case identifier                | Unsafe characters                                          | Use letters, numbers, dots, underscores or hyphens    |
+----------------------------------------+------------------------------------------------------------+-------------------------------------------------------+

.. _18-39-safe-interpretation-after-completion:

18.39 Safe interpretation after completion
------------------------------------------

After successful execution, review the output in this order:

1. External intake report

2. Preparation report

3. Readiness report

4. Variant-routing QC

5. Pipeline summary

6. Master candidate table

7. Detailed small-variant evidence

8. CNV outputs

9. Repeat-expansion report

10. Unsupported-variant report

11. Inheritance evidence

12. ClinPGx results

13. Logs and warnings

14. Reproducibility manifest and checksums

Do not begin only with the top score.

A repeat expansion or unsupported structural variant may be clinically important while having no ordinary numerical rank.

.. _18-40-real-case-privacy-protection:

18.40 Real-case privacy protection
----------------------------------

Real or externally supplied case data must remain local.

Do not commit:

-  

   .. container::

      input/cases/<case_id>/

-  

   .. container::

      results/cases/<case_id>/

-  

   .. container::

      raw or prepared VCFs

-  

   .. container::

      patient HPO files

-  

   .. container::

      intake reports

-  

   .. container::

      case logs

-  

   .. container::

      master candidate tables

-  

   .. container::

      human-readable patient reports

Check Git status:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git status --short

Confirm that the case is ignored:

.. code:: bash

   CASE_ID="case_001"
   git check-ignore -v \
   "input/cases/$CASE_ID" \
   "results/cases/$CASE_ID" \
   || true

Search staged files:

.. code:: bash

   git diff \
   --cached \
   --name-only |
   grep -E \
   '(^|/)(input/cases|results/cases)/' \
   || true

Any matching case file must be removed from the staging area before a commit.

.. _18-41-local-case-archiving:

18.41 Local case archiving
--------------------------

After all outputs have been verified, create a secure local archive:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   ARCHIVE_DIR="$PWD/local_case_archives"
   ARCHIVE="$ARCHIVE_DIR/${CASE_ID}_completed_${TIMESTAMP}.tar.gz"
   mkdir -p "$ARCHIVE_DIR"
   tar \
   --create \
   --gzip \
   --file "$ARCHIVE" \
   "input/cases/$CASE_ID" \
   "results/cases/$CASE_ID"
   sha256sum \
   "$ARCHIVE" \
   > "${ARCHIVE}.sha256"
   sha256sum \
   --check \
   "${ARCHIVE}.sha256"
   echo
   echo "Completed case archive:"
   echo "$ARCHIVE"

The archive should be stored only in a secure approved location.

.. _18-42-complete-copy-and-run-template-for-a-new-external-case:

18.42 Complete copy-and-run template for a new external case
------------------------------------------------------------

The following block performs preliminary validation and then launches the external-case wrapper.

Edit only the values at the beginning:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail

# ============================================================

# EDIT THESE VALUES

# ============================================================

.. code:: bash

   CASE_ID="case_001"
   SOURCE_VCF="/absolute/path/to/case_001.raw.vcf.gz"
   HPO_FILE="/absolute/path/to/case_001.phenotypes.txt"
   THREADS_VALUE="4"
   JAVA_MEM_VALUE="8g"
   SELECTED_SAMPLE=""
   CONFIRM_GRCH38="no"
   FORCE_RERUN="no"

# ============================================================

# DO NOT EDIT BELOW THIS LINE

# ============================================================

.. code:: bash

   if [[ ! "$CASE_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
   echo "ERROR: Invalid CASE_ID: $CASE_ID"
   exit 1
   fi
   for path in \
   "$SOURCE_VCF" \
   "$HPO_FILE"
   do
   if [[ ! -s "$path" ]]; then
   echo "ERROR: Missing or empty input:"
   echo "$path"
   exit 1
   fi
   done
   case "$SOURCE_VCF" in
   *.vcf|*.vcf.gz)
   ;;
   *)
   echo "ERROR: Input must end in .vcf or .vcf.gz"
   exit 1
   ;;
   esac
   bcftools view \
   --output-type v \
   --output /dev/null \
   "$SOURCE_VCF"
   HPO_FAILURES="$(
   awk '
   /^[[:space:]]*$/ {
   next
   }
   /^[[:space:]]*#/ {
   next
   }
   !/^HP:[0-9]{7}[[:space:]]*$/ {
   print NR ":" $0
   }
   ' "$HPO_FILE"

)"

.. code:: bash

   if [[ -n "$HPO_FAILURES" ]]; then
   echo "ERROR: Invalid HPO lines:"
   echo "$HPO_FAILURES"
   exit 1
   fi
   COMMAND=(
   bash
   pipeline/run_real_patient_case.sh
   "$CASE_ID"
   "$SOURCE_VCF"
   "$HPO_FILE"
   )
   if [[ -n "$SELECTED_SAMPLE" ]]; then
   COMMAND+=(
   --sample
   "$SELECTED_SAMPLE"
   )
   fi
   case "$CONFIRM_GRCH38" in
   yes)
   COMMAND+=(
   --confirm-grch38
   )
   ;;
   no)
   ;;
   *)
   echo "ERROR: CONFIRM_GRCH38 must be yes or no."
   exit 1
   ;;
   esac
   case "$FORCE_RERUN" in
   yes)
   COMMAND+=(
   --force
   )
   ;;
   no)
   ;;
   *)
   echo "ERROR: FORCE_RERUN must be yes or no."
   exit 1
   ;;
   esac
   echo "========================================"
   echo "NEW CASE EXECUTION"
   echo "========================================"
   echo "Case ID: $CASE_ID"
   echo "VCF: $SOURCE_VCF"
   echo "HPO file: $HPO_FILE"
   echo "Selected sample: ${SELECTED_SAMPLE:-automatic single sample}"
   echo "Confirm GRCh38: $CONFIRM_GRCH38"
   echo "Force rerun: $FORCE_RERUN"
   echo "Threads: $THREADS_VALUE"
   echo "Java memory: $JAVA_MEM_VALUE"
   echo
   THREADS="$THREADS_VALUE" \
   JAVA_MEM="$JAVA_MEM_VALUE" \
   "${COMMAND[@]}"
   echo
   echo "PASS: Launcher exited successfully."

The command does not automatically set --confirm-grch38. That decision must remain deliberate.

.. _18-43-post-run-verification-template:

18.43 Post-run verification template
------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   CASE_INPUT="input/cases/$CASE_ID"
   CASE_RESULTS="results/cases/$CASE_ID"
   SUMMARY="$CASE_RESULTS/final/${CASE_ID}.pipeline_summary.tsv"
   PIPELINE_LOG="$CASE_RESULTS/logs/${CASE_ID}.case_pipeline.log"
   REQUIRED_PATHS=(
   "$CASE_INPUT"
   "$CASE_RESULTS"
   "$SUMMARY"
   "$PIPELINE_LOG"
   )
   FAILURES=0
   for path in "${REQUIRED_PATHS[@]}"; do
   if [[ -e "$path" && ( -d "$path" || -s "$path" ) ]]; then
   printf "PASS %s\n" "$path"
   else
   printf "FAIL %s\n" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo
   echo "ERROR: $FAILURES required case component(s) are missing."
   exit 1
   fi
   echo
   echo "=== PIPELINE SUMMARY ==="
   column \
   --separator $'\t' \
   --table \
   "$SUMMARY"
   echo
   echo "=== ZERO-BYTE OUTPUT CHECK ==="
   ZERO_BYTE_FILES="$(
   find \
   "$CASE_RESULTS" \
   -type f \
   -size 0 \
   -print
   )"
   if [[ -n "$ZERO_BYTE_FILES" ]]; then
   echo "WARNING: Empty output files:"
   echo "$ZERO_BYTE_FILES"
   else
   echo "PASS: No zero-byte outputs detected."
   fi
   echo
   echo "=== FAILURE-TEXT SCREENING ==="
   FAILURE_TEXT="$(
   grep -RInE \
   'CASE PIPELINE FAILED|REAL-PATIENT PIPELINE FAILED|Traceback|FATAL' \
   "$CASE_INPUT" \
   "$CASE_RESULTS" \
   2>/dev/null \
   || true
   )"
   if [[ -n "$FAILURE_TEXT" ]]; then
   echo "WARNING: Failure-related text found:"
   echo "$FAILURE_TEXT"
   else
   echo "PASS: No obvious fatal failure text found."
   fi
   echo
   echo "PASS: Initial post-run verification completed."

.. _18-44-end-to-end-execution-completion-criteria:

18.44 End-to-end execution completion criteria
----------------------------------------------

A new-case execution is complete when:

✓ A non-identifying case identifier was used

✓ The source VCF and HPO file were preserved

✓ Source checksums were recorded

✓ The VCF was structurally readable

✓ The intended sample was selected

✓ The genome build was confirmed as GRCh38

✓ --confirm-grch38 was used only when independently justified

✓ The HPO file contained valid identifiers

✓ Production and validation resources remained isolated

✓ The external intake gate passed

✓ The intake report was preserved separately

✓ Prepared VCF and phenotype files were created

✓ Existing annotations were handled explicitly

✓ Variant classes were routed correctly

✓ Required small-variant and CNV branches completed

✓ Repeat and unsupported records remained visible

✓ ClinPGx status was recorded separately

✓ Pipeline summary was created

✓ Master candidate table was created

✓ Top candidate fields were populated where applicable

✓ Logs contained no unresolved fatal failure

✓ Empty branches were not confused with failed branches

✓ Important outputs were checksummed

✓ A backup was created before any forced rerun

✓ Sensitive case files remained outside GitHub

✓ Automated rankings were subjected to manual review

✓ No clinical diagnosis or treatment decision was issued automatically

.. _19-troubleshooting-failure-recovery-resource-maintenance-and-safe-pipeline-updat:

19. Troubleshooting, Failure Recovery, Resource Maintenance and Safe Pipeline Updates
=====================================================================================


Troubleshooting must protect the integrity of the original case, previously validated outputs and universal pipeline behaviour.

The project follows four central rules:

1. Never edit the original patient VCF to hide an error.

2. Never replace a validated output before preserving it.

3. Never introduce a patient-specific pipeline exception.

4. Never update canonical checksums merely to make a failure disappear.

The troubleshooting process is:

Pipeline warning or failure

│

▼

Preserve logs and partial outputs

│

▼

Identify the first failing stage

│

▼

Classify the failure

│

├── Input or case-context problem

├── Environment or dependency problem

├── Resource problem

├── Tool-execution problem

├── Pipeline source-code problem

└── Interpretation or output problem

│

▼

Correct the underlying universal cause

│

▼

Run targeted regression tests

│

▼

Rerun the affected case safely

│

▼

Run the complete validation suite

│

▼

Document the correction

A successful rerun is not sufficient by itself. The correction must also preserve the expected behaviour of other supported cases.

.. _19-1-first-response-to-a-failure:

19.1 First response to a failure
--------------------------------

When the pipeline fails, do not immediately use --force.

First preserve the current state:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   FAILURE_ARCHIVE_ROOT="$PWD/local_case_archives/failed_runs"
   FAILURE_ARCHIVE="$FAILURE_ARCHIVE_ROOT/${CASE_ID}_failure_${TIMESTAMP}.tar.gz"
   mkdir -p "$FAILURE_ARCHIVE_ROOT"
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
   echo "ERROR: No case input or result directory was found."
   exit 1
   fi
   tar \
   --create \
   --gzip \
   --file "$FAILURE_ARCHIVE" \
   "${ARCHIVE_PATHS[@]}"
   sha256sum \
   "$FAILURE_ARCHIVE" \
   > "${FAILURE_ARCHIVE}.sha256"
   sha256sum \
   --check \
   "${FAILURE_ARCHIVE}.sha256"
   echo
   echo "Failure snapshot:"
   echo "$FAILURE_ARCHIVE"

The archive should remain local because it may contain sensitive genomic or phenotype information.

.. _19-2-identify-the-first-failed-stage:

19.2 Identify the first failed stage
------------------------------------

A later error may be caused by an earlier missing or malformed output.

For example:

Missing master table

↓

Scoring stage failed

↓

Phenotype table was missing

↓

The wrong HPO file was selected

The first underlying failure must be corrected.

List logs by modification time:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   find \
   "input/cases/$CASE_ID" \
   "results/cases/$CASE_ID" \
   -type f \
   \( \
   -name '*.log' \
   -o -name '*.txt' \
   -o -name '*.stderr' \
   -o -name '*.stdout' \
   \) \
   -printf '%T@\t%s\t%p\n' \
   2>/dev/null |
   sort -nr |
   head -n 50

Display the end of each log:

.. code:: bash

   find \
   "input/cases/$CASE_ID" \
   "results/cases/$CASE_ID" \
   -type f \
   \( \
   -name '*.log' \
   -o -name '*.stderr' \
   -o -name '*.stdout' \
   \) \
   -print0 \
   2>/dev/null |
   while IFS= read -r -d '' log_file; do
   echo
   echo "============================================================"
   echo "$log_file"
   echo "============================================================"
   tail -n 80 "$log_file"
   done

Look for the earliest error rather than only the final launcher message.

.. _19-3-search-logs-for-common-failure-indicators:

19.3 Search logs for common failure indicators
----------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   SEARCH_PATHS=()
   if [[ -d "input/cases/$CASE_ID" ]]; then
   SEARCH_PATHS+=(
   "input/cases/$CASE_ID"
   )
   fi
   if [[ -d "results/cases/$CASE_ID" ]]; then
   SEARCH_PATHS+=(
   "results/cases/$CASE_ID"
   )
   fi
   grep -RInE \
   --include='*.log' \
   --include='*.txt' \
   --include='*.stderr' \
   --include='*.stdout' \
   'Traceback|Exception|FATAL|ERROR|FAILED|command not found|No such file|Permission denied|Killed|Out of memory|Cannot allocate memory|REF_MISMATCH|Invalid argument' \
   "${SEARCH_PATHS[@]}" \
   2>/dev/null \
   || true

Not every line containing the word error represents a fatal failure. Review the surrounding context:

.. code:: bash

   grep -RInE \
   -C 5 \
   --include='*.log' \
   --include='*.stderr' \
   'Traceback|FATAL|FAILED|Killed|Out of memory|Permission denied' \
   "${SEARCH_PATHS[@]}" \
   2>/dev/null \
   || true

.. _19-4-create-a-troubleshooting-inventory:

19.4 Create a troubleshooting inventory
---------------------------------------

The following command records the current case, environment and repository state without modifying anything:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   REPORT_DIR="results/troubleshooting"
   REPORT="$REPORT_DIR/${CASE_ID}_${TIMESTAMP}.diagnostic_report.txt"
   mkdir -p "$REPORT_DIR"
   {
   echo "============================================================"
   echo "PIPELINE TROUBLESHOOTING REPORT"
   echo "============================================================"
   echo
   echo "Generated UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
   echo "Project root: $(pwd)"
   echo "Case ID: $CASE_ID"
   echo
   echo "=== OPERATING SYSTEM ==="
   uname -a
   echo
   cat /etc/os-release 2>/dev/null || true
   echo
   echo "=== GIT ==="
   git rev-parse HEAD 2>/dev/null || true
   git status --short 2>/dev/null || true
   echo
   echo "=== PYTHON ==="
   python3 --version 2>&1 || true
   [[ -x .venv/bin/python ]] &&
   .venv/bin/python --version 2>&1 ||
   true
   echo
   echo "=== APPTAINER ==="
   apptainer --version 2>&1 || true
   echo
   echo "=== BCFTOOLS ==="
   bcftools --version 2>&1 | head -n 3 || true
   echo
   echo "=== STORAGE ==="
   df -h .
   echo
   echo "=== MEMORY ==="
   free -h
   echo
   echo "=== CASE INPUT FILES ==="
   find \
   "input/cases/$CASE_ID" \
   -maxdepth 4 \
   -type f \
   -printf '%s\t%TY-%Tm-%TdT%TH:%TM:%TS\t%p\n' \
   2>/dev/null |
   sort -k3,3
   echo
   echo "=== CASE RESULT FILES ==="
   find \
   "results/cases/$CASE_ID" \
   -maxdepth 5 \
   -type f \
   -printf '%s\t%TY-%Tm-%TdT%TH:%TM:%TS\t%p\n' \
   2>/dev/null |
   sort -k3,3
   echo
   echo "=== RECENT LOG ENDS ==="
   find \
   "input/cases/$CASE_ID" \
   "results/cases/$CASE_ID" \
   -type f \
   \( \
   -name '*.log' \
   -o -name '*.stderr' \
   -o -name '*.stdout' \
   \) \
   -print0 \
   2>/dev/null |
   while IFS= read -r -d '' log_file; do
   echo
   echo "--- $log_file ---"
   tail -n 40 "$log_file"
   done
   } > "$REPORT" 2>&1
   echo "Diagnostic report:"
   echo "$REPORT"

Review the report for private information before sharing it.

.. _19-5-failure-categories:

19.5 Failure categories
-----------------------

.. _19-5-1-input-failure:

19.5.1 Input failure
~~~~~~~~~~~~~~~~~~~~

An input failure originates from:

-  

   .. container::

      Malformed VCF

-  

   .. container::

      Wrong genome build

-  

   .. container::

      Incorrect REF alleles

-  

   .. container::

      Missing genotypes

-  

   .. container::

      Incorrect sample selection

-  

   .. container::

      Invalid HPO file

-  

   .. container::

      Unsupported variant representation

.. _19-5-2-environment-failure:

19.5.2 Environment failure
~~~~~~~~~~~~~~~~~~~~~~~~~~

An environment failure originates from:

-  

   .. container::

      Missing command

-  

   .. container::

      Broken Python environment

-  

   .. container::

      Unavailable Apptainer

-  

   .. container::

      Permission problem

-  

   .. container::

      Insufficient disk space

-  

   .. container::

      Insufficient memory

-  

   .. container::

      WSL filesystem problem

.. _19-5-3-resource-failure:

19.5.3 Resource failure
~~~~~~~~~~~~~~~~~~~~~~~

A resource failure originates from:

-  

   .. container::

      Missing FASTA

-  

   .. container::

      Missing FASTA index

-  

   .. container::

      Wrong VEP cache

-  

   .. container::

      Unindexed ClinVar VCF

-  

   .. container::

      Missing SnpEff database

-  

   .. container::

      Damaged HPO or MONDO files

-  

   .. container::

      G2P mode contamination

-  

   .. container::

      Invalid ClinPGx reference

.. _19-5-4-tool-failure:

19.5.4 Tool failure
~~~~~~~~~~~~~~~~~~~

A tool failure occurs when:

-  

   .. container::

      VEP exits unsuccessfully

-  

   .. container::

      SnpEff cannot load its database

-  

   .. container::

      SpliceAI cannot process the VCF

-  

   .. container::

      AnnotSV cannot find annotations

-  

   .. container::

      ClassifyCNV does not create Scoresheet.txt

-  

   .. container::

      ISV-CNV fails to load its model

.. _19-5-5-pipeline-logic-failure:

19.5.5 Pipeline logic failure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A pipeline logic failure may include:

-  

   .. container::

      Wrong branch routing

-  

   .. container::

      Incorrect disease-label precedence

-  

   .. container::

      Incorrect sample-to-HPO matching

-  

   .. container::

      Wrong inheritance interpretation

-  

   .. container::

      False compound-heterozygous pairing

-  

   .. container::

      PGx rsID-only matching

-  

   .. container::

      Duplicate or missing master-table rows

.. _19-5-6-interpretation-failure:

19.5.6 Interpretation failure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An interpretation failure may include:

-  

   .. container::

      Score treated as probability

-  

   .. container::

      PGx result treated as a diagnosis

-  

   .. container::

      Repeat detection treated as confirmed sizing

-  

   .. container::

      Deletion symbol treated as copy number zero

-  

   .. container::

      Unsupported structural variant treated as benign

.. _19-6-vcf-parsing-failures:

19.6 VCF parsing failures
-------------------------

Common symptoms include:

-  

   .. container::

      Could not parse VCF

-  

   .. container::

      Invalid number of columns

-  

   .. container::

      Undefined FORMAT tag

-  

   .. container::

      Undefined INFO tag

-  

   .. container::

      Malformed header

-  

   .. container::

      Contig not defined

Check basic readability:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="/absolute/path/to/input.vcf.gz"
   bcftools view \
   --output-type v \
   --output /dev/null \
   "$VCF"

Display the header:

.. code:: bash

   bcftools view \
   --header-only \
   "$VCF" |

less

Count body columns:

.. code:: bash

   bcftools view \
   --no-header \
   "$VCF" |
   awk -F '\t' '
   {
   counts[NF]++
   }
   END {
   for (width in counts) {
   print width, counts[width]
   }
   }
   ' |
   sort -n

In a single-sample VCF, ordinary records usually have ten columns:

-  

   .. container::

      CHROM

-  

   .. container::

      POS

-  

   .. container::

      ID

-  

   .. container::

      REF

-  

   .. container::

      ALT

-  

   .. container::

      QUAL

-  

   .. container::

      FILTER

-  

   .. container::

      INFO

-  

   .. container::

      FORMAT

-  

   .. container::

      SAMPLE

A site-only VCF normally has eight columns.

.. _19-7-missing-or-malformed-sample-genotypes:

19.7 Missing or malformed sample genotypes
------------------------------------------

List samples:

.. code:: bash

   bcftools query \
   --list-samples \
   "$VCF"

Inspect genotype values:

.. code:: bash

   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT[\t%SAMPLE=%GT]\n' \
   "$VCF" |
   head -n 50

Count genotype states:

.. code:: bash

   bcftools query \
   --format '[%GT\n]' \
   "$VCF" |
   sort |
   uniq -c |
   sort -nr

A VCF that contains only:

.. code:: bash

   0/0
   ./.

.

may not contain usable alternate patient genotypes.

Do not manufacture genotypes from the ALT column.

.. _19-8-incorrect-sample-selection:

19.8 Incorrect sample selection
-------------------------------

For a multisample VCF:

.. code:: bash

   bcftools query \
   --list-samples \
   "$VCF"

Confirm the selected sample exists exactly:

.. code:: bash

   SELECTED_SAMPLE="PATIENT_SAMPLE"
   if bcftools query \
   --list-samples \
   "$VCF" |
   grep -Fxq "$SELECTED_SAMPLE"
   then
   echo "PASS: Sample found."
   else
   echo "ERROR: Sample does not exist:"
   echo "$SELECTED_SAMPLE"
   exit 1
   fi

Extract a temporary single-sample test VCF:

.. code:: bash

   bcftools view \
   --samples "$SELECTED_SAMPLE" \
   --output-type z \
   --output /tmp/selected_sample.vcf.gz \
   "$VCF"
   bcftools index \
   --tbi \
   --force \
   /tmp/selected_sample.vcf.gz

Do not replace the original multisample file.

.. _19-9-genome-build-problems:

19.9 Genome-build problems
--------------------------

Typical warning signs include:

-  

   .. container::

      Many REF mismatches

-  

   .. container::

      Unexpected chromosome coordinates

-  

   .. container::

      Missing contig names

-  

   .. container::

      Known variants at incorrect positions

-  

   .. container::

      ClinVar producing no matches

Inspect the VCF header:

.. code:: bash

   bcftools view \
   --header-only \
   "$VCF" |
   grep -Ei \
   'reference=|assembly=|GRCh38|hg38|GRCh37|hg19' \
   || true

Test REF compatibility:

.. code:: bash

   REFERENCE="resources/reference/hg38.fa"
   bcftools norm \
   --fasta-ref "$REFERENCE" \
   --check-ref e \
   --output-type z \
   --output /tmp/reference_check.vcf.gz \
   "$VCF"

If this reports many mismatches, do not use:

.. code:: bash

   --check-ref s

as a universal repair.

Investigate:

-  genome build;

-  allele orientation;

-  chromosome naming;

-  source reference;

-  caller documentation.

The pipeline must not silently lift GRCh37 data to GRCh38.

.. _19-10-chromosome-name-mismatches:

19.10 Chromosome-name mismatches
--------------------------------

The project uses:

.. code:: bash

   chr1
   chr2

...

.. code:: bash

   chr22
   chrX
   chrY
   chrM

List chromosome names:

.. code:: bash

   bcftools query \
   --format '%CHROM\n' \
   "$VCF" |
   sort -u

List reference contigs:

.. code:: bash

   cut -f1 \
   resources/reference/hg38.fa.fai |
   head -n 30

Find VCF chromosomes absent from the reference:

.. code:: bash

   comm -23 \
   <(
   bcftools query \
   --format '%CHROM\n' \
   "$VCF" |
   sort -u
   ) \
   <(
   cut -f1 \
   resources/reference/hg38.fa.fai |
   sort -u
   )

An empty output is expected.

Chromosome harmonisation should create a new derived VCF. Do not overwrite the source VCF.

.. _19-11-compression-and-index-problems:

19.11 Compression and index problems
------------------------------------

Test bgzip compression:

.. code:: bash

   bgzip --test "$VCF"

List indexed chromosomes:

.. code:: bash

   tabix --list-chroms "$VCF" |

head

Recreate a missing tabix index:

.. code:: bash

   bcftools index \
   --tbi \
   --force \
   "$VCF"

When the VCF is not bgzip-compressed:

.. code:: bash

   UNCOMPRESSED_VCF="/absolute/path/to/input.vcf"
   COMPRESSED_VCF="/absolute/path/to/input.vcf.gz"
   bgzip \
   --threads "$(nproc)" \
   --stdout \
   "$UNCOMPRESSED_VCF" \
   > "${COMPRESSED_VCF}.tmp"
   mv \
   "${COMPRESSED_VCF}.tmp" \
   "$COMPRESSED_VCF"
   bcftools index \
   --tbi \
   --force \
   "$COMPRESSED_VCF"

Keep the original uncompressed file until the compressed copy has been tested.

.. _19-12-disk-space-failures:

19.12 Disk-space failures
-------------------------

Check storage:

.. code:: bash

   df -h \
   ~/rare_disease_project

Find the largest project paths:

.. code:: bash

   du -ah \
   ~/rare_disease_project |
   sort -hr |
   head -n 40

Find large files:

.. code:: bash

   find \
   ~/rare_disease_project \
   -type f \
   -size +1G \
   -printf '%s\t%p\n' |
   sort -nr

Large expected local components include:

-  

   .. container::

      Reference FASTA

-  

   .. container::

      VEP cache

-  

   .. container::

      Apptainer containers

-  

   .. container::

      SnpEff databases

-  

   .. container::

      AnnotSV annotations

Generated annotated VCFs

Do not delete these without confirming whether they are active dependencies.

.. _19-13-safe-disk-cleanup:

19.13 Safe disk cleanup
-----------------------

Display temporary files first:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find \
   results \
   validation \
   input/cases \
   -type f \
   \( \
   -name '*.tmp' \
   -o -name '*.partial' \
   -o -name '*.temporary' \
   -o -name '*~' \
   \) \
   -print \
   2>/dev/null

After reviewing the list:

.. code:: bash

   find \
   results \
   validation \
   input/cases \
   -type f \
   \( \
   -name '*.tmp' \
   -o -name '*.partial' \
   -o -name '*.temporary' \
   -o -name '*~' \
   \) \
   -delete \
   2>/dev/null

Remove Python caches:

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

Never use broad commands such as:

.. code:: bash

   rm -rf results/*
   rm -rf resources/*
   rm -rf containers/*

.. _19-14-memory-related-failures:

19.14 Memory-related failures
-----------------------------

A process terminated with:

-  

   .. container::

      Killed

-  

   .. container::

      Out of memory

-  

   .. container::

      Cannot allocate memory

may have exceeded available RAM.

Check system memory:

free -h

Check WSL memory pressure:

.. code:: bash

   grep -E \
   'MemTotal|MemAvailable|SwapTotal|SwapFree' \
   /proc/meminfo

Check the most memory-intensive processes:

.. code:: bash

   ps -eo \
   pid,etimes,%cpu,%mem,rss,vsz,cmd \
   --sort=-rss |
   head -n 20

Reduce the run settings cautiously:

.. code:: bash

   THREADS=2 \
   JAVA_MEM=4g \
   bash pipeline/run_real_patient_case.sh \
   "$CASE_ID" \
   "$SOURCE_VCF" \
   "$HPO_FILE"

Do not assign Java more memory than the system can provide.

.. _19-15-wsl-filesystem-problems:

19.15 WSL filesystem problems
-----------------------------

The project is stored physically on an external drive through WSL. If the drive is disconnected, WSL paths may fail or the project may appear missing.

Confirm the project path:

.. code:: bash

   cd ~/rare_disease_project

pwd

Check mounted filesystems:

.. code:: bash

   df -hT

Check that the project is writable:

.. code:: bash

   TEST_FILE=".project_write_test_$$"
   touch "$TEST_FILE"
   rm -f "$TEST_FILE"
   echo "PASS: Project directory is writable."

Do not run the pipeline while the external project drive is unstable or repeatedly disconnecting.

.. _19-16-permission-failures:

19.16 Permission failures
-------------------------

Inspect ownership:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find \
   pipeline \
   input \
   results \
   resources \
   -maxdepth 2 \
   ! -user "$USER" \
   -printf '%u:%g\t%p\n' |
   head -n 50

Check launcher permissions:

.. code:: bash

   find pipeline \
   -type f \
   -name '*.sh' \
   -printf '%m\t%p\n' |

sort

Make a launcher executable only when required:

.. code:: bash

   chmod u+x \
   pipeline/run_real_patient_case.sh \
   pipeline/run_case_pipeline.sh

Do not use:

.. code:: bash

   chmod -R 777 .

This creates unnecessary security and integrity risks.

.. _19-17-apptainer-failures:

19.17 Apptainer failures
------------------------

Confirm Apptainer:

.. code:: bash

   apptainer --version

Test a container:

.. code:: bash

   apptainer exec \
   containers/core_tools.sif \
   bcftools --version

Test bind mounting:

.. code:: bash

   PROJECT_ROOT="$PWD"
   apptainer exec \
   --bind "$PROJECT_ROOT:/project" \
   containers/core_tools.sif \
   sh -c '
   test -d /project &&
   echo "PASS: /project bind is available."
   '

Common Apptainer failures include:

+------------------------------+---------------------------------------+
| **Failure**                  | **Likely cause**                      |
+==============================+=======================================+
| Container not found          | Wrong SIF path                        |
+------------------------------+---------------------------------------+
| /project missing             | Bind path not supplied                |
+------------------------------+---------------------------------------+
| Permission denied            | Mount or file permissions             |
+------------------------------+---------------------------------------+
| Executable missing           | Wrong container definition            |
+------------------------------+---------------------------------------+
| Image corruption             | Incomplete build or copy              |
+------------------------------+---------------------------------------+
| No space left                | Insufficient disk space               |
+------------------------------+---------------------------------------+

Verify a container checksum before rebuilding:

.. code:: bash

   sha256sum \
   containers/core_tools.sif \
   containers/vep.sif \
   containers/snpeff.sif \
   containers/spliceai.sif \
   containers/isv.sif

.. _19-18-vep-failures:

19.18 VEP failures
------------------

Common VEP errors include:

-  

   .. container::

      Cache not found

-  

   .. container::

      Cache version mismatch

-  

   .. container::

      FASTA unavailable

-  

   .. container::

      Reference mismatch

-  

   .. container::

      Cannot write output

-  

   .. container::

      Plugin unavailable

Confirm the VEP program:

.. code:: bash

   apptainer exec \
   containers/vep.sif \
   vep --version

Inspect the cache:

.. code:: bash

   find \
   resources/vep_cache \
   -maxdepth 3 \
   -type d \
   | head -n 30

Confirm the expected human GRCh38 release directory exists:

.. code:: bash

   find \
   resources/vep_cache \
   -type d \
   -path '*/homo_sapiens/*_GRCh38' \
   -print

Confirm the FASTA bind path:

.. code:: bash

   apptainer exec \
   --bind "$PWD:/project" \
   containers/vep.sif \
   sh -c '
   test -s /project/resources/reference/hg38.fa &&
   echo "PASS: FASTA visible inside VEP container."
   '

A VEP program and cache release mismatch must be corrected by using compatible releases. Do not rename a cache directory merely to make VEP accept it.

.. _19-19-missing-vep-csq:

19.19 Missing VEP CSQ
---------------------

Check the output header:

.. code:: bash

   VEP_VCF="path/to/vep.vcf.gz"
   bcftools view \
   --header-only \
   "$VEP_VCF" |
   grep '^##INFO=<ID=CSQ,' \
   || true

Count annotated records:

.. code:: bash

   bcftools query \
   --format '%INFO/CSQ\n' \
   "$VEP_VCF" |
   awk '
   $0 != "." && $0 != "" {
   count++
   }
   END {
   print count + 0
   }
   '

Possible causes of missing CSQ include:

-  VEP did not complete;

-  the wrong output was inspected;

-  VCF output mode was not selected;

-  the input contained unsupported records;

-  an intermediate file overwrote the annotated output.

.. _19-20-snpeff-failures:

19.20 SnpEff failures
---------------------

Confirm the command:

.. code:: bash

   apptainer exec \
   containers/snpeff.sif \
   snpEff -version

Find installed databases:

.. code:: bash

   find \
   resources/snpeff_data \
   -maxdepth 2 \
   -type d \
   | sort |
   head -n 50

Inspect the database used by the pipeline:

.. code:: bash

   grep -RInE \
   'GRCh38|snpEff|SNPEFF' \
   pipeline \
   | head -n 100

A common failure is a mismatch between:

Database installed under resources/snpeff_data

and:

Database identifier passed to snpEff

Do not change the database name in only one location. Update the installation documentation and production script together, then rerun validation.

.. _19-21-missing-snpeff-ann:

19.21 Missing SnpEff ANN
------------------------

.. code:: bash

   SNPEFF_VCF="path/to/snpeff.vcf.gz"
   bcftools view \
   --header-only \
   "$SNPEFF_VCF" |
   grep '^##INFO=<ID=ANN,' \
   || true

Count annotations:

.. code:: bash

   bcftools query \
   --format '%INFO/ANN\n' \
   "$SNPEFF_VCF" |
   awk '
   $0 != "." && $0 != "" {
   count++
   }
   END {
   print count + 0
   }
   '

Check whether VEP annotations were preserved:

.. code:: bash

   for tag in CSQ ANN; do
   if bcftools view \
   --header-only \
   "$SNPEFF_VCF" |
   grep -q "^##INFO=<ID=${tag},"
   then
   echo "PASS: INFO/$tag"
   else
   echo "FAIL: INFO/$tag"
   fi
   done

.. _19-22-clinvar-annotation-failures:

19.22 ClinVar annotation failures
---------------------------------

Confirm the resource:

.. code:: bash

   CLINVAR="resources/clinvar/clinvar.vcf.gz"
   bgzip --test "$CLINVAR"
   tabix --list-chroms "$CLINVAR" |

head

Confirm required fields:

.. code:: bash

   for tag in \
   CLNSIG \
   CLNDN \
   CLNREVSTAT
   do
   if bcftools view \
   --header-only \
   "$CLINVAR" |
   grep -q "^##INFO=<ID=${tag},"
   then
   echo "PASS: ClinVar INFO/$tag"
   else
   echo "FAIL: ClinVar INFO/$tag"
   fi
   done

When ClinVar produces no matches, compare exact alleles:

.. code:: bash

   CASE_VCF="path/to/normalized.vcf.gz"
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\n' \
   "$CASE_VCF" |
   head -n 20

Query one region from ClinVar:

.. code:: bash

   REGION="chr12:102840493-102840493"
   bcftools view \
   --regions "$REGION" \
   "$CLINVAR"

No ClinVar match may be correct. Do not force a match by position alone.

.. _19-23-spliceai-failures:

19.23 SpliceAI failures
-----------------------

Confirm the package:

.. code:: bash

   apptainer exec \
   containers/spliceai.sif \
   python -c '
   from importlib.metadata import version
   print(version("spliceai"))
   '

Confirm the FASTA is visible:

.. code:: bash

   apptainer exec \
   --bind "$PWD:/project" \
   containers/spliceai.sif \
   sh -c '
   test -s /project/resources/reference/hg38.fa &&
   echo "PASS: GRCh38 FASTA visible."
   '

Inspect the input for symbolic alleles:

.. code:: bash

   SPLICEAI_INPUT="path/to/spliceai_input.vcf"
   grep -v '^#' \
   "$SPLICEAI_INPUT" |
   awk -F '\t' '
   $5 ~ /^</ ||
   $5 ~ /\[/ ||
   $5 ~ /\]/ {
   print
   }
   '

Repeat expansions, CNVs and breakends must not enter SpliceAI.

A valid variant may still lack a SpliceAI prediction because it is outside the supported annotation context.

.. _19-24-annotsv-failures:

19.24 AnnotSV failures
----------------------

Confirm the environment:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   export ANNOTSV="$PWD/resources/annotsv_setup/AnnotSV"
   test -x "$ANNOTSV/bin/AnnotSV"
   test -d "$ANNOTSV/share/AnnotSV/Annotations_Human"
   echo "PASS: AnnotSV executable and human annotations found."

Inspect the log:

.. code:: bash

   ANNOTSV_LOG="path/to/AnnotSV.log"
   tail -n 100 "$ANNOTSV_LOG"

Common problems include:

ANNOTSV variable not set

-  

   .. container::

      Annotations_Human missing

-  

   .. container::

      Incorrect genome build

-  

   .. container::

      Malformed BED

-  

   .. container::

      CNV type not in the expected column

-  

   .. container::

      Output path not writable

Validate the BED:

.. code:: bash

   CNV_BED="path/to/cnv_input.bed"
   awk '
   BEGIN {
   FS = "\t"
   failures = 0
   }
   NF == 0 || $1 ~ /^#/ {
   next
   }
   NF != 4 {
   print "Invalid width at line", NR
   failures++
   }
   $2 !~ /^[0-9]+$/ ||
   $3 !~ /^[0-9]+$/ {
   print "Invalid coordinates at line", NR
   failures++
   }
   $2 >= $3 {
   print "Invalid interval at line", NR
   failures++
   }
   $4 != "DEL" &&
   $4 != "DUP" {
   print "Invalid CNV type at line", NR
   failures++
   }
   END {
   exit failures > 0
   }
   ' "$CNV_BED"

.. _19-25-classifycnv-failures:

19.25 ClassifyCNV failures
--------------------------

Check the source:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CLASSIFYCNV_DIR="tools/ClassifyCNV"
   test -s "$CLASSIFYCNV_DIR/ClassifyCNV.py"
   python3 -m py_compile \
   "$CLASSIFYCNV_DIR/ClassifyCNV.py"

Inspect recent result directories:

find \\

.. code:: bash

   "$CLASSIFYCNV_DIR/ClassifyCNV_results" \
   -maxdepth 2 \
   -type f \
   -printf '%T@\t%s\t%p\n' \
   2>/dev/null |
   sort -nr |
   head -n 30

Find scoresheets:

.. code:: bash

   find \
   "$CLASSIFYCNV_DIR/ClassifyCNV_results" \
   -type f \
   -name 'Scoresheet.txt' \
   -print

Common problems include:

-  

   .. container::

      Wrong GenomeBuild argument

-  

   .. container::

      Malformed four-column BED

-  

   .. container::

      Missing ClassifyCNV resources

-  

   .. container::

      Result written to an unexpected directory

-  

   .. container::

      Tool process failed before Scoresheet.txt creation

The absence of Scoresheet.txt must be treated as a failed ClassifyCNV stage.

.. _19-26-isv-cnv-failures:

19.26 ISV-CNV failures
----------------------

Confirm the command:

.. code:: bash

   apptainer exec \
   containers/isv.sif \
   sh -c '
   command -v isv &&
   isv --help
   '

Confirm the input header:

.. code:: bash

   ISV_INPUT="path/to/isv_input.tsv"
   head -n 1 "$ISV_INPUT"

Expected:

chromosome start end cnv_type

Inspect the log:

.. code:: bash

   ISV_LOG="path/to/ISV_CNV.log"
   tail -n 100 "$ISV_LOG"

Common problems include:

Incorrect Python version

-  

   .. container::

      Model import failure

-  

   .. container::

      Wrong input header

-  

   .. container::

      Invalid CNV type

-  

   .. container::

      Missing output permissions

-  

   .. container::

      Container dependency mismatch

Do not convert an ISV failure into a benign CNV classification. Report the stage as unavailable or failed.

.. _19-27-g2p-resource-problems:

19.27 G2P resource problems
---------------------------

Check the resource files:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find \
   resources/gene_disease/g2p \
   -maxdepth 1 \
   -type f \
   -printf '%s\t%p\n' |
   sort -k2,2

Run the isolation tests:

.. code:: bash

   source .venv/bin/activate

-  

   .. container::

      python pipeline/tests/03_test_resource_modes.py

-  

   .. container::

      python pipeline/tests/07_test_g2p_resource_isolation.py

A production result must not depend on a validation-only G2P relationship.

When a G2P file is updated:

-  preserve the previous file;

-  record both checksums;

-  inspect the header;

-  confirm the production and validation paths;

-  rerun all relevant tests;

-  rerun the completed synthetic cases.

.. _19-28-hpo-matching-problems:

19.28 HPO matching problems
---------------------------

Common symptoms include:

-  

   .. container::

      Phenotype file not found

-  

   .. container::

      Zero phenotype terms

-  

   .. container::

      Wrong patient HPO file

-  

   .. container::

      Invalid HPO identifiers

-  

   .. container::

      Obsolete HPO terms

-  

   .. container::

      Unexpectedly low phenotype score

Validate the HPO file:

.. code:: bash

   HPO_FILE="/absolute/path/to/phenotypes.txt"
   grep -vE \
   '^[[:space:]]*$|^[[:space:]]*#' \
   "$HPO_FILE" |
   awk '
   !/^HP:[0-9]{7}$/ {
   print "Invalid:", $0
   failures++
   }
   END {
   exit failures > 0
   }
   '

Confirm exact patient matching:

.. code:: bash

   cd ~/rare_disease_project
   source .venv/bin/activate
   python \
   pipeline/tests/09_test_exact_hpo_patient_matching.py

Search for similar filenames:

.. code:: bash

   find \
   validation/universal_pipeline_testing/inputs/hpo \
   -maxdepth 1 \
   -type f \
   -printf '%f\n' |

sort

Do not use partial filename matching that allows patient_01 to select patient_010.

.. _19-29-mondo-disease-resolution-problems:

19.29 MONDO disease-resolution problems
---------------------------------------

Inspect active files:

.. code:: bash

   find \
   resources/disease_ontology/mondo \
   -maxdepth 3 \
   -type f \
   -printf '%s\t%p\n' |
   sort -k2,2

Check the ontology:

.. code:: bash

   MONDO_OBO="resources/disease_ontology/mondo/current/mondo.obo"
   grep -m 1 '^ontology:' "$MONDO_OBO"
   grep -m 1 '^data-version:' "$MONDO_OBO" || true
   grep -c '^\[Term\]$' "$MONDO_OBO"

A disease-resolution problem can result from:

-  

   .. container::

      Changed preferred labels

-  

   .. container::

      Missing cross-references

-  

   .. container::

      Broad or narrow disease mappings

-  

   .. container::

      Schema changes

-  

   .. container::

      Incorrect text-only matching

Original G2P and ClinVar disease labels must remain available even when MONDO mapping fails.

.. _19-30-clinpgx-matching-problems:

19.30 ClinPGx matching problems
-------------------------------

Run the regression test:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/04_test_allele_aware_local_pgx.py

Validate the reference checksum:

.. code:: bash

   PGX_FILE="resources/clinpgx/local_curated_pgx_reference.csv"
   PGX_HASH="resources/clinpgx/local_curated_pgx_reference.sha256"
   EXPECTED="$(
   awk 'NR == 1 {print $1}' \
   "$PGX_HASH"
   )"
   printf '%s %s\n' \
   "$EXPECTED" \
   "$PGX_FILE" |
   sha256sum --check -

When a locus or rsID matches but the allele differs:

-  

   .. container::

      Do not assign the star allele.

-  

   .. container::

      Do not assign the functional phenotype.

-  

   .. container::

      Report the mismatch explicitly.

A variants-only VCF cannot establish a normal diplotype from an absent variant.

.. _19-31-inheritance-analysis-problems:

19.31 Inheritance-analysis problems
-----------------------------------

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python pipeline/tests/05_test_inheritance_models.py
   python pipeline/tests/06_test_sex_ploidy_preflight.py
   python pipeline/tests/08_test_compound_heterozygous.py

Common errors include:

+---------------------------------------------------+----------------------------------+
| **Problem**                                       | **Correct handling**             |
+===================================================+==================================+
| One heterozygous allele satisfies recessive model | Partial evidence only            |
+---------------------------------------------------+----------------------------------+
| Unphased pair declared trans                      | Possible pair only               |
+---------------------------------------------------+----------------------------------+
| Same-phase haplotype pair declared trans          | Classify as cis                  |
+---------------------------------------------------+----------------------------------+
| Different phase sets compared directly            | Phase unresolved                 |
+---------------------------------------------------+----------------------------------+
| Homozygous variant copied into two rows           | Treat as one biallelic candidate |
+---------------------------------------------------+----------------------------------+
| X-linked variant interpreted without sex context  | Mark uncertain                   |
+---------------------------------------------------+----------------------------------+
| chrM interpreted as diploid autosomal             | Use mitochondrial handling       |
+---------------------------------------------------+----------------------------------+

The inheritance utility should be corrected centrally. Do not add separate logic for one patient.

.. _19-32-repeat-routing-problems:

19.32 Repeat-routing problems
-----------------------------

Search the source VCF:

.. code:: bash

   bcftools query \
   --format '%CHROM\t%POS\t%ID\t%REF\t%ALT\t%INFO[\t%GT]\n' \
   "$VCF" |
   grep -Ei \
   'repeat|expansion|CAG|CNV:TR|STR|REPCN|REPCI' \
   || true

Confirm the record did not enter the small-variant output:

.. code:: bash

   SMALL_VCF="path/to/routed.small_variants.vcf.gz"
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\n' \
   "$SMALL_VCF" |
   grep -E \
   '<[^>]+>|\[|\]' \
   && {
   echo "ERROR: Symbolic record entered small-variant route."
   exit 1
   } \
   || true

The correct repeat status is:

detected_not_interpreted

when the VCF record was detected but the pipeline did not independently perform specialist repeat sizing.

.. _19-33-candidate-ranking-problems:

19.33 Candidate-ranking problems
--------------------------------

Symptoms include:

-  

   .. container::

      Expected pathogenic candidate ranked below background variants

-  

   .. container::

      Candidate disappeared

-  

   .. container::

      Score changed unexpectedly

-  

   .. container::

      Duplicate candidate rows

-  

   .. container::

      Tied scores change order between runs

-  

   .. container::

      Repeat record receives an SNV score

-  

   .. container::

      PGx evidence alters disease score

First confirm the input and source checksums:

.. code:: bash

   sha256sum \
   --check \
   validation/final_audit_20260727/pipeline_source.sha256
   sha256sum \
   --check \
   validation/final_audit_20260727/key_resources.sha256

Then inspect scoring source changes:

.. code:: bash

   git diff \
   -- \
   pipeline/case_workflow

Search sort operations:

.. code:: bash

   grep -RInE \
   'sort_values|sorted\(|rank\(|ascending|reverse|candidate_rank|universal_score' \
   pipeline \
   | head -n 200

A score change must be explained through changed evidence, resources or source code.

.. _19-34-missing-master-table-rows:

19.34 Missing master-table rows
-------------------------------

Possible causes include:

-  

   .. container::

      Different variant-key formats

-  

   .. container::

      Many-to-many join

-  

   .. container::

      Transcript table using different allele representation

-  

   .. container::

      CNV interval coordinates transformed inconsistently

-  

   .. container::

      Disease identity missing

-  

   .. container::

      Empty branch merged incorrectly

Compare keys in intermediate tables:

.. code:: bash

   TABLE_A="path/to/table_a.tsv"
   TABLE_B="path/to/table_b.tsv"
   head -n 1 "$TABLE_A"
   head -n 1 "$TABLE_B"

Search one candidate:

.. code:: bash

   CANDIDATE_KEY="chr12:102840493:G>A"
   grep -RInF \
   "$CANDIDATE_KEY" \
   "results/cases/$CASE_ID" \
   || true

Trace the candidate from:

-  

   .. container::

      Normalised VCF

-  

   .. container::

      VEP output

-  

   .. container::

      Merged annotation table

-  

   .. container::

      G2P table

-  

   .. container::

      Phenotype table

-  

   .. container::

      Inheritance table

-  

   .. container::

      Scoring table

-  

   .. container::

      Master table

The first file where it disappears identifies the failing join or filter stage.

.. _19-35-duplicate-candidate-rows:

19.35 Duplicate candidate rows
------------------------------

Duplicate rows can result from:

-  

   .. container::

      Several transcripts

-  

   .. container::

      Several diseases per gene

-  

   .. container::

      Several ClinVar conditions

-  

   .. container::

      Several AnnotSV split rows

-  

   .. container::

      Several drugs per PGx allele

-  

   .. container::

      Many-to-many table joins

A duplicate genomic variant is not always an error.

The correct unique key may need to include:

-  

   .. container::

      Variant key

-  

   .. container::

      Resolved disease identifier

-  

   .. container::

      Transcript

-  

   .. container::

      Analysis branch

Inspect duplicates using the actual schema:

.. code:: bash

   MASTER_TABLE="path/to/master_candidate_table.tsv"
   python3 - "$MASTER_TABLE" <<'PY'
   from __future__ import annotations
   import csv
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
   raise SystemExit("ERROR: Header missing.")
   print("Columns:")
   for column in reader.fieldnames:
   print(f" {column}")
   PY

Determine the intended row unit before removing any apparent duplicate.

.. _19-36-safe-rerun-procedure:

19.36 Safe rerun procedure
--------------------------

Before rerunning:

1. Preserve the failed result.

2. Record its checksum.

3. Identify the first failing stage.

4. Correct the universal cause.

5. Run targeted tests.

6. Run syntax checks.

7. Rerun with --force only after backup.

8. Compare old and new outputs.

9. Run the complete validation suite.

Create a rerun backup:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   ARCHIVE="local_case_archives/${CASE_ID}_before_rerun_${TIMESTAMP}.tar.gz"
   mkdir -p \
   "$(dirname "$ARCHIVE")"
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

Then rerun through the same launcher used originally.

.. _19-37-universal-fix-policy:

19.37 Universal-fix policy
--------------------------

A valid correction should work for a class of inputs.

Acceptable examples include:

-  

   .. container::

      Use exact HPO case matching for every patient.

-  

   .. container::

      Require REF and ALT for every PGx match.

-  

   .. container::

      Require shared phase information for every phased pair.

-  

   .. container::

      Separate every repeat expansion before normalisation.

-  

   .. container::

      Validate every CNV endpoint before BED conversion.

Unacceptable examples include:

-  

   .. container::

      If case_id is patient_05, force HEXA to rank first.

-  

   .. container::

      If the variant is a known test variant, add 20 points.

-  

   .. container::

      Ignore REF mismatch for one coordinate.

-  

   .. container::

      Treat one particular rsID as matching any ALT.

-  

   .. container::

      Use a different HPO file only for one patient.

Patient-specific exceptions invalidate the universal nature of the workflow.

.. _19-38-safe-source-code-modification:

19.38 Safe source-code modification
-----------------------------------

Before changing source code:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git status --short
   git rev-parse HEAD

Create a maintenance branch:

.. code:: bash

   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   git switch \
   -c "maintenance/fix_${TIMESTAMP}"

Record the original source checksums:

.. code:: bash

   mkdir -p \
   validation/update_work
   sha256sum \
   $(find pipeline -type f \( -name '*.py' -o -name '*.sh' \) | sort) \
   > validation/update_work/pipeline_before_update.sha256

After editing:

.. code:: bash

   git diff --check
   git diff --stat
   git diff -- pipeline

Run syntax validation before any case analysis.

.. _19-39-targeted-test-selection:

19.39 Targeted test selection
-----------------------------

Use the smallest relevant test first.

+--------------------------+-------------------------------------------+
| **Changed component**    | **First targeted test**                   |
+==========================+===========================================+
| Resource-mode selection  | 03_test_resource_modes.py                 |
+--------------------------+-------------------------------------------+
| ClinPGx matching         | 04_test_allele_aware_local_pgx.py         |
+--------------------------+-------------------------------------------+
| Inheritance logic        | 05_test_inheritance_models.py             |
+--------------------------+-------------------------------------------+
| Sex/ploidy logic         | 06_test_sex_ploidy_preflight.py           |
+--------------------------+-------------------------------------------+
| G2P isolation            | 07_test_g2p_resource_isolation.py         |
+--------------------------+-------------------------------------------+
| Compound heterozygosity  | 08_test_compound_heterozygous.py          |
+--------------------------+-------------------------------------------+
| HPO selection            | 09_test_exact_hpo_patient_matching.py     |
+--------------------------+-------------------------------------------+
| Disease-label precedence | 10_test_g2p_disease_label_precedence.py   |
+--------------------------+-------------------------------------------+
| Intake preservation      | 11_test_intake_report_preservation.py     |
+--------------------------+-------------------------------------------+

Then run the complete suite.

.. _19-40-complete-source-validation-after-an-update:

19.40 Complete source validation after an update
------------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   echo "=== Bash syntax ==="
   while IFS= read -r -d '' script; do
   bash -n "$script"
   echo "PASS: $script"
   done < <(
   find pipeline \
   -type f \
   -name '*.sh' \
   -print0 |
   sort -z
   )
   echo
   echo "=== Python syntax ==="
   while IFS= read -r -d '' script; do
   python -m py_compile "$script"
   echo "PASS: $script"
   done < <(
   find pipeline validation \
   -type f \
   -name '*.py' \
   -print0 |
   sort -z
   )
   echo
   echo "PASS: Source syntax validation completed."

.. _19-41-complete-regression-tests-after-an-update:

19.41 Complete regression tests after an update
-----------------------------------------------

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
   for test_script in "${TESTS[@]}"; do
   echo
   echo "Running: $test_script"
   python "$test_script"
   done
   echo
   echo "PASS: All targeted regression tests passed."

.. _19-42-final-audit-after-a-source-update:

19.42 Final audit after a source update
---------------------------------------

The previous audit checksums may fail intentionally after source changes.

This means:

The previous audit no longer describes the current source.

It does not automatically mean:

The new source is incorrect.

Run the behavioural audit:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py

Then compare:

-  expected candidates;

-  expected routes;

-  scores;

-  PGx results;

-  output schemas.

Create a new dated audit only after the changed behaviour is deliberately accepted.

.. _19-43-resource-update-policy:

19.43 Resource-update policy
----------------------------

Every resource update should be treated as a controlled software change.

The update process is:

Preserve old resource

│

▼

Download or create new resource

│

▼

Verify integrity and schema

│

▼

Install beside old resource

│

▼

Record release and checksum

│

▼

Update active pointer or configuration

│

▼

Run targeted tests

│

▼

Rerun validation cases

│

▼

Compare outputs

│

▼

Accept or roll back

Never overwrite the only copy of an active resource before the new version has been validated.

.. _19-44-generic-resource-backup:

19.44 Generic resource backup
-----------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   RESOURCE_PATH="resources/path/to/active_resource"
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   ARCHIVE_DIR="resources/archive/$TIMESTAMP"
   if [[ ! -e "$RESOURCE_PATH" ]]; then
   echo "ERROR: Resource does not exist:"
   echo "$RESOURCE_PATH"
   exit 1
   fi
   mkdir -p "$ARCHIVE_DIR"
   cp \
   --archive \
   "$RESOURCE_PATH" \
   "$ARCHIVE_DIR/"
   find \
   "$ARCHIVE_DIR" \
   -type f \
   -print0 |
   sort -z |
   xargs -0 sha256sum \
   > "$ARCHIVE_DIR/resource_files.sha256"
   sha256sum \
   --check \
   "$ARCHIVE_DIR/resource_files.sha256"

.. _19-45-updating-clinvar-safely:

19.45 Updating ClinVar safely
-----------------------------

A ClinVar update requires:

-  

   .. container::

      New GRCh38 VCF

-  

   .. container::

      New index

-  

   .. container::

      Release or retrieval date

-  

   .. container::

      Checksum

-  

   .. container::

      Required INFO fields

-  

   .. container::

      Chromosome harmonisation

-  

   .. container::

      Annotation smoke test

-  

   .. container::

      Regression rerun

Preserve the active files:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   ARCHIVE="resources/clinvar/archive/$TIMESTAMP"
   mkdir -p "$ARCHIVE"
   cp \
   --archive \
   resources/clinvar/clinvar.vcf.gz \
   resources/clinvar/clinvar.vcf.gz.tbi \
   "$ARCHIVE/"
   sha256sum \
   "$ARCHIVE/clinvar.vcf.gz" \
   "$ARCHIVE/clinvar.vcf.gz.tbi" \
   > "$ARCHIVE/clinvar.sha256"

After installing the new release, confirm:

.. code:: bash

   bgzip --test \
   resources/clinvar/clinvar.vcf.gz
   tabix --list-chroms \
   resources/clinvar/clinvar.vcf.gz |

head

.. code:: bash

   for field in \
   CLNSIG \
   CLNDN \
   CLNREVSTAT
   do
   bcftools view \
   --header-only \
   resources/clinvar/clinvar.vcf.gz |
   grep "^##INFO=<ID=${field},"
   done

ClinVar changes can alter candidate evidence and scores even when the pipeline source is unchanged.

.. _19-46-updating-g2p-safely:

19.46 Updating G2P safely
-------------------------

A G2P update must preserve:

-  

   .. container::

      Official production resource

-  

   .. container::

      Local validation additions

-  

   .. container::

      Combined validation resource

-  

   .. container::

      Mode-isolation documentation

-  

   .. container::

      Checksums

Do not merge local validation relationships into the official production file.

After an update:

source .venv/bin/activate

-  

   .. container::

      python pipeline/tests/03_test_resource_modes.py

-  

   .. container::

      python pipeline/tests/07_test_g2p_resource_isolation.py

-  

   .. container::

      python pipeline/tests/10_test_g2p_disease_label_precedence.py

Inspect row counts and headers before accepting the new file.

.. _19-47-updating-hpo-safely:

19.47 Updating HPO safely
-------------------------

An HPO update can affect:

-  

   .. container::

      Term validity

-  

   .. container::

      Obsolete terms

-  

   .. container::

      Parent–child relationships

-  

   .. container::

      Disease annotations

-  

   .. container::

      Semantic scores

-  

   .. container::

      Candidate rankings

Install the new release in a separate dated directory.

Do not replace current until:

-  hp.obo is valid;

-  annotation files are present;

-  the semantic cache is rebuilt;

-  patient terms are validated;

-  the exact HPO matching test passes;

-  validation cases are rerun.

Record:

-  

   .. container::

      Release date

-  

   .. container::

      Source files

-  

   .. container::

      Checksums

-  

   .. container::

      Semantic-cache checksum

-  

   .. container::

      Builder-script checksum

.. _19-48-updating-mondo-safely:

19.48 Updating MONDO safely
---------------------------

A MONDO update may change:

-  

   .. container::

      Preferred disease labels

-  

   .. container::

      Synonyms

-  

   .. container::

      Obsolete identifiers

-  

   .. container::

      Cross-references

-  

   .. container::

      Disease hierarchy

After updating:

-  rebuild the crosswalk;

-  inspect mapping counts;

-  run disease-label tests;

-  compare resolved disease names;

-  preserve original G2P and ClinVar labels;

-  rerun candidate scoring.

A terminology change should not be confused with a new biological finding.

.. _19-49-updating-the-local-clinpgx-reference:

19.49 Updating the local ClinPGx reference
------------------------------------------

Before editing:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   ARCHIVE_DIR="resources/clinpgx/archive/$TIMESTAMP"
   mkdir -p "$ARCHIVE_DIR"
   cp \
   --archive \
   resources/clinpgx/local_curated_pgx_reference.csv \
   resources/clinpgx/LOCAL_REFERENCE_SCHEMA.txt \
   resources/clinpgx/local_curated_pgx_reference.sha256 \
   "$ARCHIVE_DIR/"

After editing:

1. confirm GRCh38 coordinates;

2. confirm positive genomic-strand alleles;

3. validate row widths;

4. confirm exact REF and ALT values;

5. record source and retrieval date;

6. regenerate the checksum;

7. run the allele-aware test;

8. rerun PGx validation cases.

Run:

.. code:: bash

   source .venv/bin/activate
   python \
   pipeline/tests/04_test_allele_aware_local_pgx.py

Do not add a PGx record merely because the gene is pharmacogenomically important. The exact allele and curated interpretation must be represented.

.. _19-50-updating-vep-or-its-cache:

19.50 Updating VEP or its cache
-------------------------------

The VEP program and cache must remain compatible.

Before changing either:

.. code:: bash

   apptainer exec \
   containers/vep.sif \
   vep --version

Record the current container checksum:

.. code:: bash

   sha256sum \
   containers/vep.sif

Record the cache structure:

.. code:: bash

   find \
   resources/vep_cache \
   -maxdepth 3 \
   -type d \
   | sort

After an update:

-  run the VEP smoke test;

-  verify CSQ;

-  verify MANE and canonical flags;

-  verify cached gnomAD fields;

-  compare transcript consequences;

-  rerun Patients 01–12.

A VEP update may alter consequence selection even when the variant itself is unchanged.

.. _19-51-updating-snpeff:

19.51 Updating SnpEff
---------------------

Before updating:

.. code:: bash

   apptainer exec \
   containers/snpeff.sif \
   snpEff -version
   sha256sum \
   containers/snpeff.sif

Record the active database identifier used by the pipeline.

After updating:

-  verify the database exists;

-  run one annotated VCF;

-  confirm both CSQ and ANN remain present;

-  compare transcript and consequence changes;

-  rerun scoring validation.

Do not update the SnpEff container without also documenting the database version.

.. _19-52-updating-containers-safely:

19.52 Updating containers safely
--------------------------------

Never replace a validated SIF without preserving the original checksum.

Archive:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CONTAINER="containers/spliceai.sif"
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   ARCHIVE_DIR="containers/archive/$TIMESTAMP"
   mkdir -p "$ARCHIVE_DIR"
   cp \
   --preserve=mode,timestamps \
   "$CONTAINER" \
   "$ARCHIVE_DIR/"
   sha256sum \
   "$ARCHIVE_DIR/$(basename "$CONTAINER")" \
   > "$ARCHIVE_DIR/container.sha256"

Build the replacement under a temporary filename:

.. code:: bash

   apptainer build \
   containers/spliceai.new.sif \
   containers/spliceai.def

Test it before replacement:

.. code:: bash

   apptainer exec \
   containers/spliceai.new.sif \
   spliceai --help

Replace only after successful smoke and regression tests:

.. code:: bash

   mv \
   containers/spliceai.sif \
   containers/spliceai.previous.sif
   mv \
   containers/spliceai.new.sif \
   containers/spliceai.sif

Do not commit SIF images to GitHub.

.. _19-53-rollback-procedure:

19.53 Rollback procedure
------------------------

Rollback is appropriate when:

-  

   .. container::

      A new source change breaks validation

-  

   .. container::

      A new resource changes results unexpectedly

-  

   .. container::

      A new container cannot reproduce the old output

-  

   .. container::

      A tool upgrade removes required functionality

For source code, inspect the changed files:

.. code:: bash

   git status --short
   git diff

Restore one uncommitted file:

.. code:: bash

   git restore \
   path/to/file

Restore a file from a known commit:

.. code:: bash

   git restore \
   --source COMMIT_SHA \
   path/to/file

Do not use a broad reset until the files to be discarded have been reviewed.

For resources, restore the archived version and its checksum, then rerun the relevant readiness checks.

.. _19-54-creating-a-new-validated-audit-after-updates:

19.54 Creating a new validated audit after updates
--------------------------------------------------

Do not overwrite:

validation/final_audit_20260727/

Create a new dated audit:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   AUDIT_DATE="$(
   date -u '+%Y%m%d'
   )"
   NEW_AUDIT_DIR="validation/final_audit_${AUDIT_DATE}"
   if [[ -e "$NEW_AUDIT_DIR" ]]; then
   echo "ERROR: Audit directory already exists:"
   echo "$NEW_AUDIT_DIR"
   exit 1
   fi
   mkdir -p \
   "$NEW_AUDIT_DIR/scripts"

A new audit should contain:

-  

   .. container::

      canonical_cases.tsv

-  

   .. container::

      canonical_final_outputs.sha256

-  

   .. container::

      key_resources.sha256

-  

   .. container::

      pipeline_source.sha256

-  

   .. container::

      FINAL_VALIDATION_STATUS.md

-  

   .. container::

      audit script

-  

   .. container::

      validation notes

The previous audit remains historical evidence.

.. _19-55-git-review-before-committing-an-update:

19.55 Git review before committing an update
--------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git status --short
   echo
   echo "=== Changed files ==="
   git diff \
   --name-status
   echo
   echo "=== Diff summary ==="
   git diff \
   --stat
   echo
   echo "=== Whitespace and conflict errors ==="
   git diff \
   --check

Search for unresolved conflict markers:

.. code:: bash

   grep -RInE \
   --exclude-dir=.git \
   '^(<<<<<<<|=======|>>>>>>>)' \
   pipeline \
   validation \
   README.md \
   || true

Check that large local files are not staged:

.. code:: bash

   git diff \
   --cached \
   --name-only |
   while IFS= read -r path; do
   [[ -f "$path" ]] || continue
   size="$(
   stat -c '%s' "$path"
   )"
   if (( size > 50 * 1024 * 1024 )); then
   echo "WARNING: Large staged file:"
   echo "$size $path"
   fi
   done

.. _19-56-privacy-check-before-committing:

19.56 Privacy check before committing
-------------------------------------

Search staged text files:

.. code:: bash

   git diff \
   --cached \
   --name-only \
   --diff-filter=ACMRT |
   while IFS= read -r path; do
   [[ -f "$path" ]] || continue
   case "$path" in
   *.md|*.txt|*.tsv|*.csv|*.json|*.yaml|*.yml|*.py|*.sh)
   grep -nEi \
   'patient.name|date.of.birth|\bDOB\b|hospital.number|email.address|phone.number|national.id|/home/[^/]+/' \
   "$path" \
   && echo "REVIEW: $path" \
   || true
   ;;
   esac
   done

Manual review is still required.

.. _19-57-commit-only-after-validation:

19.57 Commit only after validation
----------------------------------

After all tests and audits pass:

.. code:: bash

   git add \
   pipeline \
   validation \
   README.md \
   tools/README.md
   git status --short

Review staged changes:

.. code:: bash

   git diff \
   --cached \
   --stat
   git diff \
   --cached

Commit:

.. code:: bash

   git commit \
   -m "Improve universal pipeline reliability and validation"

Do not claim that a remote upload succeeded until the push output and remote branch have been confirmed.

.. _19-58-post-update-validation-record:

19.58 Post-update validation record
-----------------------------------

Create a compact maintenance record:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   REPORT="validation/update_work/update_${TIMESTAMP}.tsv"
   mkdir -p \
   "$(dirname "$REPORT")"
   {
   printf 'field\tvalue\n'
   printf 'updated_utc\t%s\n' \
   "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
   printf 'git_commit\t%s\n' \
   "$(git rev-parse HEAD)"
   printf 'git_branch\t%s\n' \
   "$(git branch --show-current)"
   printf 'structural_preflight\tpassed\n'
   printf 'targeted_tests\tpassed\n'
   printf 'patients_01_12_audit\tpassed\n'
   printf 'patient_13_status\tnot_executed\n'
   } > "$REPORT"
   column \
   --separator $'\t' \
   --table \
   "$REPORT"

Add a description of:

-  the problem;

-  the root cause;

-  the universal correction;

-  tests executed;

-  outputs affected;

-  limitations.

.. _19-59-common-unsafe-troubleshooting-actions:

19.59 Common unsafe troubleshooting actions
-------------------------------------------

+-----------------------------------------------------------------------------------------------------------------------------+
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | **Unsafe action**                                             | **Why it is unsafe**                                    | |
| +===============================================================+=========================================================+ |
| | Editing the original VCF                                      | Destroys input provenance                               | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Using --check-ref s without investigation                     | May alter allele and genotype interpretation            | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Deleting failed results immediately                           | Removes diagnostic evidence                             | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Running --force without backup                                | Replaces previous outputs                               | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Adding a patient-specific condition to the scorer             | Breaks universal behaviour                              | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Matching ClinPGx by rsID alone                                | Can assign the wrong allele                             | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Treating missing ClinVar as benign                            | Confuses absent evidence with benign evidence           | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Updating canonical scores after failure                       | Hides regressions                                       | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Replacing all resources simultaneously                        | Makes the cause of changed results unclear              | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Deleting previous audit directories                           | Removes historical validation                           | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Committing SIFs or reference databases                        | Creates oversized and unreproducible repository history | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Uploading real patient outputs                                | Creates a privacy risk                                  | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Using broad rm -rf commands                                   | Can destroy validated resources and outputs             | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Ignoring a checksum failure                                   | Accepts unexplained file changes                        | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
| | Claiming a pipeline stage succeeded from file existence alone | The file may be empty or incomplete                     | |
| +---------------------------------------------------------------+---------------------------------------------------------+ |
+=============================================================================================================================+
| **19.60 Troubleshooting decision table**                                                                                    |
+-----------------------------------------------------------------------------------------------------------------------------+
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | **Symptom**                   | **First check**            | **Next action**                                  |           |
| +===============================+============================+==================================================+           |
| | Pipeline stops immediately    | Launcher log               | Validate arguments and paths                     |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | VCF rejected                  | Intake report              | Check sample, build and VCF structure            |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | REF mismatch                  | FASTA and build            | Confirm GRCh38 and source alleles                |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | No VEP output                 | VEP log and cache          | Check cache release and bind paths               |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | No CSQ                        | VEP header                 | Confirm VCF output mode                          |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | No ANN                        | SnpEff log and database    | Match database identifier                        |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | No ClinVar matches            | Exact allele comparison    | Check build, chromosome and normalisation        |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | SpliceAI empty                | SpliceAI log               | Check FASTA and routed variant type              |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | AnnotSV fails                 | AnnotSV log and BED        | Check annotation directory and four-column input |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | No Scoresheet.txt             | ClassifyCNV log            | Check result directory and build option          |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | ISV fails                     | Input header and container | Check package and model                          |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | Phenotype score absent        | HPO path                   | Validate exact patient matching                  |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | Wrong disease name            | G2P and MONDO tables       | Review disease precedence                        |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | Wrong inheritance             | GT, sex and ploidy         | Run inheritance tests                            |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | False compound-het            | PS/PID and haplotypes      | Run compound-het test                            |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | Wrong PGx allele              | REF and ALT                | Run allele-aware test                            |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | Repeat appears in SNV ranking | Routing output             | Correct repeat routing                           |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | Score changes                 | Source/resource checksums  | Compare intermediate evidence                    |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | Master table missing rows     | Join keys                  | Trace stable candidate key                       |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | Output checksum fails         | File modification          | Investigate before regenerating                  |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | Disk full                     | df and du                  | Archive or remove reviewed temporary files       |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
| | Process killed                | Memory usage               | Reduce threads or memory allocation              |           |
| +-------------------------------+----------------------------+--------------------------------------------------+           |
+-----------------------------------------------------------------------------------------------------------------------------+

.. _19-61-complete-maintenance-readiness-check:

19.61 Complete maintenance readiness check
------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   echo "=== 1. Repository state ==="
   git status --short
   git rev-parse HEAD
   echo
   echo "=== 2. Essential commands ==="
   for command_name in \
   python \
   bash \
   bcftools \
   bgzip \
   tabix \
   apptainer \
   sha256sum
   do
   command -v "$command_name"
   done
   echo
   echo "=== 3. Storage and memory ==="
   df -h .
   free -h
   echo
   echo "=== 4. Pipeline syntax ==="
   while IFS= read -r -d '' script; do
   bash -n "$script"
   done < <(
   find pipeline \
   -type f \
   -name '*.sh' \
   -print0
   )
   while IFS= read -r -d '' script; do
   python -m py_compile "$script"
   done < <(
   find pipeline validation \
   -type f \
   -name '*.py' \
   -print0
   )
   echo
   echo "=== 5. Targeted tests ==="
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
   python "$test_script"
   done
   echo
   echo "=== 6. Structural preflight ==="
   bash \
   pipeline/tests/run_vcf_structural_preflight.sh
   echo
   echo "=== 7. Final behavioural audit ==="
   python \
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py
   echo
   echo "PASS: Maintenance readiness checks completed."

A modified source tree may intentionally fail the historical source-checksum manifest. The behavioural and regression results must then be documented in a new audit.

.. _19-62-failure-recovery-completion-criteria:

19.62 Failure-recovery completion criteria
------------------------------------------

Failure recovery is complete when:

✓ The original input remained unchanged

✓ The failed run was archived

✓ Logs and partial outputs were preserved

✓ The first failed stage was identified

✓ The failure category was determined

✓ The underlying cause was corrected

✓ No patient-specific exception was introduced

✓ The relevant targeted test passed

✓ All source files passed syntax validation

✓ The complete regression suite passed

✓ The affected case was rerun safely

✓ Old and new results were compared

✓ Any score changes were explained

✓ Production and validation resources remained isolated

✓ Repeat and unsupported records remained correctly routed

✓ ClinPGx matching remained allele-aware

✓ Inheritance and compound-heterozygous logic remained valid

✓ The final Patients 01–12 behavioural audit passed

✓ Patient 13 remained documented as not executed

✓ A maintenance record was created

✓ Sensitive data remained local

.. _19-63-resource-maintenance-completion-criteria:

19.63 Resource-maintenance completion criteria
----------------------------------------------

A resource update is complete when:

✓ The previous resource was archived

✓ The previous checksum was recorded

✓ The new release and source were documented

✓ The new file passed integrity checks

✓ The new schema was reviewed

✓ Genome build and chromosome convention were confirmed

✓ Derived indexes or caches were rebuilt

✓ Targeted resource tests passed

✓ Patients 01–12 were re-evaluated

✓ Changed annotations and scores were explained

✓ The previous audit remained preserved

✓ A new dated audit was created after approval

✓ The active resource pointer was updated deliberately

✓ Rollback remained possible

.. _19-64-safe-update-completion-criteria:

19.64 Safe-update completion criteria
-------------------------------------

A pipeline update is complete when:

✓ Work was performed on a separate maintenance branch

✓ Pre-update source checksums were recorded

✓ The code change addressed a universal cause

✓ The change contained no patient-specific candidate rule

✓ Git diff was reviewed

✓ Conflict markers and whitespace errors were absent

✓ Bash and Python syntax checks passed

✓ The relevant targeted tests passed

✓ The complete regression suite passed

✓ Structural VCF preflight passed

✓ Canonical candidate identities remained correct

✓ Routed-repeat behaviour remained correct

✓ PGx validation outputs remained correct

✓ Source, resource and output changes were documented

✓ Large and sensitive files were not staged

✓ Previous audit records were preserved

✓ The update was committed only after validation

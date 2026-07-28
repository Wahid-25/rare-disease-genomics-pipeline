.. _20-reproducibility-data-governance-privacy-protection-and-github-repository-mana:

20. Reproducibility, Data Governance, Privacy Protection and GitHub Repository Management
=========================================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


A genomic-analysis pipeline must preserve not only its source code but also the relationship between:

-  

   .. container::

      Input data

-  

   .. container::

      Pipeline version

-  

   .. container::

      Reference resources

-  

   .. container::

      Software environment

-  

   .. container::

      Commands executed

-  

   .. container::

      Generated outputs

-  

   .. container::

      Validation results

Reproducibility means that another authorised analyst can determine exactly how a result was produced and can repeat the analysis using the same inputs, resources and source code.

Data governance ensures that genomic and phenotype data are stored, processed, shared and deleted according to defined rules. Because genomic information is inherently identifying and may reveal information about biological relatives, it requires stronger protection than ordinary project data.

The project therefore separates:

GitHub-tracked source and documentation

│

├── compact, non-identifying validation material

└── reproducibility manifests and tests

Local protected project data

│

├── patient or case VCFs

├── phenotype files

├── detailed outputs

├── reference databases

├── containers

└── archives and failed-run evidence

The GitHub repository must never become the storage location for real case data or large licensed resources.

.. _20-1-reproducibility-objectives:

20.1 Reproducibility objectives
-------------------------------

The project’s reproducibility system should allow an authorised analyst to answer:

-  

   .. container::

      Which input file was analysed?

-  

   .. container::

      Which sample was selected?

-  

   .. container::

      Which genome build was used?

-  

   .. container::

      Which HPO terms were supplied?

-  

   .. container::

      Which pipeline commit produced the result?

-  

   .. container::

      Which resource mode was active?

-  

   .. container::

      Which reference-resource releases were used?

-  

   .. container::

      Which containers and tools were used?

-  

   .. container::

      Which commands and settings were applied?

-  

   .. container::

      Which outputs were generated?

-  

   .. container::

      Did the validation suite pass?

-  

   .. container::

      Have any files changed since the analysis?

A result that cannot answer these questions should not be treated as fully reproducible.

.. _20-2-levels-of-reproducibility:

20.2 Levels of reproducibility
------------------------------

The project uses several reproducibility levels.

.. _20-2-1-source-reproducibility:

20.2.1 Source reproducibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Source reproducibility records:

-  

   .. container::

      Git commit

-  

   .. container::

      Git branch

-  

   .. container::

      Pipeline source checksums

-  

   .. container::

      Launcher paths

-  

   .. container::

      Test-script checksums

It confirms which source code was responsible for the analysis.

.. _20-2-2-input-reproducibility:

20.2.2 Input reproducibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Input reproducibility records:

-  

   .. container::

      Original VCF path or protected identifier

-  

   .. container::

      Original VCF SHA-256 checksum

-  

   .. container::

      Selected sample

-  

   .. container::

      Phenotype-file checksum

-  

   .. container::

      Reported sex

-  

   .. container::

      Resolved sex

-  

   .. container::

      Genome build

-  

   .. container::

      Case identifier

The original source file must not be edited after its checksum is recorded.

.. _20-2-3-resource-reproducibility:

20.2.3 Resource reproducibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resource reproducibility records:

-  

   .. container::

      Reference FASTA checksum

-  

   .. container::

      VEP cache release

-  

   .. container::

      SnpEff database

-  

   .. container::

      ClinVar release

-  

   .. container::

      ClinGen dosage resource

-  

   .. container::

      G2P resource and mode

-  

   .. container::

      HPO release

-  

   .. container::

      MONDO release

-  

   .. container::

      ClinPGx reference checksum

A different resource release may produce a different result even when the source code and input remain unchanged.

.. _20-2-4-environment-reproducibility:

20.2.4 Environment reproducibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Environment reproducibility records:

-  

   .. container::

      Operating system

-  

   .. container::

      Python version

-  

   .. container::

      Python package environment

-  

   .. container::

      Apptainer version

-  

   .. container::

      Container checksums

-  

   .. container::

      bcftools version

-  

   .. container::

      Java version

-  

   .. container::

      Hardware-relevant run settings

.. _20-2-5-output-reproducibility:

20.2.5 Output reproducibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Output reproducibility records:

-  

   .. container::

      Output file paths

-  

   .. container::

      Output checksums

-  

   .. container::

      Case summary

-  

   .. container::

      Master-table checksum

-  

   .. container::

      Important intermediate-file checksums

-  

   .. container::

      Completion status

-  

   .. container::

      Warnings

.. _20-3-reproducibility-manifest:

20.3 Reproducibility manifest
-----------------------------

The project uses:

pipeline/case_workflow/00c_build_reproducibility_manifest.py

The manifest should record, where available:

-  

   .. container::

      case_id

-  

   .. container::

      sample_id

-  

   .. container::

      analysis_mode

-  

   .. container::

      resource_mode

-  

   .. container::

      pipeline_commit

-  

   .. container::

      run_timestamp

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

      genome_build

-  

   .. container::

      reference_fasta

-  

   .. container::

      reference_fasta_sha256

-  

   .. container::

      vep_version

-  

   .. container::

      vep_cache_release

-  

   .. container::

      snpeff_version

-  

   .. container::

      snpeff_database

-  

   .. container::

      clinvar_release

-  

   .. container::

      g2p_resource

-  

   .. container::

      hpo_release

-  

   .. container::

      mondo_release

-  

   .. container::

      clinpgx_reference_sha256

-  

   .. container::

      container checksums

-  

   .. container::

      tool versions

-  

   .. container::

      run parameters

-  

   .. container::

      output paths

-  

   .. container::

      output checksums

-  

   .. container::

      final status

The complete manifest should remain local with the case result.

A compact, non-identifying validation manifest may be tracked in GitHub.

.. _20-3-1-validate-the-manifest-builder-source:

20.3.1 Validate the manifest-builder source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/00c_build_reproducibility_manifest.py"
   if [[ ! -s "$SCRIPT" ]]; then
   echo "ERROR: Reproducibility-manifest builder is missing."
   exit 1
   fi
   python -m py_compile "$SCRIPT"
   echo "PASS: Reproducibility-manifest builder passed syntax validation."

Inspect its interface without guessing arguments:

.. code:: bash

   if python "$SCRIPT" --help \
   > /tmp/reproducibility_manifest_help.txt \
   2>&1
   then
   cat /tmp/reproducibility_manifest_help.txt
   else
   echo "INFO: No standard --help interface was returned."
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$SCRIPT" \
   || true
   fi
   rm -f /tmp/reproducibility_manifest_help.txt

The universal launcher should remain responsible for invoking this script with the correct paths.

.. _20-4-sha-256-checksums:

20.4 SHA-256 checksums
----------------------

The project uses SHA-256 to detect unexpected file changes.

A checksum is a fixed-length value calculated from file contents.

If one byte changes, the checksum normally changes.

Checksums can show that:

Two files are byte-for-byte identical

or:

A file has changed since the checksum was created

A checksum does not prove that the original file was biologically correct or obtained from a trustworthy source. It only verifies integrity relative to the recorded value.

.. _20-4-1-create-a-checksum-for-one-file:

20.4.1 Create a checksum for one file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   sha256sum \
   input.vcf.gz \
   > input.vcf.gz.sha256

Verify:

.. code:: bash

   sha256sum \
   --check \
   input.vcf.gz.sha256

Expected:

input.vcf.gz: OK

.. _20-4-2-checksum-a-case-input-and-phenotype-file:

20.4.2 Checksum a case input and phenotype file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   SOURCE_VCF="/absolute/path/to/case_001.raw.vcf.gz"
   HPO_FILE="/absolute/path/to/case_001.phenotypes.txt"
   MANIFEST_DIR="input/cases/$CASE_ID/manifests"
   INPUT_HASHES="$MANIFEST_DIR/source_inputs.sha256"
   mkdir -p "$MANIFEST_DIR"
   sha256sum \
   "$SOURCE_VCF" \
   "$HPO_FILE" \
   > "$INPUT_HASHES"
   sha256sum \
   --check \
   "$INPUT_HASHES"

This file may contain sensitive absolute paths and should remain local.

.. _20-4-3-checksum-a-result-directory:

20.4.3 Checksum a result directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   CASE_RESULTS="results/cases/$CASE_ID"
   CHECKSUM_FILE="$CASE_RESULTS/manifests/generated_outputs.sha256"
   mkdir -p \
   "$(dirname "$CHECKSUM_FILE")"
   find "$CASE_RESULTS" \
   -type f \
   ! -path "$CHECKSUM_FILE" \
   ! -name '*.tmp' \
   ! -name '*.partial' \
   -print0 |
   sort -z |
   xargs -0 sha256sum \
   > "$CHECKSUM_FILE"

Verify:

.. code:: bash

   sha256sum \
   --check \
   "$CHECKSUM_FILE"

The checksum manifest must not include itself.

.. _20-5-resource-version-inventory:

20.5 Resource version inventory
-------------------------------

The project should maintain a resource inventory describing all active local resources.

A resource inventory may contain:

-  

   .. container::

      resource_name

-  

   .. container::

      release

-  

   .. container::

      genome_build

-  

   .. container::

      local_path

-  

   .. container::

      source

-  

   .. container::

      retrieval_date

-  

   .. container::

      sha256

-  

   .. container::

      licence_or_access_note

-  

   .. container::

      active_status

Create a compact local inventory:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   OUTPUT="results/environment/resource_inventory.tsv"
   mkdir -p \
   "$(dirname "$OUTPUT")"
   {
   printf 'resource\tpath\tsize_bytes\tsha256\n'
   FILES=(
   resources/reference/hg38.fa
   resources/reference/hg38.fa.fai
   resources/clinvar/clinvar.vcf.gz
   resources/clinvar/clinvar.vcf.gz.tbi
   resources/clingen/clingen_dosage_genes_regions.csv
   resources/gene_disease/g2p/AllG2P.official.csv
   resources/clinpgx/local_curated_pgx_reference.csv
   )
   for path in "${FILES[@]}"; do
   if [[ ! -s "$path" ]]; then
   printf '%s\t%s\t%s\t%s\n' \
   "$(basename "$path")" \
   "$path" \
   "missing" \
   "missing"
   continue
   fi
   printf '%s\t%s\t%s\t%s\n' \
   "$(basename "$path")" \
   "$path" \
   "$(stat -c '%s' "$path")" \
   "$(sha256sum "$path" | awk '{print $1}')"
   done
   } > "$OUTPUT"
   column \
   --separator $'\t' \
   --table \
   "$OUTPUT"

Release dates and source descriptions should be added to the permanent documentation.

.. _20-6-container-reproducibility:

20.6 Container reproducibility
------------------------------

Apptainer definition files may be stored in GitHub, but generated SIF images remain local.

Track:

-  

   .. container::

      containers/core_tools.def

-  

   .. container::

      containers/vep.def or documented official image source

-  

   .. container::

      containers/snpeff.def

-  

   .. container::

      containers/spliceai.def

-  

   .. container::

      containers/annotsv.def where applicable

-  

   .. container::

      containers/classifycnv.def where applicable

-  

   .. container::

      containers/isv.def

Do not track:

containers/\*.sif

The SIF checksum identifies the exact built container used in an analysis.

.. _20-6-1-generate-a-container-inventory:

20.6.1 Generate a container inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   OUTPUT="results/environment/container_inventory.tsv"
   mkdir -p \
   "$(dirname "$OUTPUT")"
   {
   printf 'container\tsize_bytes\tsha256\n'
   find containers \
   -maxdepth 1 \
   -type f \
   -name '*.sif' \
   -print0 |
   sort -z |
   while IFS= read -r -d '' container; do
   printf '%s\t%s\t%s\n' \
   "$container" \
   "$(stat -c '%s' "$container")" \
   "$(sha256sum "$container" | awk '{print $1}')"
   done
   } > "$OUTPUT"
   column \
   --separator $'\t' \
   --table \
   "$OUTPUT"

Because SIF images may be large, this inventory should remain local.

.. _20-7-python-environment-reproducibility:

20.7 Python-environment reproducibility
---------------------------------------

The project uses:

.venv/

The virtual environment itself should not be committed.

Record the installed packages:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   mkdir -p results/environment
   python --version \
   > results/environment/python_version.txt
   python -m pip freeze \
   > results/environment/python_packages.freeze.txt

Inspect:

.. code:: bash

   head -n 30 \
   results/environment/python_packages.freeze.txt

A package freeze records the current environment but may include transitive packages not explicitly required by the pipeline.

A curated dependency file should be maintained separately where possible.

.. _20-8-command-and-execution-logging:

20.8 Command and execution logging
----------------------------------

A reproducible pipeline should log:

-  

   .. container::

      Command executed

-  

   .. container::

      Start time

-  

   .. container::

      End time

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

      Resource paths

-  

   .. container::

      Thread count

-  

   .. container::

      Memory settings

The principal launchers write case logs under:

.. code:: bash

   results/cases/<case_id>/logs/

Environment variables such as:

THREADS

JAVA_MEM

should be recorded in the case manifest.

A result produced using:

.. code:: bash

   THREADS=2
   JAVA_MEM=4g

may be biologically identical to one produced using higher settings, but the actual execution settings should still be documented.

.. _20-9-data-governance-principles:

20.9 Data-governance principles
-------------------------------

The project should follow these data-governance principles:

-  

   .. container::

      Data minimisation

-  

   .. container::

      Purpose limitation

-  

   .. container::

      Controlled access

-  

   .. container::

      Integrity protection

-  

   .. container::

      Confidentiality

-  

   .. container::

      Traceability

-  

   .. container::

      Retention control

-  

   .. container::

      Secure deletion

-  

   .. container::

      Incident documentation

.. _20-9-1-data-minimisation:

20.9.1 Data minimisation
~~~~~~~~~~~~~~~~~~~~~~~~

Store only the information needed for analysis.

A case identifier should not contain:

-  

   .. container::

      Patient name

-  

   .. container::

      Date of birth

-  

   .. container::

      Hospital number

-  

   .. container::

      National identity number

-  

   .. container::

      Address

-  

   .. container::

      Phone number

-  

   .. container::

      Email address

Use:

case_001

instead of a personally identifying label.

.. _20-9-2-purpose-limitation:

20.9.2 Purpose limitation
~~~~~~~~~~~~~~~~~~~~~~~~~

Case data should be used only for the approved analytical or educational purpose.

Do not reuse genomic data for:

-  unrelated research;

-  public demonstrations;

-  model training;

-  personal sharing;

-  unapproved teaching material.

Synthetic validation files are preferred for demonstrations and documentation.

.. _20-9-3-controlled-access:

20.9.3 Controlled access
~~~~~~~~~~~~~~~~~~~~~~~~

Access should be limited to authorised project members.

Protected data should not be copied into:

-  

   .. container::

      Public GitHub repositories

-  

   .. container::

      Unapproved cloud drives

-  

   .. container::

      Shared messaging applications

-  

   .. container::

      Public notebooks

-  

   .. container::

      Email attachments without approval

Local folder permissions should prevent unnecessary access.

.. _20-9-4-integrity:

20.9.4 Integrity
~~~~~~~~~~~~~~~~

Integrity controls include:

-  

   .. container::

      Read-only source copies

-  

   .. container::

      Checksums

-  

   .. container::

      Version-controlled source code

-  

   .. container::

      Immutable audit snapshots

-  

   .. container::

      Separate failed-run archives

-  

   .. container::

      Controlled resource updates

.. _20-9-5-traceability:

20.9.5 Traceability
~~~~~~~~~~~~~~~~~~~

Every important result should link back to:

-  

   .. container::

      Input checksum

-  

   .. container::

      Case manifest

-  

   .. container::

      Pipeline commit

-  

   .. container::

      Resource versions

-  

   .. container::

      Tool logs

-  

   .. container::

      Output checksum

.. _20-10-genomic-data-privacy:

20.10 Genomic-data privacy
--------------------------

Genomic data are difficult to anonymise completely.

Even after removing a name, a VCF may still reveal:

-  

   .. container::

      Rare inherited variants

-  

   .. container::

      Biological relationships

-  

   .. container::

      Ancestry information

-  

   .. container::

      Disease risks

-  

   .. container::

      Carrier status

-  

   .. container::

      Pharmacogenomic information

-  

   .. container::

      Potential familial implications

Therefore, a VCF should be treated as sensitive personal data even when direct identifiers have been removed.

.. _20-11-de-identification:

20.11 De-identification
-----------------------

De-identification should remove direct identifiers from:

-  

   .. container::

      Filenames

-  

   .. container::

      VCF sample names

-  

   .. container::

      Metadata

-  

   .. container::

      Phenotype files

-  

   .. container::

      Reports

-  

   .. container::

      Logs

-  

   .. container::

      Screenshots

-  

   .. container::

      Absolute paths

However, de-identification does not guarantee anonymity.

A genomic dataset can remain re-identifiable through its unique variant pattern.

.. _20-11-1-inspect-vcf-sample-names:

20.11.1 Inspect VCF sample names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   bcftools query \
   --list-samples \
   "/absolute/path/to/input.vcf.gz"

A sample name such as:

John_Smith_2005

should not be used in project outputs.

Use a controlled identifier such as:

case_001_sample

when authorised preparation requires renaming.

Preserve the original-to-project identifier mapping only in a secure, separate location.

.. _20-11-2-inspect-text-outputs-for-identifiers:

20.11.2 Inspect text outputs for identifiers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_DIR="results/cases/case_001"
   grep -RInE \
   --include='*.tsv' \
   --include='*.csv' \
   --include='*.txt' \
   --include='*.md' \
   'patient.name|date.of.birth|\bDOB\b|hospital|phone|email|address|national.id|passport' \
   "$CASE_DIR" \
   || true

This is a screening method, not a guarantee of complete de-identification.

Manual review remains necessary.

.. _20-12-absolute-path-privacy:

20.12 Absolute-path privacy
---------------------------

A local path may expose a username or organisational structure.

For example:

.. code:: bash

   /home/wahid/private_patient_data/

should not appear in public documentation.

Search:

.. code:: bash

   grep -RInE \
   --include='*.md' \
   --include='*.txt' \
   --include='*.tsv' \
   --include='*.csv' \
   '/home/[^/]+/|/mnt/[a-zA-Z]/Users/[^/]+' \
   pipeline \
   validation \
   README.md \
   || true

Use project-relative paths in public documentation:

.. code:: bash

   input/cases/<case_id>/
   results/cases/<case_id>/

.. _20-13-local-file-permissions:

20.13 Local file permissions
----------------------------

Inspect permissions:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find \
   input/cases \
   results/cases \
   -maxdepth 3 \
   -printf '%M\t%u:%g\t%p\n' \
   2>/dev/null |
   head -n 50

Restrict a case directory to the current user:

.. code:: bash

   chmod -R \
   u=rwX,go= \
   input/cases/case_001 \
   results/cases/case_001

Verify:

.. code:: bash

   find \
   input/cases/case_001 \
   results/cases/case_001 \
   -maxdepth 2 \
   -printf '%M\t%u:%g\t%p\n'

Do not apply restrictive permissions blindly when an authorised team requires shared group access. Use the approved institutional access model.

.. _20-14-backup-policy:

20.14 Backup policy
-------------------

A protected backup should include:

-  

   .. container::

      Original input

-  

   .. container::

      Phenotype file

-  

   .. container::

      Intake report

-  

   .. container::

      Final master table

-  

   .. container::

      Human-readable report

-  

   .. container::

      Reproducibility manifest

-  

   .. container::

      Important logs

-  

   .. container::

      Checksums

It may also include intermediate annotation files when storage permits.

Backups should be:

-  

   .. container::

      Encrypted where required

-  

   .. container::

      Access controlled

-  

   .. container::

      Checksummed

-  

   .. container::

      Stored separately from the working copy

-  

   .. container::

      Tested for restoration

-  

   .. container::

      Subject to retention policy

.. _20-14-1-create-a-local-case-archive:

20.14.1 Create a local case archive
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   ARCHIVE_DIR="$PWD/local_case_archives"
   ARCHIVE="$ARCHIVE_DIR/${CASE_ID}_${TIMESTAMP}.tar.gz"
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
   echo "Archive: $ARCHIVE"

The archive should not be uploaded to GitHub.

.. _20-14-2-test-an-archive-without-extracting-it:

20.14.2 Test an archive without extracting it
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   tar \
   --list \
   --file "$ARCHIVE" \
   > /dev/null
   echo "PASS: Archive structure is readable."

Display the first entries:

.. code:: bash

   tar \
   --list \
   --file "$ARCHIVE" |
   head -n 30

.. _20-15-retention-policy:

20.15 Retention policy
----------------------

The project should define how long different file categories are retained.

A conceptual retention table is:

+----------------------------+---------------------------------------------+
| **File category**          | **Recommended handling**                    |
+============================+=============================================+
| Original case input        | Retain according to approved project policy |
+----------------------------+---------------------------------------------+
| Input checksum             | Retain with the case record                 |
+----------------------------+---------------------------------------------+
| Final report               | Retain according to approved policy         |
+----------------------------+---------------------------------------------+
| Reproducibility manifest   | Retain with final output                    |
+----------------------------+---------------------------------------------+
| Important logs             | Retain through validation and review        |
+----------------------------+---------------------------------------------+
| Intermediate annotations   | Retain where needed for reproducibility     |
+----------------------------+---------------------------------------------+
| Temporary files            | Remove after final verification             |
+----------------------------+---------------------------------------------+
| Failed-run evidence        | Retain until issue resolution and audit     |
+----------------------------+---------------------------------------------+
| Synthetic validation files | Retain with project validation              |
+----------------------------+---------------------------------------------+
| Large downloaded resources | Retain while active and licensed            |
+----------------------------+---------------------------------------------+
| Deprecated resources       | Archive or securely remove after approval   |
+----------------------------+---------------------------------------------+

The manual should not invent a legal retention period. The responsible institution or project supervisor should define it.

.. _20-16-secure-deletion:

20.16 Secure deletion
---------------------

Deleting a file with:

.. code:: bash

   rm file

removes the directory entry but may not guarantee that the underlying storage blocks are unrecoverable.

Secure deletion behaviour depends on:

-  

   .. container::

      Filesystem

-  

   .. container::

      Solid-state drive

-  

   .. container::

      WSL storage

-  

   .. container::

      Snapshots

-  

   .. container::

      Backups

-  

   .. container::

      Cloud synchronisation

Therefore, sensitive-data deletion should follow the approved storage and institutional process.

Before deleting any case:

1. confirm authorisation;

2. confirm retention requirements;

3. identify all working copies;

4. identify backups and archives;

5. document the deletion;

6. confirm that no Git commit contains the data.

.. _20-17-privacy-incident-response:

20.17 Privacy-incident response
-------------------------------

A privacy incident may include:

-  

   .. container::

      Patient VCF staged in Git

-  

   .. container::

      Sensitive output pushed to a remote repository

-  

   .. container::

      Identifying sample name included in documentation

-  

   .. container::

      Case archive copied to an unapproved location

-  

   .. container::

      Credentials committed to Git

Immediate actions should include:

-  

   .. container::

      Stop further sharing

-  

   .. container::

      Preserve incident evidence

-  

   .. container::

      Restrict access

-  

   .. container::

      Notify the responsible supervisor

-  

   .. container::

      Remove exposed data from the active location

-  

   .. container::

      Assess Git history and remote copies

-  

   .. container::

      Rotate exposed credentials

-  

   .. container::

      Document the incident

Simply deleting a file in a later commit does not remove it from earlier Git history.

.. _20-18-github-repository-purpose:

20.18 GitHub repository purpose
-------------------------------

The GitHub repository should contain:

-  

   .. container::

      Pipeline source code

-  

   .. container::

      Container definition files

-  

   .. container::

      Resource-setup scripts

-  

   .. container::

      Test scripts

-  

   .. container::

      Compact synthetic validation material

-  

   .. container::

      Audit logic

-  

   .. container::

      Documentation

-  

   .. container::

      README files

-  

   .. container::

      .gitignore

-  

   .. container::

      It should not contain:

-  

   .. container::

      SIF images

-  

   .. container::

      Reference FASTA files

-  

   .. container::

      VEP caches

-  

   .. container::

      SnpEff databases

-  

   .. container::

      AnnotSV annotations

-  

   .. container::

      ANNOVAR databases

-  

   .. container::

      Real patient VCFs

-  

   .. container::

      Real phenotype files

-  

   .. container::

      Detailed patient outputs

-  

   .. container::

      Private case archives

-  

   .. container::

      Secrets or access tokens

The repository is a source-code and documentation repository, not a genomic-data repository.

.. _20-19-current-repository-identity:

20.19 Current repository identity
---------------------------------

The project repository is intended to be:

.. code:: bash

   Wahid-25/rare-disease-genomics-pipeline

The repository may be private.

The local project root is:

.. code:: bash

   ~/rare_disease_project

The last known local validated commit was:

0e40b60

The current remote connection and push status must be verified locally. A commit existing on the local main branch does not prove that it was uploaded successfully.

.. _20-20-verify-local-git-status:

20.20 Verify local Git status
-----------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   echo "=== Repository root ==="
   git rev-parse \
   --show-toplevel
   echo
   echo "=== Current branch ==="
   git branch \
   --show-current
   echo
   echo "=== Current commit ==="
   git rev-parse HEAD
   echo
   echo "=== Working tree ==="
   git status --short

A clean status produces no lines after:

=== Working tree ===

.. _20-21-verify-configured-remotes:

20.21 Verify configured remotes
-------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git remote -v

If no output appears, no Git remote is currently configured.

Inspect the remote called origin:

.. code:: bash

   if git remote get-url origin \
   > /tmp/rare_disease_origin_url.txt \
   2>/dev/null
   then
   echo "Origin:"
   cat /tmp/rare_disease_origin_url.txt
   else
   echo "INFO: No origin remote is configured."
   fi
   rm -f /tmp/rare_disease_origin_url.txt

Do not assume that the remote still exists merely because it was configured previously.

.. _20-22-confirm-local-and-remote-branch-state:

20.22 Confirm local and remote branch state
-------------------------------------------

First fetch:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git fetch \
   --all \
   --prune

Display local and upstream branches:

.. code:: bash

   git branch -vv

Check whether the current branch has an upstream:

.. code:: bash

   if UPSTREAM="$(
   git rev-parse \
   --abbrev-ref \
   --symbolic-full-name \
   '@{upstream}' \
   2>/dev/null
   )"
   then
   echo "Upstream branch: $UPSTREAM"
   else
   echo "INFO: Current branch has no configured upstream."
   fi

When an upstream exists, compare:

.. code:: bash

   git rev-list \
   --left-right \
   --count \
   HEAD..."$UPSTREAM"

The result is:

local-only commits remote-only commits

For example:

0 0

means the branches are aligned.

.. _20-23-verify-whether-a-specific-commit-exists-remotely:

20.23 Verify whether a specific commit exists remotely
------------------------------------------------------

Set the local commit:

.. code:: bash

   LOCAL_COMMIT="$(
   git rev-parse HEAD
   )"
   echo "Local commit: $LOCAL_COMMIT"

Search fetched remote branches:

.. code:: bash

   REMOTE_BRANCHES="$(
   git branch \
   --remotes \
   --contains "$LOCAL_COMMIT" \
   2>/dev/null \
   || true
   )"
   if [[ -n "$REMOTE_BRANCHES" ]]; then
   echo "Commit appears in these fetched remote branches:"
   echo "$REMOTE_BRANCHES"
   else
   echo "The local commit was not found in fetched remote branches."
   fi

This is stronger evidence than merely seeing a local commit.

.. _20-24-configure-the-remote-when-absent:

20.24 Configure the remote when absent
--------------------------------------

Only after confirming the intended repository:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   REPOSITORY_URL="https://github.com/Wahid-25/rare-disease-genomics-pipeline.git"
   if git remote get-url origin \
   >/dev/null 2>&1
   then
   echo "Origin already exists:"
   git remote get-url origin
   else
   git remote add \
   origin \
   "$REPOSITORY_URL"
   echo "Origin added:"
   git remote -v
   fi

Do not replace an existing remote without reviewing it.

.. _20-25-authentication-verification:

20.25 Authentication verification
---------------------------------

Check GitHub CLI authentication:

.. code:: bash

   gh auth status

If GitHub CLI is not authenticated, the command reports the missing or invalid login.

The user may authenticate interactively through:

gh auth login

Do not place a personal access token directly inside:

-  

   .. container::

      Shell scripts

-  

   .. container::

      README files

-  

   .. container::

      Git remote URLs

-  

   .. container::

      Command history

-  

   .. container::

      Configuration files tracked by Git

.. _20-26-gitignore-policy:

20.26 .gitignore policy
-----------------------

The project .gitignore protects:

-  

   .. container::

      Large resources

-  

   .. container::

      Generated containers

-  

   .. container::

      Patient inputs

-  

   .. container::

      Patient results

-  

   .. container::

      Temporary files

-  

   .. container::

      Python caches

-  

   .. container::

      Local archives

-  

   .. container::

      Failed runs

-  

   .. container::

      Historical backups

Inspect:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   if [[ ! -s .gitignore ]]; then
   echo "ERROR: .gitignore is missing or empty."
   exit 1
   fi
   cat .gitignore

The current project excludes large and sensitive directories while allowing selected compact validation and documentation files.

.. _20-27-confirm-sensitive-case-directories-are-ignored:

20.27 Confirm sensitive case directories are ignored
----------------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   git check-ignore -v \
   "input/cases/$CASE_ID" \
   "results/cases/$CASE_ID" \
   || true

Check a representative file:

.. code:: bash

   git check-ignore -v \
   "input/cases/$CASE_ID/prepared/${CASE_ID}.ready.vcf.gz" \
   || true

No output may mean that the path does not exist or is not ignored. Investigate before committing.

.. _20-28-audit-ignored-and-untracked-files:

20.28 Audit ignored and untracked files
---------------------------------------

List ignored files:

.. code:: bash

   git status \
   --short \
   --ignored

Show only untracked files:

.. code:: bash

   git ls-files \
   --others \
   --exclude-standard

Show tracked files:

.. code:: bash

   git ls-files

Search tracked paths for forbidden categories:

.. code:: bash

   git ls-files |
   grep -E \
   '(^|/)(input/cases|results/cases|containers/.*\.sif|resources/reference|resources/vep_cache|resources/snpeff_data)/' \
   || true

Every match should be reviewed.

.. _20-29-check-for-large-tracked-files:

20.29 Check for large tracked files
-----------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git ls-files -z |
   while IFS= read -r -d '' path; do
   [[ -f "$path" ]] || continue
   size="$(
   stat -c '%s' "$path"
   )"
   printf '%s\t%s\n' \
   "$size" \
   "$path"
   done |
   sort -nr |
   head -n 30

A large tracked file may indicate that:

-  

   .. container::

      A generated output was committed

-  

   .. container::

      A resource escaped .gitignore

-  

   .. container::

      A binary was added accidentally

.. _20-30-check-staged-files-before-committing:

20.30 Check staged files before committing
------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   echo "=== Staged paths ==="
   git diff \
   --cached \
   --name-status
   echo
   echo "=== Staged size summary ==="
   git diff \
   --cached \
   --name-only \
   --diff-filter=ACMRT |
   while IFS= read -r path; do
   [[ -f "$path" ]] || continue
   printf '%12s %s\n' \
   "$(stat -c '%s' "$path")" \
   "$path"
   done |
   sort -nr
   Check for sensitive directories:
   SENSITIVE_STAGED="$(
   git diff \
   --cached \
   --name-only |
   grep -E \
   '(^|/)(input/cases|results/cases|local_case_archives|failed_runs)/' \
   || true
   )"
   if [[ -n "$SENSITIVE_STAGED" ]]; then
   echo "ERROR: Sensitive case paths are staged:"
   echo "$SENSITIVE_STAGED"
   exit 1
   fi
   echo "PASS: No known sensitive case directory is staged."

.. _20-31-remove-an-accidentally-staged-file:

20.31 Remove an accidentally staged file
----------------------------------------

Unstage without deleting the local file:

.. code:: bash

   git restore \
   --staged \
   path/to/sensitive_file

Confirm:

.. code:: bash

   git status --short

Add the required ignore rule before continuing.

.. _20-32-check-for-secrets:

20.32 Check for secrets
-----------------------

Search tracked text files for common secret patterns:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   grep -RInE \
   --exclude-dir=.git \
   --exclude='*.sif' \
   --exclude='*.gz' \
   --exclude='*.zip' \
   --exclude='*.tar' \
   --exclude='*.tar.gz' \
   'ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|AWS_SECRET_ACCESS_KEY|api[_-]?key[[:space:]]*=' \
   . \
   || true

A match must be reviewed.

If a real credential was committed:

1. revoke or rotate it;

2. stop sharing the repository;

3. remove it from the current tree;

4. assess whether Git history must be rewritten;

5. document the incident.

.. _20-33-check-staged-content-for-personal-identifiers:

20.33 Check staged content for personal identifiers
---------------------------------------------------

.. code:: bash

   git diff \
   --cached \
   --name-only \
   --diff-filter=ACMRT |
   while IFS= read -r path; do
   [[ -f "$path" ]] || continue
   case "$path" in
   *.md|*.txt|*.tsv|*.csv|*.json|*.yaml|*.yml|*.py|*.sh)
   MATCHES="$(
   grep -nEi \
   'patient.name|date.of.birth|\bDOB\b|hospital.number|national.id|email.address|phone.number|home.address' \
   "$path" \
   || true
   )"
   if [[ -n "$MATCHES" ]]; then
   echo
   echo "REVIEW: $path"
   echo "$MATCHES"
   fi
   ;;
   esac
   done

This screening cannot detect every identifier.

.. _20-34-safe-commit-procedure:

20.34 Safe commit procedure
---------------------------

Before committing:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git status --short
   git diff --check
   git diff --cached --stat
   git diff --cached

Commit only the approved files:

.. code:: bash

   git commit \
   -m "Document and validate universal genomic pipeline"

Confirm:

.. code:: bash

   git log \
   --oneline \
   --decorate \
   -n 5

A successful commit updates the local repository only.

.. _20-35-safe-push-procedure:

20.35 Safe push procedure
-------------------------

Confirm the remote and branch:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git remote -v
   git branch -vv

Push the current branch:

.. code:: bash

   git push \
   --set-upstream \
   origin \
   main

A successful-looking local commit is not evidence that this push succeeded.

After pushing, fetch again:

.. code:: bash

   git fetch \
   origin \
   --prune

Confirm alignment:

.. code:: bash

   git rev-list \
   --left-right \
   --count \
   HEAD...origin/main

Expected:

0 0

Confirm that the local commit is contained in the remote branch:

.. code:: bash

   git branch \
   --remotes \
   --contains HEAD

Expected to include:

.. code:: bash

   origin/main

Only after these checks should the documentation state that the commit is present on the remote branch.

.. _20-36-repository-visibility:

20.36 Repository visibility
---------------------------

A private repository is appropriate when:

-  

   .. container::

      Development history is still being reviewed

-  

   .. container::

      Documentation contains internal paths

-  

   .. container::

      Validation materials require review

-  

   .. container::

      Licensing status is uncertain

-  

   .. container::

      Access should remain restricted

Changing a repository from private to public requires a complete review of:

-  

   .. container::

      Git history

-  

   .. container::

      Tracked files

-  

   .. container::

      Issues

-  

   .. container::

      Pull requests

-  

   .. container::

      Releases

-  

   .. container::

      Actions logs

-  

   .. container::

      Attached images

-  

   .. container::

      Documentation

-  

   .. container::

      Archived branches

Checking only the current main branch is insufficient.

.. _20-37-branch-management:

20.37 Branch management
-----------------------

Use branches for controlled changes.

Suggested branch categories are:

main

.. code:: bash

   maintenance/<description>
   documentation/<description>
   resource-update/<resource>
   feature/<description>

Create:

.. code:: bash

   git switch \
   -c documentation/word-manual

Review current branch:

.. code:: bash

   git branch \
   --show-current

Branches should not contain patient-specific data.

.. _20-38-tagging-validated-releases:

20.38 Tagging validated releases
--------------------------------

A Git tag can identify a validated source state.

Before tagging:

-  

   .. container::

      All source tests should pass

-  

   .. container::

      Structural preflight should pass

-  

   .. container::

      Final behavioural audit should pass

-  

   .. container::

      Documentation should identify the resource versions

-  

   .. container::

      Sensitive data should be absent

Create an annotated tag:

.. code:: bash

   git tag \
   --annotate \
   v1.0.0-validation \
   --message "Validated universal rare-disease and ClinPGx pipeline"

Inspect:

.. code:: bash

   git show \
   v1.0.0-validation \
   --no-patch

Push the tag only after confirming the remote connection:

.. code:: bash

   git push \
   origin \
   v1.0.0-validation

A tag identifies source code. It does not contain the large local resources unless those resources were separately archived and checksummed.

.. _20-39-github-readme-requirements:

20.39 GitHub README requirements
--------------------------------

The main README.md should explain:

-  

   .. container::

      Project purpose

-  

   .. container::

      Supported input

-  

   .. container::

      GRCh38 requirement

-  

   .. container::

      Main launchers

-  

   .. container::

      Directory structure

-  

   .. container::

      Installation summary

-  

   .. container::

      Resource requirements

-  

   .. container::

      Validation status

-  

   .. container::

      Privacy warning

-  

   .. container::

      Clinical-use limitation

-  

   .. container::

      Repository scope

-  

   .. container::

      It should not include:

-  

   .. container::

      Real patient details

-  

   .. container::

      Private local paths

-  

   .. container::

      Credentials

-  

   .. container::

      Large copied tool documentation

-  

   .. container::

      Unverified clinical claims

.. _20-40-placeholder-directory-readmes:

20.40 Placeholder directory READMEs
-----------------------------------

The project contains compact README files in otherwise ignored local directories such as:

containers/

.. code:: bash

   resources/reference/

results/

.. code:: bash

   input/cases/

These README files explain:

-  

   .. container::

      What belongs in the directory

-  

   .. container::

      What is intentionally excluded from Git

-  

   .. container::

      How the local content is generated

-  

   .. container::

      Why sensitive data must not be uploaded

Inspect:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find \
   containers \
   resources/reference \
   results \
   input/cases \
   -maxdepth 2 \
   -type f \
   -iname 'README*' \
   -print

These files allow the directory purpose to remain documented without tracking its large or sensitive contents.

.. _20-41-github-link-policy-in-the-word-report:

20.41 GitHub link policy in the Word report
-------------------------------------------

The Word report should link to GitHub for:

-  

   .. container::

      Long source scripts

-  

   .. container::

      Container definitions

-  

   .. container::

      Tests

-  

   .. container::

      Compact validation manifests

-  

   .. container::

      README documentation

-  

   .. container::

      Audit logic

The report should include commands directly when those commands are needed to reproduce:

-  

   .. container::

      Installation

-  

   .. container::

      Resource setup

-  

   .. container::

      Execution

-  

   .. container::

      Validation

-  

   .. container::

      Troubleshooting

Do not link to:

-  

   .. container::

      Patient inputs

-  

   .. container::

      Detailed patient outputs

-  

   .. container::

      Large resources

-  

   .. container::

      SIF files

-  

   .. container::

      Private case archives

Because the repository may remain private, a reader without access may not be able to open the source links. The written report should still describe each component adequately.

.. _20-42-git-history-and-sensitive-data-removal:

20.42 Git history and sensitive-data removal
--------------------------------------------

Removing a sensitive file from the latest commit does not remove it from earlier commits.

Check whether a path appears in history:

.. code:: bash

   git log \
   --all \
   -- \
   path/to/sensitive_file

Search object history by filename:

.. code:: bash

   git rev-list \
   --objects \
   --all |
   grep -F \
   'sensitive_file' \
   || true

If sensitive data were committed, history rewriting may be required.

History rewriting affects collaborators and remote branches and should be performed only with appropriate supervision.

The exposed data must also be removed from:

-  

   .. container::

      Remote forks

-  

   .. container::

      Clones

-  

   .. container::

      Pull requests

-  

   .. container::

      Releases

-  

   .. container::

      Actions artefacts

-  

   .. container::

      Caches

-  

   .. container::

      Backups

where applicable.

.. _20-43-github-actions-and-automated-workflows:

20.43 GitHub Actions and automated workflows
--------------------------------------------

Automated workflows can help run:

-  

   .. container::

      Python syntax tests

-  

   .. container::

      Bash syntax tests

-  

   .. container::

      Unit tests

-  

   .. container::

      Compact validation checks

-  

   .. container::

      Documentation builds

-  

   .. container::

      They should not download or expose:

-  

   .. container::

      Patient VCFs

-  

   .. container::

      Protected phenotype data

-  

   .. container::

      Licensed databases

-  

   .. container::

      Large private resources

-  

   .. container::

      Secrets in logs

Tests intended for GitHub Actions should use compact synthetic data.

The full resource-dependent pipeline remains better suited to the controlled local WSL environment unless secure compute and resource access are configured.

.. _20-44-reproducibility-versus-portability:

20.44 Reproducibility versus portability
----------------------------------------

The project is reproducible within its documented environment, but full portability requires access to:

-  

   .. container::

      Large reference resources

-  

   .. container::

      Compatible containers

-  

   .. container::

      Licensed or access-controlled databases

-  

   .. container::

      Adequate storage

Adequate memory

WSL or Linux-compatible execution

The GitHub repository alone is not sufficient to reproduce the complete analysis.

The repository provides:

-  

   .. container::

      Source code

-  

   .. container::

      Build definitions

-  

   .. container::

      Resource setup instructions

-  

   .. container::

      Tests

-  

   .. container::

      Documentation

-  

   .. container::

      Checksums

The analyst must obtain or build the large local resources separately.

.. _20-45-data-sharing-package:

20.45 Data-sharing package
--------------------------

When a non-identifying validation package must be shared, it should contain only:

-  

   .. container::

      Synthetic input

-  

   .. container::

      Expected compact result

-  

   .. container::

      Pipeline commit

-  

   .. container::

      Resource-version manifest

-  

   .. container::

      Test script

-  

   .. container::

      Checksum manifest

-  

   .. container::

      Documentation

-  

   .. container::

      It should not contain:

-  

   .. container::

      Real case data

-  

   .. container::

      Real case phenotype information

-  

   .. container::

      External case logs

-  

   .. container::

      Sensitive absolute paths

-  

   .. container::

      Large licensed resources

Create a compact validation archive only after reviewing every file.

.. _20-46-generate-a-repository-inventory:

20.46 Generate a repository inventory
-------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   OUTPUT="validation/repository_inventory.tsv"
   {
   printf 'tracked_path\tsize_bytes\tsha256\n'
   git ls-files -z |
   while IFS= read -r -d '' path; do
   if [[ -f "$path" ]]; then
   printf '%s\t%s\t%s\n' \
   "$path" \
   "$(stat -c '%s' "$path")" \
   "$(sha256sum "$path" | awk '{print $1}')"
   fi
   done
   } > "$OUTPUT"
   column \
   --separator $'\t' \
   --table \
   "$OUTPUT" |
   head -n 30

This generated inventory may change whenever tracked files change. Decide deliberately whether it should be committed or retained locally.

.. _20-47-complete-pre-commit-governance-check:

20.47 Complete pre-commit governance check
------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   echo "=== 1. Git status ==="
   git status --short
   echo
   echo "=== 2. Diff integrity ==="
   git diff --check
   git diff --cached --check
   echo
   echo "=== 3. Sensitive staged paths ==="
   SENSITIVE="$(
   git diff \
   --cached \
   --name-only |
   grep -E \
   '(^|/)(input/cases|results/cases|local_case_archives|failed_runs)/' \
   || true
   )"
   if [[ -n "$SENSITIVE" ]]; then
   echo "ERROR: Sensitive paths are staged:"
   echo "$SENSITIVE"
   exit 1
   fi
   echo "PASS: No known sensitive case paths are staged."
   echo
   echo "=== 4. Large staged files ==="
   LARGE_FILE_FAILURES=0
   while IFS= read -r path; do
   [[ -f "$path" ]] || continue
   size="$(
   stat -c '%s' "$path"
   )"
   if (( size > 50 * 1024 * 1024 )); then
   echo "ERROR: Staged file exceeds 50 MB:"
   echo "$size $path"
   LARGE_FILE_FAILURES=$((LARGE_FILE_FAILURES + 1))
   fi
   done < <(
   git diff \
   --cached \
   --name-only \
   --diff-filter=ACMRT
   )
   if (( LARGE_FILE_FAILURES > 0 )); then
   exit 1
   fi
   echo "PASS: No staged file exceeds 50 MB."
   echo
   echo "=== 5. Secret-pattern screening ==="
   SECRET_MATCHES="$(
   grep -RInE \
   --exclude-dir=.git \
   --exclude='*.gz' \
   --exclude='*.sif' \
   'ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY' \
   pipeline \
   validation \
   README.md \
   2>/dev/null \
   || true
   )"
   if [[ -n "$SECRET_MATCHES" ]]; then
   echo "ERROR: Possible secret material found:"
   echo "$SECRET_MATCHES"
   exit 1
   fi
   echo "PASS: No obvious secret patterns found."
   echo
   echo "=== 6. Staged summary ==="
   git diff \
   --cached \
   --stat
   echo
   echo "PASS: Pre-commit governance screening completed."

Manual review remains necessary even when this command passes.

.. _20-48-complete-repository-verification:

20.48 Complete repository verification
--------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   echo "=== Repository ==="
   git rev-parse \
   --show-toplevel
   echo
   echo "=== Branch ==="
   git branch \
   --show-current
   echo
   echo "=== Commit ==="
   git rev-parse HEAD
   echo
   echo "=== Status ==="
   git status --short
   echo
   echo "=== Remotes ==="
   git remote -v
   echo
   echo "=== Upstream ==="
   if UPSTREAM="$(
   git rev-parse \
   --abbrev-ref \
   --symbolic-full-name \
   '@{upstream}' \
   2>/dev/null
   )"
   then
   echo "$UPSTREAM"
   echo
   echo "=== Local/remote difference ==="
   git rev-list \
   --left-right \
   --count \
   HEAD..."$UPSTREAM"
   else
   echo "No upstream configured."
   fi
   echo
   echo "=== Remote branches containing HEAD ==="
   git branch \
   --remotes \
   --contains HEAD \
   2>/dev/null \
   || true

This command establishes the actual repository state without assuming that a push succeeded.

.. _20-49-data-governance-incident-log:

20.49 Data-governance incident log
----------------------------------

A local governance incident log may contain:

-  

   .. container::

      incident_id

-  

   .. container::

      date_detected

-  

   .. container::

      description

-  

   .. container::

      data_category

-  

   .. container::

      location

-  

   .. container::

      people_notified

-  

   .. container::

      containment_action

-  

   .. container::

      credential_rotation

-  

   .. container::

      Git-history action

-  

   .. container::

      final resolution

The incident log itself may be sensitive and should not automatically be committed.

A blank template can be stored outside the tracked repository.

.. _20-50-governance-responsibilities:

20.50 Governance responsibilities
---------------------------------

The project should distinguish responsibilities.

**Analyst responsibilities**

-  

   .. container::

      Use non-identifying case IDs

-  

   .. container::

      Preserve original inputs

-  

   .. container::

      Run approved workflows

-  

   .. container::

      Review logs

-  

   .. container::

      Protect outputs

-  

   .. container::

      Report incidents

**Pipeline-maintainer responsibilities**

-  

   .. container::

      Maintain source control

-  

   .. container::

      Validate updates

-  

   .. container::

      Protect production-resource isolation

-  

   .. container::

      Preserve audits

-  

   .. container::

      Document tool and resource changes

**Clinical or specialist responsibilities**

-  

   .. container::

      Confirm phenotype

-  

   .. container::

      Interpret clinical relevance

-  

   .. container::

      Review inheritance

-  

   .. container::

      Request confirmation testing

-  

   .. container::

      Provide counselling or treatment advice

The pipeline does not replace clinical responsibility.

.. _20-51-reproducibility-limitations:

20.51 Reproducibility limitations
---------------------------------

Perfect reproduction may be affected by:

-  

   .. container::

      Unavailable historical web resources

-  

   .. container::

      Updated external databases

-  

   .. container::

      Changed container base images

-  

   .. container::

      Changed operating-system packages

-  

   .. container::

      Licensing restrictions

-  

   .. container::

      Deleted online files

-  

   .. container::

      Hardware-specific behaviour

Mitigation includes:

-  

   .. container::

      Checksums

-  

   .. container::

      Archived containers

-  

   .. container::

      Pinned versions

-  

   .. container::

      Local resource snapshots

-  

   .. container::

      Audit directories

-  

   .. container::

      Environment manifests

-  

   .. container::

      Detailed setup documentation

The report should state honestly when a historical external resource cannot be redistributed.

.. _20-52-governance-limitations:

20.52 Governance limitations
----------------------------

The pipeline can enforce local technical safeguards, but it cannot by itself guarantee:

-  

   .. container::

      Institutional legal compliance

-  

   .. container::

      Valid informed consent

-  

   .. container::

      Correct access authorisation

-  

   .. container::

      Secure external backups

-  

   .. container::

      Approved clinical reporting

-  

   .. container::

      Proper data-retention periods

-  

   .. container::

      Complete anonymisation

These require organisational policies and authorised supervision.

.. _20-53-reproducibility-checklist:

20.53 Reproducibility checklist
-------------------------------

The project is reproducible when:

✓ The original input checksum is recorded

✓ The HPO-file checksum is recorded

✓ The selected sample is recorded

✓ GRCh38 is confirmed

✓ The analysis and resource modes are recorded

✓ The pipeline commit is recorded

✓ Source checksums are available

✓ Tool versions are recorded

✓ Container checksums are recorded

✓ Resource versions and checksums are recorded

✓ Execution settings are recorded

✓ Important logs are preserved

✓ Final outputs are checksummed

✓ The master table links to detailed evidence

✓ The validation status is preserved

✓ Historical audits remain unchanged

.. _20-54-privacy-checklist:

20.54 Privacy checklist
-----------------------

Privacy protection is adequate when:

✓ The case identifier is non-identifying

✓ Real patient names are absent from filenames

✓ Real patient names are absent from reports

✓ Sensitive sample names are controlled

✓ Direct identifiers are removed from shared files

✓ Absolute personal paths are removed from public documentation

✓ Case directories are access controlled

✓ Real case files remain outside GitHub

✓ Local archives remain protected

✓ Staged files are screened before commits

✓ Git history is checked after any accidental addition

✓ Credentials are never committed

✓ Privacy incidents are documented and escalated

.. _20-55-github-management-checklist:

20.55 GitHub-management checklist
---------------------------------

Repository management is complete when:

✓ The repository purpose is documented

✓ The correct project root is confirmed

✓ The active branch is known

✓ The current commit is known

✓ The remote URL is verified

✓ Authentication status is verified

✓ The upstream branch is known

✓ Local and remote divergence is checked

✓ The remote branch is confirmed to contain the intended commit

✓ Large local resources are ignored

✓ SIF images are ignored

✓ Patient inputs and outputs are ignored

✓ Local archives are ignored

✓ Secrets are screened

✓ Staged files are reviewed

✓ Large staged files are rejected

✓ Sensitive files are removed before commits

✓ Push success is verified rather than assumed

✓ Validated source states may be tagged

✓ Historical audit directories remain preserved

.. _20-56-section-completion-criteria:

20.56 Section completion criteria
---------------------------------

The reproducibility, governance and repository-management stage is complete when:

✓ Source, input, resource, environment and output provenance are recorded

✓ Important files have SHA-256 checksums

✓ Container and resource inventories are maintained

✓ Original case data remain unchanged

✓ Case data are stored separately from source code

✓ Non-identifying case identifiers are used

✓ Genomic data are treated as sensitive even when de-identified

✓ Access and retention requirements are documented

✓ Backups are protected and testable

✓ Secure-deletion requirements are acknowledged

✓ Privacy incidents have a defined response process

✓ GitHub contains source and compact validation material only

✓ Real case data and large resources remain local

✓ .gitignore protects sensitive and generated paths

✓ Tracked and staged files are screened

✓ Credentials are absent from repository content

✓ Local commit and remote-push status are distinguished

✓ Remote branch containment is verified before claiming upload success

✓ Previous audit snapshots remain immutable

✓ Reproduction limitations and governance boundaries are stated honestly

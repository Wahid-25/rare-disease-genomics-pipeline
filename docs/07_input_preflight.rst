.. _7-input-data-requirements-case-preparation-and-vcf-structural-preflight:

7. Input Data Requirements, Case Preparation and VCF Structural Preflight
=========================================================================


This section defines the input formats accepted by the universal pipeline and the checks that must be completed before annotation begins. Input validation is essential because a VCF can be syntactically readable while still containing an incorrect genome build, incompatible chromosome names, malformed INFO fields or biologically inconsistent genotypes.

The principal validated workflow begins with a prepared **GRCh38 VCF**. HPO terms, reported sex and other case metadata may also be supplied to improve inheritance and phenotype analysis.

.. _7-1-main-case-inputs:

7.1 Main case inputs
--------------------

A complete case may include:

Required:

• One GRCh38 VCF file

Recommended:

• Patient or case identifier

• Reported biological sex

• HPO phenotype file

• Case metadata

• Sample sheet entry

Optional:

• Known diagnosis for controlled validation

• CNV BED input

• Pharmacogenomic expectations

• Clinical notes

• Family or inheritance information

The pipeline must never overwrite the original submitted VCF. Harmonised, normalised and annotated versions are created as separate files.

.. _7-2-supported-variant-representations:

7.2 Supported variant representations
-------------------------------------

The universal pipeline is designed to detect and route several variant classes.

+----------------------+------------------------------------+---------------------------------------+
| **Variant class**    | **Typical representation**         | **Analytical branch**                 |
+======================+====================================+=======================================+
| SNV                  | A>G                                | Small-variant annotation              |
+----------------------+------------------------------------+---------------------------------------+
| Small insertion      | A>ATG                              | Small-variant annotation              |
+----------------------+------------------------------------+---------------------------------------+
| Small deletion       | ATG>A                              | Small-variant annotation              |
+----------------------+------------------------------------+---------------------------------------+
| Multiallelic variant | A>G,T                              | Decomposed during normalisation       |
+----------------------+------------------------------------+---------------------------------------+
| CNV deletion         | <DEL>                              | CNV branch                            |
+----------------------+------------------------------------+---------------------------------------+
| CNV duplication      | <DUP>                              | CNV branch                            |
+----------------------+------------------------------------+---------------------------------------+
| Repeat expansion     | Symbolic repeat allele             | Repeat-expansion report               |
+----------------------+------------------------------------+---------------------------------------+
| Other symbolic SV    | <INV>, <INS>, <BND>                | Detected and reported; support varies |
+----------------------+------------------------------------+---------------------------------------+
| ClinPGx variant      | SNV or indel matching a PGx allele | ClinPGx branch                        |
+----------------------+------------------------------------+---------------------------------------+

The pipeline separates **variant detection** from **variant interpretation**. A record may be detected successfully while still requiring specialised analysis outside the pipeline.

.. _7-3-genome-build-requirement:

7.3 Genome-build requirement
----------------------------

All case coordinates must use:

GRCh38

Genome-build compatibility cannot be determined reliably from chromosome names alone. A file using chr1 may still contain GRCh37 coordinates.

Build evidence should be checked from:

-  VCF metadata;

-  variant-caller documentation;

-  source dataset documentation;

-  known variant coordinates;

-  reference-allele comparison with the GRCh38 FASTA;

-  liftover history, when applicable.

The reference used by this project is:

.. code:: bash

   resources/reference/hg38.fa

The corresponding index is:

.. code:: bash

   resources/reference/hg38.fa.fai

.. _7-4-chromosome-naming-convention:

7.4 Chromosome naming convention
--------------------------------

The project uses UCSC-style chromosome names:

-  

   .. container::

      chr1

-  

   .. container::

      chr2

-  

   .. container::

      ...

-  

   .. container::

      chr22

-  

   .. container::

      chrX

-  

   .. container::

      chrY

-  

   .. container::

      chrM

Inputs using:

-  

   .. container::

      1

-  

   .. container::

      2

-  

   .. container::

      X

-  

   .. container::

      Y

-  

   .. container::

      MT

must be harmonised before downstream annotation.

The project script responsible for chromosome harmonisation is:

`pipeline/case_workflow/00_harmonize_vcf_chromosomes.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/00_harmonize_vcf_chromosomes.py>`__

The harmonised file must be written separately. The original VCF must remain unchanged.

.. _7-5-vcf-structure:

7.5 VCF structure
-----------------

A valid VCF normally contains three components.

.. _7-5-1-metadata-lines:

7.5.1 Metadata lines
~~~~~~~~~~~~~~~~~~~~

Metadata lines begin with:

##

The first line should identify the VCF version:

##fileformat=VCFv4.2

The metadata may define:

-  reference assembly;

-  contigs;

-  INFO fields;

-  FORMAT fields;

-  FILTER fields;

-  variant-caller details;

-  annotation fields.

.. _7-5-2-column-header-line:

7.5.2 Column-header line
~~~~~~~~~~~~~~~~~~~~~~~~

The main header begins with:

#CHROM

A case-level VCF commonly contains:

#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT SAMPLE

The exact sample name may differ, but the validation pipeline expects a case-level file containing one primary patient sample.

.. _7-5-3-variant-records:

7.5.3 Variant records
~~~~~~~~~~~~~~~~~~~~~

Each data row represents one genomic locus.

The core fields are:

+---------------------+------------------------------------------------+
| **Field**           | **Meaning**                                    |
+=====================+================================================+
| CHROM               | Chromosome or contig                           |
+---------------------+------------------------------------------------+
| POS                 | 1-based genomic position                       |
+---------------------+------------------------------------------------+
| ID                  | Database identifier, often an rsID             |
+---------------------+------------------------------------------------+
| REF                 | Reference allele                               |
+---------------------+------------------------------------------------+
| ALT                 | Alternate allele                               |
+---------------------+------------------------------------------------+
| QUAL                | Variant quality                                |
+---------------------+------------------------------------------------+
| FILTER              | Filtering status                               |
+---------------------+------------------------------------------------+
| INFO                | Record-level annotations                       |
+---------------------+------------------------------------------------+
| FORMAT              | Definition of sample-level fields              |
+---------------------+------------------------------------------------+
| Sample column       | Genotype and related sample values             |
+---------------------+------------------------------------------------+

.. _7-6-genotype-requirements:

7.6 Genotype requirements
-------------------------

The genotype field is normally represented using GT.

Common examples include:

-  

   .. container::

      0/0 homozygous reference

-  

   .. container::

      0/1 heterozygous alternate

-  

   .. container::

      1/1 homozygous alternate

-  

   .. container::

      0|1 phased heterozygous

-  

   .. container::

      1|0 phased heterozygous

-  

   .. container::

      ./. missing genotype

   1. 

      .. container::

         haploid alternate genotype

   2. 

      .. container::

         haploid reference genotype

The separator has biological meaning:

/ unphased genotype

\| phased genotype

For compound-heterozygous analysis, phased genotypes may be accompanied by fields such as:

-  

   .. container::

      PS

-  

   .. container::

      PID

-  

   .. container::

      PGT

A pair should not be described as confirmed in trans unless compatible phase evidence shows that the variants occur on opposite haplotypes.

.. _7-7-sex-and-ploidy-metadata:

7.7 Sex and ploidy metadata
---------------------------

Reported biological sex is important for interpreting variants on:

-  

   .. container::

      chrX

-  

   .. container::

      chrY

-  

   .. container::

      chrM

The pipeline uses sex and ploidy information to distinguish:

-  diploid autosomal genotypes;

-  diploid or haploid X-chromosome expectations;

-  Y-chromosome records;

-  hemizygous variants;

-  mitochondrial variants;

-  genotypes inconsistent with reported sex.

The relevant scripts are:

`pipeline/case_workflow/20_sex_ploidy_preflight.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/20_sex_ploidy_preflight.py>`__

`pipeline/case_workflow/21_resolve_case_sex.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/21_resolve_case_sex.py>`__

`pipeline/case_workflow/inheritance_utils.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/inheritance_utils.py>`__

When sex is unavailable, the pipeline should mark sex-dependent interpretation as uncertain rather than assuming a value.

.. _7-8-hpo-phenotype-input:

7.8 HPO phenotype input
-----------------------

Patient phenotypes should be represented using Human Phenotype Ontology identifiers.

A simple HPO file contains one term per line:

-  

   .. container::

      HP:0001250

-  

   .. container::

      HP:0001263

-  

   .. container::

      HP:0004322

Blank lines and comment lines may be ignored, but the safest input contains only valid HPO identifiers.

The required identifier pattern is:

HP:

followed by exactly seven digits.

Examples of committed HPO files are stored under:

.. code:: bash

   validation/universal_pipeline_testing/inputs/hpo/

The pipeline uses exact patient-name matching so that a file for patient_01 cannot accidentally match patient_10, patient_11, patient_12 or patient_13.

.. _7-8-1-validate-an-hpo-file:

7.8.1 Validate an HPO file
~~~~~~~~~~~~~~~~~~~~~~~~~~

Set the file path:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   HPO_FILE="validation/universal_pipeline_testing/inputs/hpo/patient_06_pku.hpo.txt"

Validate its format:

.. code:: bash

   python3 - "$HPO_FILE" <<'PY'
   from pathlib import Path
   import re
   import sys
   path = Path(sys.argv[1])
   if not path.is_file():
   raise SystemExit(f"ERROR: HPO file not found: {path}")
   pattern = re.compile(r"^HP:\d{7}$")
   valid_terms = []
   invalid_lines = []
   for line_number, raw_line in enumerate(
   path.read_text(encoding="utf-8-sig").splitlines(),
   start=1,
   ):
   line = raw_line.strip()
   if not line or line.startswith("#"):
   continue
   if pattern.fullmatch(line):
   valid_terms.append(line)
   else:
   invalid_lines.append((line_number, line))
   if invalid_lines:
   print("ERROR: Invalid HPO entries:")
   for line_number, value in invalid_lines:
   print(f" line {line_number}: {value!r}")
   raise SystemExit(1)
   if not valid_terms:
   raise SystemExit("ERROR: No valid HPO terms were found.")
   duplicates = len(valid_terms) - len(set(valid_terms))
   print(f"PASS: {len(valid_terms)} valid HPO term(s).")
   print(f"Duplicate entries: {duplicates}")
   PY

HPO identifiers should be checked against the installed ontology before analysis. A structurally valid identifier may refer to an obsolete or unavailable term.

.. _7-9-validation-sample-sheet:

7.9 Validation sample sheet
---------------------------

The committed validation sample sheet is:

validation/universal_pipeline_testing/inputs/reference/sample_sheet.csv

It provides the project’s authoritative example of how patient identifiers, VCF files and associated metadata are connected.

Inspect it with:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   python3 - <<'PY'
   import csv
   from pathlib import Path
   path = Path(
   "validation/universal_pipeline_testing/"
   "inputs/reference/sample_sheet.csv"
   )
   with path.open(
   newline="",
   encoding="utf-8-sig",
   ) as handle:
   reader = csv.reader(handle)
   for index, row in enumerate(reader):
   print(row)
   if index >= 4:
   break
   PY

When constructing a new sample sheet, copy the committed file and preserve its existing column names rather than creating a different schema.

.. code:: bash

   cp \
   validation/universal_pipeline_testing/inputs/reference/sample_sheet.csv \
   input/cases/sample_sheet.template.csv

.. _7-10-recommended-case-directory-structure:

7.10 Recommended case-directory structure
-----------------------------------------

Each new case should have its own directory.

input/cases/

└── case_001/

├── original/

│ └── case_001.raw.vcf

├── metadata/

│ ├── case_metadata.tsv

│ └── phenotype.hpo.txt

├── checksums/

│ └── original_inputs.sha256

└── prepared/

The original/ directory should be treated as immutable.

The prepared/ directory is used for:

-  line-ending correction;

-  chromosome harmonisation;

-  decompression;

-  normalisation;

-  annotation removal;

-  pipeline-ready copies.

.. _7-11-create-a-new-case-safely:

7.11 Create a new case safely
-----------------------------

Set the source VCF and case identifier:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   SOURCE_VCF="/absolute/path/to/input.vcf"
   CASE_ROOT="$PWD/input/cases/$CASE_ID"

Validate the values:

.. code:: bash

   if [[ ! "$CASE_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
   echo "ERROR: Unsafe case identifier: $CASE_ID"
   exit 1
   fi
   if [[ ! -s "$SOURCE_VCF" ]]; then
   echo "ERROR: Source VCF is missing or empty:"
   echo "$SOURCE_VCF"
   exit 1
   fi

Create the directory structure:

.. code:: bash

   mkdir -p \
   "$CASE_ROOT/original" \
   "$CASE_ROOT/metadata" \
   "$CASE_ROOT/checksums" \
   "$CASE_ROOT/prepared"

Copy the original input:

.. code:: bash

   ORIGINAL_VCF="$CASE_ROOT/original/${CASE_ID}.raw.vcf"
   cp \
   --preserve=mode,timestamps \
   --reflink=auto \
   "$SOURCE_VCF" \
   "$ORIGINAL_VCF"

Make the copied original read-only:

.. code:: bash

   chmod a-w "$ORIGINAL_VCF"

Create its checksum:

.. code:: bash

   sha256sum \
   "$ORIGINAL_VCF" \
   > "$CASE_ROOT/checksums/original_inputs.sha256"

Verify immediately:

.. code:: bash

   (
   cd "$CASE_ROOT"
   sha256sum \
   --check \
   checksums/original_inputs.sha256
   )

This design protects the original input while allowing derived files to be modified independently.

.. _7-12-create-case-metadata:

7.12 Create case metadata
-------------------------

A compact metadata file may contain:

.. code:: bash

   cat > "$CASE_ROOT/metadata/case_metadata.tsv" <<EOF

+-----------------------------------+-----------------------------------+
| field                             | value                             |
+===================================+===================================+
| case_id                           | $CASE_ID                          |
+-----------------------------------+-----------------------------------+
| genome_build                      | GRCh38                            |
+-----------------------------------+-----------------------------------+
| reported_sex                      | unknown                           |
+-----------------------------------+-----------------------------------+
| input_vcf                         | original/${CASE_ID}.raw.vcf       |
+-----------------------------------+-----------------------------------+
| phenotype_file                    | metadata/phenotype.hpo.txt        |
+-----------------------------------+-----------------------------------+
| analysis_mode                     | production                        |
+-----------------------------------+-----------------------------------+
| created_utc                       | $(date -u '+%Y-%m-%dT%H:%M:%SZ')  |
+-----------------------------------+-----------------------------------+

EOF

The allowed analysis modes are:

-  

   .. container::

      production

-  

   .. container::

      validation

production must use official resources only.

validation may include controlled local validation relationships.

.. _7-13-detect-and-remove-windows-line-endings:

7.13 Detect and remove Windows line endings
-------------------------------------------

VCF, TSV and HPO files copied from Windows may contain carriage-return characters.

Do not modify the original file. Create a prepared copy:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   CASE_ROOT="$PWD/input/cases/$CASE_ID"
   ORIGINAL_VCF="$CASE_ROOT/original/${CASE_ID}.raw.vcf"
   PREPARED_VCF="$CASE_ROOT/prepared/${CASE_ID}.line_endings_fixed.vcf"
   sed 's/\r$//' \
   "$ORIGINAL_VCF" \
   > "$PREPARED_VCF"

Verify that carriage returns are absent:

.. code:: bash

   if LC_ALL=C grep -q $'\r' "$PREPARED_VCF"; then
   echo "ERROR: Windows carriage returns remain."
   exit 1
   fi
   echo "PASS: Unix line endings confirmed."

.. _7-14-basic-vcf-structural-validation:

7.14 Basic VCF structural validation
------------------------------------

Set the VCF path:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="input/cases/case_001/prepared/case_001.line_endings_fixed.vcf"

Check that it exists:

.. code:: bash

   if [[ ! -s "$VCF" ]]; then
   echo "ERROR: VCF is missing or empty: $VCF"
   exit 1
   fi

Validate the complete file with bcftools:

.. code:: bash

   bcftools view \
   --output-type v \
   --output /dev/null \
   "$VCF"

Verify the VCF version line:

.. code:: bash

   FIRST_LINE="$(
   bcftools view \
   --header-only \
   "$VCF" |
   head -n 1
   )"
   case "$FIRST_LINE" in
   '##fileformat=VCFv4.'*)
   echo "PASS: $FIRST_LINE"
   ;;
   *)
   echo "ERROR: Invalid or missing VCF fileformat line."
   echo "Observed: $FIRST_LINE"
   exit 1
   ;;
   esac

Verify the #CHROM header:

.. code:: bash

   bcftools view \
   --header-only \
   "$VCF" |
   grep -q '^#CHROM[[:space:]]' ||
   {
   echo "ERROR: #CHROM header line is missing."
   exit 1
   }
   echo "PASS: #CHROM header detected."

.. _7-15-count-samples-and-variants:

7.15 Count samples and variants
-------------------------------

Count samples:

.. code:: bash

   SAMPLE_COUNT="$(
   bcftools query \
   --list-samples \
   "$VCF" |
   wc -l
   )"
   echo "Sample count: $SAMPLE_COUNT"

For the standard single-patient workflow:

.. code:: bash

   if (( SAMPLE_COUNT != 1 )); then
   echo "ERROR: The case workflow expects one primary sample."
   echo "Observed sample count: $SAMPLE_COUNT"
   exit 1
   fi

Display the sample name:

.. code:: bash

   bcftools query \
   --list-samples \
   "$VCF"

Count records:

.. code:: bash

   RECORD_COUNT="$(
   bcftools view \
   --no-header \
   "$VCF" |
   wc -l
   )"
   echo "Variant records: $RECORD_COUNT"
   if (( RECORD_COUNT == 0 )); then
   echo "ERROR: VCF contains no variant records."
   exit 1
   fi

.. _7-16-check-genotype-availability:

7.16 Check genotype availability
--------------------------------

Confirm that GT is defined in the header:

.. code:: bash

   if bcftools view --header-only "$VCF" |
   grep -q '^##FORMAT=<ID=GT,'; then
   echo "PASS: GT FORMAT field is defined."
   else
   echo "WARNING: GT FORMAT definition is absent."
   fi

Count missing genotypes:

.. code:: bash

   MISSING_GT="$(
   bcftools query \
   --format '[%GT\n]' \
   "$VCF" |
   awk '
   $0 == "." ||
   $0 == "./." ||
   $0 == ".|." {
   count++
   }
   END {
   print count + 0
   }
   '
   )"
   echo "Missing genotypes: $MISSING_GT"

Missing genotypes are not necessarily structural VCF errors, but they limit inheritance and ClinPGx interpretation.

.. _7-17-check-chromosome-names:

7.17 Check chromosome names
---------------------------

List the chromosome names present:

.. code:: bash

   bcftools query \
   --format '%CHROM\n' \
   "$VCF" |
   sort -u

Perform a strict chr-prefix check:

.. code:: bash

   INVALID_CONTIGS="$(
   bcftools query \
   --format '%CHROM\n' \
   "$VCF" |
   sort -u |
   grep -Ev '^chr([1-9]|1[0-9]|2[0-2]|X|Y|M)$' \
   || true
   )"
   if [[ -n "$INVALID_CONTIGS" ]]; then
   echo "WARNING: Non-standard or unsupported contigs detected:"
   echo "$INVALID_CONTIGS"
   else
   echo "PASS: Standard chr-prefixed chromosomes detected."
   fi

Non-standard contigs may be valid, but they must also exist in the reference FASTA and be supported by annotation resources.

.. _7-18-verify-contigs-against-the-fasta:

7.18 Verify contigs against the FASTA
-------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="input/cases/case_001/prepared/case_001.line_endings_fixed.vcf"
   FAI="resources/reference/hg38.fa.fai"
   if [[ ! -s "$FAI" ]]; then
   echo "ERROR: Reference FASTA index is missing."
   exit 1
   fi
   VCF_CONTIGS="$(
   mktemp
   )"
   FASTA_CONTIGS="$(
   mktemp
   )"

trap 'rm -f "$VCF_CONTIGS" "$FASTA_CONTIGS"' EXIT

.. code:: bash

   bcftools query \
   --format '%CHROM\n' \
   "$VCF" |
   sort -u \
   > "$VCF_CONTIGS"
   cut -f1 "$FAI" |
   sort -u \
   > "$FASTA_CONTIGS"
   MISSING_FROM_FASTA="$(
   comm \
   -23 \
   "$VCF_CONTIGS" \
   "$FASTA_CONTIGS"
   )"
   if [[ -n "$MISSING_FROM_FASTA" ]]; then
   echo "ERROR: VCF contigs absent from the reference FASTA:"
   echo "$MISSING_FROM_FASTA"
   exit 1
   fi
   echo "PASS: Every VCF contig exists in the reference FASTA."

.. _7-19-check-ref-alleles-against-grch38:

7.19 Check REF alleles against GRCh38
-------------------------------------

Reference mismatches are among the most important pre-analysis failures.

Run a strict reference check:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="input/cases/case_001/prepared/case_001.line_endings_fixed.vcf"
   REFERENCE="resources/reference/hg38.fa"
   LOG="input/cases/case_001/prepared/reference_check.log"
   if bcftools norm \
   --fasta-ref "$REFERENCE" \
   --check-ref e \
   --output-type v \
   --output /dev/null \
   "$VCF" \
   2> "$LOG"
   then
   echo "PASS: All testable REF alleles match GRCh38."
   else
   echo "ERROR: Reference mismatch or normalisation failure detected."
   cat "$LOG"
   exit 1
   fi

The --check-ref e option stops when a reference mismatch is detected.

Do not automatically swap REF and ALT alleles unless the biological and genome-build interpretation has been verified. Blind allele swapping can create incorrect variants.

Symbolic variants may not undergo the same REF check as ordinary SNVs and indels.

.. _7-20-normalise-small-variants:

7.20 Normalise small variants
-----------------------------

A standard normalisation command is:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   INPUT_VCF="input/cases/case_001/prepared/case_001.line_endings_fixed.vcf"
   OUTPUT_VCF="input/cases/case_001/prepared/case_001.normalized.vcf.gz"
   REFERENCE="resources/reference/hg38.fa"
   bcftools norm \
   --fasta-ref "$REFERENCE" \
   --multiallelics -any \
   --check-ref e \
   --output-type z \
   --output "$OUTPUT_VCF.tmp" \
   "$INPUT_VCF"
   mv \
   "$OUTPUT_VCF.tmp" \
   "$OUTPUT_VCF"
   tabix \
   --force \
   --preset vcf \
   "$OUTPUT_VCF"

Verify:

.. code:: bash

   bgzip --test "$OUTPUT_VCF"
   bcftools view \
   --header-only \
   "$OUTPUT_VCF" \
   >/dev/null
   tabix --list-chroms \
   "$OUTPUT_VCF" |

head

.. code:: bash

   echo "PASS: Normalised and indexed VCF created."

In the production workflow, only records routed to the small-variant branch should be normalised this way. Symbolic CNVs and repeat expansions must not be forced through inappropriate small-variant normalisation.

The production script is:

`pipeline/case_workflow/01_normalize_routed_small_variants.sh <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/01_normalize_routed_small_variants.sh>`__

.. _7-21-compress-and-index-an-uncompressed-vcf:

7.21 Compress and index an uncompressed VCF
-------------------------------------------

When the original input is an uncompressed .vcf, create a prepared compressed copy:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   INPUT_VCF="input/cases/case_001/prepared/case_001.normalized.vcf"
   OUTPUT_VCF="${INPUT_VCF}.gz"
   bgzip \
   --threads "$(nproc)" \
   --stdout \
   "$INPUT_VCF" \
   > "$OUTPUT_VCF.tmp"
   mv \
   "$OUTPUT_VCF.tmp" \
   "$OUTPUT_VCF"
   tabix \
   --force \
   --preset vcf \
   "$OUTPUT_VCF"

Validate:

.. code:: bash

   bgzip --test "$OUTPUT_VCF"
   tabix --list-chroms "$OUTPUT_VCF" | head

Never run ordinary gzip when a downstream tool requires block-gzip compression and tabix indexing.

.. _7-22-detect-duplicate-records:

7.22 Detect duplicate records
-----------------------------

Exact duplicate variant records can distort scoring and disease ranking.

Create a key from chromosome, position, REF and ALT:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="input/cases/case_001/prepared/case_001.normalized.vcf.gz"
   DUPLICATES="$(
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\n' \
   "$VCF" |
   sort |
   uniq -d
   )"
   if [[ -n "$DUPLICATES" ]]; then
   echo "WARNING: Duplicate variant keys detected:"
   echo "$DUPLICATES"
   else
   echo "PASS: No exact duplicate variant keys detected."
   fi

Duplicates should be investigated rather than removed blindly, especially when different records contain different IDs, genotypes or annotations.

.. _7-23-existing-annotation-handling:

7.23 Existing annotation handling
---------------------------------

Some external VCFs already contain:

-  VEP CSQ;

-  SnpEff ANN;

-  ClinVar fields;

-  SpliceAI fields;

-  caller-specific annotations.

Reusing mixed annotation versions can produce inconsistent outputs.

The project provides:

`pipeline/case_workflow/19_remove_existing_annotations.sh <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/19_remove_existing_annotations.sh>`__

This script is used during controlled case preparation when a clean reannotation is required.

The original VCF must still be preserved unchanged.

Before stripping annotations, inspect the existing INFO definitions:

.. code:: bash

   bcftools view \
   --header-only \
   "$VCF" |
   grep '^##INFO=' |

less

.. _7-24-cnv-input-requirements:

7.24 CNV input requirements
---------------------------

The CNV tools use a four-column BED-like format:

chromosome start end variant_type

Example:

-  

   .. container::

      chr1 100000 500000 DEL

-  

   .. container::

      chr7 5500000 6200000 DUP

Accepted project CNV labels are:

-  

   .. container::

      DEL

-  

   .. container::

      DUP

Important coordinate distinction:

-  

   .. container::

      VCF POS: 1-based

-  

   .. container::

      BED start: 0-based

-  

   .. container::

      BED end: end-exclusive

A direct VCF-to-BED conversion must account for this difference.

For a VCF CNV beginning at POS, a typical BED start is:

POS - 1

The end coordinate is usually obtained from the VCF END field.

.. _7-24-1-validate-a-cnv-bed-file:

7.24.1 Validate a CNV BED file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CNV_BED="input/sample.cnvs.bed"
   awk '
   BEGIN {
   FS = OFS = "\t"
   failures = 0
   }
   NF == 0 || $1 ~ /^#/ {
   next
   }
   NF < 4 {
   print "ERROR: fewer than four columns at line", NR > "/dev/stderr"
   failures++
   next
   }
   $1 !~ /^chr/ {
   print "ERROR: chromosome lacks chr prefix at line", NR > "/dev/stderr"
   failures++
   }
   $2 !~ /^[0-9]+$/ || $3 !~ /^[0-9]+$/ {
   print "ERROR: non-numeric coordinate at line", NR > "/dev/stderr"
   failures++
   next
   }
   $2 >= $3 {
   print "ERROR: start must be smaller than end at line", NR > "/dev/stderr"
   failures++
   }
   $4 != "DEL" && $4 != "DUP" {
   print "ERROR: unsupported CNV type at line", NR > "/dev/stderr"
   failures++
   }
   END {
   if (failures > 0) {
   exit 1
   }
   print "PASS: CNV BED validation completed."
   }
   ' "$CNV_BED"

.. _7-25-symbolic-cnv-vcf-records:

7.25 Symbolic CNV VCF records
-----------------------------

A deletion record may resemble:

chr1 100001 . N <DEL> . PASS SVTYPE=DEL;END=500000

A duplication record may resemble:

chr7 5500001 . N <DUP> . PASS SVTYPE=DUP;END=6200000

The VCF header should define the symbolic ALT allele and INFO fields.

Example definitions:

##ALT=<ID=DEL,Description="Deletion">

##ALT=<ID=DUP,Description="Duplication">

##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Structural variant type">

##INFO=<ID=END,Number=1,Type=Integer,Description="End coordinate">

Required CNV information should include:

-  chromosome;

-  start;

-  end;

-  structural-variant type;

-  genotype where available.

Records lacking a usable END value cannot be converted reliably to a CNV interval.

.. _7-26-repeat-expansion-input-requirements:

7.26 Repeat-expansion input requirements
----------------------------------------

Repeat-expansion records may contain:

-  a symbolic alternate allele;

-  repeat motif;

-  observed repeat count;

-  reference repeat count;

-  genotype;

-  transcript notation;

-  protein notation;

-  disease threshold;

-  rsID or other database identifier.

The authoritative project example is:

`validation/universal_pipeline_testing/inputs/vcfs/patient_03.vcf <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/validation/universal_pipeline_testing/inputs/vcfs/patient_03.vcf>`__

The pipeline detects the HTT CAG expansion in this file and writes it to a repeat-expansion report.

The relevant scripts are:

`pipeline/case_workflow/00_detect_and_split_variants.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/00_detect_and_split_variants.py>`__

`pipeline/case_workflow/00b_report_repeat_expansions.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/00b_report_repeat_expansions.py>`__

A repeat-expansion record must not be ranked as an ordinary SNV merely because it appears in a VCF.

.. _7-27-variant-detection-and-routing:

7.27 Variant detection and routing
----------------------------------

The first major universal-pipeline stage is:

00_detect_and_split_variants.py

It determines whether the input contains:

-  ordinary small variants;

-  symbolic deletions;

-  symbolic duplications;

-  other structural variants;

-  repeat expansions;

-  unsupported records.

The output may contain separate routed files for:

-  

   .. container::

      small variants

-  

   .. container::

      CNVs

-  

   .. container::

      repeat expansions

-  

   .. container::

      unsupported variants

This prevents one variant class from being processed by an inappropriate annotation method.

.. _7-28-run-the-committed-structural-preflight-suite:

7.28 Run the committed structural-preflight suite
-------------------------------------------------

The repository contains:

`pipeline/tests/run_vcf_structural_preflight.sh <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/tests/run_vcf_structural_preflight.sh>`__

Run it from the project root:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   bash \
   pipeline/tests/run_vcf_structural_preflight.sh

The validation manifest is:

.. code:: bash

   validation/universal_pipeline_testing/manifests/vcf_preflight.tsv

Inspect it with:

.. code:: bash

   column \
   --separator $'\t' \
   --table \
   validation/universal_pipeline_testing/manifests/vcf_preflight.tsv

The validated project recorded structural preflight success for all thirteen prepared validation VCFs.

Patient 13 passed input preparation and structural preflight but was intentionally not executed through the complete pipeline.

.. _7-29-generate-input-checksums:

7.29 Generate input checksums
-----------------------------

Every submitted input should have a checksum before processing.

For one case:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ROOT="input/cases/case_001"
   find \
   "$CASE_ROOT/original" \
   "$CASE_ROOT/metadata" \
   -type f \
   -print0 |
   sort -z |
   xargs -0 sha256sum \
   > "$CASE_ROOT/checksums/all_inputs.sha256"

Verify:

.. code:: bash

   sha256sum \
   --check \
   "$CASE_ROOT/checksums/all_inputs.sha256"

The universal validation checksum manifest is:

.. code:: bash

   validation/universal_pipeline_testing/manifests/input_sha256.tsv

Checksums allow later confirmation that:

-  the original input did not change;

-  the same HPO file was used;

-  the same sample sheet was used;

-  a rerun used identical case data.

.. _7-30-production-versus-validation-input-mode:

7.30 Production versus validation input mode
--------------------------------------------

**Production mode**

Production mode must use:

-  

   .. container::

      official Gene2Phenotype data

-  

   .. container::

      official phenotype resources

-  

   .. container::

      official clinical databases

-  

   .. container::

      no synthetic disease relationships

Use this mode for general case analysis.

**Validation mode**

Validation mode may combine official resources with controlled test relationships.

Use this mode only for:

-  regression testing;

-  synthetic cases;

-  pipeline-development experiments;

-  expected-result validation.

The selected mode must be written into:

-  case metadata;

-  execution logs;

-  reproducibility manifest;

-  final report.

.. _7-31-input-privacy-requirements:

7.31 Input privacy requirements
-------------------------------

Real or externally supplied case files may contain identifying information in:

-  sample names;

-  filenames;

-  VCF headers;

-  source paths;

-  pedigree identifiers;

-  free-text INFO fields;

-  metadata files.

Before sharing a case, inspect the header:

.. code:: bash

   bcftools view \
   --header-only \
   case.vcf |
   less
   Search for obvious identifiers:
   grep -Ein \
   'patient|name|hospital|email|address|phone|date.of.birth|dob' \
   case.vcf \
   || true

This search is only an initial screening method. It does not guarantee de-identification.

Real patient inputs and full outputs must not be committed to GitHub.

The repository should contain only:

-  synthetic validation inputs;

-  de-identified controlled examples;

-  source code;

-  compact reference resources;

-  validation summaries.

.. _7-32-common-preflight-failures:

7.32 Common preflight failures
------------------------------

+------------------------------+----------------------------------+----------------------------------------------+
| **Failure**                  | **Likely cause**                 | **Required response**                        |
+==============================+==================================+==============================================+
| Missing ##fileformat         | Incomplete VCF header            | Re-export or repair the header               |
+------------------------------+----------------------------------+----------------------------------------------+
| Missing #CHROM               | Truncated VCF                    | Recover a complete source file               |
+------------------------------+----------------------------------+----------------------------------------------+
| bcftools view failure        | Malformed fields or quoting      | Inspect the reported line                    |
+------------------------------+----------------------------------+----------------------------------------------+
| REF mismatch                 | Wrong build or wrong allele      | Verify build and source coordinates          |
+------------------------------+----------------------------------+----------------------------------------------+
| Chromosome 1 instead of chr1 | Naming mismatch                  | Harmonise chromosome names                   |
+------------------------------+----------------------------------+----------------------------------------------+
| MT instead of chrM           | Mitochondrial naming mismatch    | Apply chromosome mapping                     |
+------------------------------+----------------------------------+----------------------------------------------+
| Multiple samples             | Cohort VCF supplied              | Select or split the required sample          |
+------------------------------+----------------------------------+----------------------------------------------+
| Missing genotype             | Sites-only VCF                   | Obtain genotype data or limit interpretation |
+------------------------------+----------------------------------+----------------------------------------------+
| Invalid INFO semicolon       | Malformed INFO field             | Repair the record in a derived copy          |
+------------------------------+----------------------------------+----------------------------------------------+
| Undefined symbolic ALT       | Incomplete SV header             | Add valid ALT definitions                    |
+------------------------------+----------------------------------+----------------------------------------------+
| Missing END for CNV          | Incomplete interval              | Recover the correct endpoint                 |
+------------------------------+----------------------------------+----------------------------------------------+
| Missing repeat fields        | Incomplete repeat representation | Route as unsupported or obtain complete data |
+------------------------------+----------------------------------+----------------------------------------------+
| CRLF line endings            | Windows-edited text              | Create a Unix-line-ending prepared copy      |
+------------------------------+----------------------------------+----------------------------------------------+
| Ordinary gzip file           | Not block-gzip compressed        | Recompress with bgzip                        |
+------------------------------+----------------------------------+----------------------------------------------+
| Missing tabix index          | Compressed file not indexed      | Run tabix -p vcf                             |
+------------------------------+----------------------------------+----------------------------------------------+
| HPO filename mismatch        | Incorrect case association       | Correct exact patient filename               |
+------------------------------+----------------------------------+----------------------------------------------+
| Invalid HPO identifier       | Typo or obsolete term            | Verify against installed HPO release         |
+------------------------------+----------------------------------+----------------------------------------------+

.. _7-33-complete-independent-preflight-command:

7.33 Complete independent preflight command
-------------------------------------------

The following reusable block checks a single VCF without modifying it:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="input/sample.small_variants.vcf"
   REFERENCE="resources/reference/hg38.fa"
   REFERENCE_INDEX="${REFERENCE}.fai"
   for required_file in \
   "$VCF" \
   "$REFERENCE" \
   "$REFERENCE_INDEX"
   do
   if [[ ! -s "$required_file" ]]; then
   echo "ERROR: Missing or empty file: $required_file"
   exit 1
   fi
   done
   echo "=== VCF PARSE CHECK ==="
   bcftools view \
   --output-type v \
   --output /dev/null \
   "$VCF"
   echo "PASS: bcftools parsed the VCF."
   echo
   echo "=== HEADER CHECK ==="
   bcftools view \
   --header-only \
   "$VCF" |
   grep -q '^##fileformat=VCFv4\.' ||
   {
   echo "ERROR: Invalid VCF fileformat."
   exit 1
   }
   bcftools view \
   --header-only \
   "$VCF" |
   grep -q '^#CHROM[[:space:]]' ||
   {
   echo "ERROR: #CHROM line is missing."
   exit 1
   }
   echo "PASS: Required VCF headers detected."
   echo
   echo "=== SAMPLE CHECK ==="
   SAMPLES="$(
   bcftools query \
   --list-samples \
   "$VCF"
   )"
   SAMPLE_COUNT="$(
   printf '%s\n' "$SAMPLES" |
   sed '/^$/d' |
   wc -l
   )"
   echo "Samples: $SAMPLE_COUNT"
   printf '%s\n' "$SAMPLES"
   if (( SAMPLE_COUNT != 1 )); then
   echo "ERROR: Expected exactly one sample."
   exit 1
   fi
   echo
   echo "=== RECORD CHECK ==="
   RECORD_COUNT="$(
   bcftools view \
   --no-header \
   "$VCF" |
   wc -l
   )"
   echo "Records: $RECORD_COUNT"
   if (( RECORD_COUNT == 0 )); then
   echo "ERROR: VCF contains no records."
   exit 1
   fi
   echo
   echo "=== CONTIG CHECK ==="
   TEMP_VCF_CONTIGS="$(mktemp)"
   TEMP_REF_CONTIGS="$(mktemp)"

trap '

.. code:: bash

   rm -f \
   "$TEMP_VCF_CONTIGS" \
   "$TEMP_REF_CONTIGS"

' EXIT

.. code:: bash

   bcftools query \
   --format '%CHROM\n' \
   "$VCF" |
   sort -u \
   > "$TEMP_VCF_CONTIGS"
   cut -f1 "$REFERENCE_INDEX" |
   sort -u \
   > "$TEMP_REF_CONTIGS"
   MISSING_CONTIGS="$(
   comm \
   -23 \
   "$TEMP_VCF_CONTIGS" \
   "$TEMP_REF_CONTIGS"
   )"
   if [[ -n "$MISSING_CONTIGS" ]]; then
   echo "ERROR: VCF contigs missing from FASTA:"
   echo "$MISSING_CONTIGS"
   exit 1
   fi
   echo "PASS: All VCF contigs exist in the reference."
   echo
   echo "=== REFERENCE-ALLELE CHECK ==="
   REF_LOG="$(mktemp)"
   if bcftools norm \
   --fasta-ref "$REFERENCE" \
   --check-ref e \
   --output-type v \
   --output /dev/null \
   "$VCF" \
   2> "$REF_LOG"
   then
   echo "PASS: Testable REF alleles match GRCh38."
   else
   echo "ERROR: Reference check failed."
   cat "$REF_LOG"
   rm -f "$REF_LOG"
   exit 1
   fi
   rm -f "$REF_LOG"
   echo
   echo "PASS: Independent VCF preflight completed."

This command confirms structural readability, required headers, sample count, record count, contig compatibility and reference-allele consistency.

It does not replace variant-class routing, metadata checks or specialised CNV and repeat-expansion validation.

.. _7-34-case-readiness-checklist:

7.34 Case readiness checklist
-----------------------------

A case is ready for the universal pipeline when:

-  

   .. container::

      ✓ The original input is preserved

-  

   .. container::

      ✓ The original checksum has been recorded

-  

   .. container::

      ✓ The VCF is structurally readable

-  

   .. container::

      ✓ The genome build is confirmed as GRCh38

-  

   .. container::

      ✓ Chromosome names match the reference

-  

   .. container::

      ✓ REF alleles match the reference where testable

-  

   .. container::

      ✓ The case contains one intended sample

-  

   .. container::

      ✓ Genotype information is available where required

-  

   .. container::

      ✓ HPO terms follow the correct syntax

-  

   .. container::

      ✓ Reported sex is recorded or explicitly marked unknown

-  

   .. container::

      ✓ Symbolic variants contain sufficient interval information

-  

   .. container::

      ✓ CNVs contain valid start, end and DEL/DUP values

-  

   .. container::

      ✓ Repeat expansions are identifiable as repeat records

-  

   .. container::

      ✓ The analysis mode is recorded

-  

   .. container::

      ✓ No validation-only resource is active in production mode

-  

   .. container::

      ✓ The original input has not been overwritten

Once these checks pass, the case can proceed to context resolution, variant detection and branch-specific preparation.

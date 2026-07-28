.. _12-pharmacogenomic-analysis-allele-aware-clinpgx-matching-and-interpretation:

12. Pharmacogenomic Analysis: Allele-Aware ClinPGx Matching and Interpretation
==============================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


The pharmacogenomic branch identifies variants that may influence drug response, drug metabolism, treatment toxicity or dose requirements. It operates alongside the rare-disease workflow but remains a separate evidence category.

ClinPGx integrates curated pharmacogenomic information from PharmGKB, CPIC and PharmCAT, including variant–drug evidence, gene–drug relationships, prescribing guidelines and genotype-to-phenotype information. The resource is intended to support interpretation by qualified healthcare professionals rather than provide independent treatment decisions.

The project implements a deliberately compact pharmacogenomic workflow:

Normalised patient variants

│

▼

Chromosome, position and allele harmonisation

│

▼

Exact local ClinPGx-reference matching

│

▼

Genotype and zygosity evaluation

│

▼

Curated star-allele assignment where supported

│

▼

Metaboliser or functional phenotype

│

▼

Associated drug information

│

▼

Case-level ClinPGx result table

The principal project files are:

-  

   .. container::

      pipeline/case_workflow/05_add_clinpgx_matches.py

-  

   .. container::

      pipeline/case_workflow/05b_add_local_pgx_reference.py

-  

   .. container::

      pipeline/case_workflow/05c_write_disabled_local_pgx.py

-  

   .. container::

      pipeline/case_workflow/11c_add_cnv_clinpgx.py

-  

   .. container::

      pipeline/setup_resources/02_test_clinpgx_api.py

-  

   .. container::

      pipeline/tests/04_test_allele_aware_local_pgx.py

PharmCAT is not part of the automated project scope. The current workflow uses ClinPGx only as an additional pharmacogenomic evidence source.

.. _12-1-purpose-of-pharmacogenomic-analysis:

12.1 Purpose of pharmacogenomic analysis
----------------------------------------

Pharmacogenomics evaluates how inherited genomic variation may influence a patient’s response to medication.

A pharmacogenomic result may relate to:

-  

   .. container::

      Drug metabolism

-  

   .. container::

      Drug transport

-  

   .. container::

      Drug efficacy

-  

   .. container::

      Adverse drug reactions

-  

   .. container::

      Toxicity risk

-  

   .. container::

      Dose requirements

-  

   .. container::

      Drug sensitivity

-  

   .. container::

      Drug resistance

The same variant may be medically relevant in a pharmacogenomic context even when it is unrelated to the patient’s suspected rare disease.

The rare-disease and pharmacogenomic outputs must therefore remain distinguishable:

Rare-disease evidence:

Does this variant help explain the patient’s phenotype?

Pharmacogenomic evidence:

Could this variant influence response to a medication?

A pharmacogenomic match should not increase the rare-disease pathogenicity score merely because it is associated with a drug.

.. _12-2-clinpgx-evidence-types:

12.2 ClinPGx evidence types
---------------------------

ClinPGx provides several forms of pharmacogenomic information.

.. _12-2-1-variant-annotations:

12.2.1 Variant annotations
~~~~~~~~~~~~~~~~~~~~~~~~~~

Variant annotations describe an association between a genetic variant and a drug-related phenotype reported in a publication.

They may contain information such as:

-  

   .. container::

      Variant

-  

   .. container::

      Gene

-  

   .. container::

      Allele

-  

   .. container::

      Drug

-  

   .. container::

      Population

-  

   .. container::

      Phenotype category

-  

   .. container::

      Direction of association

-  

   .. container::

      Study findings

-  

   .. container::

      Publication

ClinPGx states that its variant annotations are manually curated from published studies and that alleles are represented on the positive chromosomal strand.

.. _12-2-2-summary-annotations:

12.2.2 Summary annotations
~~~~~~~~~~~~~~~~~~~~~~~~~~

Summary annotations combine evidence from several variant annotations that concern the same variant–drug relationship.

They may provide:

-  

   .. container::

      Genotype-based summary

-  

   .. container::

      Drug-response phenotype

-  

   .. container::

      Evidence level

-  

   .. container::

      Supporting publications

-  

   .. container::

      Guideline information

-  

   .. container::

      Drug-label information

ClinPGx assigns evidence levels using the amount and quality of supporting evidence, including agreement or disagreement among studies.

.. _12-2-3-clinical-guidelines:

12.2.3 Clinical guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~

CPIC guidelines translate available pharmacogenomic test results into prescribing recommendations.

CPIC guidelines are primarily designed to explain **how an available genetic result can be used**, rather than determine whether a genetic test should be ordered. They include genotype-to-phenotype translation and recommendation-strength grading. (ClinPGx)

The project may preserve guideline-related information in the local reference, but it does not independently issue prescriptions or dose changes.

.. _12-2-4-drug-label-annotations:

12.2.4 Drug-label annotations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drug labels from regulatory agencies may include statements about:

-  required genetic testing;

-  recommended testing;

-  actionable genomic biomarkers;

-  altered metabolism;

-  increased toxicity;

-  reduced effectiveness.

A drug-label association and a CPIC recommendation are not necessarily equivalent. Their evidence standards, wording and intended uses may differ.

.. _12-3-project-clinpgx-design:

12.3 Project ClinPGx design
---------------------------

The project uses two complementary sources:

1. A local curated ClinPGx reference

2. Optional ClinPGx API access

The local reference is the primary reproducible source for automated matching.

The API is used only for:

-  connectivity testing;

-  controlled supplementary retrieval;

-  updating or checking selected records;

-  confirming that the current ClinPGx service is accessible.

This design prevents normal case analysis from depending on a live web service.

.. _12-4-local-clinpgx-resource:

12.4 Local ClinPGx resource
---------------------------

The local resource files are stored under:

resources/clinpgx/

├── LOCAL_REFERENCE_SCHEMA.txt

├── local_curated_pgx_reference.csv

├── local_curated_pgx_reference.sha256

├── cache/

└── metadata/

.. _12-4-1-local-reference-schema-txt:

12.4.1 LOCAL_REFERENCE_SCHEMA.txt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file defines the expected structure of the local pharmacogenomic reference.

It should document:

-  required columns;

-  genome build;

-  chromosome convention;

-  allele orientation;

-  allowed genotype formats;

-  star-allele representation;

-  drug field;

-  phenotype field;

-  interpretation field;

-  source information.

Inspect it with:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SCHEMA="resources/clinpgx/LOCAL_REFERENCE_SCHEMA.txt"
   if [[ ! -s "$SCHEMA" ]]; then
   echo "ERROR: ClinPGx schema file is missing:"
   echo "$SCHEMA"
   exit 1
   fi
   cat "$SCHEMA"

The schema file should be treated as authoritative for the committed local reference.

.. _12-4-2-local-curated-pgx-reference-csv:

12.4.2 local_curated_pgx_reference.csv
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file contains selected pharmacogenomic records that can be matched directly to patient variants.

Its fields may include:

-  

   .. container::

      Gene

-  

   .. container::

      Chromosome

-  

   .. container::

      Position

-  

   .. container::

      Reference allele

-  

   .. container::

      Alternate allele

-  

   .. container::

      rsID

-  

   .. container::

      Star allele

-  

   .. container::

      Functional phenotype

-  

   .. container::

      Drug

-  

   .. container::

      Interpretation

The exact header must be obtained from the committed file rather than reconstructed manually.

Inspect the file safely:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PGX_REFERENCE="resources/clinpgx/local_curated_pgx_reference.csv"
   if [[ ! -s "$PGX_REFERENCE" ]]; then
   echo "ERROR: Local ClinPGx reference is missing:"
   echo "$PGX_REFERENCE"
   exit 1
   fi
   python3 - "$PGX_REFERENCE" <<'PY'
   from __future__ import annotations
   import csv
   import sys
   from pathlib import Path
   path = Path(sys.argv[1])
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.reader(handle)
   header = next(reader, None)
   if not header:
   raise SystemExit("ERROR: CSV header is missing.")
   rows = [
   row
   for row in reader
   if row and any(value.strip() for value in row)
   ]
   print(f"File: {path}")
   print(f"Data rows: {len(rows)}")
   print(f"Columns: {len(header)}")
   print()
   for index, column in enumerate(header, start=1):
   print(f"{index:02d}. {column}")
   print()
   print("First records:")
   for row in rows[:5]:
   print(row)
   PY

This inspection command does not alter the reference.

.. _12-4-3-check-the-local-reference-checksum:

12.4.3 Check the local reference checksum
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the committed checksum without depending on the path stored inside the .sha256 file:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PGX_REFERENCE="resources/clinpgx/local_curated_pgx_reference.csv"
   PGX_CHECKSUM="resources/clinpgx/local_curated_pgx_reference.sha256"
   if [[ ! -s "$PGX_REFERENCE" ]]; then
   echo "ERROR: ClinPGx reference is missing."
   exit 1
   fi
   if [[ ! -s "$PGX_CHECKSUM" ]]; then
   echo "ERROR: ClinPGx checksum file is missing."
   exit 1
   fi
   EXPECTED_SHA256="$(
   awk 'NR == 1 {print $1}' \
   "$PGX_CHECKSUM"
   )"
   if [[ ! "$EXPECTED_SHA256" =~ ^[0-9a-fA-F]{64}$ ]]; then
   echo "ERROR: Invalid SHA-256 value in:"
   echo "$PGX_CHECKSUM"
   exit 1
   fi
   printf '%s %s\n' \
   "$EXPECTED_SHA256" \
   "$PGX_REFERENCE" |
   sha256sum --check -

Expected:

resources/clinpgx/local_curated_pgx_reference.csv: OK

If the checksum fails, the file must be reviewed before analysis. It should not be silently accepted or automatically replaced.

.. _12-5-validate-the-local-clinpgx-csv-structurally:

12.5 Validate the local ClinPGx CSV structurally
------------------------------------------------

The following validator:

-  checks that every row has the same number of columns;

-  detects duplicate column names;

-  locates the allele-matching columns;

-  checks genomic positions;

-  checks chromosome names;

-  detects duplicate gene–allele keys.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PGX_REFERENCE="resources/clinpgx/local_curated_pgx_reference.csv"
   python3 - "$PGX_REFERENCE" <<'PY'
   from __future__ import annotations
   import csv
   import re
   import sys
   from collections import Counter
   from pathlib import Path
   path = Path(sys.argv[1])
   if not path.is_file() or path.stat().st_size == 0:
   raise SystemExit(
   f"ERROR: Missing or empty ClinPGx reference: {path}"
   )
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.reader(handle)
   header = next(reader, None)
   if not header:
   raise SystemExit("ERROR: CSV header is missing.")
   rows = [
   row
   for row in reader
   if row and any(value.strip() for value in row)
   ]
   header = [value.strip() for value in header]
   if any(not value for value in header):
   raise SystemExit(
   "ERROR: One or more CSV header fields are blank."
   )
   duplicates = [
   name
   for name, count in Counter(header).items()
   if count > 1
   ]
   if duplicates:
   raise SystemExit(
   "ERROR: Duplicate CSV columns: "
   + ", ".join(duplicates)
   )
   expected_width = len(header)
   width_failures = []
   for line_number, row in enumerate(rows, start=2):
   if len(row) != expected_width:
   width_failures.append(
   (line_number, len(row))
   )
   if width_failures:
   print("ERROR: Inconsistent CSV row widths:")
   for line_number, observed_width in width_failures:
   print(
   f" line {line_number}: "
   f"{observed_width} columns; "
   f"expected {expected_width}"
   )
   raise SystemExit(1)
   def normalise_header(value: str) -> str:
   value = value.strip().lower()
   value = re.sub(r"[^a-z0-9]+", "_", value)
   return value.strip("_")
   normalised = {
   normalise_header(column): index
   for index, column in enumerate(header)
   }
   aliases = {
   "gene": (
   "gene",
   "gene_symbol",
   "symbol",
   ),
   "chromosome": (
   "chromosome",
   "chrom",
   "chr",
   ),
   "position": (
   "position",
   "pos",
   "genomic_position",
   ),
   "reference": (
   "reference",
   "ref",
   "reference_allele",
   ),
   "alternate": (
   "alternate",
   "alt",
   "alternate_allele",
   ),
   "rsid": (
   "rsid",
   "rs_id",
   "variant_id",
   ),
   }
   def find_column(label: str) -> int | None:
   for candidate in aliases[label]:
   if candidate in normalised:
   return normalised[candidate]
   return None
   indices = {
   label: find_column(label)
   for label in aliases
   }
   required = (
   "gene",
   "chromosome",
   "position",
   "reference",
   "alternate",
   )
   missing = [
   label
   for label in required
   if indices[label] is None
   ]
   if missing:
   print("Detected header:")
   print(header)
   raise SystemExit(
   "ERROR: Required allele-aware columns were not found: "
   + ", ".join(missing)
   )
   allowed_chromosome = re.compile(
   r"^chr(?:[1-9]|1[0-9]|2[0-2]|X|Y|M)$"
   )
   validation_failures = []
   seen_keys: dict[
   tuple[str, str, int, str, str],
   int,
   ] = {}
   for line_number, row in enumerate(rows, start=2):
   gene = row[indices["gene"]].strip()
   chromosome = row[indices["chromosome"]].strip()
   position_text = row[indices["position"]].strip()
   reference = row[indices["reference"]].strip().upper()
   alternate = row[indices["alternate"]].strip().upper()
   if not gene:
   validation_failures.append(
   f"line {line_number}: empty gene"
   )
   if not allowed_chromosome.fullmatch(chromosome):
   validation_failures.append(
   f"line {line_number}: "
   f"invalid chromosome {chromosome!r}"
   )
   try:
   position = int(position_text)
   except ValueError:
   validation_failures.append(
   f"line {line_number}: "
   f"invalid position {position_text!r}"
   )
   continue
   if position < 1:
   validation_failures.append(
   f"line {line_number}: "
   "position must be at least 1"
   )
   if not reference:
   validation_failures.append(
   f"line {line_number}: empty reference allele"
   )
   if not alternate:
   validation_failures.append(
   f"line {line_number}: empty alternate allele"
   )
   key = (
   gene.upper(),
   chromosome,
   position,
   reference,
   alternate,
   )
   previous_line = seen_keys.get(key)
   if previous_line is not None:
   validation_failures.append(
   f"line {line_number}: duplicate allele key; "
   f"first seen at line {previous_line}: {key}"
   )
   else:
   seen_keys[key] = line_number
   if validation_failures:
   print("ERROR: ClinPGx reference validation failed:")
   for message in validation_failures:
   print(f" {message}")
   raise SystemExit(1)
   print(f"PASS: {len(rows)} ClinPGx record(s) validated.")
   print(f"PASS: {len(header)} columns have consistent structure.")
   print("PASS: Allele-aware keys are unique.")
   PY

A duplicate genomic key is not necessarily biologically invalid when several drugs are linked to the same allele. In that situation, the uniqueness rule should include the drug or annotation identifier. The committed schema and matching script determine the final key.

.. _12-6-allele-orientation:

12.6 Allele orientation
-----------------------

ClinPGx represents alleles on the positive genomic strand, including genes that are transcribed from the negative strand.

The project VCF also represents REF and ALT alleles relative to the GRCh38 reference sequence. Therefore, allele matching should normally compare the forward-reference alleles directly.

The pipeline must avoid:

-  

   .. container::

      Complementing a variant twice

-  

   .. container::

      Using transcript-oriented alleles against genomic alleles

-  

   .. container::

      Ignoring REF and ALT orientation

-  

   .. container::

      Matching only by rsID

-  

   .. container::

      Matching an allele from the wrong genome build

For a negative-strand gene, the HGVS coding allele may appear complementary to the genomic VCF allele. This does not necessarily represent a disagreement.

For example:

Genomic representation: GRCh38 forward strand

Transcript representation: gene-transcript orientation

The matching stage must use one consistent genomic orientation.

.. _12-7-required-matching-fields:

12.7 Required matching fields
-----------------------------

A reliable local pharmacogenomic match should consider:

-  

   .. container::

      Genome build

-  

   .. container::

      Chromosome

-  

   .. container::

      Position

-  

   .. container::

      Reference allele

-  

   .. container::

      Alternate allele

-  

   .. container::

      Gene

-  

   .. container::

      rsID, where available

-  

   .. container::

      Genotype

-  

   .. container::

      The central allele key is:

-  

   .. container::

      CHROM + POS + REF + ALT

The gene and rsID provide additional confirmation.

The rsID must not be the only matching field because:

-  one rsID may represent several alternate alleles;

-  reference and alternate alleles can differ by genome build;

-  merged or updated identifiers may occur;

-  strand representation can cause confusion;

-  a VCF may contain a correct genomic allele without an rsID;

-  an rsID may be present on the wrong allele record.

.. _12-8-allele-aware-matching-logic:

12.8 Allele-aware matching logic
--------------------------------

The principal local-matching script is:

pipeline/case_workflow/05b_add_local_pgx_reference.py

The conceptual matching process is:

1. Confirm the case and reference use GRCh38.

2. Standardise chromosome names.

3. Normalise the patient variant.

4. Compare chromosome and position.

5. Compare REF and ALT exactly.

6. Confirm the gene where available.

7. Compare the rsID as supporting evidence.

8. Evaluate the patient genotype.

9. Assign a curated star allele only when supported.

10. Attach the corresponding phenotype and drug information.

A position-only or rsID-only match must not be reported as an exact pharmacogenomic allele match.

.. _12-8-1-example-of-correct-matching:

12.8.1 Example of correct matching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Patient variant:

+-----------------------------------------------------------------------+
| Gene: TPMT                                                            |
+=======================================================================+
| Chromosome: chr6                                                      |
+-----------------------------------------------------------------------+
| Position: 18130687                                                    |
+-----------------------------------------------------------------------+
| REF: T                                                                |
+-----------------------------------------------------------------------+
| ALT: C                                                                |
+-----------------------------------------------------------------------+
| rsID: rs1142345                                                       |
+-----------------------------------------------------------------------+
| GT: 0/1                                                               |
+-----------------------------------------------------------------------+
| Local reference:                                                      |
+-----------------------------------------------------------------------+
| Gene: TPMT                                                            |
+-----------------------------------------------------------------------+
| Chromosome: chr6                                                      |
+-----------------------------------------------------------------------+
| Position: 18130687                                                    |
+-----------------------------------------------------------------------+
| REF: T                                                                |
+-----------------------------------------------------------------------+
| ALT: C                                                                |
+-----------------------------------------------------------------------+
| rsID: rs1142345                                                       |
+-----------------------------------------------------------------------+

Result:

Exact genomic allele match

The genotype can then be evaluated using the curated project rule.

.. _12-8-2-example-of-an-allele-mismatch:

12.8.2 Example of an allele mismatch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Patient variant:

+-----------------------------------------------------------------------+
| Chromosome: chr6                                                      |
+=======================================================================+
| Position: 18130687                                                    |
+-----------------------------------------------------------------------+
| REF: T                                                                |
+-----------------------------------------------------------------------+
| ALT: A                                                                |
+-----------------------------------------------------------------------+
| rsID: rs1142345                                                       |
+-----------------------------------------------------------------------+
| Local reference:                                                      |
+-----------------------------------------------------------------------+
| Chromosome: chr6                                                      |
+-----------------------------------------------------------------------+
| Position: 18130687                                                    |
+-----------------------------------------------------------------------+
| REF: T                                                                |
+-----------------------------------------------------------------------+
| ALT: C                                                                |
+-----------------------------------------------------------------------+
| rsID: rs1142345                                                       |
+-----------------------------------------------------------------------+

Result:

No exact allele match

The shared rsID must not override the alternate-allele mismatch.

.. _12-9-inspect-the-local-matching-script:

12.9 Inspect the local matching script
--------------------------------------

Compile the source:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/05b_add_local_pgx_reference.py"
   if [[ ! -s "$SCRIPT" ]]; then
   echo "ERROR: Local ClinPGx matching script is missing:"
   echo "$SCRIPT"
   exit 1
   fi
   python -m py_compile "$SCRIPT"
   echo "PASS: $SCRIPT"

Inspect its command-line interface:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/05b_add_local_pgx_reference.py"
   if python "$SCRIPT" --help \
   > /tmp/local_pgx_help.txt \
   2>&1
   then
   cat /tmp/local_pgx_help.txt
   else
   echo "INFO: No standard --help interface was returned."
   echo "Argument definitions found in source:"
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$SCRIPT" \
   || true
   fi
   rm -f /tmp/local_pgx_help.txt

The production launcher should call this script automatically. A manual command should be constructed only from the actual interface shown by the committed version.

.. _12-10-allele-aware-regression-test:

12.10 Allele-aware regression test
----------------------------------

The project includes:

pipeline/tests/04_test_allele_aware_local_pgx.py

This test verifies that:

-  

   .. container::

      An exact allele can match

-  

   .. container::

      A wrong alternate allele cannot match

-  

   .. container::

      A shared rsID is insufficient by itself

-  

   .. container::

      Non-matching variants remain unmatched

-  

   .. container::

      Expected genotype information is retained

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   TEST_SCRIPT="pipeline/tests/04_test_allele_aware_local_pgx.py"
   if [[ ! -s "$TEST_SCRIPT" ]]; then
   echo "ERROR: ClinPGx regression test is missing:"
   echo "$TEST_SCRIPT"
   exit 1
   fi
   python -m py_compile "$TEST_SCRIPT"
   python "$TEST_SCRIPT"
   echo
   echo "PASS: Allele-aware local ClinPGx regression test completed."

A zero exit status is required.

.. _12-11-genotype-aware-interpretation:

12.11 Genotype-aware interpretation
-----------------------------------

After an exact allele match is identified, the pipeline evaluates the patient genotype.

Examples include:

+-----------------+----------------------------------------------------+
| **Genotype**    | **General state**                                  |
+=================+====================================================+
| 0/0             | Reference allele not carried                       |
+-----------------+----------------------------------------------------+
| 0/1             | One alternate allele carried                       |
+-----------------+----------------------------------------------------+
| 1/1             | Two copies of the alternate allele                 |
+-----------------+----------------------------------------------------+
| \`0             | 1\`                                                |
+-----------------+----------------------------------------------------+
| \`1             | 0\`                                                |
+-----------------+----------------------------------------------------+
| 1               | Haploid alternate allele                           |
+-----------------+----------------------------------------------------+
| ./.             | Genotype unavailable                               |
+-----------------+----------------------------------------------------+

The same alternate allele can produce different interpretations depending on whether it is:

-  

   .. container::

      Heterozygous

-  

   .. container::

      Homozygous

-  

   .. container::

      Hemizygous

-  

   .. container::

      Part of a compound diplotype

-  

   .. container::

      Unphased

-  

   .. container::

      Missing

A variant should not be reported as carried solely because its locus is present in the VCF. The sample genotype must contain the corresponding alternate allele.

.. _12-11-1-check-whether-the-alternate-allele-is-carried:

12.11.1 Check whether the alternate allele is carried
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A simple biallelic variant with:

REF=A

ALT=G

has alternate-allele index:

1

Therefore:

0/0 alternate allele not carried

0/1 one alternate copy

1/1 two alternate copies

For a decomposed multiallelic site, genotype handling must preserve allele-index provenance.

The project should use its shared genotype utilities rather than searching the genotype string for the character 1.

.. _12-12-star-alleles:

12.12 Star alleles
------------------

A star allele is a named haplotype used for many pharmacogenes.

Examples include:

TPMT \*1

TPMT \*3C

CYP2D6 \*1

CYP2D6 \*4

DPYD \*1

DPYD \*2A

A star allele may be defined by:

-  one characteristic variant;

-  several variants;

-  a phased combination of variants;

-  a deletion;

-  a duplication;

-  a gene conversion;

-  a hybrid allele;

-  copy-number information.

The local project reference supports only the star-allele assignments explicitly represented in its curated records.

It must not infer every possible star allele from one variant.

.. _12-12-1-simple-single-variant-assignments:

12.12.1 Simple single-variant assignments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For selected project validation records, one curated variant is used to support a simplified star-allele interpretation.

Examples from the synthetic validation suite include:

TPMT rs1142345

Heterozygous project interpretation:

\*1/\*3C

Intermediate metaboliser

CYP2D6 rs3892097

Heterozygous project interpretation:

\*1/\*4

Intermediate metaboliser

DPYD rs3918290

Heterozygous project interpretation:

\*1/\*2A

Intermediate metaboliser

These examples validate the project’s local matching and output logic. They do not demonstrate comprehensive haplotype calling.

.. _12-12-2-complex-star-allele-limitations:

12.12.2 Complex star-allele limitations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current local workflow does not fully resolve:

-  

   .. container::

      CYP2D6 gene deletions

-  

   .. container::

      CYP2D6 duplications

-  

   .. container::

      CYP2D6 hybrid genes

-  

   .. container::

      Tandem arrangements

-  

   .. container::

      Copy-number-dependent diplotypes

-  

   .. container::

      Multi-variant unphased haplotypes

-  

   .. container::

      Structural star alleles

-  

   .. container::

      Novel star alleles

-  

   .. container::

      Alleles requiring long-read confirmation

For example, detecting rs3892097 alone does not exclude the possibility that other CYP2D6 variants or structural changes are also present.

Therefore, the output should state that its star-allele interpretation is based on the project’s curated marker set.

.. _12-13-diplotypes-and-phenotype-assignment:

12.13 Diplotypes and phenotype assignment
-----------------------------------------

A diplotype describes the pair of haplotypes carried for a diploid pharmacogene.

Example:

-  

   .. container::

      TPMT \*1/\*3C

-  

   .. container::

      The diplotype may be translated to a functional phenotype such as:

-  

   .. container::

      Normal metaboliser

-  

   .. container::

      Intermediate metaboliser

-  

   .. container::

      Poor metaboliser

-  

   .. container::

      Rapid metaboliser

-  

   .. container::

      Ultrarapid metaboliser

-  

   .. container::

      Indeterminate

-  

   .. container::

      Not every gene uses the same phenotype terminology.

-  

   .. container::

      Other pharmacogenes may use classifications such as:

-  

   .. container::

      Normal function

-  

   .. container::

      Decreased function

-  

   .. container::

      No function

-  

   .. container::

      Increased function

-  

   .. container::

      Deficient

-  

   .. container::

      Variable

-  

   .. container::

      Indeterminate

The pipeline must preserve the phenotype terminology provided by the curated gene-specific reference rather than applying one universal metaboliser scale to every gene.

.. _12-14-missing-reference-allele-and-default-star-assumptions:

12.14 Missing reference allele and default-star assumptions
-----------------------------------------------------------

A common simplified assumption is:

One detected non-reference star allele

+

One unspecified chromosome

=

\*1/non-reference allele

This assumption is not always valid.

The absence of another recorded variant may mean:

-  

   .. container::

      The second chromosome carries \*1

-  

   .. container::

      The second chromosome was not fully tested

-  

   .. container::

      The required locus was absent from the VCF

-  

   .. container::

      Coverage was insufficient

-  

   .. container::

      The second allele contains an untested variant

-  

   .. container::

      A structural allele is present

The project’s synthetic validation records may use a controlled \*1 assumption because the expected input content is known.

For external data, the output should distinguish:

Curated project diplotype

from:

Comprehensively resolved clinical diplotype

.. _12-15-positive-and-negative-pgx-findings:

12.15 Positive and negative PGx findings
----------------------------------------

The pipeline should distinguish at least four broad outcomes.

.. _12-15-1-exact-match:

12.15.1 Exact match
~~~~~~~~~~~~~~~~~~~

The genomic allele matches the local reference

and the alternate allele is carried.

.. _12-15-2-locus-detected-but-allele-mismatched:

12.15.2 Locus detected but allele mismatched
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The chromosome or rsID is shared,

but REF and ALT do not match the curated allele.

This is not a valid exact match.

.. _12-15-3-reference-allele-or-no-alternate-copy:

12.15.3 Reference allele or no alternate copy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The locus may be present,

but the patient genotype does not carry

the pharmacogenomic alternate allele.

.. _12-15-4-not-assessed:

12.15.4 Not assessed
~~~~~~~~~~~~~~~~~~~~

The required locus was absent,

the genotype was missing,

the PGx stage was disabled,

or the local reference lacks the allele.

Not assessed must not be reported as a normal pharmacogenomic result.

.. _12-16-missing-loci-and-vcf-limitations:

12.16 Missing loci and VCF limitations
--------------------------------------

A variant-only VCF usually contains sites where an alternate allele was called.

It may not contain reference-genotype records for every pharmacogenomic locus.

Therefore:

Variant absent from VCF

does not necessarily mean:

Patient is homozygous reference

It may mean:

-  

   .. container::

      The position was not called

-  

   .. container::

      The position was not targeted

-  

   .. container::

      The position lacked sufficient coverage

-  

   .. container::

      Reference calls were excluded

The variant caller emitted variants only

The project should not assign a complete normal diplotype from the absence of a variant in a variants-only VCF.

.. _12-17-api-access:

12.17 API access
----------------

The committed API test script is:

.. code:: bash

   pipeline/setup_resources/02_test_clinpgx_api.py

ClinPGx’s official API notice states that the former PharmGKB API hostname was scheduled to be disabled on 20 July 2026 and that clients should use api.clinpgx.org. The API documentation also requests a limit of two requests per second and notes that parameters or responses may change while development continues.

The project therefore uses:

https://api.clinpgx.org

and must not use:

https://api.pharmgkb.org

for new code.

.. _12-17-1-compile-the-api-test-script:

12.17.1 Compile the API test script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/setup_resources/02_test_clinpgx_api.py"
   if [[ ! -s "$SCRIPT" ]]; then
   echo "ERROR: ClinPGx API test script is missing:"
   echo "$SCRIPT"
   exit 1
   fi
   python -m py_compile "$SCRIPT"

echo "PASS: ClinPGx API test script passed syntax validation."

.. _12-17-2-confirm-the-api-hostname-in-the-source:

12.17.2 Confirm the API hostname in the source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SCRIPT="pipeline/setup_resources/02_test_clinpgx_api.py"
   echo "=== ClinPGx-related hostnames in script ==="
   grep -Eo \
   'https?://[^"'"'"'[:space:]]+' \
   "$SCRIPT" |
   sort -u \
   || true
   Search the complete project for the obsolete hostname:
   cd ~/rare_disease_project
   set -Eeuo pipefail
   OLD_HOST_MATCHES="$(
   grep -RIn \
   --exclude-dir=.git \
   --exclude='*.md' \
   --exclude='*.txt' \
   --exclude='*.tsv' \
   --exclude='*.csv' \
   'api\.pharmgkb\.org' \
   pipeline \
   resources \
   2>/dev/null \
   || true
   )"
   if [[ -n "$OLD_HOST_MATCHES" ]]; then
   echo "WARNING: Obsolete API hostname found:"
   echo "$OLD_HOST_MATCHES"
   else
   echo "PASS: No obsolete PharmGKB API hostname found in active code."
   fi

Documentation or historical metadata may still mention the older hostname. Active executable code should use the ClinPGx hostname.

.. _12-17-3-run-the-api-connectivity-test:

12.17.3 Run the API connectivity test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/setup_resources/02_test_clinpgx_api.py

The script should create or update:

.. code:: bash

   resources/clinpgx/metadata/clinpgx_api_test.tsv

Inspect the metadata safely:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   METADATA="resources/clinpgx/metadata/clinpgx_api_test.tsv"
   if [[ ! -s "$METADATA" ]]; then
   echo "ERROR: ClinPGx API metadata file was not created:"
   echo "$METADATA"
   exit 1
   fi
   python3 - "$METADATA" <<'PY'
   from __future__ import annotations
   import csv
   import sys
   from pathlib import Path
   path = Path(sys.argv[1])
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.reader(
   handle,
   delimiter="\t",
   )
   rows = list(reader)
   if not rows:
   raise SystemExit("ERROR: API metadata file is empty.")
   width = max(len(row) for row in rows)
   for row in rows:
   padded = row + [""] * (width - len(row))
   print("\t".join(padded))
   print()
   print(f"PASS: Read {len(rows)} metadata row(s).")
   PY

An API failure should be recorded clearly, but it should not prevent deterministic local matching when the local reference is valid.

.. _12-18-api-caching-and-rate-limiting:

12.18 API caching and rate limiting
-----------------------------------

API responses should be cached under:

resources/clinpgx/cache/

A cached response should be accompanied by metadata such as:

-  

   .. container::

      Endpoint

-  

   .. container::

      Query parameters

-  

   .. container::

      Retrieval time

-  

   .. container::

      HTTP status

-  

   .. container::

      Record count

-  

   .. container::

      Response filename

-  

   .. container::

      Checksum

The API client should not exceed the official two-request-per-second limit.

A safe conceptual request loop includes at least a half-second delay:

import time

for request in requests_to_make:

-  

   .. container::

      retrieve(request)

-  

   .. container::

      time.sleep(0.5)

The committed API test script remains authoritative for the actual request implementation.

.. _12-18-1-inspect-cached-files:

12.18.1 Inspect cached files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CACHE_DIR="resources/clinpgx/cache"
   if [[ ! -d "$CACHE_DIR" ]]; then
   echo "INFO: ClinPGx cache directory does not yet exist."
   exit 0
   fi
   find "$CACHE_DIR" \
   -type f \
   -printf '%s\t%TY-%Tm-%TdT%TH:%TM:%TS\t%p\n' |
   sort -k3,3

Generate cache checksums:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CACHE_DIR="resources/clinpgx/cache"
   CHECKSUM_FILE="resources/clinpgx/metadata/clinpgx_cache.sha256"
   mkdir -p \
   resources/clinpgx/metadata
   if find "$CACHE_DIR" \
   -type f \
   -print -quit |
   grep -q .
   then
   find "$CACHE_DIR" \
   -type f \
   -print0 |
   sort -z |
   xargs -0 sha256sum \
   > "$CHECKSUM_FILE"
   sha256sum \
   --check \
   "$CHECKSUM_FILE"
   else
   echo "INFO: No ClinPGx cache files are present."
   fi

.. _12-19-api-data-limitations:

12.19 API-data limitations
--------------------------

Live API data may change independently of the committed pipeline.

Changes can include:

-  

   .. container::

      New annotations

-  

   .. container::

      Revised evidence levels

-  

   .. container::

      Updated drug names

-  

   .. container::

      Changed endpoint responses

-  

   .. container::

      New guideline versions

-  

   .. container::

      Corrected variant mappings

-  

   .. container::

      Updated phenotype terminology

Therefore, a reproducible case should record either:

The exact cached API response and checksum

or:

That only the committed local ClinPGx reference was used

A live API response should not silently alter a previously validated result.

.. _12-20-local-matching-versus-online-evidence:

12.20 Local matching versus online evidence
-------------------------------------------

The project separates two questions.

**Local matching**

Does this exact patient allele match

a curated allele in the project reference?

**Online evidence review**

What current pharmacogenomic evidence,

guidelines and annotations exist for that allele?

The first can be automated reproducibly.

The second may require:

-  current ClinPGx review;

-  CPIC guideline review;

-  drug-label review;

-  gene-specific allele-definition review;

-  specialist interpretation.

.. _12-21-clinical-recommendation-boundaries:

12.21 Clinical recommendation boundaries
----------------------------------------

The pipeline may report a curated pharmacogenomic phenotype and associated drugs, but it must not independently instruct a patient to:

-  

   .. container::

      Start a medication

-  

   .. container::

      Stop a medication

-  

   .. container::

      Change a dose

-  

   .. container::

      Substitute a drug

-  

   .. container::

      Ignore a prescription

ClinPGx and CPIC both state that their information should not be used for direct medical decision-making without professional review.

The final output should therefore use wording such as:

-  

   .. container::

      Potential pharmacogenomic relevance identified.

-  

   .. container::

      Confirm the genotype, diplotype and current guideline

.. container::

   before clinical use.

.. _12-22-main-local-pgx-scripts:

12.22 Main local PGx scripts
----------------------------

.. _12-22-1-05-add-clinpgx-matches-py:

12.22.1 05_add_clinpgx_matches.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script integrates pharmacogenomic matches into the case workflow.

Its responsibilities may include:

-  reading the annotated variant table;

-  selecting pharmacogenomic candidate variants;

-  adding source identifiers;

-  recording matching evidence;

-  creating a case-level PGx output.

.. _12-22-2-05b-add-local-pgx-reference-py:

12.22.2 05b_add_local_pgx_reference.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the main deterministic local-reference matcher.

Its responsibilities include:

-  normalising genomic keys;

-  matching exact alleles;

-  evaluating genotype;

-  attaching star-allele information;

-  adding functional phenotype;

adding drug associations;

-  preventing rsID-only false matches.

.. _12-22-3-05c-write-disabled-local-pgx-py:

12.22.3 05c_write_disabled_local_pgx.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script creates an explicit result when local PGx matching is disabled.

It prevents:

No output file

from being confused with:

No pharmacogenomic variants detected

A disabled-stage result should state:

-  

   .. container::

      Stage disabled

-  

   .. container::

      Reason

-  

   .. container::

      Case identifier

-  

   .. container::

      Execution time

-  

   .. container::

      Reference status

.. _12-22-4-11c-add-cnv-clinpgx-py:

12.22.4 11c_add_cnv_clinpgx.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script evaluates whether a deletion or duplication overlaps a pharmacogenomically relevant gene.

A CNV overlap should be reported separately from a small-variant star-allele result.

For example:

CYP2D6 copy-number change detected

does not automatically provide a complete CYP2D6 diplotype.

Structural pharmacogenomic interpretation may require specialised copy-number and haplotype analysis.

.. _12-23-cnv-pharmacogenomic-limitations:

12.23 CNV pharmacogenomic limitations
-------------------------------------

A deletion or duplication involving a pharmacogene can affect drug response, but gene overlap alone may be insufficient.

The interpretation can depend on:

-  

   .. container::

      Complete or partial gene overlap

-  

   .. container::

      Copy-number direction

-  

   .. container::

      Number of copies

-  

   .. container::

      Hybrid alleles

-  

   .. container::

      Tandem arrangements

-  

   .. container::

      Phasing with SNVs

-  

   .. container::

      Gene conversion

-  

   .. container::

      Breakpoint precision

The project CNV PGx stage should therefore report:

Potential PGx gene overlap

rather than automatically assigning a final star allele.

.. _12-24-recommended-clinpgx-output-fields:

12.24 Recommended ClinPGx output fields
---------------------------------------

The pharmacogenomic table should preserve fields such as:

-  

   .. container::

      case_id

-  

   .. container::

      sample_id

-  

   .. container::

      chromosome

-  

   .. container::

      position

-  

   .. container::

      reference

-  

   .. container::

      alternate

-  

   .. container::

      variant_id

-  

   .. container::

      gene

-  

   .. container::

      genotype

-  

   .. container::

      zygosity

-  

   .. container::

      alternate_allele_count

-  

   .. container::

      match_status

-  

   .. container::

      match_method

-  

   .. container::

      genome_build

-  

   .. container::

      allele_orientation

-  

   .. container::

      reference_rsid

-  

   .. container::

      reference_star_allele

-  

   .. container::

      predicted_diplotype

-  

   .. container::

      functional_phenotype

-  

   .. container::

      drug

-  

   .. container::

      interpretation

-  

   .. container::

      evidence_source

-  

   .. container::

      evidence_level

-  

   .. container::

      guideline_source

-  

   .. container::

      reference_version

-  

   .. container::

      reference_checksum

-  

   .. container::

      warning

The exact output columns should follow the committed script.

.. _12-25-match-status-design:

12.25 Match-status design
-------------------------

Useful match states include:

-  

   .. container::

      exact_allele_match

-  

   .. container::

      allele_mismatch

-  

   .. container::

      position_only_match

-  

   .. container::

      rsid_only_match

-  

   .. container::

      reference_genotype

-  

   .. container::

      genotype_missing

-  

   .. container::

      no_local_reference_match

-  

   .. container::

      stage_disabled

-  

   .. container::

      not_assessed

These are conceptual status categories. The production table must use the exact labels implemented by the committed code.

A non-exact match should remain visible for review but must not be presented as a confirmed local PGx result.

.. _12-26-validate-selected-synthetic-pgx-records:

12.26 Validate selected synthetic PGx records
---------------------------------------------

The validation suite contains controlled records used to test the local pharmacogenomic branch.

The following command locates selected project PGx variants without assuming their patient filenames:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF_DIR="validation/universal_pipeline_testing/inputs/vcfs"
   TARGET_IDS=(
   rs1142345
   rs3892097
   rs3918290
   )
   if [[ ! -d "$VCF_DIR" ]]; then
   echo "ERROR: Validation VCF directory is missing:"
   echo "$VCF_DIR"
   exit 1
   fi
   for target_id in "${TARGET_IDS[@]}"; do
   echo
   echo "=== $target_id ==="
   MATCH_FOUND=0
   while IFS= read -r -d '' vcf; do
   matches="$(
   bcftools query \
   --format '%CHROM\t%POS\t%ID\t%REF\t%ALT[\t%GT]\n' \
   "$vcf" |
   awk \
   -F '\t' \
   -v id="$target_id" \
   '$3 == id'
   )"
   if [[ -n "$matches" ]]; then
   echo "File: $vcf"
   printf '%s\n' "$matches"
   MATCH_FOUND=1
   fi
   done < <(
   find "$VCF_DIR" \
   -maxdepth 1 \
   -type f \
   \( -name '*.vcf' -o -name '*.vcf.gz' \) \
   -print0 |
   sort -z
   )
   if (( MATCH_FOUND == 0 )); then
   echo "Not found in validation VCFs."
   fi
   done

This command confirms the genomic records only. The expected project diplotype and phenotype must be verified from the local reference and final PGx output.

.. _12-27-inspect-local-reference-entries-for-selected-rsids:

12.27 Inspect local reference entries for selected rsIDs
--------------------------------------------------------

The following command locates records without assuming the exact rsID column spelling:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PGX_REFERENCE="resources/clinpgx/local_curated_pgx_reference.csv"
   python3 - "$PGX_REFERENCE" <<'PY'
   from __future__ import annotations
   import csv
   import re
   import sys
   from pathlib import Path
   path = Path(sys.argv[1])
   targets = {
   "rs1142345",
   "rs3892097",
   "rs3918290",
   }
   def normalise(value: str) -> str:
   value = value.strip().lower()
   value = re.sub(r"[^a-z0-9]+", "_", value)
   return value.strip("_")
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.DictReader(handle)
   if not reader.fieldnames:
   raise SystemExit("ERROR: Header missing.")
   rsid_column = None
   for column in reader.fieldnames:
   if normalise(column) in {
   "rsid",
   "rs_id",
   "variant_id",
   }:
   rsid_column = column
   break
   if rsid_column is None:
   raise SystemExit(
   "ERROR: Could not identify the rsID column."
   )
   matches = []
   for row in reader:
   value = row.get(rsid_column, "").strip()
   if value in targets:
   matches.append(row)
   if not matches:
   raise SystemExit(
   "ERROR: None of the selected validation rsIDs "
   "were found in the local reference."
   )
   print("\t".join(reader.fieldnames))
   for row in matches:
   print(
   "\t".join(
   row.get(column, "")
   for column in reader.fieldnames
   )
   )
   print()
   print(f"PASS: Found {len(matches)} selected record(s).")
   PY

.. _12-28-validate-disabled-stage-behaviour:

12.28 Validate disabled-stage behaviour
---------------------------------------

The disabled-output script should also pass syntax validation:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/05c_write_disabled_local_pgx.py"
   if [[ ! -s "$SCRIPT" ]]; then
   echo "ERROR: Disabled-PGx output script is missing."
   exit 1
   fi
   python -m py_compile "$SCRIPT"
   echo "PASS: Disabled-stage PGx script passed syntax validation."

Inspect its interface:

.. code:: bash

   if python "$SCRIPT" --help \
   > /tmp/disabled_pgx_help.txt \
   2>&1
   then
   cat /tmp/disabled_pgx_help.txt
   else
   echo "INFO: No standard --help interface was returned."
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$SCRIPT" \
   || true
   fi
   rm -f /tmp/disabled_pgx_help.txt

This stage should be invoked by the launcher rather than guessed manually.

.. _12-29-pharmacogenomic-validation-outcomes:

12.29 Pharmacogenomic validation outcomes
-----------------------------------------

The final project audit included controlled pharmacogenomic results.

Examples include:

+---------------------+--------------+---------------------+------------------------------------+
| **Validation case** | **PGx gene** | **Project variant** | **Project interpretation**         |
+=====================+==============+=====================+====================================+
| Patient 10          | TPMT         | rs1142345           | \*1/\*3C, intermediate metaboliser |
+---------------------+--------------+---------------------+------------------------------------+
| Patient 11          | CYP2D6       | rs3892097           | \*1/\*4, intermediate metaboliser  |
+---------------------+--------------+---------------------+------------------------------------+
| Patient 12          | DPYD         | rs3918290           | \*1/\*2A, intermediate metaboliser |
+---------------------+--------------+---------------------+------------------------------------+

These results validate:

-  exact allele matching;

-  genotype retention;

-  local star-allele mapping;

-  phenotype output;

-  case-level PGx reporting.

They do not establish that the local reference can resolve every possible allele in these genes.

.. _12-30-rare-disease-gene-versus-pharmacogene:

12.30 Rare-disease gene versus pharmacogene
-------------------------------------------

A gene can appear in the rare-disease analysis without producing a local ClinPGx result.

For example, a gene may:

-  cause an inherited disorder;

-  also have drug-related evidence;

-  lack the exact PGx allele in the local reference;

-  require a different type of pharmacogenomic interpretation.

Therefore:

Gene has a pharmacogenomic guideline

does not mean:

Every variant in the gene is pharmacogenomically actionable

The patient’s exact allele and genotype must be evaluated.

.. _12-31-reference-and-guideline-updates:

12.31 Reference and guideline updates
-------------------------------------

Pharmacogenomic knowledge changes over time.

An update may modify:

-  

   .. container::

      Star-allele definitions

-  

   .. container::

      Allele function

-  

   .. container::

      Diplotype-to-phenotype translation

-  

   .. container::

      Drug recommendations

-  

   .. container::

      Evidence levels

-  

   .. container::

      Gene–drug associations

-  

   .. container::

      Variant coordinates

-  

   .. container::

      Preferred terminology

Before updating the local reference:

1.  Preserve the existing file.

2.  Record its checksum.

3.  document the source of every new record.

4.  confirm GRCh38 coordinates;

5.  confirm forward-strand REF and ALT alleles;

6.  validate the CSV structure;

7.  rerun the allele-aware unit test;

8.  rerun Patients 01–12;

9.  compare final outputs;

10. create a new resource checksum.

.. _12-32-safely-update-the-local-reference:

12.32 Safely update the local reference
---------------------------------------

Never edit the active reference without preserving its previous version.

Create a dated backup:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PGX_DIR="resources/clinpgx"
   PGX_FILE="$PGX_DIR/local_curated_pgx_reference.csv"
   TIMESTAMP="$(
   date -u '+%Y%m%dT%H%M%SZ'
   )"
   BACKUP_DIR="$PGX_DIR/archive/$TIMESTAMP"
   if [[ ! -s "$PGX_FILE" ]]; then
   echo "ERROR: Active ClinPGx reference is missing."
   exit 1
   fi
   mkdir -p "$BACKUP_DIR"
   cp \
   --preserve=mode,timestamps \
   "$PGX_FILE" \
   "$BACKUP_DIR/"
   sha256sum \
   "$BACKUP_DIR/local_curated_pgx_reference.csv" \
   > "$BACKUP_DIR/local_curated_pgx_reference.sha256"
   echo "Backup created:"
   echo "$BACKUP_DIR"

After editing the active file, validate it and generate a new checksum:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PGX_FILE="resources/clinpgx/local_curated_pgx_reference.csv"
   PGX_HASH="resources/clinpgx/local_curated_pgx_reference.sha256"
   NEW_HASH="$(
   sha256sum "$PGX_FILE" |
   awk '{print $1}'
   )"
   printf '%s %s\n' \
   "$NEW_HASH" \
   "$PGX_FILE" \
   > "$PGX_HASH"
   cat "$PGX_HASH"

The complete regression suite must pass before the updated reference is accepted.

.. _12-33-clinpgx-source-validation:

12.33 ClinPGx source validation
-------------------------------

Compile all ClinPGx-related project scripts:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPTS=(
   pipeline/case_workflow/05_add_clinpgx_matches.py
   pipeline/case_workflow/05b_add_local_pgx_reference.py
   pipeline/case_workflow/05c_write_disabled_local_pgx.py
   pipeline/case_workflow/11c_add_cnv_clinpgx.py
   pipeline/setup_resources/02_test_clinpgx_api.py
   pipeline/tests/04_test_allele_aware_local_pgx.py
   )
   FAILURES=0
   for script in "${SCRIPTS[@]}"; do
   if [[ ! -s "$script" ]]; then
   echo "FAIL: Missing script: $script"
   FAILURES=$((FAILURES + 1))
   continue
   fi
   python -m py_compile "$script"
   echo "PASS: $script"
   done
   if (( FAILURES > 0 )); then
   echo
   echo "ERROR: $FAILURES ClinPGx script(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: All ClinPGx Python files passed syntax validation."

.. _12-34-complete-local-clinpgx-readiness-check:

12.34 Complete local ClinPGx readiness check
--------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   PGX_REFERENCE="resources/clinpgx/local_curated_pgx_reference.csv"
   PGX_SCHEMA="resources/clinpgx/LOCAL_REFERENCE_SCHEMA.txt"
   PGX_HASH="resources/clinpgx/local_curated_pgx_reference.sha256"
   MATCH_SCRIPT="pipeline/case_workflow/05b_add_local_pgx_reference.py"
   TEST_SCRIPT="pipeline/tests/04_test_allele_aware_local_pgx.py"
   REQUIRED_FILES=(
   "$PGX_REFERENCE"
   "$PGX_SCHEMA"
   "$PGX_HASH"
   "$MATCH_SCRIPT"
   "$TEST_SCRIPT"
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
   echo "ERROR: $FAILURES ClinPGx component(s) are missing."
   exit 1
   fi
   EXPECTED_SHA256="$(
   awk 'NR == 1 {print $1}' \
   "$PGX_HASH"
   )"
   if [[ ! "$EXPECTED_SHA256" =~ ^[0-9a-fA-F]{64}$ ]]; then
   echo "ERROR: Invalid ClinPGx checksum."
   exit 1
   fi
   printf '%s %s\n' \
   "$EXPECTED_SHA256" \
   "$PGX_REFERENCE" |
   sha256sum --check -
   python -m py_compile "$MATCH_SCRIPT"
   python -m py_compile "$TEST_SCRIPT"
   python "$TEST_SCRIPT"
   echo
   echo "PASS: Local allele-aware ClinPGx workflow is ready."

This readiness check does not require the online API.

.. _12-35-record-the-clinpgx-resource-manifest:

12.35 Record the ClinPGx resource manifest
------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   mkdir -p results/environment
   MANIFEST="results/environment/clinpgx_resource_manifest.tsv"
   PGX_REFERENCE="resources/clinpgx/local_curated_pgx_reference.csv"
   PGX_SCHEMA="resources/clinpgx/LOCAL_REFERENCE_SCHEMA.txt"
   {
   echo -e "field\tvalue"
   echo -e "generated_utc\t$(
   date -u '+%Y-%m-%dT%H:%M:%SZ'
   )"
   echo -e "genome_build\tGRCh38"
   echo -e "chromosome_convention\tchr-prefixed"
   echo -e "allele_orientation\tpositive genomic strand"
   echo -e "reference_file\t$PGX_REFERENCE"
   echo -e "reference_sha256\t$(
   sha256sum "$PGX_REFERENCE" |
   awk '{print $1}'
   )"
   echo -e "reference_size_bytes\t$(
   stat -c '%s' "$PGX_REFERENCE"
   )"
   echo -e "schema_file\t$PGX_SCHEMA"
   echo -e "matching_script_sha256\t$(
   sha256sum \
   pipeline/case_workflow/05b_add_local_pgx_reference.py |
   awk '{print $1}'
   )"
   echo -e "test_script_sha256\t$(
   sha256sum \
   pipeline/tests/04_test_allele_aware_local_pgx.py |
   awk '{print $1}'
   )"
   echo -e "api_host\thttps://api.clinpgx.org"
   echo -e "pharmcat_enabled\tno"
   } > "$MANIFEST"
   column \
   --separator $'\t' \
   --table \
   "$MANIFEST"

The manifest records the deterministic local PGx environment used by the project.

.. _12-36-common-pharmacogenomic-failures:

12.36 Common pharmacogenomic failures
-------------------------------------

+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| **Failure**                                       | **Likely cause**                        | **Required response**                          |
+===================================================+=========================================+================================================+
| rsID matches but allele differs                   | rsID-only matching                      | Reject the exact match                         |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Correct locus but wrong genome build              | Coordinate incompatibility              | Confirm GRCh38                                 |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Alleles appear complementary                      | Strand-orientation difference           | Compare genomic positive-strand alleles        |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Patient genotype is 0/0                           | Alternate allele not carried            | Do not assign the PGx allele                   |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Genotype is missing                               | Insufficient sample information         | Report not assessed                            |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Variant absent from VCF                           | Variants-only input                     | Do not assume reference genotype               |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| One marker used for a complex star allele         | Incomplete haplotype resolution         | Report limited project assignment              |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| CYP2D6 SNV used without copy number               | Structural allele not assessed          | Add an explicit limitation                     |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Duplicate PGx reference keys                      | Multiple drugs or accidental duplicates | Include drug/source in key or correct file     |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| API test fails                                    | Network or endpoint issue               | Continue with validated local reference        |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| API returns HTTP 429                              | Rate limit exceeded                     | Reduce requests to no more than two per second |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Old API hostname used                             | Retired PharmGKB endpoint               | Replace with ClinPGx hostname                  |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Live API changes a result                         | Unpinned external data                  | Cache and checksum the response                |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Drug association treated as prescription          | Overinterpretation                      | Require guideline and professional review      |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Gene overlap interpreted as exact CNV star allele | Insufficient structural resolution      | Report potential PGx overlap only              |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| Local reference checksum fails                    | Unexpected file change                  | Stop and investigate                           |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| PGx result increases rare-disease score           | Evidence categories mixed               | Keep PGx and disease scores separate           |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+
| No result file produced                           | Stage skipped or crashed                | Write an explicit disabled or failure output   |
+---------------------------------------------------+-----------------------------------------+------------------------------------------------+

.. _12-37-pharmacogenomic-interpretation-checklist:

12.37 Pharmacogenomic interpretation checklist
----------------------------------------------

A PGx result should be accepted only when:

✓ The genome build is GRCh38

✓ Chromosome naming is harmonised

✓ Alleles use the positive genomic strand

✓ The patient variant is normalised

✓ Chromosome and position match

✓ REF and ALT match exactly

✓ The genotype carries the alternate allele

✓ The gene is consistent with the reference record

✓ The rsID supports rather than replaces allele matching

✓ The star-allele assignment is represented in the local reference

✓ Complex structural or multi-variant limitations are documented

✓ The phenotype terminology is gene appropriate

✓ The associated drug is retained

✓ The evidence source is recorded

✓ The local-reference checksum is valid

✓ Missing loci are not interpreted as reference genotypes

✓ The PGx result remains separate from rare-disease pathogenicity

✓ No treatment change is issued automatically

.. _12-38-pharmacogenomic-stage-completion-criteria:

12.38 Pharmacogenomic stage completion criteria
-----------------------------------------------

The ClinPGx stage is complete when:

✓ The local ClinPGx reference is present

✓ Its schema is documented

✓ Its checksum passes

✓ All CSV rows have consistent structure

✓ Exact genomic allele keys can be identified

✓ Allele-aware matching is used

✓ rsID-only false matches are prevented

✓ Genotypes are evaluated before assigning a carried allele

✓ Star alleles are assigned only when curated

✓ Complex haplotypes and CNVs remain explicitly limited

✓ The disabled stage produces an explicit result

✓ API access uses api.clinpgx.org

✓ API responses are cached where used

✓ The API request rate respects the published limit

✓ The API is supplementary rather than required

✓ The allele-aware regression test passes

✓ Validation PGx records produce the expected project outputs

✓ PGx evidence remains separate from rare-disease scoring

✓ Results include a professional-review disclaimer

✓ PharmCAT remains outside the current automated workflow

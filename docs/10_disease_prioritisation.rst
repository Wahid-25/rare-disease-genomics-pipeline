.. _10-gene-disease-mapping-hpo-phenotype-prioritisation-and-disease-identity-resolu:

10. Gene–Disease Mapping, HPO Phenotype Prioritisation and Disease Identity Resolution
======================================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


After functional and clinical annotation, the pipeline must determine whether the affected gene is associated with a recognised disorder and whether that disorder is compatible with the patient’s recorded phenotype and inheritance pattern.

The workflow combines:

Annotated variant

│

▼

Gene symbol and transcript extraction

│

▼

Gene2Phenotype gene–disease mapping

│

▼

Disease model and allelic requirement

│

▼

Patient HPO comparison

│

▼

Direct and semantic phenotype evidence

│

▼

MONDO identifier and synonym harmonisation

│

▼

Resolved disease identity

│

▼

Evidence supplied to inheritance and ranking stages

The principal project scripts are:

-  

   .. container::

      pipeline/case_workflow/04_map_genes_to_diseases.py

-  

   .. container::

      pipeline/case_workflow/04b_expand_hpo_disease_candidates.py

-  

   .. container::

      pipeline/case_workflow/10_add_phenotype_scores.py

-  

   .. container::

      pipeline/case_workflow/10a_add_semantic_phenotype_evidence.py

-  

   .. container::

      pipeline/case_workflow/10b_resolve_disease_identities.py

The complete source files should be linked from GitHub rather than reproduced fully in the report.

.. _10-1-purpose-of-gene-disease-mapping:

10.1 Purpose of gene–disease mapping
------------------------------------

Functional annotation identifies which genes and transcripts may be affected by a variant. However, a damaging consequence is not sufficient to establish disease relevance.

The pipeline must also determine:

-  whether the gene has an established disease relationship;

-  which disorder is associated with that gene;

-  whether the relationship has sufficient evidence;

-  whether the expected molecular mechanism matches the variant;

-  whether one or two altered alleles are required;

-  whether the inheritance model matches the genotype;

-  whether the patient’s HPO terms resemble the disease phenotype.

A gene may be associated with several disorders through different:

-  

   .. container::

      Inheritance patterns

-  

   .. container::

      Molecular mechanisms

-  

   .. container::

      Allelic requirements

-  

   .. container::

      Variant consequences

-  

   .. container::

      Disease phenotypes

-  

   .. container::

      Confidence levels

Therefore, the pipeline maps a variant to a specific **gene–disease model**, not merely to a gene name.

.. _10-2-gene2phenotype:

10.2 Gene2Phenotype
-------------------

.. _10-2-1-purpose:

10.2.1 Purpose
~~~~~~~~~~~~~~

Gene2Phenotype, abbreviated G2P, provides curated gene–disease models with information such as:

-  gene;

-  disease;

-  allelic requirement;

-  inheritance mechanism;

-  variant consequence;

-  molecular mechanism;

-  evidence or confidence level;

-  disease panel.

G2P describes each relationship as a locus–genotype–mechanism–disease–evidence model. The resource is designed as an inclusion list for filtering and interpreting genome-wide diagnostic data, and the same gene can occur in several entries when different mechanisms cause different disorders. (`EBI <https://www.ebi.ac.uk/gene2phenotype/download>`__)

.. _10-2-2-g2p-files-used-by-the-project:

10.2.2 G2P files used by the project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The project separates official and validation resources:

resources/gene_disease/g2p/

├── AllG2P.official.csv

├── AllG2P.local_validation.csv

├── AllG2P.validation.csv

├── AllG2P.metadata.tsv

├── AllG2P.validation.metadata.tsv

├── AllG2P.combined.metadata.tsv

├── G2P_RESOURCE_ISOLATION.txt

└── RESOURCE_MODES.txt

**AllG2P.official.csv**

Contains the downloaded official G2P relationships.

It is used in:

production mode

**AllG2P.local_validation.csv**

Contains controlled relationships introduced only for synthetic testing.

It must never be treated as an official resource.

**AllG2P.validation.csv**

Combines the official resource with controlled local validation entries.

It is used only in:

validation mode

The active resource is prepared by:

`pipeline/case_workflow/00b_refresh_combined_g2p.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/00b_refresh_combined_g2p.py>`__

.. _10-3-verify-the-g2p-resource-files:

10.3 Verify the G2P resource files
----------------------------------

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   G2P_DIR="resources/gene_disease/g2p"
   REQUIRED_FILES=(
   "$G2P_DIR/AllG2P.official.csv"
   "$G2P_DIR/AllG2P.local_validation.csv"
   "$G2P_DIR/AllG2P.validation.csv"
   "$G2P_DIR/G2P_RESOURCE_ISOLATION.txt"
   "$G2P_DIR/RESOURCE_MODES.txt"
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
   echo "ERROR: $FAILURES G2P resource file(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: Required G2P resources are present."

.. _10-3-1-inspect-the-g2p-files-safely:

10.3.1 Inspect the G2P files safely
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following command detects the delimiter, prints the column names and counts records without modifying the files:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   python3 - <<'PY'
   from __future__ import annotations
   import csv
   from pathlib import Path
   files = [
   Path("resources/gene_disease/g2p/AllG2P.official.csv"),
   Path("resources/gene_disease/g2p/AllG2P.local_validation.csv"),
   Path("resources/gene_disease/g2p/AllG2P.validation.csv"),
   ]
   for path in files:
   if not path.is_file() or path.stat().st_size == 0:
   raise SystemExit(f"ERROR: Missing or empty file: {path}")
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   sample = handle.read(65536)
   handle.seek(0)
   try:
   dialect = csv.Sniffer().sniff(
   sample,
   delimiters=",\t;",
   )
   except csv.Error:
   dialect = csv.excel
   reader = csv.reader(handle, dialect)
   header = next(reader, None)
   if not header:
   raise SystemExit(f"ERROR: Header missing: {path}")
   record_count = sum(
   1
   for row in reader
   if row and any(value.strip() for value in row)
   )
   print(f"\nFile: {path}")
   print(f"Delimiter: {dialect.delimiter!r}")
   print(f"Records: {record_count}")
   print("Columns:")
   for index, column in enumerate(header, start=1):
   print(f" {index:02d}. {column}")
   print("\nPASS: G2P files were parsed successfully.")
   PY

This command does not assume a particular G2P column order. The current downloaded header and the project mapping script remain authoritative.

.. _10-3-2-record-g2p-checksums:

10.3.2 Record G2P checksums
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   G2P_DIR="resources/gene_disease/g2p"
   sha256sum \
   "$G2P_DIR/AllG2P.official.csv" \
   "$G2P_DIR/AllG2P.local_validation.csv" \
   "$G2P_DIR/AllG2P.validation.csv" \
   > "$G2P_DIR/g2p_active_resources.sha256"
   sha256sum \
   --check \
   "$G2P_DIR/g2p_active_resources.sha256"

These checksums should be included in the case reproducibility manifest.

.. _10-4-gene-disease-mapping-stage:

10.4 Gene–disease mapping stage
-------------------------------

The mapping script is:

`pipeline/case_workflow/04_map_genes_to_diseases.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/04_map_genes_to_diseases.py>`__

It receives gene information extracted from VEP or SnpEff and searches the active G2P file for corresponding gene–disease models.

The mapping stage can add information such as:

-  

   .. container::

      Gene symbol

-  

   .. container::

      Disease name

-  

   .. container::

      Disease identifier

-  

   .. container::

      G2P record identifier

-  

   .. container::

      Confidence category

-  

   .. container::

      Allelic requirement

-  

   .. container::

      Molecular mechanism

-  

   .. container::

      Expected variant consequence

-  

   .. container::

      Disease panel

-  

   .. container::

      Resource mode

-  

   .. container::

      Mapping status

A gene may produce more than one result because the same gene can cause different diseases through different mechanisms.

.. _10-4-1-inspect-the-script-interface:

10.4.1 Inspect the script interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Do not guess its command-line arguments. Use the interface supplied by the committed script:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/04_map_genes_to_diseases.py"
   python -m py_compile "$SCRIPT"
   if python "$SCRIPT" --help \
   > /tmp/map_genes_to_diseases.help.txt \
   2>&1
   then
   cat /tmp/map_genes_to_diseases.help.txt
   else
   echo "INFO: The script does not expose a standard --help interface."
   echo "Command-line argument definitions found in the source:"
   grep -nE \
   'ArgumentParser|add_argument' \
   "$SCRIPT" \
   || true
   fi

The complete case pipeline should call this script automatically. A manual command should be constructed only from the actual --help output or launcher source.

.. _10-5-allelic-requirement:

10.5 Allelic requirement
------------------------

Allelic requirement describes the genotype configuration normally required for the disease model.

Common G2P categories include:

+-----------------------------+--------------------------------------------------------+
| **G2P allelic requirement** | **General interpretation**                             |
+=============================+========================================================+
| monoallelic_autosomal       | One disease-associated allele in an autosomal gene     |
+-----------------------------+--------------------------------------------------------+
| biallelic_autosomal         | Two disease-associated alleles in an autosomal gene    |
+-----------------------------+--------------------------------------------------------+
| monoallelic_X_hemizygous    | One altered allele in an X-linked hemizygous context   |
+-----------------------------+--------------------------------------------------------+
| monoallelic_X_heterozygous  | One altered allele in an X-linked heterozygous context |
+-----------------------------+--------------------------------------------------------+
| biallelic_X                 | Two affected X-chromosome alleles                      |
+-----------------------------+--------------------------------------------------------+
| Mitochondrial model         | Variant involving the mitochondrial genome             |
+-----------------------------+--------------------------------------------------------+

G2P records explicitly describe autosomal monoallelic, autosomal biallelic and X-linked hemizygous disease models. (`EBI <https://www.ebi.ac.uk/gene2phenotype/lgd/G2P00351>`__)

The allelic requirement does not by itself establish that a patient’s genotype satisfies the disease model. It must later be compared with:

-  observed genotype;

-  zygosity;

-  chromosome;

-  sex and ploidy;

-  phase information;

-  number of qualifying variants;

-  inheritance pattern.

.. _10-6-molecular-mechanism-and-variant-consequence:

10.6 Molecular mechanism and variant consequence
------------------------------------------------

Different disease models may require different molecular effects.

Examples include:

-  

   .. container::

      Loss of function

-  

   .. container::

      Gain of function

-  

   .. container::

      Dominant negative

-  

   .. container::

      Altered gene-product structure

-  

   .. container::

      Restricted mutation set

-  

   .. container::

      Absent gene product

-  

   .. container::

      Increased dosage

-  

   .. container::

      Decreased dosage

A predicted loss-of-function variant should receive stronger mechanistic support when the disease is known to result from loss of function.

It should not automatically receive the same support when the disease is caused only by:

-  

   .. container::

      gain-of-function variants

-  

   .. container::

      specific missense variants

-  

   .. container::

      dominant-negative variants

-  

   .. container::

      restricted mutational regions

For example, G2P can distinguish a disease model involving a restricted mutation set and dominant-negative mechanism from a general monoallelic loss-of-function model. (`EBI <https://www.ebi.ac.uk/gene2phenotype/lgd/G2P01300>`__)

The pipeline should therefore preserve both:

-  

   .. container::

      Predicted variant consequence

-  

   .. container::

      Expected disease mechanism

and evaluate their compatibility later in the scoring stage.

.. _10-7-g2p-confidence:

10.7 G2P confidence
-------------------

A gene–disease relationship may carry a confidence category such as:

-  

   .. container::

      definitive

-  

   .. container::

      strong

-  

   .. container::

      moderate

-  

   .. container::

      limited

-  

   .. container::

      disputed

The exact categories available must be read from the installed G2P resource rather than hard-coded from memory.

Inspect the relevant values by first locating confidence-like columns:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   python3 - <<'PY'
   from __future__ import annotations
   import csv
   from pathlib import Path
   path = Path(
   "resources/gene_disease/g2p/AllG2P.official.csv"
   )
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.DictReader(handle)
   if not reader.fieldnames:
   raise SystemExit("ERROR: G2P header is missing.")
   candidate_columns = [
   name
   for name in reader.fieldnames
   if any(
   keyword in name.lower()
   for keyword in (
   "confidence",
   "evidence",
   "category",
   )
   )
   ]
   print("Possible evidence/confidence columns:")
   for name in candidate_columns:
   print(f" {name}")
   if not candidate_columns:
   print(" No obvious column was detected.")
   print(" Inspect the complete header before mapping.")
   print("PASS: G2P header inspection completed.")
   PY

Confidence contributes to prioritisation but should not replace variant-level evidence.

.. _10-8-hpo-phenotype-resources:

10.8 HPO phenotype resources
----------------------------

The Human Phenotype Ontology provides:

-  

   .. container::

      hp.obo

-  

   .. container::

      phenotype.hpoa

-  

   .. container::

      genes_to_phenotype.txt

-  

   .. container::

      phenotype_to_genes.txt

-  

   .. container::

      genes_to_disease.txt

The HPO disease annotation file connects diseases with characteristic phenotype terms and may include information about frequency, age of onset, sex specificity, modifiers and features explicitly marked as absent.

The summary files provide different views:

+------------------------+---------------------------------------------------------+
| **HPO file**           | **Main purpose**                                        |
+========================+=========================================================+
| hp.obo                 | Ontology terms and parent–child relationships           |
+------------------------+---------------------------------------------------------+
| phenotype.hpoa         | Disease-to-phenotype annotations                        |
+------------------------+---------------------------------------------------------+
| genes_to_phenotype.txt | Gene-to-specific phenotype associations                 |
+------------------------+---------------------------------------------------------+
| phenotype_to_genes.txt | Phenotype-to-gene associations including ancestor terms |
+------------------------+---------------------------------------------------------+
| genes_to_disease.txt   | Gene-to-disease relationships                           |
+------------------------+---------------------------------------------------------+

The HPO documentation notes that genes_to_phenotype.txt contains the most specific annotated terms, while phenotype_to_genes.txt additionally includes ancestor terms from the ontology hierarchy.

.. _10-9-verify-the-active-hpo-release:

10.9 Verify the active HPO release
----------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   HPO_ROOT="resources/phenotype/hpo"
   HPO_ACTIVE="$HPO_ROOT/current"
   if [[ ! -L "$HPO_ACTIVE" && ! -d "$HPO_ACTIVE" ]]; then
   echo "ERROR: Active HPO path is missing:"
   echo "$HPO_ACTIVE"
   exit 1
   fi
   echo "Active HPO target:"

readlink -f "$HPO_ACTIVE"

.. code:: bash

   REQUIRED_HPO_FILES=(
   "$HPO_ACTIVE/hp.obo"
   "$HPO_ACTIVE/phenotype.hpoa"
   "$HPO_ACTIVE/genes_to_disease.txt"
   "$HPO_ACTIVE/genes_to_phenotype.txt"
   "$HPO_ACTIVE/phenotype_to_genes.txt"
   )
   FAILURES=0
   for path in "${REQUIRED_HPO_FILES[@]}"; do
   if [[ -s "$path" ]]; then
   printf "PASS %s\n" "$path"
   else
   printf "FAIL %s\n" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo "ERROR: $FAILURES HPO resource file(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: Active HPO release is complete."

.. _10-9-1-inspect-the-hpo-release-manifest:

10.9.1 Inspect the HPO release manifest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   HPO_ACTIVE="resources/phenotype/hpo/current"
   if [[ -s "$HPO_ACTIVE/release_manifest.tsv" ]]; then
   column \
   --separator $'\t' \
   --table \
   "$HPO_ACTIVE/release_manifest.tsv"
   else
   echo "WARNING: release_manifest.tsv is not present in the active HPO directory."
   fi

.. _10-9-2-verify-hpo-ontology-identity:

10.9.2 Verify HPO ontology identity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   HPO_OBO="resources/phenotype/hpo/current/hp.obo"
   grep -m 1 '^format-version:' "$HPO_OBO"
   grep -m 1 '^ontology:' "$HPO_OBO"
   grep -m 1 '^data-version:' "$HPO_OBO" || true
   TERM_COUNT="$(
   grep -c '^\[Term\]$' "$HPO_OBO"
   )"
   echo "HPO term blocks: $TERM_COUNT"
   if (( TERM_COUNT == 0 )); then
   echo "ERROR: No HPO terms were detected."
   exit 1
   fi
   echo "PASS: HPO ontology file is readable."

.. _10-10-validate-patient-hpo-terms-against-the-installed-ontology:

10.10 Validate patient HPO terms against the installed ontology
---------------------------------------------------------------

A term may match the syntax HP:0000000 but still be:

-  absent from the installed release;

-  obsolete;

-  replaced by another term;

-  mistyped.

The following command checks a patient HPO file against the active ontology.

Choose the input file:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   HPO_FILE="$(
   find \
   validation/universal_pipeline_testing/inputs/hpo \
   -maxdepth 1 \
   -type f \
   \( -name '*.hpo.txt' -o -name '*.txt' \) \
   | sort \
   | head -n 1
   )"
   if [[ -z "$HPO_FILE" ]]; then
   echo "ERROR: No validation HPO file was found."
   exit 1
   fi
   echo "Testing: $HPO_FILE"

Validate it:

.. code:: bash

   python3 - \
   "$HPO_FILE" \
   resources/phenotype/hpo/current/hp.obo <<'PY'
   from __future__ import annotations
   import re
   import sys
   from pathlib import Path
   input_path = Path(sys.argv[1])
   ontology_path = Path(sys.argv[2])
   if not input_path.is_file():
   raise SystemExit(f"ERROR: HPO input missing: {input_path}")
   if not ontology_path.is_file():
   raise SystemExit(f"ERROR: HPO ontology missing: {ontology_path}")
   term_pattern = re.compile(r"^HP:\d{7}$")
   terms: dict[str, dict[str, object]] = {}
   current_id: str | None = None
   current_name = ""
   current_obsolete = False
   current_replaced_by: list[str] = []
   def save_current() -> None:
   global current_id
   global current_name
   global current_obsolete
   global current_replaced_by
   if current_id:
   terms[current_id] = {
   "name": current_name,
   "obsolete": current_obsolete,
   "replaced_by": tuple(current_replaced_by),
   }
   current_id = None
   current_name = ""
   current_obsolete = False
   current_replaced_by = []
   with ontology_path.open(
   "r",
   encoding="utf-8",
   ) as handle:
   for raw_line in handle:
   line = raw_line.rstrip("\n")
   if line == "[Term]":
   save_current()
   continue
   if line.startswith("[") and line.endswith("]"):
   save_current()
   continue
   if line.startswith("id: HP:"):
   current_id = line.split("id: ", 1)[1].strip()
   elif line.startswith("name: "):
   current_name = line.split("name: ", 1)[1].strip()
   elif line == "is_obsolete: true":
   current_obsolete = True
   elif line.startswith("replaced_by: HP:"):
   current_replaced_by.append(
   line.split("replaced_by: ", 1)[1].strip()
   )
   save_current()
   input_terms: list[tuple[int, str]] = []
   for line_number, raw_line in enumerate(
   input_path.read_text(
   encoding="utf-8-sig"
   ).splitlines(),
   start=1,
   ):
   value = raw_line.strip()
   if not value or value.startswith("#"):
   continue
   input_terms.append((line_number, value))
   if not input_terms:
   raise SystemExit("ERROR: No HPO terms were supplied.")
   failures = 0
   for line_number, term_id in input_terms:
   if not term_pattern.fullmatch(term_id):
   print(
   f"FAIL line {line_number}: "
   f"invalid syntax {term_id!r}"
   )
   failures += 1
   continue
   record = terms.get(term_id)
   if record is None:
   print(
   f"FAIL line {line_number}: "
   f"{term_id} absent from ontology"
   )
   failures += 1
   continue
   if record["obsolete"]:
   replacement_text = ",".join(
   record["replaced_by"]
   ) or "no replacement listed"
   print(
   f"WARN line {line_number}: "
   f"{term_id} is obsolete; "
   f"replacement={replacement_text}"
   )
   continue
   print(
   f"PASS line {line_number}: "
   f"{term_id} — {record['name']}"
   )
   if failures:
   raise SystemExit(
   f"ERROR: {failures} invalid HPO term(s)."
   )
   print(
   f"\nPASS: {len(input_terms)} HPO term(s) "
   "validated against the active ontology."
   )
   PY

Obsolete terms should be reviewed before replacement. An automated replacement should not be made when the ontology provides several alternatives or when the clinical meaning may change.

.. _10-11-patient-hpo-matching:

10.11 Patient HPO matching
--------------------------

The project uses exact case identifiers when selecting an HPO file.

The regression test is:

`pipeline/tests/09_test_exact_hpo_patient_matching.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/tests/09_test_exact_hpo_patient_matching.py>`__

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/09_test_exact_hpo_patient_matching.py
   echo "PASS: Exact HPO patient matching test completed."

This prevents an identifier such as:

patient_01

from matching:

-  

   .. container::

      patient_010

-  

   .. container::

      patient_011

-  

   .. container::

      patient_012

.. _10-12-direct-phenotype-evidence:

10.12 Direct phenotype evidence
-------------------------------

The first phenotype stage is:

`pipeline/case_workflow/10_add_phenotype_scores.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/10_add_phenotype_scores.py>`__

Direct phenotype evidence may consider:

-  exact HPO term overlap;

-  gene-associated HPO terms;

-  disease-associated HPO terms;

-  number of matched terms;

-  total number of patient terms;

-  proportion of terms matched;

-  absence of phenotype information.

A direct match occurs when the same HPO identifier is present in both the patient and disease annotation.

For example:

-  

   .. container::

      Patient: HP:0001250

-  

   .. container::

      Disease: HP:0001250

-  

   .. container::

      Result: Exact HPO match

Direct matching is useful but limited because clinically similar features may be encoded at different levels of the ontology.

.. _10-13-semantic-phenotype-evidence:

10.13 Semantic phenotype evidence
---------------------------------

The semantic stage is:

`pipeline/case_workflow/10a_add_semantic_phenotype_evidence.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/10a_add_semantic_phenotype_evidence.py>`__

Semantic comparison uses relationships in the HPO hierarchy.

For example, a patient may be annotated with a specific term while the disease resource contains a broader parent term. These terms are related even though their identifiers are not identical.

The project’s semantic score may use information derived from:

-  

   .. container::

      Parent–child relationships

-  

   .. container::

      Shared ancestors

-  

   .. container::

      Term specificity

-  

   .. container::

      Disease annotations

-  

   .. container::

      Patient HPO terms

-  

   .. container::

      Locally generated semantic cache

The exact formula must be taken from the committed source code. It should not be reconstructed differently in the Word report.

.. _10-13-1-locate-the-semantic-cache:

10.13.1 Locate the semantic cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The exact cache filename should be determined from the installed resource and project script:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   echo "=== Candidate semantic-cache files ==="
   find \
   resources/phenotype/hpo \
   -type f \
   \( \
   -iname '*semantic*' \
   -o -iname '*.sqlite' \
   -o -iname '*.db' \
   \) \
   -print |

sort

.. code:: bash

   echo
   echo "=== Semantic-cache paths referenced in scripts ==="
   grep -RInE \
   'semantic|sqlite|phenotype\.hpoa|hp\.obo' \
   pipeline/resource_setup/build_hpo_semantic_cache.py \
   pipeline/case_workflow/10a_add_semantic_phenotype_evidence.py \
   || true

Do not hard-code a different cache filename unless the pipeline source is also updated and revalidated.

.. _10-13-2-inspect-the-semantic-cache-builder:

10.13.2 Inspect the semantic-cache builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/resource_setup/build_hpo_semantic_cache.py"
   python -m py_compile "$SCRIPT"
   if python "$SCRIPT" --help \
   > /tmp/build_hpo_semantic_cache.help.txt \
   2>&1
   then
   cat /tmp/build_hpo_semantic_cache.help.txt
   else
   echo "INFO: No standard --help output was returned."
   grep -nE \
   'ArgumentParser|add_argument' \
   "$SCRIPT" \
   || true
   fi

Use only the arguments displayed by the committed script.

.. _10-14-hpo-annotation-aspects:

10.14 HPO annotation aspects
----------------------------

The phenotype.hpoa file contains an aspect field that distinguishes:

-  

   .. container::

      P Phenotypic abnormality

-  

   .. container::

      C Clinical course

-  

   .. container::

      I Mode of inheritance

-  

   .. container::

      M Clinical modifier

-  

   .. container::

      H Past medical history

For phenotype-similarity calculations, terms belonging to the phenotypic-abnormality branch are generally the primary evidence, while inheritance is evaluated separately by the project’s inheritance module.

This separation prevents a shared inheritance term from being counted as though it were a shared clinical feature.

.. _10-15-negated-phenotype-terms:

10.15 Negated phenotype terms
-----------------------------

HPO disease annotations may include a NOT qualifier to indicate that a feature is not characteristic of a disorder. HPO also supports frequency values that can represent complete absence, such as zero affected individuals within an observed group.

The project should distinguish between:

-  

   .. container::

      Present phenotype

-  

   .. container::

      Absent phenotype

-  

   .. container::

      Unknown or unassessed phenotype

Absence must not be inferred merely because a feature was not written in the patient’s HPO file.

A missing term means:

not recorded

not necessarily:

clinically absent

.. _10-16-hpo-candidate-expansion:

10.16 HPO candidate expansion
-----------------------------

The script:

`pipeline/case_workflow/04b_expand_hpo_disease_candidates.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/04b_expand_hpo_disease_candidates.py>`__

uses patient phenotype terms to identify additional candidate genes or diseases supported by HPO resources.

This allows the workflow to recognise candidates that may have:

-  weaker existing ClinVar evidence;

-  no direct ClinVar disease label;

-  strong phenotype compatibility;

-  a known HPO gene relationship;

-  a disease relationship represented differently across databases.

Phenotype expansion must remain supporting evidence. It must not create a pathogenic classification for a variant that lacks sufficient variant-level evidence.

.. _10-16-1-inspect-the-candidate-expansion-interface:

10.16.1 Inspect the candidate-expansion interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/04b_expand_hpo_disease_candidates.py"
   python -m py_compile "$SCRIPT"
   if python "$SCRIPT" --help \
   > /tmp/expand_hpo_candidates.help.txt \
   2>&1
   then
   cat /tmp/expand_hpo_candidates.help.txt
   else
   echo "INFO: No standard --help output was returned."
   grep -nE \
   'ArgumentParser|add_argument' \
   "$SCRIPT" \
   || true
   fi

.. _10-17-mondo-disease-identity-harmonisation:

10.17 MONDO disease identity harmonisation
------------------------------------------

Different resources may use different identifiers or names for the same disease.

Examples of identifier systems include:

-  

   .. container::

      MONDO

-  

   .. container::

      OMIM or MIM

-  

   .. container::

      ORPHA

-  

   .. container::

      DOID

-  

   .. container::

      ClinVar condition labels

-  

   .. container::

      G2P identifiers

MONDO integrates terminology from several disease resources and provides mappings, synonyms and a unified identifier system. The OBO release uses cross-references as links to external disease identifiers, while the OWL and JSON editions can carry richer equivalence information.

The project uses MONDO to support:

-  disease identifier normalisation;

-  synonym recognition;

-  grouping equivalent disease labels;

-  comparison of G2P and ClinVar disease terminology;

-  reduction of duplicate disease candidates.

.. _10-18-verify-the-mondo-resource:

10.18 Verify the MONDO resource
-------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MONDO_ROOT="resources/disease_ontology/mondo"
   MONDO_ACTIVE="$MONDO_ROOT/current"
   MONDO_OBO="$MONDO_ACTIVE/mondo.obo"
   if [[ ! -L "$MONDO_ACTIVE" && ! -d "$MONDO_ACTIVE" ]]; then
   echo "ERROR: Active MONDO path is missing."
   exit 1
   fi
   if [[ ! -s "$MONDO_OBO" ]]; then
   echo "ERROR: MONDO OBO file is missing:"
   echo "$MONDO_OBO"
   exit 1
   fi
   echo "Active MONDO target:"

readlink -f "$MONDO_ACTIVE"

.. code:: bash

   echo
   grep -m 1 '^format-version:' "$MONDO_OBO"
   grep -m 1 '^ontology:' "$MONDO_OBO"
   grep -m 1 '^data-version:' "$MONDO_OBO" || true
   TERM_COUNT="$(
   grep -c '^\[Term\]$' "$MONDO_OBO"
   )"
   echo
   echo "MONDO term blocks: $TERM_COUNT"
   if (( TERM_COUNT == 0 )); then
   echo "ERROR: No MONDO terms were detected."
   exit 1
   fi
   echo "PASS: MONDO ontology is readable."

.. _10-18-1-inspect-mondo-mappings:

10.18.1 Inspect MONDO mappings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MONDO_OBO="resources/disease_ontology/mondo/current/mondo.obo"
   echo "=== Example MONDO cross-references ==="
   grep '^xref: ' "$MONDO_OBO" |
   head -n 20
   echo
   echo "=== Cross-reference counts by prefix ==="
   grep '^xref: ' "$MONDO_OBO" |
   sed -E 's/^xref: ([^: ]+).*/\1/' |
   sort |
   uniq -c |
   sort -nr |
   head -n 20

Mappings should not be treated as exact equivalence merely because two labels are textually similar. Mondo distinguishes exact, broad, narrow and related synonyms, and its mappings are curated rather than generated solely through name matching.

.. _10-19-build-and-verify-the-mondo-crosswalk:

10.19 Build and verify the MONDO crosswalk
------------------------------------------

The project script is:

`pipeline/resource_setup/build_mondo_crosswalk.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/resource_setup/build_mondo_crosswalk.py>`__

Inspect its arguments:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/resource_setup/build_mondo_crosswalk.py"
   python -m py_compile "$SCRIPT"
   if python "$SCRIPT" --help \
   > /tmp/build_mondo_crosswalk.help.txt \
   2>&1
   then
   cat /tmp/build_mondo_crosswalk.help.txt
   else
   echo "INFO: No standard --help output was returned."
   grep -nE \
   'ArgumentParser|add_argument' \
   "$SCRIPT" \
   || true
   fi

Locate the generated crosswalk:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find \
   resources/disease_ontology/mondo \
   -type f \
   \( \
   -iname '*crosswalk*' \
   -o -iname '*.sqlite' \
   -o -iname '*.db' \
   -o -iname '*.tsv' \
   \) \
   -print |

sort

When the output is an SQLite database, inspect it safely:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MONDO_DB="$(
   find \
   resources/disease_ontology/mondo/current \
   -type f \
   \( -iname '*.sqlite' -o -iname '*.db' \) \
   | sort \
   | head -n 1
   )"
   if [[ -n "$MONDO_DB" ]]; then
   echo "Database: $MONDO_DB"
   sqlite3 "$MONDO_DB" '.tables'
   else
   echo "INFO: No SQLite MONDO crosswalk was found."
   echo "The project may use a TSV or another generated format."
   fi

.. _10-20-disease-identity-resolution:

10.20 Disease identity resolution
---------------------------------

The resolution script is:

`pipeline/case_workflow/10b_resolve_disease_identities.py <https://github.com/Wahid-25/rare-disease-genomics-pipeline/blob/main/pipeline/case_workflow/10b_resolve_disease_identities.py>`__

It brings together disease information from:

-  

   .. container::

      Gene2Phenotype

-  

   .. container::

      ClinVar

-  

   .. container::

      MONDO

-  

   .. container::

      HPO annotations

-  

   .. container::

      Validation metadata, when enabled

The project applies the following conceptual precedence:

1. Use the G2P disease label for the controlled gene–disease model.

2. Retain ClinVar condition names as variant-level clinical evidence.

3. Use MONDO identifiers and synonyms to harmonise terminology.

4. Preserve the original source labels for provenance.

5. Avoid collapsing diseases when equivalence is uncertain.

.. _10-20-1-why-g2p-and-clinvar-labels-may-differ:

10.20.1 Why G2P and ClinVar labels may differ
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

G2P describes a curated gene–disease mechanism.

ClinVar condition labels describe conditions attached to submitted variant classifications.

A ClinVar record may contain:

-  several diseases;

-  a broad phenotype;

-  a phenotypic series;

-  historical terminology;

-  a generic condition;

-  conflicting condition names.

Therefore, the ClinVar disease string should not automatically replace the curated G2P disease model.

ClinVar’s review status reports the level of review supporting an aggregate classification, while the condition name remains part of the variant submission context. (`NCBI <https://www.ncbi.nlm.nih.gov/clinvar/docs/review_status/>`__)

.. _10-20-2-run-the-disease-label-precedence-test:

10.20.2 Run the disease-label precedence test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/10_test_g2p_disease_label_precedence.py
   echo "PASS: G2P disease-label precedence test completed."

.. _10-21-preserve-original-and-resolved-disease-fields:

10.21 Preserve original and resolved disease fields
---------------------------------------------------

The final table should retain separate fields rather than replacing every disease value with one string.

Recommended fields include:

-  

   .. container::

      g2p_disease_name

-  

   .. container::

      g2p_disease_id

-  

   .. container::

      g2p_confidence

-  

   .. container::

      g2p_allelic_requirement

-  

   .. container::

      g2p_molecular_mechanism

-  

   .. container::

      clinvar_condition

-  

   .. container::

      clinvar_significance

-  

   .. container::

      clinvar_review_status

-  

   .. container::

      mondo_id

-  

   .. container::

      mondo_preferred_label

-  

   .. container::

      mondo_mapping_status

-  

   .. container::

      resolved_disease_name

-  

   .. container::

      resolved_disease_id

-  

   .. container::

      disease_resolution_source

This allows reviewers to determine:

-  what each source originally reported;

-  which label was selected;

-  how the disease was harmonised;

-  whether a mapping was exact or uncertain.

.. _10-22-phenotype-score-interpretation:

10.22 Phenotype score interpretation
------------------------------------

The phenotype score is intended to prioritise candidates, not to prove causality.

A high phenotype score may indicate that:

Several patient features match the disease

Specific phenotype terms are shared

Semantically related HPO terms are present

The gene is strongly associated with those features

A low score may occur because:

-  the patient has incomplete phenotyping;

-  the disorder has age-dependent features;

-  the disease annotation is incomplete;

-  the patient has an atypical presentation;

-  broad terms were used instead of specific terms;

-  the wrong HPO release or file was selected.

A candidate should not be excluded only because of a low phenotype score when strong genomic evidence exists.

.. _10-23-missing-phenotype-data:

10.23 Missing phenotype data
----------------------------

When no HPO file is supplied, the pipeline should not assign a false phenotype mismatch.

The appropriate status is:

phenotype_not_available

or an equivalent explicit value.

The score should distinguish:

No phenotype evidence available

from:

Phenotype evidence evaluated but incompatible

These states have different meanings.

.. _10-24-phenotype-evidence-for-cnvs:

10.24 Phenotype evidence for CNVs
---------------------------------

CNVs can affect several genes and therefore require a separate phenotype-preparation stage.

Relevant scripts are:

pipeline/case_workflow/10c_prepare_cnv_semantic_input.py

pipeline/case_workflow/10d_add_cnv_semantic_phenotype_evidence.py

The CNV phenotype branch may evaluate:

-  all genes overlapping the CNV;

-  dosage-sensitive genes;

-  established gene–disease models;

-  disease-associated HPO terms;

-  similarity to patient features;

-  whether deletion or duplication matches the disease mechanism.

A CNV must not receive strong phenotype evidence merely because one overlapping gene has a broad association with one common feature.

.. _10-25-run-all-relevant-regression-tests:

10.25 Run all relevant regression tests
---------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   TESTS=(
   pipeline/tests/03_test_resource_modes.py
   pipeline/tests/07_test_g2p_resource_isolation.py
   pipeline/tests/09_test_exact_hpo_patient_matching.py
   pipeline/tests/10_test_g2p_disease_label_precedence.py
   )
   for test_script in "${TESTS[@]}"; do
   echo
   echo "=== Running $test_script ==="
   python "$test_script"
   echo "PASS: $test_script"
   done
   echo
   echo "PASS: Gene–disease and phenotype regression tests completed."

.. _10-26-validate-the-relevant-python-source-files:

10.26 Validate the relevant Python source files
-----------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPTS=(
   pipeline/case_workflow/04_map_genes_to_diseases.py
   pipeline/case_workflow/04b_expand_hpo_disease_candidates.py
   pipeline/case_workflow/10_add_phenotype_scores.py
   pipeline/case_workflow/10a_add_semantic_phenotype_evidence.py
   pipeline/case_workflow/10b_resolve_disease_identities.py
   pipeline/case_workflow/10c_prepare_cnv_semantic_input.py
   pipeline/case_workflow/10d_add_cnv_semantic_phenotype_evidence.py
   pipeline/resource_setup/build_hpo_semantic_cache.py
   pipeline/resource_setup/build_mondo_crosswalk.py
   )
   for script in "${SCRIPTS[@]}"; do
   if [[ ! -s "$script" ]]; then
   echo "ERROR: Missing source file: $script"
   exit 1
   fi
   python -m py_compile "$script"
   echo "PASS: $script"
   done
   echo
   echo "PASS: Relevant Python source files passed syntax validation."

.. _10-27-complete-resource-readiness-check:

10.27 Complete resource readiness check
---------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail

declare -A REQUIRED_PATHS=(

["G2P official"]="resources/gene_disease/g2p/AllG2P.official.csv"

["G2P local validation"]="resources/gene_disease/g2p/AllG2P.local_validation.csv"

["G2P validation"]="resources/gene_disease/g2p/AllG2P.validation.csv"

["HPO ontology"]="resources/phenotype/hpo/current/hp.obo"

["HPO disease annotations"]="resources/phenotype/hpo/current/phenotype.hpoa"

["HPO gene-to-disease"]="resources/phenotype/hpo/current/genes_to_disease.txt"

["HPO gene-to-phenotype"]="resources/phenotype/hpo/current/genes_to_phenotype.txt"

["HPO phenotype-to-gene"]="resources/phenotype/hpo/current/phenotype_to_genes.txt"

["MONDO ontology"]="resources/disease_ontology/mondo/current/mondo.obo"

.. code:: bash

   )
   FAILURES=0
   for label in "${!REQUIRED_PATHS[@]}"; do
   path="${REQUIRED_PATHS[$label]}"
   if [[ -s "$path" ]]; then
   printf "PASS %-27s %s\n" "$label" "$path"
   else
   printf "FAIL %-27s %s\n" "$label" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   echo
   if (( FAILURES > 0 )); then
   echo "ERROR: $FAILURES required resource(s) are missing."
   exit 1
   fi
   echo "PASS: Gene–disease and phenotype resources are ready."

.. _10-28-common-mapping-and-phenotype-failures:

10.28 Common mapping and phenotype failures
-------------------------------------------

+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| **Failure**                                    | **Likely cause**                               | **Required response**                                 |
+================================================+================================================+=======================================================+
| Gene has no G2P match                          | Gene is absent, new or represented differently | Retain candidate and report no G2P model              |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Several diseases map to one gene               | Multiple mechanisms or phenotypes exist        | Evaluate each gene–disease model separately           |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Wrong G2P file used                            | Production/validation mode confusion           | Check active resource and manifest                    |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Validation disease appears in production       | Resource contamination                         | Stop analysis and run isolation tests                 |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| HPO file not found                             | Incorrect case identifier or filename          | Use exact case matching                               |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| HPO syntax valid but term absent               | Typo, obsolete term or release difference      | Check against active hp.obo                           |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| HPO term is obsolete                           | Ontology update                                | Review replaced_by or alternatives                    |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Direct phenotype score is low                  | Different ontology depth                       | Review semantic evidence                              |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Semantic cache missing                         | Resource builder was not run                   | Build cache using committed script                    |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Disease appears twice                          | Synonyms or identifier mismatch                | Resolve through MONDO                                 |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Unrelated diseases are merged                  | Loose text matching                            | Require controlled identifier mapping                 |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| ClinVar label replaces G2P model               | Incorrect precedence                           | Run disease-label regression test                     |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Inheritance HPO term increases phenotype score | HPO aspects not separated                      | Restrict phenotype similarity appropriately           |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Missing HPO treated as mismatch                | Incorrect null handling                        | Report phenotype evidence unavailable                 |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Broad common feature dominates score           | Poor weighting                                 | Review specificity and scoring implementation         |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| G2P confidence missing                         | Resource schema changed                        | Inspect current header and update parser deliberately |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+
| Resource update changes ranking                | Updated relationships or ontology              | Rerun Patients 01–12 and compare outputs              |
+------------------------------------------------+------------------------------------------------+-------------------------------------------------------+

.. _10-29-output-requirements:

10.29 Output requirements
-------------------------

After this stage, each candidate should contain enough information for inheritance and final scoring.

The output should include, where available:

-  

   .. container::

      Variant identifier

-  

   .. container::

      Gene symbol

-  

   .. container::

      Transcript

Predicted consequence

-  

   .. container::

      G2P disease name

-  

   .. container::

      G2P disease identifier

-  

   .. container::

      G2P confidence

-  

   .. container::

      Allelic requirement

-  

   .. container::

      Molecular mechanism

Expected variant consequence

-  

   .. container::

      Patient HPO term count

-  

   .. container::

      Exact HPO matches

-  

   .. container::

      Semantic phenotype score

Phenotype evidence status

-  

   .. container::

      ClinVar condition

-  

   .. container::

      ClinVar significance

-  

   .. container::

      ClinVar review status

-  

   .. container::

      MONDO identifier

-  

   .. container::

      Resolved disease name

-  

   .. container::

      Disease-resolution source

-  

   .. container::

      Resource mode

Original source labels must remain available for auditing.

.. _10-30-completion-criteria:

10.30 Completion criteria
-------------------------

The gene–disease and phenotype stage is complete when:

✓ The correct G2P resource mode was selected

✓ Official and validation G2P files remained isolated

✓ Gene symbols were mapped to specific disease models

✓ Allelic requirements were retained

✓ Molecular mechanisms were retained

✓ G2P confidence was retained

✓ Patient HPO terms were validated against the active ontology

✓ Obsolete and invalid HPO terms were reported

✓ Patient HPO files were matched using exact identifiers

✓ Direct HPO evidence was calculated

✓ Semantic phenotype evidence was added where resources were available

✓ Missing phenotype data was not treated as a mismatch

✓ HPO inheritance and phenotype aspects were distinguished

✓ MONDO was used to harmonise disease identities

✓ Original G2P and ClinVar labels were preserved

✓ G2P disease-label precedence was tested

✓ CNV phenotype evidence remained separate from small-variant evidence

✓ Resource versions and checksums were recorded

✓ All relevant regression tests passed

The resulting candidates can now proceed to chromosome-aware inheritance analysis, zygosity evaluation and compound-heterozygous aggregation.

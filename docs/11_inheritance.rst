.. _11-inheritance-modelling-sex-and-ploidy-evaluation-and-compound-heterozygous-ana:

11. Inheritance Modelling, Sex and Ploidy Evaluation, and Compound-Heterozygous Analysis
========================================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


Functional annotation, clinical classification and phenotype similarity cannot determine disease relevance without considering the expected inheritance model. A candidate variant may appear damaging but remain incompatible with the disease’s allelic requirement, the patient’s genotype or the chromosome’s expected ploidy.

The inheritance stage combines:

Variant chromosome and genotype

│

▼

Patient sex and chromosome ploidy

│

▼

Gene2Phenotype allelic requirement

│

▼

Dominant, recessive, X-linked or mitochondrial model

│

▼

Single-variant or multi-variant evaluation

│

▼

Compound-heterozygous phase assessment

│

▼

Inheritance compatibility evidence

│

▼

Universal candidate scoring

The principal project files are:

.. code:: bash

   pipeline/case_workflow/inheritance_utils.py
   pipeline/case_workflow/20_sex_ploidy_preflight.py
   pipeline/case_workflow/21_resolve_case_sex.py
   pipeline/case_workflow/10b_add_compound_heterozygous_evidence.py
   pipeline/tests/05_test_inheritance_models.py
   pipeline/tests/06_test_sex_ploidy_preflight.py
   pipeline/tests/08_test_compound_heterozygous.py

These files should be described in the Word document and linked to their complete GitHub versions.

.. _11-1-purpose-of-inheritance-modelling:

11.1 Purpose of inheritance modelling
-------------------------------------

Inheritance modelling determines whether the observed genotype is compatible with the gene–disease relationship.

The analysis considers:

-  chromosome;

-  reference and alternate alleles;

-  genotype;

-  zygosity;

-  phasing;

-  patient sex;

-  chromosome ploidy;

-  allelic requirement;

-  disease inheritance;

-  number of candidate variants in the gene;

-  whether two variants are in cis, in trans or unphased;

-  whether the expected molecular mechanism is compatible with the variant.

Gene2Phenotype distinguishes gene–disease models such as monoallelic_autosomal, biallelic_autosomal, monoallelic_X_hemizygous and monoallelic_X_heterozygous. These categories describe the required genotype for a specific gene–disease model rather than a universal property of the gene. (`EBI <https://www.ebi.ac.uk/gene2phenotype/lgd/G2P01759>`__)

A gene may therefore have:

-  

   .. container::

      One dominant disease model

-  

   .. container::

      One recessive disease model

-  

   .. container::

      One X-linked model

-  

   .. container::

      Several disorders with different mechanisms

Each gene–disease model must be evaluated separately.

.. _11-2-shared-inheritance-utilities:

11.2 Shared inheritance utilities
---------------------------------

The shared inheritance functions are maintained in:

pipeline/case_workflow/inheritance_utils.py

Centralising this logic prevents different pipeline stages from independently interpreting the same genotype in different ways.

The utility module supports common operations such as:

-  chromosome normalisation;

-  genotype parsing;

-  missing-genotype detection;

-  haploid and diploid genotype handling;

-  heterozygous and homozygous classification;

-  hemizygous interpretation;

-  alternate-allele counting;

-  sex-chromosome handling;

-  inheritance-model normalisation;

-  phase extraction;

-  compatibility evaluation.

The same functions can therefore be reused by:

-  

   .. container::

      Small-variant scoring

-  

   .. container::

      Sex and ploidy preflight

-  

   .. container::

      Compound-heterozygous aggregation

-  

   .. container::

      ClinPGx genotype interpretation

-  

   .. container::

      Final candidate-table generation

.. _11-2-1-validate-the-inheritance-source-files:

11.2.1 Validate the inheritance source files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   INHERITANCE_FILES=(
   pipeline/case_workflow/inheritance_utils.py
   pipeline/case_workflow/20_sex_ploidy_preflight.py
   pipeline/case_workflow/21_resolve_case_sex.py
   pipeline/case_workflow/10b_add_compound_heterozygous_evidence.py
   )
   FAILURES=0
   for script in "${INHERITANCE_FILES[@]}"; do
   if [[ ! -s "$script" ]]; then
   echo "FAIL: Missing source file: $script"
   FAILURES=$((FAILURES + 1))
   continue
   fi
   python -m py_compile "$script"
   echo "PASS: $script"
   done
   if (( FAILURES > 0 )); then
   echo "ERROR: $FAILURES inheritance source file(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: Inheritance source files passed syntax validation."

.. _11-2-2-inspect-the-available-command-interfaces:

11.2.2 Inspect the available command interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some project scripts are called internally and may not expose a standalone --help interface. The following block checks safely without executing a patient analysis:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPTS=(
   pipeline/case_workflow/20_sex_ploidy_preflight.py
   pipeline/case_workflow/21_resolve_case_sex.py
   pipeline/case_workflow/10b_add_compound_heterozygous_evidence.py
   )
   for script in "${SCRIPTS[@]}"; do
   echo
   echo "=== $script ==="
   if python "$script" --help \
   > /tmp/inheritance_script_help.txt \
   2>&1
   then
   cat /tmp/inheritance_script_help.txt
   else
   echo "No standard --help output was returned."
   echo "Argument definitions present in source:"
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$script" \
   || true
   fi
   done
   rm -f /tmp/inheritance_script_help.txt

The universal pipeline launcher should remain the normal way to call these scripts.

.. _11-3-genotype-interpretation:

11.3 Genotype interpretation
----------------------------

The VCF GT field identifies which listed alleles are present in the sample.

Examples include:

+--------------+---------------------------------------------------------+
| **Genotype** | **Basic interpretation**                                |
+==============+=========================================================+
| 0/0          | Diploid homozygous reference                            |
+--------------+---------------------------------------------------------+
| 0/1          | Diploid heterozygous                                    |
+--------------+---------------------------------------------------------+
| 1/1          | Diploid homozygous alternate                            |
+--------------+---------------------------------------------------------+
| \`0          | 1\`                                                     |
+--------------+---------------------------------------------------------+
| \`1          | 0\`                                                     |
+--------------+---------------------------------------------------------+
| 1            | Haploid alternate                                       |
+--------------+---------------------------------------------------------+
| 0            | Haploid reference                                       |
+--------------+---------------------------------------------------------+
| ./.          | Missing diploid genotype                                |
+--------------+---------------------------------------------------------+
| .            | Missing haploid genotype                                |
+--------------+---------------------------------------------------------+
| 1/2          | Two different alternate alleles at a multiallelic locus |
+--------------+---------------------------------------------------------+

The slash / represents an unphased genotype, whereas the vertical bar \| represents a phased genotype. The current VCF specification also defines PS as a phase-set identifier and states that it is relevant when the corresponding genotype is phased.

The pipeline should not infer phase from allele order when the genotype uses /.

For example:

0/1

does not show whether the alternate allele was inherited maternally or paternally.

.. _11-3-1-inspect-genotype-fields-in-a-vcf:

11.3.1 Inspect genotype fields in a VCF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="input/sample.small_variants.vcf"
   if [[ ! -s "$VCF" ]]; then
   echo "ERROR: VCF is missing or empty: $VCF"
   exit 1
   fi
   echo "=== Samples ==="
   bcftools query \
   --list-samples \
   "$VCF"
   echo
   echo "=== Genotypes ==="
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT[\t%GT]\n' \
   "$VCF" |
   head -n 20

Count the observed genotype strings:

.. code:: bash

   bcftools query \
   --format '[%GT\n]' \
   "$VCF" |
   sort |
   uniq -c |
   sort -nr

.. _11-3-2-check-which-phase-related-format-fields-exist:

11.3.2 Check which phase-related FORMAT fields exist
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="input/sample.small_variants.vcf"
   PHASE_TAGS=(
   GT
   PS
   PID
   PGT
   )
   for tag in "${PHASE_TAGS[@]}"; do
   if bcftools view \
   --header-only \
   "$VCF" |
   grep -q "^##FORMAT=<ID=${tag},"
   then
   printf "PRESENT FORMAT/%s\n" "$tag"
   else
   printf "ABSENT FORMAT/%s\n" "$tag"
   fi
   done

The absence of PS, PID or PGT is not automatically a VCF error. It means that the corresponding phasing information is unavailable.

.. _11-4-zygosity-categories-used-by-the-pipeline:

11.4 Zygosity categories used by the pipeline
---------------------------------------------

.. _11-4-1-heterozygous:

11.4.1 Heterozygous
~~~~~~~~~~~~~~~~~~~

A diploid heterozygous variant contains one reference and one alternate allele:

0/1

1/0

0|1

1|0

This may satisfy a monoallelic dominant disease model, provided that:

-  the gene–disease relationship is appropriate;

-  the variant consequence matches the mechanism;

-  the disease evidence is sufficient;

-  the phenotype is compatible.

For a biallelic recessive model, one heterozygous variant usually provides only partial inheritance support.

.. _11-4-2-homozygous-alternate:

11.4.2 Homozygous alternate
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A diploid homozygous alternate variant is commonly represented as:

1/1

1|1

This may satisfy a biallelic recessive requirement when:

-  the variant itself is relevant;

-  homozygosity is biologically plausible;

-  the disease mechanism is compatible;

-  the record is not an artefact;

-  population frequency does not contradict the disease model.

A homozygous variant represents one locus with two alternate copies. It must not be duplicated artificially and counted as two separate variants.

.. _11-4-3-hemizygous:

11.4.3 Hemizygous
~~~~~~~~~~~~~~~~~

A hemizygous genotype means that only one relevant chromosome copy is present.

It may appear as:

1

or sometimes as a diploid-looking genotype depending on the variant caller:

1/1

The pipeline should therefore interpret hemizygosity using:

-  chromosome;

-  genomic region;

-  patient sex;

-  expected ploidy;

-  genotype representation.

The genotype string alone is insufficient.

.. _11-4-4-missing-genotype:

11.4.4 Missing genotype
~~~~~~~~~~~~~~~~~~~~~~~

Missing genotypes include:

.

./.

.\|.

A variant with a missing genotype may still have locus-level annotation, but the pipeline cannot confidently assign:

-  zygosity;

-  inheritance compatibility;

-  compound-heterozygous status;

-  genotype-based ClinPGx interpretation.

The appropriate output should state that genotype evidence is unavailable.

.. _11-5-allelic-requirements-and-inheritance-compatibility:

11.5 Allelic requirements and inheritance compatibility
-------------------------------------------------------

The pipeline maps normalised G2P allelic requirements to the observed genotype.

A conceptual compatibility table is:

+----------------------------+-------------------------------------------------------------------------+
| **Disease model**          | **Potentially compatible observation**                                  |
+============================+=========================================================================+
| Monoallelic autosomal      | One qualifying heterozygous or homozygous alternate variant             |
+----------------------------+-------------------------------------------------------------------------+
| Biallelic autosomal        | One qualifying homozygous variant or two qualifying variants in trans   |
+----------------------------+-------------------------------------------------------------------------+
| Monoallelic X hemizygous   | One qualifying X-chromosome variant in a compatible hemizygous context  |
+----------------------------+-------------------------------------------------------------------------+
| Monoallelic X heterozygous | One qualifying heterozygous X-chromosome variant                        |
+----------------------------+-------------------------------------------------------------------------+
| Biallelic X                | Two qualifying X-chromosome alleles in an appropriate context           |
+----------------------------+-------------------------------------------------------------------------+
| Mitochondrial              | A qualifying mitochondrial variant with suitable mitochondrial evidence |
+----------------------------+-------------------------------------------------------------------------+

This table describes general compatibility only. The precise scoring behaviour is controlled by:

.. code:: bash

   pipeline/case_workflow/inheritance_utils.py
   pipeline/case_workflow/11_score_universal_evidence.py

The report should not invent a new inheritance score or weighting system.

.. _11-6-autosomal-dominant-models:

11.6 Autosomal dominant models
------------------------------

An autosomal dominant or monoallelic_autosomal disease model generally requires one relevant altered allele.

Potentially compatible observations include:

-  

   .. container::

      0/1

-  

   .. container::

      0|1

-  

   .. container::

      1|0

-  

   .. container::

      1/1

However, a compatible genotype does not automatically establish causality.

Further evidence includes:

-  disease mechanism;

-  variant consequence;

-  ClinVar significance;

-  population frequency;

-  phenotype similarity;

-  de novo status;

-  segregation;

-  penetrance;

-  gene–disease confidence.

A homozygous variant can still occur in a dominant gene, but its phenotype and biological implications may differ from those of a heterozygous variant.

.. _11-7-autosomal-recessive-models:

11.7 Autosomal recessive models
-------------------------------

A biallelic_autosomal model generally requires pathogenic or likely disease-causing variation affecting both gene copies. G2P uses this category for curated recessive gene–disease relationships.

The pipeline recognises two main patterns:

Homozygous alternate variant

or:

Two qualifying heterozygous variants in trans

One unphased heterozygous variant should not receive the same inheritance support as a confirmed biallelic genotype.

Possible statuses include:

-  

   .. container::

      biallelic_homozygous

-  

   .. container::

      compound_heterozygous_phased_trans

-  

   .. container::

      possible_compound_heterozygous_unphased

-  

   .. container::

      single_heterozygous_candidate

-  

   .. container::

      inheritance_not_satisfied

The exact output labels should follow the committed source files.

.. _11-8-x-linked-inheritance:

11.8 X-linked inheritance
-------------------------

X-linked interpretation requires the combination of genotype and sex/ploidy context.

The project recognises G2P categories including:

-  

   .. container::

      monoallelic_X_hemizygous

-  

   .. container::

      monoallelic_X_heterozygous

These represent different required genotype contexts. G2P records explicitly distinguish hemizygous X-linked models from heterozygous X-linked models. (`EBI <https://www.ebi.ac.uk/gene2phenotype/lgd/G2P01759>`__)

The pipeline therefore evaluates:

-  whether the variant is on chromosome X;

-  reported or resolved sex;

-  observed genotype;

-  expected chromosome copy number;

-  disease allelic requirement;

-  whether the genotype appears hemizygous or heterozygous;

-  whether the interpretation requires additional review.

.. _11-8-1-important-x-chromosome-limitations:

11.8.1 Important X-chromosome limitations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current workflow should not claim complete clinical resolution of:

-  pseudoautosomal-region behaviour;

-  X-inactivation;

-  skewed X-inactivation;

-  sex-chromosome aneuploidy;

-  mosaic sex-chromosome variation;

-  complex structural changes involving chromosome X;

-  tissue-specific expression.

When these factors may be relevant, the result should be marked for specialist review.

.. _11-9-y-linked-records:

11.9 Y-linked records
---------------------

A chromosome Y variant requires:

-  a compatible sample context;

-  a valid Y-chromosome genotype;

-  a relevant gene–disease relationship;

-  confirmation that the region is represented correctly.

A Y-chromosome record in a case without compatible sex information should generate a warning rather than being silently interpreted.

The pipeline does not infer a clinical diagnosis solely from the presence or absence of chromosome Y records.

.. _11-10-mitochondrial-inheritance:

11.10 Mitochondrial inheritance
-------------------------------

Mitochondrial variants occur on:

chrM

They should not be evaluated using ordinary diploid autosomal rules.

Relevant factors include:

-  alternate allele presence;

-  variant allele fraction;

-  heteroplasmy;

-  homoplasmy;

-  tissue sampled;

-  sequencing depth;

-  mitochondrial haplogroup;

-  maternal inheritance;

-  disease-specific threshold effects.

The current universal workflow can identify mitochondrial inheritance and avoid inappropriate autosomal scoring. Detailed heteroplasmy analysis remains outside the fully validated scope unless the input contains reliable quantitative mitochondrial fields.

.. _11-11-sex-resolution:

11.11 Sex resolution
--------------------

The sex-resolution script is:

pipeline/case_workflow/21_resolve_case_sex.py

The workflow may receive sex information from:

-  case metadata;

-  validation sample sheet;

-  intake report;

-  explicit command-line input;

-  another controlled metadata source.

The project should distinguish:

-  

   .. container::

      male

-  

   .. container::

      female

-  

   .. container::

      unknown

-  

   .. container::

      conflicting

or the equivalent values used in its source code.

Sex should not be inferred from a person’s name or other unrelated identifying information.

When sex information is missing, sex-dependent inheritance should remain uncertain.

.. _11-11-1-sex-source-precedence:

11.11.1 Sex source precedence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A safe conceptual precedence is:

Explicit validated case metadata

↓

Structured intake or sample sheet

↓

Supported genomic evidence, where implemented

↓

Unknown

The exact precedence used by the project is maintained in:

pipeline/case_workflow/21_resolve_case_sex.py

The report should preserve the selected source in the reproducibility manifest.

.. _11-12-sex-and-ploidy-preflight:

11.12 Sex and ploidy preflight
------------------------------

The preflight script is:

pipeline/case_workflow/20_sex_ploidy_preflight.py

Its purpose is to identify potential inconsistencies before inheritance scoring.

The preflight may evaluate:

-  autosomal genotype ploidy;

-  X-chromosome genotypes;

-  Y-chromosome records;

-  mitochondrial genotypes;

-  missing or unresolved sex;

-  haploid versus diploid genotype representation;

-  unexpected genotype patterns;

-  records requiring manual review.

The preflight should report warnings and errors separately.

A warning may mean:

Interpretation is possible but uncertain

whereas an error may mean:

The required genotype context cannot be resolved safely

.. _11-12-1-run-the-sex-and-ploidy-regression-test:

11.12.1 Run the sex and ploidy regression test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/06_test_sex_ploidy_preflight.py
   echo
   echo "PASS: Sex and ploidy regression test completed."

The command is successful only when Python exits with status code zero.

.. _11-12-2-run-the-inheritance-model-regression-test:

11.12.2 Run the inheritance-model regression test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/05_test_inheritance_models.py
   echo
   echo "PASS: Inheritance-model regression test completed."

This test covers the shared inheritance logic without requiring a complete annotation run.

.. _11-13-inspect-sex-chromosome-and-mitochondrial-records:

11.13 Inspect sex-chromosome and mitochondrial records
------------------------------------------------------

The following block scans all committed validation VCFs without altering them:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF_DIR="validation/universal_pipeline_testing/inputs/vcfs"
   if [[ ! -d "$VCF_DIR" ]]; then
   echo "ERROR: Validation VCF directory is missing."
   exit 1
   fi
   FOUND=0
   while IFS= read -r -d '' vcf; do
   records="$(
   bcftools query \
   --regions chrX,chrY,chrM \
   --format '%CHROM\t%POS\t%REF\t%ALT[\t%GT]\n' \
   "$vcf" \
   2>/dev/null \
   || true
   )"
   if [[ -n "$records" ]]; then
   echo
   echo "=== $vcf ==="
   printf '%s\n' "$records"
   FOUND=$((FOUND + 1))
   fi
   done < <(
   find "$VCF_DIR" \
   -maxdepth 1 \
   -type f \
   \( -name '*.vcf' -o -name '*.vcf.gz' \) \
   -print0 |
   sort -z
   )
   echo
   if (( FOUND == 0 )); then
   echo "No chrX, chrY or chrM validation records were found."
   else
   echo "Files containing sex-chromosome or mitochondrial records: $FOUND"
   fi

The command is an inspection only. The production preflight uses the Python implementation.

.. _11-14-compound-heterozygosity:

11.14 Compound heterozygosity
-----------------------------

Compound heterozygosity occurs when two different variants affect the two copies of the same gene.

A typical recessive configuration is:

-  

   .. container::

      Maternal chromosome: variant A

-  

   .. container::

      Paternal chromosome: variant B

The two variants are therefore:

in trans

When both variants occur on the same chromosome copy, they are:

in cis

Only a trans configuration normally provides two independently affected alleles for a conventional recessive model.

ClinGen guidance distinguishes proven in-trans observations from unconfirmed phase. Depending on the context, confirmation may require parental testing or another suitable molecular phasing method.

.. _11-15-project-compound-heterozygous-logic:

11.15 Project compound-heterozygous logic
-----------------------------------------

The compound-heterozygous script is:

pipeline/case_workflow/10b_add_compound_heterozygous_evidence.py

The project uses the following safeguards:

1.  Both records must map to the same relevant gene.

2.  The disease model must support biallelic inheritance.

3.  Both variants must represent qualifying alternate alleles.

4.  Homozygous variants are not duplicated to manufacture a pair.

5.  Two unphased heterozygous variants are labelled as possible only.

6.  Phased variants must belong to a compatible shared phase set.

7.  Opposite haplotypes are required for a phased-trans pair.

8.  Same-haplotype variants are treated as cis.

9.  Missing phase data cannot establish trans.

10. Every pair retains the identifiers of both component variants.

.. _11-15-1-pipeline-terminology-versus-clinical-confirmation:

11.15.1 Pipeline terminology versus clinical confirmation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The project may label a pair as:

confirmed_trans

when the supplied VCF contains:

-  phased genotypes;

-  compatible shared PS or PID;

-  opposite haplotypes.

In the report, this should be described more precisely as:

phase-confirmed trans within the supplied VCF phasing data

This does not necessarily equal independent clinical confirmation through parental testing.

The final report should therefore distinguish:

Pipeline phase evidence

from:

Clinical or familial confirmation of trans inheritance

.. _11-16-phased-genotype-examples:

11.16 Phased genotype examples
------------------------------

Consider two variants in the same gene.

**Example A: opposite haplotypes**

-  

   .. container::

      Variant 1: 0|1

-  

   .. container::

      Variant 2: 1|0

-  

   .. container::

      Shared PS: 1000

The alternate alleles occur on opposite haplotypes.

Pipeline interpretation:

phased trans

**Example B: same haplotype**

-  

   .. container::

      Variant 1: 0|1

-  

   .. container::

      Variant 2: 0|1

-  

   .. container::

      Shared PS: 1000

The alternate alleles occur on the same haplotype.

Pipeline interpretation:

cis

**Example C: no shared phase set**

-  

   .. container::

      Variant 1: 0|1, PS=1000

-  

   .. container::

      Variant 2: 1|0, PS=9000

The variants are phased, but they are not established as belonging to the same phase block.

Pipeline interpretation:

phase relationship unresolved

They must not automatically be declared trans.

**Example D: unphased heterozygous variants**

-  

   .. container::

      Variant 1: 0/1

-  

   .. container::

      Variant 2: 0/1

Pipeline interpretation:

possible compound heterozygous

This is not phase confirmation.

.. _11-17-phase-set-fields:

11.17 Phase-set fields
----------------------

**PS**

PS identifies a phase set. Variants sharing the same valid phase set may be compared within that block.

A PS value should not be used when the genotype itself is unphased. The VCF specification states that the phase-set field is ignored for an unphased genotype. (Samtools)

**PID**

PID is used by some variant-calling workflows as a physical phasing identifier.

When the project accepts PID, two variants should share a compatible value before their haplotype orientation is compared.

**PGT**

PGT may store the phased genotype associated with PID.

Example:

GT:PID:PGT

0/1:12345_G_A:0|1

The project must not combine incompatible phase systems without explicit handling in the source code.

.. _11-18-inspect-phased-records-robustly:

11.18 Inspect phased records robustly
-------------------------------------

The following Python command reads all validation VCFs and lists records containing phased genotypes or phase-related FORMAT fields. It does not depend on every VCF defining the same tags.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   python3 - <<'PY'
   from __future__ import annotations
   import gzip
   from pathlib import Path
   vcf_directory = Path(
   "validation/universal_pipeline_testing/inputs/vcfs"
   )
   if not vcf_directory.is_dir():
   raise SystemExit(
   f"ERROR: Missing VCF directory: {vcf_directory}"
   )
   def open_text(path: Path):
   if path.suffix == ".gz":
   return gzip.open(path, "rt", encoding="utf-8")
   return path.open("r", encoding="utf-8")
   files_examined = 0
   records_reported = 0
   for path in sorted(vcf_directory.iterdir()):
   if not (
   path.name.endswith(".vcf")
   or path.name.endswith(".vcf.gz")
   ):
   continue
   files_examined += 1
   sample_names: list[str] = []
   with open_text(path) as handle:
   for raw_line in handle:
   if raw_line.startswith("##"):
   continue
   if raw_line.startswith("#CHROM"):
   header = raw_line.rstrip("\n").split("\t")
   sample_names = header[9:]
   continue
   if raw_line.startswith("#"):
   continue
   fields = raw_line.rstrip("\n").split("\t")
   if len(fields) < 10:
   continue
   chromosome = fields[0]
   position = fields[1]
   reference = fields[3]
   alternate = fields[4]
   format_keys = fields[8].split(":")
   sample_values = fields[9:]
   for sample_index, sample_value in enumerate(
   sample_values
   ):
   values = sample_value.split(":")
   format_map = {
   key: values[index]
   if index < len(values)
   else "."
   for index, key in enumerate(format_keys)
   }
   genotype = format_map.get("GT", ".")
   phase_set = format_map.get("PS", ".")
   phase_id = format_map.get("PID", ".")
   phased_gt = format_map.get("PGT", ".")
   has_phase_information = (
   "|" in genotype
   or phase_set not in {"", "."}
   or phase_id not in {"", "."}
   or phased_gt not in {"", "."}
   )
   if not has_phase_information:
   continue
   sample_name = (
   sample_names[sample_index]
   if sample_index < len(sample_names)
   else f"sample_{sample_index + 1}"
   )
   if records_reported == 0:
   print(
   "file\tsample\tchromosome\tposition\t"
   "reference\talternate\tGT\tPS\tPID\tPGT"
   )
   print(
   f"{path.name}\t"
   f"{sample_name}\t"
   f"{chromosome}\t"
   f"{position}\t"
   f"{reference}\t"
   f"{alternate}\t"
   f"{genotype}\t"
   f"{phase_set}\t"
   f"{phase_id}\t"
   f"{phased_gt}"
   )
   records_reported += 1
   print(
   f"\nFiles examined: {files_examined}",
   )
   print(
   f"Records containing phase information: "
   f"{records_reported}"
   )
   PY

This is an inspection command only. Pair formation remains the responsibility of the committed compound-heterozygous script.

.. _11-19-candidate-pair-formation:

11.19 Candidate-pair formation
------------------------------

For a gene containing (n) qualifying heterozygous variants, there may be:

n × (n − 1) / 2

possible two-variant combinations.

The pipeline should not assign every combination the same interpretation.

Each pair must be evaluated for:

-  shared gene;

-  disease model;

-  genotype;

-  phase information;

-  transcript relevance;

-  variant consequence;

-  ClinVar evidence;

-  population frequency;

-  phenotype evidence;

-  whether either component is already excluded.

The output should retain both variants rather than collapsing them into an untraceable gene-level score.

.. _11-20-homozygous-variants-are-not-compound-heterozygous:

11.20 Homozygous variants are not compound heterozygous
-------------------------------------------------------

A homozygous alternate genotype:

1/1

already indicates that the same alternate allele is present on both homologous chromosomes in a diploid context.

It should be classified as:

homozygous biallelic

not:

compound heterozygous

The project specifically prevents a homozygous record from being copied twice and treated as an artificial two-variant pair.

.. _11-21-multiallelic-loci:

11.21 Multiallelic loci
-----------------------

A genotype such as:

1/2

contains two different alternate alleles at the same locus.

After decomposition, the genotype representation may change across derived biallelic records. Compound-heterozygous interpretation must therefore preserve:

-  original allele indices;

-  normalised alleles;

-  locus identity;

-  genotype transformation;

-  phase information.

A multiallelic genotype should not be interpreted from the decomposed rows without confirming how bcftools represented the component alleles.

.. _11-22-compound-heterozygous-regression-test:

11.22 Compound-heterozygous regression test
-------------------------------------------

Run the project test:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/08_test_compound_heterozygous.py
   echo
   echo "PASS: Compound-heterozygous regression test completed."

This test verifies the project’s intended behaviours, including:

-  

   .. container::

      Phased opposite haplotypes

-  

   .. container::

      Same-haplotype cis pairs

-  

   .. container::

      Unphased possible pairs

-  

   .. container::

      Phase-set compatibility

-  

   .. container::

      Homozygous non-duplication

The exact assertions remain available in the committed test file.

.. _11-23-run-all-inheritance-tests-together:

11.23 Run all inheritance tests together
----------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   TESTS=(
   pipeline/tests/05_test_inheritance_models.py
   pipeline/tests/06_test_sex_ploidy_preflight.py
   pipeline/tests/08_test_compound_heterozygous.py
   )
   for test_script in "${TESTS[@]}"; do
   echo
   echo "=== Running $test_script ==="
   if [[ ! -s "$test_script" ]]; then
   echo "ERROR: Missing test: $test_script"
   exit 1
   fi
   python "$test_script"
   echo "PASS: $test_script"
   done
   echo
   echo "PASS: All inheritance regression tests completed."

.. _11-24-verify-that-tests-do-not-modify-tracked-files:

11.24 Verify that tests do not modify tracked files
---------------------------------------------------

Before running the tests:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git status --short \
   > /tmp/git_status_before_inheritance_tests.txt

Run the tests:

.. code:: bash

   source .venv/bin/activate
   python pipeline/tests/05_test_inheritance_models.py
   python pipeline/tests/06_test_sex_ploidy_preflight.py
   python pipeline/tests/08_test_compound_heterozygous.py

Compare the repository state:

.. code:: bash

   git status --short \
   > /tmp/git_status_after_inheritance_tests.txt
   if diff -u \
   /tmp/git_status_before_inheritance_tests.txt \
   /tmp/git_status_after_inheritance_tests.txt
   then
   echo "PASS: Tests did not change the tracked repository state."
   else
   echo "WARNING: Repository status changed during testing."
   echo "Inspect the differences before committing anything."
   fi
   rm -f \
   /tmp/git_status_before_inheritance_tests.txt \
   /tmp/git_status_after_inheritance_tests.txt

Ignored test outputs may still be created locally, but tracked source files should remain unchanged.

.. _11-25-recommended-inheritance-output-fields:

11.25 Recommended inheritance output fields
-------------------------------------------

The final candidate table should retain fields such as:

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

      gene

-  

   .. container::

      genotype

-  

   .. container::

      zygosity

-  

   .. container::

      ploidy

-  

   .. container::

      reported_sex

-  

   .. container::

      resolved_sex

-  

   .. container::

      sex_resolution_source

-  

   .. container::

      g2p_allelic_requirement

-  

   .. container::

      g2p_inheritance

-  

   .. container::

      inheritance_compatibility

-  

   .. container::

      inheritance_evidence_status

-  

   .. container::

      inheritance_warning

-  

   .. container::

      phase_status

-  

   .. container::

      phase_set

-  

   .. container::

      phase_identifier

-  

   .. container::

      haplotype_assignment

-  

   .. container::

      compound_het_status

-  

   .. container::

      compound_het_pair_id

-  

   .. container::

      paired_variant

-  

   .. container::

      paired_variant_score

-  

   .. container::

      pair_phase_evidence

The exact column names should follow the generated pipeline outputs.

.. _11-26-inheritance-evidence-categories:

11.26 Inheritance evidence categories
-------------------------------------

A useful interpretation model separates positive, uncertain and incompatible evidence.

**Strong compatibility**

Examples include:

-  

   .. container::

      Heterozygous variant in a compatible monoallelic model

-  

   .. container::

      Homozygous variant in a compatible biallelic model

-  

   .. container::

      Phased-trans qualifying pair in a biallelic model

-  

   .. container::

      Hemizygous X variant in a compatible X-linked model

**Partial or uncertain compatibility**

Examples include:

-  

   .. container::

      One heterozygous variant in a biallelic model

-  

   .. container::

      Two unphased heterozygous variants in the same recessive gene

-  

   .. container::

      Sex-dependent variant with unresolved sex

-  

   .. container::

      Mitochondrial variant without heteroplasmy information

**Incompatible or unsupported**

Examples include:

-  

   .. container::

      Single heterozygous variant treated as complete recessive evidence

-  

   .. container::

      Cis pair treated as two affected alleles

-  

   .. container::

      Autosomal assumptions applied directly to chrM

-  

   .. container::

      X-linked hemizygous model without compatible ploidy

-  

   .. container::

      Missing genotype treated as alternate

An incompatible inheritance model should reduce or qualify ranking evidence, but the original variant should remain visible for review.

.. _11-27-de-novo-inheritance:

11.27 De novo inheritance
-------------------------

A variant may be described as de novo only when suitable family evidence is available.

A single-sample VCF cannot independently demonstrate that a variant is de novo.

De novo assessment normally requires:

-  parental samples;

-  parentage confirmation where clinically required;

-  adequate parental coverage;

-  absence of the variant in both parents;

-  consideration of parental mosaicism;

-  appropriate quality checks.

When parental data are unavailable, the pipeline should state:

de_novo_status_not_assessed

rather than:

de_novo

.. _11-28-segregation-analysis:

11.28 Segregation analysis
--------------------------

The current case-level pipeline does not replace formal pedigree or family segregation analysis.

Segregation evidence may require:

-  affected and unaffected relatives;

-  family relationships;

-  family-level VCFs;

-  phenotype information for relatives;

-  penetrance assumptions;

-  age-dependent disease information;

-  confirmation testing.

When family data are unavailable, inheritance compatibility remains a computational prioritisation result.

.. _11-29-mosaicism-limitations:

11.29 Mosaicism limitations
---------------------------

A genotype such as:

0/1

does not by itself distinguish constitutional heterozygosity from mosaicism.

Mosaic interpretation requires evidence such as:

-  alternate allele depth;

-  total read depth;

-  variant allele fraction;

-  strand balance;

-  caller-specific quality;

-  tissue type;

-  orthogonal validation.

The current inheritance stage should not infer mosaicism solely from a genotype label.

.. _11-30-ploidy-limitations:

11.30 Ploidy limitations
------------------------

Ploidy may differ from the expected chromosome model because of:

-  sex-chromosome aneuploidy;

-  copy-number variation;

-  mosaicism;

-  tumour contamination;

-  caller-specific ploidy configuration;

-  pseudoautosomal regions;

-  complex structural variants.

The sex/ploidy preflight is a safeguard, not a complete cytogenetic analysis.

Unexpected ploidy should generate an explicit warning and may require:

Karyotyping

Chromosomal microarray

CNV analysis

Read-depth analysis

Specialist review

.. _11-31-common-inheritance-analysis-failures:

11.31 Common inheritance-analysis failures
------------------------------------------

+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| **Failure**                                             | **Likely cause**                         | **Required response**                              |
+=========================================================+==========================================+====================================================+
| Inheritance field missing                               | G2P mapping absent or schema changed     | Preserve candidate and report unavailable evidence |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Sex missing                                             | Incomplete case metadata                 | Mark sex-dependent interpretation uncertain        |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Sex value inconsistent                                  | Conflicting metadata sources             | Stop or issue a high-priority warning              |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Haploid genotype on autosome                            | Caller configuration or malformed record | Review ploidy and source VCF                       |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Diploid-looking genotype on hemizygous chromosome       | Caller representation                    | Interpret with chromosome and sex context          |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| One heterozygous variant satisfies recessive model      | Incorrect allelic counting               | Require a second allele or homozygous state        |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Unphased pair labelled trans                            | Phase logic error                        | Downgrade to possible compound heterozygosity      |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Different phase sets treated as comparable              | PS/PID ignored                           | Require shared compatible phase information        |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Same haplotype treated as trans                         | Haplotype orientation reversed           | Classify as cis                                    |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Homozygous variant counted twice                        | Pair-generation error                    | Treat as one homozygous biallelic candidate        |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Two variants in different genes paired                  | Gene grouping error                      | Pair only within the same relevant gene            |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Missing genotype treated as reference                   | Incorrect null handling                  | Report genotype unavailable                        |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| chrM treated as diploid                                 | Autosomal logic reused                   | Apply mitochondrial handling                       |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| X-linked variant interpreted without sex                | Missing preflight                        | Mark uncertain                                     |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| VCF phasing treated as parental confirmation            | Overinterpretation                       | Distinguish computational and clinical evidence    |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| PAR region treated as ordinary hemizygous X             | Incomplete region handling               | Flag for specialist review                         |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+
| Multiallelic decomposition changes genotype incorrectly | Lost allele-index provenance             | Review pre- and post-normalisation genotypes       |
+---------------------------------------------------------+------------------------------------------+----------------------------------------------------+

.. _11-32-inheritance-readiness-check:

11.32 Inheritance readiness check
---------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   REQUIRED_FILES=(
   pipeline/case_workflow/inheritance_utils.py
   pipeline/case_workflow/20_sex_ploidy_preflight.py
   pipeline/case_workflow/21_resolve_case_sex.py
   pipeline/case_workflow/10b_add_compound_heterozygous_evidence.py
   pipeline/tests/05_test_inheritance_models.py
   pipeline/tests/06_test_sex_ploidy_preflight.py
   pipeline/tests/08_test_compound_heterozygous.py
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
   echo "ERROR: $FAILURES inheritance component(s) are missing."
   exit 1
   fi
   for path in "${REQUIRED_FILES[@]}"; do
   if [[ "$path" == *.py ]]; then
   python -m py_compile "$path"
   fi
   done
   python pipeline/tests/05_test_inheritance_models.py
   python pipeline/tests/06_test_sex_ploidy_preflight.py
   python pipeline/tests/08_test_compound_heterozygous.py
   echo
   echo "PASS: Inheritance, sex/ploidy and compound-heterozygous components are ready."

.. _11-33-inheritance-stage-completion-criteria:

11.33 Inheritance-stage completion criteria
-------------------------------------------

The inheritance stage is complete when:

✓ The G2P allelic requirement is available where possible

✓ GT values are parsed consistently

✓ Missing genotypes remain explicitly missing

✓ Haploid and diploid genotypes are distinguished

✓ Reported and resolved sex are preserved

✓ Sex-dependent interpretation passes through ploidy preflight

✓ Autosomal dominant models require a compatible altered allele

✓ Autosomal recessive models require biallelic evidence

✓ X-linked hemizygous and heterozygous models remain distinct

✓ Mitochondrial variants are not evaluated as ordinary diploid variants

✓ Homozygous variants are treated as homozygous biallelic candidates

✓ Homozygous variants are not duplicated into artificial pairs

✓ Compound-heterozygous candidates are grouped within the same gene

✓ Unphased pairs are reported only as possible

✓ Shared compatible phase-set information is required

✓ Opposite haplotypes are required for phased-trans evidence

✓ Same-haplotype pairs are classified as cis

✓ VCF phase evidence is distinguished from parental confirmation

✓ Unsupported ploidy and inheritance situations produce warnings

✓ All inheritance regression tests pass

✓ Inheritance evidence remains part of prioritisation rather than an automatic diagnosis

The resulting inheritance evidence can now be combined with functional, clinical, phenotype and population evidence during universal candidate scoring.

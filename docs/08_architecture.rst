.. _8-universal-pipeline-architecture-variant-detection-and-branch-routing:

8. Universal Pipeline Architecture, Variant Detection and Branch Routing
========================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


The pipeline uses a modular architecture in which one case is processed through a sequence of independent stages. Rather than passing every VCF record through the same tools, the workflow first establishes the case context, validates the input, identifies the variant classes present and routes each class to the appropriate analytical branch.

This design prevents:

-  symbolic CNVs from being treated as ordinary indels;

-  repeat expansions from entering small-variant ranking;

-  pharmacogenomic matches from relying only on rsIDs;

-  validation-only disease relationships from entering production analysis;

-  sex-chromosome variants from being interpreted using autosomal assumptions;

-  failed or unsupported records from disappearing silently.

The complete workflow is coordinated by Bash launchers, while Python programs perform data parsing, evidence integration, inheritance modelling, phenotype matching and candidate scoring.

.. _8-1-high-level-pipeline-architecture:

8.1 High-level pipeline architecture
------------------------------------

The universal workflow can be represented as:

Case VCF + metadata + HPO terms

│

▼

Case-context resolution

│

▼

Structural input validation

│

▼

Sex and ploidy preflight

│

▼

Variant detection and routing

│

┌──────────┼───────────┬────────────────┐

│ │ │ │

▼ ▼ ▼ ▼

Small CNV/SV Repeat Unsupported

variants records expansions records

│ │ │ │

▼ ▼ ▼ ▼

VEP AnnotSV Dedicated Explicit

SnpEff ClassifyCNV repeat report status report

ClinVar ISV-CNV

SpliceAI

│ │

▼ ▼

Disease, phenotype, inheritance

and ClinPGx evidence integration

│

▼

Universal candidate scoring

│

▼

Master tables and case report

│

▼

Reproducibility manifest and audit

Not every case passes through every branch. The route depends on the records present in the submitted VCF.

.. _8-2-main-pipeline-entry-points:

8.2 Main pipeline entry points
------------------------------

The project contains several launchers, but they serve different purposes.

+---------------------------------------+------------------------------------------------------------------+
| **Launcher**                          | **Role**                                                         |
+=======================================+==================================================================+
| pipeline/run_universal_case.sh        | Primary launcher for a prepared universal case                   |
+---------------------------------------+------------------------------------------------------------------+
| pipeline/run_case_pipeline.sh         | Coordinates the main downstream analytical stages                |
+---------------------------------------+------------------------------------------------------------------+
| pipeline/run_real_patient_case.sh     | Performs controlled intake and preparation of an external case   |
+---------------------------------------+------------------------------------------------------------------+
| pipeline/run_rare_disease_pipeline.sh | Earlier general rare-disease workflow retained for compatibility |
+---------------------------------------+------------------------------------------------------------------+

The complete source files should be linked from GitHub in the Word report rather than reproduced in full.

The principal production entry point is:

pipeline/run_universal_case.sh

The launcher is responsible for connecting the case input with:

-  the active analysis mode;

-  case metadata;

-  phenotype information;

-  available reference resources;

-  branch-specific scripts;

-  case output directories;

-  execution logs;

-  completion status.

.. _8-2-1-confirm-the-launcher-files-after-cloning:

8.2.1 Confirm the launcher files after cloning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   REQUIRED_LAUNCHERS=(
   pipeline/run_universal_case.sh
   pipeline/run_case_pipeline.sh
   pipeline/run_real_patient_case.sh
   pipeline/run_rare_disease_pipeline.sh
   )
   FAILURES=0
   for script in "${REQUIRED_LAUNCHERS[@]}"; do
   if [[ -s "$script" ]]; then
   printf "PASS %s\n" "$script"
   else
   printf "FAIL %s\n" "$script"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo "ERROR: $FAILURES launcher file(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: Pipeline launchers are present."

Validate their Bash syntax:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   for script in \
   pipeline/run_universal_case.sh \
   pipeline/run_case_pipeline.sh \
   pipeline/run_real_patient_case.sh \
   pipeline/run_rare_disease_pipeline.sh
   do
   bash -n "$script"
   echo "PASS: $script"
   done

.. _8-3-case-context-resolution:

8.3 Case-context resolution
---------------------------

Before any variant is annotated, the pipeline establishes the context in which the case will be analysed.

The main scripts are:

.. code:: bash

   pipeline/case_workflow/00_resolve_case_context.py
   pipeline/case_workflow/00_validate_case_context.py

Context resolution identifies or verifies:

-  case identifier;

-  patient identifier;

-  VCF path;

-  HPO filename;

-  reported sex;

-  analysis mode;

-  project root;

-  output directory;

-  active resources;

-  expected genome build;

-  sample name;

-  validation metadata, where applicable.

The resolved context prevents downstream scripts from independently guessing file paths or patient information.

.. _8-3-1-why-a-case-context-is-required:

8.3.1 Why a case context is required
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Without a central case context, different stages could accidentally use:

-  different VCF files;

-  different patient identifiers;

-  an HPO file belonging to another patient;

-  different Gene2Phenotype resource modes;

-  inconsistent result directories;

-  different sex assumptions;

-  different reference versions.

A validated context ensures that every stage refers to the same case.

.. _8-3-2-case-context-validation:

8.3.2 Case-context validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The validation stage checks that:

-  

   .. container::

      The VCF exists and is not empty

-  

   .. container::

      The case identifier is valid

-  

   .. container::

      The required metadata are present

-  

   .. container::

      The genome build is GRCh38

-  

   .. container::

      The HPO file belongs to the intended case

-  

   .. container::

      The selected resource mode is valid

-  

   .. container::

      The result path is writable

-  

   .. container::

      Required scripts and resources are available

A failure at this stage should stop the workflow before annotation begins.

.. _8-4-exact-patient-file-matching:

8.4 Exact patient-file matching
-------------------------------

Patient files are matched using exact identifiers rather than loose substring matching.

For example:

patient_01

must not automatically match:

-  

   .. container::

      patient_010

-  

   .. container::

      patient_011

-  

   .. container::

      patient_012

-  

   .. container::

      patient_013

The project includes a regression test for this behaviour:

pipeline/tests/09_test_exact_hpo_patient_matching.py

This is especially important for HPO files because assigning the wrong phenotype terms could alter the candidate ranking while leaving the genomic annotations unchanged.

.. _8-5-production-and-validation-resource-selection:

8.5 Production and validation resource selection
------------------------------------------------

The workflow supports two resource modes.

.. _8-5-1-production-mode:

8.5.1 Production mode
~~~~~~~~~~~~~~~~~~~~~

Production mode uses official resources only.

Its active Gene2Phenotype source should be based on:

.. code:: bash

   resources/gene_disease/g2p/AllG2P.official.csv

This mode must not include locally inserted disease relationships created for synthetic testing.

.. _8-5-2-validation-mode:

8.5.2 Validation mode
~~~~~~~~~~~~~~~~~~~~~

Validation mode may use:

Official Gene2Phenotype relationships

+

Controlled local validation relationships

The validation resource is maintained separately from the official production file.

Relevant files include:

-  

   .. container::

      resources/gene_disease/g2p/AllG2P.official.csv

-  

   .. container::

      resources/gene_disease/g2p/AllG2P.local_validation.csv

-  

   .. container::

      resources/gene_disease/g2p/AllG2P.validation.csv

-  

   .. container::

      The active resource is prepared through:

-  

   .. container::

      pipeline/case_workflow/00b_refresh_combined_g2p.py

The production file must never be edited merely to make a synthetic test case pass.

.. _8-5-3-resource-isolation-tests:

8.5.3 Resource-isolation tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following tests confirm that validation relationships cannot contaminate production mode:

.. code:: bash

   pipeline/tests/03_test_resource_modes.py
   pipeline/tests/07_test_g2p_resource_isolation.py

Run them using the project virtual environment:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/03_test_resource_modes.py
   python \
   pipeline/tests/07_test_g2p_resource_isolation.py

The exact output wording may differ, but both tests must exit with status code zero.

Confirm the combined status:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python pipeline/tests/03_test_resource_modes.py
   python pipeline/tests/07_test_g2p_resource_isolation.py
   echo "PASS: Production and validation resources remain isolated."

.. _8-6-sex-and-ploidy-preflight:

8.6 Sex and ploidy preflight
----------------------------

Sex and ploidy evaluation occurs before inheritance evidence is assigned.

The relevant files are:

.. code:: bash

   pipeline/case_workflow/20_sex_ploidy_preflight.py
   pipeline/case_workflow/21_resolve_case_sex.py
   pipeline/case_workflow/inheritance_utils.py

The preflight evaluates whether genotype representation is compatible with:

-  chromosome type;

-  reported sex;

-  expected chromosome copy number;

-  haploid or diploid notation;

-  hemizygous interpretation;

-  mitochondrial inheritance.

.. _8-6-1-autosomal-chromosomes:

8.6.1 Autosomal chromosomes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Autosomal chromosomes are generally interpreted as diploid.

Common genotype interpretations include:

-  

   .. container::

      0/1 heterozygous

-  

   .. container::

      1/1 homozygous alternate

-  

   .. container::

      0|1 phased heterozygous

-  

   .. container::

      1|0 phased heterozygous

.. _8-6-2-chromosome-x:

8.6.2 Chromosome X
~~~~~~~~~~~~~~~~~~

The interpretation of chromosome X depends on:

-  reported sex;

-  genomic region;

-  genotype representation;

-  pseudoautosomal-region status where relevant;

-  expected inheritance model.

A single alternate allele may represent a hemizygous genotype in an individual with one X chromosome.

.. _8-6-3-chromosome-y:

8.6.3 Chromosome Y
~~~~~~~~~~~~~~~~~~

A Y-chromosome record requires compatible sex and ploidy information. An incompatible or unexplained record should be reported for review rather than silently accepted.

.. _8-6-4-mitochondrial-chromosome:

8.6.4 Mitochondrial chromosome
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Mitochondrial variants are not interpreted using ordinary diploid autosomal assumptions.

The current pipeline can recognise mitochondrial inheritance, but detailed heteroplasmy interpretation may require:

-  allele-depth information;

-  variant allele fraction;

-  tissue-specific evidence;

-  specialised mitochondrial analysis.

.. _8-6-5-run-the-sex-and-ploidy-tests:

8.6.5 Run the sex and ploidy tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/05_test_inheritance_models.py
   python \
   pipeline/tests/06_test_sex_ploidy_preflight.py
   echo "PASS: Inheritance and sex/ploidy regression tests completed."

.. _8-7-variant-detection:

8.7 Variant detection
---------------------

The central routing script is:

.. code:: bash

   pipeline/case_workflow/00_detect_and_split_variants.py

It inspects each VCF record using information such as:

-  REF allele;

-  ALT allele;

-  symbolic allele form;

-  SVTYPE;

-  END;

-  repeat-related INFO fields;

-  record length;

-  genotype fields;

-  available VCF header definitions.

The script determines the most appropriate route without modifying the original input VCF.

.. _8-8-small-variant-route:

8.8 Small-variant route
-----------------------

The small-variant branch accepts ordinary SNVs and small insertions or deletions.

Examples include:

-  

   .. container::

      REF=A ALT=G

-  

   .. container::

      REF=C ALT=T

-  

   .. container::

      REF=A ALT=AT

-  

   .. container::

      REF=GCT ALT=G

-  

   .. container::

      The branch normally performs:

   -  

      .. container::

         Small-variant extraction

   -  

      .. container::

         Normalisation

   -  

      .. container::

         VEP annotation

   -  

      .. container::

         SnpEff annotation

   -  

      .. container::

         ClinVar integration

   -  

      .. container::

         SpliceAI annotation

   -  

      .. container::

         Gene–disease mapping

   -  

      .. container::

         Phenotype scoring

   -  

      .. container::

         Inheritance scoring

   -  

      .. container::

         Compound-heterozygous analysis

   -  

      .. container::

         ClinPGx matching

   -  

      .. container::

         Universal evidence scoring

   -  

      .. container::

         Master-table generation

-  

   .. container::

      Relevant scripts include:

-  

   .. container::

      01_normalize_routed_small_variants.sh

-  

   .. container::

      02_annotate_vep.sh

-  

   .. container::

      03_annotate_snpeff.sh

-  

   .. container::

      03_extract_vep_table.py

-  

   .. container::

      04_map_genes_to_diseases.py

-  

   .. container::

      05_add_clinpgx_matches.py

-  

   .. container::

      05b_add_local_pgx_reference.py

-  

   .. container::

      06_add_clinvar.sh

-  

   .. container::

      08_add_spliceai.sh

-  

   .. container::

      09_merge_snpeff_spliceai.py

-  

   .. container::

      10_add_phenotype_scores.py

-  

   .. container::

      10a_add_semantic_phenotype_evidence.py

-  

   .. container::

      10b_add_compound_heterozygous_evidence.py

-  

   .. container::

      10b_resolve_disease_identities.py

-  

   .. container::

      10b_calibrate_clinvar_ranking.py

-  

   .. container::

      11_score_universal_evidence.py

-  

   .. container::

      12_build_universal_master.py

-  

   .. container::

      14_build_master_candidate_table.py

The exact execution order is controlled by the pipeline launchers, not by manually running each script independently.

.. _8-9-cnv-and-structural-variant-route:

8.9 CNV and structural-variant route
------------------------------------

Records representing deletions or duplications are passed to the CNV branch.

Typical indicators include:

.. code:: bash

   ALT=<DEL>
   ALT=<DUP>
   SVTYPE=DEL
   SVTYPE=DUP
   END=<genomic endpoint>

The branch converts or prepares the records in a four-column interval format:

-  

   .. container::

      chromosome start end DEL/DUP

-  

   .. container::

      The CNV branch then coordinates:

-  

   .. container::

      AnnotSV

-  

   .. container::

      ClassifyCNV

-  

   .. container::

      ISV-CNV

-  

   .. container::

      ClinGen dosage evidence

-  

   .. container::

      Gene–disease evidence

-  

   .. container::

      HPO semantic evidence

-  

   .. container::

      CNV-specific ClinPGx overlap

-  

   .. container::

      Universal CNV scoring

-  

   .. container::

      Relevant scripts include:

-  

   .. container::

      pipeline/case_workflow/10c_prepare_cnv_semantic_input.py

-  

   .. container::

      pipeline/case_workflow/10d_add_cnv_semantic_phenotype_evidence.py

-  

   .. container::

      pipeline/case_workflow/11_run_cnv_tools.sh

-  

   .. container::

      pipeline/case_workflow/11b_score_universal_cnv.py

-  

   .. container::

      pipeline/case_workflow/11c_add_cnv_clinpgx.py

-  

   .. container::

      pipeline/case_workflow/12_score_cnv_candidates.py

CNV scoring remains separate from small-variant scoring because CNVs require interval- and dosage-based evidence.

.. _8-10-repeat-expansion-route:

8.10 Repeat-expansion route
---------------------------

Repeat expansions are detected and written to a separate report through:

pipeline/case_workflow/00b_report_repeat_expansions.py

The report may contain:

-  chromosome and position;

-  gene or locus;

-  repeat motif;

-  repeat count;

-  genotype;

-  pathogenic threshold;

-  transcript notation;

-  protein notation;

-  record identifier;

-  routing status.

A repeat-expansion record is assigned a status equivalent to:

detected_not_interpreted

This means that:

-  the pipeline recognised the record;

-  the record was preserved;

-  available repeat information was extracted;

-  the record was excluded from ordinary small-variant ranking;

-  specialised repeat analysis is required.

The pipeline must not convert a repeat expansion into an ordinary insertion simply to force it through VEP or SnpEff.

.. _8-11-unsupported-variant-route:

8.11 Unsupported-variant route
------------------------------

Some records may be valid VCF entries but remain outside the current analytical scope.

Examples include:

-  

   .. container::

      Balanced translocations

-  

   .. container::

      Breakend records

-  

   .. container::

      Complex inversions

-  

   .. container::

      Mobile-element insertions

-  

   .. container::

      Complex symbolic insertions

-  

   .. container::

      Highly complex rearrangements

Records lacking sufficient endpoint information

These records should be:

1. detected;

2. retained;

3. assigned an explicit reason;

4. excluded from unsupported ranking methods;

5. reported for specialised review.

An unsupported record should never be silently removed.

.. _8-12-pharmacogenomic-route:

8.12 Pharmacogenomic route
--------------------------

ClinPGx matching is performed alongside rare-disease analysis but is maintained as a separate evidence category.

The pipeline can compare:

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

      Genotype

-  

   .. container::

      Star allele

-  

   .. container::

      Predicted metaboliser phenotype

-  

   .. container::

      Drug association

The local matching script is:

.. code:: bash

   pipeline/case_workflow/05b_add_local_pgx_reference.py

Matching is allele-aware. A shared rsID alone is insufficient.

For example, a reference may contain one particular allele of an rsID. A case carrying another allele at the same locus must not automatically receive the same pharmacogenomic interpretation.

.. _8-12-1-run-the-allele-aware-clinpgx-test:

8.12.1 Run the allele-aware ClinPGx test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/04_test_allele_aware_local_pgx.py
   echo "PASS: Allele-aware ClinPGx matching test completed."

.. _8-13-disease-identity-resolution:

8.13 Disease identity resolution
--------------------------------

The same gene or variant may be associated with differently formatted disease names across:

-  Gene2Phenotype;

-  ClinVar;

-  MONDO;

-  OMIM-derived labels;

-  HPO annotations;

-  local validation resources.

The script:

.. code:: bash

   pipeline/case_workflow/10b_resolve_disease_identities.py

harmonises these labels.

The controlled Gene2Phenotype disease label is given precedence where appropriate because it is directly connected to:

-  the gene;

-  disease model;

-  inheritance;

-  allelic requirement;

-  molecular mechanism;

-  confidence category.

ClinVar condition names remain important supporting evidence, but they may contain:

-  multiple conditions;

-  broad phenotype labels;

-  historical disease names;

-  combined condition strings;

-  submission-specific terminology.

The regression test is:

.. code:: bash

   pipeline/tests/10_test_g2p_disease_label_precedence.py

Run it with:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/10_test_g2p_disease_label_precedence.py

.. _8-14-compound-heterozygous-routing:

8.14 Compound-heterozygous routing
----------------------------------

Two heterozygous variants in the same recessive disease gene may be evaluated as a possible compound-heterozygous pair.

The relevant script is:

.. code:: bash

   pipeline/case_workflow/10b_add_compound_heterozygous_evidence.py

The pipeline distinguishes:

+------------------------------------------+-------------------------------------------+
| **State**                                | **Interpretation**                        |
+==========================================+===========================================+
| Phased on opposite haplotypes            | Confirmed trans evidence                  |
+------------------------------------------+-------------------------------------------+
| Phased on the same haplotype             | Cis; not a disease-causing pair by itself |
+------------------------------------------+-------------------------------------------+
| Both heterozygous but unphased           | Possible compound-heterozygous pair       |
+------------------------------------------+-------------------------------------------+
| Only one qualifying heterozygous variant | Insufficient for a recessive pair         |
+------------------------------------------+-------------------------------------------+
| Homozygous alternate variant             | Biallelic but not compound heterozygous   |
+------------------------------------------+-------------------------------------------+
| Different genes                          | Not a compound-heterozygous pair          |
+------------------------------------------+-------------------------------------------+

Confirmed trans evidence requires:

-  compatible phase-set information;

-  the variants to belong to the same phase block;

-  opposite haplotypes;

-  the same relevant gene;

-  compatibility with a recessive disease model.

A homozygous variant must not be counted twice to create an artificial compound-heterozygous pair.

.. _8-14-1-run-the-compound-heterozygous-test:

8.14.1 Run the compound-heterozygous test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/08_test_compound_heterozygous.py
   echo "PASS: Compound-heterozygous regression test completed."

.. _8-15-branch-specific-output-organisation:

8.15 Branch-specific output organisation
----------------------------------------

Each case should keep its analytical branches separated.

A typical result structure is:

results/cases/<case_id>/

├── intake/

├── context/

├── routed/

│ ├── small_variants/

│ ├── cnv/

│ ├── repeat_expansions/

│ └── unsupported/

├── annotations/

├── phenotype/

├── inheritance/

├── clinpgx/

├── ranking/

├── reports/

├── logs/

└── manifests/

The exact folder names may differ according to the production launcher, but the conceptual separation remains the same.

.. _8-16-empty-analytical-branches:

8.16 Empty analytical branches
------------------------------

A case may contain no records for one or more branches.

Examples include:

-  

   .. container::

      No CNVs

-  

   .. container::

      No repeat expansions

-  

   .. container::

      No ClinPGx matches

-  

   .. container::

      No small variants

An empty branch should produce an explicit status rather than causing the pipeline to fail unexpectedly.

Examples of acceptable statuses include:

not_applicable

no_records_detected

disabled

completed_with_zero_matches

This distinction is important:

No records detected ≠ analytical failure

.. _8-17-disabled-optional-stages:

8.17 Disabled optional stages
-----------------------------

An optional tool may be disabled because:

-  the resource is unavailable;

-  the container is not installed;

-  the case contains no suitable records;

-  the user selected a reduced analysis mode;

-  licensing prevents redistribution;

-  

   .. container::

      a specialist manual workflow

-  is preferred.

The project includes:

.. code:: bash

   pipeline/case_workflow/05c_write_disabled_local_pgx.py

to generate an explicit output when local ClinPGx matching is disabled.

The same design principle should be applied to other optional stages: absence of execution should be documented, not hidden.

.. _8-18-failure-handling:

8.18 Failure handling
---------------------

The Bash launchers should use:

.. code:: bash

   set -Eeuo pipefail

This causes execution to stop when:

-  a command fails;

-  an undefined variable is used;

-  a pipeline component returns a failure;

-  a required command cannot complete.

Each stage should write errors to a case-specific log.

A failed stage should preserve:

-  

   .. container::

      Input files

-  

   .. container::

      Completed intermediate files

-  

   .. container::

      Failure message

-  

   .. container::

      Failed command or stage

-  

   .. container::

      Resource mode

-  

   .. container::

      Execution timestamp

-  

   .. container::

      Case identifier

Incomplete output must not be presented as a successfully completed case.

.. _8-19-intake-report-preservation:

8.19 Intake-report preservation
-------------------------------

For external cases, the intake report must be preserved even after files are copied, harmonised or normalised.

The regression test is:

.. code:: bash

   pipeline/tests/11_test_intake_report_preservation.py

Run it with:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/11_test_intake_report_preservation.py

The original intake report provides evidence of:

-  what was supplied;

-  when it was supplied;

-  which warnings were present;

-  which checksums were calculated;

-  which preparation steps occurred.

.. _8-20-reproducibility-manifest:

8.20 Reproducibility manifest
-----------------------------

The script:

.. code:: bash

   pipeline/case_workflow/00c_build_reproducibility_manifest.py

records the analytical environment for each case.

A reproducibility manifest should include:

-  

   .. container::

      Case identifier

-  

   .. container::

      Input VCF path

-  

   .. container::

      Input checksum

-  

   .. container::

      HPO file and checksum

-  

   .. container::

      Reported sex

-  

   .. container::

      Genome build

-  

   .. container::

      Analysis mode

-  

   .. container::

      Pipeline commit or source checksums

-  

   .. container::

      Resource paths

-  

   .. container::

      Resource checksums or versions

-  

   .. container::

      Container checksums

-  

   .. container::

      Execution date and time

-  

   .. container::

      Generated outputs

-  

   .. container::

      Completion status

This allows a result to be traced back to the exact inputs, software and resources that produced it.

.. _8-21-safe-architecture-inspection-command:

8.21 Safe architecture inspection command
-----------------------------------------

The following command checks the pipeline architecture without executing a case:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   REQUIRED_FILES=(
   pipeline/run_universal_case.sh
   pipeline/run_case_pipeline.sh
   pipeline/case_workflow/00_resolve_case_context.py
   pipeline/case_workflow/00_validate_case_context.py
   pipeline/case_workflow/00_detect_and_split_variants.py
   pipeline/case_workflow/00b_report_repeat_expansions.py
   pipeline/case_workflow/00c_build_reproducibility_manifest.py
   pipeline/case_workflow/01_normalize_routed_small_variants.sh
   pipeline/case_workflow/02_annotate_vep.sh
   pipeline/case_workflow/03_annotate_snpeff.sh
   pipeline/case_workflow/04_map_genes_to_diseases.py
   pipeline/case_workflow/05b_add_local_pgx_reference.py
   pipeline/case_workflow/06_add_clinvar.sh
   pipeline/case_workflow/08_add_spliceai.sh
   pipeline/case_workflow/10_add_phenotype_scores.py
   pipeline/case_workflow/10b_add_compound_heterozygous_evidence.py
   pipeline/case_workflow/11_run_cnv_tools.sh
   pipeline/case_workflow/11_score_universal_evidence.py
   pipeline/case_workflow/12_build_universal_master.py
   pipeline/case_workflow/14_build_master_candidate_table.py
   pipeline/case_workflow/20_sex_ploidy_preflight.py
   pipeline/case_workflow/21_resolve_case_sex.py
   pipeline/case_workflow/inheritance_utils.py
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
   echo
   if (( FAILURES > 0 )); then
   echo "ERROR: $FAILURES required pipeline component(s) are missing."
   exit 1
   fi
   echo "PASS: Universal pipeline architecture is complete."

Validate all Bash files:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
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
   Validate all Python files without running the workflow:
   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   while IFS= read -r -d '' script; do
   python -m py_compile "$script"
   echo "PASS: $script"
   done < <(
   find pipeline \
   -type f \
   -name '*.py' \
   -print0 |
   sort -z
   )

.. _8-22-universal-architecture-readiness-checklist:

8.22 Universal architecture readiness checklist
-----------------------------------------------

The pipeline architecture is ready when:

-  

   .. container::

      ✓ Case-context scripts are present

-  

   .. container::

      ✓ Input validation completes successfully

-  

   .. container::

      ✓ Production and validation resources are isolated

-  

   .. container::

      ✓ Sex and ploidy checks pass

-  

   .. container::

      ✓ Small variants can be routed separately

-  

   .. container::

      ✓ CNVs can be converted to interval-based inputs

-  

   .. container::

      ✓ Repeat expansions produce a separate report

-  

   .. container::

      ✓ Unsupported variants receive an explicit status

-  

   .. container::

      ✓ ClinPGx matching is allele-aware

-  

   .. container::

      ✓ HPO files are matched exactly

-  

   .. container::

      ✓ Disease labels are harmonised

-  

   .. container::

      ✓ Compound-heterozygous evidence distinguishes trans, cis and unphased pairs

-  

   .. container::

      ✓ Empty branches are reported without false failures

-  

   .. container::

      ✓ Original intake reports remain preserved

-  

   .. container::

      ✓ Reproducibility manifests can be generated

-  

   .. container::

      ✓ Bash and Python source files pass syntax validation

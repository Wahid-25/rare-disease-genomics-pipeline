.. _3-project-directory-structure-and-the-purpose-of-every-folder-and-file-group:

3. Project Directory Structure and the Purpose of Every Folder and File Group
=============================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


.. _3-1-project-root-directory:

3.1 Project root directory
--------------------------

The complete project is maintained locally under:

.. code:: bash

   ~/rare_disease_project

This directory contains the pipeline source code, container definitions, compact reference resources, validation inputs, test scripts, generated results and locally installed bioinformatics resources.

The GitHub repository contains the reproducible source code and selected small resources:

https://github.com/Wahid-25/rare-disease-genomics-pipeline

Large databases, built container images and complete result directories remain on the local system and are excluded from GitHub through .gitignore.

The main project structure is:

rare_disease_project/

├── README.md

├── .gitignore

├── containers/

├── input/

├── pipeline/

├── resources/

├── results/

├── tools/

└── validation/

Each directory has a separate role in the workflow.

.. _3-2-root-level-files:

3.2 Root-level files
--------------------

.. _3-2-1-readme-md:

3.2.1 README.md
~~~~~~~~~~~~~~~

The root README provides a concise introduction to the repository.

It describes:

-  the purpose of the project;

-  the main pipeline capabilities;

-  the supported variant classes;

-  the validation status;

-  the distinction between research prioritisation and clinical diagnosis;

-  the exclusion of large databases and generated files;

-  the synthetic nature of the included validation data.

The README is the first file displayed when the repository is opened on GitHub.

.. _3-2-2-gitignore:

3.2.2 .gitignore
~~~~~~~~~~~~~~~~

The .gitignore file prevents unnecessary, sensitive or very large files from being committed to GitHub.

It excludes items such as:

-  

   .. container::

      Built Apptainer .sif images

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

      AnnotSV databases

-  

   .. container::

      ClassifyCNV installations

-  

   .. container::

      InterVar installations

-  

   .. container::

      BAM, CRAM and FASTQ files

-  

   .. container::

      Complete generated result folders

-  

   .. container::

      Failed run directories

-  

   .. container::

      Temporary files

-  

   .. container::

      Python cache files

-  

   .. container::

      Historical source backups

-  

   .. container::

      Local archives

-  

   .. container::

      Downloaded third-party tools

-  

   .. container::

      Large ontology databases

The .gitignore file allows the repository to remain small while preserving all source code required to reproduce the project.

.. _3-3-containers:

3.3 containers/
---------------

The containers/ directory contains Apptainer definition files used to build reproducible software environments.

containers/

├── README.md

├── core_tools.def

├── isv.def

├── read_processing.def

└── snpeff.def

Built container files use the .sif extension and remain local because they are large binary files.

.. _3-3-1-containers-readme-md:

3.3.1 containers/README.md
~~~~~~~~~~~~~~~~~~~~~~~~~~

This file explains that:

-  definition files are included in GitHub;

-  built .sif images are not uploaded;

-  users must build the containers locally;

-  containers provide isolated and reproducible software environments.

.. _3-3-2-core-tools-def:

3.3.2 core_tools.def
~~~~~~~~~~~~~~~~~~~~

This definition file describes the container containing core command-line genomics software.

Its purpose is to provide a controlled environment for tools such as:

-  bcftools;

-  samtools;

-  tabix;

-  bgzip;

-  common Linux text-processing utilities;

-  supporting libraries.

This container is used for tasks such as:

-  VCF validation;

-  VCF normalisation;

-  indexing;

-  chromosome inspection;

-  reference allele checking;

-  compressed VCF processing.

The built image is stored locally as a .sif file.

.. _3-3-3-snpeff-def:

3.3.3 snpeff.def
~~~~~~~~~~~~~~~~

This definition file creates the SnpEff environment.

SnpEff is used to predict the likely functional consequence of a variant, including:

-  synonymous variants;

-  missense variants;

-  stop-gained variants;

-  splice-region variants;

-  upstream and downstream variants;

-  intronic variants;

-  intergenic variants.

The definition file ensures that the correct Java environment and SnpEff software are available.

The SnpEff genome database remains in the local resources directory.

.. _3-3-4-isv-def:

3.3.4 isv.def
~~~~~~~~~~~~~

This definition file creates the environment required for ISV-CNV.

ISV-CNV is used as part of the copy-number variant workflow to provide machine-learning-supported CNV prioritisation.

The container may include:

-  Python;

-  required machine-learning packages;

-  SHAP-related dependencies;

-  libraries required by the ISV-CNV code.

The model and generated outputs remain local.

.. _3-3-5-read-processing-def:

3.3.5 read_processing.def
~~~~~~~~~~~~~~~~~~~~~~~~~

This definition file supports optional raw-read processing.

Its purpose is to provide software for tasks such as:

-  FASTQ preparation;

-  read alignment;

-  BAM generation;

-  BAM sorting;

-  BAM indexing;

-  basic sequencing-read processing.

This branch is not the principal validated workflow because the main pipeline begins from a prepared VCF. It is included to support future FASTQ-to-VCF expansion.

.. _3-4-input:

3.4 input/
----------

The input/ directory contains small example files and legacy synthetic inputs.

input/

├── cases/

├── cnv/

├── snv/

├── sample.cnvs.bed

├── sample.isv.bed

└── sample.small_variants.vcf

The universal validation cases are stored separately under the validation/ directory.

.. _3-4-1-input-cases:

3.4.1 input/cases/
~~~~~~~~~~~~~~~~~~

This directory is intended for case-level inputs submitted to the universal pipeline.

A prepared case directory may contain:

case_id/

├── case_id.raw.vcf

├── case_metadata.tsv

├── phenotype.hpo.txt

└── sample_information.tsv

The GitHub repository contains only a README in this directory because complete case folders may contain large or sensitive files.

The local pipeline may create case-specific prepared directories under this location.

.. _3-4-2-input-snv:

3.4.2 input/snv/
~~~~~~~~~~~~~~~~

This directory contains small synthetic SNV and indel examples.

The files are retained as general input examples showing:

-  VCF formatting;

-  GRCh38 coordinates;

-  chr-prefixed chromosomes;

-  reference and alternate alleles;

-  genotype representation;

-  background variants;

-  disease-associated variants.

These files are not the main universal validation set.

.. _3-4-3-input-cnv:

3.4.3 input/cnv/
~~~~~~~~~~~~~~~~

This directory contains small synthetic copy-number variant examples in BED format.

The files demonstrate how CNVs can be represented using:

-  

   .. container::

      chromosome

-  

   .. container::

      start coordinate

-  

   .. container::

      end coordinate

-  

   .. container::

      variant type

-  

   .. container::

      Typical CNV types include:

-  

   .. container::

      DEL

-  

   .. container::

      DUP

These examples help users understand the input format required by CNV annotation tools.

.. _3-4-4-input-sample-small-variants-vcf:

3.4.4 input/sample.small_variants.vcf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a compact example VCF for testing small-variant processing.

It can be used to demonstrate:

-  VCF structure;

-  basic normalisation;

-  annotation commands;

-  sample genotype parsing;

-  output generation.

.. _3-4-5-input-sample-cnvs-bed:

3.4.5 input/sample.cnvs.bed
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a minimal CNV BED example.

It demonstrates the input format required for deletion and duplication processing.

.. _3-4-6-input-sample-isv-bed:

3.4.6 input/sample.isv.bed
~~~~~~~~~~~~~~~~~~~~~~~~~~

This file demonstrates the format expected by the ISV-CNV branch.

It may differ slightly from the generic CNV BED format because downstream CNV tools can require specific columns or variant labels.

.. _3-5-pipeline:

3.5 pipeline/
-------------

The pipeline/ directory contains the main workflow scripts.

pipeline/

├── run_case_pipeline.sh

├── run_rare_disease_pipeline.sh

├── run_real_patient_case.sh

├── run_universal_case.sh

├── case_workflow/

├── resource_setup/

├── setup_resources/

└── tests/

The root-level pipeline scripts coordinate the individual stages located in pipeline/case_workflow/.

.. _3-6-main-pipeline-launchers:

3.6 Main pipeline launchers
---------------------------

.. _3-6-1-pipeline-run-universal-case-sh:

3.6.1 pipeline/run_universal_case.sh
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the main universal case launcher.

Its role is to:

-  receive the case input;

-  identify the project root;

-  prepare output directories;

-  resolve the case context;

-  detect the variant types present;

-  choose the appropriate processing branches;

-  run small-variant, CNV or repeat-expansion workflows;

-  manage production or validation resource mode;

-  generate case-level status information.

This is the principal entry point for universal VCF analysis.

.. _3-6-2-pipeline-run-case-pipeline-sh:

3.6.2 pipeline/run_case_pipeline.sh
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script coordinates the core case-analysis workflow.

It links together stages such as:

-  input preparation;

-  normalisation;

-  annotation;

-  disease mapping;

-  phenotype scoring;

-  ClinPGx matching;

-  candidate scoring;

-  output generation.

It is called by higher-level launchers after the case context has been resolved.

.. _3-6-3-pipeline-run-real-patient-case-sh:

3.6.3 pipeline/run_real_patient_case.sh
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script provides a more controlled launcher for externally supplied or real-case inputs.

Its responsibilities include:

-  case intake;

-  input validation;

-  preservation of original files;

-  creation of a prepared working directory;

-  verification of metadata;

-  execution of the universal workflow;

-  preservation of the intake report.

The script is designed to prevent direct modification of original input files.

.. _3-6-4-pipeline-run-rare-disease-pipeline-sh:

3.6.4 pipeline/run_rare_disease_pipeline.sh
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a general rare-disease workflow launcher.

It provides compatibility with the earlier pipeline organisation and may call several annotation stages sequentially.

It remains useful as:

-  a simplified entry point;

-  a compatibility script;

-  an alternative workflow launcher;

-  a reference for the earlier pipeline design.

The universal launcher should be preferred for the final project workflow.

.. _3-7-pipeline-case-workflow:

3.7 pipeline/case_workflow/
---------------------------

This directory contains the individual stages of the analysis.

The numeric prefixes indicate the approximate order of execution.

pipeline/case_workflow/

├── 00\_...

├── 01\_...

├── 02\_...

├── ...

├── 21\_...

├── inheritance_utils.py

└── run_universal_ranking.sh

.. _3-7-1-case-intake-and-variant-routing:

3.7.1 Case intake and variant routing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Script**                            | **Purpose**                                                                                                                                                           |
+=======================================+=======================================================================================================================================================================+
| 00_detect_and_split_variants.py       | Detects the variant classes present in the VCF and separates records into appropriate branches such as small variants, CNVs, symbolic variants and repeat expansions. |
+---------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 00_harmonize_vcf_chromosomes.py       | Standardises chromosome names, particularly conversion to the chr-prefixed GRCh38 convention.                                                                         |
+---------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 00_resolve_case_context.py            | Determines case identifiers, input paths, metadata, phenotype files, sex information and analysis mode.                                                               |
+---------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 00_validate_case_context.py           | Checks that the required case files and metadata are present and internally consistent.                                                                               |
+---------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 00b_refresh_combined_g2p.py           | Prepares the active Gene2Phenotype resource according to production or validation mode.                                                                               |
+---------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 00b_report_repeat_expansions.py       | Extracts and reports repeat-expansion records separately from ordinary small variants.                                                                                |
+---------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 00c_build_reproducibility_manifest.py | Records the files, resource versions, scripts, checksums and execution context used for the case.                                                                     |
+---------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

.. _3-7-2-input-preparation-and-normalisation:

3.7.2 Input preparation and normalisation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------+-------------------------------------------------------------------------+
| **Script**                            | **Purpose**                                                             |
+=======================================+=========================================================================+
| 01_prepare_and_normalize.sh           | Performs general VCF preparation, reference checking and normalisation. |
+---------------------------------------+-------------------------------------------------------------------------+
| 01_normalize_routed_small_variants.sh | Normalises only the records routed to the small-variant branch.         |
+---------------------------------------+-------------------------------------------------------------------------+

Normalisation may include:

-  decomposition of multiallelic records;

-  left alignment;

-  reference allele verification;

-  duplicate handling;

-  standardisation of representation;

-  preservation of the original input.

.. _3-7-3-functional-annotation:

3.7.3 Functional annotation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+-------------------------+-----------------------------------------------------------------------------+
| **Script**              | **Purpose**                                                                 |
+=========================+=============================================================================+
| 02_annotate_vep.sh      | Runs Ensembl VEP using the local GRCh38 cache.                              |
+-------------------------+-----------------------------------------------------------------------------+
| 03_annotate_snpeff.sh   | Runs SnpEff functional consequence annotation.                              |
+-------------------------+-----------------------------------------------------------------------------+
| 03_extract_vep_table.py | Converts VEP output into a structured tabular form for downstream analysis. |
+-------------------------+-----------------------------------------------------------------------------+

VEP and SnpEff provide information such as:

-  gene;

-  transcript;

-  consequence;

-  coding change;

-  protein change;

-  exon or intron;

-  transcript biotype;

-  canonical transcript;

-  MANE transcript;

-  population frequency where available.

.. _3-7-4-clinvar-integration:

3.7.4 ClinVar integration
~~~~~~~~~~~~~~~~~~~~~~~~~

+----------------------------------+-----------------------------------------------------------------------------------+
| **Script**                       | **Purpose**                                                                       |
+==================================+===================================================================================+
| 04_add_clinvar_to_snpeff.sh      | Adds ClinVar fields to the SnpEff-derived workflow.                               |
+----------------------------------+-----------------------------------------------------------------------------------+
| 06_add_clinvar.sh                | Adds ClinVar annotations to the main tabular candidate workflow.                  |
+----------------------------------+-----------------------------------------------------------------------------------+
| 10b_calibrate_clinvar_ranking.py | Adjusts ranking behaviour according to ClinVar significance and evidence quality. |
+----------------------------------+-----------------------------------------------------------------------------------+

ClinVar fields may include:

-  

   .. container::

      Clinical significance

-  

   .. container::

      Condition name

-  

   .. container::

      Review status

-  

   .. container::

      Variation identifier

-  

   .. container::

      Submission evidence

-  

   .. container::

      Conflict information

ClinVar evidence contributes to prioritisation but does not replace manual interpretation.

.. _3-7-5-gene-disease-mapping:

3.7.5 Gene–disease mapping
~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| **Script**                           | **Purpose**                                                                                                                  |
+======================================+==============================================================================================================================+
| 04_map_genes_to_diseases.py          | Maps annotated genes to Gene2Phenotype disease relationships and inheritance models.                                         |
+--------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| 04b_expand_hpo_disease_candidates.py | Uses HPO information to expand or support candidate disease associations.                                                    |
+--------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| 10b_resolve_disease_identities.py    | Harmonises disease names and identifiers, including precedence rules between Gene2Phenotype, ClinVar and ontology resources. |
+--------------------------------------+------------------------------------------------------------------------------------------------------------------------------+

Gene2Phenotype is given priority for controlled gene–disease relationships because it includes:

-  gene;

-  disease;

-  inheritance;

-  confidence category;

-  molecular mechanism;

-  allelic requirement.

MONDO may be used to harmonise disease identifiers and synonyms.

.. _3-7-6-clinpgx-annotation:

3.7.6 ClinPGx annotation
~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------+-------------------------------------------------------------------------------------+
| **Script**                      | **Purpose**                                                                         |
+=================================+=====================================================================================+
| 05_add_clinpgx_matches.py       | Searches for pharmacogenomic matches using available ClinPGx data.                  |
+---------------------------------+-------------------------------------------------------------------------------------+
| 05b_add_local_pgx_reference.py  | Performs allele-aware matching against the local curated pharmacogenomic reference. |
+---------------------------------+-------------------------------------------------------------------------------------+
| 05c_write_disabled_local_pgx.py | Produces an explicit output when local ClinPGx analysis is disabled.                |
+---------------------------------+-------------------------------------------------------------------------------------+

ClinPGx matching uses more than the rsID alone.

The matching process may compare:

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

      Gene

-  

   .. container::

      Star allele

-  

   .. container::

      Metaboliser phenotype

-  

   .. container::

      Drug

-  

   .. container::

      Clinical interpretation

This prevents incorrect matches caused by shared positions or identifiers with different alleles.

.. _3-7-7-disease-candidate-scoring:

3.7.7 Disease candidate scoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+------------------------------------+------------------------------------------------------------------------------------------------+
| **Script**                         | **Purpose**                                                                                    |
+====================================+================================================================================================+
| 07_score_disease_candidates.py     | Produces an early disease-candidate score using available annotation and disease evidence.     |
+------------------------------------+------------------------------------------------------------------------------------------------+
| 11_score_universal_evidence.py     | Combines multiple evidence categories into the main universal small-variant score.             |
+------------------------------------+------------------------------------------------------------------------------------------------+
| 12_build_universal_master.py       | Creates the integrated universal master table.                                                 |
+------------------------------------+------------------------------------------------------------------------------------------------+
| 14_build_master_candidate_table.py | Produces a final candidate table containing the most relevant fields from all analysis stages. |
+------------------------------------+------------------------------------------------------------------------------------------------+

The score may incorporate:

-  ClinVar significance;

-  variant consequence;

-  disease relationship;

-  inheritance compatibility;

-  zygosity;

-  phenotype similarity;

-  splice prediction;

-  compound-heterozygous evidence;

-  resource confidence;

-  variant class.

The score is a ranking aid, not an ACMG classification.

.. _3-7-8-spliceai-processing:

3.7.8 SpliceAI processing
~~~~~~~~~~~~~~~~~~~~~~~~~

+-----------------------------+-------------------------------------------------------------------+
| **Script**                  | **Purpose**                                                       |
+=============================+===================================================================+
| 08_add_spliceai.sh          | Adds splice-impact predictions where SpliceAI data are available. |
+-----------------------------+-------------------------------------------------------------------+
| 09_merge_snpeff_spliceai.py | Merges SnpEff consequence information with SpliceAI results.      |
+-----------------------------+-------------------------------------------------------------------+

SpliceAI evaluates the possibility that a variant may alter:

-  splice donor sites;

-  splice acceptor sites;

-  nearby cryptic splice sites;

-  exon recognition.

SpliceAI scores require interpretation alongside gene structure and transcript context.

.. _3-7-9-phenotype-scoring:

3.7.9 Phenotype scoring
~~~~~~~~~~~~~~~~~~~~~~~

+--------------------------------------------+------------------------------------------------------------------------------------------------+
| **Script**                                 | **Purpose**                                                                                    |
+============================================+================================================================================================+
| 10_add_phenotype_scores.py                 | Adds phenotype compatibility scores based on HPO information.                                  |
+--------------------------------------------+------------------------------------------------------------------------------------------------+
| 10a_add_semantic_phenotype_evidence.py     | Performs semantic comparison between patient HPO terms and disease-associated phenotype terms. |
+--------------------------------------------+------------------------------------------------------------------------------------------------+
| 10c_prepare_cnv_semantic_input.py          | Prepares CNV records for phenotype-based semantic scoring.                                     |
+--------------------------------------------+------------------------------------------------------------------------------------------------+
| 10d_add_cnv_semantic_phenotype_evidence.py | Adds HPO-based evidence to CNV candidates.                                                     |
+--------------------------------------------+------------------------------------------------------------------------------------------------+

Phenotype scoring improves candidate prioritisation by comparing the patient’s features with known disease phenotypes.

Exact patient filename matching prevents accidental use of another patient’s HPO file.

.. _3-7-10-compound-heterozygous-analysis:

3.7.10 Compound-heterozygous analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+-------------------------------------------+-------------------------------------------------------------------------------------------+
| **Script**                                | **Purpose**                                                                               |
+===========================================+===========================================================================================+
| 10b_add_compound_heterozygous_evidence.py | Identifies and annotates possible or phase-confirmed compound-heterozygous variant pairs. |
+-------------------------------------------+-------------------------------------------------------------------------------------------+

The script distinguishes:

-  

   .. container::

      Confirmed trans pair

-  

   .. container::

      Possible unphased pair

-  

   .. container::

      Cis pair

-  

   .. container::

      Single heterozygous variant

-  

   .. container::

      Homozygous variant

-  

   .. container::

      Non-qualifying pair

Confirmed trans status requires compatible phase information showing that the variants occur on opposite haplotypes.

.. _3-7-11-cnv-workflow:

3.7.11 CNV workflow
~~~~~~~~~~~~~~~~~~~

+----------------------------+--------------------------------------------------------------------------------+
| **Script**                 | **Purpose**                                                                    |
+============================+================================================================================+
| 11_run_cnv_tools.sh        | Coordinates CNV preparation and execution of AnnotSV, ClassifyCNV and ISV-CNV. |
+----------------------------+--------------------------------------------------------------------------------+
| 11b_score_universal_cnv.py | Applies the universal CNV prioritisation model.                                |
+----------------------------+--------------------------------------------------------------------------------+
| 11c_add_cnv_clinpgx.py     | Checks whether CNVs overlap pharmacogenomically relevant genes or regions.     |
+----------------------------+--------------------------------------------------------------------------------+
| 12_score_cnv_candidates.py | Generates CNV-specific candidate scores.                                       |
+----------------------------+--------------------------------------------------------------------------------+

The CNV branch considers:

-  deletion or duplication type;

-  genomic size;

-  affected genes;

-  dosage sensitivity;

-  disease relationships;

-  phenotype compatibility;

-  classification evidence;

-  ClinPGx relevance.

.. _3-7-12-clingen-annotation:

3.7.12 ClinGen annotation
~~~~~~~~~~~~~~~~~~~~~~~~~

+----------------------------------+-------------------------------------------------------------------------------+
| **Script**                       | **Purpose**                                                                   |
+==================================+===============================================================================+
| 13_add_clingen_small_variants.sh | Adds relevant ClinGen gene or dosage information to small-variant candidates. |
+----------------------------------+-------------------------------------------------------------------------------+

ClinGen information is especially important for:

-  haploinsufficiency;

-  triplosensitivity;

-  dosage-sensitive genes;

-  gene–disease validity.

.. _3-7-13-real-case-readiness-and-intake:

3.7.13 Real-case readiness and intake
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+------------------------------------+-----------------------------------------------------------------------------------------------+
| **Script**                         | **Purpose**                                                                                   |
+====================================+===============================================================================================+
| 15_check_real_patient_readiness.py | Checks whether the pipeline and required resources are ready for an externally supplied case. |
+------------------------------------+-----------------------------------------------------------------------------------------------+
| 16_prepare_real_patient_inputs.sh  | Copies and prepares case inputs without altering the original files.                          |
+------------------------------------+-----------------------------------------------------------------------------------------------+
| 17_validate_known_diagnosis.py     | Compares pipeline output with a known expected result for controlled validation.              |
+------------------------------------+-----------------------------------------------------------------------------------------------+
| 18_external_case_intake.py         | Creates a structured intake report and validates supplied metadata.                           |
+------------------------------------+-----------------------------------------------------------------------------------------------+
| 19_remove_existing_annotations.sh  | Removes previous annotations when an input must be reprocessed cleanly.                       |
+------------------------------------+-----------------------------------------------------------------------------------------------+

The intake process is designed to preserve:

-  the original file;

-  original checksums;

-  supplied metadata;

-  intake warnings;

-  preparation history.

.. _3-7-14-optional-raw-read-branch:

3.7.14 Optional raw-read branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------+-----------------------------------------------------------------------------+
| **Script**                | **Purpose**                                                                 |
+===========================+=============================================================================+
| 20_download_ena_fastqs.sh | Downloads sequencing reads from ENA for controlled external datasets.       |
+---------------------------+-----------------------------------------------------------------------------+
| 21_align_wes_fastq.sh     | Aligns whole-exome sequencing reads to GRCh38 and produces alignment files. |
+---------------------------+-----------------------------------------------------------------------------+

This branch is experimental and is not the principal validated workflow.

Large FASTQ and BAM files remain local and are excluded from GitHub.

.. _3-7-15-sex-and-ploidy-handling:

3.7.15 Sex and ploidy handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+----------------------------+----------------------------------------------------------------------------------------+
| **Script**                 | **Purpose**                                                                            |
+============================+========================================================================================+
| 20_sex_ploidy_preflight.py | Evaluates chromosome and genotype consistency before inheritance analysis.             |
+----------------------------+----------------------------------------------------------------------------------------+
| 21_resolve_case_sex.py     | Resolves reported or inferred case sex for chromosome-aware interpretation.            |
+----------------------------+----------------------------------------------------------------------------------------+
| inheritance_utils.py       | Provides shared functions for inheritance, genotype, chromosome and ploidy evaluation. |
+----------------------------+----------------------------------------------------------------------------------------+

These scripts support:

-  autosomal inheritance;

-  X-linked inheritance;

-  mitochondrial inheritance;

-  hemizygous genotypes;

-  diploid and haploid expectations;

-  sex-aware candidate scoring.

.. _3-7-16-universal-ranking-launcher:

3.7.16 Universal ranking launcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**run_universal_ranking.sh**

This script coordinates the final ranking stages.

It may execute:

-  phenotype scoring;

-  disease identity resolution;

-  ClinVar calibration;

-  inheritance evaluation;

-  compound-heterozygous analysis;

-  universal evidence scoring;

-  master candidate table generation.

It acts as a sub-workflow within the complete case pipeline.

.. _3-8-pipeline-resource-setup:

3.8 pipeline/resource_setup/
----------------------------

This directory contains scripts for preparing ontology and phenotype resources.

pipeline/resource_setup/

├── build_hpo_semantic_cache.py

├── build_mondo_crosswalk.py

└── download_mondo.sh

**build_hpo_semantic_cache.py**

Builds a local structured HPO resource for faster phenotype comparison.

It may process:

-  HPO term relationships;

-  gene-to-phenotype mappings;

-  disease-to-phenotype mappings;

-  ontology parent–child relationships.

**build_mondo_crosswalk.py**

Creates a mapping between disease identifiers and names from different sources.

It helps reconcile identifiers such as:

-  

   .. container::

      MONDO

-  

   .. container::

      OMIM

-  

   .. container::

      Orphanet

-  

   .. container::

      ClinVar disease labels

-  

   .. container::

      Gene2Phenotype disease labels

**download_mondo.sh**

Downloads the required MONDO ontology release and records its version.

The complete ontology file remains local, while lightweight release metadata may be stored in GitHub.

.. _3-9-pipeline-setup-resources:

3.9 pipeline/setup_resources/
-----------------------------

This directory contains resource-download and resource-testing scripts.

pipeline/setup_resources/

├── 01_download_g2p.sh

└── 02_test_clinpgx_api.py

**01_download_g2p.sh**

Downloads or refreshes Gene2Phenotype data.

The script supports:

-  versioned official resources;

-  metadata generation;

-  checksum recording;

-  separation between official and validation data.

**02_test_clinpgx_api.py**

Tests communication with the ClinPGx API.

It can:

-  query gene endpoints;

-  query variant endpoints;

-  cache small responses;

-  record access time;

-  record success or failure;

-  generate a metadata table.

This script confirms whether online ClinPGx retrieval is available.

.. _3-10-pipeline-tests:

3.10 pipeline/tests/
--------------------

The pipeline/tests/ directory contains regression tests and validation scripts.

pipeline/tests/

├── 01_run_final_validation_suite.sh

├── 03_test_resource_modes.py

├── 04_test_allele_aware_local_pgx.py

├── 05_test_inheritance_models.py

├── 06_test_sex_ploidy_preflight.py

├── 07_test_g2p_resource_isolation.py

├── 08_test_compound_heterozygous.py

├── 09_test_exact_hpo_patient_matching.py

├── 10_test_g2p_disease_label_precedence.py

├── 11_test_intake_report_preservation.py

└── run_vcf_structural_preflight.sh

+-----------------------------------------+----------------------------------------------------------------------------------------+
| **Test**                                | **Purpose**                                                                            |
+=========================================+========================================================================================+
| 01_run_final_validation_suite.sh        | Runs the complete final test collection.                                               |
+-----------------------------------------+----------------------------------------------------------------------------------------+
| 03_test_resource_modes.py               | Confirms that production and validation resources remain isolated.                     |
+-----------------------------------------+----------------------------------------------------------------------------------------+
| 04_test_allele_aware_local_pgx.py       | Confirms that ClinPGx matching requires correct alleles.                               |
+-----------------------------------------+----------------------------------------------------------------------------------------+
| 05_test_inheritance_models.py           | Tests autosomal, X-linked and mitochondrial inheritance logic.                         |
+-----------------------------------------+----------------------------------------------------------------------------------------+
| 06_test_sex_ploidy_preflight.py         | Tests chromosome, sex and ploidy consistency.                                          |
+-----------------------------------------+----------------------------------------------------------------------------------------+
| 07_test_g2p_resource_isolation.py       | Prevents validation relationships from entering production mode.                       |
+-----------------------------------------+----------------------------------------------------------------------------------------+
| 08_test_compound_heterozygous.py        | Tests phased and unphased compound-heterozygous aggregation.                           |
+-----------------------------------------+----------------------------------------------------------------------------------------+
| 09_test_exact_hpo_patient_matching.py   | Prevents one patient identifier from matching another similar identifier.              |
+-----------------------------------------+----------------------------------------------------------------------------------------+
| 10_test_g2p_disease_label_precedence.py | Confirms that the controlled Gene2Phenotype disease label is preferred where intended. |
+-----------------------------------------+----------------------------------------------------------------------------------------+
| 11_test_intake_report_preservation.py   | Confirms that the original intake report remains preserved.                            |
+-----------------------------------------+----------------------------------------------------------------------------------------+
| run_vcf_structural_preflight.sh         | Performs structural validation of all test VCF files before execution.                 |
+-----------------------------------------+----------------------------------------------------------------------------------------+

The accompanying text files document the expected behaviour of inheritance and compound-heterozygous components.

.. _3-11-resources:

3.11 resources/
---------------

The resources/ directory stores reference data required by the workflow.

resources/

├── reference/

├── vep_cache/

├── snpeff_data/

├── clinvar/

├── clingen/

├── clinpgx/

├── gene_disease/

├── phenotype/

├── disease_ontology/

└── annotsv_setup/

Only compact resources and metadata are stored in GitHub. Large reference files remain local.

.. _3-12-resources-reference:

3.12 resources/reference/
-------------------------

This directory contains the GRCh38 reference genome.

Typical local files include:

-  

   .. container::

      hg38.fa

-  

   .. container::

      hg38.fa.fai

-  

   .. container::

      hg38.dict

The FASTA file is used for:

-  coordinate interpretation;

-  reference allele checking;

-  VCF normalisation;

-  read alignment;

-  left alignment of indels;

-  chromosome sequence lookup.

Because the FASTA is several gigabytes, GitHub contains only README.md explaining where it should be installed.

.. _3-13-resources-vep-cache:

3.13 resources/vep_cache/
-------------------------

This directory contains the offline Ensembl VEP cache.

The project uses a GRCh38-compatible VEP release.

The cache supplies:

-  transcript structures;

-  gene names;

-  consequence terms;

-  protein consequences;

-  canonical transcript information;

-  MANE information;

-  selected frequency annotations.

The VEP cache is large and is not uploaded to GitHub.

.. _3-14-resources-snpeff-data:

3.14 resources/snpeff_data/
---------------------------

This directory stores the SnpEff genome database.

It is required for functional annotation using the selected GRCh38 SnpEff configuration.

The database remains local because of its size.

.. _3-15-resources-clinvar:

3.15 resources/clinvar/
-----------------------

This directory stores ClinVar-related files.

Typical local contents include:

-  

   .. container::

      clinvar.vcf.gz

-  

   .. container::

      clinvar.vcf.gz.tbi

-  

   .. container::

      chr_map.txt

chr_map.txt helps reconcile chromosome naming between resources.

ClinVar provides:

-  clinical significance;

-  disease assertions;

-  review status;

-  variation identifiers;

-  conflicting interpretations.

The large ClinVar VCF remains local.

.. _3-16-resources-clingen:

3.16 resources/clingen/
-----------------------

This directory contains ClinGen dosage-sensitivity information.

The committed file is:

clingen_dosage_genes_regions.csv

It contains gene- and region-level dosage evidence, including:

-  haploinsufficiency scores;

-  triplosensitivity scores;

-  gene names;

-  genomic regions;

-  evidence categories.

It supports both small-variant and CNV interpretation.

.. _3-17-resources-clinpgx:

3.17 resources/clinpgx/
-----------------------

This directory stores compact pharmacogenomic resources.

resources/clinpgx/

├── LOCAL_REFERENCE_SCHEMA.txt

├── local_curated_pgx_reference.csv

├── local_curated_pgx_reference.sha256

├── cache/

└── metadata/

**LOCAL_REFERENCE_SCHEMA.txt**

Defines the required columns and structure of the local ClinPGx reference.

**local_curated_pgx_reference.csv**

Contains controlled pharmacogenomic records used for allele-aware matching.

Typical fields include:

-  

   .. container::

      Gene

-  

   .. container::

      rsID

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

      Star allele

-  

   .. container::

      Genotype

-  

   .. container::

      Phenotype

-  

   .. container::

      Drug

-  

   .. container::

      Interpretation

**local_curated_pgx_reference.sha256**

Stores the checksum of the curated reference so that unexpected changes can be detected.

**cache/**

Stores small API responses used during testing.

**metadata/clinpgx_api_test.tsv**

Records API access tests, endpoint status, retrieved record count, cache file and access time.

.. _3-18-resources-gene-disease:

3.18 resources/gene_disease/
----------------------------

This directory stores gene–disease relationships.

The main resource is Gene2Phenotype.

resources/gene_disease/g2p/

├── AllG2P.official.csv

├── AllG2P.validation.csv

├── AllG2P.local_validation.csv

├── AllG2P.metadata.tsv

├── AllG2P.validation.metadata.tsv

├── AllG2P.combined.metadata.tsv

├── G2P_RESOURCE_ISOLATION.txt

└── RESOURCE_MODES.txt

-  

   .. container::

      **AllG2P.official.csv**

Contains official Gene2Phenotype relationships.

-  

   .. container::

      This file is used in production mode.

-  

   .. container::

      **AllG2P.validation.csv**

Contains the official relationships plus controlled validation entries.

It is used only in validation mode.

-  

   .. container::

      **AllG2P.local_validation.csv**

Contains locally defined validation relationships.

These entries must never alter the official production file.

-  

   .. container::

      **Metadata files**

The metadata files record:

-  resource version;

-  file path;

-  creation time;

-  source;

-  checksum;

-  number of relationships;

-  validation status.

-  

   .. container::

      **Resource-isolation documentation**

The text files explain why production and validation data are separated.

.. _3-19-resources-phenotype:

3.19 resources/phenotype/
-------------------------

This directory stores HPO-related resources.

resources/phenotype/hpo/

├── current

└── v2026-02-16/

├── genes_to_disease.txt

├── release_manifest.tsv

└── additional local resources

**current**

This symbolic link points to the active HPO release directory.

Using a symbolic link allows a resource version to be changed without rewriting every pipeline path.

**genes_to_disease.txt**

Connects genes with diseases represented in HPO-related resources.

**release_manifest.tsv**

Records:

-  release version;

-  source;

-  download date;

-  expected files;

-  checksum information.

Larger HPO files and semantic databases remain local.

.. _3-20-resources-disease-ontology:

3.20 resources/disease_ontology/
--------------------------------

This directory stores MONDO ontology resources.

resources/disease_ontology/mondo/

├── current

└── v2026-07-06/

└── release_manifest.tsv

The active release may contain local files such as:

-  

   .. container::

      mondo.obo

-  

   .. container::

      mondo.sqlite

identifier crosswalks

MONDO is used to:

-  harmonise disease names;

-  resolve synonyms;

-  connect identifiers from different databases;

-  reduce duplicate disease entries.

Large ontology files remain excluded from GitHub.

.. _3-21-resources-annotsv-setup:

3.21 resources/annotsv_setup/
-----------------------------

This local directory contains the AnnotSV installation and annotation databases.

AnnotSV is used for structural-variant and CNV annotation.

Its resources may include:

-  gene annotations;

-  genomic regulatory regions;

-  ClinGen dosage information;

-  disease-associated CNV databases;

-  population CNV databases;

-  transcript annotations.

The directory is excluded from GitHub because it is large and contains downloaded third-party data.

The installation commands will be documented directly in the Word report.

.. _3-22-tools:

3.22 tools/
-----------

The tools/ directory contains locally installed third-party software.

Typical local directories include:

tools/

├── AnnotSV/

├── ClassifyCNV/

├── InterVar/

└── other supporting tools

GitHub contains only tools/README.md because third-party software should normally be installed from its official source rather than redistributed.

.. _3-22-1-classifycnv:

3.22.1 ClassifyCNV
~~~~~~~~~~~~~~~~~~

ClassifyCNV applies evidence-based CNV classification rules.

It can produce:

-  evidence categories;

-  scored criteria;

-  final CNV classification;

-  supporting gene and region evidence.

Its installation directory remains local.

.. _3-22-2-intervar:

3.22.2 InterVar
~~~~~~~~~~~~~~~

InterVar supports ACMG-style small-variant interpretation.

It can provide:

-  ACMG evidence codes;

-  automated interpretation;

-  supporting database annotations.

InterVar is treated as an optional or manual interpretation source rather than the main automatic scoring engine.

.. _3-22-3-annotsv:

3.22.3 AnnotSV
~~~~~~~~~~~~~~

AnnotSV provides detailed structural-variant annotation.

It reports information such as:

-  overlapping genes;

-  transcripts;

-  cytobands;

-  dosage-sensitive regions;

-  known pathogenic CNVs;

-  population CNV overlap;

-  variant size;

-  annotation mode.

.. _3-23-results:

3.23 results/
-------------

The results/ directory stores outputs generated by the pipeline.

results/

├── README.md

├── cases/

└── other generated result directories

Complete result folders are excluded from GitHub because they can be large and may contain case-level data.

.. _3-23-1-typical-case-result-structure:

3.23.1 Typical case-result structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A case may produce:

results/cases/case_id/

├── intake/

├── prepared/

├── routed/

├── small_variants/

├── cnv/

├── repeat_expansions/

├── clinpgx/

├── ranking/

├── reports/

├── logs/

└── manifests/

**intake/**

Contains:

-  original intake report;

-  original checksums;

-  supplied metadata;

-  intake warnings.

**prepared/**

Contains:

-  harmonised input files;

-  corrected VCF files;

-  prepared metadata;

-  working copies.

**routed/**

Contains files separated by variant class.

**small_variants/**

Contains:

-  normalised VCF;

-  VEP output;

-  SnpEff output;

-  ClinVar output;

-  SpliceAI output;

-  phenotype and inheritance tables.

**cnv/**

Contains:

-  prepared CNV BED files;

-  AnnotSV output;

-  ClassifyCNV output;

-  ISV-CNV output;

-  CNV master candidate tables.

-  

   .. container::

      **repeat_expansions/**

Contains repeat-expansion detection and routing reports.

-  

   .. container::

      **clinpgx/**

Contains matched pharmacogenomic records and interpretation tables.

-  

   .. container::

      **ranking/**

Contains integrated candidate scores and ordered candidate tables.

-  

   .. container::

      **reports/**

Contains case completion and summary reports.

-  

   .. container::

      **logs/**

Contains standard output, error messages and execution logs.

-  

   .. container::

      **manifests/**

Contains resource versions, checksums and provenance records.

.. _3-24-validation:

3.24 validation/
----------------

The validation/ directory contains test cases, expected outcomes, audit information and validation scripts.

validation/

├── universal_pipeline_testing/

├── known_diagnoses/

└── final_audit_20260727/

.. _3-25-validation-universal-pipeline-testing:

3.25 validation/universal_pipeline_testing/
-------------------------------------------

This is the main universal-pipeline test collection.

validation/universal_pipeline_testing/

├── inputs/

│ ├── vcfs/

│ ├── hpo/

│ └── reference/

├── outputs/

├── manifests/

└── failed_runs/

.. _3-25-1-inputs-vcfs:

3.25.1 inputs/vcfs/
~~~~~~~~~~~~~~~~~~~

Contains the synthetic VCF files for Patients 01–13.

The cases were designed to test:

-  dominant inheritance;

-  recessive inheritance;

-  X-linked inheritance;

-  homozygous variants;

-  heterozygous variants;

-  pharmacogenomic variants;

-  repeat expansions;

-  different disease genes;

-  different VCF representations.

Patient 13 was prepared but intentionally not executed.

.. _3-25-2-inputs-hpo:

3.25.2 inputs/hpo/
~~~~~~~~~~~~~~~~~~

Contains patient-specific HPO files and related metadata.

Each HPO file contains phenotype identifiers assigned to a specific test case.

The pipeline uses exact filename matching to prevent incorrect case assignment.

.. _3-25-3-inputs-reference:

3.25.3 inputs/reference/
~~~~~~~~~~~~~~~~~~~~~~~~

Contains compact validation reference files such as:

-  

   .. container::

      sample_sheet.csv

-  

   .. container::

      drug_information_reference.csv

-  

   .. container::

      pgx_and_rare_disease_clinical_report.csv

**sample_sheet.csv**

Connects patient identifiers with:

-  VCF filenames;

-  phenotype files;

-  sex information;

-  expected disease;

-  expected pharmacogenomic result.

**drug_information_reference.csv**

Contains drug-related reference information used for validation of ClinPGx outputs.

**pgx_and_rare_disease_clinical_report.csv**

Stores expected disease and pharmacogenomic relationships for controlled testing.

.. _3-25-4-outputs:

3.25.4 outputs/
~~~~~~~~~~~~~~~

Contains the complete generated results from validation runs.

These outputs remain local and are excluded from GitHub.

They may include:

-  annotation tables;

-  candidate rankings;

-  ClinPGx results;

-  CNV reports;

-  repeat-expansion reports;

-  execution status;

-  reproducibility manifests.

.. _3-25-5-manifests:

3.25.5 manifests/
~~~~~~~~~~~~~~~~~

Contains validation provenance files.

Committed examples include:

-  

   .. container::

      input_sha256.tsv

-  

   .. container::

      vcf_preflight.tsv

**input_sha256.tsv**

Records checksums for the validation inputs.

**vcf_preflight.tsv**

Records whether each VCF passed structural validation.

Historical pre-correction manifests remain local and are excluded from GitHub.

.. _3-25-6-failed-runs:

3.25.6 failed_runs/
~~~~~~~~~~~~~~~~~~~

Stores failed validation executions for troubleshooting.

A failed run may contain:

-  error logs;

-  incomplete outputs;

-  copied input files;

-  pipeline status reports.

This directory is excluded from GitHub.

.. _3-26-validation-known-diagnoses:

3.26 validation/known_diagnoses/
--------------------------------

This directory stores expected results for controlled validation cases.

Examples include:

case_real_launcher_test.truth.tsv

real_case5_srr15174692.truth.tsv

These truth files allow the pipeline to compare:

-  expected gene;

-  expected variant;

-  expected disease;

-  observed top-ranked candidate;

-  pass or fail status.

The .gitkeep file ensures that the directory remains present even when it contains no additional files.

.. _3-27-validation-final-audit-20260727:

3.27 validation/final_audit_20260727/
-------------------------------------

This directory preserves the final project audit.

validation/final_audit_20260727/

├── FINAL_VALIDATION_STATUS.md

├── canonical_cases.tsv

├── canonical_final_outputs.sha256

├── key_resources.sha256

├── pipeline_source.sha256

└── scripts/

**FINAL_VALIDATION_STATUS.md**

Summarises the final validation outcome.

It records that:

-  Patients 01–12 were audited;

-  all audited cases passed;

-  Patient 03 was handled through repeat-expansion routing;

-  Patient 13 was not executed.

**canonical_cases.tsv**

Lists the selected canonical result directory and expected top result for each validated case.

**canonical_final_outputs.sha256**

Contains checksums of important final output files.

**key_resources.sha256**

Contains checksums of the principal resources used during validation.

**pipeline_source.sha256**

Contains checksums of the pipeline source files.

**scripts/audit_patients_01_12_final.py**

Performs the final automated audit of Patients 01–12.

It determines whether each case is:

-  

   .. container::

      CURRENT

-  

   .. container::

      LEGACY

-  

   .. container::

      ROUTED_REPEAT

and checks that the expected gene, variant, score and pharmacogenomic result are present.

.. _3-28-github-tracked-content-versus-local-only-content:

3.28 GitHub-tracked content versus local-only content
-----------------------------------------------------

The project intentionally separates reproducible source files from large runtime data.

+------------------------------------+---------------------------------+
| **Stored in GitHub**               | **Kept locally**                |
+====================================+=================================+
| Bash scripts                       | Built .sif containers           |
+------------------------------------+---------------------------------+
| Python scripts                     | GRCh38 FASTA                    |
+------------------------------------+---------------------------------+
| Container definition files         | VEP cache                       |
+------------------------------------+---------------------------------+
| Unit tests                         | SnpEff genome database          |
+------------------------------------+---------------------------------+
| Synthetic validation inputs        | Complete ClinVar VCF            |
+------------------------------------+---------------------------------+
| Compact ClinPGx resource           | AnnotSV databases               |
+------------------------------------+---------------------------------+
| Compact Gene2Phenotype files       | ClassifyCNV installation        |
+------------------------------------+---------------------------------+
| ClinGen CSV                        | InterVar installation           |
+------------------------------------+---------------------------------+
| HPO and MONDO manifests            | BAM and FASTQ files             |
+------------------------------------+---------------------------------+
| Final audit summaries              | Full result directories         |
+------------------------------------+---------------------------------+
| Checksums                          | Failed run directories          |
+------------------------------------+---------------------------------+
| README files                       | Temporary intermediate files    |
+------------------------------------+---------------------------------+

This structure keeps the repository reproducible without attempting to store large third-party databases.

.. _3-29-how-repository-files-will-be-used-in-the-documentation:

3.29 How repository files will be used in the documentation
-----------------------------------------------------------

Small commands will be written directly in the report.

Example:

.. code:: bash

   bcftools norm \
   -f resources/reference/hg38.fa \
   input.vcf \
   -o normalized.vcf

Large Bash and Python files will be explained in the report and linked to GitHub.

Example path:

pipeline/case_workflow/00_detect_and_split_variants.py

The report should explain:

-  what the script does;

-  what input it accepts;

-  what output it produces;

-  which tools or resources it requires;

-  where it occurs in the workflow.

The complete source will remain accessible through the GitHub link.

Large downloaded resources will not be linked as repository files. Instead, the report will provide:

-  official source;

-  version;

-  download command;

-  installation path;

-  verification command;

-  approximate storage requirement.

.. _3-30-recommended-directory-permissions:

3.30 Recommended directory permissions
--------------------------------------

Pipeline scripts should be executable.

.. code:: bash

   chmod +x pipeline/*.sh
   chmod +x pipeline/case_workflow/*.sh
   chmod +x pipeline/case_workflow/*.py
   chmod +x pipeline/tests/*.sh

Resource files should generally remain read-only during routine analysis.

The pipeline should write only to:

*results/*

*validation/universal_pipeline_testing/outputs/*

*validation/universal_pipeline_testing/failed_runs/*

temporary working directories

Original input and official resource files should not be modified during case execution.

.. _3-31-directory-design-principles:

3.31 Directory design principles
--------------------------------

The project structure follows five main principles.

**Separation of code and data**

Pipeline scripts are stored separately from input, resources and results.

**Separation of official and validation resources**

Synthetic validation additions cannot alter official production resources.

**Separation of input and output**

Original case files remain unchanged, while generated files are written to separate directories.

**Separation by variant class**

Small variants, CNVs and repeat expansions are processed through different branches.

**Reproducibility**

Manifests, version files and checksums record the exact inputs, resources and scripts used.

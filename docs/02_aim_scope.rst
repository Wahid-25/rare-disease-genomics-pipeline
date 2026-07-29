.. _2-project-aim-objectives-scope-and-development-requirements:

2. Project Aim, Objectives, Scope and Development Requirements
==============================================================


.. _2-1-project-aim:

2.1 Project aim
---------------

The main aim of this project was to develop a reproducible and modular genomic-analysis pipeline capable of processing rare-disease cases containing different classes of genomic variation. The pipeline was designed to accept a case-level VCF file, identify the variant types present, route each supported class through an appropriate analytical workflow and produce structured candidate-prioritisation outputs.

The system integrates rare-disease analysis with pharmacogenomic interpretation so that disease-associated variants and clinically relevant drug-response variants can be evaluated within the same case. It also incorporates phenotype information, gene–disease relationships, inheritance patterns, sex and ploidy information, clinical variant classifications and selected population or functional evidence.

The pipeline is intended as a research and educational framework for variant annotation and prioritization. It is not a replacement for clinical laboratory validation, specialist review or medical decision-making.

.. _2-2-main-objectives:

2.2 Main objectives
-------------------

The project was developed to achieve the following objectives.

.. _2-2-1-accept-different-valid-vcf-inputs:

2.2.1 Accept different valid VCF inputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The workflow should accept VCF files produced by different variant callers or prepared from different sources, provided that the records are structurally valid and compatible with the GRCh38 reference genome.

The pipeline therefore performs pre-analysis checks for:

-  VCF header completeness;

-  chromosome naming conventions;

-  reference and alternate allele structure;

-  sample genotype fields;

-  symbolic structural-variant alleles;

-  repeat-expansion records;

-  malformed INFO entries;

-  unsupported variant types;

-  genome-build consistency.

The original input file is preserved, while corrected or normalized derivatives are generated separately.

.. _2-2-2-detect-and-route-different-variant-classes:

2.2.2 Detect and route different variant classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A universal workflow should not treat every genomic record as an ordinary small variant. The pipeline first identifies the variant classes present and routes them accordingly.

Supported analytical branches include:

-  single-nucleotide variants;

-  small insertions and deletions;

-  copy-number deletions;

-  copy-number duplications;

-  selected symbolic structural variants;

-  repeat-expansion records;

-  pharmacogenomic variants.

Variants that cannot be fully interpreted are still detected and reported. They are not silently discarded or incorrectly ranked alongside supported variants.

.. _2-2-3-annotate-small-variants:

2.2.3 Annotate small variants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Small variants are processed through a sequence of normalization, functional annotation and clinical annotation stages.

The workflow is designed to incorporate information from:

-  bcftools;

-  Ensembl Variant Effect Predictor;

-  SnpEff;

-  ClinVar;

-  ClinGen;

-  SpliceAI;

-  Gene2Phenotype;

-  Human Phenotype Ontology;

-  MONDO;

-  local ClinPGx reference data.

The resulting annotations are converted into tabular formats that can be merged and scored.

.. _2-2-4-analyse-copy-number-variants-separately:

2.2.4 Analyse copy-number variants separately
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copy-number variants require evidence that differs from ordinary SNV and indel interpretation. The CNV branch prepares deletion and duplication records for tools such as:

-  AnnotSV;

-  ClassifyCNV;

-  ISV-CNV;

-  ClinGen dosage-sensitivity resources;

-  phenotype-based CNV prioritization.

The pipeline therefore creates CNV-specific intermediate and final tables instead of forcing CNVs into the small-variant scoring model.

.. _2-2-5-detect-repeat-expansions:

2.2.5 Detect repeat expansions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Repeat expansions may be represented in a VCF using symbolic alleles and repeat-specific INFO fields. These records cannot be reliably interpreted using the same consequence and allele-frequency rules as ordinary variants.

The pipeline detects repeat-expansion records, extracts available information such as:

-  repeat locus;

-  repeat motif;

-  observed repeat count;

-  pathogenic threshold;

-  genotype;

-  transcript or protein notation;

-  database identifier.

The record is written to a separate report and excluded from ordinary small-variant ranking. Specialized repeat-expansion software or manual review is still required for definitive interpretation.

.. _2-2-6-integrate-phenotype-information:

2.2.6 Integrate phenotype information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Patient phenotypes are encoded using Human Phenotype Ontology identifiers.

The pipeline uses HPO terms to:

-  connect the patient’s clinical features with candidate genes;

-  expand candidate disease lists;

-  compare phenotype compatibility across disease models;

-  calculate phenotype-support scores;

-  provide evidence for ranking variants and CNVs.

Exact filename matching is used so that the phenotype file for one patient cannot accidentally be assigned to another patient with a similar numeric identifier.

.. _2-2-7-evaluate-inheritance-patterns:

2.2.7 Evaluate inheritance patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A disease-associated variant should be evaluated in the context of the expected inheritance model.

The pipeline includes support for:

-  autosomal dominant inheritance;

-  autosomal recessive inheritance;

-  X-linked inheritance;

-  mitochondrial inheritance;

-  homozygous variants;

-  heterozygous variants;

-  hemizygous variants;

-  possible compound-heterozygous pairs;

-  phase-confirmed compound-heterozygous pairs.

Inheritance assessment uses genotype, chromosome, patient sex, ploidy and gene–disease inheritance information.

.. _2-2-8-evaluate-sex-and-ploidy:

2.2.8 Evaluate sex and ploidy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sex-chromosome variants cannot be interpreted correctly without considering biological sex and chromosome ploidy.

The pipeline includes preflight checks to:

-  resolve or validate reported sex;

-  identify variants on chromosomes X and Y;

-  distinguish diploid and haploid expectations;

-  support hemizygous interpretation;

-  prevent inappropriate autosomal genotype assumptions;

-  handle mitochondrial genotypes separately.

This is particularly important for X-linked disease models.

.. _2-2-9-identify-compound-heterozygous-candidates:

2.2.9 Identify compound-heterozygous candidates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For recessive disorders, two heterozygous variants in the same gene may form a disease-causing pair.

The pipeline distinguishes between:

-  confirmed trans variants;

-  possible unphased compound-heterozygous variants;

-  variants confirmed to be in cis;

-  unrelated heterozygous variants;

-  homozygous variants that should not be counted twice.

A pair is considered phase-confirmed only when the records share compatible phase information and occur on opposite haplotypes. Unphased pairs are reported as possible rather than confirmed.

.. _2-2-10-add-pharmacogenomic-interpretation:

2.2.10 Add pharmacogenomic interpretation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ClinPGx branch identifies variants associated with altered drug metabolism or drug response.

Matching is allele-aware and may use:

-  rsID;

-  chromosome;

-  genomic position;

-  reference allele;

-  alternate allele;

-  genotype;

-  star-allele interpretation;

-  predicted metaboliser phenotype;

-  associated drug information.

This prevents a record from being classified as a ClinPGx match solely because it shares an rsID while carrying a different allele.

.. _2-2-11-prioritize-candidate-variants:

2.2.11 Prioritize candidate variants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The pipeline combines multiple evidence categories into a structured ranking model.

Evidence considered may include:

-  functional consequence;

-  ClinVar significance;

-  review status;

-  disease association;

-  inheritance compatibility;

-  zygosity;

-  phenotype similarity;

-  gene–disease validity;

-  splice evidence;

-  compound-heterozygous evidence;

-  ClinGen dosage or gene information;

-  pharmacogenomic relevance;

-  variant-class compatibility.

The final score is intended for prioritisation, not automatic pathogenicity classification.

.. _2-2-12-preserve-provenance-and-reproducibility:

2.2.12 Preserve provenance and reproducibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every case should produce sufficient metadata to determine:

-  which input file was analyzed;

-  which pipeline scripts were used;

-  which resources were active;

-  which versions were used;

-  which outputs were generated;

-  whether the case completed successfully;

-  whether unsupported records were detected;

-  whether validation resources were enabled.

Checksums and manifests are used to preserve reproducibility.

.. _2-3-project-scope:

2.3 Project scope
-----------------

.. _2-3-1-included-within-the-project:

2.3.1 Included within the project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The project includes:

-  GRCh38-based analysis;

-  VCF structural validation;

-  chromosome harmonization;

-  variant normalization;

-  SNV and indel annotation;

-  disease mapping;

-  HPO-based phenotype prioritization;

-  inheritance evaluation;

-  sex and ploidy checks;

-  compound-heterozygous aggregation;

-  CNV preparation and annotation;

-  repeat-expansion routing;

-  ClinPGx matching;

-  universal candidate scoring;

-  generation of master candidate tables;

-  reproducibility manifests;

-  synthetic validation cases;

-  production and validation resource modes;

-  command-line execution under WSL Ubuntu;

-  container-based tool execution using Apptainer.

.. _2-3-2-partially-supported-areas:

2.3.2 Partially supported areas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some variant classes can be detected but require external specialised interpretation.

These include:

-  repeat expansions;

-  complex structural variants;

-  balanced translocations;

-  inversions;

-  mobile-element insertions;

-  low-level mosaic variants;

-  mitochondrial heteroplasmy;

-  complex pharmacogenomic haplotypes;

-  copy-number changes in highly homologous genes;

-  variants requiring family segregation analysis.

The pipeline reports these limitations rather than presenting unsupported conclusions.

.. _2-3-3-outside-the-current-scope:

2.3.3 Outside the current scope
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current project does not provide a complete clinical-grade implementation of:

-  raw sequencing quality control;

-  adapter trimming;

-  complete FASTQ-to-VCF processing for every sequencing platform;

-  short tandem repeat calling directly from BAM or FASTQ files;

-  de novo assembly;

-  long-read variant calling;

-  tumour–normal somatic analysis;

-  RNA-sequencing interpretation;

-  methylation analysis;

-  formal ACMG classification for every candidate;

-  automated diagnostic reporting;

-  clinical confirmation by Sanger sequencing;

-  family segregation testing;

-  direct treatment recommendations.

Some experimental FASTQ download and alignment scripts are present, but the principal validated workflow begins from a prepared VCF.

.. _2-4-intended-users:

2.4 Intended users
------------------

The project is intended for:

-  bioinformatics students;

-  genomics researchers;

-  computational biology laboratories;

-  developers learning rare-disease pipeline design;

-  users evaluating synthetic or de-identified genomic cases;

-  researchers who need a modular framework for extending variant-prioritisation methods.

Users should have sufficient knowledge to distinguish bioinformatic prioritisation from clinical diagnosis.

.. _2-5-knowledge-required-to-reproduce-the-project:

2.5 Knowledge required to reproduce the project
-----------------------------------------------

A person developing the same project should understand the following areas.

.. _2-5-1-genetics-and-genomics:

2.5.1 Genetics and genomics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The developer should understand:

-  DNA, genes, transcripts and proteins;

-  chromosomes and genomic coordinates;

-  GRCh37 and GRCh38 genome builds;

-  reference and alternate alleles;

-  coding and non-coding variants;

-  SNVs, insertions, deletions and indels;

-  structural variants;

-  copy-number variants;

-  repeat expansions;

-  zygosity;

-  penetrance;

-  variable expressivity;

-  mosaicism;

-  pathogenicity;

-  inheritance patterns;

-  genotype–phenotype relationships.

.. _2-5-2-variant-nomenclature:

2.5.2 Variant nomenclature
~~~~~~~~~~~~~~~~~~~~~~~~~~

The developer should recognise:

-  chromosome-position-reference-alternate notation;

-  rsIDs;

-  HGVS genomic notation;

-  HGVS coding notation;

-  HGVS protein notation;

-  transcript identifiers;

-  MANE transcripts;

-  canonical transcripts;

-  symbolic alleles such as <DEL> and <DUP>;

-  genotype formats such as ``0/1``, ``1/1``, ``0|1`` and ``1|0``.

.. _2-5-3-vcf-structure:

2.5.3 VCF structure
~~~~~~~~~~~~~~~~~~~

A VCF file contains:

-  metadata lines beginning with ##;

-  a column header beginning with #CHROM;

-  chromosome;

-  position;

-  identifier;

-  reference allele;

-  alternate allele;

-  quality;

-  filter;

-  INFO;

-  FORMAT;

-  sample genotype columns.

The developer should understand that VCF validity depends on both syntax and biological representation.

A structurally valid record may still be unsuitable for analysis when:

-  the genome build is incorrect;

-  the reference allele does not match the FASTA;

-  chromosome prefixes differ;

-  a symbolic allele lacks required INFO fields;

-  coordinates use inconsistent conventions;

-  the genotype is incompatible with chromosome ploidy.

.. _2-5-4-command-line-linux:

2.5.4 Command-line Linux
~~~~~~~~~~~~~~~~~~~~~~~~

The project is operated primarily through Bash.

Required skills include:

-  directory navigation;

-  file permissions;

-  environment variables;

-  pipes and redirection;

-  loops and conditionals;

-  text processing with grep, awk, sed, cut and sort;

-  checksum generation;

-  compressed-file handling;

-  script execution;

-  exit-code interpretation;

-  process monitoring;

-  disk-space monitoring.

.. _2-5-5-python:

2.5.5 Python
~~~~~~~~~~~~

Python is used for:

-  parsing VCF-derived tables;

-  reading CSV and TSV files;

-  disease mapping;

-  phenotype scoring;

-  inheritance modelling;

-  ClinPGx matching;

-  compound-heterozygous analysis;

-  candidate scoring;

-  validation;

-  report generation.

The developer should understand:

-  variables and data types;

-  functions;

-  modules;

-  classes where required;

-  dictionaries, lists and sets;

-  file handling;

-  CSV and TSV parsing;

-  command-line arguments;

-  exception handling;

-  unit testing;

-  regular expressions;

-  path handling;

-  deterministic output generation.

.. _2-5-6-bash-scripting:

2.5.6 Bash scripting
~~~~~~~~~~~~~~~~~~~~

Bash scripts coordinate the complete workflow.

The developer should understand:

-  shebang lines;

-  executable permissions;

-  positional arguments;

-  quoted variables;

-  arrays;

-  set -Eeuo pipefail;

-  functions;

-  file-existence checks;

-  pipeline exit status;

-  temporary directories;

-  logging;

-  conditional tool execution;

-  environment isolation.

.. _2-5-7-containers:

2.5.7 Containers
~~~~~~~~~~~~~~~~

Apptainer containers are used to isolate software dependencies.

The developer should understand:

-  container definition files;

-  image building;

-  bind mounting;

-  read-only and writable paths;

-  container execution;

-  host-to-container path mapping;

-  environment-variable forwarding;

-  version pinning;

-  container verification.

The repository contains selected container definition files, while built .sif images remain local because they are large binary files.

.. _2-5-8-databases-and-annotation-resources:

2.5.8 Databases and annotation resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The developer should understand the purpose of each major resource.

+-----------------+---------------------------------------------------------+
| **Resource**    | **Main purpose**                                        |
+=================+=========================================================+
| GRCh38 FASTA    | Reference sequence for coordinate and allele validation |
+-----------------+---------------------------------------------------------+
| VEP cache       | Offline functional and transcript annotation            |
+-----------------+---------------------------------------------------------+
| SnpEff database | Variant consequence annotation                          |
+-----------------+---------------------------------------------------------+
| ClinVar         | Clinical significance and disease assertions            |
+-----------------+---------------------------------------------------------+
| ClinGen         | Gene validity and dosage-sensitivity evidence           |
+-----------------+---------------------------------------------------------+
| Gene2Phenotype  | Gene–disease and inheritance relationships              |
+-----------------+---------------------------------------------------------+
| HPO             | Standardised patient phenotype representation           |
+-----------------+---------------------------------------------------------+
| MONDO           | Disease terminology and identifier harmonisation        |
+-----------------+---------------------------------------------------------+
| SpliceAI        | Prediction of splice-altering effects                   |
+-----------------+---------------------------------------------------------+
| ClinPGx         | Pharmacogenomic variant and drug-response information   |
+-----------------+---------------------------------------------------------+
| AnnotSV         | Structural-variant and CNV annotation                   |
+-----------------+---------------------------------------------------------+
| ClassifyCNV     | CNV classification using evidence-based scoring         |
+-----------------+---------------------------------------------------------+
| ISV-CNV         | Machine-learning-assisted CNV prioritisation            |
+-----------------+---------------------------------------------------------+

.. _2-6-software-environment:

2.6 Software environment
------------------------

The validated project environment uses:

-  

   .. container::

      Operating environment: WSL 2 Ubuntu

-  

   .. container::

      Genome build: GRCh38

-  

   .. container::

      Primary shell: Bash

-  

   .. container::

      Primary programming language: Python

-  

   .. container::

      Container platform: Apptainer

-  

   .. container::

      Version-control platform: Git and GitHub

The local project root is:

.. code:: bash

   ~/rare_disease_project

Inside containers, the project may be bound to:

.. code:: bash

   /project

Chromosome names are standardised using the chr prefix:

-  

   .. container::

      chr1

-  

   .. container::

      chr2

-  

   .. container::

      chrX

-  

   .. container::

      chrY

-  

   .. container::

      chrM

.. _2-7-minimum-computational-requirements:

2.7 Minimum computational requirements
--------------------------------------

The exact requirements depend on which databases and containers are installed.

A practical environment should provide:

-  a 64-bit Linux system or WSL 2;

-  multiple CPU cores;

-  at least 16 GB RAM for routine annotation;

-  substantially more RAM for some CNV or resource-building tasks;

-  approximately 150–250 GB of free storage for reference resources, caches, containers, intermediate files and validation outputs;

-  stable internet access during initial downloads;

-  sufficient temporary storage;

-  GitHub access for source-code retrieval.

The project itself is small, but genomic resources are large. The VEP cache, reference FASTA, tool databases and result directories account for most of the storage.

.. _2-8-expected-inputs:

2.8 Expected inputs
-------------------

A case may require the following inputs.

Required input

A structurally valid GRCh38 VCF file

**Optional inputs**

-  

   .. container::

      Patient identifier

-  

   .. container::

      Case identifier

-  

   .. container::

      Reported biological sex

-  

   .. container::

      HPO phenotype file

-  

   .. container::

      Sample sheet

-  

   .. container::

      Known diagnosis for validation

-  

   .. container::

      Pharmacogenomic reference data

-  

   .. container::

      CNV-specific files

-  

   .. container::

      Clinical metadata

An HPO file normally contains one ontology identifier per line:

-  

   .. container::

      HP:0001250

-  

   .. container::

      HP:0001263

-  

   .. container::

      HP:0004322

A sample sheet may connect:

-  patient identifier;

-  VCF filename;

-  sex;

-  phenotype filename;

-  expected analysis mode;

-  known diagnosis;

-  pharmacogenomic expectations.

.. _2-9-expected-outputs:

2.9 Expected outputs
--------------------

Depending on the records present, the pipeline may generate:

-  input validation reports;

-  chromosome-harmonised VCFs;

-  normalised VCFs;

-  routed small-variant VCFs;

-  routed CNV files;

-  repeat-expansion reports;

-  VEP-annotated files;

-  SnpEff-annotated files;

-  ClinVar-enriched tables;

-  Gene2Phenotype disease mappings;

-  phenotype-scored tables;

-  inheritance-scored tables;

-  compound-heterozygous evidence tables;

-  ClinPGx match tables;

-  CNV annotation tables;

-  universal master candidate tables;

-  ranked candidate tables;

-  case completion summaries;

-  reproducibility manifests;

-  checksums;

-  validation reports.

Not every case produces every output. Outputs depend on the variant classes and metadata available.

.. _2-10-production-and-validation-modes:

2.10 Production and validation modes
------------------------------------

The project separates official resources from synthetic validation additions.

**Production mode**

Production mode uses official resources only.

It must not include manually inserted disease relationships created solely to make a synthetic case pass.

**Validation mode**

Validation mode may combine official resources with controlled local validation entries.

This allows test cases to evaluate pipeline behaviour without modifying official resource files.

The separation prevents:

-  contamination of production analysis;

-  artificial disease prioritisation;

-  accidental reuse of synthetic relationships;

-  misleading results in future cases.

.. _2-11-universal-design-principles:

2.11 Universal design principles
--------------------------------

The project follows several core principles.

-  

   .. container::

      **Preserve original inputs**

Original VCFs are not overwritten. Corrected or normalised files are created as derivatives.

-  

   .. container::

      **Fail visibly**

Malformed files, missing resources and unsupported records should generate explicit messages.

-  

   .. container::

      **Separate detection from interpretation**

The pipeline may detect a variant class without claiming that it can fully interpret it.

-  

   .. container::

      **Use allele-aware matching**

A genomic position or rsID alone is insufficient when the reference and alternate alleles do not match.

-  

   .. container::

      **Keep production and validation resources separate**

Synthetic test relationships must not influence real analyses.

-  

   .. container::

      **Preserve provenance**

Inputs, resources, scripts and outputs should be traceable using manifests and checksums.

-  

   .. container::

      **Avoid automatic diagnosis**

The final ranking is evidence prioritisation, not a definitive medical diagnosis.

.. _2-12-development-workflow:

2.12 Development workflow
-------------------------

A developer reproducing the project should follow this order:

1. Prepare the Linux or WSL environment.

2. Install Git, Python, bcftools, samtools and Apptainer.

3. Clone the GitHub repository.

4. Build or obtain the required containers.

5. Download the GRCh38 reference genome.

6. Download and prepare annotation resources.

7. Verify all resource paths and versions.

8. Run structural VCF preflight tests.

9. Run unit tests for inheritance, ClinPGx and phenotype matching.

10. Execute the validation suite.

11. Inspect canonical outputs and manifests.

12. Test a new case in validation mode.

13. Test a new case in production mode.

14. Review unsupported-variant reports.

15. Document any resource or source-code changes.

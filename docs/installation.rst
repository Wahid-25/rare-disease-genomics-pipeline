Installation and environment
============================

The validated environment uses WSL 2 Ubuntu, Bash, Python, Git, GitHub CLI,
Apptainer and GRCh38-compatible genomics tools.

Base environment
----------------

Install and verify the core command-line environment before downloading large
resources. The project report documents the complete commands for:

* WSL 2 and Ubuntu setup
* Git and GitHub CLI authentication
* Python virtual environment creation
* bcftools, samtools, bgzip, tabix and bedtools
* Apptainer installation and cache configuration

Containers
----------

Container definition files belong in ``containers/``. Built ``.sif`` images are
local runtime artefacts and should remain excluded from GitHub.

Primary environments include:

* core tools
* VEP
* SnpEff
* SpliceAI
* ISV-CNV
* optional read processing

Reference and annotation resources
----------------------------------

The complete runtime requires local copies of:

* GRCh38 FASTA and index
* VEP release 115 GRCh38 cache
* SnpEff GRCh38 database
* ClinVar GRCh38 VCF and index
* ClinGen dosage data
* Gene2Phenotype production and validation resources
* HPO and MONDO resources
* curated local ClinPGx reference
* AnnotSV human annotations
* ClassifyCNV resources

Resource files must be versioned or checksummed. Large third-party resources
must not be committed to GitHub.

Readiness checks
----------------

Before case execution, verify that required tools and resources exist and run the
project's syntax and regression tests. See :doc:`validation`.

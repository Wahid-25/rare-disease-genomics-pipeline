.. _1-introduction:

1. Introduction
===============


Rare-disease genomic analysis requires the integration of several types of evidence rather than reliance on a single annotation source. A potentially relevant variant must be evaluated in relation to its genomic consequence, population frequency, clinical classification, disease association, inheritance pattern and compatibility with the patient’s phenotype. Structural variants, repeat expansions and pharmacogenomic variants may also require separate analytical pathways because they cannot always be interpreted using the same methods as conventional single-nucleotide variants and small insertions or deletions.

This project developed a reproducible GRCh38-based pipeline for the analysis and prioritisation of variants in rare-disease cases. The workflow combines variant preprocessing, functional annotation, clinical database integration, gene–disease mapping, phenotype-based prioritisation, inheritance assessment, copy-number variant analysis, repeat-expansion detection and pharmacogenomic matching. The pipeline was designed to accept different valid VCF representations while preserving the original input and creating structured intermediate and final outputs.

The workflow also separates production resources from validation resources to prevent synthetic test data from altering official gene–disease associations. Additional safeguards were implemented for chromosome naming, sex and ploidy evaluation, compound-heterozygous interpretation, allele-aware ClinPGx matching and the routing of unsupported variant types. These features allow the pipeline to identify variants that can be analysed directly while clearly reporting those that require specialised external interpretation.

The final workflow was evaluated using twelve synthetic patient cases containing a range of inheritance patterns, variant classes and pharmacogenomic examples. Patient 03 contained an HTT CAG repeat expansion and was therefore detected and routed to a separate repeat-expansion report rather than being treated as an ordinary small variant.

The purpose of this report is to document the complete pipeline architecture, installation procedure, required resources, analytical stages, validation strategy and interpretation of the generated outputs. Large scripts and selected input files are referenced through the project’s GitHub repository, while essential installation and resource-download commands are included directly in the document to support reproducibility.

|image1|

**Figure 1. Overview of the Universal Rare-Disease and Pharmacogenomics Analysis Pipeline.** The workflow accepts GRCh38 small-variant and CNV inputs, performs structural preflight and annotation, integrates phenotype and inheritance evidence, evaluates selected pharmacogenomic variants, and produces ranked, validated and reproducible outputs.

.. _1-1-project-repository:

1.1 Project repository
----------------------

The source code, container definition files, selected synthetic inputs, compact reference resources, validation manifests and final audit summaries are maintained in the following private GitHub repository:

https://github.com/Wahid-25/rare-disease-genomics-pipeline

Long Bash and Python scripts will be linked from the repository instead of being reproduced fully in the report. Small commands required to understand or reproduce an individual step will be shown directly in the relevant section.

.. |image1| image:: _static/images/pipeline_overview.png
   :width: 6.5in
   :height: 3.65833in

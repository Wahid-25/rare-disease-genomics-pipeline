.. meta::
   :description: Complete documentation for the Development and Validation of a Universal Rare-Disease and Pharmacogenomics Analysis Pipeline.

.. raw:: html

   <section class="genosphere-cover">
     <p class="cover-kicker">GENOMICS PIPELINE</p>
     <img class="cover-logo" src="_static/images/genosphere_logo.png" alt="GenoSphere project logo">
     <h1>Development and Validation of a Universal Rare-Disease and Pharmacogenomics Analysis Pipeline</h1>
     <p class="cover-subtitle">A reproducible GRCh38 workflow for rare-disease prioritisation, CNV analysis, repeat-expansion routing, inheritance modelling and selected pharmacogenomic interpretation.</p>
     <div class="cover-actions">
       <a class="primary-button" href="01_introduction.html">Read the complete documentation</a>
       <a class="secondary-button" href="18_new_case.html">Process a new case</a>
     </div>
   </section>

.. image:: _static/images/pipeline_overview.png
   :alt: Overview of the universal rare-disease and pharmacogenomics analysis pipeline
   :align: center
   :class: pipeline-overview

Project overview
================

The pipeline accepts GRCh38 case-level genomic data, preserves original inputs, performs structural preflight, routes supported variant classes to appropriate analytical branches and produces auditable candidate-prioritisation outputs.

It integrates small-variant annotation, copy-number analysis, repeat-expansion reporting, gene–disease mapping, HPO phenotype evidence, inheritance and ploidy modelling, compound-heterozygous assessment and exact allele-aware pharmacogenomic matching.

.. raw:: html

   <div class="feature-grid">
     <div class="feature-card"><h3>Universal intake</h3><p>Validates VCF structure, sample context, genome build, phenotype data and analysis mode.</p></div>
     <div class="feature-card"><h3>Variant-class routing</h3><p>Separates SNVs/indels, DEL/DUP CNVs, repeat expansions and unsupported structural records.</p></div>
     <div class="feature-card"><h3>Integrated evidence</h3><p>Combines VEP, SnpEff, ClinVar, SpliceAI, G2P, HPO, MONDO and ClinGen evidence.</p></div>
     <div class="feature-card"><h3>Inheritance-aware ranking</h3><p>Supports sex/ploidy evaluation and phased, cis or possible compound-heterozygous evidence.</p></div>
     <div class="feature-card"><h3>Allele-aware PGx</h3><p>Requires exact chromosome, position, REF and ALT matching before local PGx interpretation.</p></div>
     <div class="feature-card"><h3>Auditable outputs</h3><p>Preserves master tables, logs, manifests, checksums, validation evidence and canonical audits.</p></div>
   </div>

Validation status
=================

.. raw:: html

   <div class="status-note"><strong>Validated project state:</strong> Thirteen prepared synthetic VCFs passed structural preflight. Twelve cases were included in the final behavioural audit, and all twelve met their canonical candidate or routing expectations. Patient 13 was intentionally not processed through the complete workflow.</div>

Complete documentation
======================

The pages below contain the complete 23-section manuscript rather than the earlier short summary site.

.. toctree::
   :maxdepth: 3
   :caption: Foundations

   01_introduction
   02_aim_scope
   03_project_structure

.. toctree::
   :maxdepth: 3
   :caption: Installation and resources

   04_software_installation
   05_reference_resources
   06_specialised_tools

.. toctree::
   :maxdepth: 3
   :caption: Inputs and analytical workflow

   07_input_preflight
   08_architecture
   09_small_variants
   10_disease_prioritisation
   11_inheritance
   12_pharmacogenomics
   13_cnv_analysis
   14_repeat_structural
   15_scoring
   16_outputs

.. toctree::
   :maxdepth: 3
   :caption: Validation and operation

   17_validation
   18_new_case
   19_troubleshooting

.. toctree::
   :maxdepth: 3
   :caption: Governance, reporting and conclusion

   20_reproducibility
   21_reporting
   22_limitations
   23_conclusion
   glossary
   references

Clinical and privacy notice
===========================

.. warning::

   The workflow produces computational candidate-prioritisation results. It does not independently establish a diagnosis, confirm a variant or recommend a medication change. Real genomic and phenotype data must remain protected and must not be committed to a public repository.

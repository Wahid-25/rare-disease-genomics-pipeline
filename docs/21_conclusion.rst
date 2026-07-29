21. Conclusion and Final Project Summary
========================================

This project successfully developed and validated a reproducible genomic-analysis workflow for rare-disease variant prioritisation and pharmacogenomic interpretation using GRCh38-compatible inputs. The workflow integrates small-variant annotation, phenotype matching, inheritance assessment, compound-heterozygous evaluation, copy-number analysis, repeat-expansion review, pharmacogenomic matching, candidate ranking and automatic clinical-report preparation within one organised project structure.

The pipeline was designed as a universal framework rather than as a collection of disease-specific scripts. The same workflow can therefore be applied to different rare-disease cases, provided that the input VCF, phenotype file and required resources are correctly prepared.

21.1 Project Objectives Achieved
--------------------------------

The main objectives achieved during the project include:

#. Construction of a reproducible GRCh38-based analysis environment.
#. Organisation of tools, containers, reference files, input cases, pipeline scripts and results into a consistent directory structure.
#. Implementation of structural and content-based VCF preflight checks.
#. Normalisation and annotation of small variants.
#. Integration of clinical, population, transcript and splice-related annotations.
#. Use of disease–gene and phenotype evidence for candidate prioritisation.
#. Development of inheritance-aware interpretation.
#. Support for autosomal, X-linked and mitochondrial contexts.
#. Implementation of compound-heterozygous candidate aggregation.
#. Separation of confirmed phased-in-trans pairs from unphased possible pairs.
#. Integration of copy-number and structural-variant analysis.
#. Inclusion of repeat-expansion findings when suitable input data are available.
#. Incorporation of allele-aware local pharmacogenomic matching.
#. Generation of final master candidate-ranking tables.
#. Creation of pipeline summaries, provenance records and validation outputs.
#. Development of an automatic clinical-report JSON workflow.
#. Creation of a local browser-based report builder.
#. Protection of patient-specific metadata and generated reports from public version control.
#. Development of regression tests and end-to-end validation procedures.
#. Publication of the reusable source code and documentation through version-controlled project files.

21.2 Final Pipeline Architecture
--------------------------------

The completed workflow follows the general sequence below:

.. code-block:: text

   Case input
   ↓
   VCF and phenotype staging
   ↓
   Structural preflight
   ↓
   Reference-build and allele validation
   ↓
   Variant normalisation
   ↓
   Functional and clinical annotation
   ↓
   Disease–gene association
   ↓
   Phenotype matching
   ↓
   Inheritance and ploidy assessment
   ↓
   Compound-heterozygous evaluation
   ↓
   CNV, structural and repeat review
   ↓
   Pharmacogenomic matching
   ↓
   Candidate scoring and ranking
   ↓
   Master candidate table
   ↓
   Pipeline summary and provenance
   ↓
   Automatic clinical-report JSON
   ↓
   Local report population
   ↓
   Analyst review and PDF or reviewed-JSON export

Each stage produces traceable output that can be inspected independently. This modular design makes troubleshooting easier and allows individual parts of the workflow to be updated without rebuilding the entire project.

21.3 Universal Case Processing
------------------------------

A major outcome of the project is the transition from disease-specific processing to a universal case workflow.

The main case command follows the pattern:

.. code-block:: text

   cd ~/rare_disease_project

.. code-block:: text

   bash \
   pipeline/run_case_pipeline.sh \
   <case_id> \
   <input_vcf> \
   <phenotype_file> \
   --mode <production_or_validation>

The pipeline does not require the disease name to be hard-coded into the analysis logic. Instead, disease relevance is inferred from:

- annotated variants;
- disease–gene associations;
- phenotype terms;
- inheritance compatibility;
- genotype and ploidy;
- population frequency;
- clinical significance;
- predicted molecular consequence;
- structural, repeat and pharmacogenomic evidence.

This design allows the same workflow to analyse cases involving different genes, diseases and variant classes.

21.4 Production and Validation Modes
------------------------------------

The project distinguishes between production and validation resources.

Validation mode is used for:

- synthetic cases;
- controlled testing;
- demonstration datasets;
- regression testing;
- resource-isolated development.

Production mode is intended for real analysis using the approved production resource set.

This separation prevents validation-only records from being unintentionally treated as production evidence. The analysis mode should be recorded in the case summary and report provenance.

A validation result should never be presented as a clinical diagnosis solely because the pipeline completed successfully.

21.5 Small-Variant Analysis
---------------------------

The small-variant workflow includes:

- input verification;
- chromosome-name checking;
- reference-allele validation;
- normalisation;
- transcript consequence annotation;
- clinical-database matching;
- population-frequency assessment;
- splice-effect evaluation;
- gene and disease mapping;
- phenotype and inheritance assessment.

The workflow supports single-nucleotide variants and small insertions or deletions represented in VCF format.

Transcript selection remains important because the same genomic variant may have different HGVS descriptions or molecular consequences on different transcripts.

The final interpretation should therefore confirm:

- genomic coordinates;
- reference and alternate alleles;
- preferred transcript;
- coding and protein HGVS;
- genotype;
- clinical classification;
- disease association;
- inheritance pattern.

21.6 Inheritance and Ploidy Interpretation
------------------------------------------

Inheritance compatibility was incorporated directly into candidate prioritisation.

The workflow evaluates information such as:

- autosomal-dominant inheritance;
- autosomal-recessive inheritance;
- X-linked inheritance;
- mitochondrial inheritance;
- homozygous and heterozygous states;
- sex-chromosome ploidy;
- patient sex when available;
- phased and unphased variant relationships.

This reduces the likelihood of prioritising a variant whose genotype is inconsistent with the expected disease mechanism.

However, inheritance interpretation remains dependent on the available case information. Missing patient sex, parental genotypes, pedigree data or phase information may limit the strength of the conclusion.

21.7 Compound-Heterozygous Evaluation
-------------------------------------

The project includes a dedicated compound-heterozygous aggregation workflow.

It distinguishes:

- phased variants on opposite haplotypes;
- unphased variants that may be in trans;
- variants without sufficient phase evidence;
- homozygous variants that should not be double-counted as compound heterozygous.

A pair is treated as phased in trans only when compatible shared phase information demonstrates opposite haplotypes.

Unphased pairs are retained as possible candidates, but their phase must not be overstated in the report.

Parental or family testing may still be required to determine whether two variants occur in trans.

21.8 Copy-Number and Structural-Variant Analysis
------------------------------------------------

The project supports copy-number and structural-variant processing through specialised annotation and classification tools.

The structural workflow may include:

- conversion of suitable VCF records into interval-based input;
- deletion and duplication classification;
- gene-content assessment;
- dosage-sensitivity evidence;
- overlap with disease-associated regions;
- rule-based CNV scoring;
- supplementary model-based interpretation.

Structural findings require careful review because their clinical significance may depend on:

- size;
- copy-number state;
- gene content;
- dosage sensitivity;
- inheritance;
- breakpoint precision;
- mosaicism;
- phenotype correlation.

Independent confirmation may be required before a structural finding is used clinically.

21.9 Repeat-Expansion Review
----------------------------

Repeat expansions represent a specialised variant class that may not be fully characterised by standard small-variant annotation.

The workflow can preserve repeat findings when an appropriate repeat-expansion result table is available.

A detected repeat should be reviewed according to:

- locus;
- estimated repeat size;
- normal and disease-associated ranges;
- method limitations;
- assay reliability;
- need for dedicated laboratory confirmation.

The pipeline should not assign a pathogenic interpretation where the supporting repeat threshold or evidence is unavailable.

21.10 Pharmacogenomic Analysis
------------------------------

Pharmacogenomic matching was incorporated as a separate analytical component.

The workflow can identify allele-aware matches involving:

- gene;
- variant;
- genotype;
- drug;
- phenotype;
- evidence source;
- guideline context.

Pharmacogenomic findings are kept conceptually separate from rare-disease diagnostic findings.

A matched PGx record does not always establish:

- a complete star allele;
- a diplotype;
- a metaboliser phenotype;
- a medication recommendation.

Clinical implementation may require haplotype reconstruction, guideline review and consideration of non-genetic factors.

The automatically generated report therefore treats PGx results as contextual information requiring professional review.

21.11 Candidate Ranking
-----------------------

The master candidate-ranking table brings together evidence from multiple analysis modules.

Candidate scores may reflect:

- clinical classification;
- allele frequency;
- molecular consequence;
- disease–gene validity;
- phenotype similarity;
- inheritance compatibility;
- genotype;
- compound-heterozygous evidence;
- structural or repeat evidence;
- pharmacogenomic context.

The ranking system helps reduce a large candidate set to a manageable number of high-priority findings.

The numerical score is not a clinical classification and should not be interpreted as proof of pathogenicity.

The analyst must still review the evidence contributing to the score.

21.12 Final Outputs
-------------------

The main final outputs for each case may include:

.. code-block:: text

   results/cases/<case_id>/final/<case_id>.master_candidate_ranking.tsv
   results/cases/<case_id>/final/<case_id>.pipeline_summary.tsv
   results/cases/<case_id>/final/<case_id>.candidate_ranking_qc.tsv
   results/cases/<case_id>/final/report/<case_id>.report_draft.json
   results/cases/<case_id>/final/report/<case_id>.report_draft.json.sha256

Additional outputs may be produced by:

- VEP;
- SnpEff;
- ClinVar annotation;
- phenotype matching;
- inheritance analysis;
- compound-heterozygous aggregation;
- CNV tools;
- repeat-expansion tools;
- pharmacogenomic matching;
- validation and audit modules.

The final master table should be interpreted together with the supporting files rather than in isolation.

21.13 Automatic Clinical-Report Workflow
----------------------------------------

The final pipeline automatically creates a structured draft JSON after candidate ranking.

The reporting workflow:

reads final case outputs

.. code-block:: text

   ↓

selects report-relevant findings

.. code-block:: text

   ↓

loads protected metadata when available

.. code-block:: text

   ↓

creates structured JSON

.. code-block:: text

   ↓

calculates a SHA-256 checksum

.. code-block:: text

   ↓

registers the output in the pipeline summary

.. code-block:: text

   ↓

opens the report through localhost

.. code-block:: text

   ↓

populates the browser-based report builder

This automation reduces manual copying and provides a consistent report structure.

Nevertheless, the generated report remains an unreviewed draft.

Before export, the analyst must confirm:

- patient information;
- variant identity;
- transcript and HGVS;
- genotype;
- disease association;
- inheritance;
- classification;
- phenotype relationship;
- PGx grouping;
- confirmation status;
- recommendations;
- limitations.

21.14 Validation Results
------------------------

The pipeline was evaluated using controlled cases and regression tests.

Validation covered:

- structural VCF preflight;
- chromosome naming;
- reference compatibility;
- phenotype-file handling;
- exact HPO filename matching;
- production and validation resource separation;
- inheritance and ploidy logic;
- X-linked handling;
- mitochondrial handling;
- compound-heterozygous aggregation;
- homozygous double-count prevention;
- local pharmacogenomic matching;
- repeated-case routing;
- candidate-table generation;
- report-JSON generation;
- checksum validation;
- browser-based automatic report loading;
- protection of case-specific report data.

The final audit included twelve tested cases and reported:

.. code-block:: text

   PASS: 12
   FAIL: 0

Patient 13 was not included because it fell outside the planned validation timeframe.

The automatic report workflow was also tested in a fresh synthetic validation case. The test confirmed successful generation, validation, checksum creation, pipeline-summary registration and automatic browser loading.

21.15 Reproducibility
---------------------

Reproducibility was supported through:

- fixed project directories;
- containerised tools;
- explicit reference files;
- version-controlled scripts;
- consistent command-line interfaces;
- production and validation modes;
- case-level logs;
- pipeline summaries;
- resource-mode records;
- checksums;
- automated tests;
- Git commit history;
- documented input and output paths.

The reusable implementation was committed and verified on GitHub.

The automatic clinical-report integration was included in commit:

.. code-block:: text

   5b310cede201a33cf30253c9dda524715dbd4cc3

The local and remote commit hashes were confirmed to match after the final push.

21.16 Data Protection
---------------------

The project separates reusable code from protected case information.

The repository may contain:

- pipeline scripts;
- test scripts;
- documentation;
- schemas;
- metadata templates;
- non-identifiable examples.

It should not contain:

- real patient names;
- dates of birth;
- physician information;
- identifiable specimen records;
- protected metadata files;
- generated case-report JSON;
- reviewed case-report JSON;
- patient report PDFs;
- large genomic resources;
- full local result directories.

Relevant patient-specific outputs are excluded through .gitignore.

The browser-based report launcher uses a local server bound to:

.. code-block:: text

   127.0.0.1

This reduces accidental network exposure but does not replace secure device access, file permissions and institutional data-protection requirements.

21.17 Strengths of the Project
------------------------------

Important strengths include:

- one universal case workflow;
- support for multiple variant classes;
- phenotype-aware prioritisation;
- inheritance-aware interpretation;
- phased compound-heterozygous logic;
- separation of validation and production evidence;
- allele-aware pharmacogenomic matching;
- modular output structure;
- automatic report generation;
- checksum-based report integrity;
- reproducible tests;
- clear protection of patient-specific data;
- version-controlled implementation;
- detailed documentation.

The project demonstrates how multiple genomic evidence sources can be combined into a practical and auditable workflow.

21.18 Limitations
-----------------

The pipeline also has important limitations.

These include:

- dependence on the accuracy of the input VCF;
- incomplete sensitivity for variant classes not represented in the input;
- possible transcript ambiguity;
- dependence on external database quality;
- changing clinical classifications over time;
- incomplete phenotype information;
- lack of family data in many cases;
- limited phasing information;
- limited interpretation of complex structural variants;
- repeat-expansion dependence on specialised input;
- incomplete star-allele reconstruction for some PGx genes;
- inability of computational scores alone to establish pathogenicity;
- lack of automatic clinical sign-out;
- requirement for expert review;
- requirement for orthogonal confirmation where appropriate.

A negative pipeline result does not exclude a genetic disorder.

The workflow should therefore be considered a prioritisation and reporting system rather than an independent diagnostic authority.

21.19 Recommended Future Improvements
-------------------------------------

Possible future developments include:

#. Addition of stronger schema-based JSON validation.
#. Improved separation of diagnostic and pharmacogenomic findings in the report layout.
#. More complete star-allele and diplotype reconstruction.
#. Trio-aware inheritance analysis.
#. Automated segregation assessment.
#. Improved CNV breakpoint and dosage interpretation.
#. Integration of validated repeat-expansion calling tools.
#. Better mitochondrial heteroplasmy support.
#. Mosaic-variant prioritisation.
#. Automated database-version tracking.
#. Improved literature and guideline linking.
#. Analyst sign-off and report versioning.
#. Structured review-status fields.
#. Controlled reinterpretation when databases are updated.
#. Continuous integration testing through GitHub Actions.
#. Expanded synthetic validation cases covering additional inheritance and variant classes.
#. Improved report tables and print-page handling.
#. Formal security review before use with identifiable clinical data.

These developments should be added gradually and validated using controlled test cases.

21.20 Final Interpretation of the Project
-----------------------------------------

The completed work demonstrates that a reproducible genomic pipeline can combine diverse sources of evidence into an organised rare-disease and pharmacogenomic analysis framework.

The project does not merely annotate variants. It also:

- verifies inputs;
- evaluates inheritance;
- integrates phenotype;
- prioritises candidates;
- separates evidence types;
- records provenance;
- validates outputs;
- prepares structured reports;
- protects patient-specific information.

The final result is a reusable educational and research workflow that can support systematic variant review across different cases.

Its greatest value lies in reducing fragmented manual work while preserving traceability and analyst oversight.

21.21 Final Statement
---------------------

The **Universal Rare-Disease and Pharmacogenomics Analysis Pipeline** was successfully developed, tested, documented and integrated with an automatic clinical-report workflow.

The project achieved its main goals of:

- reproducibility
- universality
- modularity
- traceability
- inheritance-aware interpretation
- phenotype-aware prioritisation
- multi-variant support
- pharmacogenomic integration
- automatic report preparation
- privacy-conscious data handling

The pipeline should be used as a structured decision-support and research system. Final clinical interpretation must remain the responsibility of appropriately qualified professionals who review the complete patient context, supporting evidence, technical limitations and confirmation results.

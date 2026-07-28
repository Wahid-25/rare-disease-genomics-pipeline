.. _23-conclusion-and-final-project-summary:

23. Conclusion and Final Project Summary
========================================


The Genomic Analysis Lab project developed a reproducible GRCh38 workflow for integrating rare-disease variant annotation, phenotype evidence, inheritance modelling, copy-number analysis, repeat-expansion routing and selected pharmacogenomic interpretation.

The final workflow is more than a collection of annotation tools. It provides a structured system that:

Accepts a patient-level GRCh38 VCF

│

▼

Validates the input and case context

│

▼

Separates supported variant classes

│

├── SNVs and short indels

├── DEL and DUP CNVs

├── Repeat-expansion records

└── Unsupported structural variants

│

▼

Integrates functional, clinical, phenotype

and inheritance evidence

│

▼

Produces ranked, traceable candidate outputs

│

▼

Preserves logs, manifests and checksums

for reproducibility and audit

The project demonstrates how different genomic evidence sources can be combined while preserving uncertainty, analytical boundaries and data provenance.

.. _23-1-project-aim-achieved:

23.1 Project aim achieved
-------------------------

The central aim was to develop a universal and reproducible genomic-analysis workflow that could process different rare-disease cases without requiring patient-specific code modifications.

-  

   .. container::

      This aim was achieved through:

-  

   .. container::

      Universal case launchers

-  

   .. container::

      Structural VCF preflight

-  

   .. container::

      Variant-class routing

-  

   .. container::

      Production and validation resource isolation

-  

   .. container::

      Shared inheritance utilities

-  

   .. container::

      Phenotype-based prioritisation

-  

   .. container::

      Allele-aware pharmacogenomic matching

-  

   .. container::

      Integrated candidate scoring

-  

   .. container::

      Reproducibility manifests

-  

   .. container::

      Final regression auditing

The pipeline was designed so that the same analytical rules are applied across cases.

A candidate is prioritised because its evidence supports it, not because the pipeline contains a rule written specifically for that patient or disease.

.. _23-2-main-workflow-components:

23.2 Main workflow components
-----------------------------

The completed project integrates the following principal components.

.. _23-2-1-input-and-structural-quality-control:

23.2.1 Input and structural quality control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The intake and preflight stages evaluate:

-  

   .. container::

      VCF structure

-  

   .. container::

      Genome build

-  

   .. container::

      Chromosome convention

-  

   .. container::

      Sample columns

-  

   .. container::

      Patient genotypes

-  

   .. container::

      Symbolic alleles

-  

   .. container::

      Structural endpoints

-  

   .. container::

      Phenotype-file availability

External or newly received cases are processed through an intake wrapper before entering the main analysis.

The original intake information is preserved separately from prepared files and final results.

.. _23-2-2-small-variant-annotation:

23.2.2 Small-variant annotation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ordinary SNVs and short indels are processed through:

-  

   .. container::

      bcftools normalisation

-  

   .. container::

      VEP

-  

   .. container::

      SnpEff

-  

   .. container::

      ClinVar

-  

   .. container::

      SpliceAI

Cached population-frequency annotation

These stages provide:

-  transcript consequences;

-  predicted functional impact;

-  clinical assertions;

-  splice predictions;

-  population context;

-  stable normalised allele identifiers.

The annotations are then integrated rather than interpreted independently.

.. _23-2-3-gene-disease-and-phenotype-integration:

23.2.3 Gene–disease and phenotype integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The pipeline incorporates:

-  

   .. container::

      Gene2Phenotype

-  

   .. container::

      Human Phenotype Ontology

-  

   .. container::

      MONDO disease harmonisation

This allows a candidate to be assessed according to:

-  whether the gene is linked to a relevant disorder;

-  the confidence of that relationship;

-  the expected allelic requirement;

-  the molecular mechanism;

-  the similarity between the disease and patient phenotype.

The original G2P and ClinVar disease labels are retained even when a harmonised disease identity is generated.

.. _23-2-4-inheritance-modelling:

23.2.4 Inheritance modelling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The inheritance system evaluates:

-  

   .. container::

      Autosomal dominant models

-  

   .. container::

      Autosomal recessive models

-  

   .. container::

      X-linked models

-  

   .. container::

      Mitochondrial contexts

-  

   .. container::

      Patient sex

-  

   .. container::

      Chromosome ploidy

-  

   .. container::

      Genotype and zygosity

-  

   .. container::

      Compound heterozygosity

A major improvement was the use of shared inheritance utilities so that different stages do not apply inconsistent definitions.

The workflow distinguishes:

-  

   .. container::

      Phased trans

-  

   .. container::

      Cis

-  

   .. container::

      Possible unphased pairs

-  

   .. container::

      Unresolved phase

-  

   .. container::

      Homozygous biallelic variants

This prevents two unphased heterozygous variants from being incorrectly reported as confirmed compound heterozygous variants.

.. _23-2-5-copy-number-analysis:

23.2.5 Copy-number analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Supported deletion and duplication records are processed through:

CNV VCF-to-BED conversion

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

      Gene–disease mapping

-  

   .. container::

      Phenotype prioritisation

The pipeline preserves the distinction between:

One source CNV

-  

   .. container::

      AnnotSV full-interval rows

-  

   .. container::

      AnnotSV split gene or transcript rows

Automated CNV classifications remain evidence for review and are not treated as independent clinical confirmation.

.. _23-2-6-repeat-expansion-routing:

23.2.6 Repeat-expansion routing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Repeat-expansion records are detected before ordinary small-variant normalisation.

They are:

-  

   .. container::

      Preserved

-  

   .. container::

      Reported separately

-  

   .. container::

      Excluded from ordinary SNV scoring

-  

   .. container::

      Assigned an explicit interpretation status

The validated Patient 03 record received:

detected_not_interpreted

This indicates that the VCF record was recognised but specialist read-level repeat analysis was not performed.

.. _23-2-7-unsupported-structural-variants:

23.2.7 Unsupported structural variants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Structural records outside the validated SNV, indel, DEL, DUP and repeat routes are not silently deleted.

They are preserved in an unsupported-variant report with:

Original allele representation

-  

   .. container::

      Breakpoint information

-  

   .. container::

      Structural type

-  

   .. container::

      Reason for unsupported status

-  

   .. container::

      Required specialist route

Unsupported describes the current analytical scope. It does not mean benign or invalid.

.. _23-2-8-pharmacogenomic-analysis:

23.2.8 Pharmacogenomic analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ClinPGx branch uses a curated local reference and exact genomic allele matching.

Matching requires:

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

An rsID alone is not sufficient.

The project also preserves:

-  genotype;

-  project star-allele assignment;

-  project diplotype;

-  functional phenotype;

-  drug association;

-  limitations.

Pharmacogenomic findings remain separate from rare-disease candidate scoring.

.. _23-3-major-engineering-improvements:

23.3 Major engineering improvements
-----------------------------------

Several important technical safeguards were developed during the project.

.. _23-3-1-production-and-validation-isolation:

23.3.1 Production and validation isolation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Official production resources are separated from synthetic validation additions.

This prevents test relationships from affecting real or production-mode analysis.

.. _23-3-2-allele-aware-pgx-matching:

23.3.2 Allele-aware PGx matching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The original risk of matching pharmacogenomic records by rsID or coordinate alone was addressed by requiring exact REF and ALT agreement.

This prevents assignment of an interpretation to the wrong allele at the same locus.

.. _23-3-3-shared-inheritance-logic:

23.3.3 Shared inheritance logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inheritance and zygosity functions were centralised so that:

-  

   .. container::

      Small-variant scoring

-  

   .. container::

      Sex and ploidy evaluation

-  

   .. container::

      Compound-heterozygous aggregation

-  

   .. container::

      use consistent rules.

.. _23-3-4-sex-and-ploidy-preflight:

23.3.4 Sex and ploidy preflight
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sex-chromosome and mitochondrial variants are evaluated in an appropriate ploidy context before inheritance evidence is assigned.

This reduces incorrect interpretation using unrestricted autosomal assumptions.

.. _23-3-5-phase-aware-compound-heterozygosity:

23.3.5 Phase-aware compound heterozygosity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Confirmed phased-trans status requires:

-  

   .. container::

      A shared PS or PID context

-  

   .. container::

      Opposite haplotypes

-  

   .. container::

      Variants in the same relevant gene

Unphased pairs are retained as possible rather than confirmed.

Homozygous variants are treated as biallelic but are not duplicated into artificial compound-heterozygous pairs.

.. _23-3-6-exact-hpo-case-matching:

23.3.6 Exact HPO case matching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Patient phenotype files are matched using exact patient identifiers.

This prevents a file for:

patient_010

from being selected accidentally for:

patient_01

.. _23-3-7-disease-label-precedence:

23.3.7 Disease-label precedence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The workflow preserves the intended gene–disease model from G2P while retaining ClinVar conditions as supporting evidence.

This prevents broad or multi-condition ClinVar labels from replacing the principal disease identity automatically.

.. _23-3-8-intake-report-preservation:

23.3.8 Intake-report preservation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The original external-case intake assessment remains available after preparation, routing and analysis.

This preserves:

-  original input classification;

-  sample assessment;

-  build evidence;

-  genotype usability;

-  detected pre-existing annotations;

-  readiness status.

.. _23-4-validation-summary:

23.4 Validation summary
-----------------------

The project used thirteen prepared synthetic VCFs.

All thirteen passed structural preflight.

The complete final behavioural audit included Patients 01–12.

The final audit recorded:

Audited cases: 12

Passed cases: 12

Failed cases: 0

Patient 13 was intentionally not processed through the complete pipeline within the project timeframe.

This distinction is essential:

-  

   .. container::

      13 cases passed structural preflight

-  

   .. container::

      12 cases passed the complete final audit

.. _23-5-canonical-validation-results:

23.5 Canonical validation results
---------------------------------

The accepted principal results were:

+-------------+---------------+-------------------------------+--------------------------+
| **Patient** | **Category**  | **Principal result**          | **Score or status**      |
+=============+===============+===============================+==========================+
| 01          | LEGACY        | CFTR — chr7:117559590:ATCT>A  | 62.96                    |
+-------------+---------------+-------------------------------+--------------------------+
| 02          | LEGACY        | HBB — chr11:5227002:T>A       | 29.63                    |
+-------------+---------------+-------------------------------+--------------------------+
| 03          | ROUTED_REPEAT | HTT repeat-expansion record   | detected_not_interpreted |
+-------------+---------------+-------------------------------+--------------------------+
| 04          | LEGACY        | BRCA1 — chr17:43124027:ACT>A  | 81.48                    |
+-------------+---------------+-------------------------------+--------------------------+
| 05          | CURRENT       | HEXA — chr15:72346579:G>GGATA | 85.19                    |
+-------------+---------------+-------------------------------+--------------------------+
| 06          | CURRENT       | PAH — chr12:102840493:G>A     | 66.67                    |
+-------------+---------------+-------------------------------+--------------------------+
| 07          | CURRENT       | ATP7B — chr13:51958333:C>A    | 48.15                    |
+-------------+---------------+-------------------------------+--------------------------+
| 08          | CURRENT       | APOB — chr2:21006288:C>T      | 70.37                    |
+-------------+---------------+-------------------------------+--------------------------+
| 09          | CURRENT       | G6PD — chrX:154536002:C>T     | 59.26                    |
+-------------+---------------+-------------------------------+--------------------------+
| 10          | CURRENT       | MEFV — chr16:3243407:T>C      | 77.78                    |
+-------------+---------------+-------------------------------+--------------------------+
| 11          | CURRENT       | HFE — chr6:26092913:G>A       | 62.96                    |
+-------------+---------------+-------------------------------+--------------------------+
| 12          | CURRENT       | MLH1 — chr3:37028902:C>T      | 74.07                    |
+-------------+---------------+-------------------------------+--------------------------+

These values are project regression targets.

They are not pathogenicity probabilities or diagnostic-confidence percentages.

.. _23-6-repeat-expansion-validation-result:

23.6 Repeat-expansion validation result
---------------------------------------

Patient 03 demonstrated the dedicated repeat route.

The canonical record was:

Case:

patient_03_huntington_disease

Gene:

HTT

Variant:

chr4:3074877:N><CAG_EXPANSION>

Motif:

CAG

Reported repeat count:

45

Controlled threshold:

40

Genotype:

0/1

Status:

detected_not_interpreted

The pipeline correctly:

-  

   .. container::

      Detected the symbolic repeat record

-  

   .. container::

      Preserved its supplied metadata

-  

   .. container::

      Excluded it from ordinary small-variant ranking

-  

   .. container::

      Required specialist repeat-expansion analysis

The project did not independently confirm the repeat count from BAM or CRAM reads.

.. _23-7-pharmacogenomic-validation-results:

23.7 Pharmacogenomic validation results
---------------------------------------

The controlled validation suite also demonstrated allele-aware ClinPGx matching.

The accepted results included:

+-------------+----------------------+-----------------------+--------------------------+
| **Patient** | **Gene and variant** | **Project diplotype** | **Functional phenotype** |
+=============+======================+=======================+==========================+
| 10          | TPMT rs1142345       | \*1/\*3C              | Intermediate metaboliser |
+-------------+----------------------+-----------------------+--------------------------+
| 11          | CYP2D6 rs3892097     | \*1/\*4               | Intermediate metaboliser |
+-------------+----------------------+-----------------------+--------------------------+
| 12          | DPYD rs3918290       | \*1/\*2A              | Intermediate metaboliser |
+-------------+----------------------+-----------------------+--------------------------+

These results represent simplified project-validation interpretations from the local curated reference.

They do not constitute comprehensive clinical star-allele calling.

Patient 09’s final audit records the PGx branch as not applicable.

.. _23-8-reproducibility-and-audit-evidence:

23.8 Reproducibility and audit evidence
---------------------------------------

The final audit is stored under:

-  

   .. container::

      validation/final_audit_20260727/

-  

   .. container::

      Important files include:

-  

   .. container::

      canonical_cases.tsv

-  

   .. container::

      canonical_final_outputs.sha256

-  

   .. container::

      key_resources.sha256

-  

   .. container::

      pipeline_source.sha256

-  

   .. container::

      FINAL_VALIDATION_STATUS.md

-  

   .. container::

      scripts/audit_patients_01_12_final.py

-  

   .. container::

      Together, these files establish:

-  

   .. container::

      Which output is canonical

-  

   .. container::

      Which candidate or route is expected

-  

   .. container::

      Whether important results changed

-  

   .. container::

      Whether key resources changed

-  

   .. container::

      Whether pipeline source changed

-  

   .. container::

      Whether the final case audit passed

The audit supports three provenance categories:

-  

   .. container::

      CURRENT

-  

   .. container::

      LEGACY

-  

   .. container::

      ROUTED_REPEAT

These categories describe how the accepted output was produced.

They are not clinical classifications.

.. _23-9-data-protection-and-repository-scope:

23.9 Data protection and repository scope
-----------------------------------------

The GitHub repository is intended to contain:

-  

   .. container::

      Pipeline source code

-  

   .. container::

      Container definition files

-  

   .. container::

      Resource setup scripts

-  

   .. container::

      Tests

-  

   .. container::

      Compact synthetic validation materials

-  

   .. container::

      Documentation

-  

   .. container::

      Audit logic

-  

   .. container::

      It should not contain:

-  

   .. container::

      Real patient VCFs

-  

   .. container::

      Real patient phenotype files

-  

   .. container::

      Detailed patient outputs

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

      SIF containers

-  

   .. container::

      Private case archives

-  

   .. container::

      Credentials

The project separates reproducible source code from protected genomic data and large local resources.

The current remote and push state must always be checked directly before claiming that a commit is present on GitHub.

.. _23-10-scientific-significance:

23.10 Scientific significance
-----------------------------

The project demonstrates several broader principles in genomic analysis.

.. _23-10-1-annotation-alone-is-insufficient:

23.10.1 Annotation alone is insufficient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A variant’s functional consequence does not determine disease relevance by itself.

Interpretation also requires:

-  

   .. container::

      Gene–disease evidence

-  

   .. container::

      Phenotype compatibility

-  

   .. container::

      Inheritance

-  

   .. container::

      Population frequency

-  

   .. container::

      Clinical assertions

-  

   .. container::

      Variant mechanism

.. _23-10-2-variant-classes-require-different-methods:

23.10.2 Variant classes require different methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SNVs, CNVs, repeat expansions and complex structural variants cannot be processed through one identical annotation route.

A universal workflow must therefore be:

Unified at the case level

but:

Variant-class aware at the analytical level

.. _23-10-3-missing-evidence-is-not-negative-evidence:

23.10.3 Missing evidence is not negative evidence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The absence of:

-  

   .. container::

      ClinVar annotation

-  

   .. container::

      Splice prediction

-  

   .. container::

      G2P relationship

-  

   .. container::

      Phenotype score

-  

   .. container::

      PGx match

may indicate unavailable or incomplete evidence rather than benignity.

Explicit missing-data states are therefore important.

.. _23-10-4-reproducibility-requires-more-than-source-code:

23.10.4 Reproducibility requires more than source code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A Git repository alone does not capture:

-  

   .. container::

      Input checksums

-  

   .. container::

      Resource versions

-  

   .. container::

      Container builds

-  

   .. container::

      Execution settings

-  

   .. container::

      Generated outputs

-  

   .. container::

      Validation state

The project therefore combines Git with checksums, manifests, logs and dated audits.

.. _23-10-5-automated-prioritisation-must-preserve-uncertainty:

23.10.5 Automated prioritisation must preserve uncertainty
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The pipeline assigns ranks and scores, but it also preserves:

-  

   .. container::

      Conflicting evidence

-  

   .. container::

      Incomplete inheritance

-  

   .. container::

      Missing phenotype information

-  

   .. container::

      Unsupported variant classes

-  

   .. container::

      Specialist follow-up requirements

This reduces the risk of presenting an automated result with greater certainty than the data support.

.. _23-11-principal-limitations:

23.11 Principal limitations
---------------------------

The major project limitations are:

-  

   .. container::

      Synthetic rather than clinical validation

-  

   .. container::

      No formal sensitivity or specificity measurement

-  

   .. container::

      Dependence on variants already present in the VCF

-  

   .. container::

      No direct BAM or CRAM analysis

-  

   .. container::

      No independent laboratory confirmation

-  

   .. container::

      GRCh38-only input scope

-  

   .. container::

      Incomplete complex-SV interpretation

-  

   .. container::

      No specialist repeat sizing

-  

   .. container::

      Limited CNV validation cases

-  

   .. container::

      Limited PGx haplotype coverage

-  

   .. container::

      Incomplete family and segregation analysis

-  

   .. container::

      Project-specific, uncalibrated prioritisation scores

These limitations define the appropriate use of the workflow.

.. _23-12-clinical-boundary:

23.12 Clinical boundary
-----------------------

The project should be described as:

-  

   .. container::

      A reproducible research and educational candidate-

-  

   .. container::

      prioritisation workflow

-  

   .. container::

      It should not be described as:

-  

   .. container::

      A clinically validated diagnostic system

-  

   .. container::

      The pipeline does not independently:

-  

   .. container::

      Confirm a variant

-  

   .. container::

      Establish a diagnosis

-  

   .. container::

      Determine recurrence risk

-  

   .. container::

      Recommend medication changes

-  

   .. container::

      Replace clinical genetics review

Every clinically relevant finding requires appropriate specialist assessment and, where required, confirmatory testing.

.. _23-13-future-development-priorities:

23.13 Future development priorities
-----------------------------------

The most important future improvements are:

1. Verify and standardise every final script and resource path.

2. Expand dedicated CNV validation.

3. Add trio and family-based analysis.

4. Add read-level candidate quality review.

5. Integrate specialist repeat-expansion calling.

6. Expand complex structural-variant support.

7. Develop comprehensive PGx haplotype and CNV analysis.

8. Make scoring contributions more transparent.

9. Add compact continuous-integration tests.

10. Evaluate the workflow using an independent benchmark cohort.

These improvements would extend the project from a validated educational framework towards a more comprehensive research analysis platform.

.. _23-14-final-conclusion:

23.14 Final conclusion
----------------------

The Genomic Analysis Lab project successfully established a structured and reproducible GRCh38 pipeline for integrating rare-disease and selected pharmacogenomic evidence.

Its major strengths are:

-  

   .. container::

      Universal case intake

-  

   .. container::

      Variant-class-specific routing

-  

   .. container::

      Multi-tool functional annotation

-  

   .. container::

      Gene–disease and phenotype integration

-  

   .. container::

      Ploidy-aware inheritance modelling

-  

   .. container::

      Phase-aware compound-heterozygous analysis

-  

   .. container::

      Allele-aware ClinPGx matching

-  

   .. container::

      Dedicated repeat and unsupported-SV reporting

-  

   .. container::

      Integrated candidate prioritisation

-  

   .. container::

      Reproducibility manifests and checksum auditing

All thirteen prepared synthetic VCFs passed structural preflight, and all twelve cases included in the final behavioural audit met their canonical candidate or routing expectations.

The project therefore demonstrates reliable behaviour for its implemented synthetic scenarios.

Its results remain computational prioritisation outputs rather than confirmed clinical findings. The workflow is most appropriately used for education, research development, controlled validation and expert-supported candidate review.

.. _23-15-final-summary-statement:

23.15 Final summary statement
-----------------------------

A concise final statement for the end of the report is:

-  

   .. container::

      This project developed and validated a reproducible

.. container::

   GRCh38 rare-disease and pharmacogenomic analysis pipeline

.. container::

   that integrates functional annotation, clinical databases,

.. container::

   phenotype similarity, inheritance modelling, CNV evidence

.. container::

   and dedicated structural-variant routing.

-  

   .. container::

      The final audit confirmed the expected candidate or

.. container::

   analytical route in all twelve completed synthetic cases.

.. container::

   The workflow improves consistency, traceability and

.. container::

   candidate prioritisation while preserving important

.. container::

   uncertainties and clinical limitations.

-  

   .. container::

      It is intended as a research and educational framework and

does not replace clinical interpretation, confirmatory

testing or professional genetic counselling.

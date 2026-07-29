20. Conclusion and Final Project Summary
========================================

The Genomic Analysis Lab project developed a reproducible GRCh38 workflow for the analysis and prioritisation of rare-disease variants together with selected pharmacogenomic evidence.

The final system guides the analyst through the complete process:

.. code-block:: text

   Project installation
           │
           ▼
   Reference-resource preparation
           │
           ▼
   Case intake and input validation
           │
           ▼
   Variant-class detection and routing
           │
           ├── SNVs and short indels
           ├── Deletions and duplications
           ├── Repeat-expansion records
           └── Unsupported structural variants
           │
           ▼
   Functional and clinical annotation
           │
           ▼
   Phenotype and gene–disease prioritisation
           │
           ▼
   Inheritance, sex and ploidy evaluation
           │
           ▼
   Candidate scoring and master-table generation
           │
           ▼
   Final output review
           │
           ▼
   Clinical-style report preparation

The project therefore covers the complete analytical path from a prepared genomic input to a reviewed, human-readable report.

20.1 Achievement of the project aim
-----------------------------------

The principal aim was to construct a universal workflow that could analyse different rare-disease cases without requiring a separate patient-specific script for every condition.

This aim was achieved through:

- Universal case intake

- Structural VCF preflight

- Variant-class routing

- Standardised annotation

- Gene–disease mapping

- Phenotype prioritisation

- Shared inheritance logic

- Candidate scoring

- Final result generation

- Clinical-style report preparation

The same analytical structure can be applied to different cases while allowing each candidate to be prioritised according to its own evidence.

The pipeline does not force a predefined disease result. Instead, it integrates several independent evidence domains to determine which variants should receive the highest review priority.

20.2 Input and case preparation
-------------------------------

The workflow accepts patient-level genomic information represented in VCF format together with phenotype information represented by Human Phenotype Ontology terms.

Before analysis, the intake and preflight stages assess:

- VCF file structure

- Genome build

- Chromosome naming

- Sample columns

- Genotype availability

- Selected patient sample

- Phenotype-file validity

- Variant representation

The project uses:

Genome build:

GRCh38

Chromosome convention:

chr-prefixed chromosomes

This ensures that the genomic coordinates, reference sequence and annotation resources remain compatible throughout the workflow.

20.3 Variant-class routing
--------------------------

A major feature of the workflow is that different variant classes do not enter one inappropriate universal annotation route.

The pipeline separates:

- Ordinary SNVs and short indels

- DEL and DUP copy-number variants

- Repeat-expansion records

- Other structural variants

Each category is processed using the tools and interpretation rules appropriate to that variant class.

This design prevents, for example:

- A repeat expansion entering ordinary SNV normalisation

- A deletion being interpreted as a short indel

- A breakend being silently discarded

- A CNV being forced into a coding-HGVS field

Unsupported records remain visible for specialist review rather than being classified automatically as benign.

20.4 Small-variant analysis
---------------------------

SNVs and short indels are processed through:

- bcftools normalisation

- VEP

- SnpEff

- ClinVar

- SpliceAI

- Cached population-frequency annotation

These tools contribute different evidence.

**bcftools**

bcftools normalises the allele representation and verifies compatibility with the reference genome.

**VEP**

VEP provides transcript-level consequences, gene annotations, HGVS representations, transcript selection and available population-frequency evidence.

**SnpEff**

SnpEff provides an additional functional-consequence annotation using its configured transcript database.

**ClinVar**

ClinVar contributes existing clinical assertions, associated conditions and review status for matching alleles.

**SpliceAI**

SpliceAI provides predictions of possible splice donor or acceptor gain and loss effects.

None of these annotations independently proves that a variant causes the patient’s condition. Their evidence must be interpreted together.

20.5 Gene–disease and phenotype integration
-------------------------------------------

The workflow uses gene–disease and phenotype resources to determine whether an annotated variant is relevant to the submitted clinical features.

The main evidence includes:

- Gene2Phenotype disease relationships

- HPO phenotype terms

- MONDO disease-identity resolution

- ClinVar condition information

The prioritisation system evaluates:

- Whether the gene is linked to a relevant disease

- The confidence of the gene–disease relationship

- The expected inheritance model

- The recognised molecular mechanism

- The similarity between the disease phenotype and the patient’s HPO profile

The original disease labels from Gene2Phenotype and ClinVar remain available even when a harmonised disease identity is generated.

20.6 Inheritance, sex and ploidy analysis
-----------------------------------------

The workflow evaluates whether the patient genotype is compatible with the expected disease model.

Supported contexts include:

- Autosomal dominant

- Autosomal recessive

- X-linked

- Mitochondrial

The analysis considers:

- Genotype

- Zygosity

- Patient sex

- Chromosome

- Expected ploidy

- Allelic requirement

This prevents unrestricted autosomal assumptions from being applied to sex-chromosome or mitochondrial variants.

20.7 Compound-heterozygous analysis
-----------------------------------

The project distinguishes several possible two-variant configurations:

- Phased trans

- Cis

- Possible unphased pair

- Phase unresolved

- Homozygous biallelic variant

Confirmed phased-trans support requires:

- Variants in the same relevant gene

- A shared PS or PID context

- Opposite haplotypes

Two unphased heterozygous variants are retained as a possible pair but are not reported as confirmed trans.

A homozygous variant satisfies a biallelic genotype context without being duplicated into an artificial compound-heterozygous pair.

20.8 Copy-number variant analysis
---------------------------------

Supported deletions and duplications enter the CNV workflow.

The main CNV tools are:

- AnnotSV

- ClassifyCNV

- ISV-CNV

- ClinGen dosage evidence

The CNV branch assesses:

- Genomic interval

- DEL or DUP type

- Interval size

- Affected genes

- Dosage sensitivity

- Gene–disease relationships

- Phenotype compatibility

- Automated CNV classifications

AnnotSV full-interval and split transcript rows are recognised as different views of the same source CNV rather than independent events.

The outputs from AnnotSV, ClassifyCNV and ISV-CNV are complementary evidence. Agreement between them does not constitute three independent laboratory confirmations.

20.9 Repeat-expansion handling
------------------------------

Repeat-expansion records are detected and separated before ordinary small-variant processing.

The workflow preserves:

- Gene or locus

- Repeat motif

- Reported repeat count

- Genotype

- Threshold information

- Original VCF representation

When specialist read-level sizing was not performed, the record receives:

.. code-block:: text

   detected_not_interpreted

This status means that the submitted VCF record was detected and preserved, but the pipeline did not independently confirm the expansion from BAM or CRAM reads.

20.10 Pharmacogenomic analysis
------------------------------

The pharmacogenomic branch uses exact genomic allele matching.

Matching requires agreement in:

- Chromosome

- Position

- Reference allele

- Alternate allele

An rsID alone is not sufficient.

The ClinPGx output may include:

- Gene

- Variant

- rsID

- Genotype

- Project star allele

- Project diplotype

- Functional phenotype

- Associated drug

Pharmacogenomic evidence remains separate from rare-disease candidate scoring.

The PGx output does not independently authorise a medication or dose change.

20.11 Universal candidate prioritisation
----------------------------------------

The project combines several evidence domains into a candidate-prioritisation score.

These may include:

- Functional consequence

- ClinVar evidence

- Population frequency

- Gene–disease validity

- Phenotype similarity

- Inheritance compatibility

- Sex and ploidy

- Compound-heterozygous support

- Splice prediction

The score is used to order candidates for review.

It is not:

A pathogenicity probability

A diagnostic-confidence percentage

An ACMG classification

A candidate with a score of:

74.07

does not have a 74.07% probability of being causal.

The score should be interpreted only within the same pipeline version and resource state.

20.12 Final pipeline outputs
----------------------------

The completed workflow produces structured outputs that may include:

- Prepared and routed VCF files

- VEP-annotated VCF

- SnpEff-annotated VCF

- ClinVar-annotated VCF

- SpliceAI output

- Phenotype-prioritisation tables

- Inheritance evidence

- ClinPGx results

- CNV reports

- Repeat-expansion reports

- Unsupported-variant reports

- Master candidate table

- Pipeline summary

- Logs

- Reproducibility manifest

- Checksums

The master candidate table provides the main ranked review list.

However, the analyst must also review:

- Branch warnings

- Repeat records

- Unsupported structural variants

- CNV evidence

- ClinPGx findings

A result outside the ordinary ranked table may still be important.

20.13 Validation outcome
------------------------

The project used thirteen prepared synthetic VCFs.

The validation result was:

Structural preflight:

13 of 13 prepared VCFs passed

Complete final behavioural audit:

12 cases included

Cases passing the final audit:

12

Final audit failures:

0

Patient 13 passed structural preflight but was intentionally not processed through the complete workflow within the available project timeframe.

The correct statement is therefore:

All thirteen prepared synthetic VCFs passed structural preflight, and all twelve cases included in the complete final audit met their expected candidate or analytical-route result.

It would be inaccurate to state that all thirteen cases completed the full final pipeline.

20.14 Important validated safeguards
------------------------------------

The final project includes regression protection for:

- Production and validation resource isolation

- Allele-aware ClinPGx matching

- Shared inheritance models

- Sex and ploidy preflight

- Compound-heterozygous phase logic

- Exact patient-to-HPO matching

- G2P disease-label precedence

- Intake-report preservation

- Repeat-expansion routing

These safeguards address errors that could otherwise produce convincing but incorrect candidate interpretations.

20.15 Clinical-style report generation
--------------------------------------

After the pipeline output has been reviewed, selected evidence can be transferred into the clinical-style report builder.

The report includes:

- Patient and case information

- Testing indication

- Primary finding

- Patient phenotype

- Variant interpretation

- Gene information

- References

- Recommendations

- Signatory information

The report builder provides a live preview and allows the reviewed report to be printed or saved as a PDF.

The reporting stage must preserve:

- Genome build

- Variant representation

- Transcript version

- Zygosity

- Inheritance

- Classification source

- Confirmation status

- Uncertainty

- Clinical limitations

The generated sentence must be reviewed manually before export.

20.16 Relationship between the score and the report
---------------------------------------------------

The report should not simply copy:

Candidate rank 1

and describe it as causal.

The analyst must determine whether the candidate is suitable for reporting by reviewing:

- Gene–disease relevance

- Phenotype compatibility

- Inheritance compatibility

- Variant evidence

- Conflicting evidence

- Confirmation status

The universal score helps identify candidates requiring attention. It does not replace the reporting decision.

20.17 Relationship between the pipeline and clinical interpretation
-------------------------------------------------------------------

The pipeline provides:

- Structured annotation

- Evidence integration

- Candidate prioritisation

- Reproducibility

- Traceable outputs

A qualified genetics professional remains responsible for:

- Final variant classification

- Clinical correlation

- Confirmation requirements

- Family implications

- Clinical recommendations

- Report authorisation

The workflow supports interpretation but does not replace professional judgement.

20.18 Principal strengths
-------------------------

The major strengths of the completed project are:

- Reproducible GRCh38 workflow

- Universal case structure

- Variant-class-aware routing

- Multiple annotation tools

- Gene–disease integration

- HPO phenotype prioritisation

- Ploidy-aware inheritance analysis

- Phase-aware compound-heterozygous analysis

- Allele-aware ClinPGx matching

- Dedicated CNV analysis

- Repeat-expansion preservation

- Transparent candidate scoring

- Final report-generation workflow

Together, these features create a more complete analytical system than a workflow based only on consequence annotation.

20.19 Principal limitations
---------------------------

The main limitations are:

- Synthetic rather than clinical validation

- Dependence on variants already present in the VCF

- No direct read alignment or variant calling

- No routine BAM or CRAM review

- No independent laboratory confirmation

- Limited complex structural-variant interpretation

- Limited repeat-expansion analysis

- Limited ClinPGx haplotype coverage

- Incomplete family and segregation analysis

- Project-specific uncalibrated prioritisation score

A negative result does not exclude a genetic cause.

A causal variant may be:

- Absent from the submitted VCF

- Located in an unsupported variant class

- Missed because of incomplete phenotype information

- Associated with an unknown gene–disease relationship

20.20 Appropriate use of the workflow
-------------------------------------

The project is appropriate for:

- Educational genomic analysis

- Research workflow development

- Synthetic-case testing

- Candidate prioritisation

- Tool integration

- Evidence review

It is not independently suitable for:

- Final clinical diagnosis

- Unsupervised patient reporting

- Prenatal decision-making

- Medication changes

- Definitive recurrence-risk calculation

Every clinically relevant result requires specialist review and appropriate confirmation.

20.21 Final project conclusion
------------------------------

- The Genomic Analysis Lab project successfully developed a reproducible GRCh38 pipeline that integrates rare-disease variant annotation, phenotype evidence, gene–disease relationships, inheritance modelling, CNV analysis, repeat-expansion routing and selected pharmacogenomic interpretation.

The workflow guides the analyst from a prepared patient-level VCF to:

- A structurally validated case

- A set of annotated variants

- A phenotype- and inheritance-aware candidate ranking

- Separate CNV, repeat and PGx outputs

- A reviewed master candidate table

- A clinical-style genomic report

The final validation demonstrated reproducible behaviour across the implemented synthetic scenarios.

The project’s central contribution is not the automatic declaration of a diagnosis. Its contribution is the construction of a structured, auditable and evidence-aware process that helps an analyst determine which findings require the most careful review.

20.22 Final summary statement
-----------------------------

A concise final statement for the end of the report is:

This project developed and validated a reproducible GRCh38 workflow for the annotation and prioritisation of rare-disease variants together with selected pharmacogenomic evidence. The pipeline integrates functional consequence, clinical databases, gene–disease relationships, phenotype similarity, inheritance modelling, copy-number analysis and dedicated structural-variant routing. All twelve cases included in the final behavioural audit met their expected candidate or analytical-route result. The workflow concludes with a structured clinical-style reporting stage while preserving the distinction between computational prioritisation, professional interpretation and independent laboratory confirmation.

20.23 Final project completion criteria
---------------------------------------

The analytical project is complete when:

- ✓ The project environment is installed

- ✓ Required containers and resources are available

- ✓ The input VCF passes structural preflight

- ✓ The correct patient sample is selected

- ✓ GRCh38 is confirmed

- ✓ The phenotype file is valid

- ✓ Variants are routed by class

- ✓ Required annotation branches complete

- ✓ Gene–disease and phenotype evidence are generated

- ✓ Inheritance and ploidy are evaluated

- ✓ Compound-heterozygous evidence is assessed

- ✓ ClinPGx matching is allele aware

- ✓ CNV and repeat outputs are reviewed

- ✓ The master candidate table is generated

- ✓ The pipeline summary is generated

- ✓ Logs contain no unresolved fatal error

- ✓ The principal candidate is reviewed

- ✓ The clinical-style report is completed

- ✓ Confirmation status is reported truthfully

- ✓ The report is exported and stored securely

- ✓ Clinical and educational limitations are stated

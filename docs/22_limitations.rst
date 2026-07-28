.. _22-project-limitations-future-improvements-and-clinical-boundaries:

22. Project Limitations, Future Improvements and Clinical Boundaries
====================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


The project provides a reproducible framework for rare-disease variant prioritisation and selected pharmacogenomic interpretation. Its outputs remain computational findings derived from submitted VCF records, phenotype information, curated resources and automated prediction tools.

The pipeline is designed to answer:

-  

   .. container::

      Which variants should be reviewed first?

-  

   .. container::

      Which evidence supports or weakens each candidate?

-  

   .. container::

      Which variant classes require a specialist workflow?

-  

   .. container::

      Can the same analytical behaviour be reproduced?

-  

   .. container::

      It is not designed to answer independently:

-  

   .. container::

      Does the patient definitely have a particular disorder?

-  

   .. container::

      Is the reported variant clinically confirmed?

-  

   .. container::

      What treatment should be started, stopped or changed?

-  

   .. container::

      What is the exact recurrence risk for the family?

The principal limitations fall into the following categories:

Input-data limitations

│

├── Variant-detection limitations

├── Annotation-resource limitations

├── Phenotype limitations

├── Inheritance limitations

├── Variant-class limitations

├── Pharmacogenomic limitations

├── Validation limitations

└── Clinical-use limitations

.. _22-1-synthetic-validation-data:

22.1 Synthetic validation data
------------------------------

The final project audit used synthetic educational cases rather than a large cohort of independently diagnosed patients.

Synthetic cases are useful because they allow:

-  

   .. container::

      Known expected candidate

-  

   .. container::

      Controlled background variants

-  

   .. container::

      Known genotype structure

-  

   .. container::

      Defined HPO profile

-  

   .. container::

      Reproducible regression testing

-  

   .. container::

      Safe public documentation

-  

   .. container::

      No patient-identification risk

However, synthetic data usually contain less complexity than clinical genomic data.

Real cases may include:

-  

   .. container::

      Incomplete coverage

-  

   .. container::

      Sequencing artefacts

-  

   .. container::

      Low-quality genotypes

-  

   .. container::

      Complex multiallelic loci

-  

   .. container::

      Population-specific variation

-  

   .. container::

      Several plausible candidates

-  

   .. container::

      Incomplete phenotype information

-  

   .. container::

      Unexpected inheritance

-  

   .. container::

      Mosaicism

-  

   .. container::

      Multiple molecular diagnoses

Therefore, successful synthetic-case recovery demonstrates correct behaviour for the implemented test scenarios, not general clinical diagnostic performance.

.. _22-2-scope-of-the-final-validation:

22.2 Scope of the final validation
----------------------------------

Thirteen synthetic VCFs were prepared and passed structural preflight.

The complete final audit included Patients 01–12:

Audited cases: 12

Passed cases: 12

Failed cases: 0

Patient 13 was intentionally not processed through the complete workflow within the project timeframe.

The final report must therefore state:

Thirteen VCFs passed structural preflight, but only

twelve were included in the complete final audit.

It must not state:

All thirteen cases passed the complete pipeline.

.. _22-3-clinical-sensitivity-and-specificity-were-not-measured:

22.3 Clinical sensitivity and specificity were not measured
-----------------------------------------------------------

The project did not calculate formal clinical-performance metrics such as:

-  

   .. container::

      Sensitivity

-  

   .. container::

      Specificity

-  

   .. container::

      Positive predictive value

-  

   .. container::

      Negative predictive value

-  

   .. container::

      False-positive rate

-  

   .. container::

      False-negative rate

-  

   .. container::

      Diagnostic yield

These measurements would require:

-  a sufficiently large independent cohort;

-  confirmed molecular diagnoses;

-  blinded analysis;

-  clearly defined positive and negative cases;

-  appropriate statistical evaluation;

-  orthogonal validation.

The project’s validation result should therefore be described as:

Software and workflow validation

rather than:

Clinical validation

.. _22-4-dependence-on-the-submitted-vcf:

22.4 Dependence on the submitted VCF
------------------------------------

The pipeline analyses variants already present in the input VCF.

It does not independently perform:

-  

   .. container::

      Read alignment

-  

   .. container::

      Base-quality recalibration

-  

   .. container::

      Variant calling

-  

   .. container::

      CNV calling from read depth

-  

   .. container::

      Structural-variant discovery

-  

   .. container::

      Repeat-expansion calling from reads

Consequently, a causal variant cannot be prioritised when it is absent from the submitted VCF.

A missing variant may result from:

-  

   .. container::

      Insufficient sequencing coverage

-  

   .. container::

      Poor read alignment

-  

   .. container::

      Variant-caller filtering

-  

   .. container::

      Low variant allele fraction

-  

   .. container::

      Complex genomic sequence

-  

   .. container::

      Incorrect genome build

-  

   .. container::

      Unsupported variant representation

A negative pipeline result does not prove that no genetic cause is present.

.. _22-5-lack-of-bam-or-cram-analysis:

22.5 Lack of BAM or CRAM analysis
---------------------------------

The workflow generally begins from a VCF and does not inspect the original sequencing reads.

Without BAM or CRAM data, the pipeline cannot directly assess:

-  

   .. container::

      Read depth

-  

   .. container::

      Allele balance

-  

   .. container::

      Mapping quality

-  

   .. container::

      Strand bias

-  

   .. container::

      Local alignment quality

-  

   .. container::

      Soft-clipped reads

-  

   .. container::

      Breakpoint support

-  

   .. container::

      Repeat-supporting reads

The VCF’s genotype and quality fields are therefore accepted as supplied, subject to structural and logical checks.

Important candidates should be reviewed in the original sequencing data where available.

.. _22-6-no-independent-variant-confirmation:

22.6 No independent variant confirmation
----------------------------------------

The workflow does not replace orthogonal confirmation methods such as:

-  

   .. container::

      Sanger sequencing

-  

   .. container::

      MLPA

-  

   .. container::

      qPCR

-  

   .. container::

      Digital PCR

-  

   .. container::

      Chromosomal microarray

-  

   .. container::

      Long-read sequencing

-  

   .. container::

      Repeat-primed PCR

-  

   .. container::

      Southern blot

The appropriate confirmation method depends on the variant class.

For example:

+----------------------------+--------------------------------------------------------+
| **Variant type**           | **Possible confirmation approach**                     |
+============================+========================================================+
| SNV or short indel         | Sanger sequencing                                      |
+----------------------------+--------------------------------------------------------+
| Exon-level deletion        | MLPA or targeted copy-number assay                     |
+----------------------------+--------------------------------------------------------+
| Large CNV                  | Chromosomal microarray or another validated CNV method |
+----------------------------+--------------------------------------------------------+
| Repeat expansion           | Repeat-primed PCR or another locus-specific assay      |
+----------------------------+--------------------------------------------------------+
| Complex structural variant | Long-read or targeted breakpoint analysis              |
+----------------------------+--------------------------------------------------------+

The pipeline should report confirmation requirements rather than claiming confirmation.

.. _22-7-genome-build-limitation:

22.7 Genome-build limitation
----------------------------

The active workflow uses:

GRCh38

with chr-prefixed chromosome names.

The pipeline does not silently convert GRCh37 or hg19 inputs.

A wrong-build input may cause:

-  

   .. container::

      Reference-allele mismatches

-  

   .. container::

      Incorrect ClinVar matching

-  

   .. container::

      Incorrect gene annotation

-  

   .. container::

      Incorrect HPO-linked disease interpretation

-  

   .. container::

      Wrong PGx allele matching

Any future liftover component should:

-  preserve the original coordinates;

-  record the liftover tool and chain file;

-  report failed or ambiguous mappings;

-  verify REF alleles after conversion;

-  retain both original and converted identifiers.

.. _22-8-transcript-selection-limitations:

22.8 Transcript-selection limitations
-------------------------------------

VEP and SnpEff may annotate the same allele against several transcripts.

The predicted consequence can vary by transcript because:

-  

   .. container::

      Exon structures differ

-  

   .. container::

      Coding regions differ

-  

   .. container::

      Transcript expression differs

-  

   .. container::

      Transcript databases differ

MANE and canonical selections differ

A variant may be:

-  

   .. container::

      Frameshift in one transcript

-  

   .. container::

      Intronic in another transcript

-  

   .. container::

      Non-coding in another transcript

The pipeline retains transcript evidence, but automated prioritisation cannot always determine which transcript is clinically most relevant.

Important candidates require manual transcript review.

.. _22-9-functional-consequence-prediction-is-not-direct-evidence:

22.9 Functional-consequence prediction is not direct evidence
-------------------------------------------------------------

Annotations such as:

-  

   .. container::

      stop_gained

-  

   .. container::

      frameshift_variant

-  

   .. container::

      missense_variant

-  

   .. container::

      splice_donor_variant

-  

   .. container::

      describe predicted molecular consequences.

They do not independently establish:

-  

   .. container::

      Abnormal protein function

-  

   .. container::

      Loss of protein expression

-  

   .. container::

      Clinical pathogenicity

-  

   .. container::

      Disease causality

The consequence must be interpreted together with:

-  gene–disease validity;

-  disease mechanism;

-  transcript relevance;

-  population frequency;

-  phenotype;

-  inheritance;

-  clinical evidence.

.. _22-10-incomplete-prediction-coverage:

22.10 Incomplete prediction coverage
------------------------------------

Some variants may not receive predictions from every tool.

Examples include:

-  

   .. container::

      Variants outside supported transcript regions

-  

   .. container::

      Complex alleles

-  

   .. container::

      Large insertions

-  

   .. container::

      Symbolic variants

-  

   .. container::

      Variants near poorly annotated transcripts

-  

   .. container::

      Variants outside SpliceAI-supported contexts

A missing prediction should be reported as:

not_available

or an equivalent status.

It should not automatically be treated as benign evidence.

.. _22-11-clinvar-limitations:

22.11 ClinVar limitations
-------------------------

ClinVar evidence may be limited by:

-  

   .. container::

      Conflicting submissions

-  

   .. container::

      Low review status

-  

   .. container::

      Old interpretations

-  

   .. container::

      Condition-name differences

-  

   .. container::

      Incomplete allele representation

-  

   .. container::

      Disease assertions unrelated to the patient

A ClinVar classification should be reviewed with:

-  

   .. container::

      CLNSIG

-  

   .. container::

      CLNDN

-  

   .. container::

      CLNREVSTAT

-  

   .. container::

      Exact allele

-  

   .. container::

      Genome build

-  

   .. container::

      Release date

The absence of a ClinVar match does not mean that a variant is benign.

.. _22-12-population-frequency-limitations:

22.12 Population-frequency limitations
--------------------------------------

Cached gnomAD frequencies provide useful population context, but they may not reflect:

-  

   .. container::

      The latest release

-  

   .. container::

      Every ancestry

-  

   .. container::

      Every genomic region

-  

   .. container::

      Every structural variant

-  

   .. container::

      Every disease-specific frequency threshold

The project intentionally avoids downloading the complete gnomAD dataset.

The workflow uses frequencies available through existing annotation resources, while the primary candidate should be checked manually against the current gnomAD website during final review.

Population rarity supports plausibility but does not prove pathogenicity.

.. _22-13-gene-disease-resource-limitations:

22.13 Gene–disease resource limitations
---------------------------------------

Gene2Phenotype and similar resources are continuously updated.

Limitations include:

-  

   .. container::

      New disease genes not yet included

-  

   .. container::

      Changing confidence classifications

-  

   .. container::

      Different disease labels

-  

   .. container::

      Incomplete variant-mechanism information

-  

   .. container::

      Different inheritance terminology

The project isolates official production relationships from local validation additions.

A missing G2P relationship may indicate incomplete resource coverage rather than absence of biological relevance.

.. _22-14-hpo-phenotype-limitations:

22.14 HPO phenotype limitations
-------------------------------

Phenotype prioritisation depends strongly on the supplied HPO terms.

The result may be affected by:

-  

   .. container::

      Incomplete clinical examination

-  

   .. container::

      Broad HPO terms

-  

   .. container::

      Incorrect terms

-  

   .. container::

      Age-dependent features

-  

   .. container::

      Unrecorded negative findings

-  

   .. container::

      Phenotypic variability

-  

   .. container::

      Ontology annotation gaps

A strong phenotype match can support prioritisation, but it cannot establish causality.

A weak phenotype match may not exclude a condition when the clinical profile is incomplete.

Future improvements should include:

-  

   .. container::

      Negated HPO terms

-  

   .. container::

      Onset information

-  

   .. container::

      Severity

-  

   .. container::

      Age-dependent weighting

-  

   .. container::

      Term confidence

-  

   .. container::

      Longitudinal phenotype updates

.. _22-15-disease-identity-resolution-limitations:

22.15 Disease-identity resolution limitations
---------------------------------------------

The project harmonises disease names across:

-  

   .. container::

      Gene2Phenotype

-  

   .. container::

      ClinVar

-  

   .. container::

      MONDO

However, disease mappings may remain uncertain when:

-  

   .. container::

      One source uses a broad syndrome label

-  

   .. container::

      Another uses a specific subtype

-  

   .. container::

      A ClinVar record lists several conditions

-  

   .. container::

      MONDO mappings are incomplete

The same phenotype has several molecular causes

The pipeline therefore preserves:

-  

   .. container::

      Original G2P disease label

-  

   .. container::

      Original ClinVar condition

-  

   .. container::

      Resolved MONDO identity

-  

   .. container::

      Resolution status

The harmonised disease label should not replace the original evidence.

.. _22-16-inheritance-limitations:

22.16 Inheritance limitations
-----------------------------

The pipeline evaluates inheritance compatibility using the available genotype, patient sex, chromosome ploidy and curated disease model.

It cannot fully assess inheritance without family data.

A single-sample VCF cannot confirm:

-  

   .. container::

      De novo status

-  

   .. container::

      Maternal or paternal origin

-  

   .. container::

      Segregation

-  

   .. container::

      Reduced penetrance

-  

   .. container::

      Parental mosaicism

When parental data are absent, the report should use:

inheritance_not_assessed

or an equivalent status.

.. _22-17-compound-heterozygous-limitations:

22.17 Compound-heterozygous limitations
---------------------------------------

The pipeline correctly distinguishes:

-  

   .. container::

      Phased trans

-  

   .. container::

      Cis

-  

   .. container::

      Possible unphased pair

-  

   .. container::

      Phase unresolved

-  

   .. container::

      Homozygous biallelic

However, phase information in a VCF may be:

Absent

-  

   .. container::

      Local rather than chromosome-wide

-  

   .. container::

      Incorrectly generated

-  

   .. container::

      Based on statistical rather than parental phasing

A phased-trans result means that the submitted VCF represents the variants on opposite haplotypes within a shared phase context.

It does not automatically mean that parental testing confirmed trans inheritance.

.. _22-18-mosaicism-limitations:

22.18 Mosaicism limitations
---------------------------

Low-level mosaic variants may be absent from a standard germline VCF.

The current pipeline does not perform dedicated mosaic detection from sequencing reads.

Mosaicism analysis may require:

-  

   .. container::

      BAM or CRAM review

-  

   .. container::

      Variant allele fraction

-  

   .. container::

      Read-level quality

-  

   .. container::

      Deep sequencing

-  

   .. container::

      Tissue-specific testing

-  

   .. container::

      Specialised mosaic callers

A variant represented as heterozygous in the VCF may also require allele-balance review before mosaicism is considered.

.. _22-19-mitochondrial-limitations:

22.19 Mitochondrial limitations
-------------------------------

The workflow contains mitochondrial-aware inheritance handling, but complete mitochondrial interpretation requires additional considerations such as:

-  

   .. container::

      Heteroplasmy

-  

   .. container::

      Tissue specificity

-  

   .. container::

      Maternal segregation

-  

   .. container::

      Mitochondrial haplogroup

-  

   .. container::

      NUMT interference

-  

   .. container::

      Coverage variation

The current project does not provide a comprehensive mitochondrial-disease workflow.

A mitochondrial candidate therefore requires specialist review and appropriate heteroplasmy information.

.. _22-20-copy-number-variant-limitations:

22.20 Copy-number variant limitations
-------------------------------------

The CNV branch analyses supported DEL and DUP records supplied in the VCF or BED input.

It does not independently call CNVs from sequencing data.

CNV interpretation may be limited by:

-  

   .. container::

      Imprecise breakpoints

-  

   .. container::

      Incorrect CNV type

-  

   .. container::

      Missing copy-number value

-  

   .. container::

      Incomplete exon resolution

-  

   .. container::

      Unknown duplication orientation

-  

   .. container::

      Complex rearrangement structure

-  

   .. container::

      Caller-specific representation

A duplication does not necessarily produce functional increased dosage.

A partial duplication may be disruptive rather than dosage increasing.

.. _22-21-automated-cnv-classification-limitations:

22.21 Automated CNV classification limitations
----------------------------------------------

AnnotSV, ClassifyCNV and ISV-CNV provide complementary evidence but may use overlapping resources.

Agreement among the three tools should not be interpreted as three fully independent confirmations.

Automated CNV interpretation may omit:

-  

   .. container::

      Patient-specific phenotype

-  

   .. container::

      Family segregation

-  

   .. container::

      Breakpoint-level gene disruption

-  

   .. container::

      Updated literature

-  

   .. container::

      Regulatory effects

-  

   .. container::

      Complex rearrangement structure

The universal CNV score is a prioritisation value, not a formal clinical classification.

.. _22-22-limited-canonical-cnv-validation:

22.22 Limited canonical CNV validation
--------------------------------------

The final Patients 01–12 canonical results primarily demonstrate small-variant, repeat-routing and selected ClinPGx behaviour.

No additional canonical CNV diagnosis should be claimed unless it appears explicitly in the final audit evidence.

The CNV branch has:

-  

   .. container::

      Tool installation

-  

   .. container::

      Input validation

-  

   .. container::

      Workflow integration

-  

   .. container::

      Scoring architecture

but requires a larger set of dedicated CNV validation cases.

Future CNV validation should include:

-  

   .. container::

      Whole-gene deletion

-  

   .. container::

      Single-exon deletion

-  

   .. container::

      Partial-gene duplication

-  

   .. container::

      Multigene deletion

-  

   .. container::

      Triplosensitive duplication

-  

   .. container::

      Benign population CNV

-  

   .. container::

      VUS CNV

-  

   .. container::

      Imprecise-breakpoint CNV

.. _22-23-repeat-expansion-limitations:

22.23 Repeat-expansion limitations
----------------------------------

The current workflow detects and routes repeat-expansion records already present in the submitted VCF.

It does not independently estimate repeat size from BAM or CRAM reads.

Therefore, the status:

detected_not_interpreted

means that:

-  

   .. container::

      The record was detected

-  

   .. container::

      The supplied repeat information was preserved

-  

   .. container::

      The record was excluded from ordinary ranking

-  

   .. container::

      Specialist analysis is required

The project does not claim:

-  

   .. container::

      Independent repeat-size confirmation

-  

   .. container::

      Interruption-pattern analysis

-  

   .. container::

      Methylation analysis

-  

   .. container::

      Somatic instability analysis

.. _22-24-unsupported-structural-variants:

22.24 Unsupported structural variants
-------------------------------------

The workflow preserves but does not completely interpret:

-  

   .. container::

      Inversions

-  

   .. container::

      Breakends

-  

   .. container::

      Translocations

-  

   .. container::

      Mobile-element insertions

-  

   .. container::

      Complex rearrangements

-  

   .. container::

      Copy-neutral structural variants

These records require specialised structural-variant analysis.

Future improvements could include:

-  event-level breakend grouping;

-  breakpoint orientation interpretation;

-  gene-fusion detection;

-  long-read support;

-  optical genome mapping integration;

-  specialised mobile-element analysis.

.. _22-25-pharmacogenomic-limitations:

22.25 Pharmacogenomic limitations
---------------------------------

The ClinPGx branch uses a curated local reference and exact allele-aware genomic matching.

Its limitations include:

-  

   .. container::

      Limited curated loci

-  

   .. container::

      Incomplete star-allele coverage

-  

   .. container::

      No comprehensive haplotype phasing

-  

   .. container::

      No full structural-haplotype resolution

-  

   .. container::

      No automatic copy-number-aware CYP2D6 interpretation

-  

   .. container::

      No complete guideline engine

The controlled results such as:

-  

   .. container::

      TPMT \*1/\*3C

-  

   .. container::

      CYP2D6 \*1/\*4

-  

   .. container::

      DPYD \*1/\*2A

are simplified project-validation interpretations.

They should not be described as complete clinical pharmacogenomic testing.

.. _22-26-variants-only-vcf-limitation-in-pgx:

22.26 Variants-only VCF limitation in PGx
-----------------------------------------

A variants-only VCF usually contains non-reference sites but may omit positions where the patient is homozygous reference.

Therefore, absence of a PGx allele from the VCF does not prove:

Normal genotype

\*1 allele

Normal metaboliser status

Comprehensive diplotype assignment requires a test that covers all required defining variants and relevant structural variation.

.. _22-27-medication-recommendations-are-outside-scope:

22.27 Medication recommendations are outside scope
--------------------------------------------------

The pipeline must not instruct a patient to:

-  

   .. container::

      Start medication

-  

   .. container::

      Stop medication

-  

   .. container::

      Change a dose

-  

   .. container::

      Replace one drug with another

-  

   .. container::

      A PGx finding should instead be reported as:

-  

   .. container::

      A pharmacogenomic result requiring confirmation and review

against the current professional guideline.

Clinical decisions depend on:

-  confirmed genotype;

-  complete diplotype;

-  current guideline;

-  indication;

-  age;

-  other medications;

-  kidney and liver function;

-  treating clinician judgement.

.. _22-28-universal-scoring-limitations:

22.28 Universal scoring limitations
-----------------------------------

The universal score combines multiple evidence domains into a project-specific ranking value.

Limitations include:

-  

   .. container::

      Weights are project defined

-  

   .. container::

      Evidence sources are not fully independent

-  

   .. container::

      Missing evidence affects completeness

-  

   .. container::

      Resource updates may change scores

-  

   .. container::

      Different variant classes use different evidence

A score such as:

74.07

is not:

74.07% probability of pathogenicity

The score should only be compared within the same validated pipeline version and resource state.

.. _22-29-candidate-ranking-limitations:

22.29 Candidate-ranking limitations
-----------------------------------

The top-ranked candidate may not be the true causal variant.

Possible reasons include:

-  

   .. container::

      Causal variant absent from the VCF

-  

   .. container::

      Incomplete phenotype

-  

   .. container::

      Unknown disease gene

-  

   .. container::

      Incorrect inheritance assumption

-  

   .. container::

      Unrecognised complex variant

-  

   .. container::

      Resource gaps

-  

   .. container::

      Annotation error

-  

   .. container::

      Multiple diagnoses

All clinically plausible candidates should remain available for review rather than only the first-ranked row.

.. _22-30-multiple-diagnosis-limitation:

22.30 Multiple-diagnosis limitation
-----------------------------------

A patient may have:

-  

   .. container::

      One disorder caused by one variant

-  

   .. container::

      A blended phenotype from two disorders

-  

   .. container::

      A rare disease plus an independent PGx finding

-  

   .. container::

      A CNV plus a sequence variant

A ranking system that focuses only on one top candidate may underrepresent blended or multilocus diagnoses.

Future scoring should support:

-  

   .. container::

      Independent candidate clusters

-  

   .. container::

      Multiple-diagnosis hypotheses

-  

   .. container::

      Phenotype partitioning

-  

   .. container::

      Gene-pair or disease-pair analysis

.. _22-31-resource-update-effects:

22.31 Resource-update effects
-----------------------------

The pipeline uses resources that change over time.

Updates may alter:

-  

   .. container::

      ClinVar significance

-  

   .. container::

      G2P confidence

-  

   .. container::

      HPO annotations

-  

   .. container::

      MONDO terminology

-  

   .. container::

      gnomAD frequency

-  

   .. container::

      ClinGen dosage scores

-  

   .. container::

      Transcript consequences

-  

   .. container::

      PGx recommendations

A changed output after a resource update is not automatically a software defect.

However, every change must be:

-  

   .. container::

      Detected

-  

   .. container::

      Explained

-  

   .. container::

      Validated

-  

   .. container::

      Documented

Historical audit directories must remain preserved.

.. _22-32-software-and-container-limitations:

22.32 Software and container limitations
----------------------------------------

Pinned containers improve reproducibility but cannot eliminate every environmental dependency.

-  

   .. container::

      Potential issues include:

-  

   .. container::

      Unavailable container base image

-  

   .. container::

      Changed external download

-  

   .. container::

      Hardware-specific performance

-  

   .. container::

      WSL filesystem differences

-  

   .. container::

      Licensing restrictions

-  

   .. container::

      Archived software repositories

The project mitigates these risks through:

-  

   .. container::

      Definition files

-  

   .. container::

      Container checksums

-  

   .. container::

      Version manifests

-  

   .. container::

      Local resource snapshots

-  

   .. container::

      Validation tests

.. _22-33-licensing-and-redistribution-limitations:

22.33 Licensing and redistribution limitations
----------------------------------------------

Some tools and resources may have:

-  

   .. container::

      Non-commercial conditions

-  

   .. container::

      Academic-use restrictions

-  

   .. container::

      Registration requirements

-  

   .. container::

      Separate model licences

-  

   .. container::

      Redistribution restrictions

The GitHub repository should therefore contain:

-  

   .. container::

      Installation instructions

-  

   .. container::

      Build definitions

-  

   .. container::

      Source links

-  

   .. container::

      Licence notes

rather than unauthorised copies of restricted resources.

Before wider distribution or commercial use, each dependency’s licence must be reviewed.

.. _22-34-hardware-and-runtime-limitations:

22.34 Hardware and runtime limitations
--------------------------------------

Large genomic resources require substantial storage and memory.

Practical performance depends on:

-  

   .. container::

      Number of variants

-  

   .. container::

      CNV count

-  

   .. container::

      VEP cache size

-  

   .. container::

      Thread count

-  

   .. container::

      Available RAM

-  

   .. container::

      Disk speed

-  

   .. container::

      WSL storage location

The recommended hardware estimates in the manual are planning guidance rather than formal benchmarks.

Future work should measure:

-  

   .. container::

      Runtime per case

-  

   .. container::

      Peak memory

-  

   .. container::

      Disk usage

-  

   .. container::

      CPU utilisation

-  

   .. container::

      Stage-specific bottlenecks

across several input sizes.

.. _22-35-limited-automated-reporting:

22.35 Limited automated reporting
---------------------------------

The pipeline generates structured outputs and summaries, but final clinical-style reporting still requires manual review.

Automated report generation can introduce risks such as:

-  

   .. container::

      Overstated certainty

-  

   .. container::

      Omitted conflicting evidence

-  

   .. container::

      Incorrect transcript choice

-  

   .. container::

      Incomplete limitations

-  

   .. container::

      Inappropriate PGx advice

Future report generation should use controlled templates with mandatory evidence and limitation fields.

.. _22-36-no-regulatory-or-accreditation-status:

22.36 No regulatory or accreditation status
-------------------------------------------

The project was developed for educational and research-oriented workflow development.

It is not presented as:

-  

   .. container::

      An accredited diagnostic laboratory test

-  

   .. container::

      An approved medical device

-  

   .. container::

      A regulated clinical decision system

Clinical deployment would require additional processes such as:

-  

   .. container::

      Quality-management system

-  

   .. container::

      Analytical validation

-  

   .. container::

      Clinical validation

-  

   .. container::

      Change control

-  

   .. container::

      User training

-  

   .. container::

      Audit trails

-  

   .. container::

      Data-security review

-  

   .. container::

      Regulatory assessment

.. _22-37-clinical-boundaries:

22.37 Clinical boundaries
-------------------------

The pipeline may support:

-  

   .. container::

      Research analysis

-  

   .. container::

      Educational demonstrations

-  

   .. container::

      Synthetic-case validation

-  

   .. container::

      Candidate prioritisation

-  

   .. container::

      Tool comparison

-  

   .. container::

      Workflow development

-  

   .. container::

      It should not independently be used for:

-  

   .. container::

      Final diagnosis

-  

   .. container::

      Prenatal decision-making

-  

   .. container::

      Treatment selection

-  

   .. container::

      Dose modification

-  

   .. container::

      Predictive testing without counselling

-  

   .. container::

      Reporting to patients without specialist review

A qualified clinical genetics or laboratory professional must review any result intended for patient care.

.. _22-38-required-clinical-review:

22.38 Required clinical review
------------------------------

A clinically reviewed result should consider:

-  

   .. container::

      Patient phenotype

-  

   .. container::

      Family history

-  

   .. container::

      Pedigree

-  

   .. container::

      Consent

-  

   .. container::

      Test indication

-  

   .. container::

      Variant quality

-  

   .. container::

      Transcript relevance

-  

   .. container::

      Population frequency

-  

   .. container::

      Disease mechanism

-  

   .. container::

      Penetrance

-  

   .. container::

      Variable expressivity

-  

   .. container::

      Segregation

-  

   .. container::

      Confirmatory testing

The pipeline provides evidence for some of these categories but cannot replace the complete review.

.. _22-39-family-and-counselling-boundaries:

22.39 Family and counselling boundaries
---------------------------------------

The workflow may identify inheritance-compatible candidates but does not independently calculate definitive recurrence risk.

Formal recurrence-risk assessment may depend on:

-  

   .. container::

      Confirmed diagnosis

-  

   .. container::

      Parental testing

-  

   .. container::

      De novo status

-  

   .. container::

      Parental mosaicism

-  

   .. container::

      Penetrance

-  

   .. container::

      Germline mosaicism

-  

   .. container::

      Mode of inheritance

Genetic counselling should address:

-  uncertainty;

-  family implications;

-  reproductive options;

-  testing of relatives;

-  secondary findings;

-  VUS interpretation.

.. _22-40-future-improvement-trio-and-family-analysis:

22.40 Future improvement: trio and family analysis
--------------------------------------------------

A major future development would be support for:

-  

   .. container::

      Proband–mother–father trios

-  

   .. container::

      Sibling data

-  

   .. container::

      Extended pedigrees

This would allow:

-  

   .. container::

      De novo detection

-  

   .. container::

      Parental origin

-  

   .. container::

      Segregation

-  

   .. container::

      Confirmed trans configuration

-  

   .. container::

      Recessive carrier assessment

-  

   .. container::

      X-linked inheritance confirmation

The implementation should preserve family identifiers while protecting privacy.

.. _22-41-future-improvement-read-level-quality-review:

22.41 Future improvement: read-level quality review
---------------------------------------------------

Integration of BAM or CRAM data could support:

-  

   .. container::

      Depth checks

-  

   .. container::

      Allele-balance review

-  

   .. container::

      Mapping-quality review

-  

   .. container::

      Visual inspection

-  

   .. container::

      Mosaicism assessment

-  

   .. container::

      Breakpoint support

A future module could produce a review package for the top candidates rather than attempting to replace expert read inspection.

.. _22-42-future-improvement-comprehensive-structural-variant-analysis:

22.42 Future improvement: comprehensive structural-variant analysis
-------------------------------------------------------------------

Future structural-variant support could include:

-  

   .. container::

      BND event reconstruction

-  

   .. container::

      Inversion analysis

-  

   .. container::

      Translocation analysis

-  

   .. container::

      Gene-fusion annotation

-  

   .. container::

      Mobile-element insertion analysis

-  

   .. container::

      Complex CNV structures

This would require:

-  caller-aware parsing;

-  breakpoint pairing;

-  orientation analysis;

-  event-level rather than row-level interpretation;

-  dedicated validation cases.

.. _22-43-future-improvement-long-read-sequencing:

22.43 Future improvement: long-read sequencing
----------------------------------------------

Long-read data could improve:

-  

   .. container::

      Repeat-expansion sizing

-  

   .. container::

      Complex-SV resolution

-  

   .. container::

      Phasing

-  

   .. container::

      Pseudogene-rich regions

-  

   .. container::

      Structural pharmacogenomics

Long-read support would require separate callers, resources and validation rather than simply reusing the current short-variant workflow.

.. _22-44-future-improvement-expanded-cnv-validation:

22.44 Future improvement: expanded CNV validation
-------------------------------------------------

A dedicated CNV validation suite should include positive and negative controls for:

-  

   .. container::

      Haploinsufficient deletion

-  

   .. container::

      Triplosensitive duplication

-  

   .. container::

      Benign common CNV

-  

   .. container::

      Partial exon deletion

-  

   .. container::

      Partial duplication

-  

   .. container::

      Multigene syndrome

-  

   .. container::

      Breakpoint-disrupted gene

Expected outputs should define:

-  

   .. container::

      Correct interval conversion

-  

   .. container::

      Correct DEL or DUP mechanism

-  

   .. container::

      Correct tool execution

-  

   .. container::

      Correct gene–disease model

-  

   .. container::

      Correct phenotype prioritisation

.. _22-45-future-improvement-comprehensive-pgx-calling:

22.45 Future improvement: comprehensive PGx calling
---------------------------------------------------

A complete PGx module could include:

-  

   .. container::

      Full defining-variant coverage

-  

   .. container::

      Haplotype phasing

-  

   .. container::

      Copy-number analysis

-  

   .. container::

      Hybrid alleles

-  

   .. container::

      Gene conversions

-  

   .. container::

      No-call states

-  

   .. container::

      Guideline-version tracking

Particular attention would be required for structurally complex genes such as:

-  

   .. container::

      CYP2D6

A complete module should report assay limitations and genotype confidence.

.. _22-46-future-improvement-updated-api-and-resource-caching:

22.46 Future improvement: updated API and resource caching
----------------------------------------------------------

External APIs may change or become unavailable.

Future resource management should support:

-  

   .. container::

      Versioned API downloads

-  

   .. container::

      Local immutable caches

-  

   .. container::

      Retrieval metadata

-  

   .. container::

      Schema validation

-  

   .. container::

      Rate-limit handling

-  

   .. container::

      Offline fallback

API-derived results should be tied to:

-  

   .. container::

      Retrieval date

-  

   .. container::

      Endpoint

-  

   .. container::

      Response checksum

-  

   .. container::

      Parser version

.. _22-47-future-improvement-phenotype-enrichment:

22.47 Future improvement: phenotype enrichment
----------------------------------------------

Future phenotype processing could support:

-  

   .. container::

      Free-text-to-HPO assistance

-  

   .. container::

      Negated findings

-  

   .. container::

      Age of onset

-  

   .. container::

      Clinical severity

-  

   .. container::

      Temporal progression

-  

   .. container::

      Organ-system grouping

-  

   .. container::

      Phenotype quality scores

Any automated extraction from clinical text would require manual confirmation before it affects ranking.

.. _22-48-future-improvement-explainable-scoring:

22.48 Future improvement: explainable scoring
---------------------------------------------

The universal score could be made more transparent by reporting:

-  

   .. container::

      Individual evidence contributions

-  

   .. container::

      Penalties

-  

   .. container::

      Missing-evidence states

-  

   .. container::

      Maximum possible score

-  

   .. container::

      Reason for each rank

-  

   .. container::

      A candidate explanation might state:

-  

   .. container::

      Functional consequence: strong

-  

   .. container::

      ClinVar evidence: moderate

-  

   .. container::

      Phenotype evidence: strong

-  

   .. container::

      Inheritance evidence: partial

-  

   .. container::

      Population evidence: supportive

This would make the score easier to audit than a single numerical value.

.. _22-49-future-improvement-calibrated-scoring:

22.49 Future improvement: calibrated scoring
--------------------------------------------

The current scoring system is project-specific.

A future research phase could compare candidate scores against a large reference cohort and investigate:

-  

   .. container::

      Score calibration

-  

   .. container::

      Optimal weights

-  

   .. container::

      Rank-1 recovery

-  

   .. container::

      Top-5 recovery

-  

   .. container::

      False-positive burden

-  

   .. container::

      Performance by variant class

Such calibration would require independent data and should not be performed using only the same cases used to develop the scoring rules.

.. _22-50-future-improvement-continuous-integration:

22.50 Future improvement: continuous integration
------------------------------------------------

Compact tests could be run automatically when source code changes.

A CI workflow could perform:

-  

   .. container::

      Bash syntax validation

-  

   .. container::

      Python syntax validation

-  

   .. container::

      Unit tests

-  

   .. container::

      Resource-mode tests

-  

   .. container::

      Allele-aware PGx tests

-  

   .. container::

      Inheritance tests

-  

   .. container::

      HPO filename tests

Full annotation tests may remain local because they require large resources and containers.

No patient data should enter an external CI service.

.. _22-51-future-improvement-documentation-website:

22.51 Future improvement: documentation website
-----------------------------------------------

The current Word report can later be converted into a documentation website using:

-  

   .. container::

      MkDocs

-  

   .. container::

      Read the Docs

-  

   .. container::

      The website could include:

-  

   .. container::

      Installation

-  

   .. container::

      Workflow diagrams

-  

   .. container::

      Command reference

-  

   .. container::

      Output dictionary

-  

   .. container::

      Troubleshooting

-  

   .. container::

      Validation status

-  

   .. container::

      Version history

It should link to source code while excluding private case data and restricted resources.

.. _22-52-future-improvement-formal-release-management:

22.52 Future improvement: formal release management
---------------------------------------------------

Validated source states could be organised using:

-  

   .. container::

      Semantic versioning

-  

   .. container::

      Annotated Git tags

-  

   .. container::

      Release notes

-  

   .. container::

      Dated resource manifests

-  

   .. container::

      Migration notes

For example:

Major version:

Breaking workflow or schema change

Minor version:

New compatible feature

Patch version:

Bug fix without intended interface change

Every release should identify the corresponding validation audit.

.. _22-53-future-improvement-clinical-grade-quality-management:

22.53 Future improvement: clinical-grade quality management
-----------------------------------------------------------

Movement towards clinical use would require:

-  

   .. container::

      Document control

-  

   .. container::

      Standard operating procedures

-  

   .. container::

      Approved validation plan

-  

   .. container::

      Deviation management

-  

   .. container::

      Corrective and preventive actions

-  

   .. container::

      User access control

-  

   .. container::

      Competency assessment

-  

   .. container::

      Change approval

-  

   .. container::

      Periodic review

These organisational controls are outside the current educational project.

.. _22-54-future-improvement-priorities:

22.54 Future improvement priorities
-----------------------------------

A practical priority order is:

1. Verify and standardise all final script and resource paths.

2. Expand dedicated CNV validation.

3. Add trio and segregation analysis.

4. Add read-level quality review.

5. Expand PGx haplotype and copy-number support.

6. Add specialist repeat-calling integration.

7. Add complex structural-variant support.

8. Improve explainable scoring.

9. Develop automated documentation and CI.

10. Evaluate the workflow on an independent benchmark cohort.

.. _22-55-recommended-limitation-statement:

22.55 Recommended limitation statement
--------------------------------------

A concise report statement is:

The pipeline was validated using controlled synthetic cases

and should be interpreted as a reproducible candidate-

prioritisation workflow rather than a clinically validated

diagnostic system. Its performance depends on the

completeness of the submitted VCF, phenotype information,

resource versions and supported variant classes.

.. _22-56-recommended-clinical-boundary-statement:

22.56 Recommended clinical-boundary statement
---------------------------------------------

All findings require review by an appropriately qualified

genetics professional. The workflow does not independently

confirm variants, establish a clinical diagnosis, calculate

definitive recurrence risk or recommend medication changes.

.. _22-57-recommended-negative-result-statement:

22.57 Recommended negative-result statement
-------------------------------------------

Failure to identify a sufficiently supported candidate does

not exclude a genetic disorder. A causal variant may be

absent from the submitted VCF, located in an unsupported

variant class or remain unrecognised because of incomplete

phenotype or gene–disease knowledge.

.. _22-58-recommended-future-work-statement:

22.58 Recommended future-work statement
---------------------------------------

Future development should prioritise family-based analysis,

read-level quality assessment, expanded CNV and structural-

variant validation, comprehensive pharmacogenomic

haplotyping and testing against an independent benchmark

cohort.

.. _22-59-limitation-checklist:

22.59 Limitation checklist
--------------------------

The project limitations are reported adequately when:

✓ Synthetic validation is distinguished from clinical validation

✓ Sensitivity and specificity are not claimed

✓ Patient 13 is described accurately

✓ Dependence on the submitted VCF is stated

✓ Lack of BAM or CRAM analysis is stated

✓ Lack of independent confirmation is stated

✓ GRCh38-only scope is stated

✓ Transcript uncertainty is discussed

✓ Prediction tools are not treated as confirmation

✓ ClinVar and population-resource limitations are discussed

✓ Phenotype incompleteness is acknowledged

✓ Family and segregation limitations are stated

✓ Mosaicism limitations are stated

✓ Mitochondrial limitations are stated

✓ CNV and complex-SV limitations are stated

✓ Repeat-expansion sizing limitations are stated

✓ PGx coverage limitations are stated

✓ The universal score is not described as probability

✓ Clinical and medication boundaries are explicit

✓ Licensing and reproducibility limitations are acknowledged

.. _22-60-future-development-checklist:

22.60 Future-development checklist
----------------------------------

Future planning is complete when:

✓ Trio analysis is prioritised

✓ Read-level review is planned

✓ CNV validation is expanded

✓ Complex structural variants are considered

✓ Repeat-calling integration is planned

✓ PGx haplotype support is expanded

✓ Resource caching is versioned

✓ Phenotype modelling is improved

✓ Scoring becomes more explainable

✓ Independent benchmark evaluation is planned

✓ CI uses synthetic data only

✓ Documentation versioning is planned

✓ Clinical quality-management requirements are recognised

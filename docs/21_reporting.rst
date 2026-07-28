.. _21-documentation-scientific-reporting-and-responsible-interpretation-guidelines:

21. Documentation, Scientific Reporting and Responsible Interpretation Guidelines
=================================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


The final project report must explain not only what the pipeline produced, but also how the analysis was performed, which evidence was used, how uncertainty was handled and which conclusions remain outside the scope of the automated workflow.

The reporting process follows this structure:

Project design and objectives

│

▼

Software and resource setup

│

▼

Input preparation and quality control

│

▼

Variant annotation and branch routing

│

▼

Evidence integration and ranking

│

▼

Validation and reproducibility

│

▼

Responsible interpretation

│

▼

Limitations and future development

The report should distinguish clearly between:

-  

   .. container::

      Observed data

-  

   .. container::

      Tool-generated annotation

-  

   .. container::

      Pipeline-derived prioritisation

-  

   .. container::

      Analyst interpretation

-  

   .. container::

      Clinical confirmation

These categories must not be merged into one unsupported conclusion.

.. _21-1-purpose-of-the-written-report:

21.1 Purpose of the written report
----------------------------------

The report should allow a reader to understand:

-  

   .. container::

      Why the project was developed

-  

   .. container::

      Which variant classes it supports

-  

   .. container::

      How the workflow is organised

-  

   .. container::

      Which tools and databases are used

-  

   .. container::

      How evidence is combined

-  

   .. container::

      How the pipeline was validated

-  

   .. container::

      What the outputs mean

-  

   .. container::

      What the outputs do not mean

-  

   .. container::

      How the analysis can be reproduced

The report is therefore both:

A scientific description of the project

and:

A practical reproducibility manual

It should not read only as a command log or a list of downloaded tools.

.. _21-2-intended-audiences:

21.2 Intended audiences
-----------------------

The document may be read by several audiences.

.. _21-2-1-bioinformatics-readers:

21.2.1 Bioinformatics readers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

They require:

-  

   .. container::

      Directory structure

-  

   .. container::

      Input and output formats

-  

   .. container::

      Software versions

-  

   .. container::

      Commands

-  

   .. container::

      Pipeline scripts

-  

   .. container::

      Resource paths

-  

   .. container::

      Validation methods

-  

   .. container::

      Checksums

.. _21-2-2-genetics-readers:

21.2.2 Genetics readers
~~~~~~~~~~~~~~~~~~~~~~~

They require:

-  

   .. container::

      Gene–disease relationships

-  

   .. container::

      Inheritance models

-  

   .. container::

      Phenotype evidence

-  

   .. container::

      Variant consequences

-  

   .. container::

      CNV dosage mechanisms

-  

   .. container::

      Repeat-expansion handling

-  

   .. container::

      Interpretation limitations

.. _21-2-3-supervisors-and-assessors:

21.2.3 Supervisors and assessors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

They require:

-  

   .. container::

      Project aim

-  

   .. container::

      Original contribution

-  

   .. container::

      Technical challenges

-  

   .. container::

      Corrections made

-  

   .. container::

      Validation results

-  

   .. container::

      Evidence of reproducibility

-  

   .. container::

      Limitations

-  

   .. container::

      Future directions

.. _21-2-4-clinical-readers:

21.2.4 Clinical readers
~~~~~~~~~~~~~~~~~~~~~~~

They require:

-  

   .. container::

      Clear evidence summaries

-  

   .. container::

      Uncertainty statements

-  

   .. container::

      Inheritance context

-  

   .. container::

      Phenotype compatibility

-  

   .. container::

      Confirmation requirements

-  

   .. container::

      No unsupported diagnostic or treatment claims

The report should remain understandable to a scientifically informed reader who did not build the pipeline.

.. _21-3-recommended-document-structure:

21.3 Recommended document structure
-----------------------------------

The final Word document may use the following overall structure:

-  

   .. container::

      Title page

-  

   .. container::

      Abstract

-  

   .. container::

      Table of contents

-  

   .. container::

      List of figures

-  

   .. container::

      List of tables

-  

   .. container::

      List of abbreviations

1. Introduction

2. Project aim, objectives and scope

3. Project directory structure

4. Software installation and environment setup

5. Reference genome and core annotation resources

6. Specialised tool installation

7. Input data requirements and structural preflight

8. Universal pipeline architecture

9. Small-variant workflow

10. Gene–disease and phenotype analysis

11. Inheritance, sex, ploidy and compound heterozygosity

12. Pharmacogenomic analysis

13. Copy-number variant workflow

14. Repeat-expansion and unsupported-SV handling

15. Universal evidence scoring

16. Pipeline outputs

17. Validation strategy

18. End-to-end case execution

19. Troubleshooting and maintenance

20. Reproducibility and data governance

21. Scientific reporting and responsible interpretation

22. Limitations and future development

23. Conclusion

References

Appendices

The current sections already provide the main body of this structure.

.. _21-4-abstract:

21.4 Abstract
-------------

The abstract should summarise the project in approximately 200–300 words.

It should contain:

-  

   .. container::

      Background

-  

   .. container::

      Problem

-  

   .. container::

      Project objective

-  

   .. container::

      Main workflow

-  

   .. container::

      Key technical developments

-  

   .. container::

      Validation approach

-  

   .. container::

      Principal result

-  

   .. container::

      Main limitation

-  

   .. container::

      Conclusion

A suitable abstract structure is:

Background:

Rare-disease analysis requires the integration of variant,

phenotype, inheritance and gene–disease evidence.

Objective:

This project developed a reproducible GRCh38 pipeline for

small variants, CNVs, repeat-expansion routing and selected

pharmacogenomic findings.

Methods:

The workflow used normalisation, VEP, SnpEff, ClinVar,

SpliceAI, Gene2Phenotype, HPO, MONDO, AnnotSV,

ClassifyCNV, ISV-CNV and a curated ClinPGx reference.

Results:

The pipeline implemented production-resource isolation,

allele-aware PGx matching, ploidy-aware inheritance,

phase-aware compound-heterozygous aggregation and

dedicated repeat-expansion routing. Twelve synthetic cases

passed the final project audit.

Conclusion:

The workflow provides reproducible candidate prioritisation

but does not replace clinical interpretation or confirmatory

testing.

The abstract should not contain installation commands, large tables or detailed directory paths.

.. _21-5-introduction-writing:

21.5 Introduction writing
-------------------------

The introduction should move from the broad problem to the specific project.

A useful order is:

Rare-disease diagnostic challenge

↓

Importance of genomic testing

↓

Need for variant annotation

↓

Need for phenotype and inheritance integration

↓

Limitations of individual annotation tools

↓

Need for a reproducible universal workflow

↓

Aim of the present project

The introduction should explain why a variant cannot be prioritised from consequence alone.

For example:

A predicted damaging variant may remain clinically

irrelevant when it occurs in an unrelated gene, fails to

match the patient phenotype or is incompatible with the

expected inheritance model.

This naturally leads to the project’s evidence-integration design.

.. _21-6-avoiding-plagiarism:

21.6 Avoiding plagiarism
------------------------

Information should be understood and rewritten in the author’s own scientific language.

A safe process is:

1. Read the source.

2. Identify the main concept.

3. Close or move away from the original wording.

4. Write the concept in your own structure.

5. Compare with the source.

6. Revise phrases that remain too similar.

7. Add the citation.

Changing only a few words is not sufficient.

For example, avoid copying a source sentence and replacing:

important → significant

uses → employs

shows → demonstrates

Instead, change the organisation of the explanation.

Original-style statement:

VEP predicts the effect of genomic variants on transcripts,

proteins and regulatory regions.

Independent formulation:

Within the workflow, VEP links each normalised allele to

the transcripts and genomic features it may affect,

providing consequence and transcript-level evidence for

later prioritisation.

The second version is organised around the project’s use of the tool.

.. _21-7-citation-requirements:

21.7 Citation requirements
--------------------------

Citations should be used for:

-  

   .. container::

      Tool descriptions

-  

   .. container::

      Database descriptions

-  

   .. container::

      Variant-classification standards

-  

   .. container::

      Inheritance or disease claims

-  

   .. container::

      Software algorithms

-  

   .. container::

      Resource releases

-  

   .. container::

      Clinical guidelines

-  

   .. container::

      Pharmacogenomic recommendations

Citations are generally not required for:

-  

   .. container::

      Commands developed for this project

-  

   .. container::

      Project directory descriptions

-  

   .. container::

      Observed local validation results

-  

   .. container::

      Project-specific source filenames

-  

   .. container::

      Original workflow diagrams

The report should use one citation style consistently, such as:

-  

   .. container::

      Vancouver

-  

   .. container::

      Harvard

-  

   .. container::

      APA

The citation style selected by the university or supervisor should take precedence.

.. _21-8-primary-and-secondary-sources:

21.8 Primary and secondary sources
----------------------------------

Primary or official sources should be preferred.

Recommended source hierarchy:

1. Original research paper or technical standard

2. Official tool documentation

3. Official database documentation

4. Peer-reviewed review article

5. Educational website

6. Informal tutorial or blog

For software, cite both:

The original software publication

and, where relevant:

The official documentation or version page

A third-party tutorial should not be used as the only evidence for a tool’s scientific function.

.. _21-9-reference-management:

21.9 Reference management
-------------------------

A reference manager may be used to prevent inconsistent citations.

-  

   .. container::

      Common options include:

-  

   .. container::

      Zotero

-  

   .. container::

      Mendeley

-  

   .. container::

      EndNote

Each saved reference should include:

-  

   .. container::

      Authors

-  

   .. container::

      Year

-  

   .. container::

      Title

-  

   .. container::

      Journal or organisation

-  

   .. container::

      Volume and pages where applicable

-  

   .. container::

      DOI or stable URL

-  

   .. container::

      Access date for web resources

Duplicate references should be merged before final submission.

.. _21-10-scientific-tone:

21.10 Scientific tone
---------------------

The report should use clear, cautious scientific wording.

Prefer:

-  

   .. container::

      The pipeline identified…

-  

   .. container::

      The annotation indicated…

-  

   .. container::

      The result was compatible with…

-  

   .. container::

      The candidate was prioritised because…

-  

   .. container::

      The evidence supported…

-  

   .. container::

      The finding requires confirmation…

Avoid:

-  

   .. container::

      The pipeline proved…

-  

   .. container::

      This definitely caused the disease…

-  

   .. container::

      The patient certainly has…

-  

   .. container::

      The result guarantees…

-  

   .. container::

      The program diagnosed…

The strength of wording should match the strength of evidence.

.. _21-11-evidence-language-hierarchy:

21.11 Evidence-language hierarchy
---------------------------------

A useful interpretation hierarchy is:

+-----------------------------+----------------------------------------+
| **Evidence level**          | **Appropriate wording**                |
+=============================+========================================+
| Direct observation          | “The VCF contained…”                   |
+-----------------------------+----------------------------------------+
| Tool annotation             | “VEP annotated the variant as…”        |
+-----------------------------+----------------------------------------+
| Database assertion          | “ClinVar reported…”                    |
+-----------------------------+----------------------------------------+
| Pipeline calculation        | “The pipeline assigned…”               |
+-----------------------------+----------------------------------------+
| Compatibility assessment    | “The finding was compatible with…”     |
+-----------------------------+----------------------------------------+
| Prioritisation result       | “The variant was prioritised…”         |
+-----------------------------+----------------------------------------+
| Clinical conclusion         | “Requires clinical confirmation…”      |
+-----------------------------+----------------------------------------+

This prevents tool output from being presented as an independent laboratory confirmation.

.. _21-12-reporting-genomic-coordinates:

21.12 Reporting genomic coordinates
-----------------------------------

Every reported variant should include:

-  

   .. container::

      Genome build

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

      For this project:

-  

   .. container::

      Genome build: GRCh38

-  

   .. container::

      Chromosome convention: chr-prefixed

Example:

GRCh38 chr12:102840493 G>A

A stable project key may be written as:

chr12:102840493:G>A

The report should not list a coordinate without its genome build.

.. _21-13-hgvs-nomenclature:

21.13 HGVS nomenclature
-----------------------

Where reliable transcript annotation is available, include:

-  

   .. container::

      Genomic representation

-  

   .. container::

      Transcript identifier

-  

   .. container::

      Coding HGVS

-  

   .. container::

      Protein HGVS

-  

   .. container::

      Example structure:

Genomic:

GRCh38 chr12:102840493 G>A

Transcript:

NM_XXXXXX.X

Coding:

c.XXXG>A

Protein:

p.(XXX)

The transcript version should be retained.

Do not manually construct HGVS expressions when the transcript, strand or normalisation is uncertain.

Use the VEP or SnpEff annotation and confirm important variants through an appropriate HGVS validation resource before formal reporting.

.. _21-14-transcript-reporting:

21.14 Transcript reporting
--------------------------

A gene can have several transcripts.

The report should state whether the selected transcript was:

-  

   .. container::

      MANE Select

-  

   .. container::

      Canonical

-  

   .. container::

      Clinically relevant

-  

   .. container::

      Longest coding transcript

-  

   .. container::

      Another justified transcript

When several transcripts produce different effects, report the discrepancy.

For example:

The variant was predicted to cause a frameshift in the

MANE Select transcript but was intronic in an alternative

transcript.

Do not report only the most severe consequence without identifying the transcript.

.. _21-15-reporting-vep-and-snpeff-results:

21.15 Reporting VEP and SnpEff results
--------------------------------------

VEP and SnpEff should be described as functional-annotation tools.

A result may be reported as:

VEP annotated the variant as a missense variant in the

MANE Select transcript, while SnpEff produced a concordant

moderate-impact missense annotation.

When they disagree:

VEP and SnpEff assigned different consequences because

they used different transcript models. The transcript-level

annotations were therefore reviewed individually.

Do not write:

Both tools confirmed pathogenicity.

Neither tool independently classifies a variant as clinically pathogenic merely from consequence prediction.

.. _21-16-reporting-clinvar-evidence:

21.16 Reporting ClinVar evidence
--------------------------------

ClinVar evidence should include:

-  

   .. container::

      Clinical significance

-  

   .. container::

      Condition

-  

   .. container::

      Review status

-  

   .. container::

      Release or retrieval date

Suitable wording is:

ClinVar listed the allele as pathogenic for the stated

condition, with the recorded review status shown in the

annotation output.

When submissions conflict:

ClinVar contained conflicting interpretations; therefore,

the database evidence was not treated as a single

unambiguous pathogenic assertion.

A ClinVar condition should not replace the project’s resolved gene–disease model automatically.

.. _21-17-reporting-population-frequency:

21.17 Reporting population frequency
------------------------------------

Population-frequency reporting should include:

-  

   .. container::

      Database

-  

   .. container::

      Population or global frequency

-  

   .. container::

      Exome or genome source

-  

   .. container::

      Release or retrieval context

-  

   .. container::

      Suitable wording:

-  

   .. container::

      The allele was rare in the cached gnomAD exome data,

.. container::

   supporting compatibility with a rare disorder but not

.. container::

   establishing pathogenicity.

Avoid:

-  

   .. container::

      The variant is absent from gnomAD, so it is pathogenic.

-  

   .. container::

      Absence from a population database is supporting context only.

-  

   .. container::

      The principal candidate should be checked manually against the current gnomAD website during final review.

.. _21-18-reporting-spliceai-evidence:

21.18 Reporting SpliceAI evidence
---------------------------------

Include:

-  

   .. container::

      Maximum delta score

-  

   .. container::

      Specific gain or loss score

-  

   .. container::

      Predicted relative position

Gene

Suitable wording:

SpliceAI predicted a possible donor-loss effect with a

maximum delta score of X. This prediction requires RNA or

other functional confirmation.

Avoid:

SpliceAI confirmed abnormal splicing.

SpliceAI is predictive, not confirmatory.

.. _21-19-reporting-gene-disease-relationships:

21.19 Reporting gene–disease relationships
------------------------------------------

For Gene2Phenotype evidence, report:

-  

   .. container::

      Gene

-  

   .. container::

      Disease

-  

   .. container::

      Confidence category

-  

   .. container::

      Allelic requirement

-  

   .. container::

      Molecular mechanism

-  

   .. container::

      Expected variant consequence

-  

   .. container::

      Resource mode

Suitable wording:

Gene2Phenotype linked the gene to the resolved disorder

through a biallelic autosomal model with loss of function

as the expected molecular mechanism.

The report should state whether the relationship came from:

-  

   .. container::

      Official production G2P

-  

   .. container::

      Controlled validation G2P

A validation-only relationship must never be described as an official production record.

.. _21-20-reporting-phenotype-evidence:

21.20 Reporting phenotype evidence
----------------------------------

Phenotype reporting should include:

-  

   .. container::

      Patient HPO terms

-  

   .. container::

      Exact matches

-  

   .. container::

      Semantic matches

-  

   .. container::

      Phenotype score

-  

   .. container::

      Missing or negated features

-  

   .. container::

      Limitations

Suitable wording:

The candidate showed substantial semantic similarity to

the supplied HPO profile. This increased prioritisation but

did not independently establish the diagnosis.

When no HPO terms were supplied:

Phenotype-based prioritisation was not assessed because a

valid HPO profile was unavailable.

Do not report this as a phenotype mismatch.

.. _21-21-reporting-inheritance-evidence:

21.21 Reporting inheritance evidence
------------------------------------

Inheritance reporting should state:

-  

   .. container::

      Observed genotype

-  

   .. container::

      Zygosity

-  

   .. container::

      Expected disease model

-  

   .. container::

      Sex and ploidy context

-  

   .. container::

      Compatibility status

-  

   .. container::

      Family-data availability

Example:

The heterozygous genotype was compatible with the

monoallelic autosomal disease model.

For a recessive model with one allele:

Only one heterozygous candidate was identified. The

biallelic requirement was therefore not fully satisfied.

For an X-linked variant:

Interpretation incorporated the resolved sex and expected

chromosome ploidy.

Do not infer de novo inheritance from a single-sample VCF.

.. _21-22-reporting-compound-heterozygosity:

21.22 Reporting compound heterozygosity
---------------------------------------

The report must distinguish:

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

Suitable wording for phased trans:

The two heterozygous variants occurred on opposite

haplotypes within a shared phase set in the submitted VCF,

supporting a phased-trans configuration.

This should not be rewritten as:

Parental testing confirmed that the variants were in trans.

unless parental testing was actually performed.

For unphased variants:

The two variants formed a possible compound-heterozygous

pair, but trans configuration was not established.

.. _21-23-reporting-cnvs:

21.23 Reporting CNVs
--------------------

A CNV report should include:

-  

   .. container::

      Genome build

-  

   .. container::

      Chromosome

-  

   .. container::

      Start

-  

   .. container::

      End

-  

   .. container::

      Size

-  

   .. container::

      DEL or DUP

-  

   .. container::

      Genotype or copy number where available

-  

   .. container::

      Breakpoint precision

-  

   .. container::

      Gene content

-  

   .. container::

      Dosage evidence

-  

   .. container::

      Tool classifications

-  

   .. container::

      Phenotype compatibility

-  

   .. container::

      Inheritance

Suitable wording:

A heterozygous deletion spanning the stated GRCh38 interval

was identified and annotated using AnnotSV, ClassifyCNV and

ISV-CNV.

Do not write:

The gene copy number was zero

unless copy-number evidence supports complete loss.

.. _21-24-reporting-annotsv-results:

21.24 Reporting AnnotSV results
-------------------------------

AnnotSV output should be described at both levels:

-  

   .. container::

      Full interval

-  

   .. container::

      Split gene or transcript annotation

Suitable wording:

AnnotSV generated one full-interval record and several

split transcript-level records for the same CNV.

Do not count split rows as separate CNVs.

Important reported fields may include:

-  

   .. container::

      Cytoband

-  

   .. container::

      Gene

-  

   .. container::

      Transcript

-  

   .. container::

      CDS overlap

-  

   .. container::

      Haploinsufficiency evidence

-  

   .. container::

      Triplosensitivity evidence

-  

   .. container::

      AnnotSV ranking

-  

   .. container::

      ACMG class

.. _21-25-reporting-classifycnv-results:

21.25 Reporting ClassifyCNV results
-----------------------------------

Suitable wording:

ClassifyCNV assigned the interval a classification and

quantitative evidence score according to its implemented

constitutional CNV framework.

The report should also state that:

The automated classification was reviewed together with

phenotype, inheritance and breakpoint information.

Do not present ClassifyCNV as a complete clinical diagnosis.

.. _21-26-reporting-isv-cnv-results:

21.26 Reporting ISV-CNV results
-------------------------------

Suitable wording:

ISV-CNV produced a machine-learning prediction and

associated probability for the CNV. SHAP values were

retained to show which model features influenced the

prediction.

Avoid:

The probability means the patient has an X% chance of

disease.

The value is a model output, not patient-level disease probability.

.. _21-27-reporting-repeat-expansions:

21.27 Reporting repeat expansions
---------------------------------

A repeat report should include:

-  

   .. container::

      Locus

-  

   .. container::

      Gene

-  

   .. container::

      Motif

-  

   .. container::

      Reported repeat count

-  

   .. container::

      Confidence interval

-  

   .. container::

      Genotype

-  

   .. container::

      Threshold and source

-  

   .. container::

      Routing status

-  

   .. container::

      Required follow-up

Suitable wording:

The submitted VCF contained a repeat-expansion record.

The pipeline preserved its reported repeat information and

assigned the status detected_not_interpreted.

It should also state:

The pipeline did not independently estimate repeat size

from BAM or CRAM reads.

Do not present the VCF count as independently confirmed.

.. _21-28-reporting-unsupported-structural-variants:

21.28 Reporting unsupported structural variants
-----------------------------------------------

Suitable wording:

The workflow detected a structural variant outside the

validated SNV, indel, DEL, DUP and repeat routes. The

original record and available breakpoint fields were

preserved, but no automated classification was assigned.

Unsupported must not be interpreted as:

-  

   .. container::

      benign

-  

   .. container::

      invalid

-  

   .. container::

      unimportant

.. _21-29-reporting-pharmacogenomic-findings:

21.29 Reporting pharmacogenomic findings
----------------------------------------

A PGx report should include:

-  

   .. container::

      Gene

-  

   .. container::

      Exact genomic allele

-  

   .. container::

      rsID

-  

   .. container::

      Genotype

-  

   .. container::

      Project star-allele assignment

-  

   .. container::

      Functional phenotype

-  

   .. container::

      Associated drug

-  

   .. container::

      Evidence source

-  

   .. container::

      Limitation

Suitable wording:

The patient carried an exact genomic match to the local

curated pharmacogenomic allele. Under the controlled

project interpretation, this supported the reported

diplotype and functional phenotype.

The report must state that:

Treatment or dose changes require confirmation of the

genotype, complete diplotype and current professional

guideline.

The report should not instruct the patient to change medication.

.. _21-30-reporting-the-universal-score:

21.30 Reporting the universal score
-----------------------------------

Suitable wording:

The candidate received a universal prioritisation score of

.. _74-07-and-ranked-first-among-the-supported-scored-variants:

74.07 and ranked first among the supported scored variants.
-----------------------------------------------------------

The report should immediately clarify:

This project-specific score is not a pathogenicity

probability or diagnostic confidence percentage.

Avoid:

The variant had a 74.07% probability of causing disease.

.. _21-31-reporting-candidate-rank:

21.31 Reporting candidate rank
------------------------------

Candidate rank describes review order.

Suitable wording:

The variant was the highest-ranked supported candidate in

the completed analysis.

This does not mean:

The variant was confirmed as causal.

A lower-ranked variant may still require review, especially when the top result has conflicting or incomplete evidence.

.. _21-32-reporting-validation-results:

21.32 Reporting validation results
----------------------------------

The report should state the validation results precisely:

Thirteen synthetic VCFs passed structural preflight.

Twelve cases were included in the final behavioural audit.

All twelve audited cases passed.

Patient 13 was intentionally not processed through the

complete workflow within the available project timeframe.

Do not write:

All thirteen cases passed the full pipeline.

That statement would be inaccurate.

.. _21-33-reporting-current-legacy-and-routed-outputs:

21.33 Reporting current, legacy and routed outputs
--------------------------------------------------

The report should explain:

CURRENT:

Produced by the current universal workflow.

LEGACY:

Accepted output from an earlier compatible workflow.

ROUTED_REPEAT:

Processed through the dedicated repeat route.

These labels represent analytical provenance, not variant classifications.

A legacy case should not be described as newly rerun unless a current rerun was actually completed.

.. _21-34-tables:

21.34 Tables
------------

Tables are useful for:

-  

   .. container::

      Tool comparisons

-  

   .. container::

      Resource inventories

-  

   .. container::

      Input requirements

-  

   .. container::

      Validation cases

-  

   .. container::

      Candidate summaries

-  

   .. container::

      Failure categories

-  

   .. container::

      Version records

Every table should contain:

-  

   .. container::

      Table number

-  

   .. container::

      Descriptive title

-  

   .. container::

      Column headings

-  

   .. container::

      Units where applicable

-  

   .. container::

      Abbreviation explanation

-  

   .. container::

      Source or note where required

Example title:

Table 7. Canonical candidates recovered in the final

Patients 01–12 validation audit.

Avoid vague titles such as:

Table of results

.. _21-35-figures-and-workflow-diagrams:

21.35 Figures and workflow diagrams
-----------------------------------

Figures may include:

-  

   .. container::

      Overall pipeline architecture

-  

   .. container::

      Small-variant workflow

-  

   .. container::

      CNV workflow

-  

   .. container::

      Inheritance decision flow

-  

   .. container::

      Repeat-expansion routing

-  

   .. container::

      Validation strategy

-  

   .. container::

      Directory structure

-  

   .. container::

      Each figure should have:

-  

   .. container::

      Figure number

-  

   .. container::

      Clear caption

-  

   .. container::

      Explanation of symbols

-  

   .. container::

      Source statement

-  

   .. container::

      Readable text

-  

   .. container::

      Consistent style

A figure caption should explain what the figure demonstrates.

Example:

Figure 4. Universal variant-routing architecture. Ordinary

small variants enter the annotation workflow, DEL and DUP

records enter the CNV branch, repeat expansions are reported

separately, and unsupported structural variants are

preserved for specialist review.

.. _21-36-screenshots:

21.36 Screenshots
-----------------

Screenshots should be used only when they add evidence that cannot be explained more clearly through text or a table.

Useful screenshots include:

-  

   .. container::

      Successful pipeline completion

-  

   .. container::

      Example VEP annotation

-  

   .. container::

      Example AnnotSV full and split output

-  

   .. container::

      ClassifyCNV scoresheet

-  

   .. container::

      ISV-CNV prediction

-  

   .. container::

      Final validation status

-  

   .. container::

      Directory structure

Screenshots should not expose:

-  

   .. container::

      Real patient identifiers

-  

   .. container::

      Private sample names

-  

   .. container::

      Personal usernames

-  

   .. container::

      Access tokens

-  

   .. container::

      Full local paths

-  

   .. container::

      Unnecessary desktop content

Crop the image to the relevant area.

Add:

-  

   .. container::

      Figure number

-  

   .. container::

      Caption

-  

   .. container::

      Short interpretation

Do not leave screenshots unexplained.

.. _21-37-screenshot-caption-model:

21.37 Screenshot caption model
------------------------------

A caption may follow this structure:

Figure X. [What is shown]. The highlighted field indicates

[important observation]. This result was interpreted as

[meaning], while [limitation] remained.

Example:

Figure X. ClassifyCNV Scoresheet.txt generated for a

synthetic deletion. The output displays the total evidence

score and automated classification. The classification was

reviewed together with gene content, phenotype and

inheritance evidence.

.. _21-38-code-blocks:

21.38 Code blocks
-----------------

Commands should use a consistent monospaced style.

Each command block should state:

-  

   .. container::

      Purpose

-  

   .. container::

      Expected working directory

-  

   .. container::

      Files that must already exist

-  

   .. container::

      Output produced

-  

   .. container::

      Failure condition

For example:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   bash pipeline/run_real_patient_case.sh \
   case_001 \
   /absolute/path/to/input.vcf.gz \
   /absolute/path/to/phenotypes.txt

Follow with:

This command launches the external-case intake and universal

analysis workflow for a GRCh38 patient-level VCF.

Do not include long commands without explaining their purpose.

.. _21-39-github-links:

21.39 GitHub links
------------------

Long scripts should be referenced using GitHub links rather than copied completely into the main report.

A source-link entry may use:

Source file:

.. code:: bash

   pipeline/case_workflow/11_score_universal_evidence.py

Repository:

.. code:: bash

   Wahid-25/rare-disease-genomics-pipeline

The final link should point to the exact path and preferably the validated commit or release tag.

A commit-specific link is more reproducible than a link to the changing main branch.

Do not link to:

-  

   .. container::

      Real patient inputs

-  

   .. container::

      Real patient outputs

-  

   .. container::

      SIF files

-  

   .. container::

      Reference databases

-  

   .. container::

      Private archives

.. _21-40-appendix-use:

21.40 Appendix use
------------------

Appendices can contain material that is necessary but too detailed for the main narrative.

Recommended appendices include:

-  

   .. container::

      Appendix A — Full directory tree

-  

   .. container::

      Appendix B — Software and resource versions

-  

   .. container::

      Appendix C — Main command reference

-  

   .. container::

      Appendix D — Output-column dictionary

-  

   .. container::

      Appendix E — Validation case summary

-  

   .. container::

      Appendix F — Troubleshooting reference

-  

   .. container::

      Appendix G — Abbreviations

The main text should still explain the important concepts. It should not send the reader to an appendix for every essential point.

.. _21-41-abbreviation-list:

21.41 Abbreviation list
-----------------------

The report should define abbreviations when first used and include a consolidated list.

Recommended entries include:

+------------------+-------------------------------------------------------+
| **Abbreviation** | **Meaning**                                           |
+==================+=======================================================+
| ACMG             | American College of Medical Genetics and Genomics     |
+------------------+-------------------------------------------------------+
| AMP              | Association for Molecular Pathology                   |
+------------------+-------------------------------------------------------+
| CNV              | Copy-number variant                                   |
+------------------+-------------------------------------------------------+
| CDS              | Coding sequence                                       |
+------------------+-------------------------------------------------------+
| G2P              | Gene2Phenotype                                        |
+------------------+-------------------------------------------------------+
| GRCh38           | Genome Reference Consortium Human Build 38            |
+------------------+-------------------------------------------------------+
| HGVS             | Human Genome Variation Society                        |
+------------------+-------------------------------------------------------+
| HPO              | Human Phenotype Ontology                              |
+------------------+-------------------------------------------------------+
| MANE             | Matched Annotation from NCBI and EMBL-EBI             |
+------------------+-------------------------------------------------------+
| MONDO            | Mondo Disease Ontology                                |
+------------------+-------------------------------------------------------+
| PGx              | Pharmacogenomics                                      |
+------------------+-------------------------------------------------------+
| SNV              | Single-nucleotide variant                             |
+------------------+-------------------------------------------------------+
| SV               | Structural variant                                    |
+------------------+-------------------------------------------------------+
| VCF              | Variant Call Format                                   |
+------------------+-------------------------------------------------------+
| VEP              | Variant Effect Predictor                              |
+------------------+-------------------------------------------------------+
| VUS              | Variant of uncertain significance                     |
+------------------+-------------------------------------------------------+
| WSL              | Windows Subsystem for Linux                           |
+------------------+-------------------------------------------------------+

Only abbreviations actually used in the report should be included.

.. _21-42-output-column-dictionary:

21.42 Output-column dictionary
------------------------------

A data dictionary should explain the final master-table columns.

Example structure:

+--------------------+-------------------------------------------------+
| **Column**         | **Description**                                 |
+====================+=================================================+
| candidate_key      | Normalised GRCh38 allele identifier             |
+--------------------+-------------------------------------------------+
| gene               | Annotated gene symbol                           |
+--------------------+-------------------------------------------------+
| resolved_disease   | Harmonised principal disease label              |
+--------------------+-------------------------------------------------+
| genotype           | Patient genotype from the VCF                   |
+--------------------+-------------------------------------------------+
| phenotype_score    | Project phenotype-similarity value              |
+--------------------+-------------------------------------------------+
| inheritance_status | Compatibility with the curated disease model    |
+--------------------+-------------------------------------------------+
| universal_score    | Project-specific prioritisation score           |
+--------------------+-------------------------------------------------+
| candidate_rank     | Review order among scored candidates            |
+--------------------+-------------------------------------------------+
| warning            | Limitation or conflicting evidence              |
+--------------------+-------------------------------------------------+

The exact names must be taken from the generated header.

.. _21-43-methods-reporting:

21.43 Methods reporting
-----------------------

The Methods section should be sufficiently detailed for reproduction.

It should include:

-  

   .. container::

      Operating environment

-  

   .. container::

      Project root

-  

   .. container::

      Reference build

-  

   .. container::

      Input VCF requirements

-  

   .. container::

      Phenotype-file format

-  

   .. container::

      Normalisation procedure

-  

   .. container::

      Annotation tools

-  

   .. container::

      Database resources

-  

   .. container::

      Gene–disease mapping

-  

   .. container::

      Phenotype scoring

-  

   .. container::

      Inheritance analysis

-  

   .. container::

      CNV tools

-  

   .. container::

      PGx method

-  

   .. container::

      Candidate scoring

-  

   .. container::

      Validation approach

Commands may be included in subsections or appendices.

Do not describe a command as having been run when it was only proposed or documented.

Use:

The workflow was designed to run…

when discussing an unexecuted setup command.

Use:

The command was executed and produced…

only when the output was actually observed.

.. _21-44-results-reporting:

21.44 Results reporting
-----------------------

The Results section should report observations rather than repeat the complete Methods section.

It should cover:

-  

   .. container::

      Pipeline components completed

-  

   .. container::

      Input cases prepared

-  

   .. container::

      Structural preflight result

-  

   .. container::

      Implemented engineering safeguards

-  

   .. container::

      Validation cases audited

-  

   .. container::

      Canonical candidates recovered

-  

   .. container::

      Repeat route validated

-  

   .. container::

      PGx controls recovered

-  

   .. container::

      Audit pass count

A suitable results statement is:

All thirteen prepared synthetic VCFs passed structural

preflight. Twelve cases were subsequently included in the

final audit, and all twelve met their canonical candidate

or route expectations.

.. _21-45-discussion-writing:

21.45 Discussion writing
------------------------

The Discussion should explain:

-  

   .. container::

      Why the results matter

-  

   .. container::

      What technical problems were solved

-  

   .. container::

      How the workflow differs from a simple annotation pipeline

-  

   .. container::

      Why phenotype and inheritance integration are important

-  

   .. container::

      What the validation demonstrates

-  

   .. container::

      What remains unvalidated

Important project contributions include:

-  

   .. container::

      Universal variant routing

-  

   .. container::

      Production and validation resource isolation

-  

   .. container::

      Allele-aware ClinPGx matching

-  

   .. container::

      Shared inheritance utilities

-  

   .. container::

      Sex and ploidy preflight

-  

   .. container::

      Phase-aware compound heterozygosity

-  

   .. container::

      Exact HPO case matching

-  

   .. container::

      G2P disease-label precedence

-  

   .. container::

      Repeat-expansion preservation

-  

   .. container::

      Reproducibility and final audit

The Discussion should not merely list tools again.

.. _21-46-distinguish-development-success-from-clinical-validity:

21.46 Distinguish development success from clinical validity
------------------------------------------------------------

The project successfully demonstrates:

-  

   .. container::

      Software execution

-  

   .. container::

      Evidence integration

-  

   .. container::

      Controlled synthetic-case recovery

-  

   .. container::

      Regression protection

-  

   .. container::

      Reproducibility

It does not establish:

-  

   .. container::

      Clinical sensitivity

-  

   .. container::

      Clinical specificity

-  

   .. container::

      Diagnostic accuracy

-  

   .. container::

      Population-level validity

-  

   .. container::

      Regulatory approval

-  

   .. container::

      Suitability for unsupervised patient care

This distinction should appear in both the Discussion and Limitations sections.

.. _21-47-responsible-clinical-language:

21.47 Responsible clinical language
-----------------------------------

Recommended final-report language:

This result represents computational prioritisation based

on the submitted data and the resources available to the

pipeline.

The finding requires review by a qualified genetics

professional and, where appropriate, orthogonal laboratory

confirmation, segregation analysis and clinical

correlation.

Avoid language that encourages independent patient action.

.. _21-48-variant-of-uncertain-significance:

21.48 Variant of uncertain significance
---------------------------------------

A VUS should be explained accurately.

Suitable wording:

-  

   .. container::

      A variant of uncertain significance is a variant for whichthe available evidence is insufficient or conflicting.

-  

   .. container::

      It neither confirms nor excludes a diagnosis and should notbe used alone to direct irreversible clinical management.

The pipeline score must not convert a VUS automatically into a pathogenic classification.

.. _21-49-negative-result-wording:

21.49 Negative-result wording
-----------------------------

A negative or inconclusive pipeline result should not be written as:

No genetic disease is present.

Suitable wording:

The workflow did not identify a sufficiently supported

candidate among the variant classes and resources assessed.

This does not exclude a genetic cause.

Reasons may include:

-  

   .. container::

      Variant class outside the workflow

-  

   .. container::

      Incomplete coverage

-  

   .. container::

      Repeat expansion not represented

-  

   .. container::

      Complex structural variant

-  

   .. container::

      Mosaicism

-  

   .. container::

      Regulatory variant

-  

   .. container::

      Incomplete phenotype data

-  

   .. container::

      Unknown gene–disease relationship

-  

   .. container::

      Resource limitations

.. _21-50-incidental-and-secondary-findings:

21.50 Incidental and secondary findings
---------------------------------------

A pipeline may identify findings unrelated to the original indication.

The report should distinguish:

Primary candidate:

Potentially explains the submitted phenotype.

Pharmacogenomic finding:

May influence drug response.

Incidental or secondary finding:

Unrelated to the primary indication.

The handling of secondary findings requires an approved policy and informed consent framework.

The project should not automatically disclose every unrelated candidate.

.. _21-51-family-implications:

21.51 Family implications
-------------------------

A genomic finding may have implications for biological relatives.

Reporting may require consideration of:

-  

   .. container::

      Inheritance

-  

   .. container::

      Carrier status

-  

   .. container::

      Recurrence risk

-  

   .. container::

      Segregation testing

-  

   .. container::

      Cascade testing

-  

   .. container::

      Reproductive implications

The computational pipeline can provide inheritance compatibility, but formal recurrence-risk counselling requires a qualified genetics professional.

.. _21-52-limitations-section-within-each-result:

21.52 Limitations section within each result
--------------------------------------------

Each major result should include a brief limitation statement.

For a small variant:

Transcript selection and functional consequence remain

prediction dependent.

For a CNV:

Breakpoint precision and inheritance were not independently

confirmed.

For a repeat expansion:

Read-level repeat sizing was not performed.

For PGx:

The local reference does not provide comprehensive

star-allele resolution.

For phenotype analysis:

The score depends on the completeness and specificity of

the supplied HPO terms.

.. _21-53-quality-review-of-the-final-document:

21.53 Quality review of the final document
------------------------------------------

Before submission, check:

-  

   .. container::

      Heading numbering

-  

   .. container::

      Table and figure numbering

-  

   .. container::

      Cross-references

-  

   .. container::

      Citation consistency

-  

   .. container::

      Reference completeness

-  

   .. container::

      Spelling of gene symbols

-  

   .. container::

      GRCh38 labels

-  

   .. container::

      Variant coordinates

-  

   .. container::

      Transcript versions

-  

   .. container::

      Abbreviations

-  

   .. container::

      Command formatting

-  

   .. container::

      Path consistency

-  

   .. container::

      Privacy

-  

   .. container::

      Clinical wording

Gene symbols should be written consistently, for example:

-  

   .. container::

      CFTR

-  

   .. container::

      HEXA

-  

   .. container::

      PAH

-  

   .. container::

      ATP7B

Disease names should use consistent capitalisation.

.. _21-54-verify-project-paths-before-finalising-the-report:

21.54 Verify project paths before finalising the report
-------------------------------------------------------

Several paths may have changed during development.

Create an inventory of every path mentioned in the report, then verify it against the final project.

A local search for relevant scripts is:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find pipeline \
   -type f \
   \( -name '*.py' -o -name '*.sh' \) \
   -printf '%p\n' |

sort

Find test files:

.. code:: bash

   find pipeline/tests \
   -type f \
   -printf '%p\n' |

sort

Find resource directories:

.. code:: bash

   find resources \
   -maxdepth 3 \
   -type d \
   -printf '%p\n' |

sort

The Word report should be corrected to match the actual final paths.

.. _21-55-verify-script-names-used-in-the-report:

21.55 Verify script names used in the report
--------------------------------------------

Create a list of expected scripts:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   EXPECTED_SCRIPTS=(
   pipeline/run_real_patient_case.sh
   pipeline/run_case_pipeline.sh
   pipeline/case_workflow/00_detect_and_split_variants.py
   pipeline/case_workflow/00b_report_repeat_expansions.py
   pipeline/case_workflow/00c_build_reproducibility_manifest.py
   pipeline/case_workflow/11_score_universal_evidence.py
   pipeline/case_workflow/11b_score_universal_cnv.py
   pipeline/case_workflow/12_build_universal_master.py
   pipeline/case_workflow/14_build_master_candidate_table.py
   )
   for script in "${EXPECTED_SCRIPTS[@]}"; do
   if [[ -s "$script" ]]; then
   printf "FOUND %s\n" "$script"
   else
   printf "MISSING %s\n" "$script"
   fi
   done

Any missing path must be corrected in the final report rather than left as an assumed filename.

.. _21-56-consistency-of-reference-genome-paths:

21.56 Consistency of reference-genome paths
-------------------------------------------

The report has used reference filenames such as:

.. code:: bash

   resources/reference/hg38.fa
   resources/reference/hg38.p14.fa

Only the actual active file should appear in the final execution instructions.

Check:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find resources/reference \
   -maxdepth 1 \
   -type f \
   -printf '%s\t%f\n' |
   sort -k2,2

Search active pipeline references:

.. code:: bash

   grep -RInE \
   'hg38(\.p14)?\.fa' \
   pipeline \
   validation \
   README.md \
   || true

Resolve this path consistently before final submission.

.. _21-57-scientific-report-review-table:

21.57 Scientific-report review table
------------------------------------

+------------------------------------------------+---------------------+
| **Review question**                            | **Required answer** |
+================================================+=====================+
| Is the genome build stated?                    | Yes, GRCh38         |
+------------------------------------------------+---------------------+
| Are variants represented with REF and ALT?     | Yes                 |
+------------------------------------------------+---------------------+
| Are transcripts identified?                    | Where relevant      |
+------------------------------------------------+---------------------+
| Is ClinVar review status included?             | Yes                 |
+------------------------------------------------+---------------------+
| Is frequency interpreted cautiously?           | Yes                 |
+------------------------------------------------+---------------------+
| Is phenotype evidence explained?               | Yes                 |
+------------------------------------------------+---------------------+
| Is inheritance compatibility reported?         | Yes                 |
+------------------------------------------------+---------------------+
| Is phase uncertainty preserved?                | Yes                 |
+------------------------------------------------+---------------------+
| Are CNV full and split rows distinguished?     | Yes                 |
+------------------------------------------------+---------------------+
| Is repeat sizing limitation stated?            | Yes                 |
+------------------------------------------------+---------------------+
| Is PGx separated from diagnosis?               | Yes                 |
+------------------------------------------------+---------------------+
| Is the universal score described correctly?    | Yes                 |
+------------------------------------------------+---------------------+
| Is Patient 13 described accurately?            | Yes                 |
+------------------------------------------------+---------------------+
| Are private data absent?                       | Yes                 |
+------------------------------------------------+---------------------+
| Are citations complete?                        | Yes                 |
+------------------------------------------------+---------------------+
| Are paths and script names verified?           | Yes                 |
+------------------------------------------------+---------------------+

.. _21-58-recommended-wording-for-the-main-result:

21.58 Recommended wording for the main result
---------------------------------------------

A strong general result statement is:

The universal pipeline prioritised the candidate because

multiple evidence domains were concordant, including

functional consequence, gene–disease association,

phenotype compatibility and inheritance context.

The result represents computational prioritisation rather

than an independent clinical diagnosis. Confirmation and

specialist review remain required.

.. _21-59-recommended-wording-for-conflicting-evidence:

21.59 Recommended wording for conflicting evidence
--------------------------------------------------

Although the candidate received supporting functional and

gene–disease evidence, the available phenotype,

inheritance or population evidence was incomplete or

conflicting. The candidate was therefore retained for

review rather than interpreted as definitively causal.

.. _21-60-recommended-wording-for-no-definitive-candidate:

21.60 Recommended wording for no definitive candidate
-----------------------------------------------------

No candidate reached a level of combined evidence sufficient

for a confident molecular explanation within the variant

classes and resources assessed by the workflow.

This result does not exclude a genetic cause and may warrant

review of coverage, phenotype data, structural variants,

repeat expansions, mosaicism or future resource updates.

.. _21-61-recommended-wording-for-cnv-findings:

21.61 Recommended wording for CNV findings
------------------------------------------

The CNV was prioritised based on interval annotation,

dosage-sensitivity evidence, gene–disease relationships and

phenotype compatibility. Automated classifications from

AnnotSV, ClassifyCNV and ISV-CNV were retained as

complementary evidence and were not treated as independent

clinical confirmation.

.. _21-62-recommended-wording-for-pgx-findings:

21.62 Recommended wording for PGx findings
------------------------------------------

An exact allele-aware match was identified in the local

curated ClinPGx reference. The corresponding project

diplotype and functional phenotype were reported for

review. Medication or dose changes should not be made

without confirmation and consultation of the current

professional guideline.

.. _21-63-recommended-wording-for-the-validation-conclusion:

21.63 Recommended wording for the validation conclusion
-------------------------------------------------------

The final audit included twelve synthetic cases and

confirmed the expected principal candidate or analytical

route in all twelve. A thirteenth prepared VCF passed

structural preflight but was not included in the complete

workflow execution within the project timeframe.

These results demonstrate reproducible behaviour for the

implemented synthetic scenarios but do not establish

clinical sensitivity or specificity.

.. _21-64-documentation-completion-criteria:

21.64 Documentation-completion criteria
---------------------------------------

The documentation is scientifically complete when:

✓ The project aim and scope are clear

✓ The complete environment is described

✓ Every major tool and resource has a stated purpose

✓ Input requirements are documented

✓ Branch routing is explained

✓ Small-variant annotation is described

✓ CNV analysis is described

✓ Repeat-expansion handling is described

✓ PGx analysis is described

✓ Phenotype and inheritance analysis are described

✓ Scoring is described as prioritisation

✓ Validation results are reported accurately

✓ Patient 13 is not misrepresented

✓ Current, legacy and routed outputs are distinguished

✓ Commands are explained

✓ Long scripts are linked through GitHub

✓ Script paths are verified

✓ Reference paths are standardised

✓ Tables and figures are captioned

✓ Screenshots are de-identified

✓ Citations use a consistent style

✓ Wording is original rather than copied

✓ Observations, predictions and conclusions are separated

✓ Uncertainty is retained

✓ Clinical confirmation requirements are stated

✓ Privacy and governance requirements are included

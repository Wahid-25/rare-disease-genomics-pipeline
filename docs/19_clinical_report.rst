19. Preparing the Clinical-Style Genomic Report
===============================================

.. raw:: html

   <div class="report-launch-card">
     <h2>Interactive Clinical-Style Report Builder</h2>
     <p>Open the JSON-enabled report template in a separate tab. Use synthetic information on the publicly hosted version.</p>
     <a class="report-builder-button" href="report_builder/index.html" target="_blank" rel="noopener">Open the Report Builder</a>
   </div>

.. warning::

   The hosted builder is for synthetic or demonstration data. Prepare sensitive reports only from a protected local copy bound to ``127.0.0.1``.

After the pipeline has completed successfully, the final candidate-ranking tables and supporting annotation files must be reviewed and converted into a clear clinical-style genomic report. The report is intended to summarise the most relevant findings in a structured format that can be understood by laboratory personnel, clinicians, students and other reviewers. It does not replace professional clinical interpretation or diagnostic laboratory sign-out.

The report-building stage brings together information produced by the rare-disease, inheritance, phenotype, structural-variant, repeat-expansion and pharmacogenomic components of the pipeline. The analyst must confirm that each reported result is supported by the underlying output files before finalising the document.

19.1 Purpose of the Report
--------------------------

The clinical-style report has several main purposes:

#. To identify the analysed patient or case.
#. To describe the reason for genomic testing.
#. To summarise the methods used by the pipeline.
#. To present the most relevant genomic findings.
#. To connect each finding with the associated gene, disease and inheritance pattern.
#. To explain the level of evidence supporting the interpretation.
#. To record whether orthogonal confirmation has been performed.
#. To distinguish diagnostic findings from pharmacogenomic or secondary information.
#. To provide recommendations, limitations and references.
#. To preserve an auditable record of the analyst’s reviewed interpretation.

The report should present the evidence clearly without overstating the certainty of the findings. A pipeline-generated result remains a candidate until it has been reviewed in the context of phenotype, inheritance, allele frequency, annotation quality and available clinical evidence.

19.2 Clinical Report Builder
----------------------------

The project includes a browser-based report builder stored in:

.. code-block:: text

   clinical_report/index.html

The report builder provides a structured form in which patient information, test details, genomic findings, interpretations, recommendations and references can be reviewed and edited.

The builder can be opened manually through a local web server or through the automated launcher described in Section 20. The local server is used because modern browsers may restrict the loading of JSON files when an HTML document is opened directly from the filesystem.

The report interface contains editable fields for:

- report title;
- laboratory name and subtitle;
- patient name;
- case identifier;
- sex;
- date of birth;
- testing indication;
- ordering physician;
- account number;
- specimen type;
- collection, receipt and reporting dates;
- test methodology;
- phenotype summary;
- variant findings;
- gene and disease information;
- interpretation;
- confirmation status;
- recommendations;
- limitations;
- references;
- signatory information.

All automatically populated fields must be checked before the report is printed or saved.

19.3 Reviewing the Patient and Case Information
-----------------------------------------------

The analyst should first verify the patient and case details displayed at the beginning of the report.

The case identifier must match the identifier used by the pipeline. For example:

patient_06_pku

Real patient names, dates of birth, physician details and specimen identifiers should not be stored in public repositories. These details should be maintained in protected local metadata files or entered manually during report preparation.

The following information should be confirmed:

.. list-table::
   :header-rows: 1
   :widths: auto

   * - Field
     - Required review
   * - Patient name
     - Confirm spelling or use an approved coded identifier
   * - Case ID
     - Confirm that it matches the pipeline result directory
   * - Sex
     - Confirm because sex-chromosome ploidy may affect interpretation
   * - Date of birth
     - Confirm from protected clinical records
   * - Testing indication
     - Summarise the suspected disorder or clinical question
   * - Ordering physician
     - Enter only when appropriate and authorised
   * - Specimen
     - Record the actual specimen or clearly identify synthetic data
   * - Dates
     - Confirm collection, receipt and report dates
   * - Analysis mode
     - State whether the case was analysed in production or validation mode

For synthetic validation cases, the report must clearly state that the data are synthetic and are being used for educational or technical validation.

19.4 Reviewing the Test Methodology
-----------------------------------

The methodology section should accurately describe the stages that were applied to the case. It should not list a tool that was not actually used.

Depending on the input and available resources, the methodology may include:

- VCF structural and formatting preflight;
- GRCh38 reference validation;
- variant normalisation with bcftools;
- consequence annotation with Ensembl VEP;
- transcript-level annotation;
- SnpEff annotation;
- ClinVar matching;
- population-frequency annotation;
- splice-effect evaluation;
- disease–gene association using Gene2Phenotype;
- phenotype matching using HPO terms;
- inheritance and ploidy assessment;
- compound-heterozygous candidate evaluation;
- copy-number variant annotation;
- repeat-expansion review;
- pharmacogenomic matching;
- candidate scoring and ranking.

The report should also identify important limitations, such as unavailable resources, unsupported variant classes, incomplete phenotype information or the absence of parental samples.

19.5 Selecting Findings for the Report
--------------------------------------

The master candidate-ranking table may contain hundreds of variants. The report should not reproduce the complete table. Instead, it should present the findings that are most relevant to the clinical question.

The main source is:

.. code-block:: text

   results/cases/<case_id>/final/<case_id>.master_candidate_ranking.tsv

A finding may be selected when it is supported by several types of evidence, including:

- a strong gene–disease association;
- a phenotype match;
- an appropriate inheritance pattern;
- a rare or absent population frequency;
- a pathogenic or likely pathogenic clinical classification;
- a predicted damaging molecular consequence;
- a biologically relevant transcript;
- a matching zygosity;
- evidence for compound heterozygosity;
- a clinically relevant structural or repeat finding;
- a validated pharmacogenomic match.

The highest numerical score should not be treated as automatic proof of causality. Candidate ranking is a prioritisation mechanism, not a final diagnosis.

19.6 Recording Variant Information
----------------------------------

Each reported small-variant finding should include, where available:

- chromosome;
- genomic position;
- reference allele;
- alternate allele;
- reference genome build;
- gene symbol;
- transcript;
- coding HGVS expression;
- protein HGVS expression;
- genotype;
- zygosity;
- molecular consequence;
- ClinVar significance;
- population frequency;
- disease association;
- inheritance pattern;
- phenotype relevance;
- confirmation status.

An example format is:

- Gene: PAH
- Variant: NM_000277.3:c.1222C>T
- Protein change: p.Arg408Trp
- Genotype: Homozygous
- Inheritance: Autosomal recessive
- Associated disorder: Phenylketonuria

The transcript and HGVS description must be checked carefully. Different transcripts may produce different coding or protein descriptions for the same genomic variant. A clinically relevant or preferred transcript should be used whenever supported by the annotation.

19.7 Multi-Variant and Multi-Gene Findings
------------------------------------------

A report may contain more than one relevant finding. This may occur when:

- two variants are present in the same recessive disease gene;
- multiple genes are associated with the same phenotype;
- the case contains a diagnostic finding and additional secondary findings;
- pharmacogenomic variants are reported alongside rare-disease candidates;
- a structural or repeat-expansion finding contributes to the interpretation.

Each finding should be presented separately. However, related variants may be discussed together when they form part of the same disease mechanism.

For a possible compound-heterozygous result, the report should state whether the variants are:

- confirmed in trans;
- phased in trans by shared phase information;
- possibly in trans but unphased;
- of unknown phase.

Unphased variants should not be described as confirmed compound heterozygous findings.

19.8 Interpretation of Disease Findings
---------------------------------------

The interpretation should explain why the finding is relevant to the patient. It should integrate the molecular result with the disease mechanism, inheritance pattern and phenotype.

A useful interpretation should address:

#. What the gene normally does.
#. How the variant may affect the gene or protein.
#. Which disorder is associated with the gene.
#. Whether the patient’s phenotype is consistent with that disorder.
#. Whether the genotype fits the expected inheritance pattern.
#. What evidence supports the pathogenicity classification.
#. What uncertainties or limitations remain.

The report should avoid language that implies certainty beyond the available evidence. For example:

This finding provides a strong molecular explanation for the reported

phenotype.

may be appropriate when the variant, genotype, inheritance and phenotype are strongly concordant.

In a less certain case, a more cautious statement should be used:

This finding may be relevant to the reported phenotype, but additional

clinical, segregation or functional evidence is required.

19.9 Variant Classification
---------------------------

Clinical classifications should follow recognised evidence-based principles. Possible classifications include:

- pathogenic;
- likely pathogenic;
- variant of uncertain significance;
- likely benign;
- benign.

The report must not upgrade a variant solely because it ranks highly in the pipeline. Likewise, computational predictions alone are not sufficient to classify a variant as pathogenic.

A variant of uncertain significance must be described carefully. A VUS neither confirms nor excludes a diagnosis and should not normally be used independently for major clinical decisions.

The report should record the source of the classification, such as:

- ClinVar;
- expert-panel review;
- Gene2Phenotype;
- manually reviewed ACMG evidence;
- disease-specific literature;
- validated local interpretation.

Conflicting classifications should be disclosed rather than hidden.

19.10 Pharmacogenomic Findings
------------------------------

Pharmacogenomic findings provide information about possible gene–drug relationships. They should be clearly distinguished from rare-disease diagnostic findings.

A pharmacogenomic entry may include:

- gene;
- variant or allele;
- genotype;
- associated drug;
- phenotype or functional category;
- source guideline;
- evidence level;
- interpretation;
- review status.

Pharmacogenomic results should be presented as contextual information unless they have been reviewed against an authoritative guideline and the complete genotype or haplotype requirements have been satisfied.

A single matched variant does not always establish a complete star allele or metaboliser phenotype. Therefore, the report should not recommend changing a medicine or dose solely from an automatically generated draft result.

A suitable caution is:

This pharmacogenomic result is provided for contextual review and should

not be used independently to start, stop or modify medication.

19.11 Confirmation Status
-------------------------

The report must state whether a finding has been independently confirmed.

Possible entries include:

- not independently confirmed;
- orthogonal confirmation recommended;
- confirmed by an independent method;
- confirmation status unavailable.

The default report language should not claim that Sanger sequencing, quantitative PCR, chromosomal microarray or another method was performed unless documented evidence exists.

For pipeline-only results, the appropriate wording is:

Orthogonal confirmation was not performed within this workflow.

The required confirmation method depends on the variant type. Small variants may require targeted sequencing, whereas copy-number or structural findings may require another molecular or cytogenetic method.

19.12 Recommendations
---------------------

Recommendations should be linked to the reported findings and should remain within the scope of the available evidence.

Common recommendations include:

- clinical correlation;
- genetic counselling;
- segregation testing;
- parental testing;
- biochemical testing;
- orthogonal confirmation;
- phenotype reassessment;
- review of family history;
- specialist referral;
- periodic reinterpretation;
- review of updated databases and literature.

Recommendations should not be written as direct treatment instructions unless the report has been reviewed and authorised by a suitably qualified clinical professional.

19.13 Limitations
-----------------

Every report should include limitations. Relevant limitations may include:

- the workflow is intended for research, education or technical validation;
- not all genomic regions are equally assessable;
- some variant types may not be represented in the input VCF;
- repeat expansions may require dedicated laboratory testing;
- structural variants may require independent confirmation;
- mitochondrial heteroplasmy may not be fully represented;
- low-level mosaic variants may be missed;
- phasing may be unavailable;
- phenotype information may be incomplete;
- database classifications may change over time;
- pharmacogenomic star alleles may require haplotype-level analysis;
- the absence of a reportable variant does not exclude a genetic disorder;
- the automatically generated report is not a final clinical diagnosis.

The limitations should reflect the actual workflow rather than using a generic list without review.

19.14 References
----------------

The references section should contain the main sources used to support the interpretation. These may include:

- ClinVar records;
- Gene2Phenotype disease entries;
- peer-reviewed publications;
- recognised clinical guidelines;
- pharmacogenomic guidance;
- gene- or disease-specific databases;
- official tool documentation.

References should be reviewed before finalising the report. Automatically generated placeholder references should not be treated as sufficient evidence.

19.15 Analyst Review
--------------------

Before export, the analyst should compare the report with the underlying pipeline outputs.

The following checks should be completed:

- the correct case JSON or result directory is loaded;
- patient metadata are correct;
- the reported variants exist in the source files;
- genomic coordinates and alleles are correct;
- transcript and HGVS descriptions are consistent;
- genotype and zygosity are correct;
- disease and inheritance information are supported;
- phenotype claims match the available HPO terms;
- compound-heterozygous phase is not overstated;
- confirmation status is accurate;
- pharmacogenomic findings are appropriately labelled;
- recommendations are proportionate;
- warnings and limitations remain visible;
- no private information is being exported unintentionally.

The report should be considered a draft until these checks have been completed.

19.16 Saving the Reviewed Report
--------------------------------

After review, the report may be preserved in two forms:

#. A reviewed JSON file containing the structured report data.
#. A PDF created through the browser’s print function.

A suitable naming pattern is:

.. code-block:: text

   <case_id>.report_reviewed.json
   <case_id>.genomic_report.pdf

For example:

patient_06_pku.report_reviewed.json

patient_06_pku.genomic_report.pdf

These files may contain sensitive patient information and should remain outside the public Git repository.

The project .gitignore excludes protected metadata, draft JSON files, reviewed JSON files and exported PDFs from version control.

19.17 Privacy and Data Protection
---------------------------------

Patient-identifiable information must be handled separately from public code and documentation. The following files should not be committed to GitHub:

.. code-block:: text

   input/cases/<case_id>/metadata/report_metadata.json
   results/cases/<case_id>/final/report/<case_id>.report_draft.json
   results/cases/<case_id>/final/report/<case_id>.report_reviewed.json
   results/cases/<case_id>/final/report/<case_id>.genomic_report.pdf

The reusable metadata template may be stored in the repository because it contains no real patient information:

.. code-block:: text

   clinical_report/report_metadata.template.json

The report builder and launcher use a local server bound to:

.. code-block:: text

   127.0.0.1

This allows the report to be viewed on the local computer without deliberately exposing the case data through a public web server.

19.18 Final Report Checklist
----------------------------

Before considering the clinical-style report complete, confirm that:

- [ ] The correct case was loaded.
- [ ] Patient and specimen information were checked.
- [ ] The testing indication was stated.
- [ ] The methodology reflects the actual analysis.
- [ ] Every reported variant exists in the pipeline output.
- [ ] Transcript and HGVS descriptions were reviewed.
- [ ] Genotype and inheritance are consistent.
- [ ] Disease and phenotype associations are supported.
- [ ] PGx findings are clearly distinguished from diagnostic findings.
- [ ] Confirmation status is accurate.
- [ ] Recommendations and limitations are included.
- [ ] References were reviewed.
- [ ] No false confirmation statement remains.
- [ ] The report was saved as reviewed JSON or PDF.
- [ ] Protected files remain excluded from Git.

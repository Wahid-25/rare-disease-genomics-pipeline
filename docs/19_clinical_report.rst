19. Preparing the Clinical-Style Genomic Report
===============================================

.. raw:: html

   <div class="report-launch-card">
     <h2>Interactive Clinical-Style Report Builder</h2>
     <p>Open the browser-based report template in a separate tab. Use synthetic information on the publicly hosted version.</p>
     <a class="report-builder-button" href="report_builder/index.html" target="_blank" rel="noopener">Open the Report Builder</a>
   </div>

.. warning::

   The hosted builder is for synthetic or demonstration data. Prepare sensitive reports only from a protected local copy.

After the universal pipeline has completed, the final analytical outputs must be reviewed and converted into a clear human-readable report.

The project includes an interactive HTML report builder that accepts reviewed case information and displays a live report preview. It contains fields for laboratory details, patient information, the principal genomic finding, phenotype, interpretation, references, recommendations and signatory information. The completed report can be printed or saved as a PDF.

The reporting stage follows this sequence:

.. code-block:: text

   Completed pipeline analysis
                │
                ▼
   Review pipeline summary and warnings
                │
                ▼
   Review ranked candidate table
                │
                ▼
   Review variant-specific evidence
                │
                ▼
   Select the principal reviewed finding
                │
                ▼
   Transfer verified information into the report builder
                │
                ▼
   Review the generated report sentence
                │
                ▼
   Complete interpretation and recommendations
                │
                ▼
   Perform final report quality control
                │
                ▼
   Print or save the report as PDF

The report builder must not be used to convert an unreviewed rank-one candidate automatically into a clinical diagnosis.

19.1 Purpose of the report
--------------------------

The clinical-style report has four main purposes:

1. Summarise the submitted case and testing indication.

2. Present the principal reviewed genomic finding.

3. Explain the evidence supporting or limiting its interpretation.

4. Communicate recommendations and required follow-up.

The report should clearly distinguish:

- Information supplied by the referring source

- Pipeline-generated annotation

- Pipeline-generated prioritisation

- Analyst interpretation

- Independent laboratory confirmation

These evidence types must not be presented as though they are equivalent.

19.2 Clinical and educational boundary
--------------------------------------

The report template was developed for this educational and research project.

It is not automatically:

- An accredited clinical laboratory report

- An independent diagnostic confirmation

- A validated medical device

- A treatment recommendation

- A substitute for genetic counselling

Every generated report should retain a visible statement such as:

**This report was generated from a research and educational genomic-analysis workflow. All findings require review by an appropriately qualified genetics professional and confirmation where clinically indicated.**

For synthetic cases, retain:

**SYNTHETIC / TEMPLATE REPORT — Verify all fields before any real clinical use.**

The HTML template already includes educational-use warnings at the bottom of the report. These warnings should not be removed from synthetic demonstrations.

19.3 Recommended location of the report builder
-----------------------------------------------

Store the HTML report builder under:

.. code-block:: text

   clinical_report/
   └── index.html

The project structure may therefore include:

.. code-block:: text

   rare_disease_project/
   ├── clinical_report/
   │   └── index.html
   ├── pipeline/
   ├── input/
   ├── results/
   ├── resources/
   └── validation/

The report-builder source should remain separate from individual case reports.

Generated PDFs should be stored under the relevant protected case directory, for example:

.. code-block:: text

   results/cases/<case_id>/final/report/

19.4 Opening the report builder locally
---------------------------------------

Move to the project root:

.. code-block:: text

   cd ~/rare_disease_project
   set -Eeuo pipefail

Confirm that the report builder exists:

.. code-block:: text

   REPORT_BUILDER="clinical_report/index.html"
   if [[ ! -s "$REPORT_BUILDER" ]]; then
       echo "ERROR: Clinical report builder is missing:"
       echo "$REPORT_BUILDER"
       exit 1
   fi
   echo "PASS: Clinical report builder found."

Open it from WSL in the default Windows browser:

.. code-block:: text

   explorer.exe \
       "$(wslpath -w "$REPORT_BUILDER")"

Alternatively, open:

.. code-block:: text

   clinical_report/index.html

directly through Windows File Explorer.

The report builder operates as a local HTML page and does not require a local web server for its main report-generation functions.

19.5 Important privacy note about the hosted documentation
----------------------------------------------------------

The report builder may also be shown in the project documentation for demonstration purposes.

However:

Only synthetic information should be entered into a copy

opened from the public documentation website.

For a real or sensitive case:

download or copy the HTML file locally;

disconnect it from any public documentation page;

use a non-identifying case ID;

avoid entering unnecessary personal information;

save the report only in an approved protected location.

The template uses an external NIH Clinical Tables service for optional gene and condition autocomplete searches. Therefore, typed gene or condition search terms may be sent to that external lookup service, even though the rest of the report generation occurs locally in the browser.

For protected real-case reporting, either:

Enter gene and condition names manually without using

autocomplete

or use a local version in which the autocomplete code has been disabled.

19.6 Required files before report preparation
---------------------------------------------

Before starting the report, confirm that the following outputs are available:

- Pipeline summary

- Master candidate table

- Detailed small-variant annotation

- Inheritance or ploidy evidence

- Phenotype-prioritisation output

- CNV output, where applicable

- Repeat-expansion report, where applicable

- ClinPGx report, where applicable

- Pipeline log

- Reproducibility manifest

A report should not be prepared from the master-table score alone.

Locate the final case outputs:

.. code-block:: text

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   find \
       "results/cases/$CASE_ID" \
       -type f \
       -printf '%s\t%p\n' |
   sort -k2,2

Search for the principal summary and ranking files:

.. code-block:: text

   find \
       "results/cases/$CASE_ID" \
       -type f \
       \( \
           -iname '*summary*' \
           -o -iname '*master*' \
           -o -iname '*candidate*' \
           -o -iname '*report*' \
           -o -iname '*manifest*' \
       \) \
       -print |
   sort

19.7 Review the case before opening the report
----------------------------------------------

The analyst should confirm:

- ✓ The pipeline completed successfully

- ✓ The intended sample was analysed

- ✓ The input used GRCh38

- ✓ The phenotype file belonged to the correct case

- ✓ The correct production or validation resource mode was used

- ✓ The final master table exists

- ✓ Branch warnings were reviewed

- ✓ Repeat and unsupported records were reviewed

- ✓ ClinPGx results were reviewed separately

Do not start report preparation when an unresolved fatal error remains in the pipeline log.

Search for obvious failures:

.. code-block:: text

   CASE_ID="case_001"
   grep -RInE \
       'Traceback|FATAL|PIPELINE FAILED|No such file|Permission denied' \
       "results/cases/$CASE_ID" \
       2>/dev/null \
   || true

19.8 Selecting the principal finding
------------------------------------

The current report template contains one main primary-findings row.

The principal finding should be selected only after reviewing:

- Variant consequence

- ClinVar evidence

- Population frequency

- Gene–disease relationship

- Phenotype similarity

- Inheritance compatibility

- Sex and ploidy

- Compound-heterozygous evidence

- Splice evidence

- CNV or repeat-route evidence

- Conflicting annotations

The first-ranked variant is a prioritised candidate, not automatically a reportable diagnosis.

A principal finding may be selected when:

- The candidate has a relevant gene–disease association,

- the phenotype is reasonably compatible,

- the observed genotype fits the expected inheritance model,

- and the available variant evidence supports review.

When evidence remains uncertain, the report must preserve that uncertainty.

19.9 Report-builder interface
-----------------------------

The left panel of the report builder contains these sections:

- Lab / Letterhead

- Patient Info

- Variant / Finding

- Test Result Summary

- Narrative Content

- Actions

The right panel displays a live preview of the report.

Changes made in the left panel are immediately reflected in the preview.

The actions include:

- Print / Save as PDF

- Reset fields

The reset button reloads the original default values. Therefore, save or export the report before resetting the form.

19.10 Correcting the default template before use
------------------------------------------------

The uploaded HTML contains example values, including real-looking patient and clinician names. It also defaults to:

Confirmation status:

.. code-block:: text

   Confirmed

and:

This result was confirmed by Sanger sequencing.

These values are demonstration placeholders only.

Before preparing any report:

- ✓ Replace the patient name

- ✓ Replace or remove the ordering physician

- ✓ Replace the case ID

- ✓ Replace all example variant information

- ✓ Replace the example disease

- ✓ Replace the example interpretation

- ✓ Replace the example reference

- ✓ Correct the confirmation status

The confirmation field should initially be changed to:

.. code-block:: text

   Not independently confirmed

The confirmation line should initially be changed to:

Orthogonal confirmation was not performed within this workflow.

Only change these to a confirmed statement when a real confirmation result is available.

19.11 Report title
------------------

The template currently displays:

.. code-block:: text

   WGS FINAL REPORT

This title should be used only when the analysed case genuinely originated from whole-genome sequencing.

For a general VCF-based analysis, a safer title is:

.. code-block:: text

   GENOMIC VARIANT INTERPRETATION REPORT

Other appropriate titles may include:

- WHOLE-EXOME SEQUENCING INTERPRETATION REPORT

- TARGETED GENETIC ANALYSIS REPORT

- RESEARCH GENOMIC ANALYSIS REPORT

The report title must match the actual assay or analytical context.

A VCF input alone does not prove that whole-genome sequencing was performed.

19.12 Laboratory and letterhead information
-------------------------------------------

The report builder includes:

- Lab logo

- Lab name

- Lab subtitle

- Signatory line

Complete these fields using approved project information.

For a synthetic educational report, use a clearly fictional identity, for example:

Lab name:

Genosphere Research Genomics Laboratory

Subtitle:

Educational Genomic Variant Interpretation

Signatory:

Reviewed for educational demonstration

Do not use the name of a real clinical laboratory, professional or organisation without authorisation.

19.13 Patient and case information
----------------------------------

The patient-information section contains:

- Patient name

- Sex

- Date of birth

- Case ID

- Indication for testing

- Ordering physician

- Account number

- Specimen

- Reported date

- Collected date

- Received date

The source of each field should be:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Report field
     - Permitted source
   * - Patient name
     - Approved intake or clinical record
   * - Sex
     - Approved case metadata
   * - Date of birth
     - Approved intake record
   * - Case ID
     - Pipeline case identifier
   * - Indication
     - Referral or clinical-testing indication
   * - Ordering physician
     - Approved request information
   * - Account number
     - Laboratory accession information
   * - Specimen
     - Laboratory intake information
   * - Collected date
     - Sample record
   * - Received date
     - Sample receipt record
   * - Reported date
     - Date the final reviewed report is produced

The pipeline cannot safely infer:

- Patient name

- Date of birth

- Ordering physician

- Specimen collection date

These values must come from approved intake records.

19.13.1 Use non-identifying information for educational cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Recommended educational values are:

Patient name:

Synthetic Patient

Case ID:

SYNTHETIC_CASE_001

Ordering physician:

Not applicable

Account number:

Educational case

Specimen:

Synthetic VCF dataset

Do not include a real patient name in screenshots, documentation or public demonstration reports.

19.14 Sex and ploidy information
--------------------------------

The sex field should reflect the approved case metadata used during pipeline interpretation.

It is particularly important for:

- X-linked variants

- Y-linked variants

- Sex-chromosome ploidy

The report should not change the sex field merely to make the observed genotype fit the expected inheritance model.

When sex is unavailable or unresolved, select:

.. code-block:: text

   Other/Unspecified

and state the limitation in the interpretation.

19.15 Testing indication
------------------------

The indication should summarise why genomic analysis was requested.

Examples include:

- Developmental delay and seizures

- Suspected inherited metabolic disorder

- Unexplained cardiomyopathy

- Possible hereditary cancer predisposition

- Suspected monogenic neurological disorder

Avoid entering:

- Suspected Genetic Disease

when a more specific, verified indication is available.

The indication should describe the clinical question, not the pipeline’s predicted diagnosis.

19.16 Primary sequence-variant fields
-------------------------------------

For an SNV or short indel, complete:

- Gene

- Transcript

- Condition

- Chromosome and position

- DNA HGVS

- Protein HGVS

- Zygosity

- Inheritance

- Classification

- Confirmation status

The fields should be populated from reviewed pipeline outputs.

19.16.1 Field-mapping table for SNVs and indels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Report field
     - Pipeline evidence
   * - Gene
     - Reviewed gene symbol from the master candidate table
   * - Transcript
     - Reviewed VEP transcript, preferably MANE Select where appropriate
   * - Condition
     - Resolved G2P/MONDO disease identity
   * - Chromosome:Position
     - Normalised GRCh38 coordinate
   * - HGVS DNA
     - VEP HGVSc or another validated transcript annotation
   * - HGVS Protein
     - VEP HGVSp, where applicable
   * - Zygosity
     - Patient genotype from the VCF
   * - Inheritance
     - G2P allelic requirement and inheritance model
   * - Classification
     - Reviewed classification evidence
   * - Confirmation
     - Independent laboratory-confirmation record

Every reported coordinate should state:

Genome build: GRCh38

The current template does not provide a dedicated genome-build field. Therefore, add GRCh38 to the chromosome field:

GRCh38 chr12:102840493

or include it clearly in the interpretation.

19.17 Transcript selection
--------------------------

The transcript field should not be filled using the first transcript returned automatically.

Review:

- MANE Select transcript

- Canonical transcript

- Clinically relevant transcript

- Transcript version

- Coding consequence

For example:

NM_000000.4

is more reproducible than:

NM_000000

because the transcript version is retained.

When the consequence differs between transcripts, explain this in the interpretation.

19.18 HGVS representation
-------------------------

The report should include:

Coding HGVS:

c.XXXA>G

Protein HGVS:

p.(ExampleChange)

where applicable.

Do not manually invent HGVS expressions.

Check that:

- ✓ Transcript and HGVS agree

- ✓ Reference allele matches GRCh38

- ✓ Gene strand was considered

- ✓ Indels are normalised

- ✓ Transcript version is included

When no protein change applies, use an appropriate value such as:

Not applicable

rather than generating an unsupported protein consequence.

19.19 Zygosity
--------------

The template supports:

- Homozygous

- Heterozygous

- Compound heterozygous

- Hemizygous

Use the actual genotype evidence.

Examples:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Genotype context
     - Reported zygosity
   * - 0/1 autosomal allele
     - Heterozygous
   * - 1/1 autosomal allele
     - Homozygous
   * - Haploid alternate X allele in compatible context
     - Hemizygous
   * - Two reviewed variants forming a valid pair
     - Compound heterozygous

Do not select Compound heterozygous merely because two heterozygous variants occur in the same gene.

The pipeline must first classify the pair as:

phased_trans

or, when phase is unavailable:

possible_unphased_pair

If trans configuration is not established, state:

Two heterozygous variants formed a possible compound-heterozygous pair; trans configuration was not confirmed.

19.20 Inheritance
-----------------

The report builder includes options such as:

- Autosomal Recessive

- Autosomal Dominant

- X-linked Recessive

- X-linked Dominant

- Y-linked

- Mitochondrial

- Multifactorial / Complex

- De novo

- Unknown

The inheritance field should be based on the curated gene–disease relationship.

Do not select:

De novo

unless appropriate family or trio evidence supports that conclusion.

A single-sample VCF cannot establish de novo inheritance.

When family information is absent, use the disease inheritance model, but state:

Segregation and parental origin were not assessed.

19.21 Variant classification
----------------------------

The classification menu contains:

- Pathogenic

- Likely Pathogenic

- VUS

- Likely Benign

- Benign

This field must not be selected from the project prioritisation score alone.

The universal score:

Is a candidate-prioritisation score

and is not:

An ACMG classification

A pathogenicity probability

A diagnostic-confidence percentage

Classification should be based on reviewed evidence such as:

- ClinVar assertions and review status

- Applicable ACMG/AMP evidence

- Population frequency

- Functional studies

- Disease mechanism

- Segregation

- Literature

When the evidence has not been formally reviewed, use:

- VUS

only when this classification is justified, or adapt the template to state:

Not formally classified within this workflow

19.22 Confirmation status
-------------------------

Confirmation status must describe actual independent testing.

Possible safe values include:

- Not independently confirmed

- Confirmation pending

- Confirmed by Sanger sequencing

- Confirmed by MLPA

- Confirmed by chromosomal microarray

- Confirmed by repeat-primed PCR

The pipeline itself does not perform laboratory confirmation.

The following statements are not equivalent:

ClinVar reported the variant as pathogenic.

and:

The patient variant was confirmed by Sanger sequencing.

The first is a database annotation. The second is an independent laboratory observation.

Never report the second statement unless confirmation actually occurred.

19.23 Automatically generated test-result sentence
--------------------------------------------------

The template automatically generates a result sentence from:

- Classification

- Zygosity

- Gene

- DNA HGVS

- Protein HGVS

- Condition

- Confirmation line

For example, its structure is similar to:

A [classification], [zygosity] variant in [gene]

([coding HGVS], [protein HGVS]) was detected in this

individual. [Classification] variant(s) in [gene] are

associated with [condition]. [Confirmation statement]

This sentence must be reviewed manually.

Potential problems include:

- Missing gene

- Missing condition

- Incorrect lowercase zygosity

- Unsupported disease association

- Incorrect classification

- False confirmation statement

- Awkward wording for a VUS

- Awkward wording for CNVs or repeats

Do not export the report until the generated sentence is scientifically and grammatically correct.

19.23.1 Recommended wording for a pathogenic sequence variant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A heterozygous pathogenic variant in GENE—[HGVSc], p.(HGVSp)—was identified. Pathogenic variants in GENE are associated with [disease] through the stated inheritance model. The finding requires correlation with the patient’s phenotype and confirmation status described below.

19.23.2 Recommended wording for a VUS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A heterozygous variant of uncertain significance in GENE—[HGVSc], p.(HGVSp)—was identified. The available evidence is currently insufficient to establish or exclude a causal relationship with the patient’s phenotype.

Avoid automatically stating:

VUS variant(s) in the gene are associated with the condition.

A gene may be associated with a disease, but the specific VUS may not be established as disease-causing.

19.24 Patient phenotype section
-------------------------------

The phenotype section should convert the submitted HPO profile into a concise readable paragraph.

For example:

- HP:0001250 — Seizure

- HP:0001263 — Global developmental delay

- HP:0004322 — Short stature

may be written as:

The patient presented with seizures, global developmental delay and short stature.

The phenotype paragraph should contain:

- Observed features

- Age of onset where available

- Relevant negative findings where confirmed

- Family history where available

Do not add clinical features merely because they are typical of the prioritised disease.

19.24.1 Phenotype-source rule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every phenotype statement should be traceable to:

- The submitted HPO file

- The intake record

- A verified clinical note

A disease database should not be used as the source of patient phenotype.

19.25 Primary-findings table
----------------------------

The generated primary-findings table contains:

- Confirmation

- Gene and transcript

- Condition

- Chromosome and position

- Variant

- Zygosity

- Inheritance and classification

Review every cell independently.

The table should not contain:

- Blank transcript versions

- Mixed genome builds

- Incorrect zygosity

- ClinVar condition used as patient diagnosis

- Pipeline score entered as classification

Confirmation claimed from annotation alone

When an item is unavailable, use:

- Not available

- Not assessed

- Not applicable

rather than leaving an ambiguous blank cell.

19.26 Variant-information paragraph
-----------------------------------

The variant-information paragraph should explain the evidence for the specific allele.

A recommended order is:

1. Normalised genomic and transcript representation

2. Predicted molecular consequence

3. ClinVar evidence and review status

4. Population-frequency evidence

5. Splice or computational evidence

6. Functional or published evidence

7. Inheritance compatibility

8. Phenotype compatibility

9. Conflicting or missing evidence

10. Final interpretation and limitation

19.26.1 Sequence-variant interpretation model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The GRCh38 variant [coordinate and allele] was annotated in the reviewed transcript [transcript] as [consequence]. ClinVar reported the allele as [classification] for [condition], with [review status]. The allele was [absent/rare/present] in the available population-frequency resource. SpliceAI [did/did not] predict a relevant splice effect. The observed [zygosity] was [compatible/partially compatible/incompatible] with the expected [inheritance] disease model. The candidate also showed [degree] phenotype compatibility with the submitted HPO profile. These findings support [prioritisation/continued review], but [remaining limitation] must be considered.

Only include evidence that is actually present.

19.27 Gene-information paragraph
--------------------------------

The gene-information paragraph should explain:

- Normal gene function

- Associated disease

- Inheritance

- Disease mechanism

- Expected variant consequence

A recommended structure is:

GENE encodes [brief normal function]. Pathogenic variants in this gene are associated with [disease] through a [inheritance] model. The recognised disease mechanism is [loss of function, gain of function, dominant negative, dosage sensitivity or another mechanism]. The detected variant is [compatible/not clearly compatible] with that mechanism.

Do not copy long passages directly from OMIM, Gene2Phenotype or other copyrighted sources.

Write the information in original language and cite the source.

19.28 ClinVar evidence in the report
------------------------------------

When ClinVar evidence is used, include:

- Clinical significance

- Condition

- Review status

- Release or retrieval context

Suitable wording:

ClinVar listed the exact allele as pathogenic for the stated condition, with the review status recorded in the pipeline annotation.

When interpretations conflict:

ClinVar contained conflicting interpretations. The database evidence was therefore not treated as a single unambiguous pathogenic assertion.

Do not use a broad ClinVar condition list as the final patient diagnosis.

19.29 Population-frequency evidence
-----------------------------------

Suitable wording includes:

The allele was rare in the population-frequency evidence available to the pipeline, supporting compatibility with a rare disorder but not independently establishing pathogenicity.

Avoid:

The variant is absent from gnomAD, so it is pathogenic.

Absence or rarity is supporting evidence only.

The main candidate should be manually checked against the current gnomAD website during final review.

19.30 SpliceAI evidence
-----------------------

When a SpliceAI prediction is relevant, include:

- Maximum delta score

- Predicted donor or acceptor effect

- Relative predicted position

- Gene

Suitable wording:

SpliceAI predicted a possible donor-loss effect with a maximum delta score of [value]. This is a computational prediction and requires RNA or another functional method for confirmation.

Avoid:

SpliceAI confirmed abnormal splicing.

19.31 Phenotype-prioritisation evidence
---------------------------------------

Suitable wording:

The candidate demonstrated [strong/moderate/limited] similarity to the supplied HPO profile. This phenotype evidence contributed to prioritisation but did not independently establish the diagnosis.

When no HPO file was available:

Phenotype-based prioritisation was not assessed because a valid HPO profile was unavailable.

Do not report unavailable phenotype analysis as a phenotype mismatch.

19.32 Inheritance evidence in the interpretation
------------------------------------------------

For a compatible dominant candidate:

The heterozygous genotype was compatible with the curated monoallelic autosomal disease model.

For a recessive candidate with only one allele:

Only one heterozygous candidate allele was identified; therefore, the expected biallelic requirement was not fully satisfied.

For a possible unphased pair:

Two heterozygous variants were identified in the same gene, but trans configuration was not established.

For an X-linked candidate:

Interpretation incorporated the supplied sex and expected chromosome ploidy.

For mitochondrial findings:

The mitochondrial candidate requires specialist assessment of heteroplasmy, maternal inheritance and possible nuclear mitochondrial sequence interference.

19.33 Reporting CNVs
--------------------

The current HTML template is primarily structured for one SNV or short indel.

A CNV should not be forced into the coding-HGVS and protein-HGVS fields.

For a CNV, report:

- Genome build

- Chromosome

- Start

- End

- CNV type

- Interval size

- Copy number, where available

- Genotype

- Genes affected

- ClinGen dosage evidence

- AnnotSV result

- ClassifyCNV result

- ISV-CNV result

- Phenotype compatibility

- Inheritance

- Breakpoint precision

19.33.1 Recommended CNV result wording
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A [heterozygous/homozygous] [deletion/duplication] involving GRCh38 [interval] was identified. The interval spans approximately [size] and includes [relevant genes]. AnnotSV reported [summary], ClassifyCNV assigned [classification and score], and ISV-CNV produced [prediction]. These automated outputs were reviewed together with dosage sensitivity, phenotype and inheritance evidence.

Do not state:

The gene copy number is zero

unless the available copy-number and zygosity evidence supports complete loss of both copies.

19.33.2 CNV table adaptation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a CNV, adapt the report fields as follows:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Standard template field
     - CNV replacement
   * - Gene and transcript
     - Principal gene(s) or interval
   * - Condition
     - Resolved CNV-associated disorder
   * - Chromosome:Position
     - GRCh38 start–end interval
   * - DNA HGVS
     - CNV interval notation or not applicable
   * - Protein HGVS
     - Not applicable
   * - Zygosity
     - Heterozygous/homozygous where known
   * - Inheritance
     - Curated CNV disease model
   * - Classification
     - Reviewed CNV classification
   * - Confirmation
     - CMA, MLPA, qPCR or other method

When several genes are affected, the report should not imply that one gene alone explains the complete CNV phenotype unless the evidence supports it.

19.34 Reporting repeat expansions
---------------------------------

Repeat-expansion records require a dedicated interpretation.

Report:

- Gene or locus

- Repeat motif

- Reported repeat count

- Reference or normal allele

- Expanded allele

- Genotype

- Threshold used

- Detection status

- Specialist follow-up

Recommended wording:

The submitted VCF contained a repeat-expansion record involving GENE. The record reported [repeat count] copies of the [motif] repeat, compared with the project threshold of [threshold]. The pipeline preserved this information and assigned the status detected_not_interpreted.

Also state:

The workflow did not independently estimate repeat size from BAM or CRAM reads. Specialist repeat-expansion testing is required.

Do not enter a repeat expansion into the report as though it were an ordinary SNV.

19.35 Reporting unsupported structural variants
-----------------------------------------------

Suitable wording:

The workflow detected a structural variant outside the currently validated SNV, indel, deletion, duplication and repeat-expansion routes. The original record and available breakpoint information were preserved, but no automated clinical classification was assigned.

Unsupported does not mean:

- Benign

- Invalid

- Unimportant

It means the variant requires a specialist workflow.

19.36 Reporting pharmacogenomic findings
----------------------------------------

Pharmacogenomic findings should be presented separately from the principal rare-disease finding.

Include:

- Gene

- Exact genomic allele

- rsID

- Genotype

- Project star-allele assignment

- Project diplotype

- Functional phenotype

- Associated drug

- Evidence source

- Limitation

Recommended wording:

An exact allele-aware match was identified in the local curated pharmacogenomic reference. Under the controlled project interpretation, the genotype supported the reported project diplotype and functional phenotype.

Add:

Medication or dose changes should not be made from this project output alone. The result requires genotype confirmation, complete diplotype assessment and review of the current professional guideline.

Pharmacogenomic evidence must not increase the rare-disease universal score.

19.37 Test-result recommendations
---------------------------------

Recommendations should follow the strength of the result.

Appropriate recommendations may include:

- Clinical correlation is recommended.

- Genetic counselling is recommended.

- Orthogonal confirmation is recommended before clinical use.

- Segregation analysis may clarify inheritance.

- Testing of relevant relatives may be considered after confirmation.

- Periodic re-evaluation may be appropriate.

Specialist repeat-expansion testing is recommended.

Dedicated CNV confirmation may be required.

Avoid:

- Start this medication.

- Stop this medication.

- Increase the dose.

- The patient must undergo a procedure.

The pipeline is not a treatment-prescribing system.

19.38 References
----------------

The report builder accepts one reference per line.

Relevant references may include:

- ClinVar record or publication

- Gene2Phenotype resource

- Primary disease literature

- Functional variant study

- ACMG/AMP guideline

- CNV interpretation guideline

- ClinPGx or CPIC guideline

Each reference should be verified before inclusion.

A reference should contain, where available:

- Authors

- Title

- Journal or organisation

- Year

- DOI or PMID

Do not copy an automatically generated reference without checking it.

19.39 Signatory information
---------------------------

The signatory field should be completed only by an authorised reviewer.

For an educational report, use:

Prepared for educational demonstration; not clinically signed out.

Do not enter:

Clinical Laboratory Director

or a professional’s name unless that individual has reviewed and authorised the report.

19.40 Report quality-control review
-----------------------------------

Before export, review the report on the screen from beginning to end.

Check:

- Patient and case identifiers

- Testing indication

- Assay title

- Specimen

- Genome build

- Gene symbol

- Transcript version

- Chromosome coordinate

- REF and ALT

- HGVS coding expression

- HGVS protein expression

- Zygosity

- Inheritance

- Classification

- Confirmation status

- Phenotype

- Interpretation

- References

- Recommendations

- Signatory

- Limitations

The live preview should be treated as a draft until all fields have passed review.

19.41 Automated sentence quality control
----------------------------------------

The automatically generated test-result sentence must not contain:

- A blank classification

- A blank gene

- A blank condition

- “undefined”

- A false Sanger confirmation

- A diagnosis unsupported by the evidence

- A VUS described as definitively causal

Read the sentence aloud before export.

When the automatic sentence is inappropriate for a CNV, repeat expansion or complex result, modify the report builder or use a dedicated manually written result statement.

19.42 Exporting the report as PDF
---------------------------------

After completing the report:

Click:

.. code-block:: text

   Print / Save as PDF

Select:

Save as PDF

Review:

Paper size

Margins

Scale

Page breaks

Header and footer

Confirm that no form panel appears in the PDF.

Save the file using a non-identifying filename.

Recommended:

case_001.genomic_report.pdf

Avoid:

PatientName_DateOfBirth_genetic_report.pdf

19.42.1 Create the final report directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   REPORT_DIR="results/cases/$CASE_ID/final/report"
   mkdir -p "$REPORT_DIR"
   chmod \
       u=rwx,go= \
       "$REPORT_DIR"
   echo "Report directory:"
   echo "$REPORT_DIR"

Move the exported PDF into this directory through File Explorer or an approved local file-management method.

19.43 Checksum the final report
-------------------------------

After saving the PDF:

.. code-block:: text

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   REPORT_PDF="results/cases/$CASE_ID/final/report/${CASE_ID}.genomic_report.pdf"
   if [[ ! -s "$REPORT_PDF" ]]; then
       echo "ERROR: Final report PDF is missing or empty:"
       echo "$REPORT_PDF"
       exit 1
   fi
   sha256sum \
       "$REPORT_PDF" \
       > "${REPORT_PDF}.sha256"
   sha256sum \
       --check \
       "${REPORT_PDF}.sha256"

The checksum helps confirm that the reviewed report has not changed after finalisation.

19.44 Preserve report provenance
--------------------------------

The final report should be linked to:

- Case ID

- Input VCF checksum

- Phenotype-file checksum

- Pipeline commit or source version

- Resource mode

- Master-table checksum

- Report PDF checksum

- Report date

- Reviewer

A compact local provenance file may be created:

.. code-block:: text

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_ID="case_001"
   REPORT_DIR="results/cases/$CASE_ID/final/report"
   REPORT_PDF="$REPORT_DIR/${CASE_ID}.genomic_report.pdf"
   PROVENANCE="$REPORT_DIR/${CASE_ID}.report_provenance.tsv"
   {
       printf 'field\tvalue\n'
       printf 'case_id\t%s\n' "$CASE_ID"
       printf 'report_created_utc\t%s\n' \
           "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
       printf 'report_pdf\t%s\n' "$REPORT_PDF"
       printf 'report_sha256\t%s\n' \
           "$(sha256sum "$REPORT_PDF" | awk '{print $1}')"
       printf 'pipeline_source_version\t%s\n' \
           "$(git rev-parse HEAD 2>/dev/null || echo unavailable)"
   } > "$PROVENANCE"
   column \
       --separator $'\t' \
       --table \
       "$PROVENANCE"

This command records the existing local source version only. It does not require publishing or pushing anything.

19.45 Privacy protection for the final report
---------------------------------------------

The report may contain:

- Patient identifiers

- Phenotype information

- Genomic findings

- Family implications

- Pharmacogenomic information

It must therefore be stored as sensitive data.

Do not place the completed report in:

- Public documentation

- A public website

- An unrestricted shared folder

- Screenshots for public presentation

- The synthetic validation folder

A public Read the Docs page may contain:

- The blank report template

- Synthetic examples

- Instructions for completing the report

It must not contain a completed real patient report.

19.46 Final report review responsibilities
------------------------------------------

The pipeline analyst is responsible for:

- Transferring the correct evidence

- Preserving uncertainty

- Checking coordinates and alleles

- Documenting limitations

- Avoiding unsupported clinical claims

A qualified genetics or laboratory professional is responsible for:

- Final classification review

- Clinical correlation

- Confirmation requirements

- Family implications

- Clinical recommendations

- Report authorisation

The report builder cannot replace either responsibility.

19.47 Reporting checklist for an SNV or indel
---------------------------------------------

- ✓ GRCh38 is stated

- ✓ Chromosome, position, REF and ALT are correct

- ✓ Gene symbol is correct

- ✓ Transcript version is included

- ✓ HGVSc is verified

- ✓ HGVSp is verified

- ✓ Zygosity matches the VCF

- ✓ Inheritance matches the gene–disease model

- ✓ ClinVar evidence includes review status

- ✓ Population evidence is interpreted cautiously

- ✓ Splice prediction is not described as confirmation

- ✓ Phenotype compatibility is explained

- ✓ Classification is not derived from score alone

- ✓ Confirmation status is truthful

19.48 Reporting checklist for a CNV
-----------------------------------

- ✓ GRCh38 interval is stated

- ✓ Start and end coordinates are correct

- ✓ DEL or DUP is correct

- ✓ Interval size is correct

- ✓ Copy number is included only when available

- ✓ Breakpoint precision is described

- ✓ Full and split AnnotSV rows are not counted as separate CNVs

- ✓ ClinGen dosage evidence is reviewed

- ✓ ClassifyCNV output is reviewed

- ✓ ISV-CNV output is described as a model prediction

- ✓ Phenotype and inheritance are included

- ✓ Appropriate confirmation method is stated

19.49 Reporting checklist for a repeat expansion
------------------------------------------------

- ✓ Gene or locus is correct

- ✓ Repeat motif is stated

- ✓ Reported repeat count is stated

- ✓ Threshold source is clear

- ✓ Genotype is stated

- ✓ detected_not_interpreted is preserved where applicable

- ✓ Read-level sizing is not claimed

- ✓ Specialist confirmation is recommended

19.50 Reporting checklist for a PGx finding
-------------------------------------------

- ✓ Exact CHROM-POS-REF-ALT match is confirmed

- ✓ rsID alone was not used

- ✓ Genotype is stated

- ✓ Project diplotype is stated cautiously

- ✓ Functional phenotype is stated

- ✓ Drug association is stated

- ✓ Guideline review is recommended

- ✓ No medication change is instructed

- ✓ PGx is separated from rare-disease diagnosis

19.51 Complete final report checklist
-------------------------------------

The clinical-style reporting stage is complete when:

- ✓ The pipeline completed successfully

- ✓ The correct case outputs were reviewed

- ✓ The principal finding was selected after evidence review

- ✓ The report title matches the actual analysis

- ✓ Laboratory details are authorised

- ✓ Patient and case information is accurate

- ✓ Synthetic placeholders were removed or retained intentionally

- ✓ GRCh38 is stated

- ✓ The gene and transcript are verified

- ✓ The variant representation is verified

- ✓ Zygosity and inheritance are correct

- ✓ Classification is evidence based

- ✓ Confirmation status is truthful

- ✓ The automatic result sentence was manually reviewed

- ✓ The phenotype paragraph reflects submitted clinical information

- ✓ Variant and gene interpretations are complete

- ✓ Conflicting and missing evidence are disclosed

- ✓ CNVs and repeats are not forced into SNV fields

- ✓ PGx findings are reported separately

- ✓ References are checked

- ✓ Recommendations remain within project scope

- ✓ The educational or clinical limitation is visible

- ✓ The report was reviewed before export

- ✓ The final PDF is stored in a protected case directory

- ✓ A report checksum was generated

- ✓ The report was not uploaded to public documentation

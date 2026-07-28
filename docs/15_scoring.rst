.. _15-universal-evidence-scoring-candidate-ranking-and-master-table-generation:

15. Universal Evidence Scoring, Candidate Ranking and Master-Table Generation
=============================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


After annotation, disease mapping, phenotype comparison and inheritance evaluation, the pipeline combines the available evidence into prioritisation scores. The purpose of this stage is to arrange candidates in a reviewable order while preserving the evidence that produced each score.

The scoring workflow is:

Annotated small variants and CNVs

│

▼

Evidence-field validation

│

▼

Functional and clinical evidence

│

▼

Gene–disease and phenotype evidence

│

▼

Inheritance and genotype compatibility

│

▼

Small-variant or CNV-specific scoring

│

▼

Candidate ordering and rank assignment

│

▼

Integrated universal master table

│

▼

Human-review and reproducibility outputs

The principal project scripts are:

-  

   .. container::

      pipeline/case_workflow/10b_calibrate_clinvar_ranking.py

-  

   .. container::

      pipeline/case_workflow/11_score_universal_evidence.py

-  

   .. container::

      pipeline/case_workflow/11b_score_universal_cnv.py

-  

   .. container::

      pipeline/case_workflow/12_score_cnv_candidates.py

-  

   .. container::

      pipeline/case_workflow/12_build_universal_master.py

-  

   .. container::

      pipeline/case_workflow/14_build_master_candidate_table.py

The exact weights, thresholds and status labels are defined in the committed source code. They should not be reconstructed manually in the report or modified without rerunning the complete validation suite.

.. _15-1-purpose-of-evidence-scoring:

15.1 Purpose of evidence scoring
--------------------------------

A genomic candidate may have several independent or partially overlapping forms of evidence.

Examples include:

-  

   .. container::

      Predicted molecular consequence

-  

   .. container::

      ClinVar classification

-  

   .. container::

      ClinVar review status

-  

   .. container::

      Population allele frequency

-  

   .. container::

      SpliceAI prediction

-  

   .. container::

      Gene–disease validity

-  

   .. container::

      Disease mechanism

-  

   .. container::

      Phenotype similarity

-  

   .. container::

      Inheritance compatibility

-  

   .. container::

      Compound-heterozygous evidence

-  

   .. container::

      Dosage sensitivity

-  

   .. container::

      CNV classification

-  

   .. container::

      Machine-learning prediction

Reviewing every field separately is necessary, but it becomes difficult when a case contains many variants. The project score therefore provides a consistent method for ranking candidates.

The score answers:

Which candidates should be reviewed first?

It does not independently answer:

Which variant definitely caused the patient’s condition?

.. _15-2-the-score-is-not-a-probability:

15.2 The score is not a probability
-----------------------------------

A candidate score such as:

74.07

must not be interpreted as:

74.07% probability that the variant is pathogenic

or:

74.07% probability that the patient has the disease

The score is a project-specific numerical summary of available evidence.

It may be useful for:

-  candidate ordering;

-  regression testing;

-  comparing outputs from the same pipeline version;

-  identifying evidence-rich variants;

-  highlighting candidates requiring manual review.

It must not be used as a substitute for formal ACMG/AMP variant classification, CNV classification or clinical diagnosis.

.. _15-3-evidence-domains-for-small-variants:

15.3 Evidence domains for small variants
----------------------------------------

The small-variant scoring script is:

.. code:: bash

   pipeline/case_workflow/11_score_universal_evidence.py

The score may use evidence from the following domains.

.. _15-3-1-functional-consequence:

15.3.1 Functional consequence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Functional annotation is obtained primarily from VEP and SnpEff.

Relevant fields may include:

-  

   .. container::

      VEP Consequence

-  

   .. container::

      VEP IMPACT

-  

   .. container::

      SnpEff ANN effect

-  

   .. container::

      SnpEff impact

-  

   .. container::

      Transcript

-  

   .. container::

      MANE Select status

-  

   .. container::

      Canonical status

-  

   .. container::

      Coding or protein consequence

Examples of potentially high-priority consequences include:

-  

   .. container::

      stop_gained

-  

   .. container::

      frameshift_variant

-  

   .. container::

      splice_acceptor_variant

-  

   .. container::

      splice_donor_variant

-  

   .. container::

      start_lost

-  

   .. container::

      transcript_ablation

Examples of moderate consequences include:

-  

   .. container::

      missense_variant

-  

   .. container::

      inframe_deletion

-  

   .. container::

      inframe_insertion

-  

   .. container::

      protein_altering_variant

The score must still consider whether the predicted consequence matches the disease mechanism.

A stop-gained variant should not automatically receive maximum disease relevance when the associated condition is known to result only from a restricted gain-of-function mechanism.

.. _15-3-2-clinvar-evidence:

15.3.2 ClinVar evidence
~~~~~~~~~~~~~~~~~~~~~~~

ClinVar fields include:

-  

   .. container::

      CLNSIG

-  

   .. container::

      CLNDN

-  

   .. container::

      CLNREVSTAT

The project distinguishes between:

-  

   .. container::

      Clinical significance

-  

   .. container::

      Review status

-  

   .. container::

      Condition relevance

A pathogenic assertion with stronger review status generally provides more useful evidence than a weakly reviewed assertion.

However, ClinVar evidence must be calibrated because:

-  the assertion may relate to another disease;

-  submissions may conflict;

-  review status may be limited;

-  the record may contain several condition names;

-  classifications may change between releases.

The calibration script is:

.. code:: bash

   pipeline/case_workflow/10b_calibrate_clinvar_ranking.py

.. _15-3-3-population-frequency-evidence:

15.3.3 Population-frequency evidence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Population frequency helps determine whether a variant is plausible for a rare disorder.

The workflow may use cached gnomAD exome frequency from VEP.

Important principles include:

-  

   .. container::

      A very common allele is usually incompatible

-  

   .. container::

      with a highly penetrant severe rare disorder.

-  

   .. container::

      A rare allele is not automatically pathogenic.

-  

   .. container::

      An absent allele is not automatically pathogenic.

-  

   .. container::

      Frequency must be interpreted with inheritance,

.. container::

   penetrance, ancestry and disease prevalence.

-  

   .. container::

      The main disease candidate should also be checked manually against the current gnomAD website during final interpretation.

-  

   .. container::

      The full gnomAD dataset is not required for this project.

.. _15-3-4-spliceai-evidence:

15.3.4 SpliceAI evidence
~~~~~~~~~~~~~~~~~~~~~~~~

SpliceAI contributes predicted splice-disruption evidence.

Potentially relevant fields include:

-  

   .. container::

      DS_AG

-  

   .. container::

      DS_AL

-  

   .. container::

      DS_DG

-  

   .. container::

      DS_DL

-  

   .. container::

      maximum delta score

-  

   .. container::

      predicted splice effect

-  

   .. container::

      relative splice position

A high score can increase prioritisation when:

-  the gene–disease relationship is relevant;

-  the transcript is appropriate;

-  the predicted effect is biologically plausible;

-  the variant is compatible with the disease mechanism.

SpliceAI does not independently prove abnormal RNA splicing.

.. _15-3-5-gene-disease-evidence:

15.3.5 Gene–disease evidence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Gene2Phenotype evidence may include:

-  

   .. container::

      Disease name

-  

   .. container::

      Disease identifier

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

A candidate receives stronger disease relevance when:

-  

   .. container::

      The gene has an established disease model

-  

   .. container::

      The disease model matches the patient phenotype

-  

   .. container::

      The variant consequence matches the mechanism

-  

   .. container::

      The genotype satisfies the allelic requirement

A gene match alone is not sufficient when the variant type is incompatible with the known mechanism.

.. _15-3-6-phenotype-evidence:

15.3.6 Phenotype evidence
~~~~~~~~~~~~~~~~~~~~~~~~~

Phenotype evidence may include:

-  

   .. container::

      Exact HPO matches

-  

   .. container::

      Number of matched terms

-  

   .. container::

      Direct phenotype score

-  

   .. container::

      Semantic phenotype score

-  

   .. container::

      Phenotype evidence status

A high phenotype score can increase candidate priority, but a low phenotype score should not automatically exclude a strong candidate because:

-  phenotyping may be incomplete;

-  disease features may be age dependent;

-  the presentation may be atypical;

-  ontology annotations may be incomplete;

-  broad HPO terms may have been supplied.

Missing HPO data must be distinguished from evaluated phenotype incompatibility.

.. _15-3-7-inheritance-evidence:

15.3.7 Inheritance evidence
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inheritance evidence may include:

-  

   .. container::

      Observed genotype

-  

   .. container::

      Zygosity

-  

   .. container::

      Patient sex

-  

   .. container::

      Chromosome ploidy

-  

   .. container::

      G2P allelic requirement

-  

   .. container::

      Inheritance compatibility

-  

   .. container::

      Compound-heterozygous status

-  

   .. container::

      Phase evidence

Examples of stronger compatibility include:

-  

   .. container::

      Heterozygous candidate in a compatible monoallelic model

-  

   .. container::

      Homozygous candidate in a compatible biallelic model

-  

   .. container::

      Qualifying phased-trans pair in a recessive model

-  

   .. container::

      Hemizygous X-linked candidate in a compatible context

Examples of partial evidence include:

-  

   .. container::

      Single heterozygous candidate in a recessive model

-  

   .. container::

      Two unphased heterozygous candidates

-  

   .. container::

      Sex-dependent interpretation with unresolved sex

-  

   .. container::

      An incompatible inheritance model should be retained as a visible warning rather than silently removed.

.. _15-4-avoiding-double-counted-evidence:

15.4 Avoiding double-counted evidence
-------------------------------------

Several annotation sources may represent related biological information.

Examples include:

-  

   .. container::

      VEP high-impact consequence

-  

   .. container::

      SnpEff high-impact consequence

-  

   .. container::

      ClinVar pathogenic assertion

-  

   .. container::

      Gene2Phenotype loss-of-function mechanism

.. container::

   These are not necessarily four completely independent observations.

Similarly, CNV tools may all use:

-  ClinGen dosage data;

-  overlapping disease genes;

-  population CNVs;

-  interval size;

-  gene count.

The project score should therefore avoid treating repeated representations of the same underlying evidence as fully independent proof.

The report must describe the score as an integrated prioritisation method rather than an evidence-counting vote.

.. _15-5-missing-evidence:

15.5 Missing evidence
---------------------

A missing annotation should not automatically be treated as negative evidence.

Examples include:

-  

   .. container::

      No ClinVar match

-  

   .. container::

      No SpliceAI prediction

-  

   .. container::

      No Gene2Phenotype relationship

-  

   .. container::

      No HPO terms supplied

-  

   .. container::

      No population frequency

-  

   .. container::

      No resolved inheritance model

These may indicate:

-  a novel variant;

-  incomplete annotation;

-  unsupported variant type;

-  missing patient metadata;

-  unavailable external data;

-  a resource-version difference.

Recommended evidence states include:

-  

   .. container::

      present

-  

   .. container::

      absent

-  

   .. container::

      not_available

-  

   .. container::

      not_assessed

-  

   .. container::

      not_applicable

-  

   .. container::

      conflicting

The exact values should follow the committed output schema.

.. _15-6-conflicting-evidence:

15.6 Conflicting evidence
-------------------------

A candidate can contain contradictory evidence.

Examples include:

-  

   .. container::

      ClinVar pathogenic but population frequency is high

-  

   .. container::

      Strong functional consequence but phenotype mismatch

-  

   .. container::

      Strong phenotype match but incompatible inheritance

-  

   .. container::

      High SpliceAI score but unrelated gene–disease model

-  

   .. container::

      Machine-learning pathogenic prediction but benign CNV overlap

-  

   .. container::

      The scoring stage should preserve each contributing field and write a warning or conflict status.

-  

   .. container::

      Conflicting evidence must not be hidden by the final numerical score.

.. _15-7-clinvar-ranking-calibration:

15.7 ClinVar ranking calibration
--------------------------------

The calibration script is:

.. code:: bash

   pipeline/case_workflow/10b_calibrate_clinvar_ranking.py

Its purpose is to prevent all ClinVar matches from contributing equally.

The calibration can consider:

-  

   .. container::

      Clinical significance

-  

   .. container::

      Review status

-  

   .. container::

      Conflicting classifications

-  

   .. container::

      Condition relevance

-  

   .. container::

      Strength of supporting disease identity

Conceptually, the following are different:

-  

   .. container::

      Pathogenic with expert-panel review

-  

   .. container::

      Pathogenic from a single submitter

-  

   .. container::

      Conflicting pathogenic and benign submissions

-  

   .. container::

      Pathogenic for an unrelated condition

-  

   .. container::

      Variant of uncertain significance

-  

   .. container::

      Likely benign

-  

   .. container::

      Benign

The exact numerical contribution is controlled by the source code.

.. _15-7-1-validate-the-calibration-script:

15.7.1 Validate the calibration script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/10b_calibrate_clinvar_ranking.py"
   if [[ ! -s "$SCRIPT" ]]; then
   echo "ERROR: ClinVar calibration script is missing:"
   echo "$SCRIPT"
   exit 1
   fi
   python -m py_compile "$SCRIPT"
   echo "PASS: ClinVar calibration script passed syntax validation."

Inspect its interface:

.. code:: bash

   if python "$SCRIPT" --help \
   > /tmp/clinvar_calibration_help.txt \
   2>&1
   then
   cat /tmp/clinvar_calibration_help.txt
   else
   echo "INFO: No standard --help interface was returned."
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$SCRIPT" \
   || true
   fi
   rm -f /tmp/clinvar_calibration_help.txt

.. _15-8-stable-candidate-identity:

15.8 Stable candidate identity
------------------------------

Every candidate should have a stable genomic identifier.

For a small variant, the project commonly uses a key equivalent to:

.. code:: bash

   chromosome:position:reference>alternate

Example:

.. code:: bash

   chr12:102840493:G>A

This key is preferable to using the rsID alone because:

-  many variants have no rsID;

-  one rsID may have several alleles;

-  identifiers can be merged or updated;

-  exact allele matching requires REF and ALT.

The key must be generated after normalisation.

.. _15-8-1-create-a-normalised-small-variant-key:

15.8.1 Create a normalised small-variant key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="results/tool_tests/small_variant_workflow/05.spliceai.vcf.gz"
   bcftools query \
   --format '%CHROM:%POS:%REF>%ALT\n' \
   "$VCF" |
   head -n 20

Multiallelic records should already have been decomposed before this stage.

.. _15-9-small-variant-universal-scoring:

15.9 Small-variant universal scoring
------------------------------------

The principal script is:

.. code:: bash

   pipeline/case_workflow/11_score_universal_evidence.py

The script should receive a structured table containing the evidence produced by earlier stages.

It may generate fields such as:

-  

   .. container::

      functional_score

-  

   .. container::

      clinical_score

-  

   .. container::

      population_score

-  

   .. container::

      disease_score

-  

   .. container::

      phenotype_score

-  

   .. container::

      inheritance_score

-  

   .. container::

      splice_score

-  

   .. container::

      compound_het_score

-  

   .. container::

      conflict_penalty

-  

   .. container::

      universal_score

-  

   .. container::

      score_status

These are conceptual names. The exact output fields must be read from the generated file.

.. _15-9-1-inspect-the-scoring-interface:

15.9.1 Inspect the scoring interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/11_score_universal_evidence.py"
   if [[ ! -s "$SCRIPT" ]]; then
   echo "ERROR: Universal scoring script is missing."
   exit 1
   fi
   python -m py_compile "$SCRIPT"
   if python "$SCRIPT" --help \
   > /tmp/universal_scoring_help.txt \
   2>&1
   then
   cat /tmp/universal_scoring_help.txt
   else
   echo "INFO: No standard --help output was returned."
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$SCRIPT" \
   || true
   fi
   rm -f /tmp/universal_scoring_help.txt

The complete launcher should remain the normal method for calling the scorer.

.. _15-10-compound-heterozygous-evidence-in-scoring:

15.10 Compound-heterozygous evidence in scoring
-----------------------------------------------

A recessive candidate may involve two variants.

The scoring stage must preserve both:

-  

   .. container::

      Individual variant evidence

-  

   .. container::

      Pair-level inheritance evidence

A phased-trans pair can receive stronger inheritance support than an unphased pair.

A conceptual distinction is:

+------------------------------------------+------------------------------------------+
| **Compound-heterozygous state**          | **Scoring implication**                  |
+==========================================+==========================================+
| Shared phase set and opposite haplotypes | Stronger pair evidence                   |
+------------------------------------------+------------------------------------------+
| Same phase set and same haplotype        | Cis; no biallelic support                |
+------------------------------------------+------------------------------------------+
| Both heterozygous but unphased           | Possible pair only                       |
+------------------------------------------+------------------------------------------+
| Different phase sets                     | Phase unresolved                         |
+------------------------------------------+------------------------------------------+
| Homozygous candidate                     | Biallelic, but not compound heterozygous |
+------------------------------------------+------------------------------------------+
| Different genes                          | Not a valid pair                         |
+------------------------------------------+------------------------------------------+

The numerical score must not hide the phase status.

Recommended pair-level fields include:

-  

   .. container::

      pair_id

-  

   .. container::

      gene

-  

   .. container::

      variant_1

-  

   .. container::

      variant_2

-  

   .. container::

      phase_status

-  

   .. container::

      phase_set

-  

   .. container::

      pair_score

-  

   .. container::

      inheritance_status

.. _15-11-candidate-filtering-versus-ranking:

15.11 Candidate filtering versus ranking
----------------------------------------

The pipeline should distinguish between:

Exclusion from an inappropriate branch

and:

Low candidate rank

Examples of branch exclusion include:

-  repeat expansion excluded from ordinary SNV scoring;

-  unsupported structural variant excluded from CNV classification;

-  wrong pharmacogenomic allele excluded from exact PGx matching;

-  malformed record rejected during preflight.

Examples of low rank include:

-  common variant;

-  weak phenotype evidence;

-  low-impact consequence;

-  incompatible inheritance;

-  benign clinical evidence.

A low-ranked candidate should remain in the complete output unless there is a documented technical or structural reason for exclusion.

.. _15-12-repeat-expansion-scoring-behaviour:

15.12 Repeat-expansion scoring behaviour
----------------------------------------

A routed repeat expansion receives:

-  

   .. container::

      detected_not_interpreted

-  

   .. container::

      It must not receive an ordinary universal small-variant score.

..

   The repeat record should appear in:

-  

   .. container::

      Dedicated repeat report

-  

   .. container::

      Universal route summary

-  

   .. container::

      Reproducibility manifest

-  

   .. container::

      Case-level human-readable report

-  

   .. container::

      It should not appear as a conventionally ranked SNV or indel.

This behaviour was validated through the Patient 03 controlled repeat case.

.. _15-13-pharmacogenomic-evidence-remains-separate:

15.13 Pharmacogenomic evidence remains separate
-----------------------------------------------

ClinPGx evidence is clinically useful, but it answers a different question from rare-disease evidence.

Therefore:

-  

   .. container::

      PGx match status

-  

   .. container::

      Star allele

-  

   .. container::

      Diplotype

-  

   .. container::

      Metaboliser phenotype

-  

   .. container::

      Drug association

must not increase the rare-disease candidate score.

The final master table may contain pharmacogenomic columns for convenience, but the PGx result must remain a separate branch or evidence category.

A pharmacogenomic variant may receive:

-  

   .. container::

      PGx exact match

..

   while having:

-  

   .. container::

      No rare-disease relevance

Both statements can be correct.

.. _15-14-cnv-universal-scoring:

15.14 CNV universal scoring
---------------------------

The CNV-specific scoring script is:

.. code:: bash

   pipeline/case_workflow/11b_score_universal_cnv.py

It may combine evidence from:

-  

   .. container::

      CNV type

-  

   .. container::

      Interval size

-  

   .. container::

      Gene count

-  

   .. container::

      Coding disruption

-  

   .. container::

      AnnotSV ranking

-  

   .. container::

      AnnotSV classification

-  

   .. container::

      ClassifyCNV classification

-  

   .. container::

      ClassifyCNV total score

-  

   .. container::

      ISV-CNV prediction

-  

   .. container::

      ISV-CNV probability

-  

   .. container::

      ClinGen dosage evidence

-  

   .. container::

      Gene–disease relationship

-  

   .. container::

      Phenotype similarity

-  

   .. container::

      Inheritance information

-  

   .. container::

      Population CNV evidence

-  

   .. container::

      ClinPGx overlap

A deletion and duplication affecting the same interval must not automatically receive the same score because their dosage mechanisms differ.

For example:

Deletion + haploinsufficient gene

may be strongly compatible, while:

Duplication + haploinsufficient-only gene

may not receive the same dosage support.

.. _15-14-1-validate-the-cnv-universal-scorer:

15.14.1 Validate the CNV universal scorer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/11b_score_universal_cnv.py"
   if [[ ! -s "$SCRIPT" ]]; then
   echo "ERROR: Universal CNV scoring script is missing."
   exit 1
   fi
   python -m py_compile "$SCRIPT"
   if python "$SCRIPT" --help \
   > /tmp/universal_cnv_scoring_help.txt \
   2>&1
   then
   cat /tmp/universal_cnv_scoring_help.txt
   else
   echo "INFO: No standard --help interface was returned."
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$SCRIPT" \
   || true
   fi
   rm -f /tmp/universal_cnv_scoring_help.txt

.. _15-15-cnv-candidate-scoring-and-ordering:

15.15 CNV candidate scoring and ordering
----------------------------------------

The additional CNV scorer is:

.. code:: bash

   pipeline/case_workflow/12_score_cnv_candidates.py

This stage can transform tool-level evidence into candidate-level records.

For example, AnnotSV may contain:

-  

   .. container::

      One full interval row

-  

   .. container::

      Several split transcript rows

-  

   .. container::

      Several gene-level rows

These must be grouped into one source CNV before candidate rank is assigned.

The candidate-level record should preserve:

-  

   .. container::

      Source CNV identifier

-  

   .. container::

      Interval

-  

   .. container::

      DEL or DUP

-  

   .. container::

      Principal dosage evidence

-  

   .. container::

      Most relevant gene–disease model

-  

   .. container::

      Phenotype evidence

-  

   .. container::

      Tool classifications

-  

   .. container::

      Universal CNV score

-  

   .. container::

      Warnings

.. _15-15-1-validate-the-cnv-candidate-scorer:

15.15.1 Validate the CNV candidate scorer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/12_score_cnv_candidates.py"
   if [[ ! -s "$SCRIPT" ]]; then
   echo "ERROR: CNV candidate scorer is missing."
   exit 1
   fi
   python -m py_compile "$SCRIPT"
   echo "PASS: CNV candidate scorer passed syntax validation."

.. _15-16-ranking-rules:

15.16 Ranking rules
-------------------

Candidate ranking should be deterministic.

This means that identical inputs, resources and source code should produce the same ordering.

The main sort key is normally:

-  

   .. container::

      Universal score, descending

A deterministic secondary key should be used when scores are equal.

Possible secondary keys include:

-  

   .. container::

      Evidence completeness

-  

   .. container::

      Clinical evidence strength

-  

   .. container::

      Phenotype score

-  

   .. container::

      Inheritance compatibility

-  

   .. container::

      Stable genomic key

The exact ordering must follow the committed code.

A tie should not be broken through:

-  file-system order;

-  random order;

-  dictionary insertion order;

-  run time;

-  uncontrolled database response order.

.. _15-16-1-inspect-sort-and-rank-logic:

15.16.1 Inspect sort and rank logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SCORING_SCRIPTS=(
   pipeline/case_workflow/11_score_universal_evidence.py
   pipeline/case_workflow/11b_score_universal_cnv.py
   pipeline/case_workflow/12_score_cnv_candidates.py
   pipeline/case_workflow/12_build_universal_master.py
   pipeline/case_workflow/14_build_master_candidate_table.py
   )
   grep -nE \
   'sort_values|sorted\(|rank\(|ascending|reverse|tie|candidate_rank' \
   "${SCORING_SCRIPTS[@]}" \
   || true

This inspection does not execute or modify the workflow.

.. _15-17-universal-master-table-generation:

15.17 Universal master-table generation
---------------------------------------

The integration script is:

.. code:: bash

   pipeline/case_workflow/12_build_universal_master.py

It brings the analytical branches together.

The universal master can include:

-  

   .. container::

      Small variants

-  

   .. container::

      CNVs

-  

   .. container::

      Repeat-expansion route statuses

-  

   .. container::

      Unsupported structural variants

-  

   .. container::

      ClinPGx results

-  

   .. container::

      Case metadata

-  

   .. container::

      Phenotype information

-  

   .. container::

      Resource mode

-  

   .. container::

      Execution status

The master table should preserve branch identity so that unlike records are not interpreted as though they were scored by the same method.

Recommended branch labels include:

-  

   .. container::

      small_variant

-  

   .. container::

      cnv

-  

   .. container::

      repeat_expansion

-  

   .. container::

      unsupported_structural_variant

-  

   .. container::

      clinpgx

The exact values should follow the generated output.

.. _15-17-1-validate-the-universal-master-builder:

15.17.1 Validate the universal-master builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/12_build_universal_master.py"
   if [[ ! -s "$SCRIPT" ]]; then
   echo "ERROR: Universal-master builder is missing."
   exit 1
   fi
   python -m py_compile "$SCRIPT"
   if python "$SCRIPT" --help \
   > /tmp/universal_master_help.txt \
   2>&1
   then
   cat /tmp/universal_master_help.txt
   else
   echo "INFO: No standard --help interface was returned."
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$SCRIPT" \
   || true
   fi
   rm -f /tmp/universal_master_help.txt

.. _15-18-final-master-candidate-table:

15.18 Final master candidate table
----------------------------------

The final candidate-table script is:

.. code:: bash

   pipeline/case_workflow/14_build_master_candidate_table.py

Its purpose is to produce a reviewer-friendly table containing the most important evidence fields while preserving links or identifiers to the complete detailed outputs.

A final candidate table may contain:

-  

   .. container::

      case_id

-  

   .. container::

      sample_id

-  

   .. container::

      branch

-  

   .. container::

      candidate_rank

-  

   .. container::

      candidate_key

-  

   .. container::

      chromosome

-  

   .. container::

      position

-  

   .. container::

      reference

-  

   .. container::

      alternate

-  

   .. container::

      variant_id

-  

   .. container::

      gene

-  

   .. container::

      transcript

-  

   .. container::

      consequence

-  

   .. container::

      resolved_disease

-  

   .. container::

      disease_identifier

-  

   .. container::

      g2p_confidence

-  

   .. container::

      molecular_mechanism

-  

   .. container::

      allelic_requirement

-  

   .. container::

      clinvar_significance

-  

   .. container::

      clinvar_review_status

-  

   .. container::

      population_frequency

-  

   .. container::

      spliceai_max_score

-  

   .. container::

      phenotype_score

-  

   .. container::

      inheritance_status

-  

   .. container::

      compound_het_status

-  

   .. container::

      cnv_type

-  

   .. container::

      cnv_size

-  

   .. container::

      annotsv_class

-  

   .. container::

      classifycnv_class

-  

   .. container::

      isv_prediction

-  

   .. container::

      universal_score

-  

   .. container::

      score_status

-  

   .. container::

      warning

The exact columns should be documented by reading the generated header.

.. _15-18-1-validate-the-master-table-builder:

15.18.1 Validate the master-table builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/14_build_master_candidate_table.py"
   if [[ ! -s "$SCRIPT" ]]; then
   echo "ERROR: Master candidate-table script is missing."
   exit 1
   fi
   python -m py_compile "$SCRIPT"
   if python "$SCRIPT" --help \
   > /tmp/master_candidate_table_help.txt \
   2>&1
   then
   cat /tmp/master_candidate_table_help.txt
   else
   echo "INFO: No standard --help interface was returned."
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$SCRIPT" \
   || true
   fi
   rm -f /tmp/master_candidate_table_help.txt

.. _15-19-preserve-detailed-evidence:

15.19 Preserve detailed evidence
--------------------------------

The master table is a summary. It must not replace:

-  

   .. container::

      Annotated VCFs

-  

   .. container::

      Full VEP table

-  

   .. container::

      Full SnpEff annotations

-  

   .. container::

      ClinVar-integrated file

-  

   .. container::

      SpliceAI file

-  

   .. container::

      G2P mapping table

-  

   .. container::

      Phenotype evidence table

-  

   .. container::

      Inheritance output

-  

   .. container::

      Compound-heterozygous table

-  

   .. container::

      AnnotSV output

-  

   .. container::

      ClassifyCNV scoresheet

-  

   .. container::

      ISV-CNV output

-  

   .. container::

      Repeat report

-  

   .. container::

      Unsupported-record report

-  

   .. container::

      ClinPGx table

A reviewer should be able to move from:

Master candidate row

back to:

Original VCF record and complete evidence

using stable identifiers.

.. _15-20-recommended-evidence-provenance-fields:

15.20 Recommended evidence-provenance fields
--------------------------------------------

Each final row should retain provenance such as:

-  

   .. container::

      source_vcf

-  

   .. container::

      source_vcf_sha256

-  

   .. container::

      source_record_key

-  

   .. container::

      analysis_branch

-  

   .. container::

      resource_mode

-  

   .. container::

      vep_version

-  

   .. container::

      vep_cache_version

-  

   .. container::

      snpeff_version

-  

   .. container::

      clinvar_release

-  

   .. container::

      g2p_resource

-  

   .. container::

      hpo_release

-  

   .. container::

      mondo_release

-  

   .. container::

      scoring_script_sha256

-  

   .. container::

      pipeline_commit

-  

   .. container::

      run_timestamp

Not all values need to be repeated in every row when they are stored in a linked case manifest. The master table should at least include the manifest path or run identifier.

.. _15-21-inspect-a-generated-master-table-safely:

15.21 Inspect a generated master table safely
---------------------------------------------

Set the actual file produced by a completed case:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MASTER_TABLE="path/to/master_candidate_table.tsv"

Inspect its structure:

.. code:: bash

   if [[ ! -s "$MASTER_TABLE" ]]; then
   echo "ERROR: Master candidate table is missing:"
   echo "$MASTER_TABLE"
   exit 1
   fi
   python3 - "$MASTER_TABLE" <<'PY'
   from __future__ import annotations
   import csv
   import sys
   from pathlib import Path
   path = Path(sys.argv[1])
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.reader(
   handle,
   delimiter="\t",
   )
   header = next(reader, None)
   if not header:
   raise SystemExit("ERROR: Header is missing.")
   rows = [
   row
   for row in reader
   if row and any(value.strip() for value in row)
   ]
   width_failures = [
   index
   for index, row in enumerate(rows, start=2)
   if len(row) != len(header)
   ]
   print(f"File: {path}")
   print(f"Columns: {len(header)}")
   print(f"Candidate rows: {len(rows)}")
   print()
   for index, column in enumerate(header, start=1):
   print(f"{index:02d}. {column}")
   if width_failures:
   raise SystemExit(
   "ERROR: Inconsistent row widths at lines: "
   + ", ".join(map(str, width_failures))
   )
   print()
   print("PASS: Master table structure is consistent.")
   PY

Replace the placeholder only with the actual generated path.

.. _15-22-check-ranking-order-independently:

15.22 Check ranking order independently
---------------------------------------

The following command identifies a score column and confirms that numeric candidates are ordered from highest to lowest.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MASTER_TABLE="path/to/master_candidate_table.tsv"
   python3 - "$MASTER_TABLE" <<'PY'
   from __future__ import annotations
   import csv
   import re
   import sys
   from pathlib import Path
   path = Path(sys.argv[1])
   def normalise(value: str) -> str:
   value = value.strip().lower()
   value = re.sub(r"[^a-z0-9]+", "_", value)
   return value.strip("_")
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.DictReader(
   handle,
   delimiter="\t",
   )
   if not reader.fieldnames:
   raise SystemExit("ERROR: Header missing.")
   score_column = None
   preferred_names = (
   "universal_score",
   "candidate_score",
   "final_score",
   "score",
   )
   normalised_columns = {
   normalise(column): column
   for column in reader.fieldnames
   }
   for preferred in preferred_names:
   if preferred in normalised_columns:
   score_column = normalised_columns[preferred]
   break
   if score_column is None:
   print("Available columns:")
   for column in reader.fieldnames:
   print(f" {column}")
   raise SystemExit(
   "ERROR: No recognised score column found."
   )
   scored_rows = []
   for line_number, row in enumerate(
   reader,
   start=2,
   ):
   raw_score = row.get(
   score_column,
   "",
   ).strip()
   if raw_score in {
   "",
   ".",
   "NA",
   "N/A",
   "not_applicable",
   }:
   continue
   try:
   score = float(raw_score)
   except ValueError:
   raise SystemExit(
   f"ERROR: Non-numeric score at "
   f"line {line_number}: {raw_score!r}"
   )
   scored_rows.append(
   (
   line_number,
   score,
   )
   )
   failures = []
   for previous, current in zip(
   scored_rows,
   scored_rows[1:],
   ):
   previous_line, previous_score = previous
   current_line, current_score = current
   if current_score > previous_score:
   failures.append(
   (
   previous_line,
   previous_score,
   current_line,
   current_score,
   )
   )
   if failures:
   print("ERROR: Candidate scores are not descending:")
   for (
   previous_line,
   previous_score,
   current_line,
   current_score,
   ) in failures:
   print(
   f" line {previous_line}: {previous_score} "
   f"before line {current_line}: {current_score}"
   )
   raise SystemExit(1)
   print(
   f"PASS: {len(scored_rows)} numeric candidate(s) "
   f"are ordered by {score_column!r}."
   )
   PY

Repeat and unsupported records may have non-numeric score statuses and should be ignored by this numeric-order check.

.. _15-23-check-candidate-rank-consistency:

15.23 Check candidate-rank consistency
--------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MASTER_TABLE="path/to/master_candidate_table.tsv"
   python3 - "$MASTER_TABLE" <<'PY'
   from __future__ import annotations
   import csv
   import re
   import sys
   from pathlib import Path
   path = Path(sys.argv[1])
   def normalise(value: str) -> str:
   value = value.strip().lower()
   value = re.sub(r"[^a-z0-9]+", "_", value)
   return value.strip("_")
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.DictReader(
   handle,
   delimiter="\t",
   )
   if not reader.fieldnames:
   raise SystemExit("ERROR: Header missing.")
   columns = {
   normalise(column): column
   for column in reader.fieldnames
   }
   rank_column = None
   for candidate in (
   "candidate_rank",
   "rank",
   "final_rank",
   ):
   if candidate in columns:
   rank_column = columns[candidate]
   break
   if rank_column is None:
   raise SystemExit(
   "ERROR: Candidate-rank column not found."
   )
   numeric_ranks = []
   for line_number, row in enumerate(
   reader,
   start=2,
   ):
   raw_rank = row.get(
   rank_column,
   "",
   ).strip()
   if raw_rank in {
   "",
   ".",
   "NA",
   "N/A",
   "not_applicable",
   }:
   continue
   try:
   rank = int(raw_rank)
   except ValueError:
   raise SystemExit(
   f"ERROR: Invalid rank at line "
   f"{line_number}: {raw_rank!r}"
   )
   numeric_ranks.append(rank)
   if not numeric_ranks:
   raise SystemExit(
   "ERROR: No numeric candidate ranks found."
   )
   if numeric_ranks[0] != 1:
   raise SystemExit(
   "ERROR: First numeric candidate rank is not 1."
   )
   for previous, current in zip(
   numeric_ranks,
   numeric_ranks[1:],
   ):
   if current < previous:
   raise SystemExit(
   "ERROR: Candidate ranks decrease unexpectedly."
   )
   print(
   f"PASS: {len(numeric_ranks)} numeric rank(s) "
   "are structurally consistent."
   )
   PY

Tied scores may share a rank or receive sequential ranks depending on the committed implementation. The validator should not impose a different tie policy.

.. _15-24-canonical-validation-scores:

15.24 Canonical validation scores
---------------------------------

The final audit identified the following top small-variant candidates for the completed validation cases:

+------------+----------+------------------------------+-------------------+
| **Case**   | **Gene** | **Canonical candidate**      | **Project score** |
+============+==========+==============================+===================+
| Patient 01 | CFTR     | chr7:117559590:ATCT>A        | 62.96             |
+------------+----------+------------------------------+-------------------+
| Patient 02 | HBB      | chr11:5227002:T>A            | 29.63             |
+------------+----------+------------------------------+-------------------+
| Patient 04 | BRCA1    | chr17:43124027:ACT>A         | 81.48             |
+------------+----------+------------------------------+-------------------+
| Patient 05 | HEXA     | chr15:72346579:G>GGATA       | 85.19             |
+------------+----------+------------------------------+-------------------+
| Patient 06 | PAH      | chr12:102840493:G>A          | 66.67             |
+------------+----------+------------------------------+-------------------+
| Patient 07 | ATP7B    | chr13:51958333:C>A           | 48.15             |
+------------+----------+------------------------------+-------------------+
| Patient 08 | APOB     | chr2:21006288:C>T            | 70.37             |
+------------+----------+------------------------------+-------------------+
| Patient 09 | G6PD     | chrX:154536002:C>T           | 59.26             |
+------------+----------+------------------------------+-------------------+
| Patient 10 | MEFV     | chr16:3243407:T>C            | 77.78             |
+------------+----------+------------------------------+-------------------+
| Patient 11 | HFE      | chr6:26092913:G>A            | 62.96             |
+------------+----------+------------------------------+-------------------+
| Patient 12 | MLH1     | chr3:37028902:C>T            | 74.07             |
+------------+----------+------------------------------+-------------------+

Patient 03 was routed as a repeat expansion and therefore did not receive an ordinary small-variant score.

Patient 13 passed structural preflight but was intentionally not executed through the complete workflow within the project timeframe.

These scores are regression targets for the validated project version. They should not be treated as universal clinical thresholds.

.. _15-25-current-legacy-and-routed-validation-outputs:

15.25 Current, legacy and routed validation outputs
---------------------------------------------------

The final audit recognises three canonical output categories:

-  

   .. container::

      CURRENT

-  

   .. container::

      LEGACY

-  

   .. container::

      ROUTED_REPEAT

**CURRENT**

Produced by the current universal workflow.

**LEGACY**

Produced by an earlier compatible workflow and retained as the accepted canonical result for that validation case.

**ROUTED_REPEAT**

Produced by the dedicated repeat route rather than ordinary candidate scoring.

The audit script handles these categories explicitly so that a legacy result is not falsely presented as a newly rerun current result.

.. _15-26-final-audit-resources:

15.26 Final audit resources
---------------------------

The final audit directory is:

.. code:: bash

   validation/final_audit_20260727/

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

These files establish:

-  which output is canonical for each case;

-  whether the expected candidate was found;

-  whether the expected score matched;

-  whether key resources were unchanged;

-  whether pipeline source files were unchanged;

-  whether the final validation passed.

.. _15-26-1-inspect-the-canonical-case-table:

15.26.1 Inspect the canonical case table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CANONICAL_CASES="validation/final_audit_20260727/canonical_cases.tsv"
   if [[ ! -s "$CANONICAL_CASES" ]]; then
   echo "ERROR: Canonical-case table is missing."
   exit 1
   fi
   column \
   --separator $'\t' \
   --table \
   "$CANONICAL_CASES"

.. _15-26-2-verify-canonical-output-checksums:

15.26.2 Verify canonical output checksums
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   AUDIT_DIR="validation/final_audit_20260727"
   for checksum_file in \
   "$AUDIT_DIR/canonical_final_outputs.sha256" \
   "$AUDIT_DIR/key_resources.sha256" \
   "$AUDIT_DIR/pipeline_source.sha256"
   do
   if [[ ! -s "$checksum_file" ]]; then
   echo "ERROR: Missing checksum manifest:"
   echo "$checksum_file"
   exit 1
   fi
   echo
   echo "=== Verifying $checksum_file ==="
   sha256sum \
   --check \
   "$checksum_file"
   done

The command must be run from the same project-root layout used when the manifests were created.

.. _15-27-run-the-final-scoring-audit:

15.27 Run the final scoring audit
---------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   AUDIT_SCRIPT="validation/final_audit_20260727/scripts/audit_patients_01_12_final.py"
   if [[ ! -s "$AUDIT_SCRIPT" ]]; then
   echo "ERROR: Final audit script is missing."
   exit 1
   fi
   python -m py_compile "$AUDIT_SCRIPT"
   python "$AUDIT_SCRIPT"

Inspect the final status:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   STATUS_FILE="validation/final_audit_20260727/FINAL_VALIDATION_STATUS.md"
   if [[ ! -s "$STATUS_FILE" ]]; then
   echo "ERROR: Final validation status is missing."
   exit 1
   fi
   cat "$STATUS_FILE"

The validated project recorded:

Audited cases: 12

Passed cases: 12

Failed cases: 0

.. _15-28-deterministic-rerun-comparison:

15.28 Deterministic rerun comparison
------------------------------------

After a controlled rerun, compare the new result with the canonical result.

A basic exact checksum comparison is:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CANONICAL_OUTPUT="path/to/canonical_output.tsv"
   NEW_OUTPUT="path/to/new_output.tsv"
   for path in \
   "$CANONICAL_OUTPUT" \
   "$NEW_OUTPUT"
   do
   if [[ ! -s "$path" ]]; then
   echo "ERROR: Missing comparison file: $path"
   exit 1
   fi
   done
   CANONICAL_SHA256="$(
   sha256sum "$CANONICAL_OUTPUT" |
   awk '{print $1}'
   )"
   NEW_SHA256="$(
   sha256sum "$NEW_OUTPUT" |
   awk '{print $1}'
   )"
   echo "Canonical: $CANONICAL_SHA256"
   echo "New: $NEW_SHA256"
   if [[ "$CANONICAL_SHA256" == "$NEW_SHA256" ]]; then
   echo "PASS: Outputs are byte-for-byte identical."
   else
   echo "NOTICE: Output checksums differ."
   echo "Perform a structured field-level comparison."
   fi

A checksum difference may arise from timestamps or metadata even when the biological result is unchanged. A field-level comparison should therefore also evaluate:

-  

   .. container::

      Top candidate

-  

   .. container::

      Candidate key

-  

   .. container::

      Gene

-  

   .. container::

      Disease label

-  

   .. container::

      Score

-  

   .. container::

      Rank

-  

   .. container::

      Inheritance status

-  

   .. container::

      PGx result

-  

   .. container::

      Route status

.. _15-29-score-change-investigation:

15.29 Score-change investigation
--------------------------------

When a score changes, review the following in order:

1.  Confirm the input checksum.

2.  Confirm the pipeline source checksum.

3.  Confirm the active resource mode.

4.  Confirm the VEP and SnpEff versions.

5.  Confirm the ClinVar release.

6.  Confirm the G2P checksum.

7.  Confirm the HPO and MONDO releases.

8.  Confirm the local ClinPGx checksum.

9.  Confirm the container checksums.

10. Compare intermediate evidence columns.

11. Compare the final scoring implementation.

12. Document the reason for the difference.

Do not simply update the expected validation score to make a changed result pass.

.. _15-30-recommended-master-table-quality-checks:

15.30 Recommended master-table quality checks
---------------------------------------------

The master table should be checked for:

-  

   .. container::

      Unique candidate keys

-  

   .. container::

      Consistent row width

-  

   .. container::

      Valid numeric scores

-  

   .. container::

      Valid candidate ranks

-  

   .. container::

      Deterministic order

-  

   .. container::

      Branch identity

-  

   .. container::

      No duplicated homozygous compound-het pair

-  

   .. container::

      No validation-resource leakage

-  

   .. container::

      No repeat expansion in SNV ranking

-  

   .. container::

      No PGx evidence included in disease score

-  

   .. container::

      No silent missing outputs

.. _15-30-1-detect-duplicate-candidate-keys:

15.30.1 Detect duplicate candidate keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MASTER_TABLE="path/to/master_candidate_table.tsv"
   CANDIDATE_KEY_COLUMN="candidate_key"
   python3 - \
   "$MASTER_TABLE" \
   "$CANDIDATE_KEY_COLUMN" <<'PY'
   from __future__ import annotations
   import csv
   import sys
   from collections import Counter
   from pathlib import Path
   path = Path(sys.argv[1])
   key_column = sys.argv[2]
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.DictReader(
   handle,
   delimiter="\t",
   )
   if not reader.fieldnames:
   raise SystemExit("ERROR: Header missing.")
   if key_column not in reader.fieldnames:
   raise SystemExit(
   f"ERROR: Column not found: {key_column}"
   )
   keys = [
   row.get(key_column, "").strip()
   for row in reader
   if row.get(key_column, "").strip()
   ]
   duplicates = {
   key: count
   for key, count in Counter(keys).items()
   if count > 1
   }
   if duplicates:
   print("Duplicate candidate keys:")
   for key, count in sorted(duplicates.items()):
   print(f" {key}: {count}")
   raise SystemExit(1)
   print(f"PASS: {len(keys)} candidate key(s) are unique.")
   PY

Some master tables may intentionally contain one row per gene–disease model rather than one row per genomic variant. In that design, the unique key should include the resolved disease identifier.

.. _15-31-scoring-source-validation:

15.31 Scoring-source validation
-------------------------------

Compile every scoring and master-table script:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCORING_SCRIPTS=(
   pipeline/case_workflow/10b_calibrate_clinvar_ranking.py
   pipeline/case_workflow/11_score_universal_evidence.py
   pipeline/case_workflow/11b_score_universal_cnv.py
   pipeline/case_workflow/12_score_cnv_candidates.py
   pipeline/case_workflow/12_build_universal_master.py
   pipeline/case_workflow/14_build_master_candidate_table.py
   )
   FAILURES=0
   for script in "${SCORING_SCRIPTS[@]}"; do
   if [[ ! -s "$script" ]]; then
   echo "FAIL: Missing script: $script"
   FAILURES=$((FAILURES + 1))
   continue
   fi
   python -m py_compile "$script"
   echo "PASS: $script"
   done
   if (( FAILURES > 0 )); then
   echo
   echo "ERROR: $FAILURES scoring component(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: All scoring and master-table scripts passed syntax validation."

.. _15-32-record-scoring-script-checksums:

15.32 Record scoring-script checksums
-------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MANIFEST="results/environment/scoring_source.sha256"
   mkdir -p \
   "$(dirname "$MANIFEST")"
   sha256sum \
   pipeline/case_workflow/10b_calibrate_clinvar_ranking.py \
   pipeline/case_workflow/11_score_universal_evidence.py \
   pipeline/case_workflow/11b_score_universal_cnv.py \
   pipeline/case_workflow/12_score_cnv_candidates.py \
   pipeline/case_workflow/12_build_universal_master.py \
   pipeline/case_workflow/14_build_master_candidate_table.py \
   > "$MANIFEST"
   sha256sum \
   --check \
   "$MANIFEST"

These checksums make score changes traceable to source changes.

.. _15-33-common-scoring-and-ranking-failures:

15.33 Common scoring and ranking failures
-----------------------------------------

+---------------------------------------------------+----------------------------------+----------------------------------------+
| **Failure**                                       | **Likely cause**                 | **Required response**                  |
+===================================================+==================================+========================================+
| Score interpreted as probability                  | Misunderstanding of scale        | Describe it as project prioritisation  |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Missing evidence treated as benign                | Incorrect null handling          | Use explicit unavailable status        |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| ClinVar label used without review status          | Incomplete clinical calibration  | Include CLNREVSTAT                     |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| ClinVar condition unrelated to G2P disease        | Disease identity mismatch        | Preserve both and resolve carefully    |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Rare variant automatically scored as pathogenic   | Frequency overinterpretation     | Require additional evidence            |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| High-impact consequence dominates everything      | Functional over-weighting        | Check disease mechanism                |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| HPO missing treated as mismatch                   | Incomplete phenotype handling    | Mark phenotype not available           |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Single recessive allele receives complete support | Inheritance error                | Require biallelic evidence             |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Unphased pair treated as confirmed trans          | Phase error                      | Report possible only                   |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Homozygous variant duplicated into a pair         | Pair-generation error            | Treat as one homozygous candidate      |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| PGx match increases disease score                 | Branch contamination             | Separate PGx evidence                  |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Repeat expansion receives SNV score               | Routing failure                  | Exclude from ordinary ranking          |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| AnnotSV split rows treated as separate CNVs       | CNV grouping failure             | Group by source CNV                    |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Three CNV tools counted as independent proof      | Double-counting                  | Review overlapping evidence            |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Equal scores change order between runs            | Unstable tie handling            | Add deterministic secondary key        |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Rank starts at zero unexpectedly                  | Indexing error                   | Confirm intended rank convention       |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Candidate disappears from master table            | Join-key mismatch                | Compare stable candidate keys          |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Candidate duplicated in master table              | Many-to-many join                | Include disease or transcript identity |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Legacy result presented as current                | Audit category ignored           | Preserve CURRENT and LEGACY            |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Expected score edited after failure               | Invalid validation practice      | Investigate the actual change          |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Score changes after resource update               | Updated evidence                 | Rerun full regression and document     |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| Numerical value rounded inconsistently            | Formatting difference            | Preserve raw score and display score   |
+---------------------------------------------------+----------------------------------+----------------------------------------+
| No output interpreted as zero candidates          | Stage failure or disabled branch | Check explicit status file             |
+---------------------------------------------------+----------------------------------+----------------------------------------+

.. _15-34-scoring-stage-readiness-check:

15.34 Scoring-stage readiness check
-----------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   REQUIRED_FILES=(
   pipeline/case_workflow/10b_calibrate_clinvar_ranking.py
   pipeline/case_workflow/11_score_universal_evidence.py
   pipeline/case_workflow/11b_score_universal_cnv.py
   pipeline/case_workflow/12_score_cnv_candidates.py
   pipeline/case_workflow/12_build_universal_master.py
   pipeline/case_workflow/14_build_master_candidate_table.py
   validation/final_audit_20260727/canonical_cases.tsv
   validation/final_audit_20260727/canonical_final_outputs.sha256
   validation/final_audit_20260727/key_resources.sha256
   validation/final_audit_20260727/pipeline_source.sha256
   validation/final_audit_20260727/FINAL_VALIDATION_STATUS.md
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py
   )
   FAILURES=0
   for path in "${REQUIRED_FILES[@]}"; do
   if [[ -s "$path" ]]; then
   printf "PASS %s\n" "$path"
   else
   printf "FAIL %s\n" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo
   echo "ERROR: $FAILURES scoring or audit component(s) are missing."
   exit 1
   fi
   python -m py_compile \
   pipeline/case_workflow/10b_calibrate_clinvar_ranking.py \
   pipeline/case_workflow/11_score_universal_evidence.py \
   pipeline/case_workflow/11b_score_universal_cnv.py \
   pipeline/case_workflow/12_score_cnv_candidates.py \
   pipeline/case_workflow/12_build_universal_master.py \
   pipeline/case_workflow/14_build_master_candidate_table.py \
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py
   python \
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py
   echo
   echo "PASS: Universal scoring, ranking and audit components are ready."

.. _15-35-completion-criteria:

15.35 Completion criteria
-------------------------

The scoring and master-table stage is complete when:

✓ Every candidate has a stable identifier

✓ Small variants and CNVs use branch-appropriate scoring

✓ Repeat expansions are excluded from ordinary scoring

✓ Unsupported structural variants retain non-numeric statuses

✓ ClinPGx results remain separate from rare-disease scores

✓ Functional consequences are interpreted with disease mechanism

✓ ClinVar significance is calibrated by review status

✓ ClinVar condition relevance is retained

✓ Population frequency is interpreted cautiously

✓ Gene–disease confidence is retained

✓ Phenotype evidence distinguishes missing from incompatible

✓ Inheritance compatibility is included

✓ Compound-heterozygous phase status is preserved

✓ Homozygous variants are not double counted

✓ Related evidence is not treated as fully independent

✓ Conflicting evidence remains visible

✓ Missing evidence is not treated automatically as negative

✓ Candidate ordering is deterministic

✓ Tie behaviour follows the committed implementation

✓ AnnotSV full and split rows are grouped correctly

✓ Master rows can be traced to detailed evidence

✓ Resource and script provenance is recorded

✓ Canonical validation candidates retain their expected scores

✓ Patient 03 remains in the routed-repeat category

✓ Patients 01–12 pass the final audit

✓ Patient 13 remains documented as intentionally not executed

✓ The score is described as prioritisation, not probability

✓ Clinical review remains mandatory

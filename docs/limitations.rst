Limitations and clinical boundaries
===================================

The workflow was validated with controlled synthetic cases and has not been
shown to have clinical sensitivity, specificity or diagnostic yield in an
independent patient cohort.

Major limitations
-----------------

* It analyses variants already present in the submitted VCF.
* It does not independently perform read alignment or complete variant calling.
* It does not directly inspect BAM or CRAM evidence in the main workflow.
* CNVs and repeat expansions require specialist confirmation.
* Complex structural variants are preserved but not comprehensively interpreted.
* Family segregation and de novo status cannot be confirmed from a single sample.
* The local ClinPGx layer is not comprehensive star-allele calling.
* Universal scores are uncalibrated prioritisation values.

Clinical boundary
-----------------

The pipeline does not independently establish a diagnosis, recommend treatment,
calculate definitive recurrence risk or replace qualified genetics review.
Important findings require appropriate confirmation and clinical correlation.

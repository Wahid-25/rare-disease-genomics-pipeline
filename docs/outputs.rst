Outputs and reporting
=====================

A completed case may produce:

* intake and readiness reports
* harmonised and normalised VCFs
* routed small-variant and CNV files
* repeat-expansion and unsupported-SV reports
* VEP, SnpEff, ClinVar and SpliceAI outputs
* phenotype, inheritance and compound-heterozygous evidence tables
* ClinPGx match tables
* CNV tool outputs
* universal master candidate tables
* pipeline summaries, logs, manifests and checksums

Master candidate table
----------------------

The master table integrates the most important evidence for review. Candidate
scores are project-specific prioritisation values, not probabilities of
pathogenicity or diagnosis.

Branch status
-------------

An empty branch should have an explicit status such as ``not_applicable`` or
``no_records_detected``. Absence of applicable records is not the same as a
failed stage.

Reproducibility files
---------------------

Each case should record input checksums, pipeline source state, active resources,
container versions, run settings and output checksums.

Workflow architecture
=====================

The pipeline uses a modular, branch-aware architecture. A case is validated,
its context is resolved, and each variant class is routed to a suitable branch.

High-level flow
---------------

.. code-block:: text

   Case VCF + HPO + metadata
             |
             v
   Intake and structural preflight
             |
             v
   Sex, ploidy and case-context resolution
             |
             v
   Variant detection and routing
      |          |           |             |
      v          v           v             v
   SNV/indel   DEL/DUP     Repeat       Unsupported
      |          |        expansion        SV
      v          v           v             v
   Annotation   CNV tools  Dedicated      Status report
      \          /          report
       \        /
        v      v
   Phenotype + inheritance + disease evidence
             |
             v
   Candidate scoring and master table
             |
             v
   Logs, summaries, manifests and checksums

Small-variant branch
--------------------

The small-variant workflow performs normalisation, VEP annotation, SnpEff
annotation, ClinVar enrichment, SpliceAI prediction, gene–disease mapping,
phenotype scoring, inheritance evaluation, compound-heterozygous aggregation
and universal candidate scoring.

CNV branch
----------

DEL and DUP records are converted into branch-specific interval inputs and
processed with AnnotSV, ClassifyCNV and ISV-CNV. CNV evidence is integrated
with dosage sensitivity, gene–disease relationships and phenotype support.

Repeat-expansion route
----------------------

Repeat-expansion records are preserved and reported separately. They are not
forced into ordinary SNV scoring. A status such as ``detected_not_interpreted``
indicates that the record was recognised but not independently sized from reads.

ClinPGx layer
-------------

Pharmacogenomic matching is allele-aware and remains separate from the
rare-disease score. A shared rsID alone is insufficient; chromosome, position,
REF and ALT must match the curated reference.

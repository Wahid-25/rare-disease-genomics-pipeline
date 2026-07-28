Input requirements
==================

Primary case input
------------------

The principal workflow begins with a structurally valid patient-level VCF using
GRCh38 coordinates and the project's ``chr``-prefixed chromosome convention.

Recommended case information includes:

* non-identifying case ID
* selected sample name
* reported biological sex or explicit unknown status
* HPO phenotype file
* analysis mode: production or validation

VCF requirements
----------------

The VCF should contain:

* a valid ``##fileformat`` line
* a ``#CHROM`` header
* consistent columns
* usable REF and ALT alleles
* a patient sample and genotype fields when inheritance is assessed
* sufficient ``END`` and type information for CNVs
* complete symbolic-allele definitions where applicable

Genome build
------------

All coordinates must use GRCh38. Chromosome names alone do not establish the
build. Confirm the assembly from metadata, source documentation and REF-allele
compatibility.

HPO file
--------

A simple phenotype file contains one HPO identifier per line:

.. code-block:: text

   HP:0001250
   HP:0001263
   HP:0004322

Patient-to-HPO matching must use exact case identifiers.

Privacy
-------

Real patient VCFs, HPO files and outputs must remain local. Do not use names,
hospital IDs, dates of birth or other direct identifiers in repository paths.

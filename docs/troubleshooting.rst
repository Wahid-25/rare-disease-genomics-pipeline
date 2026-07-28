Troubleshooting
===============

Safe failure response
---------------------

When a run fails:

1. preserve logs and partial outputs;
2. identify the first failing stage;
3. classify the problem as input, environment, resource, tool or pipeline logic;
4. correct the universal cause;
5. run the relevant regression test;
6. rerun only after backing up the previous case directory;
7. compare old and new outputs;
8. run the complete validation suite.

Common problems
---------------

* **VCF parse failure:** inspect the header and the reported record.
* **REF mismatch:** verify the genome build and source alleles; do not swap blindly.
* **No ClinVar matches:** check exact allele, normalisation and chromosome naming.
* **VEP cache error:** verify software/cache release compatibility and bind paths.
* **SnpEff database error:** confirm the active database identifier and data directory.
* **CNV tool failure:** validate the four-column DEL/DUP interval input.
* **Wrong HPO file:** require exact case-identifier matching.
* **PGx mismatch:** require exact chromosome, position, REF and ALT.
* **Process killed:** check memory and reduce threads or Java memory cautiously.

Unsafe fixes
------------

Do not edit the original VCF, hide failed stages, introduce patient-specific
ranking rules or regenerate canonical checksums merely to remove a failure.

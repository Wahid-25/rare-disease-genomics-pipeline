Validation and audit
====================

The project uses layered validation:

1. Bash and Python syntax checks
2. VCF structural preflight
3. targeted regression tests
4. controlled synthetic case execution
5. canonical candidate and route comparison
6. source, resource and output checksum verification

Structural preflight
--------------------

Thirteen prepared synthetic VCFs passed structural preflight. The preflight
checks input readability, header structure, samples, variant representation and
routing compatibility.

Regression safeguards
---------------------

The committed tests cover:

* production and validation resource isolation
* exact allele-aware ClinPGx matching
* inheritance models
* sex and ploidy preflight
* compound-heterozygous phase logic
* exact HPO patient matching
* G2P disease-label precedence
* intake-report preservation

Final audit
-----------

Patients 01–12 were included in the final behavioural audit. All twelve met the
expected canonical candidate or routing conditions. Patient 03 validated the
dedicated repeat-expansion route. Patient 13 was intentionally not run through
the complete workflow.

Audit directory
---------------

The final audit is preserved under ``validation/final_audit_20260727/`` and
contains canonical case definitions, source checksums, key-resource checksums,
output checksums and the final audit script.

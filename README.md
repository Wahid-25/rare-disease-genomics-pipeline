# Rare Disease Genomics Pipeline

A reproducible GRCh38 workflow for rare-disease variant annotation,
gene-disease prioritisation, inheritance evaluation, phenotype scoring,
ClinPGx matching, CNV analysis and repeat-expansion routing.

## Main capabilities

- SNV and small-indel normalisation and annotation
- VEP, SnpEff, ClinVar, SpliceAI and ClinGen integration
- Gene2Phenotype-based disease mapping
- HPO-aware candidate ranking
- Autosomal, X-linked and mitochondrial inheritance evaluation
- Phase-aware compound-heterozygous assessment
- Allele-aware ClinPGx matching
- DEL/DUP CNV routing and scoring
- Detection and separate reporting of repeat expansions
- Production and validation resource modes

## Validation status

Patients 01-12 have canonical validated outcomes.

Patient 03 contains an HTT CAG repeat expansion. It was detected,
reported separately and excluded from ordinary small-variant ranking.

Patient 13 was prepared but intentionally not executed because of time
constraints.

## Data notice

All included patient VCFs are synthetic educational test data and must
not be interpreted as real clinical records.

## Local resources

Large reference genomes, annotation databases, container images,
sequencing reads and complete generated result directories are excluded
from Git. See the resource and container README files for details.

## Clinical notice

Pipeline outputs are candidate-prioritisation results. Manual molecular,
clinical, privacy and quality review remains required.

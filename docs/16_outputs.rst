.. _16-pipeline-outputs-result-directory-structure-and-interpretation-of-generated-f:

16. Pipeline Outputs, Result-Directory Structure and Interpretation of Generated Files
======================================================================================


The universal pipeline produces several layers of output rather than one single result file. Each layer has a different purpose:

Intermediate files:

Used by later pipeline stages and troubleshooting

Detailed annotation files:

Contain the complete evidence produced by individual tools

Integrated tables:

Combine evidence across tools and resources

Summary reports:

Present the most important case-level findings

Logs and manifests:

Record execution, software, resources and checksums

Validation outputs:

Confirm that the pipeline continues to produce expected results

The output directory must preserve the relationship between the original case, routed variant classes, individual annotation tools, integrated candidate tables and final reports.

A high candidate score or automated classification must always be interpreted together with the supporting detailed files.

.. _16-1-main-local-result-directories:

16.1 Main local result directories
----------------------------------

The principal local output locations are:

results/

validation/

The results/ directory contains generated case and tool outputs.

The validation/ directory contains:

-  controlled validation inputs;

-  regression-test materials;

-  expected outputs;

-  final audit files;

-  checksums;

-  validation summaries.

Large results and real case files remain local and are excluded from GitHub.

.. _16-2-inspect-the-result-directory-structure:

16.2 Inspect the result-directory structure
-------------------------------------------

From the project root, run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   if [[ ! -d results ]]; then
   echo "ERROR: results directory is missing."
   exit 1
   fi
   find results \
   -maxdepth 4 \
   -type d \
   | sort

List generated files:

.. code:: bash

   find results \
   -maxdepth 5 \
   -type f \
   -printf '%s\t%p\n' \
   | sort -k2,2

Display human-readable file sizes:

.. code:: bash

   find results \
   -maxdepth 5 \
   -type f \
   -print0 |
   while IFS= read -r -d '' file; do
   size="$(
   du -h "$file" |
   cut -f1
   )"
   printf '%-10s %s\n' \
   "$size" \
   "$file"
   done |
   sort -k2,2

This discovery approach is safer than assuming that every pipeline version generates identical filenames.

.. _16-3-conceptual-case-result-structure:

16.3 Conceptual case-result structure
-------------------------------------

A completed universal case may contain a structure similar to:

results/

└── cases/

└── <case_id>/

├── intake/

├── context/

├── routed/

│ ├── small_variants/

│ ├── cnv/

│ ├── repeat_expansions/

│ └── unsupported/

├── annotations/

│ ├── vep/

│ ├── snpeff/

│ ├── clinvar/

│ ├── spliceai/

│ └── gene_disease/

├── phenotype/

├── inheritance/

├── clinpgx/

├── cnv/

├── ranking/

├── reports/

├── logs/

└── manifests/

The exact names are controlled by the committed launchers and may differ slightly.

The important design principle is that:

-  

   .. container::

      Original intake

-  

   .. container::

      Routed records

-  

   .. container::

      Detailed annotations

-  

   .. container::

      Integrated scores

-  

   .. container::

      Reports

-  

   .. container::

      Logs

-  

   .. container::

      Manifests

-  

   .. container::

      remain distinguishable.

.. _16-4-original-intake-outputs:

16.4 Original intake outputs
----------------------------

The intake directory should preserve information about the submitted case before annotation begins.

Possible files include:

-  

   .. container::

      Original input path

-  

   .. container::

      Copied input path

-  

   .. container::

      Input checksum

-  

   .. container::

      Detected sample name

-  

   .. container::

      VCF version

-  

   .. container::

      Genome-build declaration

-  

   .. container::

      Chromosome convention

-  

   .. container::

      Reported sex

-  

   .. container::

      HPO file

-  

   .. container::

      Analysis mode

-  

   .. container::

      Warnings

-  

   .. container::

      Preparation actions

The intake report must remain available even after the input is harmonised, normalised or split.

The project verifies this behaviour through:

.. code:: bash

   pipeline/tests/11_test_intake_report_preservation.py

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   python \
   pipeline/tests/11_test_intake_report_preservation.py
   echo "PASS: Intake-report preservation test completed."

.. _16-5-case-context-output:

16.5 Case-context output
------------------------

The case-context output records the resolved values used throughout the analysis.

It may contain:

-  

   .. container::

      case_id

-  

   .. container::

      sample_id

-  

   .. container::

      input_vcf

-  

   .. container::

      reported_sex

-  

   .. container::

      resolved_sex

-  

   .. container::

      hpo_file

-  

   .. container::

      genome_build

-  

   .. container::

      analysis_mode

-  

   .. container::

      resource_mode

-  

   .. container::

      result_directory

-  

   .. container::

      execution_timestamp

This file is important because every later stage should use the same resolved context.

A result should not be interpreted without confirming:

-  

   .. container::

      Correct case

-  

   .. container::

      Correct input

-  

   .. container::

      Correct HPO file

-  

   .. container::

      Correct sex metadata

-  

   .. container::

      Correct production or validation mode

.. _16-6-routed-output-files:

16.6 Routed output files
------------------------

The routing stage creates separate files or reports for different variant classes.

Typical routed categories are:

-  

   .. container::

      small variants

-  

   .. container::

      copy-number variants

-  

   .. container::

      repeat expansions

-  

   .. container::

      unsupported structural variants

A routed output may be empty when no records of that type were present.

An empty branch should contain an explicit status such as:

-  

   .. container::

      no_records_detected

-  

   .. container::

      not_applicable

-  

   .. container::

      stage_disabled

rather than simply having no file.

.. _16-6-1-small-variant-routed-output:

16.6.1 Small-variant routed output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file should contain ordinary:

-  

   .. container::

      SNVs

-  

   .. container::

      short insertions

-  

   .. container::

      short deletions

It should not contain:

-  

   .. container::

      <DEL>

-  

   .. container::

      <DUP>

-  

   .. container::

      repeat-expansion symbols

-  

   .. container::

      breakend notation

other symbolic structural alleles

Check:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SMALL_VCF="path/to/routed.small_variants.vcf.gz"
   if [[ ! -s "$SMALL_VCF" ]]; then
   echo "ERROR: Routed small-variant VCF is missing."
   exit 1
   fi
   SYMBOLIC="$(
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\n' \
   "$SMALL_VCF" |
   grep -E '<[^>]+>|\[|\]' \
   || true
   )"
   if [[ -n "$SYMBOLIC" ]]; then
   echo "ERROR: Structural alleles remain in the small-variant route:"
   echo "$SYMBOLIC"
   exit 1
   fi
   echo "PASS: Routed small-variant file contains no symbolic alleles."

Replace the placeholder with the actual generated path.

.. _16-6-2-cnv-routed-output:

16.6.2 CNV routed output
~~~~~~~~~~~~~~~~~~~~~~~~

A CNV route normally contains:

-  

   .. container::

      DEL

-  

   .. container::

      DUP

-  

   .. container::

      and preserves:

-  

   .. container::

      chromosome

-  

   .. container::

      start

-  

   .. container::

      end

-  

   .. container::

      variant type

-  

   .. container::

      source identifier

-  

   .. container::

      genotype

copy number where available

The four-column tool input usually resembles:

chr1 100000 500000 DEL

chr7 5500000 6200000 DUP

The accompanying source manifest should retain the original VCF coordinates and identifiers.

.. _16-6-3-repeat-routed-output:

16.6.3 Repeat routed output
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Repeat-expansion records should appear in a dedicated report with a status such as:

detected_not_interpreted

The repeat report should preserve, where available:

-  

   .. container::

      repeat locus

-  

   .. container::

      gene

-  

   .. container::

      repeat motif

-  

   .. container::

      repeat count

-  

   .. container::

      confidence interval

-  

   .. container::

      genotype

-  

   .. container::

      threshold

-  

   .. container::

      threshold source

-  

   .. container::

      specialist follow-up requirement

It must not be interpreted as an ordinary SNV candidate table.

.. _16-6-4-unsupported-variant-output:

16.6.4 Unsupported-variant output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The unsupported report should retain records such as:

-  

   .. container::

      inversions

-  

   .. container::

      breakends

-  

   .. container::

      translocations

-  

   .. container::

      complex insertions

-  

   .. container::

      other complex structural variants

The report should explain why the record was not processed by the ordinary small-variant, CNV or repeat branch.

Unsupported means that the current workflow lacks a complete interpretation method. It does not mean benign, invalid or irrelevant.

.. _16-7-normalised-small-variant-vcf:

16.7 Normalised small-variant VCF
---------------------------------

The normalised VCF is the principal prepared input for small-variant annotation.

It should have:

-  

   .. container::

      GRCh38 coordinates

-  

   .. container::

      chr-prefixed chromosomes

-  

   .. container::

      REF alleles matching the reference

-  

   .. container::

      left-aligned indels

-  

   .. container::

      decomposed multiallelic records

-  

   .. container::

      bgzip compression

-  

   .. container::

      tabix index

-  

   .. container::

      A typical filename may include:

-  

   .. container::

      normalized.vcf.gz

Verify any normalised VCF:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   NORMALISED_VCF="path/to/normalized.vcf.gz"
   if [[ ! -s "$NORMALISED_VCF" ]]; then
   echo "ERROR: Normalised VCF is missing."
   exit 1
   fi
   bgzip --test "$NORMALISED_VCF"
   bcftools view \
   --header-only \
   "$NORMALISED_VCF" \
   >/dev/null
   bcftools index \
   --stats \
   "$NORMALISED_VCF"
   echo "PASS: Normalised VCF is readable and indexed."

.. _16-8-vep-output:

16.8 VEP output
---------------

A VEP VCF contains transcript-level consequence annotations in:

-  

   .. container::

      INFO/CSQ

-  

   .. container::

      Important evidence includes:

-  

   .. container::

      Gene symbol

-  

   .. container::

      Ensembl gene ID

-  

   .. container::

      Transcript

-  

   .. container::

      Consequence

-  

   .. container::

      Impact

-  

   .. container::

      HGVSc

-  

   .. container::

      HGVSp

-  

   .. container::

      Exon

-  

   .. container::

      Intron

-  

   .. container::

      Protein position

-  

   .. container::

      Amino-acid change

-  

   .. container::

      Canonical transcript

-  

   .. container::

      MANE Select transcript

-  

   .. container::

      Existing variant identifier

-  

   .. container::

      Cached gnomAD exome frequency

The CSQ field is pipe-delimited. Its subfield order must be read from the VCF header.

Inspect:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VEP_VCF="path/to/vep.vcf.gz"
   if [[ ! -s "$VEP_VCF" ]]; then
   echo "ERROR: VEP VCF is missing."
   exit 1
   fi
   bcftools view \
   --header-only \
   "$VEP_VCF" |
   grep '^##INFO=<ID=CSQ,'
   echo
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\t%INFO/CSQ\n' \
   "$VEP_VCF" |
   head -n 5

Multiple CSQ entries for one record normally represent several transcripts, not several genomic variants.

.. _16-9-extracted-vep-table:

16.9 Extracted VEP table
------------------------

The project converts VEP’s structured CSQ annotations into a tabular format through:

pipeline/case_workflow/03_extract_vep_table.py

This table is easier to use for:

-  gene–disease mapping;

-  transcript selection;

-  phenotype integration;

-  inheritance analysis;

-  candidate scoring.

A single variant may appear in several rows when it has several transcript consequences.

The table should preserve a stable variant key so that transcript rows can be grouped back to the same genomic record.

.. _16-10-snpeff-output:

16.10 SnpEff output
-------------------

SnpEff writes its main consequence annotations to:

-  

   .. container::

      INFO/ANN

-  

   .. container::

      Important fields may include:

-  

   .. container::

      Allele

-  

   .. container::

      Effect

-  

   .. container::

      Impact

-  

   .. container::

      Gene name

-  

   .. container::

      Gene ID

-  

   .. container::

      Feature type

-  

   .. container::

      Transcript

-  

   .. container::

      Biotype

-  

   .. container::

      Rank

-  

   .. container::

      HGVS coding notation

-  

   .. container::

      HGVS protein notation

-  

   .. container::

      Coding position

-  

   .. container::

      Protein position

-  

   .. container::

      Distance

-  

   .. container::

      Warnings

Inspect:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SNPEFF_VCF="path/to/snpeff.vcf.gz"
   if [[ ! -s "$SNPEFF_VCF" ]]; then
   echo "ERROR: SnpEff VCF is missing."
   exit 1
   fi
   bcftools view \
   --header-only \
   "$SNPEFF_VCF" |
   grep '^##INFO=<ID=ANN,'
   echo
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\t%INFO/ANN\n' \
   "$SNPEFF_VCF" |
   head -n 5

A VEP and SnpEff disagreement should be reviewed using transcript and database versions rather than treated automatically as a pipeline failure.

.. _16-11-clinvar-integrated-output:

16.11 ClinVar-integrated output
-------------------------------

The ClinVar output should retain:

-  

   .. container::

      CLNSIG

-  

   .. container::

      CLNDN

-  

   .. container::

      CLNREVSTAT

where matches exist.

These fields mean:

+-----------------------+----------------------------------------------+
| **Field**             | **Interpretation**                           |
+=======================+==============================================+
| CLNSIG                | ClinVar clinical significance                |
+-----------------------+----------------------------------------------+
| CLNDN                 | Condition names                              |
+-----------------------+----------------------------------------------+
| CLNREVSTAT            | Review status                                |
+-----------------------+----------------------------------------------+

Inspect:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CLINVAR_VCF="path/to/clinvar_annotated.vcf.gz"
   if [[ ! -s "$CLINVAR_VCF" ]]; then
   echo "ERROR: ClinVar-integrated VCF is missing."
   exit 1
   fi
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\t%CLNSIG\t%CLNDN\t%CLNREVSTAT\n' \
   "$CLINVAR_VCF" |
   head -n 20

A dot . means that no value was added for that field.

It does not automatically mean that the variant is benign.

.. _16-12-spliceai-output:

16.12 SpliceAI output
---------------------

SpliceAI writes its predictions to:

.. code:: bash

   INFO/SpliceAI

A prediction includes:

-  

   .. container::

      alternate allele

-  

   .. container::

      gene

-  

   .. container::

      acceptor-gain score

-  

   .. container::

      acceptor-loss score

-  

   .. container::

      donor-gain score

-  

   .. container::

      donor-loss score

corresponding relative positions

Inspect:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SPLICEAI_VCF="path/to/spliceai.vcf.gz"
   if [[ ! -s "$SPLICEAI_VCF" ]]; then
   echo "ERROR: SpliceAI VCF is missing."
   exit 1
   fi
   bcftools view \
   --header-only \
   "$SPLICEAI_VCF" |
   grep '^##INFO=<ID=SpliceAI,'
   echo
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\t%INFO/SpliceAI\n' \
   "$SPLICEAI_VCF" |
   head -n 20

A missing prediction is not automatically an analytical failure. Some variants fall outside SpliceAI’s supported or annotated regions.

.. _16-13-merged-small-variant-annotation-table:

16.13 Merged small-variant annotation table
-------------------------------------------

The merge stage combines evidence from:

-  

   .. container::

      VEP

-  

   .. container::

      SnpEff

-  

   .. container::

      ClinVar

-  

   .. container::

      SpliceAI

The project script is:

.. code:: bash

   pipeline/case_workflow/09_merge_snpeff_spliceai.py

The merged table should preserve:

-  

   .. container::

      stable variant key

-  

   .. container::

      original record identifier

-  

   .. container::

      gene

-  

   .. container::

      transcript

-  

   .. container::

      functional consequence

-  

   .. container::

      clinical evidence

-  

   .. container::

      splice evidence

-  

   .. container::

      population frequency

-  

   .. container::

      Later stages add:

-  

   .. container::

      gene–disease mapping

-  

   .. container::

      phenotype score

-  

   .. container::

      inheritance evidence

-  

   .. container::

      compound-heterozygous status

-  

   .. container::

      universal score

.. _16-14-gene-disease-mapping-output:

16.14 Gene–disease mapping output
---------------------------------

The G2P mapping output should contain, where available:

-  

   .. container::

      gene

-  

   .. container::

      disease name

-  

   .. container::

      disease identifier

-  

   .. container::

      G2P confidence

-  

   .. container::

      allelic requirement

-  

   .. container::

      molecular mechanism

-  

   .. container::

      expected consequence

-  

   .. container::

      resource mode

A gene may appear in several rows when it is associated with several disease models.

This is not necessarily duplication. Each disease model may have a different:

-  

   .. container::

      inheritance

-  

   .. container::

      mechanism

-  

   .. container::

      phenotype

-  

   .. container::

      variant requirement

-  

   .. container::

      The active resource mode must remain visible:

-  

   .. container::

      production

-  

   .. container::

      validation

.. _16-15-phenotype-output:

16.15 Phenotype output
----------------------

The phenotype stage may produce:

-  

   .. container::

      patient HPO terms

-  

   .. container::

      matched disease HPO terms

-  

   .. container::

      exact matches

-  

   .. container::

      semantic matches

-  

   .. container::

      direct phenotype score

-  

   .. container::

      semantic phenotype score

-  

   .. container::

      phenotype evidence status

-  

   .. container::

      The output should distinguish:

-  

   .. container::

      phenotype_not_available

from:

phenotype_evaluated_but_weak

A missing HPO file must not produce a false phenotype mismatch.

.. _16-16-disease-resolution-output:

16.16 Disease-resolution output
-------------------------------

The disease-resolution table combines:

-  

   .. container::

      G2P disease label

-  

   .. container::

      ClinVar condition label

-  

   .. container::

      MONDO identifier

-  

   .. container::

      MONDO preferred name

-  

   .. container::

      original source labels

-  

   .. container::

      resolved disease identity

-  

   .. container::

      resolution source

-  

   .. container::

      mapping status

The original labels should remain available for provenance.

The resolved disease name is intended to prevent the same condition from appearing several times only because different resources use different terminology.

.. _16-17-inheritance-output:

16.17 Inheritance output
------------------------

The inheritance stage may produce fields such as:

-  

   .. container::

      genotype

-  

   .. container::

      zygosity

-  

   .. container::

      reported sex

-  

   .. container::

      resolved sex

-  

   .. container::

      ploidy

-  

   .. container::

      allelic requirement

-  

   .. container::

      inheritance compatibility

-  

   .. container::

      inheritance warning

Important statuses include conceptual categories such as:

-  

   .. container::

      compatible

-  

   .. container::

      partially_compatible

-  

   .. container::

      incompatible

-  

   .. container::

      not_assessed

-  

   .. container::

      uncertain

The exact labels must follow the generated file.

A single heterozygous variant in a recessive model should not be interpreted as complete biallelic evidence.

.. _16-18-compound-heterozygous-output:

16.18 Compound-heterozygous output
----------------------------------

The compound-heterozygous table should preserve:

-  

   .. container::

      gene

-  

   .. container::

      variant 1

-  

   .. container::

      variant 2

-  

   .. container::

      genotype 1

-  

   .. container::

      genotype 2

-  

   .. container::

      phase status

-  

   .. container::

      phase set

-  

   .. container::

      pair classification

-  

   .. container::

      pair-level evidence

-  

   .. container::

      Possible interpretations include:

-  

   .. container::

      phased trans

-  

   .. container::

      cis

-  

   .. container::

      possible unphased pair

-  

   .. container::

      phase unresolved

-  

   .. container::

      not a qualifying pair

A homozygous variant must not appear as two duplicated records forming an artificial pair.

.. _16-19-clinpgx-output:

16.19 ClinPGx output
--------------------

The local ClinPGx table may include:

-  

   .. container::

      gene

-  

   .. container::

      chromosome

-  

   .. container::

      position

-  

   .. container::

      REF

-  

   .. container::

      ALT

-  

   .. container::

      rsID

-  

   .. container::

      genotype

-  

   .. container::

      exact match status

-  

   .. container::

      star allele

-  

   .. container::

      diplotype

-  

   .. container::

      functional phenotype

-  

   .. container::

      drug

-  

   .. container::

      interpretation

-  

   .. container::

      warning

-  

   .. container::

      The output should distinguish:

-  

   .. container::

      exact allele match

-  

   .. container::

      allele mismatch

-  

   .. container::

      rsID-only match

-  

   .. container::

      no reference match

-  

   .. container::

      not assessed

-  

   .. container::

      stage disabled

A ClinPGx finding should not alter the rare-disease candidate score.

Examples from the controlled validation suite include:

TPMT rs1142345

\*1/\*3C

Intermediate metaboliser

CYP2D6 rs3892097

\*1/\*4

Intermediate metaboliser

DPYD rs3918290

\*1/\*2A

Intermediate metaboliser

These are project-validation interpretations based on the curated local reference.

.. _16-20-annotsv-output:

16.20 AnnotSV output
--------------------

A typical AnnotSV output filename may resemble:

sample.AnnotSV.tsv

The output can contain both:

-  

   .. container::

      full

-  

   .. container::

      split

-  

   .. container::

      annotation rows.

-  

   .. container::

      Important fields may include:

-  

   .. container::

      AnnotSV_ID

-  

   .. container::

      SV chromosome

-  

   .. container::

      SV start

-  

   .. container::

      SV end

-  

   .. container::

      SV length

-  

   .. container::

      SV type

-  

   .. container::

      annotation mode

-  

   .. container::

      cytoband

-  

   .. container::

      gene

-  

   .. container::

      transcript

-  

   .. container::

      CDS overlap

-  

   .. container::

      haploinsufficiency evidence

-  

   .. container::

      triplosensitivity evidence

-  

   .. container::

      ranking score

-  

   .. container::

      ranking criteria

-  

   .. container::

      ACMG class

The same CNV may appear in several rows because each overlapping gene or transcript can generate a split row.

Do not count these rows as separate CNVs.

.. _16-20-1-inspect-an-annotsv-file:

16.20.1 Inspect an AnnotSV file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   ANNOTSV_FILE="path/to/sample.AnnotSV.tsv"
   if [[ ! -s "$ANNOTSV_FILE" ]]; then
   echo "ERROR: AnnotSV output is missing."
   exit 1
   fi
   echo "Rows:"

wc -l "$ANNOTSV_FILE"

.. code:: bash

   echo
   echo "Columns:"
   python3 - "$ANNOTSV_FILE" <<'PY'
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
   for index, column in enumerate(header, start=1):
   print(f"{index:02d}. {column}")
   PY

.. _16-21-classifycnv-output:

16.21 ClassifyCNV output
------------------------

A typical output is:

Scoresheet.txt

or a preserved file such as:

sample.ClassifyCNV.Scoresheet.txt

It contains:

-  

   .. container::

      CNV interval

-  

   .. container::

      DEL or DUP

-  

   .. container::

      total evidence score

-  

   .. container::

      classification

-  

   .. container::

      dosage-sensitive genes

-  

   .. container::

      protein-coding genes

-  

   .. container::

      evidence-category contributions

The classification should be reviewed together with:

-  the exact interval;

-  gene content;

-  phenotype;

-  inheritance;

-  breakpoint precision;

-  supporting evidence.

A ClassifyCNV result does not automatically establish that the CNV explains the patient’s phenotype.

.. _16-22-isv-cnv-output:

16.22 ISV-CNV output
--------------------

A typical output filename may resemble:

-  

   .. container::

      sample.ISV_CNV.tsv

-  

   .. container::

      The output can contain:

-  

   .. container::

      predicted class

-  

   .. container::

      prediction probability

-  

   .. container::

      feature values

-  

   .. container::

      SHAP values

The probability represents the model’s output. It is not the probability that the patient has a disease.

SHAP values explain which model features influenced the prediction. They do not independently prove a biological mechanism.

.. _16-23-combined-cnv-summary:

16.23 Combined CNV summary
--------------------------

The project may generate a file similar to:

-  

   .. container::

      sample.CNV_combined_summary.tsv

..

   This file integrates:

-  

   .. container::

      source CNV interval

-  

   .. container::

      AnnotSV evidence

-  

   .. container::

      ClassifyCNV evidence

-  

   .. container::

      ISV-CNV evidence

-  

   .. container::

      ClinGen dosage evidence

-  

   .. container::

      gene–disease relationships

-  

   .. container::

      phenotype evidence

-  

   .. container::

      ClinPGx overlap

-  

   .. container::

      universal CNV score

A combined summary is easier to review than three separate tool outputs, but the original detailed outputs must remain available.

The combined score must not treat AnnotSV, ClassifyCNV and ISV-CNV as fully independent evidence sources.

.. _16-24-repeat-expansion-report:

16.24 Repeat-expansion report
-----------------------------

The repeat-expansion output should be interpreted as a routing and preservation report.

For the controlled Patient 03 case, the canonical result includes:

Gene: HTT

Variant: chr4:3074877:N><CAG_EXPANSION>

Reported count: 45

Controlled threshold: 40

Genotype: 0/1

Status: detected_not_interpreted

This means that the pipeline:

-  detected the repeat record;

-  preserved its information;

-  excluded it from ordinary ranking;

-  required specialist repeat analysis.

It does not mean that the pipeline independently confirmed the repeat count from sequencing reads.

.. _16-25-universal-evidence-table:

16.25 Universal evidence table
------------------------------

The universal evidence table contains the detailed evidence used before final rank assignment.

It may include:

-  

   .. container::

      candidate key

-  

   .. container::

      gene

-  

   .. container::

      disease

-  

   .. container::

      functional consequence

-  

   .. container::

      ClinVar fields

-  

   .. container::

      population frequency

-  

   .. container::

      SpliceAI score

-  

   .. container::

      G2P evidence

-  

   .. container::

      phenotype score

-  

   .. container::

      inheritance score

-  

   .. container::

      compound-heterozygous status

-  

   .. container::

      universal score

-  

   .. container::

      warnings

This file is generally more detailed than the final master table.

It should be used when investigating:

Why did this candidate receive this score?

.. _16-26-universal-master-table:

16.26 Universal master table
----------------------------

The universal master table brings together the principal output branches.

It may contain rows representing:

-  

   .. container::

      small variants

-  

   .. container::

      CNVs

-  

   .. container::

      repeat-expansion route statuses

-  

   .. container::

      unsupported structural variants

-  

   .. container::

      ClinPGx findings

Each row should preserve an analysis-branch field.

A repeat record and an SNV may both appear in the master output, but they should not be interpreted as though they received the same scoring method.

.. _16-27-final-master-candidate-table:

16.27 Final master candidate table
----------------------------------

The final master candidate table is the main reviewer-oriented output.

It should contain the most important evidence required to prioritise and review candidates, such as:

-  

   .. container::

      candidate rank

-  

   .. container::

      candidate key

-  

   .. container::

      variant branch

-  

   .. container::

      gene

-  

   .. container::

      resolved disease

-  

   .. container::

      genotype

-  

   .. container::

      consequence

-  

   .. container::

      ClinVar significance

-  

   .. container::

      ClinVar review status

-  

   .. container::

      population frequency

-  

   .. container::

      phenotype score

-  

   .. container::

      inheritance status

-  

   .. container::

      compound-heterozygous status

-  

   .. container::

      CNV evidence where applicable

-  

   .. container::

      universal score

-  

   .. container::

      warning

-  

   .. container::

      The table should remain traceable to:

-  

   .. container::

      Original VCF

-  

   .. container::

      Detailed annotation files

-  

   .. container::

      Case manifest

-  

   .. container::

      Tool logs

-  

   .. container::

      Resource checksums

.. _16-27-1-inspect-a-master-table:

16.27.1 Inspect a master table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MASTER_TABLE="path/to/master_candidate_table.tsv"
   if [[ ! -s "$MASTER_TABLE" ]]; then
   echo "ERROR: Master table is missing."
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
   rows = list(reader)
   bad_rows = [
   line_number
   for line_number, row in enumerate(
   rows,
   start=2,
   )
   if len(row) != len(header)
   ]
   print(f"File: {path}")
   print(f"Columns: {len(header)}")
   print(f"Rows: {len(rows)}")
   print()
   for index, column in enumerate(header, start=1):
   print(f"{index:02d}. {column}")
   if bad_rows:
   raise SystemExit(
   "ERROR: Inconsistent row width at lines: "
   + ", ".join(map(str, bad_rows))
   )
   print()
   print("PASS: Master-table structure is consistent.")
   PY

.. _16-28-candidate-rank:

16.28 Candidate rank
--------------------

Candidate rank indicates the order in which candidates should be reviewed.

Normally:

Rank 1 = highest-priority scored candidate

Rank does not mean:

confirmed diagnosis

A lower-ranked candidate may still be important when:

-  the phenotype is incomplete;

-  the inheritance model is uncertain;

-  the candidate is novel;

-  the disease resource is incomplete;

-  the top-ranked candidate is incompatible with later clinical evidence.

Repeat and unsupported records may have no numeric rank because they follow different analytical routes.

.. _16-29-universal-score:

16.29 Universal score
---------------------

The universal score is a project-specific prioritisation score.

It combines available evidence but is not:

-  

   .. container::

      a probability

-  

   .. container::

      an ACMG classification

-  

   .. container::

      a diagnostic confidence percentage

-  

   .. container::

      a treatment recommendation

-  

   .. container::

      The score should be interpreted together with:

-  

   .. container::

      candidate rank

-  

   .. container::

      score components

-  

   .. container::

      warnings

-  

   .. container::

      resource mode

-  

   .. container::

      branch

-  

   .. container::

      detailed evidence

The validated canonical scores are regression targets for the current project implementation.

.. _16-30-human-readable-report:

16.30 Human-readable report
---------------------------

A human-readable case report should summarise:

-  

   .. container::

      Case identifier

-  

   .. container::

      Input and genome build

-  

   .. container::

      Reported phenotype

-  

   .. container::

      Reported and resolved sex

-  

   .. container::

      Analysis mode

-  

   .. container::

      Variant classes detected

-  

   .. container::

      Top small-variant candidates

-  

   .. container::

      Top CNV candidates

-  

   .. container::

      Repeat-expansion findings

-  

   .. container::

      Unsupported variants

-  

   .. container::

      ClinPGx findings

-  

   .. container::

      Limitations

-  

   .. container::

      Required follow-up

The report should avoid presenting an automated candidate as a confirmed diagnosis.

Recommended language includes:

-  

   .. container::

      The pipeline prioritised this candidate because of

.. container::

   its functional consequence, gene–disease association,

.. container::

   phenotype compatibility and inheritance evidence.

-  

   .. container::

      Clinical confirmation and specialist interpretation

.. container::

   remain required.

.. _16-31-logs:

16.31 Logs
----------

Each major stage should have a corresponding log.

Examples include:

-  

   .. container::

      normalisation log

-  

   .. container::

      VEP log

-  

   .. container::

      SnpEff log

-  

   .. container::

      ClinVar log

-  

   .. container::

      SpliceAI log

-  

   .. container::

      G2P mapping log

-  

   .. container::

      phenotype log

-  

   .. container::

      inheritance log

-  

   .. container::

      AnnotSV log

-  

   .. container::

      ClassifyCNV log

-  

   .. container::

      ISV-CNV log

-  

   .. container::

      scoring log

-  

   .. container::

      report-generation log

Logs are needed to determine:

-  

   .. container::

      Which stage ran?

-  

   .. container::

      Which command failed?

-  

   .. container::

      Which resources were used?

-  

   .. container::

      Were warnings produced?

-  

   .. container::

      Was the output complete?

.. _16-31-1-search-case-logs-for-errors:

16.31.1 Search case logs for errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_LOG_DIR="path/to/case/logs"
   if [[ ! -d "$CASE_LOG_DIR" ]]; then
   echo "ERROR: Case log directory is missing."
   exit 1
   fi
   ERROR_MATCHES="$(
   grep -RInE \
   --include='*.log' \
   --include='*.txt' \
   '(^|[^A-Za-z])(ERROR|FATAL|Traceback|Exception|command not found|No such file)([^A-Za-z]|$)' \
   "$CASE_LOG_DIR" \
   || true
   )"
   if [[ -n "$ERROR_MATCHES" ]]; then
   echo "Potential errors detected:"
   echo "$ERROR_MATCHES"
   else
   echo "No obvious fatal error strings were found."
   fi

This search is only a screening method. Some tools write the word “error” in harmless documentation or warning messages, while some failures may use different wording.

.. _16-31-2-search-logs-for-warnings:

16.31.2 Search logs for warnings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   WARNING_MATCHES="$(
   grep -RInE \
   --include='*.log' \
   --include='*.txt' \
   '(^|[^A-Za-z])(WARNING|WARN)([^A-Za-z]|$)' \
   "$CASE_LOG_DIR" \
   || true
   )"
   if [[ -n "$WARNING_MATCHES" ]]; then
   echo "Warnings detected:"
   echo "$WARNING_MATCHES"
   else
   echo "No obvious warning strings were found."
   fi

Warnings should be reviewed even when the pipeline exits successfully.

.. _16-32-reproducibility-manifest:

16.32 Reproducibility manifest
------------------------------

The project script is:

.. code:: bash

   pipeline/case_workflow/00c_build_reproducibility_manifest.py

The manifest should record:

-  

   .. container::

      case identifier

-  

   .. container::

      input paths

-  

   .. container::

      input checksums

-  

   .. container::

      HPO file and checksum

-  

   .. container::

      reported sex

-  

   .. container::

      resolved sex

-  

   .. container::

      genome build

-  

   .. container::

      analysis mode

-  

   .. container::

      resource mode

-  

   .. container::

      pipeline source checksum

-  

   .. container::

      tool versions

-  

   .. container::

      container checksums

-  

   .. container::

      resource versions

-  

   .. container::

      resource checksums

-  

   .. container::

      execution timestamp

-  

   .. container::

      output paths

-  

   .. container::

      output checksums

-  

   .. container::

      completion status

The manifest allows a result to be recreated and audited.

.. _16-32-1-validate-a-manifest-structurally:

16.32.1 Validate a manifest structurally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MANIFEST="path/to/reproducibility_manifest.tsv"
   if [[ ! -s "$MANIFEST" ]]; then
   echo "ERROR: Reproducibility manifest is missing."
   exit 1
   fi
   python3 - "$MANIFEST" <<'PY'
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
   rows = list(reader)
   if not rows:
   raise SystemExit("ERROR: Manifest is empty.")
   width = len(rows[0])
   bad_lines = [
   index
   for index, row in enumerate(rows, start=1)
   if len(row) != width
   ]
   if bad_lines:
   raise SystemExit(
   "ERROR: Inconsistent manifest rows at lines: "
   + ", ".join(map(str, bad_lines))
   )
   print(f"PASS: {len(rows)} manifest row(s) read.")
   print(f"Columns per row: {width}")
   PY

.. _16-33-output-checksums:

16.33 Output checksums
----------------------

Final and important intermediate outputs should be checksummed.

For one case:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_RESULTS="path/to/case/results"
   CHECKSUM_FILE="$CASE_RESULTS/manifests/generated_outputs.sha256"
   mkdir -p \
   "$(dirname "$CHECKSUM_FILE")"
   find "$CASE_RESULTS" \
   -type f \
   ! -path "$CHECKSUM_FILE" \
   ! -name '*.tmp' \
   ! -name '*.lock' \
   -print0 |
   sort -z |
   xargs -0 sha256sum \
   > "$CHECKSUM_FILE"

Verify:

.. code:: bash

   sha256sum \
   --check \
   "$CHECKSUM_FILE"

The checksum manifest should not include itself.

.. _16-34-output-status-categories:

16.34 Output status categories
------------------------------

A generated output should have a clear state.

Recommended conceptual categories are:

-  

   .. container::

      completed

-  

   .. container::

      completed_with_warnings

-  

   .. container::

      completed_with_zero_matches

-  

   .. container::

      not_applicable

-  

   .. container::

      disabled

-  

   .. container::

      detected_not_interpreted

-  

   .. container::

      unsupported

-  

   .. container::

      failed

-  

   .. container::

      not_run

These states must remain distinct.

Examples:

completed_with_zero_matches:

The stage ran successfully but found no records.

disabled:

The stage was intentionally turned off.

failed:

The stage attempted to run but did not complete.

not_run:

The stage was never executed.

not_applicable:

The case contained no suitable input for that branch.

.. _16-35-current-legacy-and-routed-repeat-outputs:

16.35 Current, legacy and routed-repeat outputs
-----------------------------------------------

The final audit recognises:

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

The canonical output was produced through the current universal workflow.

**LEGACY**

The accepted output came from an earlier compatible workflow and remains the canonical validation result.

**ROUTED_REPEAT**

The case was processed through the repeat-expansion route rather than ordinary candidate ranking.

These labels describe output provenance. They are not clinical classifications.

.. _16-36-final-validation-audit-directory:

16.36 Final validation-audit directory
--------------------------------------

The final audit is stored under:

.. code:: bash

   validation/final_audit_20260727/

Important files are:

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

.. _16-36-1-canonical-cases-tsv:

16.36.1 canonical_cases.tsv
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This table defines:

-  canonical case identifier;

-  canonical output category;

-  expected principal candidate;

-  expected gene;

-  expected score or route;

-  audit status.

Inspect:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   column \
   --separator $'\t' \
   --table \
   validation/final_audit_20260727/canonical_cases.tsv

.. _16-36-2-canonical-final-outputs-sha256:

16.36.2 canonical_final_outputs.sha256
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file verifies that the accepted final outputs remain unchanged.

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sha256sum \
   --check \
   validation/final_audit_20260727/canonical_final_outputs.sha256

.. _16-36-3-key-resources-sha256:

16.36.3 key_resources.sha256
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file verifies important compact resources used by the validated project.

Run:

.. code:: bash

   sha256sum \
   --check \
   validation/final_audit_20260727/key_resources.sha256

Large local resources may be represented through separate local checksums rather than being stored in GitHub.

.. _16-36-4-pipeline-source-sha256:

16.36.4 pipeline_source.sha256
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file verifies the source files responsible for the validated result.

Run:

.. code:: bash

   sha256sum \
   --check \
   validation/final_audit_20260727/pipeline_source.sha256

A failure means that at least one recorded source file has changed and the previous validation may no longer apply exactly.

.. _16-36-5-final-validation-status-md:

16.36.5 FINAL_VALIDATION_STATUS.md
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file provides the human-readable validation summary.

Inspect:

.. code:: bash

   cat \
   validation/final_audit_20260727/FINAL_VALIDATION_STATUS.md

The validated audit recorded:

-  

   .. container::

      12 audited cases

-  

   .. container::

      12 passed cases

   -  

      .. container::

         failed cases

.. _16-37-run-the-final-audit:

16.37 Run the final audit
-------------------------

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

A successful Python exit status is required.

Do not update canonical expectations merely to make a changed result pass. Any difference must be investigated.

.. _16-38-interpret-final-validation-results:

16.38 Interpret final validation results
----------------------------------------

The canonical audit includes:

+-------------+---------------------+-----------------------------------------+
| **Patient** | **Output category** | **Main result**                         |
+=============+=====================+=========================================+
| 01          | Legacy              | CFTR candidate                          |
+-------------+---------------------+-----------------------------------------+
| 02          | Legacy              | HBB candidate                           |
+-------------+---------------------+-----------------------------------------+
| 03          | Routed repeat       | HTT repeat-expansion route              |
+-------------+---------------------+-----------------------------------------+
| 04          | Legacy              | BRCA1 candidate                         |
+-------------+---------------------+-----------------------------------------+
| 05          | Current             | HEXA candidate                          |
+-------------+---------------------+-----------------------------------------+
| 06          | Current             | PAH candidate                           |
+-------------+---------------------+-----------------------------------------+
| 07          | Current             | ATP7B candidate                         |
+-------------+---------------------+-----------------------------------------+
| 08          | Current             | APOB candidate                          |
+-------------+---------------------+-----------------------------------------+
| 09          | Current             | G6PD candidate                          |
+-------------+---------------------+-----------------------------------------+
| 10          | Current             | MEFV candidate and TPMT PGx result      |
+-------------+---------------------+-----------------------------------------+
| 11          | Current             | HFE candidate and CYP2D6 PGx result     |
+-------------+---------------------+-----------------------------------------+
| 12          | Current             | MLH1 candidate and DPYD PGx result      |
+-------------+---------------------+-----------------------------------------+

This audit demonstrates expected pipeline behaviour using synthetic validation inputs.

It does not constitute clinical validation for patient care.

.. _16-39-result-file-discovery-command:

16.39 Result-file discovery command
-----------------------------------

The following command creates a local inventory of generated files.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   OUTPUT="results/environment/generated_result_inventory.tsv"
   mkdir -p \
   "$(dirname "$OUTPUT")"
   {
   printf 'size_bytes\tmodified_utc\tpath\n'
   find results \
   -type f \
   -print0 |
   sort -z |
   while IFS= read -r -d '' file; do
   size="$(
   stat -c '%s' "$file"
   )"
   modified_epoch="$(
   stat -c '%Y' "$file"
   )"
   modified_utc="$(
   date \
   -u \
   -d "@$modified_epoch" \
   '+%Y-%m-%dT%H:%M:%SZ'
   )"
   printf '%s\t%s\t%s\n' \
   "$size" \
   "$modified_utc" \
   "$file"
   done
   } > "$OUTPUT"
   column \
   --separator $'\t' \
   --table \
   "$OUTPUT" |
   head -n 40

This inventory helps document:

-  what the pipeline generated;

-  where each file is stored;

-  when it was last modified;

-  how large it is.

.. _16-40-find-likely-final-tables-automatically:

16.40 Find likely final tables automatically
--------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find results \
   -type f \
   \( \
   -iname '*master*.tsv' \
   -o -iname '*candidate*.tsv' \
   -o -iname '*summary*.tsv' \
   -o -iname '*final*.tsv' \
   -o -iname '*report*.tsv' \
   \) \
   -printf '%s\t%p\n' |
   sort -k2,2

This command helps locate final candidate files without assuming an exact filename.

.. _16-41-find-tool-specific-outputs-automatically:

16.41 Find tool-specific outputs automatically
----------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   echo "=== VEP outputs ==="
   find results \
   -type f \
   -iname '*vep*' \
   | sort
   echo
   echo "=== SnpEff outputs ==="
   find results \
   -type f \
   -iname '*snpeff*' \
   | sort
   echo
   echo "=== ClinVar outputs ==="
   find results \
   -type f \
   -iname '*clinvar*' \
   | sort
   echo
   echo "=== SpliceAI outputs ==="
   find results \
   -type f \
   -iname '*spliceai*' \
   | sort
   echo
   echo "=== AnnotSV outputs ==="
   find results \
   -type f \
   -iname '*annotsv*' \
   | sort
   echo
   echo "=== ClassifyCNV outputs ==="
   find results \
   -type f \
   \( \
   -iname '*classifycnv*' \
   -o -name 'Scoresheet.txt' \
   \) \
   | sort
   echo
   echo "=== ISV-CNV outputs ==="
   find results \
   -type f \
   -iname '*isv*' \
   | sort
   echo
   echo "=== ClinPGx outputs ==="
   find results \
   -type f \
   \( \
   -iname '*clinpgx*' \
   -o -iname '*pgx*' \
   \) \
   | sort

.. _16-42-verify-output-tabular-structure-in-bulk:

16.42 Verify output tabular structure in bulk
---------------------------------------------

The following command checks TSV files for inconsistent row widths.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   python3 - <<'PY'
   from __future__ import annotations
   import csv
   from pathlib import Path
   root = Path("results")
   if not root.is_dir():
   raise SystemExit("ERROR: results directory missing.")
   checked = 0
   failed = 0
   for path in sorted(root.rglob("*.tsv")):
   if path.stat().st_size == 0:
   print(f"FAIL empty file: {path}")
   failed += 1
   continue
   try:
   with path.open(
   "r",
   encoding="utf-8-sig",
   newline="",
   ) as handle:
   reader = csv.reader(
   handle,
   delimiter="\t",
   )
   first_row = next(reader, None)
   if first_row is None:
   print(f"FAIL no rows: {path}")
   failed += 1
   continue
   expected_width = len(first_row)
   bad_lines = []
   for line_number, row in enumerate(
   reader,
   start=2,
   ):
   if len(row) != expected_width:
   bad_lines.append(line_number)
   if bad_lines:
   print(
   f"FAIL {path}: inconsistent rows at "
   + ",".join(map(str, bad_lines[:10]))
   )
   failed += 1
   else:
   print(
   f"PASS {path}: "
   f"{expected_width} column(s)"
   )
   checked += 1
   except UnicodeDecodeError:
   print(f"SKIP non-UTF-8 text: {path}")
   print()
   print(f"TSV files checked: {checked}")
   print(f"Failures: {failed}")
   if failed:
   raise SystemExit(1)
   PY

Some tool outputs may contain optional trailing columns or unusual formatting. Such files should be reviewed before deciding that the output is invalid.

.. _16-43-distinguish-warnings-from-failures:

16.43 Distinguish warnings from failures
----------------------------------------

A completed result may contain warnings.

Examples include:

-  

   .. container::

      Phenotype data unavailable

-  

   .. container::

      Sex-dependent interpretation uncertain

-  

   .. container::

      No ClinVar match

-  

   .. container::

      SpliceAI prediction unavailable

-  

   .. container::

      Unphased possible compound-heterozygous pair

-  

   .. container::

      CNV breakpoint imprecise

-  

   .. container::

      PGx diplotype incomplete

-  

   .. container::

      Repeat analysis requires specialist confirmation

-  

   .. container::

      These do not always mean the pipeline failed.

A failure includes:

-  

   .. container::

      Required input missing

-  

   .. container::

      VCF parsing failure

-  

   .. container::

      Reference mismatch

-  

   .. container::

      Annotation tool crash

-  

   .. container::

      Missing required output

-  

   .. container::

      Checksum failure

-  

   .. container::

      Unexpected zero-byte file

-  

   .. container::

      Invalid table structure

-  

   .. container::

      Audit failure

The final case status should make this distinction explicit.

.. _16-44-file-retention-policy:

16.44 File-retention policy
---------------------------

Files should be grouped into three retention levels.

**Essential permanent records**

Retain:

-  

   .. container::

      original input checksum

-  

   .. container::

      case metadata

-  

   .. container::

      intake report

-  

   .. container::

      final master table

-  

   .. container::

      final human-readable report

-  

   .. container::

      reproducibility manifest

-  

   .. container::

      important logs

-  

   .. container::

      output checksums

**Reproducibility-supporting files**

Retain when storage permits:

-  

   .. container::

      normalised VCF

-  

   .. container::

      VEP output

-  

   .. container::

      SnpEff output

-  

   .. container::

      ClinVar output

-  

   .. container::

      SpliceAI output

-  

   .. container::

      G2P mapping

-  

   .. container::

      phenotype table

-  

   .. container::

      inheritance table

-  

   .. container::

      AnnotSV output

-  

   .. container::

      ClassifyCNV scoresheet

-  

   .. container::

      ISV-CNV output

**Temporary files**

Temporary files may be removed after validation:

-  

   .. container::

      .tmp files

-  

   .. container::

      temporary decompressed copies

-  

   .. container::

      temporary query tables

-  

   .. container::

      sort intermediates

-  

   .. container::

      temporary cache fragments

Do not delete files until the final outputs and manifests have been verified.

.. _16-45-clean-temporary-files-safely:

16.45 Clean temporary files safely
----------------------------------

First display the files that would be removed:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find results \
   -type f \
   \( \
   -name '*.tmp' \
   -o -name '*.temporary' \
   -o -name '*.partial' \
   \) \
   -print

After reviewing the list:

.. code:: bash

   find results \
   -type f \
   \( \
   -name '*.tmp' \
   -o -name '*.temporary' \
   -o -name '*.partial' \
   \) \
   -delete

Never delete based only on broad patterns such as:

.. code:: bash

   rm -rf results/*

because this would remove validated outputs, reports and manifests.

.. _16-46-github-inclusion-policy-for-outputs:

16.46 GitHub inclusion policy for outputs
-----------------------------------------

The repository should include only compact, non-identifying outputs needed to demonstrate or validate the project.

Appropriate tracked materials include:

-  

   .. container::

      synthetic validation summaries

-  

   .. container::

      compact manifests

-  

   .. container::

      final validation status

-  

   .. container::

      audit script

-  

   .. container::

      expected candidate table

-  

   .. container::

      small checksums

-  

   .. container::

      documentation

Do not upload:

-  

   .. container::

      real patient VCFs

-  

   .. container::

      identifiable case reports

-  

   .. container::

      large annotated VCFs

-  

   .. container::

      large CNV outputs

-  

   .. container::

      SIF images

-  

   .. container::

      reference FASTA files

-  

   .. container::

      VEP caches

-  

   .. container::

      complete tool databases

-  

   .. container::

      temporary files

The .gitignore file enforces this separation.

.. _16-46-1-check-whether-generated-results-are-accidentally-staged:

16.46.1 Check whether generated results are accidentally staged
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git diff \
   --cached \
   --name-only |
   grep -E \
   '(^|/)(results|containers|resources/reference|resources/vep_cache)/' \
   || true

Review every match before committing.

Check staged file sizes:

.. code:: bash

   git diff \
   --cached \
   --name-only \
   --diff-filter=ACMRT |
   while IFS= read -r path; do
   [[ -f "$path" ]] || continue
   size="$(
   stat -c '%s' "$path"
   )"
   printf '%12s %s\n' \
   "$size" \
   "$path"
   done |
   sort -nr |
   head -n 30

.. _16-47-privacy-review:

16.47 Privacy review
--------------------

Before sharing an output, inspect it for:

-  

   .. container::

      patient names

-  

   .. container::

      hospital identifiers

-  

   .. container::

      email addresses

-  

   .. container::

      dates of birth

-  

   .. container::

      phone numbers

-  

   .. container::

      absolute local paths

-  

   .. container::

      sample identifiers

-  

   .. container::

      free-text clinical notes

An initial search is:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   OUTPUT_DIR="path/to/output_directory"
   grep -RInE \
   --include='*.tsv' \
   --include='*.csv' \
   --include='*.txt' \
   --include='*.md' \
   'patient.name|date.of.birth|\bDOB\b|hospital|email|phone|address|/home/[^/]+/' \
   "$OUTPUT_DIR" \
   || true

This search cannot guarantee de-identification. Manual review remains required.

.. _16-48-final-output-interpretation-sequence:

16.48 Final output interpretation sequence
------------------------------------------

The recommended review order is:

1. Confirm case identity and input checksum.

2. Confirm analysis and resource modes.

3. Review branch-routing summary.

4. Review top-ranked small variants.

5. Review top-ranked CNVs.

6. Review inheritance compatibility.

7. Review phenotype evidence.

8. Review ClinVar and population evidence.

9. Review compound-heterozygous pairs.

10. Review repeat and unsupported records.

11. Review ClinPGx findings separately.

12. Review warnings and limitations.

13. Confirm output and resource checksums.

14. Confirm the final audit status.

Starting only with the top score may hide an important routed repeat, unsupported structural variant or pharmacogenomic result.

.. _16-49-common-output-interpretation-errors:

16.49 Common output-interpretation errors
-----------------------------------------

+----------------------------------------------+----------------------------------------------------+
| **Error**                                    | **Correct interpretation**                         |
+==============================================+====================================================+
| Highest score equals diagnosis               | Highest score means first review priority          |
+----------------------------------------------+----------------------------------------------------+
| Score is a pathogenicity percentage          | Score is a project-specific prioritisation value   |
+----------------------------------------------+----------------------------------------------------+
| No ClinVar match means benign                | Variant may be novel or absent from ClinVar        |
+----------------------------------------------+----------------------------------------------------+
| Several VEP rows mean several variants       | They may be transcript consequences of one variant |
+----------------------------------------------+----------------------------------------------------+
| Several AnnotSV rows mean several CNVs       | They may be full and split rows for one CNV        |
+----------------------------------------------+----------------------------------------------------+
| <DEL> means copy number zero                 | Copy number depends on genotype and CN evidence    |
+----------------------------------------------+----------------------------------------------------+
| ISV probability is patient disease risk      | It is a model prediction                           |
+----------------------------------------------+----------------------------------------------------+
| Repeat detected means repeat confirmed       | Read-level confirmation was not performed          |
+----------------------------------------------+----------------------------------------------------+
| Unsupported means harmless                   | Current pipeline lacks a complete method           |
+----------------------------------------------+----------------------------------------------------+
| PGx result explains rare disease             | PGx and rare-disease evidence are separate         |
+----------------------------------------------+----------------------------------------------------+
| No PGx variant in VCF means normal diplotype | Variants-only VCF may omit reference loci          |
+----------------------------------------------+----------------------------------------------------+
| Missing HPO means phenotype mismatch         | Phenotype evidence was unavailable                 |
+----------------------------------------------+----------------------------------------------------+
| Legacy output is current output              | It is an accepted earlier canonical output         |
+----------------------------------------------+----------------------------------------------------+
| Empty branch means tool failure              | It may mean no applicable records                  |
+----------------------------------------------+----------------------------------------------------+
| Output file exists, so stage succeeded       | File size, structure and logs must be checked      |
+----------------------------------------------+----------------------------------------------------+
| Checksum difference can be ignored           | It requires investigation                          |
+----------------------------------------------+----------------------------------------------------+

.. _16-50-complete-result-directory-readiness-check:

16.50 Complete result-directory readiness check
-----------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   REQUIRED_PATHS=(
   results
   validation/final_audit_20260727/canonical_cases.tsv
   validation/final_audit_20260727/canonical_final_outputs.sha256
   validation/final_audit_20260727/key_resources.sha256
   validation/final_audit_20260727/pipeline_source.sha256
   validation/final_audit_20260727/FINAL_VALIDATION_STATUS.md
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py
   pipeline/case_workflow/00c_build_reproducibility_manifest.py
   pipeline/case_workflow/12_build_universal_master.py
   pipeline/case_workflow/14_build_master_candidate_table.py
   )
   FAILURES=0
   for path in "${REQUIRED_PATHS[@]}"; do
   if [[ -e "$path" && -s "$path" || -d "$path" ]]; then
   printf "PASS %s\n" "$path"
   else
   printf "FAIL %s\n" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo
   echo "ERROR: $FAILURES output or audit component(s) are missing."
   exit 1
   fi
   python -m py_compile \
   pipeline/case_workflow/00c_build_reproducibility_manifest.py \
   pipeline/case_workflow/12_build_universal_master.py \
   pipeline/case_workflow/14_build_master_candidate_table.py \
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py
   python \
   validation/final_audit_20260727/scripts/audit_patients_01_12_final.py
   echo
   echo "PASS: Result, manifest and final-audit components are ready."

.. _16-51-output-stage-completion-criteria:

16.51 Output-stage completion criteria
--------------------------------------

The output stage is complete when:

✓ The original intake report is preserved

✓ The resolved case context is available

✓ Routed variant classes remain separate

✓ Normalised VCFs are compressed and indexed

✓ VEP CSQ annotations are preserved

✓ SnpEff ANN annotations are preserved

✓ ClinVar significance, condition and review status are retained

✓ SpliceAI predictions are retained

✓ Gene–disease mappings preserve allelic requirement and mechanism

✓ HPO evidence distinguishes unavailable from incompatible

✓ Disease-resolution provenance is retained

✓ Inheritance and phase statuses remain visible

✓ ClinPGx output remains separate from rare-disease scoring

✓ AnnotSV full and split rows remain traceable to one CNV

✓ ClassifyCNV Scoresheet.txt is preserved

✓ ISV-CNV probability and SHAP evidence are preserved

✓ Repeat findings have dedicated route statuses

✓ Unsupported variants remain visible

✓ Universal scores remain traceable to detailed evidence

✓ Candidate ranking is deterministic

✓ Master tables have consistent row structure

✓ Logs are retained for every important stage

✓ Warnings are distinguished from failures

✓ Reproducibility manifests contain resource and tool information

✓ Important output files have checksums

✓ Current, legacy and routed-repeat provenance is preserved

✓ Patients 01–12 pass the final audit

✓ Patient 13 remains documented as intentionally not executed

✓ Large and identifying outputs remain outside GitHub

✓ Final results include clinical-review limitations

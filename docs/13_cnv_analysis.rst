.. _13-copy-number-variant-workflow-bed-conversion-annotsv-classifycnv-isv-cnv-and-c:

13. Copy-Number Variant Workflow: BED Conversion, AnnotSV, ClassifyCNV, ISV-CNV and CNV Prioritisation
======================================================================================================


Copy-number variants require interval-based analysis rather than the single-position consequence framework used for SNVs and small indels. A deletion or duplication may affect one exon, one complete gene, several genes, regulatory regions or an entire dosage-sensitive genomic interval.

The CNV branch of the project follows this structure:

CNV or structural-variant VCF

│

▼

DEL/DUP detection and interval validation

│

▼

Four-column GRCh38 BED conversion

│

┌──────┼───────────┐

│ │ │

▼ ▼ ▼

AnnotSV ClassifyCNV ISV-CNV

│ │ │

└──────┼───────────┘

│

▼

ClinGen dosage and gene–disease evidence

│

▼

HPO semantic phenotype evidence

│

▼

CNV-associated ClinPGx overlap

│

▼

Universal CNV candidate score

│

▼

Integrated CNV summary and master table

The principal project scripts are:

-  

   .. container::

      pipeline/case_workflow/10c_prepare_cnv_semantic_input.py

-  

   .. container::

      pipeline/case_workflow/10d_add_cnv_semantic_phenotype_evidence.py

-  

   .. container::

      pipeline/case_workflow/11_run_cnv_tools.sh

-  

   .. container::

      pipeline/case_workflow/11b_score_universal_cnv.py

-  

   .. container::

      pipeline/case_workflow/11c_add_cnv_clinpgx.py

-  

   .. container::

      pipeline/case_workflow/12_score_cnv_candidates.py

AnnotSV, ClassifyCNV and ISV-CNV provide complementary evidence. Their outputs must not be treated as three independent confirmations of pathogenicity because they may use overlapping genes, databases and dosage evidence.

.. _13-1-constitutional-cnv-classification-framework:

13.1 Constitutional CNV classification framework
------------------------------------------------

The ACMG and ClinGen constitutional CNV standards introduced a quantitative evidence-scoring framework and a five-tier classification system:

-  

   .. container::

      Pathogenic

-  

   .. container::

      Likely pathogenic

-  

   .. container::

      Variant of uncertain significance

-  

   .. container::

      Likely benign

-  

   .. container::

      Benign

The standards also recommend separating the evidence-based classification of a CNV from its implications for a particular patient. A CNV can therefore receive a classification while its relevance to the patient still depends on phenotype, inheritance, penetrance and clinical context.

The project follows the same conceptual separation:

CNV classification:

What does existing genomic evidence indicate about this interval?

Patient interpretation:

Does this CNV provide a suitable explanation for this case?

The universal CNV score is a prioritisation score. It does not replace formal clinical classification.

.. _13-2-required-cnv-information:

13.2 Required CNV information
-----------------------------

A usable CNV should contain:

-  

   .. container::

      Chromosome

-  

   .. container::

      Start coordinate

-  

   .. container::

      End coordinate

-  

   .. container::

      CNV type

-  

   .. container::

      Genome build

-  

   .. container::

      Sample or case identifier

-  

   .. container::

      Genotype or copy number, where available

-  

   .. container::

      The main supported types are:

-  

   .. container::

      DEL deletion or copy-number loss

-  

   .. container::

      DUP duplication or copy-number gain

-  

   .. container::

      The validated workflow uses:

-  

   .. container::

      Genome build: GRCh38

-  

   .. container::

      Chromosomes: chr1–chr22, chrX, chrY and chrM

Complex structural variants such as inversions, translocations, breakends and complex rearrangements may be detected, but they are not passed automatically through a DEL/DUP classification model.

.. _13-3-cnv-representation-in-vcf:

13.3 CNV representation in VCF
------------------------------

A symbolic deletion may resemble:

chr2 100001 cnv1 N <DEL> . PASS SVTYPE=DEL;END=500000

A symbolic duplication may resemble:

chr7 5500001 cnv2 N <DUP> . PASS SVTYPE=DUP;END=6200000

Important fields include:

+-----------+----------------------------------------------------------+
| **Field** | **Purpose**                                              |
+===========+==========================================================+
| CHROM     | Chromosome                                               |
+-----------+----------------------------------------------------------+
| POS       | Start position in the VCF coordinate system              |
+-----------+----------------------------------------------------------+
| ALT       | Symbolic allele such as <DEL> or <DUP>                   |
+-----------+----------------------------------------------------------+
| SVTYPE    | Structural-variant type                                  |
+-----------+----------------------------------------------------------+
| END       | Last affected genomic coordinate                         |
+-----------+----------------------------------------------------------+
| SVLEN     | Length of the structural variant, where supplied         |
+-----------+----------------------------------------------------------+
| GT        | Genotype                                                 |
+-----------+----------------------------------------------------------+
| CN        | Estimated copy number, where supplied                    |
+-----------+----------------------------------------------------------+
| CIPOS     | Confidence interval around the start                     |
+-----------+----------------------------------------------------------+
| CIEND     | Confidence interval around the end                       |
+-----------+----------------------------------------------------------+

END is essential for converting a symbolic VCF record into a genomic interval.

.. _13-3-1-copy-number-is-not-always-written-explicitly:

13.3.1 Copy number is not always written explicitly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A deletion record does not automatically mean that the copy number is zero.

In a diploid autosomal region:

Heterozygous deletion:

one copy lost

approximate copy number = 1

Homozygous deletion:

both copies lost

approximate copy number = 0

A VCF genotype such as:

0/1

normally represents one reference allele and one deletion allele. It does not by itself indicate complete loss of both copies.

Copy number zero should be supported by information such as:

CN=0

or a homozygous deletion genotype and appropriate copy-number evidence.

When neither CN nor reliable genotype evidence is present, the pipeline should report the CNV type without inventing an absolute copy number.

.. _13-4-bed-coordinate-convention:

13.4 BED coordinate convention
------------------------------

The CNV tools use a four-column BED-like representation:

chromosome start end cnv_type

Example:

chr2 100000 500000 DEL

chr7 5500000 6200000 DUP

The coordinate systems differ:

VCF:

POS is 1-based

END is inclusive

BED:

start is 0-based

end is exclusive

For a VCF CNV covering positions POS through END, the usual conversion is:

BED start = POS - 1

BED end = END

For example:

VCF:

POS=100001

END=500000

BED:

start=100000

end=500000

The interval length is:

500000 - 100000 = 400000 bases

which is equivalent to:

END - POS + 1

.. _13-5-prepare-an-independent-cnv-workflow-directory:

13.5 Prepare an independent CNV workflow directory
--------------------------------------------------

The production pipeline creates its own case directories. The following workspace is used only to test the CNV tools independently.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   CNV_WORK_DIR="$PROJECT_ROOT/results/tool_tests/cnv_workflow"
   mkdir -p \
   "$CNV_WORK_DIR" \
   "$CNV_WORK_DIR/logs" \
   "$CNV_WORK_DIR/manifests"
   echo "Project root: $PROJECT_ROOT"
   echo "CNV workspace: $CNV_WORK_DIR"

Confirm the main tools and resources:

.. code:: bash

   set -Eeuo pipefail
   REQUIRED_PATHS=(
   "$PROJECT_ROOT/resources/reference/hg38.fa"
   "$PROJECT_ROOT/resources/reference/hg38.fa.fai"
   "$PROJECT_ROOT/resources/annotsv_setup/AnnotSV/bin/AnnotSV"
   "$PROJECT_ROOT/tools/ClassifyCNV/ClassifyCNV.py"
   "$PROJECT_ROOT/containers/isv.sif"
   "$PROJECT_ROOT/resources/clingen/clingen_dosage_genes_regions.csv"
   )
   FAILURES=0
   for path in "${REQUIRED_PATHS[@]}"; do
   if [[ -s "$path" || -x "$path" ]]; then
   printf "PASS %s\n" "$path"
   else
   printf "FAIL %s\n" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo
   echo "ERROR: $FAILURES CNV requirement(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: CNV workflow prerequisites are present."

.. _13-6-validate-an-existing-four-column-cnv-bed-file:

13.6 Validate an existing four-column CNV BED file
--------------------------------------------------

Set the input:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CNV_BED="input/sample.cnvs.bed"

Run the structural validator:

.. code:: bash

   awk '
   BEGIN {
   FS = OFS = "\t"
   records = 0
   failures = 0
   }
   NF == 0 || $1 ~ /^#/ {
   next
   }
   {
   records++
   }
   NF != 4 {
   print \
   "ERROR line " NR \
   ": expected exactly 4 columns; observed " NF \
   > "/dev/stderr"
   failures++
   next
   }
   $1 !~ /^chr([1-9]|1[0-9]|2[0-2]|X|Y|M)$/ {
   print \
   "ERROR line " NR \
   ": unsupported chromosome " $1 \
   > "/dev/stderr"
   failures++
   }
   $2 !~ /^[0-9]+$/ {
   print \
   "ERROR line " NR \
   ": invalid BED start " $2 \
   > "/dev/stderr"
   failures++
   }
   $3 !~ /^[0-9]+$/ {
   print \
   "ERROR line " NR \
   ": invalid BED end " $3 \
   > "/dev/stderr"
   failures++
   }
   $2 ~ /^[0-9]+$/ &&
   $3 ~ /^[0-9]+$/ &&
   $2 >= $3 {
   print \
   "ERROR line " NR \
   ": start must be smaller than end" \
   > "/dev/stderr"
   failures++
   }
   $4 != "DEL" && $4 != "DUP" {
   print \
   "ERROR line " NR \
   ": CNV type must be DEL or DUP; observed " $4 \
   > "/dev/stderr"
   failures++
   }
   END {
   if (records == 0) {
   print "ERROR: CNV BED contains no records." \
   > "/dev/stderr"
   exit 1
   }
   if (failures > 0) {
   exit 1
   }
   print \
   "PASS: " records \
   " four-column CNV record(s) validated."
   }
   ' "$CNV_BED"

This command requires exactly four tab-separated columns. Additional metadata should be preserved in a separate manifest rather than added to the files sent to ClassifyCNV and ISV-CNV.

.. _13-7-confirm-cnv-intervals-exist-in-grch38:

13.7 Confirm CNV intervals exist in GRCh38
------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CNV_BED="input/sample.cnvs.bed"
   REFERENCE_INDEX="resources/reference/hg38.fa.fai"
   python3 - \
   "$CNV_BED" \
   "$REFERENCE_INDEX" <<'PY'
   from __future__ import annotations
   import sys
   from pathlib import Path
   bed_path = Path(sys.argv[1])
   fai_path = Path(sys.argv[2])
   chromosome_lengths: dict[str, int] = {}
   with fai_path.open(
   "r",
   encoding="utf-8",
   ) as handle:
   for raw_line in handle:
   fields = raw_line.rstrip("\n").split("\t")
   if len(fields) < 2:
   continue
   chromosome_lengths[fields[0]] = int(fields[1])
   failures = 0
   records = 0
   with bed_path.open(
   "r",
   encoding="utf-8-sig",
   ) as handle:
   for line_number, raw_line in enumerate(
   handle,
   start=1,
   ):
   line = raw_line.strip()
   if not line or line.startswith("#"):
   continue
   records += 1
   fields = line.split("\t")
   if len(fields) != 4:
   print(
   f"FAIL line {line_number}: "
   "expected four columns"
   )
   failures += 1
   continue
   chromosome, start_text, end_text, cnv_type = fields
   chromosome_length = chromosome_lengths.get(
   chromosome
   )
   if chromosome_length is None:
   print(
   f"FAIL line {line_number}: "
   f"{chromosome} absent from reference"
   )
   failures += 1
   continue
   try:
   start = int(start_text)
   end = int(end_text)
   except ValueError:
   print(
   f"FAIL line {line_number}: "
   "non-integer coordinate"
   )
   failures += 1
   continue
   if start < 0:
   print(
   f"FAIL line {line_number}: "
   "BED start is negative"
   )
   failures += 1
   if end > chromosome_length:
   print(
   f"FAIL line {line_number}: "
   f"end {end} exceeds "
   f"{chromosome} length "
   f"{chromosome_length}"
   )
   failures += 1
   if start >= end:
   print(
   f"FAIL line {line_number}: "
   "start is not smaller than end"
   )
   failures += 1
   if records == 0:
   raise SystemExit("ERROR: No CNV records found.")
   if failures:
   raise SystemExit(
   f"ERROR: {failures} invalid interval(s)."
   )
   print(
   f"PASS: {records} CNV interval(s) fit "
   "within the GRCh38 reference."
   )
   PY

.. _13-8-convert-a-symbolic-cnv-vcf-to-four-column-bed:

13.8 Convert a symbolic CNV VCF to four-column BED
--------------------------------------------------

The following conversion:

-  reads a VCF through bcftools;

-  accepts only DEL and DUP;

-  requires a valid END;

-  converts VCF coordinates to BED coordinates;

-  sorts intervals according to the reference FASTA;

-  creates a separate source manifest;

-  writes malformed records to a rejection report.

Set the VCF:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CNV_VCF="input/cases/case_001/original/case_001.raw.vcf"
   CNV_WORK_DIR="$PWD/results/tool_tests/cnv_workflow"
   OUTPUT_BED="$CNV_WORK_DIR/01.cnv_input.bed"
   SOURCE_MANIFEST="$CNV_WORK_DIR/manifests/cnv_source_records.tsv"
   REJECTED_RECORDS="$CNV_WORK_DIR/manifests/cnv_rejected_records.tsv"
   QUERY_FILE="$CNV_WORK_DIR/01.cnv_query.tmp.tsv"

Confirm the input:

.. code:: bash

   if [[ ! -s "$CNV_VCF" ]]; then
   echo "ERROR: CNV VCF is missing or empty:"
   echo "$CNV_VCF"
   exit 1
   fi
   bcftools view \
   --output-type v \
   --output /dev/null \
   "$CNV_VCF"

Extract the required fields:

.. code:: bash

   bcftools query \
   --format '%CHROM\t%POS\t%ID\t%REF\t%ALT\t%INFO/SVTYPE\t%INFO/END\n' \
   "$CNV_VCF" \
   > "$QUERY_FILE"

Convert and sort:

.. code:: bash

   python3 - \
   "$QUERY_FILE" \
   resources/reference/hg38.fa.fai \
   "$OUTPUT_BED" \
   "$SOURCE_MANIFEST" \
   "$REJECTED_RECORDS" <<'PY'
   from __future__ import annotations
   import sys
   from pathlib import Path
   query_path = Path(sys.argv[1])
   fai_path = Path(sys.argv[2])
   bed_path = Path(sys.argv[3])
   manifest_path = Path(sys.argv[4])
   rejected_path = Path(sys.argv[5])
   chromosome_order: dict[str, int] = {}
   with fai_path.open(
   "r",
   encoding="utf-8",
   ) as handle:
   for index, raw_line in enumerate(handle):
   chromosome = raw_line.split("\t", 1)[0]
   chromosome_order[chromosome] = index
   accepted: list[
   tuple[
   int,
   int,
   int,
   str,
   str,
   str,
   str,
   str,
   int,
   str,
   ]
   ] = []
   rejected: list[
   tuple[int, str, str]
   ] = []
   with query_path.open(
   "r",
   encoding="utf-8",
   ) as handle:
   for line_number, raw_line in enumerate(
   handle,
   start=1,
   ):
   fields = raw_line.rstrip("\n").split("\t")
   if len(fields) != 7:
   rejected.append(
   (
   line_number,
   raw_line.rstrip("\n"),
   "expected_seven_fields",
   )
   )
   continue
   (
   chromosome,
   position_text,
   variant_id,
   reference,
   alternate,
   svtype,
   end_text,
   ) = fields
   alternate_type = alternate.strip("<>").upper()
   svtype = svtype.upper()
   if svtype in {"", "."}:
   svtype = alternate_type
   if svtype not in {"DEL", "DUP"}:
   rejected.append(
   (
   line_number,
   raw_line.rstrip("\n"),
   f"unsupported_svtype:{svtype}",
   )
   )
   continue
   if chromosome not in chromosome_order:
   rejected.append(
   (
   line_number,
   raw_line.rstrip("\n"),
   "chromosome_absent_from_reference",
   )
   )
   continue
   try:
   position = int(position_text)
   end = int(end_text)
   except ValueError:
   rejected.append(
   (
   line_number,
   raw_line.rstrip("\n"),
   "missing_or_invalid_position_or_end",
   )
   )
   continue
   if position < 1 or end < position:
   rejected.append(
   (
   line_number,
   raw_line.rstrip("\n"),
   "invalid_interval",
   )
   )
   continue
   bed_start = position - 1
   bed_end = end
   accepted.append(
   (
   chromosome_order[chromosome],
   bed_start,
   bed_end,
   chromosome,
   svtype,
   variant_id,
   reference,
   alternate,
   position,
   end_text,
   )
   )
   accepted.sort(
   key=lambda item: (
   item[0],
   item[1],
   item[2],
   item[4],
   )
   )
   bed_path.parent.mkdir(
   parents=True,
   exist_ok=True,
   )
   manifest_path.parent.mkdir(
   parents=True,
   exist_ok=True,
   )
   with bed_path.open(
   "w",
   encoding="utf-8",
   newline="",
   ) as bed_handle, manifest_path.open(
   "w",
   encoding="utf-8",
   newline="",
   ) as manifest_handle:
   manifest_handle.write(
   "chromosome\tvcf_position\tvcf_end\t"
   "bed_start\tbed_end\tvariant_id\t"
   "reference\talternate\tcnv_type\n"
   )
   for (
   _order,
   bed_start,
   bed_end,
   chromosome,
   svtype,
   variant_id,
   reference,
   alternate,
   position,
   end_text,
   ) in accepted:
   bed_handle.write(
   f"{chromosome}\t"
   f"{bed_start}\t"
   f"{bed_end}\t"
   f"{svtype}\n"
   )
   manifest_handle.write(
   f"{chromosome}\t"
   f"{position}\t"
   f"{end_text}\t"
   f"{bed_start}\t"
   f"{bed_end}\t"
   f"{variant_id}\t"
   f"{reference}\t"
   f"{alternate}\t"
   f"{svtype}\n"
   )
   with rejected_path.open(
   "w",
   encoding="utf-8",
   newline="",
   ) as rejected_handle:
   rejected_handle.write(
   "query_line\treason\tsource_record\n"
   )
   for line_number, source_record, reason in rejected:
   rejected_handle.write(
   f"{line_number}\t"
   f"{reason}\t"
   f"{source_record}\n"
   )
   if not accepted:
   raise SystemExit(
   "ERROR: No supported DEL or DUP records "
   "were converted."
   )
   print(
   f"PASS: {len(accepted)} CNV record(s) converted."
   )
   print(
   f"Rejected or unsupported records: "
   f"{len(rejected)}"
   )
   PY
   Inspect the outputs:
   echo "=== Four-column CNV BED ==="
   column \
   --separator $'\t' \
   --table \
   "$OUTPUT_BED"
   echo
   echo "=== Source manifest ==="
   column \
   --separator $'\t' \
   --table \
   "$SOURCE_MANIFEST"
   echo
   echo "=== Rejected records ==="
   column \
   --separator $'\t' \
   --table \
   "$REJECTED_RECORDS"

The rejection report must be retained even when it contains only a header.

.. _13-9-calculate-cnv-sizes:

13.9 Calculate CNV sizes
------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CNV_BED="results/tool_tests/cnv_workflow/01.cnv_input.bed"
   awk '
   BEGIN {
   FS = OFS = "\t"
   print \
   "chromosome", \
   "start", \
   "end", \
   "cnv_type", \
   "size_bp"
   }
   NF == 4 {
   print \
   $1, \
   $2, \
   $3, \
   $4, \
   $3 - $2
   }
   ' "$CNV_BED" \
   > results/tool_tests/cnv_workflow/01.cnv_sizes.tsv
   column \
   --separator $'\t' \
   --table \
   results/tool_tests/cnv_workflow/01.cnv_sizes.tsv

CNV size is useful for describing a variant, but size alone does not determine pathogenicity. A small deletion affecting an essential exon may be more important than a large gene-poor interval.

.. _13-10-annotsv-analysis:

13.10 AnnotSV analysis
----------------------

.. _13-10-1-purpose:

13.10.1 Purpose
~~~~~~~~~~~~~~~

AnnotSV provides structural-variant annotation at both the whole-interval level and the overlapping gene or transcript level. Its output can contain genomic location, cytoband, genes, transcripts, coding overlap, dosage sensitivity, known CNV overlap, population evidence and ranking fields.

AnnotSV supports three annotation modes:

-  

   .. container::

      full

-  

   .. container::

      split

-  

   .. container::

      both

full represents evidence for the complete structural-variant interval, while split produces gene- or transcript-level annotations for overlapping portions. both retains both levels, allowing whole-CNV and gene-specific evidence to be reviewed together. (`LBGI <https://www.lbgi.fr/AnnotSV/Documentation/README.AnnotSV_latest.pdf>`__)

The project uses:

.. code:: bash

   -annotationMode both

.. _13-10-2-confirm-the-annotsv-installation:

13.10.2 Confirm the AnnotSV installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   export ANNOTSV="$PWD/resources/annotsv_setup/AnnotSV"
   ANNOTSV_EXECUTABLE="$ANNOTSV/bin/AnnotSV"
   ANNOTSV_ANNOTATIONS="$ANNOTSV/share/AnnotSV"
   if [[ ! -x "$ANNOTSV_EXECUTABLE" ]]; then
   echo "ERROR: AnnotSV executable is unavailable:"
   echo "$ANNOTSV_EXECUTABLE"
   exit 1
   fi
   if [[ ! -d "$ANNOTSV_ANNOTATIONS/Annotations_Human" ]]; then
   echo "ERROR: AnnotSV human annotations are unavailable:"
   echo "$ANNOTSV_ANNOTATIONS/Annotations_Human"
   exit 1
   fi
   echo "PASS: AnnotSV executable and human annotations are present."

The direct source installation with make PREFIX=. install-human-annotation is important because packaged container or Bioconda builds may not include the large annotation datasets.

.. _13-10-3-run-annotsv:

13.10.3 Run AnnotSV
~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   CNV_WORK_DIR="$PROJECT_ROOT/results/tool_tests/cnv_workflow"
   export ANNOTSV="$PROJECT_ROOT/resources/annotsv_setup/AnnotSV"
   CNV_BED="$CNV_WORK_DIR/01.cnv_input.bed"
   ANNOTSV_OUTPUT="$CNV_WORK_DIR/02.AnnotSV.tsv"
   ANNOTSV_LOG="$CNV_WORK_DIR/logs/02.AnnotSV.log"
   rm -f \
   "$ANNOTSV_OUTPUT" \
   "$ANNOTSV_LOG"
   "$ANNOTSV/bin/AnnotSV" \
   -SVinputFile "$CNV_BED" \
   -outputFile "$ANNOTSV_OUTPUT" \
   -svtBEDcol 4 \
   -genomeBuild GRCh38 \
   -annotationMode both \
   -annotationsDir "$ANNOTSV/share/AnnotSV" \
   -overwrite 1 \
   > "$ANNOTSV_LOG" \
   2>&1

The documented four-column BED usage relies on -svtBEDcol 4, with the fourth column containing the structural-variant type.

.. _13-10-4-verify-annotsv-completion:

13.10.4 Verify AnnotSV completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   set -Eeuo pipefail
   if [[ ! -s "$ANNOTSV_OUTPUT" ]]; then
   echo "ERROR: AnnotSV output was not created."
   echo
   tail -n 100 "$ANNOTSV_LOG"
   exit 1
   fi
   if grep -Eqi \
   'exit with error|couldn.t open|fatal error' \
   "$ANNOTSV_LOG"
   then
   echo "ERROR: AnnotSV log contains a fatal error."
   echo
   tail -n 100 "$ANNOTSV_LOG"
   exit 1
   fi
   echo "PASS: AnnotSV output created."
   echo
   echo "Rows:"

wc -l "$ANNOTSV_OUTPUT"

.. code:: bash

   echo
   echo "Header:"
   head -n 1 "$ANNOTSV_OUTPUT"

A warning does not always indicate failure, but a missing output or explicit exit error must stop the CNV branch.

.. _13-11-understanding-important-annotsv-fields:

13.11 Understanding important AnnotSV fields
--------------------------------------------

AnnotSV output may include fields such as:

+---------------------------+---------------------------------------------+
| **Field**                 | **Interpretation**                          |
+===========================+=============================================+
| AnnotSV_ID                | Internal identifier assigned by AnnotSV     |
+---------------------------+---------------------------------------------+
| SV_chrom                  | Chromosome                                  |
+---------------------------+---------------------------------------------+
| SV_start                  | AnnotSV interval start                      |
+---------------------------+---------------------------------------------+
| SV_end                    | AnnotSV interval end                        |
+---------------------------+---------------------------------------------+
| SV_length                 | Structural-variant length                   |
+---------------------------+---------------------------------------------+
| SV_type                   | DEL, DUP or another type                    |
+---------------------------+---------------------------------------------+
| Annotation_mode           | Full or split row                           |
+---------------------------+---------------------------------------------+
| CytoBand                  | Cytogenetic chromosome band                 |
+---------------------------+---------------------------------------------+
| Gene_name                 | Overlapping gene                            |
+---------------------------+---------------------------------------------+
| Gene_count                | Number of genes affected                    |
+---------------------------+---------------------------------------------+
| Tx                        | Transcript identifier                       |
+---------------------------+---------------------------------------------+
| Tx_start                  | Transcript start                            |
+---------------------------+---------------------------------------------+
| Tx_end                    | Transcript end                              |
+---------------------------+---------------------------------------------+
| Overlapped_tx_length      | Transcript bases affected                   |
+---------------------------+---------------------------------------------+
| Overlapped_CDS_length     | Coding-sequence bases affected              |
+---------------------------+---------------------------------------------+
| Overlapped_CDS_percent    | Percentage of CDS affected                  |
+---------------------------+---------------------------------------------+
| Frameshift                | Predicted coding-frame effect               |
+---------------------------+---------------------------------------------+
| Location                  | Intragenic or transcript-region description |
+---------------------------+---------------------------------------------+
| HI                        | Haploinsufficiency-related evidence         |
+---------------------------+---------------------------------------------+
| TS                        | Triplosensitivity-related evidence          |
+---------------------------+---------------------------------------------+
| AnnotSV_ranking_score     | AnnotSV ranking score                       |
+---------------------------+---------------------------------------------+
| AnnotSV_ranking_criteria  | Evidence contributing to the ranking        |
+---------------------------+---------------------------------------------+
| ACMG_class                | AnnotSV classification category             |
+---------------------------+---------------------------------------------+

The precise columns depend on the AnnotSV release and installed resources. The output header must therefore be read directly rather than assumed.

.. _13-11-1-cytoband:

13.11.1 Cytoband
~~~~~~~~~~~~~~~~

A cytoband is a region visible in a stained chromosome.

Example:

7q11.23

means:

-  

   .. container::

      Chromosome 7

-  

   .. container::

      Long arm: q

-  

   .. container::

      Region 1

-  

   .. container::

      Band 1

-  

   .. container::

      Sub-band 23

Cytobands provide a traditional chromosome-level location, while genomic coordinates provide the exact sequence interval.

.. _13-11-2-tx:

13.11.2 Tx
~~~~~~~~~~

Tx means transcript.

A gene can have several transcripts because different combinations of exons may be used. A CNV may therefore:

-  remove one transcript completely;

-  affect only selected transcripts;

-  disrupt one exon;

-  leave another transcript unaffected.

The transcript identifier should be retained when determining whether the biologically relevant transcript is affected.

.. _13-11-3-cds:

13.11.3 CDS
~~~~~~~~~~~

CDS means coding sequence.

It represents the portion of a transcript translated into protein.

A CNV may overlap:

-  

   .. container::

      Promoter

-  

   .. container::

      5′ untranslated region

-  

   .. container::

      Coding exon

-  

   .. container::

      Intron

-  

   .. container::

      3′ untranslated region

-  

   .. container::

      Entire transcript

Overlapped_CDS_length indicates how many coding bases are affected. It does not include untranslated or intronic sequence.

.. _13-11-4-full-and-split-rows:

13.11.4 Full and split rows
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  

   .. container::

      A full row describes the CNV as one complete genomic interval.

-  

   .. container::

      A split row describes evidence associated with an overlapping gene or transcript.

-  

   .. container::

      When annotationMode both is used, the same CNV may therefore appear in several output rows. These are not separate CNVs.

-  

   .. container::

      The pipeline must group them using the AnnotSV or source CNV identifier before candidate scoring.

.. _13-12-inspect-annotsv-annotation-modes:

13.12 Inspect AnnotSV annotation modes
--------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   ANNOTSV_OUTPUT="results/tool_tests/cnv_workflow/02.AnnotSV.tsv"
   python3 - "$ANNOTSV_OUTPUT" <<'PY'
   from __future__ import annotations
   import csv
   import sys
   from collections import Counter
   from pathlib import Path
   path = Path(sys.argv[1])
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
   raise SystemExit("ERROR: AnnotSV header missing.")
   mode_column = None
   for candidate in (
   "Annotation_mode",
   "Annotation mode",
   "annotation_mode",
   ):
   if candidate in reader.fieldnames:
   mode_column = candidate
   break
   if mode_column is None:
   print("Available columns:")
   for column in reader.fieldnames:
   print(column)
   raise SystemExit(
   "ERROR: Annotation-mode column was not found."
   )
   counts = Counter(
   row.get(mode_column, "").strip()
   for row in reader
   )
   print("AnnotSV annotation modes:")
   for mode, count in sorted(counts.items()):
   print(f" {mode or '<blank>'}: {count}")
   PY

.. _13-13-classifycnv-analysis:

13.13 ClassifyCNV analysis
--------------------------

.. _13-13-1-purpose:

13.13.1 Purpose
~~~~~~~~~~~~~~~

ClassifyCNV accepts CNV genomic coordinates and type, then reports:

-  clinical classification;

-  total score;

-  evidence-score breakdown;

-  dosage-sensitive genes or regions;

-  protein-coding genes of potential importance.

It supports GRCh38 and generates a tab-delimited result suitable for downstream pipeline integration.

ClassifyCNV implements selected parts of the ACMG/ClinGen constitutional CNV framework. Its classification still requires review of phenotype, inheritance, literature and evidence that may not be fully represented in the bundled databases.

.. _13-13-2-confirm-the-classifycnv-installation:

13.13.2 Confirm the ClassifyCNV installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CLASSIFYCNV_DIR="$PWD/tools/ClassifyCNV"
   REQUIRED_FILES=(
   "$CLASSIFYCNV_DIR/ClassifyCNV.py"
   "$CLASSIFYCNV_DIR/Resources"
   )
   for path in "${REQUIRED_FILES[@]}"; do
   if [[ -e "$path" ]]; then
   echo "PASS: $path"
   else
   echo "ERROR: ClassifyCNV component missing:"
   echo "$path"
   exit 1
   fi
   done
   python3 -m py_compile \
   "$CLASSIFYCNV_DIR/ClassifyCNV.py"

.. _13-13-3-run-classifycnv:

13.13.3 Run ClassifyCNV
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   CNV_WORK_DIR="$PROJECT_ROOT/results/tool_tests/cnv_workflow"
   CLASSIFYCNV_DIR="$PROJECT_ROOT/tools/ClassifyCNV"
   CNV_BED="$CNV_WORK_DIR/01.cnv_input.bed"
   RUN_NAME="universal_cnv_smoke_test"
   CLASSIFY_LOG="$CNV_WORK_DIR/logs/03.ClassifyCNV.log"
   rm -rf \
   "$CLASSIFYCNV_DIR/ClassifyCNV_results/$RUN_NAME"
   cd "$CLASSIFYCNV_DIR"
   python3 ClassifyCNV.py \
   --infile "$CNV_BED" \
   --GenomeBuild hg38 \
   --outdir "$RUN_NAME" \
   > "$CLASSIFY_LOG" \
   2>&1

ClassifyCNV’s expected input is a BED file containing coordinates and deletion or duplication type.

.. _13-13-4-locate-and-preserve-the-classifycnv-scoresheet:

13.13.4 Locate and preserve the ClassifyCNV scoresheet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   CNV_WORK_DIR="$PROJECT_ROOT/results/tool_tests/cnv_workflow"
   CLASSIFYCNV_DIR="$PROJECT_ROOT/tools/ClassifyCNV"
   RUN_NAME="universal_cnv_smoke_test"
   SOURCE_SCORESHEET="$CLASSIFYCNV_DIR/ClassifyCNV_results/$RUN_NAME/Scoresheet.txt"
   FINAL_SCORESHEET="$CNV_WORK_DIR/03.ClassifyCNV.Scoresheet.txt"
   CLASSIFY_LOG="$CNV_WORK_DIR/logs/03.ClassifyCNV.log"
   if [[ ! -s "$SOURCE_SCORESHEET" ]]; then
   echo "ERROR: ClassifyCNV Scoresheet.txt was not created."
   echo
   tail -n 100 "$CLASSIFY_LOG"
   exit 1
   fi
   cp \
   --preserve=mode,timestamps \
   "$SOURCE_SCORESHEET" \
   "$FINAL_SCORESHEET"
   echo "PASS: ClassifyCNV scoresheet preserved at:"
   echo "$FINAL_SCORESHEET"
   echo
   head -n 3 "$FINAL_SCORESHEET"

.. _13-14-understanding-the-classifycnv-scoresheet:

13.14 Understanding the ClassifyCNV scoresheet
----------------------------------------------

The scoresheet commonly contains fields such as:

-  

   .. container::

      Variant ID

-  

   .. container::

      Chromosome

-  

   .. container::

      Start

-  

   .. container::

      End

-  

   .. container::

      Type

-  

   .. container::

      Classification

-  

   .. container::

      Total score

-  

   .. container::

      Evidence categories

-  

   .. container::

      Dosage-sensitive genes

-  

   .. container::

      Protein-coding genes

The exact fields must be read from the output header.

Inspect them:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SCORESHEET="results/tool_tests/cnv_workflow/03.ClassifyCNV.Scoresheet.txt"
   python3 - "$SCORESHEET" <<'PY'
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
   raise SystemExit(
   "ERROR: ClassifyCNV header is missing."
   )
   rows = [
   row
   for row in reader
   if row and any(value.strip() for value in row)
   ]
   print(f"Records: {len(rows)}")
   print("Columns:")
   for index, column in enumerate(header, start=1):
   print(f"{index:02d}. {column}")
   PY

Do not derive the classification solely by visually reading one evidence column. Use the final classification, total score and complete evidence breakdown together.

.. _13-15-precise-versus-imprecise-cnvs:

13.15 Precise versus imprecise CNVs
-----------------------------------

A CNV may have:

Precise breakpoints

or:

Estimated breakpoint intervals

Confidence fields such as:

-  

   .. container::

      CIPOS

-  

   .. container::

      CIEND

indicate uncertainty around the start and end positions.

An option intended for precise intragenic breakpoints should be used only when the input breakpoints are genuinely reliable. Exome-derived or read-depth CNVs may have broad boundary uncertainty even when one coordinate is written in the VCF.

The pipeline should preserve:

-  

   .. container::

      Breakpoint precision

-  

   .. container::

      Caller

-  

   .. container::

      Calling method

-  

   .. container::

      Confidence interval

where available.

.. _13-16-isv-cnv-analysis:

13.16 ISV-CNV analysis
----------------------

.. _13-16-1-purpose:

13.16.1 Purpose
~~~~~~~~~~~~~~~

ISV-CNV uses a machine-learning model to predict CNV pathogenicity. Its command-line input uses GRCh38 intervals with the columns:

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

      cnv_type

The command-line interface supports optional prediction probabilities with -p and SHAP values with -sv.

ISV-CNV contributes a separate prioritisation signal. It does not replace the evidence-based ACMG/ClinGen classification.

.. _13-16-2-prepare-the-headered-isv-input:

13.16.2 Prepare the headered ISV input
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CNV_WORK_DIR="$PWD/results/tool_tests/cnv_workflow"
   CNV_BED="$CNV_WORK_DIR/01.cnv_input.bed"
   ISV_INPUT="$CNV_WORK_DIR/04.isv_input.tsv"
   {
   printf 'chromosome\tstart\tend\tcnv_type\n'
   cat "$CNV_BED"
   } > "$ISV_INPUT"
   column \
   --separator $'\t' \
   --table \
   "$ISV_INPUT"

Validate the header:

.. code:: bash

   EXPECTED_HEADER="$(
   printf 'chromosome\tstart\tend\tcnv_type'
   )"
   OBSERVED_HEADER="$(
   head -n 1 "$ISV_INPUT"
   )"
   if [[ "$OBSERVED_HEADER" != "$EXPECTED_HEADER" ]]; then
   echo "ERROR: Incorrect ISV-CNV header."
   echo "Expected: $EXPECTED_HEADER"
   echo "Observed: $OBSERVED_HEADER"
   exit 1
   fi
   echo "PASS: ISV-CNV input header is correct."

.. _13-16-3-confirm-the-isv-command-is-exposed:

13.16.3 Confirm the ISV command is exposed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   ISV_CONTAINER="containers/isv.sif"
   if [[ ! -s "$ISV_CONTAINER" ]]; then
   echo "ERROR: ISV-CNV container is missing."
   exit 1
   fi
   if apptainer exec \
   "$ISV_CONTAINER" \
   sh -c 'command -v isv >/dev/null 2>&1'
   then
   echo "PASS: ISV command is available."
   else
   echo "ERROR: The committed ISV container does not expose the isv command."
   echo "Inspect containers/isv.def and pipeline/case_workflow/11_run_cnv_tools.sh."
   exit 1
   fi

.. _13-16-4-run-isv-cnv:

13.16.4 Run ISV-CNV
~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   CNV_WORK_DIR="$PROJECT_ROOT/results/tool_tests/cnv_workflow"
   ISV_CONTAINER="$PROJECT_ROOT/containers/isv.sif"
   ISV_INPUT="$CNV_WORK_DIR/04.isv_input.tsv"
   ISV_OUTPUT="$CNV_WORK_DIR/04.ISV_CNV.tsv"
   ISV_LOG="$CNV_WORK_DIR/logs/04.ISV_CNV.log"
   rm -f \
   "$ISV_OUTPUT" \
   "$ISV_LOG"
   apptainer exec \
   --bind "$PROJECT_ROOT:/project" \
   "$ISV_CONTAINER" \
   isv \
   -i /project/results/tool_tests/cnv_workflow/04.isv_input.tsv \
   -o /project/results/tool_tests/cnv_workflow/04.ISV_CNV.tsv \
   -p \
   -sv \
   > "$ISV_LOG" \
   2>&1

Verify:

.. code:: bash

   set -Eeuo pipefail
   if [[ ! -s "$ISV_OUTPUT" ]]; then
   echo "ERROR: ISV-CNV output was not created."
   echo
   tail -n 100 "$ISV_LOG"
   exit 1
   fi
   echo "PASS: ISV-CNV output created."
   echo
   head -n 5 "$ISV_OUTPUT"

The exact output columns depend on the ISV version recorded in containers/isv.def.

.. _13-17-interpreting-isv-cnv-probabilities:

13.17 Interpreting ISV-CNV probabilities
----------------------------------------

A probability is the model’s estimate based on its training data and input features.

It is not equivalent to:

The probability that this patient has the disease

or:

The probability that the CNV is clinically causal

The result can be affected by:

-  training-data composition;

-  feature availability;

-  CNV type;

-  interval size;

-  gene density;

-  database overlap;

-  differences between training and current data.

The model version and container checksum must be recorded with every result.

.. _13-18-interpreting-shap-values:

13.18 Interpreting SHAP values
------------------------------

SHAP values indicate how individual model features contributed to the prediction.

A positive SHAP contribution generally pushes the model towards one prediction direction, while a negative contribution pushes it towards the opposite direction.

SHAP values can help answer:

Which features influenced the model?

They do not independently answer:

Which biological mechanism caused the disease?

A high SHAP contribution from gene count or CNV size should therefore be interpreted as model behaviour rather than direct causal evidence.

.. _13-19-verify-that-every-input-cnv-has-tool-output:

13.19 Verify that every input CNV has tool output
-------------------------------------------------

Because each tool may represent coordinates differently, the first validation should compare record counts and keys.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CNV_BED="results/tool_tests/cnv_workflow/01.cnv_input.bed"
   ANNOTSV_OUTPUT="results/tool_tests/cnv_workflow/02.AnnotSV.tsv"
   CLASSIFY_OUTPUT="results/tool_tests/cnv_workflow/03.ClassifyCNV.Scoresheet.txt"
   ISV_OUTPUT="results/tool_tests/cnv_workflow/04.ISV_CNV.tsv"
   INPUT_COUNT="$(
   awk '
   NF == 4 && $1 !~ /^#/ {
   count++
   }
   END {
   print count + 0
   }
   ' "$CNV_BED"
   )"
   echo "Input CNVs: $INPUT_COUNT"
   echo "AnnotSV rows: $(($(wc -l < "$ANNOTSV_OUTPUT") - 1))"
   echo "ClassifyCNV rows: $(($(wc -l < "$CLASSIFY_OUTPUT") - 1))"
   echo "ISV-CNV rows: $(($(wc -l < "$ISV_OUTPUT") - 1))"

AnnotSV can legitimately contain more output rows than input CNVs because annotationMode both creates whole-interval and gene/transcript-level records.

ClassifyCNV and ISV-CNV should ordinarily produce one principal result per supported input interval.

.. _13-20-clingen-dosage-sensitivity:

13.20 ClinGen dosage sensitivity
--------------------------------

ClinGen dosage evidence evaluates whether loss or gain of a gene or region is associated with disease.

The two principal concepts are:

Haploinsufficiency:

-  

   .. container::

      Disease caused by loss of one functional copy

-  

   .. container::

      Triplosensitivity:

-  

   .. container::

      Disease caused by an additional copy

The relationship with CNV type is:

-  

   .. container::

      Deletion + haploinsufficient gene

-  

   .. container::

      Potentially compatible dosage mechanism

-  

   .. container::

      Duplication + triplosensitive gene

-  

   .. container::

      Potentially compatible dosage mechanism

The reverse combinations do not automatically receive the same evidence.

For example:

Deletion of a triplosensitive-only region

does not establish the disease mechanism associated with increased dosage.

.. _13-20-1-verify-the-local-clingen-resource:

13.20.1 Verify the local ClinGen resource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CLINGEN_FILE="resources/clingen/clingen_dosage_genes_regions.csv"
   if [[ ! -s "$CLINGEN_FILE" ]]; then
   echo "ERROR: ClinGen dosage file is missing."
   exit 1
   fi
   python3 - "$CLINGEN_FILE" <<'PY'
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
   reader = csv.reader(handle)
   header = next(reader, None)
   if not header:
   raise SystemExit("ERROR: ClinGen header missing.")
   rows = sum(
   1
   for row in reader
   if row and any(value.strip() for value in row)
   )
   print(f"ClinGen records: {rows}")
   print("Columns:")
   for index, column in enumerate(header, start=1):
   print(f"{index:02d}. {column}")
   PY

.. _13-21-cnv-phenotype-evidence:

13.21 CNV phenotype evidence
----------------------------

The CNV phenotype scripts are:

.. code:: bash

   pipeline/case_workflow/10c_prepare_cnv_semantic_input.py
   pipeline/case_workflow/10d_add_cnv_semantic_phenotype_evidence.py

The workflow may consider:

-  genes fully contained in the CNV;

-  genes partially disrupted by a breakpoint;

-  dosage-sensitive genes;

-  known gene–disease relationships;

-  patient HPO terms;

-  disease HPO annotations;

-  semantic similarity;

-  DEL/DUP compatibility with the disease mechanism.

A large CNV may overlap several diseases. The pipeline should retain separate gene–disease candidates rather than reporting every overlapping gene as one combined disorder.

.. _13-22-cnv-clinpgx-overlap:

13.22 CNV ClinPGx overlap
-------------------------

The script:

.. code:: bash

   pipeline/case_workflow/11c_add_cnv_clinpgx.py

checks whether a CNV overlaps a pharmacogenomically relevant gene or region.

The output should distinguish:

Pharmacogene overlap detected

from:

Complete pharmacogenomic diplotype resolved

A CYP2D6 deletion, duplication or hybrid allele may require specialised copy-number and haplotype analysis. Gene overlap alone is not sufficient for complete star-allele assignment.

.. _13-23-universal-cnv-scoring:

13.23 Universal CNV scoring
---------------------------

The project uses:

-  

   .. container::

      pipeline/case_workflow/11b_score_universal_cnv.py

-  

   .. container::

      pipeline/case_workflow/12_score_cnv_candidates.py

-  

   .. container::

      The universal CNV score may integrate:

-  

   .. container::

      CNV type

-  

   .. container::

      CNV size

-  

   .. container::

      AnnotSV evidence

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

      ClinGen dosage sensitivity

-  

   .. container::

      Gene–disease evidence

-  

   .. container::

      Phenotype similarity

-  

   .. container::

      Inheritance compatibility

-  

   .. container::

      Gene count

-  

   .. container::

      Coding disruption

-  

   .. container::

      Population CNV evidence

-  

   .. container::

      ClinPGx overlap

The exact weighting is defined in the committed Python source. It should not be recreated differently in the Word document.

.. _13-23-1-inspect-scoring-script-interfaces:

13.23.1 Inspect scoring-script interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPTS=(
   pipeline/case_workflow/10c_prepare_cnv_semantic_input.py
   pipeline/case_workflow/10d_add_cnv_semantic_phenotype_evidence.py
   pipeline/case_workflow/11b_score_universal_cnv.py
   pipeline/case_workflow/11c_add_cnv_clinpgx.py
   pipeline/case_workflow/12_score_cnv_candidates.py
   )
   for script in "${SCRIPTS[@]}"; do
   echo
   echo "=== $script ==="
   if [[ ! -s "$script" ]]; then
   echo "ERROR: Missing script."
   exit 1
   fi
   python -m py_compile "$script"
   if python "$script" --help \
   > /tmp/cnv_script_help.txt \
   2>&1
   then
   cat /tmp/cnv_script_help.txt
   else
   echo "No standard --help output was returned."
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$script" \
   || true
   fi
   done
   rm -f /tmp/cnv_script_help.txt

The complete pipeline launcher should remain the normal method for integrating these files.

.. _13-24-inspect-the-cnv-orchestration-script-safely:

13.24 Inspect the CNV orchestration script safely
-------------------------------------------------

Do not run the orchestration script with guessed arguments.

Validate its syntax:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CNV_SCRIPT="pipeline/case_workflow/11_run_cnv_tools.sh"
   if [[ ! -s "$CNV_SCRIPT" ]]; then
   echo "ERROR: CNV orchestration script is missing."
   exit 1
   fi

bash -n "$CNV_SCRIPT"

.. code:: bash

   echo "PASS: CNV orchestration script passed Bash syntax validation."

Inspect its declared usage, variables and tool calls:

.. code:: bash

   grep -nE \
   'Usage|usage|getopts|ANNOTSV|ClassifyCNV|ISV|Scoresheet|\.bed|\.tsv' \
   "$CNV_SCRIPT" \
   | head -n 200

The complete source should be referenced through GitHub in the report.

.. _13-25-cnv-inheritance-analysis:

13.25 CNV inheritance analysis
------------------------------

CNV inheritance may be:

-  

   .. container::

      De novo

-  

   .. container::

      Maternally inherited

-  

   .. container::

      Paternally inherited

-  

   .. container::

      Unknown

-  

   .. container::

      Mosaic

A single-sample VCF cannot prove de novo status.

Parental or family data are required to evaluate:

-  whether the CNV is present in either parent;

-  whether it segregates with disease;

-  whether an apparently unaffected parent has reduced penetrance;

-  whether a parent is mosaic;

-  whether the breakpoints are identical.

The pipeline should report:

inheritance_not_assessed

when suitable family data are unavailable.

.. _13-26-partial-gene-overlap:

13.26 Partial gene overlap
--------------------------

A CNV can affect a gene in several ways:

-  

   .. container::

      Complete deletion

-  

   .. container::

      Complete duplication

-  

   .. container::

      Single-exon deletion

-  

   .. container::

      Multi-exon deletion

-  

   .. container::

      Partial duplication

-  

   .. container::

      Promoter disruption

-  

   .. container::

      Breakpoint within an intron

-  

   .. container::

      Breakpoint within the coding sequence

A partial duplication is not automatically equivalent to increased dosage. It may:

-  disrupt the reading frame;

-  create a truncated transcript;

-  duplicate selected exons;

-  have unknown orientation;

-  occur in tandem or elsewhere.

Without breakpoint orientation and structure, the biological effect may remain uncertain.

.. _13-27-exon-level-cnvs:

13.27 Exon-level CNVs
---------------------

An exon-level CNV requires careful transcript review.

The analysis should determine:

-  which transcript is affected;

-  whether the exon is coding;

-  whether the exon is present in the clinically relevant transcript;

-  whether the event is in frame;

-  whether nonsense-mediated decay is expected;

-  whether similar exon-level CNVs are known;

-  whether the gene disease mechanism is loss of function.

AnnotSV split rows and transcript/CDS fields can help identify these effects, but manual transcript review remains necessary.

.. _13-28-cnv-population-evidence:

13.28 CNV population evidence
-----------------------------

A CNV overlapping common benign population variation may receive evidence against pathogenicity.

However, comparison must consider:

-  

   .. container::

      CNV type

-  

   .. container::

      Interval overlap

-  

   .. container::

      Reciprocal overlap

-  

   .. container::

      Exact breakpoints

-  

   .. container::

      Gene content

-  

   .. container::

      Population frequency

-  

   .. container::

      Study technology

-  

   .. container::

      Population ancestry

-  

   .. container::

      Quality of the source call

A small overlap with a common CNV does not automatically make the entire patient CNV benign.

Similarly, the absence of a CNV from population databases does not automatically make it pathogenic.

.. _13-29-cnv-scoring-limitations:

13.29 CNV scoring limitations
-----------------------------

The project should not automatically classify a CNV as causal solely because it is:

-  

   .. container::

      Large

-  

   .. container::

      Rare

-  

   .. container::

      Gene-rich

-  

   .. container::

      Predicted pathogenic by ISV-CNV

-  

   .. container::

      Classified by one automated tool

-  

   .. container::

      Overlapping one disease gene

-  

   .. container::

      A high-priority CNV should ideally have several compatible evidence types, such as:

-  

   .. container::

      Correct DEL/DUP mechanism

-  

   .. container::

      Established dosage-sensitive gene or region

-  

   .. container::

      Compatible disease relationship

-  

   .. container::

      Strong phenotype match

-  

   .. container::

      Relevant coding disruption

-  

   .. container::

      Low population frequency

-  

   .. container::

      Compatible inheritance

-  

   .. container::

      Supporting clinical evidence

.. _13-30-common-cnv-workflow-failures:

13.30 Common CNV workflow failures
----------------------------------

+----------------------------------------------+------------------------------------+-----------------------------------------------+
| **Failure**                                  | **Likely cause**                   | **Required response**                         |
+==============================================+====================================+===============================================+
| Missing END                                  | Incomplete symbolic VCF record     | Reject from interval conversion               |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| Unsupported SVTYPE                           | INV, BND, INS or complex event     | Route separately                              |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| BED start equals VCF POS                     | Coordinate conversion error        | Use POS - 1                                   |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| BED start is negative                        | Invalid VCF position               | Reject the record                             |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| End exceeds chromosome length                | Wrong build or malformed endpoint  | Verify against FASTA index                    |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| DEL/DUP type missing                         | Incomplete VCF annotation          | Derive cautiously from symbolic ALT or reject |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| AnnotSV cannot find annotations              | Annotation installation incomplete | Verify Annotations_Human                      |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| AnnotSV output has many rows                 | annotationMode both                | Group full and split rows by CNV              |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| AnnotSV has no split row                     | No transcript overlap or filtering | Preserve the full CNV row                     |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| ClassifyCNV scoresheet missing               | Tool failure or invalid input      | Inspect run log and results path              |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| ClassifyCNV uses wrong build                 | Incorrect command option           | Use --GenomeBuild hg38                        |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| ISV rejects header                           | Incorrect column names             | Use required headered input                   |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| ISV output absent                            | Container or dependency problem    | Inspect container and log                     |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| Tools disagree                               | Different algorithms or evidence   | Preserve all outputs and review               |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| Copy number inferred as zero from <DEL>      | Genotype overinterpretation        | Check CN, GT and zygosity                     |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| Partial duplication treated as simple gain   | Unknown structure or orientation   | Flag for manual review                        |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| Gene overlap treated as disease confirmation | Evidence overinterpretation        | Evaluate mechanism and phenotype              |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| PGx gene overlap treated as diplotype        | Structural haplotype unresolved    | Report overlap only                           |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| VCF confidence intervals ignored             | Imprecise breakpoints              | Preserve CIPOS and CIEND                      |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| CNV absent from population data              | Novelty overinterpreted            | Do not treat absence as pathogenicity         |
+----------------------------------------------+------------------------------------+-----------------------------------------------+
| Large CNV automatically prioritised          | Size-only scoring                  | Evaluate gene content and evidence            |
+----------------------------------------------+------------------------------------+-----------------------------------------------+

.. _13-31-generate-checksums-for-cnv-outputs:

13.31 Generate checksums for CNV outputs
----------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CNV_WORK_DIR="results/tool_tests/cnv_workflow"
   CHECKSUM_FILE="$CNV_WORK_DIR/manifests/cnv_tool_outputs.sha256"
   OUTPUTS=(
   "$CNV_WORK_DIR/01.cnv_input.bed"
   "$CNV_WORK_DIR/02.AnnotSV.tsv"
   "$CNV_WORK_DIR/03.ClassifyCNV.Scoresheet.txt"
   "$CNV_WORK_DIR/04.ISV_CNV.tsv"
   )
   for path in "${OUTPUTS[@]}"; do
   if [[ ! -s "$path" ]]; then
   echo "ERROR: Required CNV output is missing:"
   echo "$path"
   exit 1
   fi
   done
   sha256sum \
   "${OUTPUTS[@]}" \
   > "$CHECKSUM_FILE"
   sha256sum \
   --check \
   "$CHECKSUM_FILE"

.. _13-32-record-tool-versions-and-commits:

13.32 Record tool versions and commits
--------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CNV_WORK_DIR="results/tool_tests/cnv_workflow"
   MANIFEST="$CNV_WORK_DIR/manifests/cnv_tool_versions.tsv"
   export ANNOTSV="$PWD/resources/annotsv_setup/AnnotSV"
   ANNOTSV_VERSION="$(
   if [[ -s resources/annotsv_setup/AnnotSV.install_version.txt ]]; then
   cat resources/annotsv_setup/AnnotSV.install_version.txt
   else
   git -C "$ANNOTSV" describe \
   --tags \
   --always \
   2>/dev/null \
   || echo "unknown"
   fi
   )"
   CLASSIFYCNV_COMMIT="$(
   git -C tools/ClassifyCNV rev-parse HEAD
   )"
   ISV_CONTAINER_SHA256="$(
   sha256sum containers/isv.sif |
   awk '{print $1}'
   )"
   ISV_PACKAGE_VERSION="$(
   apptainer exec \
   containers/isv.sif \
   python3 - <<'PY'
   from importlib.metadata import PackageNotFoundError, version
   for package_name in ("isv", "ISV"):
   try:
   print(version(package_name))
   break
   except PackageNotFoundError:
   continue
   else:
   print("unknown")
   PY
   )"
   {
   echo -e "tool\tversion_or_commit\tpath"
   printf 'AnnotSV\t%s\t%s\n' \
   "$ANNOTSV_VERSION" \
   "resources/annotsv_setup/AnnotSV"
   printf 'ClassifyCNV\t%s\t%s\n' \
   "$CLASSIFYCNV_COMMIT" \
   "tools/ClassifyCNV"
   printf 'ISV-CNV\t%s\t%s\n' \
   "$ISV_PACKAGE_VERSION" \
   "containers/isv.sif"
   printf 'ISV-container-sha256\t%s\t%s\n' \
   "$ISV_CONTAINER_SHA256" \
   "containers/isv.sif"
   } > "$MANIFEST"
   column \
   --separator $'\t' \
   --table \
   "$MANIFEST"

.. _13-33-complete-cnv-readiness-check:

13.33 Complete CNV readiness check
----------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   CNV_WORK_DIR="results/tool_tests/cnv_workflow"
   REQUIRED_FILES=(
   pipeline/case_workflow/10c_prepare_cnv_semantic_input.py
   pipeline/case_workflow/10d_add_cnv_semantic_phenotype_evidence.py
   pipeline/case_workflow/11_run_cnv_tools.sh
   pipeline/case_workflow/11b_score_universal_cnv.py
   pipeline/case_workflow/11c_add_cnv_clinpgx.py
   pipeline/case_workflow/12_score_cnv_candidates.py
   resources/annotsv_setup/AnnotSV/bin/AnnotSV
   tools/ClassifyCNV/ClassifyCNV.py
   containers/isv.sif
   "$CNV_WORK_DIR/01.cnv_input.bed"
   "$CNV_WORK_DIR/02.AnnotSV.tsv"
   "$CNV_WORK_DIR/03.ClassifyCNV.Scoresheet.txt"
   "$CNV_WORK_DIR/04.ISV_CNV.tsv"
   )
   FAILURES=0
   for path in "${REQUIRED_FILES[@]}"; do
   if [[ -s "$path" || -x "$path" ]]; then
   printf "PASS %s\n" "$path"
   else
   printf "FAIL %s\n" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo
   echo "ERROR: $FAILURES CNV component(s) are missing."
   exit 1
   fi
   bash -n \
   pipeline/case_workflow/11_run_cnv_tools.sh
   python -m py_compile \
   pipeline/case_workflow/10c_prepare_cnv_semantic_input.py \
   pipeline/case_workflow/10d_add_cnv_semantic_phenotype_evidence.py \
   pipeline/case_workflow/11b_score_universal_cnv.py \
   pipeline/case_workflow/11c_add_cnv_clinpgx.py \
   pipeline/case_workflow/12_score_cnv_candidates.py
   echo
   echo "PASS: CNV annotation and prioritisation workflow is ready."

.. _13-34-recommended-final-cnv-output-fields:

13.34 Recommended final CNV output fields
-----------------------------------------

The integrated CNV candidate table should preserve, where available:

-  

   .. container::

      case_id

-  

   .. container::

      sample_id

-  

   .. container::

      source_variant_id

-  

   .. container::

      chromosome

-  

   .. container::

      vcf_position

-  

   .. container::

      vcf_end

-  

   .. container::

      bed_start

-  

   .. container::

      bed_end

-  

   .. container::

      cnv_type

-  

   .. container::

      cnv_size

-  

   .. container::

      genotype

-  

   .. container::

      copy_number

-  

   .. container::

      breakpoint_precision

-  

   .. container::

      cytoband

-  

   .. container::

      annotation_mode

-  

   .. container::

      gene

-  

   .. container::

      gene_count

-  

   .. container::

      transcript

-  

   .. container::

      coding_overlap

-  

   .. container::

      frameshift_status

-  

   .. container::

      haploinsufficiency_evidence

-  

   .. container::

      triplosensitivity_evidence

-  

   .. container::

      g2p_disease

-  

   .. container::

      g2p_inheritance

-  

   .. container::

      g2p_mechanism

-  

   .. container::

      annotsv_ranking_score

-  

   .. container::

      annotsv_ranking_criteria

-  

   .. container::

      annotsv_acmg_class

-  

   .. container::

      classifycnv_classification

-  

   .. container::

      classifycnv_total_score

-  

   .. container::

      classifycnv_evidence

-  

   .. container::

      isv_prediction

-  

   .. container::

      isv_probability

-  

   .. container::

      isv_shap_summary

-  

   .. container::

      phenotype_score

-  

   .. container::

      semantic_phenotype_status

-  

   .. container::

      inheritance_status

-  

   .. container::

      clinpgx_overlap

-  

   .. container::

      universal_cnv_score

-  

   .. container::

      candidate_rank

-  

   .. container::

      warning

-  

   .. container::

      resource_mode

Original tool fields should remain available even when a simplified master table is generated.

.. _13-35-cnv-workflow-completion-criteria:

13.35 CNV workflow completion criteria
--------------------------------------

The CNV branch is complete when:

✓ DEL and DUP records were routed separately

✓ Unsupported structural variants were preserved and reported

✓ Every supported record contains a valid END

✓ VCF coordinates were converted correctly to BED

✓ Every interval fits within the GRCh38 reference

✓ CNV type is represented as DEL or DUP

✓ Original VCF identifiers were preserved in a manifest

✓ Rejected records were written to an explicit report

✓ AnnotSV used GRCh38 annotations

✓ AnnotSV produced full and split evidence where applicable

✓ AnnotSV rows were grouped by source CNV

✓ Cytoband, transcript and coding-overlap fields were retained

✓ ClassifyCNV produced Scoresheet.txt

✓ ClassifyCNV classification and evidence breakdown were retained

✓ ISV-CNV used a valid headered GRCh38 input

✓ ISV prediction, probability and SHAP information were retained

✓ ClinGen haploinsufficiency and triplosensitivity remained distinct

✓ CNV type was compared with the correct dosage mechanism

✓ HPO phenotype evidence was added

✓ CNV ClinPGx overlap remained separate from star-allele assignment

✓ Copy number zero was not inferred from a deletion symbol alone

✓ Breakpoint uncertainty was preserved

✓ Tool disagreement was not hidden

✓ Tool versions, commits and checksums were recorded

✓ Universal CNV scoring remained a prioritisation method

✓ Final interpretation remained subject to clinical review

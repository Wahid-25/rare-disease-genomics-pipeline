.. _14-repeat-expansion-detection-dedicated-reporting-and-unsupported-structural-var:

14. Repeat-Expansion Detection, Dedicated Reporting and Unsupported Structural-Variant Handling
===============================================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


Repeat expansions and complex structural variants cannot always be interpreted correctly by workflows designed for ordinary SNVs, indels or simple copy-number changes. The universal pipeline therefore detects these records before normalisation and routes them away from incompatible annotation branches.

The repeat and unsupported-variant route follows this structure:

Original case VCF

│

▼

Structural record inspection

│

├──────── Ordinary SNV/indel → small-variant branch

│

├──────── DEL/DUP → CNV branch

│

├──────── Repeat-expansion indicator

│ │

│ ▼

│ Dedicated repeat report

│

└──────── Unsupported or complex SV

│

▼

Explicit unsupported report

The principal project files are:

-  

   .. container::

      pipeline/case_workflow/00_detect_and_split_variants.py

-  

   .. container::

      pipeline/case_workflow/00b_report_repeat_expansions.py

-  

   .. container::

      pipeline/case_workflow/00c_build_reproducibility_manifest.py

The validated workflow detects repeat-expansion records and preserves their available information, but it does **not** perform read-level repeat-size estimation. A record requiring specialist repeat analysis is therefore reported separately and excluded from ordinary candidate ranking.

.. _14-1-why-repeat-expansions-require-a-separate-branch:

14.1 Why repeat expansions require a separate branch
----------------------------------------------------

A repeat expansion consists of repeated copies of a short sequence motif, such as:

-  

   .. container::

      CAG

-  

   .. container::

      CGG

-  

   .. container::

      GAA

-  

   .. container::

      CTG

The clinically relevant information is often not simply the presence of an alternate sequence. Interpretation may depend on:

-  repeat motif;

-  repeat count on each allele;

-  repeat-count confidence interval;

-  interruption pattern;

-  locus;

-  transcript;

-  inheritance;

-  sample type;

-  assay technology;

-  disease-specific repeat thresholds.

A large expansion may be much longer than a sequencing read and therefore cannot always be represented accurately as an ordinary literal REF/ALT sequence.

For this reason, specialist repeat callers can estimate repeat sizes from BAM or CRAM data by examining reads that span the repeat, flank it or fall within it. ExpansionHunter is one example of a read-level tool designed for this purpose.

The current project starts from a VCF. It therefore reports repeat information already present in that VCF rather than independently confirming the repeat size from sequencing reads.

.. _14-2-repeat-expansion-representation-is-not-uniform:

14.2 Repeat-expansion representation is not uniform
---------------------------------------------------

Repeat-callers do not all use the same VCF representation.

A repeat record may be represented using:

-  

   .. container::

      A symbolic ALT allele

-  

   .. container::

      A tandem-repeat symbolic subtype

-  

   .. container::

      A caller-specific INFO field

-  

   .. container::

      A caller-specific FORMAT field

-  

   .. container::

      A literal expanded sequence

-  

   .. container::

      A repeat-count genotype

-  

   .. container::

      A custom project validation symbol

Possible symbolic ALT examples include:

-  

   .. container::

      <CNV:TR>

-  

   .. container::

      <STR>

-  

   .. container::

      <REPEAT_EXPANSION>

-  

   .. container::

      <CAG_EXPANSION>

The current VCF specification includes the symbolic tandem-repeat subtype:

<CNV:TR>

and repeat-related fields such as repeat-unit sequence, repeat-unit count and count-confidence intervals. It also specifies that symbolic ALT identifiers are case-sensitive.

However, the project must continue to accept controlled older or caller-specific representations where the meaning is explicitly defined in the VCF header.

A custom allele such as:

<CAG_EXPANSION>

must not be assumed to have a universal meaning merely from its name. Its header definition and accompanying INFO or FORMAT fields must be inspected.

.. _14-3-vcf-version-compatibility:

14.3 VCF-version compatibility
------------------------------

The project’s inputs may use VCF 4.2 or another earlier VCF version, while newer VCF specifications provide more explicit tandem-repeat representations.

Therefore, the pipeline should:

1. read the declared VCF version;

2. inspect the ALT, INFO and FORMAT header definitions;

3. support known project representations;

4. avoid requiring newer fields in older files;

5. record non-standard representations;

6. preserve the original record.

In VCF 4.5, SVTYPE is deprecated in favour of deriving the structural type from the symbolic allele, but earlier VCF versions commonly use SVTYPE. The project must therefore continue to parse SVTYPE when it is present rather than assuming that every input follows the latest specification.

.. _14-4-repeat-related-fields:

14.4 Repeat-related fields
--------------------------

A repeat-expansion VCF may contain fields such as:

+-----------+-----------------------------------------------------------+
| **Field** | **Possible purpose**                                      |
+===========+===========================================================+
| REPID     | Repeat-locus identifier                                   |
+-----------+-----------------------------------------------------------+
| VARID     | Variant or catalogue identifier                           |
+-----------+-----------------------------------------------------------+
| RU        | Repeat unit                                               |
+-----------+-----------------------------------------------------------+
| RUS       | Repeat-unit sequence                                      |
+-----------+-----------------------------------------------------------+
| RUL       | Repeat-unit length                                        |
+-----------+-----------------------------------------------------------+
| RN        | Number of repeat sequences                                |
+-----------+-----------------------------------------------------------+
| RUC       | Repeat-unit count                                         |
+-----------+-----------------------------------------------------------+
| RB        | Total repeat bases                                        |
+-----------+-----------------------------------------------------------+
| CIRUC     | Confidence interval around repeat-unit count              |
+-----------+-----------------------------------------------------------+
| CIRB      | Confidence interval around repeat bases                   |
+-----------+-----------------------------------------------------------+
| REPCN     | Caller-specific repeat counts                             |
+-----------+-----------------------------------------------------------+
| REPCI     | Caller-specific repeat-count confidence intervals         |
+-----------+-----------------------------------------------------------+
| SO        | Caller-specific spanning or support observation           |
+-----------+-----------------------------------------------------------+
| ADSP      | Spanning-read support                                     |
+-----------+-----------------------------------------------------------+
| ADFL      | Flanking-read support                                     |
+-----------+-----------------------------------------------------------+
| ADIR      | In-repeat-read support                                    |
+-----------+-----------------------------------------------------------+
| GT        | Genotype                                                  |
+-----------+-----------------------------------------------------------+
| END       | Repeat-locus endpoint                                     |
+-----------+-----------------------------------------------------------+
| REF       | Reference allele or anchor base                           |
+-----------+-----------------------------------------------------------+
| ALT       | Symbolic or literal alternate allele                      |
+-----------+-----------------------------------------------------------+

Not every file contains all these fields.

The presence of a field name alone is insufficient. Its exact meaning, type, cardinality and location in INFO or FORMAT must be read from the VCF header.

.. _14-5-inspect-repeat-related-vcf-header-definitions:

14.5 Inspect repeat-related VCF header definitions
--------------------------------------------------

Choose a VCF:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="$(
   find \
   validation/universal_pipeline_testing/inputs/vcfs \
   -maxdepth 1 \
   -type f \
   \( -iname 'patient_03*.vcf' -o -iname 'patient_03*.vcf.gz' \) \
   | sort \
   | head -n 1
   )"
   if [[ -z "$VCF" ]]; then
   echo "ERROR: Patient 03 validation VCF was not found."
   exit 1
   fi
   echo "VCF: $VCF"

Inspect relevant definitions:

.. code:: bash

   bcftools view \
   --header-only \
   "$VCF" |
   grep -Ei \
   '^##(ALT|INFO|FORMAT)=.*(repeat|expansion|rep|ruc|rus|rul|repcn|repci|motif|threshold|cag|str|cnv:tr)' \
   || true

Inspect every symbolic ALT definition:

.. code:: bash

   bcftools view \
   --header-only \
   "$VCF" |
   grep '^##ALT=' \
   || true

Inspect the declared VCF version:

.. code:: bash

   bcftools view \
   --header-only \
   "$VCF" |
   head -n 1

Every INFO or FORMAT field used in a VCF should have a corresponding header definition so that parsers know its type and cardinality.

.. _14-6-inspect-the-routing-scripts:

14.6 Inspect the routing scripts
--------------------------------

Validate the project scripts:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPTS=(
   pipeline/case_workflow/00_detect_and_split_variants.py
   pipeline/case_workflow/00b_report_repeat_expansions.py
   )
   for script in "${SCRIPTS[@]}"; do
   if [[ ! -s "$script" ]]; then
   echo "ERROR: Missing script: $script"
   exit 1
   fi
   python -m py_compile "$script"
   echo "PASS: $script"
   done

Inspect their command interfaces:

.. code:: bash

   for script in "${SCRIPTS[@]}"; do
   echo
   echo "=== $script ==="
   HELP_FILE="$(
   mktemp
   )"
   if python "$script" --help \
   > "$HELP_FILE" \
   2>&1
   then
   cat "$HELP_FILE"
   else
   echo "No standard --help output was returned."
   echo "Argument definitions found in the source:"
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$script" \
   || true
   fi
   rm -f "$HELP_FILE"
   done

The complete case launcher should remain the normal way to execute these scripts. Manual commands should be constructed only from the actual interface displayed by the committed files.

.. _14-7-variant-routing-logic:

14.7 Variant-routing logic
--------------------------

The routing stage examines each record independently.

A conceptual decision process is:

Is ALT a normal nucleotide allele?

│

├─ Yes → SNV or small-indel route

│

└─ No

│

▼

Does the record represent DEL or DUP?

│

├─ Yes → CNV route

│

└─ No

│

▼

Does the record contain repeat indicators?

│

├─ Yes → repeat-expansion report

│

└─ No

│

▼

Is the record an INV, BND, INS,

translocation or another complex SV?

│

├─ Yes → unsupported-SV report

│

└─ No → unclassified-record report

The actual routing logic is defined in:

00_detect_and_split_variants.py

The Word report should describe the behaviour but should not recreate a second independent implementation.

.. _14-8-inventory-all-non-standard-records-in-a-vcf:

14.8 Inventory all non-standard records in a VCF
------------------------------------------------

The following independent inspection command lists:

-  symbolic ALT alleles;

-  breakend alleles;

-  repeat-related INFO fields;

-  repeat-related FORMAT fields;

-  possible repeat records;

-  other complex records.

It does not modify the VCF.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="$(
   find \
   validation/universal_pipeline_testing/inputs/vcfs \
   -maxdepth 1 \
   -type f \
   \( -iname 'patient_03*.vcf' -o -iname 'patient_03*.vcf.gz' \) \
   | sort \
   | head -n 1
   )"
   OUTPUT="results/tool_tests/repeat_and_unsupported_inventory.tsv"
   mkdir -p \
   "$(dirname "$OUTPUT")"
   python3 - "$VCF" "$OUTPUT" <<'PY'
   from __future__ import annotations
   import gzip
   import re
   import sys
   from pathlib import Path
   vcf_path = Path(sys.argv[1])
   output_path = Path(sys.argv[2])
   if not vcf_path.is_file():
   raise SystemExit(f"ERROR: Missing VCF: {vcf_path}")
   def open_text(path: Path):
   if path.name.endswith(".gz"):
   return gzip.open(
   path,
   mode="rt",
   encoding="utf-8",
   )
   return path.open(
   mode="r",
   encoding="utf-8",
   )
   repeat_keywords = (
   "repeat",
   "expansion",
   "cag",
   "str",
   "tandem",
   "repcn",
   "repci",
   "repid",
   "ruc",
   "rus",
   "rul",
   "motif",
   "repeat_count",
   "threshold",
   )
   repeat_tags = {
   "REPID",
   "VARID",
   "RU",
   "RUS",
   "RUL",
   "RN",
   "RUC",
   "RB",
   "CIRUC",
   "CIRB",
   "REPCN",
   "REPCI",
   }
   records: list[list[str]] = []
   sample_names: list[str] = []
   with open_text(vcf_path) as handle:
   for line_number, raw_line in enumerate(
   handle,
   start=1,
   ):
   line = raw_line.rstrip("\n")
   if line.startswith("##"):
   continue
   if line.startswith("#CHROM"):
   header = line.split("\t")
   sample_names = header[9:]
   continue
   if line.startswith("#") or not line:
   continue
   fields = line.split("\t")
   if len(fields) < 8:
   records.append(
   [
   str(line_number),
   "",
   "",
   "",
   "",
   "malformed",
   "fewer_than_eight_columns",
   "",
   "",
   ]
   )
   continue
   chromosome = fields[0]
   position = fields[1]
   variant_id = fields[2]
   reference = fields[3]
   alternate = fields[4]
   info_text = fields[7]
   info_map: dict[str, str] = {}
   for entry in info_text.split(";"):
   if "=" in entry:
   key, value = entry.split("=", 1)
   info_map[key] = value
   elif entry:
   info_map[entry] = "true"
   format_keys: list[str] = []
   sample_values: list[str] = []
   if len(fields) >= 9:
   format_keys = fields[8].split(":")
   if len(fields) >= 10:
   sample_values = fields[9].split(":")
   format_map = {
   key: (
   sample_values[index]
   if index < len(sample_values)
   else "."
   )
   for index, key in enumerate(format_keys)
   }
   symbolic = bool(
   re.search(r"<[^>]+>", alternate)
   )
   breakend = "[" in alternate or "]" in alternate
   alt_lower = alternate.lower()
   repeat_alt = any(
   keyword in alt_lower
   for keyword in repeat_keywords
   )
   repeat_info = sorted(
   key
   for key in info_map
   if (
   key.upper() in repeat_tags
   or any(
   keyword in key.lower()
   for keyword in repeat_keywords
   )
   )
   )
   repeat_format = sorted(
   key
   for key in format_map
   if (
   key.upper() in repeat_tags
   or any(
   keyword in key.lower()
   for keyword in repeat_keywords
   )
   )
   )
   svtype = info_map.get("SVTYPE", "").upper()
   if repeat_alt or repeat_info or repeat_format:
   route = "repeat_candidate"
   reason = "repeat_indicator_detected"
   elif breakend:
   route = "unsupported_structural_variant"
   reason = "breakend_notation"
   elif symbolic and svtype in {"DEL", "DUP"}:
   route = "cnv_candidate"
   reason = f"svtype_{svtype.lower()}"
   elif symbolic:
   route = "unsupported_structural_variant"
   reason = (
   f"symbolic_alt:{alternate}"
   )
   else:
   route = "small_variant_candidate"
   reason = "literal_alt_allele"
   genotype = format_map.get("GT", ".")
   records.append(
   [
   str(line_number),
   chromosome,
   position,
   variant_id,
   f"{reference}>{alternate}",
   route,
   reason,
   genotype,
   ",".join(
   repeat_info + repeat_format
   ),
   ]
   )
   output_path.parent.mkdir(
   parents=True,
   exist_ok=True,
   )
   with output_path.open(
   mode="w",
   encoding="utf-8",
   newline="",
   ) as handle:
   handle.write(
   "vcf_line\tchromosome\tposition\tvariant_id\t"
   "alleles\tsuggested_route\trouting_reason\t"
   "genotype\trepeat_fields\n"
   )
   for record in records:
   handle.write(
   "\t".join(record) + "\n"
   )
   print(f"PASS: Wrote {output_path}")
   print(f"Records inspected: {len(records)}")
   print(f"Samples: {', '.join(sample_names) or 'none'}")
   PY
   Inspect the inventory:
   column \
   --separator $'\t' \
   --table \
   "$OUTPUT" |
   head -n 40

This command is a documentation smoke test. It does not replace the production router.

.. _14-9-repeat-record-validation:

14.9 Repeat-record validation
-----------------------------

A repeat record should be reviewed for:

-  

   .. container::

      A recognisable repeat indicator

-  

   .. container::

      A valid genomic locus

-  

   .. container::

      A defined symbolic ALT allele

-  

   .. container::

      A repeat motif where available

-  

   .. container::

      A repeat count where available

-  

   .. container::

      A genotype where available

-  

   .. container::

      A confidence interval where available

-  

   .. container::

      A locus or catalogue identifier

-  

   .. container::

      A threshold source if a threshold is reported

A record may still be routed as a repeat record when some of these elements are absent. Missing elements must be reported explicitly.

.. _14-9-1-validate-symbolic-alt-definitions:

14.9.1 Validate symbolic ALT definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following command confirms that every symbolic ALT value in the body has a corresponding ALT header definition.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="$(
   find \
   validation/universal_pipeline_testing/inputs/vcfs \
   -maxdepth 1 \
   -type f \
   \( -iname 'patient_03*.vcf' -o -iname 'patient_03*.vcf.gz' \) \
   | sort \
   | head -n 1
   )"
   python3 - "$VCF" <<'PY'
   from __future__ import annotations
   import gzip
   import re
   import sys
   from pathlib import Path
   path = Path(sys.argv[1])
   def open_text(file_path: Path):
   if file_path.name.endswith(".gz"):
   return gzip.open(
   file_path,
   mode="rt",
   encoding="utf-8",
   )
   return file_path.open(
   mode="r",
   encoding="utf-8",
   )
   defined_alt_ids: set[str] = set()
   used_alt_ids: set[str] = set()
   alt_header_pattern = re.compile(
   r"^##ALT=<ID=([^,>]+)"
   )
   symbolic_pattern = re.compile(
   r"<([^>]+)>"
   )
   with open_text(path) as handle:
   for raw_line in handle:
   line = raw_line.rstrip("\n")
   header_match = alt_header_pattern.match(line)
   if header_match:
   defined_alt_ids.add(
   header_match.group(1)
   )
   continue
   if line.startswith("#"):
   continue
   fields = line.split("\t")
   if len(fields) < 5:
   continue
   for match in symbolic_pattern.finditer(
   fields[4]
   ):
   used_alt_ids.add(
   match.group(1)
   )
   missing = sorted(
   used_alt_ids - defined_alt_ids
   )
   print(
   "Defined symbolic ALT IDs:",
   ", ".join(sorted(defined_alt_ids)) or "none",
   )
   print(
   "Used symbolic ALT IDs:",
   ", ".join(sorted(used_alt_ids)) or "none",
   )
   if missing:
   print(
   "ERROR: Symbolic ALT values used without "
   "header definitions:"
   )
   for alt_id in missing:
   print(f" {alt_id}")
   raise SystemExit(1)
   print("PASS: All symbolic ALT alleles are defined.")
   PY

A custom project symbol is acceptable for controlled validation only when its meaning is documented in the VCF header.

.. _14-10-dedicated-repeat-expansion-reporting:

14.10 Dedicated repeat-expansion reporting
------------------------------------------

The reporting script is:

.. code:: bash

   pipeline/case_workflow/00b_report_repeat_expansions.py

It should produce a dedicated table rather than inserting the repeat record into the ordinary small-variant candidate list.

The report may contain:

-  

   .. container::

      case_id

-  

   .. container::

      sample_id

-  

   .. container::

      chromosome

-  

   .. container::

      position

-  

   .. container::

      end

-  

   .. container::

      record_id

-  

   .. container::

      reference

-  

   .. container::

      alternate

-  

   .. container::

      repeat_locus

-  

   .. container::

      gene

-  

   .. container::

      transcript

-  

   .. container::

      repeat_motif

-  

   .. container::

      reference_repeat_count

-  

   .. container::

      observed_repeat_count

-  

   .. container::

      repeat_count_confidence_interval

-  

   .. container::

      genotype

-  

   .. container::

      zygosity

-  

   .. container::

      threshold

-  

   .. container::

      threshold_source

-  

   .. container::

      threshold_comparison

-  

   .. container::

      detection_status

-  

   .. container::

      interpretation_status

-  

   .. container::

      specialist_analysis_required

-  

   .. container::

      warning

The exact output fields must follow the committed script.

.. _14-10-1-inspect-the-reporting-interface:

14.10.1 Inspect the reporting interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   SCRIPT="pipeline/case_workflow/00b_report_repeat_expansions.py"
   if python "$SCRIPT" --help \
   > /tmp/repeat_report_help.txt \
   2>&1
   then
   cat /tmp/repeat_report_help.txt
   else
   echo "No standard --help interface was returned."
   grep -nE \
   'ArgumentParser|add_argument|sys\.argv' \
   "$SCRIPT" \
   || true
   fi
   rm -f \
   /tmp/repeat_report_help.txt

The complete universal case launcher should invoke the script with the resolved case context and routed repeat input.

.. _14-11-repeat-interpretation-status:

14.11 Repeat interpretation status
----------------------------------

The validated pipeline uses the status:

detected_not_interpreted

This status means:

-  

   .. container::

      The record was recognised as a repeat expansion

-  

   .. container::

      The available VCF information was preserved

-  

   .. container::

      The record was written to a dedicated report

-  

   .. container::

      It was excluded from normal small-variant ranking

-  

   .. container::

      It requires specialist repeat analysis

It does **not** mean:

-  

   .. container::

      The repeat is benign

-  

   .. container::

      The repeat is pathogenic

-  

   .. container::

      The reported count has been independently confirmed

-  

   .. container::

      The patient has received a molecular diagnosis

This distinction prevents the pipeline from making a stronger claim than the input data support.

.. _14-12-repeat-count-and-confidence-interval:

14.12 Repeat count and confidence interval
------------------------------------------

A repeat caller may report two allele sizes, for example:

20/45

or:

REPCN=20/45

A confidence interval may be represented as:

19-21/42-48

The exact delimiter and field meaning are caller-specific.

The pipeline should preserve:

-  

   .. container::

      Allele 1 count

-  

   .. container::

      Allele 2 count

-  

   .. container::

      Allele 1 confidence interval

-  

   .. container::

      Allele 2 confidence interval

-  

   .. container::

      Original raw field

The raw field is essential because converting caller-specific notation into separate numerical columns can lose information.

.. _14-12-1-do-not-collapse-confidence-intervals:

14.12.1 Do not collapse confidence intervals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For example:

Observed estimate: 45

Confidence interval: 42–48

should not be reported only as:

Repeat count: 45

The interval may affect whether the estimate is clearly above, below or overlapping a locus-specific interpretation boundary.

.. _14-13-repeat-thresholds:

14.13 Repeat thresholds
-----------------------

Repeat thresholds are locus-specific and should not be applied globally.

A repeat count may fall into categories such as:

-  

   .. container::

      normal

-  

   .. container::

      intermediate

-  

   .. container::

      reduced penetrance

-  

   .. container::

      full-penetrance range

-  

   .. container::

      uncertain

The available categories differ between loci.

Threshold interpretation may also depend on:

-  repeat motif;

-  interruptions;

-  assay;

-  transcript;

-  sex;

-  inheritance;

-  laboratory reporting standards;

-  updated literature.

The pipeline should preserve a threshold only when its source is known.

A threshold written into a synthetic validation VCF is a validation expectation, not an automatically current clinical standard.

.. _14-14-patient-03-controlled-validation-route:

14.14 Patient 03 controlled validation route
--------------------------------------------

The validation suite includes a synthetic repeat-expansion case for Patient 03.

The canonical project result is:

Case:

patient_03_huntington_disease

Gene:

HTT

Variant:

chr4:3074877:N><CAG_EXPANSION>

Reported repeat count:

45 CAG repeats

Controlled threshold:

40

Genotype:

0/1

Pipeline status:

detected_not_interpreted

Ranking behaviour:

excluded from ordinary small-variant ranking

Required follow-up:

specialised repeat analysis

This case demonstrates routing behaviour. It is not a disease-specific interpretation section and should not be used as a universal threshold template.

.. _14-14-1-locate-the-patient-03-input-safely:

14.14.1 Locate the Patient 03 input safely
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   find \
   validation/universal_pipeline_testing/inputs/vcfs \
   -maxdepth 1 \
   -type f \
   \( -iname 'patient_03*.vcf' -o -iname 'patient_03*.vcf.gz' \) \
   -print

Inspect matching records:

.. code:: bash

   while IFS= read -r vcf; do
   echo
   echo "=== $vcf ==="
   bcftools query \
   --format '%CHROM\t%POS\t%ID\t%REF\t%ALT\t%INFO[\t%GT]\n' \
   "$vcf"
   done < <(
   find \
   validation/universal_pipeline_testing/inputs/vcfs \
   -maxdepth 1 \
   -type f \
   \( -iname 'patient_03*.vcf' -o -iname 'patient_03*.vcf.gz' \) \
   | sort
   )

.. _14-15-why-repeat-records-are-excluded-from-small-variant-normalisation:

14.15 Why repeat records are excluded from small-variant normalisation
----------------------------------------------------------------------

The ordinary small-variant branch uses:

-  

   .. container::

      bcftools norm

-  

   .. container::

      VEP

-  

   .. container::

      SnpEff

-  

   .. container::

      ClinVar allele matching

-  

   .. container::

      SpliceAI

A symbolic repeat expansion should not be forced through this branch because:

-  the symbolic ALT is not an ordinary nucleotide allele;

-  repeat length may not be represented literally;

-  left alignment does not provide repeat-size interpretation;

-  VEP or SnpEff consequence output would not replace repeat analysis;

-  ClinVar allele matching may require a specific repeat representation;

-  SpliceAI is not a repeat-size caller.

The original repeat record should therefore be preserved unchanged.

.. _14-15-1-confirm-repeat-records-did-not-enter-a-routed-small-variant-vcf:

14.15.1 Confirm repeat records did not enter a routed small-variant VCF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set the routed small-variant file:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SMALL_VCF="path/to/case.routed.small_variants.vcf.gz"

Check for symbolic alleles:

.. code:: bash

   if [[ ! -s "$SMALL_VCF" ]]; then
   echo "ERROR: Routed small-variant VCF is missing:"
   echo "$SMALL_VCF"
   exit 1
   fi
   SYMBOLIC_RECORDS="$(
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\n' \
   "$SMALL_VCF" |
   grep -E \
   '<[^>]+>|\[|\]' \
   || true
   )"
   if [[ -n "$SYMBOLIC_RECORDS" ]]; then
   echo "ERROR: Non-literal alleles remain in the small-variant branch:"
   echo "$SYMBOLIC_RECORDS"
   exit 1
   fi
   echo "PASS: No symbolic or breakend alleles entered the small-variant branch."

Replace the placeholder path only with the actual output created by the universal launcher.

.. _14-16-specialist-read-level-follow-up:

14.16 Specialist read-level follow-up
-------------------------------------

When a repeat-expansion record requires confirmation, a specialist workflow may need:

-  

   .. container::

      Original BAM or CRAM

-  

   .. container::

      Reference genome

-  

   .. container::

      Repeat-locus catalogue

-  

   .. container::

      Read-level repeat caller

-  

   .. container::

      Repeat-support metrics

-  

   .. container::

      Repeat-alignment visualisation

-  

   .. container::

      Orthogonal laboratory confirmation

ExpansionHunter performs targeted repeat-size estimation from BAM or CRAM reads and produces outputs that can be reviewed with supporting read information.

The current universal pipeline does not automate this stage.

The final report should therefore state:

The repeat expansion was detected from the submitted VCF.

The project did not independently estimate the repeat size

from sequencing reads.

.. _14-17-unsupported-structural-variants:

14.17 Unsupported structural variants
-------------------------------------

The pipeline may encounter structural records that are valid but not fully supported by its automated annotation routes.

+-----------------------------------------------------------------------+
| Examples include:                                                     |
+=======================================================================+
| <INV> inversion                                                       |
+-----------------------------------------------------------------------+
| <INS> symbolic insertion                                              |
+-----------------------------------------------------------------------+
| BND breakend                                                          |
+-----------------------------------------------------------------------+
| TRA translocation                                                     |
+-----------------------------------------------------------------------+
| MEI mobile-element insertion                                          |
+-----------------------------------------------------------------------+
| CTX complex translocation                                             |
+-----------------------------------------------------------------------+

-  

   .. container::

      Complex replacement

-  

   .. container::

      Chromothripsis-like events

-  

   .. container::

      Nested structural variants

-  

   .. container::

      Copy-number-neutral rearrangements

The VCF specification permits symbolic structural alleles and breakpoint notation. Breakpoint ALT alleles use square brackets to encode the mate location and orientation. Symbolic and breakpoint notations are case-sensitive.

These records should be retained and reported rather than deleted.

.. _14-18-breakend-notation:

14.18 Breakend notation
-----------------------

A breakend ALT may resemble:

-  

   .. container::

      N]chr7:140000000]

-  

   .. container::

      [chr7:140000000[N

-  

   .. container::

      N[chr7:140000000[

-  

   .. container::

      ]chr7:140000000]N

The location inside the brackets identifies a mate breakend, while the bracket arrangement represents orientation.

A single breakend record should not be interpreted independently when its mate or event structure is required.

Important fields may include:

-  

   .. container::

      MATEID

-  

   .. container::

      PARID

-  

   .. container::

      EVENT

-  

   .. container::

      CIPOS

-  

   .. container::

      CIEND

The unsupported report should preserve these values where available.

.. _14-19-inventory-unsupported-structural-records:

14.19 Inventory unsupported structural records
----------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   VCF="input/cases/case_001/original/case_001.raw.vcf"
   OUTPUT="results/tool_tests/unsupported_structural_variants.tsv"
   if [[ ! -s "$VCF" ]]; then
   echo "ERROR: VCF is missing or empty:"
   echo "$VCF"
   exit 1
   fi
   python3 - "$VCF" "$OUTPUT" <<'PY'
   from __future__ import annotations
   import gzip
   import sys
   from pathlib import Path
   vcf_path = Path(sys.argv[1])
   output_path = Path(sys.argv[2])
   def open_text(path: Path):
   if path.name.endswith(".gz"):
   return gzip.open(
   path,
   mode="rt",
   encoding="utf-8",
   )
   return path.open(
   mode="r",
   encoding="utf-8",
   )
   supported_symbols = {
   "DEL",
   "DUP",
   }
   repeat_indicators = {
   "CNV:TR",
   "STR",
   "REPEAT_EXPANSION",
   "CAG_EXPANSION",
   }
   unsupported_rows: list[list[str]] = []
   with open_text(vcf_path) as handle:
   for line_number, raw_line in enumerate(
   handle,
   start=1,
   ):
   if raw_line.startswith("#"):
   continue
   fields = raw_line.rstrip("\n").split("\t")
   if len(fields) < 8:
   continue
   chromosome = fields[0]
   position = fields[1]
   variant_id = fields[2]
   reference = fields[3]
   alternate = fields[4]
   info = fields[7]
   symbolic_ids = []
   current = ""
   inside = False
   for character in alternate:
   if character == "<":
   inside = True
   current = ""
   elif character == ">" and inside:
   inside = False
   symbolic_ids.append(current)
   current = ""
   elif inside:
   current += character
   has_breakend = (
   "[" in alternate
   or "]" in alternate
   )
   reason = ""
   if has_breakend:
   reason = "breakend_notation"
   else:
   unsupported_symbols = [
   symbol
   for symbol in symbolic_ids
   if (
   symbol not in supported_symbols
   and symbol not in repeat_indicators
   )
   ]
   if unsupported_symbols:
   reason = (
   "unsupported_symbolic_alt:"
   + ",".join(unsupported_symbols)
   )
   if not reason:
   continue
   info_map = {}
   for entry in info.split(";"):
   if "=" in entry:
   key, value = entry.split("=", 1)
   info_map[key] = value
   elif entry:
   info_map[entry] = "true"
   unsupported_rows.append(
   [
   str(line_number),
   chromosome,
   position,
   variant_id,
   reference,
   alternate,
   info_map.get("SVTYPE", "."),
   info_map.get("END", "."),
   info_map.get("MATEID", "."),
   info_map.get("EVENT", "."),
   reason,
   ]
   )
   output_path.parent.mkdir(
   parents=True,
   exist_ok=True,
   )
   with output_path.open(
   mode="w",
   encoding="utf-8",
   newline="",
   ) as handle:
   handle.write(
   "vcf_line\tchromosome\tposition\tvariant_id\t"
   "reference\talternate\tsvtype\tend\tmate_id\t"
   "event_id\tunsupported_reason\n"
   )
   for row in unsupported_rows:
   handle.write(
   "\t".join(row) + "\n"
   )
   print(f"PASS: Wrote {output_path}")
   print(f"Unsupported records: {len(unsupported_rows)}")
   PY
   Inspect:
   column \
   --separator $'\t' \
   --table \
   "$OUTPUT" |
   head -n 40

An output containing only the header means that no unsupported record was detected by this independent inspection.

.. _14-20-unsupported-reason-codes:

14.20 Unsupported reason codes
------------------------------

A useful report should provide a machine-readable reason.

Conceptual reason values include:

-  

   .. container::

      unsupported_inversion

-  

   .. container::

      unsupported_breakend

-  

   .. container::

      unsupported_translocation

-  

   .. container::

      unsupported_symbolic_insertion

-  

   .. container::

      unsupported_mobile_element

-  

   .. container::

      unsupported_complex_rearrangement

-  

   .. container::

      missing_mate_breakend

-  

   .. container::

      missing_endpoint

-  

   .. container::

      missing_structural_type

-  

   .. container::

      unrecognised_symbolic_allele

-  

   .. container::

      malformed_structural_record

-  

   .. container::

      insufficient_repeat_information

The actual project output must use the labels defined by the committed routing script.

A human-readable warning may be added separately.

.. _14-21-unsupported-does-not-mean-invalid:

14.21 Unsupported does not mean invalid
---------------------------------------

The following terms have different meanings:

Invalid:

The record is malformed or cannot be parsed.

Unsupported:

The record is valid, but the current pipeline

does not provide a complete analytical method.

Uninterpreted:

The record was detected and preserved,

but no clinical conclusion was assigned.

No evidence:

The relevant analysis was performed but

did not identify supporting evidence.

These states must not be merged into one generic value.

.. _14-22-required-unsupported-variant-report-fields:

14.22 Required unsupported-variant report fields
------------------------------------------------

The unsupported report should retain:

-  

   .. container::

      case_id

-  

   .. container::

      sample_id

-  

   .. container::

      vcf_line

-  

   .. container::

      chromosome

-  

   .. container::

      position

-  

   .. container::

      record_id

-  

   .. container::

      reference

-  

   .. container::

      alternate

-  

   .. container::

      svtype

-  

   .. container::

      end

-  

   .. container::

      mate_id

-  

   .. container::

      event_id

-  

   .. container::

      genotype

-  

   .. container::

      filter

-  

   .. container::

      routing_status

-  

   .. container::

      unsupported_reason

-  

   .. container::

      recommended_specialist_route

-  

   .. container::

      warning

It should also preserve either:

the original VCF record

or:

a traceable record key and source-file checksum

This prevents loss of the original representation.

.. _14-23-empty-repeat-and-unsupported-branches:

14.23 Empty repeat and unsupported branches
-------------------------------------------

A case may contain no repeat or unsupported records.

The workflow should still create an explicit branch status such as:

no_repeat_expansions_detected

and:

no_unsupported_structural_variants_detected

An empty branch is not a pipeline failure.

The distinction is:

No records detected:

The branch was examined successfully.

No output created:

The branch may not have run or may have failed.

.. _14-24-prevent-repeat-variants-from-entering-final-ordinary-ranking:

14.24 Prevent repeat variants from entering final ordinary ranking
------------------------------------------------------------------

After a case has completed, search its candidate tables for repeat-related records.

Set the case result directory:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CASE_RESULTS="results/cases/case_001"

Search ordinary ranking outputs:

.. code:: bash

   REPEAT_RANKING_MATCHES="$(
   grep -RInE \
   --include='*.tsv' \
   --include='*.csv' \
   --include='*.txt' \
   'CAG_EXPANSION|REPEAT_EXPANSION|CNV:TR|REPCN|repeat.expansion' \
   "$CASE_RESULTS/ranking" \
   "$CASE_RESULTS/reports" \
   2>/dev/null \
   || true
   )"
   if [[ -n "$REPEAT_RANKING_MATCHES" ]]; then
   echo "Review repeat-related records found in result tables:"
   echo "$REPEAT_RANKING_MATCHES"
   else
   echo "No repeat-related strings were found in the selected ranking paths."
   fi

A repeat may appear in a master report as a dedicated routed item. It must not appear as though it received an ordinary SNV pathogenicity score.

.. _14-25-validate-the-canonical-patient-03-audit-status:

14.25 Validate the canonical Patient 03 audit status
----------------------------------------------------

The final audit directory is:

.. code:: bash

   validation/final_audit_20260727/

Search the canonical-case manifest:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CANONICAL_CASES="validation/final_audit_20260727/canonical_cases.tsv"
   if [[ ! -s "$CANONICAL_CASES" ]]; then
   echo "ERROR: Canonical-case manifest is missing."
   exit 1
   fi
   awk \
   -F '\t' \
   '
   NR == 1 ||
   tolower($0) ~ /patient_03/ ||
   tolower($0) ~ /huntington/ ||
   tolower($0) ~ /repeat/
   ' \
   "$CANONICAL_CASES" |
   column \
   --separator $'\t' \
   --table

Search the final status document:

.. code:: bash

   grep -nEi \
   'patient.?03|repeat|HTT|CAG|detected_not_interpreted' \
   validation/final_audit_20260727/FINAL_VALIDATION_STATUS.md \
   || true

The final project audit should remain the authoritative record of whether the routed repeat case passed.

.. _14-26-reproducibility-requirements:

14.26 Reproducibility requirements
----------------------------------

For each repeat or unsupported record, the reproducibility manifest should retain:

-  

   .. container::

      Input VCF path

-  

   .. container::

      Input checksum

-  

   .. container::

      Case identifier

-  

   .. container::

      Sample identifier

-  

   .. container::

      VCF version

-  

   .. container::

      Genome build

-  

   .. container::

      Routing-script checksum

-  

   .. container::

      Reporting-script checksum

-  

   .. container::

      Detected record key

-  

   .. container::

      Detected symbolic allele

-  

   .. container::

      Repeat-related raw fields

-  

   .. container::

      Routing status

-  

   .. container::

      Interpretation status

-  

   .. container::

      Execution time

-  

   .. container::

      For repeat records, also retain:

-  

   .. container::

      Repeat motif

-  

   .. container::

      Repeat count

-  

   .. container::

      Confidence interval

-  

   .. container::

      Threshold source

-  

   .. container::

      where available.

-  

   .. container::

      For unsupported structural records, retain:

-  

   .. container::

      SV type

-  

   .. container::

      Mate identifier

-  

   .. container::

      Event identifier

-  

   .. container::

      Endpoint

-  

   .. container::

      Breakpoint confidence interval

where available.

.. _14-27-generate-checksums-for-routed-reports:

14.27 Generate checksums for routed reports
-------------------------------------------

Set the actual case paths:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   REPEAT_REPORT="path/to/repeat_expansions.tsv"
   UNSUPPORTED_REPORT="path/to/unsupported_variants.tsv"
   MANIFEST_DIR="path/to/manifests"
   mkdir -p "$MANIFEST_DIR"

Generate checksums:

.. code:: bash

   OUTPUTS=()
   if [[ -s "$REPEAT_REPORT" ]]; then
   OUTPUTS+=(
   "$REPEAT_REPORT"
   )
   fi
   if [[ -s "$UNSUPPORTED_REPORT" ]]; then
   OUTPUTS+=(
   "$UNSUPPORTED_REPORT"
   )
   fi
   if (( ${#OUTPUTS[@]} == 0 )); then
   echo "ERROR: No routed reports were found."
   exit 1
   fi
   sha256sum \
   "${OUTPUTS[@]}" \
   > "$MANIFEST_DIR/repeat_and_unsupported_outputs.sha256"
   sha256sum \
   --check \
   "$MANIFEST_DIR/repeat_and_unsupported_outputs.sha256"

Replace the placeholder paths only with the files generated by the universal case launcher.

.. _14-28-common-repeat-expansion-failures:

14.28 Common repeat-expansion failures
--------------------------------------

+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| **Failure**                                  | **Likely cause**               | **Required response**                                  |
+==============================================+================================+========================================================+
| Repeat record enters normalisation           | Routing failure                | Stop and correct the router                            |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Symbolic ALT is undefined                    | Incomplete VCF header          | Add or recover the valid definition                    |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Repeat motif is missing                      | Incomplete caller output       | Preserve the record and report missing motif           |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Repeat count is missing                      | Detection-only record          | Report count unavailable                               |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Confidence interval is discarded             | Incomplete parsing             | Retain raw and parsed intervals                        |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Two allele counts are collapsed              | Genotype parsing error         | Preserve both allele values                            |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Threshold has no source                      | Untraceable interpretation     | Do not present it as authoritative                     |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Synthetic threshold treated as universal     | Validation overinterpretation  | Restrict it to the controlled case                     |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Repeat count treated as confirmed            | No read-level analysis         | State that VCF information was reported only           |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Symbolic repeat treated as an insertion      | Incorrect routing              | Use the dedicated repeat branch                        |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Repeat excluded silently                     | Missing report                 | Produce an explicit routed output                      |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| detected_not_interpreted treated as negative | Status misunderstanding        | Explain that specialist analysis is required           |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| No repeat record found                       | Caller did not emit one        | Do not infer a normal repeat result                    |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Wrong genome build                           | Locus mismatch                 | Confirm build and repeat catalogue                     |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Interrupted repeat ignored                   | VCF lacks sequence structure   | State the limitation                                   |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Ordinary VCF caller used for expansion       | Inappropriate detection method | Use a specialist repeat-calling workflow               |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+
| Repeat count near threshold                  | Measurement uncertainty        | Review the confidence interval and specialist guidance |
+----------------------------------------------+--------------------------------+--------------------------------------------------------+

.. _14-29-common-unsupported-sv-failures:

14.29 Common unsupported-SV failures
------------------------------------

+------------------------------------------+------------------------------+-----------------------------------+
| **Failure**                              | **Likely cause**             | **Required response**             |
+==========================================+==============================+===================================+
| BND record treated as a deletion         | ALT notation ignored         | Parse breakend notation           |
+------------------------------------------+------------------------------+-----------------------------------+
| Mate breakend missing                    | Incomplete event             | Report missing mate               |
+------------------------------------------+------------------------------+-----------------------------------+
| Inversion passed to ClassifyCNV          | Unsupported CNV assumption   | Route to unsupported-SV report    |
+------------------------------------------+------------------------------+-----------------------------------+
| Symbolic insertion treated as SNV        | ALT classification failure   | Route before normalisation        |
+------------------------------------------+------------------------------+-----------------------------------+
| Event records analysed separately        | EVENT or MATEID ignored      | Preserve event grouping           |
+------------------------------------------+------------------------------+-----------------------------------+
| Breakpoint orientation lost              | ALT brackets discarded       | Retain original ALT               |
+------------------------------------------+------------------------------+-----------------------------------+
| Copy-neutral rearrangement scored as CNV | Dosage assumption            | Require copy-number evidence      |
+------------------------------------------+------------------------------+-----------------------------------+
| Complex event silently removed           | Filtering without reporting  | Produce explicit status           |
+------------------------------------------+------------------------------+-----------------------------------+
| Undefined symbolic allele accepted       | Header validation skipped    | Validate ALT definitions          |
+------------------------------------------+------------------------------+-----------------------------------+
| SVTYPE absent in newer VCF               | Parser relies only on SVTYPE | Derive from ALT where supported   |
+------------------------------------------+------------------------------+-----------------------------------+
| SVTYPE ignored in older VCF              | Parser assumes latest VCF    | Support the declared file version |
+------------------------------------------+------------------------------+-----------------------------------+
| Unsupported treated as benign            | Status overinterpretation    | Report analytical limitation      |
+------------------------------------------+------------------------------+-----------------------------------+
| Breakpoint uncertainty omitted           | CIPOS/CIEND discarded        | Preserve confidence intervals     |
+------------------------------------------+------------------------------+-----------------------------------+
| One BND used as a complete translocation | Mate/event context absent    | Require the complete event        |
+------------------------------------------+------------------------------+-----------------------------------+

.. _14-30-source-code-readiness-check:

14.30 Source-code readiness check
---------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   REQUIRED_FILES=(
   pipeline/case_workflow/00_detect_and_split_variants.py
   pipeline/case_workflow/00b_report_repeat_expansions.py
   pipeline/case_workflow/00c_build_reproducibility_manifest.py
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
   echo "ERROR: $FAILURES routing component(s) are missing."
   exit 1
   fi
   for path in "${REQUIRED_FILES[@]}"; do
   python -m py_compile "$path"
   done
   echo
   echo "PASS: Repeat and unsupported-variant source files are ready."

.. _14-31-run-the-vcf-structural-preflight-suite:

14.31 Run the VCF structural-preflight suite
--------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PREFLIGHT_SCRIPT="pipeline/tests/run_vcf_structural_preflight.sh"
   if [[ ! -s "$PREFLIGHT_SCRIPT" ]]; then
   echo "ERROR: Structural-preflight launcher is missing."
   exit 1
   fi

bash -n "$PREFLIGHT_SCRIPT"

bash "$PREFLIGHT_SCRIPT"

Inspect the manifest:

.. code:: bash

   PREFLIGHT_MANIFEST="validation/universal_pipeline_testing/manifests/vcf_preflight.tsv"
   if [[ ! -s "$PREFLIGHT_MANIFEST" ]]; then
   echo "ERROR: VCF preflight manifest is missing."
   exit 1
   fi
   column \
   --separator $'\t' \
   --table \
   "$PREFLIGHT_MANIFEST"

The validated project recorded structural-preflight success for all thirteen prepared validation VCFs. Patient 03 then followed the dedicated repeat route rather than the ordinary small-variant branch.

.. _14-32-repeat-and-unsupported-route-readiness-check:

14.32 Repeat and unsupported-route readiness check
--------------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   source .venv/bin/activate
   ROUTER="pipeline/case_workflow/00_detect_and_split_variants.py"
   REPEAT_REPORTER="pipeline/case_workflow/00b_report_repeat_expansions.py"
   PREFLIGHT="pipeline/tests/run_vcf_structural_preflight.sh"
   CANONICAL_CASES="validation/final_audit_20260727/canonical_cases.tsv"
   FINAL_STATUS="validation/final_audit_20260727/FINAL_VALIDATION_STATUS.md"
   REQUIRED_FILES=(
   "$ROUTER"
   "$REPEAT_REPORTER"
   "$PREFLIGHT"
   "$CANONICAL_CASES"
   "$FINAL_STATUS"
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
   echo "ERROR: $FAILURES required component(s) are missing."
   exit 1
   fi
   python -m py_compile \
   "$ROUTER" \
   "$REPEAT_REPORTER"

bash -n "$PREFLIGHT"

.. code:: bash

   if grep -Eqi \
   'patient.?03|HTT|CAG|repeat' \
   "$CANONICAL_CASES" \
   "$FINAL_STATUS"
   then
   echo "PASS: Canonical repeat-validation evidence was found."
   else
   echo "ERROR: Patient 03 repeat-validation evidence was not found."
   exit 1
   fi
   echo
   echo "PASS: Repeat-expansion and unsupported-SV routes are ready."

.. _14-33-final-report-wording:

14.33 Final report wording
--------------------------

A repeat finding should be reported using language such as:

A repeat-expansion record was detected in the submitted

GRCh38 VCF and was routed to the dedicated repeat report.

The pipeline preserved the reported repeat motif, count,

genotype and threshold information where available.

The record was not processed as an ordinary SNV or indel

and was excluded from the standard candidate-ranking score.

The pipeline did not independently estimate the repeat size

.. code:: bash

   from BAM or CRAM reads. Specialist repeat analysis and

appropriate confirmation are required before clinical use.

An unsupported structural variant should be reported using language such as:

A structural-variant record was detected that is outside

the automated DEL/DUP, small-variant and repeat-expansion

analysis routes.

The original record and its available breakpoint metadata

were preserved. No automated clinical classification was

assigned. A specialised structural-variant workflow is

required.

.. _14-34-completion-criteria:

14.34 Completion criteria
-------------------------

The repeat-expansion and unsupported-variant stage is complete when:

✓ The original VCF was preserved

✓ The VCF version and header definitions were inspected

✓ Symbolic ALT alleles were recognised

✓ Symbolic alleles were defined in the header

✓ Repeat-related INFO and FORMAT fields were preserved

✓ Ordinary small variants were routed separately

✓ DEL and DUP records were routed to the CNV branch

✓ Repeat-expansion records entered a dedicated report

✓ Repeat records did not enter small-variant normalisation

✓ Repeat counts and confidence intervals remained separate

✓ Thresholds retained their source

✓ Synthetic thresholds were not generalised

✓ The status detected_not_interpreted was used correctly

✓ Patient 03 followed the routed repeat path

✓ Repeat records were excluded from ordinary ranking

✓ Read-level repeat sizing was not falsely claimed

✓ Unsupported complex variants were retained

✓ Breakend ALT orientation was preserved

✓ MATEID and EVENT fields were retained where available

✓ Unsupported did not mean benign or invalid

✓ Empty routes produced explicit zero-record statuses

✓ Every routed report was checksummed

✓ Routing and reporting scripts passed syntax validation

✓ The structural-preflight suite passed

✓ Specialist follow-up requirements were documented

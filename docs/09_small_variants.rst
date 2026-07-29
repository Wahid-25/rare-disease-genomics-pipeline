.. _9-small-variant-workflow-normalisation-vep-snpeff-clinvar-and-spliceai:

9. Small-Variant Workflow: Normalisation, VEP, SnpEff, ClinVar and SpliceAI
===========================================================================


The small-variant branch processes single-nucleotide variants and short insertions or deletions that have already been separated from CNVs, repeat expansions and unsupported symbolic records.

The branch performs:

Routed small-variant VCF

│

▼

bcftools normalisation

│

▼

Ensembl VEP annotation

│

▼

SnpEff consequence annotation

│

▼

ClinVar clinical annotation

│

▼

SpliceAI splice prediction

│

▼

Structured annotation table

│

▼

Disease, phenotype, inheritance and ClinPGx analysis

The principal project scripts are:

-  

   .. container::

      pipeline/case_workflow/01_normalize_routed_small_variants.sh

-  

   .. container::

      pipeline/case_workflow/02_annotate_vep.sh

-  

   .. container::

      pipeline/case_workflow/03_annotate_snpeff.sh

-  

   .. container::

      pipeline/case_workflow/03_extract_vep_table.py

-  

   .. container::

      pipeline/case_workflow/04_add_clinvar_to_snpeff.sh

-  

   .. container::

      pipeline/case_workflow/06_add_clinvar.sh

-  

   .. container::

      pipeline/case_workflow/08_add_spliceai.sh

-  

   .. container::

      pipeline/case_workflow/09_merge_snpeff_spliceai.py

The complete production scripts should be referenced through GitHub. The commands in this section provide an independent, reproducible smoke test of the same annotation stages.

.. _9-1-purpose-of-small-variant-normalisation:

9.1 Purpose of small-variant normalisation
------------------------------------------

The same biological variant can be represented in different ways in a VCF. Before annotation, the workflow standardises the representation by:

-  checking REF alleles against GRCh38;

-  left-aligning insertions and deletions;

-  decomposing multiallelic records;

-  creating one biallelic record per alternate allele;

-  generating a compressed and indexed VCF;

-  preserving the original routed input.

bcftools norm supports reference checking, indel normalisation and splitting multiallelic sites. The project uses the strict --check-ref e behaviour so that a reference mismatch stops the process rather than being silently changed. (`pd3.github.io <https://pd3.github.io/bcftools/bcftools.html>`__)

The workflow must not use --check-ref s as a general solution for reference mismatches. That mode may swap or alter alleles and genotypes, but it does not repair every allele-dependent FORMAT field. A mismatch should first be investigated for an incorrect genome build, strand, coordinate or REF allele.

.. _9-2-prepare-an-independent-small-variant-test-workspace:

9.2 Prepare an independent small-variant test workspace
-------------------------------------------------------

The production pipeline automatically creates case-specific result directories. For a manual verification, create a separate test workspace:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   WORK_DIR="$PROJECT_ROOT/results/tool_tests/small_variant_workflow"
   mkdir -p "$WORK_DIR"
   INPUT_VCF="$PROJECT_ROOT/input/sample.small_variants.vcf"
   REFERENCE="$PROJECT_ROOT/resources/reference/hg38.fa"
   VEP_CONTAINER="$PROJECT_ROOT/containers/vep.sif"
   SNPEFF_CONTAINER="$PROJECT_ROOT/containers/snpeff.sif"
   SPLICEAI_CONTAINER="$PROJECT_ROOT/containers/spliceai.sif"
   CLINVAR="$PROJECT_ROOT/resources/clinvar/clinvar.vcf.gz"
   REQUIRED_PATHS=(
   "$INPUT_VCF"
   "$REFERENCE"
   "${REFERENCE}.fai"
   "$VEP_CONTAINER"
   "$SNPEFF_CONTAINER"
   "$SPLICEAI_CONTAINER"
   "$CLINVAR"
   "${CLINVAR}.tbi"
   )
   FAILURES=0
   for path in "${REQUIRED_PATHS[@]}"; do
   if [[ -s "$path" ]]; then
   printf "PASS %s\n" "$path"
   else
   printf "FAIL %s\n" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo "ERROR: $FAILURES required file(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: Small-variant workflow prerequisites are present."

This workspace is only for installation testing. Normal case analysis should be started through the universal pipeline launcher.

.. _9-3-inspect-the-routed-small-variant-input:

9.3 Inspect the routed small-variant input
------------------------------------------

Confirm that the file contains no symbolic CNV or repeat-expansion alleles:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   INPUT_VCF="input/sample.small_variants.vcf"
   echo "=== Sample names ==="
   bcftools query \
   --list-samples \
   "$INPUT_VCF"
   echo
   echo "=== Record count ==="
   bcftools view \
   --no-header \
   "$INPUT_VCF" |

wc -l

.. code:: bash

   echo
   echo "=== Variant alleles ==="
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\n' \
   "$INPUT_VCF" |
   head -n 20

Search for symbolic alleles:

.. code:: bash

   SYMBOLIC_RECORDS="$(
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\n' \
   "$INPUT_VCF" |
   awk '$4 ~ /^</ || $4 ~ /[\[\]]/'
   )"
   if [[ -n "$SYMBOLIC_RECORDS" ]]; then
   echo "ERROR: Symbolic or breakend records remain in the small-variant input:"
   echo "$SYMBOLIC_RECORDS"
   exit 1
   fi
   echo "PASS: No symbolic variants detected in the routed small-variant VCF."

The production routing script should perform this separation before normalisation:

pipeline/case_workflow/00_detect_and_split_variants.py

.. _9-4-normalise-the-small-variants:

9.4 Normalise the small variants
--------------------------------

Run strict GRCh38 normalisation:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   WORK_DIR="$PROJECT_ROOT/results/tool_tests/small_variant_workflow"
   INPUT_VCF="$PROJECT_ROOT/input/sample.small_variants.vcf"
   REFERENCE="$PROJECT_ROOT/resources/reference/hg38.fa"
   NORMALISED_VCF="$WORK_DIR/01.normalized.vcf.gz"
   rm -f \
   "$NORMALISED_VCF" \
   "${NORMALISED_VCF}.tbi" \
   "${NORMALISED_VCF}.csi" \
   "${NORMALISED_VCF}.tmp"
   bcftools norm \
   --fasta-ref "$REFERENCE" \
   --multiallelics -any \
   --check-ref e \
   --output-type z \
   --output "${NORMALISED_VCF}.tmp" \
   "$INPUT_VCF"
   mv \
   "${NORMALISED_VCF}.tmp" \
   "$NORMALISED_VCF"
   bcftools index \
   --tbi \
   --force \
   "$NORMALISED_VCF"

Verify the output:

.. code:: bash

   set -Eeuo pipefail
   bgzip --test "$NORMALISED_VCF"
   bcftools view \
   --header-only \
   "$NORMALISED_VCF" \
   >/dev/null
   bcftools index \
   --stats \
   "$NORMALISED_VCF"
   echo
   echo "PASS: Small-variant VCF was normalised and indexed."

.. _9-4-1-compare-input-and-normalised-record-counts:

9.4.1 Compare input and normalised record counts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The record count can increase when a multiallelic record is split into multiple biallelic records.

.. code:: bash

   INPUT_COUNT="$(
   bcftools view \
   --no-header \
   "$INPUT_VCF" |
   wc -l
   )"
   NORMALISED_COUNT="$(
   bcftools view \
   --no-header \
   "$NORMALISED_VCF" |
   wc -l
   )"
   echo "Input records: $INPUT_COUNT"
   echo "Normalised records: $NORMALISED_COUNT"

A higher normalised count is not automatically an error. It may represent successful decomposition of multiallelic sites.

.. _9-4-2-confirm-that-multiallelic-records-were-decomposed:

9.4.2 Confirm that multiallelic records were decomposed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   MULTIALLELIC_COUNT="$(
   bcftools query \
   --format '%ALT\n' \
   "$NORMALISED_VCF" |
   awk '
   index($0, ",") > 0 {
   count++
   }
   END {
   print count + 0
   }
   '
   )"
   echo "Remaining multiallelic records: $MULTIALLELIC_COUNT"
   if (( MULTIALLELIC_COUNT > 0 )); then
   echo "WARNING: Multiallelic records remain."
   else
   echo "PASS: Records are represented as biallelic variants."
   fi

.. _9-4-3-check-for-duplicate-normalised-variants:

9.4.3 Check for duplicate normalised variants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   DUPLICATE_KEYS="$(
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\n' \
   "$NORMALISED_VCF" |
   sort |
   uniq -d
   )"
   if [[ -n "$DUPLICATE_KEYS" ]]; then
   echo "WARNING: Duplicate normalised variant keys detected:"
   echo "$DUPLICATE_KEYS"
   else
   echo "PASS: No duplicate CHROM-POS-REF-ALT keys detected."
   fi

Duplicates should be reviewed before removal because two records may differ in genotype, identifier, FILTER status or supporting annotations.

.. _9-5-ensembl-vep-annotation:

9.5 Ensembl VEP annotation
--------------------------

.. _9-5-1-purpose-of-vep:

9.5.1 Purpose of VEP
~~~~~~~~~~~~~~~~~~~~

Ensembl Variant Effect Predictor evaluates each variant against genes, transcripts, regulatory features and known variation. In VCF output, VEP stores transcript-level predictions in the INFO/CSQ field. The CSQ header defines the order of pipe-delimited subfields, and multiple transcript consequences are separated by commas.

The project uses VEP in offline mode with:

-  

   .. container::

      VEP program: 115.2

-  

   .. container::

      VEP cache: homo_sapiens/115_GRCh38

-  

   .. container::

      Genome build: GRCh38

-  

   .. container::

      Reference: hg38.fa

Offline mode prevents database connections and requires a compatible local cache or annotation source. A FASTA file is required for HGVS generation and reference-sequence checking.

.. _9-5-2-vep-information-retained-by-the-project:

9.5.2 VEP information retained by the project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The workflow requests information including:

+--------------------+-------------------------------------------------+
| **Field**          | **Purpose**                                     |
+====================+=================================================+
| Consequence        | Predicted Sequence Ontology consequence         |
+--------------------+-------------------------------------------------+
| IMPACT             | VEP impact category                             |
+--------------------+-------------------------------------------------+
| SYMBOL             | Gene symbol                                     |
+--------------------+-------------------------------------------------+
| Gene               | Ensembl gene identifier                         |
+--------------------+-------------------------------------------------+
| Feature            | Transcript identifier                           |
+--------------------+-------------------------------------------------+
| BIOTYPE            | Transcript biotype                              |
+--------------------+-------------------------------------------------+
| EXON               | Exon number                                     |
+--------------------+-------------------------------------------------+
| INTRON             | Intron number                                   |
+--------------------+-------------------------------------------------+
| HGVSc              | Coding HGVS notation                            |
+--------------------+-------------------------------------------------+
| HGVSp              | Protein HGVS notation                           |
+--------------------+-------------------------------------------------+
| Protein_position   | Position in the protein                         |
+--------------------+-------------------------------------------------+
| Amino_acids        | Reference and alternate amino acids             |
+--------------------+-------------------------------------------------+
| Codons             | Reference and alternate codons                  |
+--------------------+-------------------------------------------------+
| Existing_variation | Known variant identifier                        |
+--------------------+-------------------------------------------------+
| CANONICAL          | Canonical transcript flag                       |
+--------------------+-------------------------------------------------+
| MANE_SELECT        | MANE Select transcript                          |
+--------------------+-------------------------------------------------+
| VARIANT_CLASS      | SNV, insertion, deletion or other class         |
+--------------------+-------------------------------------------------+
| gnomADe_AF         | Cached gnomAD exome frequency                   |
+--------------------+-------------------------------------------------+

The --canonical and --mane options mark canonical and MANE-associated transcripts; they do not necessarily remove other transcript consequences.

The VEP cache can provide gnomAD exome frequency fields through --af_gnomade. These cached values are useful for pipeline prioritisation, although the principal candidate should still be checked manually against the current gnomAD website when preparing a final interpretation.

.. _9-5-3-run-vep-115-2-in-offline-mode:

9.5.3 Run VEP 115.2 in offline mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   WORK_DIR="$PROJECT_ROOT/results/tool_tests/small_variant_workflow"
   NORMALISED_VCF="$WORK_DIR/01.normalized.vcf.gz"
   VEP_OUTPUT="$WORK_DIR/02.vep.vcf"
   VEP_CONTAINER="$PROJECT_ROOT/containers/vep.sif"
   rm -f \
   "$VEP_OUTPUT" \
   "${VEP_OUTPUT}.gz" \
   "${VEP_OUTPUT}.gz.tbi"
   apptainer exec \
   --bind "$PROJECT_ROOT:/project" \
   "$VEP_CONTAINER" \
   vep \
   --input_file /project/results/tool_tests/small_variant_workflow/01.normalized.vcf.gz \
   --output_file /project/results/tool_tests/small_variant_workflow/02.vep.vcf \
   --format vcf \
   --vcf \
   --species homo_sapiens \
   --assembly GRCh38 \
   --offline \
   --cache \
   --cache_version 115 \
   --dir_cache /project/resources/vep_cache \
   --fasta /project/resources/reference/hg38.fa \
   --check_ref \
   --check_existing \
   --symbol \
   --canonical \
   --mane \
   --hgvs \
   --numbers \
   --protein \
   --biotype \
   --variant_class \
   --af_gnomade \
   --force_overwrite \
   --no_stats

This command intentionally does not use --pick. Retaining all transcript consequences allows the downstream pipeline to apply its own MANE, canonical and disease-context priorities.

.. _9-5-4-compress-and-index-the-vep-result:

9.5.4 Compress and index the VEP result
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   set -Eeuo pipefail
   bgzip \
   --threads "$(nproc)" \
   --stdout \
   "$VEP_OUTPUT" \
   > "${VEP_OUTPUT}.gz.tmp"
   mv \
   "${VEP_OUTPUT}.gz.tmp" \
   "${VEP_OUTPUT}.gz"
   bcftools index \
   --tbi \
   --force \
   "${VEP_OUTPUT}.gz"

Verify the CSQ header:

.. code:: bash

   CSQ_HEADER="$(
   bcftools view \
   --header-only \
   "${VEP_OUTPUT}.gz" |
   grep '^##INFO=<ID=CSQ,' \
   || true
   )"
   if [[ -z "$CSQ_HEADER" ]]; then
   echo "ERROR: VEP CSQ header was not created."
   exit 1
   fi
   echo "$CSQ_HEADER"
   echo
   echo "PASS: VEP CSQ annotation is present."

Count records containing CSQ:

.. code:: bash

   CSQ_COUNT="$(
   bcftools query \
   --format '%INFO/CSQ\n' \
   "${VEP_OUTPUT}.gz" |
   awk '
   $0 != "." && $0 != "" {
   count++
   }
   END {
   print count + 0
   }
   '
   )"
   echo "Variants with VEP CSQ: $CSQ_COUNT"

.. _9-5-5-inspect-vep-subfields:

9.5.5 Inspect VEP subfields
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the split-vep bcftools plugin is available:

.. code:: bash

   if bcftools plugin -l |
   grep -Fxq 'split-vep'
   then
   echo "=== Available VEP CSQ fields ==="
   bcftools +split-vep \
   "${VEP_OUTPUT}.gz" \
   --list |
   head -n 40
   else
   echo "INFO: bcftools split-vep plugin is unavailable."
   echo "The CSQ format remains available in the VCF header."
   fi

The split-vep plugin can inspect and extract fields from VEP’s structured INFO/CSQ annotation.

The project converts VEP output into a structured table through:

.. code:: bash

   pipeline/case_workflow/03_extract_vep_table.py

That script should remain the authoritative production extractor because it preserves the field names expected by later pipeline stages.

.. _9-6-snpeff-consequence-annotation:

9.6 SnpEff consequence annotation
---------------------------------

.. _9-6-1-purpose-of-snpeff:

9.6.1 Purpose of SnpEff
~~~~~~~~~~~~~~~~~~~~~~~

SnpEff independently predicts the functional effect of variants on genes and transcripts. It writes its main annotation into the INFO/ANN field and records the SnpEff version and command in the VCF header.

Using both VEP and SnpEff provides:

-  two consequence-annotation sources;

-  additional transcript evidence;

-  detection of annotation disagreements;

-  richer inputs for later evidence merging.

A disagreement between VEP and SnpEff does not automatically mean that one annotation is wrong. Differences can arise from:

-  transcript sets;

-  transcript versions;

-  canonical-transcript selection;

-  annotation database releases;

-  consequence-term priorities;

-  upstream and downstream distance settings.

.. _9-6-2-confirm-the-installed-snpeff-database:

9.6.2 Confirm the installed SnpEff database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The database installed in Section 5 was:

GRCh38.99

Confirm that the database is present:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SNPEFF_DB="GRCh38.99"
   if find resources/snpeff_data \
   -type f \
   -path "*/${SNPEFF_DB}/*" |
   grep -q .
   then
   echo "PASS: SnpEff database files found for $SNPEFF_DB."
   else
   echo "ERROR: SnpEff database was not found: $SNPEFF_DB"
   exit 1
   fi

Also inspect the production script before changing the database identifier:

.. code:: bash

   grep -nE \
   'GRCh38|SNPEFF|snpEff' \
   pipeline/case_workflow/03_annotate_snpeff.sh

The database configured by the production script and the database installed under resources/snpeff_data must match.

.. _9-6-3-run-snpeff-after-vep:

9.6.3 Run SnpEff after VEP
~~~~~~~~~~~~~~~~~~~~~~~~~~

The VEP-annotated VCF is used as input so that the output retains CSQ while SnpEff adds ANN.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   WORK_DIR="$PROJECT_ROOT/results/tool_tests/small_variant_workflow"
   SNPEFF_DB="GRCh38.99"
   VEP_VCF="$WORK_DIR/02.vep.vcf.gz"
   SNPEFF_OUTPUT="$WORK_DIR/03.snpeff.vcf"
   SNPEFF_CONTAINER="$PROJECT_ROOT/containers/snpeff.sif"
   rm -f \
   "$SNPEFF_OUTPUT" \
   "${SNPEFF_OUTPUT}.gz" \
   "${SNPEFF_OUTPUT}.gz.tbi"
   apptainer exec \
   --bind "$PROJECT_ROOT:/project" \
   "$SNPEFF_CONTAINER" \
   snpEff \
   -dataDir /project/resources/snpeff_data \
   -noStats \
   "$SNPEFF_DB" \
   /project/results/tool_tests/small_variant_workflow/02.vep.vcf.gz \
   > "$SNPEFF_OUTPUT"

Compress and index:

.. code:: bash

   bgzip \
   --threads "$(nproc)" \
   --stdout \
   "$SNPEFF_OUTPUT" \
   > "${SNPEFF_OUTPUT}.gz.tmp"
   mv \
   "${SNPEFF_OUTPUT}.gz.tmp" \
   "${SNPEFF_OUTPUT}.gz"
   bcftools index \
   --tbi \
   --force \
   "${SNPEFF_OUTPUT}.gz"

.. _9-6-4-verify-that-both-vep-and-snpeff-annotations-remain-present:

9.6.4 Verify that both VEP and SnpEff annotations remain present
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   set -Eeuo pipefail
   ANNOTATED_VCF="${SNPEFF_OUTPUT}.gz"
   for info_tag in CSQ ANN; do
   if bcftools view \
   --header-only \
   "$ANNOTATED_VCF" |
   grep -q "^##INFO=<ID=${info_tag},"
   then
   echo "PASS: INFO/$info_tag is defined."
   else
   echo "ERROR: INFO/$info_tag is missing."
   exit 1
   fi
   done

Count SnpEff-annotated records:

.. code:: bash

   ANN_COUNT="$(
   bcftools query \
   --format '%INFO/ANN\n' \
   "$ANNOTATED_VCF" |
   awk '
   $0 != "." && $0 != "" {
   count++
   }
   END {
   print count + 0
   }
   '
   )"
   echo "Variants with SnpEff ANN: $ANN_COUNT"

Inspect the first annotations:

.. code:: bash

   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\t%INFO/ANN\n' \
   "$ANNOTATED_VCF" |
   head -n 5

.. _9-7-clinvar-annotation:

9.7 ClinVar annotation
----------------------

.. _9-7-1-purpose-of-clinvar:

9.7.1 Purpose of ClinVar
~~~~~~~~~~~~~~~~~~~~~~~~

ClinVar aggregates submitted relationships between genomic variants and health-related conditions. The GRCh38 VCF contains summary-level annotations for variants with precise genomic locations. It is not a complete representation of every ClinVar structural or imprecisely located variant. (`NCBI <https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/>`__)

The small-variant workflow extracts fields including:

+-------------------+----------------------------------------------------+
| **ClinVar field** | **Purpose**                                        |
+===================+====================================================+
| CLNSIG            | Submitted clinical significance                    |
+-------------------+----------------------------------------------------+
| CLNDN             | Condition or disease name                          |
+-------------------+----------------------------------------------------+
| CLNREVSTAT        | Review status                                      |
+-------------------+----------------------------------------------------+
| CLNDISDB          | External disease identifiers where available       |
+-------------------+----------------------------------------------------+
| CLNVC             | ClinVar variant class where available              |
+-------------------+----------------------------------------------------+

The three core project fields are:

-  

   .. container::

      CLNSIG

-  

   .. container::

      CLNDN

-  

   .. container::

      CLNREVSTAT

.. _9-7-2-why-normalisation-is-required-before-clinvar-matching:

9.7.2 Why normalisation is required before ClinVar matching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ClinVar annotation relies on compatible:

-  

   .. container::

      chromosome

-  

   .. container::

      position

-  

   .. container::

      reference allele

-  

   .. container::

      alternate allele

-  

   .. container::

      genome build

A biologically equivalent indel represented differently may fail to match. Normalising both the case VCF and ClinVar resource increases the reliability of allele-level matching.

The ClinVar VCF used by the project must therefore:

-  use GRCh38;

-  use the same chromosome convention;

-  be bgzip-compressed;

-  be tabix-indexed;

-  contain the required INFO definitions.

.. _9-7-3-confirm-clinvar-readiness:

9.7.3 Confirm ClinVar readiness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CLINVAR="resources/clinvar/clinvar.vcf.gz"
   bgzip --test "$CLINVAR"
   tabix --list-chroms "$CLINVAR" |

head

.. code:: bash

   for field in CLNSIG CLNDN CLNREVSTAT; do
   if bcftools view \
   --header-only \
   "$CLINVAR" |
   grep -q "^##INFO=<ID=${field},"
   then
   echo "PASS: ClinVar INFO/$field"
   else
   echo "ERROR: ClinVar field missing: $field"
   exit 1
   fi
   done

.. _9-7-4-add-clinvar-fields-with-bcftools:

9.7.4 Add ClinVar fields with bcftools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

bcftools annotate can transfer selected annotations from an indexed annotation VCF into another VCF.

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   WORK_DIR="$PROJECT_ROOT/results/tool_tests/small_variant_workflow"
   INPUT_VCF="$WORK_DIR/03.snpeff.vcf.gz"
   CLINVAR="$PROJECT_ROOT/resources/clinvar/clinvar.vcf.gz"
   OUTPUT_VCF="$WORK_DIR/04.clinvar.vcf.gz"
   rm -f \
   "$OUTPUT_VCF" \
   "${OUTPUT_VCF}.tbi" \
   "${OUTPUT_VCF}.csi" \
   "${OUTPUT_VCF}.tmp"
   bcftools annotate \
   --annotations "$CLINVAR" \
   --columns INFO/CLNSIG,INFO/CLNDN,INFO/CLNREVSTAT \
   --output-type z \
   --output "${OUTPUT_VCF}.tmp" \
   "$INPUT_VCF"
   mv \
   "${OUTPUT_VCF}.tmp" \
   "$OUTPUT_VCF"
   bcftools index \
   --tbi \
   --force \
   "$OUTPUT_VCF"

This command transfers ClinVar INFO fields without replacing the original VCF ID column. Preserving the existing ID prevents a ClinVar Variation ID from overwriting an rsID or caller-provided identifier.

.. _9-7-5-verify-clinvar-integration:

9.7.5 Verify ClinVar integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   set -Eeuo pipefail
   for field in CLNSIG CLNDN CLNREVSTAT; do
   if bcftools view \
   --header-only \
   "$OUTPUT_VCF" |
   grep -q "^##INFO=<ID=${field},"
   then
   echo "PASS: INFO/$field is present in the output."
   else
   echo "ERROR: INFO/$field was not transferred."
   exit 1
   fi
   done

Count ClinVar matches:

.. code:: bash

   CLINVAR_MATCHES="$(
   bcftools query \
   --format '%INFO/CLNSIG\n' \
   "$OUTPUT_VCF" |
   awk '
   $0 != "." && $0 != "" {
   count++
   }
   END {
   print count + 0
   }
   '
   )"
   TOTAL_VARIANTS="$(
   bcftools view \
   --no-header \
   "$OUTPUT_VCF" |
   wc -l
   )"
   echo "Total variants: $TOTAL_VARIANTS"
   echo "ClinVar matches: $CLINVAR_MATCHES"

Inspect matching variants:

.. code:: bash

   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\t%CLNSIG\t%CLNDN\t%CLNREVSTAT\n' \
   "$OUTPUT_VCF" |
   awk -F '\t' '
   $5 != "." && $5 != "" {
   print
   }
   ' |
   head -n 20

A variant without a ClinVar match is not automatically benign. It may be absent because:

-  it has never been submitted;

-  its allele representation differs;

-  the ClinVar release is older;

-  it lacks a precise VCF representation;

-  the chromosome or build does not match;

-  it is a novel variant.

.. _9-8-interpreting-clinvar-fields:

9.8 Interpreting ClinVar fields
-------------------------------

.. _9-8-1-clnsig:

9.8.1 CLNSIG
~~~~~~~~~~~~

Typical values include:

-  

   .. container::

      Pathogenic

-  

   .. container::

      Likely_pathogenic

-  

   .. container::

      Uncertain_significance

-  

   .. container::

      Likely_benign

-  

   .. container::

      Benign

-  

   .. container::

      Conflicting_classifications_of_pathogenicity

-  

   .. container::

      drug_response

-  

   .. container::

      risk_factor

A clinical-significance label must be considered with review status and disease relevance. A pathogenic classification for an unrelated condition should not automatically increase the candidate score for the patient’s phenotype.

.. _9-8-2-clndn:

9.8.2 CLNDN
~~~~~~~~~~~

CLNDN contains ClinVar condition names.

A record may include:

-  one condition;

-  multiple conditions;

-  broad phenotype terms;

-  historical disease terminology;

-  generic terms such as “not provided”.

The pipeline later harmonises these labels with Gene2Phenotype and MONDO.

.. _9-8-3-clnrevstat:

9.8.3 CLNREVSTAT
~~~~~~~~~~~~~~~~

Review status describes the level of review associated with a ClinVar assertion.

The pipeline uses it to distinguish, for example:

-  practice-guideline or expert-panel review;

-  multiple submitters with agreement;

-  single-submitter records;

-  conflicting interpretations;

-  records with limited assertion criteria.

The project script responsible for calibrating ClinVar ranking is:

pipeline/case_workflow/10b_calibrate_clinvar_ranking.py

ClinVar status contributes evidence but must not become an automatic diagnosis.

.. _9-9-spliceai-annotation:

9.9 SpliceAI annotation
-----------------------

.. _9-9-1-purpose:

9.9.1 Purpose
~~~~~~~~~~~~~

SpliceAI predicts splice-site changes produced by SNVs and selected simple indels within genes. It writes one or more pipe-delimited predictions into the INFO/SpliceAI field. Each prediction contains an allele, gene symbol, four delta scores and four relative positions.

The fields are:

+----------------+-----------------------------------------------------+
| **Field**      | **Meaning**                                         |
+================+=====================================================+
| ALLELE         | Alternate allele evaluated                          |
+----------------+-----------------------------------------------------+
| SYMBOL         | Gene symbol                                         |
+----------------+-----------------------------------------------------+
| DS_AG          | Acceptor-gain delta score                           |
+----------------+-----------------------------------------------------+
| DS_AL          | Acceptor-loss delta score                           |
+----------------+-----------------------------------------------------+
| DS_DG          | Donor-gain delta score                              |
+----------------+-----------------------------------------------------+
| DS_DL          | Donor-loss delta score                              |
+----------------+-----------------------------------------------------+
| DP_AG          | Relative acceptor-gain position                     |
+----------------+-----------------------------------------------------+
| DP_AL          | Relative acceptor-loss position                     |
+----------------+-----------------------------------------------------+
| DP_DG          | Relative donor-gain position                        |
+----------------+-----------------------------------------------------+
| DP_DL          | Relative donor-loss position                        |
+----------------+-----------------------------------------------------+

The maximum of the four delta scores ranges from 0 to 1. The developer documentation describes approximately 0.2 as a high-recall threshold, 0.5 as the general recommended threshold and 0.8 as a high-precision threshold. These values are prioritisation guides rather than standalone pathogenicity classifications.

.. _9-9-2-prepare-a-plain-vcf-for-spliceai:

9.9.2 Prepare a plain VCF for SpliceAI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Although the other tools can process compressed VCFs directly, creating a plain intermediate file gives SpliceAI a simple and predictable input.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   WORK_DIR="$PROJECT_ROOT/results/tool_tests/small_variant_workflow"
   CLINVAR_VCF="$WORK_DIR/04.clinvar.vcf.gz"
   SPLICEAI_INPUT="$WORK_DIR/04.clinvar.for_spliceai.vcf"
   bcftools view \
   --output-type v \
   --output "$SPLICEAI_INPUT" \
   "$CLINVAR_VCF"

Verify:

.. code:: bash

   bcftools view \
   --header-only \
   "$SPLICEAI_INPUT" \
   >/dev/null
   echo "PASS: Plain SpliceAI input VCF created."

.. _9-9-3-run-spliceai-against-grch38:

9.9.3 Run SpliceAI against GRCh38
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   WORK_DIR="$PROJECT_ROOT/results/tool_tests/small_variant_workflow"
   SPLICEAI_CONTAINER="$PROJECT_ROOT/containers/spliceai.sif"
   SPLICEAI_OUTPUT="$WORK_DIR/05.spliceai.vcf"
   rm -f \
   "$SPLICEAI_OUTPUT" \
   "${SPLICEAI_OUTPUT}.gz" \
   "${SPLICEAI_OUTPUT}.gz.tbi"
   apptainer exec \
   --bind "$PROJECT_ROOT:/project" \
   "$SPLICEAI_CONTAINER" \
   spliceai \
   -I /project/results/tool_tests/small_variant_workflow/04.clinvar.for_spliceai.vcf \
   -O /project/results/tool_tests/small_variant_workflow/05.spliceai.vcf \
   -R /project/resources/reference/hg38.fa \
   -A grch38 \
   -D 50 \
   -M 1

-D 50 requests predictions up to 50 bases from the variant. -M 1 enables the masking behaviour provided by the official program. SpliceAI may omit variants near chromosome ends, variants inconsistent with the FASTA or deletions longer than twice the selected distance.

.. _9-9-4-compress-and-index-the-spliceai-output:

9.9.4 Compress and index the SpliceAI output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   bgzip \
   --threads "$(nproc)" \
   --stdout \
   "$SPLICEAI_OUTPUT" \
   > "${SPLICEAI_OUTPUT}.gz.tmp"
   mv \
   "${SPLICEAI_OUTPUT}.gz.tmp" \
   "${SPLICEAI_OUTPUT}.gz"
   bcftools index \
   --tbi \
   --force \
   "${SPLICEAI_OUTPUT}.gz"

Verify the annotation:

.. code:: bash

   SPLICEAI_HEADER="$(
   bcftools view \
   --header-only \
   "${SPLICEAI_OUTPUT}.gz" |
   grep '^##INFO=<ID=SpliceAI,' \
   || true
   )"
   if [[ -z "$SPLICEAI_HEADER" ]]; then
   echo "ERROR: SpliceAI INFO definition is absent."
   exit 1
   fi
   echo "$SPLICEAI_HEADER"
   echo
   echo "PASS: SpliceAI annotation is present."

Count annotated variants:

.. code:: bash

   SPLICEAI_COUNT="$(
   bcftools query \
   --format '%INFO/SpliceAI\n' \
   "${SPLICEAI_OUTPUT}.gz" |
   awk '
   $0 != "." && $0 != "" {
   count++
   }
   END {
   print count + 0
   }
   '
   )"
   echo "Variants with SpliceAI predictions: $SPLICEAI_COUNT"

.. _9-10-confirm-that-all-annotation-layers-were-preserved:

9.10 Confirm that all annotation layers were preserved
------------------------------------------------------

The final sequential smoke-test VCF should contain:

+-----------------------------------------------------------------------+
| CSQ VEP                                                               |
+=======================================================================+
| ANN SnpEff                                                            |
+-----------------------------------------------------------------------+
| CLNSIG ClinVar                                                        |
+-----------------------------------------------------------------------+
| CLNDN ClinVar                                                         |
+-----------------------------------------------------------------------+
| CLNREVSTAT ClinVar                                                    |
+-----------------------------------------------------------------------+
| SpliceAI SpliceAI                                                     |
+-----------------------------------------------------------------------+

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   FINAL_VCF="results/tool_tests/small_variant_workflow/05.spliceai.vcf.gz"
   REQUIRED_INFO_TAGS=(
   CSQ
   ANN
   CLNSIG
   CLNDN
   CLNREVSTAT
   SpliceAI
   )
   FAILURES=0
   for tag in "${REQUIRED_INFO_TAGS[@]}"; do
   if bcftools view \
   --header-only \
   "$FINAL_VCF" |
   grep -q "^##INFO=<ID=${tag},"
   then
   printf "PASS INFO/%s\n" "$tag"
   else
   printf "FAIL INFO/%s\n" "$tag"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo "ERROR: $FAILURES required annotation field(s) are absent."
   exit 1
   fi
   echo
   echo "PASS: All small-variant annotation layers are present."

.. _9-11-confirm-that-variants-were-not-lost:

9.11 Confirm that variants were not lost
----------------------------------------

Record counts should remain stable after normalisation unless records were deliberately split. Annotation stages should not silently remove variants.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   WORK_DIR="results/tool_tests/small_variant_workflow"
   FILES=(
   "$WORK_DIR/01.normalized.vcf.gz"
   "$WORK_DIR/02.vep.vcf.gz"
   "$WORK_DIR/03.snpeff.vcf.gz"
   "$WORK_DIR/04.clinvar.vcf.gz"
   "$WORK_DIR/05.spliceai.vcf.gz"
   )
   EXPECTED_COUNT=""
   for file in "${FILES[@]}"; do
   count="$(
   bcftools view \
   --no-header \
   "$file" |
   wc -l
   )"
   printf '%-70s %s\n' "$file" "$count"
   if [[ -z "$EXPECTED_COUNT" ]]; then
   EXPECTED_COUNT="$count"
   elif [[ "$count" != "$EXPECTED_COUNT" ]]; then
   echo "ERROR: Variant count changed unexpectedly."
   exit 1
   fi
   done
   echo
   echo "PASS: Annotation stages preserved the normalised variant count."

This comparison applies only after the normalisation stage. The raw input may have a different count because multiallelic records are split.

.. _9-12-generate-a-compact-annotation-summary:

9.12 Generate a compact annotation summary
------------------------------------------

Create a simple table showing whether each record received the principal annotations:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   FINAL_VCF="results/tool_tests/small_variant_workflow/05.spliceai.vcf.gz"
   SUMMARY="results/tool_tests/small_variant_workflow/annotation_presence.tsv"
   bcftools query \
   --format '%CHROM\t%POS\t%REF\t%ALT\t%ID\t%INFO/CLNSIG\t%INFO/SpliceAI\n' \
   "$FINAL_VCF" |
   awk '
   BEGIN {
   FS = OFS = "\t"
   print \
   "chromosome", \
   "position", \
   "reference", \
   "alternate", \
   "id", \
   "clinvar_present", \
   "spliceai_present"
   }
   {
   clinvar = ($6 != "." && $6 != "") ? "yes" : "no"
   spliceai = ($7 != "." && $7 != "") ? "yes" : "no"
   print \
   $1, \
   $2, \
   $3, \
   $4, \
   $5, \
   clinvar, \
   spliceai
   }
   ' > "$SUMMARY"
   column \
   --separator $'\t' \
   --table \
   "$SUMMARY" |
   head -n 20

This is a presence summary only. The complete production tables are generated by the repository’s Python scripts.

.. _9-13-vep-and-snpeff-transcript-interpretation:

9.13 VEP and SnpEff transcript interpretation
---------------------------------------------

A single variant can overlap several transcripts and therefore receive multiple consequences.

Transcript prioritisation should consider:

1. MANE Select transcript;

2. transcript relevant to the disease mechanism;

3. canonical transcript;

4. protein-coding status;

5. exon or splice-site involvement;

6. transcript expression and clinical use;

7. consistency with the reported HGVS notation.

The most severe predicted consequence is not always the most clinically relevant consequence. VEP itself provides transcript-selection flags because consequence interpretation depends on transcript context. (Ensembl Protists)

For example, the same variant may be:

-  

   .. container::

      missense_variant in one transcript

-  

   .. container::

      intron_variant in another transcript

-  

   .. container::

      upstream_gene_variant for a neighbouring gene

The pipeline should not create three independent genomic variants from these transcript consequences. They are multiple annotations of the same CHROM-POS-REF-ALT record.

.. _9-14-key-consequence-categories:

9.14 Key consequence categories
-------------------------------

**High-impact consequences**

Examples include:

-  

   .. container::

      transcript_ablation

-  

   .. container::

      splice_acceptor_variant

-  

   .. container::

      splice_donor_variant

-  

   .. container::

      stop_gained

-  

   .. container::

      frameshift_variant

-  

   .. container::

      stop_lost

-  

   .. container::

      start_lost

These consequences may strongly affect gene function but still require review of:

-  transcript relevance;

-  inheritance;

-  allele frequency;

-  disease mechanism;

-  nonsense-mediated decay;

-  ClinVar evidence;

-  phenotype compatibility.

**Moderate-impact consequences**

Examples include:

-  

   .. container::

      missense_variant

-  

   .. container::

      inframe_insertion

-  

   .. container::

      inframe_deletion

-  

   .. container::

      protein_altering_variant

Their significance depends strongly on:

-  amino-acid position;

-  protein domain;

-  conservation;

-  population frequency;

-  functional evidence;

-  disease-associated mechanism.

**Low-impact consequences**

Examples include:

-  

   .. container::

      synonymous_variant

-  

   .. container::

      splice_region_variant

-  

   .. container::

      start_retained_variant

-  

   .. container::

      stop_retained_variant

A synonymous variant should not automatically be considered harmless because some synonymous changes can affect splicing, RNA stability or translation.

**Modifier consequences**

Examples include:

-  

   .. container::

      intron_variant

-  

   .. container::

      upstream_gene_variant

-  

   .. container::

      downstream_gene_variant

-  

   .. container::

      intergenic_variant

-  

   .. container::

      non_coding_transcript_variant

Modifier consequences usually receive lower initial priority, but may become relevant when supported by:

-  SpliceAI;

-  regulatory evidence;

-  known ClinVar classification;

-  strong phenotype association;

-  established non-coding disease mechanisms.

.. _9-15-interpreting-spliceai-output:

9.15 Interpreting SpliceAI output
---------------------------------

A SpliceAI entry may resemble:

``A|GENE1|0.01|0.02|0.78|0.04|-12|-3|5|19``

The fields represent:

ALLELE A

SYMBOL GENE1

.. code:: bash

   DS_AG 0.01
   DS_AL 0.02
   DS_DG 0.78
   DS_DL 0.04

DP_AG -12

DP_AL -3

DP_DG 5

DP_DL 19

The largest delta score is:

.. code:: bash

   DS_DG = 0.78

This predicts a potential donor-gain effect five bases downstream of the variant.

A high SpliceAI score should be interpreted with:

-  transcript structure;

-  position relative to the exon;

-  canonical splice sites;

-  RNA evidence;

-  ClinVar assertions;

-  segregation;

-  functional studies.

SpliceAI prediction alone does not prove that abnormal splicing occurs.

.. _9-16-extract-the-maximum-spliceai-delta-score:

9.16 Extract the maximum SpliceAI delta score
---------------------------------------------

The following Python block creates a compact table with the maximum delta score for each annotated variant:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   INPUT_VCF="results/tool_tests/small_variant_workflow/05.spliceai.vcf.gz"
   OUTPUT_TSV="results/tool_tests/small_variant_workflow/spliceai_max_scores.tsv"
   python3 - "$INPUT_VCF" "$OUTPUT_TSV" <<'PY'
   from __future__ import annotations
   import gzip
   import sys
   from pathlib import Path
   input_path = Path(sys.argv[1])
   output_path = Path(sys.argv[2])
   if not input_path.is_file():
   raise SystemExit(f"ERROR: Missing input VCF: {input_path}")
   open_text = gzip.open if input_path.suffix == ".gz" else open
   with open_text(
   input_path,
   mode="rt",
   encoding="utf-8",
   ) as source, output_path.open(
   mode="w",
   encoding="utf-8",
   newline="",
   ) as destination:
   destination.write(
   "chromosome\tposition\treference\talternate\t"
   "gene\tmax_delta_score\tmax_effect\n"
   )
   for raw_line in source:
   if raw_line.startswith("#"):
   continue
   fields = raw_line.rstrip("\n").split("\t")
   if len(fields) < 8:
   continue
   chromosome = fields[0]
   position = fields[1]
   reference = fields[3]
   alternate = fields[4]
   info = fields[7]
   splice_value = None
   for entry in info.split(";"):
   if entry.startswith("SpliceAI="):
   splice_value = entry.split("=", 1)[1]
   break
   if not splice_value:
   continue
   for prediction in splice_value.split(","):
   parts = prediction.split("|")
   if len(parts) < 10:
   continue
   allele = parts[0]
   gene = parts[1]
   score_names = [
   "acceptor_gain",
   "acceptor_loss",
   "donor_gain",
   "donor_loss",
   ]
   try:
   scores = [
   float(parts[2]),
   float(parts[3]),
   float(parts[4]),
   float(parts[5]),
   ]
   except ValueError:
   continue
   max_index = max(
   range(len(scores)),
   key=scores.__getitem__,
   )
   destination.write(
   f"{chromosome}\t"
   f"{position}\t"
   f"{reference}\t"
   f"{allele or alternate}\t"
   f"{gene}\t"
   f"{scores[max_index]:.4f}\t"
   f"{score_names[max_index]}\n"
   )
   print(f"PASS: Wrote {output_path}")
   PY
   Inspect:
   column \
   --separator $'\t' \
   --table \
   "$OUTPUT_TSV" |
   head -n 20

The production pipeline uses its committed parsing and merge scripts rather than this demonstration extractor.

.. _9-17-common-small-variant-workflow-failures:

9.17 Common small-variant workflow failures
-------------------------------------------

+-----------------------------------------+--------------------------------------+---------------------------------------+
| **Failure**                             | **Likely cause**                     | **Required response**                 |
+=========================================+======================================+=======================================+
| REF mismatch during normalisation       | Wrong build or REF allele            | Confirm coordinates and GRCh38 source |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| Multiallelic records remain             | Incorrect bcftools norm options      | Use --multiallelics -any              |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| VEP cannot locate cache                 | Wrong --dir_cache path               | Confirm homo_sapiens/115_GRCh38       |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| VEP cache-version error                 | Program and cache releases differ    | Use VEP 115 with cache 115            |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| VEP HGVS unavailable                    | FASTA not supplied                   | Add --fasta                           |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| Missing CSQ                             | VEP did not produce VCF output       | Confirm --vcf and output path         |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| SnpEff database not found               | Incorrect genome database identifier | Match installed database and script   |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| Missing ANN                             | SnpEff failed or output was replaced | Inspect stderr and output header      |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| No ClinVar matches                      | Build, chromosome or allele mismatch | Compare exact CHROM-POS-REF-ALT       |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| ClinVar fields absent from header       | Incorrect --columns list             | Confirm source INFO definitions       |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| SpliceAI output empty                   | FASTA or annotation incompatibility  | Check reference and input alleles     |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| Some variants lack SpliceAI             | Unsupported or out-of-scope variant  | Report as no prediction, not failure  |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| Variant count changes during annotation | Records were dropped or split        | Compare every intermediate file       |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| Existing annotations duplicated         | Input was previously annotated       | Prepare a clean derived VCF           |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| Output cannot be indexed                | Invalid sort order or compression    | Sort, bgzip and re-index              |
+-----------------------------------------+--------------------------------------+---------------------------------------+
| Tool runs but output is incomplete      | Resource or container mismatch       | Review logs and manifest              |
+-----------------------------------------+--------------------------------------+---------------------------------------+

.. _9-18-preserve-logs-for-every-annotation-stage:

9.18 Preserve logs for every annotation stage
---------------------------------------------

The production pipeline should preserve standard output and standard error separately.

A general pattern is:

.. code:: bash

   mkdir -p results/cases/case_001/logs
   command_name \
   argument1 \
   argument2 \
   > results/cases/case_001/logs/stage.stdout.log \
   2> results/cases/case_001/logs/stage.stderr.log

However, VCF-producing commands that write their output to standard output require careful redirection. For example:

.. code:: bash

   snpEff ... \
   > annotated.vcf \
   2> snpeff.stderr.log

Do not combine the VCF output and error messages into one file.

.. _9-19-record-annotation-versions:

9.19 Record annotation versions
-------------------------------

Create a local version manifest:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MANIFEST="results/tool_tests/small_variant_workflow/tool_versions.tsv"
   {
   echo -e "tool\tversion"
   printf 'bcftools\t%s\n' \
   "$(bcftools --version | head -n 1)"
   printf 'VEP\t%s\n' \
   "$(
   apptainer exec \
   containers/vep.sif \
   vep --version
   )"
   printf 'SnpEff\t%s\n' \
   "$(
   apptainer exec \
   containers/snpeff.sif \
   snpEff -version 2>&1 |
   head -n 1
   )"
   printf 'SpliceAI\t%s\n' \
   "$(
   apptainer exec \
   containers/spliceai.sif \
   python -c \
   'from importlib.metadata import version; print(version("spliceai"))'
   )"
   printf 'ClinVar downloaded\t%s\n' \
   "$(
   awk -F '\t' \
   '$1 == "downloaded_utc" {print $2}' \
   resources/clinvar/clinvar_download_metadata.tsv \
   2>/dev/null \
   || true
   )"
   } > "$MANIFEST"
   column \
   --separator $'\t' \
   --table \
   "$MANIFEST"

.. _9-20-generate-checksums-for-the-annotation-outputs:

9.20 Generate checksums for the annotation outputs
--------------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   WORK_DIR="results/tool_tests/small_variant_workflow"
   sha256sum \
   "$WORK_DIR/01.normalized.vcf.gz" \
   "$WORK_DIR/02.vep.vcf.gz" \
   "$WORK_DIR/03.snpeff.vcf.gz" \
   "$WORK_DIR/04.clinvar.vcf.gz" \
   "$WORK_DIR/05.spliceai.vcf.gz" \
   > "$WORK_DIR/small_variant_outputs.sha256"
   sha256sum \
   --check \
   "$WORK_DIR/small_variant_outputs.sha256"

These checksums allow later comparison after:

-  a tool update;

-  a resource update;

-  source-code changes;

-  a container rebuild;

-  changes to transcript databases.

.. _9-21-complete-small-variant-branch-readiness-check:

9.21 Complete small-variant branch readiness check
--------------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   FINAL_VCF="results/tool_tests/small_variant_workflow/05.spliceai.vcf.gz"
   if [[ ! -s "$FINAL_VCF" ]]; then
   echo "ERROR: Final small-variant VCF is missing."
   exit 1
   fi
   bgzip --test "$FINAL_VCF"
   bcftools index \
   --stats \
   "$FINAL_VCF" \
   >/dev/null
   REQUIRED_TAGS=(
   CSQ
   ANN
   CLNSIG
   CLNDN
   CLNREVSTAT
   SpliceAI
   )
   FAILURES=0
   for tag in "${REQUIRED_TAGS[@]}"; do
   if bcftools view \
   --header-only \
   "$FINAL_VCF" |
   grep -q "^##INFO=<ID=${tag},"
   then
   printf "PASS INFO/%s\n" "$tag"
   else
   printf "FAIL INFO/%s\n" "$tag"
   FAILURES=$((FAILURES + 1))
   fi
   done
   VARIANT_COUNT="$(
   bcftools view \
   --no-header \
   "$FINAL_VCF" |
   wc -l
   )"
   echo
   echo "Final variant count: $VARIANT_COUNT"
   if (( VARIANT_COUNT == 0 )); then
   echo "ERROR: Final VCF contains no variants."
   exit 1
   fi
   if (( FAILURES > 0 )); then
   echo "ERROR: $FAILURES required annotation field(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: Small-variant annotation workflow is ready."

.. _9-22-small-variant-workflow-completion-criteria:

9.22 Small-variant workflow completion criteria
-----------------------------------------------

The small-variant annotation branch is complete when:

✓ Only ordinary SNVs and short indels entered the branch

✓ The original routed file was preserved

✓ REF alleles were checked against GRCh38

✓ Multiallelic variants were decomposed

✓ The normalised VCF was bgzip-compressed and indexed

✓ VEP 115 used the matching release-115 GRCh38 cache

✓ VEP produced CSQ annotations

✓ VEP retained MANE and canonical transcript information

✓ Cached gnomAD exome frequencies were requested

✓ SnpEff produced ANN annotations

✓ VEP and SnpEff annotations were both preserved

✓ ClinVar fields were transferred by exact allele matching

✓ ClinVar review status was retained

✓ SpliceAI produced splice predictions where applicable

✓ Missing SpliceAI values were not treated as pipeline failures

✓ Annotation stages preserved the normalised variant count

✓ Tool versions and resource dates were recorded

✓ Intermediate and final outputs were checksummed

✓ Full production scripts remained available through GitHub

The annotated small-variant data can now proceed to gene–disease mapping, ClinPGx matching, phenotype comparison, inheritance assessment and candidate scoring.

.. _5-reference-genome-annotation-resources-and-specialised-tool-installation:

5. Reference Genome, Annotation Resources and Specialised Tool Installation
===========================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


The pipeline depends on large reference files that are deliberately excluded from GitHub. They must be downloaded into the expected local directories after cloning the repository.

The validated project uses:

Reference assembly: GRCh38

Chromosome convention: chr1–chr22, chrX, chrY and chrM

VEP software: 115.2

VEP cache: release 115, GRCh38

HPO release: 2026-02-16

MONDO release: 2026-07-06

The commands below are designed to stop immediately if a download, checksum, extraction or verification step fails.

.. _5-1-prepare-the-resource-directories:

5.1 Prepare the resource directories
------------------------------------

Open Ubuntu Bash and run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   mkdir -p \
   "$PROJECT_ROOT/containers" \
   "$PROJECT_ROOT/resources/reference" \
   "$PROJECT_ROOT/resources/vep_cache" \
   "$PROJECT_ROOT/resources/snpeff_data" \
   "$PROJECT_ROOT/resources/clinvar" \
   "$PROJECT_ROOT/resources/clingen" \
   "$PROJECT_ROOT/resources/gene_disease/g2p" \
   "$PROJECT_ROOT/resources/phenotype/hpo" \
   "$PROJECT_ROOT/resources/disease_ontology/mondo" \
   "$PROJECT_ROOT/resources/clinpgx" \
   "$PROJECT_ROOT/results/environment"
   echo "Project root: $PROJECT_ROOT"
   df -h "$PROJECT_ROOT"

Before downloading the full resource collection, approximately 100–150 GB of free space should be available. The VEP cache, reference genome, structural-variant annotation databases and temporary extraction files account for most of the storage.

.. _5-2-download-the-grch38-reference-genome:

5.2 Download the GRCh38 reference genome
----------------------------------------

.. _5-2-1-purpose-of-the-reference-fasta:

5.2.1 Purpose of the reference FASTA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The reference FASTA is required for:

-  REF-allele validation;

-  left alignment of insertions and deletions;

-  VCF normalisation;

-  SpliceAI analysis;

-  VEP HGVS generation;

-  optional read alignment;

-  chromosome sequence lookup.

The UCSC GRCh38.p14 FASTA is suitable for this project because it uses chr-prefixed chromosome names. UCSC provides the compressed FASTA and an accompanying MD5 checksum file in its official GRCh38 download directory.

.. _5-2-2-download-and-verify-grch38:

5.2.2 Download and verify GRCh38
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   REF_DIR="$PWD/resources/reference"
   REF_URL="https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/p14/hg38.p14.fa.gz"
   MD5_URL="https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/p14/md5sum.txt"
   mkdir -p "$REF_DIR"
   cd "$REF_DIR"
   curl \
   --fail \
   --location \
   --retry 5 \
   --retry-delay 5 \
   --continue-at - \
   --output hg38.p14.fa.gz \
   "$REF_URL"
   curl \
   --fail \
   --location \
   --retry 5 \
   --output md5sum.ucsc.txt \
   "$MD5_URL"
   EXPECTED_LINE="$(
   grep -E '(^|[[:space:]])hg38\.p14\.fa\.gz$' \
   md5sum.ucsc.txt
   )"
   if [[ -z "$EXPECTED_LINE" ]]; then
   echo "ERROR: hg38.p14.fa.gz checksum was not found."
   exit 1
   fi
   printf '%s\n' "$EXPECTED_LINE" |

md5sum --check -

.. code:: bash

   echo "PASS: UCSC reference checksum verified."

Do not rename or decompress the file until the checksum passes.

.. _5-2-3-decompress-the-fasta-safely:

5.2.3 Decompress the FASTA safely
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   REF_DIR="$PWD/resources/reference"
   if [[ ! -s "$REF_DIR/hg38.p14.fa.gz" ]]; then
   echo "ERROR: Compressed GRCh38 FASTA is missing."
   exit 1
   fi
   pigz \
   --decompress \
   --stdout \
   "$REF_DIR/hg38.p14.fa.gz" \
   > "$REF_DIR/hg38.fa.tmp"
   if [[ ! -s "$REF_DIR/hg38.fa.tmp" ]]; then
   echo "ERROR: FASTA decompression produced an empty file."
   rm -f "$REF_DIR/hg38.fa.tmp"
   exit 1
   fi
   mv \
   "$REF_DIR/hg38.fa.tmp" \
   "$REF_DIR/hg38.fa"
   echo "PASS: FASTA created at:"
   echo "$REF_DIR/hg38.fa"

The compressed archive may be retained as a backup or deleted after successful indexing when disk space is limited.

.. _5-2-4-index-the-reference-genome:

5.2.4 Index the reference genome
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   REF="resources/reference/hg38.fa"
   samtools faidx "$REF"
   if [[ ! -s "${REF}.fai" ]]; then
   echo "ERROR: FASTA index was not created."
   exit 1
   fi
   echo "PASS: FASTA index created."

The index contains the chromosome names and chromosome lengths.

.. _5-2-5-verify-chromosome-naming:

5.2.5 Verify chromosome naming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   FAI="resources/reference/hg38.fa.fai"
   REQUIRED_CONTIGS=(
   chr1
   chr2
   chr3
   chr4
   chr5
   chr6
   chr7
   chr8
   chr9
   chr10
   chr11
   chr12
   chr13
   chr14
   chr15
   chr16
   chr17
   chr18
   chr19
   chr20
   chr21
   chr22
   chrX
   chrY
   chrM
   )
   FAILURES=0
   for contig in "${REQUIRED_CONTIGS[@]}"; do
   if cut -f1 "$FAI" | grep -Fxq "$contig"; then
   printf "PASS %s\n" "$contig"
   else
   printf "FAIL %s not found\n" "$contig"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo "ERROR: Required chromosomes are missing."
   exit 1
   fi
   echo
   echo "PASS: All required chromosomes use the chr-prefixed convention."

Check the first few records:

.. code:: bash

   head resources/reference/hg38.fa.fai

.. _5-2-6-record-the-reference-checksum:

5.2.6 Record the reference checksum
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sha256sum \
   resources/reference/hg38.fa \
   resources/reference/hg38.fa.fai \
   > resources/reference/hg38.sha256
   cat resources/reference/hg38.sha256

This local checksum allows future analyses to confirm that the same reference file is being used.

.. _5-3-build-the-repository-container-definitions:

5.3 Build the repository container definitions
----------------------------------------------

The repository contains definition files for the core tools, SnpEff, ISV-CNV and optional read processing. The built .sif files are excluded from GitHub.

.. _5-3-1-validate-the-definition-files:

5.3.1 Validate the definition files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   for definition in containers/*.def; do
   [[ -f "$definition" ]] || continue
   echo "Found: $definition"
   done

Expected files include:

-  

   .. container::

      containers/core_tools.def

-  

   .. container::

      containers/snpeff.def

-  

   .. container::

      containers/isv.def

-  

   .. container::

      containers/read_processing.def

.. _5-3-2-build-the-core-tools-container:

5.3.2 Build the core-tools container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sudo -E apptainer build \
   --force \
   containers/core_tools.sif \
   containers/core_tools.def

Verify:

.. code:: bash

   apptainer exec \
   containers/core_tools.sif \
   bcftools --version |
   head -n 1
   apptainer exec \
   containers/core_tools.sif \
   samtools --version |
   head -n 1

.. _5-3-3-build-the-snpeff-container:

5.3.3 Build the SnpEff container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sudo -E apptainer build \
   --force \
   containers/snpeff.sif \
   containers/snpeff.def

Verify:

.. code:: bash

   apptainer exec \
   containers/snpeff.sif \
   snpEff -version

.. _5-3-4-build-the-isv-cnv-container:

5.3.4 Build the ISV-CNV container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sudo -E apptainer build \
   --force \
   containers/isv.sif \
   containers/isv.def

Verify that Python is available:

.. code:: bash

   apptainer exec \
   containers/isv.sif \
   python3 --version

.. _5-3-5-build-the-optional-read-processing-container:

5.3.5 Build the optional read-processing container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sudo -E apptainer build \
   --force \
   containers/read_processing.sif \
   containers/read_processing.def

This container is required only for the optional FASTQ and alignment branch.

.. _5-3-6-record-container-checksums:

5.3.6 Record container checksums
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sha256sum containers/*.sif \
   > containers/container_images.sha256
   cat containers/container_images.sha256

.. _5-4-install-ensembl-vep-115-2:

5.4 Install Ensembl VEP 115.2
-----------------------------

The project was validated with VEP 115.2. Ensembl publishes an official container tag named release_115.2; its official image is available for both AMD64 and ARM64 platforms.

VEP itself and its cache must be kept on the same major release. The project therefore uses:

VEP program: 115.2

VEP cache: 115_GRCh38

.. _5-4-1-pull-the-official-vep-container:

5.4.1 Pull the official VEP container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   apptainer pull \
   --force \
   containers/vep.sif \
   docker://ensemblorg/ensembl-vep:release_115.2

Verify the container:

.. code:: bash

   apptainer exec \
   containers/vep.sif \
   vep --help \
   >/dev/null
   echo "PASS: VEP executable is available."

Check the version:

.. code:: bash

   apptainer exec \
   containers/vep.sif \
   vep --version

VEP can also be installed from its official GitHub source using INSTALL.pl, but the official versioned container provides the most direct match to this project. (`GitHub <https://github.com/ensembl/ensembl-vep>`__)

.. _5-5-download-the-vep-115-grch38-cache:

5.5 Download the VEP 115 GRCh38 cache
-------------------------------------

VEP caches contain transcript models and additional annotation data for a particular species, assembly and Ensembl release. Ensembl supports manual cache installation by downloading and extracting the appropriate archive into the cache directory. (Ensembl)

.. _5-5-1-download-the-indexed-cache:

5.5.1 Download the indexed cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CACHE_DIR="$PWD/resources/vep_cache"
   CACHE_ARCHIVE="$CACHE_DIR/homo_sapiens_vep_115_GRCh38.tar.gz"
   CACHE_URL="https://ftp.ensembl.org/pub/release-115/variation/indexed_vep_cache/homo_sapiens_vep_115_GRCh38.tar.gz"
   mkdir -p "$CACHE_DIR"
   curl \
   --fail \
   --location \
   --retry 5 \
   --retry-delay 10 \
   --continue-at - \
   --output "$CACHE_ARCHIVE" \
   "$CACHE_URL"

Confirm that the archive exists:

.. code:: bash

   test -s \
   resources/vep_cache/homo_sapiens_vep_115_GRCh38.tar.gz
   ls -lh \
   resources/vep_cache/homo_sapiens_vep_115_GRCh38.tar.gz

.. _5-5-2-test-the-archive-before-extraction:

5.5.2 Test the archive before extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   tar \
   --list \
   --file resources/vep_cache/homo_sapiens_vep_115_GRCh38.tar.gz \
   >/dev/null
   echo "PASS: VEP cache archive is readable."

.. _5-5-3-extract-the-cache:

5.5.3 Extract the cache
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CACHE_DIR="$PWD/resources/vep_cache"
   CACHE_ARCHIVE="$CACHE_DIR/homo_sapiens_vep_115_GRCh38.tar.gz"
   tar \
   --extract \
   --gzip \
   --file "$CACHE_ARCHIVE" \
   --directory "$CACHE_DIR"

Verify the expected cache path:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   EXPECTED_CACHE="resources/vep_cache/homo_sapiens/115_GRCh38"
   if [[ ! -d "$EXPECTED_CACHE" ]]; then
   echo "ERROR: Expected VEP cache directory was not created:"
   echo "$EXPECTED_CACHE"
   exit 1
   fi
   echo "PASS: VEP cache installed at:"
   echo "$EXPECTED_CACHE"

Record the archive checksum:

.. code:: bash

   sha256sum \
   resources/vep_cache/homo_sapiens_vep_115_GRCh38.tar.gz \
   > resources/vep_cache/homo_sapiens_vep_115_GRCh38.tar.gz.sha256

The archive may be removed after successful extraction to recover disk space:

.. code:: bash

   rm \
   resources/vep_cache/homo_sapiens_vep_115_GRCh38.tar.gz

Keep its checksum and release metadata even when the archive is deleted.

.. _5-6-test-vep-in-offline-mode:

5.6 Test VEP in offline mode
----------------------------

The official VEP documentation supports --cache and --offline operation with a locally mounted cache directory. (Ensembl

Run a controlled test using the included example VCF:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   mkdir -p results/environment
   apptainer exec \
   --bind "$PWD:/project" \
   containers/vep.sif \
   vep \
   --input_file /project/input/sample.small_variants.vcf \
   --output_file /project/results/environment/vep_test.vcf \
   --format vcf \
   --vcf \
   --offline \
   --cache \
   --cache_version 115 \
   --dir_cache /project/resources/vep_cache \
   --species homo_sapiens \
   --assembly GRCh38 \
   --fasta /project/resources/reference/hg38.fa \
   --symbol \
   --canonical \
   --mane \
   --hgvs \
   --force_overwrite \
   --no_stats

Confirm that VEP created an output:

.. code:: bash

   test -s results/environment/vep_test.vcf
   grep '^##VEP=' \
   results/environment/vep_test.vcf |
   head -n 1
   grep -v '^#' \
   results/environment/vep_test.vcf |
   head -n 3

Successful execution confirms that:

-  the VEP container works;

-  the cache is visible;

-  the reference FASTA is accessible;

-  the sample VCF is readable;

-  offline annotation can be performed.

.. _5-7-install-the-snpeff-grch38-database:

5.7 Install the SnpEff GRCh38 database
--------------------------------------

SnpEff predicts sequence consequences using a genome-specific annotation database. The database is stored separately from the container so that it can be versioned and replaced independently.

The exact database name used by the pipeline should be checked inside the current pipeline script:

.. code:: bash

   cd ~/rare_disease_project
   grep -R \
   --line-number \
   --extended-regexp \
   'GRCh38|SnpEff|snpEff' \
   pipeline/case_workflow/03_annotate_snpeff.sh

For the validated workflow, use the database identifier written in that script. A commonly used SnpEff human database identifier is GRCh38.99; the script remains the authoritative source for this project.

Set it explicitly:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SNPEFF_DATABASE="GRCh38.99"
   SNPEFF_DATA="$PWD/resources/snpeff_data"
   mkdir -p "$SNPEFF_DATA"

Download through the container:

.. code:: bash

   apptainer exec \
   --bind "$PWD:/project" \
   containers/snpeff.sif \
   snpEff \
   download \
   -v \
   -dataDir /project/resources/snpeff_data \
   "$SNPEFF_DATABASE"

Verify that files were created:

.. code:: bash

   find \
   resources/snpeff_data \
   -maxdepth 3 \
   -type f |

head

Test the database:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   apptainer exec \
   --bind "$PWD:/project" \
   containers/snpeff.sif \
   snpEff \
   -dataDir /project/resources/snpeff_data \
   GRCh38.99 \
   /project/input/sample.small_variants.vcf \
   > results/environment/snpeff_test.vcf

Confirm:

.. code:: bash

   test -s results/environment/snpeff_test.vcf
   grep '^##SnpEffVersion' \
   results/environment/snpeff_test.vcf |
   head -n 1

.. _5-8-download-and-prepare-clinvar:

5.8 Download and prepare ClinVar
--------------------------------

ClinVar distributes GRCh38 VCF files through its official FTP service. These files contain variants with precise genomic locations and summary-level ClinVar annotations. ClinVar’s VCF does not represent every structural or imprecisely located variant, so it is used primarily for the small-variant branch.

ClinVar data are updated regularly. For exact reproducibility, the downloaded file should be accompanied by its date and checksum.

.. _5-8-1-download-the-current-grch38-clinvar-vcf:

5.8.1 Download the current GRCh38 ClinVar VCF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download the source file separately before chromosome harmonisation:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CLINVAR_DIR="$PWD/resources/clinvar"
   mkdir -p "$CLINVAR_DIR"
   cd "$CLINVAR_DIR"
   curl \
   --fail \
   --location \
   --retry 5 \
   --retry-delay 5 \
   --continue-at - \
   --output clinvar.source.GRCh38.vcf.gz \
   "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz"
   curl \
   --fail \
   --location \
   --retry 5 \
   --output clinvar.source.GRCh38.vcf.gz.tbi \
   "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz.tbi"

Validate the compressed file:

.. code:: bash

   bgzip --test \
   clinvar.source.GRCh38.vcf.gz
   tabix --list-chroms \
   clinvar.source.GRCh38.vcf.gz |

head

.. _5-8-2-harmonise-clinvar-chromosome-names:

5.8.2 Harmonise ClinVar chromosome names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The repository contains:

.. code:: bash

   resources/clinvar/chr_map.txt

This file maps source chromosome names to the chr-prefixed convention required by the project.

Run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SOURCE="resources/clinvar/clinvar.source.GRCh38.vcf.gz"
   OUTPUT="resources/clinvar/clinvar.vcf.gz"
   MAP="resources/clinvar/chr_map.txt"
   if [[ ! -s "$SOURCE" ]]; then
   echo "ERROR: ClinVar source VCF is missing."
   exit 1
   fi
   if [[ ! -s "$MAP" ]]; then
   echo "ERROR: Chromosome mapping file is missing."
   exit 1
   fi
   bcftools annotate \
   --rename-chrs "$MAP" \
   --output-type z \
   --output "$OUTPUT.tmp" \
   "$SOURCE"
   mv \
   "$OUTPUT.tmp" \
   "$OUTPUT"
   tabix \
   --force \
   --preset vcf \
   "$OUTPUT"

Verify:

.. code:: bash

   bcftools query \
   --format '%CHROM\n' \
   resources/clinvar/clinvar.vcf.gz |

head

.. code:: bash

   tabix --list-chroms \
   resources/clinvar/clinvar.vcf.gz |

head

The main chromosomes should appear as:

.. code:: bash

   chr1
   chr2
   chr3

...

.. code:: bash

   chrX
   chrY

.. _5-8-3-verify-required-clinvar-info-fields:

5.8.3 Verify required ClinVar INFO fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CLINVAR="resources/clinvar/clinvar.vcf.gz"
   REQUIRED_FIELDS=(
   CLNSIG
   CLNDN
   CLNREVSTAT
   )
   for field in "${REQUIRED_FIELDS[@]}"; do
   if bcftools view --header-only "$CLINVAR" |
   grep -q "ID=${field},"; then
   echo "PASS: $field"
   else
   echo "FAIL: $field is missing."
   exit 1
   fi
   done

Record the download date and checksum:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   {
   echo -e "field\tvalue"
   echo -e "assembly\tGRCh38"
   echo -e "downloaded_utc\t$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
   echo -e "source_file\tclinvar.source.GRCh38.vcf.gz"
   echo -e "pipeline_file\tclinvar.vcf.gz"
   echo -e "source_url\thttps://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz"
   } > resources/clinvar/clinvar_download_metadata.tsv
   sha256sum \
   resources/clinvar/clinvar.source.GRCh38.vcf.gz \
   resources/clinvar/clinvar.vcf.gz \
   resources/clinvar/clinvar.vcf.gz.tbi \
   > resources/clinvar/clinvar.sha256

.. _5-9-clingen-dosage-sensitivity-resource:

5.9 ClinGen dosage-sensitivity resource
---------------------------------------

The repository already contains the compact ClinGen dosage file:

.. code:: bash

   resources/clingen/clingen_dosage_genes_regions.csv

ClinGen dosage curation is used to evaluate whether loss or gain of a gene or region is associated with disease. It is particularly relevant to deletion and duplication interpretation. ClinGen maintains formal dosage-sensitivity curation procedures and periodically updates its downloadable resources. (ClinGen)

Because the validated file is already committed to GitHub, exact project reproduction should initially use that version rather than silently replacing it with a newer release.

Verify the file:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CLINGEN_FILE="resources/clingen/clingen_dosage_genes_regions.csv"
   if [[ ! -s "$CLINGEN_FILE" ]]; then
   echo "ERROR: ClinGen dosage file is missing."
   exit 1
   fi
   echo "Rows:"

wc -l "$CLINGEN_FILE"

.. code:: bash

   echo
   echo "Header:"
   head -n 1 "$CLINGEN_FILE"

Record its checksum:

.. code:: bash

   sha256sum \
   resources/clingen/clingen_dosage_genes_regions.csv \
   > resources/clingen/clingen_dosage_genes_regions.csv.sha256

A future ClinGen update should be treated as a deliberate resource-version change and followed by complete regression testing.

.. _5-10-download-gene2phenotype:

5.10 Download Gene2Phenotype
----------------------------

Gene2Phenotype provides gene–disease models containing attributes such as allelic requirement, molecular mechanism, variant consequence and evidence level. Its official API supports downloading all panels as a CSV file.

The project separates:

-  

   .. container::

      AllG2P.official.csv

-  

   .. container::

      AllG2P.local_validation.csv

-  

   .. container::

      AllG2P.validation.csv

The official file is used in production mode. Local validation entries are permitted only in validation mode.

.. _5-10-1-preserve-the-committed-official-version:

5.10.1 Preserve the committed official version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For exact reproduction of the validated project, first verify the committed file:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   G2P_DIR="resources/gene_disease/g2p"
   G2P_FILE="$G2P_DIR/AllG2P.official.csv"
   if [[ ! -s "$G2P_FILE" ]]; then
   echo "ERROR: Committed G2P resource is missing."
   exit 1
   fi
   echo "Rows:"

wc -l "$G2P_FILE"

.. code:: bash

   echo
   echo "Header:"
   head -n 1 "$G2P_FILE"

.. _5-10-2-refresh-g2p-only-when-deliberately-updating-resources:

5.10.2 Refresh G2P only when deliberately updating resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use a temporary file so a failed download cannot overwrite the working resource:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   G2P_DIR="$PWD/resources/gene_disease/g2p"
   TEMP_FILE="$G2P_DIR/AllG2P.official.download.tmp.csv"
   FINAL_FILE="$G2P_DIR/AllG2P.official.csv"
   curl \
   --fail \
   --location \
   --retry 5 \
   --retry-delay 5 \
   --output "$TEMP_FILE" \
   "https://www.ebi.ac.uk/gene2phenotype/api/panel/all/download"

Validate the CSV:

.. code:: bash

   python3 - "$TEMP_FILE" <<'PY'
   import csv
   import sys
   from pathlib import Path
   path = Path(sys.argv[1])
   if not path.is_file() or path.stat().st_size == 0:
   raise SystemExit("ERROR: G2P download is missing or empty.")
   with path.open(newline="", encoding="utf-8-sig") as handle:
   reader = csv.reader(handle)
   rows = list(reader)
   if len(rows) < 2:
   raise SystemExit("ERROR: G2P download contains no data rows.")
   if len(rows[0]) < 5:
   raise SystemExit("ERROR: G2P header has too few columns.")
   print(f"PASS: {len(rows) - 1} G2P records detected.")
   print("Header:", rows[0])
   PY
   Replace the official file only after validation:
   mv \
   "$TEMP_FILE" \
   "$FINAL_FILE"
   sha256sum \
   "$FINAL_FILE" \
   > "$FINAL_FILE.sha256"

Record the retrieval metadata:

.. code:: bash

   cat > "$G2P_DIR/AllG2P.download.metadata.tsv" <<EOF
   field value
   downloaded_utc $(date -u '+%Y-%m-%dT%H:%M:%SZ')
   endpoint https://www.ebi.ac.uk/gene2phenotype/api/panel/all/download
   resource_mode official
   file AllG2P.official.csv
   EOF

After refreshing G2P, rebuild the validation resource using the project script rather than manually editing the official file:

.. code:: bash

   python3 \
   pipeline/case_workflow/00b_refresh_combined_g2p.py \
   --help

The exact command-line arguments should follow the script’s displayed help and the production/validation mode selected for the analysis.

.. _5-11-install-the-human-phenotype-ontology-release:

5.11 Install the Human Phenotype Ontology release
-------------------------------------------------

HPO provides both the ontology structure and disease annotations. Its downloadable annotation products include phenotype.hpoa, genes_to_phenotype.txt, phenotype_to_genes.txt and genes_to_disease.txt.

The project uses the pinned release:

v2026-02-16

That release provides versioned downloadable assets and published checksums for several files.

.. _5-11-1-download-the-pinned-hpo-files:

5.11.1 Download the pinned HPO files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   HPO_VERSION="v2026-02-16"
   HPO_RELEASE_DIR="$PWD/resources/phenotype/hpo/v2026-02-16"
   HPO_BASE_URL="https://github.com/obophenotype/human-phenotype-ontology/releases/download/${HPO_VERSION}"
   mkdir -p "$HPO_RELEASE_DIR"
   FILES=(
   hp.obo
   phenotype.hpoa
   genes_to_disease.txt
   genes_to_phenotype.txt
   phenotype_to_genes.txt
   )
   for filename in "${FILES[@]}"; do
   echo "Downloading $filename"
   curl \
   --fail \
   --location \
   --retry 5 \
   --retry-delay 5 \
   --output "$HPO_RELEASE_DIR/${filename}.tmp" \
   "$HPO_BASE_URL/$filename"
   if [[ ! -s "$HPO_RELEASE_DIR/${filename}.tmp" ]]; then
   echo "ERROR: Empty HPO file: $filename"
   exit 1
   fi
   mv \
   "$HPO_RELEASE_DIR/${filename}.tmp" \
   "$HPO_RELEASE_DIR/$filename"
   done

.. _5-11-2-verify-the-two-published-release-checksums:

5.11.2 Verify the two published release checksums
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The official release lists these checksums:

genes_to_disease.txt

364429870dd8326c5d293eeec31c3f1c89351c8d63a9d66c294b171966fa8b60

genes_to_phenotype.txt

25d3e5a40203cbb4cc027747c70fcb5431bcfb26283479608a97f3d810285c7d

Verify:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   HPO_DIR="resources/phenotype/hpo/v2026-02-16"
   cat > "$HPO_DIR/official_checksums.sha256" <<'EOF'
   364429870dd8326c5d293eeec31c3f1c89351c8d63a9d66c294b171966fa8b60 genes_to_disease.txt
   25d3e5a40203cbb4cc027747c70fcb5431bcfb26283479608a97f3d810285c7d genes_to_phenotype.txt
   EOF
   (
   cd "$HPO_DIR"
   sha256sum --check official_checksums.sha256
   )

Expected:

genes_to_disease.txt: OK

genes_to_phenotype.txt: OK

Generate checksums for all downloaded HPO files:

.. code:: bash

   cd "$HPO_DIR"
   sha256sum \
   hp.obo \
   phenotype.hpoa \
   genes_to_disease.txt \
   genes_to_phenotype.txt \
   phenotype_to_genes.txt \
   > release_files.sha256

.. _5-11-3-update-the-active-hpo-symbolic-link:

5.11.3 Update the active HPO symbolic link
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   HPO_ROOT="$PWD/resources/phenotype/hpo"
   ln \
   --symbolic \
   --force \
   --no-dereference \
   v2026-02-16 \
   "$HPO_ROOT/current"
   readlink \
   "$HPO_ROOT/current"

Expected:

v2026-02-16

.. _5-11-4-build-the-hpo-semantic-cache:

5.11.4 Build the HPO semantic cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inspect the script’s accepted arguments first:

.. code:: bash

   python3 \
   pipeline/resource_setup/build_hpo_semantic_cache.py \
   --help

Then run it using the paths defined by its help output. A typical invocation is:

.. code:: bash

   python3 \
   pipeline/resource_setup/build_hpo_semantic_cache.py \
   --hpo-obo resources/phenotype/hpo/current/hp.obo \
   --phenotype-annotations resources/phenotype/hpo/current/phenotype.hpoa \
   --output resources/phenotype/hpo/current/hpo_semantic.sqlite

Because argument names are controlled by the repository script, the --help output must be treated as authoritative. Do not guess different argument names if the script displays another interface.

Verify the database:

.. code:: bash

   test -s \
   resources/phenotype/hpo/current/hpo_semantic.sqlite
   sqlite3 \
   resources/phenotype/hpo/current/hpo_semantic.sqlite \
   '.tables'

.. _5-12-install-the-mondo-disease-ontology:

5.12 Install the MONDO disease ontology
---------------------------------------

MONDO harmonises disease names and identifiers across multiple biomedical resources. The official project distributes MONDO in OWL, OBO and JSON formats.

The validated project records:

MONDO release: 2026-07-06

.. _5-12-1-download-the-pinned-obo-release:

5.12.1 Download the pinned OBO release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MONDO_VERSION="v2026-07-06"
   MONDO_DIR="$PWD/resources/disease_ontology/mondo/v2026-07-06"
   MONDO_URL="https://github.com/monarch-initiative/mondo/releases/download/${MONDO_VERSION}/mondo.obo"
   mkdir -p "$MONDO_DIR"
   curl \
   --fail \
   --location \
   --retry 5 \
   --retry-delay 5 \
   --output "$MONDO_DIR/mondo.obo.tmp" \
   "$MONDO_URL"
   if [[ ! -s "$MONDO_DIR/mondo.obo.tmp" ]]; then
   echo "ERROR: MONDO download is empty."
   exit 1
   fi
   mv \
   "$MONDO_DIR/mondo.obo.tmp" \
   "$MONDO_DIR/mondo.obo"

Check that it is an ontology file:

.. code:: bash

   grep -m 1 '^format-version:' \
   resources/disease_ontology/mondo/v2026-07-06/mondo.obo
   grep -m 1 '^ontology:' \
   resources/disease_ontology/mondo/v2026-07-06/mondo.obo

Record the checksum:

.. code:: bash

   sha256sum \
   resources/disease_ontology/mondo/v2026-07-06/mondo.obo \
   > resources/disease_ontology/mondo/v2026-07-06/mondo.obo.sha256

Update the active symbolic link:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MONDO_ROOT="$PWD/resources/disease_ontology/mondo"
   ln \
   --symbolic \
   --force \
   --no-dereference \
   v2026-07-06 \
   "$MONDO_ROOT/current"

readlink "$MONDO_ROOT/current"

.. _5-12-2-build-the-mondo-crosswalk:

5.12.2 Build the MONDO crosswalk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inspect the script interface:

.. code:: bash

   python3 \
   pipeline/resource_setup/build_mondo_crosswalk.py \
   --help

A typical invocation is:

.. code:: bash

   python3 \
   pipeline/resource_setup/build_mondo_crosswalk.py \
   --mondo-obo resources/disease_ontology/mondo/current/mondo.obo \
   --output resources/disease_ontology/mondo/current/mondo_crosswalk.sqlite

Verify:

.. code:: bash

   test -s \
   resources/disease_ontology/mondo/current/mondo_crosswalk.sqlite
   sqlite3 \
   resources/disease_ontology/mondo/current/mondo_crosswalk.sqlite \
   '.tables'

Again, the script’s actual --help output takes precedence over the example argument names.

.. _5-13-configure-and-test-clinpgx:

5.13 Configure and test ClinPGx
-------------------------------

ClinPGx provides pharmacogenomic genes, variants, clinical annotations, dosing guidelines and related reference objects through a REST API. The active API hostname is api.clinpgx.org; the older PharmGKB API hostname was scheduled to be discontinued in July 2026. ClinPGx also asks automated clients to limit requests to two per second.

The project avoids repeated online requests by using:

-  a small locally curated reference;

-  cached API responses;

-  an API-access metadata table;

-  allele-aware matching.

.. _5-13-1-verify-the-local-curated-reference:

5.13.1 Verify the local curated reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PGX_FILE="resources/clinpgx/local_curated_pgx_reference.csv"
   PGX_HASH="resources/clinpgx/local_curated_pgx_reference.sha256"
   if [[ ! -s "$PGX_FILE" ]]; then
   echo "ERROR: Local ClinPGx reference is missing."
   exit 1
   fi
   if [[ ! -s "$PGX_HASH" ]]; then
   echo "ERROR: ClinPGx checksum file is missing."
   exit 1
   fi
   sha256sum \
   --check \
   "$PGX_HASH"

Inspect the structure:

.. code:: bash

   head -n 5 \
   resources/clinpgx/local_curated_pgx_reference.csv
   cat \
   resources/clinpgx/LOCAL_REFERENCE_SCHEMA.txt

.. _5-13-2-test-the-clinpgx-api:

5.13.2 Test the ClinPGx API
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Activate the project virtual environment:

.. code:: bash

   cd ~/rare_disease_project
   source .venv/bin/activate

Run the committed test script:

.. code:: bash

   python \
   pipeline/setup_resources/02_test_clinpgx_api.py

Inspect the resulting metadata:

.. code:: bash

   column \
   --separator $'\t' \
   --table \
   resources/clinpgx/metadata/clinpgx_api_test.tsv

A successful test should report:

status: success

records: at least 1

api_base: https://api.clinpgx.org/v1

The cache files should appear under:

.. code:: bash

   find \
   resources/clinpgx/cache \
   -type f \
   -maxdepth 3 |

sort

.. _5-14-run-the-core-resource-readiness-check:

5.14 Run the core-resource readiness check
------------------------------------------

After completing the previous installations, run:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail

declare -A REQUIRED_PATHS=(

["GRCh38 FASTA"]="resources/reference/hg38.fa"

["GRCh38 FASTA index"]="resources/reference/hg38.fa.fai"

["VEP container"]="containers/vep.sif"

["VEP cache"]="resources/vep_cache/homo_sapiens/115_GRCh38"

["SnpEff container"]="containers/snpeff.sif"

["SnpEff data"]="resources/snpeff_data"

["Core tools container"]="containers/core_tools.sif"

["ISV container"]="containers/isv.sif"

["ClinVar VCF"]="resources/clinvar/clinvar.vcf.gz"

["ClinVar index"]="resources/clinvar/clinvar.vcf.gz.tbi"

["ClinGen dosage"]="resources/clingen/clingen_dosage_genes_regions.csv"

["G2P official"]="resources/gene_disease/g2p/AllG2P.official.csv"

["G2P validation"]="resources/gene_disease/g2p/AllG2P.validation.csv"

["HPO active release"]="resources/phenotype/hpo/current"

["MONDO active release"]="resources/disease_ontology/mondo/current"

["ClinPGx reference"]="resources/clinpgx/local_curated_pgx_reference.csv"

.. code:: bash

   )
   FAILURES=0
   for label in "${!REQUIRED_PATHS[@]}"; do
   path="${REQUIRED_PATHS[$label]}"
   if [[ -e "$path" || -L "$path" ]]; then
   printf "PASS %-24s %s\n" "$label" "$path"
   else
   printf "FAIL %-24s %s\n" "$label" "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   echo
   if (( FAILURES > 0 )); then
   echo "Core resource check failed: $FAILURES item(s) missing."
   exit 1
   fi
   echo "PASS: All core reference and annotation resources are present."

.. _5-15-record-the-complete-resource-inventory:

5.15 Record the complete resource inventory
-------------------------------------------

Create a local manifest:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   mkdir -p results/environment
   MANIFEST="results/environment/core_resource_inventory.tsv"
   {
   echo -e "resource\tpath\tsize_bytes\tmodified_utc"
   PATHS=(
   resources/reference/hg38.fa
   resources/reference/hg38.fa.fai
   containers/core_tools.sif
   containers/vep.sif
   containers/snpeff.sif
   containers/isv.sif
   resources/clinvar/clinvar.vcf.gz
   resources/clinvar/clinvar.vcf.gz.tbi
   resources/clingen/clingen_dosage_genes_regions.csv
   resources/gene_disease/g2p/AllG2P.official.csv
   resources/gene_disease/g2p/AllG2P.validation.csv
   resources/clinpgx/local_curated_pgx_reference.csv
   )
   for path in "${PATHS[@]}"; do
   if [[ -f "$path" ]]; then
   printf '%s\t%s\t%s\t%s\n' \
   "$(basename "$path")" \
   "$path" \
   "$(stat -c '%s' "$path")" \
   "$(date -u -d "@$(stat -c '%Y' "$path")" '+%Y-%m-%dT%H:%M:%SZ')"
   fi
   done
   } > "$MANIFEST"
   column \
   --separator $'\t' \
   --table \
   "$MANIFEST"

The manifest remains local because complete resource paths and installed binary files are not stored in GitHub.

At this stage, the reference genome, VEP, SnpEff, ClinVar, ClinGen, Gene2Phenotype, HPO, MONDO and ClinPGx resources are prepared.

.. _6-specialised-tool-installation-spliceai-annotsv-classifycnv-isv-cnv-and-optiona:

6. Specialised Tool Installation: SpliceAI, AnnotSV, ClassifyCNV, ISV-CNV and Optional InterVar
===============================================================================================

.. note::

   This page is a web-formatted transcription of the corresponding section in ``genomics_pipeline.docx``. Commands and paths are preserved from the source manuscript and should be verified against the final repository state before execution.


**6. Specialised Tool Installation: SpliceAI, AnnotSV, ClassifyCNV, ISV-CNV and Optional InterVar**

This section installs the specialised tools used after the core reference and annotation resources have been prepared.

The automated pipeline uses:

SpliceAI Splice-effect prediction for SNVs and small indels

AnnotSV Structural-variant and CNV annotation

ClassifyCNV Evidence-based DEL/DUP scoring and classification

ISV-CNV Machine-learning-assisted CNV pathogenicity prediction

InterVar is optional and is used only as an additional manual ACMG-supporting source. It is not required for the universal pipeline to complete.

All commands in this section must be run in **Ubuntu Bash** from:

.. code:: bash

   ~/rare_disease_project

.. _6-1-prepare-specialised-tool-directories:

6.1 Prepare specialised-tool directories
----------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   mkdir -p \
   "$PROJECT_ROOT/containers" \
   "$PROJECT_ROOT/tools" \
   "$PROJECT_ROOT/resources/annotsv_setup" \
   "$PROJECT_ROOT/results/environment" \
   "$PROJECT_ROOT/results/tool_tests"
   echo "Project root: $PROJECT_ROOT"
   df -h "$PROJECT_ROOT"

Confirm that the core dependencies are present:

.. code:: bash

   set -Eeuo pipefail
   REQUIRED_COMMANDS=(
   git
   curl
   wget
   make
   python3
   bcftools
   bedtools
   apptainer
   )
   FAILURES=0
   for command_name in "${REQUIRED_COMMANDS[@]}"; do
   if command -v "$command_name" >/dev/null 2>&1; then
   printf "PASS %-12s %s\n" \
   "$command_name" \
   "$(command -v "$command_name")"
   else
   printf "FAIL %-12s not found\n" \
   "$command_name"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo "ERROR: $FAILURES required command(s) are missing."
   exit 1
   fi
   echo
   echo "PASS: Specialised-tool prerequisites are available."

.. _6-2-spliceai:

6.2 SpliceAI
------------

.. _6-2-1-purpose:

6.2.1 Purpose
~~~~~~~~~~~~~

SpliceAI predicts whether a sequence variant may create or disrupt splice acceptor or donor sites. Its VCF annotation contains four delta scores and four corresponding relative positions:

-  

   .. container::

      DS_AG acceptor gain score

-  

   .. container::

      DS_AL acceptor loss score

-  

   .. container::

      DS_DG donor gain score

-  

   .. container::

      DS_DL donor loss score

-  

   .. container::

      DP_AG acceptor gain position

-  

   .. container::

      DP_AL acceptor loss position

-  

   .. container::

      DP_DG donor gain position

-  

   .. container::

      DP_DL donor loss position

SpliceAI supports SNVs and selected simple indels located within genes represented by its annotation file. The official command accepts an input VCF, output VCF, reference FASTA and either a custom annotation file or the built-in grch37/grch38 annotation.

The official repository became read-only in April 2026. Its current repository notice also places restrictions on commercial use of the source and trained models, so licensing must be reviewed before non-academic deployment.

.. _6-2-2-build-a-reproducible-spliceai-container:

6.2.2 Build a reproducible SpliceAI container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The official installation supports pip install spliceai or installation through Bioconda. The project uses a separate container to avoid mixing TensorFlow and Keras dependencies with the main Python environment.

Create the definition file:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   cat > containers/spliceai.def <<'EOF'
   Bootstrap: docker
   From: python:3.10-slim-bookworm
   %labels
   Tool SpliceAI
   ToolVersion 1.3.1
   GenomeBuild GRCh38
   Purpose "Splice-effect prediction"
   %post
   set -eux
   apt-get update
   DEBIAN_FRONTEND=noninteractive apt-get install -y \
   --no-install-recommends \
   ca-certificates \
   gcc \
   g++ \
   libhdf5-dev \
   zlib1g-dev
   python -m pip install \
   --no-cache-dir \
   --upgrade \
   pip \
   setuptools \
   wheel
   python -m pip install \
   --no-cache-dir \
   "numpy<2" \
   "tensorflow-cpu==2.15.1" \
   "spliceai==1.3.1"
   python -m pip check
   spliceai --help >/dev/null
   apt-get clean
   rm -rf /var/lib/apt/lists/*
   %environment
   export TF_CPP_MIN_LOG_LEVEL=2
   %runscript
   exec spliceai "$@"
   EOF

The latest PyPI release of SpliceAI remains version 1.3.1. The TensorFlow and NumPy versions above are explicit project dependency pins; they are added for container reproducibility rather than being required verbatim by the original SpliceAI documentation.

Build the container:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   if [[ "$(uname -m)" != "x86_64" ]]; then
   echo "WARNING: This definition was prepared for x86_64 WSL/Linux."
   echo "Architecture detected: $(uname -m)"
   fi
   sudo -E apptainer build \
   --force \
   containers/spliceai.sif \
   containers/spliceai.def

.. _6-2-3-verify-spliceai:

6.2.3 Verify SpliceAI
~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   apptainer exec \
   containers/spliceai.sif \
   python - <<'PY'
   from importlib.metadata import version
   print("SpliceAI:", version("spliceai"))
   print("TensorFlow:", version("tensorflow-cpu"))
   PY
   apptainer run \
   containers/spliceai.sif \
   --help \
   >/dev/null
   echo "PASS: SpliceAI container is operational."

Record the checksum:

.. code:: bash

   sha256sum \
   containers/spliceai.sif \
   > containers/spliceai.sif.sha256

.. _6-2-4-run-a-grch38-smoke-test:

6.2.4 Run a GRCh38 smoke test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   INPUT_VCF="input/sample.small_variants.vcf"
   OUTPUT_VCF="results/tool_tests/spliceai_test.vcf"
   REFERENCE="resources/reference/hg38.fa"
   if [[ ! -s "$INPUT_VCF" ]]; then
   echo "ERROR: Test VCF is missing: $INPUT_VCF"
   exit 1
   fi
   if [[ ! -s "$REFERENCE" ]]; then
   echo "ERROR: GRCh38 FASTA is missing: $REFERENCE"
   exit 1
   fi
   apptainer exec \
   --bind "$PWD:/project" \
   containers/spliceai.sif \
   spliceai \
   -I "/project/$INPUT_VCF" \
   -O "/project/$OUTPUT_VCF" \
   -R "/project/$REFERENCE" \
   -A grch38 \
   -D 50 \
   -M 1

For variant interpretation, the official SpliceAI documentation recommends masked scores, represented by -M 1; raw scores may be preferable when investigating alternative splicing more broadly.

Verify the output:

.. code:: bash

   set -Eeuo pipefail
   test -s results/tool_tests/spliceai_test.vcf
   bcftools view \
   --header-only \
   results/tool_tests/spliceai_test.vcf |
   grep -F 'ID=SpliceAI' \
   >/dev/null
   echo "PASS: SpliceAI test output was created."
   grep -v '^#' \
   results/tool_tests/spliceai_test.vcf |
   head -n 3

A variant may remain without a SpliceAI score when it lies outside the supplied gene annotation, near a chromosome end, contains an unsupported deletion length or does not match the reference FASTA.

.. _6-3-annotsv:

6.3 AnnotSV
-----------

.. _6-3-1-purpose:

6.3.1 Purpose
~~~~~~~~~~~~~

AnnotSV annotates and ranks structural variants, including deletions and duplications. It can report:

-  variant type and size;

-  cytoband;

-  affected genes and transcripts;

-  exon and coding-sequence overlap;

-  dosage-sensitive genes and regions;

-  known pathogenic or benign CNV overlaps;

-  regulatory regions;

-  population CNV evidence;

-  ranking and classification fields.

The validated project used AnnotSV 3.5.10.

The official installation method consists of cloning the source, running make PREFIX=. install, and downloading human annotations with make PREFIX=. install-human-annotation.

.. _6-3-2-install-additional-annotsv-prerequisites:

6.3.2 Install additional AnnotSV prerequisites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   set -Eeuo pipefail
   sudo apt-get update
   sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
   tcl \
   tk \
   make \
   git \
   curl \
   wget \
   unzip \
   gzip \
   tar \
   bcftools \
   bedtools \
   python3 \
   default-jre-headless

Verify:

tclsh <<< 'puts [info patchlevel]'

.. code:: bash

   bedtools --version
   bcftools --version | head -n 1
   java -version 2>&1 | head -n 1

.. _6-3-3-confirm-that-the-required-annotsv-version-exists:

6.3.3 Confirm that the required AnnotSV version exists
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   ANNOTSV_TAG="v3.5.10"
   ANNOTSV_REPOSITORY="https://github.com/lgmgeo/AnnotSV.git"
   if git ls-remote \
   --exit-code \
   --tags \
   "$ANNOTSV_REPOSITORY" \
   "refs/tags/$ANNOTSV_TAG" \
   >/dev/null 2>&1
   then
   echo "PASS: AnnotSV tag found: $ANNOTSV_TAG"
   else
   echo "ERROR: AnnotSV tag was not found: $ANNOTSV_TAG"
   echo "Do not silently install another version."
   exit 1
   fi

This check prevents the installation command from silently falling back to a different AnnotSV release.

.. _6-3-4-install-annotsv-and-its-human-annotation-resources:

6.3.4 Install AnnotSV and its human annotation resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   ANNOTSV_ROOT="$PWD/resources/annotsv_setup/AnnotSV"
   ANNOTSV_TAG="v3.5.10"
   if [[ -e "$ANNOTSV_ROOT" ]]; then
   echo "ERROR: AnnotSV installation path already exists:"
   echo "$ANNOTSV_ROOT"
   echo "Move or archive it before reinstalling."
   exit 1
   fi
   git clone \
   --branch "$ANNOTSV_TAG" \
   --depth 1 \
   https://github.com/lgmgeo/AnnotSV.git \
   "$ANNOTSV_ROOT"
   cd "$ANNOTSV_ROOT"

make PREFIX=. install

make PREFIX=. install-human-annotation

The human annotation installation can take considerable time and disk space because multiple external genomic resources are downloaded. The official quick-start distinguishes installation of the software from installation of the human and mouse annotation datasets.

.. _6-3-5-configure-the-annotsv-environment-variable:

6.3.5 Configure the AnnotSV environment variable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   ANNOTSV_PATH="$PWD/resources/annotsv_setup/AnnotSV"
   grep -qxF \
   "export ANNOTSV=\"$ANNOTSV_PATH\"" \
   "$HOME/.bashrc" ||
   printf 'export ANNOTSV="%s"\n' \
   "$ANNOTSV_PATH" \
   >> "$HOME/.bashrc"
   export ANNOTSV="$ANNOTSV_PATH"
   echo "ANNOTSV=$ANNOTSV"
   test -x "$ANNOTSV/bin/AnnotSV"

The official AnnotSV quick-start instructs Bash users to set the ANNOTSV environment variable to the installation directory.

.. _6-3-6-record-the-installed-annotsv-revision:

6.3.6 Record the installed AnnotSV revision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   git -C "$ANNOTSV" \
   rev-parse HEAD \
   > resources/annotsv_setup/AnnotSV.install_commit.txt
   git -C "$ANNOTSV" \
   describe \
   --tags \
   --always \
   > resources/annotsv_setup/AnnotSV.install_version.txt
   cat \
   resources/annotsv_setup/AnnotSV.install_version.txt

.. _6-3-7-test-annotsv-using-a-project-cnv-file:

6.3.7 Test AnnotSV using a project CNV file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   export ANNOTSV="$PWD/resources/annotsv_setup/AnnotSV"
   INPUT_BED="$PWD/input/sample.cnvs.bed"
   OUTPUT_TSV="$PWD/results/tool_tests/annotsv_test.tsv"
   if [[ ! -s "$INPUT_BED" ]]; then
   echo "ERROR: CNV test file is missing: $INPUT_BED"
   exit 1
   fi
   "$ANNOTSV/bin/AnnotSV" \
   -SVinputFile "$INPUT_BED" \
   -outputFile "$OUTPUT_TSV" \
   -svtBEDcol 4 \
   -genomeBuild GRCh38 \
   -annotationMode both \
   -overwrite 1

AnnotSV’s official test uses a four-column BED file and identifies the CNV type through -svtBEDcol 4.

Verify:

.. code:: bash

   set -Eeuo pipefail
   test -s results/tool_tests/annotsv_test.tsv
   echo "AnnotSV output rows:"

wc -l results/tool_tests/annotsv_test.tsv

.. code:: bash

   echo
   echo "AnnotSV header:"
   head -n 1 results/tool_tests/annotsv_test.tsv

.. _6-3-8-optional-annotsv-container:

6.3.8 Optional AnnotSV container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The direct source installation above is the official and simplest method. When the pipeline is configured to call containers/annotsv.sif, the installed tool may also be packaged into an Apptainer image.

The container must contain both:

-  

   .. container::

      AnnotSV executable

-  

   .. container::

      AnnotSV human annotation resources

The resulting image can be large. The direct installation should therefore be tested successfully before creating a container wrapper.

The expected tool path used by the pipeline can be inspected with:

.. code:: bash

   grep -nEi \
   'annotsv|ANNOTSV' \
   pipeline/case_workflow/11_run_cnv_tools.sh

The script’s active path and environment-variable handling should be treated as authoritative for the project installation.

.. _6-4-classifycnv:

6.4 ClassifyCNV
---------------

.. _6-4-1-purpose:

6.4.1 Purpose
~~~~~~~~~~~~~

ClassifyCNV implements the 2019 ACMG/ClinGen technical standards for germline deletions and duplications. It accepts a four-column BED file:

chromosome

-  

   .. container::

      start

-  

   .. container::

      end

-  

   .. container::

      DEL or DUP

It supports both hg19 and hg38, requires Python 3.6 or later and BEDTools 2.27.1 or later, and includes its required pre-parsed databases within the repository.

.. _6-4-2-install-classifycnv:

6.4.2 Install ClassifyCNV
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CLASSIFYCNV_DIR="$PWD/tools/ClassifyCNV"
   if [[ -e "$CLASSIFYCNV_DIR" ]]; then
   echo "ERROR: ClassifyCNV installation path already exists:"
   echo "$CLASSIFYCNV_DIR"
   exit 1
   fi
   git clone \
   https://github.com/Genotek/ClassifyCNV.git \
   "$CLASSIFYCNV_DIR"

Record the exact commit:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   CLASSIFYCNV_DIR="$PWD/tools/ClassifyCNV"
   git -C "$CLASSIFYCNV_DIR" \
   rev-parse HEAD \
   > "$CLASSIFYCNV_DIR/INSTALL_COMMIT.txt"
   cat "$CLASSIFYCNV_DIR/INSTALL_COMMIT.txt"

ClassifyCNV does not use a conventional package installer. Reproducibility therefore depends on storing the exact Git commit used.

.. _6-4-3-verify-classifycnv-requirements:

6.4.3 Verify ClassifyCNV requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   set -Eeuo pipefail
   python3 --version
   bedtools --version
   python3 - <<'PY'
   import sys
   minimum = (3, 6)
   if sys.version_info < minimum:
   raise SystemExit(
   "ERROR: ClassifyCNV requires Python 3.6 or later."
   )
   print("PASS: Compatible Python version.")
   PY
   The official project requires Python 3.6+ and BEDTools 2.27.1+.

.. _6-4-4-clingen-resource-update-policy:

6.4.4 ClinGen resource-update policy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ClassifyCNV includes bundled resources. Its official documentation recommends running update_clingen.sh before analysis to obtain updated ClinGen files. (`GitHub <https://github.com/Genotek/ClassifyCNV>`__)

For exact reproduction of the validated project, first retain the resources present at the recorded commit.

For a deliberate resource update, run:

.. code:: bash

   cd ~/rare_disease_project/tools/ClassifyCNV
   set -Eeuo pipefail

bash update_clingen.sh

After updating, record resource checksums and rerun the full validation suite because updated ClinGen data may change evidence scores:

.. code:: bash

   cd ~/rare_disease_project/tools/ClassifyCNV
   set -Eeuo pipefail
   find Resources \
   -type f \
   -print0 |
   sort -z |
   xargs -0 sha256sum \
   > ClassifyCNV_resources.sha256

.. _6-4-5-run-the-classifycnv-smoke-test:

6.4.5 Run the ClassifyCNV smoke test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   PROJECT_ROOT="$(pwd)"
   CLASSIFYCNV_DIR="$PROJECT_ROOT/tools/ClassifyCNV"
   INPUT_BED="$PROJECT_ROOT/input/sample.cnvs.bed"
   RUN_NAME="project_smoke_test"
   if [[ ! -s "$INPUT_BED" ]]; then
   echo "ERROR: Test CNV BED file is missing."
   exit 1
   fi
   cd "$CLASSIFYCNV_DIR"
   rm -rf \
   "ClassifyCNV_results/$RUN_NAME"
   python3 ClassifyCNV.py \
   --infile "$INPUT_BED" \
   --GenomeBuild hg38 \
   --outdir "$RUN_NAME"

The official execution format is:

python3 ClassifyCNV.py --infile file.bed --GenomeBuild hg38

The --precise option should be used only when the CNV breakpoints are considered exact and intragenic effects should be evaluated.

Verify the scoresheet:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   SCORESHEET="tools/ClassifyCNV/ClassifyCNV_results/project_smoke_test/Scoresheet.txt"
   if [[ ! -s "$SCORESHEET" ]]; then
   echo "ERROR: ClassifyCNV Scoresheet.txt was not created."
   exit 1
   fi
   echo "PASS: ClassifyCNV scoresheet created."
   head -n 3 "$SCORESHEET"

ClassifyCNV stores the evidence scores, final classification, dosage-sensitive genes and protein-coding genes in Scoresheet.txt.

.. _6-5-isv-cnv:

6.5 ISV-CNV
-----------

.. _6-5-1-purpose:

6.5.1 Purpose
~~~~~~~~~~~~~

ISV-CNV predicts CNV pathogenicity using a machine-learning model. It can optionally return prediction probabilities and SHAP values that describe how individual features influenced the prediction.

The package expects GRCh38 CNVs represented by:

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

The command-line interface accepts -p for probabilities and -sv for SHAP values. (PyPI)

.. _6-5-2-use-the-committed-isv-cnv-definition-file:

6.5.2 Use the committed ISV-CNV definition file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The project repository already contains:

containers/isv.def

This definition file should be used instead of installing whichever version currently happens to be returned by an unpinned pip install isv.

The current PyPI release is ISV 0.3.17 and requires Python 3.14 or later, which may differ from the dependency environment used during the validated project. (PyPI)

Build the project container:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   if [[ ! -s containers/isv.def ]]; then
   echo "ERROR: containers/isv.def is missing."
   exit 1
   fi
   sudo -E apptainer build \
   --force \
   containers/isv.sif \
   containers/isv.def

.. _6-5-3-verify-the-isv-cnv-container:

6.5.3 Verify the ISV-CNV container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   apptainer exec \
   containers/isv.sif \
   python3 - <<'PY'
   import isv
   print("PASS: ISV Python module imported.")
   print("Module path:", isv.__file__)
   PY

Check whether the command-line executable is available:

.. code:: bash

   if apptainer exec \
   containers/isv.sif \
   sh -c 'command -v isv' \
   >/dev/null 2>&1
   then
   apptainer exec \
   containers/isv.sif \
   isv --help |
   head
   else
   echo "ISV CLI is not exposed directly."
   echo "The project pipeline will use the installed Python module."
   fi

Record the image checksum:

.. code:: bash

   sha256sum \
   containers/isv.sif \
   > containers/isv.sif.sha256

.. _6-5-4-prepare-a-valid-isv-cnv-test-input:

6.5.4 Prepare a valid ISV-CNV test input
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current ISV command-line documentation requires a header row. (PyPI)

Create a controlled test BED:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   TEST_INPUT="results/tool_tests/isv_test_input.bed"
   cat > "$TEST_INPUT" <<'EOF'
   chromosome start end cnv_type
   chr8 100000 500000 DEL
   chrX 52000000 55000000 DUP
   EOF
   column \
   --separator $'\t' \
   --table \
   "$TEST_INPUT"

Run the test when the container exposes the isv command:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   if apptainer exec \
   containers/isv.sif \
   sh -c 'command -v isv' \
   >/dev/null 2>&1
   then
   apptainer exec \
   --bind "$PWD:/project" \
   containers/isv.sif \
   isv \
   -i /project/results/tool_tests/isv_test_input.bed \
   -o /project/results/tool_tests/isv_test_output.tsv \
   -p \
   -sv
   test -s \
   results/tool_tests/isv_test_output.tsv
   echo "PASS: ISV-CNV test output created."
   else
   echo "INFO: The container exposes ISV through Python rather than the CLI."
   echo "Use pipeline/case_workflow/11_run_cnv_tools.sh."
   fi

The pipeline’s complete ISV invocation is maintained inside:

.. code:: bash

   pipeline/case_workflow/11_run_cnv_tools.sh

That GitHub file should be linked in the Word document rather than reproducing the entire production command.

.. _6-6-optional-intervar-installation:

6.6 Optional InterVar installation
----------------------------------

.. _6-6-1-role-in-this-project:

6.6.1 Role in this project
~~~~~~~~~~~~~~~~~~~~~~~~~~

InterVar applies the 2015 ACMG/AMP framework to small variants and reports evidence codes contributing to classifications such as:

-  

   .. container::

      pathogenic

-  

   .. container::

      likely pathogenic

-  

   .. container::

      uncertain significance

-  

   .. container::

      likely benign

-  

   .. container::

      benign

It can accept VCF or ANNOVAR-formatted inputs. For unannotated inputs, it calls ANNOVAR to obtain the required annotations.

InterVar is optional in this project because:

-  its local installation requires ANNOVAR;

-  several supporting databases must be downloaded separately;

-  OMIM data require authorised access;

-  manual review of evidence codes remains necessary;

-  the core universal pipeline already performs its own evidence prioritisation.

The official InterVar documentation states that users must obtain ANNOVAR and OMIM permissions or licences themselves. (`GitHub <https://github.com/WGLab/InterVar>`__)

.. _6-6-2-clone-intervar:

6.6.2 Clone InterVar
~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   INTERVAR_DIR="$PWD/tools/InterVar"
   if [[ -e "$INTERVAR_DIR" ]]; then
   echo "ERROR: InterVar installation path already exists:"
   echo "$INTERVAR_DIR"
   exit 1
   fi
   git clone \
   https://github.com/WGLab/InterVar.git \
   "$INTERVAR_DIR"
   git -C "$INTERVAR_DIR" \
   rev-parse HEAD \
   > "$INTERVAR_DIR/INSTALL_COMMIT.txt"
   cat "$INTERVAR_DIR/INSTALL_COMMIT.txt"

.. _6-6-3-preserve-a-local-configuration-file:

6.6.3 Preserve a local configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Do not edit the original tracked configuration directly.

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   cp \
   tools/InterVar/config.ini \
   tools/InterVar/config.local.ini

The local configuration must eventually contain the correct paths for:

-  

   .. container::

      ANNOVAR table_annovar.pl

-  

   .. container::

      ANNOVAR convert2annovar.pl

-  

   .. container::

      ANNOVAR annotate_variation.pl

-  

   .. container::

      ANNOVAR humandb directory

-  

   .. container::

      InterVar database directory

-  

   .. container::

      OMIM-derived authorised files

The official InterVar options expose these paths through the configuration file or command-line arguments. (`GitHub <https://github.com/WGLab/InterVar>`__)

.. _6-6-4-do-not-automate-restricted-database-downloads:

6.6.4 Do not automate restricted database downloads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ANNOVAR registration and authorised OMIM access should be completed through their respective official services. Their files must not be redistributed through the GitHub repository.

After obtaining ANNOVAR legitimately, a possible local layout is:

tools/

├── InterVar/

└── annovar/

├── table_annovar.pl

├── convert2annovar.pl

├── annotate_variation.pl

└── humandb/

Verify manually obtained ANNOVAR scripts:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   ANNOVAR_DIR="$PWD/tools/annovar"
   REQUIRED_ANNOVAR_FILES=(
   table_annovar.pl
   convert2annovar.pl
   annotate_variation.pl
   )
   FAILURES=0
   for filename in "${REQUIRED_ANNOVAR_FILES[@]}"; do
   path="$ANNOVAR_DIR/$filename"
   if [[ -s "$path" ]]; then
   echo "PASS: $path"
   else
   echo "MISSING: $path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   if (( FAILURES > 0 )); then
   echo "InterVar local execution is not ready."
   else
   echo "PASS: Required ANNOVAR scripts are present."
   fi

.. _6-6-5-check-the-intervar-interface:

6.6.5 Check the InterVar interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   python3 \
   tools/InterVar/Intervar.py \
   --help |
   head -n 40

The official interface supports arguments including:

.. code:: bash

   --input
   --input_type
   --output
   --buildver
   --config
   --database_intervar
   --database_locat
   --table_annovar
   --convert2annovar
   --annotate_variation

A local analysis should not be run until config.local.ini points to valid, authorised and complete ANNOVAR, InterVar and OMIM resources.

.. _6-7-specialised-tool-readiness-check:

6.7 Specialised-tool readiness check
------------------------------------

Run this after installation:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail

declare -A REQUIRED_ITEMS=(

["SpliceAI container"]="containers/spliceai.sif"

["AnnotSV executable"]="resources/annotsv_setup/AnnotSV/bin/AnnotSV"

["ClassifyCNV script"]="tools/ClassifyCNV/ClassifyCNV.py"

["ISV-CNV container"]="containers/isv.sif"

.. code:: bash

   )
   FAILURES=0
   for label in "${!REQUIRED_ITEMS[@]}"; do
   path="${REQUIRED_ITEMS[$label]}"
   if [[ -s "$path" || -x "$path" ]]; then
   printf "PASS %-24s %s\n" \
   "$label" \
   "$path"
   else
   printf "FAIL %-24s %s\n" \
   "$label" \
   "$path"
   FAILURES=$((FAILURES + 1))
   fi
   done
   echo
   if [[ -s tools/InterVar/Intervar.py ]]; then
   echo "OPTIONAL PASS InterVar source is present."
   else
   echo "OPTIONAL N/A InterVar is not installed."
   fi
   echo
   if (( FAILURES > 0 )); then
   echo "ERROR: $FAILURES required specialised tool(s) are missing."
   exit 1
   fi
   echo "PASS: Required specialised tools are installed."

.. _6-8-record-specialised-tool-versions-and-checksums:

6.8 Record specialised-tool versions and checksums
--------------------------------------------------

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   MANIFEST="results/environment/specialised_tools.tsv"
   {
   echo -e "tool\tversion_or_commit\tpath"
   SPLICEAI_VERSION="$(
   apptainer exec \
   containers/spliceai.sif \
   python -c \
   'from importlib.metadata import version; print(version("spliceai"))'
   )"
   ANNOTSV_VERSION="$(
   cat \
   resources/annotsv_setup/AnnotSV.install_version.txt
   )"
   CLASSIFYCNV_COMMIT="$(
   git -C tools/ClassifyCNV rev-parse HEAD
   )"
   ISV_MODULE="$(
   apptainer exec \
   containers/isv.sif \
   python3 -c \
   'import isv; print(isv.__file__)'
   )"
   printf 'SpliceAI\t%s\t%s\n' \
   "$SPLICEAI_VERSION" \
   "containers/spliceai.sif"
   printf 'AnnotSV\t%s\t%s\n' \
   "$ANNOTSV_VERSION" \
   "resources/annotsv_setup/AnnotSV"
   printf 'ClassifyCNV\t%s\t%s\n' \
   "$CLASSIFYCNV_COMMIT" \
   "tools/ClassifyCNV"
   printf 'ISV-CNV\t%s\t%s\n' \
   "$ISV_MODULE" \
   "containers/isv.sif"
   if [[ -d tools/InterVar/.git ]]; then
   printf 'InterVar\t%s\t%s\n' \
   "$(git -C tools/InterVar rev-parse HEAD)" \
   "tools/InterVar"
   fi
   } > "$MANIFEST"
   column \
   --separator $'\t' \
   --table \
   "$MANIFEST"

Generate checksums for the built containers:

.. code:: bash

   cd ~/rare_disease_project
   set -Eeuo pipefail
   sha256sum \
   containers/spliceai.sif \
   containers/isv.sif \
   > results/environment/specialised_container_images.sha256
   cat \
   results/environment/specialised_container_images.sha256

When an AnnotSV container is also created, add it to this checksum file.

.. _6-9-position-of-each-tool-in-the-workflow:

6.9 Position of each tool in the workflow
-----------------------------------------

+-------------+------------------------+---------------------------------+----------------------------------------------------+
| **Tool**    | **Pipeline stage**     | **Main input**                  | **Main output**                                    |
+=============+========================+=================================+====================================================+
| SpliceAI    | Small-variant branch   | Normalised VCF and GRCh38 FASTA | VCF containing splice delta scores                 |
+-------------+------------------------+---------------------------------+----------------------------------------------------+
| AnnotSV     | CNV/SV branch          | DEL/DUP BED or structural VCF   | Comprehensive annotated TSV                        |
+-------------+------------------------+---------------------------------+----------------------------------------------------+
| ClassifyCNV | CNV classification     | Four-column DEL/DUP BED         | Scoresheet.txt                                     |
+-------------+------------------------+---------------------------------+----------------------------------------------------+
| ISV-CNV     | CNV prioritisation     | GRCh38 four-column CNV table    | Prediction, probability and optional SHAP evidence |
+-------------+------------------------+---------------------------------+----------------------------------------------------+
| InterVar    | Optional manual review | VCF or ANNOVAR input            | ACMG evidence codes and preliminary classification |
+-------------+------------------------+---------------------------------+----------------------------------------------------+

The first four tools are integrated through:

.. code:: bash

   pipeline/case_workflow/08_add_spliceai.sh
   pipeline/case_workflow/11_run_cnv_tools.sh
   pipeline/case_workflow/09_merge_snpeff_spliceai.py
   pipeline/case_workflow/11b_score_universal_cnv.py

-  

   .. container::

      These long production scripts should be explained briefly in the Word document and linked to their full GitHub versions.

-  

   .. container::

      InterVar should be described as an external supporting interpretation source rather than as the final authority for variant classification.

.. _6-10-important-reproducibility-rules:

6.10 Important reproducibility rules
------------------------------------

The following rules should be applied whenever one of these tools is changed:

1. Record the exact version, Git tag or commit.

2. Record the container or resource checksum.

3. Preserve the previous working version until validation finishes.

4. Do not overwrite official resources with validation data.

5. Rerun the unit tests and Patients 01–12 validation audit.

6. Compare new canonical outputs with the previous checksums.

7. Document any score or ranking changes.

8. Never interpret a machine-generated classification without manual review.

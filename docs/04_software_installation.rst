.. _4-complete-software-installation-and-environment-setup:

4. Complete Software Installation and Environment Setup
=======================================================


This section describes the setup required to reproduce the project on a new Windows computer. Commands are separated into **Windows PowerShell** and **Ubuntu Bash** blocks. They must be executed in the shell indicated above each block.

The recommended environment is:

-  

   .. container::

      Windows 10/11

-  

   .. container::

      WSL 2

-  

   .. container::

      Ubuntu 24.04 LTS

-  

   .. container::

      GRCh38

-  

   .. container::

      Python 3

-  

   .. container::

      Apptainer

-  

   .. container::

      bcftools 1.19

-  

   .. container::

      samtools 1.19.2

Ubuntu 24.04 is particularly suitable because its official repositories provide bcftools 1.19 and samtools 1.19.2, which match the versions used during development closely.

.. _4-1-install-wsl-2-and-ubuntu:

4.1 Install WSL 2 and Ubuntu
----------------------------

Open **Windows PowerShell as Administrator**.

First, inspect the available WSL distributions:

-  

   .. container::

      wsl --status

-  

   .. container::

      wsl --list --online

Install Ubuntu 24.04 using the exact distribution name shown by the previous command:

-  

   .. container::

      wsl --install -d Ubuntu-24.04

Restart Windows when requested.

After restarting, confirm that Ubuntu is using WSL 2:

-  

   .. container::

      wsl --set-default-version 2

-  

   .. container::

      wsl --list --verbose

The expected output should show:

NAME STATE VERSION

Ubuntu-24.04 Running 2

Microsoft documents wsl --install as the standard installation method and recommends checking the installed distribution with wsl --list --verbose.

Launch Ubuntu from Windows Terminal or the Start menu. During its first launch, create a Linux username and password.

.. _4-2-confirm-the-ubuntu-environment:

4.2 Confirm the Ubuntu environment
----------------------------------

Run the following inside **Ubuntu Bash**, not PowerShell:

.. code:: bash

   set -Eeuo pipefail
   source /etc/os-release
   echo "Distribution: $PRETTY_NAME"
   echo "Kernel: $(uname -r)"
   echo "Architecture: $(uname -m)"
   echo "User: $USER"
   echo "Home: $HOME"
   echo "CPUs: $(nproc)"
   echo
   free -h
   echo
   df -hT "$HOME"

The project should preferably be stored under the Linux home directory:

.. code:: bash

   /home/<username>/rare_disease_project

which is normally represented as:

.. code:: bash

   ~/rare_disease_project

Avoid placing the active project under:

/mnt/c/

.. code:: bash

   /mnt/d/

unless there is a specific storage requirement. Microsoft recommends keeping Linux projects in the WSL Linux filesystem because Linux tools perform faster there than when repeatedly accessing Windows-mounted drives. (`Microsoft Learn <https://learn.microsoft.com/en-us/windows/wsl/filesystems>`__)

The Linux project can still be accessed from Windows Explorer through:

\\\\wsl.localhost\\Ubuntu-24.04\\home\\<username>\\rare_disease_project

.. _4-3-update-ubuntu-and-enable-required-repositories:

4.3 Update Ubuntu and enable required repositories
--------------------------------------------------

Run:

.. code:: bash

   set -Eeuo pipefail
   sudo apt-get update
   sudo apt-get install -y software-properties-common
   sudo add-apt-repository -y universe
   sudo apt-get update

The universe repository is required because several genomics packages, including bcftools and samtools, are distributed through it on Ubuntu.

.. _4-4-install-the-base-operating-system-packages:

4.4 Install the base operating-system packages
----------------------------------------------

Use the following complete installation block:

.. code:: bash

   set -Eeuo pipefail
   sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
   build-essential \
   autoconf \
   automake \
   cmake \
   pkg-config \
   gcc \
   g++ \
   make \
   git \
   git-lfs \
   curl \
   wget \
   aria2 \
   ca-certificates \
   gnupg \
   lsb-release \
   jq \
   tree \
   rsync \
   gawk \
   grep \
   sed \
   coreutils \
   findutils \
   parallel \
   bc \
   time \
   file \
   less \
   nano \
   vim \
   dos2unix \
   unzip \
   zip \
   tar \
   gzip \
   pigz \
   bzip2 \
   xz-utils \
   sqlite3 \
   libsqlite3-dev \
   python3 \
   python3-dev \
   python3-pip \
   python3-venv \
   python3-setuptools \
   openjdk-17-jre-headless \
   perl \
   cpanminus \
   zlib1g-dev \
   libbz2-dev \
   liblzma-dev \
   libcurl4-openssl-dev \
   libssl-dev \
   libncurses-dev \
   libxml2-dev \
   bcftools \
   samtools \
   tabix \
   bedtools
   git lfs install

These packages provide the compilers, archive utilities, Python environment, Java runtime, Perl environment, VCF manipulation tools, compression utilities and command-line programs needed by the project.

.. _4-5-verify-the-installed-core-software:

4.5 Verify the installed core software
--------------------------------------

Run:

.. code:: bash

   set -Eeuo pipefail
   echo "=== Operating system ==="
   source /etc/os-release
   echo "$PRETTY_NAME"
   echo
   echo "=== Core development software ==="
   git --version
   curl --version | head -n 1
   wget --version | head -n 1
   python3 --version
   python3 -m pip --version
   java -version 2>&1 | head -n 1
   perl -e 'print "Perl $^V\n"'
   sqlite3 --version
   jq --version
   echo
   echo "=== Genomics software ==="
   bcftools --version | head -n 1
   samtools --version | head -n 1
   bgzip --version 2>&1 | head -n 1
   tabix --version 2>&1 | head -n 1
   bedtools --version

On Ubuntu 24.04, the relevant output should be similar to:

.. code:: bash

   bcftools 1.19
   samtools 1.19.2
   bedtools v2.31.x

Perform an explicit version check:

.. code:: bash

   set -Eeuo pipefail
   BCFTOOLS_VERSION="$(
   bcftools --version |
   awk 'NR == 1 {print $2}'
   )"
   SAMTOOLS_VERSION="$(
   samtools --version |
   awk 'NR == 1 {print $2}'
   )"
   echo "bcftools version: $BCFTOOLS_VERSION"
   echo "samtools version: $SAMTOOLS_VERSION"
   if [[ "$BCFTOOLS_VERSION" != 1.19* ]]; then
   echo "WARNING: The validated project used bcftools 1.19."
   fi
   if [[ "$SAMTOOLS_VERSION" != 1.19* ]]; then
   echo "WARNING: The validated project used samtools 1.19.x."
   fi

BCFtools manipulates VCF and BCF files, while samtools manages SAM, BAM and CRAM alignment files. HTSlib supplies utilities such as bgzip and tabix. (HTSLib)

.. _4-6-configure-git:

4.6 Configure Git
-----------------

Set the line-ending behaviour appropriate for Linux:

.. code:: bash

   git config --global core.autocrlf input
   git config --global init.defaultBranch main

Confirm the configuration:

.. code:: bash

   git config --global --get core.autocrlf
   git config --global --get init.defaultBranch

Configure the Git identity used for commits:

.. code:: bash

   git config --global user.name "Wahid-25"
   git config --global user.email \
   "256620669+Wahid-25@users.noreply.github.com"

Verify:

.. code:: bash

   echo "Git name: $(git config --global user.name)"
   echo "Git email: $(git config --global user.email)"

Git can be installed using Ubuntu’s package manager, and Git version 2 maintains strong backward compatibility for ordinary repository operations. (`Git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`__)

.. _4-7-install-github-cli-from-the-official-repository:

4.7 Install GitHub CLI from the official repository
---------------------------------------------------

The ordinary Ubuntu gh package can be outdated. GitHub currently recommends using its official Debian/Ubuntu package repository. (`GitHub <https://github.com/cli/cli/blob/trunk/docs/install_linux.md>`__)

Run:

.. code:: bash

   set -Eeuo pipefail
   if ! command -v wget >/dev/null 2>&1; then
   sudo apt-get update
   sudo apt-get install -y wget
   fi
   sudo mkdir -p -m 755 /etc/apt/keyrings
   sudo mkdir -p -m 755 /etc/apt/sources.list.d
   KEYRING_TEMP="$(mktemp)"
   wget -nv \
   -O "$KEYRING_TEMP" \
   https://cli.github.com/packages/githubcli-archive-keyring.gpg
   sudo install \
   -m 644 \
   "$KEYRING_TEMP" \
   /etc/apt/keyrings/githubcli-archive-keyring.gpg
   rm -f "$KEYRING_TEMP"
   echo \
   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" |
   sudo tee /etc/apt/sources.list.d/github-cli.list \
   >/dev/null
   sudo apt-get update
   sudo apt-get install -y gh
   gh --version

Authenticate with GitHub:

.. code:: bash

   GH_BROWSER=echo gh auth login \
   --hostname github.com \
   --git-protocol https \
   --web

Choose:

GitHub.com

HTTPS

Authenticate Git: Yes

Login with a web browser

The terminal will display a one-time code and the GitHub device-login address. Open the address manually in a Windows browser, enter the code and approve access.

Verify authentication:

.. code:: bash

   gh auth status

Protect the local credentials file:

.. code:: bash

   if [[ -f "$HOME/.config/gh/hosts.yml" ]]; then
   chmod 600 "$HOME/.config/gh/hosts.yml"
   fi

Do not include this credentials file in the project or documentation.

.. _4-8-clone-the-project-repository:

4.8 Clone the project repository
--------------------------------

The repository is currently private, so the authenticated GitHub account must have access.

Run:

.. code:: bash

   set -Eeuo pipefail
   PROJECT_ROOT="$HOME/rare_disease_project"
   if [[ -d "$PROJECT_ROOT/.git" ]]; then
   echo "Repository already exists at:"
   echo "$PROJECT_ROOT"
   elif [[ -e "$PROJECT_ROOT" ]]; then
   echo "ERROR: $PROJECT_ROOT exists but is not a Git repository."
   echo "Rename or remove that directory before cloning."
   exit 1
   else
   gh repo clone \
   Wahid-25/rare-disease-genomics-pipeline \
   "$PROJECT_ROOT"
   fi
   cd "$PROJECT_ROOT"
   echo
   echo "Project root: $(pwd)"
   echo
   git remote -v
   echo
   git branch --show-current
   echo
   git log -1 --oneline

Expected information should include:

Project root: /home/<username>/rare_disease_project

Branch: main

Remote: Wahid-25/rare-disease-genomics-pipeline

Confirm that the checkout is unchanged:

git status

Expected:

On branch main

Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean

.. _4-9-create-the-local-runtime-directories:

4.9 Create the local runtime directories
----------------------------------------

Large resources and generated outputs are not stored in GitHub. Create their expected local directories:

.. code:: bash

   set -Eeuo pipefail
   cd "$HOME/rare_disease_project"
   mkdir -p \
   containers \
   input/cases \
   resources/reference \
   resources/vep_cache \
   resources/snpeff_data \
   resources/clinvar \
   resources/clingen \
   resources/clinpgx \
   resources/gene_disease \
   resources/phenotype/hpo \
   resources/disease_ontology/mondo \
   resources/annotsv_setup \
   tools \
   results/cases \
   results/environment \
   validation/universal_pipeline_testing/outputs \
   validation/universal_pipeline_testing/failed_runs

Confirm the main structure:

.. code:: bash

   find . \
   -maxdepth 2 \
   -type d \
   -not -path './.git*' |

sort

The mkdir -p option makes this command safe to repeat because existing directories are not overwritten.

.. _4-10-create-a-python-virtual-environment:

4.10 Create a Python virtual environment
----------------------------------------

A virtual environment isolates project-specific Python packages from the system Python installation. Python’s official documentation recommends creating one with python -m venv.

Run:

.. code:: bash

   set -Eeuo pipefail
   cd "$HOME/rare_disease_project"
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install \
   --upgrade \
   pip \
   setuptools \
   wheel
   echo "Python executable: $(command -v python)"
   echo "Python version: $(python --version)"
   echo "Pip version: $(python -m pip --version)"

The active prompt may appear as:

(.venv) user@computer:~/rare_disease_project$

To reactivate it in a later terminal session:

.. code:: bash

   cd ~/rare_disease_project
   source .venv/bin/activate

To leave the environment:

.. code:: bash

   deactivate

When a project dependency file is available, install it with:

.. code:: bash

   cd ~/rare_disease_project
   source .venv/bin/activate
   if [[ -f requirements.txt ]]; then
   python -m pip install \
   --requirement requirements.txt
   else
   echo "requirements.txt is not currently present."
   fi

The .venv directory must remain excluded from Git.

.. _4-11-install-apptainer:

4.11 Install Apptainer
----------------------

Apptainer is required to build and execute the project’s container images. Apptainer supports installation inside WSL 2 and provides an official Ubuntu PPA. (Apptainer)

Install the non-setuid package:

.. code:: bash

   set -Eeuo pipefail
   sudo apt-get update
   sudo apt-get install -y software-properties-common
   sudo add-apt-repository \
   -y \
   ppa:apptainer/ppa
   sudo apt-get update
   sudo apt-get install -y apptainer

Verify:

.. code:: bash

   apptainer version
   apptainer buildcfg

Perform an execution test:

.. code:: bash

   apptainer exec \
   docker://alpine \
   cat /etc/alpine-release

The first execution downloads a small test container. A version number from Alpine should be printed.

The original project used Apptainer 1.5.1. The official PPA may now install a later compatible 1.5 release, so the resolved version must be recorded in the environment manifest.

.. _4-12-configure-apptainer-cache-and-temporary-storage:

4.12 Configure Apptainer cache and temporary storage
----------------------------------------------------

Container builds can use substantial temporary disk space. Create dedicated cache and temporary directories:

.. code:: bash

   set -Eeuo pipefail
   mkdir -p \
   "$HOME/.apptainer/cache" \
   "$HOME/.apptainer/tmp"
   export APPTAINER_CACHEDIR="$HOME/.apptainer/cache"
   export APPTAINER_TMPDIR="$HOME/.apptainer/tmp"

Make the settings persistent:

.. code:: bash

   grep -qxF \
   'export APPTAINER_CACHEDIR="$HOME/.apptainer/cache"' \
   "$HOME/.bashrc" ||
   echo \
   'export APPTAINER_CACHEDIR="$HOME/.apptainer/cache"' \
   >> "$HOME/.bashrc"
   grep -qxF \
   'export APPTAINER_TMPDIR="$HOME/.apptainer/tmp"' \
   "$HOME/.bashrc" ||
   echo \
   'export APPTAINER_TMPDIR="$HOME/.apptainer/tmp"' \
   >> "$HOME/.bashrc"

Confirm:

.. code:: bash

   echo "Cache: $APPTAINER_CACHEDIR"
   echo "Temp: $APPTAINER_TMPDIR"
   df -h "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR"

When the home filesystem has insufficient storage, these paths may be moved to a larger Linux-formatted disk.

.. _4-13-validate-all-bash-and-python-source-files:

4.13 Validate all Bash and Python source files
----------------------------------------------

Before downloading large genomic resources, validate the repository source code.

**Check Bash syntax**

.. code:: bash

   set -Eeuo pipefail
   cd "$HOME/rare_disease_project"
   while IFS= read -r -d '' script; do
   echo "Checking Bash: $script"
   bash -n "$script"
   done < <(
   find pipeline \
   -type f \
   -name '*.sh' \
   -print0 |
   sort -z
   )
   echo "PASS: Bash syntax validation completed."

**Check Python syntax**

Activate the environment:

.. code:: bash

   cd "$HOME/rare_disease_project"
   source .venv/bin/activate

Then run:

.. code:: bash

   set -Eeuo pipefail
   while IFS= read -r -d '' script; do
   echo "Checking Python: $script"
   python -m py_compile "$script"
   done < <(
   find pipeline validation \
   -type f \
   -name '*.py' \
   -print0 |
   sort -z
   )
   echo "PASS: Python syntax validation completed."

Python may create \__pycache\_\_ directories during this test. These directories are excluded by .gitignore.

.. _4-14-test-the-included-example-vcf:

4.14 Test the included example VCF
----------------------------------

Run:

.. code:: bash

   set -Eeuo pipefail
   cd "$HOME/rare_disease_project"
   TEST_VCF="input/sample.small_variants.vcf"
   if [[ ! -s "$TEST_VCF" ]]; then
   echo "ERROR: Example VCF is missing or empty: $TEST_VCF"
   exit 1
   fi
   bcftools view \
   --header-only \
   "$TEST_VCF" \
   >/dev/null
   bcftools view \
   --no-header \
   "$TEST_VCF" \
   | head
   bcftools stats \
   "$TEST_VCF" \
   > /tmp/sample.small_variants.stats.txt
   echo
   echo "PASS: bcftools successfully read the example VCF."
   echo "Statistics: /tmp/sample.small_variants.stats.txt"

This test verifies that:

-  bcftools is accessible;

-  the example VCF is readable;

-  the VCF header is recognised;

-  the variant records can be parsed;

-  a statistics report can be generated.

.. _4-15-record-the-software-environment:

4.15 Record the software environment
------------------------------------

Create a local environment manifest:

.. code:: bash

   cd "$ set -Eeuo pipefail
   HOME/rare_disease_project"
   mkdir -p results/environment
   MANIFEST="results/environment/software_versions.txt"
   {
   echo "Rare Disease Genomics Pipeline"
   echo "Environment manifest"
   echo
   echo "Generated UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
   echo "User: $USER"
   echo "Hostname: $(hostname)"
   echo
   source /etc/os-release
   echo "Operating system: $PRETTY_NAME"
   echo "Kernel: $(uname -r)"
   echo "Architecture: $(uname -m)"
   echo "CPU count: $(nproc)"
   echo
   echo "Git: $(git --version)"
   echo "GitHub CLI: $(gh --version | head -n 1)"
   echo "Python: $(python3 --version)"
   echo "Pip: $(python3 -m pip --version)"
   echo "Java: $(java -version 2>&1 | head -n 1)"
   echo "Perl: $(perl -e 'print $^V')"
   echo
   echo "bcftools: $(bcftools --version | head -n 1)"
   echo "samtools: $(samtools --version | head -n 1)"
   echo "bgzip: $(bgzip --version 2>&1 | head -n 1)"
   echo "tabix: $(tabix --version 2>&1 | head -n 1)"
   echo "bedtools: $(bedtools --version)"
   echo "Apptainer: $(apptainer version)"
   } > "$MANIFEST"
   cat "$MANIFEST"

This manifest records the resolved software versions rather than assuming that a package manager always supplies the same release.

.. _4-16-final-environment-readiness-check:

4.16 Final environment readiness check
--------------------------------------

Run this final block:

.. code:: bash

   set -Eeuo pipefail
   REQUIRED_COMMANDS=(
   git
   gh
   curl
   wget
   jq
   python3
   java
   perl
   sqlite3
   bcftools
   samtools
   bgzip
   tabix
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
   echo
   if (( FAILURES > 0 )); then
   echo "Environment check failed: $FAILURES command(s) missing."
   exit 1
   fi
   echo "PASS: Base software environment is ready."

A successful environment will finish with:

PASS: Base software environment is ready.

At this stage, the operating system, Git repository, Python environment, genomics command-line utilities and Apptainer runtime are ready. The reference genome, annotation databases and specialised tools are installed in the following section.

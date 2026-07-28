Getting started
===============

This page provides the shortest route to a working documentation website.
It does not install the complete genomic runtime or large annotation resources.

Requirements
------------

* Git
* Python 3.10 or later
* Access to the project repository
* A Read the Docs account connected to the GitHub repository

Clone the repository
--------------------

.. code-block:: bash

   gh auth status
   gh repo clone Wahid-25/rare-disease-genomics-pipeline "$HOME/rare_disease_project"
   cd "$HOME/rare_disease_project"

Add the documentation bundle
----------------------------

Copy the supplied files into the repository root so that the structure contains:

.. code-block:: text

   rare_disease_project/
   ├── .readthedocs.yaml
   ├── docs/
   │   ├── conf.py
   │   ├── requirements.txt
   │   ├── index.rst
   │   ├── getting_started.rst
   │   ├── installation.rst
   │   ├── workflow.rst
   │   ├── inputs.rst
   │   ├── outputs.rst
   │   ├── validation.rst
   │   ├── troubleshooting.rst
   │   ├── limitations.rst
   │   ├── references.rst
   │   └── _static/
   └── README.md

Build locally
-------------

.. code-block:: bash

   cd ~/rare_disease_project
   python3 -m venv .docs-venv
   source .docs-venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r docs/requirements.txt
   sphinx-build -W --keep-going -b html docs docs/_build/html

Open the local website
----------------------

From WSL, start a simple server:

.. code-block:: bash

   python -m http.server 8000 --directory docs/_build/html

Then open ``http://localhost:8000`` in the Windows browser.

Next steps
----------

1. Review every page and replace any placeholder or outdated path.
2. Add the files to Git.
3. Commit and push them to the repository.
4. Import the repository into Read the Docs.
5. Confirm that the first build succeeds.
6. Set the default version and project visibility.

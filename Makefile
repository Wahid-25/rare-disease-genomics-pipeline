SPHINXOPTS ?=
SPHINXBUILD ?= sphinx-build
SOURCEDIR = docs
BUILDDIR = docs/_build

.PHONY: help clean docs

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

clean:
	rm -rf "$(BUILDDIR)"

docs:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

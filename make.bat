@ECHO OFF
pushd %~dp0
set SPHINXBUILD=sphinx-build
set SOURCEDIR=docs
set BUILDDIR=docs\_build
%SPHINXBUILD% -M html %SOURCEDIR% %BUILDDIR% %SPHINXOPTS%
popd

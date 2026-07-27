#!/usr/bin/env python3
"""Regression tests for allele-aware local PGx validation."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "local_pgx_matcher",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        print(f"FAIL: {message}")
        raise SystemExit(1)
    print(f"PASS: {message}")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    matcher_path = (
        root
        / "pipeline"
        / "case_workflow"
        / "05b_add_local_pgx_reference.py"
    )
    disabled_path = (
        root
        / "pipeline"
        / "case_workflow"
        / "05c_write_disabled_local_pgx.py"
    )
    reference_path = (
        root
        / "resources"
        / "clinpgx"
        / "local_curated_pgx_reference.csv"
    )

    for path in (matcher_path, disabled_path, reference_path):
        require(path.is_file(), f"{path} exists")

    matcher = load_module(matcher_path)
    disabled = load_module(disabled_path)

    require(
        matcher.OUTPUT_FIELDS == disabled.OUTPUT_FIELDS,
        "validation and production-disabled outputs share one schema",
    )

    require(
        matcher.parse_variant("chrX:154536002:C>T")
        == ("X", 154536002, "C", "T"),
        "chr-prefixed X variant parsing",
    )
    require(
        matcher.parse_variant("2:21006288:c>t")
        == ("2", 21006288, "C", "T"),
        "alleles and chromosome are normalized",
    )
    require(
        matcher.normalize_chromosome("chrM") == "MT",
        "mitochondrial chromosome alias normalization",
    )

    complete = [
        {
            "sample_id": "PATIENT_01",
            "category": "PGx",
            "gene": "GENE1",
            "rsid": "rs1",
            "assembly": "GRCh38",
            "chromosome": "1",
            "position": "100",
            "ref": "A",
            "alt": "G",
            "genotype": "Heterozygous",
            "phenotype": "",
            "affected_drugs": "",
            "cpic_level": "",
            "clinical_recommendation": "",
        }
    ]
    records = matcher.prepare_local_records(complete)

    selected, method, ambiguous = matcher.choose_candidate(
        records,
        "rs1",
        ("1", 100, "A", "G"),
    )
    require(
        selected is not None
        and method == "rsid_and_allele"
        and not ambiguous,
        "rsID and allele matching has highest priority",
    )

    selected, method, ambiguous = matcher.choose_candidate(
        records,
        "",
        ("1", 100, "A", "G"),
    )
    require(
        selected is not None
        and method == "allele_coordinates"
        and not ambiguous,
        "allele matching works when VCF ID is missing",
    )

    incomplete = [
        {
            "sample_id": "PATIENT_01",
            "category": "PGx",
            "gene": "GENE1",
            "rsid": "rs1",
            "assembly": "",
            "chromosome": "",
            "position": "",
            "ref": "",
            "alt": "",
            "genotype": "Heterozygous",
            "phenotype": "",
            "affected_drugs": "",
            "cpic_level": "",
            "clinical_recommendation": "",
        }
    ]
    records = matcher.prepare_local_records(incomplete)

    selected, method, ambiguous = matcher.choose_candidate(
        records,
        "rs1",
        ("1", 100, "A", "G"),
    )
    require(
        selected is not None
        and method == "rsid_only"
        and not ambiguous,
        "rsID-only fallback is allowed when coordinates are unavailable",
    )

    records = matcher.prepare_local_records(complete)
    selected, method, ambiguous = matcher.choose_candidate(
        records,
        "rs1",
        ("1", 101, "A", "G"),
    )
    require(
        selected is None and not method and not ambiguous,
        "conflicting complete allele keys do not match by rsID alone",
    )

    duplicate_coordinate = [
        complete[0],
        {
            **complete[0],
            "rsid": "rs2",
            "gene": "GENE2",
        },
    ]
    records = matcher.prepare_local_records(duplicate_coordinate)
    selected, method, ambiguous = matcher.choose_candidate(
        records,
        "",
        ("1", 100, "A", "G"),
    )
    require(
        selected is None
        and method == "ambiguous_allele_coordinates"
        and ambiguous,
        "ambiguous allele-only matches are rejected",
    )

    with reference_path.open(
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        reader = csv.DictReader(handle)
        header = set(reader.fieldnames or [])
        rows = list(reader)

    required_coordinate_columns = {
        "assembly",
        "chromosome",
        "position",
        "ref",
        "alt",
    }
    require(
        required_coordinate_columns <= header,
        "local PGx reference contains allele-coordinate columns",
    )

    pgx_rows = [
        row
        for row in rows
        if "pgx" in str(row.get("category") or "").lower()
    ]
    incomplete_rows = [
        row.get("sample_id", "")
        for row in pgx_rows
        if not all(
            str(row.get(column) or "").strip()
            for column in required_coordinate_columns
        )
    ]
    require(
        not incomplete_rows,
        "all local PGx validation rows have complete GRCh38 alleles",
    )

    print()
    print(
        "PASS: Allele-aware local PGx regression tests completed."
    )


if __name__ == "__main__":
    main()

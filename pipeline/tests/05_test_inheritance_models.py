#!/usr/bin/env python3
"""Regression tests for shared inheritance-model parsing and scoring."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")
    print(f"PASS: {message}")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"FAIL: Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    project = Path(__file__).resolve().parents[2]
    workflow = project / "pipeline" / "case_workflow"

    sys.path.insert(0, str(workflow))
    import inheritance_utils as inheritance

    models = {
        "monoallelic_autosomal": "autosomal_dominant",
        "biallelic_autosomal": "autosomal_recessive",
        "monoallelic_X_hemizygous": "x_linked_hemizygous",
        "monoallelic_X_heterozygous": "x_linked_heterozygous",
        "biallelic_X": "x_linked_biallelic",
        "x-linked recessive": "x_linked_recessive",
        "x-linked dominant": "x_linked_dominant",
        "mitochondrial": "mitochondrial",
        "": "unknown",
    }

    for requirement, expected in models.items():
        observed = inheritance.classify_inheritance_model(requirement).model
        require(
            observed == expected,
            f"{requirement or 'empty'} -> {expected}",
        )

    small_cases = [
        (
            "monoallelic_autosomal",
            "heterozygous",
            (3, "compatible_monoallelic_heterozygous"),
        ),
        (
            "biallelic_autosomal",
            "homozygous_alt",
            (3, "compatible_biallelic_homozygous"),
        ),
        (
            "biallelic_autosomal",
            "heterozygous",
            (0, "single_heterozygous_recessive_allele"),
        ),
        (
            "monoallelic_X_hemizygous",
            "hemizygous_or_haploid_alt",
            (3, "compatible_hemizygous_x_linked"),
        ),
        (
            "biallelic_X",
            "homozygous_alt",
            (3, "compatible_biallelic_x_linked"),
        ),
        (
            "mitochondrial",
            "hemizygous_or_haploid_alt",
            (
                2,
                "mitochondrial_variant_present_heteroplasmy_not_assessed",
            ),
        ),
        (
            "",
            "heterozygous",
            (0, "inheritance_not_scored"),
        ),
    ]

    for requirement, zygosity, expected in small_cases:
        observed = inheritance.score_small_variant_inheritance(
            requirement,
            zygosity,
        )
        require(
            observed == expected,
            f"small variant {requirement}/{zygosity}",
        )

    small = load_module(
        workflow / "07_score_disease_candidates.py",
        "small_variant_scorer_test",
    )
    cnv = load_module(
        workflow / "12_score_cnv_candidates.py",
        "cnv_scorer_test",
    )
    universal = load_module(
        workflow / "11_score_universal_evidence.py",
        "universal_scorer_test",
    )

    require(
        small.inheritance_points(
            "monoallelic_X_hemizygous",
            "hemizygous_or_haploid_alt",
        )
        == (3, "compatible_hemizygous_x_linked"),
        "small-variant scorer uses shared X-linked precedence",
    )

    require(
        cnv.inheritance_points(
            "biallelic_X",
            "homozygous_alt",
        )
        == (3, "compatible_biallelic_x_linked"),
        "CNV scorer uses shared biallelic-X precedence",
    )

    require(
        universal.inheritance_model(
            {
                "allelic_requirement": "monoallelic_X_hemizygous",
                "disease_inheritance_names": "",
            }
        )
        == "x_linked_hemizygous",
        "universal evidence does not misclassify X-linked as autosomal",
    )

    require(
        universal.inheritance_model(
            {
                "allelic_requirement": "mitochondrial",
                "disease_inheritance_names": "",
            }
        )
        == "mitochondrial",
        "universal evidence recognises mitochondrial inheritance",
    )

    print()
    print("PASS: Universal inheritance regression tests completed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Regression tests for GRCh38 sex-chromosome/ploidy preflight."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")
    print(f"PASS: {message}")


def load(path: Path):
    spec = importlib.util.spec_from_file_location("ploidy_preflight_test", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"FAIL: Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    project = Path(__file__).resolve().parents[2]
    module = load(
        project
        / "pipeline"
        / "case_workflow"
        / "20_sex_ploidy_preflight.py"
    )

    require(module.in_par("X", 10001), "GRCh38 X PAR1 lower boundary")
    require(module.in_par("X", 2781479), "GRCh38 X PAR1 upper boundary")
    require(not module.in_par("X", 2781480), "X non-PAR after PAR1")
    require(module.in_par("X", 155701383), "GRCh38 X PAR2 lower boundary")
    require(module.in_par("Y", 56887903), "GRCh38 Y PAR2 lower boundary")

    cases = [
        (
            ("X", 154536002, "1", "male"),
            ("pass", "male_X_nonPAR_haploid_call"),
        ),
        (
            ("X", 154536002, "0/1", "male"),
            ("warning", "male_X_nonPAR_heterozygous_call"),
        ),
        (
            ("X", 154536002, "0/1", "female"),
            ("pass", "female_X_nonPAR_diploid_call"),
        ),
        (
            ("Y", 10000000, "1", "female"),
            ("warning", "female_Y_nonPAR_nonreference_call"),
        ),
        (
            ("1", 100000, "1", "unknown"),
            ("warning", "haploid_autosomal_call_review_required"),
        ),
        (
            ("MT", 100, "0/1", "unknown"),
            ("notice", "mitochondrial_GT_heteroplasmy_not_assessed"),
        ),
        (
            ("X", 10001, "0/1", "male"),
            ("pass", "diploid_PAR_call"),
        ),
    ]

    for args, expected in cases:
        observed = module.assess_record(*args)
        require(observed == expected, f"ploidy assessment {args}")

    print()
    print("PASS: Sex-chromosome/ploidy regression tests completed.")


if __name__ == "__main__":
    main()

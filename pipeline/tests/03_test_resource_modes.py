#!/usr/bin/env python3
"""Static and resource-level regression tests for production/validation modes."""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")

    print(f"PASS: {message}")


def main() -> None:
    root = Path(__file__).resolve().parents[2]

    runner = root / "pipeline" / "run_case_pipeline.sh"
    wrapper = root / "pipeline" / "run_real_patient_case.sh"
    mapper = (
        root
        / "pipeline"
        / "case_workflow"
        / "04_map_genes_to_diseases.py"
    )
    builder = (
        root
        / "pipeline"
        / "case_workflow"
        / "00b_refresh_combined_g2p.py"
    )
    disabled = (
        root
        / "pipeline"
        / "case_workflow"
        / "05c_write_disabled_local_pgx.py"
    )
    official = (
        root
        / "resources"
        / "gene_disease"
        / "g2p"
        / "AllG2P.official.csv"
    )
    validation = (
        root
        / "resources"
        / "gene_disease"
        / "g2p"
        / "AllG2P.validation.csv"
    )

    for path in (
        runner,
        wrapper,
        mapper,
        builder,
        disabled,
        official,
        validation,
    ):
        require(path.is_file() and path.stat().st_size > 0, f"{path} exists")

    runner_text = runner.read_text(encoding="utf-8")
    wrapper_text = wrapper.read_text(encoding="utf-8")
    mapper_text = mapper.read_text(encoding="utf-8")
    builder_text = builder.read_text(encoding="utf-8")

    require(
        'PIPELINE_MODE="${PIPELINE_MODE:-production}"'
        in runner_text,
        "case runner defaults to production",
    )
    require(
        'if [[ "$PIPELINE_MODE" == "validation" ]]'
        in runner_text,
        "case runner gates validation resources explicitly",
    )
    require(
        "05c_write_disabled_local_pgx.py" in runner_text,
        "production writes explicit disabled local-PGx outputs",
    )
    require(
        'PIPELINE_MODE="${PIPELINE_MODE:-production}"'
        in wrapper_text,
        "real-patient wrapper defaults to production",
    )
    require(
        "export PIPELINE_MODE" in wrapper_text,
        "wrapper propagates the selected mode",
    )
    require(
        "AllG2P.official.csv" in mapper_text,
        "mapper defaults to the official G2P resource",
    )
    require(
        "AllG2P.validation.csv" in builder_text,
        "builder writes a separate validation G2P resource",
    )
    require(
        'write_csv(validation_file' in builder_text,
        "builder writes validation output explicitly",
    )
    require(
        re.search(
            r"if not official_file\.is_file\(\):"
            r".*?write_csv\(\s*official_file\s*,",
            builder_text,
            flags=re.DOTALL,
        )
        is not None,
        "builder only initializes the official resource when absent",
    )
    require(
        'write_csv(legacy_file' not in builder_text,
        "builder does not overwrite the legacy active resource",
    )
    require(
        "ATP7B" not in builder_text and "APOB" not in builder_text,
        "G2P self-validation is generic rather than gene-specific",
    )

    official_rows = csv_rows(official)
    validation_rows = csv_rows(validation)

    require(
        not any(
            (row.get("g2p id") or "").startswith("LOCAL_VALIDATION_")
            for row in official_rows
        ),
        "official G2P resource contains no local validation rows",
    )
    require(
        len(validation_rows) >= len(official_rows),
        "validation G2P resource contains the official baseline",
    )
    require(
        any(
            (row.get("g2p id") or "").startswith("LOCAL_VALIDATION_")
            or "local_validation_hpo_extension"
            in (row.get("review") or "")
            for row in validation_rows
        ),
        "validation G2P resource contains clearly marked validation evidence",
    )

    print()
    print(f"Official SHA256:   {sha256(official)}")
    print(f"Validation SHA256: {sha256(validation)}")
    print()
    print("PASS: Production/validation resource-mode regression tests passed.")


if __name__ == "__main__":
    main()

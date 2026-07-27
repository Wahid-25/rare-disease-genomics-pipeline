#!/usr/bin/env python3
"""Resolve optional case sex metadata without contaminating production mode."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def normalize_sex(value: object) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "m": "male",
        "male": "male",
        "xy": "male",
        "f": "female",
        "female": "female",
        "xx": "female",
        "u": "unknown",
        "unknown": "unknown",
        "not_provided": "unknown",
        "": "unknown",
    }
    if text not in mapping:
        raise ValueError(
            f"Unsupported sex value {value!r}; use male, female, or unknown."
        )
    return mapping[text]


def patient_id_from_case(case_id: str) -> str:
    match = re.search(r"patient[_-]?(\d+)", case_id, flags=re.IGNORECASE)
    if not match:
        return ""
    return f"PATIENT_{int(match.group(1)):02d}"


def validation_sheet_sex(
    project_root: Path,
    case_id: str,
    selected_sample: str,
) -> tuple[str, str]:
    sheet = (
        project_root
        / "validation"
        / "universal_pipeline_testing"
        / "inputs"
        / "reference"
        / "sample_sheet.csv"
    )

    if not sheet.is_file():
        return "unknown", "validation_sample_sheet_unavailable"

    target = selected_sample.strip().upper() or patient_id_from_case(case_id)
    if not target:
        return "unknown", "validation_sample_not_resolved"

    with sheet.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            sample_id = str(row.get("sample_id") or "").strip().upper()
            if sample_id != target:
                continue
            return (
                normalize_sex(row.get("sex")),
                "validation_sample_sheet",
            )

    return "unknown", "validation_sample_not_found"


def write_metadata(
    output: Path,
    case_id: str,
    sex: str,
    source: str,
    mode: str,
    selected_sample: str,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "field\tvalue\n"
        f"case_id\t{case_id}\n"
        f"sex\t{sex}\n"
        f"sex_source\t{source}\n"
        f"pipeline_mode\t{mode}\n"
        f"selected_sample\t{selected_sample}\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("--mode", choices=("production", "validation"), default="production")
    parser.add_argument("--requested-sex", default="unknown")
    parser.add_argument("--selected-sample", default="")
    parser.add_argument("--project-root", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    root = (
        Path(args.project_root).expanduser().resolve()
        if args.project_root
        else Path(__file__).resolve().parents[2]
    )

    requested = normalize_sex(args.requested_sex)

    if requested != "unknown":
        resolved = requested
        source = "explicit_cli_or_environment"
    elif args.mode == "validation":
        resolved, source = validation_sheet_sex(
            root,
            args.case_id,
            args.selected_sample,
        )
    else:
        resolved = "unknown"
        source = "not_provided_in_production"

    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else root
        / "input"
        / "cases"
        / args.case_id
        / "case_sex.resolved.tsv"
    )

    write_metadata(
        output,
        args.case_id,
        resolved,
        source,
        args.mode,
        args.selected_sample,
    )

    print(resolved)


if __name__ == "__main__":
    main()

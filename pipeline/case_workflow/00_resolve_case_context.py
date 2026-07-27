#!/usr/bin/env python3

import csv
import re
import subprocess
import sys
from pathlib import Path


HPO_PATTERN = re.compile(r"\bHP:\d{7}\b", re.I)

ORDERED_FIELDS = [
    "case_id",
    "case_mode",
    "affected_status",
    "testing_indication",
    "phenotype_status",
    "sex",
    "age_years",
    "family_history",
    "clinical_note",
    "phenotype_file",
    "valid_hpo_terms",
    "context_source",
]


def read_context(path: Path) -> dict[str, str]:
    values = {}

    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.reader(handle, delimiter="\t")

        for row in reader:
            if not row or row[0].startswith("#"):
                continue

            if row[0].strip().lower() == "field":
                continue

            if len(row) >= 2:
                key = row[0].strip()
                value = row[1].strip()

                if key:
                    values[key] = value

    return values


def count_hpo(path: Path) -> int:
    terms = set()

    with path.open(
        encoding="utf-8",
        errors="replace",
    ) as handle:
        for line in handle:
            terms.update(
                match.upper()
                for match in HPO_PATTERN.findall(line)
            )

    return len(terms)


def resolve_path(
    project_root: Path,
    value: str,
) -> Path:
    path = Path(value)

    if path.is_absolute():
        return path

    return project_root / path


def main() -> None:
    if len(sys.argv) not in {3, 4}:
        raise SystemExit(
            "Usage: 00_resolve_case_context.py "
            "CASE_ID PHENOTYPE_FILE|- [CONTEXT_TSV|-]"
        )

    case_id = sys.argv[1]
    phenotype_argument = sys.argv[2]
    context_argument = (
        sys.argv[3]
        if len(sys.argv) == 4
        else "-"
    )

    project_root = Path(__file__).resolve().parents[2]

    output_dir = (
        project_root
        / "input"
        / "cases"
        / case_id
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = (
        output_dir
        / "case_context.resolved.tsv"
    )

    phenotype_file = None
    hpo_count = 0

    if phenotype_argument != "-":
        phenotype_file = resolve_path(
            project_root,
            phenotype_argument,
        )

        if not phenotype_file.is_file():
            raise SystemExit(
                f"ERROR: Phenotype file missing: {phenotype_file}"
            )

        hpo_count = count_hpo(phenotype_file)

    if context_argument == "-":
        if phenotype_file is None:
            raise SystemExit(
                "ERROR: Standard diagnostic mode requires "
                "a phenotype file."
            )

        if hpo_count == 0:
            raise SystemExit(
                "ERROR: No valid HP:####### terms were found."
            )

        context = {
            "case_id": case_id,
            "case_mode": "affected_diagnostic",
            "affected_status": "affected",
            "testing_indication": "diagnostic",
            "phenotype_status": "available",
            "sex": "unknown",
            "age_years": "",
            "family_history": "",
            "clinical_note": (
                "Automatically generated standard "
                "diagnostic context"
            ),
            "context_source": "automatic_default",
        }

    else:
        context_file = resolve_path(
            project_root,
            context_argument,
        )

        if not context_file.is_file():
            raise SystemExit(
                f"ERROR: Context file missing: {context_file}"
            )

        validator = (
            project_root
            / "pipeline"
            / "case_workflow"
            / "00_validate_case_context.py"
        )

        command = [
            sys.executable,
            str(validator),
            str(context_file),
            (
                str(phenotype_file)
                if phenotype_file is not None
                else "-"
            ),
        ]

        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
        )

        print(completed.stdout, end="")

        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)

        if completed.returncode != 0:
            raise SystemExit(
                "ERROR: Case-context validation failed."
            )

        context = read_context(context_file)
        context["case_id"] = case_id
        context["context_source"] = (
            str(context_file.relative_to(project_root))
        )

    phenotype_status = context.get(
        "phenotype_status",
        "",
    )

    if phenotype_status == "available" and hpo_count == 0:
        raise SystemExit(
            "ERROR: phenotype_status=available requires "
            "at least one valid HPO term."
        )

    context["phenotype_file"] = (
        str(phenotype_file.relative_to(project_root))
        if phenotype_file is not None
        else "not_provided"
    )

    context["valid_hpo_terms"] = str(hpo_count)

    all_fields = list(ORDERED_FIELDS)

    for field in context:
        if field not in all_fields:
            all_fields.append(field)

    with output_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["field", "value"])

        for field in all_fields:
            writer.writerow(
                [field, context.get(field, "")]
            )

    print()
    print("=" * 68)
    print("UNIVERSAL CASE CONTEXT RESOLVED")
    print("=" * 68)
    print(f"Case ID:             {case_id}")
    print(
        f"Case mode:           "
        f"{context.get('case_mode', '')}"
    )
    print(
        f"Phenotype status:    "
        f"{phenotype_status}"
    )
    print(f"Valid HPO terms:     {hpo_count}")
    print(
        f"Context source:      "
        f"{context.get('context_source', '')}"
    )
    print(f"Resolved context:    {output_file}")


if __name__ == "__main__":
    main()

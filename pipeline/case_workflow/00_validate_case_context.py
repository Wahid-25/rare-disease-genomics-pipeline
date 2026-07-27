#!/usr/bin/env python3

import csv
import re
import sys
from pathlib import Path


HPO_PATTERN = re.compile(r"\bHP:\d{7}\b", re.I)

ALLOWED = {
    "case_mode": {
        "affected_diagnostic",
        "unaffected_carrier",
        "presymptomatic_testing",
        "incidental_finding",
        "screening",
        "unknown",
    },
    "affected_status": {
        "affected",
        "unaffected",
        "unknown",
    },
    "testing_indication": {
        "diagnostic",
        "cascade_testing",
        "predictive_testing",
        "carrier_screening",
        "secondary_finding",
        "screening",
        "unknown",
    },
    "phenotype_status": {
        "available",
        "not_evaluable",
        "not_provided",
    },
    "sex": {
        "male",
        "female",
        "other",
        "unknown",
    },
}


def load_context(path):
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

            if len(row) < 2:
                continue

            key = row[0].strip()
            value = row[1].strip()

            if key:
                values[key] = value

    return values


def count_hpo_terms(path):
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


def main():
    if len(sys.argv) not in {2, 3}:
        raise SystemExit(
            "Usage: 00_validate_case_context.py "
            "CONTEXT_TSV [PHENOTYPE_FILE|-]"
        )

    context_file = Path(sys.argv[1]).resolve()

    phenotype_argument = (
        sys.argv[2]
        if len(sys.argv) == 3
        else "-"
    )

    if not context_file.is_file():
        raise SystemExit(
            f"ERROR: Context file missing: {context_file}"
        )

    context = load_context(context_file)

    required = [
        "case_mode",
        "affected_status",
        "testing_indication",
        "phenotype_status",
        "sex",
    ]

    errors = []
    warnings = []

    for field in required:
        value = context.get(field, "")

        if not value:
            errors.append(f"missing_required_field:{field}")
            continue

        if value not in ALLOWED[field]:
            errors.append(
                f"invalid_{field}:{value}"
            )

    case_mode = context.get("case_mode", "")
    affected = context.get("affected_status", "")
    phenotype_status = context.get(
        "phenotype_status",
        "",
    )

    if (
        case_mode == "affected_diagnostic"
        and affected != "affected"
    ):
        errors.append(
            "affected_diagnostic_requires_affected_status"
        )

    if (
        case_mode == "unaffected_carrier"
        and affected != "unaffected"
    ):
        errors.append(
            "unaffected_carrier_requires_unaffected_status"
        )

    hpo_count = 0

    if phenotype_status == "available":
        if phenotype_argument == "-":
            errors.append(
                "phenotype_file_required_when_available"
            )
        else:
            phenotype_file = Path(
                phenotype_argument
            ).resolve()

            if not phenotype_file.is_file():
                errors.append(
                    f"phenotype_file_missing:{phenotype_file}"
                )
            else:
                hpo_count = count_hpo_terms(
                    phenotype_file
                )

                if hpo_count == 0:
                    errors.append(
                        "no_valid_HPO_terms_found"
                    )

    elif phenotype_status == "not_evaluable":
        warnings.append(
            "phenotype_scoring_must_be_marked_not_evaluable"
        )

    elif phenotype_status == "not_provided":
        warnings.append(
            "phenotype_evidence_unavailable"
        )

    status = "PASS" if not errors else "FAIL"

    print("=" * 68)
    print("UNIVERSAL CASE-CONTEXT VALIDATION")
    print("=" * 68)
    print(f"Context file:       {context_file}")
    print(f"Case mode:          {case_mode}")
    print(f"Affected status:    {affected}")
    print(
        "Testing indication: "
        f"{context.get('testing_indication', '')}"
    )
    print(f"Phenotype status:   {phenotype_status}")
    print(f"Valid HPO terms:    {hpo_count}")
    print(f"Validation status:  {status}")

    for warning in warnings:
        print(f"WARNING: {warning}")

    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

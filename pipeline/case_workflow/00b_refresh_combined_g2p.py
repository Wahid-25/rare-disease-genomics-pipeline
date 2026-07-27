#!/usr/bin/env python3
"""Build a validation-only G2P resource without changing official resources."""

from __future__ import annotations

import csv
import os
import re
from datetime import date
from pathlib import Path

G2P_COLUMNS = [
    "g2p id",
    "gene symbol",
    "gene mim",
    "hgnc id",
    "previous gene symbols",
    "disease name",
    "disease mim",
    "disease MONDO",
    "allelic requirement",
    "cross cutting modifier",
    "confidence",
    "variant consequence",
    "variant types",
    "molecular mechanism",
    "molecular mechanism support",
    "molecular mechanism categorisation",
    "molecular mechanism evidence",
    "phenotypes",
    "publications",
    "additional mined publications",
    "panel",
    "comments",
    "date of last review",
    "review",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def patient_number(sample_id: str) -> int:
    match = re.search(r"(\d+)", sample_id)
    if not match:
        raise ValueError(f"Cannot determine patient number: {sample_id}")
    return int(match.group(1))


def inheritance_to_g2p(value: str, sex: str) -> str:
    text = clean(value).lower()
    sex_value = clean(sex).upper()

    if "autosomal recessive" in text:
        return "biallelic_autosomal"
    if "autosomal dominant" in text:
        return "monoallelic_autosomal"
    if "x-linked recessive" in text or "x linked recessive" in text:
        return (
            "monoallelic_X_hemizygous"
            if sex_value == "M"
            else "biallelic_X"
        )
    if "x-linked dominant" in text or "x linked dominant" in text:
        return (
            "monoallelic_X_hemizygous"
            if sex_value == "M"
            else "monoallelic_X_heterozygous"
        )
    if "mitochondrial" in text:
        return "mitochondrial"
    return ""


def hpo_terms_for_sample(hpo_dir: Path, sample_id: str) -> list[str]:
    """Return HPO terms from the file for the exact numeric patient ID.

    Exact numeric matching prevents PATIENT_01 from matching filenames
    such as patient_10, patient_11, patient_12, or patient_13.
    """

    number = patient_number(sample_id)
    matched_paths: list[Path] = []

    for path in sorted(hpo_dir.glob("*.hpo.txt")):
        match = re.search(
            r"(?i)(?:^|[^a-z0-9])patient[_-]?0*(\d+)(?:[^0-9]|$)",
            path.name,
        )

        if match and int(match.group(1)) == number:
            matched_paths.append(path)

    if len(matched_paths) > 1:
        joined = ", ".join(str(path) for path in matched_paths)
        raise RuntimeError(
            f"Multiple HPO files found for {sample_id}: {joined}"
        )

    if not matched_paths:
        return []

    text = matched_paths[0].read_text(
        encoding="utf-8",
        errors="replace",
    )

    return sorted(set(re.findall(r"HP:\d{7}", text)))


def parse_hpo_field(value: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()

    for term in re.findall(r"HP:\d{7}", clean(value)):
        if term not in seen:
            terms.append(term)
            seen.add(term)

    return terms


def merge_hpo(existing: str, additional: list[str]) -> str:
    terms = parse_hpo_field(existing)
    seen = set(terms)

    for term in additional:
        if term not in seen:
            terms.append(term)
            seen.add(term)

    return "; ".join(terms)


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = [
            {key: clean(value) for key, value in row.items()}
            for row in reader
        ]

    return fields, rows


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    temporary = path.with_name(path.name + ".tmp")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    os.replace(temporary, path)


def find_matches(
    rows: list[dict[str, str]],
    gene: str,
    disease_name: str,
    disease_mim: str,
) -> list[int]:
    matches: list[int] = []

    for index, row in enumerate(rows):
        if clean(row.get("gene symbol")).upper() != gene:
            continue

        row_mim = clean(row.get("disease mim"))
        row_disease = clean(row.get("disease name")).casefold()

        if disease_mim and row_mim == disease_mim:
            matches.append(index)
        elif row_disease == disease_name.casefold():
            matches.append(index)

    return matches


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    resource_dir = (
        project_root
        / "resources"
        / "gene_disease"
        / "g2p"
    )

    official_file = resource_dir / "AllG2P.official.csv"
    legacy_file = resource_dir / "AllG2P.latest.csv"
    validation_file = resource_dir / "AllG2P.validation.csv"
    local_file = resource_dir / "AllG2P.local_validation.csv"
    metadata_file = resource_dir / "AllG2P.validation.metadata.tsv"

    sample_sheet = (
        project_root
        / "validation"
        / "universal_pipeline_testing"
        / "inputs"
        / "reference"
        / "sample_sheet.csv"
    )
    hpo_dir = (
        project_root
        / "validation"
        / "universal_pipeline_testing"
        / "inputs"
        / "hpo"
    )

    resource_dir.mkdir(parents=True, exist_ok=True)
    hpo_dir.mkdir(parents=True, exist_ok=True)

    if not official_file.is_file():
        if not legacy_file.is_file():
            raise SystemExit(
                "ERROR: Neither AllG2P.official.csv nor "
                "AllG2P.latest.csv is available."
            )

        legacy_fields, legacy_rows = load_csv(legacy_file)
        official_rows = [
            row
            for row in legacy_rows
            if not clean(row.get("g2p id")).startswith(
                "LOCAL_VALIDATION_"
            )
        ]
        write_csv(
            official_file,
            legacy_fields or G2P_COLUMNS,
            official_rows,
        )

    for required in (official_file, sample_sheet):
        if not required.is_file():
            raise SystemExit(
                f"ERROR: Required file not found: {required}"
            )

    official_fields, official_rows = load_csv(official_file)
    missing_columns = set(G2P_COLUMNS) - set(official_fields)

    if missing_columns:
        raise SystemExit(
            "ERROR: Official G2P file is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    _, sample_rows = load_csv(sample_sheet)

    combined_rows = [dict(row) for row in official_rows]
    local_rows: list[dict[str, str]] = []

    official_relationships_found = 0
    official_rows_hpo_augmented = 0
    local_relationships_added = 0
    validation_relationships_with_hpo = 0

    validation_checks: list[
        tuple[str, str, str, list[str]]
    ] = []

    for sample in sorted(
        sample_rows,
        key=lambda row: patient_number(row["sample_id"]),
    ):
        sample_id = clean(sample.get("sample_id")).upper()
        gene = clean(sample.get("gene")).upper()
        disease = clean(sample.get("disorder"))
        disease_mim = clean(sample.get("omim_id"))

        if not sample_id or not gene or not disease:
            continue

        terms = hpo_terms_for_sample(hpo_dir, sample_id)
        validation_checks.append(
            (sample_id, gene, disease_mim, terms)
        )

        if terms:
            validation_relationships_with_hpo += 1

        official_indexes = find_matches(
            official_rows,
            gene,
            disease,
            disease_mim,
        )

        if official_indexes:
            official_relationships_found += 1

            for index in official_indexes:
                before = set(
                    parse_hpo_field(
                        combined_rows[index].get(
                            "phenotypes",
                            "",
                        )
                    )
                )
                combined_rows[index]["phenotypes"] = merge_hpo(
                    combined_rows[index].get("phenotypes", ""),
                    terms,
                )
                after = set(
                    parse_hpo_field(
                        combined_rows[index].get(
                            "phenotypes",
                            "",
                        )
                    )
                )

                if after != before:
                    official_rows_hpo_augmented += 1

                    note = (
                        "Local synthetic validation HPO extension "
                        f"for {sample_id}; the untouched official "
                        "relationship is preserved separately in "
                        "AllG2P.official.csv."
                    )
                    existing_comment = clean(
                        combined_rows[index].get("comments")
                    )
                    combined_rows[index]["comments"] = (
                        f"{existing_comment} {note}".strip()
                    )

                    existing_review = clean(
                        combined_rows[index].get("review")
                    )
                    marker = "local_validation_hpo_extension"
                    combined_rows[index]["review"] = (
                        f"{existing_review};{marker}"
                        if existing_review
                        else marker
                    )

            continue

        number = patient_number(sample_id)
        row = {column: "" for column in G2P_COLUMNS}

        row.update(
            {
                "g2p id": (
                    f"LOCAL_VALIDATION_PATIENT_{number:02d}"
                ),
                "gene symbol": gene,
                "disease name": disease,
                "disease mim": disease_mim,
                "allelic requirement": inheritance_to_g2p(
                    clean(sample.get("inheritance_pattern")),
                    clean(sample.get("sex")),
                ),
                "confidence": "definitive",
                "phenotypes": "; ".join(terms),
                "panel": "Local synthetic validation extension",
                "comments": (
                    "Synthetic validation truth-set relationship; "
                    "not an official Gene2Phenotype assertion. "
                    f"Source sample: {sample_id}."
                ),
                "date of last review": date.today().isoformat(),
                "review": "local_validation",
            }
        )

        local_rows.append(row)
        combined_rows.append(row)
        local_relationships_added += 1

    write_csv(local_file, G2P_COLUMNS, local_rows)
    write_csv(validation_file, G2P_COLUMNS, combined_rows)

    failed_checks: list[str] = []

    for sample_id, gene, disease_mim, terms in validation_checks:
        matches = [
            row
            for row in combined_rows
            if clean(row.get("gene symbol")).upper() == gene
            and (
                not disease_mim
                or clean(row.get("disease mim")) == disease_mim
            )
        ]

        if not matches:
            failed_checks.append(
                f"{sample_id}:{gene}:relationship_missing"
            )
            continue

        if terms:
            observed_terms: set[str] = set()

            for row in matches:
                observed_terms.update(
                    parse_hpo_field(
                        row.get("phenotypes", "")
                    )
                )

            missing_terms = set(terms) - observed_terms

            if missing_terms:
                failed_checks.append(
                    f"{sample_id}:{gene}:missing_hpo="
                    + ",".join(sorted(missing_terms))
                )

    with metadata_file.open("w", encoding="utf-8") as handle:
        handle.write("metric\tvalue\n")
        handle.write("resource_mode\tvalidation\n")
        handle.write(
            f"official_resource\t"
            f"{official_file.relative_to(project_root)}\n"
        )
        handle.write(
            f"validation_resource\t"
            f"{validation_file.relative_to(project_root)}\n"
        )
        handle.write(
            f"local_extension\t"
            f"{local_file.relative_to(project_root)}\n"
        )
        handle.write(f"official_rows\t{len(official_rows)}\n")
        handle.write(
            "official_validation_relationships_found\t"
            f"{official_relationships_found}\n"
        )
        handle.write(
            "official_rows_hpo_augmented\t"
            f"{official_rows_hpo_augmented}\n"
        )
        handle.write(
            f"local_relationships_added\t"
            f"{local_relationships_added}\n"
        )
        handle.write(
            "validation_relationships_with_hpo\t"
            f"{validation_relationships_with_hpo}\n"
        )
        handle.write(
            f"validation_relationships_checked\t"
            f"{len(validation_checks)}\n"
        )
        handle.write(
            f"validation_relationship_check_failures\t"
            f"{len(failed_checks)}\n"
        )
        handle.write(
            "validation_relationship_failure_details\t"
            + ";".join(failed_checks)
            + "\n"
        )
        handle.write(f"combined_rows\t{len(combined_rows)}\n")

    print("========================================")
    print("VALIDATION-ONLY G2P RESOURCE")
    print("========================================")
    print(f"Official rows:                     {len(official_rows)}")
    print(
        "Official validation relationships: "
        f"{official_relationships_found}"
    )
    print(
        "Official rows HPO-augmented:        "
        f"{official_rows_hpo_augmented}"
    )
    print(
        "Local relationships added:          "
        f"{local_relationships_added}"
    )
    print(
        "Validation relationships with HPO:  "
        f"{validation_relationships_with_hpo}"
    )
    print(
        "Validation relationships checked:   "
        f"{len(validation_checks)}"
    )
    print(
        "Validation check failures:           "
        f"{len(failed_checks)}"
    )
    print(f"Official file:                     {official_file}")
    print(f"Validation file:                   {validation_file}")
    print(f"Local extension:                   {local_file}")
    print(f"Metadata:                          {metadata_file}")

    if failed_checks:
        raise SystemExit(
            "ERROR: Generic validation relationship checks failed: "
            + "; ".join(failed_checks)
        )

    print(
        "PASS: Validation G2P resource rebuilt without "
        "modifying the official resource."
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import csv
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path


CONFIDENCE_RANK = {
    "refuted": 0,
    "disputed": 1,
    "limited": 2,
    "moderate": 3,
    "strong": 4,
    "definitive": 5,
}

ASSOCIATION_RANK = {
    "unknown": 1,
    "polygenic": 2,
    "mendelian": 3,
}

PHENOTYPE_FIELDS = [
    "phenotype_evidence_status",
    "patient_hpo_count",
    "invalid_patient_hpo_count",
    "disease_hpo_count",
    "exact_hpo_count",
    "exact_hpo_terms",
    "patient_to_disease_similarity",
    "exact_patient_hpo_coverage",
    "phenotype_component_score",
    "phenotype_component_evaluable_maximum",
    "phenotype_scoring_method",
]


def clean(value):
    return str(value).strip() if value is not None else ""


def number(value, default=-1.0):
    try:
        return float(clean(value))
    except (TypeError, ValueError):
        return default


def normalize_identifier(value):
    value = clean(value)

    if not value:
        return ""

    if value.lower().startswith("orphanet:"):
        return "ORPHA:" + value.split(":", 1)[1]

    if ":" in value:
        prefix, suffix = value.split(":", 1)
        return f"{prefix.upper()}:{suffix}"

    return value.upper()


def unique_values(rows, field):
    values = []

    for row in rows:
        value = clean(row.get(field))

        if value and value not in values:
            values.append(value)

    return values


def join_values(values):
    return "|".join(
        value
        for value in values
        if value
    )


def choose_confidence(rows):
    values = unique_values(rows, "confidence")

    if not values:
        return ""

    return max(
        values,
        key=lambda value: CONFIDENCE_RANK.get(
            value.lower(),
            -1,
        ),
    )


def choose_association(rows):
    values = unique_values(
        rows,
        "hpo_association_type",
    )

    if not values:
        return ""

    return max(
        values,
        key=lambda value: ASSOCIATION_RANK.get(
            value.lower(),
            -1,
        ),
    )


def valid_disease_name(name, disease_id):
    name = clean(name)
    disease_id = clean(disease_id)

    if not name:
        return False

    if name.upper() == disease_id.upper():
        return False

    generic = {
        "not provided",
        "not specified",
        "see cases",
        "unknown",
    }

    return name.lower() not in generic


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: "
            "10b_resolve_disease_identities.py CASE_ID"
        )

    case_id = sys.argv[1]
    project = Path(__file__).resolve().parents[2]

    final_dir = (
        project
        / "results"
        / "cases"
        / case_id
        / "final"
    )

    input_table = (
        final_dir
        / (
            f"{case_id}."
            "variant_gene_disease.phenotype.tsv"
        )
    )

    output_table = (
        final_dir
        / (
            f"{case_id}."
            "variant_gene_disease.resolved.tsv"
        )
    )

    qc_file = (
        final_dir
        / (
            f"{case_id}."
            "disease_identity_resolution_qc.tsv"
        )
    )

    database = (
        project
        / "resources"
        / "disease_ontology"
        / "mondo"
        / "current"
        / "mondo_crosswalk.sqlite"
    ).resolve()

    for required in [input_table, database]:
        if not required.is_file():
            raise SystemExit(
                f"ERROR: Required file missing: {required}"
            )

    with input_table.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        original_columns = list(
            reader.fieldnames or []
        )
        rows = list(reader)

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row

    try:
        mondo_names = {
            row["mondo_id"]: row["mondo_name"]
            for row in connection.execute(
                """
                SELECT mondo_id, mondo_name
                FROM mondo_term
                """
            )
        }

        external_mappings = defaultdict(set)

        for row in connection.execute(
            """
            SELECT mondo_id, external_id
            FROM mondo_mapping
            WHERE relation_type = 'exact'
            """
        ):
            external_id = normalize_identifier(
                row["external_id"]
            )

            external_mappings[external_id].add(
                row["mondo_id"]
            )

    finally:
        connection.close()

    groups = defaultdict(list)
    ambiguous_identifiers = set()
    unmapped_identifiers = set()

    for index, row in enumerate(rows):
        disease_id = normalize_identifier(
            row.get("canonical_disease_id")
        )

        if disease_id.startswith("MONDO:"):
            resolved_id = disease_id
            resolution_status = "canonical_mondo"

        elif disease_id:
            matches = external_mappings.get(
                disease_id,
                set(),
            )

            if len(matches) == 1:
                resolved_id = next(iter(matches))
                resolution_status = "exact_mondo_crosswalk"

            elif len(matches) > 1:
                resolved_id = disease_id
                resolution_status = (
                    "ambiguous_exact_mapping_not_merged"
                )
                ambiguous_identifiers.add(disease_id)

            else:
                resolved_id = disease_id
                resolution_status = "no_exact_mapping"
                unmapped_identifiers.add(disease_id)

        else:
            resolved_id = ""
            resolution_status = "no_disease_identifier"

        if resolved_id:
            group_key = (
                clean(row.get("variant")),
                clean(row.get("gene")).upper(),
                resolved_id,
            )
        else:
            # Rows without disease IDs are retained separately.
            group_key = (
                clean(row.get("variant")),
                clean(row.get("gene")).upper(),
                f"UNIDENTIFIED_ROW_{index}",
            )

        copied = dict(row)
        copied["_original_disease_id"] = disease_id
        copied["_resolved_disease_id"] = resolved_id
        copied["_resolution_status"] = resolution_status

        groups[group_key].append(copied)

    output_rows = []
    merged_groups = 0
    collapsed_rows = 0

    for group_key, members in groups.items():
        variant, gene, group_identifier = group_key

        resolved_id = clean(
            members[0].get("_resolved_disease_id")
        )

        g2p_members = [
            row
            for row in members
            if "G2P" in clean(
                row.get("disease_source")
            ).upper()
        ]

        strongest_g2p = None

        if g2p_members:
            strongest_g2p = max(
                g2p_members,
                key=lambda row: CONFIDENCE_RANK.get(
                    clean(
                        row.get("confidence")
                    ).lower(),
                    -1,
                ),
            )

        phenotype_member = max(
            members,
            key=lambda row: number(
                row.get("phenotype_component_score")
            ),
        )

        base = dict(
            strongest_g2p
            or phenotype_member
            or members[0]
        )

        # Fill empty fields using other equivalent records.
        for member in members:
            for field, value in member.items():
                if field.startswith("_"):
                    continue

                if (
                    clean(value)
                    and not clean(base.get(field))
                ):
                    base[field] = clean(value)

        # Keep phenotype values from the strongest phenotype row.
        for field in PHENOTYPE_FIELDS:
            base[field] = clean(
                phenotype_member.get(field)
            )

        source_ids = unique_values(
            members,
            "_original_disease_id",
        )

        source_names = unique_values(
            members,
            "disease_name",
        )

        source_types = unique_values(
            members,
            "disease_source",
        )

        resolution_statuses = unique_values(
            members,
            "_resolution_status",
        )

        if resolved_id.startswith("MONDO:"):
            canonical_name = clean(
                mondo_names.get(resolved_id)
            )
        else:
            canonical_name = ""

        if not canonical_name:
            for member in members:
                candidate_name = clean(
                    member.get("disease_name")
                )

                candidate_id = clean(
                    member.get(
                        "_original_disease_id"
                    )
                )

                if valid_disease_name(
                    candidate_name,
                    candidate_id,
                ):
                    canonical_name = candidate_name
                    break

        if not canonical_name:
            canonical_name = (
                resolved_id
                or clean(
                    members[0].get("disease_name")
                )
            )

        confidence = choose_confidence(members)
        association = choose_association(members)

        inheritance_hpo = join_values(
            unique_values(
                members,
                "disease_inheritance_hpo",
            )
        )

        inheritance_names = join_values(
            unique_values(
                members,
                "disease_inheritance_names",
            )
        )

        base["canonical_disease_id"] = resolved_id
        base["disease_name"] = canonical_name
        base["disease_source"] = join_values(
            source_types
        )
        base["confidence"] = confidence
        base["hpo_association_type"] = association
        base["disease_inheritance_hpo"] = (
            inheritance_hpo
        )
        base["disease_inheritance_names"] = (
            inheritance_names
        )

        base["source_disease_ids"] = join_values(
            source_ids
        )
        base["source_disease_names"] = join_values(
            source_names
        )
        base["disease_identity_status"] = (
            "exact_identity_merged"
            if len(members) > 1
            and resolved_id.startswith("MONDO:")
            else join_values(resolution_statuses)
        )
        base["disease_identity_member_count"] = str(
            len(members)
        )
        base["disease_identity_method"] = (
            "Mondo_exact_cross_reference"
            if resolved_id.startswith("MONDO:")
            else "original_identifier_retained"
        )

        base["gene"] = gene
        base["variant"] = variant

        for field in list(base):
            if field.startswith("_"):
                del base[field]

        output_rows.append(base)

        if len(members) > 1:
            merged_groups += 1
            collapsed_rows += len(members) - 1

    output_rows.sort(
        key=lambda row: (
            clean(row.get("variant")),
            clean(row.get("gene")),
            clean(
                row.get("canonical_disease_id")
            ),
            clean(row.get("disease_name")),
        )
    )

    added_columns = [
        "source_disease_ids",
        "source_disease_names",
        "disease_identity_status",
        "disease_identity_member_count",
        "disease_identity_method",
    ]

    output_columns = list(original_columns)

    for field in added_columns:
        if field not in output_columns:
            output_columns.append(field)

    with output_table.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=output_columns,
            delimiter="\t",
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(output_rows)

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(
            handle,
            delimiter="\t",
        )

        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(["input_rows", len(rows)])
        writer.writerow(
            ["resolved_candidate_rows", len(output_rows)]
        )
        writer.writerow(
            ["merged_identity_groups", merged_groups]
        )
        writer.writerow(
            ["collapsed_duplicate_rows", collapsed_rows]
        )
        writer.writerow(
            [
                "ambiguous_identifiers_not_merged",
                len(ambiguous_identifiers),
            ]
        )
        writer.writerow(
            [
                "identifiers_without_exact_mapping",
                len(unmapped_identifiers),
            ]
        )
        writer.writerow(
            [
                "output_table",
                str(output_table.relative_to(project)),
            ]
        )

    print("=" * 72)
    print("UNIVERSAL DISEASE-IDENTITY RESOLUTION")
    print("=" * 72)
    print(f"Case ID:                   {case_id}")
    print(f"Input disease rows:        {len(rows)}")
    print(f"Resolved candidate rows:   {len(output_rows)}")
    print(f"Merged identity groups:    {merged_groups}")
    print(f"Collapsed duplicate rows:  {collapsed_rows}")
    print(
        f"Ambiguous IDs retained:    "
        f"{len(ambiguous_identifiers)}"
    )
    print(f"Output:                    {output_table}")
    print(f"QC:                        {qc_file}")


if __name__ == "__main__":
    main()

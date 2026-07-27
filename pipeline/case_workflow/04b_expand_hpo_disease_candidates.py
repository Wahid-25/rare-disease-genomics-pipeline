#!/usr/bin/env python3

import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path


def clean(value):
    return str(value).strip() if value is not None else ""


def g2p_disease_id(row):
    mondo = clean(row.get("disease_mondo"))

    if mondo:
        if mondo.upper().startswith("MONDO:"):
            return mondo.upper()

        return f"MONDO:{mondo}"

    mim = clean(row.get("disease_mim"))

    if mim:
        if mim.upper().startswith("OMIM:"):
            return mim.upper()

        return f"OMIM:{mim}"

    return ""


def hpo_diseases(connection, gene):
    rows = connection.execute(
        """
        SELECT
            gd.disease_id,
            COALESCE(
                NULLIF(d.disease_name, ''),
                gd.disease_id
            ) AS disease_name,
            GROUP_CONCAT(
                DISTINCT gd.association_type
            ) AS association_types,
            GROUP_CONCAT(
                DISTINCT gd.source
            ) AS sources
        FROM gene_disease AS gd
        LEFT JOIN disease AS d
          ON d.disease_id = gd.disease_id
        WHERE gd.gene_symbol = ?
        GROUP BY
            gd.disease_id,
            disease_name
        ORDER BY gd.disease_id
        """,
        (gene.upper(),),
    ).fetchall()

    return [dict(row) for row in rows]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: 04b_expand_hpo_disease_candidates.py "
            "CASE_ID"
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
        / f"{case_id}.variant_gene_disease.tsv"
    )

    output_table = (
        final_dir
        / (
            f"{case_id}."
            "variant_gene_disease.universal.tsv"
        )
    )

    qc_file = (
        final_dir
        / (
            f"{case_id}."
            "universal_disease_mapping_qc.tsv"
        )
    )

    database = (
        project
        / "resources"
        / "phenotype"
        / "hpo"
        / "current"
        / "hpo_semantic.sqlite"
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

        input_rows = list(reader)

    groups = defaultdict(list)

    for row in input_rows:
        key = (
            clean(row.get("variant")),
            clean(row.get("gene")).upper(),
        )

        groups[key].append(row)

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row

    output_rows = []

    g2p_rows_retained = 0
    hpo_rows_added = 0
    fallback_rows_retained = 0
    genes_with_hpo_mapping = set()

    try:
        for (
            variant,
            gene,
        ), rows in groups.items():

            base_row = dict(rows[0])

            existing_disease_ids = set()
            existing_disease_rows = []

            for row in rows:
                disease_name = clean(
                    row.get("disease_name")
                )

                disease_id = g2p_disease_id(row)

                if not disease_name and not disease_id:
                    continue

                copied = dict(row)

                copied["disease_source"] = "G2P"
                copied["canonical_disease_id"] = (
                    disease_id
                )
                copied["hpo_association_type"] = ""
                copied["hpo_mapping_source"] = ""

                existing_disease_rows.append(copied)
                g2p_rows_retained += 1

                if disease_id:
                    existing_disease_ids.add(
                        disease_id.upper()
                    )

            output_rows.extend(
                existing_disease_rows
            )

            hpo_candidates = (
                hpo_diseases(connection, gene)
                if gene
                else []
            )

            if hpo_candidates:
                genes_with_hpo_mapping.add(gene)

            for disease in hpo_candidates:
                disease_id = clean(
                    disease.get("disease_id")
                ).upper()

                if (
                    disease_id
                    and disease_id in existing_disease_ids
                ):
                    continue

                new_row = dict(base_row)

                for field in [
                    "g2p_id",
                    "disease_mim",
                    "disease_mondo",
                    "allelic_requirement",
                    "confidence",
                    "variant_consequence_model",
                    "variant_types_model",
                    "molecular_mechanism",
                    "panel",
                    "last_review",
                    "gene_disease_score",
                ]:
                    new_row[field] = ""

                new_row["disease_name"] = clean(
                    disease.get("disease_name")
                )

                if disease_id.startswith("OMIM:"):
                    new_row["disease_mim"] = (
                        disease_id.removeprefix(
                            "OMIM:"
                        )
                    )

                elif disease_id.startswith("MONDO:"):
                    new_row["disease_mondo"] = (
                        disease_id
                    )

                new_row["disease_source"] = (
                    "HPO_gene_disease"
                )

                new_row["canonical_disease_id"] = (
                    disease_id
                )

                new_row["hpo_association_type"] = clean(
                    disease.get(
                        "association_types"
                    )
                )

                new_row["hpo_mapping_source"] = clean(
                    disease.get("sources")
                )

                output_rows.append(new_row)
                hpo_rows_added += 1

            if (
                not existing_disease_rows
                and not hpo_candidates
            ):
                fallback = dict(base_row)

                fallback["disease_source"] = (
                    "unmapped"
                )
                fallback["canonical_disease_id"] = ""
                fallback["hpo_association_type"] = ""
                fallback["hpo_mapping_source"] = ""

                output_rows.append(fallback)
                fallback_rows_retained += 1

    finally:
        connection.close()

    added_columns = [
        "disease_source",
        "canonical_disease_id",
        "hpo_association_type",
        "hpo_mapping_source",
    ]

    output_columns = list(original_columns)

    for column in added_columns:
        if column not in output_columns:
            output_columns.append(column)

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
        writer.writerow(
            ["input_variant_disease_rows", len(input_rows)]
        )
        writer.writerow(
            ["unique_variant_gene_groups", len(groups)]
        )
        writer.writerow(
            ["retained_G2P_rows", g2p_rows_retained]
        )
        writer.writerow(
            ["added_HPO_disease_rows", hpo_rows_added]
        )
        writer.writerow(
            [
                "genes_with_HPO_mapping",
                len(genes_with_hpo_mapping),
            ]
        )
        writer.writerow(
            [
                "unmapped_fallback_rows",
                fallback_rows_retained,
            ]
        )
        writer.writerow(
            ["output_rows", len(output_rows)]
        )
        writer.writerow(
            [
                "output_table",
                str(output_table.relative_to(project)),
            ]
        )

    print("=" * 72)
    print("UNIVERSAL GENE–DISEASE CANDIDATE EXPANSION")
    print("=" * 72)
    print(f"Case ID:                  {case_id}")
    print(f"Variant–gene groups:      {len(groups)}")
    print(f"Retained G2P rows:        {g2p_rows_retained}")
    print(f"Added HPO disease rows:   {hpo_rows_added}")
    print(
        f"Genes with HPO mapping:   "
        f"{len(genes_with_hpo_mapping)}"
    )
    print(
        f"Unmapped fallback rows:   "
        f"{fallback_rows_retained}"
    )
    print(f"Final mapping rows:       {len(output_rows)}")
    print(f"Output:                   {output_table}")
    print(f"QC:                       {qc_file}")


if __name__ == "__main__":
    main()

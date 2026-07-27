#!/usr/bin/env python3

import csv
import sys
from pathlib import Path


if len(sys.argv) != 2:
    raise SystemExit(
        "Usage: 12_build_universal_master.py CASE_ID"
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

sources = [
    (
        final_dir
        / f"{case_id}.universal_evidence_scores.tsv",
        "small_variant",
    ),
    (
        final_dir
        / f"{case_id}.universal_cnv_scores.tsv",
        "copy_number_variant",
    ),
]

rows = []

for path, candidate_type in sources:
    if not path.is_file():
        continue

    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        for row in reader:
            row["candidate_type"] = candidate_type
            row["candidate_source_table"] = path.name
            rows.append(row)

if not rows:
    raise SystemExit(
        f"ERROR: No universal candidate table found for {case_id}"
    )


def ranking_score(row):
    try:
        return float(
            row.get("universal_ranking_score_100", "")
            or 0
        )
    except ValueError:
        return 0.0


rows.sort(
    key=lambda row: (
        -ranking_score(row),
        row.get("gene", ""),
        row.get("disease_name", ""),
    )
)

for rank, row in enumerate(rows, start=1):
    row["master_rank"] = str(rank)
    row["case_id"] = case_id

preferred = [
    "master_rank",
    "candidate_type",
    "case_id",
    "variant",
    "vcf_id",
    "gene",
    "canonical_disease_id",
    "disease_name",
    "clinvar_significance",
    "genotype",
    "zygosity",
    "case_mode",
    "affected_status",
    "phenotype_evidence_status",
    "semantic_phenotype_score",
    "evidence_strength_100",
    "evidence_coverage_fraction",
    "universal_ranking_score_100",
    "priority",
    "evidence_gaps",
    "candidate_source_table",
]

other_columns = []

for row in rows:
    for column in row:
        if (
            column not in preferred
            and column not in other_columns
        ):
            other_columns.append(column)

columns = preferred + other_columns

output = (
    final_dir
    / f"{case_id}.master_candidate_table.tsv"
)

with output.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=columns,
        delimiter="\t",
        extrasaction="ignore",
    )

    writer.writeheader()
    writer.writerows(rows)

top = rows[0]

print("=" * 68)
print("UNIVERSAL MASTER TABLE CREATED")
print("=" * 68)
print(f"Case ID:          {case_id}")
print(f"Candidates:       {len(rows)}")
print(f"Top gene:         {top.get('gene', '')}")
print(f"Top disease:      {top.get('disease_name', '')}")
print(
    "Top score:        "
    f"{top.get('universal_ranking_score_100', '')}"
)
print(f"Master table:     {output}")

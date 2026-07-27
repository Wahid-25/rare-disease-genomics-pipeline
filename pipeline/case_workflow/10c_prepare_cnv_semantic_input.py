#!/usr/bin/env python3

import csv
import sys
from pathlib import Path


def clean(value):
    return str(value).strip() if value is not None else ""


if len(sys.argv) != 2:
    raise SystemExit(
        "Usage: 10c_prepare_cnv_semantic_input.py CASE_ID"
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

source = (
    final_dir
    / f"{case_id}.cnv_gene_disease_scores.final.tsv"
)

output = (
    final_dir
    / f"{case_id}.cnv_gene_disease.semantic_input.tsv"
)

if not source.is_file():
    raise SystemExit(f"ERROR: Missing CNV table: {source}")

with source.open(
    encoding="utf-8",
    newline="",
) as handle:
    reader = csv.DictReader(handle, delimiter="\t")
    columns = list(reader.fieldnames or [])
    rows = list(reader)

added = [
    "variant",
    "canonical_disease_id",
    "disease_name",
]

for column in added:
    if column not in columns:
        columns.append(column)

for row in rows:
    row["variant"] = clean(
        row.get("cnv_variant")
    )

    mondo = clean(
        row.get("disease_mondo")
    )

    mim = clean(
        row.get("disease_mim")
    )

    omim_id = ""

    if mim:
        omim_id = (
            mim
            if mim.upper().startswith("OMIM:")
            else f"OMIM:{mim}"
        )

    # The HPO annotation database primarily uses source
    # identifiers such as OMIM and ORPHA. Mondo remains
    # preserved in the disease_mondo field for later identity
    # resolution and final reporting.
    row["canonical_disease_id"] = (
        omim_id
        or mondo
    )

    row["disease_name"] = clean(
        row.get("candidate_disease")
        or row.get("g2p_disease_name")
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

print("CNV semantic input prepared")
print(f"Rows:   {len(rows)}")
print(f"Output: {output}")

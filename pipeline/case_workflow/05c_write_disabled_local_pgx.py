#!/usr/bin/env python3
"""Write explicit disabled local-PGX outputs for production mode."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


OUTPUT_FIELDS = [
    "case_id",
    "sample",
    "variant",
    "vcf_id",
    "genotype",
    "zygosity",
    "gene",
    "consequence",
    "local_pgx_sample_id",
    "local_pgx_rsid",
    "local_pgx_gene",
    "local_pgx_reference_variant",
    "local_pgx_observed_variant",
    "local_pgx_match_method",
    "local_pgx_allele_match",
    "local_pgx_expected_genotype",
    "local_pgx_observed_genotype_class",
    "local_pgx_genotype_match",
    "local_pgx_phenotype",
    "local_pgx_affected_drugs",
    "local_pgx_cpic_level",
    "local_pgx_clinical_recommendation",
    "local_pgx_source",
    "local_pgx_status",
]


def main() -> None:
    if len(sys.argv) not in {2, 3}:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/05c_write_disabled_local_pgx.py "
            "CASE_ID [REASON]"
        )
        raise SystemExit(1)

    case_id = sys.argv[1]
    reason = (
        sys.argv[2]
        if len(sys.argv) == 3
        else "disabled_in_production_mode"
    )

    project_root = Path(__file__).resolve().parents[2]

    output_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "clinpgx"
        / f"{case_id}.local_pgx_matches.tsv"
    )
    qc_file = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.local_pgx_qc.tsv"
    )

    output_table.parent.mkdir(parents=True, exist_ok=True)
    qc_file.parent.mkdir(parents=True, exist_ok=True)

    with output_table.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=OUTPUT_FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()

    qc_rows = [
        ("case_id", case_id),
        ("local_pgx_schema_version", "2"),
        ("local_pgx_enabled", "no"),
        ("disabled_reason", reason),
        ("expected_local_pgx_rows", "0"),
        ("coordinate_complete_reference_rows", "0"),
        ("matched_local_pgx_rows", "0"),
        ("rsid_and_allele_matches", "0"),
        ("allele_coordinate_matches", "0"),
        ("rsid_only_matches", "0"),
        ("ambiguous_observed_rows", "0"),
        ("gene_mismatch_rows", "0"),
        ("genotype_mismatch_rows", "0"),
        ("missing_expected_variants", ""),
        ("output_table", str(output_table.relative_to(project_root))),
    ]

    with qc_file.open("w", encoding="utf-8") as handle:
        handle.write("metric\tvalue\n")
        for metric, value in qc_rows:
            handle.write(f"{metric}\t{value}\n")

    print("========================================")
    print("LOCAL PGX VALIDATION DISABLED")
    print("========================================")
    print(f"Case ID:  {case_id}")
    print(f"Reason:   {reason}")
    print(f"Output:   {output_table}")
    print(f"QC:       {qc_file}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import csv
import gzip
import sys
from pathlib import Path


ADDED_COLUMNS = [
    "snpeff_effect",
    "snpeff_impact",
    "snpeff_gene",
    "snpeff_transcript",
    "snpeff_hgvsc",
    "snpeff_hgvsp",
    "snpeff_vep_agreement",
    "spliceai_gene",
    "spliceai_ds_ag",
    "spliceai_ds_al",
    "spliceai_ds_dg",
    "spliceai_ds_dl",
    "spliceai_max_ds",
    "spliceai_max_effect",
    "spliceai_prediction_present",
    "score_before_phenotype",
]


def clean(value: str) -> str:
    return value.strip() if value else ""


def parse_info(info_text: str) -> dict[str, str]:
    result: dict[str, str] = {}

    if info_text in {"", "."}:
        return result

    for item in info_text.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            result[key] = value
        else:
            result[item] = "true"

    return result


def safe_float(value: str):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_ann_records(value: str) -> list[dict[str, str]]:
    records = []

    if not value or value == ".":
        return records

    for annotation in value.split(","):
        fields = annotation.split("|")

        while len(fields) < 16:
            fields.append("")

        records.append(
            {
                "allele": fields[0],
                "effect": fields[1],
                "impact": fields[2],
                "gene": fields[3],
                "gene_id": fields[4],
                "feature_type": fields[5],
                "transcript": fields[6],
                "biotype": fields[7],
                "rank": fields[8],
                "hgvsc": fields[9],
                "hgvsp": fields[10],
            }
        )

    return records


def choose_ann(
    records: list[dict[str, str]],
    gene: str,
) -> dict[str, str]:
    if not records:
        return {}

    gene_upper = gene.upper()

    matching = [
        record
        for record in records
        if clean(record.get("gene", "")).upper() == gene_upper
    ]

    if matching:
        return matching[0]

    return records[0]


def parse_spliceai_records(value: str) -> list[dict[str, str]]:
    records = []

    if not value or value == ".":
        return records

    for annotation in value.split(","):
        fields = annotation.split("|")

        while len(fields) < 10:
            fields.append("")

        records.append(
            {
                "allele": fields[0],
                "gene": fields[1],
                "ds_ag": fields[2],
                "ds_al": fields[3],
                "ds_dg": fields[4],
                "ds_dl": fields[5],
                "dp_ag": fields[6],
                "dp_al": fields[7],
                "dp_dg": fields[8],
                "dp_dl": fields[9],
            }
        )

    return records


def spliceai_maximum(
    record: dict[str, str],
) -> tuple[str, str]:
    scores = {
        "acceptor_gain": safe_float(record.get("ds_ag", "")),
        "acceptor_loss": safe_float(record.get("ds_al", "")),
        "donor_gain": safe_float(record.get("ds_dg", "")),
        "donor_loss": safe_float(record.get("ds_dl", "")),
    }

    available = {
        effect: score
        for effect, score in scores.items()
        if score is not None
    }

    if not available:
        return "", ""

    maximum_effect = max(
        available,
        key=available.get,
    )

    maximum_score = available[maximum_effect]

    return f"{maximum_score:g}", maximum_effect


def choose_spliceai(
    records: list[dict[str, str]],
    gene: str,
) -> dict[str, str]:
    if not records:
        return {}

    gene_upper = gene.upper()

    matching = [
        record
        for record in records
        if clean(record.get("gene", "")).upper() == gene_upper
    ]

    candidates = matching if matching else records

    def record_score(record: dict[str, str]) -> float:
        values = [
            safe_float(record.get("ds_ag", "")),
            safe_float(record.get("ds_al", "")),
            safe_float(record.get("ds_dg", "")),
            safe_float(record.get("ds_dl", "")),
        ]

        valid = [
            value
            for value in values
            if value is not None
        ]

        return max(valid) if valid else -1.0

    return max(candidates, key=record_score)


def consequence_agreement(
    vep_consequence: str,
    snpeff_effect: str,
) -> str:
    if not snpeff_effect:
        return "not_available"

    vep_terms = {
        term.strip().lower()
        for term in vep_consequence.split("&")
        if term.strip()
    }

    snpeff_terms = {
        term.strip().lower()
        for term in snpeff_effect.split("&")
        if term.strip()
    }

    if vep_terms & snpeff_terms:
        return "yes"

    return "different_or_additional"


def load_cumulative_vcf(
    path: Path,
) -> dict[str, dict[str, str]]:
    annotations: dict[str, dict[str, str]] = {}

    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue

            fields = line.rstrip("\n").split("\t")

            if len(fields) < 8:
                continue

            chrom, pos, _vcf_id, ref, alt = fields[:5]
            info = parse_info(fields[7])

            key = f"{chrom}:{pos}:{ref}>{alt}"

            annotations[key] = {
                "ANN": clean(info.get("ANN", "")),
                "SpliceAI": clean(info.get("SpliceAI", "")),
            }

    return annotations


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/"
            "09_merge_snpeff_spliceai.py CASE_ID"
        )
        sys.exit(1)

    case_id = sys.argv[1]

    script_path = Path(__file__).resolve()
    project_root = script_path.parents[2]

    score_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.variant_gene_disease_scores.tsv"
    )

    cumulative_vcf = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "annotated"
        / (
            f"{case_id}.vep.snpeff."
            "clinvar.spliceai.vcf.gz"
        )
    )

    output_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / (
            f"{case_id}.variant_gene_disease_scores."
            "prephenotype.tsv"
        )
    )

    qc_file = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.small_variant_evidence_qc.tsv"
    )

    for required in [score_table, cumulative_vcf]:
        if not required.is_file():
            print(f"ERROR: Required file not found: {required}")
            sys.exit(1)

    vcf_annotations = load_cumulative_vcf(cumulative_vcf)

    output_rows = []
    variants_with_ann = set()
    variants_with_spliceai = set()
    rows_with_vep_snpeff_agreement = 0

    with score_table.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        original_columns = reader.fieldnames or []

        base_columns = [
            column
            for column in original_columns
            if column not in ADDED_COLUMNS
        ]

        for row in reader:
            variant = clean(row.get("variant", ""))
            gene = clean(row.get("gene", "")).upper()
            evidence = vcf_annotations.get(variant, {})

            ann_records = parse_ann_records(
                evidence.get("ANN", "")
            )

            snpeff = choose_ann(ann_records, gene)

            spliceai_records = parse_spliceai_records(
                evidence.get("SpliceAI", "")
            )

            spliceai = choose_spliceai(
                spliceai_records,
                gene,
            )

            maximum_ds, maximum_effect = spliceai_maximum(
                spliceai
            )

            agreement = consequence_agreement(
                clean(row.get("consequence", "")),
                clean(snpeff.get("effect", "")),
            )

            if ann_records:
                variants_with_ann.add(variant)

            if spliceai_records:
                variants_with_spliceai.add(variant)

            if agreement == "yes":
                rows_with_vep_snpeff_agreement += 1

            output_row = {
                column: clean(row.get(column, ""))
                for column in base_columns
            }

            output_row.update(
                {
                    "snpeff_effect": clean(
                        snpeff.get("effect", "")
                    ),
                    "snpeff_impact": clean(
                        snpeff.get("impact", "")
                    ),
                    "snpeff_gene": clean(
                        snpeff.get("gene", "")
                    ),
                    "snpeff_transcript": clean(
                        snpeff.get("transcript", "")
                    ),
                    "snpeff_hgvsc": clean(
                        snpeff.get("hgvsc", "")
                    ),
                    "snpeff_hgvsp": clean(
                        snpeff.get("hgvsp", "")
                    ),
                    "snpeff_vep_agreement": agreement,
                    "spliceai_gene": clean(
                        spliceai.get("gene", "")
                    ),
                    "spliceai_ds_ag": clean(
                        spliceai.get("ds_ag", "")
                    ),
                    "spliceai_ds_al": clean(
                        spliceai.get("ds_al", "")
                    ),
                    "spliceai_ds_dg": clean(
                        spliceai.get("ds_dg", "")
                    ),
                    "spliceai_ds_dl": clean(
                        spliceai.get("ds_dl", "")
                    ),
                    "spliceai_max_ds": maximum_ds,
                    "spliceai_max_effect": maximum_effect,
                    "spliceai_prediction_present": (
                        "yes"
                        if spliceai_records
                        else "no"
                    ),
                    "score_before_phenotype": clean(
                        row.get("final_score", "")
                    ),
                }
            )

            output_rows.append(output_row)

    output_columns = base_columns + ADDED_COLUMNS

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

    unique_variants = {
        clean(row.get("variant", ""))
        for row in output_rows
        if clean(row.get("variant", ""))
    }

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(["candidate_rows", len(output_rows)])
        writer.writerow(
            ["unique_candidate_variants", len(unique_variants)]
        )
        writer.writerow(
            [
                "variants_with_snpeff_ANN",
                len(variants_with_ann),
            ]
        )
        writer.writerow(
            [
                "variants_with_spliceai_prediction",
                len(variants_with_spliceai),
            ]
        )
        writer.writerow(
            [
                "rows_with_vep_snpeff_agreement",
                rows_with_vep_snpeff_agreement,
            ]
        )
        writer.writerow(
            ["snpeff_points_added", "0"]
        )
        writer.writerow(
            ["spliceai_points_added", "0"]
        )
        writer.writerow(
            ["phenotype_scoring_included", "no"]
        )
        writer.writerow(
            [
                "output_table",
                str(output_table.relative_to(project_root)),
            ]
        )

    print("========================================")
    print("SMALL-VARIANT EVIDENCE INTEGRATION")
    print("========================================")
    print(f"Case ID:                    {case_id}")
    print(f"Candidate rows:             {len(output_rows)}")
    print(f"Unique candidate variants: {len(unique_variants)}")
    print(
        "Variants with SnpEff ANN:  "
        f"{len(variants_with_ann)}"
    )
    print(
        "Variants with SpliceAI:    "
        f"{len(variants_with_spliceai)}"
    )
    print()
    print("SnpEff scoring points:      0")
    print("SpliceAI scoring points:    0")
    print("Phenotype scoring:          not added yet")
    print()
    print(f"Output: {output_table}")
    print(f"QC:     {qc_file}")
    print()
    print(
        "SMALL-VARIANT EVIDENCE INTEGRATION "
        "COMPLETED SUCCESSFULLY"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# UNIVERSAL_RESOURCE_MODE_V1: official default with explicit resource override

import csv
import sys
from pathlib import Path


CONFIDENCE_POINTS = {
    "definitive": 4,
    "strong": 3,
    "moderate": 2,
    "limited": 1,
    "disputed": 0,
    "refuted": 0,
}


def clean(value: str) -> str:
    return value.strip() if value else ""


def load_g2p(path: Path) -> dict[str, list[dict[str, str]]]:
    """Load G2P records and group them by gene symbol."""

    gene_map: dict[str, list[dict[str, str]]] = {}

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            gene = clean(row.get("gene symbol", "")).upper()

            if not gene:
                continue

            confidence = clean(row.get("confidence", "")).lower()

            record = {
                "g2p_id": clean(row.get("g2p id", "")),
                "disease_name": clean(row.get("disease name", "")),
                "disease_mim": clean(row.get("disease mim", "")),
                "disease_mondo": clean(row.get("disease MONDO", "")),
                "allelic_requirement": clean(
                    row.get("allelic requirement", "")
                ),
                "confidence": confidence,
                "variant_consequence_model": clean(
                    row.get("variant consequence", "")
                ),
                "variant_types_model": clean(
                    row.get("variant types", "")
                ),
                "molecular_mechanism": clean(
                    row.get("molecular mechanism", "")
                ),
                "panel": clean(row.get("panel", "")),
                "last_review": clean(
                    row.get("date of last review", "")
                ),
                "gene_disease_score": str(
                    CONFIDENCE_POINTS.get(confidence, 0)
                ),
            }

            gene_map.setdefault(gene, []).append(record)

    return gene_map


def main() -> None:
    if len(sys.argv) not in {2, 3}:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/04_map_genes_to_diseases.py "
            "CASE_ID [G2P_RESOURCE_CSV]"
        )
        sys.exit(1)

    case_id = sys.argv[1]

    script_path = Path(__file__).resolve()
    project_root = script_path.parents[2]

    variant_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "annotated"
        / f"{case_id}.vep_best_transcripts.tsv"
    )

    g2p_file = (
        Path(sys.argv[2]).expanduser().resolve()
        if len(sys.argv) == 3
        else project_root
        / "resources"
        / "gene_disease"
        / "g2p"
        / "AllG2P.official.csv"
    )

    output_file = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.variant_gene_disease.tsv"
    )

    unmatched_file = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.genes_without_g2p_match.tsv"
    )

    qc_file = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.gene_disease_qc.tsv"
    )

    for required in [variant_table, g2p_file]:
        if not required.is_file():
            print(f"ERROR: Required file not found: {required}")
            sys.exit(1)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    g2p_map = load_g2p(g2p_file)

    output_rows: list[dict[str, str]] = []
    unmatched_rows: list[dict[str, str]] = []
    input_rows = 0
    matched_variants = set()
    matched_genes = set()
    diseases = set()

    with variant_table.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        for variant_row in reader:
            input_rows += 1

            gene = clean(variant_row.get("gene", "")).upper()
            matches = g2p_map.get(gene, [])

            if not gene or not matches:
                reason = (
                    "missing_gene_symbol"
                    if not gene
                    else "no_G2P_match"
                )

                unmatched_rows.append(
                    {
                        "case_id": case_id,
                        "variant": clean(
                            variant_row.get("variant", "")
                        ),
                        "gene": gene,
                        "consequence": clean(
                            variant_row.get(
                                "consequence",
                                "",
                            )
                        ),
                        "reason": reason,
                    }
                )

                # UNIVERSAL_RETENTION_FIX
                # G2P is supporting evidence, not a hard filter.
                fallback = dict(variant_row)

                fallback.update(
                    {
                        "case_id": case_id,
                        "gene": gene,
                        "g2p_id": "",
                        "disease_name": "",
                        "disease_mim": "",
                        "disease_mondo": "",
                        "allelic_requirement": "",
                        "confidence": "",
                        "variant_consequence_model": "",
                        "variant_types_model": "",
                        "molecular_mechanism": "",
                        "panel": "",
                        "last_review": "",
                        "gene_disease_score": "0",
                    }
                )

                output_rows.append(fallback)
                continue

            for disease in matches:
                combined = {
                    "case_id": case_id,
                    "sample": clean(
                        variant_row.get("sample", "")
                    ),
                    "variant": clean(
                        variant_row.get("variant", "")
                    ),
                    "vcf_id": clean(
                        variant_row.get("vcf_id", "")
                    ),
                    "genotype": clean(
                        variant_row.get("genotype", "")
                    ),
                    "zygosity": clean(
                        variant_row.get("zygosity", "")
                    ),
                    "depth_DP": clean(
                        variant_row.get("depth_DP", "")
                    ),
                    "genotype_quality_GQ": clean(
                        variant_row.get(
                            "genotype_quality_GQ",
                            "",
                        )
                    ),
                    "allelic_depth_AD": clean(
                        variant_row.get(
                            "allelic_depth_AD",
                            "",
                        )
                    ),
                    "allele_balance": clean(
                        variant_row.get(
                            "allele_balance",
                            "",
                        )
                    ),
                    "genotype_quality_status": clean(
                        variant_row.get(
                            "genotype_quality_status",
                            "",
                        )
                    ),
                    "genotype_quality_notes": clean(
                        variant_row.get(
                            "genotype_quality_notes",
                            "",
                        )
                    ),
                    "gene": gene,
                    "consequence": clean(
                        variant_row.get("consequence", "")
                    ),
                    "impact": clean(
                        variant_row.get("impact", "")
                    ),
                    "hgvsc": clean(
                        variant_row.get("hgvsc", "")
                    ),
                    "hgvsp": clean(
                        variant_row.get("hgvsp", "")
                    ),
                    "gnomad_exome_af": clean(
                        variant_row.get("gnomad_exome_af", "")
                    ),
                    "gnomad_genome_af": clean(
                        variant_row.get("gnomad_genome_af", "")
                    ),
                    "max_af": clean(
                        variant_row.get("max_af", "")
                    ),
                    **disease,
                }

                output_rows.append(combined)
                matched_variants.add(combined["variant"])
                matched_genes.add(gene)
                diseases.add(disease["disease_name"])

    output_columns = [
        "case_id",
        "sample",
        "variant",
        "vcf_id",
        "genotype",
        "zygosity",
        "depth_DP",
        "genotype_quality_GQ",
        "allelic_depth_AD",
        "allele_balance",
        "genotype_quality_status",
        "genotype_quality_notes",
        "gene",
        "consequence",
        "impact",
        "hgvsc",
        "hgvsp",
        "gnomad_exome_af",
        "gnomad_genome_af",
        "max_af",
        "g2p_id",
        "disease_name",
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
    ]

    with output_file.open(
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

    unmatched_columns = [
        "case_id",
        "variant",
        "gene",
        "consequence",
        "reason",
    ]

    with unmatched_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=unmatched_columns,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(unmatched_rows)

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(["input_variant_rows", input_rows])
        writer.writerow(
            ["matched_unique_variants", len(matched_variants)]
        )
        writer.writerow(
            ["matched_unique_genes", len(matched_genes)]
        )
        writer.writerow(
            ["candidate_diseases", len(diseases)]
        )
        writer.writerow(
            ["variant_disease_rows", len(output_rows)]
        )
        writer.writerow(
            ["unmatched_variant_rows", len(unmatched_rows)]
        )
        writer.writerow(
            [
                "output_table",
                str(output_file.relative_to(project_root)),
            ]
        )

    print("========================================")
    print("GENE TO DISEASE MAPPING")
    print("========================================")
    print(f"Case ID:                  {case_id}")
    print(f"Input variant rows:       {input_rows}")
    print(f"Matched unique variants:  {len(matched_variants)}")
    print(f"Matched unique genes:     {len(matched_genes)}")
    print(f"Candidate diseases:       {len(diseases)}")
    print(f"Variant-disease rows:     {len(output_rows)}")
    print(f"Unmatched variant rows:   {len(unmatched_rows)}")
    print()
    print(f"Output: {output_file}")
    print(f"QC:     {qc_file}")
    print()
    print("GENE TO DISEASE MAPPING COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()

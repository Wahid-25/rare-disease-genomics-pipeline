#!/usr/bin/env python3
"""Add conservative gene-level recessive and compound-heterozygous evidence.

This stage augments the active small-variant candidate table after phenotype
scoring. It does not infer trans configuration from unphased variants.
Confirmed trans requires opposite haplotypes within a shared PS or PID block.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

from inheritance_utils import classify_inheritance_model


PHASE_FIELDS = [
    "phase_set_PS",
    "phase_id_PID",
    "phased_genotype_PGT",
    "genotype_is_phased",
]

ADDED_FIELDS = PHASE_FIELDS + [
    "gene_level_inheritance_status",
    "gene_level_variant_count",
    "compound_partner_variants",
    "compound_phase_evidence",
    "compound_score_adjustment",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def safe_int(value: object, default: int = 0) -> int:
    try:
        return int(float(clean(value)))
    except (TypeError, ValueError):
        return default


def priority_label(final_score: int, clinvar_points: int) -> str:
    if clinvar_points < 0:
        return "deprioritized"
    if final_score >= 17:
        return "high_priority_candidate"
    if final_score >= 10:
        return "moderate_priority_candidate"
    return "low_priority_candidate"


def stable_disease_key(row: dict[str, str]) -> str:
    for field in (
        "disease_mim",
        "disease_mondo",
        "g2p_disease_name",
        "candidate_disease",
    ):
        value = clean(row.get(field))
        if value:
            return f"{field}:{value.lower()}"
    return "disease:unspecified"


def phase_genotype(row: dict[str, str]) -> str:
    pgt = clean(row.get("phased_genotype_PGT"))
    gt = clean(row.get("genotype"))

    if "|" in pgt and "." not in pgt:
        return pgt

    if "|" in gt and "." not in gt:
        return gt

    return ""


def alternate_haplotype(row: dict[str, str]) -> int | None:
    genotype = phase_genotype(row)

    if not genotype:
        return None

    alleles = genotype.split("|")

    if len(alleles) != 2:
        return None

    non_reference = [
        index
        for index, allele in enumerate(alleles)
        if allele not in {"", ".", "0"}
    ]
    reference = [
        index
        for index, allele in enumerate(alleles)
        if allele == "0"
    ]

    if len(non_reference) != 1 or len(reference) != 1:
        return None

    return non_reference[0]


def phase_blocks(row: dict[str, str]) -> set[str]:
    blocks: set[str] = set()

    ps = clean(row.get("phase_set_PS"))
    pid = clean(row.get("phase_id_PID"))

    if ps and ps != ".":
        blocks.add(f"PS:{ps}")

    if pid and pid != ".":
        blocks.add(f"PID:{pid}")

    return blocks


def pair_phase_evidence(
    first: dict[str, str],
    second: dict[str, str],
) -> tuple[str, str]:
    """Classify phase evidence for two heterozygous variants."""

    shared_blocks = phase_blocks(first) & phase_blocks(second)
    first_haplotype = alternate_haplotype(first)
    second_haplotype = alternate_haplotype(second)

    pair = (
        f"{clean(first.get('variant'))}|"
        f"{clean(second.get('variant'))}"
    )

    if (
        shared_blocks
        and first_haplotype is not None
        and second_haplotype is not None
    ):
        block = sorted(shared_blocks)[0]

        if first_haplotype != second_haplotype:
            return (
                "confirmed_trans",
                f"pair={pair};shared_block={block};"
                "opposite_haplotypes",
            )

        return (
            "likely_cis",
            f"pair={pair};shared_block={block};"
            "same_haplotype",
        )

    return (
        "phase_not_available",
        f"pair={pair};unphased_or_no_shared_phase_block",
    )


def phase_index_from_rows(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str], dict[str, str]]:
    index: dict[tuple[str, str], dict[str, str]] = {}

    for row in rows:
        key = (
            clean(row.get("sample")),
            clean(row.get("variant")),
        )

        if key[1] and key not in index:
            index[key] = row

    return index


def enrich_phase_fields(
    rows: list[dict[str, str]],
    phase_index: dict[tuple[str, str], dict[str, str]],
) -> None:
    variant_fallback: dict[str, dict[str, str]] = {}

    for (_sample, variant), phase_row in phase_index.items():
        variant_fallback.setdefault(variant, phase_row)

    for row in rows:
        key = (
            clean(row.get("sample")),
            clean(row.get("variant")),
        )
        phase_row = phase_index.get(key)

        if phase_row is None:
            phase_row = variant_fallback.get(key[1], {})

        for field in PHASE_FIELDS:
            row[field] = clean(phase_row.get(field))

        if not row["genotype_is_phased"]:
            row["genotype_is_phased"] = (
                "yes"
                if "|" in clean(row.get("genotype"))
                else "no"
            )


def recessive_group_key(
    row: dict[str, str],
) -> tuple[str, str, str, str, str] | None:
    inheritance = clean(
        row.get("inheritance")
        or row.get("allelic_requirement")
    )
    model = classify_inheritance_model(inheritance).model

    if model not in {
        "autosomal_recessive",
        "x_linked_biallelic",
        "x_linked_recessive",
    }:
        return None

    return (
        clean(row.get("case_id")),
        clean(row.get("sample")),
        clean(row.get("gene")).upper(),
        stable_disease_key(row),
        model,
    )


def unique_variant_rows(
    indexed_rows: list[tuple[int, dict[str, str]]],
) -> dict[str, dict[str, str]]:
    variants: dict[str, dict[str, str]] = {}

    for _index, row in indexed_rows:
        variant = clean(row.get("variant"))

        if variant and variant not in variants:
            variants[variant] = row

    return variants


def status_for_heterozygous_variant(
    target: dict[str, str],
    other_rows: list[dict[str, str]],
) -> tuple[str, str]:
    if not other_rows:
        return (
            "single_recessive_allele",
            "only_one_heterozygous_variant_in_gene_disease_group",
        )

    evaluations = [
        pair_phase_evidence(target, partner)
        for partner in other_rows
    ]

    confirmed = [
        evidence
        for status, evidence in evaluations
        if status == "confirmed_trans"
    ]

    if confirmed:
        return "confirmed_trans", confirmed[0]

    uncertain = [
        evidence
        for status, evidence in evaluations
        if status == "phase_not_available"
    ]

    if uncertain:
        return (
            "possible_compound_heterozygous",
            uncertain[0],
        )

    cis = [
        evidence
        for status, evidence in evaluations
        if status == "likely_cis"
    ]

    if cis and len(cis) == len(evaluations):
        return "likely_cis", cis[0]

    return (
        "possible_compound_heterozygous",
        "multiple_heterozygous_variants_without_confirmed_trans_phase",
    )


def score_target(
    status: str,
    current_points: int,
) -> tuple[int, int]:
    if status in {
        "confirmed_trans",
        "homozygous_biallelic",
        "hemizygous_x_linked",
    }:
        target = max(current_points, 3)
    elif status == "possible_compound_heterozygous":
        target = max(current_points, 1)
    else:
        target = current_points

    return target, target - current_points


def inheritance_match_for_status(
    status: str,
    previous: str,
) -> str:
    mapping = {
        "confirmed_trans": (
            "compatible_compound_heterozygous_trans"
        ),
        "possible_compound_heterozygous": (
            "possible_compound_heterozygous_unphased"
        ),
        "likely_cis": "likely_cis_not_biallelic",
        "single_recessive_allele": "single_recessive_allele",
        "homozygous_biallelic": (
            "compatible_biallelic_homozygous"
        ),
        "hemizygous_x_linked": (
            "compatible_hemizygous_x_linked"
        ),
    }
    return mapping.get(status, previous)


def apply_compound_evidence(
    rows: list[dict[str, str]],
    phase_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, int]]:
    phase_index = phase_index_from_rows(phase_rows)
    enrich_phase_fields(rows, phase_index)

    groups: dict[
        tuple[str, str, str, str, str],
        list[tuple[int, dict[str, str]]],
    ] = defaultdict(list)

    for index, row in enumerate(rows):
        for field in ADDED_FIELDS:
            row.setdefault(field, "")

        group_key = recessive_group_key(row)

        if group_key is None:
            row["gene_level_inheritance_status"] = (
                "not_applicable_non_recessive"
            )
            row["gene_level_variant_count"] = "0"
            row["compound_score_adjustment"] = "0"
            continue

        groups[group_key].append((index, row))

    counts: dict[str, int] = defaultdict(int)

    for indexed_rows in groups.values():
        variants = unique_variant_rows(indexed_rows)
        qualifying = {
            variant: row
            for variant, row in variants.items()
            if clean(row.get("zygosity")) in {
                "heterozygous",
                "homozygous_alt",
                "hemizygous_or_haploid_alt",
            }
        }
        heterozygous = {
            variant: row
            for variant, row in qualifying.items()
            if clean(row.get("zygosity")) == "heterozygous"
        }

        qualifying_count = len(qualifying)

        for _index, row in indexed_rows:
            variant = clean(row.get("variant"))
            zygosity = clean(row.get("zygosity"))
            row["gene_level_variant_count"] = str(
                qualifying_count
            )

            if zygosity == "homozygous_alt":
                status = "homozygous_biallelic"
                evidence = (
                    "homozygous_alternate_genotype;"
                    "compound_pair_not_required"
                )
                partners: list[str] = []
            elif zygosity == "hemizygous_or_haploid_alt":
                model = classify_inheritance_model(
                    clean(row.get("inheritance"))
                ).model

                if model in {
                    "x_linked_biallelic",
                    "x_linked_recessive",
                }:
                    status = "hemizygous_x_linked"
                    evidence = (
                        "haploid_or_hemizygous_alternate_call"
                    )
                else:
                    status = "single_recessive_allele"
                    evidence = (
                        "haploid_call_not_sufficient_for_"
                        "autosomal_biallelic_model"
                    )
                partners = []
            elif zygosity == "heterozygous":
                partners = sorted(
                    partner
                    for partner in heterozygous
                    if partner != variant
                )
                status, evidence = (
                    status_for_heterozygous_variant(
                        row,
                        [
                            heterozygous[partner]
                            for partner in partners
                        ],
                    )
                )
            else:
                status = "biallelic_status_not_evaluable"
                evidence = (
                    "genotype_not_eligible_for_recessive_aggregation"
                )
                partners = []

            row["gene_level_inheritance_status"] = status
            row["compound_partner_variants"] = ",".join(
                partners
            )
            row["compound_phase_evidence"] = evidence

            current_points = safe_int(
                row.get("inheritance_points")
            )
            new_points, adjustment = score_target(
                status,
                current_points,
            )

            row["inheritance_points"] = str(new_points)
            row["compound_score_adjustment"] = str(adjustment)
            row["inheritance_match"] = (
                inheritance_match_for_status(
                    status,
                    clean(row.get("inheritance_match")),
                )
            )

            if adjustment:
                row["final_score"] = str(
                    safe_int(row.get("final_score"))
                    + adjustment
                )

            row["priority"] = priority_label(
                safe_int(row.get("final_score")),
                safe_int(row.get("clinvar_points")),
            )

            counts[status] += 1

    rows.sort(
        key=lambda row: (
            -safe_int(row.get("final_score")),
            -safe_int(row.get("clinvar_points")),
            clean(row.get("gene")),
            clean(row.get("candidate_disease")),
            clean(row.get("variant")),
        )
    )

    for rank, row in enumerate(rows, start=1):
        row["rank"] = str(rank)

    counts["candidate_rows"] = len(rows)
    counts["recessive_groups"] = len(groups)
    return rows, dict(counts)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python3 "
            "pipeline/case_workflow/"
            "10b_add_compound_heterozygous_evidence.py CASE_ID"
        )

    case_id = sys.argv[1]
    project_root = Path(__file__).resolve().parents[2]

    final_dir = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
    )
    input_table = (
        final_dir
        / f"{case_id}.variant_gene_disease_scores.final.tsv"
    )
    phase_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "annotated"
        / f"{case_id}.vep_best_transcripts.tsv"
    )
    qc_file = (
        final_dir
        / f"{case_id}.compound_heterozygous_qc.tsv"
    )

    for required in (input_table, phase_table):
        if not required.is_file():
            raise SystemExit(
                f"ERROR: Required file missing: {required}"
            )

    with input_table.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        columns = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]

    with phase_table.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        phase_rows = list(
            csv.DictReader(handle, delimiter="\t")
        )

    for field in ADDED_FIELDS:
        if field not in columns:
            columns.append(field)

    output_rows, metrics = apply_compound_evidence(
        rows,
        phase_rows,
    )

    temporary = input_table.with_suffix(
        input_table.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(output_rows)

    temporary.replace(input_table)

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(
            handle,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(
            ["candidate_rows", metrics.get("candidate_rows", 0)]
        )
        writer.writerow(
            ["recessive_groups", metrics.get("recessive_groups", 0)]
        )
        for status in (
            "homozygous_biallelic",
            "confirmed_trans",
            "possible_compound_heterozygous",
            "likely_cis",
            "single_recessive_allele",
            "hemizygous_x_linked",
            "biallelic_status_not_evaluable",
        ):
            writer.writerow(
                [f"{status}_rows", metrics.get(status, 0)]
            )
        writer.writerow(
            [
                "phase_policy",
                "confirmed_trans_requires_same_PS_or_PID_"
                "and_opposite_haplotypes",
            ]
        )
        writer.writerow(
            [
                "unphased_pair_policy",
                "possible_only_manual_review_required",
            ]
        )
        writer.writerow(
            [
                "output_table",
                str(input_table.relative_to(project_root)),
            ]
        )

    print("========================================")
    print("COMPOUND-HETEROZYGOUS AGGREGATION")
    print("========================================")
    print(f"Case ID:                    {case_id}")
    print(
        "Candidate rows:             "
        f"{metrics.get('candidate_rows', 0)}"
    )
    print(
        "Recessive groups:           "
        f"{metrics.get('recessive_groups', 0)}"
    )
    print(
        "Confirmed trans rows:       "
        f"{metrics.get('confirmed_trans', 0)}"
    )
    print(
        "Possible compound rows:     "
        f"{metrics.get('possible_compound_heterozygous', 0)}"
    )
    print(
        "Likely cis rows:            "
        f"{metrics.get('likely_cis', 0)}"
    )
    print(f"Output:                     {input_table}")
    print(f"QC:                         {qc_file}")
    print()
    print(
        "NOTE: Unphased pairs are never promoted to confirmed trans."
    )


if __name__ == "__main__":
    main()

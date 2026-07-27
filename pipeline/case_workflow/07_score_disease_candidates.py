#!/usr/bin/env python3
from inheritance_utils import score_small_variant_inheritance

import csv
import gzip
import re
import sys
from pathlib import Path
from urllib.parse import unquote


LOSS_OF_FUNCTION_TERMS = {
    "frameshift_variant",
    "stop_gained",
    "start_lost",
    "splice_acceptor_variant",
    "splice_donor_variant",
    "transcript_ablation",
}


def clean(value: str) -> str:
    return value.strip() if value else ""


def open_vcf(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def parse_info(info_text: str) -> dict[str, str]:
    result = {}

    if info_text in {"", "."}:
        return result

    for item in info_text.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            result[key] = unquote(value)
        else:
            result[item] = "true"

    return result


def load_clinvar_vcf(path: Path) -> dict[str, dict[str, str]]:
    """Index ClinVar annotations by CHROM, POS, REF and ALT."""

    records = {}

    with open_vcf(path) as handle:
        for line in handle:
            if line.startswith("#"):
                continue

            fields = line.rstrip("\n").split("\t")

            if len(fields) < 8:
                continue

            chrom, pos, vcf_id, ref, alt = fields[:5]
            info = parse_info(fields[7])

            key = f"{chrom}:{pos}:{ref}>{alt}"

            records[key] = {
                "clinvar_id": vcf_id,
                "clinvar_significance": clean(
                    info.get("CLNSIG", "")
                ),
                "clinvar_conditions": clean(
                    info.get("CLNDN", "")
                ),
                "clinvar_review_status": clean(
                    info.get("CLNREVSTAT", "")
                ),
                "clinvar_disease_ids": clean(
                    info.get("CLNDISDB", "")
                ),
                "clinvar_hgvs": clean(
                    info.get("CLNHGVS", "")
                ),
                "clinvar_geneinfo": clean(
                    info.get("GENEINFO", "")
                ),
            }

    return records


def load_clinpgx(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Load optional ClinPGx matches by variant and gene."""

    results = {}

    if not path.is_file():
        return results

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        for row in reader:
            key = (
                clean(row.get("variant", "")),
                clean(row.get("gene", "")).upper(),
            )
            results[key] = row

    return results


def clinvar_classification_points(value: str) -> int:
    normalized = value.lower().replace(" ", "_")

    tokens = {
        token.strip()
        for token in re.split(r"[|/,;]+", normalized)
        if token.strip()
    }

    if any("conflicting" in token for token in tokens):
        return 0

    if "pathogenic" in tokens:
        return 5

    if "likely_pathogenic" in tokens:
        return 4

    if "uncertain_significance" in tokens:
        return 0

    if "likely_benign" in tokens:
        return -3

    if "benign" in tokens:
        return -4

    return 0


def clinvar_review_points(value: str) -> int:
    normalized = value.lower()

    if (
        "practice_guideline" in normalized
        or "expert_panel" in normalized
    ):
        return 2

    if (
        "multiple_submitters" in normalized
        and "no_conflicts" in normalized
    ):
        return 1

    return 0


def consequence_points(consequence: str, impact: str) -> int:
    terms = set(consequence.lower().split("&"))

    if terms & LOSS_OF_FUNCTION_TERMS:
        return 3

    if impact.upper() == "MODERATE":
        return 2

    if impact.upper() == "HIGH":
        return 3

    return 0


def parse_frequency(value: str):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def rarity_points(exome_af: str, genome_af: str) -> tuple[int, str]:
    frequencies = [
        value
        for value in [
            parse_frequency(exome_af),
            parse_frequency(genome_af),
        ]
        if value is not None
    ]

    if not frequencies:
        return 0, "frequency_not_available"

    frequency = max(frequencies)

    if frequency <= 0.001:
        return 2, f"rare_AF={frequency:g}"

    if frequency <= 0.01:
        return 1, f"low_frequency_AF={frequency:g}"

    if frequency > 0.05:
        return -2, f"common_AF={frequency:g}"

    return 0, f"AF={frequency:g}"


def inheritance_points(
    allelic_requirement: str,
    zygosity: str,
) -> tuple[int, str]:
    # Shared universal inheritance model.
    return score_small_variant_inheritance(
        allelic_requirement,
        zygosity,
    )

def mechanism_points(
    molecular_mechanism: str,
    variant_model: str,
    consequence: str,
) -> tuple[int, str]:
    mechanism = (
        molecular_mechanism
        + " "
        + variant_model
    ).lower()

    consequence_terms = set(consequence.lower().split("&"))

    if (
        "loss of function" in mechanism
        or "absent gene product" in mechanism
    ):
        if consequence_terms & LOSS_OF_FUNCTION_TERMS:
            return 3, "loss_of_function_match"

        return 0, "loss_of_function_model_without_lof_variant"

    if (
        "gain of function" in mechanism
        or "activating" in mechanism
    ):
        if (
            "missense_variant" in consequence_terms
            or "inframe_insertion" in consequence_terms
            or "inframe_deletion" in consequence_terms
        ):
            return 2, "possible_gain_of_function_match"

        return 0, "gain_of_function_model_not_confirmed"

    if "altered gene product sequence" in mechanism:
        if (
            "missense_variant" in consequence_terms
            or "inframe_insertion" in consequence_terms
            or "inframe_deletion" in consequence_terms
        ):
            return 2, "altered_sequence_match"

    return 0, "mechanism_match_not_scored"


def preferred_clinvar_condition(value: str) -> str:
    """Choose a readable, non-generic ClinVar condition."""

    conditions = [
        condition.strip()
        for condition in value.split("|")
        if condition.strip()
    ]

    generic_patterns = [
        "not_provided",
        "not_specified",
        "inborn_genetic_diseases",
        "intellectual_disability",
        "related_disorder",
    ]

    for condition in conditions:
        lower = condition.lower()

        if not any(
            pattern in lower
            for pattern in generic_patterns
        ):
            return condition.replace("_", " ")

    if conditions:
        return conditions[0].replace("_", " ")

    return ""


def choose_candidate_disease(
    g2p_disease: str,
    clinvar_condition: str,
) -> str:
    """Choose the disease label for one gene-disease candidate row.

    A G2P row is disease-specific, whereas ClinVar conditions describe
    the variant and may contain multiple or differently ordered disorders.
    Therefore ClinVar must not overwrite an available G2P disease label.
    """

    g2p_label = clean(g2p_disease)
    if g2p_label:
        return g2p_label

    return clean(clinvar_condition)

def priority_label(score: int, clinvar_points: int) -> str:
    if clinvar_points < 0:
        return "deprioritized"

    if score >= 17:
        return "high_priority_candidate"

    if score >= 10:
        return "moderate_priority_candidate"

    return "low_priority_candidate"


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/"
            "07_score_disease_candidates.py CASE_ID"
        )
        sys.exit(1)

    case_id = sys.argv[1]

    script_path = Path(__file__).resolve()
    project_root = script_path.parents[2]

    disease_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.variant_gene_disease.tsv"
    )

    clinvar_vcf = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "annotated"
        / f"{case_id}.vep.clinvar.vcf.gz"
    )

    clinpgx_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "clinpgx"
        / f"{case_id}.clinpgx_matches.tsv"
    )

    output_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.variant_gene_disease_scores.tsv"
    )

    qc_file = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.scoring_qc.tsv"
    )

    for required in [disease_table, clinvar_vcf]:
        if not required.is_file():
            print(f"ERROR: Required file not found: {required}")
            sys.exit(1)

    clinvar_records = load_clinvar_vcf(clinvar_vcf)
    clinpgx_records = load_clinpgx(clinpgx_table)

    scored_rows = []

    with disease_table.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        for row in reader:
            variant = clean(row.get("variant", ""))
            gene = clean(row.get("gene", "")).upper()

            clinvar = clinvar_records.get(variant, {})
            clinpgx = clinpgx_records.get(
                (variant, gene),
                {},
            )

            gene_disease_score = int(
                clean(row.get("gene_disease_score", "0"))
                or 0
            )

            clinvar_score = clinvar_classification_points(
                clinvar.get("clinvar_significance", "")
            )

            review_score = clinvar_review_points(
                clinvar.get("clinvar_review_status", "")
            )

            effect_score = consequence_points(
                clean(row.get("consequence", "")),
                clean(row.get("impact", "")),
            )

            population_score, population_note = rarity_points(
                clean(row.get("gnomad_exome_af", "")),
                clean(row.get("gnomad_genome_af", "")),
            )

            inherit_score, inheritance_match = inheritance_points(
                clean(row.get("allelic_requirement", "")),
                clean(row.get("zygosity", "")),
            )

            mechanism_score, mechanism_match = mechanism_points(
                clean(row.get("molecular_mechanism", "")),
                clean(
                    row.get("variant_consequence_model", "")
                ),
                clean(row.get("consequence", "")),
            )

            # Phenotype/HPO scoring will be added in the next stage.
            phenotype_score = 0

            final_score = (
                gene_disease_score
                + clinvar_score
                + review_score
                + effect_score
                + population_score
                + inherit_score
                + mechanism_score
                + phenotype_score
            )

            clinvar_condition = preferred_clinvar_condition(
                clinvar.get("clinvar_conditions", "")
            )

            g2p_disease = clean(row.get("disease_name", ""))

            candidate_disease = choose_candidate_disease(
                g2p_disease,
                clinvar_condition,
            )

            scored_rows.append(
                {
                    "case_id": case_id,
                    "sample": clean(row.get("sample", "")),
                    "variant": variant,
                    "vcf_id": clean(row.get("vcf_id", "")),
                    "gene": gene,
                    "candidate_disease": candidate_disease,
                    "g2p_disease_name": g2p_disease,
                    "disease_mim": clean(
                        row.get("disease_mim", "")
                    ),
                    "disease_mondo": clean(
                        row.get("disease_mondo", "")
                    ),
                    "inheritance": clean(
                        row.get("allelic_requirement", "")
                    ),
                    "genotype": clean(row.get("genotype", "")),
                    "zygosity": clean(row.get("zygosity", "")),
                    "depth_DP": clean(
                        row.get("depth_DP", "")
                    ),
                    "genotype_quality_GQ": clean(
                        row.get("genotype_quality_GQ", "")
                    ),
                    "allelic_depth_AD": clean(
                        row.get("allelic_depth_AD", "")
                    ),
                    "allele_balance": clean(
                        row.get("allele_balance", "")
                    ),
                    "genotype_quality_status": clean(
                        row.get(
                            "genotype_quality_status",
                            "",
                        )
                    ),
                    "genotype_quality_notes": clean(
                        row.get(
                            "genotype_quality_notes",
                            "",
                        )
                    ),
                    "consequence": clean(
                        row.get("consequence", "")
                    ),
                    "impact": clean(row.get("impact", "")),
                    "hgvsc": clean(row.get("hgvsc", "")),
                    "hgvsp": clean(row.get("hgvsp", "")),
                    "clinvar_significance": clinvar.get(
                        "clinvar_significance",
                        "",
                    ),
                    "clinvar_conditions": clinvar.get(
                        "clinvar_conditions",
                        "",
                    ),
                    "clinvar_review_status": clinvar.get(
                        "clinvar_review_status",
                        "",
                    ),
                    "gnomad_exome_af": clean(
                        row.get("gnomad_exome_af", "")
                    ),
                    "gnomad_genome_af": clean(
                        row.get("gnomad_genome_af", "")
                    ),
                    "max_af": clean(row.get("max_af", "")),
                    "population_note": population_note,
                    "g2p_confidence": clean(
                        row.get("confidence", "")
                    ),
                    "molecular_mechanism": clean(
                        row.get("molecular_mechanism", "")
                    ),
                    "gene_disease_points": gene_disease_score,
                    "clinvar_points": clinvar_score,
                    "clinvar_review_points": review_score,
                    "consequence_points": effect_score,
                    "rarity_points": population_score,
                    "inheritance_points": inherit_score,
                    "mechanism_points": mechanism_score,
                    "phenotype_points": phenotype_score,
                    "final_score": final_score,
                    "priority": priority_label(
                        final_score,
                        clinvar_score,
                    ),
                    "inheritance_match": inheritance_match,
                    "mechanism_match": mechanism_match,
                    "clinpgx_status": clean(
                        clinpgx.get("clinpgx_status", "")
                    ),
                    "clinpgx_gene_id": clean(
                        clinpgx.get("clinpgx_gene_id", "")
                    ),
                    "clinpgx_variant_id": clean(
                        clinpgx.get(
                            "clinpgx_variant_id",
                            "",
                        )
                    ),
                }
            )

    scored_rows.sort(
        key=lambda row: (
            -int(row["final_score"]),
            -int(row["clinvar_points"]),
            row["gene"],
            row["candidate_disease"],
        )
    )

    for rank, row in enumerate(scored_rows, start=1):
        row["rank"] = rank

    columns = [
        "rank",
        "case_id",
        "sample",
        "variant",
        "vcf_id",
        "gene",
        "candidate_disease",
        "g2p_disease_name",
        "disease_mim",
        "disease_mondo",
        "inheritance",
        "genotype",
        "zygosity",
        "depth_DP",
        "genotype_quality_GQ",
        "allelic_depth_AD",
        "allele_balance",
        "genotype_quality_status",
        "genotype_quality_notes",
        "consequence",
        "impact",
        "hgvsc",
        "hgvsp",
        "clinvar_significance",
        "clinvar_conditions",
        "clinvar_review_status",
        "gnomad_exome_af",
        "gnomad_genome_af",
        "max_af",
        "population_note",
        "g2p_confidence",
        "molecular_mechanism",
        "gene_disease_points",
        "clinvar_points",
        "clinvar_review_points",
        "consequence_points",
        "rarity_points",
        "inheritance_points",
        "mechanism_points",
        "phenotype_points",
        "final_score",
        "priority",
        "inheritance_match",
        "mechanism_match",
        "clinpgx_status",
        "clinpgx_gene_id",
        "clinpgx_variant_id",
    ]

    with output_table.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(scored_rows)

    high_priority = sum(
        row["priority"] == "high_priority_candidate"
        for row in scored_rows
    )

    genotype_qc_pass_rows = sum(
        row.get("genotype_quality_status")
        == "pass_basic_qc"
        for row in scored_rows
    )

    genotype_qc_review_rows = sum(
        row.get(
            "genotype_quality_status",
            "",
        ).startswith("review")
        for row in scored_rows
    )

    genotype_qc_not_evaluable_rows = sum(
        row.get("genotype_quality_status")
        in {
            "",
            "not_evaluable",
            "not_applicable_site_only",
        }
        for row in scored_rows
    )

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(["scored_rows", len(scored_rows)])
        writer.writerow(
            ["high_priority_candidates", high_priority]
        )
        writer.writerow(
            [
                "genotype_QC_pass_candidate_rows",
                genotype_qc_pass_rows,
            ]
        )
        writer.writerow(
            [
                "genotype_QC_review_candidate_rows",
                genotype_qc_review_rows,
            ]
        )
        writer.writerow(
            [
                "genotype_QC_not_evaluable_rows",
                genotype_qc_not_evaluable_rows,
            ]
        )
        writer.writerow(
            [
                "genotype_quality_points_added",
                "0",
            ]
        )
        writer.writerow(
            [
                "phenotype_scoring_included",
                "no",
            ]
        )
        writer.writerow(
            [
                "output_table",
                str(output_table.relative_to(project_root)),
            ]
        )

    print("========================================")
    print("DISEASE CANDIDATE SCORING")
    print("========================================")
    print(f"Case ID:                  {case_id}")
    print(f"Scored candidate rows:    {len(scored_rows)}")
    print(f"High-priority candidates: {high_priority}")
    print(f"Genotype QC pass rows:    {genotype_qc_pass_rows}")
    print(f"Genotype QC review rows:  {genotype_qc_review_rows}")
    print("Genotype quality points:  0")
    print("Phenotype scoring:        not added yet")
    print()
    print(f"Output: {output_table}")
    print(f"QC:     {qc_file}")
    print()
    print("DISEASE CANDIDATE SCORING COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()

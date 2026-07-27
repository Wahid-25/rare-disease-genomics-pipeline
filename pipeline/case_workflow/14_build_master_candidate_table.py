#!/usr/bin/env python3

import csv
import gzip
import sys
from pathlib import Path
from urllib.parse import unquote


SMALL_VARIANT_MAX_SCORE = 27
CNV_MAX_SCORE = 28

PRIORITY_ORDER = {
    "high_priority_candidate": 3,
    "moderate_priority_candidate": 2,
    "low_priority_candidate": 1,
    "deprioritized": 0,
}


def clean(value) -> str:
    return str(value).strip() if value is not None else ""


def safe_float(value, default=0.0) -> float:
    try:
        return float(clean(value))
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0) -> int:
    try:
        return int(float(clean(value)))
    except (TypeError, ValueError):
        return default


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


def load_clingen_vcf(path: Path) -> dict[str, dict[str, str]]:
    """
    Load ClinGen dosage fields from the final cumulative small-variant VCF.
    """

    records = {}

    if not path.is_file():
        return records

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

            records[key] = {
                "clingen_region": clean(
                    info.get("CLINGEN_REGION", "")
                ),
                "clingen_haplo": clean(
                    info.get("CLINGEN_HAPLO", "")
                ),
                "clingen_triplo": clean(
                    info.get("CLINGEN_TRIPLO", "")
                ),
            }

    return records


def normalized_score(score: float, maximum: float) -> float:
    if maximum <= 0:
        return 0.0

    result = (score / maximum) * 100

    return max(0.0, min(100.0, result))


def small_variant_evidence_summary(
    row: dict[str, str],
    clingen: dict[str, str],
) -> str:
    evidence = []

    clinvar = clean(row.get("clinvar_significance"))

    if clinvar:
        evidence.append(f"ClinVar={clinvar}")

    confidence = clean(row.get("g2p_confidence"))

    if confidence:
        evidence.append(f"G2P={confidence}")

    consequence = clean(row.get("consequence"))

    if consequence:
        evidence.append(f"Consequence={consequence}")

    zygosity = clean(row.get("zygosity"))

    if zygosity:
        evidence.append(f"Zygosity={zygosity}")

    depth = clean(row.get("depth_DP"))

    if depth:
        evidence.append(f"DP={depth}")

    genotype_quality = clean(
        row.get("genotype_quality_GQ")
    )

    if genotype_quality:
        evidence.append(f"GQ={genotype_quality}")

    allelic_depth = clean(
        row.get("allelic_depth_AD")
    )

    if allelic_depth:
        evidence.append(f"AD={allelic_depth}")

    allele_balance = clean(
        row.get("allele_balance")
    )

    if allele_balance:
        evidence.append(
            f"Allele_balance={allele_balance}"
        )

    quality_status = clean(
        row.get("genotype_quality_status")
    )

    if quality_status:
        evidence.append(
            f"Genotype_QC={quality_status}"
        )

    hpo_matches = clean(
        row.get("matched_hpo_count")
    )

    if hpo_matches:
        evidence.append(
            f"HPO_matches={hpo_matches}"
        )

    spliceai = clean(row.get("spliceai_max_ds"))

    if spliceai:
        evidence.append(
            f"SpliceAI_max={spliceai}"
        )

    clingen_region = clean(
        clingen.get("clingen_region")
    )

    if clingen_region:
        evidence.append(
            f"ClinGen={clingen_region}"
        )

    gene_level_status = clean(
        row.get("gene_level_inheritance_status")
    )

    if gene_level_status:
        evidence.append(
            f"Gene_level_inheritance={gene_level_status}"
        )

    compound_partners = clean(
        row.get("compound_partner_variants")
    )

    if compound_partners:
        evidence.append(
            f"Compound_partners={compound_partners}"
        )

    compound_phase = clean(
        row.get("compound_phase_evidence")
    )

    if compound_phase:
        evidence.append(
            f"Compound_phase={compound_phase}"
        )

    return "; ".join(evidence)


def small_variant_interpretation_note(
    row: dict[str, str],
) -> str:
    base = (
        "Small-variant prioritization score; "
        "genotype-quality fields are technical "
        "screening evidence and do not add "
        "ranking points; ClinPGx and ClinGen "
        "are contextual."
    )

    status = clean(
        row.get("gene_level_inheritance_status")
    )

    notes = {
        "confirmed_trans": (
            " Opposite haplotypes in a shared phase block "
            "support a confirmed trans configuration."
        ),
        "possible_compound_heterozygous": (
            " Multiple heterozygous variants are present, "
            "but trans configuration is unconfirmed and "
            "requires segregation or phasing review."
        ),
        "likely_cis": (
            " Available phase evidence places the variants "
            "on the same haplotype, so biallelic disease is "
            "not established."
        ),
        "single_recessive_allele": (
            " Only one qualifying recessive allele was found."
        ),
        "homozygous_biallelic": (
            " A homozygous alternate genotype supports the "
            "biallelic requirement."
        ),
    }

    return base + notes.get(status, "")


def cnv_evidence_summary(
    row: dict[str, str],
) -> str:
    evidence = []

    cnv_type = clean(row.get("cnv_type"))

    if cnv_type:
        evidence.append(f"CNV_type={cnv_type}")

    copy_number = clean(row.get("copy_number_CN"))

    if copy_number:
        evidence.append(f"CN={copy_number}")

    zygosity = clean(row.get("zygosity"))

    if zygosity:
        evidence.append(f"Zygosity={zygosity}")

    depth = clean(row.get("depth_DP"))

    if depth:
        evidence.append(f"DP={depth}")

    genotype_quality = clean(
        row.get("genotype_quality_GQ")
    )

    if genotype_quality:
        evidence.append(f"GQ={genotype_quality}")

    allelic_depth = clean(
        row.get("allelic_depth_AD")
    )

    if allelic_depth:
        evidence.append(f"AD={allelic_depth}")

    quality_status = clean(
        row.get("cnv_quality_status")
    )

    if quality_status:
        evidence.append(
            f"CNV_genotype_QC={quality_status}"
        )

    confidence = clean(row.get("g2p_confidence"))

    if confidence:
        evidence.append(f"G2P={confidence}")

    classification = clean(
        row.get("classifycnv_classification")
    )

    if classification:
        evidence.append(
            f"ClassifyCNV={classification}"
        )

    annotsv_class = clean(
        row.get("annotsv_acmg_class")
    )

    if annotsv_class:
        evidence.append(
            f"AnnotSV_ACMG={annotsv_class}"
        )

    isv = clean(row.get("isv_probability"))

    if isv:
        evidence.append(f"ISV={isv}")

    hpo_matches = clean(
        row.get("matched_hpo_count")
    )

    if hpo_matches:
        evidence.append(
            f"HPO_matches={hpo_matches}"
        )

    return "; ".join(evidence)


def load_small_variant_candidates(
    table_path: Path,
    clingen_records: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    output_rows = []

    if not table_path.is_file():
        return output_rows

    with table_path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        for row in reader:
            raw_score = safe_float(
                row.get("final_score")
            )

            normalized = normalized_score(
                raw_score,
                SMALL_VARIANT_MAX_SCORE,
            )

            variant = clean(row.get("variant"))
            clingen = clingen_records.get(variant, {})

            output_rows.append(
                {
                    "candidate_type": "small_variant",
                    "branch_rank": clean(row.get("rank")),
                    "case_id": clean(row.get("case_id")),
                    "sample": clean(row.get("sample")),
                    "variant": variant,
                    "vcf_id": clean(row.get("vcf_id")),
                    "gene": clean(row.get("gene")),
                    "candidate_disease": clean(
                        row.get("candidate_disease")
                    ),
                    "inheritance": clean(
                        row.get("inheritance")
                    ),
                    "gene_level_inheritance_status": clean(
                        row.get("gene_level_inheritance_status")
                    ),
                    "gene_level_variant_count": clean(
                        row.get("gene_level_variant_count")
                    ),
                    "compound_partner_variants": clean(
                        row.get("compound_partner_variants")
                    ),
                    "compound_phase_evidence": clean(
                        row.get("compound_phase_evidence")
                    ),
                    "compound_score_adjustment": clean(
                        row.get("compound_score_adjustment")
                    ),
                    "genotype": clean(row.get("genotype")),
                    "zygosity": clean(row.get("zygosity")),
                    "phase_set_PS": clean(row.get("phase_set_PS")),
                    "phase_id_PID": clean(row.get("phase_id_PID")),
                    "phased_genotype_PGT": clean(
                        row.get("phased_genotype_PGT")
                    ),
                    "genotype_is_phased": clean(
                        row.get("genotype_is_phased")
                    ),
                    "copy_number_CN": "",
                    "depth_DP": clean(
                        row.get("depth_DP")
                    ),
                    "genotype_quality_GQ": clean(
                        row.get("genotype_quality_GQ")
                    ),
                    "allelic_depth_AD": clean(
                        row.get("allelic_depth_AD")
                    ),
                    "allele_balance": clean(
                        row.get("allele_balance")
                    ),
                    "genotype_quality_status": clean(
                        row.get(
                            "genotype_quality_status"
                        )
                    ),
                    "genotype_quality_notes": clean(
                        row.get(
                            "genotype_quality_notes"
                        )
                    ),
                    "molecular_effect": clean(
                        row.get("consequence")
                    ),
                    "g2p_confidence": clean(
                        row.get("g2p_confidence")
                    ),
                    "clinvar_significance": clean(
                        row.get("clinvar_significance")
                    ),
                    "clinvar_review_status": clean(
                        row.get("clinvar_review_status")
                    ),
                    "gnomad_exome_af": clean(
                        row.get("gnomad_exome_af")
                    ),
                    "gnomad_genome_af": clean(
                        row.get("gnomad_genome_af")
                    ),
                    "snpeff_effect": clean(
                        row.get("snpeff_effect")
                    ),
                    "spliceai_max_ds": clean(
                        row.get("spliceai_max_ds")
                    ),
                    "spliceai_max_effect": clean(
                        row.get("spliceai_max_effect")
                    ),
                    "clingen_region": clean(
                        clingen.get("clingen_region")
                    ),
                    "clingen_haplo": clean(
                        clingen.get("clingen_haplo")
                    ),
                    "clingen_triplo": clean(
                        clingen.get("clingen_triplo")
                    ),
                    "clinpgx_status": clean(
                        row.get("clinpgx_status")
                    ),
                    "annotsv_acmg_class": "",
                    "annotsv_ranking_score": "",
                    "classifycnv_classification": "",
                    "classifycnv_total_score": "",
                    "isv_probability": "",
                    "matched_hpo_count": clean(
                        row.get("matched_hpo_count")
                    ),
                    "matched_hpo_terms": clean(
                        row.get("matched_hpo_terms")
                    ),
                    "phenotype_points": clean(
                        row.get("phenotype_points")
                    ),
                    "raw_branch_score": f"{raw_score:g}",
                    "branch_score_maximum": str(
                        SMALL_VARIANT_MAX_SCORE
                    ),
                    "normalized_score_100": (
                        f"{normalized:.2f}"
                    ),
                    "priority": clean(row.get("priority")),
                    "inheritance_match": clean(
                        row.get("inheritance_match")
                    ),
                    "mechanism_match": clean(
                        row.get("mechanism_match")
                    ),
                    "evidence_summary": (
                        small_variant_evidence_summary(
                            row,
                            clingen,
                        )
                    ),
                    "interpretation_note": (
                        small_variant_interpretation_note(row)
                    ),
                }
            )

    return output_rows


def load_cnv_candidates(
    table_path: Path,
) -> list[dict[str, str]]:
    output_rows = []

    if not table_path.is_file():
        return output_rows

    with table_path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        for row in reader:
            raw_score = safe_float(
                row.get("final_score")
            )

            normalized = normalized_score(
                raw_score,
                CNV_MAX_SCORE,
            )

            output_rows.append(
                {
                    "candidate_type": "cnv",
                    "branch_rank": clean(row.get("rank")),
                    "case_id": clean(row.get("case_id")),
                    "sample": clean(row.get("sample")),
                    "variant": clean(
                        row.get("cnv_variant")
                    ),
                    "vcf_id": clean(row.get("vcf_id")),
                    "gene": clean(row.get("gene")),
                    "candidate_disease": clean(
                        row.get("candidate_disease")
                    ),
                    "inheritance": clean(
                        row.get("inheritance")
                    ),
                    "genotype": clean(row.get("genotype")),
                    "zygosity": clean(row.get("zygosity")),
                    "copy_number_CN": clean(
                        row.get("copy_number_CN")
                    ),
                    "depth_DP": clean(
                        row.get("depth_DP")
                    ),
                    "genotype_quality_GQ": clean(
                        row.get("genotype_quality_GQ")
                    ),
                    "allelic_depth_AD": clean(
                        row.get("allelic_depth_AD")
                    ),
                    "allele_balance": "",
                    "genotype_quality_status": clean(
                        row.get("cnv_quality_status")
                    ),
                    "genotype_quality_notes": clean(
                        row.get("cnv_quality_notes")
                    ),
                    "molecular_effect": (
                        clean(row.get("cnv_type"))
                        + " "
                        + clean(
                            row.get("annotsv_location")
                        )
                    ).strip(),
                    "g2p_confidence": clean(
                        row.get("g2p_confidence")
                    ),
                    "clinvar_significance": "",
                    "clinvar_review_status": "",
                    "gnomad_exome_af": "",
                    "gnomad_genome_af": "",
                    "snpeff_effect": "",
                    "spliceai_max_ds": "",
                    "spliceai_max_effect": "",
                    "clingen_region": clean(
                        row.get(
                            "classifycnv_dosage_sensitive_genes"
                        )
                    ),
                    "clingen_haplo": clean(
                        row.get("annotsv_hi")
                    ),
                    "clingen_triplo": clean(
                        row.get("annotsv_ts")
                    ),
                    "clinpgx_status": "",
                    "annotsv_acmg_class": clean(
                        row.get("annotsv_acmg_class")
                    ),
                    "annotsv_ranking_score": clean(
                        row.get("annotsv_ranking_score")
                    ),
                    "classifycnv_classification": clean(
                        row.get(
                            "classifycnv_classification"
                        )
                    ),
                    "classifycnv_total_score": clean(
                        row.get(
                            "classifycnv_total_score"
                        )
                    ),
                    "isv_probability": clean(
                        row.get("isv_probability")
                    ),
                    "matched_hpo_count": clean(
                        row.get("matched_hpo_count")
                    ),
                    "matched_hpo_terms": clean(
                        row.get("matched_hpo_terms")
                    ),
                    "phenotype_points": clean(
                        row.get("phenotype_points")
                    ),
                    "raw_branch_score": f"{raw_score:g}",
                    "branch_score_maximum": str(
                        CNV_MAX_SCORE
                    ),
                    "normalized_score_100": (
                        f"{normalized:.2f}"
                    ),
                    "priority": clean(row.get("priority")),
                    "inheritance_match": clean(
                        row.get("inheritance_match")
                    ),
                    "mechanism_match": clean(
                        row.get("mechanism_match")
                    ),
                    "evidence_summary": (
                        cnv_evidence_summary(row)
                    ),
                    "interpretation_note": clean(
                        row.get("interpretation_note")
                    ),
                }
            )

    return output_rows


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/"
            "14_build_master_candidate_table.py CASE_ID"
        )
        sys.exit(1)

    case_id = sys.argv[1]

    project_root = Path(__file__).resolve().parents[2]

    final_dir = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
    )

    small_table = (
        final_dir
        / (
            f"{case_id}."
            "variant_gene_disease_scores.final.tsv"
        )
    )

    cnv_table = (
        final_dir
        / (
            f"{case_id}."
            "cnv_gene_disease_scores.final.tsv"
        )
    )

    final_small_vcf = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "annotated"
        / (
            f"{case_id}."
            "final.small_variants.annotated.vcf.gz"
        )
    )

    output_table = (
        final_dir
        / f"{case_id}.master_candidate_ranking.tsv"
    )

    qc_file = (
        final_dir
        / f"{case_id}.master_ranking_qc.tsv"
    )

    final_dir.mkdir(parents=True, exist_ok=True)

    clingen_records = load_clingen_vcf(
        final_small_vcf
    )

    master_rows = []

    small_rows = load_small_variant_candidates(
        small_table,
        clingen_records,
    )

    cnv_rows = load_cnv_candidates(cnv_table)

    master_rows.extend(small_rows)
    master_rows.extend(cnv_rows)

    if not master_rows:
        print("ERROR: No candidate result tables were found.")
        print(f"Checked: {small_table}")
        print(f"Checked: {cnv_table}")
        sys.exit(1)

    master_rows.sort(
        key=lambda row: (
            -safe_float(
                row.get("normalized_score_100")
            ),
            -PRIORITY_ORDER.get(
                row.get("priority", ""),
                -1,
            ),
            row.get("gene", ""),
            row.get("candidate_disease", ""),
        )
    )

    for rank, row in enumerate(master_rows, start=1):
        row["overall_rank"] = str(rank)

    columns = [
        "overall_rank",
        "candidate_type",
        "branch_rank",
        "case_id",
        "sample",
        "variant",
        "vcf_id",
        "gene",
        "candidate_disease",
        "inheritance",
        "gene_level_inheritance_status",
        "gene_level_variant_count",
        "compound_partner_variants",
        "compound_phase_evidence",
        "compound_score_adjustment",
        "genotype",
        "zygosity",
        "phase_set_PS",
        "phase_id_PID",
        "phased_genotype_PGT",
        "genotype_is_phased",
        "copy_number_CN",
        "depth_DP",
        "genotype_quality_GQ",
        "allelic_depth_AD",
        "allele_balance",
        "genotype_quality_status",
        "genotype_quality_notes",
        "molecular_effect",
        "g2p_confidence",
        "clinvar_significance",
        "clinvar_review_status",
        "gnomad_exome_af",
        "gnomad_genome_af",
        "snpeff_effect",
        "spliceai_max_ds",
        "spliceai_max_effect",
        "clingen_region",
        "clingen_haplo",
        "clingen_triplo",
        "clinpgx_status",
        "annotsv_acmg_class",
        "annotsv_ranking_score",
        "classifycnv_classification",
        "classifycnv_total_score",
        "isv_probability",
        "matched_hpo_count",
        "matched_hpo_terms",
        "phenotype_points",
        "raw_branch_score",
        "branch_score_maximum",
        "normalized_score_100",
        "priority",
        "inheritance_match",
        "mechanism_match",
        "evidence_summary",
        "interpretation_note",
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
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(master_rows)

    top_row = master_rows[0]

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")

        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(
            ["small_variant_candidate_rows", len(small_rows)]
        )
        writer.writerow(
            ["cnv_candidate_rows", len(cnv_rows)]
        )
        writer.writerow(
            ["total_master_rows", len(master_rows)]
        )
        writer.writerow(
            [
                "normalization_method",
                "small_variant_score_divided_by_27;"
                "cnv_score_divided_by_28",
            ]
        )
        writer.writerow(
            [
                "top_candidate_type",
                top_row.get("candidate_type", ""),
            ]
        )
        writer.writerow(
            [
                "top_ranked_gene",
                top_row.get("gene", ""),
            ]
        )
        writer.writerow(
            [
                "top_ranked_disease",
                top_row.get(
                    "candidate_disease",
                    "",
                ),
            ]
        )
        writer.writerow(
            [
                "top_normalized_score",
                top_row.get(
                    "normalized_score_100",
                    "",
                ),
            ]
        )
        writer.writerow(
            [
                "output_table",
                str(output_table.relative_to(project_root)),
            ]
        )

    print("========================================")
    print("MASTER CANDIDATE RANKING")
    print("========================================")
    print(f"Case ID:                   {case_id}")
    print(f"Small-variant candidates:  {len(small_rows)}")
    print(f"CNV candidates:            {len(cnv_rows)}")
    print(f"Total candidates:          {len(master_rows)}")
    print(
        "Top candidate type:       "
        f"{top_row.get('candidate_type', '')}"
    )
    print(
        "Top-ranked gene:          "
        f"{top_row.get('gene', '')}"
    )
    print(
        "Top-ranked disease:       "
        f"{top_row.get('candidate_disease', '')}"
    )
    print(
        "Top normalized score:     "
        f"{top_row.get('normalized_score_100', '')}"
    )
    print()
    print(f"Output: {output_table}")
    print(f"QC:     {qc_file}")
    print()
    print(
        "MASTER CANDIDATE RANKING "
        "COMPLETED SUCCESSFULLY"
    )


if __name__ == "__main__":
    main()

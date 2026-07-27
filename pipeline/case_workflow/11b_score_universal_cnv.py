#!/usr/bin/env python3

import csv
import math
import sys
from pathlib import Path


GLOBAL_MAXIMUM = 15.0

CONFIDENCE_SCORES = {
    "definitive": 2.0,
    "strong": 1.8,
    "moderate": 1.5,
    "limited": 0.8,
    "disputed": 0.0,
    "refuted": 0.0,
}


def clean(value):
    return str(value).strip() if value is not None else ""


def pick(row, *names):
    for name in names:
        value = clean(row.get(name))
        if value:
            return value
    return ""


def number(value):
    try:
        return float(clean(value))
    except (TypeError, ValueError):
        return None


def read_context(path):
    if not path.is_file():
        return {}

    values = {}

    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) >= 2 and row[0].lower() != "field":
                values[row[0].strip()] = row[1].strip()

    return values


def classify_text(value):
    value = clean(value).lower().replace("_", " ")

    if not value:
        return None

    if "likely pathogenic" in value:
        return 3.2

    if "pathogenic" in value:
        return 4.0

    if (
        "uncertain" in value
        or value == "vus"
    ):
        return 1.0

    if "likely benign" in value:
        return 0.3

    if "benign" in value:
        return 0.0

    return None


def classify_annotsv(value):
    numeric = number(value)

    if numeric is not None:
        return {
            5.0: 4.0,
            4.0: 3.2,
            3.0: 1.0,
            2.0: 0.3,
            1.0: 0.0,
        }.get(numeric)

    return classify_text(value)


def classification_component(row):
    tool_scores = []
    notes = []

    classify_value = pick(
        row,
        "classifycnv_classification",
        "ClassifyCNV_classification",
    )

    classify_score = classify_text(classify_value)

    if classify_score is not None:
        tool_scores.append(classify_score)
        notes.append(
            f"ClassifyCNV={classify_value}"
        )

    annotsv_value = pick(
        row,
        "annotsv_acmg_class",
        "AnnotSV_ACMG_class",
    )

    annotsv_score = classify_annotsv(
        annotsv_value
    )

    if annotsv_score is not None:
        tool_scores.append(annotsv_score)
        notes.append(
            f"AnnotSV={annotsv_value}"
        )

    if not tool_scores:
        return None, None, "not_available"

    return (
        sum(tool_scores) / len(tool_scores),
        4.0,
        ";".join(notes),
    )


def validity_component(row):
    confidence = pick(
        row,
        "g2p_confidence",
        "confidence",
    ).lower()

    if not confidence:
        return None, None, "not_available"

    return (
        CONFIDENCE_SCORES.get(
            confidence,
            0.5,
        ),
        2.0,
        f"G2P_{confidence}",
    )


def phenotype_component(row, context):
    phenotype_status = clean(
        context.get("phenotype_status")
    )

    if (
        phenotype_status
        and phenotype_status != "available"
    ):
        return (
            None,
            None,
            phenotype_status,
        )

    semantic_score = number(
        pick(
            row,
            "phenotype_component_score",
        )
    )

    if semantic_score is not None:
        semantic_score = min(
            max(semantic_score, 0.0),
            1.0,
        )

        status = pick(
            row,
            "phenotype_evidence_status",
        ) or "semantic_HPO_evidence"

        return (
            semantic_score * 4.0,
            4.0,
            status,
        )

    points = number(
        pick(
            row,
            "phenotype_points",
            "phenotype_score",
        )
    )

    if points is not None:
        return (
            min(max(points, 0.0), 4.0),
            4.0,
            "legacy_exact_HPO_evidence",
        )

    count = number(
        pick(
            row,
            "matched_hpo_count",
            "hpo_match_count",
        )
    )

    if count is not None:
        return (
            min(max(count, 0.0), 4.0),
            4.0,
            "legacy_matched_HPO_count",
        )

    return None, None, "not_available"

def inheritance_component(row):
    inheritance = pick(
        row,
        "inheritance",
        "allelic_requirement",
    ).lower()

    zygosity = pick(
        row,
        "zygosity",
    ).lower()

    genotype = pick(
        row,
        "genotype",
    )

    if not inheritance:
        return None, None, "not_available"

    if (
        "biallelic" in inheritance
        or "recessive" in inheritance
    ):
        if (
            zygosity == "homozygous_alt"
            or genotype in {"1/1", "1|1"}
        ):
            return 2.0, 2.0, "compatible_biallelic"

        if (
            zygosity == "heterozygous"
            or genotype in {"0/1", "1/0", "0|1", "1|0"}
        ):
            return 0.5, 2.0, "single_recessive_allele"

        return 0.0, 2.0, "not_confirmed"

    if (
        "monoallelic" in inheritance
        or "dominant" in inheritance
    ):
        if genotype not in {"", "0/0", "0|0"}:
            return 2.0, 2.0, "compatible_monoallelic"

        return 0.0, 2.0, "not_confirmed"

    return 0.5, 2.0, "inheritance_available_unclear"


def mechanism_component(row):
    cnv_type = pick(
        row,
        "cnv_type",
        "SV_type",
    ).upper()

    mechanism = " ".join(
        [
            pick(
                row,
                "molecular_mechanism",
            ),
            pick(
                row,
                "g2p_variant_model",
                "variant_consequence_model",
            ),
        ]
    ).lower()

    if not mechanism:
        return None, None, "not_available"

    if cnv_type == "DEL":
        if (
            "loss of function" in mechanism
            or "absent gene product" in mechanism
            or "haploinsuff" in mechanism
        ):
            return 2.0, 2.0, "deletion_matches_mechanism"

        return 0.0, 2.0, "deletion_mechanism_mismatch"

    if cnv_type == "DUP":
        if (
            "gain of function" in mechanism
            or "increased dosage" in mechanism
            or "triplosens" in mechanism
        ):
            return 2.0, 2.0, "duplication_matches_mechanism"

        return 0.0, 2.0, "duplication_mechanism_mismatch"

    return 0.5, 2.0, "mechanism_available"


def isv_component(row):
    probability = number(
        pick(
            row,
            "isv_probability",
            "ISV",
        )
    )

    if probability is None:
        return None, None, "not_available"

    probability = min(
        max(probability, 0.0),
        1.0,
    )

    return probability, 1.0, f"ISV={probability:g}"


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: 11b_score_universal_cnv.py CASE_ID"
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

    semantic_input_table = (
        final_dir
        / f"{case_id}.cnv_gene_disease.phenotype.tsv"
    )

    legacy_input_table = (
        final_dir
        / f"{case_id}.cnv_gene_disease_scores.final.tsv"
    )

    input_table = (
        semantic_input_table
        if semantic_input_table.is_file()
        else legacy_input_table
    )

    output_table = (
        final_dir
        / f"{case_id}.universal_cnv_scores.tsv"
    )

    context_file = (
        project
        / "input"
        / "cases"
        / case_id
        / "case_context.resolved.tsv"
    )

    if not input_table.is_file():
        raise SystemExit(
            f"ERROR: CNV score table missing: {input_table}"
        )

    context = read_context(context_file)

    with input_table.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )
        rows = list(reader)

    output_rows = []

    for row in rows:
        components = {
            "cnv_classification":
                classification_component(row),
            "gene_disease_validity":
                validity_component(row),
            "phenotype":
                phenotype_component(row, context),
            "inheritance":
                inheritance_component(row),
            "mechanism":
                mechanism_component(row),
            "isv":
                isv_component(row),
        }

        obtained = sum(
            score
            for score, maximum, status
            in components.values()
            if score is not None
        )

        evaluable_maximum = sum(
            maximum
            for score, maximum, status
            in components.values()
            if maximum is not None
        )

        strength = (
            obtained / evaluable_maximum
            if evaluable_maximum
            else 0.0
        )

        coverage = (
            evaluable_maximum / GLOBAL_MAXIMUM
        )

        ranking = (
            strength
            * math.sqrt(coverage)
            * 100
            if coverage
            else 0.0
        )

        disease_mondo = pick(
            row,
            "disease_mondo",
        )

        disease_mim = pick(
            row,
            "disease_mim",
        )

        if disease_mondo:
            disease_id = disease_mondo
        elif disease_mim:
            disease_id = f"OMIM:{disease_mim}"
        else:
            disease_id = ""

        result = dict(row)

        result.update(
            {
                "candidate_type":
                    "copy_number_variant",
                "variant": pick(
                    row,
                    "cnv_variant",
                    "variant",
                ),
                "canonical_disease_id":
                    disease_id,
                "disease_name": pick(
                    row,
                    "candidate_disease",
                    "g2p_disease_name",
                ),
                "phenotype_evidence_status":
                    components["phenotype"][2],
                "semantic_phenotype_score": pick(
                    row,
                    "phenotype_component_score",
                ),
                "evidence_obtained":
                    f"{obtained:.4f}",
                "evidence_evaluable_maximum":
                    f"{evaluable_maximum:.4f}",
                "global_score_maximum":
                    f"{GLOBAL_MAXIMUM:.4f}",
                "evidence_strength_100":
                    f"{strength * 100:.2f}",
                "evidence_coverage_fraction":
                    f"{coverage:.4f}",
                "universal_ranking_score_100":
                    f"{ranking:.2f}",
                "priority": (
                    "high_priority_candidate"
                    if ranking >= 70
                    else
                    "moderate_priority_candidate"
                    if ranking >= 45
                    else
                    "low_priority_candidate"
                ),
                "evidence_gaps": ";".join(
                    name
                    for name, values
                    in components.items()
                    if values[1] is None
                ),
            }
        )

        for name, (
            component_score,
            component_maximum,
            component_status,
        ) in components.items():

            result[
                f"{name}_component_score"
            ] = (
                ""
                if component_score is None
                else f"{component_score:.4f}"
            )

            result[
                f"{name}_component_maximum"
            ] = (
                ""
                if component_maximum is None
                else f"{component_maximum:.4f}"
            )

            result[
                f"{name}_component_status"
            ] = component_status

        output_rows.append(result)

    output_rows.sort(
        key=lambda row: -float(
            row["universal_ranking_score_100"]
        )
    )

    for rank, row in enumerate(
        output_rows,
        start=1,
    ):
        row["universal_rank"] = str(rank)

    columns = [
        "universal_rank",
        "candidate_type",
        "case_id",
        "variant",
        "vcf_id",
        "gene",
        "canonical_disease_id",
        "disease_name",
        "cnv_type",
        "genotype",
        "zygosity",
        "phenotype_evidence_status",
        "semantic_phenotype_score",
        "evidence_strength_100",
        "evidence_coverage_fraction",
        "universal_ranking_score_100",
        "priority",
        "evidence_gaps",
    ]

    for row in output_rows:
        for column in row:
            if column not in columns:
                columns.append(column)

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
        writer.writerows(output_rows)

    top = output_rows[0]

    print("=" * 68)
    print("UNIVERSAL CNV SCORING")
    print("=" * 68)
    print(f"Case ID:       {case_id}")
    print(f"Candidates:    {len(output_rows)}")
    print(f"Top gene:      {top.get('gene', '')}")
    print(
        f"Top disease:   "
        f"{top.get('disease_name', '')}"
    )
    print(
        f"Top score:     "
        f"{top.get('universal_ranking_score_100', '')}"
    )
    print(f"Output:        {output_table}")


if __name__ == "__main__":
    main()

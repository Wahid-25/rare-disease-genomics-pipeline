#!/usr/bin/env python3
from inheritance_utils import classify_inheritance_model, variant_is_present

import csv
import gzip
import math
import re
import sys
from pathlib import Path
from urllib.parse import unquote


GLOBAL_MAXIMUM = 19.0

STOP_WORDS = {
    "and",
    "associated",
    "disease",
    "disorder",
    "familial",
    "hereditary",
    "related",
    "syndrome",
    "the",
    "type",
    "with",
    "without",
}

LOF_TERMS = {
    "frameshift_variant",
    "splice_acceptor_variant",
    "splice_donor_variant",
    "start_lost",
    "stop_gained",
    "transcript_ablation",
}


def clean(value):
    return str(value).strip() if value is not None else ""


def safe_float(value):
    try:
        return float(clean(value))
    except (TypeError, ValueError):
        return None


def read_tsv(path):
    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        return list(
            csv.DictReader(handle, delimiter="\t")
        )


def read_context(path):
    values = {}

    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.reader(handle, delimiter="\t")

        for row in reader:
            if not row:
                continue

            if row[0].startswith("#"):
                continue

            if row[0].strip().lower() == "field":
                continue

            if len(row) >= 2:
                values[row[0].strip()] = row[1].strip()

    return values


def parse_info(value):
    result = {}

    if value in {"", "."}:
        return result

    for item in value.split(";"):
        if "=" in item:
            key, item_value = item.split("=", 1)
            result[key] = unquote(item_value)
        else:
            result[item] = "true"

    return result


def load_clinvar_records(path):
    records = {}

    with gzip.open(
        path,
        "rt",
        encoding="utf-8",
        errors="replace",
    ) as handle:
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
                    info.get("CLNSIG")
                ),
                "clinvar_conditions": clean(
                    info.get("CLNDN")
                ),
                "clinvar_review_status": clean(
                    info.get("CLNREVSTAT")
                ),
                "clinvar_disease_ids": clean(
                    info.get("CLNDISDB")
                ),
            }

    return records


def merge_nonempty(target, source):
    for key, value in source.items():
        value = clean(value)

        if value and not clean(target.get(key)):
            target[key] = value


def normalize_text(value):
    value = unquote(clean(value))
    value = value.lower().replace("_", " ")
    value = re.sub(r"[^a-z0-9]+", " ", value)

    return " ".join(value.split())


def meaningful_words(value):
    return {
        word
        for word in normalize_text(value).split()
        if word not in STOP_WORDS
        and len(word) > 1
    }


def disease_condition_match(
    disease_id,
    disease_name,
    clinvar_conditions,
    clinvar_disease_ids,
    source_disease_ids="",
):
    disease_id = clean(disease_id).upper()
    disease_name = clean(disease_name)

    # Optional ClinVar fields may be absent for some
    # variant-disease candidates. Normalize null values
    # before string parsing.
    clinvar_conditions = clean(clinvar_conditions)
    clinvar_disease_ids = clean(clinvar_disease_ids)
    source_disease_ids = clean(source_disease_ids)

    if not disease_id and not disease_name:
        return "not_evaluable"

    normalized_ids = normalize_text(
        clinvar_disease_ids
    ).replace(" ", "")

    candidate_identifiers = []

    for identifier in [
        disease_id,
        *re.split(
            r"[|;,]+",
            source_disease_ids,
        ),
    ]:
        identifier = clean(identifier)

        if (
            identifier
            and identifier not in candidate_identifiers
        ):
            candidate_identifiers.append(identifier)

    for identifier in candidate_identifiers:
        compact_identifier = normalize_text(
            identifier
        ).replace(" ", "")

        if (
            compact_identifier
            and compact_identifier in normalized_ids
        ):
            return "matched_by_identifier"

    candidate_words = meaningful_words(
        disease_name
    )

    if not candidate_words:
        return "not_evaluable"

    conditions = [
        condition
        for condition in re.split(
            r"[|;]+",
            clinvar_conditions,
        )
        if clean(condition)
    ]

    if not conditions:
        return "not_available"

    candidate_normalized = normalize_text(
        disease_name
    )

    for condition in conditions:
        condition_normalized = normalize_text(
            condition
        )

        if not condition_normalized:
            continue

        if (
            candidate_normalized == condition_normalized
            or candidate_normalized
            in condition_normalized
            or condition_normalized
            in candidate_normalized
        ):
            return "matched_by_name"

        condition_words = meaningful_words(
            condition
        )

        if not condition_words:
            continue

        overlap = (
            len(candidate_words & condition_words)
            / len(candidate_words | condition_words)
        )

        if overlap >= 0.50:
            return "matched_by_name"

    return "condition_mismatch"


def split_tokens(value):
    normalized = normalize_text(value).replace(
        " ",
        "_",
    )

    return {
        token
        for token in re.split(
            r"[|/,;]+",
            normalized,
        )
        if token
    }


def clinvar_component(
    significance,
    condition_match,
):
    significance = clean(significance)

    if not significance:
        return None, None, "not_available"

    if condition_match in {
        "condition_mismatch",
        "not_evaluable",
    }:
        return 0.0, 4.0, condition_match

    if condition_match == "not_available":
        return None, None, "condition_not_available"

    tokens = split_tokens(significance)

    if any(
        "conflicting" in token
        for token in tokens
    ):
        return 1.0, 4.0, "conflicting_interpretations"

    if "pathogenic" in tokens:
        return 4.0, 4.0, "pathogenic"

    if "likely_pathogenic" in tokens:
        return 3.2, 4.0, "likely_pathogenic"

    if "uncertain_significance" in tokens:
        return 0.5, 4.0, "uncertain_significance"

    if "likely_benign" in tokens:
        return 0.0, 4.0, "likely_benign"

    if "benign" in tokens:
        return 0.0, 4.0, "benign"

    return 0.0, 4.0, "other_classification"


def review_component(review_status, clinvar_evaluable):
    if not clinvar_evaluable:
        return None, None, "not_evaluable"

    review = normalize_text(
        review_status
    ).replace(" ", "_")

    if not review:
        return 0.0, 1.0, "review_status_not_available"

    if (
        "practice_guideline" in review
        or "expert_panel" in review
    ):
        return 1.0, 1.0, "authoritative_review"

    if (
        "multiple_submitters" in review
        and "no_conflicts" in review
    ):
        return 0.75, 1.0, "multiple_submitters_no_conflicts"

    if "criteria_provided" in review:
        return 0.50, 1.0, "criteria_provided"

    return 0.25, 1.0, "limited_review"


def consequence_component(consequence, impact):
    consequence = clean(consequence).lower()
    impact = clean(impact).upper()

    if not consequence and not impact:
        return None, None, "not_available"

    terms = set(consequence.split("&"))

    if terms & LOF_TERMS:
        return 2.0, 2.0, "predicted_loss_of_function"

    if (
        "inframe_deletion" in terms
        or "inframe_insertion" in terms
        or "missense_variant" in terms
    ):
        return 1.2, 2.0, "protein_altering"

    if impact == "HIGH":
        return 2.0, 2.0, "high_impact"

    if impact == "MODERATE":
        return 1.2, 2.0, "moderate_impact"

    if (
        "splice_region_variant" in terms
        or "synonymous_variant" in terms
    ):
        return 0.4, 2.0, "limited_functional_effect"

    return 0.1, 2.0, "low_predicted_effect"


def rarity_component(row):
    values = []

    for field in [
        "gnomad_exome_af",
        "gnomad_genome_af",
        "max_af",
    ]:
        value = safe_float(row.get(field))

        if value is not None:
            values.append(value)

    if not values:
        return None, None, "not_available", ""

    frequency = max(values)

    if frequency <= 0.001:
        score = 2.0
        note = "very_rare"
    elif frequency <= 0.01:
        score = 1.5
        note = "rare"
    elif frequency <= 0.05:
        score = 0.5
        note = "low_frequency"
    else:
        score = 0.0
        note = "common"

    return score, 2.0, note, f"{frequency:g}"


def validity_component(row):
    confidence = normalize_text(
        row.get("confidence")
    )

    association = normalize_text(
        row.get("hpo_association_type")
    )

    source = clean(
        row.get("disease_source")
    )

    if confidence:
        scores = {
            "definitive": 2.0,
            "strong": 1.8,
            "moderate": 1.5,
            "limited": 0.8,
            "disputed": 0.0,
            "refuted": 0.0,
        }

        return (
            scores.get(confidence, 0.5),
            2.0,
            f"G2P_{confidence}",
        )

    if association:
        scores = {
            "mendelian": 1.5,
            "polygenic": 0.7,
            "unknown": 0.5,
        }

        return (
            scores.get(association, 0.5),
            2.0,
            f"HPO_{association}",
        )

    if source:
        return 0.5, 2.0, f"mapped_by_{source}"

    return None, None, "not_available"


def phenotype_component(row):
    status = clean(
        row.get("phenotype_evidence_status")
    )

    if status in {
        "not_evaluable",
        "not_provided",
        "not_available",
        "no_disease_mapping",
        "",
    }:
        return None, None, status or "not_available"

    score = safe_float(
        row.get("phenotype_component_score")
    )

    if score is None:
        return None, None, "not_available"

    return (
        max(0.0, min(1.0, score)) * 4.0,
        4.0,
        status,
    )


def inheritance_model(row):
    value = " ".join(
        [
            clean(row.get("allelic_requirement")),
            clean(row.get("disease_inheritance_names")),
        ]
    )
    return classify_inheritance_model(value).model

def inheritance_component(row, context):
    model = inheritance_model(row)

    if not model or model == "unknown":
        return None, None, "not_available", ""

    zygosity = clean(row.get("zygosity")).lower()
    sex = clean(context.get("sex")).lower()

    if model == "autosomal_recessive":
        if zygosity == "homozygous_alt":
            return 2.0, 2.0, "compatible", model
        if zygosity == "heterozygous":
            return 0.5, 2.0, "single_recessive_allele", model
        return 0.0, 2.0, "not_confirmed", model

    if model == "autosomal_dominant":
        if zygosity in {"heterozygous", "homozygous_alt"}:
            return 2.0, 2.0, "compatible", model
        return 0.0, 2.0, "not_confirmed", model

    if model.startswith("x_linked"):
        if zygosity == "hemizygous_or_haploid_alt":
            if model == "x_linked_biallelic":
                return 0.5, 2.0, "hemizygous_but_biallelic_model", model
            return 2.0, 2.0, "compatible_hemizygous", model

        if zygosity == "homozygous_alt":
            return 2.0, 2.0, "compatible_biallelic_X", model

        if zygosity == "heterozygous" and sex == "female":
            if model == "x_linked_biallelic":
                return 0.5, 2.0, "single_X_linked_allele", model
            return 1.5, 2.0, "compatible_female_heterozygous", model

        return 0.5, 2.0, "possible_x_linked", model

    if model == "mitochondrial":
        if variant_is_present(zygosity):
            return 1.5, 2.0, "variant_present_heteroplasmy_not_assessed", model
        return 0.0, 2.0, "not_confirmed", model

    return None, None, "not_available", model

def mechanism_component(row):
    mechanism = " ".join(
        [
            clean(row.get("molecular_mechanism")),
            clean(
                row.get("variant_consequence_model")
            ),
        ]
    ).lower()

    if not mechanism:
        return None, None, "not_available"

    consequence = clean(
        row.get("consequence")
    ).lower()

    terms = set(consequence.split("&"))

    if (
        "loss of function" in mechanism
        or "absent gene product" in mechanism
    ):
        if terms & LOF_TERMS:
            return 1.0, 1.0, "loss_of_function_match"

        return 0.0, 1.0, "loss_of_function_mismatch"

    if (
        "altered gene product sequence" in mechanism
        or "gain of function" in mechanism
        or "activating" in mechanism
    ):
        if terms & {
            "missense_variant",
            "inframe_deletion",
            "inframe_insertion",
        }:
            return 1.0, 1.0, "protein_altering_match"

        return 0.0, 1.0, "mechanism_mismatch"

    return 0.5, 1.0, "mechanism_available_not_specific"


def splice_component(row):
    value = safe_float(
        row.get("spliceai_max_ds")
    )

    if value is None:
        return None, None, "not_available"

    if value >= 0.80:
        score = 1.0
    elif value >= 0.50:
        score = 0.75
    elif value >= 0.20:
        score = 0.50
    elif value >= 0.10:
        score = 0.25
    else:
        score = 0.0

    return score, 1.0, f"SpliceAI_DS={value:g}"


def add_component(
    components,
    name,
    score,
    maximum,
    status,
):
    components[name] = {
        "score": score,
        "maximum": maximum,
        "status": status,
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: 11_score_universal_evidence.py CASE_ID"
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

    phenotype_table = (
        final_dir
        / (
            f"{case_id}."
            "variant_gene_disease.resolved.tsv"
        )
    )

    annotation_candidates = [
        final_dir
        / (
            f"{case_id}."
            "variant_gene_disease_scores."
            "prephenotype.tsv"
        ),
        final_dir
        / (
            f"{case_id}."
            "variant_gene_disease_scores.tsv"
        ),
    ]

    annotation_table = next(
        (
            path
            for path in annotation_candidates
            if path.is_file()
        ),
        None,
    )

    context_file = (
        project
        / "input"
        / "cases"
        / case_id
        / "case_context.resolved.tsv"
    )

    clinvar_vcf = (
        project
        / "results"
        / "cases"
        / case_id
        / "annotated"
        / f"{case_id}.vep.clinvar.vcf.gz"
    )

    required = [
        phenotype_table,
        context_file,
        clinvar_vcf,
    ]

    for path in required:
        if not path.is_file():
            raise SystemExit(
                f"ERROR: Required file missing: {path}"
            )

    if annotation_table is None:
        raise SystemExit(
            "ERROR: No annotation evidence table was found."
        )

    context = read_context(context_file)

    sex_context_file = (
        project
        / "input"
        / "cases"
        / case_id
        / "case_sex.resolved.tsv"
    )
    if sex_context_file.is_file():
        sex_context = read_context(sex_context_file)
        if clean(sex_context.get("sex")):
            context["sex"] = clean(sex_context.get("sex"))
        if clean(sex_context.get("sex_source")):
            context["sex_source"] = clean(
                sex_context.get("sex_source")
            )
    phenotype_rows = read_tsv(phenotype_table)
    annotation_rows = read_tsv(annotation_table)
    clinvar_records = load_clinvar_records(
        clinvar_vcf
    )

    annotation_index = {}

    for row in annotation_rows:
        key = (
            clean(row.get("variant")),
            clean(row.get("gene")).upper(),
        )

        if key not in annotation_index:
            annotation_index[key] = {}

        merge_nonempty(
            annotation_index[key],
            row,
        )

    output_rows = []

    for phenotype_row in phenotype_rows:
        row = dict(phenotype_row)

        # Preserve the original normalized semantic phenotype
        # score before the weighted 0–4 phenotype component is
        # calculated later.
        row["semantic_phenotype_score"] = clean(
            row.get("phenotype_component_score")
        )

        variant = clean(row.get("variant"))
        gene = clean(row.get("gene")).upper()

        merge_nonempty(
            row,
            annotation_index.get(
                (variant, gene),
                {},
            ),
        )

        merge_nonempty(
            row,
            clinvar_records.get(
                variant,
                {},
            ),
        )

        condition_match = disease_condition_match(
            row.get("canonical_disease_id"),
            row.get("disease_name"),
            row.get("clinvar_conditions"),
            row.get("clinvar_disease_ids"),
            row.get("source_disease_ids"),
        )

        components = {}

        clinvar_score, clinvar_max, clinvar_status = (
            clinvar_component(
                row.get("clinvar_significance"),
                condition_match,
            )
        )

        add_component(
            components,
            "clinvar",
            clinvar_score,
            clinvar_max,
            clinvar_status,
        )

        review_score, review_max, review_status = (
            review_component(
                row.get("clinvar_review_status"),
                clinvar_max is not None,
            )
        )

        add_component(
            components,
            "clinvar_review",
            review_score,
            review_max,
            review_status,
        )

        score, maximum, status = consequence_component(
            row.get("consequence"),
            row.get("impact"),
        )

        add_component(
            components,
            "consequence",
            score,
            maximum,
            status,
        )

        (
            score,
            maximum,
            status,
            maximum_frequency,
        ) = rarity_component(row)

        add_component(
            components,
            "rarity",
            score,
            maximum,
            status,
        )

        score, maximum, status = validity_component(
            row
        )

        add_component(
            components,
            "gene_disease_validity",
            score,
            maximum,
            status,
        )

        score, maximum, status = phenotype_component(
            row
        )

        add_component(
            components,
            "phenotype",
            score,
            maximum,
            status,
        )

        (
            score,
            maximum,
            status,
            inheritance_model_name,
        ) = inheritance_component(
            row,
            context,
        )

        add_component(
            components,
            "inheritance",
            score,
            maximum,
            status,
        )

        score, maximum, status = mechanism_component(
            row
        )

        add_component(
            components,
            "mechanism",
            score,
            maximum,
            status,
        )

        score, maximum, status = splice_component(
            row
        )

        add_component(
            components,
            "splicing",
            score,
            maximum,
            status,
        )

        obtained = sum(
            component["score"]
            for component in components.values()
            if component["score"] is not None
        )

        evaluable_maximum = sum(
            component["maximum"]
            for component in components.values()
            if component["maximum"] is not None
        )

        strength = (
            obtained / evaluable_maximum
            if evaluable_maximum > 0
            else 0.0
        )

        coverage = (
            evaluable_maximum / GLOBAL_MAXIMUM
        )

        ranking_score = (
            strength * math.sqrt(coverage) * 100
            if coverage > 0
            else 0.0
        )

        available_components = [
            name
            for name, component in components.items()
            if component["maximum"] is not None
        ]

        evidence_gaps = [
            name
            for name, component in components.items()
            if component["maximum"] is None
        ]

        benign_flag = clinvar_status in {
            "benign",
            "likely_benign",
        }

        qc_status = clean(
            row.get("genotype_quality_status")
        )

        if benign_flag:
            priority = "deprioritized"
        elif qc_status.startswith("fail"):
            priority = "technical_review_required"
        elif ranking_score >= 70 and coverage >= 0.50:
            priority = "high_priority_candidate"
        elif ranking_score >= 45:
            priority = "moderate_priority_candidate"
        else:
            priority = "low_priority_candidate"

        result = dict(row)

        result.update(
            {
                "case_mode": clean(
                    context.get("case_mode")
                ),
                "affected_status": clean(
                    context.get("affected_status")
                ),
                "testing_indication": clean(
                    context.get("testing_indication")
                ),
                "clinvar_condition_match": (
                    condition_match
                ),
                "maximum_population_frequency": (
                    maximum_frequency
                ),
                "inheritance_model_resolved": (
                    inheritance_model_name
                ),
                "evidence_obtained": (
                    f"{obtained:.4f}"
                ),
                "evidence_evaluable_maximum": (
                    f"{evaluable_maximum:.4f}"
                ),
                "global_score_maximum": (
                    f"{GLOBAL_MAXIMUM:.4f}"
                ),
                "evidence_strength_100": (
                    f"{strength * 100:.2f}"
                ),
                "evidence_coverage_fraction": (
                    f"{coverage:.4f}"
                ),
                "universal_ranking_score_100": (
                    f"{ranking_score:.2f}"
                ),
                "priority": priority,
                "available_components": ";".join(
                    available_components
                ),
                "evidence_gaps": ";".join(
                    evidence_gaps
                ),
                "scoring_method": (
                    "evaluable_evidence_strength_times_"
                    "square_root_of_evidence_coverage"
                ),
            }
        )

        for name, component in components.items():
            result[f"{name}_component_score"] = (
                ""
                if component["score"] is None
                else f"{component['score']:.4f}"
            )

            result[f"{name}_component_maximum"] = (
                ""
                if component["maximum"] is None
                else f"{component['maximum']:.4f}"
            )

            result[f"{name}_component_status"] = (
                component["status"]
            )

        output_rows.append(result)

    output_rows.sort(
        key=lambda row: (
            -float(
                row.get(
                    "universal_ranking_score_100",
                    0,
                )
            ),
            -float(
                row.get(
                    "evidence_coverage_fraction",
                    0,
                )
            ),
            clean(row.get("gene")),
            clean(row.get("disease_name")),
        )
    )

    for rank, row in enumerate(
        output_rows,
        start=1,
    ):
        row["universal_rank"] = str(rank)

    preferred_columns = [
        "universal_rank",
        "case_id",
        "case_mode",
        "affected_status",
        "testing_indication",
        "variant",
        "vcf_id",
        "gene",
        "canonical_disease_id",
        "disease_name",
        "disease_source",
        "genotype",
        "zygosity",
        "consequence",
        "impact",
        "clinvar_significance",
        "clinvar_review_status",
        "clinvar_condition_match",
        "maximum_population_frequency",
        "phenotype_evidence_status",
        "semantic_phenotype_score",
        "phenotype_component_score",
        "disease_inheritance_names",
        "inheritance_model_resolved",
        "evidence_obtained",
        "evidence_evaluable_maximum",
        "global_score_maximum",
        "evidence_strength_100",
        "evidence_coverage_fraction",
        "universal_ranking_score_100",
        "priority",
        "available_components",
        "evidence_gaps",
        "scoring_method",
    ]

    component_columns = []

    for name in [
        "clinvar",
        "clinvar_review",
        "consequence",
        "rarity",
        "gene_disease_validity",
        "phenotype",
        "inheritance",
        "mechanism",
        "splicing",
    ]:
        component_columns.extend(
            [
                f"{name}_component_score",
                f"{name}_component_maximum",
                f"{name}_component_status",
            ]
        )

    remaining_columns = []

    for row in output_rows:
        for column in row:
            if (
                column not in preferred_columns
                and column not in component_columns
                and column not in remaining_columns
            ):
                remaining_columns.append(column)

    output_columns = (
        preferred_columns
        + component_columns
        + remaining_columns
    )

    output_table = (
        final_dir
        / f"{case_id}.universal_evidence_scores.tsv"
    )

    qc_file = (
        final_dir
        / f"{case_id}.universal_evidence_scoring_qc.tsv"
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

    top = output_rows[0] if output_rows else {}

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")

        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(
            ["candidate_rows", len(output_rows)]
        )
        writer.writerow(
            ["global_score_maximum", GLOBAL_MAXIMUM]
        )
        writer.writerow(
            [
                "normalization_method",
                (
                    "evidence_strength_times_square_root_"
                    "of_evidence_coverage"
                ),
            ]
        )
        writer.writerow(
            ["top_gene", top.get("gene", "")]
        )
        writer.writerow(
            [
                "top_disease_id",
                top.get("canonical_disease_id", ""),
            ]
        )
        writer.writerow(
            [
                "top_disease",
                top.get("disease_name", ""),
            ]
        )
        writer.writerow(
            [
                "top_score",
                top.get(
                    "universal_ranking_score_100",
                    "",
                ),
            ]
        )
        writer.writerow(
            [
                "output_table",
                str(output_table.relative_to(project)),
            ]
        )

    print("=" * 72)
    print("UNIVERSAL EVIDENCE SCORING")
    print("=" * 72)
    print(f"Case ID:             {case_id}")
    print(f"Candidate rows:      {len(output_rows)}")
    print(f"Top gene:            {top.get('gene', '')}")
    print(
        f"Top disease:         "
        f"{top.get('disease_name', '')}"
    )
    print(
        f"Top disease ID:      "
        f"{top.get('canonical_disease_id', '')}"
    )
    print(
        f"Top ranking score:   "
        f"{top.get('universal_ranking_score_100', '')}"
    )
    print(f"Output:              {output_table}")
    print(f"QC:                  {qc_file}")


if __name__ == "__main__":
    main()

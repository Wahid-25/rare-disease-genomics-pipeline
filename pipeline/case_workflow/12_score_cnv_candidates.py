#!/usr/bin/env python3
from inheritance_utils import score_cnv_inheritance

import csv
import hashlib
import gzip
import re
import sys
from collections import defaultdict
from pathlib import Path


HPO_PATTERN = re.compile(r"\bHP:\d{7}\b", re.I)

G2P_CONFIDENCE_POINTS = {
    "definitive": 4,
    "strong": 3,
    "moderate": 2,
    "limited": 1,
    "disputed": 0,
    "refuted": 0,
}

ISV_THRESHOLD = 0.95


def clean(value) -> str:
    return str(value).strip() if value is not None else ""


def normalize_chromosome(value: str) -> str:
    value = clean(value)
    return value[3:] if value.lower().startswith("chr") else value


def safe_int(value, default=None):
    try:
        return int(float(clean(value)))
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(clean(value))
    except (TypeError, ValueError):
        return default


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")

    return path.open("r", encoding="utf-8")


def extract_hpo_terms(value: str) -> set[str]:
    return {
        term.upper()
        for term in HPO_PATTERN.findall(value or "")
    }


def load_patient_hpo(path: Path) -> set[str]:
    terms: set[str] = set()

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            terms.update(extract_hpo_terms(line))

    return terms


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


def genotype_to_zygosity(genotype: str) -> str:
    genotype = clean(genotype).replace("|", "/")

    if genotype in {"", ".", "./."}:
        return "unknown"

    alleles = genotype.split("/")

    if len(alleles) == 1:
        if alleles[0] not in {"0", "."}:
            return "hemizygous_or_haploid_alt"

        return "reference_or_unknown"

    called = [
        allele
        for allele in alleles
        if allele != "."
    ]

    if not called:
        return "unknown"

    alt_count = sum(
        allele != "0"
        for allele in called
    )

    if alt_count == len(called):
        return "homozygous_alt"

    if alt_count > 0:
        return "heterozygous"

    return "homozygous_reference"


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def parse_sample_format(
    format_text: str,
    sample_text: str,
) -> dict[str, str]:
    """Parse one FORMAT/sample field from a VCF record."""

    if not format_text or format_text == ".":
        return {}

    keys = format_text.split(":")
    values = sample_text.split(":")

    if len(values) < len(keys):
        values.extend(
            [""] * (len(keys) - len(values))
        )

    return dict(zip(keys, values))


def cnv_genotype_quality_assessment(
    genotype: str,
    dp_text: str,
    gq_text: str,
) -> tuple[str, str]:
    """
    Basic technical screening only.

    CNV caller-specific evidence and read-level review remain
    necessary for final interpretation.
    """

    genotype = clean(genotype)

    if genotype in {"", ".", "./.", ".|."}:
        return (
            "not_evaluable",
            "genotype_missing",
        )

    problems = []
    incomplete = []

    dp = safe_int(dp_text)
    gq = safe_int(gq_text)

    if dp is None:
        incomplete.append("DP_missing")
    elif dp < 10:
        problems.append("DP_below_10")

    if gq is None:
        incomplete.append("GQ_missing")
    elif gq < 20:
        problems.append("GQ_below_20")

    if problems:
        return (
            "review_low_quality_or_complex",
            ";".join(problems + incomplete),
        )

    if incomplete:
        return (
            "review_incomplete_quality_fields",
            ";".join(incomplete),
        )

    return (
        "pass_basic_qc",
        "GT_DP_GQ_pass_basic_screening",
    )


def load_original_cnv_genotypes(
    path: Path,
) -> dict[tuple[str, int, int, str], dict[str, str]]:
    """
    Restore sample-level CNV information lost during VCF-to-BED
    conversion.

    Captured fields:
    GT, zygosity, CN, DP, GQ and AD.
    """

    records = {}
    sample_names: list[str] = []

    with open_text(path) as handle:
        for line in handle:
            if line.startswith("#CHROM"):
                header = line.rstrip("\n").split("\t")
                sample_names = header[9:]
                continue

            if line.startswith("#"):
                continue

            fields = line.rstrip("\n").split("\t")

            if len(fields) < 8:
                continue

            chrom, pos_text, vcf_id, _ref, alt = fields[:5]
            info = parse_info(fields[7])

            pos = safe_int(pos_text)

            if pos is None:
                continue

            svtype = clean(
                info.get("SVTYPE", "")
            ).upper()

            if not svtype:
                symbolic = re.search(
                    r"<(DEL|DUP)>",
                    alt.upper(),
                )

                if symbolic:
                    svtype = symbolic.group(1)

            if svtype not in {"DEL", "DUP"}:
                continue

            end = safe_int(info.get("END"))

            if end is None:
                svlen = safe_int(info.get("SVLEN"))

                if svlen:
                    end = pos + abs(svlen) - 1

            if end is None:
                continue

            candidates = []

            if len(fields) >= 10:
                format_text = fields[8]

                for sample_name, sample_text in zip(
                    sample_names,
                    fields[9:],
                ):
                    sample_data = parse_sample_format(
                        format_text,
                        sample_text,
                    )

                    genotype = clean(
                        sample_data.get("GT", "")
                    )

                    zygosity = genotype_to_zygosity(
                        genotype
                    )

                    dp = clean(sample_data.get("DP", ""))
                    gq = clean(sample_data.get("GQ", ""))
                    ad = clean(sample_data.get("AD", ""))

                    copy_number = clean(
                        sample_data.get(
                            "CN",
                            info.get("CN", ""),
                        )
                    )

                    (
                        quality_status,
                        quality_notes,
                    ) = cnv_genotype_quality_assessment(
                        genotype,
                        dp,
                        gq,
                    )

                    candidates.append(
                        {
                            "sample": sample_name,
                            "genotype": genotype,
                            "zygosity": zygosity,
                            "copy_number_CN": copy_number,
                            "depth_DP": dp,
                            "genotype_quality_GQ": gq,
                            "allelic_depth_AD": ad,
                            "cnv_quality_status": (
                                quality_status
                            ),
                            "cnv_quality_notes": (
                                quality_notes
                            ),
                        }
                    )

            selected = {}

            for candidate in candidates:
                if candidate["zygosity"] in {
                    "heterozygous",
                    "homozygous_alt",
                    "hemizygous_or_haploid_alt",
                }:
                    selected = candidate
                    break

            if not selected and candidates:
                selected = candidates[0]

            if not selected:
                selected = {
                    "sample": "",
                    "genotype": "",
                    "zygosity": "unknown",
                    "copy_number_CN": clean(
                        info.get("CN", "")
                    ),
                    "depth_DP": "",
                    "genotype_quality_GQ": "",
                    "allelic_depth_AD": "",
                    "cnv_quality_status": "not_evaluable",
                    "cnv_quality_notes": (
                        "sample_quality_fields_unavailable"
                    ),
                }

            key = (
                normalize_chromosome(chrom),
                pos - 1,
                end,
                svtype,
            )

            records[key] = {
                **selected,
                "vcf_id": clean(vcf_id),
                "vcf_pos": str(pos),
                "vcf_alt": clean(alt),
            }

    return records


def load_annotsv(
    path: Path,
) -> dict[
    tuple[str, int, int, str],
    dict[str, object],
]:
    groups = defaultdict(
        lambda: {
            "full": {},
            "gene_rows": [],
        }
    )

    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        for row in reader:
            start_1based = safe_int(row.get("SV_start"))
            end = safe_int(row.get("SV_end"))
            svtype = clean(row.get("SV_type")).upper()

            if start_1based is None or end is None:
                continue

            key = (
                normalize_chromosome(
                    row.get("SV_chrom", "")
                ),
                start_1based - 1,
                end,
                svtype,
            )

            mode = clean(
                row.get("Annotation_mode")
            ).lower()

            if mode == "full":
                groups[key]["full"] = row

            if mode == "split":
                gene = clean(row.get("Gene_name"))

                if gene:
                    groups[key]["gene_rows"].append(row)

    return groups


def load_classifycnv(
    path: Path,
) -> dict[tuple[str, int, int, str], dict[str, str]]:
    results = {}

    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        for row in reader:
            start = safe_int(row.get("Start"))
            end = safe_int(row.get("End"))

            if start is None or end is None:
                continue

            key = (
                normalize_chromosome(
                    row.get("Chromosome", "")
                ),
                start,
                end,
                clean(row.get("Type")).upper(),
            )

            results[key] = row

    return results


def load_isv(
    path: Path,
) -> dict[tuple[str, int, int, str], dict[str, str]]:
    results = {}

    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        for row in reader:
            start = safe_int(row.get("start"))
            end = safe_int(row.get("end"))

            if start is None or end is None:
                continue

            key = (
                normalize_chromosome(
                    row.get("chrom", "")
                ),
                start,
                end,
                clean(row.get("cnv_type")).upper(),
            )

            results[key] = row

    return results


def load_g2p(
    path: Path,
) -> dict[str, list[dict[str, object]]]:
    gene_models = defaultdict(list)

    with path.open(
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            gene = clean(
                row.get("gene symbol")
            ).upper()

            if not gene:
                continue

            record = dict(row)
            record["_hpo_terms"] = extract_hpo_terms(
                row.get("phenotypes", "")
            )

            gene_models[gene].append(record)

    return gene_models


def preferred_omim_condition(value: str) -> str:
    conditions = [
        item.strip()
        for item in clean(value).split(";")
        if item.strip()
    ]

    usable = [
        condition
        for condition in conditions
        if not condition.startswith("[")
        and "pseudodeficiency" not in condition.lower()
    ]

    specific = [
        condition
        for condition in usable
        if "several forms" not in condition.lower()
    ]

    if specific:
        selected = specific[0]
    elif usable:
        selected = usable[0]
    elif conditions:
        selected = conditions[0]
    else:
        return ""

    selected = re.sub(
        r",\s*\d{6}\s*\(\d+\)\s*[A-Z-]+$",
        "",
        selected,
    )

    return selected.strip(" ,")


def gene_disease_points(confidence: str) -> int:
    return G2P_CONFIDENCE_POINTS.get(
        clean(confidence).lower(),
        0,
    )


def inheritance_points(
    requirement: str,
    zygosity: str,
) -> tuple[int, str]:
    # Shared universal inheritance model.
    return score_cnv_inheritance(
        requirement,
        zygosity,
    )

def mechanism_points(
    cnv_type: str,
    mechanism: str,
    variant_model: str,
) -> tuple[int, str]:
    text = (
        clean(mechanism)
        + " "
        + clean(variant_model)
    ).lower()

    if cnv_type == "DEL":
        if (
            "loss of function" in text
            or "absent gene product" in text
            or "decreased gene product" in text
        ):
            return 3, "deletion_matches_loss_of_function"

        return 0, "deletion_mechanism_not_confirmed"

    if cnv_type == "DUP":
        if (
            "gain of function" in text
            or "increased gene product" in text
            or "increased dosage" in text
            or "overexpression" in text
        ):
            return 3, "duplication_matches_increased_dosage"

        return 0, "duplication_mechanism_not_confirmed"

    return 0, "mechanism_not_scored"


def overlap_points(
    cnv_type: str,
    row: dict[str, str],
) -> int:
    location = clean(row.get("Location")).lower()

    cds_percent = safe_float(
        row.get("Overlapped_CDS_percent")
    )

    if cnv_type == "DEL":
        if location == "txstart-txend":
            return 3

        if cds_percent is not None and cds_percent >= 90:
            return 3

        if cds_percent is not None and cds_percent > 0:
            return 2

        return 1

    if cnv_type == "DUP":
        if location == "txstart-txend":
            return 1

        return 0

    return 0


def annotsv_acmg_points(value: str) -> int:
    acmg_class = safe_int(value)

    return {
        5: 3,
        4: 2,
        3: 0,
        2: -2,
        1: -3,
    }.get(acmg_class, 0)


def classifycnv_points(value: str) -> int:
    value = clean(value).lower()

    if value == "pathogenic":
        return 3

    if value == "likely pathogenic":
        return 2

    if "uncertain" in value:
        return 0

    if value == "likely benign":
        return -2

    if value == "benign":
        return -3

    return 0


def gene_in_dosage_field(gene: str, value: str) -> bool:
    tokens = {
        token.upper()
        for token in re.split(
            r"[,;|\s]+",
            clean(value),
        )
        if token
    }

    return gene.upper() in tokens


def isv_points(value: str) -> int:
    score = safe_float(value)

    if score is not None and score >= ISV_THRESHOLD:
        return 2

    return 0


def phenotype_points(match_count: int) -> int:
    return min(5, max(0, match_count))


def priority_label(score: int) -> str:
    if score >= 15:
        return "high_priority_candidate"

    if score >= 8:
        return "moderate_priority_candidate"

    return "low_priority_candidate"


def main() -> None:
    if len(sys.argv) not in {2, 3}:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/"
            "12_score_cnv_candidates.py CASE_ID [G2P_RESOURCE]"
        )
        sys.exit(1)

    case_id = sys.argv[1]

    project_root = Path(__file__).resolve().parents[2]

    case_input_dir = (
        project_root
        / "input"
        / "cases"
        / case_id
    )

    result_dir = (
        project_root
        / "results"
        / "cases"
        / case_id
    )

    raw_vcf = (
        case_input_dir
        / f"{case_id}.raw.vcf"
    )

    if not raw_vcf.is_file():
        compressed = (
            case_input_dir
            / f"{case_id}.raw.vcf.gz"
        )

        if compressed.is_file():
            raw_vcf = compressed

    phenotype_file = case_input_dir / "phenotypes.txt"

    manifest_file = (
        result_dir
        / "work"
        / f"{case_id}.cnv_manifest.tsv"
    )

    annotsv_file = (
        result_dir
        / "cnv"
        / f"{case_id}.AnnotSV.tsv"
    )

    classify_file = (
        result_dir
        / "cnv"
        / f"{case_id}.ClassifyCNV"
        / "Scoresheet.txt"
    )

    isv_file = (
        result_dir
        / "cnv"
        / f"{case_id}.ISV_with_SHAP.tsv"
    )

    if len(sys.argv) == 3:
        g2p_argument = Path(sys.argv[2])
        g2p_file = (
            g2p_argument
            if g2p_argument.is_absolute()
            else project_root / g2p_argument
        )
    else:
        g2p_file = (
            project_root
            / "resources"
            / "gene_disease"
            / "g2p"
            / "AllG2P.official.csv"
        )

    output_file = (
        result_dir
        / "final"
        / f"{case_id}.cnv_gene_disease_scores.final.tsv"
    )

    qc_file = (
        result_dir
        / "final"
        / f"{case_id}.cnv_scoring_qc.tsv"
    )

    required_files = [
        raw_vcf,
        phenotype_file,
        manifest_file,
        annotsv_file,
        classify_file,
        isv_file,
        g2p_file,
    ]

    for required in required_files:
        if not required.is_file():
            print(f"ERROR: Required file not found: {required}")
            sys.exit(1)

    try:
        g2p_resource_display = str(
            g2p_file.relative_to(project_root)
        )
    except ValueError:
        g2p_resource_display = str(g2p_file)

    g2p_resource_sha256 = hashlib.sha256(
        g2p_file.read_bytes()
    ).hexdigest()

    patient_hpo = load_patient_hpo(phenotype_file)

    if not patient_hpo:
        print("ERROR: No valid HPO terms found.")
        sys.exit(1)

    manifest = load_manifest(manifest_file)
    genotypes = load_original_cnv_genotypes(raw_vcf)
    annotsv = load_annotsv(annotsv_file)
    classify = load_classifycnv(classify_file)
    isv = load_isv(isv_file)
    g2p = load_g2p(g2p_file)

    output_rows = []

    for cnv in manifest:
        chrom = clean(cnv.get("chrom"))
        bed_start = safe_int(cnv.get("bed_start"))
        bed_end = safe_int(cnv.get("bed_end"))
        cnv_type = clean(cnv.get("cnv_type")).upper()

        if bed_start is None or bed_end is None:
            continue

        key = (
            normalize_chromosome(chrom),
            bed_start,
            bed_end,
            cnv_type,
        )

        genotype = genotypes.get(key, {})
        annotsv_group = annotsv.get(
            key,
            {
                "full": {},
                "gene_rows": [],
            },
        )

        full_row = annotsv_group.get("full", {}) or {}
        split_rows = annotsv_group.get(
            "gene_rows",
            [],
        ) or []

        classify_row = classify.get(key, {})
        isv_row = isv.get(key, {})

        selected_gene_rows = {}

        for gene_row in split_rows:
            gene = clean(
                gene_row.get("Gene_name")
            ).upper()

            if not gene:
                continue

            current = selected_gene_rows.get(gene)

            if current is None:
                selected_gene_rows[gene] = gene_row
            elif (
                not clean(current.get("OMIM_phenotype"))
                and clean(gene_row.get("OMIM_phenotype"))
            ):
                selected_gene_rows[gene] = gene_row

        if not selected_gene_rows:
            full_genes = [
                gene.strip().upper()
                for gene in clean(
                    full_row.get("Gene_name")
                ).split(";")
                if gene.strip()
            ]

            for gene in full_genes:
                copied = dict(full_row)
                copied["Gene_name"] = gene
                selected_gene_rows[gene] = copied

        if not selected_gene_rows:
            selected_gene_rows[""] = full_row

        for gene, gene_row in selected_gene_rows.items():
            disease_models = g2p.get(gene, [])

            if not disease_models:
                disease_models = [
                    {
                        "g2p id": "",
                        "disease name": "",
                        "disease mim": "",
                        "disease MONDO": "",
                        "allelic requirement": "",
                        "confidence": "",
                        "variant consequence": "",
                        "molecular mechanism": "",
                        "panel": "",
                        "_hpo_terms": set(),
                    }
                ]

            for model in disease_models:
                g2p_hpo = set(
                    model.get("_hpo_terms", set())
                )

                if cnv_type == "DEL":
                    annotsv_hpo = (
                        extract_hpo_terms(
                            gene_row.get("P_loss_hpo", "")
                        )
                        | extract_hpo_terms(
                            gene_row.get(
                                "po_P_loss_hpo",
                                "",
                            )
                        )
                    )
                else:
                    annotsv_hpo = (
                        extract_hpo_terms(
                            gene_row.get("P_gain_hpo", "")
                        )
                        | extract_hpo_terms(
                            gene_row.get(
                                "po_P_gain_hpo",
                                "",
                            )
                        )
                    )

                disease_hpo = g2p_hpo | annotsv_hpo
                matched_hpo = patient_hpo & disease_hpo

                inheritance_score, inheritance_match = (
                    inheritance_points(
                        model.get(
                            "allelic requirement",
                            "",
                        ),
                        genotype.get("zygosity", ""),
                    )
                )

                mechanism_score, mechanism_match = (
                    mechanism_points(
                        cnv_type,
                        model.get(
                            "molecular mechanism",
                            "",
                        ),
                        model.get(
                            "variant consequence",
                            "",
                        ),
                    )
                )

                gene_score = gene_disease_points(
                    model.get("confidence", "")
                )

                overlap_score = overlap_points(
                    cnv_type,
                    gene_row,
                )

                phenotype_score = phenotype_points(
                    len(matched_hpo)
                )

                annotsv_score = annotsv_acmg_points(
                    full_row.get("ACMG_class", "")
                )

                classify_score = classifycnv_points(
                    classify_row.get(
                        "Classification",
                        "",
                    )
                )

                dosage_field = clean(
                    classify_row.get(
                        "Known or predicted "
                        "dosage-sensitive genes",
                        "",
                    )
                )

                dosage_score = (
                    2
                    if gene
                    and gene_in_dosage_field(
                        gene,
                        dosage_field,
                    )
                    else 0
                )

                computational_score = isv_points(
                    isv_row.get("ISV", "")
                )

                final_score = (
                    gene_score
                    + overlap_score
                    + mechanism_score
                    + inheritance_score
                    + phenotype_score
                    + annotsv_score
                    + classify_score
                    + dosage_score
                    + computational_score
                )

                omim_conditions = clean(
                    gene_row.get("OMIM_phenotype")
                )

                specific_condition = (
                    preferred_omim_condition(
                        omim_conditions
                    )
                )

                g2p_disease = clean(
                    model.get("disease name")
                )

                candidate_disease = (
                    specific_condition
                    or g2p_disease
                    or "unresolved_gene_association"
                )

                interpretation_notes = []

                if (
                    "biallelic"
                    in clean(
                        model.get(
                            "allelic requirement"
                        )
                    ).lower()
                    and genotype.get("zygosity")
                    == "homozygous_alt"
                ):
                    interpretation_notes.append(
                        "CNV genotype supports a "
                        "biallelic recessive model"
                    )

                if (
                    "uncertain"
                    in clean(
                        classify_row.get(
                            "Classification"
                        )
                    ).lower()
                ):
                    interpretation_notes.append(
                        "ClassifyCNV is uncertain and "
                        "is not treated as negative evidence"
                    )

                isv_probability = safe_float(
                    isv_row.get("ISV")
                )

                if (
                    isv_probability is not None
                    and isv_probability < ISV_THRESHOLD
                ):
                    interpretation_notes.append(
                        "ISV is below 0.95 and contributes "
                        "no scoring points"
                    )

                output_rows.append(
                    {
                        "case_id": case_id,
                        "sample": clean(
                            genotype.get("sample")
                        ),
                        "cnv_variant": (
                            f"{chrom}:{bed_start + 1}-"
                            f"{bed_end}:{cnv_type}"
                        ),
                        "vcf_id": clean(
                            genotype.get("vcf_id")
                            or cnv.get("vcf_id")
                        ),
                        "chromosome": chrom,
                        "vcf_start": str(bed_start + 1),
                        "bed_start": str(bed_start),
                        "end": str(bed_end),
                        "cnv_type": cnv_type,
                        "genotype": clean(
                            genotype.get("genotype")
                        ),
                        "zygosity": clean(
                            genotype.get("zygosity")
                        ),
                        "copy_number_CN": clean(
                            genotype.get("copy_number_CN")
                        ),
                        "depth_DP": clean(
                            genotype.get("depth_DP")
                        ),
                        "genotype_quality_GQ": clean(
                            genotype.get(
                                "genotype_quality_GQ"
                            )
                        ),
                        "allelic_depth_AD": clean(
                            genotype.get(
                                "allelic_depth_AD"
                            )
                        ),
                        "cnv_quality_status": clean(
                            genotype.get(
                                "cnv_quality_status"
                            )
                        ),
                        "cnv_quality_notes": clean(
                            genotype.get(
                                "cnv_quality_notes"
                            )
                        ),
                        "gene": gene,
                        "candidate_disease": candidate_disease,
                        "g2p_disease_name": g2p_disease,
                        "g2p_id": clean(
                            model.get("g2p id")
                        ),
                        "disease_mim": clean(
                            model.get("disease mim")
                        ),
                        "disease_mondo": clean(
                            model.get("disease MONDO")
                        ),
                        "inheritance": clean(
                            model.get(
                                "allelic requirement"
                            )
                        ),
                        "g2p_confidence": clean(
                            model.get("confidence")
                        ),
                        "molecular_mechanism": clean(
                            model.get(
                                "molecular mechanism"
                            )
                        ),
                        "g2p_variant_model": clean(
                            model.get(
                                "variant consequence"
                            )
                        ),
                        "annotsv_id": clean(
                            gene_row.get("AnnotSV_ID")
                            or full_row.get("AnnotSV_ID")
                        ),
                        "annotsv_cytoband": clean(
                            gene_row.get("CytoBand")
                            or full_row.get("CytoBand")
                        ),
                        "annotsv_location": clean(
                            gene_row.get("Location")
                        ),
                        "annotsv_transcript": clean(
                            gene_row.get("Tx")
                        ),
                        "annotsv_omim_phenotype": (
                            omim_conditions
                        ),
                        "annotsv_omim_inheritance": clean(
                            gene_row.get(
                                "OMIM_inheritance"
                            )
                        ),
                        "annotsv_ranking_score": clean(
                            full_row.get(
                                "AnnotSV_ranking_score"
                            )
                        ),
                        "annotsv_ranking_criteria": clean(
                            full_row.get(
                                "AnnotSV_ranking_criteria"
                            )
                        ),
                        "annotsv_acmg_class": clean(
                            full_row.get("ACMG_class")
                        ),
                        "annotsv_hi": clean(
                            gene_row.get("HI")
                        ),
                        "annotsv_ts": clean(
                            gene_row.get("TS")
                        ),
                        "classifycnv_classification": clean(
                            classify_row.get(
                                "Classification"
                            )
                        ),
                        "classifycnv_total_score": clean(
                            classify_row.get(
                                "Total score"
                            )
                        ),
                        "classifycnv_dosage_sensitive_genes": (
                            dosage_field
                        ),
                        "classifycnv_protein_coding_genes": clean(
                            classify_row.get(
                                "All protein coding genes"
                            )
                        ),
                        "isv_probability": clean(
                            isv_row.get("ISV")
                        ),
                        "isv_threshold": str(ISV_THRESHOLD),
                        "patient_hpo_count": str(
                            len(patient_hpo)
                        ),
                        "disease_hpo_count": str(
                            len(disease_hpo)
                        ),
                        "matched_hpo_count": str(
                            len(matched_hpo)
                        ),
                        "matched_hpo_terms": ";".join(
                            sorted(matched_hpo)
                        ),
                        "gene_disease_points": str(
                            gene_score
                        ),
                        "gene_overlap_points": str(
                            overlap_score
                        ),
                        "mechanism_points": str(
                            mechanism_score
                        ),
                        "inheritance_points": str(
                            inheritance_score
                        ),
                        "phenotype_points": str(
                            phenotype_score
                        ),
                        "annotsv_acmg_points": str(
                            annotsv_score
                        ),
                        "classifycnv_points": str(
                            classify_score
                        ),
                        "dosage_sensitive_points": str(
                            dosage_score
                        ),
                        "isv_points": str(
                            computational_score
                        ),
                        "final_score": str(final_score),
                        "priority": priority_label(
                            final_score
                        ),
                        "inheritance_match": (
                            inheritance_match
                        ),
                        "mechanism_match": (
                            mechanism_match
                        ),
                        "phenotype_match_method": (
                            "exact_HPO_ID_overlap"
                        ),
                        "interpretation_note": "; ".join(
                            interpretation_notes
                        ),
                    }
                )

    output_rows.sort(
        key=lambda row: (
            -safe_int(row.get("final_score"), 0),
            row.get("gene", ""),
            row.get("candidate_disease", ""),
        )
    )

    for rank, row in enumerate(output_rows, start=1):
        row["rank"] = str(rank)

    columns = [
        "rank",
        "case_id",
        "sample",
        "cnv_variant",
        "vcf_id",
        "chromosome",
        "vcf_start",
        "bed_start",
        "end",
        "cnv_type",
        "genotype",
        "zygosity",
        "copy_number_CN",
        "depth_DP",
        "genotype_quality_GQ",
        "allelic_depth_AD",
        "cnv_quality_status",
        "cnv_quality_notes",
        "gene",
        "candidate_disease",
        "g2p_disease_name",
        "g2p_id",
        "disease_mim",
        "disease_mondo",
        "inheritance",
        "g2p_confidence",
        "molecular_mechanism",
        "g2p_variant_model",
        "annotsv_id",
        "annotsv_cytoband",
        "annotsv_location",
        "annotsv_transcript",
        "annotsv_omim_phenotype",
        "annotsv_omim_inheritance",
        "annotsv_ranking_score",
        "annotsv_ranking_criteria",
        "annotsv_acmg_class",
        "annotsv_hi",
        "annotsv_ts",
        "classifycnv_classification",
        "classifycnv_total_score",
        "classifycnv_dosage_sensitive_genes",
        "classifycnv_protein_coding_genes",
        "isv_probability",
        "isv_threshold",
        "patient_hpo_count",
        "disease_hpo_count",
        "matched_hpo_count",
        "matched_hpo_terms",
        "gene_disease_points",
        "gene_overlap_points",
        "mechanism_points",
        "inheritance_points",
        "phenotype_points",
        "annotsv_acmg_points",
        "classifycnv_points",
        "dosage_sensitive_points",
        "isv_points",
        "final_score",
        "priority",
        "inheritance_match",
        "mechanism_match",
        "phenotype_match_method",
        "interpretation_note",
    ]

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
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

    top_row = output_rows[0] if output_rows else {}

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")

        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(
            ["g2p_resource", g2p_resource_display]
        )
        writer.writerow(
            ["g2p_resource_sha256", g2p_resource_sha256]
        )
        writer.writerow(
            ["input_cnv_records", len(manifest)]
        )
        writer.writerow(
            ["candidate_disease_rows", len(output_rows)]
        )
        writer.writerow(
            ["patient_hpo_terms", len(patient_hpo)]
        )
        writer.writerow(
            [
                "restored_cnv_genotypes",
                len(genotypes),
            ]
        )
        writer.writerow(
            [
                "high_priority_candidates",
                sum(
                    row["priority"]
                    == "high_priority_candidate"
                    for row in output_rows
                ),
            ]
        )
        writer.writerow(
            ["top_ranked_gene", top_row.get("gene", "")]
        )
        writer.writerow(
            [
                "top_ranked_disease",
                top_row.get("candidate_disease", ""),
            ]
        )
        writer.writerow(
            [
                "top_final_score",
                top_row.get("final_score", ""),
            ]
        )
        writer.writerow(
            [
                "output_table",
                str(
                    output_file.relative_to(
                        project_root
                    )
                ),
            ]
        )

    print("========================================")
    print("CNV GENE-DISEASE SCORING")
    print("========================================")
    print(f"Case ID:                {case_id}")
    print(f"Input CNVs:             {len(manifest)}")
    print(f"Candidate rows:         {len(output_rows)}")
    print(f"Patient HPO terms:      {len(patient_hpo)}")
    print(
        "Restored genotypes:    "
        f"{len(genotypes)}"
    )
    print(
        "Top-ranked gene:       "
        f"{top_row.get('gene', '')}"
    )
    print(
        "Top-ranked disease:    "
        f"{top_row.get('candidate_disease', '')}"
    )
    print(
        "Top score:             "
        f"{top_row.get('final_score', '')}"
    )
    print()
    print(f"Output: {output_file}")
    print(f"QC:     {qc_file}")
    print()
    print(
        "CNV GENE-DISEASE SCORING "
        "COMPLETED SUCCESSFULLY"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build a draft clinical-report JSON from completed pipeline outputs.

The JSON is designed for clinical_report/index.html schema version 1.0.
It is a machine-generated draft, not a final clinical report.

Default output:
results/cases/<CASE_ID>/final/report/<CASE_ID>.report_draft.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"

REPORTABLE_PRIORITIES = {
    "high_priority_candidate",
    "moderate_priority_candidate",
    "low_priority_candidate",
}

BENIGN_TERMS = {
    "benign",
    "likely benign",
    "likely_benign",
}

VARIANT_PATTERN = re.compile(
    r"^(?P<chrom>[^:]+):(?P<pos>\d+):(?P<ref>[^>]+)>(?P<alt>.+)$"
)


def clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        return []

    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            {key: clean(value) for key, value in row.items()}
            for row in csv.DictReader(handle, delimiter="\t")
        ]


def read_metric_tsv(path: Path) -> dict[str, str]:
    rows = read_tsv(path)
    result: dict[str, str] = {}

    for row in rows:
        key = clean(row.get("field") or row.get("metric"))
        value = clean(row.get("value"))
        if key:
            result[key] = value

    return result


def normalize_text_key(value: str) -> str:
    text = clean(value).lower().replace("_", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(clean(value))
    except (TypeError, ValueError):
        return default


def parse_variant_key(value: str) -> dict[str, Any]:
    text = clean(value)
    match = VARIANT_PATTERN.fullmatch(text)

    if not match:
        return {
            "genome_build": "GRCh38",
            "chromosome": None,
            "position": None,
            "reference": None,
            "alternate": None,
            "display": f"GRCh38 {text}" if text else "GRCh38",
        }

    chromosome = match.group("chrom")
    position = int(match.group("pos"))
    reference = match.group("ref")
    alternate = match.group("alt")

    return {
        "genome_build": "GRCh38",
        "chromosome": chromosome,
        "position": position,
        "reference": reference,
        "alternate": alternate,
        "display": f"GRCh38 {chromosome}:{position}",
    }


def normalize_zygosity(value: str) -> str:
    text = normalize_text_key(value)

    if "compound" in text and "heterozyg" in text:
        return "Compound heterozygous"
    if "hemizyg" in text or "haploid alt" in text:
        return "Hemizygous"
    if "homozyg" in text and "reference" not in text:
        return "Homozygous"
    if "heterozyg" in text:
        return "Heterozygous"

    genotype = clean(value).replace("|", "/")
    if genotype in {"0/1", "1/0"}:
        return "Heterozygous"
    if genotype == "1/1":
        return "Homozygous"
    if genotype == "1":
        return "Hemizygous"

    return "Heterozygous"


def normalize_inheritance(value: str) -> str:
    text = normalize_text_key(value)

    if "biallelic" in text or "autosomal recessive" in text:
        return "Autosomal Recessive"
    if "monoallelic" in text or "autosomal dominant" in text:
        return "Autosomal Dominant"
    if "x linked recessive" in text:
        return "X-linked Recessive"
    if "x linked dominant" in text:
        return "X-linked Dominant"
    if "y linked" in text:
        return "Y-linked"
    if "mitochond" in text:
        return "Mitochondrial"
    if "de novo" in text:
        return "De novo"
    if "multifactor" in text or "complex" in text:
        return "Multifactorial / Complex"

    return "Unknown"


def classification_label(value: str) -> str:
    text = normalize_text_key(value)

    if "conflicting" in text or "uncertain" in text or text == "vus":
        return "VUS"
    if "likely pathogenic" in text:
        return "Likely Pathogenic"
    if "pathogenic" in text:
        return "Pathogenic"
    if "likely benign" in text:
        return "Likely Benign"
    if text == "benign":
        return "Benign"

    return "VUS"


def classification_source(row: dict[str, str]) -> tuple[str, str, str]:
    candidate_type = clean(row.get("candidate_type")).lower()

    if candidate_type == "cnv":
        classifycnv = clean(row.get("classifycnv_classification"))
        annotsv = clean(row.get("annotsv_acmg_class"))

        if classifycnv:
            return (
                classification_label(classifycnv),
                "ClassifyCNV",
                classifycnv,
            )
        if annotsv:
            return (
                classification_label(annotsv),
                "AnnotSV",
                annotsv,
            )

        return ("VUS", "pipeline CNV prioritisation", "not formally classified")

    clinvar = clean(row.get("clinvar_significance"))
    review = clean(row.get("clinvar_review_status"))

    if clinvar:
        return (classification_label(clinvar), "ClinVar", review)

    return ("VUS", "pipeline prioritisation", "not formally classified")


def load_vep_index(path: Path) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}

    for row in read_tsv(path):
        variant = clean(row.get("variant"))
        if variant and variant not in index:
            index[variant] = row

    return index


def load_metadata(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"ERROR: Invalid metadata JSON: {path}: {error}") from error

    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: Metadata JSON must contain an object: {path}")

    return data


def find_default_metadata(project_root: Path, case_id: str) -> Path | None:
    candidates = [
        project_root
        / "input"
        / "cases"
        / case_id
        / "metadata"
        / "report_metadata.json",
        project_root
        / "input"
        / "cases"
        / case_id
        / "metadata"
        / "case_metadata.json",
        project_root / "input" / "cases" / case_id / "report_metadata.json",
    ]

    return next((path for path in candidates if path.is_file()), None)


def load_hpo_terms(path: Path) -> list[str]:
    if not path.is_file():
        return []

    pattern = re.compile(r"\bHP:\d{7}\b", flags=re.I)
    terms: set[str] = set()

    for line in path.read_text(encoding="utf-8-sig").splitlines():
        terms.update(match.upper() for match in pattern.findall(line))

    return sorted(terms)


def choose_master_rows(
    rows: list[dict[str, str]],
    selected_variants: list[str],
    include_all_high_priority: bool,
    max_findings: int,
) -> tuple[list[dict[str, str]], list[str]]:
    warnings: list[str] = []

    if not rows:
        return [], warnings

    rows = sorted(
        rows,
        key=lambda row: (
            safe_float(row.get("overall_rank"), 10**9),
            -safe_float(row.get("normalized_score_100")),
        ),
    )

    if selected_variants:
        selected_keys = set(selected_variants)
        selected = [
            row
            for row in rows
            if clean(row.get("variant")) in selected_keys
        ]
        missing = selected_keys - {
            clean(row.get("variant")) for row in selected
        }

        if missing:
            raise SystemExit(
                "ERROR: Selected variant(s) were not found in the master table: "
                + ", ".join(sorted(missing))
            )

        warnings.append(
            "Findings were selected explicitly by genomic variant key."
        )
        return selected[:max_findings], warnings

    top = rows[0]
    top_disease_key = normalize_text_key(top.get("candidate_disease", ""))

    selected: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()

    def add(row: dict[str, str]) -> None:
        identity = (
            clean(row.get("candidate_type")),
            clean(row.get("variant")),
            clean(row.get("gene")),
            normalize_text_key(row.get("candidate_disease", "")),
        )
        if identity not in seen:
            seen.add(identity)
            selected.append(row)

    add(top)

    for row in rows[1:]:
        priority = clean(row.get("priority"))
        disease_key = normalize_text_key(
            row.get("candidate_disease", "")
        )
        clinvar = normalize_text_key(
            row.get("clinvar_significance", "")
        )

        if clinvar in BENIGN_TERMS or priority == "deprioritized":
            continue

        same_top_disease = bool(top_disease_key) and disease_key == top_disease_key
        high_other_disease = (
            include_all_high_priority
            and priority == "high_priority_candidate"
        )

        if same_top_disease or high_other_disease:
            add(row)

        if len(selected) >= max_findings:
            break

    # Retain compound-heterozygous partner alleles even when a partner
    # was ranked below the ordinary automatic selection threshold.
    partner_keys: set[str] = set()
    for row in list(selected):
        partner_text = clean(row.get("compound_partner_variants"))
        for token in re.split(r"[;,|]", partner_text):
            token = token.strip()
            if token:
                partner_keys.add(token)

    for row in rows:
        if clean(row.get("variant")) in partner_keys:
            add(row)
        if len(selected) >= max_findings:
            break

    warnings.append(
        "Automatic draft selection used the top-ranked disease group. "
        "The selection requires analyst review and is not a diagnosis."
    )

    if not include_all_high_priority:
        other_diseases = {
            clean(row.get("candidate_disease"))
            for row in rows
            if normalize_text_key(row.get("candidate_disease", ""))
            != top_disease_key
            and clean(row.get("priority")) == "high_priority_candidate"
        }
        if other_diseases:
            warnings.append(
                "Additional high-priority disease hypotheses remain in the "
                "master table and were not automatically added to this draft: "
                + "; ".join(sorted(filter(None, other_diseases)))
            )

    return selected[:max_findings], warnings


def candidate_to_finding(
    row: dict[str, str],
    vep_index: dict[str, dict[str, str]],
    finding_number: int,
) -> dict[str, Any]:
    variant = clean(row.get("variant"))
    candidate_type = clean(row.get("candidate_type")).lower()
    vep = vep_index.get(variant, {})

    label, source, review_status = classification_source(row)

    if candidate_type == "cnv":
        finding_type = "copy_number_variant"
        coordinate = {
            "genome_build": "GRCh38",
            "chromosome": None,
            "position": None,
            "reference": None,
            "alternate": None,
            "display": f"GRCh38 {variant}" if variant else "GRCh38 CNV",
        }
        hgvsc = None
        hgvsp = None
    else:
        finding_type = "small_variant"
        coordinate = parse_variant_key(variant)
        hgvsc = clean(vep.get("hgvsc")) or None
        hgvsp = clean(vep.get("hgvsp")) or None

    return {
        "finding_id": f"F{finding_number}",
        "finding_type": finding_type,
        "report_role": (
            "primary"
            if finding_number == 1
            else "additional_candidate"
        ),
        "pipeline_rank": clean(row.get("overall_rank")) or None,
        "pipeline_priority": clean(row.get("priority")) or None,
        "pipeline_score_100": clean(
            row.get("normalized_score_100")
        ) or None,
        "gene": clean(row.get("gene")) or None,
        "transcript": clean(vep.get("transcript")) or None,
        "condition": clean(row.get("candidate_disease")) or None,
        "coordinate": coordinate,
        "hgvs": {
            "coding": hgvsc,
            "protein": hgvsp,
        },
        "zygosity": normalize_zygosity(
            clean(row.get("zygosity"))
            or clean(row.get("genotype"))
        ),
        "genotype": clean(row.get("genotype")) or None,
        "inheritance": normalize_inheritance(
            row.get("inheritance", "")
        ),
        "inheritance_evidence": {
            "inheritance_match": clean(
                row.get("inheritance_match")
            ) or None,
            "gene_level_status": clean(
                row.get("gene_level_inheritance_status")
            ) or None,
            "compound_partner_variants": clean(
                row.get("compound_partner_variants")
            ) or None,
            "compound_phase_evidence": clean(
                row.get("compound_phase_evidence")
            ) or None,
        },
        "classification": {
            "label": label,
            "source": source,
            "review_status": review_status or None,
            "analyst_reviewed": False,
        },
        "confirmation": {
            "status": "Not independently confirmed",
            "method": None,
            "statement": (
                "Orthogonal confirmation was not performed within "
                "this workflow."
            ),
        },
        "clinpgx": {
            "summary": "",
        },
        "evidence": {
            "molecular_effect": clean(
                row.get("molecular_effect")
            ) or None,
            "clinvar_significance": clean(
                row.get("clinvar_significance")
            ) or None,
            "clinvar_review_status": clean(
                row.get("clinvar_review_status")
            ) or None,
            "g2p_confidence": clean(
                row.get("g2p_confidence")
            ) or None,
            "gnomad_exome_af": clean(
                row.get("gnomad_exome_af")
            ) or None,
            "gnomad_genome_af": clean(
                row.get("gnomad_genome_af")
            ) or None,
            "spliceai_max_ds": clean(
                row.get("spliceai_max_ds")
            ) or None,
            "spliceai_max_effect": clean(
                row.get("spliceai_max_effect")
            ) or None,
            "matched_hpo_count": clean(
                row.get("matched_hpo_count")
            ) or None,
            "matched_hpo_terms": clean(
                row.get("matched_hpo_terms")
            ) or None,
            "evidence_summary": clean(
                row.get("evidence_summary")
            ) or None,
            "interpretation_note": clean(
                row.get("interpretation_note")
            ) or None,
            "copy_number": clean(
                row.get("copy_number_CN")
            ) or None,
            "annotsv_acmg_class": clean(
                row.get("annotsv_acmg_class")
            ) or None,
            "classifycnv_classification": clean(
                row.get("classifycnv_classification")
            ) or None,
            "isv_probability": clean(
                row.get("isv_probability")
            ) or None,
        },
    }


def local_pgx_summary(row: dict[str, str]) -> str:
    parts = []

    gene = clean(row.get("local_pgx_gene") or row.get("gene"))
    rsid = clean(row.get("local_pgx_rsid") or row.get("vcf_id"))
    genotype = clean(
        row.get("local_pgx_observed_genotype_class")
        or row.get("genotype")
    )
    phenotype = clean(row.get("local_pgx_phenotype"))
    drugs = clean(row.get("local_pgx_affected_drugs"))
    cpic = clean(row.get("local_pgx_cpic_level"))

    if gene:
        parts.append(gene)
    if rsid:
        parts.append(rsid)
    if genotype:
        parts.append(genotype)
    if phenotype:
        parts.append(phenotype)
    if drugs:
        parts.append(f"associated drug(s): {drugs}")
    if cpic:
        parts.append(f"CPIC level: {cpic}")

    if not parts:
        return ""

    return "; ".join(parts) + "; professional guideline review required."


def official_pgx_summary(row: dict[str, str]) -> str:
    parts = []

    gene = clean(row.get("gene"))
    rsid = clean(
        row.get("clinpgx_variant_query")
        or row.get("vcf_id")
    )
    variant_id = clean(row.get("clinpgx_variant_id"))
    gene_id = clean(row.get("clinpgx_gene_id"))

    if gene:
        parts.append(gene)
    if rsid:
        parts.append(rsid)
    if variant_id:
        parts.append(f"ClinPGx variant ID: {variant_id}")
    if gene_id:
        parts.append(f"ClinPGx gene ID: {gene_id}")

    if not parts:
        return ""

    return (
        "; ".join(parts)
        + "; database match only—complete diplotype and guideline review required."
    )


def attach_pgx_findings(
    findings: list[dict[str, Any]],
    local_rows: list[dict[str, str]],
    official_rows: list[dict[str, str]],
    warnings: list[str],
) -> None:
    by_variant = {
        clean(finding.get("coordinate", {}).get("chromosome"))
        + ":"
        + clean(finding.get("coordinate", {}).get("position"))
        + ":"
        + clean(finding.get("coordinate", {}).get("reference"))
        + ">"
        + clean(finding.get("coordinate", {}).get("alternate")): finding
        for finding in findings
        if finding.get("finding_type") == "small_variant"
    }

    # The variant string produced by the pipeline is easier and safer to
    # compare than rebuilding the key from optional JSON properties.
    by_source_variant = {
        clean(finding.get("_source_variant")): finding
        for finding in findings
        if clean(finding.get("_source_variant"))
    }

    used_variants: set[str] = set()

    for row in local_rows:
        if clean(row.get("local_pgx_status")) != "local_reference_match":
            continue

        variant = clean(row.get("variant"))
        summary = local_pgx_summary(row)
        if not summary:
            continue

        target = by_source_variant.get(variant)

        if target is not None:
            target["clinpgx"]["summary"] = summary
            target["clinpgx"]["source"] = "local_curated_pgx_reference"
            used_variants.add(variant)
            continue

        coordinate = parse_variant_key(variant)
        findings.append(
            {
                "finding_id": f"F{len(findings) + 1}",
                "finding_type": "pharmacogenomic",
                "report_role": "pharmacogenomic",
                "gene": clean(
                    row.get("local_pgx_gene") or row.get("gene")
                ) or None,
                "transcript": None,
                "condition": "Pharmacogenomic finding",
                "coordinate": coordinate,
                "hgvs": {"coding": None, "protein": None},
                "zygosity": normalize_zygosity(
                    row.get("zygosity") or row.get("genotype", "")
                ),
                "genotype": clean(row.get("genotype")) or None,
                "inheritance": "Unknown",
                "classification": {
                    "label": "VUS",
                    "source": "local curated ClinPGx reference",
                    "review_status": "project interpretation",
                    "analyst_reviewed": False,
                },
                "confirmation": {
                    "status": "Not independently confirmed",
                    "method": None,
                    "statement": (
                        "Orthogonal confirmation was not performed within "
                        "this workflow."
                    ),
                },
                "clinpgx": {
                    "summary": summary,
                    "source": "local_curated_pgx_reference",
                },
                "evidence": {
                    "match_method": clean(
                        row.get("local_pgx_match_method")
                    ) or None,
                    "allele_match": clean(
                        row.get("local_pgx_allele_match")
                    ) or None,
                    "genotype_match": clean(
                        row.get("local_pgx_genotype_match")
                    ) or None,
                },
                "_source_variant": variant,
            }
        )
        used_variants.add(variant)

    for row in official_rows:
        if clean(row.get("clinpgx_variant_match")).lower() != "yes":
            continue

        variant = clean(row.get("variant"))
        if variant in used_variants:
            continue

        summary = official_pgx_summary(row)
        if not summary:
            continue

        target = by_source_variant.get(variant)

        if target is not None:
            target["clinpgx"]["summary"] = summary
            target["clinpgx"]["source"] = "ClinPGx"
            continue

        coordinate = parse_variant_key(variant)
        findings.append(
            {
                "finding_id": f"F{len(findings) + 1}",
                "finding_type": "pharmacogenomic",
                "report_role": "pharmacogenomic",
                "gene": clean(row.get("gene")) or None,
                "transcript": None,
                "condition": "Pharmacogenomic database match",
                "coordinate": coordinate,
                "hgvs": {"coding": None, "protein": None},
                "zygosity": normalize_zygosity(
                    row.get("zygosity") or row.get("genotype", "")
                ),
                "genotype": clean(row.get("genotype")) or None,
                "inheritance": "Unknown",
                "classification": {
                    "label": "VUS",
                    "source": "ClinPGx",
                    "review_status": "database match only",
                    "analyst_reviewed": False,
                },
                "confirmation": {
                    "status": "Not independently confirmed",
                    "method": None,
                    "statement": (
                        "Orthogonal confirmation was not performed within "
                        "this workflow."
                    ),
                },
                "clinpgx": {
                    "summary": summary,
                    "source": "ClinPGx",
                },
                "evidence": {},
                "_source_variant": variant,
            }
        )

    if local_rows or official_rows:
        warnings.append(
            "Pharmacogenomic information is contextual and must not be used "
            "alone to change medication or dose."
        )


def repeat_to_finding(
    row: dict[str, str],
    finding_number: int,
) -> dict[str, Any]:
    chromosome = clean(row.get("chromosome"))
    position_text = clean(row.get("position"))
    position = int(position_text) if position_text.isdigit() else None

    return {
        "finding_id": f"F{finding_number}",
        "finding_type": "repeat_expansion",
        "report_role": "specialist_review",
        "gene": clean(row.get("gene")) or "Repeat locus",
        "transcript": None,
        "condition": clean(
            row.get("reported_disease_label")
        ) or "Repeat-expansion finding",
        "coordinate": {
            "genome_build": "GRCh38",
            "chromosome": chromosome or None,
            "position": position,
            "reference": clean(row.get("ref")) or None,
            "alternate": clean(row.get("alt")) or None,
            "display": (
                f"GRCh38 {chromosome}:{position_text}"
                if chromosome and position_text
                else "GRCh38 repeat locus"
            ),
        },
        "hgvs": {
            "coding": clean(row.get("reported_hgvs_c")) or None,
            "protein": clean(row.get("reported_hgvs_p")) or None,
        },
        "zygosity": normalize_zygosity(
            row.get("zygosity") or row.get("genotype", "")
        ),
        "genotype": clean(row.get("genotype")) or None,
        "inheritance": "Unknown",
        "classification": {
            "label": "VUS",
            "source": "repeat-expansion routing",
            "review_status": clean(
                row.get("interpretation_status")
            ) or "detected_not_interpreted",
            "analyst_reviewed": False,
        },
        "confirmation": {
            "status": "Not independently confirmed",
            "method": None,
            "statement": (
                "Specialist repeat-expansion analysis or a validated repeat "
                "assay is required."
            ),
        },
        "clinpgx": {"summary": ""},
        "evidence": {
            "repeat_unit": clean(row.get("repeat_unit")) or None,
            "observed_repeats": clean(
                row.get("observed_repeats")
            ) or None,
            "normal_range": clean(row.get("normal_range")) or None,
            "reported_pathogenic_threshold": clean(
                row.get("reported_pathogenic_threshold")
            ) or None,
            "interpretation_status": clean(
                row.get("interpretation_status")
            ) or None,
            "required_next_step": clean(
                row.get("required_next_step")
            ) or None,
            "interpretation_note": clean(
                row.get("interpretation_note")
            ) or None,
        },
    }


def build_variant_narrative(findings: list[dict[str, Any]]) -> str:
    paragraphs: list[str] = []

    for finding in findings:
        if finding.get("finding_type") == "pharmacogenomic":
            continue

        gene = clean(finding.get("gene")) or "the reported locus"
        condition = clean(finding.get("condition")) or "the candidate condition"
        coordinate = clean(
            finding.get("coordinate", {}).get("display")
        )
        classification = clean(
            finding.get("classification", {}).get("label")
        )
        source = clean(
            finding.get("classification", {}).get("source")
        )
        score = clean(finding.get("pipeline_score_100"))
        priority = clean(finding.get("pipeline_priority"))
        evidence_summary = clean(
            finding.get("evidence", {}).get("evidence_summary")
        )
        interpretation_note = clean(
            finding.get("evidence", {}).get("interpretation_note")
        )

        parts = [
            f"{coordinate or 'The finding'} in {gene} was associated with "
            f"{condition} by the pipeline."
        ]

        if classification:
            parts.append(
                f"The draft classification field is {classification}"
                + (f" from {source}" if source else "")
                + "."
            )
        if score:
            parts.append(
                f"The pipeline prioritisation score was {score}/100"
                + (f" with status {priority}" if priority else "")
                + "; this is not a pathogenicity probability."
            )
        if evidence_summary:
            parts.append(f"Recorded evidence: {evidence_summary}.")
        if interpretation_note:
            parts.append(interpretation_note)

        paragraphs.append(" ".join(parts))

    return "\n\n".join(paragraphs)


def build_patient_section(
    case_id: str,
    metadata: dict[str, Any],
    summary: dict[str, str],
) -> dict[str, Any]:
    patient_data = metadata.get("patient", metadata)

    return {
        "case_id": case_id,
        "patient_name": patient_data.get("patient_name"),
        "sex": patient_data.get("sex") or patient_data.get("reported_sex"),
        "date_of_birth": patient_data.get("date_of_birth"),
        "indication": patient_data.get("indication"),
        "ordering_physician": patient_data.get("ordering_physician"),
        "account_number": patient_data.get("account_number"),
        "specimen": patient_data.get("specimen"),
        "reported_date": patient_data.get("reported_date"),
        "collected_date": patient_data.get("collected_date"),
        "received_date": patient_data.get("received_date"),
    }


def strip_internal_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_internal_fields(item)
            for key, item in value.items()
            if not key.startswith("_")
        }
    if isinstance(value, list):
        return [strip_internal_fields(item) for item in value]
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a schema-1.0 draft report JSON from completed pipeline "
            "outputs."
        )
    )
    parser.add_argument("case_id")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root; normally inferred from this script.",
    )
    parser.add_argument(
        "--metadata-json",
        type=Path,
        default=None,
        help="Optional protected administrative/clinical metadata JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Override the default draft JSON output path.",
    )
    parser.add_argument(
        "--selected-variant",
        action="append",
        default=[],
        help=(
            "Explicit genomic variant key to report. Repeat this option for "
            "multiple selected variants."
        ),
    )
    parser.add_argument(
        "--include-all-high-priority",
        action="store_true",
        help=(
            "Also add high-priority candidates from diseases other than the "
            "top-ranked disease."
        ),
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=10,
        help="Maximum automatically selected master-table findings.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    case_id = clean(args.case_id)

    if not re.fullmatch(r"[A-Za-z0-9._-]+", case_id):
        raise SystemExit("ERROR: Unsafe case ID.")

    if args.max_findings < 1:
        raise SystemExit("ERROR: --max-findings must be at least 1.")

    project_root = (
        args.project_root.expanduser().resolve()
        if args.project_root
        else Path(__file__).resolve().parents[2]
    )

    case_result = project_root / "results" / "cases" / case_id
    final_dir = case_result / "final"
    report_dir = final_dir / "report"

    master_table = final_dir / f"{case_id}.master_candidate_ranking.tsv"
    summary_file = final_dir / f"{case_id}.pipeline_summary.tsv"
    resource_mode_file = final_dir / f"{case_id}.resource_mode.tsv"
    vep_table = (
        case_result
        / "annotated"
        / f"{case_id}.vep_best_transcripts.tsv"
    )
    hpo_file = (
        project_root
        / "input"
        / "cases"
        / case_id
        / "staged"
        / f"{case_id}.pipeline_phenotypes.txt"
    )
    local_pgx_table = (
        case_result
        / "clinpgx"
        / f"{case_id}.local_pgx_matches.tsv"
    )
    official_pgx_table = (
        case_result
        / "clinpgx"
        / f"{case_id}.clinpgx_matches.tsv"
    )
    repeat_table = (
        final_dir
        / f"{case_id}.repeat_expansions.detected.tsv"
    )

    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else report_dir / f"{case_id}.report_draft.json"
    )

    summary = read_metric_tsv(summary_file)
    resource_mode = read_metric_tsv(resource_mode_file)
    master_rows = read_tsv(master_table)
    repeat_rows = read_tsv(repeat_table)

    if not master_rows and not repeat_rows:
        raise SystemExit(
            "ERROR: Neither a master candidate table nor a repeat-expansion "
            f"report was found for {case_id}."
        )

    metadata_path = (
        args.metadata_json.expanduser().resolve()
        if args.metadata_json
        else find_default_metadata(project_root, case_id)
    )
    metadata = load_metadata(metadata_path)
    vep_index = load_vep_index(vep_table)

    selected_rows, warnings = choose_master_rows(
        master_rows,
        args.selected_variant,
        args.include_all_high_priority,
        args.max_findings,
    )

    findings: list[dict[str, Any]] = []

    for row in selected_rows:
        finding = candidate_to_finding(
            row,
            vep_index,
            len(findings) + 1,
        )
        finding["_source_variant"] = clean(row.get("variant"))
        findings.append(finding)

    for row in repeat_rows:
        findings.append(
            repeat_to_finding(row, len(findings) + 1)
        )

    local_pgx_rows = read_tsv(local_pgx_table)
    official_pgx_rows = read_tsv(official_pgx_table)

    attach_pgx_findings(
        findings,
        local_pgx_rows,
        official_pgx_rows,
        warnings,
    )

    if repeat_rows:
        warnings.append(
            "Repeat-expansion records were detected but not independently "
            "sized or clinically classified by this workflow."
        )

    hpo_terms = load_hpo_terms(hpo_file)
    phenotype_summary = (
        "Submitted HPO terms: " + ", ".join(hpo_terms)
        if hpo_terms
        else ""
    )

    patient = build_patient_section(
        case_id,
        metadata,
        summary,
    )

    if not patient.get("patient_name"):
        warnings.append(
            "Patient name was not available from protected report metadata."
        )
    if not patient.get("sex"):
        patient["sex"] = "Other/Unspecified"
        warnings.append(
            "Patient sex was not available from protected report metadata."
        )

    variant_narrative = build_variant_narrative(findings)

    report = {
        "schema_version": SCHEMA_VERSION,
        "report_status": "draft",
        "laboratory": {
            "name": (
                metadata.get("laboratory", {}).get("name")
                if isinstance(metadata.get("laboratory"), dict)
                else None
            )
            or "Genosphere Clinical Genome Center",
            "subtitle": (
                metadata.get("laboratory", {}).get("subtitle")
                if isinstance(metadata.get("laboratory"), dict)
                else None
            )
            or "Educational Genomic Variant Interpretation",
            "signatory": (
                metadata.get("laboratory", {}).get("signatory")
                if isinstance(metadata.get("laboratory"), dict)
                else None
            )
            or (
                "Prepared for educational demonstration; "
                "not clinically signed out."
            ),
        },
        "patient": patient,
        "test": {
            "report_title": metadata.get(
                "report_title",
                "GENOMIC VARIANT INTERPRETATION REPORT",
            ),
            "genome_build": summary.get("assembly", "GRCh38"),
            "analysis_mode": (
                resource_mode.get("pipeline_mode")
                or metadata.get("analysis_mode")
                or "unknown"
            ),
            "pipeline_status": "completed",
        },
        "findings": findings,
        "narrative": {
            "patient_phenotype": (
                metadata.get("phenotype_summary")
                or phenotype_summary
            ),
            "variant_information": variant_narrative,
            "gene_information": metadata.get(
                "gene_information",
                "",
            ),
        },
        "references": metadata.get("references", []),
        "recommendations": metadata.get(
            "recommendations",
            [
                "Clinical correlation is recommended.",
                "Genetic counselling is recommended.",
                (
                    "Orthogonal confirmation is recommended before "
                    "clinical use."
                ),
                (
                    "The complete candidate table should be reviewed before "
                    "a reporting decision is finalised."
                ),
            ],
        ),
        "provenance": {
            "generated_utc": now_utc(),
            "generator": (
                "pipeline/case_workflow/"
                "22_build_clinical_report_json.py"
            ),
            "case_id": case_id,
            "master_table": (
                str(master_table.relative_to(project_root))
                if master_table.is_file()
                else None
            ),
            "master_table_sha256": sha256_file(master_table),
            "pipeline_summary": (
                str(summary_file.relative_to(project_root))
                if summary_file.is_file()
                else None
            ),
            "pipeline_summary_sha256": sha256_file(summary_file),
            "phenotype_file": (
                str(hpo_file.relative_to(project_root))
                if hpo_file.is_file()
                else None
            ),
            "phenotype_sha256": sha256_file(hpo_file),
            "metadata_file": (
                str(metadata_path.relative_to(project_root))
                if metadata_path
                and metadata_path.is_file()
                and metadata_path.is_relative_to(project_root)
                else str(metadata_path)
                if metadata_path
                else None
            ),
            "resource_mode": resource_mode.get("pipeline_mode"),
            "selection_method": (
                "explicit_selected_variants"
                if args.selected_variant
                else (
                    "top_disease_plus_all_high_priority"
                    if args.include_all_high_priority
                    else "top_disease_group"
                )
            ),
        },
        "warnings": sorted(set(warnings)),
        "review": {
            "analyst_review_required": True,
            "reviewed_utc": None,
        },
    }

    report = strip_internal_fields(report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    checksum_path = output_path.with_suffix(
        output_path.suffix + ".sha256"
    )
    checksum_path.write_text(
        f"{sha256_file(output_path)}  {output_path.name}\n",
        encoding="utf-8",
    )

    print("=" * 68)
    print("CLINICAL REPORT DRAFT JSON CREATED")
    print("=" * 68)
    print(f"Case ID:             {case_id}")
    print(f"Master candidates:   {len(master_rows)}")
    print(f"Selected findings:   {len(findings)}")
    print(f"Repeat findings:     {len(repeat_rows)}")
    print(f"HPO terms:           {len(hpo_terms)}")
    print(f"Metadata:            {metadata_path or 'not provided'}")
    print(f"Output:              {output_path}")
    print(f"Checksum:            {checksum_path}")
    print()
    print("IMPORTANT: This is an unreviewed draft JSON.")


if __name__ == "__main__":
    main()

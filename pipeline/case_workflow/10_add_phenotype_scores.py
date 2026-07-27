#!/usr/bin/env python3

import csv
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path


HPO_PATTERN = re.compile(r"\bHP:\d{7}\b", flags=re.I)

ADDED_COLUMNS = [
    "patient_hpo_count",
    "disease_hpo_count",
    "matched_hpo_count",
    "matched_hpo_terms",
    "phenotype_patient_coverage",
    "phenotype_match_status",
    "phenotype_match_method",
]


def clean(value: str) -> str:
    return value.strip() if value else ""


def normalize_disease_name(value: str) -> str:
    value = clean(value).lower().replace("_", " ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def extract_hpo_terms(value: str) -> set[str]:
    return {
        match.upper()
        for match in HPO_PATTERN.findall(value or "")
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


def load_g2p_phenotypes(path: Path):
    """
    Build multiple indexes because candidate tables may identify a
    disease by its name, MONDO identifier, or MIM identifier.
    """

    by_gene_disease = defaultdict(set)
    by_gene_mondo = defaultdict(set)
    by_gene_mim = defaultdict(set)

    with path.open(
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            gene = clean(row.get("gene symbol", "")).upper()
            disease = normalize_disease_name(
                row.get("disease name", "")
            )
            mondo = clean(row.get("disease MONDO", "")).upper()
            mim = clean(row.get("disease mim", ""))
            phenotypes = extract_hpo_terms(
                row.get("phenotypes", "")
            )

            if not gene or not phenotypes:
                continue

            if disease:
                by_gene_disease[(gene, disease)].update(
                    phenotypes
                )

            if mondo:
                by_gene_mondo[(gene, mondo)].update(
                    phenotypes
                )

            if mim:
                by_gene_mim[(gene, mim)].update(
                    phenotypes
                )

    return by_gene_disease, by_gene_mondo, by_gene_mim


def find_disease_phenotypes(
    row: dict[str, str],
    by_gene_disease,
    by_gene_mondo,
    by_gene_mim,
) -> set[str]:
    gene = clean(row.get("gene", "")).upper()

    g2p_disease = normalize_disease_name(
        row.get("g2p_disease_name", "")
    )

    mondo = clean(row.get("disease_mondo", "")).upper()
    mim = clean(row.get("disease_mim", ""))

    if gene and g2p_disease:
        terms = by_gene_disease.get(
            (gene, g2p_disease),
            set(),
        )

        if terms:
            return set(terms)

    if gene and mondo:
        terms = by_gene_mondo.get(
            (gene, mondo),
            set(),
        )

        if terms:
            return set(terms)

    if gene and mim:
        terms = by_gene_mim.get(
            (gene, mim),
            set(),
        )

        if terms:
            return set(terms)

    return set()


def phenotype_points(match_count: int) -> int:
    """
    Transparent educational score:
    one point per exact HPO match, maximum five.
    """

    return min(5, max(0, match_count))


def safe_integer(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def priority_label(
    final_score: int,
    clinvar_points: int,
) -> str:
    if clinvar_points < 0:
        return "deprioritized"

    if final_score >= 17:
        return "high_priority_candidate"

    if final_score >= 10:
        return "moderate_priority_candidate"

    return "low_priority_candidate"


def main() -> None:
    if len(sys.argv) not in {2, 3, 4}:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/"
            "10_add_phenotype_scores.py "
            "CASE_ID [PHENOTYPE_FILE] [G2P_RESOURCE]"
        )
        sys.exit(1)

    case_id = sys.argv[1]

    script_path = Path(__file__).resolve()
    project_root = script_path.parents[2]

    if len(sys.argv) >= 3:
        phenotype_argument = Path(sys.argv[2])

        if phenotype_argument.is_absolute():
            phenotype_file = phenotype_argument
        else:
            phenotype_file = (
                project_root / phenotype_argument
            )
    else:
        phenotype_file = (
            project_root
            / "input"
            / "cases"
            / case_id
            / "phenotypes.txt"
        )

    input_table = (
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

    if len(sys.argv) == 4:
        g2p_argument = Path(sys.argv[3])
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

    output_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.variant_gene_disease_scores.final.tsv"
    )

    qc_file = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.phenotype_scoring_qc.tsv"
    )

    for required in [
        phenotype_file,
        input_table,
        g2p_file,
    ]:
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
        print(
            "ERROR: No valid HP:####### terms were found in:"
        )
        print(phenotype_file)
        sys.exit(1)

    (
        by_gene_disease,
        by_gene_mondo,
        by_gene_mim,
    ) = load_g2p_phenotypes(g2p_file)

    output_rows = []
    rows_with_disease_phenotypes = 0
    rows_with_exact_matches = 0

    with input_table.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        original_columns = reader.fieldnames or []

        output_columns = list(original_columns)

        for column in ADDED_COLUMNS:
            if column not in output_columns:
                output_columns.append(column)

        for row in reader:
            disease_hpo = find_disease_phenotypes(
                row,
                by_gene_disease,
                by_gene_mondo,
                by_gene_mim,
            )

            matched_hpo = patient_hpo & disease_hpo
            match_count = len(matched_hpo)

            points = phenotype_points(match_count)

            score_before = safe_integer(
                row.get(
                    "score_before_phenotype",
                    row.get("final_score", "0"),
                )
            )

            new_final_score = score_before + points

            if disease_hpo:
                rows_with_disease_phenotypes += 1
                match_status = (
                    "exact_hpo_match"
                    if matched_hpo
                    else "no_exact_hpo_match"
                )
            else:
                match_status = "no_g2p_phenotypes_available"

            if matched_hpo:
                rows_with_exact_matches += 1

            coverage = (
                len(matched_hpo) / len(patient_hpo)
                if patient_hpo
                else 0.0
            )

            row["patient_hpo_count"] = str(
                len(patient_hpo)
            )

            row["disease_hpo_count"] = str(
                len(disease_hpo)
            )

            row["matched_hpo_count"] = str(
                match_count
            )

            row["matched_hpo_terms"] = ";".join(
                sorted(matched_hpo)
            )

            row["phenotype_patient_coverage"] = (
                f"{coverage:.4f}"
            )

            row["phenotype_match_status"] = match_status

            row["phenotype_match_method"] = (
                "exact_HPO_ID_overlap"
            )

            row["phenotype_points"] = str(points)
            row["final_score"] = str(new_final_score)

            clinvar_points = safe_integer(
                row.get("clinvar_points", "0")
            )

            row["priority"] = priority_label(
                new_final_score,
                clinvar_points,
            )

            output_rows.append(row)

    output_rows.sort(
        key=lambda row: (
            -safe_integer(row.get("final_score", "0")),
            -safe_integer(row.get("clinvar_points", "0")),
            clean(row.get("gene", "")),
            clean(row.get("candidate_disease", "")),
        )
    )

    for rank, row in enumerate(output_rows, start=1):
        row["rank"] = str(rank)

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

    high_priority = sum(
        row.get("priority") == "high_priority_candidate"
        for row in output_rows
    )

    top_gene = (
        clean(output_rows[0].get("gene", ""))
        if output_rows
        else ""
    )

    top_disease = (
        clean(
            output_rows[0].get(
                "candidate_disease",
                "",
            )
        )
        if output_rows
        else ""
    )

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(
            [
                "phenotype_file",
                str(
                    phenotype_file.relative_to(project_root)
                ),
            ]
        )
        writer.writerow(
            ["g2p_resource", g2p_resource_display]
        )
        writer.writerow(
            ["g2p_resource_sha256", g2p_resource_sha256]
        )
        writer.writerow(
            ["patient_hpo_terms", len(patient_hpo)]
        )
        writer.writerow(
            ["candidate_rows", len(output_rows)]
        )
        writer.writerow(
            [
                "rows_with_g2p_phenotypes",
                rows_with_disease_phenotypes,
            ]
        )
        writer.writerow(
            [
                "rows_with_exact_hpo_match",
                rows_with_exact_matches,
            ]
        )
        writer.writerow(
            [
                "phenotype_scoring_method",
                "one_point_per_exact_HPO_match_maximum_5",
            ]
        )
        writer.writerow(
            [
                "high_priority_candidates",
                high_priority,
            ]
        )
        writer.writerow(["top_ranked_gene", top_gene])
        writer.writerow(
            ["top_ranked_disease", top_disease]
        )
        writer.writerow(
            [
                "output_table",
                str(output_table.relative_to(project_root)),
            ]
        )

    print("========================================")
    print("PHENOTYPE-AWARE DISEASE SCORING")
    print("========================================")
    print(f"Case ID:                 {case_id}")
    print(f"Patient HPO terms:       {len(patient_hpo)}")
    print(f"Candidate rows:          {len(output_rows)}")
    print(
        "Rows with HPO matches:  "
        f"{rows_with_exact_matches}"
    )
    print(f"Top-ranked gene:         {top_gene}")
    print(f"Top-ranked disease:      {top_disease}")
    print()
    print(f"Output: {output_table}")
    print(f"QC:     {qc_file}")
    print()
    print(
        "PHENOTYPE SCORING COMPLETED SUCCESSFULLY"
    )


if __name__ == "__main__":
    main()

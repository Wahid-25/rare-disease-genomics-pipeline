#!/usr/bin/env python3

import csv
import re
import sys
from pathlib import Path
from urllib.parse import unquote


def clean(value):
    return value.strip() if value else ""


def safe_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def normalized(value):
    value = unquote(clean(value))
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def first_available(row, names):
    for name in names:
        value = clean(row.get(name, ""))

        if value:
            return value

    return ""


def clinvar_score_floor(significance, review_status):
    significance = normalized(significance).lower()
    review_status = normalized(review_status).lower()

    if (
        "benign" in significance
        and "pathogenic" not in significance
    ):
        return 0, "benign_or_likely_benign"

    if "pathogenic" not in significance:
        return 0, "no_pathogenic_clinvar_assertion"

    likely_only = (
        "likely pathogenic" in significance
        and significance.replace(
            "likely pathogenic",
            "",
        ).strip(" /,;") == ""
    )

    if likely_only:
        if (
            "practice guideline" in review_status
            or "expert panel" in review_status
        ):
            return 14, "likely_pathogenic_strong_review"

        if "multiple submitters" in review_status:
            return 12, "likely_pathogenic_multiple_submitters"

        if "criteria provided" in review_status:
            return 10, "likely_pathogenic_criteria_provided"

        return 9, "likely_pathogenic_assertion"

    if (
        "practice guideline" in review_status
        or "expert panel" in review_status
    ):
        return 17, "pathogenic_authoritative_review"

    if (
        "multiple submitters" in review_status
        and "no conflicts" in review_status
    ):
        return 15, "pathogenic_multiple_submitters_no_conflicts"

    if "criteria provided" in review_status:
        return 13, "pathogenic_criteria_provided"

    return 11, "pathogenic_assertion"


def poor_disease_label(value):
    value = normalized(value).lower()

    if not value:
        return True

    unwanted = (
        "diagnostic test",
        "not provided",
        "not specified",
        "screening",
        "finding",
    )

    return any(term in value for term in unwanted)


def choose_clinvar_condition(raw_value, gene):
    raw_value = clean(raw_value)

    if not raw_value:
        return ""

    candidates = []

    for index, value in enumerate(
        re.split(r"[|;]+", raw_value)
    ):
        value = normalized(value).strip(" ,")

        if not value:
            continue

        lowered = value.lower()

        excluded = (
            "diagnostic test",
            "not provided",
            "not specified",
            "screening",
        )

        if any(term in lowered for term in excluded):
            continue

        candidates.append((index, value))

    if not candidates:
        return ""

    gene_lower = clean(gene).lower()

    specific = [
        item
        for item in candidates
        if not (
            gene_lower
            and item[1].lower()
            in {
                f"{gene_lower}-related disorder",
                f"{gene_lower} related disorder",
            }
        )
    ]

    if specific:
        candidates = specific

    candidates.sort(
        key=lambda item: (
            len(item[1].split()),
            len(item[1]),
            item[0],
        )
    )

    return candidates[0][1]


def priority(score, significance, old_priority):
    significance = normalized(significance).lower()

    if (
        "benign" in significance
        and "pathogenic" not in significance
    ):
        return "deprioritized"

    if old_priority == "deprioritized":
        return old_priority

    if score >= 17:
        return "high_priority_candidate"

    if score >= 10:
        return "moderate_priority_candidate"

    return "low_priority_candidate"


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: 10b_calibrate_clinvar_ranking.py CASE_ID"
        )

    case_id = sys.argv[1]
    root = Path(__file__).resolve().parents[2]

    table = (
        root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.variant_gene_disease_scores.final.tsv"
    )

    qc = table.with_name(
        f"{case_id}.clinvar_ranking_calibration_qc.tsv"
    )

    if not table.is_file():
        raise SystemExit(
            f"ERROR: Scoring table not found: {table}"
        )

    with table.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    added_columns = [
        "pre_calibration_score",
        "clinvar_priority_floor",
        "candidate_disease_source",
        "ranking_calibration_note",
    ]

    for column in added_columns:
        if column not in fieldnames:
            fieldnames.append(column)

    score_changed = 0
    disease_changed = 0

    for row in rows:
        original_score = safe_int(
            row.get(
                "pre_calibration_score",
                row.get("final_score", "0"),
            )
        )

        significance = first_available(
            row,
            [
                "clinvar_significance",
                "CLNSIG",
            ],
        )

        review_status = first_available(
            row,
            [
                "clinvar_review_status",
                "CLNREVSTAT",
            ],
        )

        floor, note = clinvar_score_floor(
            significance,
            review_status,
        )

        calibrated_score = max(
            original_score,
            floor,
        )

        if calibrated_score != original_score:
            score_changed += 1

        current_disease = clean(
            row.get("candidate_disease", "")
        )

        condition_names = first_available(
            row,
            [
                "clinvar_disease_names",
                "clinvar_conditions",
                "clinvar_diseases",
                "clinvar_condition",
                "clinvar_disease",
            ],
        )

        selected_condition = choose_clinvar_condition(
            condition_names,
            row.get("gene", ""),
        )

        disease_source = "existing_candidate_disease"

        if (
            poor_disease_label(current_disease)
            and selected_condition
        ):
            row["candidate_disease"] = selected_condition
            disease_source = "cleaned_clinvar_condition"
            disease_changed += 1

        row["pre_calibration_score"] = str(
            original_score
        )
        row["clinvar_priority_floor"] = str(floor)
        row["final_score"] = str(calibrated_score)
        row["priority"] = priority(
            calibrated_score,
            significance,
            clean(row.get("priority", "")),
        )
        row["candidate_disease_source"] = (
            disease_source
        )
        row["ranking_calibration_note"] = note

    rows.sort(
        key=lambda row: (
            -safe_int(row.get("final_score")),
            -safe_int(row.get("matched_hpo_count")),
            clean(row.get("gene", "")),
            clean(row.get("candidate_disease", "")),
        )
    )

    for rank, row in enumerate(rows, start=1):
        row["rank"] = str(rank)

    temporary = table.with_suffix(".tmp")

    with temporary.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(table)

    with qc.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(["candidate_rows", len(rows)])
        writer.writerow(
            ["scores_changed", score_changed]
        )
        writer.writerow(
            ["disease_labels_changed", disease_changed]
        )
        writer.writerow(
            ["top_gene", rows[0].get("gene", "") if rows else ""]
        )
        writer.writerow(
            [
                "top_disease",
                rows[0].get("candidate_disease", "")
                if rows else "",
            ]
        )
        writer.writerow(
            [
                "top_score",
                rows[0].get("final_score", "")
                if rows else "",
            ]
        )

    print(f"Updated: {table}")
    print(f"QC:      {qc}")

    if rows:
        print(
            "Top:     "
            f"{rows[0].get('gene', '')} | "
            f"{rows[0].get('candidate_disease', '')} | "
            f"score={rows[0].get('final_score', '')}"
        )


if __name__ == "__main__":
    main()

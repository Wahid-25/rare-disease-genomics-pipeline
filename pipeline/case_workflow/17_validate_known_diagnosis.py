#!/usr/bin/env python3

import csv
import hashlib
import re
import sys
from pathlib import Path


REQUIRED_TRUTH_COLUMNS = {
    "expected_gene",
    "expected_disease",
    "expected_variant",
    "expected_candidate_type",
    "max_acceptable_rank",
}


def clean(value) -> str:
    return str(value).strip() if value is not None else ""


def safe_int(value, default=None):
    try:
        return int(float(clean(value)))
    except (TypeError, ValueError):
        return default


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


def normalize_gene(value: str) -> str:
    return clean(value).upper()


def normalize_text(value: str) -> str:
    value = clean(value).lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def normalize_variant(value: str) -> str:
    value = clean(value).lower()
    value = re.sub(r"\s+", "", value)

    if value.startswith("chr"):
        value = value[3:]

    return value


def normalize_candidate_type(value: str) -> str:
    value = clean(value).lower()
    value = value.replace("-", "_")
    value = value.replace(" ", "_")

    aliases = {
        "snv": "small_variant",
        "indel": "small_variant",
        "snv_indel": "small_variant",
        "smallvariant": "small_variant",
        "structural_variant": "cnv",
        "copy_number_variant": "cnv",
    }

    return aliases.get(value, value)


def split_alternatives(value: str) -> list[str]:
    return [
        item.strip()
        for item in clean(value).split("|")
        if item.strip()
    ]


def disease_matches(
    expected_value: str,
    observed_value: str,
) -> bool:
    expected_options = split_alternatives(expected_value)

    if not expected_options:
        return True

    observed = normalize_text(observed_value)

    if not observed:
        return False

    for expected_option in expected_options:
        expected = normalize_text(expected_option)

        if not expected:
            continue

        if expected == observed:
            return True

        if expected in observed or observed in expected:
            return True

    return False


def gene_matches(
    expected_value: str,
    observed_value: str,
) -> bool:
    expected_options = {
        normalize_gene(item)
        for item in split_alternatives(expected_value)
    }

    if not expected_options:
        return True

    return normalize_gene(observed_value) in expected_options


def variant_matches(
    expected_value: str,
    observed_value: str,
) -> bool:
    expected_options = {
        normalize_variant(item)
        for item in split_alternatives(expected_value)
    }

    if not expected_options:
        return True

    return normalize_variant(observed_value) in expected_options


def candidate_type_matches(
    expected_value: str,
    observed_value: str,
) -> bool:
    expected_options = {
        normalize_candidate_type(item)
        for item in split_alternatives(expected_value)
    }

    if not expected_options:
        return True

    return (
        normalize_candidate_type(observed_value)
        in expected_options
    )


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        return list(reader)


def best_rank(
    candidates: list[dict[str, str]],
    predicate,
):
    matching = [
        candidate
        for candidate in candidates
        if predicate(candidate)
    ]

    if not matching:
        return None

    matching.sort(
        key=lambda row: safe_int(
            row.get("overall_rank"),
            10**9,
        )
    )

    return matching[0]


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage:\n"
            "python3 "
            "pipeline/case_workflow/"
            "17_validate_known_diagnosis.py "
            "CASE_ID TRUTH_FILE"
        )
        sys.exit(1)

    case_id = sys.argv[1]
    truth_file = Path(sys.argv[2]).expanduser().resolve()

    project_root = Path(__file__).resolve().parents[2]

    final_dir = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
    )

    ranking_file = (
        final_dir
        / f"{case_id}.master_candidate_ranking.tsv"
    )

    detailed_output = (
        final_dir
        / f"{case_id}.blinded_validation.tsv"
    )

    summary_output = (
        final_dir
        / f"{case_id}.blinded_validation_summary.tsv"
    )

    if not truth_file.is_file():
        raise SystemExit(
            f"ERROR: Truth file not found: {truth_file}"
        )

    if not ranking_file.is_file():
        raise SystemExit(
            f"ERROR: Master ranking not found: {ranking_file}"
        )

    truth_rows = load_tsv(truth_file)
    candidates = load_tsv(ranking_file)

    if not truth_rows:
        raise SystemExit(
            "ERROR: Truth file contains no expected diagnoses."
        )

    if not candidates:
        raise SystemExit(
            "ERROR: Master candidate ranking is empty."
        )

    truth_headers = set(truth_rows[0].keys())

    missing_columns = (
        REQUIRED_TRUTH_COLUMNS - truth_headers
    )

    if missing_columns:
        raise SystemExit(
            "ERROR: Truth file is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    validation_rows = []

    for truth_number, truth in enumerate(
        truth_rows,
        start=1,
    ):
        expected_gene = clean(
            truth.get("expected_gene")
        )

        expected_disease = clean(
            truth.get("expected_disease")
        )

        expected_variant = clean(
            truth.get("expected_variant")
        )

        expected_type = clean(
            truth.get("expected_candidate_type")
        )

        max_rank = safe_int(
            truth.get("max_acceptable_rank"),
            10,
        )

        if max_rank is None or max_rank < 1:
            max_rank = 10

        if not expected_gene and not expected_disease:
            raise SystemExit(
                "ERROR: Each truth row must contain at least "
                "an expected gene or disease."
            )

        def full_match(candidate):
            return (
                gene_matches(
                    expected_gene,
                    candidate.get("gene", ""),
                )
                and disease_matches(
                    expected_disease,
                    candidate.get(
                        "candidate_disease",
                        "",
                    ),
                )
                and variant_matches(
                    expected_variant,
                    candidate.get("variant", ""),
                )
                and candidate_type_matches(
                    expected_type,
                    candidate.get(
                        "candidate_type",
                        "",
                    ),
                )
            )

        matched_candidate = best_rank(
            candidates,
            full_match,
        )

        gene_candidate = best_rank(
            candidates,
            lambda candidate: gene_matches(
                expected_gene,
                candidate.get("gene", ""),
            ),
        )

        disease_candidate = best_rank(
            candidates,
            lambda candidate: disease_matches(
                expected_disease,
                candidate.get(
                    "candidate_disease",
                    "",
                ),
            ),
        )

        variant_candidate = None

        if expected_variant:
            variant_candidate = best_rank(
                candidates,
                lambda candidate: variant_matches(
                    expected_variant,
                    candidate.get("variant", ""),
                ),
            )

        matched_rank = (
            safe_int(
                matched_candidate.get("overall_rank")
            )
            if matched_candidate
            else None
        )

        if matched_rank is None:
            status = "NOT_FOUND"
        elif matched_rank <= max_rank:
            status = "MATCHED_WITHIN_THRESHOLD"
        else:
            status = "MATCHED_BELOW_THRESHOLD"

        validation_rows.append(
            {
                "truth_record": str(truth_number),
                "expected_gene": expected_gene,
                "expected_disease": expected_disease,
                "expected_variant": expected_variant,
                "expected_candidate_type": expected_type,
                "max_acceptable_rank": str(max_rank),
                "validation_status": status,
                "matched_overall_rank": (
                    str(matched_rank)
                    if matched_rank is not None
                    else ""
                ),
                "matched_candidate_type": (
                    clean(
                        matched_candidate.get(
                            "candidate_type"
                        )
                    )
                    if matched_candidate
                    else ""
                ),
                "matched_gene": (
                    clean(matched_candidate.get("gene"))
                    if matched_candidate
                    else ""
                ),
                "matched_disease": (
                    clean(
                        matched_candidate.get(
                            "candidate_disease"
                        )
                    )
                    if matched_candidate
                    else ""
                ),
                "matched_variant": (
                    clean(
                        matched_candidate.get("variant")
                    )
                    if matched_candidate
                    else ""
                ),
                "matched_normalized_score": (
                    clean(
                        matched_candidate.get(
                            "normalized_score_100"
                        )
                    )
                    if matched_candidate
                    else ""
                ),
                "matched_priority": (
                    clean(
                        matched_candidate.get("priority")
                    )
                    if matched_candidate
                    else ""
                ),
                "top1_match": (
                    "yes"
                    if matched_rank == 1
                    else "no"
                ),
                "top5_match": (
                    "yes"
                    if matched_rank is not None
                    and matched_rank <= 5
                    else "no"
                ),
                "top10_match": (
                    "yes"
                    if matched_rank is not None
                    and matched_rank <= 10
                    else "no"
                ),
                "best_gene_rank": (
                    clean(
                        gene_candidate.get(
                            "overall_rank"
                        )
                    )
                    if gene_candidate
                    else ""
                ),
                "best_disease_rank": (
                    clean(
                        disease_candidate.get(
                            "overall_rank"
                        )
                    )
                    if disease_candidate
                    else ""
                ),
                "best_variant_rank": (
                    clean(
                        variant_candidate.get(
                            "overall_rank"
                        )
                    )
                    if variant_candidate
                    else ""
                ),
                "notes": clean(truth.get("notes")),
            }
        )

    detailed_columns = [
        "truth_record",
        "expected_gene",
        "expected_disease",
        "expected_variant",
        "expected_candidate_type",
        "max_acceptable_rank",
        "validation_status",
        "matched_overall_rank",
        "matched_candidate_type",
        "matched_gene",
        "matched_disease",
        "matched_variant",
        "matched_normalized_score",
        "matched_priority",
        "top1_match",
        "top5_match",
        "top10_match",
        "best_gene_rank",
        "best_disease_rank",
        "best_variant_rank",
        "notes",
    ]

    with detailed_output.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=detailed_columns,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(validation_rows)

    expected_count = len(validation_rows)

    matched_count = sum(
        row["validation_status"]
        != "NOT_FOUND"
        for row in validation_rows
    )

    within_threshold_count = sum(
        row["validation_status"]
        == "MATCHED_WITHIN_THRESHOLD"
        for row in validation_rows
    )

    top1_count = sum(
        row["top1_match"] == "yes"
        for row in validation_rows
    )

    top5_count = sum(
        row["top5_match"] == "yes"
        for row in validation_rows
    )

    top10_count = sum(
        row["top10_match"] == "yes"
        for row in validation_rows
    )

    if within_threshold_count == expected_count:
        overall_status = "PASS"
    elif matched_count > 0:
        overall_status = "PARTIAL_PASS"
    else:
        overall_status = "FAIL"

    with summary_output.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")

        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(
            ["validation_status", overall_status]
        )
        writer.writerow(
            ["expected_truth_records", expected_count]
        )
        writer.writerow(
            ["matched_truth_records", matched_count]
        )
        writer.writerow(
            [
                "matched_within_threshold",
                within_threshold_count,
            ]
        )
        writer.writerow(["top1_matches", top1_count])
        writer.writerow(["top5_matches", top5_count])
        writer.writerow(["top10_matches", top10_count])
        writer.writerow(
            [
                "candidate_rows_evaluated",
                len(candidates),
            ]
        )
        writer.writerow(
            [
                "truth_file_sha256",
                sha256_file(truth_file),
            ]
        )
        writer.writerow(
            [
                "truth_used_during_pipeline",
                "no",
            ]
        )
        writer.writerow(
            [
                "master_ranking",
                str(
                    ranking_file.relative_to(
                        project_root
                    )
                ),
            ]
        )
        writer.writerow(
            [
                "detailed_validation",
                str(
                    detailed_output.relative_to(
                        project_root
                    )
                ),
            ]
        )

    print("========================================")
    print("BLINDED DIAGNOSIS VALIDATION")
    print("========================================")
    print(f"Case ID:                   {case_id}")
    print(f"Validation status:         {overall_status}")
    print(f"Expected truth records:    {expected_count}")
    print(f"Matched records:           {matched_count}")
    print(
        "Within rank threshold:     "
        f"{within_threshold_count}"
    )
    print(f"Top-1 matches:             {top1_count}")
    print(f"Top-5 matches:             {top5_count}")
    print(f"Top-10 matches:            {top10_count}")
    print()
    print(f"Detailed result: {detailed_output}")
    print(f"Summary:         {summary_output}")
    print()

    for row in validation_rows:
        print(
            f"Truth {row['truth_record']}: "
            f"{row['expected_gene']} | "
            f"{row['expected_disease']} | "
            f"{row['validation_status']} | "
            f"rank={row['matched_overall_rank'] or 'not found'}"
        )

    if overall_status == "FAIL":
        sys.exit(2)


if __name__ == "__main__":
    main()

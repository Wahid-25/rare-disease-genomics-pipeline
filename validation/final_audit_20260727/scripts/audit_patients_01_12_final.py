#!/usr/bin/env python3
"""Final canonical validation audit for Patients 01-12.

Recognises:
- CURRENT: completed real-patient runs;
- ROUTED_REPEAT: repeat expansions detected and correctly excluded from
  ordinary small-variant ranking;
- LEGACY: reusable earlier outputs with a master ranking and final
  annotated VCF.

For legacy runs, the master-ranking first row is treated as the result
source of truth, avoiding stale pipeline-summary fields.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


RESULTS_ROOT = Path("results/cases")
SAMPLE_SHEET = Path(
    "validation/universal_pipeline_testing/inputs/reference/sample_sheet.csv"
)
PGX_REFERENCE = Path(
    "resources/clinpgx/local_curated_pgx_reference.csv"
)

SUPPORTED_ROUTED_STATUSES = {
    "COMPLETED_WITH_UNSUPPORTED_VARIANTS",
    "COMPLETED_WITH_SUPPORTED_AND_UNSUPPORTED_VARIANTS",
}


def read_two_column_tsv(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}

    if not path.is_file():
        return data

    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) >= 2 and row[0] not in {"field", "metric"}:
                data[row[0]] = row[1]

    return data


def read_first_tsv_row(path: Path) -> dict[str, str]:
    if not path.is_file() or path.stat().st_size == 0:
        return {}

    with path.open(newline="", encoding="utf-8-sig") as handle:
        return next(csv.DictReader(handle, delimiter="\t"), {})


def patient_number(case_name: str) -> int | None:
    match = re.match(
        r"^patient_0*(\d+)(?:_|$)",
        case_name,
        re.IGNORECASE,
    )
    return int(match.group(1)) if match else None


def load_expected_cases() -> dict[int, dict[str, str]]:
    expected: dict[int, dict[str, str]] = {}

    with SAMPLE_SHEET.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            sample = row.get("sample_id", "").strip().upper()
            match = re.fullmatch(r"PATIENT_0*(\d+)", sample)

            if not match:
                continue

            number = int(match.group(1))
            expected[number] = row

    return expected


def load_expected_pgx() -> dict[str, int]:
    counts: dict[str, int] = {}

    with PGX_REFERENCE.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("category", "").strip().upper() != "PGX":
                continue

            sample = row.get("sample_id", "").strip().upper()
            counts[sample] = counts.get(sample, 0) + 1

    return counts


def assess_case(case_dir: Path) -> tuple[int, dict[str, object]]:
    case_id = case_dir.name
    final = case_dir / "final"

    run_summary_path = final / f"{case_id}.real_patient_run_summary.tsv"
    run_summary = read_two_column_tsv(run_summary_path)

    ranking_path = final / f"{case_id}.master_candidate_ranking.tsv"
    ranking_top = read_first_tsv_row(ranking_path)

    pipeline_summary_path = final / f"{case_id}.pipeline_summary.tsv"
    pipeline_summary = read_two_column_tsv(pipeline_summary_path)

    completion_path = final / f"{case_id}.case_completion_status.tsv"
    completion = read_two_column_tsv(completion_path)

    repeat_path = final / f"{case_id}.repeat_expansions.detected.tsv"
    repeat_top = read_first_tsv_row(repeat_path)

    repeat_qc_path = final / f"{case_id}.repeat_expansion_qc.tsv"
    repeat_qc = read_two_column_tsv(repeat_qc_path)

    pgx_qc_path = final / f"{case_id}.local_pgx_qc.tsv"
    pgx_qc = read_two_column_tsv(pgx_qc_path)

    annotated_vcfs = list(
        (case_dir / "annotated").glob(
            "*.final.small_variants.annotated.vcf.gz"
        )
    )

    current = (
        run_summary.get("run_status") == "completed"
        and bool(ranking_top)
    )

    routed_repeat = (
        completion.get("completion_status")
        in SUPPORTED_ROUTED_STATUSES
        and bool(repeat_top)
        and int(repeat_qc.get("repeat_expansions_detected", "0")) > 0
    )

    legacy = (
        bool(ranking_top)
        and pipeline_summary_path.is_file()
        and bool(annotated_vcfs)
    )

    if current:
        quality = 4
        mode = "CURRENT"
    elif routed_repeat:
        quality = 3
        mode = "ROUTED_REPEAT"
    elif legacy:
        quality = 2
        mode = "LEGACY"
    elif any(
        (
            run_summary_path.is_file(),
            ranking_path.is_file(),
            completion_path.is_file(),
            repeat_path.is_file(),
            pipeline_summary_path.is_file(),
            bool(annotated_vcfs),
        )
    ):
        quality = 1
        mode = "PARTIAL"
    else:
        quality = 0
        mode = "EMPTY"

    return quality, {
        "case_id": case_id,
        "case_dir": case_dir,
        "mode": mode,
        "run_summary": run_summary,
        "ranking_top": ranking_top,
        "pipeline_summary": pipeline_summary,
        "completion": completion,
        "repeat_top": repeat_top,
        "repeat_qc": repeat_qc,
        "pgx_qc": pgx_qc,
    }


def current_result(info: dict[str, object]) -> tuple[str, str, str, str]:
    run = info["run_summary"]
    assert isinstance(run, dict)

    return (
        str(run.get("top_gene", "")),
        str(run.get("top_disease", "")),
        str(run.get("top_variant", "")),
        str(run.get("top_normalized_score", "")),
    )


def legacy_result(info: dict[str, object]) -> tuple[str, str, str, str]:
    top = info["ranking_top"]
    assert isinstance(top, dict)

    return (
        str(top.get("gene", "")),
        str(top.get("candidate_disease", "")),
        str(top.get("variant", "")),
        str(top.get("normalized_score_100", "")),
    )


def routed_repeat_result(
    info: dict[str, object],
    expected_row: dict[str, str],
) -> tuple[str, str, str, str]:
    repeat = info["repeat_top"]
    assert isinstance(repeat, dict)

    chrom = repeat.get("chromosome", "")
    pos = repeat.get("position", "")
    ref = repeat.get("ref", "")
    alt = repeat.get("alt", "")

    genomic = (
        f"{chrom}:{pos}:{ref}>{alt}"
        if chrom and pos and ref and alt
        else expected_row.get("variant_hgvs_c", "")
    )

    return (
        expected_row.get("gene", ""),
        repeat.get(
            "reported_disease_label",
            expected_row.get("disorder", ""),
        ),
        genomic,
        "routed",
    )


def pgx_status(
    sample: str,
    expected_count: int,
    info: dict[str, object],
) -> tuple[str, str]:
    if expected_count == 0:
        return "N/A", ""

    metrics = info["pgx_qc"]
    assert isinstance(metrics, dict)

    try:
        matched = int(metrics.get("matched_local_pgx_rows", "-1"))
        ambiguous = int(metrics.get("ambiguous_observed_rows", "-1"))
        mismatch = int(metrics.get("genotype_mismatch_rows", "-1"))
    except ValueError:
        return "FAIL", "non-numeric PGx QC metrics"

    if (
        matched == expected_count
        and ambiguous == 0
        and mismatch == 0
    ):
        return "PASS", ""

    return (
        "FAIL",
        (
            f"PGx expected={expected_count}, matched={matched}, "
            f"ambiguous={ambiguous}, mismatch={mismatch}"
        ),
    )


def main() -> None:
    expected_cases = load_expected_cases()
    expected_pgx = load_expected_pgx()

    all_dirs = [
        path
        for path in RESULTS_ROOT.iterdir()
        if path.is_dir()
    ]

    output_rows: list[dict[str, str]] = []
    failures: list[str] = []

    print("=== FINAL PATIENTS 01-12 AUDIT ===")

    for number in range(1, 13):
        sample = f"PATIENT_{number:02d}"
        expected = expected_cases.get(number, {})
        expected_gene = expected.get("gene", "").strip().upper()

        matching_dirs = [
            path
            for path in all_dirs
            if patient_number(path.name) == number
        ]

        assessed = [
            assess_case(path)
            for path in matching_dirs
        ]
        assessed.sort(
            key=lambda item: (
                item[0],
                str(item[1]["case_id"]),
            ),
            reverse=True,
        )

        if not assessed or assessed[0][0] == 0:
            output_rows.append({
                "patient": sample,
                "mode": "MISSING",
                "gene": "",
                "variant": "",
                "score": "",
                "pgx": "N/A",
                "status": "FAIL",
            })
            failures.append(f"{sample}: no reusable output")
            continue

        quality, selected = assessed[0]
        mode = str(selected["mode"])

        if mode == "CURRENT":
            gene, disease, variant, score = current_result(selected)
        elif mode == "ROUTED_REPEAT":
            gene, disease, variant, score = routed_repeat_result(
                selected,
                expected,
            )
        elif mode == "LEGACY":
            gene, disease, variant, score = legacy_result(selected)
        else:
            gene = disease = variant = score = ""

        status = "PASS"
        notes: list[str] = []

        if mode == "PARTIAL":
            status = "FAIL"
            notes.append("selected output is partial")

        if not gene or not variant:
            status = "FAIL"
            notes.append("missing result gene or variant")

        if expected_gene and gene.strip().upper() != expected_gene:
            status = "FAIL"
            notes.append(
                f"top gene {gene or 'missing'} != expected {expected_gene}"
            )

        pgx, pgx_note = pgx_status(
            sample,
            expected_pgx.get(sample, 0),
            selected,
        )
        if pgx == "FAIL":
            status = "FAIL"
            notes.append(pgx_note)

        if mode == "ROUTED_REPEAT":
            repeat = selected["repeat_top"]
            assert isinstance(repeat, dict)

            if (
                repeat.get("ranking_status")
                != "excluded_from_universal_ranking"
            ):
                status = "FAIL"
                notes.append(
                    "repeat expansion was not excluded from ordinary ranking"
                )

        output_rows.append({
            "patient": sample,
            "mode": mode,
            "gene": gene,
            "variant": variant,
            "score": score,
            "pgx": pgx,
            "status": status,
        })

        if status == "FAIL":
            failures.append(
                f"{sample}: " + "; ".join(notes)
            )

        stale = [
            str(info["case_id"])
            for other_quality, info in assessed[1:]
            if other_quality < quality
        ]
        if stale:
            print(
                f"{sample}: canonical={selected['case_id']}; "
                f"ignored stale={','.join(stale)}"
            )

    columns = [
        "patient",
        "mode",
        "gene",
        "variant",
        "score",
        "pgx",
        "status",
    ]

    widths = {
        column: max(
            len(column),
            *[len(row[column]) for row in output_rows],
        )
        for column in columns
    }

    print()
    print(
        "  ".join(
            column.ljust(widths[column])
            for column in columns
        )
    )

    for row in output_rows:
        print(
            "  ".join(
                row[column].ljust(widths[column])
                for column in columns
            )
        )

    print()
    print("Patients audited:", len(output_rows))
    print("Failures:", len(failures))

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        sys.exit(1)

    print(
        "PASS: Patients 01-12 have valid canonical outcomes."
    )
    print(
        "PASS: Repeat expansions are accepted only when detected, "
        "reported and excluded from ordinary ranking."
    )
    print("NOTE: Patient 13 was intentionally skipped.")


if __name__ == "__main__":
    main()

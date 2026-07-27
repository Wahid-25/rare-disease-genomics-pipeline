#!/usr/bin/env python3
"""Regression tests for production/validation G2P resource isolation."""

from __future__ import annotations

from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")
    print(f"PASS: {message}")


def main() -> None:
    project = Path(__file__).resolve().parents[2]

    phenotype = (
        project / "pipeline" / "case_workflow" / "10_add_phenotype_scores.py"
    ).read_text(encoding="utf-8")
    cnv = (
        project / "pipeline" / "case_workflow" / "12_score_cnv_candidates.py"
    ).read_text(encoding="utf-8")
    runner = (project / "pipeline" / "run_case_pipeline.sh").read_text(
        encoding="utf-8"
    )
    downloader = (
        project / "pipeline" / "setup_resources" / "01_download_g2p.sh"
    ).read_text(encoding="utf-8")
    final_suite = (
        project / "pipeline" / "tests" / "01_run_final_validation_suite.sh"
    ).read_text(encoding="utf-8")

    require(
        "AllG2P.latest.csv" not in phenotype
        and "AllG2P.official.csv" in phenotype,
        "phenotype scoring defaults independently to official G2P",
    )
    require(
        "AllG2P.latest.csv" not in cnv
        and "AllG2P.official.csv" in cnv,
        "CNV scoring defaults independently to official G2P",
    )
    require(
        "g2p_resource_sha256" in phenotype
        and "g2p_resource" in phenotype,
        "phenotype QC records G2P path and checksum",
    )
    require(
        "g2p_resource_sha256" in cnv
        and "g2p_resource" in cnv,
        "CNV QC records G2P path and checksum",
    )

    resource_position = runner.find(
        "# Resolve G2P resource once for every active branch"
    )
    routing_position = runner.find("# Automatic routing")
    require(
        resource_position >= 0
        and routing_position >= 0
        and resource_position < routing_position,
        "runner resolves one G2P resource before branch routing",
    )

    phenotype_call = """pipeline/case_workflow/10_add_phenotype_scores.py \\
        \"$CASE_ID\" \\
        \"$STAGED_PHENOTYPES\" \\
        \"$G2P_RESOURCE\""""
    require(
        phenotype_call in runner,
        "runner passes selected G2P resource to phenotype scoring",
    )

    cnv_call = """pipeline/case_workflow/12_score_cnv_candidates.py \\
        \"$CASE_ID\" \\
        \"$G2P_RESOURCE\""""
    require(
        cnv_call in runner,
        "runner passes selected G2P resource to CNV scoring",
    )

    require(
        "OFFICIAL_FILE=" in downloader
        and "AllG2P.official.csv" in downloader
        and "versioned_official_file" in downloader
        and 'mv -f "$OFFICIAL_TEMP" "$OFFICIAL_FILE"' in downloader,
        "downloader atomically refreshes the official production resource",
    )
    require(
        "AllG2P.latest.csv" in downloader
        and "compatibility_latest_file" in downloader,
        "downloader retains latest only as a compatibility copy",
    )
    require(
        "AllG2P.official.csv" in final_suite
        and "resource_g2p_official" in final_suite,
        "final validation suite checks official production G2P",
    )
    require(
        "AllG2P.latest.csv" not in final_suite,
        "final validation suite no longer treats legacy latest as production",
    )

    print()
    print("PASS: G2P resource-isolation regression tests completed.")


if __name__ == "__main__":
    main()

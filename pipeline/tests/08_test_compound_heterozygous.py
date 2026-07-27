#!/usr/bin/env python3
"""Regression tests for phase preservation and compound-heterozygous logic."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def require(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(
    variant: str,
    genotype: str,
    zygosity: str,
    *,
    ps: str = "",
    pid: str = "",
    pgt: str = "",
    inheritance: str = "biallelic_autosomal",
) -> dict[str, str]:
    return {
        "rank": "1",
        "case_id": "synthetic_case",
        "sample": "SAMPLE",
        "variant": variant,
        "gene": "GENE1",
        "candidate_disease": "Synthetic recessive disorder",
        "disease_mim": "000001",
        "inheritance": inheritance,
        "genotype": genotype,
        "zygosity": zygosity,
        "inheritance_points": (
            "3" if zygosity == "homozygous_alt" else "0"
        ),
        "clinvar_points": "4",
        "final_score": "12",
        "priority": "moderate_priority_candidate",
        "inheritance_match": "",
        "phase_set_PS": ps,
        "phase_id_PID": pid,
        "phased_genotype_PGT": pgt,
        "genotype_is_phased": (
            "yes" if "|" in genotype else "no"
        ),
    }


def run_case(module, rows):
    phase_rows = [dict(item) for item in rows]
    result, metrics = module.apply_compound_evidence(
        [dict(item) for item in rows],
        phase_rows,
    )
    by_variant = {
        item["variant"]: item
        for item in result
    }
    return by_variant, metrics


def main() -> None:
    project = Path(__file__).resolve().parents[2]
    workflow = project / "pipeline" / "case_workflow"

    import sys
    sys.path.insert(0, str(workflow))

    compound = load_module(
        workflow
        / "10b_add_compound_heterozygous_evidence.py",
        "compound_evidence",
    )

    first = row(
        "1:100:A>G",
        "0|1",
        "heterozygous",
        ps="1000",
    )
    second = row(
        "1:200:C>T",
        "1|0",
        "heterozygous",
        ps="1000",
    )
    rows, metrics = run_case(compound, [first, second])
    require(
        rows["1:100:A>G"]["gene_level_inheritance_status"]
        == "confirmed_trans",
        "opposite haplotypes in one PS block are confirmed trans",
    )
    require(
        rows["1:100:A>G"]["compound_score_adjustment"] == "3",
        "confirmed trans receives full inheritance credit",
    )
    require(
        metrics.get("confirmed_trans") == 2,
        "both variants in a confirmed trans pair are annotated",
    )

    first = row(
        "1:100:A>G",
        "0|1",
        "heterozygous",
        ps="1000",
    )
    second = row(
        "1:200:C>T",
        "0|1",
        "heterozygous",
        ps="1000",
    )
    rows, _metrics = run_case(compound, [first, second])
    require(
        rows["1:100:A>G"]["gene_level_inheritance_status"]
        == "likely_cis",
        "same haplotype in one PS block is likely cis",
    )
    require(
        rows["1:100:A>G"]["compound_score_adjustment"] == "0",
        "likely cis receives no biallelic credit",
    )

    first = row("1:100:A>G", "0/1", "heterozygous")
    second = row("1:200:C>T", "0/1", "heterozygous")
    rows, _metrics = run_case(compound, [first, second])
    require(
        rows["1:100:A>G"]["gene_level_inheritance_status"]
        == "possible_compound_heterozygous",
        "unphased heterozygous pair remains possible only",
    )
    require(
        rows["1:100:A>G"]["compound_score_adjustment"] == "1",
        "unphased pair receives limited supporting credit",
    )

    rows, _metrics = run_case(
        compound,
        [row("1:100:A>G", "0/1", "heterozygous")],
    )
    require(
        rows["1:100:A>G"]["gene_level_inheritance_status"]
        == "single_recessive_allele",
        "one heterozygous variant is a single recessive allele",
    )

    homozygous = row(
        "1:300:G>A",
        "1/1",
        "homozygous_alt",
    )
    rows, _metrics = run_case(compound, [homozygous])
    require(
        rows["1:300:G>A"]["gene_level_inheritance_status"]
        == "homozygous_biallelic",
        "homozygous alternate call is biallelic",
    )
    require(
        rows["1:300:G>A"]["compound_score_adjustment"] == "0",
        "existing homozygous inheritance credit is not double counted",
    )

    dominant = row(
        "1:400:T>C",
        "0/1",
        "heterozygous",
        inheritance="monoallelic_autosomal",
    )
    rows, _metrics = run_case(compound, [dominant])
    require(
        rows["1:400:T>C"]["gene_level_inheritance_status"]
        == "not_applicable_non_recessive",
        "dominant models are excluded from compound aggregation",
    )

    extractor = (
        workflow / "03_extract_vep_table.py"
    ).read_text(encoding="utf-8")
    require(
        all(
            field in extractor
            for field in (
                "phase_set_PS",
                "phase_id_PID",
                "phased_genotype_PGT",
                "genotype_is_phased",
            )
        ),
        "VEP extraction preserves phase fields",
    )
    require(
        extractor.count("writer.writerows(output_rows)") == 1,
        "VEP extraction writes candidate rows exactly once",
    )

    runner = (
        project / "pipeline" / "run_case_pipeline.sh"
    ).read_text(encoding="utf-8")
    require(
        "10b_add_compound_heterozygous_evidence.py"
        in runner,
        "case runner invokes compound aggregation",
    )

    master = (
        workflow / "14_build_master_candidate_table.py"
    ).read_text(encoding="utf-8")
    require(
        all(
            field in master
            for field in (
                "gene_level_inheritance_status",
                "compound_partner_variants",
                "compound_phase_evidence",
                "compound_score_adjustment",
            )
        ),
        "master ranking propagates compound evidence",
    )

    print()
    print(
        "PASS: Compound-heterozygous regression tests completed."
    )


if __name__ == "__main__":
    main()

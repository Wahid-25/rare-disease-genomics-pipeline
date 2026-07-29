#!/usr/bin/env python3
"""Regression test for 22_build_clinical_report_json.py."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(rows[0]) if rows else ["field", "value"]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "case_workflow"
        / "22_build_clinical_report_json.py"
    )

    with tempfile.TemporaryDirectory() as temporary:
        project = Path(temporary)
        case_id = "case_json_test"
        result = project / "results" / "cases" / case_id
        final = result / "final"
        annotated = result / "annotated"
        clinpgx = result / "clinpgx"
        staged = (
            project
            / "input"
            / "cases"
            / case_id
            / "staged"
        )

        write_tsv(
            final / f"{case_id}.master_candidate_ranking.tsv",
            [
                {
                    "overall_rank": "1",
                    "candidate_type": "small_variant",
                    "case_id": case_id,
                    "variant": "chr1:100:A>G",
                    "vcf_id": "rs1",
                    "gene": "GENE1",
                    "candidate_disease": "Example disease",
                    "inheritance": "monoallelic_autosomal",
                    "genotype": "0/1",
                    "zygosity": "heterozygous",
                    "clinvar_significance": "Pathogenic",
                    "clinvar_review_status": "criteria provided",
                    "normalized_score_100": "80.00",
                    "priority": "high_priority_candidate",
                    "evidence_summary": "ClinVar=Pathogenic; HPO_matches=2",
                    "interpretation_note": "Analyst review required.",
                    "compound_partner_variants": "",
                },
                {
                    "overall_rank": "2",
                    "candidate_type": "small_variant",
                    "case_id": case_id,
                    "variant": "chr2:200:C>T",
                    "vcf_id": "rs2",
                    "gene": "GENE2",
                    "candidate_disease": "Example disease",
                    "inheritance": "monoallelic_autosomal",
                    "genotype": "0/1",
                    "zygosity": "heterozygous",
                    "clinvar_significance": "Likely pathogenic",
                    "clinvar_review_status": "criteria provided",
                    "normalized_score_100": "70.00",
                    "priority": "high_priority_candidate",
                    "evidence_summary": "ClinVar=Likely pathogenic; HPO_matches=2",
                    "interpretation_note": "Alternative gene candidate.",
                    "compound_partner_variants": "",
                },
            ],
        )

        write_tsv(
            annotated / f"{case_id}.vep_best_transcripts.tsv",
            [
                {
                    "variant": "chr1:100:A>G",
                    "transcript": "ENST000001",
                    "hgvsc": "ENST000001:c.1A>G",
                    "hgvsp": "ENSP000001:p.Lys1Arg",
                },
                {
                    "variant": "chr2:200:C>T",
                    "transcript": "ENST000002",
                    "hgvsc": "ENST000002:c.2C>T",
                    "hgvsp": "ENSP000002:p.Ala2Val",
                },
            ],
        )

        write_tsv(
            final / f"{case_id}.pipeline_summary.tsv",
            [
                {"field": "case_id", "value": case_id},
                {"field": "assembly", "value": "GRCh38"},
            ],
        )

        write_tsv(
            final / f"{case_id}.resource_mode.tsv",
            [
                {"metric": "pipeline_mode", "value": "validation"},
            ],
        )

        staged.mkdir(parents=True, exist_ok=True)
        (
            staged / f"{case_id}.pipeline_phenotypes.txt"
        ).write_text(
            "HP:0001250\nHP:0001263\n",
            encoding="utf-8",
        )

        write_tsv(
            clinpgx / f"{case_id}.local_pgx_matches.tsv",
            [
                {
                    "case_id": case_id,
                    "variant": "chr1:100:A>G",
                    "vcf_id": "rs1",
                    "genotype": "0/1",
                    "zygosity": "heterozygous",
                    "gene": "GENE1",
                    "local_pgx_gene": "GENE1",
                    "local_pgx_rsid": "rs1",
                    "local_pgx_observed_genotype_class": "heterozygous",
                    "local_pgx_phenotype": "intermediate function",
                    "local_pgx_affected_drugs": "ExampleDrug",
                    "local_pgx_cpic_level": "A",
                    "local_pgx_status": "local_reference_match",
                    "local_pgx_match_method": "rsid_and_allele",
                    "local_pgx_allele_match": "yes",
                    "local_pgx_genotype_match": "yes",
                },
            ],
        )

        output = (
            final
            / "report"
            / f"{case_id}.report_draft.json"
        )

        command = [
            sys.executable,
            str(script),
            case_id,
            "--project-root",
            str(project),
            "--output",
            str(output),
        ]

        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )

        data = json.loads(output.read_text(encoding="utf-8"))

        assert data["schema_version"] == "1.0"
        assert data["report_status"] == "draft"
        assert data["patient"]["case_id"] == case_id
        assert data["test"]["genome_build"] == "GRCh38"
        assert len(data["findings"]) == 2
        assert {item["gene"] for item in data["findings"]} == {
            "GENE1",
            "GENE2",
        }
        assert (
            data["findings"][0]["hgvs"]["coding"]
            == "ENST000001:c.1A>G"
        )
        assert "ExampleDrug" in (
            data["findings"][0]["clinpgx"]["summary"]
        )
        assert output.with_suffix(".json.sha256").is_file()

        print(completed.stdout)
        print("PASS: clinical report JSON regression test")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import csv
import json
import os
import re
import shutil
import sys
from pathlib import Path

FIELDS = [
    "clinpgx_status",
    "clinpgx_gene_match",
    "clinpgx_gene_ids",
    "clinpgx_gene_names",
    "clinpgx_evidence_scope",
    "clinpgx_cnv_interpretation_status",
    "clinpgx_drug_guidance_available",
    "clinpgx_note",
]


def genes_from(row):
    value = row.get("gene", "") or row.get("genes", "")
    genes = []
    for token in re.split(r"[;,|&/]+", value.upper()):
        token = token.strip()
        if token and token not in genes and re.fullmatch(r"[A-Z0-9._-]+", token):
            genes.append(token)
    return genes


def cache_result(path, gene):
    if not path.is_file() or path.stat().st_size == 0:
        return "cache_miss_not_queried", "", gene
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "invalid_cache", "", gene
    data = payload.get("data", []) if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        return "cached_no_match", "", gene
    record = data[0] if isinstance(data[0], dict) else {}
    identifier = str(
        record.get("id")
        or record.get("geneId")
        or record.get("clinpgxId")
        or ""
    )
    name = str(
        record.get("symbol")
        or record.get("geneSymbol")
        or record.get("name")
        or gene
    )
    return "matched", identifier, name


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: 11c_add_cnv_clinpgx.py CASE_ID")

    case = sys.argv[1]
    root = Path(__file__).resolve().parents[2]
    final = root / "results" / "cases" / case / "final"
    source = final / f"{case}.universal_cnv_scores.tsv"
    outdir = root / "results" / "cases" / case / "clinpgx"
    output = outdir / f"{case}.cnv_clinpgx_matches.tsv"
    qc = final / f"{case}.cnv_clinpgx_qc.tsv"
    cache = root / "resources" / "clinpgx" / "cache" / "genes"

    if not source.is_file():
        raise SystemExit(f"ERROR: Missing {source}")

    outdir.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)

    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        columns = list(reader.fieldnames or [])
        rows = list(reader)

    columns += [field for field in FIELDS if field not in columns]
    matched_rows = 0
    enriched = []

    for row in rows:
        genes = genes_from(row)
        results = [cache_result(cache / f"{gene}.json", gene) for gene in genes]
        matches = [item for item in results if item[0] == "matched"]

        if matches:
            matched_rows += 1
            annotation = {
                "clinpgx_status": "matched",
                "clinpgx_gene_match": "yes",
                "clinpgx_gene_ids": ";".join(sorted({x[1] for x in matches if x[1]})),
                "clinpgx_gene_names": ";".join(sorted({x[2] for x in matches if x[2]})),
                "clinpgx_evidence_scope": "gene_level_only",
                "clinpgx_cnv_interpretation_status": "requires_specialized_pgx_cnv_interpretation",
                "clinpgx_drug_guidance_available": "not_assessed",
                "clinpgx_note": "CNV overlaps a cached ClinPGx pharmacogene; no metabolizer phenotype or drug recommendation was inferred.",
            }
        elif any(x[0] in {"cache_miss_not_queried", "invalid_cache"} for x in results):
            annotation = {
                "clinpgx_status": "cache_miss_not_queried",
                "clinpgx_gene_match": "not_available",
                "clinpgx_gene_ids": "",
                "clinpgx_gene_names": "",
                "clinpgx_evidence_scope": "not_available",
                "clinpgx_cnv_interpretation_status": "not_evaluable",
                "clinpgx_drug_guidance_available": "not_assessed",
                "clinpgx_note": "ClinPGx gene evidence was unavailable in the local cache; this is not a negative result.",
            }
        else:
            annotation = {
                "clinpgx_status": "cached_no_match" if genes else "not_applicable",
                "clinpgx_gene_match": "no",
                "clinpgx_gene_ids": "",
                "clinpgx_gene_names": "",
                "clinpgx_evidence_scope": "gene_level_only" if genes else "not_applicable",
                "clinpgx_cnv_interpretation_status": "not_applicable",
                "clinpgx_drug_guidance_available": "not_assessed",
                "clinpgx_note": "No cached ClinPGx gene match." if genes else "No CNV gene was available for matching.",
            }

        row.update(annotation)
        enriched.append(row)

    tmp = source.with_suffix(".tmp")
    for path in (tmp, output):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
            writer.writeheader()
            writer.writerows(enriched)

    backup = final / f"{case}.universal_cnv_scores.pre_clinpgx.tsv"
    if not backup.exists():
        shutil.copy2(source, backup)
    os.replace(tmp, source)

    with qc.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerows([
            ["metric", "value"],
            ["case_id", case],
            ["mode", "cache_only_gene_level"],
            ["cnv_rows", len(rows)],
            ["matched_rows", matched_rows],
            ["ranking_score_modified", "no"],
            ["phenotype_or_drug_guidance_inferred", "no"],
            ["output_table", output.relative_to(root)],
        ])

    print("CNV CLINPGX CONTEXT COMPLETED")
    print(f"Rows: {len(rows)} | matched: {matched_rows}")
    print(output)
    print(qc)


if __name__ == "__main__":
    main()

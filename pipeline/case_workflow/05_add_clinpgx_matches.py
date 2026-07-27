#!/usr/bin/env python3

import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://api.clinpgx.org/v1"
REQUEST_DELAY_SECONDS = 0.6

# cache_only:
#   use existing local responses but make no network requests.
#
# api:
#   allow new ClinPGx API requests.
#
# Cache-only is the reproducible and fast default.
CLINPGX_MODE = os.environ.get(
    "CLINPGX_MODE",
    "cache_only",
).strip().lower()

if CLINPGX_MODE not in {"cache_only", "api"}:
    raise SystemExit(
        "ERROR: CLINPGX_MODE must be cache_only or api."
    )


def clean(value: str) -> str:
    """Return a safely stripped string."""
    return value.strip() if value else ""


def safe_filename(value: str) -> str:
    """Convert a query value into a safe filename."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def extract_rsids(*values: str) -> list[str]:
    """Extract unique rs identifiers from one or more fields."""
    found = []

    for value in values:
        for rsid in re.findall(r"\brs\d+\b", value or "", flags=re.I):
            rsid = rsid.lower()

            if rsid not in found:
                found.append(rsid)

    return found


def request_json(url: str) -> dict:
    """Retrieve one JSON response from ClinPGx."""

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "rare-disease-case-pipeline/1.0",
        },
    )

    with urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8")
        return json.loads(text)


def records_from_payload(payload: dict) -> list[dict]:
    """Return the records stored in a ClinPGx response."""

    data = payload.get("data", [])

    if isinstance(data, list):
        return [
            record
            for record in data
            if isinstance(record, dict)
        ]

    if isinstance(data, dict):
        return [data]

    return []


def query_with_cache(
    endpoint: str,
    parameters: dict[str, str],
    cache_file: Path,
) -> tuple[list[dict], str, str]:
    """
    Query ClinPGx or reuse an existing cache.

    Returns:
        records
        source: cache or api
        error message
    """

    if cache_file.is_file() and cache_file.stat().st_size > 0:
        try:
            payload = json.loads(
                cache_file.read_text(encoding="utf-8")
            )
            return records_from_payload(payload), "cache", ""

        except (json.JSONDecodeError, OSError):
            # Invalid cache will be replaced with a new API result.
            pass

    if CLINPGX_MODE != "api":
        return [], "cache_miss_not_queried", ""

    url = BASE_URL + endpoint + "?" + urlencode(parameters)

    try:
        payload = request_json(url)

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        time.sleep(REQUEST_DELAY_SECONDS)

        return records_from_payload(payload), "api", ""

    except HTTPError as error:
        # ClinPGx returns HTTP 404 when the queried object is absent.
        # This is a normal no-match result, not a pipeline failure.
        if error.code == 404:
            return [], "api_no_match", ""

        message = f"HTTP {error.code}: {error.reason}"
        return [], "api_error", message

    except URLError as error:
        message = f"Connection error: {error.reason}"
        return [], "api_error", message

    except json.JSONDecodeError as error:
        message = f"Invalid JSON: {error}"
        return [], "api_error", message

    except Exception as error:
        message = f"Unexpected error: {error}"
        return [], "api_error", message


def summarize_record(
    records: list[dict],
    expected_value: str,
    record_type: str,
) -> tuple[str, str, str]:
    """
    Extract the best record ID, label and match status.

    record_type must be 'gene' or 'variant'.
    """

    if not records:
        return "no", "", ""

    expected_upper = expected_value.upper()

    preferred = None

    for record in records:
        if record_type == "gene":
            record_value = clean(record.get("symbol", "")).upper()
        else:
            record_value = clean(record.get("name", "")).upper()

        if record_value == expected_upper:
            preferred = record
            break

    if preferred is None:
        preferred = records[0]

    record_id = clean(preferred.get("id", ""))

    if record_type == "gene":
        record_label = (
            clean(preferred.get("name", ""))
            or clean(preferred.get("symbol", ""))
        )
    else:
        record_label = (
            clean(preferred.get("name", ""))
            or clean(preferred.get("symbol", ""))
        )

    return "yes", record_id, record_label


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/"
            "05_add_clinpgx_matches.py CASE_ID"
        )
        sys.exit(1)

    case_id = sys.argv[1]

    script_path = Path(__file__).resolve()
    project_root = script_path.parents[2]

    input_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "annotated"
        / f"{case_id}.vep_best_transcripts.tsv"
    )

    output_dir = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "clinpgx"
    )

    output_table = (
        output_dir
        / f"{case_id}.clinpgx_matches.tsv"
    )

    qc_file = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.clinpgx_qc.tsv"
    )

    gene_cache_dir = (
        project_root
        / "resources"
        / "clinpgx"
        / "cache"
        / "genes"
    )

    variant_cache_dir = (
        project_root
        / "resources"
        / "clinpgx"
        / "cache"
        / "variants"
    )

    if not input_table.is_file():
        print(f"ERROR: VEP table was not found: {input_table}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    qc_file.parent.mkdir(parents=True, exist_ok=True)
    gene_cache_dir.mkdir(parents=True, exist_ok=True)
    variant_cache_dir.mkdir(parents=True, exist_ok=True)

    input_rows = []

    with input_table.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        input_rows = list(reader)

    gene_results: dict[str, dict[str, str]] = {}
    variant_results: dict[str, dict[str, str]] = {}

    unique_genes = sorted(
        {
            clean(row.get("gene", "")).upper()
            for row in input_rows
            if clean(row.get("gene", ""))
        }
    )

    unique_rsids = sorted(
        {
            rsid
            for row in input_rows
            for rsid in extract_rsids(
                clean(row.get("vcf_id", "")),
                clean(row.get("existing_variation", "")),
            )
        }
    )

    print("========================================")
    print("CLINPGX CASE MATCHING")
    print("========================================")
    print(f"Case ID:          {case_id}")
    print(f"ClinPGx mode:     {CLINPGX_MODE}")
    print(f"Variant rows:     {len(input_rows)}")
    print(f"Unique genes:     {len(unique_genes)}")
    print(f"Unique rsIDs:     {len(unique_rsids)}")
    print()

    print("[1/3] Querying ClinPGx genes")

    for index, gene in enumerate(unique_genes, start=1):
        cache_file = (
            gene_cache_dir
            / f"{safe_filename(gene)}.json"
        )

        records, source, error = query_with_cache(
            endpoint="/data/gene",
            parameters={
                "symbol": gene,
                "view": "base",
            },
            cache_file=cache_file,
        )

        matched, clinpgx_id, label = summarize_record(
            records,
            gene,
            "gene",
        )

        gene_results[gene] = {
            "matched": matched,
            "id": clinpgx_id,
            "label": label,
            "source": source,
            "error": error,
        }

        print(
            f"  [{index}/{len(unique_genes)}] "
            f"{gene}: {matched}"
        )

    print()
    print("[2/3] Querying ClinPGx variants")

    for index, rsid in enumerate(unique_rsids, start=1):
        cache_file = (
            variant_cache_dir
            / f"{safe_filename(rsid)}.json"
        )

        records, source, error = query_with_cache(
            endpoint="/data/variant",
            parameters={
                "name": rsid,
                "view": "base",
            },
            cache_file=cache_file,
        )

        matched, clinpgx_id, label = summarize_record(
            records,
            rsid,
            "variant",
        )

        variant_results[rsid] = {
            "matched": matched,
            "id": clinpgx_id,
            "label": label,
            "source": source,
            "error": error,
        }

        print(
            f"  [{index}/{len(unique_rsids)}] "
            f"{rsid}: {matched}"
        )

    print()
    print("[3/3] Creating case ClinPGx table")

    output_columns = [
        "case_id",
        "sample",
        "variant",
        "vcf_id",
        "genotype",
        "zygosity",
        "gene",
        "consequence",
        "clinpgx_variant_query",
        "clinpgx_variant_match",
        "clinpgx_variant_id",
        "clinpgx_variant_name",
        "clinpgx_variant_source",
        "clinpgx_gene_query",
        "clinpgx_gene_match",
        "clinpgx_gene_id",
        "clinpgx_gene_name",
        "clinpgx_gene_source",
        "clinpgx_status",
        "clinpgx_error",
    ]

    output_rows = []
    variant_match_rows = 0
    gene_match_rows = 0
    rows_with_errors = 0

    for row in input_rows:
        gene = clean(row.get("gene", "")).upper()

        rsids = extract_rsids(
            clean(row.get("vcf_id", "")),
            clean(row.get("existing_variation", "")),
        )

        rsid = rsids[0] if rsids else ""

        gene_result = gene_results.get(
            gene,
            {
                "matched": "no",
                "id": "",
                "label": "",
                "source": "not_queried",
                "error": "",
            },
        )

        variant_result = variant_results.get(
            rsid,
            {
                "matched": "no",
                "id": "",
                "label": "",
                "source": "not_queried",
                "error": "",
            },
        )

        errors = [
            message
            for message in [
                variant_result["error"],
                gene_result["error"],
            ]
            if message
        ]

        if variant_result["matched"] == "yes":
            variant_match_rows += 1

        if gene_result["matched"] == "yes":
            gene_match_rows += 1

        if errors:
            status = "api_error"
            rows_with_errors += 1
        elif variant_result["matched"] == "yes":
            status = "exact_variant_match"
        elif gene_result["matched"] == "yes":
            # A gene object only confirms that the gene exists in
            # ClinPGx. It does not prove a gene-drug association.
            status = "gene_reference_only"
        else:
            status = "no_clinpgx_match"

        output_rows.append(
            {
                "case_id": case_id,
                "sample": clean(row.get("sample", "")),
                "variant": clean(row.get("variant", "")),
                "vcf_id": clean(row.get("vcf_id", "")),
                "genotype": clean(row.get("genotype", "")),
                "zygosity": clean(row.get("zygosity", "")),
                "gene": gene,
                "consequence": clean(
                    row.get("consequence", "")
                ),
                "clinpgx_variant_query": rsid,
                "clinpgx_variant_match": (
                    variant_result["matched"]
                ),
                "clinpgx_variant_id": variant_result["id"],
                "clinpgx_variant_name": (
                    variant_result["label"]
                ),
                "clinpgx_variant_source": (
                    variant_result["source"]
                ),
                "clinpgx_gene_query": gene,
                "clinpgx_gene_match": gene_result["matched"],
                "clinpgx_gene_id": gene_result["id"],
                "clinpgx_gene_name": gene_result["label"],
                "clinpgx_gene_source": gene_result["source"],
                "clinpgx_status": status,
                "clinpgx_error": "; ".join(errors),
            }
        )

    with output_table.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=output_columns,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(output_rows)

    matched_unique_variants = sum(
        1
        for result in variant_results.values()
        if result["matched"] == "yes"
    )

    matched_unique_genes = sum(
        1
        for result in gene_results.values()
        if result["matched"] == "yes"
    )

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(["input_rows", len(input_rows)])
        writer.writerow(["queried_unique_genes", len(unique_genes)])
        writer.writerow(["queried_unique_rsids", len(unique_rsids)])
        writer.writerow(
            ["matched_unique_genes", matched_unique_genes]
        )
        writer.writerow(
            ["matched_unique_variants", matched_unique_variants]
        )
        writer.writerow(
            ["rows_with_variant_match", variant_match_rows]
        )
        writer.writerow(
            ["rows_with_gene_match", gene_match_rows]
        )
        writer.writerow(["rows_with_errors", rows_with_errors])
        writer.writerow(
            [
                "output_table",
                str(output_table.relative_to(project_root)),
            ]
        )

    print()
    print("ClinPGx summary")
    print("----------------")
    print(f"Matched genes:     {matched_unique_genes}")
    print(f"Matched variants:  {matched_unique_variants}")
    print(f"Rows with errors:  {rows_with_errors}")
    print()
    print(f"Output: {output_table}")
    print(f"QC:     {qc_file}")
    print()
    print("CLINPGX CASE MATCHING COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()

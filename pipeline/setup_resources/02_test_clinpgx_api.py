#!/usr/bin/env python3

import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://api.clinpgx.org/v1"

# Known pharmacogenomic controls used only to test the API.
TEST_QUERIES = [
    {
        "name": "gene_CYP2C19",
        "endpoint": "/data/gene",
        "parameters": {
            "symbol": "CYP2C19",
            "view": "base",
        },
    },
    {
        "name": "variant_rs4244285",
        "endpoint": "/data/variant",
        "parameters": {
            "name": "rs4244285",
            "view": "base",
        },
    },
]


def request_json(url: str) -> dict:
    """Retrieve and decode one JSON response."""

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


def count_records(payload: dict) -> int:
    """Count returned data objects safely."""

    data = payload.get("data")

    if isinstance(data, list):
        return len(data)

    if isinstance(data, dict):
        return 1

    return 0


def main() -> None:
    script_path = Path(__file__).resolve()
    project_root = script_path.parents[2]

    cache_dir = (
        project_root
        / "resources"
        / "clinpgx"
        / "cache"
        / "setup_test"
    )

    metadata_dir = (
        project_root
        / "resources"
        / "clinpgx"
        / "metadata"
    )

    cache_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    metadata_file = metadata_dir / "clinpgx_api_test.tsv"

    results = []
    overall_success = True

    print("========================================")
    print("CLINPGX API CONNECTION TEST")
    print("========================================")
    print(f"API base: {BASE_URL}")
    print()

    for index, query in enumerate(TEST_QUERIES, start=1):
        url = (
            BASE_URL
            + query["endpoint"]
            + "?"
            + urlencode(query["parameters"])
        )

        output_file = cache_dir / f"{query['name']}.json"

        print(
            f"[{index}/{len(TEST_QUERIES)}] "
            f"Testing {query['name']}"
        )

        status = "failed"
        record_count = 0
        error_message = ""

        try:
            payload = request_json(url)

            with output_file.open(
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(
                    payload,
                    handle,
                    indent=2,
                    ensure_ascii=False,
                )

            api_status = str(payload.get("status", "")).lower()
            record_count = count_records(payload)

            if api_status == "success" and record_count > 0:
                status = "success"
            elif record_count > 0:
                status = "success"
            else:
                status = "no_records"
                overall_success = False

        except HTTPError as error:
            error_message = (
                f"HTTP {error.code}: {error.reason}"
            )
            overall_success = False

        except URLError as error:
            error_message = f"Connection error: {error.reason}"
            overall_success = False

        except json.JSONDecodeError as error:
            error_message = f"Invalid JSON: {error}"
            overall_success = False

        except Exception as error:
            error_message = f"Unexpected error: {error}"
            overall_success = False

        results.append(
            {
                "test": query["name"],
                "endpoint": query["endpoint"],
                "status": status,
                "records": record_count,
                "cache_file": str(
                    output_file.relative_to(project_root)
                ),
                "error": error_message,
            }
        )

        print(f"Status:  {status}")
        print(f"Records: {record_count}")

        if error_message:
            print(f"Error:   {error_message}")

        print()

        # ClinPGx asks clients to remain below two requests/second.
        if index < len(TEST_QUERIES):
            time.sleep(0.6)

    accessed_at = datetime.now(timezone.utc).isoformat()

    with metadata_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        columns = [
            "test",
            "endpoint",
            "status",
            "records",
            "cache_file",
            "error",
            "accessed_at_utc",
            "api_base",
        ]

        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
        )

        writer.writeheader()

        for row in results:
            row["accessed_at_utc"] = accessed_at
            row["api_base"] = BASE_URL
            writer.writerow(row)

    print("Metadata:")
    print(metadata_file)
    print()

    if not overall_success:
        print("CLINPGX API TEST DID NOT FULLY PASS")
        sys.exit(1)

    print("CLINPGX API TEST COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()

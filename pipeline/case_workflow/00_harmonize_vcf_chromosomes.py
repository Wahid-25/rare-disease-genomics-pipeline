#!/usr/bin/env python3

import gzip
import re
import sys
from pathlib import Path


if len(sys.argv) != 3:
    raise SystemExit(
        "Usage: 00_harmonize_vcf_chromosomes.py INPUT_VCF OUTPUT_VCF"
    )

source = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()

if not source.is_file():
    raise SystemExit(f"ERROR: Input VCF missing: {source}")


def open_input(path):
    if path.name.endswith(".gz"):
        return gzip.open(
            path,
            "rt",
            encoding="utf-8",
            errors="replace",
        )

    return path.open(
        encoding="utf-8",
        errors="replace",
    )


def normalize_chromosome(value):
    value = value.strip()

    if value.startswith("chr"):
        return value

    if value in {"M", "MT"}:
        return "chrM"

    if value in {
        *(str(number) for number in range(1, 23)),
        "X",
        "Y",
    }:
        return f"chr{value}"

    return value


output.parent.mkdir(parents=True, exist_ok=True)

records = 0
changed = 0

with open_input(source) as input_handle, output.open(
    "w",
    encoding="utf-8",
) as output_handle:

    for line in input_handle:
        if line.startswith("##contig=<ID="):
            old_line = line

            line = re.sub(
                r"^(##contig=<ID=)([^,>]+)",
                lambda match: (
                    match.group(1)
                    + normalize_chromosome(match.group(2))
                ),
                line,
            )

            if line != old_line:
                changed += 1

        elif not line.startswith("#"):
            fields = line.rstrip("\n").split("\t")

            if len(fields) < 8:
                raise SystemExit(
                    f"ERROR: Malformed VCF record: {line[:100]}"
                )

            old_chromosome = fields[0]
            fields[0] = normalize_chromosome(fields[0])

            if fields[0] != old_chromosome:
                changed += 1

            records += 1
            line = "\t".join(fields) + "\n"

        output_handle.write(line)

if records == 0:
    raise SystemExit("ERROR: Input VCF contains no variant records.")

print(f"Prepared VCF:       {output}")
print(f"Variant records:    {records}")
print(f"Chromosome changes: {changed}")

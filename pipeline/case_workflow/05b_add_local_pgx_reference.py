#!/usr/bin/env python3
"""Validate local curated PGx truth with rsID and allele-aware matching.

This script is used only in explicit validation mode. Production mode uses
official ClinPGx evidence and writes disabled local-validation outputs.

Matching priority:
1. rsID and normalized chromosome/position/REF/ALT
2. normalized chromosome/position/REF/ALT when rsID is absent or differs
3. unambiguous rsID-only fallback when allele coordinates are unavailable

A conflicting rsID with two complete but different allele keys is not treated
as a match.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "2"

OUTPUT_FIELDS = [
    "case_id",
    "sample",
    "variant",
    "vcf_id",
    "genotype",
    "zygosity",
    "gene",
    "consequence",
    "local_pgx_sample_id",
    "local_pgx_rsid",
    "local_pgx_gene",
    "local_pgx_reference_variant",
    "local_pgx_observed_variant",
    "local_pgx_match_method",
    "local_pgx_allele_match",
    "local_pgx_expected_genotype",
    "local_pgx_observed_genotype_class",
    "local_pgx_genotype_match",
    "local_pgx_phenotype",
    "local_pgx_affected_drugs",
    "local_pgx_cpic_level",
    "local_pgx_clinical_recommendation",
    "local_pgx_source",
    "local_pgx_status",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def patient_id_from_case(case_id: str) -> str:
    match = re.search(r"patient[_-]?(\d+)", case_id, flags=re.IGNORECASE)
    if not match:
        raise ValueError(
            f"Cannot derive validation patient ID from case ID: {case_id}"
        )
    return f"PATIENT_{int(match.group(1)):02d}"


def normalize_chromosome(value: str) -> str:
    chromosome = clean(value)
    chromosome = re.sub(r"^chr", "", chromosome, flags=re.IGNORECASE)
    chromosome = chromosome.upper()

    aliases = {
        "M": "MT",
        "MITO": "MT",
        "MITOCHONDRIAL": "MT",
    }
    chromosome = aliases.get(chromosome, chromosome)

    if chromosome.isdigit():
        chromosome = str(int(chromosome))

    return chromosome


def normalize_allele(value: str) -> str:
    return clean(value).upper()


def normalize_rsid(value: str) -> str:
    candidate = clean(value).lower()

    if not candidate or candidate == ".":
        return ""

    for token in re.split(r"[;,|]", candidate):
        token = token.strip()
        if re.fullmatch(r"rs\d+", token):
            return token

    return candidate


def variant_key_from_parts(
    chromosome: str,
    position: str,
    reference: str,
    alternate: str,
) -> tuple[str, int, str, str] | None:
    chrom = normalize_chromosome(chromosome)
    ref = normalize_allele(reference)
    alt = normalize_allele(alternate)
    pos_text = clean(position)

    if not chrom or not pos_text or not ref or not alt:
        return None

    try:
        pos = int(pos_text)
    except ValueError:
        return None

    if pos <= 0 or "," in alt:
        return None

    return chrom, pos, ref, alt


def parse_variant(value: str) -> tuple[str, int, str, str] | None:
    text = clean(value)

    match = re.fullmatch(
        r"(?:chr)?([^:]+):(\d+):([^:>]+)>([^:>]+)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    return variant_key_from_parts(
        match.group(1),
        match.group(2),
        match.group(3),
        match.group(4),
    )


def format_variant_key(
    key: tuple[str, int, str, str] | None,
) -> str:
    if key is None:
        return ""

    chrom, pos, ref, alt = key
    return f"chr{chrom}:{pos}:{ref}>{alt}"


def local_variant_key(row: dict[str, str]) -> tuple[str, int, str, str] | None:
    return variant_key_from_parts(
        row.get("chromosome", ""),
        row.get("position", ""),
        row.get("ref", ""),
        row.get("alt", ""),
    )


def observed_genotype_class(genotype: str, zygosity: str) -> str:
    z = clean(zygosity).lower()
    gt = clean(genotype).replace("|", "/")

    if "hemizyg" in z or "haploid_alt" in z:
        return "hemizygous"
    if "heterozyg" in z:
        return "heterozygous"
    if "homozyg" in z:
        return "homozygous"

    alleles = [
        item
        for item in gt.split("/")
        if item not in {"", "."}
    ]

    if len(alleles) == 1:
        return "hemizygous" if alleles[0] != "0" else "reference"

    if len(alleles) == 2:
        if alleles[0] == alleles[1]:
            return "homozygous" if alleles[0] != "0" else "reference"
        return "heterozygous"

    return "unknown"


def expected_genotype_class(text: str) -> str:
    value = clean(text).lower()

    if "hemizyg" in value:
        return "hemizygous"
    if "heterozyg" in value:
        return "heterozygous"
    if "homozyg" in value:
        return "homozygous"

    return "unknown"


def prepare_local_records(
    local_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_identity: set[tuple[str, str, str]] = set()

    for index, row in enumerate(local_rows):
        rsid = normalize_rsid(row.get("rsid", ""))
        key = local_variant_key(row)
        gene = clean(row.get("gene")).upper()

        if not rsid and key is None:
            raise ValueError(
                "Each local PGx row requires an rsID, an allele key, "
                "or both."
            )

        identity = (
            rsid,
            format_variant_key(key),
            gene,
        )
        if identity in seen_identity:
            raise ValueError(
                "Duplicate local PGx identity: "
                + "|".join(identity)
            )
        seen_identity.add(identity)

        record = dict(row)
        record["_index"] = index
        record["_rsid"] = rsid
        record["_key"] = key
        records.append(record)

    return records


def choose_candidate(
    local_records: list[dict[str, Any]],
    observed_rsid: str,
    observed_key: tuple[str, int, str, str] | None,
    used_indices: set[int] | None = None,
) -> tuple[dict[str, Any] | None, str, bool]:
    used = used_indices or set()
    available = [
        record
        for record in local_records
        if int(record["_index"]) not in used
    ]

    exact = [
        record
        for record in available
        if observed_rsid
        and record["_rsid"] == observed_rsid
        and observed_key is not None
        and record["_key"] == observed_key
    ]

    if len(exact) == 1:
        return exact[0], "rsid_and_allele", False
    if len(exact) > 1:
        return None, "ambiguous_rsid_and_allele", True

    coordinate = [
        record
        for record in available
        if observed_key is not None
        and record["_key"] == observed_key
    ]

    if len(coordinate) == 1:
        return coordinate[0], "allele_coordinates", False
    if len(coordinate) > 1:
        return None, "ambiguous_allele_coordinates", True

    rsid_only = [
        record
        for record in available
        if observed_rsid
        and record["_rsid"] == observed_rsid
        and (observed_key is None or record["_key"] is None)
    ]

    if len(rsid_only) == 1:
        return rsid_only[0], "rsid_only", False
    if len(rsid_only) > 1:
        return None, "ambiguous_rsid_only", True

    return None, "", False


def expected_identifier(record: dict[str, Any]) -> str:
    rsid = clean(record.get("rsid"))
    key = format_variant_key(record.get("_key"))

    if rsid and key:
        return f"{rsid}|{key}"
    return rsid or key or f"local_row_{record['_index']}"


def main() -> None:
    if len(sys.argv) not in {2, 3}:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/05b_add_local_pgx_reference.py "
            "CASE_ID [LOCAL_REFERENCE_CSV]"
        )
        raise SystemExit(1)

    case_id = sys.argv[1]
    script_path = Path(__file__).resolve()
    project_root = script_path.parents[2]

    reference_file = (
        Path(sys.argv[2]).resolve()
        if len(sys.argv) == 3
        else project_root
        / "resources"
        / "clinpgx"
        / "local_curated_pgx_reference.csv"
    )

    official_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "clinpgx"
        / f"{case_id}.clinpgx_matches.tsv"
    )
    output_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "clinpgx"
        / f"{case_id}.local_pgx_matches.tsv"
    )
    qc_file = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.local_pgx_qc.tsv"
    )

    for required in (reference_file, official_table):
        if not required.is_file():
            print(f"ERROR: Required file not found: {required}")
            raise SystemExit(1)

    patient_id = patient_id_from_case(case_id)

    with reference_file.open(
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        reader = csv.DictReader(handle)
        required_columns = {
            "sample_id",
            "category",
            "gene",
            "rsid",
            "genotype",
            "phenotype",
            "affected_drugs",
            "cpic_level",
            "clinical_recommendation",
        }
        missing = required_columns - set(reader.fieldnames or [])

        if missing:
            print(
                "ERROR: Local PGx reference is missing columns: "
                + ", ".join(sorted(missing))
            )
            raise SystemExit(1)

        local_rows = [
            {key: clean(value) for key, value in row.items()}
            for row in reader
            if "pgx" in clean(row.get("category")).lower()
            and clean(row.get("sample_id")).upper() == patient_id
        ]

    try:
        local_records = prepare_local_records(local_rows)
    except ValueError as error:
        print(f"ERROR: {error}")
        raise SystemExit(1) from error

    with official_table.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        official_reader = csv.DictReader(handle, delimiter="\t")
        official_rows = list(official_reader)

    matched_rows: list[dict[str, str]] = []
    used_indices: set[int] = set()
    gene_mismatches = 0
    genotype_mismatches = 0
    ambiguous_observed_rows = 0
    rsid_and_allele_matches = 0
    allele_coordinate_matches = 0
    rsid_only_matches = 0

    for row in official_rows:
        observed_rsid = normalize_rsid(
            row.get("vcf_id")
            or row.get("clinpgx_variant_query")
        )
        observed_key = parse_variant(row.get("variant", ""))

        local, method, ambiguous = choose_candidate(
            local_records,
            observed_rsid,
            observed_key,
            used_indices,
        )

        if ambiguous:
            ambiguous_observed_rows += 1
            continue

        if local is None:
            continue

        used_indices.add(int(local["_index"]))

        if method == "rsid_and_allele":
            rsid_and_allele_matches += 1
        elif method == "allele_coordinates":
            allele_coordinate_matches += 1
        elif method == "rsid_only":
            rsid_only_matches += 1

        observed_gene = clean(row.get("gene")).upper()
        expected_gene = clean(local.get("gene")).upper()

        observed_class = observed_genotype_class(
            clean(row.get("genotype")),
            clean(row.get("zygosity")),
        )
        expected_class = expected_genotype_class(
            clean(local.get("genotype"))
        )

        gene_match = observed_gene == expected_gene
        genotype_match = (
            expected_class == "unknown"
            or observed_class == expected_class
        )

        local_key = local.get("_key")
        allele_match = (
            "yes"
            if local_key is not None
            and observed_key is not None
            and local_key == observed_key
            else "not_available"
        )

        if not gene_match:
            status = "local_reference_gene_mismatch"
            gene_mismatches += 1
        elif not genotype_match:
            status = "local_reference_genotype_mismatch"
            genotype_mismatches += 1
        else:
            status = "local_reference_match"

        matched_rows.append(
            {
                "case_id": case_id,
                "sample": clean(row.get("sample")),
                "variant": clean(row.get("variant")),
                "vcf_id": clean(row.get("vcf_id")),
                "genotype": clean(row.get("genotype")),
                "zygosity": clean(row.get("zygosity")),
                "gene": observed_gene,
                "consequence": clean(row.get("consequence")),
                "local_pgx_sample_id": patient_id,
                "local_pgx_rsid": clean(local.get("rsid")),
                "local_pgx_gene": clean(local.get("gene")),
                "local_pgx_reference_variant": format_variant_key(
                    local_key
                ),
                "local_pgx_observed_variant": format_variant_key(
                    observed_key
                ),
                "local_pgx_match_method": method,
                "local_pgx_allele_match": allele_match,
                "local_pgx_expected_genotype": clean(
                    local.get("genotype")
                ),
                "local_pgx_observed_genotype_class": observed_class,
                "local_pgx_genotype_match": (
                    "yes" if genotype_match else "no"
                ),
                "local_pgx_phenotype": clean(
                    local.get("phenotype")
                ),
                "local_pgx_affected_drugs": clean(
                    local.get("affected_drugs")
                ),
                "local_pgx_cpic_level": clean(
                    local.get("cpic_level")
                ),
                "local_pgx_clinical_recommendation": clean(
                    local.get("clinical_recommendation")
                ),
                "local_pgx_source": "local_curated_pgx_reference",
                "local_pgx_status": status,
            }
        )

    output_table.parent.mkdir(parents=True, exist_ok=True)
    qc_file.parent.mkdir(parents=True, exist_ok=True)

    with output_table.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=OUTPUT_FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(matched_rows)

    missing_expected = [
        expected_identifier(record)
        for record in local_records
        if int(record["_index"]) not in used_indices
    ]

    coordinate_complete_rows = sum(
        record["_key"] is not None
        for record in local_records
    )

    qc_rows = [
        ("case_id", case_id),
        ("local_reference", str(reference_file.relative_to(project_root))),
        ("local_pgx_schema_version", SCHEMA_VERSION),
        ("patient_id", patient_id),
        ("expected_local_pgx_rows", str(len(local_records))),
        ("coordinate_complete_reference_rows", str(coordinate_complete_rows)),
        ("matched_local_pgx_rows", str(len(matched_rows))),
        ("rsid_and_allele_matches", str(rsid_and_allele_matches)),
        ("allele_coordinate_matches", str(allele_coordinate_matches)),
        ("rsid_only_matches", str(rsid_only_matches)),
        ("ambiguous_observed_rows", str(ambiguous_observed_rows)),
        ("gene_mismatch_rows", str(gene_mismatches)),
        ("genotype_mismatch_rows", str(genotype_mismatches)),
        ("missing_expected_variants", ",".join(missing_expected)),
        ("output_table", str(output_table.relative_to(project_root))),
    ]

    with qc_file.open("w", encoding="utf-8") as handle:
        handle.write("metric\tvalue\n")
        for metric, value in qc_rows:
            handle.write(f"{metric}\t{value}\n")

    print("========================================")
    print("ALLELE-AWARE LOCAL PGX VALIDATION")
    print("========================================")
    print(f"Case ID:                     {case_id}")
    print(f"Patient ID:                  {patient_id}")
    print(f"Expected local PGx rows:     {len(local_records)}")
    print(f"Coordinate-complete rows:    {coordinate_complete_rows}")
    print(f"Matched local PGx rows:      {len(matched_rows)}")
    print(f"rsID + allele matches:       {rsid_and_allele_matches}")
    print(f"Allele-coordinate matches:   {allele_coordinate_matches}")
    print(f"rsID-only fallback matches:  {rsid_only_matches}")
    print(f"Ambiguous observed rows:     {ambiguous_observed_rows}")
    print(f"Gene mismatches:             {gene_mismatches}")
    print(f"Genotype mismatches:         {genotype_mismatches}")
    print(
        "Missing expected variants:   "
        + (",".join(missing_expected) if missing_expected else "none")
    )
    print(f"Output:                      {output_table}")
    print(f"QC:                          {qc_file}")

    if (
        missing_expected
        or ambiguous_observed_rows
        or gene_mismatches
        or genotype_mismatches
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()

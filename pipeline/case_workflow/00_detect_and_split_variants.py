#!/usr/bin/env python3

import csv
import gzip
import re
import sys
from pathlib import Path


SUPPORTED_CNV_TYPES = {"DEL", "DUP"}

REPEAT_TYPES = {
    "STR",
    "RE",
    "REPEAT",
    "REPEAT_EXPANSION",
    "EXPANSION",
    "CAG_EXPANSION",
}


def clean(value) -> str:
    return str(value).strip() if value is not None else ""


def open_text(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")

    return path.open("r", encoding="utf-8")


def parse_info(info_text: str) -> dict[str, str]:
    result = {}

    if info_text in {"", "."}:
        return result

    for item in info_text.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            result[key] = value
        else:
            result[item] = "true"

    return result


def first_integer(value: str):
    if not value:
        return None

    match = re.search(r"-?\d+", value)

    if not match:
        return None

    return int(match.group())


def calculate_end(
    pos: int,
    info: dict[str, str],
) -> tuple[int | None, str]:
    end = first_integer(info.get("END", ""))

    if end is not None and end >= pos:
        return end, "INFO/END"

    svlen = first_integer(info.get("SVLEN", ""))

    if svlen is not None and svlen != 0:
        calculated = pos + abs(svlen) - 1

        if calculated >= pos:
            return calculated, "INFO/SVLEN"

    return None, "missing_END_and_SVLEN"


def sequence_allele(value: str) -> bool:
    return bool(re.fullmatch(r"[ACGTNacgtn]+", value))


def symbolic_type(allele: str) -> str:
    match = re.fullmatch(r"<([^>]+)>", allele)

    if match:
        return match.group(1).upper()

    if "[" in allele or "]" in allele:
        return "BND"

    return ""


def detect_svtype(
    alternate_alleles: list[str],
    info: dict[str, str],
) -> tuple[str, str]:
    info_type = clean(info.get("SVTYPE")).upper()

    if info_type:
        return info_type, "INFO/SVTYPE"

    detected = {
        symbolic_type(allele)
        for allele in alternate_alleles
        if symbolic_type(allele)
    }

    if len(detected) == 1:
        return next(iter(detected)), "ALT"

    if len(detected) > 1:
        return "MIXED_SYMBOLIC", "ALT"

    return "", "sequence_alleles"


def classify_sequence_variant(
    reference: str,
    alternate_alleles: list[str],
) -> tuple[str, str, str]:
    if not sequence_allele(reference):
        return (
            "unresolved_sequence_variant",
            "other_or_unsupported_report",
            "detected_not_fully_supported",
        )

    if any(allele == "*" for allele in alternate_alleles):
        return (
            "spanning_deletion_allele",
            "other_or_unsupported_report",
            "detected_not_fully_supported",
        )

    if not all(
        sequence_allele(allele)
        for allele in alternate_alleles
    ):
        return (
            "unresolved_sequence_variant",
            "other_or_unsupported_report",
            "detected_not_fully_supported",
        )

    length_differences = [
        len(allele) - len(reference)
        for allele in alternate_alleles
    ]

    if any(abs(value) >= 50 for value in length_differences):
        if all(value > 0 for value in length_differences):
            variant_class = "large_sequence_insertion"
        elif all(value < 0 for value in length_differences):
            variant_class = "large_sequence_deletion"
        else:
            variant_class = "large_sequence_complex"

        return (
            variant_class,
            "other_or_unsupported_report",
            "detected_not_fully_supported",
        )

    if (
        len(reference) == 1
        and all(len(allele) == 1 for allele in alternate_alleles)
    ):
        return (
            "SNV",
            "small_variant_branch",
            "fully_supported",
        )

    if all(
        len(allele) == len(reference)
        for allele in alternate_alleles
    ):
        return (
            "MNV",
            "small_variant_branch",
            "fully_supported",
        )

    if all(value > 0 for value in length_differences):
        return (
            "small_insertion",
            "small_variant_branch",
            "fully_supported",
        )

    if all(value < 0 for value in length_differences):
        return (
            "small_deletion",
            "small_variant_branch",
            "fully_supported",
        )

    return (
        "small_complex_variant",
        "small_variant_branch",
        "fully_supported",
    )


def safe_relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/00_detect_and_split_variants.py "
            "CASE_ID INPUT_VCF"
        )
        sys.exit(1)

    case_id = sys.argv[1]
    input_argument = Path(sys.argv[2])

    project_root = Path(__file__).resolve().parents[2]

    input_vcf = (
        input_argument
        if input_argument.is_absolute()
        else project_root / input_argument
    )

    if not input_vcf.is_file():
        raise SystemExit(
            f"ERROR: Input VCF was not found: {input_vcf}"
        )

    work_dir = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "work"
    )

    final_dir = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
    )

    work_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    small_vcf = work_dir / f"{case_id}.small_variants.raw.vcf"
    cnv_bed = work_dir / f"{case_id}.cnvs.bed"
    cnv_manifest = work_dir / f"{case_id}.cnv_manifest.tsv"

    other_vcf = (
        work_dir
        / f"{case_id}.other_structural_variants.vcf"
    )

    routing_manifest = (
        final_dir
        / f"{case_id}.variant_routing_manifest.tsv"
    )

    qc_file = (
        final_dir
        / f"{case_id}.variant_routing_qc.tsv"
    )

    headers = []
    small_records = []
    other_records = []
    cnv_rows = []
    manifest_rows = []

    total_records = 0
    malformed_records = 0
    small_variant_records = 0
    supported_cnv_records = 0
    other_records_count = 0

    class_counts: dict[str, int] = {}

    with open_text(input_vcf) as handle:
        for line in handle:
            if line.startswith("#"):
                headers.append(line)
                continue

            total_records += 1
            record_line = (
                line if line.endswith("\n") else line + "\n"
            )

            fields = line.rstrip("\n").split("\t")

            if len(fields) < 8:
                malformed_records += 1

                manifest_rows.append(
                    {
                        "record_number": str(total_records),
                        "chrom": fields[0] if fields else "",
                        "pos": fields[1] if len(fields) > 1 else "",
                        "vcf_id": fields[2] if len(fields) > 2 else "",
                        "ref": fields[3] if len(fields) > 3 else "",
                        "alt": fields[4] if len(fields) > 4 else "",
                        "filter": "",
                        "detected_class": "malformed_record",
                        "route": "malformed",
                        "support_status": "not_processible",
                        "svtype": "",
                        "detection_method": "",
                        "end": "",
                        "end_source": "",
                        "multiallelic": "",
                        "reason": "fewer_than_8_VCF_columns",
                    }
                )

                class_counts["malformed_record"] = (
                    class_counts.get("malformed_record", 0) + 1
                )
                continue

            chrom, pos_text, record_id, ref, alt = fields[:5]
            filter_value = fields[6]
            info = parse_info(fields[7])

            try:
                pos = int(pos_text)
            except ValueError:
                malformed_records += 1

                manifest_rows.append(
                    {
                        "record_number": str(total_records),
                        "chrom": chrom,
                        "pos": pos_text,
                        "vcf_id": record_id,
                        "ref": ref,
                        "alt": alt,
                        "filter": filter_value,
                        "detected_class": "malformed_record",
                        "route": "malformed",
                        "support_status": "not_processible",
                        "svtype": "",
                        "detection_method": "",
                        "end": "",
                        "end_source": "",
                        "multiallelic": "",
                        "reason": "invalid_POS",
                    }
                )

                class_counts["malformed_record"] = (
                    class_counts.get("malformed_record", 0) + 1
                )
                continue

            alternate_alleles = alt.split(",")
            multiallelic = (
                "yes" if len(alternate_alleles) > 1 else "no"
            )

            svtype, detection_method = detect_svtype(
                alternate_alleles,
                info,
            )

            end = None
            end_source = ""
            reason = ""

            if svtype in SUPPORTED_CNV_TYPES:
                end, end_source = calculate_end(pos, info)

                if len(alternate_alleles) > 1:
                    detected_class = (
                        f"multiallelic_{svtype}"
                    )
                    route = "other_or_unsupported_report"
                    support_status = (
                        "detected_not_fully_supported"
                    )
                    reason = (
                        "multiallelic_symbolic_CNV_requires_review"
                    )

                    other_records.append(record_line)
                    other_records_count += 1

                elif end is None:
                    detected_class = f"{svtype}_missing_end"
                    route = "other_or_unsupported_report"
                    support_status = (
                        "detected_not_fully_supported"
                    )
                    reason = "END_and_SVLEN_missing"

                    other_records.append(record_line)
                    other_records_count += 1

                else:
                    detected_class = svtype
                    route = "cnv_branch"
                    support_status = "fully_supported"
                    reason = "supported_DEL_DUP_interval"

                    cnv_rows.append(
                        [
                            chrom,
                            str(pos - 1),
                            str(end),
                            svtype,
                            record_id,
                            str(pos),
                            alt,
                            detection_method,
                            end_source,
                            str(total_records),
                            detected_class,
                            support_status,
                        ]
                    )

                    supported_cnv_records += 1

            elif (
                svtype in REPEAT_TYPES
                or "EXPANSION" in svtype
                or "REPEAT" in svtype
            ):
                end, end_source = calculate_end(pos, info)

                detected_class = "repeat_expansion"
                route = "other_or_unsupported_report"
                support_status = "detected_not_fully_supported"
                reason = "repeat_expansion_branch_not_implemented"

                other_records.append(record_line)
                other_records_count += 1

            elif svtype == "NON_REF":
                end, end_source = calculate_end(pos, info)

                detected_class = "gVCF_reference_block"
                route = "other_or_unsupported_report"
                support_status = "requires_genotyping"
                reason = "gVCF_block_is_not_a_called_variant"

                other_records.append(record_line)
                other_records_count += 1

            elif svtype:
                end, end_source = calculate_end(pos, info)

                structural_classes = {
                    "INV": "inversion",
                    "INS": "structural_insertion",
                    "BND": "breakend",
                    "TRA": "translocation",
                    "CNV": "unspecified_CNV",
                    "MIXED_SYMBOLIC": (
                        "mixed_symbolic_multiallelic"
                    ),
                }

                detected_class = structural_classes.get(
                    svtype,
                    f"symbolic_{svtype}",
                )

                route = "other_or_unsupported_report"
                support_status = "detected_not_fully_supported"
                reason = "structural_type_not_fully_supported"

                other_records.append(record_line)
                other_records_count += 1

            else:
                (
                    detected_class,
                    route,
                    support_status,
                ) = classify_sequence_variant(
                    ref,
                    alternate_alleles,
                )

                reason = (
                    "sequence_variant"
                    if route == "small_variant_branch"
                    else "large_or_special_sequence_variant"
                )

                if route == "small_variant_branch":
                    small_records.append(record_line)
                    small_variant_records += 1
                else:
                    other_records.append(record_line)
                    other_records_count += 1

            class_counts[detected_class] = (
                class_counts.get(detected_class, 0) + 1
            )

            manifest_rows.append(
                {
                    "record_number": str(total_records),
                    "chrom": chrom,
                    "pos": str(pos),
                    "vcf_id": record_id,
                    "ref": ref,
                    "alt": alt,
                    "filter": filter_value,
                    "detected_class": detected_class,
                    "route": route,
                    "support_status": support_status,
                    "svtype": svtype,
                    "detection_method": detection_method,
                    "end": str(end) if end is not None else "",
                    "end_source": end_source,
                    "multiallelic": multiallelic,
                    "reason": reason,
                }
            )

    if not any(
        line.startswith("#CHROM")
        for line in headers
    ):
        raise SystemExit(
            "ERROR: The VCF #CHROM header was not found."
        )

    with small_vcf.open("w", encoding="utf-8") as handle:
        handle.writelines(headers)
        handle.writelines(small_records)

    with other_vcf.open("w", encoding="utf-8") as handle:
        handle.writelines(headers)
        handle.writelines(other_records)

    with cnv_bed.open("w", encoding="utf-8") as handle:
        for row in cnv_rows:
            handle.write("\t".join(row[:4]) + "\n")

    cnv_columns = [
        "chrom",
        "bed_start",
        "bed_end",
        "cnv_type",
        "vcf_id",
        "vcf_pos",
        "vcf_alt",
        "type_detection_method",
        "end_detection_method",
        "source_record_number",
        "detected_class",
        "support_status",
    ]

    with cnv_manifest.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(cnv_columns)
        writer.writerows(cnv_rows)

    manifest_columns = [
        "record_number",
        "chrom",
        "pos",
        "vcf_id",
        "ref",
        "alt",
        "filter",
        "detected_class",
        "route",
        "support_status",
        "svtype",
        "detection_method",
        "end",
        "end_source",
        "multiallelic",
        "reason",
    ]

    with routing_manifest.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=manifest_columns,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    accounted_records = (
        small_variant_records
        + supported_cnv_records
        + other_records_count
        + malformed_records
    )

    accounting_status = (
        "PASS"
        if accounted_records == total_records
        else "FAIL"
    )

    with qc_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(
            [
                "input_vcf",
                safe_relative(input_vcf, project_root),
            ]
        )
        writer.writerow(["total_records", total_records])
        writer.writerow(
            ["accounted_records", accounted_records]
        )
        writer.writerow(
            ["record_accounting_status", accounting_status]
        )
        writer.writerow(
            ["small_variant_records", small_variant_records]
        )
        writer.writerow(
            ["supported_DEL_DUP_records", supported_cnv_records]
        )
        writer.writerow(
            [
                "other_structural_variant_records",
                other_records_count,
            ]
        )
        writer.writerow(
            ["malformed_records", malformed_records]
        )

        for variant_class in sorted(class_counts):
            writer.writerow(
                [
                    f"class_{variant_class}",
                    class_counts[variant_class],
                ]
            )

        writer.writerow(
            [
                "small_variant_branch_required",
                "yes" if small_variant_records else "no",
            ]
        )
        writer.writerow(
            [
                "cnv_branch_required",
                "yes" if supported_cnv_records else "no",
            ]
        )
        writer.writerow(
            [
                "small_variant_vcf",
                safe_relative(small_vcf, project_root),
            ]
        )
        writer.writerow(
            [
                "cnv_bed",
                safe_relative(cnv_bed, project_root),
            ]
        )
        writer.writerow(
            [
                "other_sv_vcf",
                safe_relative(other_vcf, project_root),
            ]
        )
        writer.writerow(
            [
                "routing_manifest",
                safe_relative(routing_manifest, project_root),
            ]
        )

    print("========================================")
    print("UNIVERSAL VARIANT ROUTING")
    print("========================================")
    print(f"Case ID:                    {case_id}")
    print(f"Total records:              {total_records}")
    print(f"Accounted records:          {accounted_records}")
    print(f"Accounting status:          {accounting_status}")
    print(f"Small variants:             {small_variant_records}")
    print(f"Supported DEL/DUP records:  {supported_cnv_records}")
    print(f"Other/special records:      {other_records_count}")
    print(f"Malformed records:          {malformed_records}")
    print()
    print(f"Routing manifest: {routing_manifest}")
    print(f"QC table:         {qc_file}")

    if accounting_status != "PASS":
        raise SystemExit(
            "ERROR: Not every input record was accounted for."
        )

    print()
    print("VARIANT ROUTING COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()

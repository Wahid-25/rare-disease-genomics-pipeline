#!/usr/bin/env python3
"""GRCh38-aware sex-chromosome and ploidy preflight.

This is a transparent technical/biological consistency screen. It does not
infer sex, diagnose aneuploidy, or reject unusual biology by default. It
reports warnings and fails only for unreadable or structurally invalid input.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import re
from collections import Counter
from pathlib import Path
from typing import Iterable


PAR_GRCH38 = {
    "X": ((10001, 2781479), (155701383, 156030895)),
    "Y": ((10001, 2781479), (56887903, 57217415)),
}


def clean(value: object) -> str:
    return str(value or "").strip()


def normalize_chromosome(value: object) -> str:
    chrom = clean(value)
    if chrom.lower().startswith("chr"):
        chrom = chrom[3:]
    upper = chrom.upper()
    if upper in {"M", "MT", "MTRNR"}:
        return "MT"
    return upper


def normalize_sex(value: object) -> str:
    text = clean(value).lower()
    mapping = {
        "m": "male",
        "male": "male",
        "xy": "male",
        "f": "female",
        "female": "female",
        "xx": "female",
        "u": "unknown",
        "unknown": "unknown",
        "": "unknown",
    }
    if text not in mapping:
        raise ValueError("Sex must be male, female, or unknown.")
    return mapping[text]


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def in_par(chrom: str, pos: int) -> bool:
    return any(start <= pos <= end for start, end in PAR_GRCH38.get(chrom, ()))


def region_class(chrom: str, pos: int) -> str:
    if chrom in {"X", "Y"} and in_par(chrom, pos):
        return "pseudoautosomal"
    if chrom == "X":
        return "X_nonPAR"
    if chrom == "Y":
        return "Y_nonPAR"
    if chrom == "MT":
        return "mitochondrial"
    if chrom.isdigit() and 1 <= int(chrom) <= 22:
        return "autosomal"
    return "other"


def parse_gt(format_text: str, sample_text: str) -> str:
    keys = format_text.split(":") if format_text not in {"", "."} else []
    values = sample_text.split(":")
    if "GT" not in keys:
        return ""
    index = keys.index("GT")
    return values[index] if index < len(values) else ""


def gt_alleles(gt: str) -> list[str]:
    if gt in {"", ".", "./.", ".|."}:
        return []
    return re.split(r"[/|]", gt)


def ploidy(gt: str) -> int:
    alleles = gt_alleles(gt)
    if not alleles or any(a == "." for a in alleles):
        return 0
    return len(alleles)


def is_heterozygous(gt: str) -> bool:
    alleles = gt_alleles(gt)
    return len(alleles) >= 2 and len(set(alleles)) > 1 and "." not in alleles


def has_nonreference(gt: str) -> bool:
    return any(a not in {"0", ".", ""} for a in gt_alleles(gt))


def assess_record(
    chrom: str,
    pos: int,
    gt: str,
    sex: str,
) -> tuple[str, str]:
    region = region_class(chrom, pos)
    call_ploidy = ploidy(gt)

    if not gt:
        return "not_evaluated", "GT_not_available"
    if call_ploidy == 0:
        return "not_evaluated", "GT_missing_or_partial"

    if call_ploidy > 2:
        return "warning", "polyploid_or_complex_GT_review_required"

    if region == "autosomal":
        if call_ploidy == 1:
            return "warning", "haploid_autosomal_call_review_required"
        return "pass", "diploid_autosomal_call"

    if region == "pseudoautosomal":
        if call_ploidy == 1:
            return "warning", "haploid_PAR_call_review_required"
        return "pass", "diploid_PAR_call"

    if region == "X_nonPAR":
        if sex == "male":
            if call_ploidy == 1:
                return "pass", "male_X_nonPAR_haploid_call"
            if is_heterozygous(gt):
                return "warning", "male_X_nonPAR_heterozygous_call"
            return "notice", "male_X_nonPAR_diploid_homozygous_encoding"

        if sex == "female":
            if call_ploidy == 1:
                return "warning", "female_X_nonPAR_haploid_call"
            return "pass", "female_X_nonPAR_diploid_call"

        return "notice", "X_nonPAR_call_sex_unknown"

    if region == "Y_nonPAR":
        if sex == "female" and has_nonreference(gt):
            return "warning", "female_Y_nonPAR_nonreference_call"
        if sex == "male":
            if call_ploidy == 1:
                return "pass", "male_Y_nonPAR_haploid_call"
            if is_heterozygous(gt):
                return "warning", "male_Y_nonPAR_heterozygous_call"
            return "notice", "male_Y_nonPAR_diploid_homozygous_encoding"
        return "notice", "Y_nonPAR_call_sex_unknown"

    if region == "mitochondrial":
        return "notice", "mitochondrial_GT_heteroplasmy_not_assessed"

    return "notice", "unclassified_contig_ploidy_not_interpreted"


def iter_records(path: Path) -> tuple[str, Iterable[dict[str, str]]]:
    handle = open_text(path)
    sample_name = ""
    rows: list[dict[str, str]] = []

    with handle:
        for line in handle:
            if line.startswith("##"):
                continue

            if line.startswith("#CHROM"):
                header = line.rstrip("\n").split("\t")
                if len(header) != 10:
                    raise ValueError(
                        "Preflight requires exactly one selected patient sample."
                    )
                sample_name = header[9]
                continue

            if line.startswith("#"):
                continue

            fields = line.rstrip("\n").split("\t")
            if len(fields) != 10:
                raise ValueError(
                    "VCF record does not match a one-sample #CHROM header."
                )

            chrom = normalize_chromosome(fields[0])
            try:
                pos = int(fields[1])
            except ValueError as exc:
                raise ValueError(f"Invalid VCF position: {fields[1]!r}") from exc

            gt = parse_gt(fields[8], fields[9])
            rows.append(
                {
                    "chromosome": chrom,
                    "position": str(pos),
                    "vcf_id": fields[2],
                    "ref": fields[3],
                    "alt": fields[4],
                    "genotype": gt,
                }
            )

    if not sample_name:
        raise ValueError("VCF #CHROM header was not found.")

    return sample_name, rows


def write_outputs(
    case_id: str,
    vcf: Path,
    sex: str,
    output_dir: Path,
) -> tuple[Path, Path, Counter]:
    sample_name, rows = iter_records(vcf)
    output_dir.mkdir(parents=True, exist_ok=True)

    detail = output_dir / f"{case_id}.sex_ploidy_records.tsv"
    qc = output_dir / f"{case_id}.sex_ploidy_qc.tsv"

    counts: Counter = Counter()

    fields = [
        "case_id",
        "sample",
        "reported_sex",
        "chromosome",
        "position",
        "region_class",
        "vcf_id",
        "ref",
        "alt",
        "genotype",
        "called_ploidy",
        "assessment",
        "reason",
    ]

    with detail.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()

        for row in rows:
            chrom = row["chromosome"]
            pos = int(row["position"])
            assessment, reason = assess_record(
                chrom,
                pos,
                row["genotype"],
                sex,
            )
            counts[assessment] += 1
            counts[f"region:{region_class(chrom, pos)}"] += 1

            writer.writerow(
                {
                    "case_id": case_id,
                    "sample": sample_name,
                    "reported_sex": sex,
                    **row,
                    "region_class": region_class(chrom, pos),
                    "called_ploidy": str(ploidy(row["genotype"])),
                    "assessment": assessment,
                    "reason": reason,
                }
            )

    overall = (
        "PASS_WITH_WARNINGS"
        if counts["warning"]
        else "PASS"
    )

    qc_rows = [
        ("case_id", case_id),
        ("input_vcf", str(vcf)),
        ("sample", sample_name),
        ("reported_sex", sex),
        ("assembly", "GRCh38"),
        ("total_records", str(len(rows))),
        ("pass_records", str(counts["pass"])),
        ("notice_records", str(counts["notice"])),
        ("warning_records", str(counts["warning"])),
        ("not_evaluated_records", str(counts["not_evaluated"])),
        ("autosomal_records", str(counts["region:autosomal"])),
        ("X_nonPAR_records", str(counts["region:X_nonPAR"])),
        ("Y_nonPAR_records", str(counts["region:Y_nonPAR"])),
        ("PAR_records", str(counts["region:pseudoautosomal"])),
        ("mitochondrial_records", str(counts["region:mitochondrial"])),
        ("preflight_status", overall),
        ("hard_failure_policy", "structural_errors_only"),
        ("biological_warning_policy", "report_and_continue"),
        ("detail_table", str(detail)),
    ]

    with qc.open("w", encoding="utf-8") as handle:
        handle.write("metric\tvalue\n")
        for metric, value in qc_rows:
            handle.write(f"{metric}\t{value}\n")

    return detail, qc, counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("vcf")
    parser.add_argument("--sex", default="unknown")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    vcf = Path(args.vcf).expanduser().resolve()
    if not vcf.is_file():
        raise SystemExit(f"ERROR: VCF not found: {vcf}")

    sex = normalize_sex(args.sex)
    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else Path.cwd() / "input" / "cases" / args.case_id / "prepared"
    )

    try:
        detail, qc, counts = write_outputs(
            args.case_id,
            vcf,
            sex,
            output_dir,
        )
    except (OSError, ValueError) as exc:
        raise SystemExit(f"ERROR: Sex/ploidy preflight failed: {exc}") from exc

    print("========================================")
    print("SEX-CHROMOSOME AND PLOIDY PREFLIGHT")
    print("========================================")
    print(f"Case ID:               {args.case_id}")
    print(f"Reported sex:          {sex}")
    print(f"Warnings:              {counts['warning']}")
    print(f"Not evaluated:         {counts['not_evaluated']}")
    print(f"Detail:                {detail}")
    print(f"QC:                    {qc}")
    print(
        "Status:                "
        + ("PASS_WITH_WARNINGS" if counts["warning"] else "PASS")
    )

    if args.strict and counts["warning"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

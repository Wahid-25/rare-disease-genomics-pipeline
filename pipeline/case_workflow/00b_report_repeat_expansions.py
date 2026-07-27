#!/usr/bin/env python3

import csv
import sys
from pathlib import Path


REPEAT_TYPES = {
    "STR",
    "RE",
    "REPEAT",
    "REPEAT_EXPANSION",
    "EXPANSION",
    "CAG_EXPANSION",
}


def clean(value):
    return str(value).strip() if value is not None else ""


def parse_info(value):
    result = {}

    for item in clean(value).split(";"):
        if not item:
            continue

        if "=" in item:
            key, val = item.split("=", 1)
            result[key] = val
        else:
            result[item] = "true"

    return result


def zygosity(genotype):
    gt = clean(genotype).replace("|", "/")

    if gt in {"0/1", "1/0"}:
        return "heterozygous"

    if gt == "1/1":
        return "homozygous_alt"

    if gt == "0/0":
        return "homozygous_reference"

    if gt in {"", ".", "./."}:
        return "not_available"

    return "other_or_complex"


if len(sys.argv) != 2:
    raise SystemExit(
        "Usage: 00b_report_repeat_expansions.py CASE_ID"
    )

case_id = sys.argv[1]
project = Path(__file__).resolve().parents[2]

case_dir = project / "results" / "cases" / case_id
final_dir = case_dir / "final"
work_dir = case_dir / "work"

manifest = (
    final_dir
    / f"{case_id}.variant_routing_manifest.tsv"
)

unsupported_vcf = (
    work_dir
    / f"{case_id}.other_structural_variants.vcf"
)

output = (
    final_dir
    / f"{case_id}.repeat_expansions.detected.tsv"
)

qc_file = (
    final_dir
    / f"{case_id}.repeat_expansion_qc.tsv"
)

if not manifest.is_file():
    raise SystemExit(
        f"ERROR: Routing manifest missing: {manifest}"
    )

vcf_records = {}

if unsupported_vcf.is_file():
    with unsupported_vcf.open(
        encoding="utf-8",
    ) as handle:
        for line in handle:
            if line.startswith("#"):
                continue

            fields = line.rstrip("\n").split("\t")

            if len(fields) < 8:
                continue

            chrom, pos, vcf_id, ref, alt = fields[:5]
            info = parse_info(fields[7])

            genotype = ""
            depth = ""
            genotype_quality = ""
            allelic_depth = ""

            if len(fields) >= 10:
                format_keys = fields[8].split(":")
                sample_values = fields[9].split(":")
                sample = dict(
                    zip(format_keys, sample_values)
                )

                genotype = clean(sample.get("GT"))
                depth = clean(sample.get("DP"))
                genotype_quality = clean(
                    sample.get("GQ")
                )
                allelic_depth = clean(
                    sample.get("AD")
                )

            key = (
                chrom,
                pos,
                vcf_id,
                ref,
                alt,
            )

            vcf_records[key] = {
                "info": info,
                "genotype": genotype,
                "depth_DP": depth,
                "genotype_quality_GQ":
                    genotype_quality,
                "allelic_depth_AD":
                    allelic_depth,
            }

with manifest.open(
    encoding="utf-8",
    newline="",
) as handle:
    routing_rows = list(
        csv.DictReader(handle, delimiter="\t")
    )

output_rows = []

for row in routing_rows:
    detected_class = clean(
        row.get("detected_class")
    ).lower()

    svtype = clean(row.get("svtype")).upper()
    alt = clean(row.get("alt"))

    is_repeat = (
        detected_class == "repeat_expansion"
        or svtype in REPEAT_TYPES
        or "EXPANSION" in svtype
        or "REPEAT" in svtype
        or "EXPANSION" in alt.upper()
    )

    if not is_repeat:
        continue

    chrom = clean(
        row.get("chromosome")
        or row.get("chrom")
    )

    pos = clean(
        row.get("position")
        or row.get("pos")
    )

    vcf_id = clean(
        row.get("id")
        or row.get("vcf_id")
    )

    ref = clean(row.get("ref"))
    alt = clean(row.get("alt"))

    key = (
        chrom,
        pos,
        vcf_id,
        ref,
        alt,
    )

    record = vcf_records.get(key, {})
    info = record.get("info", {})
    genotype = clean(record.get("genotype"))

    output_rows.append(
        {
            "case_id": case_id,
            "chromosome": chrom,
            "position": pos,
            "vcf_id": vcf_id,
            "ref": ref,
            "alt": alt,
            "svtype": svtype,
            "genotype": genotype,
            "zygosity": zygosity(genotype),
            "depth_DP": clean(
                record.get("depth_DP")
            ),
            "genotype_quality_GQ": clean(
                record.get(
                    "genotype_quality_GQ"
                )
            ),
            "allelic_depth_AD": clean(
                record.get("allelic_depth_AD")
            ),
            "repeat_unit": clean(
                info.get("REPEAT_UNIT")
            ),
            "observed_repeats": clean(
                info.get("OBSERVED_REPEATS")
            ),
            "normal_range": clean(
                info.get("NORMAL_RANGE")
            ),
            "reported_pathogenic_threshold":
                clean(
                    info.get(
                        "PATHOGENIC_THRESHOLD"
                    )
                ),
            "reported_disease_label": clean(
                info.get("DISEASE")
            ),
            "reported_hgvs_c": clean(
                info.get("HGVS_C")
            ),
            "reported_hgvs_p": clean(
                info.get("HGVS_P")
            ),
            "routing_status": clean(
                row.get("support_status")
            ),
            "interpretation_status":
                "detected_not_interpreted",
            "ranking_status":
                "excluded_from_universal_ranking",
            "required_next_step":
                "specialized_repeat_expansion_"
                "analysis_or_validated_repeat_assay",
            "interpretation_note":
                "Repeat-expansion metadata was "
                "preserved, but no diagnostic "
                "classification was inferred by "
                "this pipeline.",
        }
    )

columns = [
    "case_id",
    "chromosome",
    "position",
    "vcf_id",
    "ref",
    "alt",
    "svtype",
    "genotype",
    "zygosity",
    "depth_DP",
    "genotype_quality_GQ",
    "allelic_depth_AD",
    "repeat_unit",
    "observed_repeats",
    "normal_range",
    "reported_pathogenic_threshold",
    "reported_disease_label",
    "reported_hgvs_c",
    "reported_hgvs_p",
    "routing_status",
    "interpretation_status",
    "ranking_status",
    "required_next_step",
    "interpretation_note",
]

with output.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=columns,
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(output_rows)

with qc_file.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:
    writer = csv.writer(
        handle,
        delimiter="\t",
    )

    writer.writerows(
        [
            ["metric", "value"],
            ["case_id", case_id],
            [
                "repeat_expansions_detected",
                len(output_rows),
            ],
            [
                "repeat_expansions_ranked",
                0,
            ],
            [
                "interpretation_support",
                "detected_not_interpreted",
            ],
            [
                "output_table",
                output.relative_to(project),
            ],
        ]
    )

print("REPEAT-EXPANSION REPORT COMPLETE")
print(f"Detected: {len(output_rows)}")
print(f"Output:   {output}")
print(f"QC:       {qc_file}")

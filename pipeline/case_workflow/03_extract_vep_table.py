#!/usr/bin/env python3

import csv
import gzip
import re
import sys
from pathlib import Path
from urllib.parse import unquote


def open_text(path: Path):
    """Open plain-text or gzip-compressed files."""
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def parse_info(info_text: str) -> dict[str, str]:
    """Convert a VCF INFO field into a dictionary."""
    info = {}

    if info_text == ".":
        return info

    for item in info_text.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            info[key] = value
        else:
            info[item] = "true"

    return info


def decode_vep(value: str) -> str:
    """Decode characters escaped by VEP."""
    return unquote(value) if value else ""


def annotation_priority(annotation: dict[str, str]) -> tuple:
    """
    Select the most useful transcript.

    Priority:
    1. VEP PICK transcript
    2. MANE Select transcript
    3. Canonical transcript
    4. Higher predicted impact
    5. Protein-coding transcript
    """
    impact_scores = {
        "HIGH": 4,
        "MODERATE": 3,
        "LOW": 2,
        "MODIFIER": 1,
        "": 0,
    }

    return (
        1 if annotation.get("PICK") == "1" else 0,
        1 if annotation.get("MANE_SELECT") else 0,
        1 if annotation.get("CANONICAL") == "YES" else 0,
        impact_scores.get(annotation.get("IMPACT", ""), 0),
        1 if annotation.get("BIOTYPE") == "protein_coding" else 0,
    )


def choose_best_annotation(
    csq_text: str,
    csq_fields: list[str],
) -> dict[str, str]:
    """Choose one preferred VEP transcript annotation."""

    annotations = []

    for transcript_text in csq_text.split(","):
        values = transcript_text.split("|")

        if len(values) < len(csq_fields):
            values.extend([""] * (len(csq_fields) - len(values)))

        annotation = dict(zip(csq_fields, values))
        annotations.append(annotation)

    if not annotations:
        return {}

    return max(annotations, key=annotation_priority)


def genotype_to_zygosity(genotype: str) -> str:
    """Convert a VCF genotype into a readable zygosity label."""

    if genotype in {"", ".", "./.", ".|."}:
        return "missing"

    alleles = re.split(r"[/|]", genotype)

    if not alleles or any(allele == "." for allele in alleles):
        return "partial_or_missing"

    if len(alleles) == 1:
        if alleles[0] == "0":
            return "haploid_reference"
        return "hemizygous_or_haploid_alt"

    if all(allele == "0" for allele in alleles):
        return "homozygous_reference"

    if len(set(alleles)) == 1 and alleles[0] != "0":
        return "homozygous_alt"

    if "0" in alleles:
        return "heterozygous"

    return "multiallelic_alt"


def genotype_is_phased(genotype: str) -> str:
    """Report whether GT is explicitly phased with a vertical bar."""

    value = str(genotype or "").strip()

    if value in {"", ".", ".|."}:
        return "no"

    return "yes" if "|" in value else "no"


def parse_sample_data(
    format_text: str,
    sample_text: str,
) -> dict[str, str]:
    """Parse one VCF FORMAT/sample cell."""

    if not format_text or format_text == ".":
        return {}

    format_keys = format_text.split(":")
    sample_values = sample_text.split(":")

    if len(sample_values) < len(format_keys):
        sample_values.extend(
            [""] * (len(format_keys) - len(sample_values))
        )

    return dict(zip(format_keys, sample_values))


def safe_integer(value: str):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def calculate_allele_balance(
    genotype: str,
    ad_text: str,
) -> str:
    """
    Calculate alternate-read fraction from FORMAT/AD.

    For a normal biallelic record:
        AD = reference_depth,alternate_depth
    """

    if not ad_text or ad_text in {".", ""}:
        return ""

    try:
        depths = [
            int(value)
            for value in ad_text.split(",")
        ]
    except ValueError:
        return ""

    if len(depths) < 2:
        return ""

    total_depth = sum(depths)

    if total_depth <= 0:
        return ""

    genotype_alleles = [
        allele
        for allele in re.split(r"[/|]", genotype)
        if allele not in {"", ".", "0"}
    ]

    alternate_indices = set()

    for allele in genotype_alleles:
        try:
            index = int(allele)
        except ValueError:
            continue

        if 0 < index < len(depths):
            alternate_indices.add(index)

    if not alternate_indices:
        alternate_indices = {1}

    alternate_depth = sum(
        depths[index]
        for index in alternate_indices
    )

    return f"{alternate_depth / total_depth:.4f}"


def genotype_quality_assessment(
    genotype: str,
    zygosity: str,
    dp_text: str,
    gq_text: str,
    ad_text: str,
    allele_balance_text: str,
) -> tuple[str, str]:
    """
    Perform transparent basic technical QC.

    These thresholds are screening flags, not clinical
    laboratory validation criteria.
    """

    if genotype in {"", ".", "./.", ".|."}:
        return (
            "not_evaluable",
            "genotype_missing",
        )

    if zygosity == "homozygous_reference":
        return (
            "review",
            "reference_genotype_present_in_candidate_VCF",
        )

    dp = safe_integer(dp_text)
    gq = safe_integer(gq_text)

    try:
        allele_balance = float(allele_balance_text)
    except (TypeError, ValueError):
        allele_balance = None

    problems = []
    incomplete = []

    if dp is None:
        incomplete.append("DP_missing")
    elif dp < 10:
        problems.append("DP_below_10")

    if gq is None:
        incomplete.append("GQ_missing")
    elif gq < 20:
        problems.append("GQ_below_20")

    if not ad_text or ad_text == ".":
        incomplete.append("AD_missing")

    if zygosity == "heterozygous":
        if allele_balance is None:
            incomplete.append(
                "heterozygous_allele_balance_unavailable"
            )
        elif not 0.20 <= allele_balance <= 0.80:
            problems.append(
                "heterozygous_allele_balance_outside_0.20_to_0.80"
            )

    elif zygosity == "homozygous_alt":
        if allele_balance is None:
            incomplete.append(
                "homozygous_alt_allele_balance_unavailable"
            )
        elif allele_balance < 0.80:
            problems.append(
                "homozygous_alt_allele_balance_below_0.80"
            )

    elif zygosity in {
        "multiallelic_alt",
        "partial_or_missing",
    }:
        problems.append(
            "complex_genotype_requires_manual_review"
        )

    notes = problems + incomplete

    if problems:
        return (
            "review_low_quality_or_complex",
            ";".join(notes),
        )

    if incomplete:
        return (
            "review_incomplete_quality_fields",
            ";".join(notes),
        )

    return (
        "pass_basic_qc",
        "GT_DP_GQ_AD_consistent_with_basic_thresholds",
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python3 "
            "pipeline/case_workflow/03_extract_vep_table.py CASE_ID"
        )
        sys.exit(1)

    case_id = sys.argv[1]

    script_path = Path(__file__).resolve()
    project_root = script_path.parents[2]

    input_vcf = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "annotated"
        / f"{case_id}.vep.vcf.gz"
    )

    output_table = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "annotated"
        / f"{case_id}.vep_best_transcripts.tsv"
    )

    qc_file = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
        / f"{case_id}.vep_table_qc.tsv"
    )

    if not input_vcf.is_file():
        print(f"ERROR: VEP VCF not found: {input_vcf}")
        sys.exit(1)

    output_table.parent.mkdir(parents=True, exist_ok=True)
    qc_file.parent.mkdir(parents=True, exist_ok=True)

    csq_fields: list[str] = []
    sample_names: list[str] = []
    output_rows: list[dict[str, str]] = []
    variant_count = 0

    with open_text(input_vcf) as handle:
        for line in handle:
            if line.startswith("##INFO=<ID=CSQ"):
                match = re.search(r"Format: ([^\">]+)", line)

                if match:
                    csq_fields = match.group(1).split("|")

                continue

            if line.startswith("#CHROM"):
                header_columns = line.rstrip("\n").split("\t")
                sample_names = header_columns[9:]
                continue

            if line.startswith("#"):
                continue

            if not csq_fields:
                print("ERROR: The VEP CSQ header format was not detected.")
                sys.exit(1)

            fields = line.rstrip("\n").split("\t")

            if len(fields) < 8:
                continue

            variant_count += 1

            chrom = fields[0]
            pos = fields[1]
            vcf_id = fields[2]
            ref = fields[3]
            alt = fields[4]
            info = parse_info(fields[7])

            csq_text = info.get("CSQ", "")
            best = choose_best_annotation(csq_text, csq_fields)

            variant_name = f"{chrom}:{pos}:{ref}>{alt}"

            common_row = {
                "case_id": case_id,
                "variant": variant_name,
                "chrom": chrom,
                "pos": pos,
                "vcf_id": vcf_id,
                "ref": ref,
                "alt": alt,
                "gene": best.get("SYMBOL", ""),
                "ensembl_gene": best.get("Gene", ""),
                "transcript": best.get("Feature", ""),
                "mane_select": best.get("MANE_SELECT", ""),
                "canonical": best.get("CANONICAL", ""),
                "pick": best.get("PICK", ""),
                "biotype": best.get("BIOTYPE", ""),
                "consequence": best.get("Consequence", ""),
                "impact": best.get("IMPACT", ""),
                "hgvsc": decode_vep(best.get("HGVSc", "")),
                "hgvsp": decode_vep(best.get("HGVSp", "")),
                "existing_variation": best.get("Existing_variation", ""),
                "gnomad_exome_af": best.get("gnomADe_AF", ""),
                "gnomad_genome_af": best.get("gnomADg_AF", ""),
                "max_af": best.get("MAX_AF", ""),
            }

            format_text = fields[8] if len(fields) > 8 else "."

            if sample_names:
                for index, sample_name in enumerate(sample_names):
                    sample_column_index = 9 + index
                    sample_text = (
                        fields[sample_column_index]
                        if sample_column_index < len(fields)
                        else "."
                    )

                    sample_data = parse_sample_data(
                        format_text,
                        sample_text,
                    )

                    genotype = sample_data.get("GT", ".")
                    zygosity = genotype_to_zygosity(genotype)

                    dp = sample_data.get("DP", "")
                    gq = sample_data.get("GQ", "")
                    ad = sample_data.get("AD", "")
                    phase_set = sample_data.get("PS", "")
                    phase_id = sample_data.get("PID", "")
                    phased_genotype = sample_data.get("PGT", "")
                    phased_status = genotype_is_phased(genotype)

                    allele_balance = calculate_allele_balance(
                        genotype,
                        ad,
                    )

                    (
                        genotype_quality_status,
                        genotype_quality_notes,
                    ) = genotype_quality_assessment(
                        genotype,
                        zygosity,
                        dp,
                        gq,
                        ad,
                        allele_balance,
                    )

                    row = common_row.copy()
                    row["sample"] = sample_name
                    row["genotype"] = genotype
                    row["zygosity"] = zygosity
                    row["phase_set_PS"] = phase_set
                    row["phase_id_PID"] = phase_id
                    row["phased_genotype_PGT"] = phased_genotype
                    row["genotype_is_phased"] = phased_status
                    row["depth_DP"] = dp
                    row["genotype_quality_GQ"] = gq
                    row["allelic_depth_AD"] = ad
                    row["allele_balance"] = allele_balance
                    row["genotype_quality_status"] = (
                        genotype_quality_status
                    )
                    row["genotype_quality_notes"] = (
                        genotype_quality_notes
                    )
                    output_rows.append(row)

            else:
                row = common_row.copy()
                row["sample"] = "."
                row["genotype"] = "."
                row["zygosity"] = "unknown"
                row["phase_set_PS"] = ""
                row["phase_id_PID"] = ""
                row["phased_genotype_PGT"] = ""
                row["genotype_is_phased"] = "no"
                row["depth_DP"] = ""
                row["genotype_quality_GQ"] = ""
                row["allelic_depth_AD"] = ""
                row["allele_balance"] = ""
                row["genotype_quality_status"] = (
                    "not_applicable_site_only"
                )
                row["genotype_quality_notes"] = (
                    "no_sample_column"
                )
                output_rows.append(row)

    if not csq_fields:
        print("ERROR: No CSQ field definition was found.")
        sys.exit(1)

    output_columns = [
        "case_id",
        "sample",
        "variant",
        "chrom",
        "pos",
        "vcf_id",
        "ref",
        "alt",
        "genotype",
        "zygosity",
        "phase_set_PS",
        "phase_id_PID",
        "phased_genotype_PGT",
        "genotype_is_phased",
        "depth_DP",
        "genotype_quality_GQ",
        "allelic_depth_AD",
        "allele_balance",
        "genotype_quality_status",
        "genotype_quality_notes",
        "gene",
        "ensembl_gene",
        "transcript",
        "mane_select",
        "canonical",
        "pick",
        "biotype",
        "consequence",
        "impact",
        "hgvsc",
        "hgvsp",
        "existing_variation",
        "gnomad_exome_af",
        "gnomad_genome_af",
        "max_af",
    ]

    with output_table.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=output_columns,
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(output_rows)

    genes = {
        row["gene"]
        for row in output_rows
        if row.get("gene")
    }

    rows_with_genotype = sum(
        row.get("genotype") not in {
            "",
            ".",
            "./.",
            ".|.",
        }
        for row in output_rows
    )

    rows_with_phased_genotype = sum(
        row.get("genotype_is_phased") == "yes"
        for row in output_rows
    )

    rows_passing_basic_genotype_qc = sum(
        row.get("genotype_quality_status")
        == "pass_basic_qc"
        for row in output_rows
    )

    rows_requiring_genotype_review = sum(
        row.get("genotype_quality_status", "").startswith(
            "review"
        )
        for row in output_rows
    )

    with qc_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerow(["case_id", case_id])
        writer.writerow(["input_vcf_records", variant_count])
        writer.writerow(["output_table_rows", len(output_rows)])
        writer.writerow(["sample_count", len(sample_names)])
        writer.writerow(
            ["rows_with_called_genotype", rows_with_genotype]
        )
        writer.writerow(
            ["rows_with_phased_genotype", rows_with_phased_genotype]
        )
        writer.writerow(
            [
                "rows_passing_basic_genotype_qc",
                rows_passing_basic_genotype_qc,
            ]
        )
        writer.writerow(
            [
                "rows_requiring_genotype_review",
                rows_requiring_genotype_review,
            ]
        )
        writer.writerow(["unique_gene_symbols", len(genes)])
        writer.writerow(
            [
                "output_table",
                str(output_table.relative_to(project_root)),
            ]
        )

    print("========================================")
    print("VEP TABLE EXTRACTION")
    print("========================================")
    print(f"Case ID:              {case_id}")
    print(f"VCF records:          {variant_count}")
    print(f"Output table rows:    {len(output_rows)}")
    print(f"Samples:              {len(sample_names)}")
    print(f"Rows with genotype:   {rows_with_genotype}")
    print(f"Rows with phased GT:  {rows_with_phased_genotype}")
    print(
        "Rows passing GT QC:   "
        f"{rows_passing_basic_genotype_qc}"
    )
    print(
        "Rows needing review:  "
        f"{rows_requiring_genotype_review}"
    )
    print(f"Unique gene symbols:  {len(genes)}")
    print()
    print(f"Output table: {output_table}")
    print(f"QC table:     {qc_file}")
    print()
    print("VEP TABLE EXTRACTION COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()

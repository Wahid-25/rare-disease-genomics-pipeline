#!/usr/bin/env python3

import gzip
import hashlib
import re
import sys
from pathlib import Path


HPO_PATTERN = re.compile(r"\bHP:\d{7}\b", re.IGNORECASE)

SUPPORTED_CHROMOSOMES = {
    *(str(number) for number in range(1, 23)),
    "X",
    "Y",
    "M",
    "MT",
}

PRIVACY_PATTERNS = {
    "sample_metadata": re.compile(
        r"^##(?:SAMPLE|PEDIGREE|Individual|Patient)=",
        re.IGNORECASE,
    ),
    "medical_identifier": re.compile(
        r"\b(?:MRN|medical.record|patient.id|subject.id)\b",
        re.IGNORECASE,
    ),
    "date_of_birth": re.compile(
        r"\b(?:DOB|date.of.birth|birth.date)\b",
        re.IGNORECASE,
    ),
    "email_address": re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    ),
}


def clean(value) -> str:
    return str(value).strip() if value is not None else ""


def open_text(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")

    return path.open("r", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


def parse_info(value: str) -> dict[str, str]:
    result = {}

    if value in {"", "."}:
        return result

    for item in value.split(";"):
        if "=" in item:
            key, item_value = item.split("=", 1)
            result[key] = item_value
        else:
            result[item] = "true"

    return result


def normalize_chromosome(chromosome: str) -> str:
    chromosome = clean(chromosome)

    if chromosome.lower().startswith("chr"):
        chromosome = chromosome[3:]

    return chromosome.upper()


def genotype_has_alt(genotype: str) -> bool:
    genotype = clean(genotype).replace("|", "/")

    if genotype in {"", ".", "./."}:
        return False

    alleles = genotype.split("/")

    return any(
        allele not in {"", ".", "0"}
        for allele in alleles
    )


def detect_reference_status(reference_headers: list[str]) -> str:
    combined = " ".join(reference_headers).lower()

    if "grch37" in combined or "hg19" in combined:
        return "wrong_build_GRCh37_or_hg19"

    if "grch38" in combined or "hg38" in combined:
        return "GRCh38_confirmed"

    return "not_declared"


def load_hpo_file(path: Path) -> tuple[set[str], list[str]]:
    terms = set()
    unrecognized_lines = []

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            found = {
                term.upper()
                for term in HPO_PATTERN.findall(line)
            }

            if found:
                terms.update(found)
            else:
                unrecognized_lines.append(
                    f"line_{line_number}"
                )

    return terms, unrecognized_lines


def add_issue(
    collection: list[str],
    message: str,
) -> None:
    if message not in collection:
        collection.append(message)


def main() -> None:
    if len(sys.argv) != 4:
        print(
            "Usage:\n"
            "python3 "
            "pipeline/case_workflow/"
            "15_check_real_patient_readiness.py "
            "CASE_ID INPUT_VCF PHENOTYPE_FILE"
        )
        sys.exit(1)

    case_id = sys.argv[1]
    vcf_path = Path(sys.argv[2]).expanduser().resolve()
    phenotype_path = Path(sys.argv[3]).expanduser().resolve()

    project_root = Path(__file__).resolve().parents[2]

    output_directory = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
    )

    output_directory.mkdir(parents=True, exist_ok=True)

    report_path = (
        output_directory
        / f"{case_id}.real_patient_readiness.tsv"
    )

    errors = []
    warnings = []

    if not vcf_path.is_file():
        raise SystemExit(f"ERROR: VCF not found: {vcf_path}")

    if not phenotype_path.is_file():
        raise SystemExit(
            f"ERROR: Phenotype file not found: {phenotype_path}"
        )

    if not (
        vcf_path.name.endswith(".vcf")
        or vcf_path.name.endswith(".vcf.gz")
    ):
        add_issue(
            errors,
            "Input filename must end with .vcf or .vcf.gz.",
        )

    reference_headers = []
    contig_headers = []
    privacy_flags = set()
    sample_names = []

    total_records = 0
    valid_records = 0
    malformed_records = 0

    small_variant_records = 0
    supported_cnv_records = 0
    other_sv_records = 0
    del_dup_missing_end = 0
    multiallelic_records = 0

    chr_prefixed_records = 0
    non_chr_prefixed_records = 0
    primary_chromosome_records = 0
    alternate_contig_records = 0

    records_with_gt_format = 0
    records_with_nonreference_genotype = 0
    genotype_cells = 0
    missing_genotype_cells = 0

    chrom_header_found = False

    try:
        with open_text(vcf_path) as handle:
            for line_number, line in enumerate(
                handle,
                start=1,
            ):
                line = line.rstrip("\n")

                if line.startswith("##reference="):
                    reference_headers.append(line)

                if line.startswith("##contig="):
                    contig_headers.append(line)

                if line.startswith("##"):
                    for flag_name, pattern in (
                        PRIVACY_PATTERNS.items()
                    ):
                        if pattern.search(line):
                            privacy_flags.add(flag_name)

                    continue

                if line.startswith("#CHROM"):
                    chrom_header_found = True
                    header = line.split("\t")
                    sample_names = header[9:]
                    continue

                if line.startswith("#"):
                    continue

                total_records += 1
                fields = line.split("\t")

                if len(fields) < 8:
                    malformed_records += 1
                    continue

                valid_records += 1

                chrom = clean(fields[0])
                alt = clean(fields[4])
                info = parse_info(fields[7])

                if chrom.lower().startswith("chr"):
                    chr_prefixed_records += 1
                else:
                    non_chr_prefixed_records += 1

                normalized_chrom = normalize_chromosome(chrom)

                if normalized_chrom in SUPPORTED_CHROMOSOMES:
                    primary_chromosome_records += 1
                else:
                    alternate_contig_records += 1

                if "," in alt:
                    multiallelic_records += 1

                svtype = clean(
                    info.get("SVTYPE", "")
                ).upper()

                symbolic_alt_match = re.fullmatch(
                    r"<([^>]+)>",
                    alt,
                )

                if not svtype and symbolic_alt_match:
                    svtype = symbolic_alt_match.group(1).upper()

                is_symbolic = bool(symbolic_alt_match)

                if svtype in {"DEL", "DUP"}:
                    if clean(info.get("END")):
                        supported_cnv_records += 1
                    else:
                        del_dup_missing_end += 1
                        other_sv_records += 1

                elif svtype or is_symbolic:
                    other_sv_records += 1

                else:
                    small_variant_records += 1

                if len(fields) >= 9:
                    format_fields = fields[8].split(":")

                    try:
                        gt_index = format_fields.index("GT")
                    except ValueError:
                        gt_index = None

                    if gt_index is not None:
                        records_with_gt_format += 1

                        record_has_alt = False

                        for sample_value in fields[9:]:
                            genotype_cells += 1
                            sample_fields = sample_value.split(":")

                            genotype = (
                                sample_fields[gt_index]
                                if gt_index < len(sample_fields)
                                else ""
                            )

                            if genotype in {"", ".", "./.", ".|."}:
                                missing_genotype_cells += 1

                            if genotype_has_alt(genotype):
                                record_has_alt = True

                        if record_has_alt:
                            records_with_nonreference_genotype += 1

    except (OSError, UnicodeError, gzip.BadGzipFile) as error:
        add_issue(
            errors,
            f"VCF could not be read: {error}",
        )

    reference_status = detect_reference_status(
        reference_headers
    )

    hpo_terms, unrecognized_hpo_lines = load_hpo_file(
        phenotype_path
    )

    compressed = vcf_path.name.endswith(".gz")
    index_found = False
    index_type = ""

    if compressed:
        tbi_path = Path(str(vcf_path) + ".tbi")
        csi_path = Path(str(vcf_path) + ".csi")

        if tbi_path.is_file():
            index_found = True
            index_type = "tbi"
        elif csi_path.is_file():
            index_found = True
            index_type = "csi"

    # --------------------------------------------------
    # Determine readiness problems
    # --------------------------------------------------

    if not chrom_header_found:
        add_issue(
            errors,
            "VCF #CHROM header was not found.",
        )

    if total_records == 0:
        add_issue(
            errors,
            "VCF contains no variant records.",
        )

    if malformed_records > 0:
        add_issue(
            errors,
            f"{malformed_records} malformed VCF records were found.",
        )

    if len(sample_names) == 0:
        add_issue(
            warnings,
            "VCF contains no patient sample column; "
            "processing is limited to site-annotation mode.",
        )

    if len(sample_names) > 1:
        add_issue(
            errors,
            "Current disease-scoring workflow expects one patient "
            "sample, but the VCF contains multiple samples.",
        )

    if reference_status == "wrong_build_GRCh37_or_hg19":
        add_issue(
            errors,
            "VCF declares GRCh37/hg19; the pipeline requires GRCh38.",
        )

    if reference_status == "not_declared":
        add_issue(
            warnings,
            "Genome build is not declared in the VCF header; "
            "GRCh38 must be confirmed independently.",
        )

    if chr_prefixed_records > 0 and non_chr_prefixed_records > 0:
        add_issue(
            errors,
            "Mixed chromosome naming was detected.",
        )
    elif (
        non_chr_prefixed_records > 0
        and chr_prefixed_records == 0
    ):
        add_issue(
            errors,
            "Chromosomes lack the required chr prefix.",
        )

    if records_with_gt_format == 0 and sample_names:
        add_issue(
            warnings,
            "No GT genotype fields were detected; "
            "genotype-dependent interpretation is unavailable.",
        )

    if (
        sample_names
        and records_with_nonreference_genotype == 0
    ):
        add_issue(
            warnings,
            "No usable non-reference patient genotypes were detected; "
            "the listed variants will be processed in annotation-only mode.",
        )

    if len(hpo_terms) == 0:
        add_issue(
            errors,
            "No valid HP:####### phenotype terms were found.",
        )

    if del_dup_missing_end > 0:
        add_issue(
            errors,
            f"{del_dup_missing_end} DEL/DUP records lack INFO/END.",
        )

    if (
        small_variant_records == 0
        and supported_cnv_records == 0
    ):
        add_issue(
            errors,
            "No supported small variants or DEL/DUP CNVs "
            "were detected.",
        )

    if multiallelic_records > 0:
        add_issue(
            warnings,
            f"{multiallelic_records} multiallelic records will "
            "be split during normalization.",
        )

    if alternate_contig_records > 0:
        add_issue(
            warnings,
            f"{alternate_contig_records} records occur on alternate "
            "or non-primary contigs.",
        )

    if compressed and not index_found:
        add_issue(
            warnings,
            "Compressed VCF has no adjacent .tbi or .csi index.",
        )

    if privacy_flags:
        add_issue(
            warnings,
            "Potentially identifying metadata categories were "
            "detected in VCF headers.",
        )

    if unrecognized_hpo_lines:
        add_issue(
            warnings,
            f"{len(unrecognized_hpo_lines)} non-comment phenotype "
            "lines contained no recognizable HPO ID.",
        )

    if genotype_cells > 0 and missing_genotype_cells > 0:
        missing_percent = (
            missing_genotype_cells / genotype_cells
        ) * 100

        if missing_percent >= 20:
            add_issue(
                warnings,
                f"{missing_percent:.1f}% of genotype cells are missing.",
            )

    # Determine the safe interpretation mode.

    if len(sample_names) == 0:
        analysis_mode = "site_annotation"
        genotype_available = "no"
        inheritance_evaluated = "no"
        patient_variant_interpretation_allowed = "no"
        confidence_level = "site_only_contextual"

    elif records_with_nonreference_genotype > 0:
        analysis_mode = "genotype_aware"
        genotype_available = "yes"
        inheritance_evaluated = "yes"
        patient_variant_interpretation_allowed = "yes"
        confidence_level = "standard"

    else:
        analysis_mode = "annotation_only"
        genotype_available = "no"
        inheritance_evaluated = "no"
        patient_variant_interpretation_allowed = "conditional"
        confidence_level = "reduced"

    # Manual privacy review is always needed because automatic
    # detection cannot reliably identify every personal identifier.

    if errors:
        readiness_status = "NOT_READY"
    elif warnings:
        readiness_status = "READY_WITH_WARNINGS"
    else:
        readiness_status = "READY"

    metrics = [
        ("case_id", case_id),
        ("readiness_status", readiness_status),
        ("analysis_mode", analysis_mode),
        ("genotype_available", genotype_available),
        ("inheritance_evaluated", inheritance_evaluated),
        (
            "patient_variant_interpretation_allowed",
            patient_variant_interpretation_allowed,
        ),
        ("confidence_level", confidence_level),
        ("input_vcf", str(vcf_path)),
        ("input_vcf_sha256", sha256_file(vcf_path)),
        ("input_vcf_size_bytes", vcf_path.stat().st_size),
        ("phenotype_file", str(phenotype_path)),
        ("phenotype_sha256", sha256_file(phenotype_path)),
        ("reference_status", reference_status),
        ("reference_header_count", len(reference_headers)),
        ("contig_header_count", len(contig_headers)),
        ("sample_count", len(sample_names)),
        ("manual_sample_label_review_required", "yes"),
        ("total_records", total_records),
        ("valid_records", valid_records),
        ("malformed_records", malformed_records),
        ("small_variant_records", small_variant_records),
        ("supported_DEL_DUP_records", supported_cnv_records),
        ("other_structural_variant_records", other_sv_records),
        ("DEL_DUP_missing_END", del_dup_missing_end),
        ("multiallelic_records", multiallelic_records),
        ("chr_prefixed_records", chr_prefixed_records),
        ("non_chr_prefixed_records", non_chr_prefixed_records),
        ("primary_chromosome_records", primary_chromosome_records),
        ("alternate_contig_records", alternate_contig_records),
        ("records_with_GT", records_with_gt_format),
        (
            "records_with_nonreference_genotype",
            records_with_nonreference_genotype,
        ),
        ("genotype_cells", genotype_cells),
        ("missing_genotype_cells", missing_genotype_cells),
        ("valid_patient_HPO_terms", len(hpo_terms)),
        ("unrecognized_phenotype_lines", len(unrecognized_hpo_lines)),
        ("compressed_vcf", "yes" if compressed else "no"),
        ("index_found", "yes" if index_found else "no"),
        ("index_type", index_type),
        (
            "potential_privacy_header_categories",
            ";".join(sorted(privacy_flags)),
        ),
        ("manual_privacy_review_required", "yes"),
        ("error_count", len(errors)),
        ("warning_count", len(warnings)),
    ]

    with report_path.open("w", encoding="utf-8") as handle:
        handle.write("metric\tvalue\n")

        for metric, value in metrics:
            handle.write(f"{metric}\t{value}\n")

        for index, message in enumerate(errors, start=1):
            handle.write(f"error_{index}\t{message}\n")

        for index, message in enumerate(warnings, start=1):
            handle.write(f"warning_{index}\t{message}\n")

    print("========================================")
    print("REAL-PATIENT INPUT READINESS CHECK")
    print("========================================")
    print(f"Case ID:                 {case_id}")
    print(f"Status:                  {readiness_status}")
    print(f"Analysis mode:           {analysis_mode}")
    print(f"Genotype available:      {genotype_available}")
    print(f"Inheritance evaluated:   {inheritance_evaluated}")
    print(f"Confidence level:        {confidence_level}")
    print(f"Reference:               {reference_status}")
    print(f"Samples:                 {len(sample_names)}")
    print(f"Total records:           {total_records}")
    print(f"Small variants:          {small_variant_records}")
    print(f"DEL/DUP CNVs:            {supported_cnv_records}")
    print(f"Other SVs:               {other_sv_records}")
    print(f"Records with GT:         {records_with_gt_format}")
    print(
        "Non-reference records:   "
        f"{records_with_nonreference_genotype}"
    )
    print(f"Patient HPO terms:       {len(hpo_terms)}")
    print(f"Errors:                  {len(errors)}")
    print(f"Warnings:                {len(warnings)}")
    print()
    print(f"Report: {report_path}")

    if errors:
        print()
        print("Blocking problems:")

        for message in errors:
            print(f"- {message}")

    if warnings:
        print()
        print("Warnings:")

        for message in warnings:
            print(f"- {message}")

    print()
    print(
        "Automatic checks cannot guarantee de-identification. "
        "A manual privacy review is still required."
    )

    if errors:
        sys.exit(2)


if __name__ == "__main__":
    main()

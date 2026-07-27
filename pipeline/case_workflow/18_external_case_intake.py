#!/usr/bin/env python3

import gzip
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path


GRCH38_CHR1_LENGTH = 248_956_422
GRCH37_CHR1_LENGTH = 249_250_621

PRIMARY_CHROMOSOMES = {
    *(str(number) for number in range(1, 23)),
    "X",
    "Y",
    "M",
    "MT",
}

KNOWN_ANNOTATION_TAGS = {
    "CSQ",
    "ANN",
    "CLNSIG",
    "CLNDN",
    "CLNREVSTAT",
    "CLNDISDB",
    "CADD",
    "SpliceAI",
    "CLINGEN_REGION",
    "CLINGEN_HAPLO",
    "CLINGEN_TRIPLO",
    "GNOMADAF",
    "GNOMADAF_popmax",
    "most_severe_consequence",
    "most_severe_pli",
    "Annotation",
    "GeneticModels",
    "ModelScore",
    "Compounds",
}

PIPELINE_CONFLICTING_TAGS = {
    "CSQ",
    "ANN",
    "CLNSIG",
    "CLNDN",
    "CLNREVSTAT",
    "CLNDISDB",
    "SpliceAI",
    "CLINGEN_REGION",
    "CLINGEN_HAPLO",
    "CLINGEN_TRIPLO",
}

ACCESSION_PATTERN = re.compile(
    r"\b(?:SRR|ERR|DRR)\d+\b",
    re.IGNORECASE,
)

META_ID_PATTERN = re.compile(
    r"^##(?:INFO|FORMAT)=<ID=([^,>]+)"
)

CONTIG_PATTERN = re.compile(
    r"^##contig=<ID=([^,>]+)(?:,length=(\d+))?",
    re.IGNORECASE,
)


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


def hash_name(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:16]


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


def normalize_chromosome(value: str) -> str:
    value = clean(value)

    if value.lower().startswith("chr"):
        value = value[3:]

    return value.upper()


def genotype_state(genotype: str) -> str:
    genotype = clean(genotype).replace("|", "/")

    if genotype in {"", ".", "./.", ".|."}:
        return "missing"

    alleles = genotype.split("/")

    called = [
        allele
        for allele in alleles
        if allele not in {"", "."}
    ]

    if not called:
        return "missing"

    if all(allele == "0" for allele in called):
        return "reference"

    if any(allele != "0" for allele in called):
        return "alternate"

    return "unresolved"


def detect_build(
    reference_headers: list[str],
    contig_lengths: dict[str, int],
) -> tuple[str, str]:
    reference_text = " ".join(
        reference_headers
    ).lower()

    if (
        "grch38" in reference_text
        or "hg38" in reference_text
        or "gcf_000001405.39" in reference_text
    ):
        return (
            "GRCh38",
            "declared_in_reference_header",
        )

    if (
        "grch37" in reference_text
        or "hg19" in reference_text
        or "gcf_000001405.25" in reference_text
    ):
        return (
            "GRCh37",
            "declared_in_reference_header",
        )

    chr1_length = (
        contig_lengths.get("chr1")
        or contig_lengths.get("1")
    )

    if chr1_length == GRCH38_CHR1_LENGTH:
        return (
            "GRCh38",
            "inferred_from_chr1_contig_length",
        )

    if chr1_length == GRCH37_CHR1_LENGTH:
        return (
            "GRCh37",
            "inferred_from_chr1_contig_length",
        )

    return (
        "unknown",
        "not_determined",
    )


def classify_non_symbolic_variant(
    reference: str,
    alternate_alleles: list[str],
) -> str:
    valid_alts = [
        allele
        for allele in alternate_alleles
        if allele not in {"", ".", "*"}
    ]

    if not valid_alts:
        return "unresolved"

    if (
        len(reference) == 1
        and all(len(allele) == 1 for allele in valid_alts)
    ):
        return "snv"

    if any(
        len(reference) != len(allele)
        for allele in valid_alts
    ):
        return "indel"

    return "mnv_or_complex"


def determine_intake_status(
    genome_build: str,
    total_records: int,
    inconsistent_sample_column_records: int,
    sample_count: int,
    genotype_alt_cells: int,
    genotype_called_cells: int,
    conflicting_tags: set[str],
) -> tuple[str, str, str]:
    """
    Classify a VCF without assuming that patient genotypes must exist.

    The intake stage decides whether the file can enter:
    - genotype-aware patient analysis;
    - annotation-only patient analysis;
    - site-only annotation;
    - a preparation or correction stage.
    """

    if total_records == 0:
        return (
            "NOT_READY_EMPTY_VCF",
            "no",
            "The VCF contains no variant records.",
        )

    if inconsistent_sample_column_records > 0:
        return (
            "NOT_READY_INCONSISTENT_SAMPLE_COLUMNS",
            "no",
            "Reject before preparation: one or more records do not contain the columns declared by the #CHROM header.",
        )

    if genome_build == "GRCh37":
        return (
            "NOT_READY_WRONG_GENOME_BUILD",
            "no",
            "Use a GRCh38 VCF or a separately validated liftover workflow.",
        )

    if genome_build == "unknown":
        return (
            "NEEDS_GENOME_BUILD_CONFIRMATION",
            "conditional",
            "Confirm the genome build before preparation or annotation.",
        )

    if sample_count == 0:
        return (
            "SITE_ANNOTATION_NO_SAMPLE",
            "yes",
            "Run site-only annotation. Patient genotype, zygosity and inheritance conclusions must remain unavailable.",
        )

    if sample_count > 1:
        if genotype_alt_cells > 0:
            return (
                "NEEDS_EXPLICIT_SAMPLE_SELECTION",
                "conditional",
                "Select the patient sample before genotype-aware analysis.",
            )

        return (
            "NEEDS_EXPLICIT_SAMPLE_SELECTION_ANNOTATION_ONLY",
            "conditional",
            "Select one sample before annotation-only patient processing.",
        )

    if genotype_called_cells == 0 or genotype_alt_cells == 0:
        return (
            "ANNOTATION_ONLY_NO_USABLE_GENOTYPES",
            "yes",
            "Annotate and phenotype-rank all listed variants, but disable genotype-dependent inheritance scoring.",
        )

    if conflicting_tags:
        return (
            "READY_AFTER_EXISTING_ANNOTATION_CLEANUP",
            "yes",
            "Remove conflicting existing annotations before independent re-annotation.",
        )

    return (
        "READY_FOR_PREPARATION_AND_FULL_PIPELINE",
        "yes",
        "Run genotype-aware preparation and the complete pipeline.",
    )


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage:\n"
            "python3 "
            "pipeline/case_workflow/"
            "18_external_case_intake.py "
            "CASE_ID INPUT_VCF"
        )
        sys.exit(1)

    case_id = sys.argv[1]
    vcf_path = Path(
        sys.argv[2]
    ).expanduser().resolve()

    if not re.fullmatch(
        r"[A-Za-z0-9._-]+",
        case_id,
    ):
        raise SystemExit(
            "ERROR: Invalid CASE_ID."
        )

    if not vcf_path.is_file():
        raise SystemExit(
            f"ERROR: VCF not found: {vcf_path}"
        )

    project_root = Path(__file__).resolve().parents[2]

    output_directory = (
        project_root
        / "results"
        / "cases"
        / case_id
        / "final"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_file = (
        output_directory
        / f"{case_id}.external_vcf_intake.tsv"
    )

    reference_headers = []
    contig_lengths = {}
    declared_info_ids = set()
    declared_format_ids = set()

    sample_names = []
    sample_accessions = set()

    total_records = 0
    malformed_records = 0
    expected_column_count = None
    inconsistent_sample_column_records = 0
    pass_records = 0
    nonpass_records = 0

    snv_records = 0
    indel_records = 0
    mnv_complex_records = 0
    supported_del_dup_records = 0
    incomplete_del_dup_records = 0
    other_structural_variant_records = 0
    unresolved_variant_records = 0
    multiallelic_records = 0

    chr_prefixed_records = 0
    non_chr_prefixed_records = 0
    alternate_contig_records = 0

    records_with_gt_format = 0
    records_without_gt_format = 0

    genotype_cells_total = 0
    genotype_missing_cells = 0
    genotype_reference_cells = 0
    genotype_alternate_cells = 0
    genotype_unresolved_cells = 0

    undefined_format_keys = Counter()
    used_format_keys = Counter()
    used_info_keys = Counter()

    chrom_header_found = False
    fileformat_header_found = False

    try:
        with open_text(vcf_path) as handle:
            for line_number, line in enumerate(
                handle,
                start=1,
            ):
                line = line.rstrip("\n")

                if line.startswith("##fileformat="):
                    fileformat_header_found = True
                    continue

                if line.startswith("##reference="):
                    reference_headers.append(line)
                    continue

                if line.startswith("##contig="):
                    match = CONTIG_PATTERN.match(line)

                    if match:
                        contig_name = match.group(1)
                        length_text = match.group(2)

                        if length_text:
                            contig_lengths[contig_name] = int(
                                length_text
                            )

                    continue

                if line.startswith("##INFO=<ID="):
                    match = META_ID_PATTERN.match(line)

                    if match:
                        declared_info_ids.add(
                            match.group(1)
                        )

                    continue

                if line.startswith("##FORMAT=<ID="):
                    match = META_ID_PATTERN.match(line)

                    if match:
                        declared_format_ids.add(
                            match.group(1)
                        )

                    continue

                if line.startswith("#CHROM"):
                    chrom_header_found = True
                    fields = line.split("\t")
                    expected_column_count = len(fields)
                    sample_names = fields[9:]

                    for sample_name in sample_names:
                        sample_accessions.update(
                            accession.upper()
                            for accession in ACCESSION_PATTERN.findall(
                                sample_name
                            )
                        )

                    continue

                if line.startswith("#"):
                    continue

                total_records += 1
                fields = line.split("\t")

                if len(fields) < 8:
                    malformed_records += 1
                    continue

                if (
                    expected_column_count is not None
                    and len(fields) != expected_column_count
                ):
                    inconsistent_sample_column_records += 1
                    continue

                chrom = clean(fields[0])
                reference = clean(fields[3])
                alt_text = clean(fields[4])
                filter_value = clean(fields[6])
                info = parse_info(fields[7])

                for info_key in info:
                    used_info_keys[info_key] += 1

                if filter_value in {"PASS", "."}:
                    pass_records += 1
                else:
                    nonpass_records += 1

                if chrom.lower().startswith("chr"):
                    chr_prefixed_records += 1
                else:
                    non_chr_prefixed_records += 1

                normalized_chromosome = normalize_chromosome(
                    chrom
                )

                if (
                    normalized_chromosome
                    not in PRIMARY_CHROMOSOMES
                ):
                    alternate_contig_records += 1

                alternate_alleles = alt_text.split(",")

                if len(alternate_alleles) > 1:
                    multiallelic_records += 1

                svtype = clean(
                    info.get("SVTYPE", "")
                ).upper()

                symbolic_types = []

                for allele in alternate_alleles:
                    symbolic_match = re.fullmatch(
                        r"<([^>]+)>",
                        allele,
                    )

                    if symbolic_match:
                        symbolic_types.append(
                            symbolic_match.group(1).upper()
                        )
                    elif "[" in allele or "]" in allele:
                        symbolic_types.append("BND")

                detected_svtype = svtype

                if not detected_svtype and symbolic_types:
                    detected_svtype = symbolic_types[0]

                if detected_svtype in {"DEL", "DUP"}:
                    if (
                        clean(info.get("END"))
                        or clean(info.get("SVLEN"))
                    ):
                        supported_del_dup_records += 1
                    else:
                        incomplete_del_dup_records += 1

                elif detected_svtype or symbolic_types:
                    other_structural_variant_records += 1

                else:
                    variant_class = classify_non_symbolic_variant(
                        reference,
                        alternate_alleles,
                    )

                    if variant_class == "snv":
                        snv_records += 1

                    elif variant_class == "indel":
                        indel_records += 1

                    elif variant_class == "mnv_or_complex":
                        mnv_complex_records += 1

                    else:
                        unresolved_variant_records += 1

                if len(fields) >= 9:
                    format_keys = fields[8].split(":")

                    for format_key in format_keys:
                        used_format_keys[format_key] += 1

                        if (
                            format_key
                            and format_key != "."
                            and format_key
                            not in declared_format_ids
                        ):
                            undefined_format_keys[
                                format_key
                            ] += 1

                    try:
                        gt_index = format_keys.index("GT")
                    except ValueError:
                        gt_index = None

                    if gt_index is None:
                        records_without_gt_format += 1
                    else:
                        records_with_gt_format += 1

                        for sample_value in fields[9:]:
                            genotype_cells_total += 1
                            sample_fields = sample_value.split(":")

                            genotype = (
                                sample_fields[gt_index]
                                if gt_index < len(sample_fields)
                                else ""
                            )

                            state = genotype_state(genotype)

                            if state == "missing":
                                genotype_missing_cells += 1

                            elif state == "reference":
                                genotype_reference_cells += 1

                            elif state == "alternate":
                                genotype_alternate_cells += 1

                            else:
                                genotype_unresolved_cells += 1
                else:
                    records_without_gt_format += 1

    except (
        OSError,
        UnicodeError,
        gzip.BadGzipFile,
    ) as error:
        raise SystemExit(
            f"ERROR: VCF could not be read: {error}"
        )

    genome_build, build_detection_method = detect_build(
        reference_headers,
        contig_lengths,
    )

    if (
        chr_prefixed_records > 0
        and non_chr_prefixed_records == 0
    ):
        chromosome_naming = "chr_prefixed"

    elif (
        non_chr_prefixed_records > 0
        and chr_prefixed_records == 0
    ):
        chromosome_naming = "non_prefixed"

    elif (
        chr_prefixed_records > 0
        and non_chr_prefixed_records > 0
    ):
        chromosome_naming = "mixed"

    else:
        chromosome_naming = "not_determined"

    existing_annotations = (
        declared_info_ids & KNOWN_ANNOTATION_TAGS
    )

    conflicting_annotations = (
        declared_info_ids & PIPELINE_CONFLICTING_TAGS
    )

    sample_hashes = [
        hash_name(sample_name)
        for sample_name in sample_names
    ]

    intake_status, pipeline_processing_allowed, recommended_action = (
        determine_intake_status(
            genome_build=genome_build,
            total_records=total_records,
            inconsistent_sample_column_records=(
                inconsistent_sample_column_records
            ),
            sample_count=len(sample_names),
            genotype_alt_cells=genotype_alternate_cells,
            genotype_called_cells=(
                genotype_reference_cells
                + genotype_alternate_cells
            ),
            conflicting_tags=conflicting_annotations,
        )
    )

    if intake_status == "NOT_READY_INCONSISTENT_SAMPLE_COLUMNS":
        analysis_mode = "not_applicable"
        patient_variant_interpretation = "no"
        inheritance_evaluated = "no"

    elif intake_status == "SITE_ANNOTATION_NO_SAMPLE":
        analysis_mode = "site_annotation"
        patient_variant_interpretation = "no"
        inheritance_evaluated = "no"

    elif intake_status in {
        "ANNOTATION_ONLY_NO_USABLE_GENOTYPES",
        "NEEDS_EXPLICIT_SAMPLE_SELECTION_ANNOTATION_ONLY",
    }:
        analysis_mode = "annotation_only"
        patient_variant_interpretation = "yes"
        inheritance_evaluated = "no"

    else:
        analysis_mode = "genotype_aware"
        patient_variant_interpretation = "yes"
        inheritance_evaluated = (
            "yes"
            if genotype_alternate_cells > 0
            else "no"
        )

    genotype_available = (
        "yes"
        if (
            intake_status
            != "NOT_READY_INCONSISTENT_SAMPLE_COLUMNS"
            and genotype_alternate_cells > 0
        )
        else "no"
    )

    warnings = []

    if not fileformat_header_found:
        warnings.append(
            "VCF fileformat header is missing."
        )

    if not chrom_header_found:
        warnings.append(
            "VCF #CHROM header is missing."
        )

    if malformed_records:
        warnings.append(
            f"{malformed_records} malformed records were detected."
        )

    if inconsistent_sample_column_records:
        warnings.append(
            f"{inconsistent_sample_column_records} records do not match the column count declared by the #CHROM header."
        )

    if chromosome_naming == "non_prefixed":
        warnings.append(
            "Chromosome names require chr-prefix conversion."
        )

    if chromosome_naming == "mixed":
        warnings.append(
            "Mixed chromosome naming requires manual review."
        )

    if alternate_contig_records:
        warnings.append(
            f"{alternate_contig_records} records occur on alternate contigs."
        )

    if undefined_format_keys:
        warnings.append(
            "Undefined FORMAT keys were used: "
            + ",".join(sorted(undefined_format_keys))
        )

    if conflicting_annotations:
        warnings.append(
            "Existing annotations conflict with independent pipeline annotation."
        )

    compressed = vcf_path.name.endswith(".gz")

    tbi_file = Path(str(vcf_path) + ".tbi")
    csi_file = Path(str(vcf_path) + ".csi")

    index_found = tbi_file.is_file() or csi_file.is_file()

    if compressed and not index_found:
        warnings.append(
            "Compressed VCF has no adjacent TBI or CSI index."
        )

    report_rows = [
        ("case_id", case_id),
        ("intake_status", intake_status),
        ("analysis_mode", analysis_mode),
        (
            "pipeline_processing_allowed",
            pipeline_processing_allowed,
        ),
        (
            "patient_variant_interpretation_allowed",
            patient_variant_interpretation,
        ),
        ("genotype_available", genotype_available),
        ("inheritance_evaluated", inheritance_evaluated),
        ("recommended_action", recommended_action),
        ("input_vcf", str(vcf_path)),
        ("input_vcf_sha256", sha256_file(vcf_path)),
        ("input_size_bytes", vcf_path.stat().st_size),
        ("genome_build", genome_build),
        ("build_detection_method", build_detection_method),
        ("reference_header_count", len(reference_headers)),
        ("chromosome_naming", chromosome_naming),
        ("sample_count", len(sample_names)),
        (
            "sample_name_hashes",
            ";".join(sample_hashes),
        ),
        (
            "detected_public_run_accessions",
            ";".join(sorted(sample_accessions)),
        ),
        (
            "expected_columns_per_record",
            (
                expected_column_count
                if expected_column_count is not None
                else ""
            ),
        ),
        ("total_records", total_records),
        ("malformed_records", malformed_records),
        (
            "inconsistent_sample_column_records",
            inconsistent_sample_column_records,
        ),
        ("pass_or_unfiltered_records", pass_records),
        ("nonpass_records", nonpass_records),
        ("snv_records", snv_records),
        ("indel_records", indel_records),
        ("mnv_or_complex_records", mnv_complex_records),
        (
            "supported_DEL_DUP_records",
            supported_del_dup_records,
        ),
        (
            "incomplete_DEL_DUP_records",
            incomplete_del_dup_records,
        ),
        (
            "other_structural_variant_records",
            other_structural_variant_records,
        ),
        (
            "unresolved_variant_records",
            unresolved_variant_records,
        ),
        ("multiallelic_records", multiallelic_records),
        ("chr_prefixed_records", chr_prefixed_records),
        (
            "non_chr_prefixed_records",
            non_chr_prefixed_records,
        ),
        (
            "alternate_contig_records",
            alternate_contig_records,
        ),
        (
            "records_with_GT_format",
            records_with_gt_format,
        ),
        (
            "records_without_GT_format",
            records_without_gt_format,
        ),
        (
            "genotype_cells_total",
            genotype_cells_total,
        ),
        (
            "genotype_missing_cells",
            genotype_missing_cells,
        ),
        (
            "genotype_reference_cells",
            genotype_reference_cells,
        ),
        (
            "genotype_alternate_cells",
            genotype_alternate_cells,
        ),
        (
            "genotype_unresolved_cells",
            genotype_unresolved_cells,
        ),
        (
            "declared_INFO_tag_count",
            len(declared_info_ids),
        ),
        (
            "declared_FORMAT_tag_count",
            len(declared_format_ids),
        ),
        (
            "existing_annotation_tags",
            ";".join(sorted(existing_annotations)),
        ),
        (
            "pipeline_conflicting_annotation_tags",
            ";".join(sorted(conflicting_annotations)),
        ),
        (
            "undefined_FORMAT_keys",
            ";".join(sorted(undefined_format_keys)),
        ),
        (
            "compressed_vcf",
            "yes" if compressed else "no",
        ),
        (
            "index_found",
            "yes" if index_found else "no",
        ),
        (
            "preannotated_vcf",
            "yes" if existing_annotations else "no",
        ),
        (
            "usable_patient_genotypes",
            genotype_available,
        ),
        ("warning_count", len(warnings)),
    ]

    with report_file.open(
        "w",
        encoding="utf-8",
    ) as handle:
        handle.write("metric\tvalue\n")

        for metric, value in report_rows:
            handle.write(
                f"{metric}\t{value}\n"
            )

        for index, warning in enumerate(
            warnings,
            start=1,
        ):
            handle.write(
                f"warning_{index}\t{warning}\n"
            )

    print("========================================")
    print("UNIVERSAL EXTERNAL VCF INTAKE")
    print("========================================")
    print(f"Case ID:                {case_id}")
    print(f"Intake status:          {intake_status}")
    print(f"Genome build:           {genome_build}")
    print(
        "Build detection:        "
        f"{build_detection_method}"
    )
    print(f"Samples:                {len(sample_names)}")
    print(f"Total records:          {total_records}")
    print(
        "Column-mismatch records:"
        f" {inconsistent_sample_column_records}"
    )
    print(f"SNVs:                   {snv_records}")
    print(f"Indels:                 {indel_records}")
    print(
        "Supported DEL/DUP:      "
        f"{supported_del_dup_records}"
    )
    print(
        "Records with GT:        "
        f"{records_with_gt_format}"
    )
    print(
        "Alternate genotype cells:"
        f" {genotype_alternate_cells}"
    )
    print(
        "Existing annotations:   "
        + (
            ",".join(sorted(existing_annotations))
            if existing_annotations
            else "none"
        )
    )
    print(
        "Undefined FORMAT keys:  "
        + (
            ",".join(sorted(undefined_format_keys))
            if undefined_format_keys
            else "none"
        )
    )
    print(f"Analysis mode:          {analysis_mode}")
    print(
        "Pipeline processing:    "
        f"{pipeline_processing_allowed}"
    )
    print(
        "Genotype available:     "
        f"{genotype_available}"
    )
    print(
        "Inheritance evaluated:  "
        f"{inheritance_evaluated}"
    )
    print()
    print(f"Decision: {recommended_action}")
    print()
    print(f"Report: {report_file}")


if __name__ == "__main__":
    main()

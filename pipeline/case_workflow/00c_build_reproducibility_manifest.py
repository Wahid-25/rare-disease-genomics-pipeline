#!/usr/bin/env python3

import hashlib
import os
import sys
from pathlib import Path


FULL_HASH_LIMIT = 64 * 1024 * 1024
SAMPLE_SIZE = 1024 * 1024


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except (ValueError, FileNotFoundError):
        return str(path.resolve())


def hash_stream(handle) -> str:
    digest = hashlib.sha256()

    while True:
        block = handle.read(1024 * 1024)

        if not block:
            break

        digest.update(block)

    return digest.hexdigest()


def fingerprint_file(path: Path) -> str:
    if not path.is_file():
        return "missing"

    size = path.stat().st_size

    if size <= FULL_HASH_LIMIT:
        with path.open("rb") as handle:
            digest = hash_stream(handle)

        return f"full_sha256:{size}:{digest}"

    digest = hashlib.sha256()
    digest.update(f"size={size}\n".encode())

    offsets = sorted(
        {
            0,
            max(0, (size // 2) - (SAMPLE_SIZE // 2)),
            max(0, size - SAMPLE_SIZE),
        }
    )

    with path.open("rb") as handle:
        for offset in offsets:
            handle.seek(offset)
            block = handle.read(SAMPLE_SIZE)

            digest.update(
                f"offset={offset};length={len(block)}\n".encode()
            )
            digest.update(block)

    return (
        f"sampled_sha256:{size}:"
        f"{digest.hexdigest()}"
    )



def fingerprint_prepared_vcf(path: Path) -> str:
    """Hash stable VCF content while ignoring generated bcftools headers."""
    if not path.is_file():
        return "missing"

    digest = hashlib.sha256()
    stable_lines = 0
    variant_records = 0

    with path.open(
        "rt",
        encoding="utf-8",
        errors="replace",
    ) as handle:
        for line in handle:
            if line.startswith("##bcftools_"):
                continue

            digest.update(line.encode("utf-8"))
            stable_lines += 1

            if not line.startswith("#"):
                variant_records += 1

    return (
        f"canonical_vcf_sha256:"
        f"{stable_lines}:"
        f"{variant_records}:"
        f"{digest.hexdigest()}"
    )

def directory_metadata_hash(path: Path) -> str:
    if not path.is_dir():
        return "missing"

    digest = hashlib.sha256()
    file_count = 0

    for item in sorted(
        (entry for entry in path.rglob("*") if entry.is_file()),
        key=lambda entry: str(entry.relative_to(path)),
    ):
        stat = item.stat()
        relative = item.relative_to(path)

        digest.update(
            (
                f"{relative}\t{stat.st_size}\t"
                f"{stat.st_mtime_ns}\n"
            ).encode()
        )

        file_count += 1

    return (
        f"directory_metadata_sha256:{file_count}:"
        f"{digest.hexdigest()}"
    )


def pipeline_tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    count = 0

    files = sorted(
        (
            item
            for item in path.rglob("*")
            if item.is_file()
            and item.suffix in {".py", ".sh"}
        ),
        key=lambda item: str(item.relative_to(path)),
    )

    for item in files:
        relative = item.relative_to(path)

        digest.update(f"{relative}\n".encode())

        with item.open("rb") as handle:
            digest.update(hash_stream(handle).encode())

        count += 1

    return f"pipeline_sha256:{count}:{digest.hexdigest()}"


def optional_file(
    argument: str,
    root: Path,
) -> tuple[str, str]:
    if argument == "-":
        return "-", "-"

    path = Path(argument)

    if not path.is_absolute():
        path = root / path

    return (
        display_path(path, root),
        fingerprint_file(path),
    )


def add_file(
    rows: list[tuple[str, str]],
    metric: str,
    path: Path,
    root: Path,
) -> None:
    rows.append(
        (
            f"{metric}_path",
            display_path(path, root),
        )
    )

    rows.append(
        (
            f"{metric}_fingerprint",
            fingerprint_file(path),
        )
    )


def add_directory(
    rows: list[tuple[str, str]],
    metric: str,
    path: Path,
    root: Path,
) -> None:
    if path.exists():
        target = display_path(path.resolve(), root)
    else:
        target = "missing"

    rows.append((f"{metric}_target", target))
    rows.append(
        (
            f"{metric}_metadata",
            directory_metadata_hash(path),
        )
    )


def main() -> None:
    if len(sys.argv) != 7:
        raise SystemExit(
            "Usage: 00c_build_reproducibility_manifest.py "
            "CASE_ID INPUT_VCF PHENOTYPE_OR_- CONTEXT_OR_- "
            "PREPARED_VCF OUTPUT_TSV"
        )

    (
        case_id,
        input_argument,
        phenotype_argument,
        context_argument,
        prepared_argument,
        output_argument,
    ) = sys.argv[1:]

    root = Path(__file__).resolve().parents[2]

    input_vcf = Path(input_argument)
    prepared_vcf = Path(prepared_argument)
    output = Path(output_argument)

    if not input_vcf.is_absolute():
        input_vcf = root / input_vcf

    if not prepared_vcf.is_absolute():
        prepared_vcf = root / prepared_vcf

    if not output.is_absolute():
        output = root / output

    if not input_vcf.is_file():
        raise SystemExit(
            f"ERROR: Input VCF missing: {input_vcf}"
        )

    if not prepared_vcf.is_file():
        raise SystemExit(
            f"ERROR: Prepared VCF missing: {prepared_vcf}"
        )

    phenotype_path, phenotype_fingerprint = optional_file(
        phenotype_argument,
        root,
    )

    context_path, context_fingerprint = optional_file(
        context_argument,
        root,
    )

    rows: list[tuple[str, str]] = [
        ("manifest_version", "1"),
        ("project_name", "Universal Rare Disease Pipeline"),
        ("case_id", case_id),
        (
            "input_vcf_path",
            display_path(input_vcf, root),
        ),
        (
            "input_vcf_fingerprint",
            fingerprint_file(input_vcf),
        ),
        ("phenotype_file_path", phenotype_path),
        (
            "phenotype_file_fingerprint",
            phenotype_fingerprint,
        ),
        ("context_file_path", context_path),
        (
            "context_file_fingerprint",
            context_fingerprint,
        ),
        (
            "prepared_vcf_path",
            display_path(prepared_vcf, root),
        ),
        (
            "prepared_vcf_fingerprint",
            fingerprint_prepared_vcf(prepared_vcf),
        ),
        (
            "pipeline_tree_fingerprint",
            pipeline_tree_hash(root / "pipeline"),
        ),
        (
            "clinpgx_mode",
            os.environ.get(
                "CLINPGX_MODE",
                "cache_only",
            ),
        ),
    ]

    add_file(
        rows,
        "reference_fasta",
        root / "resources/reference/hg38.fa",
        root,
    )

    add_file(
        rows,
        "reference_fai",
        root / "resources/reference/hg38.fa.fai",
        root,
    )

    add_file(
        rows,
        "clinvar_vcf",
        root / "resources/clinvar/clinvar.vcf.gz",
        root,
    )

    add_file(
        rows,
        "clinvar_index",
        root / "resources/clinvar/clinvar.vcf.gz.tbi",
        root,
    )

    add_file(
        rows,
        "clingen_dosage",
        (
            root
            / "resources/clingen/"
            "clingen_dosage_genes_regions.csv"
        ),
        root,
    )

    add_file(
        rows,
        "hpo_semantic_database",
        (
            root
            / "resources/phenotype/hpo/current/"
            "hpo_semantic.sqlite"
        ),
        root,
    )

    add_directory(
        rows,
        "hpo_release",
        root / "resources/phenotype/hpo/current",
        root,
    )

    add_directory(
        rows,
        "mondo_release",
        (
            root
            / "resources/disease_ontology/"
            "mondo/current"
        ),
        root,
    )

    add_directory(
        rows,
        "vep_cache_release",
        (
            root
            / "resources/vep_cache/"
            "homo_sapiens/115_GRCh38"
        ),
        root,
    )

    add_directory(
        rows,
        "classifycnv_tool",
        root / "tools/ClassifyCNV",
        root,
    )

    for container_name in [
        "core_tools.sif",
        "vep_release115.sif",
        "snpeff.sif",
        "spliceai.sif",
        "annotsv.sif",
        "isv.sif",
    ]:
        metric = (
            "container_"
            + container_name.removesuffix(".sif")
        )

        add_file(
            rows,
            metric,
            root / "containers" / container_name,
            root,
        )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output.open(
        "w",
        encoding="utf-8",
    ) as handle:
        handle.write("metric\tvalue\n")

        for metric, value in rows:
            handle.write(f"{metric}\t{value}\n")

    print("REPRODUCIBILITY MANIFEST CREATED")
    print(f"Case:   {case_id}")
    print(f"Output: {output}")


if __name__ == "__main__":
    main()

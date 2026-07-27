#!/usr/bin/env python3

import csv
import math
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path


sys.setrecursionlimit(10000)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HPO_DIR = (
    PROJECT_ROOT
    / "resources"
    / "phenotype"
    / "hpo"
    / "current"
).resolve()

OBO_FILE = HPO_DIR / "hp.obo"
HPOA_FILE = HPO_DIR / "phenotype.hpoa"
GENE_DISEASE_FILE = HPO_DIR / "genes_to_disease.txt"
GENE_PHENOTYPE_FILE = HPO_DIR / "genes_to_phenotype.txt"

DATABASE = HPO_DIR / "hpo_semantic.sqlite"
TEMP_DATABASE = HPO_DIR / "hpo_semantic.sqlite.building"

QC_FILE = (
    PROJECT_ROOT
    / "validation"
    / "pipeline_revision"
    / "hpo_semantic_cache_qc.tsv"
)


def non_comment_lines(path: Path):
    with path.open(
        encoding="utf-8-sig",
        errors="replace",
    ) as handle:
        for line in handle:
            if not line.strip():
                continue

            if line.startswith("#"):
                continue

            yield line


def parse_obo(path: Path):
    terms = {}
    alternate_ids = {}
    current = None

    def save_term(term):
        if not term:
            return

        term_id = term.get("id", "")

        if not term_id:
            return

        if term.get("obsolete") == "true":
            return

        terms[term_id] = {
            "name": term.get("name", ""),
            "parents": set(term.get("parents", set())),
        }

        for alternate_id in term.get("alt_ids", set()):
            alternate_ids[alternate_id] = term_id

    with path.open(
        encoding="utf-8",
        errors="replace",
    ) as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")

            if line == "[Term]":
                save_term(current)

                current = {
                    "parents": set(),
                    "alt_ids": set(),
                    "obsolete": "false",
                }
                continue

            if line.startswith("["):
                save_term(current)
                current = None
                continue

            if current is None:
                continue

            if line.startswith("id: "):
                current["id"] = line[4:].strip()

            elif line.startswith("name: "):
                current["name"] = line[6:].strip()

            elif line.startswith("alt_id: "):
                current["alt_ids"].add(
                    line[8:].strip()
                )

            elif line.startswith("is_a: "):
                parent = (
                    line[6:]
                    .split(" ! ", 1)[0]
                    .strip()
                )

                if parent:
                    current["parents"].add(parent)

            elif line.startswith("is_obsolete: "):
                current["obsolete"] = (
                    line.split(":", 1)[1]
                    .strip()
                    .lower()
                )

    save_term(current)

    return terms, alternate_ids


def resolve_hpo(
    term_id: str,
    terms,
    alternate_ids,
) -> str:
    term_id = (term_id or "").strip().upper()

    if term_id in terms:
        return term_id

    return alternate_ids.get(term_id, "")


def create_schema(connection):
    connection.executescript(
        """
        PRAGMA foreign_keys = OFF;

        CREATE TABLE resource_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE hpo_term (
            hpo_id TEXT PRIMARY KEY,
            hpo_name TEXT NOT NULL
        );

        CREATE TABLE hpo_alt_id (
            alt_id TEXT PRIMARY KEY,
            hpo_id TEXT NOT NULL
        );

        CREATE TABLE hpo_parent (
            child_id TEXT NOT NULL,
            parent_id TEXT NOT NULL,
            PRIMARY KEY (child_id, parent_id)
        );

        CREATE TABLE hpo_closure (
            term_id TEXT NOT NULL,
            ancestor_id TEXT NOT NULL,
            distance INTEGER NOT NULL,
            PRIMARY KEY (term_id, ancestor_id)
        );

        CREATE TABLE disease (
            disease_id TEXT PRIMARY KEY,
            disease_name TEXT NOT NULL
        );

        CREATE TABLE disease_hpo (
            disease_id TEXT NOT NULL,
            hpo_id TEXT NOT NULL,
            frequency TEXT,
            onset TEXT,
            evidence TEXT,
            PRIMARY KEY (disease_id, hpo_id)
        );

        CREATE TABLE disease_inheritance (
            disease_id TEXT NOT NULL,
            hpo_id TEXT NOT NULL,
            PRIMARY KEY (disease_id, hpo_id)
        );

        CREATE TABLE gene_disease (
            gene_symbol TEXT NOT NULL,
            disease_id TEXT NOT NULL,
            association_type TEXT,
            source TEXT,
            PRIMARY KEY (
                gene_symbol,
                disease_id,
                association_type
            )
        );

        CREATE TABLE gene_hpo (
            gene_symbol TEXT NOT NULL,
            disease_id TEXT NOT NULL,
            hpo_id TEXT NOT NULL,
            PRIMARY KEY (
                gene_symbol,
                disease_id,
                hpo_id
            )
        );

        CREATE TABLE hpo_information_content (
            hpo_id TEXT PRIMARY KEY,
            annotated_disease_count INTEGER NOT NULL,
            information_content REAL NOT NULL,
            normalized_information_content REAL NOT NULL
        );

        CREATE INDEX idx_disease_hpo_disease
        ON disease_hpo(disease_id);

        CREATE INDEX idx_disease_hpo_term
        ON disease_hpo(hpo_id);

        CREATE INDEX idx_gene_disease_gene
        ON gene_disease(gene_symbol);

        CREATE INDEX idx_gene_hpo_gene
        ON gene_hpo(gene_symbol);

        CREATE INDEX idx_closure_term
        ON hpo_closure(term_id);

        CREATE INDEX idx_closure_ancestor
        ON hpo_closure(ancestor_id);
        """
    )


def read_release_name():
    manifest = HPO_DIR / "release_manifest.tsv"

    if not manifest.is_file():
        return "unknown"

    with manifest.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        row = next(reader, {})

    return (row.get("release") or "unknown").strip()


def main():
    required = [
        OBO_FILE,
        HPOA_FILE,
        GENE_DISEASE_FILE,
        GENE_PHENOTYPE_FILE,
    ]

    for path in required:
        if not path.is_file():
            raise SystemExit(
                f"ERROR: Required HPO resource missing: {path}"
            )

    print("=" * 72)
    print("BUILDING UNIVERSAL HPO SEMANTIC CACHE")
    print("=" * 72)
    print(f"HPO directory: {HPO_DIR}")
    print()

    print("[1/7] Parsing HPO ontology")

    terms, alternate_ids = parse_obo(OBO_FILE)

    parents = {
        term_id: {
            parent
            for parent in record["parents"]
            if parent in terms
        }
        for term_id, record in terms.items()
    }

    print(f"Active HPO terms:    {len(terms)}")
    print(f"Alternate HPO IDs:   {len(alternate_ids)}")

    @lru_cache(maxsize=None)
    def ancestors(term_id):
        result = {term_id: 0}

        for parent in parents.get(term_id, set()):
            for ancestor, distance in ancestors(parent).items():
                new_distance = distance + 1
                old_distance = result.get(ancestor)

                if (
                    old_distance is None
                    or new_distance < old_distance
                ):
                    result[ancestor] = new_distance

        return result

    print("[2/7] Computing HPO ancestor closure")

    closure_rows = []

    for term_id in sorted(terms):
        for ancestor_id, distance in ancestors(
            term_id
        ).items():
            closure_rows.append(
                (term_id, ancestor_id, distance)
            )

    inheritance_root = "HP:0000005"

    inheritance_terms = {
        term_id
        for term_id in terms
        if inheritance_root in ancestors(term_id)
    }

    print(f"Closure relationships: {len(closure_rows)}")
    print(f"Inheritance terms:     {len(inheritance_terms)}")

    if TEMP_DATABASE.exists():
        TEMP_DATABASE.unlink()

    connection = sqlite3.connect(TEMP_DATABASE)

    try:
        create_schema(connection)

        connection.executemany(
            """
            INSERT INTO hpo_term(hpo_id, hpo_name)
            VALUES (?, ?)
            """,
            [
                (
                    term_id,
                    record["name"],
                )
                for term_id, record in terms.items()
            ],
        )

        connection.executemany(
            """
            INSERT INTO hpo_alt_id(alt_id, hpo_id)
            VALUES (?, ?)
            """,
            sorted(alternate_ids.items()),
        )

        connection.executemany(
            """
            INSERT INTO hpo_parent(child_id, parent_id)
            VALUES (?, ?)
            """,
            [
                (child, parent)
                for child, parent_set in parents.items()
                for parent in parent_set
            ],
        )

        connection.executemany(
            """
            INSERT INTO hpo_closure(
                term_id,
                ancestor_id,
                distance
            )
            VALUES (?, ?, ?)
            """,
            closure_rows,
        )

        print("[3/7] Loading disease–phenotype annotations")

        disease_names = {}
        disease_hpo_rows = {}
        disease_inheritance_rows = set()

        reader = csv.DictReader(
            non_comment_lines(HPOA_FILE),
            delimiter="\t",
        )

        for row in reader:
            disease_id = (
                row.get("database_id") or ""
            ).strip()

            disease_name = (
                row.get("disease_name") or ""
            ).strip()

            qualifier = (
                row.get("qualifier") or ""
            ).strip().upper()

            aspect = (
                row.get("aspect") or ""
            ).strip().upper()

            hpo_id = resolve_hpo(
                row.get("hpo_id") or "",
                terms,
                alternate_ids,
            )

            if not disease_id or not hpo_id:
                continue

            if disease_name:
                disease_names[disease_id] = disease_name

            if qualifier == "NOT":
                continue

            if aspect == "P":
                disease_hpo_rows[
                    (disease_id, hpo_id)
                ] = (
                    disease_id,
                    hpo_id,
                    (row.get("frequency") or "").strip(),
                    (row.get("onset") or "").strip(),
                    (row.get("evidence") or "").strip(),
                )

            elif aspect == "I":
                disease_inheritance_rows.add(
                    (disease_id, hpo_id)
                )

        connection.executemany(
            """
            INSERT OR REPLACE INTO disease(
                disease_id,
                disease_name
            )
            VALUES (?, ?)
            """,
            sorted(disease_names.items()),
        )

        connection.executemany(
            """
            INSERT OR REPLACE INTO disease_hpo(
                disease_id,
                hpo_id,
                frequency,
                onset,
                evidence
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            disease_hpo_rows.values(),
        )

        connection.executemany(
            """
            INSERT OR IGNORE INTO disease_inheritance(
                disease_id,
                hpo_id
            )
            VALUES (?, ?)
            """,
            sorted(disease_inheritance_rows),
        )

        print(f"Diseases:             {len(disease_names)}")
        print(
            "Disease HPO links:    "
            f"{len(disease_hpo_rows)}"
        )
        print(
            "Inheritance links:    "
            f"{len(disease_inheritance_rows)}"
        )

        print("[4/7] Loading gene–disease mappings")

        gene_disease_rows = set()

        reader = csv.DictReader(
            non_comment_lines(GENE_DISEASE_FILE),
            delimiter="\t",
        )

        for row in reader:
            gene = (
                row.get("gene_symbol") or ""
            ).strip().upper()

            disease_id = (
                row.get("disease_id") or ""
            ).strip()

            association_type = (
                row.get("association_type") or ""
            ).strip().upper()

            source = (
                row.get("source") or ""
            ).strip()

            if not gene or not disease_id:
                continue

            gene_disease_rows.add(
                (
                    gene,
                    disease_id,
                    association_type,
                    source,
                )
            )

            connection.execute(
                """
                INSERT OR IGNORE INTO disease(
                    disease_id,
                    disease_name
                )
                VALUES (?, '')
                """,
                (disease_id,),
            )

        connection.executemany(
            """
            INSERT OR IGNORE INTO gene_disease(
                gene_symbol,
                disease_id,
                association_type,
                source
            )
            VALUES (?, ?, ?, ?)
            """,
            sorted(gene_disease_rows),
        )

        print(
            "Gene–disease links:   "
            f"{len(gene_disease_rows)}"
        )

        print("[5/7] Loading gene–phenotype mappings")

        gene_hpo_rows = set()

        reader = csv.DictReader(
            non_comment_lines(GENE_PHENOTYPE_FILE),
            delimiter="\t",
        )

        for row in reader:
            gene = (
                row.get("gene_symbol") or ""
            ).strip().upper()

            disease_id = (
                row.get("disease_id") or ""
            ).strip()

            hpo_id = resolve_hpo(
                row.get("hpo_id") or "",
                terms,
                alternate_ids,
            )

            if not gene or not hpo_id:
                continue

            # Keep inheritance separate from clinical phenotype.
            if hpo_id in inheritance_terms:
                continue

            gene_hpo_rows.add(
                (
                    gene,
                    disease_id,
                    hpo_id,
                )
            )

        connection.executemany(
            """
            INSERT OR IGNORE INTO gene_hpo(
                gene_symbol,
                disease_id,
                hpo_id
            )
            VALUES (?, ?, ?)
            """,
            sorted(gene_hpo_rows),
        )

        print(
            "Gene–phenotype links: "
            f"{len(gene_hpo_rows)}"
        )

        print("[6/7] Calculating HPO information content")

        disease_to_terms = defaultdict(set)

        for disease_id, hpo_id in connection.execute(
            """
            SELECT disease_id, hpo_id
            FROM disease_hpo
            """
        ):
            disease_to_terms[disease_id].add(hpo_id)

        annotation_counts = Counter()

        for direct_terms in disease_to_terms.values():
            expanded_terms = set()

            for hpo_id in direct_terms:
                expanded_terms.update(
                    ancestors(hpo_id).keys()
                )

            for hpo_id in expanded_terms:
                annotation_counts[hpo_id] += 1

        disease_count = len(disease_to_terms)

        ic_values = {}

        for hpo_id, count in annotation_counts.items():
            probability = count / disease_count
            ic_values[hpo_id] = -math.log(probability)

        maximum_ic = max(ic_values.values(), default=1.0)

        connection.executemany(
            """
            INSERT INTO hpo_information_content(
                hpo_id,
                annotated_disease_count,
                information_content,
                normalized_information_content
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    hpo_id,
                    annotation_counts[hpo_id],
                    information_content,
                    (
                        information_content / maximum_ic
                        if maximum_ic > 0
                        else 0.0
                    ),
                )
                for hpo_id, information_content
                in ic_values.items()
            ],
        )

        release = read_release_name()

        metadata = {
            "hpo_release": release,
            "ontology_file": OBO_FILE.name,
            "disease_annotation_file": HPOA_FILE.name,
            "gene_disease_file": GENE_DISEASE_FILE.name,
            "gene_phenotype_file": GENE_PHENOTYPE_FILE.name,
            "scoring_ready": "yes",
            "semantic_method": (
                "ontology_ancestor_closure_and_information_content"
            ),
        }

        connection.executemany(
            """
            INSERT INTO resource_metadata(key, value)
            VALUES (?, ?)
            """,
            sorted(metadata.items()),
        )

        connection.commit()
        connection.execute("VACUUM")
        connection.commit()

    finally:
        connection.close()

    os.replace(TEMP_DATABASE, DATABASE)

    print("[7/7] Writing cache QC")

    connection = sqlite3.connect(DATABASE)

    try:
        counts = {
            "hpo_terms": connection.execute(
                "SELECT COUNT(*) FROM hpo_term"
            ).fetchone()[0],
            "hpo_closure_rows": connection.execute(
                "SELECT COUNT(*) FROM hpo_closure"
            ).fetchone()[0],
            "diseases": connection.execute(
                "SELECT COUNT(*) FROM disease"
            ).fetchone()[0],
            "disease_hpo_links": connection.execute(
                "SELECT COUNT(*) FROM disease_hpo"
            ).fetchone()[0],
            "gene_disease_links": connection.execute(
                "SELECT COUNT(*) FROM gene_disease"
            ).fetchone()[0],
            "gene_hpo_links": connection.execute(
                "SELECT COUNT(*) FROM gene_hpo"
            ).fetchone()[0],
            "ic_terms": connection.execute(
                """
                SELECT COUNT(*)
                FROM hpo_information_content
                """
            ).fetchone()[0],
        }

        test_gene_rows = []

        for gene in [
            "CFTR",
            "HBB",
            "BRCA1",
            "HEXA",
            "HTT",
        ]:
            disease_links = connection.execute(
                """
                SELECT COUNT(DISTINCT disease_id)
                FROM gene_disease
                WHERE gene_symbol = ?
                """,
                (gene,),
            ).fetchone()[0]

            phenotype_links = connection.execute(
                """
                SELECT COUNT(*)
                FROM gene_hpo
                WHERE gene_symbol = ?
                """,
                (gene,),
            ).fetchone()[0]

            test_gene_rows.append(
                (
                    gene,
                    disease_links,
                    phenotype_links,
                )
            )

    finally:
        connection.close()

    QC_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with QC_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerow(["database", DATABASE])
        writer.writerow(
            ["hpo_release", read_release_name()]
        )

        for metric, value in counts.items():
            writer.writerow([metric, value])

        for gene, diseases, phenotypes in test_gene_rows:
            writer.writerow(
                [
                    f"test_gene_{gene}",
                    (
                        f"diseases={diseases};"
                        f"phenotypes={phenotypes}"
                    ),
                ]
            )

    print()
    print("HPO semantic cache created successfully.")
    print(f"Database: {DATABASE}")
    print(f"QC:       {QC_FILE}")


if __name__ == "__main__":
    main()

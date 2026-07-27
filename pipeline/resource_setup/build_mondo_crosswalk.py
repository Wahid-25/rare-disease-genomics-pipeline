#!/usr/bin/env python3

import csv
import re
import sqlite3
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]

MONDO_DIR = (
    PROJECT
    / "resources"
    / "disease_ontology"
    / "mondo"
    / "current"
).resolve()

OBO_FILE = MONDO_DIR / "mondo.obo"
DATABASE = MONDO_DIR / "mondo_crosswalk.sqlite"

QC_FILE = (
    PROJECT
    / "validation"
    / "pipeline_revision"
    / "mondo_crosswalk_qc.tsv"
)


def normalize_identifier(value):
    value = value.strip().strip("<>")

    if value.startswith("Orphanet:"):
        return "ORPHA:" + value.split(":", 1)[1]

    return value


def save_term(term, terms, synonyms, mappings):
    if not term:
        return

    mondo_id = term.get("id", "")

    if not mondo_id.startswith("MONDO:"):
        return

    if term.get("obsolete"):
        return

    terms[mondo_id] = term.get("name", "")

    for synonym, scope in term.get("synonyms", set()):
        synonyms.add(
            (
                mondo_id,
                synonym,
                scope,
            )
        )

    for external_id, relation, source_line in term.get(
        "mappings",
        set(),
    ):
        external_id = normalize_identifier(
            external_id
        )

        if not external_id or external_id == mondo_id:
            continue

        if external_id.startswith(
            (
                "http:",
                "https:",
                "urn:",
            )
        ):
            continue

        mappings.add(
            (
                mondo_id,
                external_id,
                relation,
                source_line,
            )
        )


def parse_mondo(path):
    terms = {}
    synonyms = set()
    mappings = set()
    current = None

    synonym_pattern = re.compile(
        r'^synonym:\s+"(.*)"\s+'
        r'(EXACT|RELATED|BROAD|NARROW)\b'
    )

    with path.open(
        encoding="utf-8",
        errors="replace",
    ) as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")

            if line == "[Term]":
                save_term(
                    current,
                    terms,
                    synonyms,
                    mappings,
                )

                current = {
                    "synonyms": set(),
                    "mappings": set(),
                    "obsolete": False,
                }
                continue

            if line.startswith("["):
                save_term(
                    current,
                    terms,
                    synonyms,
                    mappings,
                )

                current = None
                continue

            if current is None:
                continue

            if line.startswith("id: "):
                current["id"] = line[4:].strip()

            elif line.startswith("name: "):
                current["name"] = line[6:].strip()

            elif line == "is_obsolete: true":
                current["obsolete"] = True

            elif line.startswith("synonym: "):
                match = synonym_pattern.match(line)

                if match:
                    current["synonyms"].add(
                        (
                            match.group(1),
                            match.group(2),
                        )
                    )

            elif line.startswith("xref: "):
                external_id = (
                    line[6:]
                    .split(None, 1)[0]
                    .strip()
                )

                relation = "xref"

                if (
                    "equivalentTo" in line
                    or "exactMatch" in line
                ):
                    relation = "exact"

                current["mappings"].add(
                    (
                        external_id,
                        relation,
                        line,
                    )
                )

            elif line.startswith(
                "property_value: skos:exactMatch "
            ):
                remainder = line.split(
                    "property_value: skos:exactMatch ",
                    1,
                )[1]

                external_id = (
                    remainder
                    .split(None, 1)[0]
                    .strip()
                )

                current["mappings"].add(
                    (
                        external_id,
                        "exact",
                        line,
                    )
                )

    save_term(
        current,
        terms,
        synonyms,
        mappings,
    )

    return terms, synonyms, mappings


def read_release():
    manifest = MONDO_DIR / "release_manifest.tsv"

    if not manifest.is_file():
        return "unknown"

    with manifest.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        values = {
            row.get("field", ""): row.get("value", "")
            for row in reader
        }

    return values.get("release", "unknown")


def main():
    if not OBO_FILE.is_file():
        raise SystemExit(
            f"ERROR: Mondo ontology missing: {OBO_FILE}"
        )

    print("=" * 72)
    print("BUILDING MONDO DISEASE-IDENTITY CROSSWALK")
    print("=" * 72)

    terms, synonyms, mappings = parse_mondo(
        OBO_FILE
    )

    if DATABASE.exists():
        DATABASE.unlink()

    connection = sqlite3.connect(DATABASE)

    try:
        connection.executescript(
            """
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE mondo_term (
                mondo_id TEXT PRIMARY KEY,
                mondo_name TEXT NOT NULL
            );

            CREATE TABLE mondo_synonym (
                mondo_id TEXT NOT NULL,
                synonym TEXT NOT NULL,
                scope TEXT NOT NULL,
                PRIMARY KEY (
                    mondo_id,
                    synonym,
                    scope
                )
            );

            CREATE TABLE mondo_mapping (
                mondo_id TEXT NOT NULL,
                external_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                source_line TEXT,
                PRIMARY KEY (
                    mondo_id,
                    external_id,
                    relation_type
                )
            );

            CREATE INDEX idx_mapping_external
            ON mondo_mapping(external_id);

            CREATE INDEX idx_mapping_mondo
            ON mondo_mapping(mondo_id);

            CREATE INDEX idx_synonym_text
            ON mondo_synonym(synonym);
            """
        )

        connection.executemany(
            """
            INSERT INTO mondo_term(
                mondo_id,
                mondo_name
            )
            VALUES (?, ?)
            """,
            sorted(terms.items()),
        )

        connection.executemany(
            """
            INSERT INTO mondo_synonym(
                mondo_id,
                synonym,
                scope
            )
            VALUES (?, ?, ?)
            """,
            sorted(synonyms),
        )

        # Mondo may contain the same identity mapping in
        # multiple ontology statements. The SQLite primary key
        # represents the biological mapping, while source lines
        # are combined for provenance.
        mapping_sources = {}

        for (
            mondo_id,
            external_id,
            relation_type,
            source_line,
        ) in sorted(mappings):
            key = (
                mondo_id,
                external_id,
                relation_type,
            )

            mapping_sources.setdefault(
                key,
                [],
            )

            if (
                source_line
                and source_line
                not in mapping_sources[key]
            ):
                mapping_sources[key].append(
                    source_line
                )

        unique_mappings = [
            (
                mondo_id,
                external_id,
                relation_type,
                " || ".join(
                    mapping_sources[
                        (
                            mondo_id,
                            external_id,
                            relation_type,
                        )
                    ]
                ),
            )
            for (
                mondo_id,
                external_id,
                relation_type,
            ) in sorted(mapping_sources)
        ]

        connection.executemany(
            """
            INSERT INTO mondo_mapping(
                mondo_id,
                external_id,
                relation_type,
                source_line
            )
            VALUES (?, ?, ?, ?)
            """,
            unique_mappings,
        )

        metadata = {
            "mondo_release": read_release(),
            "ontology_file": "mondo.obo",
            "identity_policy":
                "exact_mappings_only_for_candidate_merging",
        }

        connection.executemany(
            """
            INSERT INTO metadata(key, value)
            VALUES (?, ?)
            """,
            sorted(metadata.items()),
        )

        connection.commit()

        exact_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM mondo_mapping
            WHERE relation_type = 'exact'
            """
        ).fetchone()[0]

        xref_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM mondo_mapping
            WHERE relation_type = 'xref'
            """
        ).fetchone()[0]

        tay_sachs = connection.execute(
            """
            SELECT
                term.mondo_name,
                mapping.external_id,
                mapping.relation_type
            FROM mondo_term AS term
            LEFT JOIN mondo_mapping AS mapping
              ON mapping.mondo_id = term.mondo_id
            WHERE term.mondo_id = 'MONDO:0010100'
            ORDER BY
                mapping.relation_type,
                mapping.external_id
            """
        ).fetchall()

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
        writer = csv.writer(
            handle,
            delimiter="\t",
        )

        writer.writerow(["metric", "value"])
        writer.writerow(
            ["mondo_release", read_release()]
        )
        writer.writerow(
            ["mondo_terms", len(terms)]
        )
        writer.writerow(
            ["mondo_synonyms", len(synonyms)]
        )
        writer.writerow(
            ["exact_identity_mappings", exact_count]
        )
        writer.writerow(
            ["other_xrefs", xref_count]
        )
        writer.writerow(
            ["database", str(DATABASE)]
        )

        for name, external_id, relation in tay_sachs:
            writer.writerow(
                [
                    "MONDO_0010100_mapping",
                    (
                        f"name={name};"
                        f"external_id={external_id};"
                        f"relation={relation}"
                    ),
                ]
            )

    print(f"Mondo terms:            {len(terms)}")
    print(f"Synonyms:               {len(synonyms)}")
    print(f"Exact identity links:   {exact_count}")
    print(f"Other cross-references: {xref_count}")
    print(f"Database:               {DATABASE}")
    print(f"QC:                     {QC_FILE}")


if __name__ == "__main__":
    main()

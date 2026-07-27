#!/usr/bin/env python3

import csv
import re
import sqlite3
import sys
from functools import lru_cache
from pathlib import Path


HPO_PATTERN = re.compile(r"\bHP:\d{7}\b", re.I)


def clean(value):
    return str(value).strip() if value is not None else ""


def read_context(path):
    values = {}

    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.reader(handle, delimiter="\t")

        for row in reader:
            if not row or row[0].startswith("#"):
                continue

            if row[0].strip().lower() == "field":
                continue

            if len(row) >= 2:
                values[row[0].strip()] = row[1].strip()

    return values


def load_patient_hpo(path):
    terms = set()

    with path.open(
        encoding="utf-8",
        errors="replace",
    ) as handle:
        for line in handle:
            terms.update(
                match.upper()
                for match in HPO_PATTERN.findall(line)
            )

    return terms


def resolve_project_path(project, value):
    path = Path(value)

    if path.is_absolute():
        return path

    return project / path


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: "
            "10a_add_semantic_phenotype_evidence.py CASE_ID"
        )

    case_id = sys.argv[1]
    project = Path(__file__).resolve().parents[2]

    final_dir = (
        project
        / "results"
        / "cases"
        / case_id
        / "final"
    )

    input_table = (
        final_dir
        / (
            f"{case_id}."
            "cnv_gene_disease.semantic_input.tsv"
        )
    )

    output_table = (
        final_dir
        / (
            f"{case_id}."
            "cnv_gene_disease.phenotype.tsv"
        )
    )

    qc_file = (
        final_dir
        / (
            f"{case_id}."
            "cnv_semantic_phenotype_qc.tsv"
        )
    )

    context_file = (
        project
        / "input"
        / "cases"
        / case_id
        / "case_context.resolved.tsv"
    )

    database = (
        project
        / "resources"
        / "phenotype"
        / "hpo"
        / "current"
        / "hpo_semantic.sqlite"
    ).resolve()

    for required in [
        input_table,
        context_file,
        database,
    ]:
        if not required.is_file():
            raise SystemExit(
                f"ERROR: Required file missing: {required}"
            )

    context = read_context(context_file)

    phenotype_status = clean(
        context.get("phenotype_status")
    )

    case_mode = clean(
        context.get("case_mode")
    )

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row

    try:
        def resolve_term(term):
            term = clean(term).upper()

            row = connection.execute(
                """
                SELECT hpo_id
                FROM hpo_term
                WHERE hpo_id = ?

                UNION

                SELECT hpo_id
                FROM hpo_alt_id
                WHERE alt_id = ?
                """,
                (term, term),
            ).fetchone()

            return row["hpo_id"] if row else ""

        patient_terms = set()
        invalid_patient_terms = set()

        if phenotype_status == "available":
            phenotype_value = clean(
                context.get("phenotype_file")
            )

            if not phenotype_value:
                raise SystemExit(
                    "ERROR: phenotype_status=available but "
                    "phenotype_file is empty."
                )

            phenotype_file = resolve_project_path(
                project,
                phenotype_value,
            )

            if not phenotype_file.is_file():
                raise SystemExit(
                    f"ERROR: Phenotype file missing: "
                    f"{phenotype_file}"
                )

            raw_terms = load_patient_hpo(
                phenotype_file
            )

            for term in raw_terms:
                resolved = resolve_term(term)

                if resolved:
                    patient_terms.add(resolved)
                else:
                    invalid_patient_terms.add(term)

            if not patient_terms:
                raise SystemExit(
                    "ERROR: No valid HPO terms were available "
                    "for semantic scoring."
                )

        @lru_cache(maxsize=None)
        def ancestors(term):
            rows = connection.execute(
                """
                SELECT
                    closure.ancestor_id,
                    COALESCE(
                        ic.normalized_information_content,
                        0.0
                    ) AS normalized_ic
                FROM hpo_closure AS closure
                LEFT JOIN hpo_information_content AS ic
                  ON ic.hpo_id = closure.ancestor_id
                WHERE closure.term_id = ?
                """,
                (term,),
            ).fetchall()

            return {
                row["ancestor_id"]: float(
                    row["normalized_ic"]
                )
                for row in rows
            }

        @lru_cache(maxsize=None)
        def term_similarity(first, second):
            first_ancestors = ancestors(first)
            second_ancestors = ancestors(second)

            common = (
                set(first_ancestors)
                & set(second_ancestors)
            )

            if not common:
                return 0.0

            return max(
                first_ancestors[ancestor]
                for ancestor in common
            )

        @lru_cache(maxsize=None)
        def disease_terms(disease_id):
            rows = connection.execute(
                """
                SELECT hpo_id
                FROM disease_hpo
                WHERE disease_id = ?
                """,
                (disease_id,),
            ).fetchall()

            return frozenset(
                row["hpo_id"]
                for row in rows
            )

        @lru_cache(maxsize=None)
        def disease_inheritance(disease_id):
            rows = connection.execute(
                """
                SELECT
                    inheritance.hpo_id,
                    term.hpo_name
                FROM disease_inheritance AS inheritance
                LEFT JOIN hpo_term AS term
                  ON term.hpo_id = inheritance.hpo_id
                WHERE inheritance.disease_id = ?
                ORDER BY inheritance.hpo_id
                """,
                (disease_id,),
            ).fetchall()

            return tuple(
                (
                    row["hpo_id"],
                    clean(row["hpo_name"]),
                )
                for row in rows
            )

        def calculate_score(disease_id):
            terms = set(
                disease_terms(disease_id)
            )

            if not terms:
                return {
                    "status": "not_available",
                    "disease_hpo_count": 0,
                    "exact_count": "",
                    "exact_terms": "",
                    "patient_to_disease": "",
                    "exact_coverage": "",
                    "component_score": "",
                    "evaluable_maximum": "",
                }

            best_scores = []

            for patient_term in patient_terms:
                best_scores.append(
                    max(
                        term_similarity(
                            patient_term,
                            disease_term,
                        )
                        for disease_term in terms
                    )
                )

            patient_to_disease = (
                sum(best_scores) / len(best_scores)
            )

            exact = patient_terms & terms
            exact_coverage = (
                len(exact) / len(patient_terms)
            )

            component_score = (
                0.80 * patient_to_disease
                + 0.20 * exact_coverage
            )

            status = (
                "evaluable_match"
                if component_score > 0
                else "evaluable_no_match"
            )

            return {
                "status": status,
                "disease_hpo_count": len(terms),
                "exact_count": len(exact),
                "exact_terms": ";".join(sorted(exact)),
                "patient_to_disease": (
                    f"{patient_to_disease:.4f}"
                ),
                "exact_coverage": (
                    f"{exact_coverage:.4f}"
                ),
                "component_score": (
                    f"{component_score:.4f}"
                ),
                "evaluable_maximum": "1.0000",
            }

        with input_table.open(
            encoding="utf-8",
            newline="",
        ) as handle:
            reader = csv.DictReader(
                handle,
                delimiter="\t",
            )

            original_columns = list(
                reader.fieldnames or []
            )

            rows = list(reader)

        added_columns = [
            "case_mode",
            "phenotype_evidence_status",
            "patient_hpo_count",
            "invalid_patient_hpo_count",
            "disease_hpo_count",
            "exact_hpo_count",
            "exact_hpo_terms",
            "patient_to_disease_similarity",
            "exact_patient_hpo_coverage",
            "phenotype_component_score",
            "phenotype_component_evaluable_maximum",
            "phenotype_scoring_method",
            "disease_inheritance_hpo",
            "disease_inheritance_names",
        ]

        output_columns = list(original_columns)

        for column in added_columns:
            if column not in output_columns:
                output_columns.append(column)

        output_rows = []

        evaluable_rows = 0
        positive_rows = 0
        unavailable_rows = 0
        not_evaluable_rows = 0

        for row in rows:
            disease_id = clean(
                row.get("canonical_disease_id")
            )

            row["case_mode"] = case_mode
            row["patient_hpo_count"] = str(
                len(patient_terms)
            )
            row["invalid_patient_hpo_count"] = str(
                len(invalid_patient_terms)
            )

            inheritance = (
                disease_inheritance(disease_id)
                if disease_id
                else ()
            )

            row["disease_inheritance_hpo"] = ";".join(
                item[0]
                for item in inheritance
            )

            row["disease_inheritance_names"] = ";".join(
                item[1]
                for item in inheritance
                if item[1]
            )

            if phenotype_status != "available":
                row["phenotype_evidence_status"] = (
                    phenotype_status
                )
                row["disease_hpo_count"] = ""
                row["exact_hpo_count"] = ""
                row["exact_hpo_terms"] = ""
                row["patient_to_disease_similarity"] = ""
                row["exact_patient_hpo_coverage"] = ""
                row["phenotype_component_score"] = ""
                row[
                    "phenotype_component_evaluable_maximum"
                ] = ""
                row["phenotype_scoring_method"] = (
                    "not_evaluable"
                )

                not_evaluable_rows += 1

            elif not disease_id:
                row["phenotype_evidence_status"] = (
                    "no_disease_mapping"
                )
                row["disease_hpo_count"] = ""
                row["exact_hpo_count"] = ""
                row["exact_hpo_terms"] = ""
                row["patient_to_disease_similarity"] = ""
                row["exact_patient_hpo_coverage"] = ""
                row["phenotype_component_score"] = ""
                row[
                    "phenotype_component_evaluable_maximum"
                ] = ""
                row["phenotype_scoring_method"] = (
                    "disease_mapping_required"
                )

                unavailable_rows += 1

            else:
                result = calculate_score(
                    disease_id
                )

                row["phenotype_evidence_status"] = (
                    result["status"]
                )
                row["disease_hpo_count"] = str(
                    result["disease_hpo_count"]
                )
                row["exact_hpo_count"] = str(
                    result["exact_count"]
                )
                row["exact_hpo_terms"] = (
                    result["exact_terms"]
                )
                row["patient_to_disease_similarity"] = (
                    result["patient_to_disease"]
                )
                row["exact_patient_hpo_coverage"] = (
                    result["exact_coverage"]
                )
                row["phenotype_component_score"] = (
                    result["component_score"]
                )
                row[
                    "phenotype_component_evaluable_maximum"
                ] = result["evaluable_maximum"]
                row["phenotype_scoring_method"] = (
                    "0.80_patient_to_disease_semantic_"
                    "plus_0.20_exact_patient_HPO_coverage"
                )

                if result["status"].startswith(
                    "evaluable"
                ):
                    evaluable_rows += 1

                if result["status"] == "evaluable_match":
                    positive_rows += 1

                if result["status"] == "not_available":
                    unavailable_rows += 1

            output_rows.append(row)

        output_rows.sort(
            key=lambda row: (
                clean(row.get("variant")),
                clean(row.get("gene")),
                -float(
                    row.get("phenotype_component_score")
                    or -1
                ),
                clean(
                    row.get("canonical_disease_id")
                ),
            )
        )

        with output_table.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=output_columns,
                delimiter="\t",
                extrasaction="ignore",
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

            writer.writerow(["metric", "value"])
            writer.writerow(["case_id", case_id])
            writer.writerow(["case_mode", case_mode])
            writer.writerow(
                ["phenotype_status", phenotype_status]
            )
            writer.writerow(
                ["valid_patient_hpo_terms", len(patient_terms)]
            )
            writer.writerow(
                [
                    "invalid_patient_hpo_terms",
                    len(invalid_patient_terms),
                ]
            )
            writer.writerow(["input_rows", len(rows)])
            writer.writerow(
                ["evaluable_rows", evaluable_rows]
            )
            writer.writerow(
                ["positive_match_rows", positive_rows]
            )
            writer.writerow(
                ["unavailable_rows", unavailable_rows]
            )
            writer.writerow(
                ["not_evaluable_rows", not_evaluable_rows]
            )
            writer.writerow(
                [
                    "output_table",
                    str(output_table.relative_to(project)),
                ]
            )

    finally:
        connection.close()

    print("=" * 72)
    print("CNV SEMANTIC PHENOTYPE EVIDENCE")
    print("=" * 72)
    print(f"Case ID:               {case_id}")
    print(f"Case mode:             {case_mode}")
    print(f"Phenotype status:      {phenotype_status}")
    print(f"Valid patient HPO:     {len(patient_terms)}")
    print(f"Input candidate rows:  {len(rows)}")
    print(f"Evaluable rows:        {evaluable_rows}")
    print(f"Positive match rows:   {positive_rows}")
    print(f"Unavailable rows:      {unavailable_rows}")
    print(f"Not-evaluable rows:    {not_evaluable_rows}")
    print(f"Output:                 {output_table}")
    print(f"QC:                     {qc_file}")


if __name__ == "__main__":
    main()

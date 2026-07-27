#!/usr/bin/env python3
"""Shared inheritance-model parsing and transparent compatibility scoring.

The functions in this module are deliberately independent of any patient,
gene, disease, rsID, or validation case. They provide one precedence-aware
interpretation layer for small variants, CNVs, and weighted evidence scoring.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class InheritanceModel:
    model: str
    normalized_requirement: str
    chromosome_class: str
    allele_requirement: str


def clean(value: object) -> str:
    return str(value or "").strip()


def normalize_requirement(value: object) -> str:
    text = clean(value).lower()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def is_x_requirement(value: object) -> bool:
    requirement = normalize_requirement(value)
    return (
        "x_linked" in requirement
        or "x-linked" in requirement
        or "_x_" in requirement
        or requirement.startswith("x_")
        or requirement.endswith("_x")
        or "x_chromosome" in requirement
    )


def is_mitochondrial_requirement(value: object) -> bool:
    requirement = normalize_requirement(value)
    return any(
        token in requirement
        for token in (
            "mitochond",
            "maternal_inheritance",
            "maternally_inherited",
            "mt_dna",
            "mtdna",
        )
    )


def classify_inheritance_model(value: object) -> InheritanceModel:
    requirement = normalize_requirement(value)

    if not requirement:
        return InheritanceModel(
            model="unknown",
            normalized_requirement="",
            chromosome_class="unknown",
            allele_requirement="unknown",
        )

    if is_mitochondrial_requirement(requirement):
        return InheritanceModel(
            model="mitochondrial",
            normalized_requirement=requirement,
            chromosome_class="mitochondrial",
            allele_requirement="variant_present",
        )

    if is_x_requirement(requirement):
        if "biallelic" in requirement:
            model = "x_linked_biallelic"
            allele_requirement = "biallelic"
        elif "hemizyg" in requirement:
            model = "x_linked_hemizygous"
            allele_requirement = "hemizygous"
        elif "heterozyg" in requirement:
            model = "x_linked_heterozygous"
            allele_requirement = "heterozygous"
        elif "recessive" in requirement:
            model = "x_linked_recessive"
            allele_requirement = "sex_dependent"
        elif "dominant" in requirement:
            model = "x_linked_dominant"
            allele_requirement = "monoallelic"
        else:
            model = "x_linked"
            allele_requirement = "sex_dependent"

        return InheritanceModel(
            model=model,
            normalized_requirement=requirement,
            chromosome_class="X",
            allele_requirement=allele_requirement,
        )

    if (
        "biallelic" in requirement
        or "autosomal_recessive" in requirement
        or requirement in {"ar", "recessive"}
    ):
        return InheritanceModel(
            model="autosomal_recessive",
            normalized_requirement=requirement,
            chromosome_class="autosomal",
            allele_requirement="biallelic",
        )

    if (
        "monoallelic" in requirement
        or "autosomal_dominant" in requirement
        or requirement in {"ad", "dominant"}
    ):
        return InheritanceModel(
            model="autosomal_dominant",
            normalized_requirement=requirement,
            chromosome_class="autosomal",
            allele_requirement="monoallelic",
        )

    return InheritanceModel(
        model="unknown",
        normalized_requirement=requirement,
        chromosome_class="unknown",
        allele_requirement="unknown",
    )


def variant_is_present(zygosity: object) -> bool:
    value = clean(zygosity).lower()
    return value in {
        "heterozygous",
        "homozygous_alt",
        "hemizygous_or_haploid_alt",
        "multiallelic_alt",
    }


def score_small_variant_inheritance(
    requirement: object,
    zygosity: object,
) -> tuple[int, str]:
    model = classify_inheritance_model(requirement)
    z = clean(zygosity).lower()

    if model.model == "autosomal_recessive":
        if z == "homozygous_alt":
            return 3, "compatible_biallelic_homozygous"
        if z == "heterozygous":
            return 0, "single_heterozygous_recessive_allele"
        return 0, "biallelic_requirement_not_confirmed"

    if model.model == "autosomal_dominant":
        if z == "heterozygous":
            return 3, "compatible_monoallelic_heterozygous"
        if z == "homozygous_alt":
            return 1, "alternate_allele_present_but_unusual"
        return 0, "monoallelic_requirement_not_confirmed"

    if model.model.startswith("x_linked"):
        if z == "hemizygous_or_haploid_alt":
            if model.model == "x_linked_biallelic":
                return 1, "hemizygous_x_variant_but_biallelic_model"
            return 3, "compatible_hemizygous_x_linked"

        if z == "homozygous_alt":
            return 3, "compatible_biallelic_x_linked"

        if z == "heterozygous":
            if model.model == "x_linked_biallelic":
                return 0, "single_heterozygous_x_linked_allele"
            return 1, "possible_heterozygous_x_linked"

        return 0, "x_linked_requirement_not_confirmed"

    if model.model == "mitochondrial":
        if variant_is_present(z):
            return (
                2,
                "mitochondrial_variant_present_heteroplasmy_not_assessed",
            )
        return 0, "mitochondrial_variant_not_confirmed"

    return 0, "inheritance_not_scored"


def score_cnv_inheritance(
    requirement: object,
    zygosity: object,
) -> tuple[int, str]:
    model = classify_inheritance_model(requirement)
    z = clean(zygosity).lower()

    if model.model == "autosomal_recessive":
        if z == "homozygous_alt":
            return 3, "compatible_biallelic_homozygous"
        if z == "heterozygous":
            return 0, "single_recessive_CNV_allele"
        return 0, "biallelic_status_not_confirmed"

    if model.model == "autosomal_dominant":
        if z == "heterozygous":
            return 3, "compatible_monoallelic_heterozygous"
        if z == "homozygous_alt":
            return 2, "alternate_allele_present"
        return 0, "monoallelic_status_not_confirmed"

    if model.model.startswith("x_linked"):
        if z == "hemizygous_or_haploid_alt":
            if model.model == "x_linked_biallelic":
                return 1, "hemizygous_x_CNV_but_biallelic_model"
            return 3, "compatible_x_linked_hemizygous"

        if z == "homozygous_alt":
            return 3, "compatible_biallelic_x_linked"

        if z == "heterozygous":
            if model.model == "x_linked_biallelic":
                return 0, "single_heterozygous_x_linked_CNV_allele"
            return 1, "possible_x_linked_heterozygous"

        return 0, "x_linked_status_not_confirmed"

    if model.model == "mitochondrial":
        if variant_is_present(z):
            return (
                2,
                "mitochondrial_CNV_or_copy_state_present_review_required",
            )
        return 0, "mitochondrial_copy_state_not_confirmed"

    return 0, "inheritance_not_scored"

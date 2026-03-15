from __future__ import annotations

import re


FIELDS = ("ti", "abs", "co")


def _quote(term: str) -> str:
    stripped = term.strip()
    if re.search(r"[\s-]", stripped):
        return f'"{stripped}"'
    return stripped


def _field_or(term: str) -> str:
    quoted = _quote(term)
    return "(" + " OR ".join(f"{field}:{quoted}" for field in FIELDS) + ")"


def _expand_variants(keyword: str) -> list[str]:
    stripped = keyword.strip()
    variants = {stripped}
    if " " in stripped:
        variants.add(stripped.replace(" ", "-"))
    if "-" in stripped:
        variants.add(stripped.replace("-", " "))
    return sorted(variants, key=len, reverse=True)


def _keyword_group(keyword: str) -> str:
    parts = [_field_or(variant) for variant in _expand_variants(keyword)]
    lowered = keyword.lower()
    if ("open vocabulary" in lowered or "open-vocabulary" in lowered) and "segmentation" in lowered:
        open_vocab_terms = [
            "open vocabulary",
            "open-vocabulary",
            "open vocabulary segmentation",
            "open-vocabulary segmentation",
        ]
        segmentation_terms = ["segmentation", "image segmentation"]
        open_vocab_group = "(" + " OR ".join(_field_or(term) for term in open_vocab_terms) + ")"
        segmentation_group = "(" + " OR ".join(_field_or(term) for term in segmentation_terms) + ")"
        parts.append(f"({open_vocab_group} AND {segmentation_group})")
    return "(" + " OR ".join(parts) + ")"


def build_search_query(
    categories: list[str],
    keywords: list[str],
    exclude_keywords: list[str] | None = None,
    logic: str = "AND",
) -> str:
    normalized_categories = [category.strip() for category in categories if category and category.strip()]
    normalized_keywords = [keyword.strip() for keyword in keywords if keyword and keyword.strip()]
    normalized_excludes = [keyword.strip() for keyword in (exclude_keywords or []) if keyword and keyword.strip()]

    category_query = ""
    keyword_query = ""
    exclude_query = ""

    if normalized_categories:
        category_query = "(" + " OR ".join(f"cat:{category}" for category in normalized_categories) + ")"
    if normalized_keywords:
        keyword_query = "(" + " OR ".join(_keyword_group(keyword) for keyword in normalized_keywords) + ")"
    if normalized_excludes:
        exclude_query = " AND NOT (" + " OR ".join(_keyword_group(keyword) for keyword in normalized_excludes) + ")"

    positive_query = "all:*"
    if category_query and keyword_query:
        operator = "AND" if (logic or "AND").upper() == "AND" else "OR"
        positive_query = f"({category_query} {operator} {keyword_query})"
    elif category_query:
        positive_query = category_query
    elif keyword_query:
        positive_query = keyword_query

    return positive_query + exclude_query

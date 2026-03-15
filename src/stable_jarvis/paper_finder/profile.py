from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_STATE_PATH = ".state/paper_finder_seen.json"


@dataclass(slots=True)
class ZoteroBasis:
    collections: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: str | None = None


@dataclass(slots=True)
class RetrievalDefaults:
    logic: str = "AND"
    sort_by: str = "lastUpdatedDate"
    sort_order: str = "descending"
    since_days: int = 7
    max_results_per_interest: int = 10
    max_pages: int = 10
    state_path: str = DEFAULT_STATE_PATH


@dataclass(slots=True)
class Interest:
    interest_id: str
    label: str
    enabled: bool = True
    categories: list[str] = field(default_factory=list)
    method_keywords: list[str] = field(default_factory=list)
    query_aliases: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)
    logic: str = "AND"
    notes: str | None = None


@dataclass(slots=True)
class ResearchProfile:
    schema_version: str
    profile_id: str
    profile_name: str
    updated_at: str | None = None
    maintainer: str | None = None
    zotero_basis: ZoteroBasis = field(default_factory=ZoteroBasis)
    retrieval_defaults: RetrievalDefaults = field(default_factory=RetrievalDefaults)
    interests: list[Interest] = field(default_factory=list)


def _ensure_str_list(values: object, field_name: str) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list")
    return [str(value).strip() for value in values if str(value).strip()]


def load_profile(path: str | Path) -> ResearchProfile:
    profile_path = Path(path)
    raw = json.loads(profile_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Profile root must be a JSON object")

    schema_version = str(raw.get("schema_version") or "").strip()
    profile_id = str(raw.get("profile_id") or "").strip()
    profile_name = str(raw.get("profile_name") or "").strip()
    if not schema_version or not profile_id or not profile_name:
        raise ValueError("Profile must include schema_version, profile_id, and profile_name")

    basis_raw = raw.get("zotero_basis") or {}
    defaults_raw = raw.get("retrieval_defaults") or {}
    interests_raw = raw.get("interests") or []
    if not isinstance(basis_raw, dict) or not isinstance(defaults_raw, dict) or not isinstance(interests_raw, list):
        raise ValueError("Profile sections have invalid types")

    interests: list[Interest] = []
    for index, interest_raw in enumerate(interests_raw):
        if not isinstance(interest_raw, dict):
            raise ValueError(f"interests[{index}] must be an object")
        interest_id = str(interest_raw.get("interest_id") or "").strip()
        label = str(interest_raw.get("label") or "").strip()
        if not interest_id or not label:
            raise ValueError(f"interests[{index}] must include interest_id and label")
        interests.append(
            Interest(
                interest_id=interest_id,
                label=label,
                enabled=bool(interest_raw.get("enabled", True)),
                categories=_ensure_str_list(interest_raw.get("categories"), f"interests[{index}].categories"),
                method_keywords=_ensure_str_list(interest_raw.get("method_keywords"), f"interests[{index}].method_keywords"),
                query_aliases=_ensure_str_list(interest_raw.get("query_aliases"), f"interests[{index}].query_aliases"),
                exclude_keywords=_ensure_str_list(interest_raw.get("exclude_keywords"), f"interests[{index}].exclude_keywords"),
                logic=str(interest_raw.get("logic") or defaults_raw.get("logic") or "AND").upper(),
                notes=str(interest_raw.get("notes") or "").strip() or None,
            )
        )

    return ResearchProfile(
        schema_version=schema_version,
        profile_id=profile_id,
        profile_name=profile_name,
        updated_at=str(raw.get("updated_at") or "").strip() or None,
        maintainer=str(raw.get("maintainer") or "").strip() or None,
        zotero_basis=ZoteroBasis(
            collections=_ensure_str_list(basis_raw.get("collections"), "zotero_basis.collections"),
            tags=_ensure_str_list(basis_raw.get("tags"), "zotero_basis.tags"),
            notes=str(basis_raw.get("notes") or "").strip() or None,
        ),
        retrieval_defaults=RetrievalDefaults(
            logic=str(defaults_raw.get("logic") or "AND").upper(),
            sort_by=str(defaults_raw.get("sort_by") or "lastUpdatedDate"),
            sort_order=str(defaults_raw.get("sort_order") or "descending"),
            since_days=int(defaults_raw.get("since_days") or 7),
            max_results_per_interest=int(defaults_raw.get("max_results_per_interest") or 10),
            max_pages=int(defaults_raw.get("max_pages") or 10),
            state_path=str(defaults_raw.get("state_path") or DEFAULT_STATE_PATH),
        ),
        interests=interests,
    )

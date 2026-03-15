from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

from .candidate import CandidateCard, PaperInfo
from .client import fetch_arxiv_feed
from .parser import ParsedArxivEntry, parse_feed
from .profile import Interest, ResearchProfile
from .query import build_search_query


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _iso_now() -> str:
    return _now_utc().isoformat()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "paper"


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _load_seen_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {str(value).strip() for value in raw if str(value).strip()}
    if isinstance(raw, dict):
        values = raw.get("seen_ids") or []
        return {str(value).strip() for value in values if str(value).strip()}
    return set()


def _save_seen_ids(path: Path, seen_ids: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"seen_ids": sorted(seen_ids), "updated_at": _iso_now()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _select_keywords(interest: Interest) -> list[str]:
    keywords: list[str] = []
    for value in interest.method_keywords[:2]:
        if value not in keywords:
            keywords.append(value)
    for value in interest.query_aliases[:2]:
        if value not in keywords:
            keywords.append(value)
    return keywords[:4]


def _build_candidate(
    entry: ParsedArxivEntry,
    *,
    interest: Interest,
    profile: ResearchProfile,
    batch_id: str,
    query_text: str,
    generated_at: str,
) -> CandidateCard:
    identifier = entry.arxiv_id or _slug(entry.title)
    published_at = _parse_datetime(entry.published)
    return CandidateCard(
        candidate_id=f"arxiv-{_slug(identifier)}",
        batch_id=batch_id,
        generated_at=generated_at,
        collected_at=generated_at,
        retrieval_profile_id=profile.profile_id,
        query_label=interest.label,
        query_text=query_text,
        paper=PaperInfo(
            title=entry.title,
            authors=entry.authors,
            venue=entry.venue_inferred,
            year=published_at.year if published_at is not None else None,
            categories=entry.categories,
            abstract=entry.summary,
            arxiv_id=entry.arxiv_id,
            url=entry.html_url,
            pdf_url=entry.pdf_url,
            comments=entry.comments,
            journal_ref=entry.journal_ref,
            code_urls=entry.code_urls,
            project_urls=entry.project_urls,
            other_urls=entry.other_urls,
            published=entry.published,
            updated=entry.updated,
        ),
    )


def _merge_interest(candidate: CandidateCard, interest: Interest) -> None:
    if interest.interest_id not in candidate.triage.matched_interest_ids:
        candidate.triage.matched_interest_ids.append(interest.interest_id)
    if interest.label not in candidate.triage.matched_interest_labels:
        candidate.triage.matched_interest_labels.append(interest.label)


def run_retrieval(
    profile: ResearchProfile,
    state_path: str | Path | None = None,
    since_days: int | None = None,
) -> list[CandidateCard]:
    generated_at = _iso_now()
    batch_id = _now_utc().strftime("%Y%m%dT%H%M%SZ")
    effective_since_days = since_days if since_days is not None else profile.retrieval_defaults.since_days
    cutoff = _now_utc() - timedelta(days=effective_since_days)

    effective_state_path = Path(state_path or profile.retrieval_defaults.state_path)
    seen_ids = _load_seen_ids(effective_state_path)
    updated_seen_ids = set(seen_ids)
    candidates_by_arxiv_id: dict[str, CandidateCard] = {}

    for interest in profile.interests:
        if not interest.enabled:
            continue
        query_text = build_search_query(
            interest.categories,
            _select_keywords(interest),
            exclude_keywords=interest.exclude_keywords,
            logic=interest.logic or profile.retrieval_defaults.logic,
        )
        collected = 0
        page_size = min(50, max(profile.retrieval_defaults.max_results_per_interest, 1))
        for page_index in range(profile.retrieval_defaults.max_pages):
            if collected >= profile.retrieval_defaults.max_results_per_interest:
                break
            xml_text = fetch_arxiv_feed(
                query_text,
                start=page_index * page_size,
                max_results=page_size,
                sort_by=profile.retrieval_defaults.sort_by,
                sort_order=profile.retrieval_defaults.sort_order,
            )
            entries = parse_feed(xml_text)
            if not entries:
                break

            stop_paging = False
            for entry in entries:
                updated_at = _parse_datetime(entry.updated or entry.published)
                if updated_at is not None and updated_at < cutoff:
                    stop_paging = True
                    continue
                arxiv_id = str(entry.arxiv_id or "").strip()
                if not arxiv_id or arxiv_id in seen_ids:
                    continue
                if arxiv_id in candidates_by_arxiv_id:
                    _merge_interest(candidates_by_arxiv_id[arxiv_id], interest)
                    continue

                candidate = _build_candidate(
                    entry,
                    interest=interest,
                    profile=profile,
                    batch_id=batch_id,
                    query_text=query_text,
                    generated_at=generated_at,
                )
                _merge_interest(candidate, interest)
                if not candidate.paper.abstract:
                    candidate.triage.abstract_status = "missing"
                candidates_by_arxiv_id[arxiv_id] = candidate
                updated_seen_ids.add(arxiv_id)
                collected += 1
                if collected >= profile.retrieval_defaults.max_results_per_interest:
                    break
            if stop_paging:
                break

    _save_seen_ids(effective_state_path, updated_seen_ids)
    return list(candidates_by_arxiv_id.values())

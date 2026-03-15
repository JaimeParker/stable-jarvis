from __future__ import annotations

import copy
import math
import re
from collections.abc import Callable
from typing import Any

from .candidate import CandidateCard, ScoreSummary, SemanticNeighbor
from .profile import ResearchProfile


SemanticSearchFn = Callable[[str, int], dict[str, Any]]


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{2,}", text.lower()))


def _paper_tokens(candidate: CandidateCard) -> set[str]:
    return _tokenize(
        " ".join(
            [
                candidate.paper.title or "",
                candidate.paper.abstract or "",
                " ".join(candidate.paper.categories),
            ]
        )
    )


def _phrase_score(paper_tokens: set[str], phrases: list[str]) -> float:
    best = 0.0
    for phrase in phrases:
        phrase_tokens = _tokenize(phrase)
        if not phrase_tokens:
            continue
        overlap = len(paper_tokens & phrase_tokens)
        best = max(best, min(overlap / len(phrase_tokens), 1.0))
    return min(best, 1.0)


def score_map_match(candidate: CandidateCard, profile: ResearchProfile) -> float:
    paper_tokens = _paper_tokens(candidate)
    if not paper_tokens:
        return 0.0

    paper_categories = {category.strip().lower() for category in candidate.paper.categories if category.strip()}
    matched_interest_ids = set(candidate.triage.matched_interest_ids)

    best = 0.0
    for interest in profile.interests:
        if not interest.enabled:
            continue
        if matched_interest_ids and interest.interest_id not in matched_interest_ids:
            continue
        method_score = _phrase_score(paper_tokens, interest.method_keywords)
        alias_score = _phrase_score(paper_tokens, interest.query_aliases)
        interest_categories = {category.strip().lower() for category in interest.categories if category.strip()}
        category_score = 1.0 if paper_categories.intersection(interest_categories) else 0.0
        interest_score = (0.65 * method_score) + (0.20 * alias_score) + (0.15 * category_score)
        best = max(best, interest_score)

    return round(min(best, 1.0), 4)


def _semantic_query(candidate: CandidateCard) -> str:
    title = " ".join((candidate.paper.title or "").split())
    abstract = " ".join((candidate.paper.abstract or "").split())
    if abstract:
        return f"{title}. {abstract[:800]}"
    return title


def _distance_to_affinity(distance: float | None) -> float:
    if not isinstance(distance, (int, float)):
        return 0.0
    return 1.0 / (1.0 + max(float(distance), 0.0))


def _normalize_semantic_scores(raw_scores: dict[str, float]) -> dict[str, float]:
    if not raw_scores:
        return {}
    values = list(raw_scores.values())
    min_value = min(values)
    max_value = max(values)
    if math.isclose(min_value, max_value, rel_tol=1e-9, abs_tol=1e-9):
        return {candidate_id: round(values[0], 4) for candidate_id in raw_scores}
    span = max_value - min_value
    return {candidate_id: round((raw_value - min_value) / span, 4) for candidate_id, raw_value in raw_scores.items()}


def collect_semantic_scores(
    candidates: list[CandidateCard],
    *,
    semantic_search_fn: SemanticSearchFn | None,
    semantic_limit: int = 3,
) -> tuple[dict[str, float], dict[str, dict[str, Any]]]:
    if semantic_search_fn is None:
        return {}, {}

    raw_scores: dict[str, float] = {}
    evidence: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        try:
            payload = semantic_search_fn(_semantic_query(candidate), semantic_limit)
        except Exception:
            continue
        results = payload.get("results", []) if isinstance(payload, dict) else []
        if not results:
            evidence[candidate.candidate_id] = {"count": 0, "best_distance": None}
            continue
        distances = [
            float(result["distance"])
            for result in results
            if isinstance(result.get("distance"), (int, float))
        ]
        best_distance = min(distances) if distances else None
        raw_scores[candidate.candidate_id] = _distance_to_affinity(best_distance)
        evidence[candidate.candidate_id] = {
            "count": len(results),
            "best_distance": best_distance,
            "top_item_key": results[0].get("item_key"),
            "top_title": (results[0].get("metadata") or {}).get("title"),
            "neighbors": results,
        }
    return _normalize_semantic_scores(raw_scores), evidence


def rank_candidates(
    candidates: list[CandidateCard],
    profile: ResearchProfile,
    *,
    semantic_search_fn: SemanticSearchFn | None = None,
    semantic_limit: int = 3,
    w_map_match: float = 0.30,
    w_zotero_semantic: float = 0.70,
    min_map_match: float = 0.30,
    low_map_penalty: float = 0.75,
) -> list[CandidateCard]:
    semantic_scores, semantic_evidence = collect_semantic_scores(
        candidates,
        semantic_search_fn=semantic_search_fn,
        semantic_limit=semantic_limit,
    )
    semantic_available = bool(semantic_scores)

    ranked: list[CandidateCard] = []
    for candidate in candidates:
        ranked_candidate = copy.deepcopy(candidate)
        map_match = score_map_match(ranked_candidate, profile)
        zotero_semantic = semantic_scores.get(ranked_candidate.candidate_id, 0.0)
        total = (w_map_match * map_match) + (w_zotero_semantic * zotero_semantic) if semantic_available else map_match
        penalty_applied = False
        if map_match < min_map_match:
            total *= low_map_penalty
            penalty_applied = True

        evidence = semantic_evidence.get(ranked_candidate.candidate_id, {})
        neighbors = [
            SemanticNeighbor(
                item_key=result.get("item_key"),
                title=(result.get("metadata") or {}).get("title"),
                collections=list((result.get("metadata") or {}).get("collections") or []),
                distance=result.get("distance"),
            )
            for result in evidence.get("neighbors", [])
        ]
        ranked_candidate.scores = ScoreSummary(
            map_match=round(map_match, 4),
            zotero_semantic=round(zotero_semantic, 4),
            total=round(total, 4),
            weights={
                "map_match": round(w_map_match, 4),
                "zotero_semantic": round(w_zotero_semantic, 4) if semantic_available else 0.0,
            },
            min_map_match=round(min_map_match, 4),
            low_map_penalty=round(low_map_penalty, 4),
            penalty_applied=penalty_applied,
            semantic_available=semantic_available,
            semantic_best_distance=evidence.get("best_distance"),
            semantic_neighbor_count=evidence.get("count", 0),
            semantic_top_item_key=evidence.get("top_item_key"),
            semantic_top_title=evidence.get("top_title"),
            semantic_neighbors=neighbors,
        )
        ranked.append(ranked_candidate)

    ranked.sort(key=lambda item: item.scores.total, reverse=True)
    return ranked

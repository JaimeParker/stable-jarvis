from __future__ import annotations

import re

from .candidate import CandidateCard, ReviewBlock, ZoteroComparison
from .profile import ResearchProfile


def _first_sentence(text: str, *, max_length: int = 220) -> str | None:
    normalized = " ".join((text or "").split())
    if not normalized:
        return None
    parts = re.split(r"(?<=[.!?])\s+", normalized, maxsplit=1)
    sentence = parts[0].strip() if parts else normalized
    if len(sentence) <= max_length:
        return sentence
    return sentence[: max_length - 1].rstrip() + "..."


def _recommendation_from_scores(candidate: CandidateCard) -> str:
    total = candidate.scores.total
    map_match = candidate.scores.map_match
    zotero_semantic = candidate.scores.zotero_semantic
    if total >= 0.72 and map_match >= 0.55:
        return "read_first"
    if total >= 0.55 and map_match >= 0.40:
        return "skim"
    if map_match >= 0.28 or zotero_semantic >= 0.45:
        return "watch"
    return "skip_for_now"


def _recommendation_label(value: str) -> str:
    labels = {
        "read_first": "Read First",
        "skim": "Skim",
        "watch": "Watch",
        "skip_for_now": "Skip for now",
        "unset": "Unset",
    }
    return labels.get(value, value.replace("_", " ").title())


def _strongest_signal(candidate: CandidateCard) -> str | None:
    components = {
        "research-map fit": candidate.scores.map_match,
        "zotero semantic affinity": candidate.scores.zotero_semantic,
    }
    label, value = max(components.items(), key=lambda item: item[1])
    return label if value > 0 else None


def build_system_review(candidate: CandidateCard, profile: ResearchProfile | None = None) -> ReviewBlock:
    matched_labels = [label for label in candidate.triage.matched_interest_labels if label.strip()]
    recommendation = _recommendation_from_scores(candidate)
    recommendation_label = _recommendation_label(recommendation)

    why_parts: list[str] = []
    if matched_labels:
        if len(matched_labels) == 1:
            why_parts.append(f"Matches your active profile interest in {matched_labels[0]}.")
        else:
            why_parts.append("Matches multiple active profile interests: " + ", ".join(matched_labels[:3]) + ".")
    elif profile is not None:
        why_parts.append("Retrieved as an exploratory paper; direct profile-match labels are weak.")
    else:
        why_parts.append("Profile context was not available when this digest note was generated.")

    if candidate.scores.map_match >= 0.70:
        why_parts.append("Research-map fit is strong for the active profile slices.")
    elif candidate.scores.map_match >= 0.45:
        why_parts.append("Research-map fit is moderate and worth a targeted skim.")
    else:
        why_parts.append("Research-map fit is limited, so treat this as lower-confidence triage.")

    if candidate.scores.zotero_semantic >= 0.65:
        why_parts.append("It also sits close to existing Zotero literature in your library.")
    elif candidate.scores.zotero_semantic > 0:
        why_parts.append("Zotero semantic evidence is present, but not especially concentrated.")
    why_parts.append(f"Current system recommendation: {recommendation_label}.")

    quick_takeaways = [f"Recommendation: {recommendation_label}"]
    if matched_labels:
        quick_takeaways.append("Matched interests: " + ", ".join(matched_labels[:3]))
    strongest_signal = _strongest_signal(candidate)
    if strongest_signal is not None:
        quick_takeaways.append(f"Strongest signal: {strongest_signal}")
    if candidate.scores.total > 0:
        quick_takeaways.append(f"Ranking score: {candidate.scores.total:.2f}")

    caveats: list[str] = []
    if not candidate.paper.abstract:
        caveats.append("Abstract is missing, so the note is title-led.")
    if not matched_labels:
        caveats.append("No strong matched-interest label was attached to this candidate.")
    caveats.append("Zotero comparison has not been run in digest mode yet.")
    caveats.append("Recommendation is generated from profile labels and ranking signals, not full-text review.")

    return ReviewBlock(
        review_status="system_generated",
        recommendation=recommendation,
        reviewer_summary=candidate.review.reviewer_summary or _first_sentence(candidate.paper.abstract or ""),
        why_it_matters=" ".join(why_parts),
        quick_takeaways=quick_takeaways,
        caveats=caveats,
        zotero_comparison=candidate.review.zotero_comparison or ZoteroComparison(),
        generation={
            "mode": "system_profile_only",
            "sources": ["matched_interest_labels", "map_semantic_scores", "abstract_first_sentence"],
        },
    )


def enrich_candidates_with_system_review(
    candidates: list[CandidateCard],
    profile: ResearchProfile | None = None,
) -> list[CandidateCard]:
    enriched: list[CandidateCard] = []
    for candidate in candidates:
        candidate.review = build_system_review(candidate, profile)
        enriched.append(candidate)
    return enriched

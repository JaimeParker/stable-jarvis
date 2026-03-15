from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SemanticNeighbor:
    item_key: str | None = None
    title: str | None = None
    collections: list[str] = field(default_factory=list)
    distance: float | None = None


@dataclass(slots=True)
class ScoreSummary:
    map_match: float = 0.0
    zotero_semantic: float = 0.0
    total: float = 0.0
    model: str = "map_semantic_v1"
    weights: dict[str, float] = field(default_factory=lambda: {"map_match": 0.3, "zotero_semantic": 0.7})
    min_map_match: float = 0.3
    low_map_penalty: float = 0.75
    penalty_applied: bool = False
    semantic_available: bool = False
    semantic_best_distance: float | None = None
    semantic_neighbor_count: int = 0
    semantic_top_item_key: str | None = None
    semantic_top_title: str | None = None
    semantic_neighbors: list[SemanticNeighbor] = field(default_factory=list)


@dataclass(slots=True)
class ZoteroComparison:
    status: str = "not_run"
    summary: str = "Zotero comparison is not generated during digest rendering yet."
    related_items: list[dict[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class ReviewBlock:
    review_status: str = "unreviewed"
    recommendation: str = "unset"
    reviewer_summary: str | None = None
    why_it_matters: str | None = None
    quick_takeaways: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    zotero_comparison: ZoteroComparison = field(default_factory=ZoteroComparison)
    generation: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class TriageInfo:
    extraction_confidence: float = 1.0
    abstract_status: str = "available"
    duplicate_hint: str | None = None
    matched_interest_ids: list[str] = field(default_factory=list)
    matched_interest_labels: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PaperInfo:
    title: str
    authors: list[str] = field(default_factory=list)
    venue: str | None = None
    year: int | None = None
    categories: list[str] = field(default_factory=list)
    abstract: str | None = None
    arxiv_id: str | None = None
    doi: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    comments: str | None = None
    journal_ref: str | None = None
    code_urls: list[str] = field(default_factory=list)
    project_urls: list[str] = field(default_factory=list)
    other_urls: list[str] = field(default_factory=list)
    published: str | None = None
    updated: str | None = None


@dataclass(slots=True)
class CandidateCard:
    candidate_id: str
    batch_id: str
    generated_at: str
    source_kind: str = "arxiv_query"
    collected_at: str | None = None
    retrieval_profile_id: str | None = None
    query_label: str | None = None
    query_text: str | None = None
    paper: PaperInfo = field(default_factory=lambda: PaperInfo(title=""))
    triage: TriageInfo = field(default_factory=TriageInfo)
    review: ReviewBlock = field(default_factory=ReviewBlock)
    scores: ScoreSummary = field(default_factory=ScoreSummary)
    note_path: str | None = None

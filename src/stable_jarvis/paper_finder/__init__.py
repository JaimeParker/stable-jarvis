from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .candidate import CandidateCard
from .obsidian import write_notes
from .profile import ResearchProfile, load_profile
from .ranker import rank_candidates
from .retrieval import run_retrieval
from .review import enrich_candidates_with_system_review


@dataclass(slots=True)
class PaperFinderConfig:
    profile_path: str | Path
    output_dir: str | Path
    state_path: str | Path | None = None
    since_days: int | None = None
    semantic_search_fn: Any = None
    semantic_config: Any = None
    semantic_limit: int = 3
    overwrite: bool = False


def _resolve_semantic_search_fn(config: PaperFinderConfig):
    if config.semantic_search_fn is not None:
        return config.semantic_search_fn
    if config.semantic_config is None:
        return None
    from .semantic import SemanticConfig, build_semantic_search_fn

    semantic_config = config.semantic_config
    if isinstance(semantic_config, dict):
        semantic_config = SemanticConfig(**semantic_config)
    return build_semantic_search_fn(semantic_config)


def run_paper_finder(config: PaperFinderConfig) -> tuple[ResearchProfile, list[CandidateCard]]:
    profile = load_profile(config.profile_path)
    candidates = run_retrieval(profile, state_path=config.state_path, since_days=config.since_days)
    semantic_search_fn = _resolve_semantic_search_fn(config)
    ranked = rank_candidates(
        candidates,
        profile,
        semantic_search_fn=semantic_search_fn,
        semantic_limit=config.semantic_limit,
    )
    reviewed = enrich_candidates_with_system_review(ranked, profile)
    write_notes(reviewed, config.output_dir, overwrite=config.overwrite)
    return profile, reviewed


def find_papers(
    profile_path: str | Path,
    output_dir: str | Path,
    *,
    since_days: int | None = None,
    state_path: str | Path | None = None,
    semantic_search_fn: Any = None,
    semantic_config: Any = None,
    semantic_limit: int = 3,
    overwrite: bool = False,
) -> list[CandidateCard]:
    config = PaperFinderConfig(
        profile_path=profile_path,
        output_dir=output_dir,
        state_path=state_path,
        since_days=since_days,
        semantic_search_fn=semantic_search_fn,
        semantic_config=semantic_config,
        semantic_limit=semantic_limit,
        overwrite=overwrite,
    )
    _, candidates = run_paper_finder(config)
    return candidates


__all__ = [
    "CandidateCard",
    "PaperFinderConfig",
    "find_papers",
    "load_profile",
    "run_paper_finder",
]
from __future__ import annotations

from pathlib import Path

from .candidate import CandidateCard, SemanticNeighbor


def _yaml_scalar(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    escaped = text.replace('"', '\\"')
    return f'"{escaped}"'


def _yaml_list(key: str, values: list[object]) -> list[str]:
    if not values:
        return [f"{key}: []"]
    lines = [f"{key}:"]
    for value in values:
        lines.append(f"  - {_yaml_scalar(value)}")
    return lines


def _render_neighbors(neighbors: list[SemanticNeighbor]) -> list[str]:
    if not neighbors:
        return ["No semantic neighbors were attached."]
    lines: list[str] = []
    for neighbor in neighbors:
        title = neighbor.title or neighbor.item_key or "Untitled Zotero item"
        suffix = f" (distance: {neighbor.distance:.4f})" if isinstance(neighbor.distance, (int, float)) else ""
        lines.append(f"- {title}{suffix}")
        if neighbor.collections:
            lines.append(f"  Collections: {', '.join(neighbor.collections)}")
    return lines


def render_obsidian_note(candidate: CandidateCard) -> str:
    frontmatter: list[str] = ["---"]
    frontmatter.append(f"title: {_yaml_scalar(candidate.paper.title)}")
    frontmatter.extend(_yaml_list("authors", candidate.paper.authors))
    frontmatter.append(f"year: {_yaml_scalar(candidate.paper.year)}")
    frontmatter.append(f"arxiv_id: {_yaml_scalar(candidate.paper.arxiv_id)}")
    frontmatter.append(f"doi: {_yaml_scalar(candidate.paper.doi)}")
    frontmatter.append(f"url: {_yaml_scalar(candidate.paper.url)}")
    frontmatter.append(f"pdf_url: {_yaml_scalar(candidate.paper.pdf_url)}")
    frontmatter.extend(_yaml_list("categories", candidate.paper.categories))
    frontmatter.append(f"recommendation: {_yaml_scalar(candidate.review.recommendation)}")
    frontmatter.append(f"map_match_score: {candidate.scores.map_match:.4f}")
    frontmatter.append(f"semantic_score: {candidate.scores.zotero_semantic:.4f}")
    frontmatter.append(f"total_score: {candidate.scores.total:.4f}")
    tags = [f"arxiv/{category.lower()}" for category in candidate.paper.categories]
    tags.append(f"recommendation/{candidate.review.recommendation}")
    frontmatter.extend(_yaml_list("tags", tags))
    frontmatter.extend(_yaml_list("matched_interests", candidate.triage.matched_interest_labels))
    frontmatter.append("---")

    body = [
        f"# {candidate.paper.title}",
        "",
        "## Abstract",
        candidate.paper.abstract or "No abstract was available from arXiv.",
        "",
        "## Why It Matters",
        candidate.review.why_it_matters or "Not yet enriched.",
        "",
        "## Quick Takeaways",
    ]
    body.extend([f"- {item}" for item in candidate.review.quick_takeaways] or ["- No takeaways yet."])
    body.extend([
        "",
        "## Caveats",
    ])
    body.extend([f"- {item}" for item in candidate.review.caveats] or ["- No caveats recorded."])
    body.extend([
        "",
        "## Related",
    ])
    body.extend(_render_neighbors(candidate.scores.semantic_neighbors))
    body.extend([
        "",
        "## Links",
    ])
    if candidate.paper.url:
        body.append(f"- arXiv: {candidate.paper.url}")
    if candidate.paper.pdf_url:
        body.append(f"- PDF: {candidate.paper.pdf_url}")
    for url in candidate.paper.code_urls:
        body.append(f"- Code: {url}")
    for url in candidate.paper.project_urls:
        body.append(f"- Project: {url}")
    for url in candidate.paper.other_urls:
        body.append(f"- Link: {url}")
    if len(body) == 2:
        body.append("- No links extracted.")
    return "\n".join(frontmatter + [""] + body).strip() + "\n"


def write_notes(candidates: list[CandidateCard], output_dir: str | Path, overwrite: bool = False) -> list[Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []
    for candidate in candidates:
        identifier = candidate.paper.arxiv_id or candidate.candidate_id
        note_path = directory / f"{identifier}.md"
        if note_path.exists() and not overwrite:
            written_paths.append(note_path)
            candidate.note_path = str(note_path)
            continue
        note_path.write_text(render_obsidian_note(candidate), encoding="utf-8")
        written_paths.append(note_path)
        candidate.note_path = str(note_path)
    return written_paths

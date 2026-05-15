#!/usr/bin/env python3
"""Semantic search over Obsidian vault notes using configurable embeddings.

Modes:
    --build      Walk vault, embed all .md notes, save cache to JSON
    --embed Q    Embed query Q, compute cosine vs cache, print top-k results as JSON
    --content Q  No-op: just print the query (content search is done via Obsidian MCP)

The script delegates embedding to research_helper.kb.embedder (qwen/openai/local).
Set EMBEDDING_PROVIDER env var to choose the provider.

Usage:
    python search_obsidian.py --build [--vault /path/to/vault] [--provider qwen]
    python search_obsidian.py --embed "offline reinforcement learning" --top-k 5
    python search_obsidian.py --content "offline reinforcement learning"
"""
from __future__ import annotations
import argparse
import json
import math
import os
import sys
from pathlib import Path

# Locate paperwise embedder
_PAPERWISE = Path(__file__).resolve().parents[4] / "3rd_party" / "paperwise"
if str(_PAPERWISE) not in sys.path:
    sys.path.insert(0, str(_PAPERWISE))

CACHE_FILE = Path("outputs/.obsidian_embeddings.json")
CHUNK_SIZE = 2000  # characters per note to embed


def _find_vault() -> Path:
    """Try to locate the Obsidian vault path."""
    env = os.environ.get("OBSIDIAN_VAULT", "")
    if env:
        return Path(env)
    # Common default locations
    candidates = [
        Path.home() / "Documents" / "Obsidian",
        Path.home() / "Obsidian",
        Path.home() / "vault",
    ]
    for c in candidates:
        if (c / ".obsidian").is_dir():
            return c
    print("Error: Cannot locate Obsidian vault. Set OBSIDIAN_VAULT env var.", file=sys.stderr)
    sys.exit(1)


def _iter_notes(vault: Path):
    """Yield (relative_path, title, content_first_2k) for each .md in vault."""
    for md in sorted(vault.rglob("*.md")):
        if any(p.startswith(".") for p in md.relative_to(vault).parts):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue
        # Extract title from first heading or filename
        title = md.stem
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        # Extract arxiv_id from frontmatter or content
        arxiv_id = ""
        in_fm = False
        for line in text.splitlines():
            if line.strip() == "---":
                if not in_fm:
                    in_fm = True
                    continue
                else:
                    break
            if in_fm and line.startswith("arxiv_id:"):
                arxiv_id = line.split(":", 1)[1].strip().strip('"')
                break
        rel = str(md.relative_to(vault))
        yield rel, title, arxiv_id, text[:CHUNK_SIZE]


def cmd_build(vault: Path, provider: str | None):
    """Embed all notes and save cache."""
    from research_helper.kb import embedder

    if provider:
        os.environ["EMBEDDING_PROVIDER"] = provider

    notes = list(_iter_notes(vault))
    if not notes:
        print("No notes found in vault.", file=sys.stderr)
        sys.exit(1)

    texts = [n[3] for n in notes]  # content chunks
    print(f"Embedding {len(texts)} notes with provider={embedder.config.EMBEDDING_PROVIDER}...", file=sys.stderr)

    embeddings = embedder.embed(texts)

    data = []
    for (rel, title, arxiv_id, text), vec in zip(notes, embeddings):
        data.append({
            "path": rel,
            "title": title,
            "arxiv_id": arxiv_id,
            "text_snippet": text[:200],
            "embedding": vec,
        })

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(data)} embeddings → {CACHE_FILE}", file=sys.stderr)


def cmd_embed(query: str, top_k: int):
    """Embed query and search cache."""
    from research_helper.kb import embedder

    if not CACHE_FILE.exists():
        print("Error: Embedding cache not found. Run --build first.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    if not data:
        print("[]")
        return

    q_vec = embedder.embed_one(query[:2000])
    scored = []
    for entry in data:
        sim = _cosine(q_vec, entry["embedding"])
        scored.append((sim, entry))
    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for sim, entry in scored[:top_k]:
        results.append({
            "title": entry["title"],
            "arxiv_id": entry.get("arxiv_id", ""),
            "text": entry.get("text_snippet", ""),
            "path": entry["path"],
            "source": "obsidian-embed",
            "distance": round(1.0 - sim, 4),
        })

    print(json.dumps(results, ensure_ascii=False, indent=2))


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def cmd_content(query: str):
    """Content search is handled by Obsidian MCP — just echo the query."""
    print(json.dumps({"mode": "content", "query": query}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="Semantic search over Obsidian vault")
    ap.add_argument("--build", action="store_true", help="Build embedding cache from vault")
    ap.add_argument("--embed", type=str, default=None, help="Query for semantic search")
    ap.add_argument("--content", type=str, default=None, help="Query for content search (MCP)")
    ap.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    ap.add_argument("--vault", type=Path, default=None, help="Obsidian vault path")
    ap.add_argument("--provider", type=str, default=None, help="Embedding provider: qwen|openai|local")
    args = ap.parse_args()

    vault = args.vault or _find_vault()

    if args.build:
        cmd_build(vault, args.provider)
    elif args.embed:
        cmd_embed(args.embed, args.top_k)
    elif args.content:
        cmd_content(args.content)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()

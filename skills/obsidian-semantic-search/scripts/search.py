#!/usr/bin/env python3
"""Semantic search over Obsidian vault using pre-built embedding index.

Requires index built by build_index.py at temp/obsidian/embeddings.json.

Usage:
    python search.py "reinforcement learning exploration"
    python search.py "offline RL fine-tuning" --top-k 10
    python search.py "diffusion policy" --min-score 0.5
    python search.py "robot grasping" --provider qwen
"""
from __future__ import annotations
import argparse
import json
import math
import os
import sys
from pathlib import Path

from stable_jarvis.llm import embed_one

INDEX_PATH = Path("temp/obsidian/embeddings.json")


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def cmd_search(query: str, top_k: int = 5, min_score: float = 0.0,
               provider: str | None = None):
    if not INDEX_PATH.exists():
        print(
            f"Error: Index not found at {INDEX_PATH}.\n"
            "Run build_index.py --build first.",
            file=sys.stderr,
        )
        sys.exit(1)

    if provider:
        os.environ["EMBEDDING_PROVIDER"] = provider

    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if not data:
        print("[]")
        return

    ep = os.environ.get("EMBEDDING_PROVIDER", "local")
    print(f"Searching {len(data)} notes with provider={ep}...", file=sys.stderr)

    q_vec = embed_one(query[:2000])
    scored = []
    for entry in data:
        sim = _cosine(q_vec, entry["embedding"])
        if sim >= min_score:
            scored.append((sim, entry))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for sim, entry in scored[:top_k]:
        results.append({
            "title": entry["title"],
            "arxiv_id": entry.get("arxiv_id", ""),
            "path": entry["path"],
            "score": round(sim, 4),
            "text_snippet": entry.get("text_snippet", ""),
            "source": "obsidian-embed",
        })

    print(json.dumps(results, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Semantic search over Obsidian vault")
    ap.add_argument("query", type=str, nargs="?", help="Search query string")
    ap.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    ap.add_argument("--min-score", type=float, default=0.0,
                    help="Minimum cosine similarity threshold (default: 0.0)")
    ap.add_argument("--provider", type=str, default=None,
                    help="Embedding provider: qwen|openai|local")
    args = ap.parse_args()

    if not args.query:
        ap.print_help()
        sys.exit(1)

    cmd_search(args.query, top_k=args.top_k, min_score=args.min_score,
               provider=args.provider)


if __name__ == "__main__":
    main()

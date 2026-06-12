#!/usr/bin/env python3
"""Semantic search over Mao Selected Works using pre-built embedding index.

Requires index built by build_index.py at temp/mao/embeddings.json.

Usage:
    python search.py "游击战的战略问题"
    python search.py "群众路线和党的领导" --top-k 10
    python search.py "正确处理人民内部矛盾" --min-score 0.5
    python search.py "土地改革政策" --volume 4
    python search.py "抗日民族统一战线" --provider qwen
"""
from __future__ import annotations
import argparse
import json
import math
import os
import sys
from pathlib import Path

from stable_jarvis.llm import embed_one

INDEX_PATH = Path("temp/mao/embeddings.json")


def _cosine(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def cmd_search(
    query: str,
    top_k: int = 5,
    min_score: float = 0.0,
    provider: str | None = None,
    volume: int | None = None,
):
    if not INDEX_PATH.exists():
        print(
            f"Error: Index not found at {INDEX_PATH}.\n"
            "Run build_index.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    if provider:
        os.environ["EMBEDDING_PROVIDER"] = provider

    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if not data:
        print("[]")
        return

    # Filter by volume if specified
    if volume is not None:
        data = [e for e in data if e.get("volume") == volume]
        if not data:
            print(f"[]  # No articles in volume {volume}")
            return

    ep = os.environ.get("EMBEDDING_PROVIDER", "local")
    vol_msg = f" (volume {volume} only)" if volume else ""
    print(
        f"Searching {len(data)} articles{vol_msg} with provider={ep}...",
        file=sys.stderr,
    )

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
            "volume": entry.get("volume", 0),
            "path": entry["path"],
            "score": round(sim, 4),
            "text_snippet": entry.get("text_snippet", ""),
            "source": "mao-embed",
        })

    print(json.dumps(results, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(
        description="Semantic search over Mao Selected Works"
    )
    ap.add_argument(
        "query", type=str, nargs="?", help="Search query string"
    )
    ap.add_argument(
        "--top-k", type=int, default=5,
        help="Number of results (default: 5)"
    )
    ap.add_argument(
        "--min-score", type=float, default=0.0,
        help="Minimum cosine similarity threshold (default: 0.0)"
    )
    ap.add_argument(
        "--provider", type=str, default=None,
        help="Embedding provider: qwen|openai|local"
    )
    ap.add_argument(
        "--volume", type=int, default=None,
        help="Restrict search to a specific volume (1-5)"
    )
    args = ap.parse_args()

    if not args.query:
        ap.print_help()
        sys.exit(1)

    if args.volume is not None and not (1 <= args.volume <= 5):
        print(f"Error: Volume must be 1-5, got {args.volume}", file=sys.stderr)
        sys.exit(1)

    cmd_search(
        args.query,
        top_k=args.top_k,
        min_score=args.min_score,
        provider=args.provider,
        volume=args.volume,
    )


if __name__ == "__main__":
    main()

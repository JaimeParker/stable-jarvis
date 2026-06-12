#!/usr/bin/env python3
"""Build semantic search index over Mao Selected Works — one embedding per article.

Reads all .md files from mao-selected-works/vol-*/, extracts frontmatter and
body text, embeds with stable_jarvis.llm.embed(), and saves a flat JSON index.

Usage:
    python build_index.py                    # full build
    python build_index.py --provider qwen    # use specific provider
    python build_index.py --stats            # print index stats only
    python build_index.py --clear            # remove index file
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

from stable_jarvis.llm import embed

INDEX_PATH = Path("temp/mao/embeddings.json")
# Qwen3-Embedding-8B has a ~32K token limit. Chinese text averages ~1.5 chars/token.
# 20000 chars ≈ 13K tokens — safe margin. For longer articles, we embed the first
# 20K chars which captures the core argument in nearly all cases.
MAX_CHARS = 20000


def _find_works_dir() -> Path:
    """Locate mao-selected-works directory."""
    env = os.environ.get("MAO_WORKS_DIR", "")
    if env:
        return Path(env)
    # Try default location relative to project root
    default = Path("assets/mao-selected-works")
    if default.is_dir():
        return default
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "assets" / "mao-selected-works",
        Path.home() / "Projects" / "stable-jarvis" / "assets" / "mao-selected-works",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    print(
        "Error: Cannot locate mao-selected-works/ directory. Set MAO_WORKS_DIR env var.",
        file=sys.stderr,
    )
    sys.exit(1)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML-style frontmatter and return (frontmatter_dict, body_text)."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_text = text[4:end]
    body = text[end + 5:]
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm, body


def _iter_articles(works_dir: Path):
    """Yield (rel_path, title, volume, body_text) for each .md file."""
    for vol_dir in sorted(works_dir.glob("vol-*")):
        vol_num = int(vol_dir.name.split("-")[-1])
        for md in sorted(vol_dir.glob("*.md")):
            try:
                text = md.read_text(encoding="utf-8")
            except Exception:
                continue

            fm, body = _parse_frontmatter(text)

            title = fm.get("title", md.stem)
            # Strip leading number prefix like "001-" from filename for fallback
            if title == md.stem:
                parts = md.stem.split("-", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    title = parts[1]

            body = body.strip()
            if not body:
                continue

            truncated = False
            if len(body) > MAX_CHARS:
                body = body[:MAX_CHARS]
                truncated = True

            rel = str(md.relative_to(works_dir))
            yield rel, title, vol_num, body, truncated


def cmd_build(works_dir: Path, provider: str | None = None):
    """Build embedding index over all Mao articles."""
    if provider:
        os.environ["EMBEDDING_PROVIDER"] = provider

    articles = list(_iter_articles(works_dir))
    if not articles:
        print("No articles found in mao-selected-works/.", file=sys.stderr)
        sys.exit(1)

    truncation_warnings = []
    to_embed = []
    for rel, title, vol, body, truncated in articles:
        if truncated:
            truncation_warnings.append(
                f"  {rel} ({len(body):,} chars → truncated to {MAX_CHARS:,})"
            )
        to_embed.append((rel, title, vol, body))

    if truncation_warnings:
        print(
            f"Warning: {len(truncation_warnings)} article(s) exceed {MAX_CHARS:,} char limit:",
            file=sys.stderr,
        )
        for w in truncation_warnings:
            print(w, file=sys.stderr)

    ep = os.environ.get("EMBEDDING_PROVIDER", "local")
    texts = [t[3] for t in to_embed]
    total_chars = sum(len(t) for t in texts)
    print(
        f"Embedding {len(texts)} articles "
        f"({total_chars:,} chars total) with provider={ep}...",
        file=sys.stderr,
    )

    embeddings = embed(texts)

    data = []
    for (rel, title, vol, body), vec in zip(to_embed, embeddings):
        data.append({
            "path": rel,
            "title": title,
            "volume": vol,
            "text_snippet": body[:200],
            "embedding": vec,
        })

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(data)} articles → {INDEX_PATH}", file=sys.stderr)


def cmd_stats():
    """Print index statistics."""
    if not INDEX_PATH.exists():
        print("No index found. Run build_index.py first.", file=sys.stderr)
        sys.exit(1)
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    print(f"Index: {INDEX_PATH}")
    print(f"  Articles: {len(data)}")
    if data:
        total_chars = sum(len(e.get("text_snippet", "")) for e in data)
        print(f"  Total snippet chars: {total_chars:,}")
        # Per-volume breakdown
        vols = {}
        for e in data:
            v = e.get("volume", 0)
            vols[v] = vols.get(v, 0) + 1
        for v in sorted(vols):
            print(f"  Volume {v}: {vols[v]} articles")


def cmd_clear():
    """Remove the index file."""
    if INDEX_PATH.exists():
        INDEX_PATH.unlink()
        print(f"Removed {INDEX_PATH}", file=sys.stderr)
    else:
        print("No index to clear.", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(
        description="Build semantic index over Mao Selected Works"
    )
    ap.add_argument(
        "--stats", action="store_true", help="Print index statistics"
    )
    ap.add_argument(
        "--clear", action="store_true", help="Remove the index file"
    )
    ap.add_argument(
        "--provider", type=str, default=None,
        help="Embedding provider: qwen|openai|local"
    )
    ap.add_argument(
        "--works-dir", type=Path, default=None,
        help="Path to mao-selected-works/ directory"
    )
    args = ap.parse_args()

    if args.clear:
        cmd_clear()
    elif args.stats:
        cmd_stats()
    else:
        works_dir = args.works_dir or _find_works_dir()
        cmd_build(works_dir, args.provider)


if __name__ == "__main__":
    main()

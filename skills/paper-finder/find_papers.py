from __future__ import annotations

import argparse
import json
from pathlib import Path

from stable_jarvis.paper_finder import PaperFinderConfig, run_paper_finder


def _load_semantic_config(path: str | None) -> dict[str, object] | None:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find recent arXiv papers for a stable-jarvis research profile")
    parser.add_argument("--profile", required=True, help="Path to the research profile JSON")
    parser.add_argument("--output", required=True, help="Directory to write Obsidian markdown notes into")
    parser.add_argument("--since-days", type=int, default=None, help="Override the profile's since_days window")
    parser.add_argument("--state", default=None, help="Override the seen-ids state file path")
    parser.add_argument(
        "--semantic",
        action="store_true",
        help="Enable semantic ranking; reads model settings from config/api_keys.json unless overridden",
    )
    parser.add_argument("--semantic-config", default=None, help="JSON file with semantic ranking config")
    parser.add_argument("--semantic-limit", type=int, default=3, help="Number of semantic neighbors to retain")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing Obsidian notes")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    semantic_config = _load_semantic_config(args.semantic_config)
    if args.semantic and semantic_config is None:
        semantic_config = {}
    config = PaperFinderConfig(
        profile_path=args.profile,
        output_dir=args.output,
        state_path=args.state,
        since_days=args.since_days,
        semantic_config=semantic_config,
        semantic_limit=args.semantic_limit,
        overwrite=args.overwrite,
    )
    profile, candidates = run_paper_finder(config)
    print(f"Profile: {profile.profile_name} ({profile.profile_id})")
    print(f"Candidates written: {len(candidates)}")
    for index, candidate in enumerate(candidates[:10], start=1):
        print(
            f"{index}. {candidate.paper.title} | {candidate.review.recommendation} | total={candidate.scores.total:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
from __future__ import annotations

import json

from stable_jarvis.paper_finder import load_profile
from stable_jarvis.paper_finder.candidate import CandidateCard, PaperInfo
from stable_jarvis.paper_finder.obsidian import render_obsidian_note
from stable_jarvis.paper_finder.parser import parse_feed
from stable_jarvis.paper_finder.query import build_search_query
from stable_jarvis.paper_finder.ranker import rank_candidates, score_map_match
from stable_jarvis.paper_finder.review import build_system_review
from stable_jarvis.paper_finder.semantic import load_semantic_model_settings


def _profile_payload() -> dict[str, object]:
    return {
        "schema_version": "1.1.0",
        "profile_id": "robotics-locomotion",
        "profile_name": "Robotics Locomotion",
        "updated_at": "2026-03-08T00:00:00+00:00",
        "zotero_basis": {"collections": ["Robotics"], "tags": ["locomotion"]},
        "retrieval_defaults": {
            "logic": "AND",
            "sort_by": "lastUpdatedDate",
            "sort_order": "descending",
            "since_days": 7,
            "max_results_per_interest": 5,
            "max_pages": 2,
            "state_path": ".state/test_seen.json",
        },
        "interests": [
            {
                "interest_id": "legged-rl",
                "label": "Legged RL",
                "enabled": True,
                "categories": ["cs.RO"],
                "method_keywords": ["legged robot", "reinforcement learning"],
                "query_aliases": ["quadruped locomotion"],
                "exclude_keywords": ["survey"],
                "logic": "AND",
            }
        ],
    }


def test_load_profile(tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(_profile_payload()), encoding="utf-8")

    profile = load_profile(profile_path)

    assert profile.profile_id == "robotics-locomotion"
    assert profile.retrieval_defaults.max_results_per_interest == 5
    assert profile.interests[0].method_keywords == ["legged robot", "reinforcement learning"]


def test_build_search_query_includes_categories_keywords_and_excludes():
    query = build_search_query(
        ["cs.RO"],
        ["legged robot", "reinforcement learning"],
        exclude_keywords=["survey"],
        logic="AND",
    )

    assert "cat:cs.RO" in query
    assert "reinforcement learning" in query
    assert "AND NOT" in query


def test_parse_feed_extracts_arxiv_metadata():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>http://arxiv.org/abs/2501.12345v1</id>
        <updated>2026-03-10T12:00:00Z</updated>
        <published>2026-03-09T12:00:00Z</published>
        <title>Learning Agile Quadruped Locomotion</title>
        <summary>We study reinforcement learning for legged robot control. Code: https://github.com/example/project</summary>
        <author><name>Alice Smith</name></author>
        <author><name>Bob Chen</name></author>
        <link rel="alternate" type="text/html" href="http://arxiv.org/abs/2501.12345v1" />
        <link title="pdf" rel="related" type="application/pdf" href="http://arxiv.org/pdf/2501.12345v1" />
        <arxiv:comment>Accepted to ICRA 2026</arxiv:comment>
        <category term="cs.RO" />
      </entry>
    </feed>"""

    entries = parse_feed(xml)

    assert len(entries) == 1
    assert entries[0].arxiv_id == "2501.12345v1"
    assert entries[0].venue_inferred == "ICRA 2026"
    assert entries[0].code_urls == ["https://github.com/example/project"]


def test_rank_candidates_prefers_stronger_profile_match(tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(_profile_payload()), encoding="utf-8")
    profile = load_profile(profile_path)

    strong = CandidateCard(
        candidate_id="a",
        batch_id="batch",
        generated_at="2026-03-15T00:00:00+00:00",
        paper=PaperInfo(
            title="Reinforcement Learning for Legged Robot Control",
            abstract="This paper studies quadruped locomotion with reinforcement learning.",
            categories=["cs.RO"],
            arxiv_id="2501.1",
        ),
    )
    strong.triage.matched_interest_ids.append("legged-rl")
    strong.triage.matched_interest_labels.append("Legged RL")

    weak = CandidateCard(
        candidate_id="b",
        batch_id="batch",
        generated_at="2026-03-15T00:00:00+00:00",
        paper=PaperInfo(
            title="A Survey of Vision Transformers",
            abstract="This survey reviews image models.",
            categories=["cs.CV"],
            arxiv_id="2501.2",
        ),
    )
    weak.triage.matched_interest_ids.append("legged-rl")
    weak.triage.matched_interest_labels.append("Legged RL")

    assert score_map_match(strong, profile) > score_map_match(weak, profile)

    ranked = rank_candidates([weak, strong], profile)
    assert ranked[0].candidate_id == "a"


def test_build_system_review_assigns_recommendation():
    candidate = CandidateCard(
        candidate_id="a",
        batch_id="batch",
        generated_at="2026-03-15T00:00:00+00:00",
        paper=PaperInfo(
            title="Reinforcement Learning for Legged Robot Control",
            abstract="This paper studies quadruped locomotion with reinforcement learning.",
            categories=["cs.RO"],
            arxiv_id="2501.1",
        ),
    )
    candidate.triage.matched_interest_labels.append("Legged RL")
    candidate.scores.map_match = 0.8
    candidate.scores.total = 0.82

    review = build_system_review(candidate)

    assert review.recommendation == "read_first"
    assert review.review_status == "system_generated"
    assert review.why_it_matters is not None


def test_render_obsidian_note_contains_frontmatter_and_sections():
    candidate = CandidateCard(
        candidate_id="a",
        batch_id="batch",
        generated_at="2026-03-15T00:00:00+00:00",
        paper=PaperInfo(
            title="Learning Agile Quadruped Locomotion",
            authors=["Alice Smith", "Bob Chen"],
            abstract="A concise abstract.",
            categories=["cs.RO"],
            arxiv_id="2501.12345v1",
            url="http://arxiv.org/abs/2501.12345v1",
        ),
    )
    candidate.review.recommendation = "skim"
    candidate.review.why_it_matters = "Useful for legged locomotion work."
    candidate.review.quick_takeaways = ["Strong policy learning baseline"]
    candidate.review.caveats = ["Needs full paper review"]
    candidate.scores.map_match = 0.55
    candidate.scores.total = 0.61

    note = render_obsidian_note(candidate)

    assert note.startswith("---\n")
    assert "recommendation: \"skim\"" in note
    assert "## Why It Matters" in note
    assert "## Quick Takeaways" in note


def test_load_semantic_model_settings_from_api_keys_file(tmp_path):
    api_keys_path = tmp_path / "api_keys.json"
    api_keys_path.write_text(
        json.dumps(
            {
                "semantic_model": {
                    "api_base_url": "https://example.com/v1",
                    "api_key": "test-key",
                    "model": "my-embed-model",
                }
            }
        ),
        encoding="utf-8",
    )

    settings = load_semantic_model_settings(str(api_keys_path))

    assert settings["api_base_url"] == "https://example.com/v1"
    assert settings["api_key"] == "test-key"
    assert settings["model"] == "my-embed-model"
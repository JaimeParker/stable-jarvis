"""Multi-provider embedding generation: qwen, openai, local sentence-transformers.

Reads configuration from environment variables (stable_jarvis/__init__.py
already loads .env into os.environ before this module is imported).
"""
from __future__ import annotations
import os

_DEFAULT_MODELS = {
    "openai": "text-embedding-3-small",
    "qwen":   "text-embedding-v3",
}

_st_model = None


def embed(texts: list[str]) -> list[list[float]]:
    provider = os.getenv("EMBEDDING_PROVIDER", "local")
    if provider == "qwen":
        return _embed_openai_compat(texts, "qwen")
    if provider == "openai":
        return _embed_openai_compat(texts, "openai")
    return _embed_local(texts)


def embed_one(text: str) -> list[float]:
    return embed([text])[0]


def _embed_openai_compat(texts: list[str], provider: str) -> list[list[float]]:
    from openai import OpenAI
    from stable_jarvis.llm.client import _get_base_url, _api_key

    model = os.getenv("EMBEDDING_MODEL") or _DEFAULT_MODELS[provider]
    api_key = os.getenv("EMBEDDING_API_KEY") or _api_key(provider)
    base_url = os.getenv("EMBEDDING_BASE_URL") or _get_base_url(provider)
    client = OpenAI(api_key=api_key, base_url=base_url)
    results: list[list[float]] = []
    for batch in _batched(texts, 10 if provider == "qwen" else 25):
        resp = client.embeddings.create(model=model, input=batch)
        results.extend(d.embedding for d in resp.data)
    return results


def _embed_local(texts: list[str]) -> list[list[float]]:
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    vecs = _st_model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def _batched(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]

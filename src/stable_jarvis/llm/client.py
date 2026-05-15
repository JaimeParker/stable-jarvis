"""Multi-provider LLM client: anthropic, openai, deepseek, qwen.

Reads configuration from environment variables (stable_jarvis/__init__.py
already loads .env into os.environ before this module is imported).
"""
from __future__ import annotations
import os

_DEFAULT_BASE_URLS = {
    "deepseek": "https://api.deepseek.com",
    "qwen":     "https://dashscope.aliyuncs.com/compatible-mode/v1",
}

_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai":    "gpt-4o",
    "deepseek":  "deepseek-chat",
    "qwen":      "qwen-plus",
}


def _get_base_url(provider: str) -> str | None:
    generic = os.getenv("EMBEDDING_BASE_URL")
    if generic and provider in ("qwen", "openai"):
        return generic
    env_key = f"{provider.upper()}_BASE_URL"
    return os.getenv(env_key) or _DEFAULT_BASE_URLS.get(provider)


def _api_key(provider: str) -> str:
    key = os.getenv(f"{provider.upper()}_API_KEY", "")
    if not key:
        raise EnvironmentError(
            f"{provider.upper()}_API_KEY is not set. Add it to .env or environment."
        )
    return key


def complete(system: str, user: str, max_tokens: int = 4096) -> str:
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    model = os.getenv("LLM_MODEL") or _DEFAULT_MODELS.get(provider, "")

    if provider == "anthropic":
        return _anthropic(system, user, model, max_tokens)
    elif provider in ("openai", "deepseek", "qwen"):
        return _openai_compat(system, user, model, max_tokens, provider)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {provider!r}. "
            "Choose from: anthropic, openai, deepseek, qwen"
        )


def _anthropic(system: str, user: str, model: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=_api_key("anthropic"))
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


def _openai_compat(system: str, user: str, model: str, max_tokens: int, provider: str) -> str:
    from openai import OpenAI

    key = _api_key(provider)
    base_url = _get_base_url(provider)
    client = OpenAI(api_key=key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return resp.choices[0].message.content or ""

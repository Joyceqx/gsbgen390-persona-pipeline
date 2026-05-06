"""LLM router — minimal OpenRouter (or direct OpenAI) client for Phase 1.

Locked panel (gss_phase1_design.md §12):
  - 4 cheap OpenRouter models, n_samples=1 each, primary path
  - GPT-4o anchor on N=50 subset, n_samples=2, primary-conditions-only

This module is intentionally small — it does not own scoring, prompt
construction, or result accumulation. Those live in gss_pipeline.py.

Usage:
    from llm_router import call_panel, MODEL_PANEL_PRIMARY, MODEL_ANCHOR
    responses = call_panel(system, user, models=MODEL_PANEL_PRIMARY)
    # responses = {'qwen-2.5-72b': '4', 'deepseek-v3.1': '4', 'minimax-m1': '5', 'kimi-k2': '4'}

API key:
    set environment variable OPENROUTER_API_KEY
    OR put it in OpenRouter_api.txt at the project root (gitignored).
    GPT-4o anchor falls back to OPENAI_API_KEY / Openai_api.txt for direct
    OpenAI access if OpenRouter doesn't carry GPT-4o cheaply.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Iterable

WORK = Path("/Users/joyce/Documents/GSBGEN390")

# ---------------------------------------------------------------------------
# Locked model panel (matches gss_phase1_design.md §12)
# ---------------------------------------------------------------------------

# OpenRouter model slugs — verify exact slugs at https://openrouter.ai/models
# before launching Phase 1b. These are reasonable defaults as of 2026-05.
MODEL_PANEL_PRIMARY: tuple[str, ...] = (
    "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat",          # V3.1 family
    "minimax/minimax-m1",
    "moonshotai/kimi-k2",
)

# Anchor model — Park-comparable; run on N=50 subset only. Available via
# OpenRouter as "openai/gpt-4o" or directly via OpenAI SDK.
MODEL_ANCHOR: str = "openai/gpt-4o"

# Default per-call hyperparameters
DEFAULT_TEMPERATURE: float = 0.7
DEFAULT_MAX_TOKENS: int = 16   # we only need a single integer code
DEFAULT_TIMEOUT: float = 30.0


# ---------------------------------------------------------------------------
# API key loading
# ---------------------------------------------------------------------------

def _load_key(env_var: str, fallback_file: str) -> str | None:
    v = os.environ.get(env_var)
    if v:
        return v.strip()
    p = WORK / fallback_file
    if p.exists():
        return p.read_text().strip()
    return None


def get_openrouter_key() -> str:
    k = _load_key("OPENROUTER_API_KEY", "OpenRouter_api.txt")
    if not k:
        raise RuntimeError(
            "No OpenRouter API key found. Set OPENROUTER_API_KEY env var "
            "or put your key in OpenRouter_api.txt at the project root. "
            "Get a key at https://openrouter.ai/keys."
        )
    return k


def get_openai_key() -> str:
    k = _load_key("OPENAI_API_KEY", "Openai_api.txt")
    if not k:
        raise RuntimeError("No OpenAI API key — needed for GPT-4o anchor")
    return k


# ---------------------------------------------------------------------------
# Single LLM call with retry / exponential backoff
# ---------------------------------------------------------------------------

class LLMError(Exception):
    pass


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(t in msg for t in (
        "rate", "429", "timeout", "timed out", "503", "502", "overload",
        "connection", "econnreset", "temporar", "try again",
    ))


def call_llm(
    system: str,
    user: str,
    model: str,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = 8,
    initial_backoff_s: float = 4.0,
) -> str:
    """One LLM call. Returns raw response text. Raises LLMError on persistent
    failure after max_retries.

    Routing:
      - if model starts with 'openai/' AND OpenRouter has a cheaper rate,
        could route via OpenRouter; we keep direct OpenAI for the GPT-4o
        anchor only (more reliable for self-consistency reproducibility).
      - all other models route via OpenRouter.
    """
    use_openai_direct = model.startswith("openai/") and "gpt-4o" in model
    if use_openai_direct:
        from openai import OpenAI
        client = OpenAI(api_key=get_openai_key(), timeout=timeout)
        actual_model = model.replace("openai/", "")
    else:
        from openai import OpenAI
        client = OpenAI(
            api_key=get_openrouter_key(),
            base_url="https://openrouter.ai/api/v1",
            timeout=timeout,
        )
        actual_model = model

    delay = initial_backoff_s
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=actual_model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            last_exc = e
            if not _is_retryable(e):
                raise LLMError(f"non-retryable error from {model}: {e}") from e
            if attempt == max_retries - 1:
                break
            print(f"  [retry {attempt+1}/{max_retries} after {delay:.0f}s: {type(e).__name__}: {e}]", flush=True)
            time.sleep(delay)
            delay = min(delay * 2, 60.0)  # cap at 60s
    raise LLMError(f"max retries ({max_retries}) exhausted for {model}: {last_exc}")


# ---------------------------------------------------------------------------
# Multi-model panel call
# ---------------------------------------------------------------------------

def call_panel(
    system: str,
    user: str,
    models: Iterable[str] = MODEL_PANEL_PRIMARY,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    on_error: str = "raise",  # "raise" | "skip" | "record"
) -> dict[str, str | None]:
    """Call the same prompt to multiple models sequentially. Returns
    {model_slug: response_str_or_None}.

    on_error:
      - "raise":  bubble up the first LLMError (good for smoke testing).
      - "skip":   silently drop failing models (return None for them).
      - "record": store the error message as the value (debug-friendly).
    """
    out: dict[str, str | None] = {}
    for m in models:
        try:
            out[m] = call_llm(system, user, model=m,
                              temperature=temperature, max_tokens=max_tokens)
        except LLMError as e:
            if on_error == "raise":
                raise
            elif on_error == "skip":
                out[m] = None
            else:  # "record"
                out[m] = f"<<ERROR: {e}>>"
    return out


# ---------------------------------------------------------------------------
# Smoke test (requires API keys)
# ---------------------------------------------------------------------------

def _smoke_one_call(model: str = "qwen/qwen-2.5-72b-instruct"):
    system = "You answer survey questions in character. Output a single integer."
    user = (
        "GSS question: think of self as liberal or conservative\n\n"
        "Options:\n  1. Extremely liberal\n  2. Liberal\n  3. Slightly liberal\n"
        "  4. Moderate\n  5. Slightly conservative\n  6. Conservative\n  7. Extremely conservative\n\n"
        "You are a moderate-leaning person.\n\n"
        "Output ONLY a single integer code (1-7)."
    )
    print(f"\n=== smoke test: 1 call to {model} ===")
    print(f"system: {system!r}")
    print(f"user prompt:\n{user}")
    print()
    try:
        out = call_llm(system, user, model=model)
        print(f"response: {out!r}")
        return out
    except LLMError as e:
        print(f"ERROR: {e}")
        return None


def _smoke_panel():
    system = "You answer survey questions in character. Output a single integer."
    user = (
        "GSS question: think of self as liberal or conservative\n\n"
        "Options:\n  1. Extremely liberal\n  2. Liberal\n  3. Slightly liberal\n"
        "  4. Moderate\n  5. Slightly conservative\n  6. Conservative\n  7. Extremely conservative\n\n"
        "You are a moderate-leaning person.\n\n"
        "Output ONLY a single integer code (1-7)."
    )
    print(f"\n=== smoke test: panel of {len(MODEL_PANEL_PRIMARY)} models ===")
    out = call_panel(system, user, on_error="record")
    for m, r in out.items():
        print(f"  {m:<35s} → {r!r}")
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-one", action="store_true", help="single-call test, default Qwen")
    ap.add_argument("--smoke-panel", action="store_true", help="all 4 cheap models")
    ap.add_argument("--smoke-anchor", action="store_true", help="GPT-4o anchor")
    ap.add_argument("--model", default="qwen/qwen-2.5-72b-instruct")
    args = ap.parse_args()
    if args.smoke_one:
        _smoke_one_call(args.model)
    elif args.smoke_panel:
        _smoke_panel()
    elif args.smoke_anchor:
        _smoke_one_call("openai/gpt-4o")
    else:
        print("Usage: python3 llm_router.py [--smoke-one | --smoke-panel | --smoke-anchor]")
        print(f"Cheap-panel models: {MODEL_PANEL_PRIMARY}")
        print(f"Anchor model:        {MODEL_ANCHOR}")

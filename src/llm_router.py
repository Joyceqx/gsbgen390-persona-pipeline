"""LLM router — minimal OpenRouter (or direct OpenAI) client for Phase 1.

Locked panel (gss_phase1_design.md §12; sample sizes revised 2026-05-09 night):
  - 4 cheap OpenRouter models (Qwen-2.5-72B / DeepSeek-V3.1 /
    Llama-3.3-70B-Instruct / Kimi K2 — 3 China-trained + 1 Western-trained
    after the 2026-05-09 MiniMax→Llama swap for cross-family balance),
    n_samples=1 each, primary path (Phase 1a, N=200 with 100/100 split).
  - Phase 1b: single §12.2-quality-selected model on N=3,309 (full GSS 2024),
    n_samples=1.
  - GPT-4o anchor on N=100 selection subset, n_samples=2, primary-conditions-only.

This module is intentionally small — it does not own scoring, prompt
construction, or result accumulation. Those live in gss_pipeline.py.

Usage:
    from llm_router import call_panel, MODEL_PANEL_PRIMARY, MODEL_ANCHOR
    responses = call_panel(system, user, models=MODEL_PANEL_PRIMARY)
    # responses = {'qwen-2.5-72b': '4', 'deepseek-v3.1': '4', 'llama-3.3-70b': '5', 'kimi-k2': '4'}

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

WORK = Path("/Users/joyce/Developer/gsbgen390")

# ---------------------------------------------------------------------------
# Locked model panel (matches gss_phase1_design.md §12)
# ---------------------------------------------------------------------------

# OpenRouter model slugs — verify exact slugs at https://openrouter.ai/models
# before launching Phase 1b. These are reasonable defaults as of 2026-05.
#
# Cross-family balance (locked 2026-05-09 night per Audit-3 review): the
# original all-China panel (Qwen + DeepSeek + MiniMax + Kimi) was swapped
# pre-OSF to introduce one Western-trained model. MiniMax-M1 → Llama-3.3-70B-
# Instruct (Meta); the panel now reads as 3 China-trained + 1 Western, which
# preserves cost-efficiency while defending Western-venue cross-family
# generalization claims. Llama-3.3-70B is comparable in OpenRouter pricing.
MODEL_PANEL_PRIMARY: tuple[str, ...] = (
    "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat",            # V3.1 family
    "meta-llama/llama-3.3-70b-instruct", # Western (Meta) — swapped in pre-OSF for cross-family balance
    "moonshotai/kimi-k2",
)

# Anchor model — Park-comparable; run on N=100 subset only. Available via
# OpenRouter as "openai/gpt-4o" or directly via OpenAI SDK.
MODEL_ANCHOR: str = "openai/gpt-4o"

# OpenRouter provider locking (Reviewer round-3 P1 #5, locked 2026-05-29).
#
# By default call_llm_meta sends `allow_fallbacks: False` and
# `require_parameters: True` to OpenRouter for every non-OpenAI-direct call.
# Together those mean: pick a provider that can honor every parameter we
# asked for (including `seed`); never silently route to a different
# provider mid-run. Without them, OpenRouter can route `qwen-2.5-72b-instruct`
# to provider A on call 1 and provider B on call 2 — possibly at different
# quantizations — and our cross-model comparison loses provenance.
#
# Additionally, populate PROVIDER_LOCK below with the exact provider name
# returned by the smoke test for each panel model. When non-empty, the
# router adds `order: [<name>]` to extra_body so OpenRouter is pinned to
# that provider for the entire paid run. Empty default = let OpenRouter
# pick the first parameter-supporting provider on first call, but rely on
# allow_fallbacks=False to keep that provider sticky thereafter.
#
# Workflow:
#   1. Run `python3 src/gss_driver.py --smoke`; record the `provider` field
#      printed for each panel model.
#   2. Populate PROVIDER_LOCK[model_slug] = "<provider name>" below.
#   3. Verify with a second --smoke that the locked provider is selected.
#   4. Launch paid Phase 1A.
PROVIDER_LOCK: dict[str, str] = {
    # "qwen/qwen-2.5-72b-instruct":        "<populate from smoke output>",
    # "deepseek/deepseek-chat":            "<populate from smoke output>",
    # "meta-llama/llama-3.3-70b-instruct": "<populate from smoke output>",
    # "moonshotai/kimi-k2":                "<populate from smoke output>",
}

# Default per-call hyperparameters
DEFAULT_TEMPERATURE: float = 0.7
# We only need a single integer code, but some models (notably DeepSeek-V3.1
# in reasoning mode) emit chain-of-thought before the final answer. 64 tokens
# is a safe ceiling for an integer + brief reasoning, while still cheap.
# Per Codex audit 2026-05-06.
DEFAULT_MAX_TOKENS: int = 64
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
    """Decide whether an LLM exception should trigger backoff+retry.

    First check exception class via openai SDK exceptions (preferred — robust);
    fall back to substring matching the error message (handles non-OpenAI
    SDK errors and OpenRouter-passthrough cases).
    """
    # Class-based check (most reliable)
    try:
        from openai import RateLimitError, APITimeoutError, APIConnectionError, APIStatusError
        if isinstance(exc, (RateLimitError, APITimeoutError, APIConnectionError)):
            return True
        if isinstance(exc, APIStatusError):
            # Retry on server-side errors (5xx) and rate limits
            status = getattr(exc, "status_code", None)
            if status is not None and (status >= 500 or status == 429):
                return True
    except ImportError:
        pass

    msg = str(exc).lower()
    # Substring fallback
    return any(t in msg for t in (
        "rate", "429", "500", "502", "503", "504",
        "internal server", "service unavailable", "bad gateway", "gateway timeout",
        "timeout", "timed out", "overload", "connection",
        "econnreset", "temporar", "try again",
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
    seed: int | None = 42,
) -> str:
    """One LLM call. Returns raw response text. Raises LLMError on persistent
    failure after max_retries.

    Routing:
      - if model starts with 'openai/' AND OpenRouter has a cheaper rate,
        could route via OpenRouter; we keep direct OpenAI for the GPT-4o
        anchor only (more reliable for self-consistency reproducibility).
      - all other models route via OpenRouter.

    Seed (locked 2026-05-09 night per Codex N1 audit):
      - OpenAI direct (GPT-4o anchor): passes `seed=` to chat.completions.create.
        OpenAI honors this and returns `system_fingerprint` for verification.
      - OpenRouter: passes `extra_body={"seed": seed}` which OpenRouter forwards
        to backing providers that support it (varies by provider — must be
        verified on N=10 smoke per panel model).
      - seed is a HINT, not a guarantee — providers may ignore it. The §14
        reproducibility commitment in `gss_phase1_design.md` documents this
        per-model verification requirement.
      - Pass `seed=None` to disable explicitly (e.g., for deliberate
        non-determinism testing).
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

    out = call_llm_meta(
        system=system, user=user, model=model,
        temperature=temperature, max_tokens=max_tokens, timeout=timeout,
        max_retries=max_retries, initial_backoff_s=initial_backoff_s,
        seed=seed,
    )
    return out["text"]


def call_llm_meta(
    system: str,
    user: str,
    model: str,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = 8,
    initial_backoff_s: float = 4.0,
    seed: int | None = 42,
) -> dict:
    """Same as call_llm but returns a metadata dict instead of bare text.

    Returns:
        {
            "text": str,                          # the response text
            "model_returned": str | None,         # provider-reported model name
            "system_fingerprint": str | None,     # OpenAI's reproducibility fingerprint
            "provider": str | None,               # OpenRouter's backend provider
            "tokens_in": int | None,              # prompt token count
            "tokens_out": int | None,             # completion token count
        }

    Provider identity logging is required for the cross-model paper claim —
    without it, the same "qwen-2.5-72b" slug can be silently served by
    different backends at different quantizations across the paid Phase 1A
    run, and the cross-cell comparison loses provenance. The provider /
    fingerprint fields are best-effort: not every provider returns them
    (None when unavailable).
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
            create_kwargs: dict = {
                "model": actual_model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
            if use_openai_direct:
                # OpenAI direct: seed goes as a top-level kwarg.
                if seed is not None:
                    create_kwargs["seed"] = seed
            else:
                # OpenRouter: seed + provider preferences via extra_body.
                # Per Reviewer round-3 P1 #5: enforce allow_fallbacks=False +
                # require_parameters=True on every call so a parameter-
                # supporting provider is chosen and silently held mid-run.
                # If PROVIDER_LOCK has an entry for this model, pin to it.
                provider_prefs: dict = {
                    "allow_fallbacks": False,
                    "require_parameters": True,
                }
                if model in PROVIDER_LOCK:
                    provider_prefs["order"] = [PROVIDER_LOCK[model]]
                extra_body: dict = {"provider": provider_prefs}
                if seed is not None:
                    extra_body["seed"] = seed
                create_kwargs["extra_body"] = extra_body
            resp = client.chat.completions.create(**create_kwargs)
            usage = getattr(resp, "usage", None)
            return {
                "text": (resp.choices[0].message.content or "").strip(),
                "model_returned": getattr(resp, "model", None),
                "system_fingerprint": getattr(resp, "system_fingerprint", None),
                # OpenRouter exposes `provider` on the response object; OpenAI does not.
                "provider": getattr(resp, "provider", None),
                "tokens_in": getattr(usage, "prompt_tokens", None) if usage else None,
                "tokens_out": getattr(usage, "completion_tokens", None) if usage else None,
            }
        except Exception as e:
            last_exc = e
            if not _is_retryable(e):
                raise LLMError(f"non-retryable error from {model}: {e}") from e
            if attempt == max_retries - 1:
                break
            print(f"  [retry {attempt+1}/{max_retries} after {delay:.0f}s: {type(e).__name__}: {e}]", flush=True)
            time.sleep(delay)
            delay = min(delay * 2, 60.0)
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

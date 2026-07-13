"""No-persona baseline for the selected cell (Kimi-K2 × P2).

The fair, equal-information comparator to the base-rate baseline (§1 of the
report): the same model and prompt template with the persona stripped to
nothing, predicting each item from the model's own prior. Because an empty
persona makes the prompt identical across respondents, the model's no-persona
prediction is a per-ITEM prior, so we sample it M times per item (not once per
respondent) to characterise that prior.

Reuses the exact pipeline path: build_prompt_variant (empty persona via
exclude_vars = all feature variables) -> call_llm_meta -> parse_response.

  python3 report/run_no_persona.py --dry-run   # build prompts, no API calls
  python3 report/run_no_persona.py             # paid sampling run
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/Users/joyce/Developer/gsbgen390")
sys.path.insert(0, str(ROOT / "src"))
from gss_pipeline import (load_taxonomy, format_eval_question, parse_response,  # noqa: E402
                          sample_respondents)
from prompt_variants import build_prompt as build_prompt_variant  # noqa: E402

MODEL = "moonshotai/kimi-k2-0905"   # §7-recommended cell model
PROMPT = "P2"                        # §7-recommended cell prompt
TEMPERATURE = 0.7                    # match Phase 1A
M = 40                               # samples per item to estimate the prior
OUT = ROOT / "report" / "no_persona_samples.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("-M", type=int, default=M)
    args = ap.parse_args()

    tx = load_taxonomy()
    items = tx["primary_eval"]["items"]
    bins = tx["_feature_bins_sets"]
    all_feature_vars = sorted(set().union(*[set(bins[b]) for b in bins]))
    respondent = sample_respondents(200).iloc[0]   # any row; all features excluded

    # Build the empty-persona system message per item (verify it is empty).
    built = {}
    for it in items:
        out = build_prompt_variant(
            respondent, tx, prompt_id=PROMPT,
            drop_bin=None, exclude_vars=set(all_feature_vars),
        )
        fc = out["metadata"]["feature_count"]
        assert fc == 0, f"persona not empty for {it['id']}: feature_count={fc}"
        system = out["system_instruction"] + "\n\n" + out["persona_prompt"]
        question, meta = format_eval_question(it)
        built[it["id"]] = {"system": system, "question": question,
                           "valid_codes": meta["valid_codes"]}

    print(f"model={MODEL}  prompt={PROMPT}  temp={TEMPERATURE}  M={args.M}")
    print(f"empty-persona feature_count = 0 for all {len(items)} items  ✓")
    print(f"persona char_count = {len(built[items[0]['id']]['system'])} "
          f"(vs full-persona ~3500)")
    if args.dry_run:
        ex = built[items[0]["id"]]
        print("\n--- example empty-persona SYSTEM message (POLVIEWS) ---")
        print(ex["system"])
        print("\n--- example QUESTION ---")
        print(ex["question"])
        print(f"\ntotal calls if run: {len(items)} items × {args.M} = {len(items)*args.M}")
        return

    from llm_router import call_llm_meta, LLMError  # import here so dry-run needs no key
    results = {}
    provider_seen = set()
    total = len(items) * args.M
    done = 0
    for it in items:
        iid = it["id"]
        b = built[iid]
        codes, raws, parse_fail = [], [], 0
        for s in range(args.M):
            seed = 70000 + items.index(it) * 1000 + s
            try:
                out = call_llm_meta(b["system"], b["question"], model=MODEL,
                                    temperature=TEMPERATURE, seed=seed)
                raw = out["text"]
                if out.get("provider"):
                    provider_seen.add(out["provider"])
            except LLMError as e:
                raw = f"<<ERR {e}>>"
            code = parse_response(raw, b["valid_codes"])
            raws.append(raw)
            if code is None:
                parse_fail += 1
            else:
                codes.append(code)
            done += 1
            if done % 40 == 0:
                print(f"  {done}/{total} calls done", flush=True)
        results[iid] = {
            "valid_codes": b["valid_codes"],
            "codes": codes, "parse_fail": parse_fail, "n": args.M,
            "prior_dist": dict(Counter(codes)),
            "prior_mode": Counter(codes).most_common(1)[0][0] if codes else None,
        }
        dist = results[iid]["prior_dist"]
        print(f"[{iid:9s}] mode={results[iid]['prior_mode']} dist={dist} parse_fail={parse_fail}", flush=True)

    OUT.write_text(json.dumps({
        "model": MODEL, "prompt": PROMPT, "temperature": TEMPERATURE, "M": args.M,
        "provider": sorted(provider_seen), "items": results,
    }, indent=2))
    print(f"\nprovider(s): {sorted(provider_seen)}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

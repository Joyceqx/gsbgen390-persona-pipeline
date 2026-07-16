"""Equivalence test: run_primary_one_respondent with parallel=1 vs parallel=8
must produce identical records when call_llm_meta is stubbed deterministically.

No API calls, no cost. Uses the real GSS loader/taxonomy/prompt builder so the
full Phase A build path is exercised on one real respondent with the real
Phase 1B condition set.
"""
import json
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))

import gss_driver as gd


def fake_call_llm_meta(system, user, model, temperature=0.7, seed=42, **kw):
    # Deterministic function of the call coordinates (seed encodes them all).
    time.sleep(0.02)  # force real thread interleaving
    return {
        "text": str(seed % 3 + 1),  # a plausible small answer code
        "model_returned": model,
        "system_fingerprint": f"fp_{seed}",
        "provider": "stub",
        "tokens_in": len(system),
        "tokens_out": 1,
    }


def main():
    gd.call_llm_meta = fake_call_llm_meta  # monkeypatch the router entry point

    taxonomy = gd.load_taxonomy()
    primary_eval_items = taxonomy["primary_eval"]["items"]
    sample = gd.sample_respondents(n=3309, seed=42)
    respondent = sample.iloc[0]

    kwargs = dict(
        taxonomy=taxonomy,
        primary_eval_items=primary_eval_items,
        models=["kimi-k2-0905"],  # what random dispatch picked for rid=1
        prompt_id="P1",
        n_samples=1,
        verbose=False,
        conditions=gd.CONDITIONS_PHASE1B,
    )

    t0 = time.time()
    seq = gd.run_primary_one_respondent(respondent, parallel=1, **kwargs)
    t_seq = time.time() - t0
    t0 = time.time()
    par = gd.run_primary_one_respondent(respondent, parallel=8, **kwargs)
    t_par = time.time() - t0

    s = json.dumps(seq, sort_keys=True, default=str)
    p = json.dumps(par, sort_keys=True, default=str)
    # Also check ORDER of records (not just content) since resume keys rely on it
    s_ord = json.dumps(seq, default=str)
    p_ord = json.dumps(par, default=str)

    n_calls = sum(
        len(v) for r in seq for v in [r["per_item_scores"]]
    )
    print(f"records: seq={len(seq)} par={len(par)}")
    print(f"items scored across conditions: {sum(len(r['per_item_scores']) for r in seq)}")
    print(f"wall: sequential={t_seq:.2f}s parallel(8)={t_par:.2f}s "
          f"speedup={t_seq / t_par:.1f}x (stub sleep 20ms/call)")
    assert len(seq) == len(gd.CONDITIONS_PHASE1B), "one record per condition expected"
    assert s == p, "MISMATCH: content differs between sequential and parallel"
    assert s_ord == p_ord, "MISMATCH: record/sample ordering differs"
    # n_samples=2 sample-order check too
    kwargs["n_samples"] = 2
    seq2 = gd.run_primary_one_respondent(respondent, parallel=1, **kwargs)
    par2 = gd.run_primary_one_respondent(respondent, parallel=8, **kwargs)
    assert json.dumps(seq2, default=str) == json.dumps(par2, default=str), \
        "MISMATCH at n_samples=2 (sample ordering)"
    print("✓ EQUIVALENCE PASSED: parallel records byte-identical to sequential "
          "(incl. ordering, n_samples=1 and 2)")


if __name__ == "__main__":
    main()

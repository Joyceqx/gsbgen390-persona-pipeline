"""End-to-end equivalence for the across-respondent pool: run_phase1 with
parallel_respondents=1 vs 6 on N=10 respondents (stubbed LLM, random dispatch,
Phase 1B conditions) must produce the same record SET (order may differ — the
parallel path persists in completion order by design) and identical per-record
content. Also exercises resume: a second parallel invocation must be a no-op.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))
import gss_driver as gd

SCRATCH = Path(__file__).resolve().parent / "_tmp_parallel_equiv"; SCRATCH.mkdir(exist_ok=True)


def fake_call_llm_meta(system, user, model, temperature=0.7, seed=42, **kw):
    time.sleep(0.02)
    return {
        "text": str(seed % 3 + 1),
        "model_returned": model,
        "system_fingerprint": f"fp_{seed}",
        "provider": "stub",
        "tokens_in": len(system),
        "tokens_out": 1,
    }


def canon(path):
    recs = json.loads(Path(path).read_text())
    keyed = {
        (r["respondent_id"], r["condition"], r["model"], r["prompt_id"]):
            json.dumps(r, sort_keys=True, default=str)
        for r in recs
    }
    assert len(keyed) == len(recs), "duplicate (rid, cond, model, prompt) records!"
    return keyed


def main():
    gd.call_llm_meta = fake_call_llm_meta

    out_seq = SCRATCH / "pool_seq.json"
    out_par = SCRATCH / "pool_par.json"
    for f in (out_seq, out_par):
        f.unlink(missing_ok=True)

    common = dict(
        n=10,
        models=["random"],
        prompt_id="P1",
        n_samples=1,
        seed=42,
        do_primary=True,
        do_sensitivity=False,
        verbose=False,
        conditions=gd.CONDITIONS_PHASE1B,
    )

    t0 = time.time()
    gd.run_phase1(output_path=out_seq, parallel=1, parallel_respondents=1, **common)
    t_seq = time.time() - t0
    t0 = time.time()
    gd.run_phase1(output_path=out_par, parallel=8, parallel_respondents=6, **common)
    t_par = time.time() - t0

    seq, par = canon(out_seq), canon(out_par)
    assert set(seq) == set(par), "record key sets differ"
    diffs = [k for k in seq if seq[k] != par[k]]
    assert not diffs, f"content differs for {diffs[:3]}"
    print(f"✓ record sets identical: {len(seq)} records "
          f"({len({k[0] for k in seq})} respondents × {len(gd.CONDITIONS_PHASE1B)} conditions)")
    print(f"wall: sequential={t_seq:.1f}s pooled(6 resp × 8 calls)={t_par:.1f}s "
          f"speedup={t_seq / t_par:.1f}x (stub 20ms/call)")

    # Resume no-op: re-invoke the pooled path on the completed artifact.
    n_before = len(json.loads(out_par.read_text()))
    calls = {"n": 0}
    real_fake = gd.call_llm_meta
    def counting(*a, **kw):
        calls["n"] += 1
        return real_fake(*a, **kw)
    gd.call_llm_meta = counting
    gd.run_phase1(output_path=out_par, parallel=8, parallel_respondents=6, **common)
    n_after = len(json.loads(out_par.read_text()))
    assert n_before == n_after == 60, f"resume changed record count {n_before}->{n_after}"
    assert calls["n"] == 0, f"resume issued {calls['n']} LLM calls (expected 0)"
    print("✓ resume no-op: 0 calls issued, record count unchanged")

    # Partial resume: delete 2 respondents' records, rerun pooled, expect only those redone.
    recs = json.loads(out_par.read_text())
    dropped_rids = sorted({r["respondent_id"] for r in recs})[:2]
    recs = [r for r in recs if r["respondent_id"] not in dropped_rids]
    out_par.write_text(json.dumps(recs))
    calls["n"] = 0
    gd.run_phase1(output_path=out_par, parallel=8, parallel_respondents=6,
                  force_resume_partial=True, **common)
    par2 = canon(out_par)
    assert set(par2) == set(seq), "partial resume did not restore the full record set"
    diffs = [k for k in seq if seq[k] != par2[k]]
    assert not diffs, "partial-resume records differ from sequential reference"
    assert calls["n"] > 0, "partial resume issued no calls?"
    print(f"✓ partial resume: rids {dropped_rids} redone ({calls['n']} calls), "
          f"records byte-identical to sequential reference")


if __name__ == "__main__":
    main()

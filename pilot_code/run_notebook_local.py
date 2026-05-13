"""Run persona_pipeline.ipynb locally (Colab cells patched)."""
import json
import os
import sys
from pathlib import Path

WORK = Path("/Users/joyce/Developer/gsbgen390")
os.chdir(WORK)

# --- API key from local file ---
key = (WORK / "Openai_api.txt").read_text().strip()
os.environ["OPENAI_API_KEY"] = key
print(f"API key loaded ({len(key)} chars)")

# --- Load notebook ---
nb = json.loads((WORK / "persona_pipeline.ipynb").read_text())

# --- Patch cell 8 (was Colab files.upload) to load from cookiy_transcripts/ ---
LOCAL_LOAD = '''\
from pathlib import Path
TRANSCRIPTS = {}
for fn in ["study1_interview_p1.json", "study1_interview_p2.json", "study2_survey_p1.json"]:
    p = Path("cookiy_transcripts") / fn
    data = json.loads(p.read_text())
    TRANSCRIPTS[fn] = data
    print(f"loaded {fn}: {len(data['transcript'])} turns")
assert len(TRANSCRIPTS) >= 1, "no transcripts loaded"
'''

# --- Execute code cells in order, skipping Colab-specific download ---
def _display(obj=None, *a, **kw):
    """Jupyter display() stub: just print or call to_string for DataFrames."""
    if obj is None:
        return
    if hasattr(obj, "to_string"):
        print(obj.to_string())
    else:
        print(obj)
ns = {"__name__": "__main__", "display": _display}
for i, c in enumerate(nb["cells"]):
    if c["cell_type"] != "code":
        continue
    src = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]

    if i == 8:
        src = LOCAL_LOAD

    # Skip Jupyter shell magics (!pip, %magic) — only used to bootstrap Colab.
    src_stripped = src.lstrip()
    if src_stripped.startswith("!") or src_stripped.startswith("%"):
        print(f"\n========== CELL {i} (SKIPPED Jupyter magic) ==========")
        print(src[:120])
        continue

    # Strip Colab-only file download tail of cell 30
    if "google.colab" in src and "files.download" in src:
        src = src.split("# Optional: download")[0] if "# Optional: download" in src else src
        src = src.replace("from google.colab import files", "")
        src = src.replace("files.download(", "# files.download(")

    # Skip plt.show() — we're headless
    src = src.replace("plt.show()", "plt.close()")

    print(f"\n========== CELL {i} ==========")
    print(src[:200] + ("..." if len(src) > 200 else ""))
    print("---- output ----")
    sys.stdout.flush()
    try:
        exec(compile(src, f"<cell {i}>", "exec"), ns)
    except SystemExit:
        pass
    except Exception as e:
        print(f"!! CELL {i} FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # After cell 20 (LLM dispatcher) is defined, wrap _call_openai with retry+backoff
    if i == 20 and "_call_openai" in ns:
        import time
        _orig_openai = ns["_call_openai"]
        def _call_openai_with_retry(system, user, model, temperature):
            delay = 4.0
            for attempt in range(8):
                try:
                    return _orig_openai(system, user, model, temperature)
                except Exception as e:
                    msg = str(e).lower()
                    if "rate" in msg or "429" in msg or "timeout" in msg:
                        wait = delay * (2 ** min(attempt, 4))
                        print(f"  [retry {attempt+1}/8 after {wait:.0f}s due to: {type(e).__name__}]", flush=True)
                        time.sleep(wait)
                        continue
                    raise
            raise RuntimeError("max retries exceeded")
        ns["_call_openai"] = _call_openai_with_retry
        print("  [injected retry+exponential-backoff wrapper around _call_openai]")

print("\n========== DONE ==========")

# Persist RESULTS (per-item primary + samples for each condition) so we can
# re-score offline (e.g., on a leak-free subset of eval items).
outputs_dir = WORK / "outputs"
outputs_dir.mkdir(exist_ok=True)
results_path = outputs_dir / "persona_answers_full.json"
results = ns.get("RESULTS", [])
def _safe(v):
    if isinstance(v, dict):
        return {k: _safe(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_safe(x) for x in v]
    if hasattr(v, "to_dict"):
        return v.to_dict()
    return v
serial = [{
    "arm": r["arm"], "respondent": r["respondent"], "condition": r["condition"],
    "primary": _safe(r["primary"]), "samples": _safe(r["samples"]),
} for r in results]
results_path.write_text(json.dumps(serial, indent=2, default=str))
print(f"Saved {len(serial)} per-condition records to {results_path.name}")

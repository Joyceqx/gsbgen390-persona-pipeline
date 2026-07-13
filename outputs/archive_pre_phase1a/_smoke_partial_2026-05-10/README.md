# Partial smoke artifacts — DELETED 2026-05-10 night

This directory previously contained three partial NDJSON files that were
created on 2026-05-10 by a Claude session verifying `gss_driver.py`
named-mode banner behavior. The driver had been invoked with
`run_in_background:true` and left dispatching API calls before being
killed, producing partial-record JSONs at canonical-looking paths.

The JSON files have been **deleted** per Joyce's 2026-05-10 night
directive (Audit-fresh-4 critical: "Quarantine or remove the
official-looking partial output JSON files before OSF lock and paid
execution"). They had no scientific value — `llm_raw_text` was empty
across all records (API calls returned empty/errored).

This directory + README is preserved as a marker so future sessions
recognize that:
1. The canonical paid-run output paths (`outputs/gss_phase1_records_n*_*_seed42.json`)
   should be **empty before any paid Phase 1 run**.
2. The driver supports resume-by-existing-output; if stray partial files
   reappear at those paths, the driver will silently resume from them
   and produce nonsense. The `gss_driver.py` partial-resume guard
   (added 2026-05-10 night per Audit-fresh-4 P1) refuses to resume
   from a file with suspiciously few records, but the safest discipline
   is to ensure `outputs/gss_phase1_records*.json` is absent before
   invoking the locked named modes.

If you find this directory containing **only this README**, that's the correct state. Any `gss_phase1_records*.json` reappearing here means a future driver invocation re-created stray partials — investigate.

When ready for the OSF lock + paid Phase 1 run, this entire directory may be deleted as a final cleanup step.

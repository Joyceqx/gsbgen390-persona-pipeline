# Dashboard — GSBGEN390 Persona Pipeline

Static HTML dashboard, deployable to GitHub Pages. Self-contained: just `index.html` + `style.css` + `app.js` + `data/`.

## Local preview

The dashboard fetches data via `fetch('./data/...')`, which won't work over `file://` due to browser CORS. Use a local server:

```bash
cd ~/Developer/gsbgen390/docs
python3 -m http.server 8080
# then open http://localhost:8080
```

If you skip the local server, the page still loads — it falls back to inline mock data so you can see the layout.

## Update with real data

After every pipeline run:

```bash
cd ~/Developer/gsbgen390
python3 build_site_data.py     # converts CSVs → docs/data/*.json with naming normalization
git add docs/data
git commit -m "Update dashboard with metrics from $(date +%Y-%m-%d) run"
git push
```

`build_site_data.py` reads `metrics_per_respondent.csv`, `metrics_with_leakage_audit.csv`, and `eval_answers_extracted.csv`, and writes four files into `docs/data/` after normalizing pipeline-internal IDs (`study1_interview_p1`, `A_demographics`) to the site's preferred form (`R1`, `A_demographic_only`).

GitHub Pages auto-rebuilds; refresh the live URL.

## Deploy to GitHub Pages

1. Create a public GitHub repo (or use an existing one).
2. Push the entire `GSBGEN390` directory.
3. In repo settings → Pages → Build from branch → `main` → `/docs`.
4. Site URL appears within ~1 minute.

## Privacy reminder

GitHub Pages is **public**. Before pushing:

- ✅ Aggregate metrics, condition labels, design overview — fine to publish.
- ⚠️ Per-respondent metrics (R1, R2 numbers) — OK if anonymized via codes (already done).
- ❌ Raw transcript content / personal disclosures — do NOT publish. Keep transcripts in the local `responses/` and `cookiy_transcripts/` folders only; never `cp` them to `docs/data/`.

If unsure, ask Prof. Bayati about IRB / Cookiy consent terms before going public.

## File structure

```
docs/
├── README.md              ← this file
├── index.html             ← entry point
├── style.css              ← academic-modern theme, dark + light auto
├── app.js                 ← Chart.js renderers + drill-down logic
└── data/
    ├── metrics_per_respondent.json   (drop in after pipeline run)
    ├── metrics_aggregate.json        (drop in after pipeline run)
    └── eval_answers_extracted.csv    (drop in after pipeline run)
```

## Sections (8 total)

0. **Intro** — Park 2024 context + thesis question
1. **Pipeline architecture** — 8-stage flow diagram
2. **The data** — Cookiy sessions, eval/construction batteries, truth-table summary
3. **Conditions** — A/B/C/D + LOO ablation cards
4. **Headline results** — per-condition charts (MAE, categorical accuracy, self-consistency)
5. **Feature importance** — LOO ablation horizontal bar chart
6. **Drill-down** — per-respondent, per-item LLM answers vs ground truth
7. **Limitations** — known deviations and caveats
8. **Next steps** — thesis roadmap

## To customize

- **Theme colors**: edit CSS variables at top of `style.css` (`--bg`, `--accent`, etc.)
- **Add a new chart**: define `<canvas id="chart-foo"></canvas>` in `index.html`, add a `renderFooChart(metrics)` function in `app.js`, and call it from the boot block at bottom.
- **Different layout**: sections are independent CSS-grid blocks; rearrange `<section>` elements in `index.html`.

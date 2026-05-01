# How to run `persona_pipeline.ipynb` on Colab

**Estimated time end-to-end: 15–20 minutes.** API cost: roughly $5–10 depending on toggles.

## Step-by-step

### 1. Open Colab and upload the notebook

- Go to [colab.research.google.com](https://colab.research.google.com)
- Click **File → Upload notebook**
- Upload `persona_pipeline.ipynb` from your `~/Documents/GSBGEN390/` folder

### 2. Set your OpenAI API key (once, persistent)

Recommended way: use Colab Secrets so the key isn't hardcoded.

- Click the 🔑 key icon in the left sidebar
- Click "Add new secret"
- Name: `OPENAI_API_KEY`, Value: paste the key from `Openai_api.txt`
- Toggle "Notebook access" to ON for this notebook

(If Secrets isn't available, the notebook will prompt you to paste it.)

### 3. Run cells 1 → 6 (setup)

Cells 2 (install), 4 (imports), 6 (API key), and 8 (file upload). When cell 8 runs, the file upload widget appears — upload these three files:

- `cookiy_transcripts/study1_interview_p1.json`
- `cookiy_transcripts/study1_interview_p2.json`
- `cookiy_transcripts/study2_survey_p1.json`

You should see "✓ ... 103 turns" / "✓ ... 84 turns" / "✓ ... 75 turns" output.

### 4. Run cells 7 → 9 (parsing)

Cells 10 (batteries), 12 (normalizers), 14 (parser), 16 (parse all). Cell 16 displays two DataFrames:
- The 15-item eval truth answers per respondent (should be 15/15 filled for all 3)
- The 18-item construction-survey answers (should be 18/18 filled for the Study 2 row)

If any cells show empty values, ping me — the anchors may need patching for your specific transcripts.

### 5. Run cells 10 → 11 (prompt builder + LLM dispatcher)

These define functions; no API calls yet. Should take seconds.

### 6. Run cell 22 (baseline conditions) — this is where the API spending starts

You'll see one line per condition like:
```
[Study1/study1_interview_p1/A_demographics] running...
[Study1/study1_interview_p1/B_description] running...
[Study1/study1_interview_p2/C_interview] running...
[Study2/study2_survey_p1/A_demographics] running...
[Study2/study2_survey_p1/D_survey] running...
```

8 baseline conditions × 15 items × 2 samples = **240 API calls**, ~$2–4. Expect ~3–5 minutes.

### 7. Run cell 24 (LOO ablation)

4 ablation conditions × 15 items × 2 samples = **120 API calls**, ~$1–2. Expect ~2 minutes.

### 8. Run cell 26 (scoring) and cell 28 (visualization)

Produces the metrics DataFrame and two charts. The LOO chart shows which feature category, when removed, hurt the survey persona most — this is your headline feature-importance result.

### 9. Run cell 30 (save + download metrics CSV)

Saves `metrics_per_respondent.csv` to the Colab session and offers a download link. Save it to your laptop's `~/Documents/GSBGEN390/` so we can include the numbers in the writeup.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Module 'openai' not found" | Cell 2 didn't run | Re-run cell 2 |
| API auth error | Key not loaded | Re-run cell 6, paste key when prompted |
| "0 transcripts loaded" | Wrong file format | Make sure you uploaded the `.json` files (not `.txt`) |
| Eval row has nulls | Anchor regex missed a question stem | Send me the transcript ID and missing item ID |
| Persona returns weird answers | LLM not following format | Check the per-condition output; rerun if needed (cache will skip already-completed calls) |

## What the LOO chart will tell you

The bar with the **largest positive Δ MAE** (highest bar) is the feature category whose removal hurt persona accuracy most — i.e., the **most predictive category** at this pilot scale.

Don't over-interpret: with N=1 in the survey arm, the result is a single point estimate per category. Treat as exploratory direction, not as evidence. The thesis-stage replication needs N≥30 to put error bars on these.

## After the run

Send me three things and I'll polish the meeting handout:
1. A screenshot of the eval-truth + construction-truth DataFrames (cell 16 output)
2. A screenshot of the metrics DataFrame (cell 26 output)
3. A screenshot of the LOO chart (cell 28 output)

Or just download `metrics_per_respondent.csv` and tell me when it's done.

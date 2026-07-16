# Phase 1B Raw Data — Column Dictionary & Quickstart

File: `phase1b_raw.parquet` — 159,804 rows, one row per
(respondent, condition, item) LLM prediction. N = 3,309 GSS 2024
respondents × 6 conditions × ~8 on-ballot items each.

## Load it

```python
import pandas as pd
df = pd.read_parquet("phase1b_raw.parquet")
```

```sql
-- DuckDB
SELECT condition, AVG(abs_err::DOUBLE / span) AS mae
FROM 'phase1b_raw.parquet' ...
```

## Columns

| Column | Type | Meaning |
|---|---|---|
| `respondent_id` | int | GSS 2024 respondent (`ID_`) |
| `model` | str | Panel model that answered this respondent (same across all 6 conditions — dispatch is per respondent, seeded hash) |
| `prompt` | str | `P1` everywhere (the locked cell) |
| `condition` | str | `Full`, `drop_demographic`, `drop_behavioral`, `drop_psychological`, `drop_attitudinal`, `random_battery_drop` |
| `item` | str | Predicted GSS item (12 primary_eval attitude items) |
| `true_code` | int | Respondent's actual GSS answer |
| `pred_code` | Int (nullable) | Model's parsed answer; null when `parse_ok = false` |
| `parse_ok` | bool | Whether the raw response parsed to a valid code |
| `abs_err` | Int (nullable) | \|pred − true\| on the item's raw scale; null when unparsed |
| `error_type` | str | `ok` / `parse_fail` (zero `provider_error` in final artifact) |
| `random_dropped_battery` | str (nullable) | Only in `random_battery_drop`: which battery was ablated for this (respondent, item). Join key for the per-battery analysis |
| `provider`, `model_returned`, `system_fingerprint`, `tokens_in/out`, `cost_usd`, `timestamp`, `sample_position` | — | provenance / audit fields |

## Scoring conventions (match the report)

- Normalized error = `abs_err / (max_code − min_code)` per item, in [0,1].
- **Conservative** (primary): `parse_ok = false` → error 1.0.
  **Optimistic**: unparsed rows dropped. Both reported.
- Macro-averaging: mean within respondent, then across respondents.
- Headline cohort excludes the 200 Phase 1A selector respondents
  (`sample_respondents(200, seed=42)`); they are 6% of rows.

## Two example analyses

```python
# Bin-LOO ΔMAE (combined column)
span = df["item"].map(ITEM_SPANS)          # see report §2 for ranges
df["err"] = (df["abs_err"] / span).where(df["parse_ok"], 1.0)
full = df[df.condition == "Full"].groupby("respondent_id")["err"].mean()
drop = df[df.condition == "drop_attitudinal"].groupby("respondent_id")["err"].mean()
print((drop - full).mean())                # ≈ +0.0095

# Per-battery paired ablation
rbd  = df[df.condition == "random_battery_drop"]
pair = rbd.merge(df[df.condition == "Full"],
                 on=["respondent_id", "item"], suffixes=("_abl", "_full"))
ok   = pair[pair.parse_ok_abl & pair.parse_ok_full]
delta = (ok.abs_err_abl - ok.abs_err_full) / ok.item.map(ITEM_SPANS)
print(delta.groupby(ok.random_dropped_battery).mean().sort_values())
```

Full reproduction: `python3 src/phase1b_analysis.py` regenerates every table
in `phase1b_tables.xlsx` from this parquet (BCa bootstrap B=10,000, seed 42).

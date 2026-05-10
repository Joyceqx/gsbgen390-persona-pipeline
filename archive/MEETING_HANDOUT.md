# GSBGEN390 — Comprehensive Project Brief

> ⚠️ **FROZEN AS PILOT-WRAP STATE (2026-04-30)** — This document captures the project state at the end of the pilot phase. The Phase 1 design described here ("GSS Three-Wave Panel 2010-2014, normalized accuracy directly comparable to Park's 0.82-0.83") **was abandoned in May 2026** in favor of a single-wave GSS 2024 design with raw-accuracy primary metrics, no test-retest normalization, and a forbidden-language list that explicitly bans "normalized accuracy directly comparable to Park" claims. **For the current Phase 1 design, see `gss_phase1_design.md` (especially §1.0, §4, §10, §11.1) and `PROJECT_SYNTHESIS.md` §3.** Do NOT cite this file as the live Phase 1 spec. It is preserved for pilot-era historical reference and decision-log purposes only.

**Joyce Yu · for Prof. Mohsen Bayati · 2026-04-30**

This document is written in two complete versions: **English first, then 中文** (scroll down). Either version covers the full project state. Pick whichever reads faster.

---

# Part I — English

## 1. Background & motivation

This independent research project replicates and extends **Park, Zou, Shaw, Hill, Cai, Morris, Willer, Liang & Bernstein (2024)** — *Generative Agent Simulations of 1,000 People* (arXiv:2411.10109). The paper is the foundational work behind the Stanford spinout **Simile**.

What Park did:

1. Recruited 1,052 stratified U.S. adults via a market-research panel.
2. Conducted ~2-hour AVP-protocol-based interviews with each respondent using a custom voice-to-voice AI moderator (not a human interviewer).
3. Constructed an LLM "persona agent" for each respondent by feeding the verbatim transcript into GPT-4o as a system prompt — no fine-tuning, just in-context prompting.
4. Asked each persona agent to answer the same held-out battery (GSS attitudinal items, BFI-44 personality, 5 behavioral economic games, 5 social-science experiments) that the same real respondent had also answered.
5. Compared persona-predicted answers vs. respondent's own answers. Headline finding: persona agents reach ~83% of the respondent's own two-week test-retest reliability on GSS items.

**This means LLM personas don't just simulate "a generic person" — they can simulate a *specific* real person well enough to predict that person's survey responses.**

The Park 2024 paper has been quietly updated. The **arXiv v2 version**, retitled *LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals*, reorganized the conditions and added a per-outcome breakdown that materially changes how to read the paper. I'll explain that in §5 below — it's the most important framing update of this sprint.

## 2. Research objective (refined post-pilot)

The thesis this project is leading toward asks: **which survey-collectible feature categories most predict LLM-persona fidelity, and on which outcome dimensions?**

The pilot's role is to prove the pipeline runs end-to-end and to surface the design questions a higher-N replication will need to resolve.

The original framing in the proposal was: *"surveys-only nearly matches interviews — let's figure out which survey features do the work."* After re-reading Park v2 carefully, the framing has been refined to:

> **Park v2 shows the surveys ≈ interview tie holds *only* on GSS attitudes (0.82 vs 0.83). Surveys lag interviews by 0.15 on BFI personality and by 0.28 on behavioral economic games. The thesis question is therefore *outcome-stratified*: which feature category closes which part of that gap on which outcome dimension?**

This is sharper than the original framing because it asks two questions simultaneously (feature category × outcome dimension) and produces a 4×3 matrix as the headline artifact — something Park v2 implies but does not produce.

## 3. Pilot work completed (this sprint, 2026-04-29 to 2026-04-30)

In ~1.5 days I built and ran an end-to-end pilot replication.

**Two-arm design** (forced by Cookiy's 15-min cap and inability to pair respondents across studies):

| | Study 1 — Interview arm | Study 2 — Survey arm |
|---|---|---|
| N | 2 panel respondents | 1 panel respondent |
| Format | 15-min combined session: ~9-min open AVP-style interview + ~6-min held-out eval | 15-min combined session: 18 structured survey items + ~6-min held-out eval |
| Conditions | A demographics-only · B persona description · C interview-conditioned | A demographics-only · D survey-conditioned · 4 LOO ablations dropping each of {demographic, behavioral, psychological, attitudinal} |

**Pipeline characteristics:**
- LLM-persona-in-context architecture (transcript → system prompt), identical to Park's method
- Default model GPT-4o (matching Park); Claude Sonnet 4.6 supported for robustness checks
- Each eval item asked twice at temperature 0.7 → measures self-consistency in addition to accuracy-vs-truth
- Smart parser uses moderator's confirmation utterance as gold signal, robust to participants giving multi-attempt answers
- 100% parse rate (15/15 eval items × 3 respondents; 18/18 construction items × 1 respondent)
- Stem-anchored transcript splitter prevents eval Q&A leaking into the persona prompt — verified zero leakage
- Manual leakage audit on every eval item per respondent (STRONG / SOFT / CLEAN tagging) for robustness analysis

**Artifacts produced:**
- 3 Cookiy session transcripts collected and audited
- Truth-answer extraction CSV (`eval_answers_extracted.csv`) with 100% coverage
- Persona pipeline (`persona_pipeline.py` + `persona_pipeline.ipynb`) — runnable locally or on Colab in ~9 minutes for ~$3-5 in API
- 12 conditions × 15 eval items × 2 samples = full results in `metrics_per_respondent.csv` and `persona_answers_full.json`
- Leakage robustness audit (`metrics_with_leakage_audit.csv`) + visualization (`chart_robustness.png`)
- GitHub Pages dashboard: live results, methodology, leakage analysis
- Comprehensive design docs: `replication_scoping.md`, `STATUS.md`, `progress_report.md`, two cookiy briefs, `LIT_REVIEW.md`, `PRIMER.md`, `FUTURE_DESIGN.md`

## 4. Pilot results

### 4.1 Headline table — Likert MAE per condition (lower = closer to truth, 0 = perfect)

| Arm | Resp. | A demo | B desc | C/D | LOO best | LOO worst |
|---|---|---|---|---|---|---|
| Study 1 | P1 | 0.83 | 0.92 | **C: 0.08** | — | — |
| Study 1 | P2 | 1.17 | 0.75 | **C: 0.00** | — | — |
| Study 2 | S2-P1 | 0.50 | — | D: 0.83 | drop attitudinal: 0.58 | drop demographic: 1.17 |

How to read MAE: the average distance, in absolute value, between the LLM persona's predicted answer and the real respondent's answer on the 1-5 Likert scale. 0 = perfect match on every item; 0.83 ≈ "off by ~1 step on average per item"; theoretical max = 4.

**Study 1 (interview arm) — interview conditioning effect is large.** Condition C beats Condition A by ~0.75-1.17 MAE on both respondents. Direction matches Park v2's interview-only > demographics-only on GSS.

**Study 2 (survey arm) — A > D unexpectedly.** Adding the 18 construction items on top of demographics did not improve accuracy for this respondent. With N=1 this could be noise (≈ 2 items more wrong out of 12) or real signal that rich-context survey items beyond demographics aren't always additive. The LOO ranking shows dropping demographics hurt most (MAE 0.50 → 1.17), then psychological (0.92), then behavioral and attitudinal (smaller deltas).

**Caveat**: N=2 + N=1 cannot statistically separate any of these effects. The pilot demonstrates the architecture works; numbers are illustrative.

### 4.2 Leakage robustness audit (defense against the "in-session priming" objection)

Because Cookiy can't pair respondents across studies, our eval is administered in the same session as the interview/construction — Park's protocol uses a 2-week gap. This means **some eval items have their answer effectively pre-stated in the interview** (e.g., P1 disclosed political ideology during the open interview, then minutes later was asked to self-place on the 1-7 liberal-conservative eval scale). Question: is C's win driven by leakage or by real prediction?

I manually audited each of the 15 eval items per respondent against their interview transcript and tagged each as **STRONG** (construct directly stated by participant or paraphrased by moderator), **SOFT** (construct semantically related), or **CLEAN** (no detectable mention). Then I re-scored each condition under three filters:

| | full eval (15) | strict-clean (drop STRONG) | broad-clean (drop STRONG + SOFT) |
|---|---|---|---|
| P1/A | 0.83 | 0.70 | 1.00 |
| P1/B | 0.92 | 0.80 | 1.00 |
| **P1/C** | **0.08** | **0.10** | **0.00** |
| P2/A | 1.17 | 1.20 | 1.00 |
| P2/B | 0.75 | 0.80 | 0.75 |
| **P2/C** | **0.00** | **0.00** | **0.00** |

**Finding**: C's advantage over A and B does not collapse when leak-suspect items are dropped. Even on the broad-clean subset (only items where the construct was *not* mentioned in any form in the interview), C's MAE remains essentially zero. The interview transcript apparently encodes enough personality structure that the LLM can predict held-out responses on uncovered items by inference, not just regex.

The 0.00 numbers are noisy (broad-clean for P2 has only 4 items). The honest headline is the **strict-clean** column: drop the 3 STRONG-leaked items (bfi_c, polviews, happy/satjob) and C still wins by 0.6-1.2 MAE over A.

## 5. The Park v1 → v2 reconciliation (this sprint's most important framing update)

The proposal v2 cited a "85%" headline. In re-reading the actual Park PDF I discovered:

- **arXiv v1** (original release, *Generative Agent Simulations of 1,000 People*) reported a normalized-accuracy headline of **~0.85** for interview-only on GSS. This is what the proposal cited.
- **arXiv v2** (current live version, retitled *LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals*) reorganized the conditions and reports the per-outcome breakdown below.

Both versions live at the same arXiv ID, with v2 being the current canonical citation.

**Park v2 headline numbers (% of two-week test-retest reliability, GSS attitudinal items):**

| Construction condition | GSS accuracy |
|---|---|
| Demographics only | 74% |
| Interview only | 83% |
| Surveys only | 82% |
| Interview + surveys combined | 86% |

**Critical caveat — "surveys ≈ interview" is GSS-specific.** v2 also reports per-outcome breakdowns:

| Outcome | Interview | Surveys-only | Gap |
|---|---|---|---|
| GSS attitudes (normalized accuracy) | 0.83 | 0.82 | tie |
| BFI-44 personality (normalized correlation) | 0.80 | 0.65 | surveys lag by 0.15 |
| Behavioral economic games (normalized correlation) | 0.66 | 0.38 | surveys lag by 0.28 |

**Implication for the thesis**: the productive question is not *"can surveys substitute for interviews?"* (no — depends on the outcome) but ***"which survey-collectible feature categories close which parts of the gap on which outcome dimensions?"*** The interview→surveys delta is small for attitudes, moderate for personality, and large for behavioral games — that pattern itself motivates an outcome-stratified feature-importance analysis. **This is exactly the analysis Park did not run.**

## 6. Two-phase thesis plan

The thesis question is two-way (feature category × outcome dimension). Different cells of the matrix demand different methods. Proposed two-phase plan:

### Phase 1 — GSS public-data feature-importance (~1-4 weeks, ~$300-500 API)
Full design: [`gss_phase1_design.md`](gss_phase1_design.md)

- **Data source**: GSS Three-Wave Panel 2010-2014 (NORC), N≈1,500 same respondents across waves. Public, free, no recruitment friction.
- **Method**: Park's persona-in-context, but inputs are wave-1 items, held-out outcomes are wave-3 items. Within-person wave-1↔wave-3 agreement supplies a **test-retest baseline** — for the first time we can report normalized accuracy directly comparable to Park's 0.82-0.83 figure.
- **Coverage**: GSS-attitudes outcome row only (Park's row where surveys ≈ interview).
- **LOO ablation**: 5 conditions per respondent (full + 4 drops, one per feature category). Bootstrap 95% CIs.

### Phase 2 — Interview-decomposed feature-importance study (~7-9 weeks, ~$1,500-1,750)
Full design: [`thesis_phase2_design.md`](thesis_phase2_design.md)

- **Recruitment**: N=20-30 panel respondents via **Prolific** (Cookiy's 15-min cap is incompatible with this design; Prolific supports 2-week recontact across waves).
- **Wave 1 — long modular interview (30-45 min)**: AVP-style, but the moderator script is structured into **4 modules each mapped 1:1 to a feature category**:
  - M1 — Life basics (demographic)
  - M2 — Daily behaviors (behavioral)
  - M3 — Inner self (psychological)
  - M4 — Values & attitudes (attitudinal)
- **Moderator**: self-hosted AI agent built on OpenAI Realtime API (production replacement for the pilot's Cookiy moderator). Documented as a deployment recipe — itself a methodological contribution.
- **2-week separation** before Wave 2 (Park's protocol; resolves pilot's in-session priming concern).
- **Wave 2 — outcome battery (25 min)**: BFI-44 + 5 behavioral-game survey vignettes + 15 GSS attitudinal items.
- **Transcript decomposition**: cut at module boundaries, then LLM-assisted reassignment of cross-module utterances. 10% sample human-coded for validation.
- **LOO ablation operates *at the interview-content level*** (drop M1 / M2 / M3 / M4). Directly decomposes Park's monolithic "interview-only" condition into pre-registered content bins.
- **Coverage**: BFI row + games row + GSS row. The two rows where Park found the largest interview-vs-surveys gap.

### Composed thesis output

The full **4 (feature category) × 3 (outcome dimension) feature-importance matrix**:

|  | BFI MAE Δ | Games MAE Δ | GSS MAE Δ |
|---|---|---|---|
| Drop demographic | ?? (Phase 2) | ?? (Phase 2) | ?? (Phase 1 + Phase 2) |
| Drop behavioral | ?? (Phase 2) | ?? (Phase 2) | ?? (Phase 1 + Phase 2) |
| Drop psychological | ?? (Phase 2) | ?? (Phase 2) | ?? (Phase 1 + Phase 2) |
| Drop attitudinal | ?? (Phase 2) | ?? (Phase 2) | ?? (Phase 1 + Phase 2) |

This matrix is the headline artifact — Park v2 implies it but does not produce it.

### Strategic logic

- **Phase 1 is cheap and answers one row at high N.** Confidence-intervaled feature-importance ranking on GSS attitudes; first comparison of normalized accuracy directly to Park's 0.82-0.83 at comparable N.
- **Phase 2 is more expensive but answers two rows where the gap actually matters.** Small N (20-30) is justified because: (a) Park's effect sizes are large (0.15, 0.28); (b) BFI is item-rich (44 items per respondent); (c) Phase 2 is *confirmatory* relative to Phase 1's priors, not exploratory.
- **Composed**, the two phases produce the full matrix in one semester, ~$2,000 total budget.
- **Pre-registration on OSF** before each phase launches.

## 7. Open methodological questions

1. **In-session eval priming (pilot limitation)** — Pilot's eval is in the same session as the interview. Documented and audited via leakage filter, but Phase 2's 2-week separation is the real fix. Is the leakage-filtered analysis sufficient defense for the *pilot* writeup, or do we re-collect even at pilot scale?
2. **LOO ranking instability at low N** — Across two pilot runs at temperature 0.7, the "most-important-when-dropped" category changed. Confidence-interval estimation of LOO effects requires multi-seed runs and N≥30; pilot is direction-only.
3. **Test-retest baseline** — Park reports % of test-retest reliability. We don't have it. Phase 1 recovers it from the GSS panel structure; Phase 2 does not have it. Acceptable, or do we add a within-person retest sub-study to Phase 2?
4. **AI-moderator paraphrase variance** — Cookiy moderators paraphrase eval items. Smart parser absorbs this for the pilot; Phase 2 self-hosted moderator gives us tighter control. Acceptable noise at scale, or a real concern?
5. **BFI-10 → BFI-44 upgrade** — Pilot used BFI-10 for time. Real study (especially Phase 2) needs BFI-44 for trait-level scoring to be statistically meaningful.
6. **Eval-battery extension to behavioral games** — Phase 2 uses survey-vignette versions of dictator/ultimatum/trust/public-goods/donation games. This is a deviation from Park's real-money games. Acceptable proxy or methodological concern?
7. **Module structure for Phase 2 interview** — Is the 4-module structure (1:1 with feature categories) the right granularity, or should it follow SCOPE's 8-facet sociopsychological taxonomy (Bao et al. 2026)?

## 8. What I'd like to discuss tomorrow

Five concrete decisions:

1. **Confirm or reframe the thesis question** in light of Park v2's outcome-stratified findings.
2. **Endorse the two-phase plan** (Phase 1 GSS public-data + Phase 2 interview-decomposed Prolific study) vs. an alternative direction.
3. **Endorse the platform pivot for Phase 2** — Cookiy → Prolific + self-hosted OpenAI Realtime API moderator. Required because Cookiy's 15-min cap blocks the long modular interview design.
4. **Confirm 4-bin granularity** for the feature taxonomy (or argue for SCOPE-style finer subdivision).
5. **Pre-registration commitment** — agree to OSF pre-registration before Phase 1 launches.

Beyond these five, I'd love your input on whether the pilot's leakage-audit defense is enough for a 3-5 page pilot writeup, or whether to redo data collection at the pilot stage with proper 2-week separation before scaling.

---

*Supporting documents in `~/Documents/GSBGEN390/`:*
- [`gss_phase1_design.md`](gss_phase1_design.md) — Phase 1 standalone proposal
- [`thesis_phase2_design.md`](thesis_phase2_design.md) — Phase 2 standalone proposal
- [`progress_report.md`](progress_report.md) — full sprint narrative
- [`STATUS.md`](STATUS.md) — current state
- [`replication_scoping.md`](replication_scoping.md) — pilot design rationale
- [`FUTURE_DESIGN.md`](FUTURE_DESIGN.md) — full discussion agenda
- [`LIT_REVIEW.md`](LIT_REVIEW.md) — bibliography
- Live dashboard: `https://joyceqx.github.io/gsbgen390-persona-pipeline/`

---
---

# Part II — 中文版

## 1. 背景与动机

这个独立研究复现并扩展 **Park, Zou, Shaw, Hill, Cai, Morris, Willer, Liang & Bernstein (2024)** —— *Generative Agent Simulations of 1,000 People* (arXiv:2411.10109)。这篇是 Stanford spinout **Simile** 的奠基论文。

Park 做了什么：

1. 通过市场调研 panel 招募了 1,052 个分层抽样的美国成年人
2. 给每个人做了 ~2 小时的 AVP 协议访谈，访谈的主持人不是真人，是 Park 团队自建的语音 AI agent
3. 把每个人的访谈逐字稿丢进 GPT-4o 当 system prompt，构建 LLM "persona agent"——**没有 fine-tuning，纯 in-context prompting**
4. 让每个 persona 答跟真人答过的同一份测试集（GSS 态度题、BFI-44 人格、5 个行为经济学游戏、5 个社会科学实验）
5. 比对 persona 的预测答案 vs 真人自己的答案。核心发现：persona 的准确率达到了真人自己 2 周后重测一致率的 ~83%

**这意味着：LLM persona 不只能模仿"一般人"，它能模仿"具体某一个真人"，准到能预测这个真人的问卷答案。**

Park 这篇文章悄悄更新过。**arXiv v2 版本**改了标题为 *LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals*，重新组织了 condition，还加了一个按 outcome 分类的细分结果——这个细分**根本性地改变了文章的解读方式**。下面 §5 详细讲，这是这次 sprint 最重要的 framing 更新。

## 2. 研究目标（pilot 后精炼）

这个项目的最终 thesis 要回答：**哪些 survey-collectible 的 feature 类别最能预测 LLM persona 的 fidelity，以及在哪些 outcome 维度上？**

Pilot 的角色是：证明 pipeline 能跑通端到端，并且暴露出"高 N 复现"必须先解决的设计问题。

原 proposal 的 framing 是："surveys-only 几乎追平 interview——我们去研究哪些 survey feature 在做主要工作。" 仔细重读 Park v2 后，framing 精炼为：

> **Park v2 表明，surveys ≈ interview 这个等式*只在* GSS 态度题上成立（0.82 vs 0.83）。在 BFI 人格上 surveys 落后 interview 0.15，在行为经济学游戏上落后 0.28。所以 thesis 的研究问题是 *outcome-stratified* 的：哪类 feature 在哪类 outcome 上补 gap 最多？**

这个 framing 比原来的更锋利，因为它**同时问两个问题**（feature 类别 × outcome 维度），输出是一个 **4×3 feature-importance 矩阵**——这是 Park v2 暗示但没有产出的 artifact。

## 3. Pilot 完成的工作（这次 sprint，2026-04-29 到 2026-04-30）

我用 ~1.5 天搭好并跑通了端到端的 pilot 复现。

**两臂设计**（被 Cookiy 的 15 分钟上限和无法跨 study 配对受访者所迫）：

| | Study 1 — 访谈臂 | Study 2 — 问卷臂 |
|---|---|---|
| N | 2 个 panel 受访者 | 1 个 panel 受访者 |
| 形式 | 15 分钟综合 session：~9 分钟开放 AVP-style 访谈 + ~6 分钟测试题 | 15 分钟综合 session：18 道结构化问卷 + ~6 分钟测试题 |
| Conditions | A 只人口统计 · B 人物描述 · C 完整访谈 | A 只人口统计 · D 完整问卷 · 4 个 LOO ablation（逐一去掉 {人口/行为/心理/态度}）|

**Pipeline 关键特征：**
- LLM persona-in-context 架构（transcript → system prompt），跟 Park 完全一致
- 默认模型 GPT-4o（与 Park 一致），支持 Claude Sonnet 4.6 做 robustness 检查
- 每道测试题问两遍 temperature=0.7 → 同时算准确度 + 自一致性
- 智能 parser 用 moderator 的"我记下来是 X 分"作为 gold signal，对受访者多轮回答 robust
- Parse 率 100%（15/15 测试题 × 3 人；18/18 构建题 × 1 人）
- Stem-anchored transcript 切分器防止测试 Q&A 泄漏到 persona 输入——已验证零泄漏
- 对每个测试题手工标注 STRONG / SOFT / CLEAN 做泄漏 robustness 分析

**产出 artifact：**
- 3 份 Cookiy 访谈 transcript，已审计可用
- Truth-answer 提取 CSV (`eval_answers_extracted.csv`)，100% 覆盖
- Persona pipeline (`persona_pipeline.py` + `persona_pipeline.ipynb`)——本地或 Colab 运行约 9 分钟，API 成本 $3-5
- 12 conditions × 15 题 × 2 samples 完整结果 (`metrics_per_respondent.csv` + `persona_answers_full.json`)
- Leakage robustness audit (`metrics_with_leakage_audit.csv`) + 可视化 (`chart_robustness.png`)
- GitHub Pages dashboard：在线展示结果、方法、leakage 分析
- 完整设计文档：`replication_scoping.md`、`STATUS.md`、`progress_report.md`、两份 cookiy brief、`LIT_REVIEW.md`、`PRIMER.md`、`FUTURE_DESIGN.md`

## 4. Pilot 结果

### 4.1 核心数据表 — 各 condition 的 Likert MAE（越小越接近真值，0 = 完美）

| 臂 | 受访者 | A 人口统计 | B 描述 | C/D | LOO 最好 | LOO 最差 |
|---|---|---|---|---|---|---|
| Study 1 | P1 | 0.83 | 0.92 | **C: 0.08** | — | — |
| Study 1 | P2 | 1.17 | 0.75 | **C: 0.00** | — | — |
| Study 2 | S2-P1 | 0.50 | — | D: 0.83 | drop attitudinal: 0.58 | drop demographic: 1.17 |

MAE 怎么读：LLM persona 的预测答案跟真人答案在 1-5 Likert 量表上的平均绝对距离。0 = 每道题完全对上，0.83 ≈ 平均每题差 1 个等级，理论最大值 = 4。

**Study 1（访谈臂）—— 访谈条件效应巨大。** Condition C 在两个受访者上都比 Condition A 优 ~0.75-1.17 MAE。方向上跟 Park v2 的 interview-only > demographics-only on GSS 一致。

**Study 2（问卷臂）—— A > D 反直觉。** 在人口统计基础上加上 18 道结构化问卷，对这个受访者的预测准确率没有提升。N=1 的情况下这可能是 noise（≈ 12 题中多答错 2 题），也可能是真信号——"超过人口统计的 rich-context survey item 不一定 additive"。LOO 排序显示去掉人口统计伤害最大（MAE 0.50 → 1.17），其次心理（0.92），再次行为和态度（差距更小）。

**注意**：N=2 + N=1 在统计上无法分离这些效应。Pilot 证明的是架构跑通，数字本身是 illustrative 的。

### 4.2 泄漏 robustness 审计（应对"in-session priming"质疑）

由于 Cookiy 不能跨 study 配对受访者，我们的测试题跟访谈/构建是同一 session 做的——Park 的 protocol 是 2 周间隔。**这意味着有些测试题的答案在访谈里已经被"提前说出"了**（比如 P1 在开放访谈段聊到了政治立场，几分钟后被要求在 1-7 自由派-保守派量表上自评）。问题：C 的胜出是泄漏导致的，还是真预测？

我手工对每个受访者的 15 道题逐一审计 transcript，标注每题为 **STRONG**（受访者直接说出该构念，或主持人复述）/ **SOFT**（语义相关）/ **CLEAN**（任何形式都没提到）。然后在三种过滤下重算各 condition：

| | 完整测试 (15) | strict-clean（去掉 STRONG）| broad-clean（去掉 STRONG + SOFT）|
|---|---|---|---|
| P1/A | 0.83 | 0.70 | 1.00 |
| P1/B | 0.92 | 0.80 | 1.00 |
| **P1/C** | **0.08** | **0.10** | **0.00** |
| P2/A | 1.17 | 1.20 | 1.00 |
| P2/B | 0.75 | 0.80 | 0.75 |
| **P2/C** | **0.00** | **0.00** | **0.00** |

**发现**：去掉所有泄漏嫌疑题之后，C 仍然显著领先 A 和 B。即使在 broad-clean 子集上（只保留访谈里完全没提到的构念），C 的 MAE 仍接近零。**说明访谈 transcript 编码了足够的人格结构，让 LLM 能对未直接覆盖的构念做*推理*预测，而不是 regex 匹配。**

0.00 的数字有 noise（broad-clean 在 P2 只有 4 道题）。诚实的 headline 是 **strict-clean** 这一列：去掉 3 个 STRONG-leaked 题（bfi_c, polviews, happy/satjob）后 C 仍以 0.6-1.2 MAE 领先 A。

## 5. Park v1 → v2 的 reconciliation（这次 sprint 最重要的 framing 更新）

Proposal v2 引用了 "85%" 这个 headline 数字。我去重读 Park PDF 原文后发现：

- **arXiv v1**（最初版本，*Generative Agent Simulations of 1,000 People*）报告的 normalized-accuracy headline 是 **~0.85**，对应 interview-only 在 GSS 上的表现。这是 proposal 引用的来源。
- **arXiv v2**（当前 live 版本，重新命名为 *LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals*）重组了 condition，给出下面这套按 outcome 分类的细分。

两个版本在同一个 arXiv ID，v2 是当前规范引用。

**Park v2 核心数字（占 2 周自重测一致率的百分比，GSS 态度题）：**

| 构建 condition | GSS 准确率 |
|---|---|
| 只人口统计 | 74% |
| 只 interview | 83% |
| 只 surveys | 82% |
| Interview + surveys 综合 | 86% |

**关键 caveat —— "surveys ≈ interview" 只在 GSS 上成立。** v2 还报告了按 outcome 维度的细分：

| Outcome | Interview | Surveys-only | Gap |
|---|---|---|---|
| GSS 态度（normalized accuracy）| 0.83 | 0.82 | 几乎打平 |
| BFI-44 人格（normalized correlation）| 0.80 | 0.65 | surveys 落后 0.15 |
| 行为经济学游戏（normalized correlation）| 0.66 | 0.38 | surveys 落后 0.28 |

**对 thesis 的含义**：真正有意义的研究问题不是 *"survey 能不能取代 interview？"*（答：取决于你预测什么），而是 ***"哪类 survey-collectible 的 feature 能在哪类 outcome 上补多少 gap？"*** Interview→surveys 的差距在态度题上 ≈ 0，在人格题上是 0.15，在行为博弈题上是 0.28——**这个 pattern 本身就是 outcome-stratified feature-importance 分析的研究动机。这正是 Park 没做的分析。**

## 6. 两阶段 thesis 计划

Thesis 问题是二维的（feature 类别 × outcome 维度）。矩阵不同的 cell 需要不同的方法。两阶段计划：

### Phase 1 —— GSS 公开数据 feature-importance 分析（~1-4 周，~$300-500 API）
完整设计：[`gss_phase1_design.md`](gss_phase1_design.md)

- **数据来源**：GSS Three-Wave Panel 2010-2014（NORC），N≈1,500 个跨 wave 同人受访者。公开、免费、无招募摩擦。
- **方法**：Park 的 persona-in-context，但输入是 wave-1 题项，held-out outcome 是 wave-3 题项。同人 wave-1↔wave-3 的一致率提供 **test-retest baseline**——首次能给出**直接可与 Park 0.82-0.83 同框比较的 normalized accuracy**。
- **覆盖**：仅 GSS 态度行（Park 矩阵里 surveys ≈ interview 的那一行）。
- **LOO ablation**：每人 5 个 condition（full + 4 个 drop，每次去掉一个 feature 类别）。Bootstrap 95% CI。

### Phase 2 —— Interview-decomposed feature-importance study（~7-9 周，~$1,500-1,750）
完整设计：[`thesis_phase2_design.md`](thesis_phase2_design.md)

- **招募**：N=20-30 panel 受访者，**通过 Prolific**（Cookiy 的 15 分钟上限不兼容这个设计；Prolific 支持跨 wave 2 周后再次邀约）。
- **Wave 1 —— 30-45 分钟模块化长访谈**：AVP 风格，但主持人 script **结构化为 4 个模块，每个模块 1:1 对应一个 feature 类别**：
  - M1 —— 生活基础（demographic）
  - M2 —— 日常行为（behavioral）
  - M3 —— 内在自我（psychological）
  - M4 —— 价值观与态度（attitudinal）
- **主持人**：基于 OpenAI Realtime API 自托管的 AI agent（替代 pilot 用的 Cookiy moderator 进入正式生产）。这套部署 recipe 本身也是方法学贡献。
- **2 周间隔**后做 Wave 2（Park 的 protocol；解决 pilot 的 in-session priming 问题）。
- **Wave 2 —— outcome battery（25 分钟）**：BFI-44 + 5 道行为博弈 survey vignette + 15 道 GSS 态度题。
- **Transcript 拆分**：按模块边界剪，然后用 LLM 辅助重新分配跨模块片段。10% 样本人工编码做验证。
- **LOO ablation 在 *interview 内容层面* 操作**（去掉 M1 / M2 / M3 / M4）。**直接把 Park 的"interview-only" condition 拆解为 pre-registered 内容 bin。**
- **覆盖**：BFI 行 + games 行 + GSS 行。Park 找到 interview-vs-surveys gap 最大的两行。

### 综合 thesis 输出

完整 **4（feature 类别）× 3（outcome 维度）feature-importance 矩阵**：

|  | BFI MAE Δ | Games MAE Δ | GSS MAE Δ |
|---|---|---|---|
| 去掉 demographic | ?? (Phase 2) | ?? (Phase 2) | ?? (Phase 1 + Phase 2) |
| 去掉 behavioral | ?? (Phase 2) | ?? (Phase 2) | ?? (Phase 1 + Phase 2) |
| 去掉 psychological | ?? (Phase 2) | ?? (Phase 2) | ?? (Phase 1 + Phase 2) |
| 去掉 attitudinal | ?? (Phase 2) | ?? (Phase 2) | ?? (Phase 1 + Phase 2) |

这张矩阵就是 thesis 的核心 artifact——Park v2 暗示了它，但没有产出它。

### 战略逻辑

- **Phase 1 便宜，在一行上给出高 N 答案。** 在 GSS 态度上给出有 confidence interval 的 feature importance 排名；首次实现 normalized accuracy 直接对标 Park 0.82-0.83。
- **Phase 2 贵一些，但答的是 gap 真正存在的两行。** 小 N（20-30）合理，因为：(a) Park 的效应量大（0.15, 0.28）；(b) BFI 题量多（每人 44 道）；(c) Phase 2 相对 Phase 1 是 *confirmatory*，不是 exploratory。
- **两阶段组合**起来在一学期内产出完整矩阵，总预算 ~$2,000。
- 每阶段启动前 **OSF 预注册**。

## 7. 待解决的方法学问题

1. **In-session 测试 priming（pilot 局限）**——Pilot 测试跟访谈在同一 session。已通过 leakage filter 文档化和审计，但 Phase 2 的 2 周间隔才是真正的解决。Pilot writeup 的 leakage-filtered 分析是不是足够的辩护，还是需要在 pilot 阶段就重新采集？
2. **低 N 下 LOO 排序不稳定**——Pilot 在 temp 0.7 跑两次，"去掉后伤害最大"的类别会变。LOO effects 的 confidence interval 估计需要多 seed run + N≥30；pilot 只能给方向。
3. **Test-retest baseline**——Park 报的是占自重测一致率的百分比。我们没有。Phase 1 从 GSS panel 结构里 recover；Phase 2 没有。可接受，还是给 Phase 2 加一个 within-person retest 子研究？
4. **AI moderator paraphrase variance**——Cookiy moderator 会改写测试题。Pilot 的 smart parser 吸收了；Phase 2 自托管 moderator 给我们更紧的控制。规模化下可接受 noise，还是真问题？
5. **BFI-10 → BFI-44 升级**——Pilot 用 BFI-10 是因为时间紧。正式研究（尤其 Phase 2）需要 BFI-44 才能让 trait-level 评分有统计意义。
6. **行为博弈的 survey vignette 化**——Phase 2 用 survey-vignette 版本的 dictator/ultimatum/trust/public-goods/donation 游戏，跟 Park 真钱版游戏不同。可接受 proxy 还是方法学问题？
7. **Phase 2 interview 模块结构**——4 模块（1:1 对应 feature 类别）granularity 是否合适？还是该用 SCOPE 的 8-facet 社会心理 taxonomy（Bao et al. 2026）？

## 8. 明天希望讨论的问题

五个具体决策：

1. **确认或重新框定 thesis 问题**——基于 Park v2 的 outcome-stratified findings。
2. **Endorse 两阶段计划**（Phase 1 GSS 公开数据 + Phase 2 interview-decomposed Prolific 研究）vs. 替代方向。
3. **Endorse Phase 2 的平台 pivot**——Cookiy → Prolific + OpenAI Realtime API 自托管 moderator。需要因为 Cookiy 的 15 分钟上限阻断了模块化长访谈设计。
4. **确认 4-bin granularity** 用于 feature taxonomy（或主张 SCOPE 风格的更细分类）。
5. **预注册承诺**——同意 Phase 1 启动前在 OSF 做 pre-registration。

除了这五项，我也想听您对一件事的看法：pilot 的 leakage-audit 辩护对 3-5 页 pilot writeup 是不是足够，还是要在 pilot 阶段就用 2 周间隔重新采集后再 scaling？

---

*相关文档（在 `~/Documents/GSBGEN390/`）：*
- [`gss_phase1_design.md`](gss_phase1_design.md) —— Phase 1 独立提案
- [`thesis_phase2_design.md`](thesis_phase2_design.md) —— Phase 2 独立提案
- [`progress_report.md`](progress_report.md) —— 完整 sprint 叙事
- [`STATUS.md`](STATUS.md) —— 当前状态
- [`replication_scoping.md`](replication_scoping.md) —— pilot 设计 rationale
- [`FUTURE_DESIGN.md`](FUTURE_DESIGN.md) —— 完整讨论 agenda
- [`LIT_REVIEW.md`](LIT_REVIEW.md) —— 文献综述
- 在线 dashboard：`https://joyceqx.github.io/gsbgen390-persona-pipeline/`

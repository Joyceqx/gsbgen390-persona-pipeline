# GSBGEN390 项目综合文档 / Project Synthesis Document

**作者 / Author**: Joyce Yu
**指导教师 / Advisor**: Prof. Mohsen Bayati (Stanford GSB)
**课程 / Course**: GSBGEN390 thesis-track research, Stanford GSB, Spring 2026
**文档生成日期 / Generated**: 2026-05-08, revised 2026-05-09 (lean-design lock)
**文档定位 / Document role**: 烟雾测试前的综合审阅文档；包含全部进展、决策依据、创新论证、可能的质疑、后续方案 / Pre-smoke-test comprehensive review; covers full progress, decision rationale, innovation argument, anticipated criticisms, follow-up plans

> **Revision note (2026-05-09)**: Per Codex's lean-design audit, the Phase 1 design was slimmed from a six-theory horse-race confirmatory framework to a leaner structure with 4-bin LOO as primary, Shapley as robustness, attitudinal-bin Battery LOO as interpretability, and theory framing as Discussion-section interpretation only. RSA / permutation importance / Stage 3 refinement / Friedman's H were all explicitly deferred to future work. See `gss_phase1_design.md` §13 + `theory_interpretation_guide.md` for the live spec.
>
> **Further revision 2026-05-09 evening**: Battery LOO promoted from "conditional secondary, attitudinal-only" to **"unconditional co-primary across all 4 bins"** with nested Holm-Bonferroni per bin. `gss_battery_map.json` expanded v0.1 → v0.2: 15 batteries (attitudinal only) → 34 batteries (D=7 / B=10 / P=2 / A=15). Phase 1 now has **two co-primary findings**: broad (4-bin LOO) + mechanistic (34-battery LOO). See `gss_phase1_design.md` §8.8 + §13.2 for the live spec.
>
> **Comprehensive cleanup 2026-05-09 night**: 16-item Codex re-audit absorbed. Adds joint-34 Holm sensitivity layer for cross-bin claims; practical-effect-size thresholds (small <0.02 / modest 0.02-0.05 / substantive ≥0.05); explicit hierarchical justification §13.0 (4-bin and Battery LOO answer DIFFERENT LEVELS of the same attribution-question family, not unrelated multiplicity-inflating tests); Battery LOO estimand caveat (predictive dependence under fixed prompt-construction procedure, NOT causal importance); R2 framed as rhetorical comparator NOT causal partition; honest impact framing §1.0 (forbidden language list); OSF lock checklist §9e + readiness gate §9f; operational-risk note about accidental sensitivity-pass on all 4 cheap models (§9g). Implementation status corrected: base pipeline tested, Battery LOO + Shapley *specified but not implemented*. See `gss_phase1_design.md` §1.0 / §8.8 / §8.9 / §13.0 / §13.2 / §9e-g for the revised spec.

---

# 第一部分（中文）

## 0. 执行摘要

本项目研究 **LLM persona synthesis 的特征价值归因问题**——当我们让大语言模型假装是某个具体的人去做预测时，给它哪类输入信息（人口学 / 行为 / 心理 / 态度）最有效？这是 LLM persona simulation 这个 research area 的一个核心方法学问题，但目前**没有任何论文做过大-N 的系统归因**。

Phase 1 在**态度预测**这一 outcome 维度上回答这个问题，用 GSS 2024 cross-section（N≈1,500），**两个 co-primary 分析**：(1) 4-bin LOO ablation（broad finding：哪类 feature 重要）；(2) **34-battery LOO across all 4 bins** with nested Holm per-bin（mechanistic finding：每 bin 内具体哪些 cluster 重要；2026-05-09 evening 从 conditional secondary 升级为 co-primary）。Bin-level Shapley 16-condition 作 4-bin robustness。多模型 panel（4 个便宜 OpenRouter 模型 + GPT-4o anchor）控制 model-specific bias。R1 (battery exclusion) + R2 (regression baseline partition) 作泄漏防御和 auto-correlation 分割。Phase 2 扩展到**人格**（BFI-44）+ **行为博弈**两个 outcome 维度，用定向 Cookiy 收集 + 2-周复测 baseline。

Park et al. 2024（"Generative Agent Simulations of 1,000 People"）是当前 area 内被引最多的 prior work——本项目以其作为 cross-paper benchmarking 的 anchor（GPT-4o subset 上 N=100 的 per-item raw accuracy 直接对照 Park v2 SI Table），但研究问题独立成立，不依赖 Park 的具体框架。

整个 Phase 1 设计经过 **3 轮独立 Codex 审计 + 1 轮研究层 Codex 审计**，共修复 27 项发现。当前代码库通过 `validate_taxonomy.py`（10 个检查项）+ 5 个 AUDIT 智能测试 + §12.2 选择器 5 分支测试 + R2 回归基线 self-test，全部绿灯。OSF 预注册可在 N=10 烟雾测试通过后立即起草。

## 1. 研究问题与立场

### 1.1 核心研究问题

**在 LLM persona synthesis 中，4 类调研可采集的特征（人口学 / 行为 / 心理 / 态度）中，哪一类对人格预测准确度的贡献最大？这种贡献又如何随 outcome 维度（态度 / 人格 / 行为）变化？**

LLM persona synthesis 已经被广泛用于 synthetic survey panels (Argyle 2023, Aher 2023, Bisbee 2024)、agent-based simulation (Park 2023, 2024)、商用合成 panel (Aaru, Voicepanel, Synthetic Users)、in-silico RCT 预测 (Hewitt 2024, Manning et al. 2024) 等场景。但**当前没有任何论文做过大-N 的、leakage-clean 的、多模型 robust 的特征价值归因**。本项目填这个 area-level methodological gap。

Phase 1 在 **态度预测**这一 outcome 维度上回答这个问题（最便宜——GSS 公共数据免费、N 上千）。Phase 2 扩展到**人格**（BFI-44）+ **行为博弈**两个 outcome 维度，用 Cookiy 定向收集 + 2-周复测 baseline。

### 1.2 研究估计量（estimand）

> Phase 1 估计的是 **GSS 2024 单波次预测**：从同波次 GSS 特征变量预测 12 个留出 `primary_eval` 题目（外加 ~118 个 sensitivity_eval 题目用作 cross-paper benchmarking），按 4 个预先注册的特征类别贡献分解。

**它显式不是**：
- 复测预测（GSS 2024 没有 recontact baseline）
- 跨波次预测（不用 panel 结构）
- 归一化人格保真度（不除以 test-retest 分母）
- 关于"人类模拟能力"的一般性主张

它**是**：在单波次 GSS 态度预测内部，对 4 个特征类别贡献做的归因分析。

### 1.3 Park v2 作 benchmarking anchor（不是研究框架）

Park et al. 2024（"Generative Agent Simulations of 1,000 People"，arXiv:2411.10109 v2）是 LLM persona synthesis area 当前被引最多的 prior work。本项目以其作为 **cross-paper benchmarking anchor**：在 N=100 的 GPT-4o anchor 子集上，per-item raw accuracy 直接对照 Park v2 SI Table 3，使我们的 GSS-attitude prediction 结果可与现有文献基准互校。

Park 的 outcome-stratified observation（surveys ≈ interviews on GSS attitudes 0.82 vs 0.83；surveys lag interviews by 0.15 on BFI personality, 0.28 on behavioral games）是本项目的**经验先验之一**——它提示不同 outcome 维度可能需要不同 input feature mixture，但本项目的 feature-importance 估计**不依赖**这个先验是否准确。

**关键 framing 声明**：本项目的研究问题（"feature attribution for LLM persona synthesis"）独立于 Park 而存在；Park 是 area 内的重要 prior work，不是本项目的定义框架。本项目 Phase 2 + 后续工作可能扩展到 Park 没覆盖的 outcome 维度（例如开放式回答、多轮决策、long-term behavior）。

## 2. 项目阶段全图

| 阶段 | 状态 | 描述 |
|---|---|---|
| **Pilot** | ✅ 已完成 (2026-04-30) | N=2 访谈 + N=1 调查（Cookiy → GPT-4o → eval）。包含人工泄漏审计 + LOO ablation。**仅作可行性演示，不作统计推断**。 |
| **Phase 1** | 🟢 流水线已建好；待 OpenRouter API key | GSS 2024 cross-section, N≈1,500，单波次快照预测。4-bin LOO 主分析；~118 个 Park-comparable items 作 sensitivity。Phase 1a (N=100) 多模型便宜 panel → §12.2 quality-primary 单模型选择 → Phase 1b (N=1500) + GPT-4o anchor on N=100。预算 ~$215。OSF 预注册必须在 1a 跑之前完成。 |
| **Phase 2** | 📐 已设计，未启动 | Prolific N=20-30，30-45 分钟模块化 AVP 风格访谈（4 模块 ↔ 4 特征类别），2-周间隔的输出 battery（BFI-44 + 行为博弈 + GSS）。访谈内容层面 LOO 直接分解 Park 的 interview-only 条件。预算 ~$1,500-1,750。 |

**复合论文产出**：填好 4×3 矩阵，单学期、~$2,000——这是当前任何已发表论文都没有提供的产物。

## 3. Phase 1 设计：从决策到实现

### 3.1 数据源

**GSS 2024 cross-section**：3,309 受访者 × 973 个独立变量。从 GSS Data Explorer 三批次定宽提取，由 `gss_loader.py` 合并。**单波次快照**——不用早期波次做预测或归一化。

### 3.2 锁定的 4-bin 特征分类（v0.3）

经 AUDIT-A 概念修正（HOMOSEX/XMARSEX/GRASS 从 behavioral 重新归到 attitudinal；ETHNIC 从 behavioral 归到 demographic）后，最终 140 个变量分布：

| Bin | 变量数 | 例 |
|---|---|---|
| Demographic | 24 | AGE, SEX, RACE, EDUC, INCOME16 |
| Behavioral | 25 | ATTEND, PRAY, NEWS, VOTE16, OWNGUN |
| Psychological | 8 | HAPPY, HEALTH, FAIR, HELPFUL, TRUST |
| Attitudinal | 83 | 堕胎 / 信任机构 / 国家优先 / 性别角色 / 公民自由 / 道德 / 经济帮扶 / 宗教 / ... |

`primary_eval` = 12 题（每个构念家族选一题，最小化族内自相关）；`sensitivity_eval` = 118 题（Park v2 GSS list 减去 2024 已退役/改名的 15 题）。validator 强制 `primary_eval ∩ feature_bins = ∅`。

### 3.3 多模型 panel（locked 2026-05-05；调整 2026-05-06）

GPT-4o-only 在 N=1500 要 ~$900，超预算。重设计：

| 角色 | 模型 | 预算 |
|---|---|---|
| Phase 1a 便宜 panel + anchor (N=100) | Qwen-2.5-72B + DeepSeek-V3.1 + MiniMax-M1 + Kimi K2 + GPT-4o anchor | ~$65 |
| Phase 1b 单 quality-selected 模型 (N=1500, n=1) | 由 §12.2 quality-primary 规则选 | ~$95 |
| Phase 1b GPT-4o anchor (N=100 子集, n=2) | GPT-4o | ~$50 |
| **Phase 1 合计** | | **~$215** |

**多样性范围的诚实声明**：4 个便宜模型都是中国训练的（Alibaba / DeepSeek / MiniMax / Moonshot）——多样性是真实的（4 支团队 + 4 种 RLHF 哲学），但**不是"西方 vs 东方训练数据稳健性"**。GPT-4o anchor 提供唯一的西方训练参考。任何"跨 LLM 家族"声明在论文里必须**被严格限制为 N=100 panel 比较**，**不能**应用到 N=1500 headline。

### 3.4 §12.2 模型选择规则（locked 2026-05-08，quality-primary）

经过一日的反思（见下文 §4.3 决策依据），从原 cost-primary 规则**翻转为 quality-primary**：

```
primary_score(model) = respondent-macro Likert MAE on 1a primary_eval (full only)
choose argmin among DQ-passers
```

**预注册护栏**：

1. **DQ-1 解析失败上限**：`parse_failure_rate > 30%` 直接淘汰。
2. **DQ-3 模式坍缩护栏（per-item 相对阈值，2026-05-08 修订）**：每道 primary_eval 题，模型输出方差必须满足 `var(model) ≥ 0.30 × var(human_2024)`。模型若 >50% 的题失败则淘汰。锁定的人类方差参考保存在 `outputs/primary_eval_human_variance_2024.json`。这条规则替代了原绝对阈值 0.5——后者在偏态题（FEPOL, GUNLAW）上过松，在 PARTYID 上过紧。
3. **Cost tie-break**：质量在 5% 之内时按 `cost_per_call × (1 + parse_fail)` 选最便宜。
4. **Qwen 确定性 fallback**：所有模型 DQ 失败或在 quality+cost 都打平时强制用 Qwen-2.5-72B-Instruct。

**论文一句话表达**：
> "We selected the lowest-MAE Phase 1a candidate among models passing pre-registered parse-failure (≤30%) and per-item relative-variance (≥30% of human variance) gates; cost served as a within-5% tie-break, with Qwen-2.5-72B-Instruct as the named fallback."

### 3.5 泄漏防御四层（R1 + R2 添加 2026-05-08）

经第三方研究层审计 §3.1 提出，并经 Park v2 PDF p.10/37/39 引用核实：

1. **Layer 1（直接，已防）**：feature bins ⊥ primary_eval（validator 强制）；sensitivity 单题排除。
2. **Layer 2（同义，GSS 内部不存在）**：Park v2 SI §9 已实证 GSS-内部无同义对。
3. **Layer 3 — R1（battery 级结构性排除，新增）**：预测任一 battery 内的 primary_eval 题时，整个 battery 从 persona prompt 移除。镜像 Park BFI 的 whole-trait-block hold-out。Battery map 锁定在 `gss_battery_map.json`，包含 15 个 batteries + 9 个单题。
4. **Layer 4 — R2（回归基线分割，新增）**：与 LLM panel 平行，跑非-LLM 回归（Ridge for Likert / multinomial Logistic for binary，5-fold respondent-level CV，同样应用 R1 battery exclusion）。Per-item MAE 是任何特征-到-题预测器能榨出的 auto-correlation 上限。

**Headline 分割等式**：
```
LLM-panel MAE on item X = (regression MAE on X) + (LLM gain over regression)
                          = pure auto-correlation + persona reasoning
```

**为什么不做 R3**：R3 全局把所有 batteries 从 attitudinal bin 移除，得到一个永久瘦身的 bin。这会人为压低 attitudinal LOO ΔMAE 而无法分清是"battery 信息少了"还是"bin 容量整体小了"。R1 已经在每道题做精确的 battery 排除，加上 R2 的 partition test 足够。

**Park 标定的引用证据（已核实）**：
- "27 GSS items removed via cross-instrument synonym audit" — Park v2 PDF p.10 原文：*"The process flagged 27 GSS items, which we removed..."*
- "GSS-internal synonymy = none" — Park v2 PDF p.10 原文：*"We applied the same procedure to identify questions in the GSS that are synonymous to other GSS questions and **found none**."*
- "BFI uses whole-trait-block hold-out, GSS uses single-item hold-out as main + whole-module as SI robustness" — Park v2 PDF p.37 原文：*"For the Big-5 we always hold-out the whole block...First, we remove only the outcome question we predict...Second, we hold-out the whole GSS module..."*
- "Survey agents 0.82 → 0.77 ≈ 0.05 inflation under whole-module hold-out" — Park v2 PDF p.39: *"normalized accuracy on the GSS of 0.82 (std = 0.18)" / "average normalized accuracy of 0.77 (std = 0.12)"*

第三方审计的 std=0.13 引用是错的（应是 0.18 vs 0.12），但核心 ~0.05 inflation 论证站得住——**所以 R1 + R2 的 Park-precedent 论证可信**。

### 3.6 多重比较（FWER 控制；2026-05-09 lean-design + 同日傍晚 Battery LOO 升 co-primary）

Phase 1 当前的 5 个独立 Holm families（**nested**, 不是 joint）：

- **4-bin LOO primary family** (4 ΔMAE tests) — Holm at α=0.05 within family.
- **Battery LOO co-primary, nested per bin（2026-05-09 evening 升级）**：
  - Demographic battery family (n=7): smallest p < α/7 = 0.0071
  - Behavioral battery family (n=10): smallest p < α/10 = 0.0050
  - Psychological battery family (n=2): smallest p < α/2 = 0.025
  - Attitudinal battery family (n=15): smallest p < α/15 = 0.0033
- **Bin-level Shapley decomposition** —— 4-bin LOO 同一估计量的 robustness re-aggregation；不需要单独 Holm 校正（共享 4-bin family）。

**为什么 nested 而不是 joint**：bin 是 pre-registered 的有意义边界；joint Holm 在 n=34 上会让 psychological 的 2-battery family 必须 clear α/34=0.0015——不切实际，会让一个预注册 arm 失声。Nested 在每 bin 内部独立校正，每 bin 的 within-bin 归因可以独立成立，不被其他 bin 的 multiplicity 拖累。

**已撤掉**（2026-05-09 lean-design lock）：theory-bin LOO 不再是 confirmatory family。理论解释只进 Discussion 章节，不驱动任何 primary claim。详见 §3.8 + `theory_interpretation_guide.md`。

### 3.7 §11.1 论文措辞模板（强制）

为防止过度声明，下表是任何 Phase 1 abstract / headline figure / dashboard 必须遵守的:

| 约束 | 必须用 | 禁用 |
|---|---|---|
| "Persona fidelity" 限定 | "within-wave attitudinal prediction" | 裸 "persona fidelity" |
| Cross-model 范围 | "across four China-trained instruction-tuned models in a 100-respondent comparison" | 裸 "across LLM families" |
| Headline-N 模型身份 | "the {selected_model} reported under the §12.2 quality-primary rule, N=1500" | "the cheap panel" |
| Park 比较锚 | "the GPT-4o anchor on the N=100 subset, with single-item hold-out matching Park v2 SI §6" | "matches Park's 82%" |
| Auto-correlation 框架 | "after R1 battery-level exclusion and R2 regression-baseline partition" | 裸 "after leakage hygiene" |
| Test-retest 主张 | （什么都不说） | "normalized accuracy" / "fidelity" |

### 3.8 Secondary 分析（lean 结构，2026-05-09 锁）

设计哲学：论文有**一个**清晰的 primary contribution——*哪些 survey-collectible feature categories 真正改善 LLM 人格预测 GSS 态度结果?*——由 4-bin LOO 回答。两个 secondary 分析延伸该贡献；理论解释进 Discussion section，**不**驱动任何 primary claim。

#### 3.8.1 Bin-level Shapley decomposition（secondary — robustness）

- **目的**：检查 4-bin LOO ranking 是否 robust to bin-bin interactions（LOO 是 marginal-effects estimator，捕捉不到 interactions）。
- **算法**：枚举所有 2⁴ = 16 个 conditions（每 bin include/exclude）。Shapley value for bin B = average of `MAE(coalition without B) - MAE(coalition ∪ {B})` over all 8 coalitions not containing B。
- **何时跑**：Phase 1a (N=100)，每个 cheap-panel 模型一次；可选在 Phase 1b 选定模型上重跑。
- **Reporting role**：与 4-bin LOO 同一估计量的 robustness re-aggregation；不是单独的 confirmatory family；不需独立 Holm 校正。
- **明确禁用**：custom variance-share 量绝对**不**叫 "Friedman's H"——重命名为 `interaction_variance_share`，因为 Friedman & Popescu (2008) 的 H-statistic 有特定的 partial-dependence-on-tree-models 定义，我们没实现那个。

#### 3.8.2 Battery LOO 跨全 4 bins（**co-primary**，2026-05-09 evening 从 conditional secondary 升级）

- **目的**：mechanistic 归因——每 bin 内部具体哪些 construct-level cluster 驱动 LLM persona prediction 的信号。与 4-bin LOO（broad）共同构成 paper 两个 co-primary findings。
- **范围**：全部 34 个 batteries 跨 4 个 bins（per `gss_battery_map.json` v0.2: 7 demographic + 10 behavioral + 2 psychological + 15 attitudinal）。Singletons 不进 LOO 测试（per §3.8.4 deferred list）。
- **算法**：对每个 battery B，把整个 battery 从 persona prompt 移除（外加 R1 per-item battery exclusion 已应用——两者独立操作），re-run prediction on all 12 primary_eval items，compute respondent-macro Likert ΔMAE vs FULL。Bootstrap CI at respondent level (B=1000, seed=42)。
- **Multiplicity**：**Nested Holm-Bonferroni** within each bin's battery family（NOT joint）：
  - Demographic family (n=7): smallest p < α/7 = 0.0071
  - Behavioral family (n=10): smallest p < α/10 = 0.0050
  - Psychological family (n=2): smallest p < α/2 = 0.025
  - Attitudinal family (n=15): smallest p < α/15 = 0.0033
- **为什么 nested 不是 joint**：bin 是 pre-registered 边界；joint Holm 在 n=34 上会让 psychological 2-battery family 必须 clear α/34=0.0015，practically impossible，会 silence 一个预注册 arm。
- **何时跑**：Phase 1c (post Phase 1b headline) 在 §12.2-selected 1b 模型上。增量 ~$50-60（升级前 ~$25-30 是 attitudinal-only 的 conditional 设计）。
- **Reporting role**：**co-primary mechanistic finding**——abstract 与 4-bin LOO 同等显著性。论文 Headline #1 (broad) + Headline #2 (mechanistic) 并列。
- **Anti-overclaim**：battery size 不平衡（2-15 items），ΔMAE 必须与 `n_items_in_battery` + `delta_mae_per_item` 一起报告，让 size-aware 解读成为可能。Cross-bin rank 比较是描述性的（不是 jointly Holm-corrected）。

#### 3.8.3 Theory interpretation（Discussion 章节）

4-bin taxonomy 是 atheoretical 的——一种排序惯例，不源自任何认知理论。primary 结果出来后，论文 Discussion 章节会把实证 pattern 在 6 个候选认知/社会学框架下做**定性解读**（见 `theory_interpretation_guide.md`）。

**关键 preregistration commitment**：理论解释是 **secondary and explanatory**。primary findings (4-bin LOO ranking, Shapley decomposition, attitudinal battery LOO) **不依赖** 哪个理论最对齐。具体：

- Abstract 用 atheoretical engineering 措辞（如 *"attitudinal features dominate, with within-bin contribution concentrated in [batteries]"*）。
- Theory framing 进入 Discussion 一个明确标为 *interpretive secondary analysis* 的小节。
- **不**做 horse race 让某个 theory "win"。
- **不**在 abstract 写 "LLM persona representation aligns with [Theory X]"。
- **Null 或 mixed 理论对齐会诚实报告**——如果没有任何框架 cleanly 解释实证 pattern，Discussion 直说，不扭曲。

#### 3.8.4 已 defer 到 future work（2026-05-09 lean-design lock）

以下分析**显式撤出** Phase 1 lean 范围，可能作为 future work 列入 Discussion 末尾，但**不**进 OSF preregistration：

- Theory-bin LOO 作 confirmatory family（需要 `gss_theory_taxonomy.json` lock + OSF amendment）
- Representational Similarity Analysis (RSA)（理论派生相似度矩阵 vs LLM-output 相似度）
- Permutation importance theory adjudication（per-(item, var) importance 用于 rank 理论）
- Stage 3 refinement experiments（theory-organized prompts; counterfactual perturbation; theory-derived feature subsets）
- Six-theory horse race with hard numeric thresholds
- Friedman & Popescu (2008) H-statistic（proper 实现需要 partial-dependence machinery；lean 设计用 `interaction_variance_share` 替代）

## 4. 关键决策的依据档案

按时间顺序，**每个**重要决策都附依据。这是 OSF "decisions locked, when, against what evidence" 日志的来源。

### 4.1 Phase split: GSS-first → 定向 Cookiy（2026-05-02）

**决策**：先做 GSS Phase 1，再做 Cookiy Phase 2。

**依据**：
- Cookiy 单受访者成本 ~$11，N=1500 不可行（>$16k）
- GSS 2024 是免费、已收集、N=3309 的现成数据；ROI 是 Cookiy 的 100×
- BFI / 行为博弈 GSS 没测——必然要做 Cookiy 才能填补 4×3 矩阵
- Bayati 在 2026-05-02 的会议上明确背书 phase split

**牺牲**：GSS 没有 BFI、没有行为博弈、没有访谈、没有 2-周 recontact baseline。这意味着 Phase 1 的 estimand 与 Park 不同（同波次 vs 跨波次）；§11 显式 disclaim。

### 4.2 单波次快照而非跨波次（2026-05-05）

**决策**：用 GSS 2024 单波次预测，不用 wave-1 → wave-3 的 panel 结构。

**考虑过的反方**：跨波次有"持久性"信号，更接近 Park。

**反方失败原因**：
- GSS panel 设计是 3-wave（同一受访者间隔约 2 年回测），但题目部分重叠 — 跨波次预测会引入直接的题目重复泄漏。
- 2 年间真实人格本身可能改变；预测 wave-3 的 ABANY 用 wave-1 的 ABANY，是在测"持久性 + 模型预测"的混合，无法分清。
- 单波次更干净：明确定义为"同波次特征 → 同波次留出题"，与 Park 不同但内部一致。

**牺牲**：失去 test-retest baseline；不能算 Park-style normalized accuracy。在 §11 / §11.1 严格限定 raw-only。

### 4.3 §12.2 cost-primary → quality-primary（2026-05-06）

**决策**：从 `score = cost × (1 + parse_fail)` 翻成 `score = MAE`，cost 仅作 5% tie-break。

**依据**：
- 4 个便宜模型 cost 跨度只有 ~2×，N=1500 总成本差距 $50-80
- Likert MAE 跨度可能 0.85 vs 1.40——量级大得多
- 论文 headline 指标是 MAE；选择标准应当与 headline 指标对齐
- cost-primary 听起来"保守"，但选模型的内在不一致会被审稿人立刻看穿

**保留 cost-primary 作 history note**，明示反转的逻辑。

### 4.4 DQ-3 绝对阈值 → per-item 相对阈值（2026-05-08）

**决策**：从 `mean(per_item_var) < 0.5 → DQ` 改为 `var(model_i) / var(human_i) < 0.30 for >50% items → DQ`。

**依据**（量化）：人类方差跨度 28×：
- FEPOL (var=0.15)：偏 82%/18%——绝对阈值 0.5 等于"必须比人类离散 3×"
- PARTYID (var=4.24)：8-point 谱——绝对阈值 0.5 是 ~12% 人类方差，几乎任何模型都过
- 30% 相对阈值：FEPOL 阈值 0.045（catches 单 mode），PARTYID 阈值 1.27（catches 单 mode），二者都 calibrated

锁定参考保存在 `outputs/primary_eval_human_variance_2024.json`，OSF 预注册一并锁。

### 4.5 R1 battery boundaries（2026-05-08）

**决策（v0.1, 2026-05-08）**：15 batteries + 9 singletons（attitudinal-only 范围），civil_liberties 按 target group 分 3 个（atheists / racists / communists），不合成 1 个。

**后续扩展（v0.2, 2026-05-09 evening）**：扩展到全 4 bins，34 batteries + 17 singletons（demographic 7 + behavioral 10 + psychological 2 + attitudinal 15 不变），用于支持 co-primary Battery LOO。详见 §3.6 + §3.8.2。

**依据**：
- 知道 R 对种族主义者的态度，对预测堕胎几乎没帮助；但对种族主义者 vs 共产主义者 vs 无神论者三类内部强相关
- Park BFI 不按"全部人格特质"做一个 battery；按 trait（neuroticism / openness 各自一个 block）分组——battery 应当与论文 LOO 的"族内"对应
- `morality_lifestyle` 之前太宽，重新分成 `sexual_morality` / `moral_legalization` / `adolescent_sex_policy`

完整 mapping 在 `gss_battery_map.json`。

### 4.6 R3 不做（2026-05-08）

**决策**：R1 + R2 做，R3（全 attitudinal bin Park-strict 重新定义）不做。

**依据**：
- R3 会同时压低所有 condition 的 accuracy，让 LOO ranking 不可解释——分不清"battery 信息丢了"vs"bin 容量小了"
- R1 在每题精度做精确排除，比 R3 更精细
- R2 直接 partition inflation，比 R3 的"bracket 它"前进一步
- Park 自己也没做 R3 风格的预先全 block 删除

### 4.7 Theory-bin via OSF amendment（2026-05-08）

**决策**：初始 OSF 预注册只锁 4-bin LOO；theory-bin LOO 在 Joyce 文献综述选定理论后通过 amendment 加入。

**依据**：
- 理论尚未选定（Round 1 + Round 2 文献综述中：MFT / Schwartz / Bourdieu / Cultural Theory / Inglehart-Welzel / Big Five 6 个候选）
- 把 theory-bin 跟 4-bin 一起锁是 false locking——本质是说"我们承诺在还没选定的理论上做某种分析"
- amendment 路径完全合规——重要的是任何 theory-bin re-aggregation 都必须在 amendment 后进行

### 4.8 Lean-design lock：撤掉 staged confirmatory discovery（2026-05-09）

**决策**：撤掉 2026-05-09 早晨提出的"staged confirmatory discovery"框架（Stage 1 ML discovery + Stage 2 preregistered theory horse race + Stage 3 refinement），改回 lean 结构：4-bin LOO primary + Shapley robustness + Battery LOO interpretability + theory 仅进 Discussion 解释。

**依据**：
- Codex's lean-design audit (2026-05-09 下午) 指出：横扫 6 理论 + Stage 3 refinement + RSA + permutation importance 会让论文从"clean primary contribution"漂向"tool-stack paper"。
- 论文的核心贡献是"哪类 survey-collectible features 改善 LLM 人格预测"——这是 engineering question，不需要"哪个认知理论 wins"作为 primary 主张支撑它。
- 反 HARKing discipline 不必通过"preregistered horse race"实现——通过"theory 只进 Discussion + null-alignment 诚实报告 + 候选框架 list pre-commit"也能保护，且不引入不必要的 multiplicity 校正负担。
- Saved scope：RSA / permutation importance theory adjudication / Stage 3 refinement / 6-theory horse race / Friedman's H 全部 defer 到 future work。

**保留**：
- 4-bin LOO 作 primary
- Shapley decomposition 作 robustness
- ~~Attitudinal-bin Battery LOO 作 secondary interpretability（trigger 条件：attitudinal 主导）~~ → 2026-05-09 evening 升级为 **34-battery co-primary，unconditional，跨全 4 bins，nested Holm per-bin**（详见 §3.8.2 修订版）
- R1 + R2 leakage hygiene（locked, 不变）
- §11.1 abstract 措辞模板（locked, 不变）
- §12.2 quality-primary 选择规则（locked, 不变）

**撤掉的具体部件**：见 §3.8.4 + `gss_phase1_design.md` §13.4。

**撤掉的 history note**：早晨 v0.1 DRAFT 的 `osf_preregistration_appendix_a_theory_predictions.md` 改名为 `*.SUPERSEDED-2026-05-09.md`。新文件 `theory_interpretation_guide.md` 是当前 live spec。

## 5. 创新与影响

### 5.1 概念贡献

- **第一篇大-N 的 LLM persona synthesis feature attribution**：在 attitude prediction 上 N=1500 的系统归因，回答"persona 输入的哪类信息最有效"——这是 LLM persona simulation area 内的方法学核心问题，但当前没有论文做过这种规模、这种泄漏防御严格度、这种 multi-model robust 的归因。
- **(input feature × outcome dimension) 二维 feature-importance map 的 first instance**：Phase 1 提供 attitude 维度的 4-bin 归因；Phase 2 扩展到 personality + behavior。最终 deliverable 是 (feature × outcome) 二维 map——这个结构是心理学测量传统的自然产物（attitude / personality / behavior 是三个独立测量传统），不依赖任何单一 prior work 的框架。
- **持续 research program 的第一篇**：本项目设定的研究方向（feature attribution for LLM persona synthesis）天然外推到 long-term behavior、cross-cultural validation、多模态 persona、开放式回答等 outcome 维度。Phase 1 + Phase 2 是 program 的前两篇。

### 5.2 方法学贡献（独立成立）

四个可被任何后续 LLM persona synthesis 论文借走的工件，**每个都不依赖 Park 的存在**：

1. **R1 — Battery-level structural exclusion** (`gss_battery_map.json` + `build_persona_prompt(exclude_vars=...)`)：在 LLM persona prompt 中预测某 within-construct cluster 的 item 时，整个 cluster 必须从 prompt 移除。Park v2 在 BFI 上做了 trait-block hold-out 但在 GSS 上是松策略；R1 把更严的 hold-out 标准应用到 GSS（也对应到任何后续基于其它 survey instrument 的 persona 工作）。
2. **R2 — Regression-baseline partition** (`regression_baseline.py`)：与 LLM panel 平行跑非-LLM regression baseline，把 LLM 准确率拆成 (auto-correlation 任何模型都能榨出) + (LLM persona reasoning gain) 两部分。这是**新方法**——prior work 都是 *bracket* inflation 范围；R2 直接 *partition*。
3. **Multi-model cheap-panel + §12.2 quality-primary selection rule + named fallback** (`select_phase1b_model.py`)：给预算受限的研究者一个不靠 GPT-4o 也能做严肃 LLM persona 论文的预算控制 + 模型选择 OSF 模板。Self-test 5 个 branch 全过。
4. **DQ-3 per-item relative variance threshold** (`outputs/primary_eval_human_variance_2024.json`)：mode-collapse 检测的 item-level 相对阈值，比绝对阈值更稳——在偏态 item（如 FEPOL 82/18）和宽分布 item（PARTYID 8-point）上都正确判别。

### 5.3 行业关联

- 商用合成 panel（Aaru / Voicepanel / Synthetic Users）受商业压力都走"more data, more models"工程视角——没人做 careful feature attribution + leakage hygiene。Phase 1 的 R1+R2 + Shapley + Battery LOO 工具链是这个 niche 的清晰公共贡献。
- Stanford spinout Simile 把 LLM persona 流水线产品化；本项目的 (input feature × outcome dimension) 归因 map 是当下最接近"哪些输入对哪些输出有用"的公开 artifact——可被产品化的 persona service 直接借用作 input recommendation。

### 5.4 学术贡献定位

可投：
- *Management Science* methods track（最匹配的 GSB 取向）
- NeurIPS Datasets & Benchmarks（pre-reg + reproducible artifact）
- CSCW / FAccT（persona 审计角度）

不可投：
- 主流 NeurIPS / ICML（不是 algorithmic 创新）
- 顶级 JPSP / 心理学期刊（不是 human-cognition 主张）

## 6. 可能的质疑及应对

### 6.1 "你的 estimand 不是 Park 的 estimand"

**应对**：完全承认。§11 / §11.1 显式禁用 "persona fidelity" 这种含 normalization 暗示的词。abstract 必须用 "within-wave attitudinal prediction"。Park 比较只通过 N=100 GPT-4o anchor + single-item hold-out 做 per-item raw accuracy 对照——明确为 SI / appendix，不进 headline。

### 6.2 "Auto-correlation 让 attitudinal bin 看起来重要"

**应对**：R1 + R2 是直接的方法学防御。
- R1：battery-level 排除，与 Park BFI rule 同构
- R2：regression baseline partition——把 LLM 的"persona reasoning gain"和"任何模型都能榨出的 auto-correlation"分开

具体在 abstract / headline 中报告：
- LLM panel MAE on attitudinal-bin LOO drop = X
- Regression-only MAE on same bin = Y
- LLM persona gain = X − Y

如果 Y/X 接近 1，attitudinal bin 的"贡献"完全是 auto-correlation；如果 Y/X 接近 0，是真正的 persona reasoning。**这是论文的中心实证发现**。

### 6.3 "4 个便宜模型都是中国训练的"

**应对**：§11.1 明示限制 "across LLM families" 仅适用 N=100 1a panel；Phase 1b headline 用 single quality-selected model；GPT-4o anchor (N=100) 提供西方对照。论文若需更强 cross-cultural diversity 主张，sensitivity 中加入 Llama-3.3-70B (Meta) 重跑——但这是后置选项。

### 6.4 "LOO 在不平衡 bins 上是弱归因方法"

**应对**：admitted。lean 设计的两个 secondary 工具直接回应：
- **Bin-level Shapley decomposition (§3.8.1)** —— 16-condition 全枚举，自动捕捉 bin 间 interactions；与 4-bin LOO 对比看 ranking 一致性。Phase 1a 上跑。
- **34-battery LOO across all 4 bins (§3.8.2)** —— **co-primary mechanistic finding**, unconditional, nested Holm per-bin. Phase 1c 上跑。

LOO ΔMAE 是 marginal estimator；Shapley 补 interaction-aware 估计 (4-bin only)；Battery LOO 补 cross-bin within-construct 颗粒度。三者**互补不重叠**：4-bin 答 broad bin-level question；Shapley 答 bin interaction question；Battery LOO 答 mechanistic cluster-level question。其他方法（Bin-size-balanced subsampling / leave-one-in / RSA / sampled Shapley on batteries）defer 到 future work（详见 §3.8.4）。

### 6.5 "DQ-3 阈值是任意选的"

**应对**：30% 不是任意。在 §4.4 决策依据里 quantitative 分析过——人类方差跨度 28×，相对阈值是必须的。30% 相对阈值在 (FEPOL, GUNLAW, ABANY, ..., PARTYID, POLVIEWS) 12 个 items 上一致地区分了 calibrated 模型与 mode-collapsed 模型。alternative X=20% / 50% 在 §4.4 也讨论过。所有依据进 OSF。

### 6.6 "Pre-registration is post-pilot"

**应对**：admitted。OSF 预注册前会附 "decisions locked, when, against what evidence" log（本文档 §4 即模板）。审稿人可以追溯每个决策的时间线和经验依据。

### 6.7 "Phase 2 N=20-30 太少"

**应对**：Phase 2 设计文档承认这个限制。预注册前会跑 Phase-1-empirics-seeded power-calc simulation，预先披露 4×3 矩阵中哪些格在 N=30 下可检测、哪些需要 N≥60。

### 6.8 "Theory-driven LOO 需要选定理论"

**应对**（lean-design 后修订）：lean 设计中 theory 不再是 confirmatory family 的一部分。理论解释**只**进 Discussion section（见 `theory_interpretation_guide.md`），primary findings 不依赖理论对齐。这一修订把 "需要选定理论" 这个反对意见消解为 "discussion 中讨论 6 个候选框架，不必胜出一个"。

### 6.9 "Lean 设计 = 论文太薄"（潜在批评）

**应对**：lean 设计 ≠ 论文薄。两个 co-primary 分析 + Shapley robustness 一起是 4-stage 归因的 well-defined 答案：
- Stage 1（co-primary #1，broad）：哪个 bin 重要（4-bin LOO）
- Stage 2（robustness）：4-bin ranking 是否 robust to interactions（Shapley）
- Stage 3（**co-primary #2，mechanistic**）：每 bin 内具体哪些 batteries 出力（**34-battery LOO 跨全 4 bins, nested Holm per-bin**）
- Stage 4（Discussion）：哪些 framework 在 Discussion 解读这个 pattern（theory_interpretation_guide.md）

加上 R1 + R2 leakage hygiene + §12.2 quality-primary multi-model selection + GPT-4o anchor 的 Park comparability，方法学贡献本身就是论文的一半价值。论文不需要"6-theory horse race"才能 publishable——清晰、可验证、reproducible 的 ablation 比 tool-stack 更可投。

## 7. 后续方案与时间线

### 7.1 Phase 1a 之前必做（~2-3 天）

1. ✅ Joyce 跑 N=10 烟雾测试（需 OpenRouter API key，~$2-3）
2. ✅ Joyce 起草 OSF 预注册（4-bin primary scope；本文档 §3+§4 是模板）
3. ✅ Joyce 与 Bayati 对一次 final design（特别是 §12.2 quality-primary 反转 + R1+R2 新加项）

### 7.2 Phase 1a 之后（~1 周）

4. 跑 §12.2 selector 自动选出 1b model
5. 跑 R2 regression baseline on 1b sample
6. 出 1a multi-model 报告作为 robustness 1a panel

### 7.3 Phase 1b 之后（~2 周）

7. 跑 Phase 1b headline（N=1500）
8. 计算 4-bin LOO ΔMAE + Holm-Bonferroni FWER
9. 计算 LLM-vs-regression partition (R2)
10. 出 sensitivity table（Park v2 ~118-item per-item raw accuracy 对照 GPT-4o anchor）

### 7.4 ~~Theory-bin amendment~~（已撤掉 — lean lock 2026-05-09）

原计划 (§4.7) 是"Joyce 文献综述完成 → 锁 `gss_theory_taxonomy.json` → OSF amendment → theory-bin LOO 作 secondary headline"。**lean-design lock 撤掉了整个这条路径**（§4.8）。理论解释只进 Discussion section，不需要 amendment、不需要 taxonomy 构建、不需要 secondary headline。Joyce 的文献综述继续，但仅作 Discussion 写作输入，不阻塞 OSF 或 Phase 1c。

### 7.5 Phase 2（2026 暑期）

11. 用 Phase 1 经验 seed power calc，预先披露可检测格
12. Cookiy + Prolific 收 N=20-30 with 2-周 recontact
13. 填充 BFI 行 + 行为博弈行
14. 写论文

---

# Part 2 (English)

## 0. Executive Summary

This project investigates **feature attribution for LLM persona synthesis** — when we prompt a language model to respond as a specific human individual for prediction, simulation, or modeling tasks, which input feature categories (demographic, behavioral, psychological, attitudinal) drive prediction quality? This is a core methodological question for LLM persona simulation as a research area, but **no prior published work has performed large-N, leakage-clean, multi-model-robust attribution at scale**.

Phase 1 answers this question for **attitude prediction** using GSS 2024 cross-section (N≈1,500), with **two co-primary analyses**: (1) a 4-bin leave-one-out ablation (broad finding: which feature category contributes most); (2) **a 34-battery LOO across all 4 bins with nested Holm per-bin** (mechanistic finding: which construct-level clusters drive the signal within each bin; promoted from conditional secondary to co-primary on 2026-05-09 evening). A bin-level Shapley 16-condition decomposition serves as 4-bin LOO robustness. A multi-model panel (4 cheap OpenRouter models + GPT-4o anchor) controls for model-specific bias. R1 (battery exclusion) + R2 (regression-baseline partition) provide leakage hygiene and auto-correlation partition. Phase 2 extends to **personality** (BFI-44) + **behavioral economic games** outcome dimensions via targeted Cookiy collection with 2-week recontact baseline.

Park et al. 2024 ("Generative Agent Simulations of 1,000 People") is the most-cited prior work in this area — this project uses Park as a **cross-paper benchmarking anchor** (per-item raw accuracy on N=100 GPT-4o anchor subset compared directly to Park v2 SI Table 3) but the research question stands independently of Park's specific framework.

The Phase 1 design has been hardened by **3 rounds of independent Codex audit + 1 research-layer Codex audit**, fixing 27 distinct findings. The codebase passes `validate_taxonomy.py` (10 checks) + 5 AUDIT smoke tests + the §12.2 selector's 5-branch self-test + the R2 regression-baseline self-test, all green. The OSF pre-registration can be drafted immediately after the N=10 paid smoke test passes.

## 1. Research question + stance

### 1.1 Research question

**In LLM persona synthesis, which of four survey-collectible feature categories (demographic / behavioral / psychological / attitudinal) contributes most to persona prediction accuracy, and how does this contribution vary across outcome dimensions (attitudes / personality / behavior)?**

LLM persona synthesis is increasingly used for synthetic survey panels (Argyle et al. 2023; Aher et al. 2023; Bisbee et al. 2024), agent-based simulation (Park et al. 2023, 2024), commercial synthetic-respondent panels (Aaru, Voicepanel, Synthetic Users), and in-silico RCT prediction (Hewitt et al. 2024; Manning et al. 2024). But **no published work has performed a large-N, leakage-clean, multi-model attribution at the feature-category level**. This project fills that area-level methodological gap.

Phase 1 answers the question for the **attitude** outcome dimension (cheapest — GSS public data is free, N in the thousands). Phase 2 extends to **personality** (BFI-44) + **behavioral economic games** via Cookiy collection + 2-week recontact baseline.

### 1.2 Estimand

> Phase 1 estimates **single-wave GSS 2024 prediction** of held-out items (the 12 in `primary_eval`, plus ~118 sensitivity_eval items used for cross-paper benchmarking) **from same-wave GSS feature variables**, decomposed into the contribution of four pre-registered feature categories.

This is **explicitly NOT**:
- Test-retest prediction (no GSS 2024 recontact baseline)
- Cross-wave prediction (no panel structure used)
- Normalized persona fidelity (no test-retest denominator)
- A general claim about "human simulation ability"

It **is**: feature-category contribution analysis within single-wave GSS-attitudinal-item prediction.

### 1.3 Park v2 as benchmarking anchor (not research framework)

Park et al. 2024 ("Generative Agent Simulations of 1,000 People", arXiv:2411.10109 v2) is the most-cited prior work in LLM persona synthesis. This project uses Park as a **cross-paper benchmarking anchor**: on the N=100 GPT-4o anchor subset, per-item raw accuracy is directly comparable to Park v2 SI Table 3, allowing our GSS-attitude prediction results to be cross-checked against the leading existing benchmark.

Park's outcome-stratified observation (surveys ≈ interviews on GSS attitudes 0.82 vs 0.83; surveys lag interviews by 0.15 on BFI personality, 0.28 on behavioral games) serves as **one of several empirical priors** for this project — it suggests that different outcome dimensions may require different input feature mixtures. But the project's feature-importance estimates **do not depend** on whether this prior is correct.

**Critical framing statement**: This project's research question (*"feature attribution for LLM persona synthesis"*) exists independently of Park; Park is an important prior work, not the project's defining framework. Phase 2 + future extensions may cover outcome dimensions Park did not (e.g., open-ended responses, multi-turn decisions, long-term behavior).

## 2. Phase landscape

| Phase | State | Description |
|---|---|---|
| **Pilot** | ✅ Done (2026-04-30) | N=2 interview + N=1 survey via Cookiy → GPT-4o → eval. Includes manual leakage audit + LOO ablation. **Feasibility demo only, not inference**. |
| **Phase 1** | 🟢 Pipeline built; awaiting OpenRouter key | GSS 2024 cross-section, N≈1,500, single-wave snapshot. 4-bin LOO primary; ~118 Park-comparable items as sensitivity. Phase 1a (N=100) cheap-panel → §12.2 quality-primary single-model selection → Phase 1b (N=1500) + GPT-4o anchor on N=100 subset. ~$215. OSF pre-reg required before 1a fires. |
| **Phase 2** | 📐 Designed, not started | Prolific N=20-30, 30-45 min modular AVP-style interview (4 modules ↔ 4 feature bins), 2-week-separated outcome battery (BFI-44 + behavioral games + GSS). Interview-content-level LOO directly decomposes Park's interview-only condition. ~$1,500-1,750. |

**Composed thesis output**: filled 4×3 matrix in one semester at ~$2,000 — an artifact no published paper currently provides.

## 3. Phase 1 design: from decisions to implementation

### 3.1 Data source

**GSS 2024 cross-section**: 3,309 respondents × 973 unique variables. Extracted in 3 fixed-width batches via GSS Data Explorer; merged by `gss_loader.py`. **Single-wave snapshot only** — no use of earlier GSS waves for prediction or normalization.

### 3.2 Locked 4-bin feature taxonomy (v0.3)

After AUDIT-A conceptual reclassifications (HOMOSEX/XMARSEX/GRASS moved from behavioral to attitudinal; ETHNIC moved from behavioral to demographic), the 140 features distribute:

| Bin | Vars | Examples |
|---|---|---|
| Demographic | 24 | AGE, SEX, RACE, EDUC, INCOME16 |
| Behavioral | 25 | ATTEND, PRAY, NEWS, VOTE16, OWNGUN |
| Psychological | 8 | HAPPY, HEALTH, FAIR, HELPFUL, TRUST |
| Attitudinal | 83 | abortion / institutional confidence / national priorities / gender roles / civil liberties / morality / economic help / religion / ... |

`primary_eval` = 12 items (one per construct family, autocorrelation-minimized within each); `sensitivity_eval` = 118 items (Park v2 GSS list minus 15 retired/renamed in 2024). The validator enforces `primary_eval ∩ feature_bins = ∅`.

### 3.3 Multi-model panel (locked 2026-05-05; revised 2026-05-06)

GPT-4o-only at N=1500 would cost ~$900, exceeding budget. Redesigned to:

| Role | Model | Budget |
|---|---|---|
| Phase 1a cheap panel + anchor (N=100) | Qwen-2.5-72B + DeepSeek-V3.1 + MiniMax-M1 + Kimi K2 + GPT-4o anchor | ~$65 |
| Phase 1b single quality-selected model (N=1500, n=1) | Selected by §12.2 quality-primary rule | ~$95 |
| Phase 1b GPT-4o anchor (N=100 subset, n=2) | GPT-4o | ~$50 |
| **Phase 1 total** | | **~$215** |

**Honest scope-of-diversity caveat**: All 4 cheap-panel models are trained by China-based organizations (Alibaba / DeepSeek / MiniMax / Moonshot). The diversity is real (4 teams + 4 RLHF philosophies), but is **NOT** a Western-vs-Eastern training-data robustness check. The GPT-4o anchor provides the only Western-trained reference. Any "robust across LLM families" claim in the writeup must be **strictly limited to N=100 panel comparison**, **not** applied to the N=1500 headline.

### 3.4 §12.2 model-selection rule (locked 2026-05-08, quality-primary)

After a same-day reconsideration (see §4.3), flipped from cost-primary to quality-primary:

```
primary_score(model) = respondent-macro Likert MAE on 1a primary_eval (full only)
choose argmin among DQ-passers
```

**Pre-registered guard rails**:

1. **DQ-1 parse-failure ceiling**: `parse_failure_rate > 30%` disqualifies.
2. **DQ-3 mode-collapse guard (per-item relative threshold, revised 2026-05-08)**: For each primary_eval item, the model's output variance must satisfy `var(model_i) ≥ 0.30 × var(human_2024_i)`. Disqualified if >50% of items fail. The locked human-variance reference is `outputs/primary_eval_human_variance_2024.json`. This replaces the prior absolute threshold of 0.5, which was too lenient on skewed items (FEPOL, GUNLAW) and too strict on widely-spread items (PARTYID).
3. **Cost tie-break**: Within 5% of best MAE, pick lowest `cost_per_call × (1 + parse_fail)`.
4. **Qwen deterministic fallback**: If all DQ-fail, or ≥2 candidates tie on both quality and cost, use Qwen-2.5-72B-Instruct.

**One-line writeup form**:
> "We selected the lowest-MAE Phase 1a candidate among models passing pre-registered parse-failure (≤30%) and per-item relative-variance (≥30% of human variance) gates; cost served as a within-5% tie-break, with Qwen-2.5-72B-Instruct as the named fallback."

### 3.5 Four-layer leakage hygiene (R1 + R2 added 2026-05-08)

Per third-party research-layer audit §3.1, with Park v2 PDF p.10/37/39 citations independently verified by reading the source:

1. **Layer 1 (direct, prevented)**: `feature_bins ⊥ primary_eval` (validator-enforced); per-item exclusion in sensitivity pass.
2. **Layer 2 (synonymous, GSS-internal absent)**: Park v2 SI §9 empirically shows GSS-internal synonymy is empty.
3. **Layer 3 — R1 (battery-level structural exclusion, NEW; battery map expanded to v0.2 on 2026-05-09 evening)**: When predicting any primary_eval item in a battery, the entire battery is dropped from the persona prompt for that prediction. Mirrors Park v2's BFI whole-trait-block hold-out (Park v2 PDF p.37). Battery map locked in `gss_battery_map.json` **v0.2** (34 batteries + 17 singletons across all 4 bins; expanded from v0.1's 15 attitudinal-only batteries to support co-primary Battery LOO). Validated by `validate_taxonomy.py` check 7c.
4. **Layer 4 — R2 (regression-baseline partition, NEW)**: In parallel with the LLM panel, run a non-LLM regression (Ridge for Likert, multinomial Logistic for binary; 5-fold respondent-level CV; same R1 battery exclusion applied symmetrically). Per-item MAE is the auto-correlation upper bound any feature-to-item predictor can extract.

**Headline partition equation**:
```
LLM-panel MAE on item X = (regression MAE on X) + (LLM gain over regression)
                          = pure auto-correlation + persona reasoning
```

**Why R3 is NOT done**: R3 would globally remove all batteries from the attitudinal bin before any LOO ran, depressing accuracy across all conditions and conflating "battery info loss" with "bin capacity reduction." R1 already does precise per-item exclusion at the right granularity; R2 partitions inflation rather than just bracketing it. Park itself does not do an R3-style global pre-trim.

**Park v2 citations (independently verified by reading the PDF)**:
- "27 GSS items removed via cross-instrument synonym audit" — Park v2 PDF p.10 verbatim: *"The process flagged 27 GSS items, which we removed..."*
- "GSS-internal synonymy = none" — Park v2 PDF p.10 verbatim: *"We applied the same procedure to identify questions in the GSS that are synonymous to other GSS questions and **found none**."*
- "BFI uses whole-trait-block hold-out, GSS uses single-item hold-out as main + whole-module as SI robustness" — Park v2 PDF p.37 verbatim: *"For the Big-5 we always hold-out the whole block...First, we remove only the outcome question we predict...Second, we hold-out the whole GSS module..."*
- "Survey agents 0.82 → 0.77 ≈ 0.05 inflation under whole-module hold-out" — Park v2 PDF p.39: *"normalized accuracy on the GSS of 0.82 (std = 0.18)" / "average normalized accuracy of 0.77 (std = 0.12)"*

The third-party audit's citation of std=0.13 is incorrect (true values are 0.18 and 0.12 respectively), but the core ~0.05 inflation argument holds — **so the R1 + R2 Park-precedent foundation is sound**.

### 3.6 Multiplicity (FWER control; 2026-05-09 lean-design revision)

Phase 1's current LOO families:
- **4-bin primary family** (4 ΔMAE tests) — Holm-Bonferroni at α=0.05 within family.
- **Battery LOO co-primary family across all 4 bins, nested Holm per bin (revised 2026-05-09 evening)**:
  - Demographic battery family (n=7): smallest p < α/7 = 0.0071
  - Behavioral battery family (n=10): smallest p < α/10 = 0.0050
  - Psychological battery family (n=2): smallest p < α/2 = 0.025
  - Attitudinal battery family (n=15): smallest p < α/15 = 0.0033
  - Reporting role: **co-primary mechanistic finding**, equal prominence to 4-bin LOO. Cross-bin rank comparisons are descriptive only (not jointly Holm-corrected).
- **Bin-level Shapley decomposition** — robustness re-aggregation of the same 4-bin estimand; no separate Holm correction (shares the 4-bin family).

**Removed under 2026-05-09 lean-design lock**: theory-bin LOO is no longer a confirmatory family. Theory interpretation enters Discussion section only and does NOT drive any primary claim. See §3.8 + `theory_interpretation_guide.md`.

### 3.7 §11.1 Writeup language template (mandatory)

To prevent over-claiming, the following sentence-level constraints govern any Phase 1 abstract / headline figure / dashboard:

| Constraint | Required form | Forbidden form |
|---|---|---|
| "Persona fidelity" qualifier | "within-wave attitudinal prediction" | bare "persona fidelity" |
| Cross-model robustness scope | "across four China-trained instruction-tuned models in a 100-respondent comparison" | bare "across LLM families" |
| Headline-N model identity | "the {selected_model} reported under the §12.2 quality-primary rule, N=1500" | "the cheap panel" |
| Park comparison anchor | "the GPT-4o anchor on the N=100 subset, with single-item hold-out matching Park v2 SI §6" | "matches Park's 82%" |
| Auto-correlation framing | "after R1 battery-level exclusion and R2 regression-baseline partition" | bare "after leakage hygiene" |
| Test-retest claim | (none — say nothing about test-retest) | "normalized accuracy" / "fidelity" |

## 4. Decisions log (with evidence)

In chronological order, every load-bearing decision is annotated with rationale. This is the source for the OSF "decisions locked, when, against what evidence" log.

### 4.1 Phase split: GSS-first → targeted Cookiy (2026-05-02)

**Decision**: Phase 1 (GSS) before Phase 2 (Cookiy).

**Evidence**:
- Cookiy unit cost ~$11/respondent; N=1500 infeasible (>$16k)
- GSS 2024 is free, already-collected, N=3309 — ROI 100× over Cookiy
- BFI / behavioral games are not in GSS — Cookiy is required to fill the 4×3 matrix
- Bayati explicitly endorsed the phase split at 2026-05-02 meeting

**Sacrifice**: GSS lacks BFI / games / interviews / 2-week recontact. Phase 1 estimand differs from Park (single-wave vs multi-wave); §11 explicitly disclaims.

### 4.2 Single-wave snapshot rather than cross-wave (2026-05-05)

**Decision**: Predict GSS 2024 from GSS 2024 only; no use of wave-1 → wave-3 panel structure.

**Counterargument considered**: Cross-wave provides a "persistence" signal closer to Park.

**Why it failed**:
- GSS panel design is 3-wave (~2 years apart) with overlapping items — cross-wave would introduce direct item-repetition leakage
- True personality may shift over 2 years; predicting wave-3 ABANY from wave-1 ABANY mixes "persistence" with "model accuracy" — un-decomposable
- Single-wave is cleaner: defined as "same-wave features → same-wave held-out items," internally consistent if non-Park

**Sacrifice**: No test-retest baseline; cannot compute Park-style normalized accuracy. §11 / §11.1 strictly limit to raw metrics.

### 4.3 §12.2 cost-primary → quality-primary (2026-05-06)

**Decision**: Flip from `score = cost × (1 + parse_fail)` to `score = MAE` with cost as 5% tie-break only.

**Evidence**:
- 4 cheap models' cost spread is only ~2×; the N=1500 total budget swing is $50-80
- Likert MAE swings could be 0.85 vs 1.40 — orders of magnitude larger
- The paper headline metric is MAE; the selection criterion must align with the headline metric
- Cost-primary sounds "conservative" but creates an internal inconsistency reviewers will spot immediately

**Cost-primary preserved as a history note** to make the reversal logic auditable.

### 4.4 DQ-3 absolute threshold → per-item relative threshold (2026-05-08)

**Decision**: From `mean(per_item_var) < 0.5 → DQ` to `var(model_i) / var(human_i) < 0.30 for >50% items → DQ`.

**Evidence (quantitative)**: Human variance spans 28× across primary_eval items:
- FEPOL (var=0.15): 82/18 split — a 0.5 absolute threshold demands variance 3× higher than humans
- PARTYID (var=4.24): 8-point spread — a 0.5 threshold is ~12% of human variance, almost any model passes
- 30% relative threshold: FEPOL → 0.045 (catches single-mode), PARTYID → 1.27 (catches single-mode), both calibrated

The locked reference is at `outputs/primary_eval_human_variance_2024.json`, OSF-pre-registered as a frozen artifact.

### 4.5 R1 battery boundaries (2026-05-08)

**Decision (v0.1, 2026-05-08)**: 15 batteries + 9 singletons (attitudinal-only scope). Civil-liberties split into 3 batteries by target group (atheists / racists / communists), not collapsed into one.

**Subsequent expansion (v0.2, 2026-05-09 evening)**: expanded to all 4 bins, 34 batteries + 17 singletons (demographic 7 + behavioral 10 + psychological 2 + attitudinal 15 unchanged), to support co-primary Battery LOO. See §3.6 + §3.8.2.

**Evidence**:
- Knowing R's view of racists' free-speech tells you very little about R's view of atheists' free-speech, but lots about R's other racism-related views
- Park's BFI doesn't make "all personality traits" one battery — it groups by trait (neuroticism / openness as separate blocks) — so battery should align with the LOO's "within-construct" semantics
- The earlier `morality_lifestyle` aggregation was too broad; refined into `sexual_morality` / `moral_legalization` / `adolescent_sex_policy`

The complete mapping is in `gss_battery_map.json`.

### 4.6 R3 NOT implemented (2026-05-08)

**Decision**: R1 + R2 only; R3 (whole-attitudinal-bin Park-strict reanalysis) NOT done.

**Evidence**:
- R3 globally depresses all condition accuracies, making LOO ranking uninterpretable — can't separate "battery info loss" from "bin capacity reduction"
- R1 does precise per-item exclusion at the right granularity, finer than R3
- R2 partitions inflation directly, surpassing R3's "bracket" approach
- Park itself does not run an R3-style global pre-trim

### 4.7 Theory-bin via OSF amendment (2026-05-08)

**Decision (interim, superseded by §4.8)**: Initial OSF locks 4-bin LOO only; theory-bin LOO enters via amendment after Joyce's literature lock.

**Evidence**:
- Theory not yet selected (Round 1 + Round 2 literature reviews ongoing: 6 candidates — MFT / Schwartz / Bourdieu / Cultural Theory / Inglehart-Welzel / Big Five)
- Locking theory-bin alongside 4-bin would be false locking — committing to "some analysis on a theory not yet chosen"
- Amendment path is fully compliant — what matters is that any theory-bin re-aggregation occurs only after the amendment is filed

### 4.8 Lean-design lock: theory-bin removed entirely from confirmatory plan (2026-05-09)

**Decision**: Theory-bin LOO is removed as a confirmatory family entirely (it is NOT entering the OSF pre-reg, neither initially nor via amendment). Theory framing enters Discussion section only as interpretive secondary analysis across 6 candidate frameworks.

**Evidence**:
- Codex's lean-design audit (2026-05-09) flagged that a 6-theory horse-race confirmatory framework would push the paper toward "tool-stack paper" territory and overshadow its clean primary contribution.
- The paper's primary question is engineering (*"which feature categories drive LLM persona prediction?"*), not theoretical (*"which cognitive theory wins?"*) — the methodology should match.
- Anti-HARKing discipline is preserved through (a) theory-list pre-commitment in `theory_interpretation_guide.md`, (b) primary findings stand alone in atheoretical engineering language, (c) null-alignment reporting commitment.
- See `gss_phase1_design.md` §13.3 + §13.4 for the full deferred-to-future-work list.

## 5. Innovation + impact

### 5.1 Conceptual contribution

- **First large-N feature attribution for LLM persona synthesis**: N=1500 systematic attribution on attitude prediction, answering "which input feature category most effectively drives LLM persona accuracy" — a core methodological question for the LLM persona simulation research area, but no prior published work has done this at this scale, leakage-stringency, or multi-model robustness.
- **First instance of an (input feature × outcome dimension) two-dimensional feature-importance map**: Phase 1 provides the attitude-dimension 4-bin attribution; Phase 2 extends to personality + behavior. The final deliverable is a 2D map — this structure follows naturally from the three independent measurement traditions in psychology (attitude / personality / behavior), not from any single prior work's framework.
- **First paper of an ongoing research program**: the research direction this project sets up (feature attribution for LLM persona synthesis) extends naturally to long-term behavior, cross-cultural validation, multimodal personas, open-ended responses, and other outcome dimensions. Phase 1 + Phase 2 are the first two papers of this program.

### 5.2 Methodological contribution (independent of Park)

Four transferable artifacts that **stand alone without Park as a frame**:

1. **R1 — Battery-level structural exclusion** (`gss_battery_map.json` + `build_persona_prompt(exclude_vars=...)`): when an LLM persona prompt is used to predict any item in a within-construct cluster, the entire cluster must be removed from the prompt. Park v2 applies trait-block hold-out for BFI but uses the lenient single-item strategy for GSS; R1 applies the stricter standard to GSS (and to any subsequent persona work using other survey instruments).
2. **R2 — Regression-baseline partition** (`regression_baseline.py`): a non-LLM regression baseline runs in parallel with the LLM panel, partitioning LLM accuracy into (auto-correlation any predictor can exploit) + (LLM persona-reasoning gain). This is **a new method** — prior work *brackets* inflation ranges; R2 directly *partitions* it.
3. **Multi-model cheap-panel + §12.2 quality-primary selection rule + named fallback** (`select_phase1b_model.py`): a budget-constrained model-selection OSF template for serious LLM persona research that doesn't rely on GPT-4o. 5-branch self-test passes.
4. **DQ-3 per-item relative variance threshold** (`outputs/primary_eval_human_variance_2024.json`): item-level relative threshold for mode-collapse detection, more robust than absolute thresholds — correctly discriminates on both skewed items (e.g., FEPOL 82/18) and wide-distribution items (e.g., PARTYID 8-point).

### 5.3 Industry adjacency

- Commercial synthetic-respondent panels (Aaru / Voicepanel / Synthetic Users) under commercial pressure converge on "more data, more models" engineering — none do careful feature attribution + leakage hygiene. Phase 1's R1+R2 + Shapley + Battery LOO toolchain is a clean public contribution to this niche.
- Stanford spinout Simile productionizes LLM persona pipelines; this project's (input feature × outcome dimension) attribution map is the closest public artifact to "which inputs matter for which outputs" — directly usable by productized persona services as input recommendation guidance.

### 5.4 Academic placement

Realistic submission targets:
- *Management Science* methods track (best fit for the GSB orientation)
- NeurIPS Datasets & Benchmarks (pre-reg + reproducible artifact)
- CSCW / FAccT (persona auditing angle)

Not realistic:
- Mainstream NeurIPS / ICML (not algorithmic innovation)
- Top-tier JPSP / psychology (not a human-cognition claim)

## 6. Anticipated criticisms + responses

### 6.1 "Your estimand isn't Park's"

**Response**: Fully accepted. §11 / §11.1 explicitly forbid "persona fidelity"-style normalization-implying language. The abstract must use "within-wave attitudinal prediction." Park comparison happens only via the N=100 GPT-4o anchor + single-item hold-out per-item raw accuracy table — explicitly SI / appendix, not headline.

### 6.2 "Auto-correlation makes the attitudinal bin look important"

**Response**: R1 + R2 are the direct methodological defense.
- R1: battery-level exclusion isomorphic to Park's BFI rule
- R2: regression-baseline partition — separates "LLM persona-reasoning gain" from "auto-correlation any model can exploit"

Reported in abstract / headline:
- LLM-panel MAE on attitudinal-bin LOO drop = X
- Regression-only MAE on same bin = Y
- LLM persona gain = X − Y

If Y/X ≈ 1, the attitudinal bin's "contribution" is fully auto-correlation; if Y/X ≈ 0, it's genuine persona reasoning. **This is the central empirical finding of the paper.**

### 6.3 "All 4 cheap models are China-trained"

**Response**: §11.1 explicitly limits "across LLM families" to the N=100 1a panel; the Phase 1b headline runs on a single quality-selected model; the GPT-4o anchor (N=100) provides the Western reference. If a stronger cross-cultural diversity claim is needed, sensitivity adds Llama-3.3-70B (Meta) — but this is post-headline, not primary.

### 6.4 "LOO on unbalanced bins is a known weak attribution method"

**Response (lean-design revision)**: Accepted. The two secondary tools in the lean lock directly respond:
- **Bin-level Shapley decomposition (§3.8.1)** — 16-condition full enumeration, automatically captures bin-bin interactions; compared against 4-bin LOO ranking for consistency. Runs on Phase 1a.
- **34-battery LOO across all 4 bins (§3.8.2)** — **co-primary mechanistic finding**, unconditional, nested Holm per-bin. Runs on Phase 1c.

LOO ΔMAE is a marginal estimator; Shapley adds interaction-aware estimates (4-bin only); Battery LOO adds construct-level granularity across all 4 bins. The three are **complementary, not redundant**: 4-bin answers the bin-level question; Shapley answers the bin-interaction question; Battery LOO answers the cluster-level mechanistic question. Other approaches (Bin-size-balanced subsampling / leave-one-in / RSA / sampled Shapley on batteries) are deferred to future work (see §3.8.4).

### 6.5 "DQ-3 threshold is arbitrary"

**Response**: 30% is not arbitrary. §4.4 contains the quantitative analysis — human variance spans 28×, so a relative threshold is required. 30% consistently separates calibrated models from mode-collapsed models across all 12 primary_eval items. Alternatives X=20% / 50% are discussed in §4.4. All evidence enters OSF.

### 6.6 "Pre-registration is post-pilot"

**Response**: Accepted. The OSF pre-reg includes a "decisions locked, when, against what evidence" log (this document §4 is the template). Reviewers can audit the timeline and empirical basis for every decision.

### 6.7 "Phase 2 N=20-30 is too small"

**Response**: Phase 2 design doc admits the limit. Before pre-reg, a Phase-1-empirics-seeded power-calc simulation will pre-disclose which 4×3 cells are detectable at N=30 vs need N≥60.

### 6.8 "Theory-driven LOO needs a chosen theory"

**Response (revised under lean lock)**: Under the 2026-05-09 lean-design lock, theory is no longer a confirmatory family. Theory interpretation enters **Discussion section only** (see `theory_interpretation_guide.md`); primary findings do not depend on theory alignment. This revision dissolves the "needs a chosen theory" objection — the Discussion discusses 6 candidate frameworks qualitatively, with no requirement to declare a winner.

### 6.9 "Lean design = thin paper" (potential criticism)

**Response**: Lean ≠ thin. Two co-primary analyses + Shapley robustness together form a 4-stage attribution answer:
- Stage 1 (co-primary #1, broad): Which bin matters (4-bin LOO)
- Stage 2 (robustness): Whether the 4-bin ranking is robust to bin-bin interactions (Shapley)
- Stage 3 (**co-primary #2, mechanistic**): Which construct-level clusters drive the signal within each bin (**34-battery LOO across all 4 bins, nested Holm per-bin**)
- Stage 4 (Discussion): How the empirical pattern is interpreted across 6 candidate frameworks (`theory_interpretation_guide.md`)

Add R1 + R2 leakage hygiene + §12.2 quality-primary multi-model selection + GPT-4o anchor for Park comparability, and the methodological contribution itself is half the paper's value. The paper does not need a 6-theory horse race to be publishable — a clear, verifiable, reproducible ablation outweighs a tool stack at peer review.

## 7. Follow-up plans + timeline

### 7.1 Before Phase 1a (~2-3 days)

1. Joyce runs N=10 paid smoke test (needs OpenRouter API key, ~$2-3)
2. Joyce drafts OSF pre-registration (4-bin primary scope; this document §3+§4 is the template)
3. Joyce + Bayati final-design alignment (especially §12.2 quality-primary flip + R1+R2 additions)

### 7.2 After Phase 1a (~1 week)

4. Run §12.2 selector to pick the Phase 1b model
5. Run R2 regression baseline on the 1b sample
6. Produce 1a multi-model panel report as the cross-model robustness evidence

### 7.3 After Phase 1b (~2 weeks)

7. Run Phase 1b headline (N=1500)
8. Compute 4-bin LOO ΔMAE + Holm-Bonferroni FWER
9. Compute LLM-vs-regression partition (R2)
10. Produce sensitivity table: per-item raw accuracy on ~118 Park-comparable items, N=100 GPT-4o anchor

### 7.4 ~~Theory-bin amendment~~ (REMOVED under lean lock 2026-05-09)

The original §4.7 plan ("after Joyce's literature lock → build `gss_theory_taxonomy.json` → file OSF amendment → run theory-bin LOO as secondary headline") **was removed entirely under the lean-design lock** (see §4.8). Theory interpretation now enters Discussion only — no amendment, no taxonomy build, no secondary headline. Joyce's literature review continues, but as Discussion-writing input only, NOT as a Phase 1c gating activity.

### 7.5 Phase 2 (Summer 2026)

11. Use Phase 1 empirics to seed power calc, pre-disclose detectable cells
12. Cookiy + Prolific collect N=20-30 with 2-week recontact
13. Fill BFI row + behavioral-game row of the 4×3 matrix
14. Write paper

---

# Document end / 文档结束

This document is the canonical pre-smoke-test review artifact. After tonight's review and any redirection from Joyce, it can be removed — its content is fully derived from the locked design files (`gss_phase1_design.md`, `gss_battery_map.json`, `select_phase1b_model.py`, `regression_baseline.py`, `outputs/primary_eval_human_variance_2024.json`) and reproducible from them.

本文档是烟雾测试前的标准审阅工件。今晚审阅并听取 Joyce 的修订意见后即可删除——其内容完全来自已锁定的设计文件，并可从中复现。

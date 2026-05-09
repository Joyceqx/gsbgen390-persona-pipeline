# GSBGEN390 项目综合文档 / Project Synthesis Document

**作者 / Author**: Joyce Yu
**指导教师 / Advisor**: Prof. Mohsen Bayati (Stanford GSB)
**课程 / Course**: GSBGEN390 thesis-track research, Stanford GSB, Spring 2026
**文档生成日期 / Generated**: 2026-05-08, revised 2026-05-09 (lean-design lock)
**文档定位 / Document role**: 烟雾测试前的综合审阅文档；包含全部进展、决策依据、创新论证、可能的质疑、后续方案 / Pre-smoke-test comprehensive review; covers full progress, decision rationale, innovation argument, anticipated criticisms, follow-up plans

> **Revision note (2026-05-09)**: Per Codex's lean-design audit, the Phase 1 design was slimmed from a six-theory horse-race confirmatory framework to a leaner structure with 4-bin LOO as primary, Shapley as robustness, attitudinal-bin Battery LOO as interpretability, and theory framing as Discussion-section interpretation only. RSA / permutation importance / Stage 3 refinement / Friedman's H were all explicitly deferred to future work. See `gss_phase1_design.md` §13 + `theory_interpretation_guide.md` for the live spec.

---

# 第一部分（中文）

## 0. 执行摘要

本项目的核心目标是**为 Park et al. 2024（"Generative Agent Simulations of 1,000 People"）填补一个论文里**暗示但从未实证填补的空白**：将 Park 那个 "调查 vs 访谈" 的人格保真度差距按 **(特征类别 × 输出维度) 的 4×3 矩阵**分解。Phase 1 攻击 GSS-态度这一行（最便宜、最易验证的一格），用 N≈1,500 公开 GSS 2024 数据 + 4 个便宜 OpenRouter 模型 panel + GPT-4o anchor 做 LOO ablation。Phase 2 用定向 Cookiy 收集补齐 BFI 人格 + 行为博弈两行（小 N + 2 周复测 baseline）。

整个 Phase 1 设计经过 **3 轮独立 Codex 审计 + 1 轮研究层 Codex 审计**，共修复 27 项发现。当前代码库通过 `validate_taxonomy.py`（10 个检查项）+ 5 个 AUDIT 智能测试 + §12.2 选择器 5 分支测试 + R2 回归基线 self-test，全部绿灯。OSF 预注册可在 N=10 烟雾测试通过后立即起草。

## 1. 研究问题与立场

### 1.1 核心研究问题

**在 GSS 态度这一输出维度上，4 类调研可采集的特征（人口学 / 行为 / 心理 / 态度）中，哪一类对 LLM 人格预测的贡献最大？**

这是 (特征类别 × 输出维度) 论文矩阵的 GSS-态度格。它最便宜——GSS 公共数据免费、N 上千。BFI 人格与行为博弈两个输出维度推迟到 Phase 2（Cookiy 定向收集）。

### 1.2 研究估计量（estimand）

> Phase 1 估计的是 **GSS 2024 单波次预测**：从同波次 GSS 特征变量预测 12 个留出 `primary_eval` 题目（外加 ~118 个 Park-comparable sensitivity_eval 题目），按 4 个预先注册的特征类别贡献分解。

**它显式不是**：
- 复测预测（GSS 2024 没有 recontact baseline）
- 跨波次预测（不用 panel 结构）
- 归一化人格保真度（不除以 test-retest 分母）
- 关于"人类模拟能力"的一般性主张

它**是**：在单波次 GSS 态度预测内部，对 4 个特征类别贡献做的归因分析。

### 1.3 与 Park v2 的对照标定

Park v2（arXiv:2411.10109 v2）是活基准。Park 的输出按维度分层：
- GSS 态度：surveys ≈ interviews（0.82 vs 0.83 归一化精度）
- BFI 人格：surveys 落后 interviews 0.15
- 行为博弈：surveys 落后 interviews 0.28

整个项目的论点是：**Park 这个 0.15 / 0.28 的差距不是"interview 普遍更优"，而是"interview 在不同特征 → 不同输出维度的组合上有结构性优势"。** 4×3 矩阵把这个论点变成可证伪。

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

### 3.6 多重比较（FWER 控制；2026-05-09 lean-design 修订）

Phase 1 当前的 LOO families：
- **4-bin primary family** (4 ΔMAE tests) — Holm-Bonferroni at α=0.05 within family.
- **Attitudinal-bin battery LOO secondary family**（~10-11 tests）—— 仅在 4-bin LOO 确认 attitudinal 主导后启动；Holm-Bonferroni 独立校正。Reporting role 是描述性 within-bin decomposition，不是 co-primary headline。
- **Bin-level Shapley decomposition** —— 4-bin LOO 同一估计量的 robustness re-aggregation；不需要单独 Holm 校正（共享 4-bin family）。

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

#### 3.8.2 Attitudinal-bin battery LOO（secondary — interpretability）

- **目的**：**条件依赖于** 4-bin LOO 确认 attitudinal 主导，确定 bin 内具体哪些 batteries 驱动 prediction 信号。
- **触发条件**：仅在 `shapley_per_bin.attitudinal.rank == 1` AND attitudinal-bin LOO ΔMAE > 其他三 bin LOO ΔMAE 时跑。否则报告 "attitudinal 不主导，battery decomposition 未跑"。
- **算法**：对 attitudinal bin 的 ~10-11 个 batteries（per `gss_battery_map.json`），drop 整个 battery（外加 R1 per-item battery exclusion 已经应用），re-run prediction，computer respondent-macro Likert ΔMAE vs FULL。Bootstrap CI + Holm-Bonferroni at α=0.05 within attitudinal-bin battery family。
- **何时跑**：Phase 1c (post Phase 1b headline) 在 §12.2-selected 1b 模型上。增量 ~$25-30。
- **Reporting role**：descriptive within-bin decomposition；不是 co-primary headline。

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

**决策**：15 batteries + 9 singletons，civil_liberties 按 target group 分 3 个（atheists / racists / communists），不合成 1 个。

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
- Attitudinal-bin Battery LOO 作 secondary interpretability（trigger 条件：attitudinal 主导）
- R1 + R2 leakage hygiene（locked, 不变）
- §11.1 abstract 措辞模板（locked, 不变）
- §12.2 quality-primary 选择规则（locked, 不变）

**撤掉的具体部件**：见 §3.8.4 + `gss_phase1_design.md` §13.4。

**撤掉的 history note**：早晨 v0.1 DRAFT 的 `osf_preregistration_appendix_a_theory_predictions.md` 改名为 `*.SUPERSEDED-2026-05-09.md`。新文件 `theory_interpretation_guide.md` 是当前 live spec。

## 5. 创新与影响

### 5.1 概念贡献

- **Park 4×3 矩阵的首次系统填充**：Park 的 (interview / survey / demo) × (GSS / BFI / 行为博弈) 在论文里只填了对角线和总平均；Phase 1 + Phase 2 一起填满 12 格中的 4 格（4 特征类别 × 3 输出维度）。这是个二阶导数贡献——不重新发明 Park 的框架，而是细化它。
- **Park 的 0.15 / 0.28 差距是结构性的，不是偶然**：通过证明特征类别贡献在 BFI / 行为博弈输出上分布不同（Phase 2），可以告诉别人"哪些特征不该再被忽视"。

### 5.2 方法学贡献（更强）

三个可迁移的工件：

1. **泄漏审计 + strict/broad-clean rescoring 流程**（pilot 阶段已落地）
2. **多模型便宜 panel + §12.2 quality-primary 选择规则 + 命名 fallback OSF 模板** —— 任何后续 LLM-persona 论文都可借鉴
3. **R1 + R2 dual defense（battery 排除 + 回归基线分割）—— Park v2 自己没做的 partition test**

R2 是这次审计修复后**新增的方法学贡献**——Park v2 用两种 hold-out 策略 *bracket* 偏差范围，我们用 regression baseline *partition* 偏差。这是真正"超越 Park"的一步。

### 5.3 行业关联

- Stanford 出来的 Simile 把 Park 的流水线产品化；4×3 矩阵是当下最接近"哪些输入对哪些输出有用"的公开 artifact
- Aaru / Voicepanel / Synthetic Users 全是商用合成 panel，但商用压力让他们都是 "more data, more models" 工程视角——没人做 careful feature attribution + leakage hygiene。Phase 1 的 R1+R2 + Shapley + Battery LOO 工具链是这个 niche 的清晰公共贡献。

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
- **Attitudinal-bin Battery LOO (§3.8.2)** —— attitudinal 主导时，within-bin battery-level decomposition。Phase 1c 上跑。

LOO ΔMAE 是 marginal estimator；Shapley 补 interaction-aware 估计；Battery LOO 补 within-bin 颗粒度。三者互为 robustness 与 interpretability。其他方法（Bin-size-balanced subsampling / leave-one-in / RSA）defer 到 future work（详见 §3.8.4）。

### 6.5 "DQ-3 阈值是任意选的"

**应对**：30% 不是任意。在 §4.4 决策依据里 quantitative 分析过——人类方差跨度 28×，相对阈值是必须的。30% 相对阈值在 (FEPOL, GUNLAW, ABANY, ..., PARTYID, POLVIEWS) 12 个 items 上一致地区分了 calibrated 模型与 mode-collapsed 模型。alternative X=20% / 50% 在 §4.4 也讨论过。所有依据进 OSF。

### 6.6 "Pre-registration is post-pilot"

**应对**：admitted。OSF 预注册前会附 "decisions locked, when, against what evidence" log（本文档 §4 即模板）。审稿人可以追溯每个决策的时间线和经验依据。

### 6.7 "Phase 2 N=20-30 太少"

**应对**：Phase 2 设计文档承认这个限制。预注册前会跑 Phase-1-empirics-seeded power-calc simulation，预先披露 4×3 矩阵中哪些格在 N=30 下可检测、哪些需要 N≥60。

### 6.8 "Theory-driven LOO 需要选定理论"

**应对**（lean-design 后修订）：lean 设计中 theory 不再是 confirmatory family 的一部分。理论解释**只**进 Discussion section（见 `theory_interpretation_guide.md`），primary findings 不依赖理论对齐。这一修订把 "需要选定理论" 这个反对意见消解为 "discussion 中讨论 6 个候选框架，不必胜出一个"。

### 6.9 "Lean 设计 = 论文太薄"（潜在批评）

**应对**：lean 设计 ≠ 论文薄。primary 4-bin LOO + Shapley + Battery LOO 三者一起仍然是 4-stage 归因的 well-defined 答案：
- Stage 1：哪个 bin 重要（4-bin LOO）
- Stage 2：4-bin ranking 是否 robust to interactions（Shapley）
- Stage 3：attitudinal 主导时哪些 batteries 出力（Battery LOO）
- Stage 4：哪些 framework 在 Discussion 解读这个 pattern（theory_interpretation_guide.md）

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

### 7.4 Theory-bin amendment（Joyce 文献完成后）

11. 锁定 `gss_theory_taxonomy.json`
12. OSF amendment for theory-bin LOO
13. Re-aggregate 既有 1a/1b 输出，出 secondary headline

### 7.5 Phase 2（2026 暑期）

14. 用 Phase 1 经验 seed power calc，预先披露可检测格
15. Cookiy + Prolific 收 N=20-30 with 2-周 recontact
16. 填充 BFI 行 + 行为博弈行
17. 写论文

---

# Part 2 (English)

## 0. Executive Summary

This project's central goal is to **fill an empirical gap implied but never delivered by Park et al. 2024 ("Generative Agent Simulations of 1,000 People")**: decompose Park's aggregate "interview vs surveys" persona-fidelity gap along a **(feature category × outcome dimension) 4×3 matrix**. Phase 1 attacks the GSS-attitudes row (cheapest, most verifiable cell) using N≈1,500 of the public GSS 2024 cross-section + a 4-cheap-OpenRouter-model panel + GPT-4o anchor in a leave-one-out (LOO) ablation. Phase 2 uses targeted Cookiy collection at smaller N with a 2-week recontact to fill the BFI personality and behavioral-economic-game rows.

The Phase 1 design has been hardened by **3 rounds of independent Codex audit + 1 research-layer Codex audit**, fixing 27 distinct findings. The codebase passes `validate_taxonomy.py` (10 checks) + 5 AUDIT smoke tests + the §12.2 selector's 5-branch self-test + the R2 regression-baseline self-test, all green. The OSF pre-registration can be drafted immediately after the N=10 paid smoke test passes.

## 1. Research question + stance

### 1.1 Research question

**Among four survey-collectible feature categories (demographic / behavioral / psychological / attitudinal), which contributes most to LLM-persona prediction of GSS attitudes?**

This is the GSS-attitudes cell of the (feature × outcome) thesis matrix. It's the cheapest cell to attack first — GSS public data is free and N is in the thousands. The BFI-personality and behavioral-game outcome dimensions are deferred to Phase 2 (targeted Cookiy collection).

### 1.2 Estimand

> Phase 1 estimates **single-wave GSS 2024 prediction** of held-out items (the 12 in `primary_eval`, plus per-item Park-comparable sensitivity over ~118 items) **from same-wave GSS feature variables**, decomposed into the contribution of four pre-registered feature categories.

This is **explicitly NOT**:
- Test-retest prediction (no GSS 2024 recontact baseline)
- Cross-wave prediction (no panel structure used)
- Normalized persona fidelity (no test-retest denominator)
- A general claim about "human simulation ability"

It **is**: feature-category contribution analysis within single-wave GSS-attitudinal-item prediction.

### 1.3 Park v2 reference

Park v2 (arXiv:2411.10109 v2) is the live benchmark. Park's headline is outcome-stratified:
- GSS attitudes: surveys ≈ interviews (0.82 vs 0.83 normalized accuracy)
- BFI personality: surveys lag interviews by 0.15
- Behavioral games: surveys lag interviews by 0.28

The thesis-level claim: **Park's 0.15 / 0.28 gap is not "interviews are universally better" but "interviews have structural advantages on specific feature → outcome combinations."** The 4×3 matrix renders this falsifiable.

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
3. **Layer 3 — R1 (battery-level structural exclusion, NEW)**: When predicting any primary_eval item in a battery, the entire battery is dropped from the persona prompt for that prediction. Mirrors Park v2's BFI whole-trait-block hold-out (Park v2 PDF p.37). Battery map locked in `gss_battery_map.json` (15 batteries + 9 singletons). Validated by `validate_taxonomy.py` check 7c.
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

### 3.6 Multiplicity (FWER control)

Phase 1 has TWO LOO families:
- **4-bin primary family** (4 ΔMAE tests) — Holm-Bonferroni at α=0.05 within family.
- **Theory-bin secondary family** (~5-10 tests, depending on theory choice) — entered via OSF amendment after Joyce's literature lock; reported only as secondary confirmation, never as co-primary headline.

The initial OSF pre-reg locks **the 4-bin family only**; theory-bin enters via amendment.

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

**Decision**: 15 batteries + 9 singletons. Civil-liberties split into 3 batteries by target group (atheists / racists / communists), not collapsed into one.

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

**Decision**: Initial OSF locks 4-bin LOO only; theory-bin LOO enters via amendment after Joyce's literature lock.

**Evidence**:
- Theory not yet selected (Round 1 + Round 2 literature reviews ongoing: 6 candidates — MFT / Schwartz / Bourdieu / Cultural Theory / Inglehart-Welzel / Big Five)
- Locking theory-bin alongside 4-bin would be false locking — committing to "some analysis on a theory not yet chosen"
- Amendment path is fully compliant — what matters is that any theory-bin re-aggregation occurs only after the amendment is filed

## 5. Innovation + impact

### 5.1 Conceptual contribution

- **First systematic filling of the Park 4×3 matrix**: Park's (interview / survey / demo) × (GSS / BFI / games) is filled only along the diagonal and aggregate; Phase 1 + Phase 2 together populate 4 of 12 cells (4 feature categories × 3 outcome dimensions). This is a second-derivative contribution — it doesn't reinvent Park's framework, it refines it.
- **Park's 0.15 / 0.28 gap is structural, not incidental**: by demonstrating that feature-category contributions distribute differently across BFI / games (Phase 2), the paper tells future researchers "these features can no longer be ignored on these outcomes."

### 5.2 Methodological contribution (stronger than conceptual)

Three transferable artifacts:

1. **Leakage audit + strict/broad-clean rescoring procedure** (delivered in pilot)
2. **Multi-model cheap panel + §12.2 quality-primary selection rule + named fallback OSF template** — directly reusable by any subsequent LLM-persona paper
3. **R1 + R2 dual defense (battery exclusion + regression-baseline partition) — a partition test Park v2 itself does not run**

R2 is the genuine **methodological gain after this audit**: Park brackets inflation between two hold-out strategies; we partition it via a regression baseline. This is the actual "step beyond Park."

### 5.3 Industry adjacency

- Stanford-spinout Simile productionizes Park's pipeline; the 4×3 matrix is the closest public artifact to "which inputs matter for which outputs"
- Aaru / Voicepanel / Synthetic Users are all commercial synthetic-respondent panels, but commercial pressure pushes them toward "more data, more models" engineering — **none are doing theory-driven input organization** — exactly the Phase 1c (theory-driven LOO) niche

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

**Response**: Accepted in third-party audit §3.2. Three complements:
- Leave-one-in (reported in sensitivity, ~$25 incremental)
- Bin-size-balanced subsampling (Phase 2 / post-1a sensitivity)
- Shapley 16-condition decomposition (post-1a sensitivity, ~$15)

These do not enter primary headline because pre-reg conditions are locked; they enter the sensitivity section as a robustness triangle.

### 6.5 "DQ-3 threshold is arbitrary"

**Response**: 30% is not arbitrary. §4.4 contains the quantitative analysis — human variance spans 28×, so a relative threshold is required. 30% consistently separates calibrated models from mode-collapsed models across all 12 primary_eval items. Alternatives X=20% / 50% are discussed in §4.4. All evidence enters OSF.

### 6.6 "Pre-registration is post-pilot"

**Response**: Accepted. The OSF pre-reg includes a "decisions locked, when, against what evidence" log (this document §4 is the template). Reviewers can audit the timeline and empirical basis for every decision.

### 6.7 "Phase 2 N=20-30 is too small"

**Response**: Phase 2 design doc admits the limit. Before pre-reg, a Phase-1-empirics-seeded power-calc simulation will pre-disclose which 4×3 cells are detectable at N=30 vs need N≥60.

### 6.8 "Theory-driven LOO needs a chosen theory"

**Response**: §13 explicitly NOT-LOCK-READY; the initial OSF doesn't include theory-bin LOO; entry via amendment. Joyce is conducting Round 1 + Round 2 literature reviews (candidates: MFT / Schwartz / Bourdieu / Cultural Theory / Inglehart-Welzel / Big Five).

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

### 7.4 Theory-bin amendment (after Joyce's literature lock)

11. Lock `gss_theory_taxonomy.json`
12. File OSF amendment for theory-bin LOO
13. Re-aggregate existing 1a/1b outputs; produce secondary headline

### 7.5 Phase 2 (Summer 2026)

14. Use Phase 1 empirics to seed power calc, pre-disclose detectable cells
15. Cookiy + Prolific collect N=20-30 with 2-week recontact
16. Fill BFI row + behavioral-game row of the 4×3 matrix
17. Write paper

---

# Document end / 文档结束

This document is the canonical pre-smoke-test review artifact. After tonight's review and any redirection from Joyce, it can be removed — its content is fully derived from the locked design files (`gss_phase1_design.md`, `gss_battery_map.json`, `select_phase1b_model.py`, `regression_baseline.py`, `outputs/primary_eval_human_variance_2024.json`) and reproducible from them.

本文档是烟雾测试前的标准审阅工件。今晚审阅并听取 Joyce 的修订意见后即可删除——其内容完全来自已锁定的设计文件，并可从中复现。

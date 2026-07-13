# Park v2 Comparability — Thinking Log (2026-06-01)

> **Status**: Phase 1A 跑期间的思考存档，**未决定**。Phase 1B 启动前再 revisit。
> 主线 Phase 1A 框架 NOT TOUCHED；这里只记录 framing options。

## TL;DR

Park v2 surveys-only 有两种 leakage 协议（A: item-only / B: module hold-out）。
我们的 R1 OFF = Park A 严格相等。我们的 R1 ON 落在 A 和 B **之间**。
Phase 1B 待决定：要不要再加一个 R1 = Park-B-equivalent 的 condition。

---

## 1. Park v2 surveys-only 协议（Researcher 已 verified, SI §"Exploratory robustness"）

| Park 协议 | persona 里去掉什么 | aggregate raw / normalized |
|---|---|---|
| **Strategy A** (item-only) | 只去掉要预测那 1 题 | 64.25% / **0.82** |
| **Strategy B** (module hold-out) | 整个 GSS topic module | 60.57% / **0.77** |
| Maximal (not us) | GSS + BFI + economic games + interviews | — |

surveys-only persona = **GSS core + BFI-44**（economic games 不在）。
Park v2 SI **没有 per-item surveys-only 表**，只有 aggregate + per-item interview (Table 3)。

## 2. 我们 R1 vs Park A/B 的具体映射

| 我们的 condition | 对 abortion battery | 对 polviews/partyid (非 battery) | 等价于 Park 谁 |
|---|---|---|---|
| **R1 OFF (anchor A)** | 只去 ABANY | 只去 POLVIEWS | **= Strategy A 严格相等** ✓ |
| **R1 ON (anchor B / Phase 1A)** | 去 AB* 7 题（整 battery）| 只去 POLVIEWS | **介于 A 和 B 之间** |
| **(假想) R1 = module hold-out** | 整 abortion module + 邻居 | 整 political module（POLINT etc.）| **= Strategy B 严格相等** |

R1 vs Park B 的本质差别：
- **R1 = principled semantic siblings**（GSS battery 是命名共享、语义共享的家族）
- **Strategy B = operational GSS topic block**（GSS 编辑给的 module 边界，有些 module 杂）

## 3. Phase 1B 待决定的开放问题

### Q1: 要不要加 "R1-module" condition 直接对标 Park B?
- **Pro**: 多一个 apples-to-apples aggregate 比较点（0.77 normalized 是 Park 唯一在 R1-style protocol 下的数字）
- **Con**: 多一个 condition = 多 $24/model；GSS module 边界要单独定义；我们 R1 已经是 principled，可能不必为了对标 Park 而改方法论
- **决策依据**: Phase 1A 结果出来后看 R1 ON aggregate 落在哪——如果落在 [0.77, 0.82] 区间内 = sanity check pass，可能不需要单独跑 module condition

### Q2: per-item Park 比较该怎么写?
- Park v2 SI **没发表过 surveys-only per-item table** → 我们 12 个 per-item × R1 ON / OFF 数字 = **novel contribution**（"我们拆开看，Park 没拆"）
- 但**不能**用 Park Table 3 (interview-based) 当 per-item surveys baseline——这是误导
- 可以用 Park aggregate (0.82 / 0.77) 当 reference line 横线

## 4. Phase 1B framing 可选方案

| 方案 | 内容 | 成本 | 干净度 |
|---|---|---|---|
| **A 极简** | 只保留 anchor A (R1 OFF) ⇆ Park A 直接比；R1 ON bracket | $0 增 | ✓✓ 干净 |
| **B 加 module** | 再跑一个 R1 = module hold-out condition，直接 ⇆ Park B | +$24/model | ✓✓✓ 最严 |
| **C 概念分离** | 解释 R1 = principled vs Park B = operational, 不假装 equal | $0 增 | ✓ 智识诚实 |

**当前默认**: A + C（极简 + 概念分离）。Phase 1A 数据出来后 reconsider。

## 5. 当前 Phase 1A / anchor 实际跑的设计

- **Phase 1A**: cheap × 4 models × R1 ON × P1-P3 × N=100 cohort
- **Anchor A**: GPT-4o × R1 OFF × N=100（**= Park Strategy A 严格对标**）
- **Anchor B**: GPT-4o × R1 ON × N=100（**bracket Park A/B, 同 cohort 与 Phase 1A 做 model-axis comparison**）

## 6. 已经更新到 RESEARCH_DESIGN.md §5.6 的内容

- ⚠️ 之前给 Joyce 的 per-item table (POLVIEWS 0.55 etc.) 实际是 **Park interview condition**，需要从 §5.6 移除/修正
- §5.6 应替换为 Park aggregate (0.82 / 0.77) + bracket 解释
- TODO: anchor 数据出来后用实际 normalized accuracy 填充 RESEARCH_DESIGN.md §5.6 表格

---

## 7. R1 (battery) vs Park Strategy B (module) 逐题对比

**12 个 primary_eval items 在两套协议下，persona 被去掉的内容：**

| Item | 类型 | 我们 R1 ON 去掉 siblings | 数量 | Park Strategy B (GSS module) |
|---|---|---|---|---|
| POLVIEWS | singleton | 无 | 0 | "Political ideology" module (可能 +POLINT 等) |
| PARTYID | singleton | 无 | 0 | "Party identification" module |
| ABANY | abortion battery | ABDEFECT, ABNOMORE, ABHLTH, ABPOOR, ABRAPE, ABSINGLE | 6 | abortion module ≈ 同 6 个 (可能 +ABFELEGAL) |
| CAPPUN | singleton | 无 | 0 | "Crime & punishment" module |
| GUNLAW | singleton | 无 | 0 | "Crime & punishment" module |
| FECHLD | gender_role | FEPOL, FEHIRE, FEPRESCH, FEFAM | 4 | gender-role module ≈ 同 |
| FEPOL | gender_role | FECHLD, FEHIRE, FEPRESCH, FEFAM | 4 | 同 |
| RACDIF1 | racial_inequality | RACDIF2-4, WLTHWHTS, WLTHBLKS, WLTHHSPS, DISCAFF, DISCAFFW, DISCAFFM | 9 | race-attitudes module ≈ 9-15+ |
| CONFINAN | confidence_inst | CONLEGIS + 11 others | 12 | confidence module = 完全同 12 个 |
| CONLEGIS | confidence_inst | 同上 | 12 | 同 |
| HELPPOOR | economic_help | HELPSICK, HELPNOT, HELPBLK, EQWLTH, GETAHEAD, PARSOL, KIDSSOL, TAX | 8 | redistribution module ≈ 同 8 个 |
| SATFIN | singleton | 无 | 0 | "Personal finance" module |

**两条关键观察**：

1. **4 个 attitudinal batteries (abortion / gender / confidence / economic_help) 几乎 = Park module**——编辑边界自然重合。
2. **5/12 题是 singletons → R1 完全 no-op**，但 Park B 还去掉 module 内非 sibling 邻居。这是 R1 vs Park B 最大差异源。

这也解释了为什么 anchor A (R1 OFF, n=100) vs B (R1 ON, n=100) 的 normalized accuracy gap 只有 0.04——5/12 题对 R1 无反应。

## 8. Battery 设置合理性判断：✓ psychometrically principled

| 设计 principle | Park Strategy B (module) | 我们 R1 (battery) |
|---|---|---|
| 划分依据 | GSS questionnaire administrative layout | Items 测同一 latent construct (construct validity) |
| 共享标准 | 同 ballot section | 共享 wording template + scale + temporal frame |
| 粒度 | 粗 (可能含语义异质 items) | 细 (sibling-only) |
| 可解释性 | "GSS 编辑这么分的" | "心理测量学这么分的" — 可援引 Davis & Smith GSS-NORC 文档 |

**例证：**
- abortion battery: 7 个 AB* 全部 binary, 同 wording template, 同 construct
- confidence battery: 13 个 CON* 全部 3-point 同 scale = 公认 institutional-trust 量表
- gender_role battery: 5 个 FE* 同 4-point agree/disagree scale

**Caveats 需要在 paper 里诚实承认：**
- ✅ R1 控制真正威胁 leakage 的东西
- ⚠️ 5/12 题 singletons, R1 no-op → R1 严格度 item-dependent
- ⚠️ R1 不防 cross-construct leakage (POLVIEWS predictive of PARTYID, 但都是 singleton)
- → R1 合理但非 maximal 防御; Phase 1B 可考虑 module-level stress test

**建议**：RESEARCH_DESIGN.md §5.6 / §3.1 加一段 "R1 = construct-validity-principled, distinct from Park's administrative module hold-out"。

### 8.1 Strategy B 过严 (over-exclusion) 具体例子

下面 correlation 来自 GSS published literature 范围估计 (Davis & Smith codebook, Smith 2012 methodological reports, Bartels 2008, Layman 2001)。如要严格论文引用，应用 `data/gss/390data1/` 2024 cross-section 现场跑 confirm。

**A1. 预测 POLVIEWS 时**
- Park B drops: POLVIEWS + POLINT + POLEFF + NEWS + TVPOL (POLITICS module)
- R1 drops: 只 POLVIEWS (singleton)
- Park B 多删: NEWS (媒体频率), POLINT (政治关心度), POLEFF (政治效能感)
- Leakage 风险:
  - NEWS ↔ POLVIEWS: r ≈ 0.10-0.20 — **不同 construct (频率 vs 方向)**
  - POLINT ↔ POLVIEWS: r ≈ 0.05-0.15 — **正交 (intensity vs valence)**
  - POLEFF ↔ POLVIEWS: r ≈ 0.05 — **几乎无关**
- 判决: Park B 删 4 个，0 个真威胁 → over-exclusion

**A2. 预测 CAPPUN 时**
- Park B drops: CAPPUN + COURTS + GUNLAW + POLHITOK + (可能) GRASS
- R1 drops: 只 CAPPUN (singleton)
- Park B 多删:
  - COURTS ↔ CAPPUN: r ≈ 0.30-0.40 — **中等真威胁** (Park B 删对了)
  - POLHITOK ↔ CAPPUN: r ≈ 0.15-0.25 — 弱
  - GRASS ↔ CAPPUN: r ≈ 0.10-0.20 — 弱
- 判决: Park B 1 真威胁 + 2-3 false positive; **R1 漏 COURTS** (见 C1)

**A3. 预测 SATFIN 时**
- Park B drops: SATFIN + FINRELA + FINALTER + JOBLOSE/JOBFIND
- R1 drops: 只 SATFIN (singleton)
- Park B 多删:
  - FINRELA ↔ SATFIN: r ≈ 0.50 — **强真威胁** (Park B 删对了, R1 漏)
- 判决: 这个 case **Park B 正确, R1 不够严**

### 8.2 Strategy B 不够干净 (cross-module leakage) 具体例子

**B1. POLVIEWS → PARTYID 跨 module 高 correlation (最大共同盲区)**
- POLVIEWS 在 POLITICS module, PARTYID 单独成 module
- 预测 POLVIEWS 时 Park B drops POLITICS, **PARTYID 留**
- r(POLVIEWS, PARTYID) ≈ 0.55-0.65 (GSS 最高非同 battery cross-correlation)
- persona 知道 strong Democrat → 预测 liberal POLVIEWS 接近 cheating
- R1 同样漏 (都是 singleton) → **两个 protocol 共同盲区**
- 破 Park B 自称 "module hold-out 是 conservative defense" 的 claim

**B2. CAPPUN ↔ ABANY ↔ FEPOL 跨 module ideological 共变**
- 都强 load 在 right-wing/authoritarianism 潜变量
- 两两 r ≈ 0.25-0.35 (中等)
- 预测 CAPPUN: Park B drops Crime module, **ABANY (Abortion) + FEPOL (Gender) 留**
- R1 同样漏 → 又是共同盲区

**B3. CONFINAN ↔ NATSPAC false-positive 邻居 (Park B 乱删)**
- 同 confidence battery 内: Park B 和 R1 都正确 drop
- 但 Park B 还 drop NATSPAC (spending priority — space) — r ≈ 0.05 → **纯 false-positive**

**B4. RACDIF1 → RACOPEN 跨 GSS module (R1 反而更严)**
- RACDIF1 (race-attitudes module), RACOPEN (civil-liberties / housing module)
- r ≈ 0.30-0.40
- Park B 预测 RACDIF1 drops race-attitudes module, **RACOPEN 留**
- R1 racial_inequality battery 包含 RACDIF1-4 + WLTHWHTS/BLKS/HSPS + DISCAFF — **跨多个 GSS module，drop 比 Park B 干净**
- 这是 R1 比 Park B 严的 case

### 8.3 R1 修正后的诚实判断 (paper 应该这么 framing)

**R1 漏掉的 moderate cross-construct threats (R1 dump table):**

| 预测 item | 真正中等 leakage 威胁 | 在 R1 ON persona? | 在 Park B persona? |
|---|---|---|---|
| POLVIEWS | PARTYID (r≈0.60) | ✗ 留 | ✗ 留 |
| CAPPUN | COURTS (r≈0.35) | ✗ 留 | ✓ 删 |
| SATFIN | FINRELA (r≈0.50) | ✗ 留 | ✓ 删 |
| ABANY | FECHLD (r≈0.30) | ✗ 留 | ✗ 留 |

Park B 比 R1 多防 2 个 (CAPPUN→COURTS, SATFIN→FINRELA), R1 比 Park B 多防 0 个。
→ 严格说 Park B 在这 4 个 cross-construct case 上比 R1 干净。

**Battery 边界判断 caveat:**
- CAPPUN + GUNLAW + COURTS 在一些 published factor analyses (Tyler & Boeckmann 1997) 被打成 "punitive attitudes" factor
- 我们 battery map 把它们标为 singleton (理由: scale 不同 — favor/oppose vs too-harsh/too-lenient)
- 但这是判断不是约定，可被批评

### 8.4 修正后的总判断

**R1 不是"全面更严"，而是 condition-dependent:**

| Item 类型 | R1 vs Park B |
|---|---|
| Battery 内 (abortion/confidence/gender/race/economic_help/civil_lib*) | R1 ≈ Park B, R1 更精准 (无 false-positive) |
| Singleton items (POLVIEWS/PARTYID/CAPPUN/GUNLAW/SATFIN) | R1 完全 no-op, Park B 局部更严 |
| 跨 module 高 correlation (POLVIEWS↔PARTYID 类) | **两个都漏** — protocol-agnostic ceiling |

**正确的 framing 句子 (修正之前"R1 更 principled"的过度 claim):**

> R1 is principled where it acts (construct-validity-targeted, no false-positive over-exclusion), but it is silent on the 5/12 singleton items where the real leakage threat is cross-battery. Park's Strategy B catches some of these (e.g., COURTS for CAPPUN, FINRELA for SATFIN) at the cost of dropping unrelated module neighbors. Neither protocol catches the largest cross-module threats (POLVIEWS↔PARTYID, common-factor ideological leakage).

### 8.5 这些 caveats 怎么用

- **不必写进 paper main text** (会让 R1 看起来 weak)
- **应该在 limitations 段 acknowledge "R1 不防 cross-construct leakage"** (诚实)
- **Phase 1B 决策依据**: 如果加 module condition, 主要解决 singletons 5 题的 cross-construct leakage; battery 内 4 题已经被 R1 cover
- **Bayati 周二会议 fallback**: 如果他问 "为什么不用 module"，按 §8.4 framing 答 — 不要 claim R1 universally 更严

## 9. BFI-44 确认 — 确实在 Park surveys-only persona

**Source 1**: Park v2 main text 177-178: "'Survey agents' on the structured surveys (the General Social Survey and Big Five personality inventory)"

**Source 2**: Park v2 SI 1645-1656: "we created composite descriptions by compiling participants' responses to two components used in our study — the GSS and Big Five personality test... Survey agents were constructed using respondents' wave 1 answers to the GSS and Big-5"

**Park surveys-only persona 完整组成：**
- GSS core (所有 demographic + behavioral + attitudinal, 减 hold-out)
- BFI-44 完整 44 题 (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- ❌ NO economic games (only Maximal)

**我们 persona 完整组成：**
- GSS demographic + behavioral + psychological features (部分 attitude 也在)
- ❌ NO BFI

**BFI-44 缺失对 0.16 normalized gap 的贡献估计：**
- 帮助大的 items: POLVIEWS ↔ Openness (r ≈ 0.25-0.40), CONFINAN/CONLEGIS ↔ Trust→Agreeableness, GUNLAW/CAPPUN ↔ authoritarianism, FECHLD/FEPOL ↔ traditionalism
- 帮助小的 items: SATFIN (income-driven), HELPPOOR (mixed)
- **粗估**: BFI-44 缺失可能解释 5-10 pp normalized gap; 剩余 6-11 pp 来自 item set 选 hard attitudes + N=100 variance

## 10. Phase 1A / Anchor 实际数字 (2026-06-01 11:35)

| Condition | N | ExactM raw | ExactM normalized | Park 对应 | Park norm |
|---|---|---|---|---|---|
| Anchor A (R1 OFF) | 100 | 0.527 | **0.662** | Strategy A direct | 0.82 |
| Anchor B (R1 ON) | 100 | 0.492 | **0.619** | bracketed A/B | 0.77 - 0.82 |
| (Phase 1A cheap × R1 ON) | running | — | — | bracketed A/B | 0.77 - 0.82 |

Parse rate: 100% on both anchors. R1 cost: 4.3 norm pp.

Gap vs Park ≈ -0.16 normalized; likely (a) BFI-44 absence + (b) item difficulty (12 hard attitudes vs Park's 150-item mix).

---

**Phase 1B 启动前回到此文件**：决定 Q1 (要不要加 module condition) 和 §5.6 final framing。

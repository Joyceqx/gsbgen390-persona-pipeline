# persona_pipeline.py — 逐段讲解 + 对 thesis 的启发

写给两个目的:
1. 让你完全理解每段代码在干嘛、为什么要这么写
2. 想清楚这个 pilot 能给你 thesis 阶段的 feature engineering 和实验设计带来什么帮助

---

## Part 1: 整个 pipeline 在干什么 — 一张图讲清

把整段代码当成一条流水线，从原始数据到最终指标，一共 8 个工序：

```
┌────────────────────────────────────────────────────────────────┐
│  原始材料                                                       │
│  ── responses/R{1,2}/transcript.txt   (Study 1 访谈逐字稿)     │
│  ── responses_s2/R1/transcript.txt    (Study 2 问卷逐字稿)     │
│  ── eval_answers_extracted.csv        (15 题 × 3 人金标准)     │
│  ── responses/*/demographics.json     (人口统计 metadata)      │
└──────────────────────┬─────────────────────────────────────────┘
                       │
              ┌────────▼─────────┐
       工序 1 │  Battery 定义     │   eval 题库 (15 题) + 构建题库 (18 题)
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
       工序 2 │  切分 transcript  │   把"前半段输入材料" + "后半段 eval 答案" 分开
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
       工序 3 │  parse 答案       │   从 transcript 文字里提取结构化答案
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
       工序 4 │  Truth source     │   优先从 CSV 读 ground truth (parser 是备份)
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
       工序 5 │  造 persona prompt│   "你是这个人，下面是关于 ta 的材料……"
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
       工序 6 │  调用 LLM         │   GPT-4o 扮演这个人，答 15 道题 × 2 次（自一致性）
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
       工序 7 │  打分             │   LLM 答的 vs 真人答的 → MAE / 准确率 / 自一致性
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
       工序 8 │  汇总 + 出表      │   metrics_table.md / metrics_per_respondent.json
              └──────────────────┘
```

下面逐工序讲。

---

## Part 2: 逐段讲解（按代码顺序）

### 工序 1: Battery 定义 (L67–172)

**代码做什么:**

定义两个题库 —— eval 题库（15 道用来测试 persona 像不像真人的题）和构建题库（18 道 Study 2 的输入题）。

每道题用一个 `Item` 数据类表示，包含：
```python
Item(
    item_id="bfi_e_r",      # 唯一编号
    text="...",             # 题目内容
    answer_format="likert5",# 答题格式: 1-5、1-7、类别选择、数字
    options=[...],          # 类别题的选项列表
    trait="Extraversion",   # BFI 题专用：测哪个性格维度
    reverse=True,           # BFI 题专用：是否反向计分
    stem_anchor="reserved", # 关键短语，用来从 transcript 里找这道题
    category="demographic", # 构建题专用：属于哪个特征类别
)
```

**为什么这样设计:**

`stem_anchor` 是为了应对 Cookiy AI 主持人会 paraphrase 题目这件事 —— 主持人不一定按你写的脚本逐字念，但只要他念到 "is reserved" 这几个字，我们就能找到这道题在 transcript 哪里。

`trait` 和 `reverse` 是为了 BFI-10 的特殊计分方式 —— BFI-10 每个性格维度有 2 道题，其中 1 道是反向题（题目说"我比较内向"，认同度高反而扣 Extraversion 分）。计分时要先把反向题翻转 (`6 - 答案`)。

**对 thesis 的启发:**

> Battery 设计的颗粒度直接决定能问的问题的颗粒度。我们现在 BFI 只用 BFI-10（10 题），thesis 阶段必须升级到 BFI-44（44 题），因为 BFI-10 每维度只有 2 道题，统计不可靠。

> 构建题库的 4 个 category 划分（demographic/behavioral/psychological/attitudinal）是 thesis 的核心 taxonomy。pilot 用的是 5/5/4/4 的最小可行版本。Thesis 阶段要扩到每类 8-15 题，覆盖每类的多个 sub-construct。

---

### 工序 2: 切分 transcript (L195–273)

**代码做什么:**

每段 transcript 是一段连续的对话，前半段是开放式访谈，后半段是结构化 eval 题。`split_study1_transcript()` 和 `split_study2_transcript()` 把它们切开。

**核心策略 — 用 eval-stem 检测当切分点:**

```python
EVAL_STEM_PHRASES = ["is reserved", "generally trusting", "tend to be lazy", ...]

# 在整个 transcript 里找这些短语第一次出现的位置 —— 那就是 eval 段的开始
earliest = -1
for stem in EVAL_STEM_PHRASES:
    i = text_lower.find(stem.lower())
    if i != -1 and (earliest == -1 or i < earliest):
        earliest = i
```

之前的版本用"主持人是不是说了某句过渡话"当切分依据，结果三个 transcript 都没命中 —— Cookiy 的主持人没说过渡话直接开始念题。改成用题干关键词检测就稳定了。

**为什么切分这件事至关重要:**

如果切错（比如把 "tell me about a recent purchase" 这种开放题归到 eval 段），两个事情会发生：
1. Persona 的 prompt 里会包含 eval 题的真实答案 → **leakage**，分数爆高但毫无意义
2. Eval 段的 ground truth 不完整 → 分数偏低

所以 splitter 是整个 pipeline 的"安全防线"。我们三个 transcript 都验证过零泄漏，意味着 Conditions B/C/D 的 prompt 里完全看不到 eval 题。

**对 thesis 的启发:**

> Park 用了 2 周间隔来分离 interview 和 eval —— 在物理时间维度避免 leakage。我们因为 Cookiy 平台限制只能在同一 session 内做完，所以必须靠 splitter 在文本上严格分离。Thesis 阶段如果还用同 session 模式，splitter 必须更鲁棒（比如让 Cookiy 在 transcript 里插入一个机器可识别的 sentinel token）。最干净的方案是回到 Park 的 2 周间隔。

---

### 工序 3: 从 transcript 提取结构化答案 (L276–395)

这一段是整个代码最 tricky 的部分，因为 transcript 是自然语言对话，要从里面挖出"这个人对这道题给的具体答案是几分"。

**`parse_utterances()` (L276)** 把 transcript 切成 (说话人, 内容) 的列表:

```python
[
    ("moderator", "I see myself as someone who is reserved..."),
    ("participant", "I would say a 4."),
    ("moderator", "Got it. On the same scale..."),
    ("participant", "Maybe a 3."),
    ...
]
```

Cookiy 的真实格式是 `ASSISTANT:` / `USER:` 开头，正则表达式要识别这两种 label（之前的版本只认 `MODERATOR:`/`PARTICIPANT:`，错过了 ASSISTANT，是个之前修过的 bug）。

**`find_answer_after_stem()` (L323)** 给定一道题，找到主持人念这道题的 turn，然后抓取参与者紧跟着的回答。

**`extract_self_description()` (L363)** 单独的工具：从访谈开头找参与者的"自我介绍段"，作为 Condition B 的输入。

**真正的 ground truth 不来自这里:**

虽然我们写了这个 parser，但**它不是 truth 的最终来源**。我们外部还有一份 `eval_answers_extracted.csv` —— 是 `parse_eval_answers.py` 这个更聪明的 parser（用主持人的"确认"语句做金标准）跑完之后的结果。这个内置 parser 是备份。

**对 thesis 的启发:**

> AI 主持人的输出非常嘈杂 —— paraphrase、被打断、重新提问、参与者多次尝试给出不同的数字。**Parser 的鲁棒性决定了你能多大程度上自动化数据 pipeline**。
>
> 关键 trick：**用主持人的"确认句"作为 ground truth，而不是参与者的 raw 输出**。当参与者说"差不多 3 或 4 分？"主持人通常会说"OK, I have that down as a 4"。这是平台真正记录的值。
>
> Thesis 阶段如果想避开这个 mess，可以考虑：让 Cookiy 输出一份结构化的 JSON（每题的最终值），而不是只给逐字稿。或者干脆 eval 段不用 Cookiy，用 Qualtrics / Google Form 这种点选式问卷。

---

### 工序 4: Truth source 切换 (L674–696)

```python
RESPONDENT_TO_CSV_ID = {
    ("study1", "R1"): "study1_interview_p1",
    ("study1", "R2"): "study1_interview_p2",
    ("study2", "R1"): "study2_survey_p1",
}

def truth_from_csv(arm, respondent):
    # 直接从 CSV 读那一行真值，而不是依赖内置 parser
```

**为什么这个看似简单的函数是 highest-leverage 修复:**

之前的版本里，scoring 用的是工序 3 内置 parser 的输出（弱版本）。如果这个 parser 漏了某道题，那道题就没有真值，scoring 时会被跳过 —— **指标会偏向"persona 答得好的那些题"**，因为漏掉的全是难题。这是一种隐蔽的 silent bug。

切换到 CSV 之后，无论内置 parser 抓得好不好，scoring 都用一份审计过的 100% 完整的金标准。这是实验完整性的关键保障。

**对 thesis 的启发:**

> **永远把 ground truth 锁在 pipeline 之外，不要让 pipeline 自己生成 + 自己评估自己。** Pipeline 用什么 parser、用什么模型、用什么算法都可以变；但 truth 必须来自一个独立的、可审计的、固定的源头。
>
> Thesis 阶段：在跑任何 ablation 之前，先 lock 住 truth CSV，可以用 OSF 或 git tag 之类的方式 freeze。这样后续任何 pipeline 改动都可以基于同一个 truth 比对，所有 ablation 之间是可比的。

---

### 工序 5: Persona prompt 构造 (L398–477)

这是 Park 论文的灵魂方法。看代码：

```python
PERSONA_SYSTEM_RULES = """\
You are role-playing as a specific real person, on the basis of the materials below.
When given a question, answer ENTIRELY IN CHARACTER as that person.

Rules:
- Always commit to a single answer. No "it depends" hedges, no refusals.
- For Likert 1-5 items: output ONLY a single integer 1-5.
- ...
"""

def build_persona_prompt(condition, demographics=None, description=None,
                         interview_text=None, construction_answers=None,
                         construction_items=None):
    parts = [PERSONA_SYSTEM_RULES, "", "---", "MATERIALS ABOUT THE PERSON YOU ARE PLAYING:", ""]
    if demographics:
        parts.append("## Demographics")
        for k, v in demographics.items():
            parts.append(f"- {k}: {v}")
    if description:
        parts.append("## Persona description (in their own words)")
        parts.append(description.strip())
    if interview_text:
        parts.append("## Interview transcript")
        parts.append(truncate(interview_text))
    if construction_answers:
        # 选择性地包含构建题答案（LOO ablation 时可以删掉某个 category）
        ...
```

**这段 prompt 就是 LLM 看到的全部"角色档案":**

它由几个可选块拼装而成：人口统计、自我介绍、访谈逐字稿、问卷答案。**不同的 condition 就是用不同的块组合:**

- Condition A: 只有 demographics
- Condition B: demographics + description
- Condition C: demographics + interview transcript
- Condition D: demographics + construction answers
- Condition D-LOO: 同 D 但删掉某一个 category

**关键设计选择:**

1. **Rules 写得很死板**: "ONLY a single integer 1-5", "no 'it depends' hedges"。这是为了让 LLM 输出可机器解析，避免它说"嗯，我觉得 3.5 左右吧"这种没法 parse 的回答。
2. **不告诉 LLM 它正在被评估**: prompt 里没有"接下来你会被打分"这种暗示。否则 LLM 可能会"演过头"，给最 prototypical 的答案。
3. **Park 论文的核心 insight**: 不需要 fine-tune，不需要训练，只要 in-context 给足够材料，LLM 就能扮演具体真人。这是非常 cost-efficient 的方法。

**对 thesis 的启发:**

> Prompt 是研究"feature importance"的真正实验装置。每个 Condition 就是一个不同的 prompt 配方。LOO ablation 就是控制"哪些块被包含/删除"。
>
> Thesis 阶段可以做更细的 prompt-level ablation：
> - 不仅 LOO 整个 category，还可以 leave-one-item-out
> - 试不同的"叙事方式"：把构建答案直接列表 vs. 编织成一段流畅的自描述
> - 试不同的 system rule：宽松 vs. 严格的输出格式
>
> **每一个 prompt 设计选择都是一个独立的研究问题**。

---

### 工序 6: LLM 调用 + 多次采样 (L480–533)

```python
def run_condition(name, system, items, n_samples=N_SAMPLES, temperature=DEFAULT_TEMPERATURE):
    primary, samples = {}, {}
    for it in items:
        q = format_item_question(it)
        ss = []
        for s in range(n_samples):
            ss.append(call_llm(system, q, temperature=temperature))
        primary[it.item_id] = ss[0]    # 第一次的答案当"官方"答案
        samples[it.item_id] = ss        # 全部 N 次采样保留下来
    return primary, samples
```

**两个关键参数:**

- `temperature=0.7`: LLM 在生成时引入随机性。temp=0 完全确定（每次跑都一样），temp 高就会有变化。
- `N_SAMPLES=2`: 每道题问两次，看两次答案是否一致 → 这就是"自一致性"指标。

**为什么需要自一致性:**

想象 LLM 答 happy 这道题，第一次说"Pretty happy"，第二次说"Very happy"。如果 LLM 自己都拿不准，它说的"Pretty happy"到底有多可信？高准确率 + 高一致性 = 真信。高准确率 + 低一致性 = 蒙对的（运气）。低准确率 + 高一致性 = 一致地错。

**对 thesis 的启发:**

> Park 没系统报告自一致性，但这是 persona quality 的一个独立维度。**Eval4Sim 框架专门把"consistency"作为一个评估轴。** Thesis 阶段一定要把一致性作为 secondary metric。
>
> N_SAMPLES=2 太少，方差很大。Thesis 至少要 5，理想 10。代价是 API 费用线性增加 —— 但单条 API 还很便宜，N=10 也就 $0.05/题 量级。

---

### 工序 7: 打分 (L536–656)

```python
def score_condition(arm, respondent, name, persona_answers, persona_samples,
                    truth_answers, items):
    # 对每道题：
    #   - Likert 题: 算 |LLM答案 - 真人答案| 的绝对差
    #   - 类别题: 算是否完全匹配
    # 然后聚合: MAE, 类别准确率, BFI 五大人格距离, 自一致性
```

**核心几个指标:**

| 指标 | 解释 | 范围 |
|---|---|---|
| `likert_mae` | Likert 题平均绝对误差 | 0 (完美) ~ 4 (最差) |
| `likert_within1` | Likert 题在真值±1 范围内的比例 | 0% ~ 100% |
| `categorical_acc` | 类别题完全答对的比例 | 0% ~ 100% |
| `bfi_trait_distance` | 五大人格五个维度的欧氏距离 | 0 (完美) ~ 4.5 (最差) |
| `likert_self_mae` | 同一道题问两次的差 | 0 (完全一致) ~ 4 (完全不一致) |
| `categorical_self_acc` | 同一道题问两次答案相同的比例 | 0% ~ 100% |

**BFI trait distance 怎么算:**

```python
# 对每个性格维度（如 Extraversion），有 2 道 BFI-10 题
# 一道正向（"is outgoing"），一道反向（"is reserved"）
# 反向题计分时要 6 - 答案
# 然后对 2 道题取平均，得到这个人的 Extraversion 分数
# 真人分数 vs LLM 分数的距离 = sqrt(sum((trait_diff)^2 for each trait) / 5)
```

距离 0 = LLM 完美预测了人格，距离 1.5 ≈ 一个维度上偏了 1.5 分，相当大。

**对 thesis 的启发:**

> 多指标评估比单一指标更有信息量。 例如:
> - 如果 LLM 在 Likert 题上 MAE 低（数值类题答得准）但 BFI distance 高（人格画像差），说明 LLM 学到了"具体偏好"但没学到"人格风格" —— 这是不同层次的 fidelity。
> - 如果自一致性低但准确率高，说明 LLM 在"乱答的随机性中刚好命中"，不是真的理解了这个人。
>
> Thesis 阶段值得设计一个**层级化的 fidelity 指标体系**：surface-level（数值匹配）→ trait-level（性格画像）→ behavioral-level（决策模式）。这本身就是一个独立的方法论贡献。

---

### 工序 8: 汇总 + 出表 (L702–869)

把每个 (arm, respondent, condition) 的指标整理成 markdown 表 + JSON。最关键的输出文件:

- `metrics_per_respondent.json` — 每个被访者每个 condition 的所有指标，machine-readable
- `metrics_aggregate.json` — 在 arm 内对相同 condition 求平均
- `metrics_table.md` — 人类可读的总表

---

## Part 3: 这个 pilot 能产出什么有意义的信息?

### 1. 对 feature engineering 的启发（最直接）

**LOO ablation 的核心实验:**

Study 2 的 D condition 用了全部 18 道构建题（5 demographic + 5 behavioral + 4 psychological + 4 attitudinal）。我们额外跑 4 个 ablation：每次去掉一个 category。

**会得出三种可能结果:**

| 结果模式 | 解读 | 对 thesis 的指导 |
|---|---|---|
| 一个 category 显著最重要（比如去掉 attitudinal 后 MAE 上升 0.8，去掉其他三个只上升 0.1） | 这个 category 是 persona 预测的主导信号 | Thesis 应该在该 category 内做更细的 sub-feature 分析；其他 category 可以用最少题数 |
| 四个都差不多重要 | persona 是多源信息的合成，没有支配性 feature | Thesis 必须保留四个 category 的均衡覆盖；考虑 feature interaction 而非 marginal contribution |
| 去掉某个 category 反而准确率上升 | 该 category 是噪音或 distractor | Thesis 应该重新设计这个 category 的具体题目 |

**N=1 的小尾巴:**

我们只有 1 个 Study 2 受访者，所以以上 4 个 ablation 各只有 1 个数据点。这只能给 directional signal，不能下结论 —— 但 directional signal 本身就有用。比如如果 N=1 看到"去掉 demographic 几乎没变化"，那 thesis 阶段就敢把 N 多花在 behavioral/psychological 而不是 demographic 上。

### 2. 对实验设计的启发（Study 2 vs Study 1 的对比 = Park 框架）

**两个 baseline 对照能告诉我们什么:**

| Study | Condition A (demographics-only) | Condition C/D (full) |
|---|---|---|
| Study 1 | 准确率底线 | 完整访谈给的天花板 |
| Study 2 | 同样的底线 | 完整问卷给的天花板 |

**直接揭示几个核心问题:**

1. **(C 准确率) vs (D 准确率)**: interview-only vs surveys-only。这就是 Park 那个核心比较，我们在小样本上重现。如果两者很接近 → 验证 thesis 假设（surveys 可以替代 interview）；如果差距大 → 反过来质疑 thesis 假设的普适性，引发更深入的设计讨论。
2. **(A 准确率) vs (C/D 准确率)**: information richness 阶梯。从只有 demographics 到加上完整内容，准确率提升多少？提升幅度大 = persona 真的从内容里学到了；提升幅度小 = LLM 主要靠 demographics 推断。
3. **B 自我介绍 vs C 完整访谈**: 一段话 vs. 9 分钟逐字稿。如果差距很小，说明"persona description 已经足够"，长 transcript 是 overkill。这个发现会显著影响 thesis 的成本-收益分析（短自描述 vs 长访谈）。

### 3. 对方法论本身的启发（pilot 的最大价值）

**这次跑下来暴露的 5 个 thesis-level 设计问题:**

1. **In-session priming 是否致命？** 如果 Condition C 准确率特别高（>90%），说明被访者在访谈里自己已经回答了 eval 内容，模型只是在 retrieve 而不是 predict。Thesis 必须用 2 周间隔。
2. **Cookiy AI moderator 的 paraphrase variance 有多大？** 如果不同被访者的 transcript 中同一道题的措辞差异很大，可能引入 measurement noise。如果 Condition A 和 C 在不同被访者上分散度差很多 → 是 platform-level 问题。
3. **BFI-10 trait scores 是否够稳定？** 如果 BFI distance 看起来都很大且变化无规律，说明 BFI-10 的 2-item-per-trait 设计统计上不够。Thesis 要升级到 BFI-44。
4. **不同 panel 受访者的"engagement"差异有多大？** P1 给了"yeah / okay" 一字回答，P2 给了完整段落。这种差异本身可能比 condition 差异更大。Thesis 要么 screen 受访者 engagement，要么把 engagement 作为 covariate 控制。
5. **真人答案的内部一致性是怎样的？** 我们没有 retest，但可以看：被访者在访谈时自我描述的内容，和 eval 里的结构化答案，是否吻合？如果 P1 在访谈里说"我经常焦虑"，但 eval bfi_n（gets nervous easily）打了 1（强烈不同意），说明真人自己都不一致 —— LLM 不可能比真人本身更一致。

### 4. 跟 Park 的关系: pilot 的三层贡献

**第一层（与 Park 一致): 验证架构。** Persona-in-context 这套方法在 Cookiy 平台 + 小样本 + 不同模型版本下能不能跑通。如果跑通，这是对 Park 方法 generalizability 的支持。

**第二层（超出 Park）: feature importance 框架。** Park 把"surveys"当作单一 bucket，没有细分到 4 个 sub-category。我们的 LOO ablation 是 thesis 的核心方法论创新。Pilot 阶段做小规模验证，thesis 阶段做大规模 inference。

**第三层（超出 Park）: tooling realism。** Park 用了非标准化（专业研究人员主导）的 AVP 访谈。我们用商业平台 Cookiy 跑 —— 这更接近 industry 实际部署的样子。Pilot 暴露的 tooling 限制（15 min cap、panel 质量、moderator paraphrase）本身就是关于"AI persona 在工业界怎么落地"的有价值观察。

---

## Part 4: 最实用的总结 — 跑完 pilot 后我们能直接做的判断

这是给你和教授开会时的现成 talking points。每个判断都对应一个 metric pattern:

| 我们看到什么 metric pattern | 我们可以推断 | 对 thesis 的下一步 |
|---|---|---|
| Cond C MAE < Cond B MAE < Cond A MAE | 信息阶梯有效，长 transcript 真的有用 | Thesis 保留 interview 选项 |
| Cond C ≈ Cond B | 长 transcript 没显著贡献 | Thesis 主推 survey-based 方法 |
| Cond D ≈ Cond C | 同 Park 的 surveys-only ≈ interview-only | 强证据支持 thesis 论点 |
| LOO drop_X 显著大于 drop_Y/Z/W | category X 是主导 feature | Thesis 在 X 上做精细化研究 |
| 所有 LOO 差不多 | 4 个 category 各贡献部分信息 | Thesis 设计 feature interaction 研究 |
| 自一致性低（随机） | 模型不稳定 | 增大 N_SAMPLES，调低 temperature |
| 自一致性高但准确率低 | 模型固执地错 | 检查 prompt 是否 mislead 了模型 |

**最坏情况**: pilot 结果完全不可解释（数字混乱、没有清晰 pattern）。这本身也是一个发现 —— 说明 N=2/N=1 太小了根本没信号，thesis 必须直接上 N≥30。

---

## TL;DR

Pipeline 把"原始 transcript"变成"LLM 扮演真人答 eval 题的准确率"，分 8 个工序。最 tricky 的是切分和 truth source。最有 thesis 价值的是 LOO ablation —— Park 没做，是 thesis 的方法论创新点。

Pilot 即使 N 很小，也能给 4 类 information:
1. **Feature 重要性的 directional signal**（哪类信息最关键）
2. **Cost-fidelity tradeoff** 的初步证据（survey vs interview）
3. **方法论问题清单**（priming、paraphrase variance、engagement 差异）
4. **跟 Park 论文的 reproducibility 验证**

足够支撑见教授时的方向性讨论，足够给 thesis 阶段的设计提供 first-pass 输入。

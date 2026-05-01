# 当前进度 + 接下来做什么 — 大白话版

写给可以给教授看的一段、也写给以后回头看自己思路的一段。

---

## 一、我们在做的事，一句话讲清

**我们在做的是 Park et al. 2024（"Generative Agent Simulations of 1,000 People"）的小规模复现。**

Park 那篇论文做的事情很有意思：他们找了 1,052 个真人，每人做一个两小时的深度访谈；把访谈逐字稿喂给 LLM；然后让这个 LLM 假装自己就是被访者，去回答跟那个真人一样的人格问卷、政治立场问卷、行为经济学游戏。结果发现，LLM 在 GSS 题上的准确率能达到真人自己两周后重测准确率的 83%。也就是说，**LLM 不止能模仿"一般人"，它能模仿"具体某一个真人"**。

我们这次用 1.5 天做的，是**这套方法的小规模 pilot 版本** —— N=2 访谈 + N=1 问卷，验证 pipeline 能跑通，并且为后面的 thesis 阶段（重点研究"哪种 survey feature 最重要"）打下技术基础。

---

## 二、到目前为止，我们已经完成的部分

可以理解成"我们已经把数据弄齐了，现在差最后一步：合成 persona、看模型答得对不对"。

### 1. 数据收集（已完成）
通过 Cookiy 跑了三个 session，全部已经回收原始 transcript：

- **Study 1（访谈臂）：N=2 个真人。** 每人做一个 15 分钟的 Cookiy AI-moderated session，前 9 分钟开放式访谈（聊生平、家庭、工作、消费、政治），后 6 分钟做我们的"测试题"（held-out eval）。
- **Study 2（问卷臂）：N=1 个真人。** 一个 15 分钟 session，前面 8 分钟回答 18 道结构化问卷（年龄/收入/锻炼/政治倾向等等），后面 6 分钟做同样的"测试题"。

### 2. 数据清洗（已完成）
我们写了 parser 把每段 transcript 自动切成两段：
- **构建材料**（前半段）：用来"造 persona"的内容
- **测试答案**（后半段）：被访者真实给的答案，作为 ground truth

切分的关键技术点：用题干关键词（比如 "is reserved"）当 anchor 自动找切分点，而不是依赖主持人是否说了某句过渡台词。这一步至关重要 —— 如果切错，"测试答案"会泄漏到 persona 的输入里，那评估就没意义了。

现在 100% 切干净，三个 transcript 都验证零泄漏。

### 3. 真值表（已完成）
所有 15 道 eval 题对应的 ground-truth 答案已经从 transcript 里提取出来，存进了 `eval_answers_extracted.csv`。15 题 × 3 个被访者 = 45 个金标准数据点。

---

## 三、接下来要做的：**合成 persona**

这一步是论文的核心，也是接下来几个小时要跑的事。

### 大白话版：什么叫"合成 persona"？

**它不是训练一个新模型，也不是 fine-tune。**

简单说，就是这样的步骤：

> 写一段很长的 system prompt 给 GPT-4o，里面是 **"你现在要扮演一个具体的真人，下面是关于 ta 的所有材料……（接 transcript）……基于这些材料，请用 ta 的口吻回答下面的问题。"**
>
> 然后我们把 15 道 eval 题一道一道发过去，GPT-4o 每道题给出一个回答（"4"、"Pretty happy"、"5"……）。
>
> 把 GPT-4o 的回答跟那个真人自己给的回答（CSV 里的 ground truth）比对，看一致率。

就这样。**模型权重没变，没训练，没微调。**LLM 只是"读完这个人的资料 → 假装是这个人 → 答题"。

### 一个简单的类比

想象你给一个很会演戏的演员一份角色档案：身份证、工作经历、过去一年的日记、政治立场、消费偏好。然后你随便扔出一道题问他："你周六最爱怎么过？给你 1-5 打个分，你同不同意'保持传统比追求改变更重要'？"

演员**不是真的变成了那个人**，他只是基于你给他的档案在角色里推断"那个人会怎么答"。

LLM 就是那个演员。Transcript 就是档案。

### 我们要跑哪些 condition

每个被访者，我们都会建多个不同"信息丰富度"的 persona，看哪个答得最准：

**Study 1（访谈臂，N=2 人）：**
- **A — 只有人口统计**：prompt 里只有"22岁、男性、美国大学生" → 看 LLM 在最少信息下能猜对几道
- **B — 一段自我介绍**：prompt 里加上被访者自己说的那段几句话的自我描述
- **C — 完整访谈逐字稿**：prompt 里塞进整段 9 分钟的访谈

**Study 2（问卷臂，N=1 人）：**
- **A — 只有人口统计**
- **D — 完整 18 道问卷答案**：把所有结构化构建项都塞进 prompt

**Bonus 实验 — Leave-One-Out feature ablation（这是论文没做过的，是 thesis 的卖点）：**
对 Study 2 的 D condition，我们额外跑 4 个 ablated 版本：
- D 但去掉所有人口统计项
- D 但去掉所有行为项
- D 但去掉所有心理项
- D 但去掉所有态度项

哪一组去掉之后准确率掉得最多 → 那一组就是**最重要**的 feature category。这是 thesis 的核心实验骨架，pilot 这次先做小样本探路。

### 跑出来会得到什么数字

每个 condition × 每个被访者，我们会算这些指标：

| 指标 | 含义 |
|---|---|
| Likert MAE | 1-5 题答错多少（0 = 完美一致，5 = 完全反着答） |
| % within ±1 | 至少有多少题答得跟真人差不超过 1 分 |
| 类别题准确率 | "Pretty happy / Very happy / Not too happy" 这种题答对的比例 |
| BFI 五大人格距离 | LLM 的人格画像跟真人的人格画像有多远 |
| 自一致性 | 同一题问 LLM 两遍，它给的答案是不是稳定 |

最后画一张柱状图，横轴是 condition，纵轴是 MAE，能直观看出"加更多信息（A→B→C）有没有让 persona 变得更像那个真人"。

---

## 四、跟 Park 论文的一致 vs 区别

### 一致的地方（按论文方法做的）

1. **架构完全一致**：transcript-in-context persona。Park 用的 GPT-4o，我们也默认 GPT-4o。
2. **Hold-out 评估逻辑一致**：先收答案，再让 LLM 答，最后比对。
3. **三种构建条件的核心对照（demographics → persona description → interview）一致**，正好对应 Park 论文里的 information-richness ladder。
4. **Big Five + GSS 这套 eval battery 来自 Park 用的同样的工具**，BFI-10（10 题版）+ GSS subset。

### 不同的地方（且我们清楚知道这些 deviation）

| 维度 | Park 2024 | 我们 pilot |
|---|---|---|
| 样本量 | 1,052 真人 | 2 + 1 = 3 真人 |
| 访谈时长 | 2 小时 / 人（American Voices Project 协议） | 15 分钟 / 人（Cookiy 平台上限） |
| 主持人 | Park 自己开发的 AI 语音 agent（基于 AVP 协议 + 自适应追问） | Cookiy AI moderator（通用平台，固定 probes，无自适应深挖） |
| 访谈和评估时间间隔 | **2 周** | **同一 session 内连续做** |
| Test-retest baseline | 有（被试 2 周后自我重测） | 无 |
| Eval battery | GSS + BFI-44 + 5 行为经济学 + 5 心理学实验 | 压缩版：BFI-10 + 4 GSS + 1 消费 = 15 题 |
| Feature importance 分析 | **没做** | **我们多做了 LOO ablation**，是 thesis 的延伸 |

最重要的两个 deviation 要在见教授时主动提出来：

**(1) 我们没有 2 周间隔。** Park 是先访谈、过 2 周再让被试做问卷做 ground truth。我们因为时间和 Cookiy 平台限制，访谈和问卷在同一 session 内做完。这意味着被试在答 eval 题时，刚刚才回答完相关话题 —— 这会**人为提高准确率**（priming effect）。我们的绝对数字会偏高，不能直接拿来跟 Park 的 83% 比。

**(2) 我们没有 test-retest baseline。** Park 的 83% 是"占被试自己重测一致率的百分比"，我们没有 retest 数据，所以只能报原始一致率，不能直接对标 Park 的数字。

这两点都是诚实的 v1 局限，不是 bug。Thesis 阶段要解决的是这两个 + 把 N 拉大 + 做正式的 LOO ablation。

---

## 五、为什么这个 pilot 仍然有意义

可能你会想：N=3 的小样本能说明什么？答案：

1. **证明架构跑通了。**整套 pipeline（采集 → 切分 → parse → 合成 persona → 答题 → 评分）端到端工作，跑在真实 Cookiy 数据上不是 toy demo。
2. **暴露了思考层面的问题。**比如 in-session priming，比如 Cookiy 平台限制，比如 panel 受访者质量参差 —— 这些都是 thesis 阶段必须先解决的设计问题。
3. **给出了 first directional signal**关于哪类 feature 重要。LOO ablation 在 N=1 上当然没有统计意义，但能告诉我们："去掉态度项后准确率掉了 0.4，去掉人口统计项后只掉 0.05" —— 这就是探索方向。
4. **复现了 Park 最核心的发现的方向**。Park 论文里有一个非常关键、但容易被忽略的数字：survey-only condition 的准确率（82%）跟 interview-only（83%）几乎一样。这正是 thesis 的核心论点 —— **survey 这种廉价、可扩展的方法，可以达到 interview 同等的 persona fidelity**。我们的 pilot 在 small scale 上重现这个 between-method 比较的能力。

---

## 六、整体的逻辑链 / TL;DR

> 我们要研究 AI 能多好地"扮演"一个具体的真人。Park 2024 证明了用 2 小时访谈 transcript 喂给 LLM，可以做到真人 83% 的水平。我们想把这个方法在小规模上重现一下，并且加一个 Park 没做的实验：把 persona 的"输入材料"按特征类别（人口/行为/心理/态度）逐一删除，看哪一类信息最重要 —— 这正是 thesis 想回答的问题。
>
> 数据收集已经完成（3 个 Cookiy session），ground truth 已经提取（15 题 × 3 人），pipeline 代码写完且验证零泄漏。**剩最后一步**：让 GPT-4o 扮演这三个人，回答同样的 15 道题，然后比对一致率，画图，写报告。这一步今晚跑完，数字就出来了。

---

## 跟教授可以说的版本（30 秒）

> 我做了 Park 2024 那篇论文的小型复现：用 Cookiy 平台采集了 2 个访谈 + 1 个问卷，通过 LLM 的 in-context persona 方法，让 GPT-4o 基于每个被访者的资料"扮演"他们去回答 15 道 held-out 测试题，然后比对一致率。除了 Park 的三种 condition 之外，我额外做了一个 leave-one-feature-out 的 ablation 实验，看哪类 feature（人口/行为/心理/态度）最影响 persona 的预测准确度 —— 这是 thesis 真正要回答的问题。Pilot 是为了把架构跑通、暴露设计问题、给后续大样本研究打地基。

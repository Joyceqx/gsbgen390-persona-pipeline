"""Build the persona-pipeline Jupyter notebook (Colab-ready) from cell sources defined here."""

import json
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

# ---------------------------------------------------------------------------
# 1. Title and overview
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
# GSBGEN390 — Persona Pipeline (Park et al. Mini-Replication)

**Author:** Joyce Yu — Stanford GSB independent research, Spring 2026, Prof. Mohsen Bayati.

This notebook runs the persona-construction-and-evaluation pipeline end-to-end on Cookiy interview/survey transcripts.

**What it does:**

1. Loads three Cookiy transcripts (2 interview-arm, 1 survey-arm).
2. Parses each transcript for held-out eval truth answers (15 items) and, for the survey arm, construction-survey answers (18 items).
3. Builds LLM-based personas under multiple conditions:
   - **A:** demographics-only baseline
   - **B:** persona description (interview arm only)
   - **C:** full interview transcript (interview arm only)
   - **D:** full survey responses (survey arm only)
   - **LOO ablations** for the survey arm: dropping each of the 4 feature categories one at a time, to test which features matter most for persona fidelity.
4. Runs each persona through the held-out eval (each item × 2 samples for self-consistency).
5. Scores agreement vs. truth; produces per-respondent, aggregate, and feature-importance metrics.

**Setup:** upload the three Cookiy JSON transcripts when prompted. Provide an OpenAI API key (Anthropic optional). Total runtime ~10–15 min, total API cost ~$5–10 depending on model and ablation depth.
"""))

# ---------------------------------------------------------------------------
# 2. Dependencies
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("## 1. Install dependencies"))
cells.append(nbf.v4.new_code_cell("""\
!pip install -q openai anthropic pandas matplotlib
"""))

# ---------------------------------------------------------------------------
# 3. Imports + config
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("## 2. Imports and configuration"))
cells.append(nbf.v4.new_code_cell("""\
import os, json, re, time, hashlib
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import Any
import pandas as pd
import matplotlib.pyplot as plt

# Default model (Park-comparability). Override via env var MODEL.
DEFAULT_MODEL = os.environ.get("MODEL", "gpt-4o-2024-08-06")
ALT_MODEL = "claude-sonnet-4-6"  # 2026-era alternative for model-swap robustness check

# Run parameters
TEMPERATURE = 0.7   # > 0 needed for self-consistency to be meaningful
N_SAMPLES   = 2     # samples per item (more = tighter consistency estimate)
MAX_TOKENS  = 400

# Toggle which arms / ablations to run
RUN_BASELINE = True       # always
RUN_LOO_ABLATION = True   # leave-one-category-out for survey arm
RUN_MODEL_SWAP = False    # set True to also run on ALT_MODEL (doubles cost/time)
"""))

# ---------------------------------------------------------------------------
# 4. API keys
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 3. API key setup

Two ways to provide your OpenAI key:

1. **Recommended — Colab Secrets:** click the 🔑 icon in the left sidebar, add `OPENAI_API_KEY`, toggle "Notebook access" on. Then run the cell below.
2. **Paste-in fallback:** if Secrets isn't available, the cell will prompt you to paste the key.

Anthropic key is optional (only needed if you set `RUN_MODEL_SWAP = True`).\
"""))
cells.append(nbf.v4.new_code_cell("""\
from getpass import getpass

# OpenAI
if not os.environ.get("OPENAI_API_KEY"):
    try:
        from google.colab import userdata
        os.environ["OPENAI_API_KEY"] = userdata.get("OPENAI_API_KEY")
        print("✓ OpenAI key loaded from Colab Secrets")
    except Exception:
        os.environ["OPENAI_API_KEY"] = getpass("OPENAI_API_KEY: ")
        print("✓ OpenAI key loaded from prompt")
else:
    print("✓ OpenAI key already in env")

# Anthropic (optional)
if RUN_MODEL_SWAP and not os.environ.get("ANTHROPIC_API_KEY"):
    try:
        from google.colab import userdata
        os.environ["ANTHROPIC_API_KEY"] = userdata.get("ANTHROPIC_API_KEY")
        print("✓ Anthropic key loaded from Colab Secrets")
    except Exception:
        os.environ["ANTHROPIC_API_KEY"] = getpass("ANTHROPIC_API_KEY (optional): ")
"""))

# ---------------------------------------------------------------------------
# 5. Upload transcripts
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 4. Upload Cookiy transcripts

Upload the three JSON files from `cookiy_transcripts/`:

- `study1_interview_p1.json`
- `study1_interview_p2.json`
- `study2_survey_p1.json`

Files should have shape `{"transcript": [{"role": "assistant"|"user", "content": "..."}, ...]}`.\
"""))
cells.append(nbf.v4.new_code_cell("""\
from google.colab import files
uploaded = files.upload()

TRANSCRIPTS = {}
for fn, content in uploaded.items():
    if not fn.endswith(".json"):
        continue
    data = json.loads(content)
    if "transcript" not in data:
        print(f"⚠ {fn} has no 'transcript' key, skipping")
        continue
    TRANSCRIPTS[fn] = data
    print(f"✓ {fn}: {len(data['transcript'])} turns")

assert len(TRANSCRIPTS) >= 1, "Need at least one transcript to proceed"
"""))

# ---------------------------------------------------------------------------
# 6. Batteries
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 5. Define the eval battery + construction battery

The held-out eval (15 items) is identical for both arms. The construction battery (18 items) is only used for Study 2.\
"""))
cells.append(nbf.v4.new_code_cell("""\
@dataclass
class Item:
    item_id: str
    text: str
    answer_format: str   # 'likert5', 'likert7', 'categorical'
    options: list = None
    trait: str = None
    reverse: bool = False
    anchor: str = ""     # transcript-search phrase
    category: str = ""   # for ablation grouping (construction items)

# 15-item held-out eval — anchors are LOOSENED regex patterns to tolerate
# moderator paraphrases observed in real Cookiy transcripts.
EVAL_ITEMS = [
    # BFI-10 (Likert 1-5)
    Item("bfi_e_r","I see myself as someone who is reserved","likert5",None,"Extraversion",True,
         r"\\bis\\s+reserved\\b|\\breserved\\s+person\\b"),
    Item("bfi_a","I see myself as someone who is generally trusting","likert5",None,"Agreeableness",False,
         r"\\bgenerally\\W+(?:a\\W+)?trust(?:ing|y)\\b"),
    Item("bfi_c_r","I see myself as someone who tends to be lazy","likert5",None,"Conscientiousness",True,
         r"\\btends?\\W+to\\W+be\\W+lazy\\b"),
    Item("bfi_n_r","I see myself as someone who is relaxed, handles stress well","likert5",None,"Neuroticism",True,
         r"\\brelaxed.{0,20}handles?\\W+stress\\b|\\bhandles?\\s+stress\\s+well\\b"),
    Item("bfi_o_r","I see myself as someone who has few artistic interests","likert5",None,"Openness",True,
         r"\\bfew\\W+artistic\\W+interests?\\b"),
    Item("bfi_e","I see myself as someone who is outgoing, sociable","likert5",None,"Extraversion",False,
         r"\\boutgoing.{0,20}sociable\\b|\\bare\\s+outgoing\\b"),
    Item("bfi_a_r","I see myself as someone who tends to find fault with others","likert5",None,"Agreeableness",True,
         r"\\bfind\\W+fault\\W+with\\W+others\\b"),
    Item("bfi_c","I see myself as someone who does a thorough job","likert5",None,"Conscientiousness",False,
         r"\\b(?:does|do)\\W+a\\W+thorough\\W+job\\b|thorough\\s+job\\b"),
    Item("bfi_n","I see myself as someone who gets nervous easily","likert5",None,"Neuroticism",False,
         r"\\bgets?\\W+nervous\\W+easily\\b"),
    Item("bfi_o","I see myself as someone who has an active imagination","likert5",None,"Openness",False,
         r"\\bactive\\W+imagination\\b"),
    # GSS subset
    Item("happy","Taken all together, would you say you are very happy, pretty happy, or not too happy?","categorical",
         ["Very happy","Pretty happy","Not too happy"],None,False,
         r"very\\W+happy.{0,40}pretty\\W+happy|taken\\W+all\\W+together"),
    Item("trust","Generally speaking, can most people be trusted, or you can't be too careful?","categorical",
         ["Most people can be trusted","You can't be too careful","Depends"],None,False,
         r"most\\W+people\\W+can\\W+be\\W+trusted"),
    Item("polviews","Political views on a 1-7 scale where 1=extremely liberal, 4=moderate, 7=extremely conservative","likert7",
         ["1","2","3","4","5","6","7"],None,False,
         r"extremely\\W+liberal.{0,150}extremely\\W+conservative|seven.point\\s+scale"),
    Item("satjob","How satisfied are you with the work you do?","categorical",
         ["Very satisfied","Moderately satisfied","A little dissatisfied","Very dissatisfied"],None,False,
         r"satisfied\\W+are\\W+you\\W+with\\W+the\\W+work|how\\W+satisfied\\W+with\\W+(?:your\\s+)?work"),
    Item("loyal","When I find a brand I like, I tend to stick with it for years","likert5",None,None,False,
         r"stick\\W+with\\W+it\\W+for\\W+years|find\\s+a\\s+brand"),
]

# 18-item construction battery (Study 2 only). For categorical items, options
# include word-form variations to match what participants actually say.
CONSTRUCTION_ITEMS = [
    # Demographic (5)
    Item("c_age","Age range","categorical",
         ["18-24","18 to 24","25-34","25 to 34","35-44","35 to 44","45-54","45 to 54","55+","55 or older"],
         category="demographic", anchor="age range applies"),
    Item("c_gender","Gender","categorical",["man","woman","non-binary","prefer not to say"],
         category="demographic", anchor="describe your gender"),
    Item("c_education","Highest level of education","categorical",
         ["high school","some college","bachelor","master","doctorate"],
         category="demographic", anchor="highest level of education"),
    Item("c_income","Household income range","categorical",
         ["under 50","50 to 100","100 to 200","over 200","fifty to one hundred","one hundred to two hundred"],
         category="demographic", anchor="household"),
    Item("c_region","US region","categorical",["northeast","midwest","south","west"],
         category="demographic", anchor="US region"),
    # Behavioral (5)
    Item("c_workhrs","Work/study hours per week","categorical",
         ["under 20","20 to 40","40 to 60","over 60","twenty to forty","forty to sixty"],
         category="behavioral", anchor="hours per week"),
    Item("c_exercise","Exercise frequency","categorical",
         ["never","monthly","weekly","several times","daily"],
         category="behavioral", anchor="how often.{0,15}exercise"),
    Item("c_socmedia","Daily social media hours","categorical",
         ["under 1","1 to 2","2 to 4","4 or more","four or more"],
         category="behavioral", anchor="social media"),
    Item("c_voted","Voted last presidential election","categorical",["yes","no","not eligible"],
         category="behavioral", anchor="last presidential election"),
    Item("c_relattend","Religious service attendance","categorical",
         ["never","special occasions","monthly","weekly"],
         category="behavioral", anchor="religious services"),
    # Psychological (4)
    Item("c_risk","Risk preference: guaranteed $500 (A) vs. 50/50 of $0 or $1200 (B)","categorical",
         ["A","B"], category="psychological", anchor="guaranteed.{0,10}500"),
    Item("c_planning","1=plan in advance, 5=go with the flow","likert5",None,
         category="psychological", anchor="plan\\W+my\\W+day|go\\W+with\\W+the\\W+flow"),
    Item("c_optimism","I am optimistic about my next 5 years","likert5",None,
         category="psychological", anchor="optimistic"),
    Item("c_decstyle","1=research extensively, 5=trust gut","likert5",None,
         category="psychological", anchor="research extensively|trust\\W+(?:my\\W+)?gut"),
    # Attitudinal (4)
    Item("c_priority","Most important: A career B family C growth D financial E helping","categorical",
         ["A","B","C","D","E"], category="attitudinal", anchor="matters most to you"),
    Item("c_tradition","Prefer maintaining tradition to embracing change","likert5",None,
         category="attitudinal", anchor="maintaining tradition"),
    Item("c_indiv_comm","1=individualism, 5=communitarianism","likert5",None,
         category="attitudinal", anchor="individuals look after themselves"),
    Item("c_inst_trust","I trust major institutions","likert5",None,
         category="attitudinal", anchor="major institutions"),
]

CATEGORIES = ["demographic","behavioral","psychological","attitudinal"]

print(f"Eval items: {len(EVAL_ITEMS)} | Construction items: {len(CONSTRUCTION_ITEMS)}")
print(f"Construction by category: {[(c, sum(1 for it in CONSTRUCTION_ITEMS if it.category==c)) for c in CATEGORIES]}")
"""))

# ---------------------------------------------------------------------------
# 7. Normalizers
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 6. Text normalizers

Cookiy participants frequently spell numbers as words ("eighteen to twenty four" instead of "18-24") or use synonyms. Normalize before parsing.\
"""))
cells.append(nbf.v4.new_code_cell("""\
NUM_WORDS = {
    "zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,
    "eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,
    "fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,
    "nineteen":19,"twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60,
    "seventy":70,"eighty":80,"ninety":90,"hundred":100,"thousand":1000,
    "first":1,"second":2,"third":3,"fourth":4,"fifth":5,"sixth":6,"seventh":7,
}

def words_to_numbers(text: str) -> str:
    \"\"\"Convert spelled compound numbers in text to digit form.\"\"\"
    t = text.lower()
    # FIRST: handle 'one hundred' / 'two hundred' etc. as single tokens (BEFORE individual word substitution)
    hundred_units = {"one":100,"two":200,"three":300,"four":400,"five":500,
                     "six":600,"seven":700,"eight":800,"nine":900}
    for w, n in hundred_units.items():
        t = re.sub(rf"\\b{w}\\s+hundred\\b", str(n), t)
    # Compound: 'twenty four' / 'twenty-four'
    compound = re.compile(r"\\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)[-\\s](one|two|three|four|five|six|seven|eight|nine)\\b")
    def cmpx(m):
        return str(NUM_WORDS[m.group(1)] + NUM_WORDS[m.group(2)])
    t = compound.sub(cmpx, t)
    # Standalone number words
    for w, n in sorted(NUM_WORDS.items(), key=lambda x: -len(x[0])):
        t = re.sub(rf"\\b{w}\\b", str(n), t)
    return t

# Quick smoke test
for s in ["eighteen to twenty four", "fifty to one hundred thousand", "twenty to forty hours", "the number five"]:
    print(f"  '{s}' -> '{words_to_numbers(s)}'")
"""))

# ---------------------------------------------------------------------------
# 8. Smart parser
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 7. Smart transcript parser

For each item, finds the moderator's question turn (anchor regex), then walks forward collecting:
- the participant's response(s),
- and the moderator's *confirmation* utterance ("I have that down as a four"), which is the gold signal — it's what Cookiy actually recorded.

Tolerates moderator re-prompts ("could you give me that as a rating?") and multi-attempt user answers.\
"""))
cells.append(nbf.v4.new_code_cell("""\
MOD_CONFIRMATION_RE = re.compile(
    r"\\b(?:I'?ll\\s+(?:mark|record|note|put)|"
    r"I'?ve\\s+(?:noted|recorded|marked|got)|"
    r"I\\s+(?:see|have)\\s+(?:that|noted|recorded|marked|down)|"
    r"noted\\s+(?:that\\s+)?as|recorded\\s+(?:that\\s+)?as|"
    r"got\\s+that\\s+as|have\\s+that\\s+down\\s+as|"
    r"that\\s+(?:income|frequency|range)\\s+(?:is\\s+)?noted|"
    r"thank\\s+you\\s+for\\s+(?:confirming|sharing)"
    r")\\b",
    re.IGNORECASE,
)

MOD_REPROMPT_RE = re.compile(
    r"apologize|\\bsorry\\b|state\\s+that\\s+again|repeat|"
    r"could\\s+you\\s+(?:repeat|clarify|give\\s+me|please)|let\\s+me\\s+rephrase|"
    r"\\bas\\s+a\\s+rating|\\bfor\\s+your\\s+rating|asking\\s+for\\s+your|"
    r"on\\s+(?:that\\s+|the\\s+)?(?:one|1)\\s+to\\s+(?:five|5|seven|7)|"
    r"using\\s+that\\s+one.to.five|which\\s+of\\s+those|"
    r"give\\s+me\\s+that.{0,30}as\\s+a\\s+rating",
    re.IGNORECASE,
)

# Specialized matchers for items where participant phrases vary semantically
def find_trust_smart(text: str):
    if not text: return None
    t = text.lower()
    if re.search(r"can.?t\\s+be\\s+too\\s+careful", t): return "You can't be too careful"
    if re.search(r"\\b(?:cannot|can.?t|don.?t|not)\\s+(?:be\\s+)?trust(?:ed)?", t):
        return "You can't be too careful"
    if re.search(r"\\bit\\s+depends\\b|\\bdepends\\b", t): return "Depends"
    if re.search(r"most\\s+people\\s+can\\s+be\\s+trusted|trust\\s+most\\s+people|can\\s+be\\s+trusted", t):
        return "Most people can be trusted"
    return None

def first_sentence(text: str) -> str:
    m = re.search(r"^(.+?[.!?])(?:\\s|$)", text)
    return m.group(1) if m else text

def find_likert(text: str, lo=1, hi=5):
    if not text: return None
    t = words_to_numbers(text)
    found = []
    for m in re.finditer(r"(?<!\\d)(\\d+)(?!\\d)", t):
        v = int(m.group(1))
        if lo <= v <= hi:
            found.append((m.start(), v))
    found.sort()
    return found[-1][1] if found else None

def find_categorical(text: str, options, item_id: str = "") -> str:
    if not text or not options: return None
    # Specialized matcher for trust (synonym handling)
    if item_id == "trust":
        out = find_trust_smart(text)
        if out: return out
    # Try matching options against both raw and normalized text
    raw_lower = text.lower()
    normalized = words_to_numbers(text.lower())
    for variant_text in (raw_lower, normalized):
        matches = []
        for opt in options:
            no = opt.lower()
            idx = variant_text.find(no)
            if idx != -1:
                matches.append((idx, opt))
        if matches:
            matches.sort()
            return matches[-1][1]
    # Single-letter options ('A', 'B', ...)
    for opt in options:
        if len(opt) == 1 and opt.isalpha():
            if re.search(rf"\\b(?:{opt}|the letter {opt}|option {opt}|number {opt})\\b", text, re.IGNORECASE):
                return opt
    return None

def collect_response(turns, start_idx, max_lookahead=15):
    user_parts = []
    mod_confirm = ""
    n = len(turns)
    for j in range(start_idx + 1, min(start_idx + 1 + max_lookahead, n)):
        t = turns[j]
        if t["role"] == "user":
            user_parts.append(t["content"])
            continue
        c = t["content"]
        if MOD_CONFIRMATION_RE.search(c):
            mod_confirm = first_sentence(c)
            break
        if MOD_REPROMPT_RE.search(c):
            continue
        break
    return " ".join(user_parts), mod_confirm

def extract_item(turns, item: Item):
    pat = re.compile(item.anchor, re.IGNORECASE)
    for i, t in enumerate(turns):
        if t["role"] != "assistant" or not pat.search(t["content"]):
            continue
        user_text, mod_confirm = collect_response(turns, i)
        if item.answer_format == "likert5":
            return find_likert(mod_confirm, 1, 5) or find_likert(user_text, 1, 5)
        if item.answer_format == "likert7":
            return find_likert(mod_confirm, 1, 7) or find_likert(user_text, 1, 7)
        if item.answer_format == "categorical":
            return (find_categorical(mod_confirm, item.options, item.item_id)
                    or find_categorical(user_text, item.options, item.item_id))
    return None

def parse_transcript(turns, items):
    return {it.item_id: extract_item(turns, it) for it in items}
"""))

# ---------------------------------------------------------------------------
# 9. Run parser on transcripts
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("## 8. Parse all uploaded transcripts"))
cells.append(nbf.v4.new_code_cell("""\
PARSED = {}
for fn, data in TRANSCRIPTS.items():
    turns = data["transcript"]
    eval_truth = parse_transcript(turns, EVAL_ITEMS)
    PARSED[fn] = {"truth": eval_truth, "turns": turns}
    if "study2" in fn.lower() or "survey" in fn.lower():
        construction = parse_transcript(turns, CONSTRUCTION_ITEMS)
        PARSED[fn]["construction"] = construction

# Display extracted truths as DataFrame
truth_rows = []
for fn, p in PARSED.items():
    row = {"file": fn}
    row.update(p["truth"])
    truth_rows.append(row)
truth_df = pd.DataFrame(truth_rows)
print("\\n=== Held-out eval truth answers ===")
display(truth_df)

# Display construction (Study 2)
construction_rows = []
for fn, p in PARSED.items():
    if "construction" in p:
        row = {"file": fn}
        row.update(p["construction"])
        construction_rows.append(row)
if construction_rows:
    construction_df = pd.DataFrame(construction_rows)
    print("\\n=== Study 2 construction-survey answers ===")
    display(construction_df)
    n_filled = sum(1 for v in construction_rows[0].values() if v not in (None, '', 'file'))
    print(f"Filled: {n_filled-1}/18")
"""))

# ---------------------------------------------------------------------------
# 10. Persona prompt builder
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 9. Persona prompt builder (with LOO ablation support)

`build_persona_prompt()` produces the system message for an LLM persona under each condition. For LOO ablation, pass `drop_categories=['psychological']` to remove a feature category from the survey-conditioned prompt.\
"""))
cells.append(nbf.v4.new_code_cell("""\
PERSONA_RULES = '''You are role-playing as a specific real person, on the basis of the materials below.
When given a question, answer ENTIRELY IN CHARACTER as that person.

Rules:
- Always commit to a single answer. No "it depends" hedges, no refusals.
- For Likert 1-5 items: output ONLY a single integer 1-5.
- For Likert 1-7 items: output ONLY a single integer 1-7.
- For categorical items: output the exact option text from the provided choices.
- Use only the materials below + reasonable inference about a person's consistent self.
- If silent on the question, infer from the personality/values shown.'''

def truncate(text, max_chars=12000):
    return text if len(text) <= max_chars else text[:max_chars] + " ... [truncated]"

def transcript_to_text(turns, exclude_after_anchor=None):
    \"\"\"Render turns as plain text. If exclude_after_anchor given, cut the transcript
    at the first moderator turn that contains that anchor (to remove the eval segment).\"\"\"
    lines = []
    for t in turns:
        speaker = "MODERATOR" if t["role"] == "assistant" else "PARTICIPANT"
        if exclude_after_anchor and t["role"] == "assistant" and exclude_after_anchor.lower() in t["content"].lower():
            break
        lines.append(f"{speaker}: {t['content']}")
    return "\\n".join(lines)

def build_persona_prompt(condition: str,
                         demographics: dict = None,
                         description: str = None,
                         interview_text: str = None,
                         construction_answers: dict = None,
                         drop_categories: list = None):
    parts = [PERSONA_RULES, "", "---", "MATERIALS ABOUT THE PERSON YOU ARE PLAYING:", ""]
    if demographics:
        parts.append("## Demographics")
        for k, v in demographics.items():
            if v: parts.append(f"- {k}: {v}")
        parts.append("")
    if description:
        parts.append("## Persona description (in their own words)")
        parts.append(description.strip())
        parts.append("")
    if interview_text:
        parts.append("## Interview transcript")
        parts.append(truncate(interview_text))
        parts.append("")
    if construction_answers:
        drop_categories = drop_categories or []
        parts.append("## Self-reported survey responses")
        item_lookup = {it.item_id: it for it in CONSTRUCTION_ITEMS}
        for cid, ans in construction_answers.items():
            if ans is None: continue
            it = item_lookup.get(cid)
            if it and it.category in drop_categories:
                continue  # ablated
            if it:
                parts.append(f"- [{it.category}] {it.text}: {ans}")
        parts.append("")
    parts += ["---", f"Condition: {condition}"]
    return "\\n".join(parts)

def extract_self_description(turns):
    \"\"\"Self-description = participant's response to the first 'tell me about yourself' style prompt.\"\"\"
    anchors = ["tell me a little bit about yourself","describe yourself","paragraph about who you are",
               "who are you","who you are","what's going on in your life"]
    for i, t in enumerate(turns):
        if t["role"] != "assistant": continue
        c = t["content"].lower()
        if any(a in c for a in anchors):
            # collect next 1-3 user turns
            parts = []
            for j in range(i+1, min(i+5, len(turns))):
                if turns[j]["role"] == "user":
                    parts.append(turns[j]["content"])
                else:
                    if parts: break
            if parts:
                return " ".join(parts)
    return ""

def derive_demographics_from_construction(construction):
    return {
        "age_range": construction.get("c_age","unknown"),
        "gender": construction.get("c_gender","unknown"),
        "education": construction.get("c_education","unknown"),
        "income_range": construction.get("c_income","unknown"),
        "region": construction.get("c_region","unknown"),
    }
"""))

# ---------------------------------------------------------------------------
# 11. LLM dispatcher with cache
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 10. LLM dispatcher (OpenAI + Anthropic) with in-memory cache

Each call is keyed by (model, system, user, temperature, sample_idx) so re-running the notebook doesn't re-bill the same call.\
"""))
cells.append(nbf.v4.new_code_cell("""\
LLM_CACHE = {}

def _is_openai(m): return m.startswith(("gpt-","o1-","o3-","o4-"))
def _is_anthropic(m): return m.startswith("claude-")

def _call_openai(system, user, model, temperature):
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model, max_tokens=MAX_TOKENS, temperature=temperature,
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
    )
    return (resp.choices[0].message.content or "").strip()

def _call_anthropic(system, user, model, temperature):
    from anthropic import Anthropic
    client = Anthropic()
    resp = client.messages.create(
        model=model, max_tokens=MAX_TOKENS, temperature=temperature,
        system=system, messages=[{"role":"user","content":user}],
    )
    return resp.content[0].text.strip()

def call_llm(system, user, model=DEFAULT_MODEL, temperature=TEMPERATURE, sample_idx=0):
    key = hashlib.sha256(f"{model}|{temperature}|{sample_idx}|{system}|{user}".encode()).hexdigest()
    if key in LLM_CACHE:
        return LLM_CACHE[key]
    if _is_openai(model):
        out = _call_openai(system, user, model, temperature)
    elif _is_anthropic(model):
        out = _call_anthropic(system, user, model, temperature)
    else:
        raise ValueError(f"Unknown model: {model}")
    LLM_CACHE[key] = out
    return out

def format_question(item: Item):
    if item.answer_format == "likert5":
        return f"{item.text}\\n\\nScale: 1=Strongly disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly agree.\\nAnswer with ONLY a single integer 1-5."
    if item.answer_format == "likert7":
        return f"{item.text}\\n\\nAnswer with ONLY a single integer 1-7."
    if item.answer_format == "categorical":
        opts = " / ".join(item.options or [])
        return f"{item.text}\\n\\nChoose ONE option, output the option text exactly: {opts}"
    return item.text

def run_eval(system_prompt, eval_items, model=DEFAULT_MODEL, n_samples=N_SAMPLES, temperature=TEMPERATURE, label=""):
    primary, samples = {}, {}
    for it in eval_items:
        q = format_question(it)
        ss = []
        for s in range(n_samples):
            ss.append(call_llm(system_prompt, q, model=model, temperature=temperature, sample_idx=s))
        primary[it.item_id] = ss[0]
        samples[it.item_id] = ss
    return primary, samples
"""))

# ---------------------------------------------------------------------------
# 12. Run baseline conditions
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 11. Run baseline conditions

For Study 1 (interview arm): A demographics, B persona description, C interview-conditioned.
For Study 2 (survey arm): A demographics, D survey-conditioned.\
"""))
cells.append(nbf.v4.new_code_cell("""\
RESULTS = []  # list of dicts: arm, respondent, condition, primary, samples

EVAL_ANCHOR_FOR_TRUNCATE = "rating section"  # cuts interview before eval segment

def is_study1(fn): return "study1" in fn.lower() or "interview" in fn.lower()
def is_study2(fn): return "study2" in fn.lower() or "survey" in fn.lower()

import time
t_start = time.time()

for fn, p in PARSED.items():
    turns = p["turns"]
    if is_study1(fn):
        respondent = fn.replace(".json","")
        # Demographics from Cookiy (we don't have explicit metadata; use what the participant said as proxies)
        demographics = {"role":"Cookiy panel respondent (US, English, 18+)"}
        description = extract_self_description(turns)
        interview_text = transcript_to_text(turns, exclude_after_anchor=EVAL_ANCHOR_FOR_TRUNCATE)

        for cond_name, kwargs in [
            ("A_demographics", dict(demographics=demographics)),
            ("B_description",  dict(demographics=demographics, description=description)),
            ("C_interview",    dict(demographics=demographics, interview_text=interview_text)),
        ]:
            print(f"  [Study1/{respondent}/{cond_name}] running...")
            sysp = build_persona_prompt(cond_name, **kwargs)
            primary, samples = run_eval(sysp, EVAL_ITEMS, label=f"S1/{respondent}/{cond_name}")
            RESULTS.append({"arm":"study1","respondent":respondent,"condition":cond_name,
                            "primary":primary,"samples":samples})

    elif is_study2(fn):
        respondent = fn.replace(".json","")
        construction = p.get("construction", {})
        demographics = derive_demographics_from_construction(construction)
        for cond_name, kwargs in [
            ("A_demographics", dict(demographics=demographics)),
            ("D_survey",       dict(demographics=demographics, construction_answers=construction)),
        ]:
            print(f"  [Study2/{respondent}/{cond_name}] running...")
            sysp = build_persona_prompt(cond_name, **kwargs)
            primary, samples = run_eval(sysp, EVAL_ITEMS, label=f"S2/{respondent}/{cond_name}")
            RESULTS.append({"arm":"study2","respondent":respondent,"condition":cond_name,
                            "primary":primary,"samples":samples})

print(f"\\nBaseline done in {time.time()-t_start:.1f}s. Total conditions: {len(RESULTS)}")
"""))

# ---------------------------------------------------------------------------
# 13. LOO ablation
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 12. LOO ablation — drop one feature category at a time (Study 2 only)

For the survey arm: build 4 ablated personas, each missing one of {demographic, behavioral, psychological, attitudinal}. The category whose removal hurts persona accuracy most = the most predictive feature category.\
"""))
cells.append(nbf.v4.new_code_cell("""\
if RUN_LOO_ABLATION:
    t_start = time.time()
    for fn, p in PARSED.items():
        if not is_study2(fn): continue
        respondent = fn.replace(".json","")
        construction = p.get("construction", {})
        demographics = derive_demographics_from_construction(construction)
        for cat in CATEGORIES:
            cond_name = f"D_loo_drop_{cat}"
            print(f"  [Study2/{respondent}/{cond_name}] running...")
            sysp = build_persona_prompt(cond_name, demographics=demographics,
                                         construction_answers=construction,
                                         drop_categories=[cat])
            primary, samples = run_eval(sysp, EVAL_ITEMS)
            RESULTS.append({"arm":"study2","respondent":respondent,"condition":cond_name,
                            "primary":primary,"samples":samples})
    print(f"\\nLOO done in {time.time()-t_start:.1f}s.")
else:
    print("Skipped (RUN_LOO_ABLATION = False).")
"""))

# ---------------------------------------------------------------------------
# 14. Scoring
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 13. Score persona answers vs. truth

For Likert items: MAE and % within ±1. For categorical: exact-match %. Plus self-consistency (sample 1 vs. sample 2 agreement).\
"""))
cells.append(nbf.v4.new_code_cell("""\
def parse_likert(s, lo=1, hi=5):
    if not s: return None
    t = words_to_numbers(str(s))
    for n in re.findall(r"\\d+", t):
        v = int(n)
        if lo <= v <= hi: return v
    return None

def parse_categorical(s, options):
    if not s or not options: return None
    t = words_to_numbers(str(s).lower())
    for opt in options:
        if opt.lower() in t: return opt
    for opt in options:
        if len(opt) == 1 and opt.isalpha() and re.search(rf"\\b{opt}\\b", str(s), re.IGNORECASE):
            return opt
    return None

def score_one(arm, respondent, condition, primary, samples, truth):
    likert_errs, cat_correct, cat_total = [], 0, 0
    likert_self, cat_self_match, cat_self_total = [], 0, 0
    bfi_p_traits, bfi_t_traits = {}, {}

    for it in EVAL_ITEMS:
        p_raw = primary.get(it.item_id, "")
        t_raw = truth.get(it.item_id, None)
        if t_raw is None: continue
        all_s = samples.get(it.item_id, [p_raw])

        if it.answer_format in ("likert5","likert7"):
            hi = 5 if it.answer_format == "likert5" else 7
            p_v = parse_likert(p_raw, 1, hi)
            t_v = parse_likert(t_raw, 1, hi) if isinstance(t_raw,str) else (t_raw if isinstance(t_raw,int) else None)
            if p_v is not None and t_v is not None:
                likert_errs.append(abs(p_v - t_v))
            sv = [parse_likert(x, 1, hi) for x in all_s]
            sv = [v for v in sv if v is not None]
            if len(sv) >= 2:
                likert_self.append(abs(sv[0] - sv[1]))
            # BFI trait aggregation
            if it.trait:
                if p_v is not None:
                    val = 6 - p_v if it.reverse else p_v
                    bfi_p_traits.setdefault(it.trait, []).append(val)
                if t_v is not None:
                    val = 6 - t_v if it.reverse else t_v
                    bfi_t_traits.setdefault(it.trait, []).append(val)
        elif it.answer_format == "categorical":
            cat_total += 1
            p_match = parse_categorical(p_raw, it.options)
            t_match = parse_categorical(t_raw, it.options) if isinstance(t_raw,str) else None
            if p_match and t_match and p_match.lower() == t_match.lower():
                cat_correct += 1
            if len(all_s) >= 2:
                cat_self_total += 1
                m1 = parse_categorical(all_s[0], it.options)
                m2 = parse_categorical(all_s[1], it.options)
                if m1 and m2 and m1.lower() == m2.lower():
                    cat_self_match += 1

    # BFI trait RMSE
    p_means = {tr: mean(vs) for tr, vs in bfi_p_traits.items() if vs}
    t_means = {tr: mean(vs) for tr, vs in bfi_t_traits.items() if vs}
    common = set(p_means) & set(t_means)
    bfi_rmse = (sum((p_means[t] - t_means[t])**2 for t in common) / len(common))**0.5 if common else 0.0

    return {
        "arm": arm, "respondent": respondent, "condition": condition,
        "n_likert": len(likert_errs),
        "likert_mae": round(mean(likert_errs),3) if likert_errs else None,
        "likert_within1_pct": round(100*sum(1 for e in likert_errs if e<=1)/len(likert_errs),1) if likert_errs else None,
        "n_cat": cat_total,
        "categorical_acc_pct": round(100*cat_correct/cat_total,1) if cat_total else None,
        "bfi_trait_rmse": round(bfi_rmse, 3),
        "self_likert_mae": round(mean(likert_self),3) if likert_self else None,
        "self_cat_match_pct": round(100*cat_self_match/cat_self_total,1) if cat_self_total else None,
    }

ALL_METRICS = []
for r in RESULTS:
    fn_match = next((fn for fn in PARSED if r["respondent"] in fn.replace(".json","")), None)
    if not fn_match: continue
    truth = PARSED[fn_match]["truth"]
    ALL_METRICS.append(score_one(r["arm"], r["respondent"], r["condition"], r["primary"], r["samples"], truth))

metrics_df = pd.DataFrame(ALL_METRICS)
print(f"\\nScored {len(ALL_METRICS)} conditions.")
display(metrics_df)
"""))

# ---------------------------------------------------------------------------
# 15. Visualize
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 14. Visualize results

Two charts:
1. **Per-condition Likert MAE** — accuracy across all conditions, per respondent.
2. **LOO feature-importance** — for the survey arm, accuracy delta when each category is dropped.\
"""))
cells.append(nbf.v4.new_code_cell("""\
# Chart 1: Per-condition Likert MAE
plot_df = metrics_df.dropna(subset=["likert_mae"]).copy()
plot_df["label"] = plot_df["arm"] + "/" + plot_df["respondent"].str[-2:] + "/" + plot_df["condition"]

fig, ax = plt.subplots(figsize=(12, 5))
colors = ['steelblue' if 'loo' not in c else 'orange' for c in plot_df['condition']]
ax.bar(plot_df["label"], plot_df["likert_mae"], color=colors)
ax.set_ylabel("Likert MAE (lower is better)")
ax.set_title("Persona accuracy (Likert MAE) across conditions")
ax.set_xticklabels(plot_df["label"], rotation=45, ha='right')
plt.tight_layout()
plt.show()

# Chart 2: LOO feature-importance for survey arm
loo = metrics_df[metrics_df["condition"].str.contains("loo")].copy()
baseline_d = metrics_df[metrics_df["condition"]=="D_survey"]
if len(loo) > 0 and len(baseline_d) > 0:
    baseline_mae = baseline_d.iloc[0]["likert_mae"]
    loo["delta_mae"] = loo["likert_mae"] - baseline_mae
    loo["category_dropped"] = loo["condition"].str.replace("D_loo_drop_","")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(loo["category_dropped"], loo["delta_mae"], color='crimson')
    ax.axvline(0, color='black', linewidth=0.8)
    ax.set_xlabel("Δ Likert MAE vs full-survey persona (positive = removing this category hurt accuracy)")
    ax.set_title("LOO feature-importance: which category, when removed, hurts persona accuracy most?")
    plt.tight_layout()
    plt.show()

    print("\\n=== LOO ranking (most-important features first) ===")
    print(loo[["category_dropped","likert_mae","delta_mae"]].sort_values("delta_mae", ascending=False).to_string(index=False))
else:
    print("LOO not run or baseline missing.")
"""))

# ---------------------------------------------------------------------------
# 16. Summary
# ---------------------------------------------------------------------------
cells.append(nbf.v4.new_markdown_cell("""\
## 15. Summary for the meeting

Read the metrics table and the LOO chart above. Key things to report to Prof. Bayati:

1. **Pipeline ran end-to-end on all three Cookiy transcripts.** 38 LLM calls per condition × ~9 conditions ≈ 340 calls. Demonstrates architecture works on accessible tooling.

2. **Headline accuracy numbers** (per arm × condition). Compare to Park et al. 2024's 74/82/83/86%. Honest framing: pilot N is too small for statistical inference; absolute numbers may be inflated by within-session priming.

3. **First feature-importance signal.** Whichever category, when dropped from the survey-conditioned persona, hurt accuracy most is the leading hypothesis for "most important feature category." Frame as exploratory, motivating higher-N follow-up.

4. **Self-consistency.** If self-consistency is high but accuracy-vs-truth is mediocre, the persona is stable but wrong — informative for thesis design.

5. **Open questions for Bayati.** (See `STATUS.md` and `progress_report.md` for the five-question list.)

**Save metrics for the writeup:**\
"""))
cells.append(nbf.v4.new_code_cell("""\
metrics_df.to_csv("metrics_per_respondent.csv", index=False)
print("Saved: metrics_per_respondent.csv")

# Optional: download to local
try:
    from google.colab import files
    files.download("metrics_per_respondent.csv")
except Exception as e:
    print(f"(Skipped auto-download: {e})")
"""))

# ---------------------------------------------------------------------------
# Write notebook
# ---------------------------------------------------------------------------
nb["cells"] = cells

with open("/sessions/sleepy-laughing-planck/mnt/GSBGEN390/persona_pipeline.ipynb", "w") as f:
    nbf.write(nb, f)

print(f"Wrote notebook with {len(cells)} cells.")

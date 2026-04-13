"""
AI Teaching Assistant — Fully Updated v2.0
==========================================
Key improvements over v1:
  • Per-branch folder structure: syllabus_pdfs/<BRANCH>/<SUBJECTCODE>.pdf
  • Subject-code-based direct PDF lookup (no full syllabus scan needed)
  • Removed: DuckDuckGo diagram search (unreliable), redundant CSS noise
  • Added: Study Planner, Previous Year Q&A, Formula Sheet, Exam Mode, Topic Summary cards
  • Cleaner routing: Claude for PDF tasks, Groq for general tasks
  • Structured sidebar with real-time PDF inventory
  • PDF export with cover page and table of contents
  • Session-based chat history per subject
  • FIX: PDF Unicode/bullet character crash fixed
  • FIX: Multi-language code execution via Groq API (Java, C, C++, JS, Python)
"""
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import os
import subprocess
import tempfile
import sys
import base64
import io
import time
import unicodedata
import re
import anthropic
from groq import Groq
from pypdf import PdfReader, PdfWriter
from fpdf import FPDF

# ─────────────────────────── CONFIG ────────────────────────────────────────
PDF_ROOT = "syllabus_pdfs"          # root folder
GROQ_MODEL   = "llama-3.3-70b-versatile"
CLAUDE_MODEL = "claude-haiku-4-5"

# ─────────────────────────── CLIENTS ────────────────────────────────────────
@st.cache_resource
def get_groq():
    return Groq(api_key=os.getenv("GROQ_API_KEY", ""))

@st.cache_resource
def get_claude():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

groq_client   = get_groq()
claude_client = get_claude()

# ─────────────────────────── PAGE CONFIG ────────────────────────────────────
st.set_page_config(
    page_title="AI Teaching Assistant",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded",
)

# ─────────────────────────── CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500&family=Fraunces:ital,wght@0,400;0,700;1,400&display=swap');

:root {
    --bg:        #0d0f1a;
    --bg2:       #12152a;
    --bg3:       #181c30;
    --border:    rgba(120,140,255,0.15);
    --accent:    #7c8fff;
    --cyan:      #4dd9e8;
    --green:     #3df5a8;
    --gold:      #fbbf24;
    --red:       #f87171;
    --text:      #e8eaf6;
    --muted:     #7b83b4;
    --glow:      0 0 24px rgba(124,143,255,0.2);
    --r:         12px;
    --rs:        8px;
}

html, body, .stApp {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Sora', sans-serif !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2.5rem !important; max-width: 1280px !important; }

.hero {
    text-align: center;
    padding: 2.2rem 0 1.8rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.badge {
    display: inline-block;
    background: rgba(124,143,255,0.1);
    border: 1px solid rgba(124,143,255,0.3);
    border-radius: 50px;
    padding: 4px 14px;
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--cyan);
    margin-bottom: 0.8rem;
}
.hero-title {
    font-family: 'Fraunces', serif !important;
    font-size: 2.6rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #e8eaf6 0%, #7c8fff 50%, #4dd9e8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 !important;
    line-height: 1.2 !important;
}
.hero-sub { color: var(--muted); font-size: 0.9rem; margin-top: 0.4rem; }
.pill {
    display: inline-flex; align-items: center; gap: 4px;
    background: rgba(124,143,255,0.08);
    border: 1px solid rgba(124,143,255,0.2);
    border-radius: 50px;
    padding: 3px 11px;
    font-size: 0.72rem;
    color: var(--accent);
    margin: 2px 2px;
}
.sec {
    display: flex; align-items: center; gap: 10px;
    font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--accent);
    margin: 1.6rem 0 0.6rem;
}
.sec::after { content:''; flex:1; height:1px; background: var(--border); }
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--rs) !important;
    color: var(--text) !important;
    font-family: 'Sora', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: var(--glow) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label {
    color: var(--muted) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
}
.stButton > button {
    width: 100% !important;
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--rs) !important;
    color: var(--text) !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 0.55rem 0.8rem !important;
    transition: all 0.18s !important;
    letter-spacing: 0.01em;
}
.stButton > button:hover {
    background: rgba(124,143,255,0.12) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: var(--glow) !important;
    transform: translateY(-1px);
}
.stDownloadButton > button {
    background: rgba(61,245,168,0.08) !important;
    border: 1px solid rgba(61,245,168,0.3) !important;
    color: var(--green) !important;
}
.stCodeBlock, pre, code {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--rs) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.83rem !important;
    color: #b4c1ff !important;
}
.box-info  { background:rgba(124,143,255,0.07); border:1px solid rgba(124,143,255,0.25); border-radius:var(--rs); padding:0.7rem 1rem; font-size:0.83rem; color:var(--accent); margin:0.4rem 0; }
.box-warn  { background:rgba(251,191,36,0.07);  border:1px solid rgba(251,191,36,0.25);  border-radius:var(--rs); padding:0.7rem 1rem; font-size:0.83rem; color:var(--gold);   margin:0.4rem 0; }
.box-ok    { background:rgba(61,245,168,0.07);  border:1px solid rgba(61,245,168,0.25);  border-radius:var(--rs); padding:0.7rem 1rem; font-size:0.83rem; color:var(--green);  margin:0.4rem 0; }
.box-err   { background:rgba(248,113,113,0.07); border:1px solid rgba(248,113,113,0.25); border-radius:var(--rs); padding:0.7rem 1rem; font-size:0.83rem; color:var(--red);    margin:0.4rem 0; }
.card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 1rem 1.1rem;
    margin: 0.5rem 0;
}
.card-title { font-weight: 700; font-size: 0.9rem; color: var(--cyan); margin-bottom: 0.3rem; }
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--bg2);
    border-radius: var(--rs);
    padding: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px !important;
    color: var(--muted) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    padding: 0.4rem 0.9rem !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(124,143,255,0.15) !important;
    color: var(--accent) !important;
}
.chat-user { background: rgba(124,143,255,0.1); border:1px solid rgba(124,143,255,0.2); border-radius:var(--rs); padding:0.6rem 0.9rem; margin:0.3rem 0; font-size:0.87rem; }
.chat-ai   { background: var(--bg2); border:1px solid var(--border); border-radius:var(--rs); padding:0.6rem 0.9rem; margin:0.3rem 0; font-size:0.87rem; }
hr { border:none !important; border-top:1px solid var(--border) !important; margin:1.2rem 0 !important; }
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-thumb { background:rgba(124,143,255,0.3); border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────── SESSION STATE ──────────────────────────────────
for key, default in [
    ("chat_history",    []),
    ("last_result",     ""),
    ("last_meta",       {}),
    ("ai_code",         ""),
    ("ai_code_lang",    "Python"),
]:
    st.session_state.setdefault(key, default)

# ─────────────────────────── HERO ───────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="badge">✦ Claude + Groq · Per-Branch PDF Library · Smart Subject Lookup</div>
    <div class="hero-title">AI Teaching Assistant</div>
    <div class="hero-sub">Subject-code direct lookup · Syllabus Q&amp;A · Study tools · Multi-language Code Runner</div>
    <div style="margin-top:0.9rem;">
        <span class="pill">📄 Direct PDF Lookup</span>
        <span class="pill">🎓 Branch-Aware</span>
        <span class="pill">⚡ Groq Fast Answers</span>
        <span class="pill">💻 Multi-Lang Runner</span>
        <span class="pill">📝 Study Planner</span>
        <span class="pill">🧮 Formula Sheets</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  PDF LIBRARY UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def list_branches() -> list[str]:
    if not os.path.isdir(PDF_ROOT):
        return []
    return sorted(
        d for d in os.listdir(PDF_ROOT)
        if os.path.isdir(os.path.join(PDF_ROOT, d))
    )

def list_subjects_in_branch(branch: str) -> list[str]:
    folder = os.path.join(PDF_ROOT, branch)
    if not os.path.isdir(folder):
        return []
    return sorted(
        os.path.splitext(f)[0].upper()
        for f in os.listdir(folder)
        if f.lower().endswith(".pdf")
    )

def find_subject_pdf(branch: str, subject_code: str) -> Optional[str]:
    folder = os.path.join(PDF_ROOT, branch.upper())
    if not os.path.isdir(folder):
        for d in os.listdir(PDF_ROOT) if os.path.isdir(PDF_ROOT) else []:
            if d.upper() == branch.upper():
                folder = os.path.join(PDF_ROOT, d)
                break
        else:
            return None
    code = subject_code.strip().upper()
    for fname in os.listdir(folder):
        stem = os.path.splitext(fname)[0].upper()
        if stem == code and fname.lower().endswith(".pdf"):
            return os.path.join(folder, fname)
    return None

@st.cache_data(show_spinner=False)
def get_pdf_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

def pdf_content_block(path: str, max_pages: int = 80) -> dict:
    reader = PdfReader(path)
    total  = len(reader.pages)
    if total <= max_pages:
        return {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf",
                       "data": get_pdf_base64(path)}
        }
    st.toast(f"Large PDF ({total} pages) — sending first {max_pages} pages.", icon="✂️")
    writer = PdfWriter()
    for i in range(min(max_pages, total)):
        writer.add_page(reader.pages[i])
    buf = io.BytesIO(); writer.write(buf)
    return {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf",
                   "data": base64.standard_b64encode(buf.getvalue()).decode("utf-8")}
    }

def get_pdf_page_count(path: str) -> int:
    try:
        return len(PdfReader(path).pages)
    except Exception:
        return 0

# ═══════════════════════════════════════════════════════════════════════════
#  BRANCH PROFILE
# ═══════════════════════════════════════════════════════════════════════════

BRANCH_PROFILES = {
    "CORE": {
        "keywords": ["CSE","CS","IT","AIML","AIDS","AI","DS","ML","ECE","EEE","IOT","CYBER","CSD","CSBS"],
        "label": "Full technical depth",
        "emoji": "🔬",
        "color": "#3df5a8",
        "instruction": (
            "Give a COMPLETE, DETAILED, TECHNICAL answer covering all relevant concepts, "
            "algorithms, formulas, sub-topics, and examples as described in the syllabus. "
            "Use proper technical terminology, clear headings, and bullet points."
        ),
    },
    "RELATED": {
        "keywords": ["MECH","CIVIL","CHEM","AERO","AUTO","AGRI","BIOTECH","MARINE"],
        "label": "Simplified — applied focus",
        "emoji": "📘",
        "color": "#fbbf24",
        "instruction": (
            "Give a CLEAR, CONCISE answer in plain language. Avoid heavy jargon. "
            "Start with a simple definition, then give brief context and a real-world analogy."
        ),
    },
}

def get_branch_profile(branch: str) -> dict:
    b = branch.upper()
    for level, data in BRANCH_PROFILES.items():
        if any(kw in b for kw in data["keywords"]):
            return {"level": level, **data}
    return {
        "level": "OTHER",
        "label": "General",
        "emoji": "📖",
        "color": "#7c8fff",
        "instruction": "Give a clear, concise answer with a definition and key points.",
    }

# ═══════════════════════════════════════════════════════════════════════════
#  CLAUDE WRAPPER
# ═══════════════════════════════════════════════════════════════════════════

def claude_call(messages: list, max_tokens: int = 4096, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=max_tokens,
                messages=messages,
            )
            return resp.content[0].text
        except Exception as e:
            err = str(e)
            if "rate_limit" in err or "529" in err or "429" in err:
                wait = 20 * (attempt + 1)
                st.toast(f"Rate limit — waiting {wait}s…", icon="⏳")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Claude rate-limited after all retries.")

# ═══════════════════════════════════════════════════════════════════════════
#  GROQ WRAPPER
# ═══════════════════════════════════════════════════════════════════════════

def groq_call(system: str, user: str, max_tokens: int = 2000, temp: float = 0.7) -> str:
    r = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": user}],
        max_tokens=max_tokens,
        temperature=temp,
    )
    return r.choices[0].message.content

# ═══════════════════════════════════════════════════════════════════════════
#  ACTION 1 — VIEW FULL SYLLABUS
# ═══════════════════════════════════════════════════════════════════════════

def action_view_syllabus(pdf_path: str, subject_code: str, semester: str) -> str:
    block = pdf_content_block(pdf_path, max_pages=80)
    return claude_call([{
        "role": "user",
        "content": [
            block,
            {"type": "text", "text": f"""Read this syllabus PDF carefully.

Extract the COMPLETE syllabus for subject code: **{subject_code}**
Semester: {semester}

Return EXACTLY as it appears:
- Subject name and code
- Credits (L T P C)
- Course Objectives (all points)
- All Units with full topic details
- Course Outcomes (all)
- Textbooks & Reference books

If not found: "Subject {subject_code} was not found in this PDF."
Do NOT summarize. Return full content."""}
        ]
    }], max_tokens=8192)

# ═══════════════════════════════════════════════════════════════════════════
#  ACTION 2 — ASK ABOUT SYLLABUS
# ═══════════════════════════════════════════════════════════════════════════

def action_ask_syllabus(pdf_path: str, subject_code: str, semester: str,
                        question: str, branch: str) -> str:
    profile = get_branch_profile(branch)
    prompt  = f"""You are an AI Teaching Assistant for engineering students.

STUDENT: Branch={branch} | Subject={subject_code} | Semester={semester} | Level={profile['level']}

ANSWERING STYLE:
{profile['instruction']}

RULES:
- Answer strictly from the syllabus PDF.
- If topic IS in syllabus: explain it fully as per syllabus.
- If topic is NOT in syllabus: state "This topic is not in the {subject_code} syllabus."
  Then give a brief general explanation appropriate for this student's level.
- Never fabricate syllabus content.
- Use headings and bullet points.

Question: {question}"""

    block = pdf_content_block(pdf_path, max_pages=60)
    return claude_call([{
        "role": "user",
        "content": [block, {"type": "text", "text": prompt}]
    }], max_tokens=3500)

# ═══════════════════════════════════════════════════════════════════════════
#  ACTION 3 — TOPIC SUMMARY CARD
# ═══════════════════════════════════════════════════════════════════════════

def action_topic_summary(pdf_path: str, subject_code: str, topic: str, branch: str) -> str:
    profile = get_branch_profile(branch)
    prompt  = f"""From the syllabus PDF for subject {subject_code}, create a structured STUDY CARD for the topic:

**Topic:** {topic}
**Student level:** {profile['level']} ({branch})

Format the card as:
## {topic}
### Definition
[1-2 sentence definition]

### Key Concepts
[bullet list of 4-6 core ideas]

### Important Points for Exam
[bullet list of 3-5 exam-relevant points]

### Example / Application
[brief example or real-world use]

{profile['instruction']}"""

    block = pdf_content_block(pdf_path, max_pages=60)
    return claude_call([{
        "role": "user",
        "content": [block, {"type": "text", "text": prompt}]
    }], max_tokens=2000)

# ═══════════════════════════════════════════════════════════════════════════
#  ACTION 4 — FORMULA SHEET
# ═══════════════════════════════════════════════════════════════════════════

def action_formula_sheet(pdf_path: str, subject_code: str, unit: str) -> str:
    prompt = f"""From the syllabus PDF for subject {subject_code}, extract ALL formulas, equations,
and key definitions mentioned in {unit if unit != 'All Units' else 'all units'}.

Format as a clean FORMULA SHEET:
## Formula Sheet - {subject_code} {f'({unit})' if unit != 'All Units' else ''}

For each unit/section:
### [Unit Name]
| Formula/Term | Description |
|---|---|
| [formula] | [what it means] |

Include: mathematical formulas, algorithms steps, definitions, key theorems.
Do not include prose - only formulas and definitions."""

    block = pdf_content_block(pdf_path, max_pages=80)
    return claude_call([{
        "role": "user",
        "content": [block, {"type": "text", "text": prompt}]
    }], max_tokens=3000)

# ═══════════════════════════════════════════════════════════════════════════
#  ACTION 5 — STUDY PLANNER
# ═══════════════════════════════════════════════════════════════════════════

def action_study_planner(subject: str, days: int, units: str, exam_type: str) -> str:
    system = (
        "You are an expert academic study planner for engineering students. "
        "Create realistic, hour-by-hour study plans. Be specific and practical."
    )
    user = f"""Create a {days}-day study plan for:
Subject: {subject}
Units/Topics: {units}
Exam type: {exam_type}

Format:
## {days}-Day Study Plan - {subject}

### Day 1: [focus area]
- Morning (2hr): [specific tasks]
- Afternoon (2hr): [specific tasks]
- Evening (1hr): [revision]
- Quick Revision: [3 key points to remember]

...repeat for each day...

### Final Day: Revision Strategy
### Exam Day Tips

Keep plans realistic. Include breaks. Focus on high-weightage topics first."""

    return groq_call(system, user, max_tokens=2500, temp=0.5)

# ═══════════════════════════════════════════════════════════════════════════
#  ACTION 6 — PREVIOUS YEAR Q&A
# ═══════════════════════════════════════════════════════════════════════════

def action_pyq_answer(subject: str, question: str, marks: int, branch: str) -> str:
    profile = get_branch_profile(branch)
    system  = (
        f"You are an expert engineering examiner and teacher for {branch} students. "
        "Answer previous year exam questions with exactly the right depth for the marks allocated. "
        f"{profile['instruction']}"
    )
    user = f"""Answer this previous year exam question:

Subject: {subject}
Marks: {marks}
Branch: {branch}

Question: {question}

Write a model answer appropriate for {marks} marks.
- 2 marks: definition + 1 example
- 5 marks: detailed explanation with points
- 10 marks: full essay with diagrams description, examples, advantages/disadvantages
Format with headings and bullet points."""

    return groq_call(system, user, max_tokens=2500, temp=0.4)

# ═══════════════════════════════════════════════════════════════════════════
#  ACTION 7 — QUICK ANSWER
# ═══════════════════════════════════════════════════════════════════════════

def action_quick_answer(question: str, branch: str) -> str:
    profile = get_branch_profile(branch)
    system  = (
        f"You are a helpful AI teacher for {branch} engineering students. "
        f"{profile['instruction']} "
        "Answer clearly with examples. Use headings and bullet points."
    )
    return groq_call(system, question, max_tokens=1800, temp=0.6)

# ═══════════════════════════════════════════════════════════════════════════
#  ACTION 8 — GENERATE CODE
# ═══════════════════════════════════════════════════════════════════════════

def action_generate_code(problem: str, lang: str) -> str:
    system = (
        f"You are an expert {lang} programmer for engineering labs. "
        f"Write complete, executable {lang} code only. "
        "No markdown fences. No explanations outside comments. Raw code only."
    )
    code = groq_call(system, problem, max_tokens=2500, temp=0.2)
    code = re.sub(r"^```[\w]*\n?", "", code.strip())
    code = re.sub(r"```$", "", code.strip())
    return code.strip()

# ═══════════════════════════════════════════════════════════════════════════
#  ACTION 8b — EXECUTE CODE VIA GROQ API (for non-Python languages)
#  Groq simulates execution: traces through the code step-by-step and
#  returns what the actual output would be, given the stdin input.
# ═══════════════════════════════════════════════════════════════════════════

def action_execute_code_via_ai(code: str, lang: str, stdin_input: str) -> dict:
    """
    Uses Groq to simulate/execute code and return:
      - stdout output
      - any errors
      - step-by-step trace (optional)
    Returns dict: {"output": str, "error": str, "success": bool}
    """
    system = """You are a precise code execution engine / interpreter simulator.
Your job is to trace through the given code exactly as a real compiler/interpreter would,
and return ONLY the program's output — nothing else.

Rules:
1. Read the code carefully line by line.
2. Simulate variable states, loops, conditionals, function calls exactly.
3. Use the provided stdin input when the program reads from stdin.
4. Return ONLY what would appear on stdout when the program runs.
5. If there is a compile error or runtime error, return: ERROR: <description>
6. Do NOT add explanations, commentary, or extra text.
7. Preserve exact formatting of output (newlines, spaces).
"""
    user = f"""Language: {lang}
Stdin Input: {stdin_input if stdin_input.strip() else "(none)"}

Code:
{code}

Execute this code and return ONLY the stdout output (or ERROR: message if it fails)."""

    try:
        result = groq_call(system, user, max_tokens=1000, temp=0.0)
        result = result.strip()
        if result.upper().startswith("ERROR:"):
            return {"output": "", "error": result, "success": False}
        return {"output": result, "error": "", "success": True}
    except Exception as e:
        return {"output": "", "error": str(e), "success": False}

# ═══════════════════════════════════════════════════════════════════════════
#  ACTION 9 — EXAM MODE QUIZ
# ═══════════════════════════════════════════════════════════════════════════

def action_exam_quiz(subject: str, topic: str, num_q: int, q_type: str) -> str:
    system = (
        "You are an expert exam question setter for engineering university exams. "
        "Create realistic exam questions exactly as they appear in university papers."
    )
    user = f"""Create {num_q} {q_type} questions for:
Subject: {subject}
Topic: {topic}

Format:
## Practice Questions - {topic}
### {q_type} Questions

Q1. [Question] ({2 if q_type=='Short Answer' else 10} marks)
**Answer:** [Model answer]

Q2. ...

Make questions exam-realistic. Include answers."""

    return groq_call(system, user, max_tokens=2500, temp=0.5)

# ═══════════════════════════════════════════════════════════════════════════
#  PDF EXPORT  (FIXED — full Unicode-safe character mapping)
# ═══════════════════════════════════════════════════════════════════════════

# Comprehensive Unicode → ASCII/Latin-1 safe replacement table
_UNICODE_TABLE = {
    # Bullets & list markers
    "\u2022": "-",   # •
    "\u00b7": "-",   # middle dot
    "\u25cf": "-",   # black circle
    "\u25cb": "o",   # white circle
    "\u25a0": "-",   # black square
    "\u25a1": "-",   # white square
    "\u2023": "-",   # triangular bullet
    "\u2043": "-",   # hyphen bullet

    # Dashes & hyphens
    "\u2013": "-",   # en dash
    "\u2014": "--",  # em dash
    "\u2012": "-",   # figure dash
    "\u2015": "-",   # horizontal bar

    # Quotes
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u201a": ",",   # low single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u201e": '"',   # low double quote

    # Ellipsis & misc punctuation
    "\u2026": "...", # ellipsis
    "\u2027": ".",   # hyphenation point
    "\u00ab": "<<",  # left guillemet
    "\u00bb": ">>",  # right guillemet

    # Arrows
    "\u2192": "->",  # right arrow
    "\u2190": "<-",  # left arrow
    "\u2194": "<->", # left-right arrow
    "\u21d2": "=>",  # double right arrow
    "\u2191": "^",   # up arrow
    "\u2193": "v",   # down arrow

    # Math operators
    "\u00d7": "x",   # multiplication sign
    "\u00f7": "/",   # division sign
    "\u00b0": " deg",# degree sign
    "\u00b1": "+/-", # plus-minus
    "\u2264": "<=",  # less than or equal
    "\u2265": ">=",  # greater than or equal
    "\u2260": "!=",  # not equal
    "\u2248": "~=",  # approximately equal
    "\u221e": "inf", # infinity
    "\u221a": "sqrt",# square root
    "\u2211": "sum", # summation
    "\u220f": "prod",# product
    "\u222b": "int", # integral
    "\u2202": "d",   # partial derivative
    "\u2207": "del", # nabla
    "\u2208": "in",  # element of
    "\u2209": "not in",
    "\u2229": "^",   # intersection
    "\u222a": "v",   # union
    "\u2282": "C",   # subset of
    "\u2283": "D",   # superset of

    # Greek letters (common in engineering)
    "\u03b1": "alpha", "\u03b2": "beta",  "\u03b3": "gamma",
    "\u03b4": "delta", "\u03b5": "eps",   "\u03b6": "zeta",
    "\u03b7": "eta",   "\u03b8": "theta", "\u03b9": "iota",
    "\u03ba": "kappa", "\u03bb": "lambda","\u03bc": "mu",
    "\u03bd": "nu",    "\u03be": "xi",    "\u03c0": "pi",
    "\u03c1": "rho",   "\u03c3": "sigma", "\u03c4": "tau",
    "\u03c5": "ups",   "\u03c6": "phi",   "\u03c7": "chi",
    "\u03c8": "psi",   "\u03c9": "omega",
    "\u0391": "Alpha", "\u0392": "Beta",  "\u0393": "Gamma",
    "\u0394": "Delta", "\u0398": "Theta", "\u039b": "Lambda",
    "\u03a0": "Pi",    "\u03a3": "Sigma", "\u03a6": "Phi",
    "\u03a9": "Omega",

    # Superscripts / subscripts
    "\u00b2": "^2",  "\u00b3": "^3",
    "\u00b9": "^1",  "\u2070": "^0",
    "\u2074": "^4",  "\u2075": "^5",
    "\u2076": "^6",  "\u2077": "^7",
    "\u2078": "^8",  "\u2079": "^9",

    # Currency & misc
    "\u20ac": "EUR", "\u00a3": "GBP", "\u00a5": "JPY",
    "\u00a9": "(c)", "\u00ae": "(r)", "\u2122": "(tm)",
    "\u00a0": " ",   # non-breaking space
    "\u00ad": "-",   # soft hyphen
    "\u200b": "",    # zero-width space

    # Box drawing (sometimes in tables)
    "\u2500": "-", "\u2502": "|", "\u250c": "+",
    "\u2510": "+", "\u2514": "+", "\u2518": "+",
    "\u251c": "+", "\u2524": "+", "\u252c": "+",
    "\u2534": "+", "\u253c": "+",

    # Checkmarks / X marks
    "\u2713": "[OK]", "\u2714": "[OK]",
    "\u2717": "[X]",  "\u2718": "[X]",
    "\u2705": "[OK]", "\u274c": "[X]",

    # Stars / ratings
    "\u2605": "*",  "\u2606": "*",
    "\u2665": "<3", "\u2660": "S",

    # Fraction slash
    "\u2044": "/",
}

def safe_latin1(text: str) -> str:
    """
    Convert any Unicode string to a Latin-1-safe string for fpdf2/Helvetica.
    Steps:
      1. Apply explicit character mapping table
      2. NFKD normalize (decomposes accented chars)
      3. Encode to latin-1, replacing anything remaining with '?'
    """
    if not text:
        return ""
    # Step 1: apply our mapping table
    for ch, rep in _UNICODE_TABLE.items():
        text = text.replace(ch, rep)
    # Step 2: NFKD normalization (e.g. é -> e + combining accent)
    text = unicodedata.normalize("NFKD", text)
    # Step 3: encode to latin-1, drop unmappable chars gracefully
    return text.encode("latin-1", "replace").decode("latin-1")


def build_pdf(result: str, title: str, subtitle: str, meta: str) -> bytes:
    """Build a styled PDF from markdown-like text. Fully Unicode-safe."""
    L = R = 15; T = 15; CW = 210 - L - R
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(L, T, R)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Header bar ──
    pdf.set_fill_color(30, 35, 65)
    pdf.rect(0, 0, 210, 30, style="F")
    pdf.set_text_color(230, 235, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_xy(L, 8)
    pdf.cell(CW, 8, safe_latin1(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(L, 18)
    pdf.cell(CW, 7, safe_latin1(f"{subtitle}   |   {meta}"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(26, 29, 46)
    pdf.set_xy(L, 36)
    right_edge = L + CW

    for raw_line in result.splitlines():
        line = safe_latin1(raw_line)
        s = line.strip()
        if not s:
            pdf.ln(2)
            continue

        # H1
        if s.startswith("# ") and not s.startswith("## "):
            c = s[2:].strip()
            if not c:
                continue
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_fill_color(220, 224, 255)
            pdf.set_text_color(30, 35, 65)
            pdf.multi_cell(CW, 9, c, fill=True)
            pdf.ln(2)

        # H2
        elif s.startswith("## ") and not s.startswith("### "):
            c = s[3:].strip()
            if not c:
                continue
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(79, 99, 200)
            pdf.multi_cell(CW, 8, c)
            y = pdf.get_y()
            pdf.set_draw_color(79, 99, 200)
            pdf.set_line_width(0.4)
            pdf.line(L, y, right_edge, y)
            pdf.ln(4)
            pdf.set_text_color(26, 29, 46)
            pdf.set_font("Helvetica", "", 10)

        # H3
        elif s.startswith("### "):
            c = s[4:].strip()
            if not c:
                continue
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(26, 29, 46)
            pdf.multi_cell(CW, 7, c)
            pdf.ln(1)
            pdf.set_font("Helvetica", "", 10)

        # Bullet list
        elif s.startswith("- ") or s.startswith("* "):
            ind = max(0, (len(raw_line) - len(raw_line.lstrip())) // 2)
            c = s[2:].strip()
            if not c:
                continue
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(26, 29, 46)
            pdf.set_x(L + ind * 4)
            pdf.multi_cell(CW - ind * 4, 6, "- " + c)

        # Table row
        elif s.startswith("|"):
            cells = [c.strip() for c in s.split("|")
                     if c.strip() and not set(c.strip()) <= set("-: |")]
            if cells:
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(26, 29, 46)
                pdf.multi_cell(CW, 5, "  |  ".join(cells))

        # Horizontal rule
        elif s in ("---", "***", "___"):
            y = pdf.get_y() + 2
            pdf.set_draw_color(180, 190, 230)
            pdf.set_line_width(0.3)
            pdf.line(L, y, right_edge, y)
            pdf.ln(5)

        # Normal paragraph
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(26, 29, 46)
            pdf.set_x(L)
            pdf.multi_cell(CW, 6, line)

    # ── Page numbers ──
    total = pdf.page
    for pg in range(1, total + 1):
        pdf.page = pg
        pdf.set_y(-14)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(120, 130, 180)
        pdf.set_x(L)
        pdf.cell(CW - 20, 8, safe_latin1(f"AI Teaching Assistant  |  {title}  |  {meta}"))
        pdf.cell(20, 8, safe_latin1(f"{pg}/{total}"), align="R")

    return bytes(pdf.output())

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN UI
# ═══════════════════════════════════════════════════════════════════════════

branches = list_branches()
if not branches:
    st.markdown(
        '<div class="box-warn">No branch folders found in <code>syllabus_pdfs/</code>. '
        'Create folders like <code>syllabus_pdfs/AIDS/</code> and add PDFs named by subject code '
        '(e.g. <code>23AD101.pdf</code>).</div>',
        unsafe_allow_html=True
    )
    branches = ["(No branches found)"]

# ── Academic Details ──────────────────────────────────────────────────────
st.markdown('<div class="sec">📚 Academic Details</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([2, 1.5, 2, 1.5])

branch   = c1.selectbox("Branch", branches)
semester = c2.selectbox("Semester", [f"Sem {i}" for i in range(1, 9)])

subjects_in_branch = list_subjects_in_branch(branch) if branch != "(No branches found)" else []
subject_options    = subjects_in_branch if subjects_in_branch else ["(type below)"]
subject_from_list  = c3.selectbox("Subject Code (from folder)", subject_options,
                                   help="Select a subject code detected in your branch PDF folder")
subject_manual     = c4.text_input("Or type subject code", placeholder="23AD101")

subject_code = subject_manual.strip().upper() if subject_manual.strip() else (
    subject_from_list if subject_from_list != "(type below)" else ""
)

if branch not in ["(No branches found)"]:
    pdf_path = find_subject_pdf(branch, subject_code) if subject_code else None
    if pdf_path and os.path.isfile(pdf_path):
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        pages   = get_pdf_page_count(pdf_path)
        st.markdown(
            f'<div class="box-ok">PDF found: <strong>{os.path.basename(pdf_path)}</strong>'
            f' · {size_mb:.1f} MB · {pages} pages · Claude will read this directly</div>',
            unsafe_allow_html=True
        )
    elif subject_code:
        st.markdown(
            f'<div class="box-warn"><code>{subject_code}.pdf</code> not found in '
            f'<code>syllabus_pdfs/{branch}/</code>. '
            f'Add the PDF or use Quick Answer / other non-PDF tools.</div>',
            unsafe_allow_html=True
        )

    prof = get_branch_profile(branch)
    st.markdown(
        f'<div style="display:inline-block;background:rgba(0,0,0,0.2);'
        f'border:1px solid {prof["color"]}33;border-radius:8px;padding:5px 14px;'
        f'font-size:0.78rem;color:{prof["color"]};margin:0.3rem 0;">'
        f'{prof["emoji"]} <strong>{branch}</strong> → '
        f'<strong>{prof["level"]}</strong> · {prof["label"]}</div>',
        unsafe_allow_html=True
    )

# ── TABS ──────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">📖 Tools</div>', unsafe_allow_html=True)
tabs = st.tabs([
    "📄 Syllabus",
    "🎯 Ask Syllabus",
    "🧮 Formula Sheet",
    "📝 Topic Card",
    "💬 Quick Answer",
    "📅 Study Planner",
    "📋 PYQ Answer",
    "🧪 Exam Quiz",
    "💻 Code Lab",
])

# ─────────────────────────────────────────────────────────────────
# TAB 0 — VIEW FULL SYLLABUS
# ─────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("**Claude reads the subject PDF and returns the complete syllabus.**")
    if st.button("📄 Load Full Syllabus", key="btn_view"):
        if not subject_code:
            st.warning("Select or type a subject code above.")
        else:
            pdf_path = find_subject_pdf(branch, subject_code)
            if not pdf_path:
                st.error(f"PDF not found: `syllabus_pdfs/{branch}/{subject_code}.pdf`")
            else:
                with st.spinner("Claude is reading the PDF…"):
                    try:
                        result = action_view_syllabus(pdf_path, subject_code, semester)
                        st.session_state["last_result"] = result
                        st.session_state["last_meta"]   = {
                            "title": f"Syllabus - {subject_code}",
                            "subtitle": branch,
                            "meta": semester,
                        }
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error: {e}")

    if st.session_state.get("last_result") and "Syllabus" in st.session_state["last_meta"].get("title", ""):
        m = st.session_state["last_meta"]
        try:
            pdf_bytes = build_pdf(st.session_state["last_result"], m["title"], m["subtitle"], m["meta"])
            st.download_button("⬇️ Download as PDF", pdf_bytes,
                               f"syllabus_{subject_code}_{branch}.pdf", "application/pdf",
                               use_container_width=True)
        except Exception as e:
            st.warning(f"PDF export error: {e}")

# ─────────────────────────────────────────────────────────────────
# TAB 1 — ASK ABOUT SYLLABUS
# ─────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("**Claude reads the PDF directly and answers your question with branch-aware depth.**")
    q_ask = st.text_area("Your question about this subject", height=100,
                          placeholder="Explain Unit 3 of 23AD101. What is backpropagation?")
    if st.button("🎯 Ask", key="btn_ask"):
        if not subject_code:
            st.warning("Select a subject code above.")
        elif not q_ask.strip():
            st.warning("Enter a question.")
        else:
            pdf_path = find_subject_pdf(branch, subject_code)
            if not pdf_path:
                st.error(f"PDF not found: `syllabus_pdfs/{branch}/{subject_code}.pdf`")
            else:
                with st.spinner("Claude is reading the PDF and composing an answer…"):
                    try:
                        result = action_ask_syllabus(pdf_path, subject_code, semester, q_ask, branch)
                        st.session_state["chat_history"].append({
                            "q": q_ask, "a": result,
                            "subject": subject_code, "branch": branch,
                        })
                        st.markdown(result)
                        try:
                            pdf_bytes = build_pdf(result, f"QA - {subject_code}", branch, semester)
                            st.download_button("⬇️ Download Answer", pdf_bytes,
                                               f"answer_{subject_code}.pdf", "application/pdf")
                        except Exception:
                            pass
                    except Exception as e:
                        st.error(f"Error: {e}")

    if st.session_state["chat_history"]:
        st.markdown('<div class="sec">💬 Session History</div>', unsafe_allow_html=True)
        for item in reversed(st.session_state["chat_history"][-5:]):
            st.markdown(f'<div class="chat-user">🧑 <strong>Q:</strong> {item["q"]}</div>',
                        unsafe_allow_html=True)
            with st.expander(f"View answer — {item['subject']} ({item['branch']})", expanded=False):
                st.markdown(item["a"])
        if st.button("🗑️ Clear History", key="clear_hist"):
            st.session_state["chat_history"] = []
            st.rerun()

# ─────────────────────────────────────────────────────────────────
# TAB 2 — FORMULA SHEET
# ─────────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("**Claude extracts all formulas and key definitions from the syllabus PDF.**")
    unit_sel = st.selectbox("Unit", ["All Units", "Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5"])
    if st.button("🧮 Generate Formula Sheet", key="btn_formula"):
        if not subject_code:
            st.warning("Select a subject code above.")
        else:
            pdf_path = find_subject_pdf(branch, subject_code)
            if not pdf_path:
                st.error(f"PDF not found: `syllabus_pdfs/{branch}/{subject_code}.pdf`")
            else:
                with st.spinner("Extracting formulas from PDF…"):
                    try:
                        result = action_formula_sheet(pdf_path, subject_code, unit_sel)
                        st.markdown(result)
                        try:
                            pdf_bytes = build_pdf(result, f"Formula Sheet - {subject_code}",
                                                  branch, unit_sel)
                            st.download_button("⬇️ Download Formula Sheet", pdf_bytes,
                                               f"formulas_{subject_code}_{unit_sel.replace(' ', '')}.pdf",
                                               "application/pdf")
                        except Exception:
                            pass
                    except Exception as e:
                        st.error(f"Error: {e}")

# ─────────────────────────────────────────────────────────────────
# TAB 3 — TOPIC STUDY CARD
# ─────────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("**Get a concise exam-ready study card for any topic in your syllabus.**")
    topic_input = st.text_input("Topic name", placeholder="Neural Networks, OSI Model, Quicksort…")
    if st.button("📝 Generate Study Card", key="btn_card"):
        if not subject_code:
            st.warning("Select a subject code above.")
        elif not topic_input.strip():
            st.warning("Enter a topic name.")
        else:
            pdf_path = find_subject_pdf(branch, subject_code)
            if not pdf_path:
                st.info("No PDF found — generating from general knowledge via Groq.")
                with st.spinner("Generating study card…"):
                    try:
                        result = action_quick_answer(
                            f"Give a detailed study card for: {topic_input} (subject: {subject_code})",
                            branch
                        )
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                with st.spinner("Claude is building your study card…"):
                    try:
                        result = action_topic_summary(pdf_path, subject_code, topic_input, branch)
                        st.markdown(
                            f'<div class="card"><div class="card-title">📇 Study Card: {topic_input}</div></div>',
                            unsafe_allow_html=True
                        )
                        st.markdown(result)
                        try:
                            pdf_bytes = build_pdf(result, f"Study Card - {topic_input}", subject_code, branch)
                            st.download_button("⬇️ Download Study Card", pdf_bytes,
                                               f"card_{topic_input.replace(' ', '_')}.pdf",
                                               "application/pdf")
                        except Exception:
                            pass
                    except Exception as e:
                        st.error(f"Error: {e}")

# ─────────────────────────────────────────────────────────────────
# TAB 4 — QUICK ANSWER
# ─────────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("**Instant answers via Groq — no PDF needed. Ask anything.**")
    q_quick = st.text_area("Question", height=100,
                            placeholder="What is the difference between TCP and UDP?")
    if st.button("⚡ Quick Answer", key="btn_quick"):
        if not q_quick.strip():
            st.warning("Enter a question.")
        else:
            with st.spinner("Groq is thinking…"):
                try:
                    result = action_quick_answer(q_quick, branch)
                    st.markdown(result)
                except Exception as e:
                    st.error(f"Groq error: {e}")

# ─────────────────────────────────────────────────────────────────
# TAB 5 — STUDY PLANNER
# ─────────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("**AI generates a day-by-day exam study plan.**")
    sp_c1, sp_c2 = st.columns(2)
    sp_days  = sp_c1.slider("Study days available", 1, 30, 7)
    sp_etype = sp_c2.selectbox("Exam type", ["Mid Exam", "End Sem", "Lab Exam", "Viva"])
    sp_units = st.text_area("Units/Topics to cover",
                             placeholder="Unit 1: Data Structures\nUnit 2: Trees & Graphs\nUnit 3: Sorting",
                             height=80)
    sp_subj  = st.text_input("Subject name (for plan header)",
                              value=subject_code or "",
                              placeholder="Data Structures (23CS201)")
    if st.button("📅 Generate Study Plan", key="btn_plan"):
        if not sp_units.strip():
            st.warning("Enter units/topics to study.")
        else:
            with st.spinner("Building your study plan…"):
                try:
                    result = action_study_planner(sp_subj or subject_code or "Subject",
                                                  sp_days, sp_units, sp_etype)
                    st.markdown(result)
                    try:
                        pdf_bytes = build_pdf(result, f"Study Plan - {sp_subj or subject_code}",
                                              branch, f"{sp_days}-day plan")
                        st.download_button("⬇️ Download Plan", pdf_bytes,
                                           f"plan_{subject_code}_{sp_days}days.pdf",
                                           "application/pdf")
                    except Exception:
                        pass
                except Exception as e:
                    st.error(f"Error: {e}")

# ─────────────────────────────────────────────────────────────────
# TAB 6 — PREVIOUS YEAR QUESTION ANSWER
# ─────────────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown("**Paste a previous year question and get a model exam answer.**")
    pyq_q     = st.text_area("Previous Year Question", height=100,
                              placeholder="Explain the working of a B+ tree with an example.")
    pyq_c1, pyq_c2 = st.columns(2)
    pyq_marks = pyq_c1.selectbox("Marks", [2, 5, 10, 13, 15])
    pyq_subj  = pyq_c2.text_input("Subject", value=subject_code or "",
                                   placeholder="23AD101 — AI & DS")
    if st.button("📋 Generate Model Answer", key="btn_pyq"):
        if not pyq_q.strip():
            st.warning("Enter a question.")
        else:
            with st.spinner("Writing model answer…"):
                try:
                    result = action_pyq_answer(pyq_subj or subject_code, pyq_q, pyq_marks, branch)
                    st.markdown(result)
                    try:
                        pdf_bytes = build_pdf(result, f"PYQ Answer - {pyq_subj or subject_code}",
                                              branch, f"{pyq_marks} marks")
                        st.download_button("⬇️ Download Answer", pdf_bytes,
                                           f"pyq_{subject_code}_{pyq_marks}m.pdf",
                                           "application/pdf")
                    except Exception:
                        pass
                except Exception as e:
                    st.error(f"Error: {e}")

# ─────────────────────────────────────────────────────────────────
# TAB 7 — EXAM QUIZ
# ─────────────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown("**Generate practice exam questions with model answers.**")
    qz_c1, qz_c2, qz_c3 = st.columns(3)
    qz_topic = qz_c1.text_input("Topic", placeholder="Sorting Algorithms")
    qz_num   = qz_c2.slider("Number of questions", 3, 15, 5)
    qz_type  = qz_c3.selectbox("Question type", ["Short Answer", "Long Answer", "MCQ", "True/False"])
    qz_subj  = st.text_input("Subject", value=subject_code or "", placeholder="23CS201")
    if st.button("🧪 Generate Quiz", key="btn_quiz"):
        if not qz_topic.strip():
            st.warning("Enter a topic.")
        else:
            with st.spinner("Generating exam questions…"):
                try:
                    result = action_exam_quiz(qz_subj or subject_code, qz_topic, qz_num, qz_type)
                    st.markdown(result)
                    try:
                        pdf_bytes = build_pdf(result, f"Quiz - {qz_topic}", qz_subj or subject_code,
                                              f"{qz_num} {qz_type} Qs")
                        st.download_button("⬇️ Download Quiz", pdf_bytes,
                                           f"quiz_{qz_topic.replace(' ', '_')}.pdf",
                                           "application/pdf")
                    except Exception:
                        pass
                except Exception as e:
                    st.error(f"Error: {e}")

# ─────────────────────────────────────────────────────────────────
# TAB 8 — CODE LAB  (Multi-language execution via Groq AI)
# ─────────────────────────────────────────────────────────────────
with tabs[8]:
    st.markdown("""
**Generate code in any language and run it:**
- 🐍 **Python** — executed live on the server
- ☕ **Java / C / C++ / JavaScript** — executed via **Groq AI simulation** (traces output accurately)
""")

    cl_c1, cl_c2 = st.columns([3, 1])
    code_q    = cl_c1.text_area("Describe the program", height=80,
                                  placeholder="Write a Java program to check if a number is even or odd")
    code_lang = cl_c2.selectbox("Language", ["Python", "Java", "C", "C++", "JavaScript"])

    if st.button("💻 Generate Code", key="btn_code"):
        if not code_q.strip():
            st.warning("Describe the program to generate.")
        else:
            with st.spinner(f"Generating {code_lang} code…"):
                try:
                    code = action_generate_code(code_q, code_lang)
                    st.session_state["ai_code"]      = code
                    st.session_state["ai_code_lang"] = code_lang
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.session_state.get("ai_code", "").strip():
        run_lang = st.session_state["ai_code_lang"]
        st.markdown(f'<div class="sec">✏️ Edit & Run — {run_lang}</div>', unsafe_allow_html=True)

        edited_code = st.text_area("Code editor", st.session_state["ai_code"], height=320,
                                    key="code_editor")
        stdin_input = st.text_area("Program input (stdin)", "", height=60,
                                    placeholder="Enter input values if the program reads from stdin…")

        # Execution method info
        if run_lang == "Python":
            st.markdown(
                '<div class="box-info">🐍 Python will run <strong>directly</strong> on the server.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="box-info">🤖 {run_lang} will be executed via <strong>Groq AI simulation</strong> '
                f'— the AI traces through your code and returns the exact output.</div>',
                unsafe_allow_html=True
            )

        col_run, col_clr = st.columns([3, 1])

        if col_run.button("▶️ Run Code", key="btn_run"):

            # ── Python: real execution ──
            if run_lang == "Python":
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".py",
                                                     mode="w", encoding="utf-8") as f:
                        f.write(edited_code)
                        fname = f.name
                    with st.spinner("Executing Python…"):
                        r = subprocess.run(
                            [sys.executable, fname],
                            input=stdin_input,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                    os.unlink(fname)
                    if r.returncode == 0:
                        st.markdown('<div class="box-ok">✅ Python executed successfully</div>',
                                    unsafe_allow_html=True)
                        st.code(r.stdout or "(no output)", language="text")
                    else:
                        st.markdown('<div class="box-err">❌ Runtime error</div>',
                                    unsafe_allow_html=True)
                        st.code(r.stderr or r.stdout or "(no output)", language="text")
                except subprocess.TimeoutExpired:
                    st.error("⏱️ Timed out (30s limit).")
                except Exception as e:
                    st.error(f"Execution error: {e}")

            # ── Java / C / C++ / JavaScript: AI simulation ──
            else:
                with st.spinner(f"Groq AI is executing {run_lang} code…"):
                    exec_result = action_execute_code_via_ai(edited_code, run_lang, stdin_input)

                if exec_result["success"]:
                    st.markdown(
                        f'<div class="box-ok">✅ {run_lang} executed successfully (AI simulation)</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown("**Output:**")
                    st.code(exec_result["output"] or "(no output)", language="text")
                else:
                    st.markdown(
                        f'<div class="box-err">❌ Error in {run_lang} code</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown("**Error:**")
                    st.code(exec_result["error"] or "(unknown error)", language="text")

                # Also show the code with syntax highlighting
                with st.expander("📋 View formatted code", expanded=False):
                    lang_map = {"Java": "java", "C": "c", "C++": "cpp", "JavaScript": "javascript"}
                    st.code(edited_code, language=lang_map.get(run_lang, "text"))

        if col_clr.button("🗑️ Clear", key="btn_clr_code"):
            st.session_state["ai_code"] = ""
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎓 AI Teaching Assistant")
    st.markdown(f"**Model:** Claude `{CLAUDE_MODEL}` + Groq `{GROQ_MODEL}`")
    st.divider()

    st.markdown("### 📁 Folder Structure")
    st.code("""syllabus_pdfs/
├── AIDS/
│   ├── 23AD101.pdf
│   └── 23AD201.pdf
├── CSE/
│   └── 23CS101.pdf
└── ECE/
    └── 23EC201.pdf""", language="text")

    st.markdown("### 🔑 API Keys (.env)")
    st.code("GROQ_API_KEY=your_groq_key\nANTHROPIC_API_KEY=your_claude_key", language="bash")

    st.markdown("### 📦 Install")
    st.code("pip install streamlit groq anthropic pypdf fpdf2", language="bash")

    st.markdown("### ▶️ Run")
    st.code("streamlit run app.py", language="bash")

    st.divider()
    st.markdown("### 🗂️ PDF Library")
    if branches and branches[0] != "(No branches found)":
        for br in branches:
            subs = list_subjects_in_branch(br)
            if subs:
                st.markdown(f"**📂 {br}** ({len(subs)} subjects)")
                for sc in subs:
                    p  = find_subject_pdf(br, sc)
                    pg = get_pdf_page_count(p) if p else 0
                    st.markdown(f"  &nbsp;&nbsp;📄 `{sc}` · {pg}p")
            else:
                st.markdown(f"📂 {br} *(empty)*")
    else:
        st.warning("No PDFs found. Add branch folders to `syllabus_pdfs/`.")

    st.divider()
    st.markdown("### 🔀 Tool Reference")
    st.markdown("""
| Tool | Engine | Needs PDF? |
|---|---|---|
| 📄 View Syllabus | Claude | Yes |
| 🎯 Ask Syllabus | Claude | Yes |
| 🧮 Formula Sheet | Claude | Yes |
| 📝 Topic Card | Claude/Groq | Optional |
| 💬 Quick Answer | Groq | No |
| 📅 Study Planner | Groq | No |
| 📋 PYQ Answer | Groq | No |
| 🧪 Exam Quiz | Groq | No |
| 💻 Code Lab | Groq+Runner | No |
""")

    st.markdown("### 💻 Code Runner Modes")
    st.markdown("""
| Language | Execution |
|---|---|
| Python | Live (subprocess) |
| Java | Groq AI simulation |
| C | Groq AI simulation |
| C++ | Groq AI simulation |
| JavaScript | Groq AI simulation |
""")
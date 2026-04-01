import streamlit as st
import os
import subprocess
import tempfile
import sys
import base64
import io
import time
import unicodedata
import anthropic
from groq import Groq
from duckduckgo_search import DDGS
from pypdf import PdfReader, PdfWriter
from fpdf import FPDF

# ================= CONFIG =================
PDF_FOLDER = "syllabus_pdfs"

# ================= CLIENTS =================
groq_client   = Groq(api_key=os.getenv("GROQ_API_KEY"))
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ================= PAGE CONFIG =================
st.set_page_config(page_title="AI Teaching Assistant", layout="wide", page_icon="🎓")

# ================= CSS =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary:  #f5f7ff;
    --bg-card:     #ffffff;
    --bg-elevated: #eef0fb;
    --border:      rgba(79,99,231,0.2);
    --accent:      #4f63e7;
    --cyan:        #0099cc;
    --green:       #00a878;
    --gold:        #e6a800;
    --text:        #1a1d2e;
    --muted:       #6b72a0;
    --glow:        0 0 20px rgba(79,99,231,0.15);
    --r:           14px;
    --rs:          8px;
}
html, body, .stApp { background: var(--bg-primary) !important; color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem !important; max-width: 1200px !important; }
.hero { text-align: center; padding: 2.5rem 0 2rem; background: linear-gradient(180deg, rgba(79,99,231,0.05) 0%, transparent 100%); border-radius: var(--r); margin-bottom: 1rem; }
.badge { display: inline-block; background: linear-gradient(135deg,rgba(79,99,231,0.1),rgba(0,153,204,0.08)); border: 1px solid var(--border); border-radius: 50px; padding: 5px 16px; font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--cyan); margin-bottom: 0.8rem; }
.hero-title { font-family: 'Playfair Display', serif !important; font-size: 2.8rem !important; font-weight: 900 !important; background: linear-gradient(135deg, #1a1d2e 0%, #0099cc 50%, #4f63e7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin: 0 !important; line-height: 1.2 !important; }
.hero-sub { color: var(--muted); font-size: 0.95rem; margin-top: 0.5rem; }
.pill { display: inline-flex; align-items: center; gap: 5px; background: rgba(79,99,231,0.07); border: 1px solid rgba(79,99,231,0.18); border-radius: 50px; padding: 3px 12px; font-size: 0.75rem; color: var(--accent); margin: 2px 3px; }
.sec { display: flex; align-items: center; gap: 10px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--accent); margin: 1.8rem 0 0.7rem; }
.sec::after { content:''; flex:1; height:1px; background: var(--border); }
.stSelectbox > div > div, .stTextInput > div > div > input, .stTextArea > div > div > textarea { background: var(--bg-elevated) !important; border: 1px solid var(--border) !important; border-radius: var(--rs) !important; color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; }
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus, .stSelectbox > div > div:focus-within { border-color: var(--accent) !important; box-shadow: var(--glow) !important; }
.stTextInput label, .stTextArea label, .stSelectbox label { color: var(--muted) !important; font-size: 0.8rem !important; font-weight: 500 !important; }
.stButton > button { width: 100% !important; background: var(--bg-elevated) !important; border: 1px solid var(--border) !important; border-radius: var(--rs) !important; color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.86rem !important; font-weight: 500 !important; padding: 0.6rem 1rem !important; transition: all 0.2s !important; }
.stButton > button:hover { background: rgba(79,99,231,0.08) !important; border-color: var(--accent) !important; color: var(--accent) !important; box-shadow: var(--glow) !important; transform: translateY(-1px); }
.stCodeBlock, pre, code { background: #f0f2ff !important; border: 1px solid var(--border) !important; border-radius: var(--rs) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.84rem !important; color: #2d3178 !important; }
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.5rem 0 !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-thumb { background: rgba(79,99,231,0.3); border-radius:3px; }
.info-box { background: rgba(79,99,231,0.06); border: 1px solid rgba(79,99,231,0.2); border-radius: var(--rs); padding: 0.8rem 1rem; font-size: 0.85rem; color: var(--accent); margin: 0.5rem 0; }
.warn-box { background: rgba(230,168,0,0.06); border: 1px solid rgba(230,168,0,0.25); border-radius: var(--rs); padding: 0.8rem 1rem; font-size: 0.85rem; color: var(--gold); margin: 0.5rem 0; }
.ok-box { background: rgba(0,168,120,0.06); border: 1px solid rgba(0,168,120,0.25); border-radius: var(--rs); padding: 0.8rem 1rem; font-size: 0.85rem; color: var(--green); margin: 0.5rem 0; }
.route-box { background: rgba(79,99,231,0.03); border: 1px solid rgba(79,99,231,0.12); border-radius: var(--rs); padding: 0.6rem 1rem; font-size: 0.78rem; color: var(--muted); margin: 0.4rem 0 0.8rem; line-height: 1.8; }
</style>
""", unsafe_allow_html=True)

# ================= HERO =================
st.markdown("""
<div class="hero">
    <div class="badge">✦ Claude API + Groq &nbsp;·&nbsp; Direct PDF Reading</div>
    <div class="hero-title">AI Teaching Assistant</div>
    <div class="hero-sub">Reads your syllabus PDFs directly — no preprocessing, no limits</div>
    <div style="margin-top:1rem;">
        <span class="pill">📄 Direct PDF Reading</span>
        <span class="pill">🎓 Multi-Regulation</span>
        <span class="pill">⚡ Groq Powered</span>
        <span class="pill">💻 Code Runner</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ================= SESSION =================
st.session_state.setdefault("ai_code", "")
st.session_state.setdefault("ai_code_lang", "Python")
st.session_state.setdefault("syllabus_result", "")
st.session_state.setdefault("syllabus_meta", {})

# ================= PDF FOLDER SCANNER =================
def scan_pdf_folder(folder: str) -> dict:
    mapping = {}
    if not os.path.isdir(folder):
        return mapping
    for fname in os.listdir(folder):
        if fname.lower().endswith(".pdf"):
            key = fname.lower().replace("syllabus", "").replace(".pdf", "").strip()
            mapping[key] = fname
    return mapping

PDF_MAP = scan_pdf_folder(PDF_FOLDER)

def get_options():
    options = []
    for key in sorted(PDF_MAP.keys()):
        reg    = key[:3].upper()
        branch = key[3:].upper()
        options.append(f"{reg} {branch}")
    return options if options else ["⚠️ No PDFs found — add to syllabus_pdfs/"]

def find_pdf(reg_branch: str) -> str:
    key   = reg_branch.lower().replace(" ", "")
    fname = PDF_MAP.get(key)
    return os.path.join(PDF_FOLDER, fname) if fname else None

# ================= PDF CACHE =================
def get_cached_pdf_base64(path: str) -> str:
    mtime     = str(os.path.getmtime(path))
    cache_key = f"__pdf_cache__{path}__{mtime}"
    if cache_key not in st.session_state:
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > 5:
            st.toast(f"📄 Loading {size_mb:.1f} MB PDF into memory… (cached after this)", icon="⏳")
        with open(path, "rb") as f:
            st.session_state[cache_key] = base64.standard_b64encode(f.read()).decode("utf-8")
    return st.session_state[cache_key]

# ================= SMART PDF SPLITTER =================
def find_subject_page_range(path: str, subject_code: str, window: int = 15) -> tuple:
    try:
        reader = PdfReader(path)
        total  = len(reader.pages)
        code   = subject_code.upper().strip()
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if code in text.upper():
                start = max(0, i - 1)
                end   = min(total - 1, i + window)
                return start, end
        return 0, min(99, total - 1)
    except Exception:
        return 0, 99

def make_pdf_content_block(path: str, subject_code: str = "", max_pages: int = 90) -> dict:
    reader = PdfReader(path)
    total  = len(reader.pages)

    if total <= max_pages:
        return {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf",
                       "data": get_cached_pdf_base64(path)}
        }

    if subject_code.strip():
        start, end = find_subject_page_range(path, subject_code, window=20)
        label = f"pages {start+1}–{end+1}"
    else:
        start, end = 0, max_pages - 1
        label = f"first {max_pages} pages"

    st.toast(f"Large PDF ({total} pages) — sending {label} to Claude.", icon="✂️")

    writer = PdfWriter()
    for i in range(start, end + 1):
        writer.add_page(reader.pages[i])

    buf = io.BytesIO()
    writer.write(buf)
    data = base64.standard_b64encode(buf.getvalue()).decode("utf-8")

    return {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": data}
    }

# ================= CLAUDE CALLER =================
CLAUDE_MODELS = ["claude-haiku-4-5", "claude-sonnet-4-5"]

def _claude_call(messages: list, max_tokens: int = 4096, retries: int = 3) -> str:
    last_err = None
    for model in CLAUDE_MODELS:
        for attempt in range(retries):
            try:
                response = claude_client.messages.create(
                    model=model, max_tokens=max_tokens, messages=messages)
                return response.content[0].text
            except Exception as e:
                err_str = str(e)
                if "rate_limit_error" in err_str or "429" in err_str:
                    wait = 20 * (attempt + 1)
                    st.toast(f"⏳ Rate limit on {model} — waiting {wait}s…", icon="⏳")
                    time.sleep(wait)
                    last_err = e
                else:
                    raise
        st.toast(f"⚠️ Switching from {model} to next model…", icon="🔄")
    raise RuntimeError(f"All Claude models rate-limited. Last error: {last_err}")

# ================= BRANCH PROFILE =================
def _get_branch_profile(reg_branch: str) -> dict:
    branch = reg_branch.upper()
    CORE_BRANCHES    = ["CSE","CS","IT","AIML","AIDS","AI","DS","ML","ECE","EEE","EE","CSBS","IOT","CYBER","CSD"]
    RELATED_BRANCHES = ["MECH","CIVIL","CHEM","AERO","AUTO"]

    for b in CORE_BRANCHES:
        if b in branch:
            return {
                "level": "CORE",
                "instruction": (
                    "This student is from a core CS/IT/AI/ECE branch. "
                    "Give a COMPLETE, DETAILED, TECHNICAL answer. "
                    "Cover all relevant concepts, sub-topics, algorithms, formulas, and examples "
                    "exactly as described in the syllabus. Use proper technical terminology. "
                    "Structure your answer with clear headings and sub-points. Be thorough — "
                    "the student needs this for exams and lab work."
                )
            }
    for b in RELATED_BRANCHES:
        if b in branch:
            return {
                "level": "RELATED",
                "instruction": (
                    "This student is from a non-CS branch (Mechanical, Civil, etc.). "
                    "Give a SIMPLE, CLEAR answer in plain language. Avoid heavy jargon. "
                    "Use a short definition, brief context, and a real-world analogy if helpful. "
                    "If the topic is not very relevant to their branch, politely note it and "
                    "give a brief general explanation."
                )
            }
    return {
        "level": "OTHER",
        "instruction": (
            "Give a clear, concise answer. Include a brief definition and the key points "
            "from the syllabus. Avoid unnecessary jargon."
        )
    }

# =================================================================================
# ACTION 1 — VIEW FULL SYLLABUS   (Claude + PDF, needs subject_code)
# Returns the complete syllabus for the given subject exactly as in the PDF.
# =================================================================================
def view_syllabus_from_pdf(pdf_path: str, subject_code: str, semester: str) -> str:
    messages = [{
        "role": "user",
        "content": [
            make_pdf_content_block(pdf_path, subject_code, max_pages=60),
            {
                "type": "text",
                "text": f"""Read this syllabus PDF carefully.

Find the subject with code: **{subject_code}**
Semester: {semester}

Return the COMPLETE syllabus for that subject exactly as it appears:
- Subject name and code
- L T P C credits
- Course Objectives (all points)
- All Units with complete topic details
- Course Outcomes (all)
- Text books / Reference books

If not found, respond: "Subject code {subject_code} was not found in this PDF."
Do not summarize. Return full content."""
            }
        ]
    }]
    return _claude_call(messages, max_tokens=8192)

# =================================================================================
# ACTION 2 — ASK ABOUT SYLLABUS   (Claude + PDF, needs subject_code)
# Answers the student's question using the PDF, depth depends on branch.
# Does NOT require the syllabus to be loaded first — reads PDF directly.
# =================================================================================
def ask_syllabus_from_pdf(pdf_path: str, subject_code: str, semester: str,
                          question: str, reg_branch: str) -> str:
    profile = _get_branch_profile(reg_branch)

    prompt = f"""You are an AI Teaching Assistant for engineering students.

STUDENT PROFILE:
- Branch      : {reg_branch}
- Subject Code: {subject_code}
- Semester    : {semester}
- Level       : {profile["level"]}

ANSWERING INSTRUCTION:
{profile["instruction"]}

RULES:
- Answer strictly based on the syllabus PDF provided.
- If the topic is in the syllabus, explain it exactly as covered there.
- If the topic is NOT in the syllabus, clearly state:
  "This topic is not covered in the {subject_code} syllabus."
  Then give a brief general explanation appropriate for this student's branch level.
- Never fabricate syllabus content.
- Format clearly with headings and bullet points where needed.

Student Question: {question}

Answer now:"""

    messages = [{
        "role": "user",
        "content": [
            make_pdf_content_block(pdf_path, subject_code, max_pages=30),
            {"type": "text", "text": prompt}
        ]
    }]
    return _claude_call(messages, max_tokens=3000)

# =================================================================================
# ACTION 3 — QUICK ANSWER   (Groq only)
# No PDF, no subject code, no branch — just answers the question like ChatGPT.
# =================================================================================
def quick_answer_groq(question: str) -> str:
    r = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant for engineering students. "
                    "Answer any question clearly and concisely. "
                    "Explain concepts, solve problems, give examples. "
                    "Format with headings and bullet points where useful. "
                    "Be direct — do not ask for clarification, just answer."
                )
            },
            {"role": "user", "content": question}
        ],
        max_tokens=1500,
        temperature=0.7,
    )
    return r.choices[0].message.content

# =================================================================================
# ACTION 4 — GENERATE CODE   (Groq only)
# =================================================================================
def generate_code_groq(question: str, lang: str) -> str:
    r = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are an expert {lang} programmer. "
                    f"Generate only complete, executable {lang} code. "
                    "No markdown fences. No explanation before or after. Raw code only."
                )
            },
            {"role": "user", "content": question}
        ],
        max_tokens=2000,
        temperature=0.2,
    )
    lines = [l for l in r.choices[0].message.content.splitlines()
             if not l.strip().startswith("```")]
    return "\n".join(lines).strip()

# =================================================================================
# IMAGES — DuckDuckGo diagram search
# =================================================================================
def show_diagrams(query: str):
    images = []
    try:
        with DDGS() as ddgs:
            results = ddgs.images(
                keywords=query + " diagram",
                region="wt-wt",
                safesearch="off",
                max_results=9,
            )
            for r in results:
                url = r.get("image", "")
                if url:
                    images.append(url)
    except Exception as e:
        st.error(f"❌ Image search failed: {e}")
        return

    if not images:
        st.warning("No diagrams found. Try a more specific topic.")
        return

    st.markdown(
        f'<div class="info-box">🔍 Showing diagrams for: <strong>{query}</strong></div>',
        unsafe_allow_html=True
    )

    cols  = st.columns(3)
    shown = 0
    for url in images:
        if shown >= 6:
            break
        try:
            cols[shown % 3].image(url, use_column_width=True)
            shown += 1
        except Exception:
            continue  # skip broken URLs silently

    if shown == 0:
        st.warning("Images found but could not be loaded. Try a different search term.")

# =================================================================================
# PDF EXPORT BUILDER
# =================================================================================
def build_syllabus_pdf(result: str, subject_code: str, reg_branch: str, semester: str) -> bytes:
    LEFT = RIGHT = 15
    TOP  = 15
    CW   = 210 - LEFT - RIGHT

    def to_latin1(text: str) -> str:
        table = {
            "\u2022":"-", "\u00b7":"-", "\u25cf":"-", "\u25a0":"-",
            "\u2013":"-", "\u2014":"-", "\u2015":"-",
            "\u2018":"'", "\u2019":"'",
            "\u201c":'"', "\u201d":'"',
            "\u2026":"...",
            "\u2192":"->", "\u2190":"<-", "\u2194":"<->",
            "\u00d7":"x",  "\u00f7":"/",
            "\u00b0":" deg", "\u00b1":"+/-",
            "\u2264":"<=", "\u2265":">=", "\u2260":"!=",
            "\u221a":"sqrt", "\u03c0":"pi",
            "\u03b1":"alpha", "\u03b2":"beta",  "\u03b3":"gamma",
            "\u03b4":"delta", "\u03bc":"mu",    "\u03c3":"sigma",
            "\u03c9":"omega", "\u03bb":"lambda",
            "\u00e9":"e", "\u00e8":"e", "\u00ea":"e",
            "\u00e0":"a", "\u00e2":"a", "\u00f4":"o",
            "\u00fc":"u", "\u00e4":"a", "\u00f6":"o",
        }
        for ch, rep in table.items():
            text = text.replace(ch, rep)
        text = unicodedata.normalize("NFKD", text)
        return text.encode("latin-1", "ignore").decode("latin-1")

    def ct(text): return to_latin1(str(text))

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(LEFT, TOP, RIGHT)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_fill_color(79, 99, 231)
    pdf.rect(0, 0, 210, 28, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_xy(LEFT, 7)
    pdf.cell(0, 8, ct(f"Syllabus | {subject_code.upper()}"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(LEFT, 17)
    pdf.cell(0, 7, ct(f"{reg_branch}   |   {semester}"), ln=True)
    pdf.set_text_color(26, 29, 46)
    pdf.set_xy(LEFT, 34)
    right_edge = LEFT + CW

    for raw_line in result.splitlines():
        line     = to_latin1(raw_line)
        stripped = line.strip()

        if not stripped:
            pdf.ln(2); continue
        if stripped in ("**", "__"):
            continue

        if stripped.startswith("# ") and not stripped.startswith("## "):
            content = stripped[2:].strip()
            if not content: continue
            pdf.set_font("Helvetica","B",13); pdf.set_fill_color(235,238,255); pdf.set_text_color(26,29,46)
            pdf.multi_cell(CW,9,content,fill=True); pdf.ln(2); pdf.set_font("Helvetica","",10)

        elif stripped.startswith("## ") and not stripped.startswith("### "):
            content = stripped[3:].strip()
            if not content: continue
            pdf.set_font("Helvetica","B",12); pdf.set_text_color(79,99,231)
            pdf.multi_cell(CW,8,content)
            y=pdf.get_y(); pdf.set_draw_color(79,99,231); pdf.set_line_width(0.4)
            pdf.line(LEFT,y,right_edge,y); pdf.ln(4)
            pdf.set_text_color(26,29,46); pdf.set_font("Helvetica","",10)

        elif stripped.startswith("### "):
            content = stripped[4:].strip()
            if not content: continue
            pdf.set_font("Helvetica","B",11); pdf.set_text_color(26,29,46)
            pdf.multi_cell(CW,7,content); pdf.ln(1); pdf.set_font("Helvetica","",10)

        elif stripped.startswith("#### "):
            content = stripped[5:].strip()
            if not content: continue
            pdf.set_font("Helvetica","BI",10); pdf.set_text_color(26,29,46)
            pdf.multi_cell(CW,6,content); pdf.set_font("Helvetica","",10)

        elif (stripped.startswith("**") and stripped.endswith("**") and len(stripped)>4) or \
             (stripped.startswith("__") and stripped.endswith("__") and len(stripped)>4):
            content = stripped[2:-2].strip()
            if not content: continue
            pdf.set_font("Helvetica","B",10); pdf.set_text_color(26,29,46)
            pdf.multi_cell(CW,6,content); pdf.set_font("Helvetica","",10)

        elif stripped.startswith("- ") or stripped.startswith("* "):
            indent    = max(0,(len(raw_line)-len(raw_line.lstrip()))//2)
            prefix    = ("  "*indent)+"*  "
            content   = stripped[2:].strip()
            if not content: continue
            indent_mm = indent*4
            pdf.set_font("Helvetica","",10); pdf.set_text_color(26,29,46)
            pdf.set_x(LEFT+indent_mm); pdf.multi_cell(CW-indent_mm,6,prefix+content)

        elif len(stripped)>2 and stripped[0].isdigit() and stripped[1] in ".)":
            pdf.set_font("Helvetica","",10); pdf.set_text_color(26,29,46)
            pdf.set_x(LEFT+4); pdf.multi_cell(CW-4,6,stripped)

        elif stripped in ("---","***","___"):
            y=pdf.get_y()+2; pdf.set_draw_color(200,204,240); pdf.set_line_width(0.3)
            pdf.line(LEFT,y,right_edge,y); pdf.ln(5)

        elif stripped.startswith("|"):
            cells=[c.strip() for c in stripped.split("|") if c.strip() and c.strip()!="---"]
            if cells:
                pdf.set_font("Helvetica","",9); pdf.set_text_color(26,29,46)
                pdf.multi_cell(CW,5,"  |  ".join(cells))

        else:
            pdf.set_font("Helvetica","",10); pdf.set_text_color(26,29,46)
            pdf.set_x(LEFT); pdf.multi_cell(CW,6,line)

    total_pages = pdf.page
    for page_num in range(1, total_pages+1):
        pdf.page = page_num
        pdf.set_y(-14); pdf.set_font("Helvetica","I",8); pdf.set_text_color(107,114,160)
        pdf.set_x(LEFT)
        pdf.cell(CW-20,8,ct(f"AI Teaching Assistant  |  {subject_code.upper()}  |  {reg_branch}  |  {semester}"))
        pdf.cell(20,8,ct(f"Page {page_num} / {total_pages}"),align="R")

    return bytes(pdf.output())

# =================================================================================
# VALIDATION
# =================================================================================
def _pdf_ok(reg_branch: str):
    if "⚠️" in reg_branch:
        st.error("❌ No PDFs found. Add PDFs to `syllabus_pdfs/` folder.")
        return None
    p = find_pdf(reg_branch)
    if not p or not os.path.isfile(p):
        st.error(f"❌ PDF not found for **{reg_branch}**. Check `syllabus_pdfs/`.")
        return None
    return p

# =================================================================================
# MAIN UI
# =================================================================================
options = get_options()

st.markdown('<div class="sec">📚 Academic Details</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
reg_branch   = c1.selectbox("Regulation & Branch", options)
semester     = c2.selectbox("Semester", [f"SEM{i}" for i in range(1, 9)])
subject_code = c3.text_input(
    "Subject Code",
    placeholder="e.g. 23AD101, 20MA1T01  (needed for syllabus actions)"
)

# PDF status
if "⚠️" not in reg_branch:
    pdf_path = find_pdf(reg_branch)
    if pdf_path and os.path.isfile(pdf_path):
        size_mb = os.path.getsize(pdf_path) / (1024*1024)
        try:
            total_pages = len(PdfReader(pdf_path).pages)
            page_info   = f"{total_pages} pages"
        except Exception:
            page_info = ""
        st.markdown(
            f'<div class="info-box">📄 <strong>{os.path.basename(pdf_path)}</strong>'
            f'&nbsp;·&nbsp;{size_mb:.1f} MB&nbsp;·&nbsp;{page_info}'
            f'&nbsp;·&nbsp;Claude reads this PDF directly</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="warn-box">⚠️ PDF not found. Add your PDFs to <strong>syllabus_pdfs/</strong></div>',
            unsafe_allow_html=True
        )

st.markdown('<div class="sec">❓ Your Question</div>', unsafe_allow_html=True)
question = st.text_area("", placeholder="Ask anything — topics, concepts, code problems, general doubts…", height=100)

# Branch badge
if "⚠️" not in reg_branch:
    _prof = _get_branch_profile(reg_branch)
    _level_colors = {
        "CORE":    ("🔬","#00a878","Core branch — full technical answers"),
        "RELATED": ("📘","#e6a800","Non-CS branch — simplified answers"),
        "OTHER":   ("📖","#4f63e7","General branch — concise answers"),
    }
    _emoji, _color, _label = _level_colors[_prof["level"]]
    st.markdown(
        f'<div style="background:rgba(0,0,0,0.03);border:1px solid {_color}33;'
        f'border-radius:8px;padding:6px 14px;font-size:0.8rem;color:{_color};'
        f'margin-bottom:0.4rem;display:inline-block;">'
        f'{_emoji} <strong>{reg_branch}</strong> → <strong>{_prof["level"]}</strong> — {_label}</div>',
        unsafe_allow_html=True
    )

# Action guide
st.markdown(
    '<div class="route-box">'
    '📘 <b>View Full Syllabus</b> — Claude reads PDF → returns complete syllabus '
    '<em>(needs subject code)</em>&nbsp;&nbsp;|&nbsp;&nbsp;'
    '🎯 <b>Ask About Syllabus</b> — Claude answers from PDF, branch-aware depth '
    '<em>(needs subject code)</em>&nbsp;&nbsp;|&nbsp;&nbsp;'
    '⚡ <b>Quick Answer</b> — Groq answers instantly like ChatGPT '
    '<em>(no code needed)</em>&nbsp;&nbsp;|&nbsp;&nbsp;'
    '💻 <b>Generate Code</b> — Groq writes code '
    '<em>(no code needed)</em>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown('<div class="sec">⚙️ Actions</div>', unsafe_allow_html=True)
b1, b2, b3, b4 = st.columns(4)
btn_view    = b1.button("📘 View Full Syllabus")
btn_ask     = b2.button("🎯 Ask About Syllabus")
btn_quick   = b3.button("⚡ Quick Answer")
btn_code    = b4.button("💻 Generate Code")

btn_diagram = st.button("📊 Search Diagrams / Flowcharts")
language    = st.selectbox("Programming Language (for Generate Code)", ["Python","C","C++","Java"])

st.divider()
st.markdown('<div class="sec">📤 Output</div>', unsafe_allow_html=True)
out = st.empty()

# ─────────────────────────────────────────────────────────────────────────────
# ACTION 1 — View Full Syllabus   (Claude + PDF)
# ─────────────────────────────────────────────────────────────────────────────
if btn_view:
    if not subject_code.strip():
        st.warning("⚠️ Enter a subject code to view its full syllabus.")
    else:
        p = _pdf_ok(reg_branch)
        if p:
            with st.spinner(f"📄 Claude is reading the PDF for **{subject_code.upper()}**…"):
                try:
                    result = view_syllabus_from_pdf(p, subject_code.strip().upper(), semester)

                    truncation_hints = [
                        result.rstrip().endswith(("...", "…")),
                        len(result.strip()) < 300,
                        result.strip().endswith(("to","the","and","of","in","a","is")),
                    ]
                    seems_truncated = any(truncation_hints) and len(result) < 2000

                    st.session_state["syllabus_result"] = result
                    st.session_state["syllabus_meta"]   = {
                        "subject_code": subject_code.strip().upper(),
                        "reg_branch":   reg_branch,
                        "semester":     semester,
                    }

                    st.markdown(
                        f'<div class="ok-box">✅ Syllabus loaded: '
                        f'<strong>{subject_code.upper()}</strong> · {reg_branch} · {semester} '
                        f'({len(result):,} characters)</div>',
                        unsafe_allow_html=True
                    )
                    if seems_truncated:
                        st.warning("⚠️ Response looks short — verify the subject code or try again.")

                    out.markdown(result)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# Persistent download button after view
if st.session_state.get("syllabus_result"):
    meta = st.session_state["syllabus_meta"]
    try:
        pdf_bytes = build_syllabus_pdf(
            result       = st.session_state["syllabus_result"],
            subject_code = meta["subject_code"],
            reg_branch   = meta["reg_branch"],
            semester     = meta["semester"],
        )
        fname = (
            f"syllabus_{meta['subject_code']}_"
            f"{meta['reg_branch'].replace(' ','')}_{meta['semester']}.pdf"
        )
        st.download_button(
            label               = "⬇️ Download Syllabus as PDF",
            data                = pdf_bytes,
            file_name           = fname,
            mime                = "application/pdf",
            use_container_width = True,
        )
    except Exception as e:
        st.warning(f"⚠️ PDF download unavailable: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# ACTION 2 — Ask About Syllabus   (Claude + PDF)
# Does NOT require loading syllabus first. Reads PDF directly and answers.
# Branch-aware: CORE branches get full technical depth, others get simplified.
# ─────────────────────────────────────────────────────────────────────────────
if btn_ask:
    if not subject_code.strip():
        st.warning("⚠️ Enter a subject code so Claude knows which syllabus to reference.")
    elif not question.strip():
        st.warning("⚠️ Enter a question.")
    else:
        p = _pdf_ok(reg_branch)
        if p:
            profile     = _get_branch_profile(reg_branch)
            level_emoji = {"CORE":"🔬","RELATED":"📘","OTHER":"📖"}.get(profile["level"],"📖")
            with st.spinner(
                f"{level_emoji} Claude is answering for **{reg_branch}** "
                f"({profile['level']} level) using subject **{subject_code.upper()}**…"
            ):
                try:
                    result = ask_syllabus_from_pdf(
                        p,
                        subject_code.strip().upper(),
                        semester,
                        question.strip(),
                        reg_branch,
                    )
                    out.markdown(result)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# ACTION 3 — Quick Answer   (Groq only — no PDF, no subject code, no branch)
# Answers any question directly like ChatGPT using Groq.
# ─────────────────────────────────────────────────────────────────────────────
if btn_quick:
    if not question.strip():
        st.warning("⚠️ Enter a question.")
    else:
        with st.spinner("⚡ Groq is thinking…"):
            try:
                result = quick_answer_groq(question.strip())
                out.markdown(result)
            except Exception as e:
                st.error(f"❌ Groq error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# ACTION 4 — Generate Code   (Groq only)
# ─────────────────────────────────────────────────────────────────────────────
if btn_code:
    if not question.strip():
        st.warning("⚠️ Describe what code you need.")
    else:
        with st.spinner(f"💻 Groq is generating {language} code…"):
            try:
                code = generate_code_groq(question.strip(), language)
                st.session_state["ai_code"]      = code
                st.session_state["ai_code_lang"] = language
                st.code(code, language=language.lower())
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Search Diagrams
# ─────────────────────────────────────────────────────────────────────────────
if btn_diagram:
    if not question.strip():
        st.warning("⚠️ Enter a topic to search diagrams for.")
    else:
        with st.spinner("🔍 Searching for diagrams…"):
            show_diagrams(question.strip())

# =================================================================================
# CODE RUNNER
# =================================================================================
if st.session_state.get("ai_code", "").strip():
    st.markdown('<div class="sec">🛠️ Code Editor & Runner</div>', unsafe_allow_html=True)
    run_lang   = st.session_state.get("ai_code_lang", "Python")
    edited     = st.text_area("Edit code before running", st.session_state["ai_code"], height=280)
    user_input = st.text_area("Program Input (optional)", "", placeholder="stdin input if needed…")
    if st.button("▶  Run Code"):
        try:
            if run_lang == "Python":
                f = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
                f.write(edited.encode()); f.close()
                with st.spinner("⚙️ Executing…"):
                    r = subprocess.run(
                        [sys.executable, f.name],
                        input=user_input,
                        capture_output=True, text=True, timeout=30
                    )
                st.success("✅ Done") if r.returncode == 0 else st.error("❌ Runtime error")
                st.code(r.stdout or r.stderr, language="text")
            else:
                st.info(f"ℹ️ Copy and run {run_lang} in your local environment.")
        except subprocess.TimeoutExpired:
            st.error("⏱️ Timed out (30 s).")
        except Exception as e:
            st.error(f"Error: {e}")

# =================================================================================
# SIDEBAR
# =================================================================================
with st.sidebar:
    st.markdown("### 🛠️ Setup")
    st.markdown("""
**1. Add your PDFs**
```
syllabus_pdfs/
├── r23aidssyllabus.pdf
├── r23csesyllabus.pdf
├── r20aimlsyllabus.pdf
└── ...
```
**2. Set API Keys**
```bash
GROQ_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```
**3. Install & Run**
```bash
pip install streamlit groq anthropic \\
    duckduckgo-search pypdf fpdf2
streamlit run app.py
```
    """)

    st.divider()
    st.markdown("### 🔀 Button Guide")
    st.markdown("""
| Button | Engine | Subject Code? |
|--------|--------|---------------|
| 📘 View Syllabus | Claude + PDF | ✅ Required |
| 🎯 Ask Syllabus | Claude + PDF | ✅ Required |
| ⚡ Quick Answer | Groq only | ❌ Not needed |
| 💻 Generate Code | Groq only | ❌ Not needed |
| 📊 Diagrams | DuckDuckGo | ❌ Not needed |
    """)

    st.divider()
    st.markdown("### 📂 Detected PDFs")
    if PDF_MAP:
        for key, fname in sorted(PDF_MAP.items()):
            try:
                pages = len(PdfReader(os.path.join(PDF_FOLDER, fname)).pages)
                st.markdown(f"✅ `{fname}` · {pages}p")
            except Exception:
                st.markdown(f"✅ `{fname}`")
    else:
        st.warning("No PDFs in `syllabus_pdfs/`")

    if st.session_state.get("syllabus_result"):
        st.divider()
        st.markdown("### ⬇️ Last Loaded Syllabus")
        meta = st.session_state["syllabus_meta"]
        st.markdown(f"**{meta['subject_code']}** · {meta['reg_branch']} · {meta['semester']}")
        try:
            pdf_bytes = build_syllabus_pdf(
                result       = st.session_state["syllabus_result"],
                subject_code = meta["subject_code"],
                reg_branch   = meta["reg_branch"],
                semester     = meta["semester"],
            )
            st.download_button(
                label     = "⬇️ Download PDF",
                data      = pdf_bytes,
                file_name = f"syllabus_{meta['subject_code']}.pdf",
                mime      = "application/pdf",
                key       = "sidebar_dl",
            )
        except Exception as e:
            st.warning(f"PDF unavailable: {e}")
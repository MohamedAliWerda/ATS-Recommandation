import os
import re
import PyPDF2 as pdf
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# ── Environment & Model ──────────────────────────────────────────────────────
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="ATS Resume Checker", page_icon="🎯", layout="wide")

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base / Background ── */
[data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 50%, #0a1628 100%);
    min-height: 100vh;
}
[data-testid="stHeader"]  { background: rgba(0,0,0,0); }
[data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #0d1b2a 0%, #0a0e1a 100%);
    border-right: 1px solid rgba(0,210,200,0.15);
}

/* ── Typography ── */
html, body, [class*="css"] {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}
h1, h2, h3, h4, h5, h6 { color: #e8f4f8 !important; }
p, li, span, div { color: #c8d8e8; }
label { color: #a0b8c8 !important; font-weight: 500; }

/* ── Hero Banner ── */
.hero-banner {
    background: linear-gradient(135deg, rgba(0,210,200,0.12) 0%, rgba(100,120,255,0.12) 100%);
    border: 1px solid rgba(0,210,200,0.25);
    border-radius: 20px;
    padding: 2.5rem 3rem;
    text-align: center;
    margin-bottom: 2.5rem;
    backdrop-filter: blur(10px);
}
.hero-banner h1 {
    font-size: 2.6rem !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, #00d2c8, #6478ff, #00d2c8);
    background-size: 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.5rem 0 !important;
}
.hero-banner p {
    color: #a0b8c8 !important;
    font-size: 1.05rem;
    margin: 0;
}

/* ── Glass Cards ── */
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(0,210,200,0.18);
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}
.glass-card h3 {
    color: #00d2c8 !important;
    font-size: 1rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 1rem 0;
}

/* ── Section Labels ── */
.section-label {
    color: #00d2c8 !important;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
    display: block;
}

/* ── Score Badge ── */
.score-badge {
    display: inline-block;
    font-size: 3rem;
    font-weight: 900;
    line-height: 1;
    background: linear-gradient(135deg, #00d2c8, #6478ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.score-label {
    font-size: 0.8rem;
    color: #7090a0 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── Result Section Cards ── */
.result-section {
    background: rgba(255,255,255,0.03);
    border-left: 3px solid #00d2c8;
    border-radius: 0 12px 12px 0;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.2rem;
}
.result-section.keywords  { border-left-color: #ff6b6b; }
.result-section.summary   { border-left-color: #6478ff; }
.result-section.suggest   { border-left-color: #ffd166; }
.result-section.success   { border-left-color: #06d6a0; }
.result-section h4 {
    margin: 0 0 0.6rem 0;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.result-section.match    h4 { color: #00d2c8 !important; }
.result-section.keywords h4 { color: #ff6b6b !important; }
.result-section.summary  h4 { color: #6478ff !important; }
.result-section.suggest  h4 { color: #ffd166 !important; }
.result-section.success  h4 { color: #06d6a0 !important; }
.result-section p { color: #c8d8e8 !important; margin: 0; line-height: 1.7; }

/* ── Streamlit Widget Overrides ── */
.stTextArea textarea {
    background: rgba(255,255,255,0.05) !important;
    color: #e8f4f8 !important;
    border: 1px solid rgba(0,210,200,0.25) !important;
    border-radius: 10px !important;
    font-size: 0.95rem !important;
}
.stTextArea textarea:focus {
    border-color: #00d2c8 !important;
    box-shadow: 0 0 0 2px rgba(0,210,200,0.15) !important;
}
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.04) !important;
    border: 2px dashed rgba(0,210,200,0.3) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #00d2c8 !important;
    background: rgba(0,210,200,0.05) !important;
}

/* ── Primary Button ── */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #00d2c8, #6478ff) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.85rem 2.5rem !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em;
    transition: all 0.2s ease;
    box-shadow: 0 4px 20px rgba(0,210,200,0.25) !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(0,210,200,0.4) !important;
    filter: brightness(1.1);
}
.stButton > button:active { transform: translateY(0); }

/* ── Progress Bar ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #00d2c8, #6478ff) !important;
    border-radius: 8px;
}
.stProgress > div > div > div {
    background: rgba(255,255,255,0.06) !important;
    border-radius: 8px;
}

/* ── Metric Boxes ── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(0,210,200,0.15);
    border-radius: 12px;
    padding: 1rem 1.2rem;
}
[data-testid="stMetricLabel"] > div { color: #7090a0 !important; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetricValue"] > div { color: #00d2c8 !important; font-size: 1.8rem !important; font-weight: 800 !important; }

/* ── Divider ── */
hr { border-color: rgba(0,210,200,0.15) !important; margin: 2rem 0 !important; }

/* ── Sidebar Styles ── */
.sidebar-tip {
    background: rgba(0,210,200,0.07);
    border: 1px solid rgba(0,210,200,0.2);
    border-radius: 10px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.8rem;
    font-size: 0.88rem;
    color: #a0b8c8 !important;
}
.sidebar-tip strong { color: #00d2c8 !important; }

/* ── Alert overrides ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 How It Works")
    st.markdown('<div class="sidebar-tip"><strong>Step 1</strong><br>Paste the job description from the listing you are targeting.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tip"><strong>Step 2</strong><br>Upload your resume as a PDF file.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tip"><strong>Step 3</strong><br>Click <em>Analyse Resume</em> and get your ATS score instantly.</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📋 What You Get")
    st.markdown("""
- **ATS Match Score** — % alignment with JD  
- **Missing Keywords** — gaps to fill  
- **Profile Summary** — overall evaluation  
- **Enhancement Tips** — skills & achievements  
- **Success Rate** — predicted application outcome  
""")
    st.markdown("---")
    st.markdown('<p style="color:#4a6070;font-size:0.78rem;text-align:center;">Powered by Gemini AI</p>', unsafe_allow_html=True)

# ── Hero Banner ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1>🎯 ATS Resume Checker</h1>
    <p>Instantly analyse your resume against any job description — get your ATS score, missing keywords & actionable tips.</p>
</div>
""", unsafe_allow_html=True)

# ── Input Section ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<span class="section-label">📄 Job Description</span>', unsafe_allow_html=True)
    jd = st.text_area(
        "Job Description",
        height=260,
        placeholder="Paste the full job description here…",
        label_visibility="collapsed",
    )

with col_right:
    st.markdown('<span class="section-label">📎 Your Resume (PDF)</span>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload Resume",
        type="pdf",
        help="Upload your resume as a PDF",
        label_visibility="collapsed",
    )
    if uploaded_file:
        st.success(f"✅ **{uploaded_file.name}** uploaded successfully")
    else:
        st.info("📤 Drag & drop or click to upload your PDF resume")

st.markdown("<br>", unsafe_allow_html=True)
btn_col = st.columns([1, 2, 1])[1]
with btn_col:
    submit = st.button("🚀 Analyse Resume", use_container_width=True)

# ── Processing ────────────────────────────────────────────────────────────────
if submit:
    if not jd.strip():
        st.warning("⚠️ Please paste a job description before analysing.")
    elif uploaded_file is None:
        st.warning("⚠️ Please upload your resume (PDF) before analysing.")
    else:
        # Extract text from PDF
        with st.spinner("🔍 Reading your resume…"):
            reader = pdf.PdfReader(uploaded_file)
            extracted_text = "".join(
                reader.pages[i].extract_text() or "" for i in range(len(reader.pages))
            )

        input_prompt = f"""
        You are an advanced and highly experienced Applicant Tracking System (ATS) with specialized knowledge in the tech industry, including but not limited to software engineering, data science, data analysis, big data engineering, AI/ML, and cloud engineering. Your primary task is to meticulously evaluate resumes based on the provided job description. Considering the highly competitive job market, your goal is to offer the best possible guidance for enhancing resumes.

        Responsibilities:
        1. Assess resumes with a high degree of accuracy against the job description.
        2. Identify and highlight missing keywords crucial for the role.
        3. Provide a percentage match score reflecting the resume's alignment with the job requirements on the scale of 1-100.
        4. Offer detailed feedback for improvement to help candidates stand out.
        5. Analyze the Resume, Job description and industry trends and provide personalized suggestions for skills, keywords and achievements that can enhance the provided resume.
        6. Provide suggestions for improving the language, tone and clarity of the resume content.
        7. Provide users with insights into the performance of their resumes. Provide an application success rate on the scale of 1-100.

        If the same job description and resume is provided, always give the same result.

        Resume: {extracted_text}
        Description: {jd}

        Respond ONLY in this exact format with these exact section headers:
        • Job Description Match: [number 1-100]%
        • Missing Keywords: [comma-separated list of missing keywords]
        • Profile Summary: [2-4 sentence summary of the candidate's profile fit]
        • Personalized suggestions for skills, keywords and achievements that can enhance the provided resume: [bullet points or paragraph with specific suggestions]
        • Application Success rates: [number 1-100]%
        """

        with st.spinner("🤖 Analysing with AI — this takes a few seconds…"):
            response = model.generate_content(input_prompt)
            raw = response.text

        st.markdown("---")
        st.markdown("## 📊 Analysis Results")

        # ── Parse scores for visual metrics ──────────────────────────────────
        match_score, success_score = 0, 0
        m = re.search(r"Job Description Match[:\s]*(\d+)", raw, re.IGNORECASE)
        if m:
            match_score = min(int(m.group(1)), 100)
        s = re.search(r"Application Success rates?[:\s]*(\d+)", raw, re.IGNORECASE)
        if s:
            success_score = min(int(s.group(1)), 100)

        # ── Score Metrics Row ─────────────────────────────────────────────────
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.metric("🎯 ATS Match Score", f"{match_score}%")
        with mc2:
            st.metric("📈 Application Success Rate", f"{success_score}%")
        with mc3:
            overall = (match_score + success_score) // 2
            st.metric("⭐ Overall Score", f"{overall}%")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Visual Progress Bars ──────────────────────────────────────────────
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            st.markdown('<span class="section-label">ATS Match</span>', unsafe_allow_html=True)
            st.progress(match_score / 100)
        with pcol2:
            st.markdown('<span class="section-label">Application Success Rate</span>', unsafe_allow_html=True)
            st.progress(success_score / 100)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Structured Result Sections ────────────────────────────────────────
        def extract_section(text, header):
            """Extract the content after a bullet-point section header."""
            pattern = rf"•\s*{re.escape(header)}[:\s]*(.*?)(?=\n•|\Z)"
            m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            return m.group(1).strip() if m else ""

        sections = [
            ("match",    "🎯 Job Description Match",     "Job Description Match",        "match"),
            ("keywords", "🔑 Missing Keywords",           "Missing Keywords",             "keywords"),
            ("summary",  "👤 Profile Summary",            "Profile Summary",              "summary"),
            ("suggest",  "💡 Enhancement Suggestions",    "Personalized suggestions for skills, keywords and achievements that can enhance the provided resume", "suggest"),
            ("success",  "📈 Application Success Rate",   "Application Success rates",    "success"),
        ]

        for css_class, title, header, _ in sections:
            content = extract_section(raw, header)
            if not content:
                continue
            st.markdown(f"""
<div class="result-section {css_class}">
    <h4>{title}</h4>
    <p>{content.replace(chr(10), '<br>')}</p>
</div>
""", unsafe_allow_html=True)

        # ── Fallback: show raw text if parsing fails completely ───────────────
        all_empty = all(not extract_section(raw, h) for _, _, h, _ in sections)
        if all_empty:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.write(raw)
            st.markdown('</div>', unsafe_allow_html=True)

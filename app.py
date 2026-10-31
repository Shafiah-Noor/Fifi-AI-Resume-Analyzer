
import io
import json
import re
import time

import streamlit as st
from PyPDF2 import PdfReader
from google import genai
from google.genai import errors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable
from xml.sax.saxutils import escape


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Fifi AI Resume Analyzer",
    page_icon="🐥",
    layout="wide"
)


# =====================================================
# GREEN AND BROWN THEME
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #F7F7EF;
    color: #29291F;
}

[data-testid="stHeader"] {
    background-color: #F7F7EF;
}

[data-testid="stSidebar"] {
    background-color: #E8EBDD;
}

h1, h2, h3, h4, p, label, span {
    color: #29291F;
}

.main-title {
    color: #315B3A;
    font-size: 38px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #76543B;
    font-size: 15px;
    margin-bottom: 25px;
}

.section-title {
    color: #315B3A;
    font-size: 21px;
    font-weight: 750;
    border-bottom: 2px solid #A7B99A;
    padding-bottom: 7px;
    margin-top: 18px;
}

.stButton > button,
.stDownloadButton > button {
    background-color: #456B4A;
    color: white !important;
    border-radius: 9px;
    border: 1px solid #456B4A;
    font-weight: 700;
    padding: 10px 20px;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background-color: #76543B;
    color: white !important;
    border-color: #76543B;
}

div[data-testid="stMetric"] {
    background-color: #E8EBDD;
    border: 1px solid #C4D0BA;
    padding: 15px;
    border-radius: 10px;
}

div[data-testid="stExpander"] {
    border: 1px solid #C8D1BE;
    border-radius: 10px;
}

textarea,
input {
    background-color: white !important;
}

.footer {
    text-align: center;
    color: #76543B;
    font-size: 13px;
    padding: 25px;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# HEADER
# =====================================================

st.markdown(
    '<div class="main-title">🐥 Fifi AI Resume Analyzer</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Analyze your resume. Improve your skills. Build your career.</div>',
    unsafe_allow_html=True
)


# =====================================================
# GEMINI SETTINGS
# =====================================================

MODEL_NAME = "gemini-3.6-flash"

with st.expander("⚙️ AI Settings", expanded=True):

    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key = ""

    if api_key:
        st.success("Gemini API key loaded securely.")
        st.info("AI Model: Gemini 3.6 Flash")
    else:
        st.warning(
            "Add GEMINI_API_KEY to .streamlit/secrets.toml"
        )


# =====================================================
# PDF TEXT EXTRACTION
# =====================================================

def extract_resume_text(uploaded_file):

    try:

        uploaded_file.seek(0)

        reader = PdfReader(uploaded_file)

        pages = []

        for page in reader.pages:

            page_text = page.extract_text() or ""

            if page_text.strip():
                pages.append(page_text)

        result = "\n".join(pages).strip()

        if not result:

            raise ValueError(
                "No readable text found. "
                "The PDF may be scanned or image-based."
            )

        return result

    except Exception as e:

        raise ValueError(
            f"Could not read the PDF: {e}"
        )


# =====================================================
# GEMINI API FUNCTION
# =====================================================

def call_gemini(prompt):

    if not api_key:

        raise ValueError(
            "Gemini API key is missing. "
            "Add it to .streamlit/secrets.toml."
        )

    client = genai.Client(
        api_key=api_key.strip()
    )

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            answer = getattr(
                response,
                "text",
                None
            )

            if not answer:

                raise ValueError(
                    "Gemini returned an empty response."
                )

            return answer.strip()

        except errors.ServerError as e:

            if attempt == 2:

                raise RuntimeError(
                    "Gemini is temporarily busy. "
                    "Please wait and try again."
                ) from e

            time.sleep(2 * (attempt + 1))

        except Exception as e:

            message = str(e)

            if "404" in message or "NOT_FOUND" in message:

                raise RuntimeError(
                    f"Model '{MODEL_NAME}' was not found "
                    "or is not available for your API key. "
                    "The model ID needs to be verified."
                ) from e

            if "429" in message or "RESOURCE_EXHAUSTED" in message:

                raise RuntimeError(
                    "Gemini quota or rate limit reached. "
                    "Please wait and try again."
                ) from e

            raise RuntimeError(
                f"Gemini API error: {message}"
            ) from e

    raise RuntimeError("Gemini request failed.")


# =====================================================
# TF-IDF SIMILARITY SCORE
# =====================================================

def calculate_similarity(resume, job):

    try:

        vectorizer = TfidfVectorizer(
            stop_words="english"
        )

        matrix = vectorizer.fit_transform([
            resume,
            job
        ])

        score = cosine_similarity(
            matrix[0:1],
            matrix[1:2]
        )[0][0]

        return round(float(score) * 100, 2)

    except Exception:

        return 0.0


# =====================================================
# RESUME ANALYSIS
# =====================================================

def analyze_resume(resume, job):

    prompt = f"""
You are an ATS resume evaluator and career advisor.

Analyze this resume against the job description.

RESUME:
{resume}

JOB DESCRIPTION:
{job}

Use these headings:

## 1. Resume Match Score
Give a realistic score out of 100 with explanation.

## 2. Matching Skills
List skills found in the resume that match the job.

## 3. Missing Skills
List important job skills not clearly present in the resume.

## 4. Resume Strengths
List the strongest points.

## 5. Areas to Improve
Explain what can be improved.

## 6. Recommended Keywords
Suggest keywords only if the candidate genuinely has those skills.

## 7. Final Recommendations
Give practical suggestions.

IMPORTANT:
Do not invent skills, qualifications or experience.
Use simple professional language.
"""

    return call_gemini(prompt)


# =====================================================
# PARSE GEMINI JSON
# =====================================================

def parse_json(response_text):

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        response_text.strip(),
        flags=re.I
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    first = text.find("{")
    last = text.rfind("}")

    if first < 0 or last < first:

        raise ValueError(
            "The AI did not return valid resume data."
        )

    return json.loads(
        text[first:last + 1]
    )


# =====================================================
# GENERATE IMPROVED RESUME
# =====================================================

def generate_resume(resume, job):

    prompt = f"""
You are a professional ATS resume writer.

Create an improved resume based ONLY on the candidate's
original resume.

ORIGINAL RESUME:
{resume}

TARGET JOB DESCRIPTION:
{job}

Return valid JSON only. No Markdown code fences.

Use exactly this structure:

{{
"name": "",
"contact": "",
"professional_title": "",
"summary": "",
"skills": [],
"experience": [
    {{
        "role": "",
        "company": "",
        "dates": "",
        "bullets": []
    }}
],
"education": [
    {{
        "degree": "",
        "institution": "",
        "dates": "",
        "details": ""
    }}
],
"projects": [
    {{
        "name": "",
        "description": "",
        "technologies": []
    }}
],
"certifications": [],
"additional_information": []
}}

IMPORTANT RULES:

1. Never invent names, contact details, dates or employers.
2. Never invent education, marks or qualifications.
3. Never invent skills or work experience.
4. Never invent achievements or percentages.
5. Preserve all factual information.
6. Improve grammar and professional wording.
7. Tailor the summary to the job where supported by facts.
8. Use empty strings or lists if information is unavailable.
9. Keep the resume suitable for the candidate's actual experience.
10. Return valid JSON only.
"""

    result = call_gemini(prompt)

    return parse_json(result)


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def txt(value):

    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return ""

    return str(value).strip()


def items(value):

    if isinstance(value, list):

        return [
            str(v).strip()
            for v in value
            if str(v).strip()
        ]

    if isinstance(value, str):

        return [
            v.strip(" •-\t")
            for v in value.splitlines()
            if v.strip(" •-\t")
        ]

    return []


# =====================================================
# WORD RESUME GENERATOR
# =====================================================

def build_word(data):

    doc = Document()

    section = doc.sections[0]

    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)

    normal = doc.styles["Normal"]

    normal.font.name = "Arial"
    normal.font.size = Pt(9.5)
    normal.font.color.rgb = RGBColor(40, 40, 40)

    normal.paragraph_format.space_after = Pt(3)

    name = txt(data.get("name"))

    if name:

        p = doc.add_paragraph()

        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        r = p.add_run(name.upper())

        r.bold = True
        r.font.size = Pt(19)

        r.font.color.rgb = RGBColor(49, 91, 58)

    for field in [
        "professional_title",
        "contact"
    ]:

        value = txt(data.get(field))

        if value:

            p = doc.add_paragraph(value)

            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def heading(label):

        p = doc.add_paragraph()

        p.paragraph_format.space_before = Pt(8)

        r = p.add_run(label.upper())

        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(49, 91, 58)

    def bullet(value):

        doc.add_paragraph(
            str(value),
            style="List Bullet"
        )

    if txt(data.get("summary")):

        heading("Professional Summary")

        doc.add_paragraph(
            txt(data["summary"])
        )

    if items(data.get("skills")):

        heading("Skills")

        doc.add_paragraph(
            " • ".join(items(data["skills"]))
        )

    for section_name, key in [
        ("Experience", "experience"),
        ("Education", "education"),
        ("Projects", "projects")
    ]:

        rows = data.get(key, [])

        usable = [
            x for x in rows
            if isinstance(x, dict)
        ] if isinstance(rows, list) else []

        if not usable:
            continue

        heading(section_name)

        for row in usable:

            if key == "experience":

                line = " | ".join(
                    filter(None, [
                        txt(row.get("role")),
                        txt(row.get("company")),
                        txt(row.get("dates"))
                    ])
                )

                if line:

                    p = doc.add_paragraph()

                    p.add_run(line).bold = True

                for b in items(row.get("bullets")):

                    bullet(b)

            elif key == "education":

                line = " | ".join(
                    filter(None, [
                        txt(row.get("degree")),
                        txt(row.get("institution")),
                        txt(row.get("dates"))
                    ])
                )

                if line:

                    p = doc.add_paragraph()

                    p.add_run(line).bold = True

                if txt(row.get("details")):

                    doc.add_paragraph(
                        txt(row["details"])
                    )

            else:

                if txt(row.get("name")):

                    p = doc.add_paragraph()

                    p.add_run(
                        txt(row["name"])
                    ).bold = True

                if txt(row.get("description")):

                    doc.add_paragraph(
                        txt(row["description"])
                    )

                if items(row.get("technologies")):

                    doc.add_paragraph(
                        "Technologies: "
                        + ", ".join(
                            items(row["technologies"])
                        )
                    )

    for label, key in [
        ("Certifications", "certifications"),
        ("Additional Information", "additional_information")
    ]:

        values = items(data.get(key))

        if values:

            heading(label)

            for value in values:

                bullet(value)

    output = io.BytesIO()

    doc.save(output)

    return output.getvalue()


# =====================================================
# PDF RESUME GENERATOR
# =====================================================

def build_pdf(data):

    output = io.BytesIO()

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=35,
        bottomMargin=35
    )

    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "ResumeName",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        alignment=1,
        textColor=colors.HexColor("#315B3A"),
        spaceAfter=3
    )

    center_style = ParagraphStyle(
        "Center",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#76543B"),
        spaceAfter=4
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        spaceAfter=3
    )

    head = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#315B3A"),
        spaceBefore=8,
        spaceAfter=3
    )

    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body,
        leftIndent=12,
        firstLineIndent=-8
    )

    story = []

    if txt(data.get("name")):

        story.append(
            Paragraph(
                escape(txt(data["name"]).upper()),
                name_style
            )
        )

    for field in [
        "professional_title",
        "contact"
    ]:

        if txt(data.get(field)):

            story.append(
                Paragraph(
                    escape(txt(data[field])),
                    center_style
                )
            )

    def heading(label):

        story.append(
            Paragraph(
                escape(label.upper()),
                head
            )
        )

        story.append(
            HRFlowable(
                width="100%",
                thickness=0.6,
                color=colors.HexColor("#A7B99A"),
                spaceAfter=4
            )
        )

    def bullet(value):

        story.append(
            Paragraph(
                "&#8226; " + escape(str(value)),
                bullet_style
            )
        )

    if txt(data.get("summary")):

        heading("Professional Summary")

        story.append(
            Paragraph(
                escape(txt(data["summary"])),
                body
            )
        )

    if items(data.get("skills")):

        heading("Skills")

        story.append(
            Paragraph(
                escape(
                    " • ".join(items(data["skills"]))
                ),
                body
            )
        )

    for section_name, key in [
        ("Experience", "experience"),
        ("Education", "education"),
        ("Projects", "projects")
    ]:

        rows = data.get(key, [])

        usable = [
            x for x in rows
            if isinstance(x, dict)
        ] if isinstance(rows, list) else []

        if not usable:
            continue

        heading(section_name)

        for row in usable:

            if key == "experience":

                line = " | ".join(
                    filter(None, [
                        txt(row.get("role")),
                        txt(row.get("company")),
                        txt(row.get("dates"))
                    ])
                )

                if line:

                    story.append(
                        Paragraph(
                            "<b>" + escape(line) + "</b>",
                            body
                        )
                    )

                for b in items(row.get("bullets")):

                    bullet(b)

            elif key == "education":

                line = " | ".join(
                    filter(None, [
                        txt(row.get("degree")),
                        txt(row.get("institution")),
                        txt(row.get("dates"))
                    ])
                )

                if line:

                    story.append(
                        Paragraph(
                            "<b>" + escape(line) + "</b>",
                            body
                        )
                    )

                if txt(row.get("details")):

                    story.append(
                        Paragraph(
                            escape(txt(row["details"])),
                            body
                        )
                    )

            else:

                if txt(row.get("name")):

                    story.append(
                        Paragraph(
                            "<b>" + escape(txt(row["name"])) + "</b>",
                            body
                        )
                    )

                if txt(row.get("description")):

                    story.append(
                        Paragraph(
                            escape(txt(row["description"])),
                            body
                        )
                    )

                if items(row.get("technologies")):

                    story.append(
                        Paragraph(
                            "Technologies: "
                            + escape(
                                ", ".join(items(row["technologies"]))
                            ),
                            body
                        )
                    )

    for label, key in [
        ("Certifications", "certifications"),
        ("Additional Information", "additional_information")
    ]:

        values = items(data.get(key))

        if values:

            heading(label)

            for value in values:

                bullet(value)

    doc.build(story)

    return output.getvalue()


# =====================================================
# MAIN INPUT SECTION
# =====================================================

st.markdown(
    '<div class="section-title">1. Upload Your Resume</div>',
    unsafe_allow_html=True
)

uploaded = st.file_uploader(
    "Upload your resume as a PDF",
    type=["pdf"]
)

st.markdown(
    '<div class="section-title">2. Add the Target Job Description</div>',
    unsafe_allow_html=True
)

job_description = st.text_area(
    "Paste the job description here",
    height=220,
    placeholder="Paste the complete job description..."
)

col1, col2 = st.columns(2)

with col1:

    analyze = st.button(
        "🔎 Analyze Resume",
        use_container_width=True
    )

with col2:

    generate = st.button(
        "🌿 Generate Improved Resume",
        use_container_width=True
    )


# =====================================================
# PROCESS RESUME
# =====================================================

if analyze or generate:

    if uploaded is None:

        st.error(
            "Please upload your resume PDF first."
        )

    elif not job_description.strip():

        st.error(
            "Please paste the target job description."
        )

    else:

        try:

            resume_text = extract_resume_text(
                uploaded
            )

            st.session_state["resume_text"] = resume_text

            if analyze:

                with st.spinner(
                    "Analyzing your resume..."
                ):

                    st.session_state["analysis_result"] = analyze_resume(
                        resume_text,
                        job_description
                    )

                    st.session_state["similarity_score"] = calculate_similarity(
                        resume_text,
                        job_description
                    )

                st.success(
                    "Resume analysis completed!"
                )

            if generate:

                with st.spinner(
                    "Generating your improved resume..."
                ):

                    st.session_state["resume_data"] = generate_resume(
                        resume_text,
                        job_description
                    )

                st.success(
                    "Your improved resume is ready!"
                )

        except Exception as e:

            st.error(str(e))


# =====================================================
# DISPLAY ANALYSIS
# =====================================================

if st.session_state.get("analysis_result"):

    st.markdown(
        '<div class="section-title">3. Resume Analysis</div>',
        unsafe_allow_html=True
    )

    st.metric(
        "TF-IDF Text Similarity",
        f'{st.session_state.get("similarity_score", 0):.2f}%'
    )

    st.caption(
        "This is a text similarity estimate, not a hiring decision."
    )

    st.markdown(
        st.session_state["analysis_result"]
    )


# =====================================================
# EDIT GENERATED RESUME
# =====================================================

if st.session_state.get("resume_data"):

    st.markdown(
        '<div class="section-title">4. Edit Your Improved Resume</div>',
        unsafe_allow_html=True
    )

    data = st.session_state["resume_data"]

    with st.form("resume_edit_form"):

        name = st.text_input(
            "Full Name",
            value=txt(data.get("name"))
        )

        contact = st.text_input(
            "Contact Details",
            value=txt(data.get("contact"))
        )

        title = st.text_input(
            "Professional Title",
            value=txt(data.get("professional_title"))
        )

        summary = st.text_area(
            "Professional Summary",
            value=txt(data.get("summary")),
            height=100
        )

        skills = st.text_area(
            "Skills (one per line)",
            value="\n".join(items(data.get("skills"))),
            height=100
        )

        experience = data.get("experience", [])

        exp_text = "\n\n".join(
            "\n".join([
                f"Role: {txt(x.get('role'))}",
                f"Company: {txt(x.get('company'))}",
                f"Dates: {txt(x.get('dates'))}",
                "Bullets:\n" + "\n".join(
                    "- " + b for b in items(x.get("bullets"))
                )
            ])
            for x in experience
            if isinstance(x, dict)
        ) if isinstance(experience, list) else ""

        experience_text = st.text_area(
            "Experience (editable text)",
            value=exp_text,
            height=160
        )

        education = data.get("education", [])

        edu_text = "\n\n".join(
            "\n".join([
                f"Degree: {txt(x.get('degree'))}",
                f"Institution: {txt(x.get('institution'))}",
                f"Dates: {txt(x.get('dates'))}",
                f"Details: {txt(x.get('details'))}"
            ])
            for x in education
            if isinstance(x, dict)
        ) if isinstance(education, list) else ""

        education_text = st.text_area(
            "Education (editable text)",
            value=edu_text,
            height=120
        )

        projects = data.get("projects", [])

        project_text = "\n\n".join(
            "\n".join([
                f"Project: {txt(x.get('name'))}",
                f"Description: {txt(x.get('description'))}",
                f"Technologies: {', '.join(items(x.get('technologies')))}"
            ])
            for x in projects
            if isinstance(x, dict)
        ) if isinstance(projects, list) else ""

        projects_text = st.text_area(
            "Projects (editable text)",
            value=project_text,
            height=130
        )

        certifications = st.text_area(
            "Certifications (one per line)",
            value="\n".join(items(data.get("certifications")))
        )

        additional = st.text_area(
            "Additional Information (one per line)",
            value="\n".join(items(data.get("additional_information")))
        )

        save = st.form_submit_button(
            "Save Resume Edits"
        )

    if save:

        data.update({

            "name": name.strip(),

            "contact": contact.strip(),

            "professional_title": title.strip(),

            "summary": summary.strip(),

            "skills": items(skills),

            "experience": [
                {
                    "role": "",
                    "company": "",
                    "dates": "",
                    "bullets": [experience_text.strip()]
                }
            ] if experience_text.strip() else [],

            "education": [
                {
                    "degree": "",
                    "institution": "",
                    "dates": "",
                    "details": education_text.strip()
                }
            ] if education_text.strip() else [],

            "projects": [
                {
                    "name": "",
                    "description": projects_text.strip(),
                    "technologies": []
                }
            ] if projects_text.strip() else [],

            "certifications": items(certifications),

            "additional_information": items(additional)

        })

        st.session_state["resume_data"] = data

        st.success(
            "Your edits have been saved."
        )

    data = st.session_state["resume_data"]

    word_file = build_word(data)

    pdf_file = build_pdf(data)

    d1, d2 = st.columns(2)

    with d1:

        st.download_button(
            "⬇️ Download Word Resume",
            word_file,
            "Fifi_Improved_Resume.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    with d2:

        st.download_button(
            "⬇️ Download PDF Resume",
            pdf_file,
            "Fifi_Improved_Resume.pdf",
            "application/pdf",
            use_container_width=True
        )

    st.caption(
        "Check every detail before applying. "
        "Never keep AI-generated information that is not true."
    )


# =====================================================
# FOOTER
# =====================================================

st.markdown(
    '<div class="footer">Made with care for your next career step 🐥</div>',
    unsafe_allow_html=True
)

# 🐥 Fifi AI Resume Analyzer

An AI-powered resume analyzer and resume generator built using Python, Streamlit, and Google Gemini API.

Fifi AI Resume Analyzer helps job seekers evaluate their resumes against job descriptions, identify missing skills, improve resume content, and generate an ATS-friendly resume.

## ✨ Features

- **PDF Resume Upload:** Upload your existing resume in PDF format.
- **AI Resume Analysis:** Analyze your resume using Google Gemini AI.
- **Resume Match Insights:** Identify matching skills and missing skills based on the target job description.
- **ATS-Oriented Feedback:** Receive suggestions to improve your resume.
- **Keyword Recommendations:** Discover relevant keywords for your target role.
- **AI Resume Generation:** Generate an improved resume based on your existing information.
- **Resume Editing:** Edit your generated resume before downloading.
- **Download Options:** Export your improved resume in Word (.docx) and PDF formats.
- **Text Similarity Score:** Calculate TF-IDF similarity between your resume and the job description.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Streamlit | User interface |
| Google Gemini API | AI-powered resume analysis and generation |
| PyPDF2 | PDF text extraction |
| Scikit-learn | TF-IDF text similarity |
| python-docx | Word resume generation |
| ReportLab | PDF resume generation |

## 📁 Project Structure

```text
Fifi-AI-Resume-Analyzer/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── .streamlit/
    └── secrets.toml
```

**Note:** The `secrets.toml` file is stored locally and should not be uploaded to GitHub.

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Shafiah-Noor/Fifi-AI-Resume-Analyzer.git
```

### 2. Navigate to the project folder

```bash
cd Fifi-AI-Resume-Analyzer
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

**Windows:**

```powershell
.venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure the Gemini API key

Create a folder named `.streamlit` and inside it create a file named `secrets.toml`.

Add your Gemini API key:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Get an API key from [Google AI Studio](https://aistudio.google.com/).

### 7. Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

## 🚀 How to Use

1. Open the Fifi AI Resume Analyzer application.
2. Upload your resume in PDF format.
3. Paste the job description for the role you are applying for.
4. Click **Analyze Resume** to receive AI-powered feedback.
5. Review matching skills, missing skills, strengths, and improvement suggestions.
6. Click **Generate Improved Resume** to create an updated resume.
7. Edit the generated resume if required.
8. Download your resume in Word or PDF format.

## 🔐 Security and Privacy

- Keep your Gemini API key private.
- Never upload `secrets.toml` or `.env` files containing API keys.
- Add sensitive configuration files to `.gitignore`.
- Resume text and job descriptions are sent to the Google Gemini API when AI features are used. Avoid uploading sensitive personal information unless you are comfortable sharing it with that service.

## 📌 Important Notes

- The application currently supports text-based PDF resumes.
- Scanned or image-only PDFs may not produce readable text.
- The TF-IDF score represents text similarity, not an official ATS score or a guarantee of selection.
- AI-generated resume content should always be reviewed for accuracy before applying.
- Gemini model availability depends on the model ID supported by your API key.

## 🔮 Future Enhancements

- Resume analysis for multiple job descriptions.
- More detailed ATS keyword comparison.
- Additional resume templates.
- Support for DOCX resume uploads.
- Enhanced resume formatting and customization.

## 👩‍💻 Author

**Shafiah Noor**

GitHub: [Shafiah-Noor](https://github.com/Shafiah-Noor)

---

*Built with Python, Streamlit, and Google Gemini AI. 🐥*
# AI-Powered Resume Analyzer & ATS Optimization System

An intelligent web application that analyzes resumes against job descriptions using **Natural Language Processing (NLP)**, **Semantic Similarity**, and **Local Large Language Models (LLMs)** to provide ATS compatibility scores, skill gap detection, improvement suggestions, and interview preparation guidance.

---

## 🚀 Project Overview

Modern recruitment heavily relies on **Applicant Tracking Systems (ATS)** to filter resumes before they reach recruiters. Many qualified candidates are rejected due to poor keyword matching, formatting issues, or lack of semantic alignment with job descriptions.

This project aims to bridge that gap by creating an **AI-driven Resume Optimization Platform** that not only evaluates resumes but also provides actionable feedback, skill transfer insights, and interview preparation tools.

---

## 🎯 Objectives

* Parse and analyze resumes using NLP
* Match resumes against Job Descriptions (JD)
* Generate ATS compatibility scores
* Detect skill gaps and missing sections
* Provide AI-generated improvement suggestions
* Generate interview questions
* Identify transferable skills across domains
* Deliver real-time feedback through a simple UI

---

## 🧠 Core Concepts Used

* **Natural Language Processing (spaCy, NLTK)**
* **Semantic Similarity (Sentence-BERT)**
* **Vector Embeddings & Cosine Similarity**
* **Rule-Based Heuristics**
* **Local LLM Integration (Ollama – Mistral / Llama / Phi)**
* **Streamlit UI Framework**
* **Modular Python Service Architecture**

---

## 🏗 System Architecture

```
User Input (Resume + JD)
        ↓
PDF/Text Extraction
        ↓
NLP Preprocessing
        ↓
Embedding Generation
        ↓
Scoring Engine
        ↓
Gap & Improvement Analysis
        ↓
LLM Enhancement Layer
        ↓
UI Output
```

---

## 📦 Features Implemented

### 1. Resume Parsing

* PDF text extraction using `pdfplumber`
* Multi-page support
* Clean text normalization

### 2. NLP Preprocessing

* Lowercasing
* Lemmatization
* Stopword removal
* Token filtering

### 3. Semantic Similarity

* Sentence-BERT embeddings
* Cosine similarity scoring
* Context-aware matching

### 4. ATS Compatibility Score

Weighted formula:

```
Final Score = 70% Semantic Similarity + 30% Keyword Match
```

### 5. Skill Gap Detection

* Keyword intersection analysis
* Domain filtering
* Stop-skill removal
* Categorized display

### 6. Resume Quality Checks

* Resume length
* Measurable achievements
* Section detection
* Structural feedback

### 7. AI Suggestions (LLM Layer)

Powered by **Ollama (Local LLM)**

Generates:

* Bullet rewrites
* Resume improvements
* Skill explanations
* Structural advice

### 8. Interview Preparation

* Technical questions
* Behavioral questions
* Weak-area questions
* Key revision topics

### 9. Transferable Skill Detection

* Embedding-based skill similarity
* Domain mapping
* Career pivot suggestions

---

## 🛠 Technology Stack

| Layer       | Tools                                    |
| ----------- | ---------------------------------------- |
| Frontend    | Streamlit                                |
| Backend     | Python                                   |
| NLP         | spaCy, NLTK                              |
| Embeddings  | Sentence-Transformers (all-MiniLM-L6-v2) |
| LLM         | Ollama (Mistral / Llama / Phi)           |
| Similarity  | Scikit-Learn                             |
| PDF Parsing | pdfplumber                               |
| Storage     | Local / Optional DB                      |

---

## 📂 Project Structure

```
resume_ats/
│
├── app.py
│
├── services/
│   ├── pdf_service.py
│   ├── nlp_service.py
│   ├── embedding_service.py
│   ├── scoring_service.py
│   ├── improvement_service.py
│   ├── llm_service.py
│   ├── interview_service.py
│   └── skill_transfer_service.py
│
├── data/
│   ├── tech_skills.txt
│   ├── skill_stopwords.txt
│   └── skill_domains.json
│
└── requirements.txt
```

---

## ⚙ Installation

### 1. Clone Repository

```bash
git clone <repo_url>
cd resume_ats
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 5. Install Ollama & Pull Model

```bash
ollama pull mistral
```

### 6. Run Application

```bash
streamlit run app.py
```

---

## 🧪 Example Use Case

1. Upload Resume PDF
2. Paste Job Description
3. Click **Analyze Resume**
4. View:

   * ATS Score
   * Skill Gaps
   * Missing Sections
   * Improvement Suggestions
5. Generate:

   * AI Feedback
   * Interview Questions

---

## 📊 Scoring Logic

### Semantic Similarity

Measures contextual meaning using embeddings.

### Keyword Match

Measures direct skill overlap.

### Guardrails

* Minimum JD length
* Stop-skill filtering
* Template detection
* Spam detection

---

## 🔒 Design Principles

* Deterministic scoring core
* Explainable AI
* Modular architecture
* Offline LLM capability
* Scalable service design
* No API dependency
* Reproducible results

---

## 🚧 Current Limitations

* Exact skill synonym mapping limited
* No multi-language support
* No recruiter analytics
* No cloud database
* No user authentication (yet)

---

## 🔮 Future Enhancements

* Resume version tracking
* Skill progression roadmap
* Recruiter simulation modes
* Job trend analysis
* Multi-resume benchmarking
* Cover letter generation
* Market demand heatmaps
* Soft-skill sentiment analysis
* SaaS deployment

---

## 📸 Screenshots (Add Later)

* Resume Upload UI
* ATS Score Display
* Skill Gap Analysis
* AI Suggestions Output
* Interview Preparation Output

---

## 🧩 Why This Project Is Unique

* Combines **Deterministic NLP + Generative AI**
* Uses **Local LLM (No API Costs)**
* Hybrid scoring system
* Career intelligence features
* Production-ready modular design
* Explainable decision pipeline

---

## 🤝 Contribution

Open for improvements:

* Skill datasets
* UI enhancements
* Model experimentation
* Deployment pipelines

---

## 📜 License

MIT License

---

## 👨‍💻 Author

**Arnav Trivedi**
AI-Powered Resume Analyzer & ATS Optimization System

---

## ⭐ Final Note

This project evolves the idea of a resume checker into a **Career Intelligence Platform**, combining semantic AI, rule-based logic, and local LLM capabilities to provide real, actionable career guidance rather than just numerical scoring.

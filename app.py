import streamlit as st

# ---------- SERVICES ----------
from services.pdf_service import extract_text
from services.nlp_service import preprocess, extract_keywords
from services.embedding_service import embed
from services.scoring_service import semantic_score, keyword_score, final_score
from services.improvement_service import (
    detect_missing_sections,
    detect_quality_issues,
    jd_alignment_issue,
    skill_gap_analysis,
)
from services.llm_service import ask_llm
from services.prompt_builder import improvement_prompt
from services.interview_service import generate_interview_questions

# ---------- PAGE ----------
st.set_page_config(page_title="AI Resume ATS Analyzer", layout="wide")
st.title("AI Resume ATS Analyzer")

# ---------- SESSION INIT ----------
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

# ---------- INPUTS ----------
resume_pdf = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
jd_text = st.text_area("Paste Job Description")

analyze_clicked = st.button("Analyze Resume")

# ---------- ANALYSIS ----------
if analyze_clicked:

    # Validate inputs
    if not resume_pdf or not jd_text:
        st.warning("Provide both Resume and Job Description.")
        st.stop()

    if len(jd_text.split()) < 20:
        st.warning("Job Description too short.")
        st.stop()

    with st.spinner("Analyzing..."):

        # Extract resume text
        resume_text = extract_text(resume_pdf)

        # NLP preprocessing
        clean_resume = preprocess(resume_text)
        clean_jd = preprocess(jd_text)

        # Embeddings
        resume_emb = embed(clean_resume)
        jd_emb = embed(clean_jd)

        # Scoring
        semantic = semantic_score(resume_emb, jd_emb)
        resume_keys = extract_keywords(resume_text)
        jd_keys = extract_keywords(jd_text)
        keyword = keyword_score(resume_keys, jd_keys)
        score = final_score(semantic, keyword)

        # Save everything to session
        st.session_state.resume_text = resume_text
        st.session_state.jd_text = jd_text
        st.session_state.resume_keys = resume_keys
        st.session_state.jd_keys = jd_keys
        st.session_state.skill_gaps = list(jd_keys - resume_keys)
        st.session_state.semantic = semantic
        st.session_state.keyword = keyword
        st.session_state.score = score
        st.session_state.analysis_done = True

# ---------- RESULTS ----------
if st.session_state.analysis_done:

    # Load session data
    resume_text = st.session_state.resume_text
    jd_text = st.session_state.jd_text
    skill_gaps = st.session_state.skill_gaps
    score = st.session_state.score

    # Debug raw scores
    st.write("Semantic Raw:", st.session_state.semantic)
    st.write("Keyword Raw:", st.session_state.keyword)

    # ATS Score
    st.subheader("ATS Compatibility Score")
    st.metric("Score", f"{round(score,2)}%")
    st.divider()

    # Improvements
    missing_sections = detect_missing_sections(resume_text)
    quality_issues = detect_quality_issues(resume_text)
    alignment_issue = jd_alignment_issue(score)

    col1, col2 = st.columns(2)

    # Missing sections
    with col1:
        st.subheader("Missing Resume Sections")
        if missing_sections:
            for sec in missing_sections:
                st.write(f"• {sec}")
        else:
            st.write("All major sections present.")

    # Skill gaps
    with col2:
        st.subheader("Skill Gaps")
        if skill_gaps:
            st.write(", ".join(skill_gaps[:15]))
        else:
            st.write("No major skill gaps.")

    # Suggestions
    st.subheader("Improvement Suggestions")
    if quality_issues:
        for issue in quality_issues:
            st.write(f"• {issue}")
    else:
        st.write("Resume looks strong.")

    if alignment_issue:
        st.write(f"• {alignment_issue}")

    st.divider()

    # ---------- AI FEEDBACK ----------
    st.subheader("AI Resume Assistant")
    if st.button("Generate AI Feedback"):
        with st.spinner("Generating..."):
            prompt = improvement_prompt(
                resume_text=resume_text[:2000],
                skill_gaps=skill_gaps,
                score=score,
            )
            ai_response = ask_llm(prompt)
        st.write(ai_response)

    st.divider()

    # ---------- INTERVIEW PREP ----------
    st.subheader("Interview Preparation")
    if st.button("Generate Interview Questions"):
        with st.spinner("Preparing..."):
            questions = generate_interview_questions(
                resume_text,
                jd_text,
                skill_gaps,
            )
        st.write(questions)

else:
    st.info("Upload resume and job description, then click Analyze.")

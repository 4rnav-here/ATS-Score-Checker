from app.services.llm_service import ask_llm


def generate_interview_questions(
    resume_text: str,
    jd_text: str,
    skill_gaps: list[str],
) -> str:
    """
    Generate a structured set of interview questions using the local LLM.

    Phase 1 placeholder — exposed via /api/interview in a later phase.
    """
    prompt = f"""You are a technical interviewer.

Resume:
{resume_text[:1500]}

Job Description:
{jd_text[:1500]}

Missing Skills:
{', '.join(skill_gaps)}

Generate:
1. 5 Technical Questions
2. 3 Behavioral Questions
3. 3 Weak Area Questions (based on skill gaps)
4. 5 Key Topics to Revise

Keep responses concise."""

    return ask_llm(prompt)

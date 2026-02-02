from services.llm_service import ask_llm

def generate_interview_questions(resume_text, jd_text, skill_gaps):
    prompt = f"""
You are a technical interviewer.

Resume:
{resume_text[:1500]}

Job Description:
{jd_text[:1500]}

Missing Skills:
{', '.join(skill_gaps)}

Generate:
1. 5 Technical Questions
2. 3 Behavioral Questions
3. 3 Weak Area Questions
4. 5 Key Topics to Revise

Keep concise.
"""

    return ask_llm(prompt)

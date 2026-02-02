def improvement_prompt(resume_text, skill_gaps, score):
    return f"""
You are an ATS resume expert.

Resume Score: {score}%

Missing Skills: {', '.join(skill_gaps)}

Resume Text:
{resume_text}

Provide:
1. Top 3 improvements
2. Rewrite one bullet point
3. Structural suggestion
"""

import re

SECTION_KEYWORDS = {
    "skills": ["skill", "technology", "tools"],
    "projects": ["project"],
    "experience": ["experience", "work history"],
    "education": ["education", "degree", "university"],
}

def detect_missing_sections(resume_text):
    text = resume_text.lower()
    missing = []

    for section, keywords in SECTION_KEYWORDS.items():
        if not any(k in text for k in keywords):
            missing.append(section.capitalize())

    return missing


def detect_quality_issues(resume_text):
    issues = []
    words = resume_text.split()

    if len(words) < 150:
        issues.append("Resume length is short. Add more details.")

    if not re.search(r"\d+%", resume_text):
        issues.append("Add measurable achievements (%, numbers, metrics).")

    if "project" not in resume_text.lower():
        issues.append("Include at least one project section.")

    return issues


def skill_gap_analysis(resume_keys, jd_keys):
    return list(jd_keys - resume_keys)


def jd_alignment_issue(score):
    if score < 40:
        return "Resume is poorly aligned with the job description."
    return None

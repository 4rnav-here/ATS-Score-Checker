"""
Recommendation Service — generates prioritized, actionable improvement
recommendations by analyzing the full output of the scoring pipeline.

Consumes:
    - ScoreBreakdown (semantic, keyword, format_penalty, final)
    - Section scores (per-section cosine similarity)
    - Skill gaps (set difference between JD and resume keywords)
    - Format issues (layout problems detected by pdf_service)
    - Quality issues (heuristic checks from improvement_service)
    - Sections found / missing

Produces:
    - List[Recommendation] sorted by priority (critical → low)
    - Each recommendation has: priority, category, title, description, impact
"""

from app.core.config import SECTION_WEIGHTS


# ── Priority levels ───────────────────────────────────────────────────────────
PRIORITY_CRITICAL = "critical"
PRIORITY_HIGH = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_LOW = "low"

# ── Categories ────────────────────────────────────────────────────────────────
CAT_KEYWORD = "keyword_alignment"
CAT_SEMANTIC = "semantic_alignment"
CAT_SECTION = "missing_section"
CAT_FORMAT = "formatting"
CAT_QUALITY = "content_quality"
CAT_SKILL = "skill_gap"

# ── Thresholds ────────────────────────────────────────────────────────────────
FINAL_CRITICAL_THRESHOLD = 40.0
FINAL_LOW_THRESHOLD = 60.0
SEMANTIC_WEAK_THRESHOLD = 50.0
KEYWORD_WEAK_THRESHOLD = 35.0
SECTION_WEAK_THRESHOLD = 45.0

# ── Priority ordering for sorting ─────────────────────────────────────────────
PRIORITY_ORDER = {
    PRIORITY_CRITICAL: 0,
    PRIORITY_HIGH: 1,
    PRIORITY_MEDIUM: 2,
    PRIORITY_LOW: 3,
}


def generate_recommendations(
    scores: dict,
    section_scores: dict,
    skill_gaps: list[str],
    format_issues: list[str],
    quality_issues: list[str],
    sections_found: list[str],
    sections_missing: list[str],
) -> list[dict]:
    """
    Generate a prioritized list of recommendations from the full analysis output.

    Each recommendation is a dict with keys:
        priority    — "critical" | "high" | "medium" | "low"
        category    — classification tag for UI grouping
        title       — short headline (e.g., "Add Missing Skills Section")
        description — actionable detail explaining what to do and why
        impact      — estimated score improvement description

    Returns:
        Sorted list of recommendation dicts (critical first).
    """
    recs: list[dict] = []

    semantic = scores.get("semantic", 0.0)
    keyword = scores.get("keyword", 0.0)
    format_penalty = scores.get("format_penalty", 0.0)
    final = scores.get("final", 0.0)

    # ── 1. Overall alignment warning ──────────────────────────────────────────
    if final < FINAL_CRITICAL_THRESHOLD:
        recs.append({
            "priority": PRIORITY_CRITICAL,
            "category": CAT_SEMANTIC,
            "title": "Resume is critically misaligned with this job description",
            "description": (
                f"Your overall ATS score is {final:.1f}/100, well below the "
                f"minimum threshold of {FINAL_CRITICAL_THRESHOLD}. This resume would likely be "
                "auto-rejected by most ATS systems. Consider a major rewrite "
                "targeting the specific role requirements."
            ),
            "impact": "Could improve final score by 20–40 points",
        })
    elif final < FINAL_LOW_THRESHOLD:
        recs.append({
            "priority": PRIORITY_HIGH,
            "category": CAT_SEMANTIC,
            "title": "Resume alignment needs significant improvement",
            "description": (
                f"Your overall ATS score is {final:.1f}/100. Most competitive "
                "roles require scores above 60. Focus on keyword integration "
                "and tailoring your experience bullets to mirror JD language."
            ),
            "impact": "Could improve final score by 10–25 points",
        })

    # ── 2. Semantic score recommendations ─────────────────────────────────────
    if semantic < SEMANTIC_WEAK_THRESHOLD:
        recs.append({
            "priority": PRIORITY_HIGH,
            "category": CAT_SEMANTIC,
            "title": "Strengthen semantic alignment with the job description",
            "description": (
                f"Semantic similarity score is {semantic:.1f}/100 (weight: 70% of final). "
                "Your resume content doesn't closely match the meaning of the JD. "
                "Rewrite your experience bullets and project descriptions using "
                "language, context, and domain terms from the job posting — not "
                "just the exact keywords, but the same concepts and phrasing."
            ),
            "impact": "Directly affects 70% of your final score",
        })

    # ── 3. Per-section weakness detection ─────────────────────────────────────
    for section_name, weight in sorted(
        SECTION_WEIGHTS.items(), key=lambda x: x[1], reverse=True
    ):
        score = section_scores.get(section_name)
        if score is None:
            continue
        if score < SECTION_WEAK_THRESHOLD:
            weight_pct = int(weight * 100)
            priority = PRIORITY_HIGH if weight >= 0.25 else PRIORITY_MEDIUM
            recs.append({
                "priority": priority,
                "category": CAT_SEMANTIC,
                "title": f"Improve your {section_name.capitalize()} section",
                "description": (
                    f"Your {section_name} section scored {score:.1f}/100 against the JD "
                    f"(this section carries {weight_pct}% of the semantic score). "
                    f"Review the job description and align your {section_name} content "
                    "more closely with the required qualifications, tools, and "
                    "responsibilities mentioned."
                ),
                "impact": f"Affects {weight_pct}% of the semantic component",
            })

    # ── 4. Keyword score recommendations ──────────────────────────────────────
    if keyword < KEYWORD_WEAK_THRESHOLD:
        recs.append({
            "priority": PRIORITY_HIGH,
            "category": CAT_KEYWORD,
            "title": "Increase keyword density from the job description",
            "description": (
                f"TF-IDF keyword score is {keyword:.1f}/100 (weight: 30% of final). "
                "Your resume is missing many important terms from the JD. "
                "Integrate specific technologies, methodologies, and role-specific "
                "terminology directly into your bullet points. Use the exact "
                "phrasing from the job posting where natural."
            ),
            "impact": "Directly affects 30% of your final score",
        })
    elif keyword < SEMANTIC_WEAK_THRESHOLD:
        recs.append({
            "priority": PRIORITY_MEDIUM,
            "category": CAT_KEYWORD,
            "title": "Add more JD-specific terminology to your resume",
            "description": (
                f"TF-IDF keyword score is {keyword:.1f}/100. There is moderate overlap "
                "but room for improvement. Scan the JD for specific tools, frameworks, "
                "and qualifications mentioned, and work them naturally into your "
                "experience and skills sections."
            ),
            "impact": "Could improve keyword component by 10–20 points",
        })

    # ── 5. Skill gap recommendations ──────────────────────────────────────────
    if len(skill_gaps) > 5:
        top_skills = ", ".join(skill_gaps[:8])
        recs.append({
            "priority": PRIORITY_HIGH,
            "category": CAT_SKILL,
            "title": f"{len(skill_gaps)} skill gaps detected",
            "description": (
                f"The JD requires skills not found in your resume: {top_skills}. "
                "Add these to your Skills section if you have experience with them. "
                "For skills you're learning, mention them in project descriptions "
                "or a 'Currently Learning' subsection."
            ),
            "impact": "Improves both keyword and semantic scores",
        })
    elif len(skill_gaps) > 0:
        skills_str = ", ".join(skill_gaps)
        recs.append({
            "priority": PRIORITY_MEDIUM,
            "category": CAT_SKILL,
            "title": f"{len(skill_gaps)} minor skill gap(s) detected",
            "description": (
                f"Missing skills: {skills_str}. If you have experience with "
                "these, make sure they are explicitly mentioned in your resume."
            ),
            "impact": "Moderate improvement to keyword matching",
        })

    # ── 6. Missing section recommendations ────────────────────────────────────
    for section in sections_missing:
        section_lower = section.lower()
        weight = SECTION_WEIGHTS.get(section_lower, 0.0)

        if section_lower in ("skills", "experience"):
            priority = PRIORITY_CRITICAL
        elif section_lower in ("projects", "education"):
            priority = PRIORITY_HIGH
        else:
            priority = PRIORITY_MEDIUM

        recs.append({
            "priority": priority,
            "category": CAT_SECTION,
            "title": f"Add a {section} section to your resume",
            "description": (
                f"Your resume is missing a '{section}' section. ATS systems "
                "specifically scan for standard sections. Adding this section "
                "will improve both your semantic alignment and structural "
                f"completeness. This section carries {int(weight * 100)}% of "
                "the semantic score weight."
            ),
            "impact": f"Enables {int(weight * 100)}% of semantic scoring",
        })

    # ── 7. Format issue recommendations ───────────────────────────────────────
    for issue in format_issues:
        recs.append({
            "priority": PRIORITY_MEDIUM,
            "category": CAT_FORMAT,
            "title": "Fix ATS-unfriendly formatting",
            "description": (
                f"{issue} Convert to a single-column, text-based layout without "
                "tables or complex formatting. Use standard section headers and "
                "simple bullet points."
            ),
            "impact": f"Removes up to {format_penalty:.0f} points of penalty",
        })

    # ── 8. Quality issue recommendations ──────────────────────────────────────
    for issue in quality_issues:
        recs.append({
            "priority": PRIORITY_LOW,
            "category": CAT_QUALITY,
            "title": "Improve content quality",
            "description": issue,
            "impact": "Improves ATS readability and recruiter impression",
        })

    # ── Sort by priority ──────────────────────────────────────────────────────
    recs.sort(key=lambda r: PRIORITY_ORDER.get(r["priority"], 99))

    return recs


def summarize_recommendations(recommendations: list[dict]) -> dict:
    """
    Generate a summary of recommendation counts by priority level.

    Returns:
        {"critical": int, "high": int, "medium": int, "low": int, "total": int}
    """
    summary = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "total": len(recommendations),
    }
    for rec in recommendations:
        priority = rec.get("priority", "low")
        if priority in summary:
            summary[priority] += 1
    return summary

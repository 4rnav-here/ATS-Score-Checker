import re

from app.core.config import FORMAT_PENALTY_MAX
from app.core.logger import logger

# ── Section detection ─────────────────────────────────────────────────────────
SECTION_KEYWORDS: dict[str, list[str]] = {
    "skills": ["skill", "technology", "tools", "competencies"],
    "projects": ["project"],
    "experience": ["experience", "work history", "employment"],
    "education": ["education", "degree", "university", "college"],
    "summary": ["summary", "objective", "profile"],
}

# ── Format penalty weights ────────────────────────────────────────────────────
FORMAT_PENALTY_WEIGHTS: dict[str, float] = {
    "multi_column": 8.0,
    "has_tables": 4.0,
    "low_text_density": 3.0,
}

# ── Quality issue checks ──────────────────────────────────────────────────────
QUALITY_CHECKS: list[tuple] = [
    (
        lambda text, words: len(words) < 150,
        "Resume is too short — add more detail (aim for 400+ words).",
    ),
    (
        lambda text, words: not re.search(r"\d+\s*%", text),
        "Add measurable achievements (e.g., 'improved performance by 30%').",
    ),
    (
        lambda text, words: not re.search(r"\b(19|20)\d{2}\b", text),
        "Include specific years for positions and education.",
    ),
    (
        lambda text, words: "project" not in text.lower(),
        "Include at least one projects section.",
    ),
]


def detect_missing_sections(resume_text: str) -> tuple[list[str], list[str]]:
    """
    Scan the resume for expected sections.

    Returns:
        (sections_found, sections_missing)
    """
    text_lower = resume_text.lower()
    found: list[str] = []
    missing: list[str] = []

    for section, keywords in SECTION_KEYWORDS.items():
        if any(k in text_lower for k in keywords):
            found.append(section.capitalize())
        else:
            missing.append(section.capitalize())

    return found, missing


def detect_quality_issues(resume_text: str) -> list[str]:
    """Run all quality heuristics and return a list of issue strings."""
    issues: list[str] = []
    words = resume_text.split()

    for check_fn, message in QUALITY_CHECKS:
        try:
            if check_fn(resume_text, words):
                issues.append(message)
        except Exception as exc:
            logger.warning(f"Quality check skipped: {exc}")

    return issues


def compute_format_penalty(layout_metadata: dict) -> tuple[float, list[str]]:
    """
    Calculate ATS format penalty from PDF layout metadata.

    Args:
        layout_metadata: Output of pdf_service.extract_layout_metadata()

    Returns:
        (penalty: float, issues: list[str])   — penalty is capped at FORMAT_PENALTY_MAX (15)
    """
    penalty = 0.0
    issues: list[str] = []

    if layout_metadata.get("is_multi_column"):
        penalty += FORMAT_PENALTY_WEIGHTS["multi_column"]
        issues.append(
            "Multi-column layout detected — ATS parsers often misread columns. Convert to single-column."
        )

    if layout_metadata.get("has_tables"):
        penalty += FORMAT_PENALTY_WEIGHTS["has_tables"]
        issues.append(
            "Tables detected — ATS systems may fail to parse table content. Replace with plain text bullet points."
        )

    if layout_metadata.get("low_text_density"):
        penalty += FORMAT_PENALTY_WEIGHTS["low_text_density"]
        issues.append(
            "Low text density — possible heavy use of images or whitespace. Add more text content."
        )

    penalty = min(penalty, FORMAT_PENALTY_MAX)
    return round(penalty, 2), issues


def jd_alignment_warning(score: float) -> str | None:
    """Return a warning string if overall score is critically low (< 40)."""
    if score < 40:
        return (
            "Resume is poorly aligned with this job description. "
            "Major revision recommended."
        )
    return None

# ── Fix 8: Skill gap cleanup ───────────────────────────────────────────────
def compute_skill_gaps(
    resume_keywords: set[str],
    jd_keywords: set[str],
    resume_raw_text: str,
    top_n: int = 15,
) -> list[str]:
    """
    Compute the list of skills present in the JD but missing from the resume.

    Three-stage filtering:
    1. Set difference: jd_keywords - resume_keywords (NLP-based)
    2. Length filter: gaps must be >= 3 characters
    3. False-positive removal: if the gap word appears verbatim in the raw
       resume text (case-insensitive), it is not a real gap — the NLP pipeline
       missed it due to normalisation. Remove it.

    Returns the top_n gaps sorted by length (longer = more specific = more
    meaningful to the user), truncated to top_n.
    """
    raw_gaps = jd_keywords - resume_keywords

    # Remove single/double character tokens
    gaps = {g for g in raw_gaps if len(g) >= 3}

    # Remove false positives: skill appears in raw resume text
    resume_lower = resume_raw_text.lower()
    real_gaps = {
        gap for gap in gaps
        if gap.lower() not in resume_lower
    }

    # Sort: longer skills first (more specific), then alphabetically
    sorted_gaps = sorted(real_gaps, key=lambda g: (-len(g), g))

    return sorted_gaps[:top_n]

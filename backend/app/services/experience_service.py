"""
Experience Extractor Service — detects candidate experience level from resume text.

Uses a combination of:
    1. Year range extraction (strongest signal)
    2. Job title keyword matching
    3. spaCy NER for title detection

Returns:
    {total_years, level, titles, level_confidence}
"""

import re
from datetime import date

import spacy

from app.core.logger import logger

nlp = spacy.load("en_core_web_sm")

# ── Level keyword patterns ────────────────────────────────────────────────────
LEVEL_KEYWORDS: dict[str, list[str]] = {
    "intern": ["intern", "trainee", "student worker", "co-op"],
    "junior": ["junior", "jr.", "entry level", "entry-level", "associate", "graduate"],
    "senior": ["senior", "sr.", "lead", "principal", "staff"],
    "staff": ["staff engineer", "principal engineer", "architect", "director"],
}

# ── Date patterns for year extraction ─────────────────────────────────────────
YEAR_PATTERN = re.compile(r"\b(19[89]\d|20[0-3]\d)\b")


def extract_experience(resume_text: str) -> dict:
    """
    Extract experience level and total years from resume text.

    Returns:
        {
            "total_years": float,
            "level": str,       # "intern"|"junior"|"mid"|"senior"|"staff"
            "titles": list[str],
            "level_confidence": float,  # 0.0 - 1.0
        }
    """
    text_lower = resume_text.lower()

    # ── Step 1: Find all year mentions ────────────────────────────────────────
    years_found = YEAR_PATTERN.findall(resume_text)
    years_int = sorted(set(int(y) for y in years_found))

    total_years = 0.0
    if len(years_int) >= 2:
        current_year = date.today().year
        # Earliest professional year to now, capped at 40 years
        total_years = min(current_year - years_int[0], 40)

    # ── Step 2: Extract job titles via spaCy NER ──────────────────────────────
    doc = nlp(resume_text[:3000])  # Limit to first 3000 chars for speed
    titles = []
    for ent in doc.ents:
        if ent.label_ in ("ORG", "WORK_OF_ART") and len(ent.text.split()) <= 5:
            titles.append(ent.text)

    # ── Step 3: Rule-based level detection ────────────────────────────────────
    level = "mid"  # Default
    confidence = 0.5

    # Check for keyword-based level hints
    for lvl, keywords in LEVEL_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                level = lvl
                confidence = 0.85
                break

    # Year-count override (stronger signal than keywords)
    if total_years < 1:
        level = "intern"
        confidence = 0.9
    elif total_years < 3:
        level = "junior"
        confidence = 0.8
    elif total_years < 6:
        level = "mid"
        confidence = 0.75
    elif total_years < 11:
        level = "senior"
        confidence = 0.8
    else:
        level = "staff"
        confidence = 0.85

    result = {
        "total_years": round(total_years, 1),
        "level": level,
        "titles": titles[:10],
        "level_confidence": confidence,
    }

    logger.info(f"Experience extracted: level={level}, years={total_years:.1f}")
    return result

"""
Scoring Service — semantic section scoring, TF-IDF, and final aggregation.

Fixes from atsfix.md:
    Fix 4: normalize_text_for_tfidf() + bigrams (1,2) + sublinear_tf
            ensures React.js/ReactJS/React all match, two-word phrases captured.
    Fix 6: direct_skill_match_bonus() acts as score floor, preventing near-zero
            scores when the NLP pipeline partially fails.
"""

import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import KEYWORD_WEIGHT, SECTION_WEIGHTS, SEMANTIC_WEIGHT
from app.core.logger import logger


# ── Fix 4: Taxonomy-normalised TF-IDF ────────────────────────────────────────

def normalize_text_for_tfidf(text: str) -> str:
    """
    Prepare text for TF-IDF vectorization by normalising skill name variants.

    Ensures "React.js", "ReactJS", and "react" all become the same token
    before the vectorizer sees them, preventing false mismatches.

    Also:
    - Lowercases everything
    - Applies SKILL_ALIASES substitution
    - Removes intra-word dots ("React.js" → "reactjs")
    - Removes intra-word hyphens ("full-stack" → "fullstack")
    - Collapses remaining punctuation to spaces
    """
    from app.services.skills_taxonomy import SKILL_ALIASES

    normalised = text.lower()

    # Apply taxonomy: replace variants with canonical lowercase form.
    # Sort by length descending to ensure "react.js" matches before "react".
    aliases = sorted(SKILL_ALIASES.items(), key=lambda x: len(x[0]), reverse=True)
    
    for variant, canonical in aliases:
        pattern = r'\b' + re.escape(variant.lower()) + r'\b'
        replacement = canonical.lower().replace(".", "").replace("-", "").replace(" ", "")
        normalised = re.sub(pattern, replacement, normalised)

    # Remove dots between word characters: "react.js" → "reactjs"
    normalised = re.sub(r'(?<=\w)\.(?=\w)', '', normalised)
    # Remove hyphens between word characters: "full-stack" → "fullstack"
    normalised = re.sub(r'(?<=\w)-(?=\w)', '', normalised)
    # Replace remaining punctuation with space
    normalised = re.sub(r'[^\w\s]', ' ', normalised)
    normalised = re.sub(r'\s+', ' ', normalised).strip()

    return normalised


def tfidf_keyword_score(resume_text: str, jd_text: str) -> float:
    """
    TF-IDF cosine similarity between resume and JD.

    Fix 4 improvements over v1:
    - Both texts run through normalize_text_for_tfidf() first
    - ngram_range=(1, 2) captures two-word phrases ("server side", "unit testing")
    - sublinear_tf=True prevents a single high-frequency term from dominating

    Returns a float 0.0–100.0.
    """
    resume_norm = normalize_text_for_tfidf(resume_text)
    jd_norm     = normalize_text_for_tfidf(jd_text)

    try:
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform([resume_norm, jd_norm])
        raw = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        # Scale up TF-IDF cosine similarity as it's typically very low for doc-vs-JD
        score = min(1.0, raw * 5.0)
        return round(score * 100, 2)
    except ValueError:
        # Raised when input is empty or all stop words
        logger.warning("TF-IDF vectorization failed — empty or all-stopword input")
        return 0.0
    except Exception as e:
        logger.error(f"TF-IDF scoring failed: {e}")
        return 0.0


# ── Semantic section scoring (unchanged logic, kept for reference) ────────────

def semantic_score_sections(
    section_embeddings: dict,
    jd_embedding: np.ndarray,
) -> tuple[float, dict]:
    """
    Compute a section-weighted semantic ATS score.

    Each detected resume section is scored against the full JD embedding,
    then combined via SECTION_WEIGHTS from config.

    Returns:
        (final_semantic_score: float 0-100, per_section_scores: dict)
    """
    section_scores: dict[str, float] = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for section_name, embedding in section_embeddings.items():
        weight = SECTION_WEIGHTS.get(section_name, 0.0)
        if weight == 0.0:
            continue

        raw = float(cosine_similarity([embedding], [jd_embedding])[0][0])
        # Scale semantic cosine similarity slightly for 0-100 presentation
        raw = max(0.0, min(1.0, raw * 1.5))
        section_scores[section_name] = round(raw * 100, 2)
        weighted_sum += raw * weight
        total_weight += weight

    if total_weight > 0:
        final_semantic = (weighted_sum / total_weight) * 100
    elif section_scores:
        final_semantic = sum(section_scores.values()) / len(section_scores)
    else:
        final_semantic = 0.0

    return round(final_semantic, 2), section_scores


def keyword_overlap_score(resume_keys: set, jd_keys: set) -> float:
    """Simple keyword intersection ratio (for debugging/display only)."""
    if not jd_keys:
        return 0.0
    return round((len(resume_keys & jd_keys) / len(jd_keys)) * 100, 2)


# ── Fix 6: Direct skill match bonus (score floor) ────────────────────────────

def direct_skill_match_bonus(resume_raw: str, jd_raw: str) -> float:
    """
    Compute a score bonus based on direct string matching of canonical skill names.

    Bypasses the NLP pipeline entirely. Acts as a floor — if 50% of the JD's
    technical skills appear literally in the resume, the score should not be
    near zero regardless of what went wrong upstream.

    Returns a bonus float in range 0.0–20.0.
    """
    from app.services.skills_taxonomy import SKILL_ALIASES

    resume_lower = resume_raw.lower()
    jd_lower     = jd_raw.lower()

    canonical_skills = set(SKILL_ALIASES.values())
    jd_skills_present:     set[str] = set()
    resume_skills_matched: set[str] = set()

    for skill in canonical_skills:
        skill_lower = skill.lower()
        if skill_lower in jd_lower:
            jd_skills_present.add(skill)
            if skill_lower in resume_lower:
                resume_skills_matched.add(skill)

    if not jd_skills_present:
        return 0.0

    match_ratio = len(resume_skills_matched) / len(jd_skills_present)
    bonus = round(min(20.0, match_ratio * 25.0), 2)

    logger.info(
        f"Skill bonus: {len(resume_skills_matched)}/{len(jd_skills_present)} "
        f"skills matched -> +{bonus}"
    )
    return bonus


# ── Final score aggregation ───────────────────────────────────────────────────

def final_score(
    semantic: float,
    keyword: float,
    format_penalty: float,
    resume_raw: str = "",
    jd_raw: str = "",
) -> float:
    """
    Compute the final ATS score using config-driven weights.

    Formula:
        content  = (semantic * SEMANTIC_WEIGHT) + (keyword * KEYWORD_WEIGHT)
        bonus    = direct_skill_match_bonus(resume_raw, jd_raw)
        raw      = content + bonus - format_penalty
        final    = clamp(raw, 0, 100)
    """
    content = (semantic * SEMANTIC_WEIGHT) + (keyword * KEYWORD_WEIGHT)
    bonus   = direct_skill_match_bonus(resume_raw, jd_raw) if resume_raw else 0.0
    raw     = content + bonus - format_penalty
    return round(max(0.0, min(100.0, raw)), 2)


def final_score_breakdown(
    semantic: float,
    keyword: float,
    format_penalty: float,
    resume_raw: str = "",
    jd_raw: str = "",
) -> dict:
    """
    Return all sub-scores as a dict for detailed display in the API response.

    Fix 7: exposes content_score and skill_bonus separately so the UI can
    show users what the penalty actually cost them.
    """
    content = round((semantic * SEMANTIC_WEIGHT) + (keyword * KEYWORD_WEIGHT), 2)
    bonus   = direct_skill_match_bonus(resume_raw, jd_raw) if resume_raw else 0.0
    raw     = content + bonus - format_penalty
    final   = round(max(0.0, min(100.0, raw)), 2)

    return {
        "semantic":       round(semantic, 2),
        "keyword":        round(keyword, 2),
        "skill_bonus":    bonus,
        "format_penalty": round(format_penalty, 2),
        "content_score":  content,
        "final":          final,
    }

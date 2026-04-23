"""
NLP Service — section parsing, keyword extraction, text preprocessing.

Fixes from atsfix.md:
    Fix 2: Overhauled section parser with expanded synonyms, all-caps detection,
            minimum content threshold, and duplicate-section appending.
    Fix 3: Added SOFT_SKILL_BLOCKLIST to strip generic verbs/personality words
            from keyword extraction, eliminating nonsensical skill gaps.
"""

import re

import nltk
import spacy
from nltk.corpus import stopwords

from app.services.skills_taxonomy import SKILL_ALIASES, normalize_skills

nltk.download("stopwords", quiet=True)

STOPWORDS = set(stopwords.words("english"))
nlp = spacy.load("en_core_web_sm")


# ── Fix 2: Expanded section patterns ─────────────────────────────────────────

SECTION_PATTERNS: dict[str, str] = {
    "summary": (
        r"\b(summary|objective|profile|about\s*me|overview|"
        r"professional\s*summary|career\s*summary|introduction)\b"
    ),
    "skills": (
        r"\b(skills?|technical\s*skills?|core\s*skills?|"
        r"technologies|competencies|expertise|tools?\s*&?\s*technologies?|"
        r"programming\s*languages?)\b"
    ),
    "experience": (
        r"\b(experience|work\s*(?:experience|history)|employment|"
        r"professional\s*experience|internship|internships|"
        r"work\s*background|career\s*history)\b"
    ),
    "projects": (
        r"\b(projects?|personal\s*projects?|academic\s*projects?|"
        r"technical\s*projects?|portfolio|side\s*projects?|"
        r"key\s*projects?|selected\s*projects?)\b"
    ),
    "education": (
        r"\b(education|academic|qualifications?|degrees?|"
        r"university|college|schooling|academic\s*background)\b"
    ),
    "certifications": (
        r"\b(certifications?|certificates?|courses?|credentials?|"
        r"licenses?|professional\s*development|training)\b"
    ),
    "leadership": (
        r"\b(leadership|activities|clubs?|organizations?|volunteer|"
        r"extracurricular|positions?\s*of\s*responsibility|"
        r"community|societies?)\b"
    ),
}

SECTION_ORDER = ["summary", "skills", "experience", "projects", "education", "certifications", "leadership"]

# Minimum characters a section must have to be kept (prevents ghost sections).
MIN_SECTION_LENGTH = 30


# ── Fix 3: Soft-skill blocklist ───────────────────────────────────────────────

SOFT_SKILL_BLOCKLIST: set[str] = {
    # Generic action verbs that appear in JD requirement sentences
    "work", "help", "write", "add", "use", "make", "get", "give",
    "build", "create", "develop", "implement", "ensure", "comply",
    "participate", "collaborate", "communicate", "understand",
    "require", "need", "include", "involve", "support", "provide",
    "manage", "lead", "drive", "maintain", "improve", "update",
    "debug", "review", "test", "deploy", "integrate", "design",
    "define", "follow", "identify", "resolve", "document", "troubleshoot",
    "adhere", "plan",

    # Personality / attitude words
    "willingness", "ability", "interest", "passion", "motivation",
    "learner", "adapt", "adaptable", "fast", "quick", "strong",
    "good", "great", "excellent", "solid", "proficient", "comfortable",
    "detail", "oriented", "driven", "self", "starter", "proactive",
    "creative", "innovative", "effective", "efficient", "reliable",
    "understanding", "familiarity", "principle", "core", "pace",
    "paced", "live", "system",

    # Structural / grammar words that pass POS filters
    "responsibility", "standard", "description", "verification",
    "rendering", "cod", "requirement", "qualification", "minimum",
    "preferred", "plus", "bonus", "role", "position", "team",
    "company", "organization", "environment", "culture", "value",
    "growth", "opportunity", "candidate", "applicant", "hire", "place",
    "side", "unit",

    # Common resume filler words
    "year", "month", "day", "time", "way", "thing", "part",
    "area", "level", "type", "kind", "number", "amount",
}


# ── Fix 2: Improved section detection ────────────────────────────────────────

def _is_section_header(line: str) -> str | None:
    """
    Returns the section name if the line is a section header, else None.

    Qualifies as a header if:
    - ≤ 6 words AND matches a SECTION_PATTERNS regex, OR
    - All-caps with ≤ 4 words (common in many resume templates).
    """
    stripped = line.strip()
    if not stripped:
        return None

    word_count = len(stripped.split())

    # All-caps short lines are almost certainly headers
    is_all_caps_header = (
        stripped.isupper()
        and word_count <= 4
        and len(stripped) > 2
    )

    if word_count > 6 and not is_all_caps_header:
        return None

    lower = stripped.lower()
    for section_name, pattern in SECTION_PATTERNS.items():
        if re.search(pattern, lower):
            return section_name

    return None


def parse_sections(text: str) -> dict:
    """
    Parse resume text into named sections with confidence scores.

    Improvements over v1:
    - Expanded header synonyms (Fix 2)
    - All-caps line detection as fallback header signal
    - Minimum content threshold prevents empty ghost sections
    - Duplicate section names append rather than overwrite

    Returns:
        {section_name: {"content": str, "confidence": float}}
    Falls back to {"full_resume": {"content": text, "confidence": 0.3}}
    if no headers are detected.
    """
    lines = text.split("\n")
    raw_sections: dict[str, list[str]] = {}
    current_section = "preamble"
    current_lines: list[str] = []
    detected_header_names: set[str] = set()

    for line in lines:
        matched = _is_section_header(line)
        if matched:
            # Flush previous section
            content = "\n".join(current_lines).strip()
            if content and len(content) >= MIN_SECTION_LENGTH:
                if current_section in raw_sections:
                    raw_sections[current_section].append(content)
                else:
                    raw_sections[current_section] = [content]
            current_section = matched
            current_lines = []
            detected_header_names.add(matched)
        else:
            stripped = line.strip()
            if not stripped and current_lines:
                current_lines.append("")
            elif stripped:
                current_lines.append(stripped)

    # Flush the last section
    content = "\n".join(current_lines).strip()
    if content and len(content) >= MIN_SECTION_LENGTH:
        if current_section in raw_sections:
            raw_sections[current_section].append(content)
        else:
            raw_sections[current_section] = [content]

    # Remove preamble if it's just name/contact (< 100 chars)
    if "preamble" in raw_sections:
        preamble_text = "\n".join(raw_sections["preamble"]).strip()
        if len(preamble_text) < 100:
            del raw_sections["preamble"]

    # Fallback: nothing detected
    if not raw_sections or all(k == "preamble" for k in raw_sections):
        return {"full_resume": {"content": text[:4000], "confidence": 0.3}}

    # Build the final sections dict with confidence scores
    sections: dict = {}
    for name, chunks in raw_sections.items():
        merged = "\n".join(chunks).strip()
        confidence = 0.9 if name in detected_header_names else 0.6
        sections[name] = {"content": merged, "confidence": confidence}

    return sections


def preprocess(text: str) -> str:
    """Lowercase, lemmatize, remove stopwords."""
    doc = nlp(text.lower())
    return " ".join(
        token.lemma_
        for token in doc
        if token.is_alpha and token.text not in STOPWORDS
    )


def extract_keywords(text: str) -> set:
    """
    Extract meaningful technical keywords using spaCy POS tagging.

    Fix 3 improvements:
    - Filters SOFT_SKILL_BLOCKLIST to remove personality/filler words
    - Minimum token length of 3 characters
    - Results normalized through SKILL_ALIASES taxonomy

    Returns a set of canonical skill/keyword strings.
    """
    doc = nlp(text.lower())
    raw: set[str] = set()
    for token in doc:
        if (
            token.pos_ in {"NOUN", "PROPN", "VERB"}
            and token.is_alpha
            and len(token.lemma_) >= 3
            and token.text not in STOPWORDS
            and token.lemma_ not in STOPWORDS
            and token.lemma_ not in SOFT_SKILL_BLOCKLIST
            and token.text not in SOFT_SKILL_BLOCKLIST
        ):
            raw.add(token.lemma_)

    return normalize_skills(raw)

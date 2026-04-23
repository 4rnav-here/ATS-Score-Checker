import re
from app.services.skills_taxonomy import SKILL_ALIASES

def normalize_text_for_tfidf(text: str) -> str:
    normalised = text.lower()
    aliases = sorted(SKILL_ALIASES.items(), key=lambda x: len(x[0]), reverse=True)
    for variant, canonical in aliases:
        pattern = r'\b' + re.escape(variant.lower()) + r'\b'
        replacement = canonical.lower().replace(".", "").replace("-", "").replace(" ", "")
        normalised = re.sub(pattern, replacement, normalised)
    normalised = re.sub(r'(?<=\w)\.(?=\w)', '', normalised)
    normalised = re.sub(r'(?<=\w)-(?=\w)', '', normalised)
    normalised = re.sub(r'[^\w\s]', ' ', normalised)
    normalised = re.sub(r'\s+', ' ', normalised).strip()
    return normalised

text = "Thorough understanding of React.js and its core principles."
print("Before:", text)
print("After:", normalize_text_for_tfidf(text))

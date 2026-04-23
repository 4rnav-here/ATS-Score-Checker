"""
Job Match Scoring Tool — scores how well a job description matches a candidate.
Uses the same Sentence-BERT + TF-IDF pipeline from the ATS scoring engine.
"""

from app.services.embedding_service import embed
from app.services.nlp_service import preprocess, extract_keywords
from app.services.scoring_service import tfidf_keyword_score

from sklearn.metrics.pairwise import cosine_similarity


def score_job_match(
    job_description: str,
    resume_text: str,
    resume_keywords: list[str],
) -> float:
    """
    Score how well a job description matches the candidate resume.

    Uses:
        - Semantic similarity (Sentence-BERT cosine sim) × 0.7
        - Keyword overlap × 0.3

    Returns:
        float 0-100
    """
    # Semantic component
    jd_clean = preprocess(job_description)
    resume_clean = preprocess(resume_text)

    jd_emb = embed(jd_clean)
    res_emb = embed(resume_clean)

    sem_raw = float(cosine_similarity([res_emb], [jd_emb])[0][0])
    sem_raw = max(0.0, min(1.0, sem_raw))
    sem_score = sem_raw * 100

    # Keyword component
    jd_keys = extract_keywords(job_description)
    resume_key_set = set(resume_keywords)
    if jd_keys:
        kw_score = (len(resume_key_set & jd_keys) / len(jd_keys)) * 100
    else:
        kw_score = 0.0

    # Weighted combination (same weights as ATS scoring)
    final = sem_score * 0.7 + kw_score * 0.3
    return round(max(0.0, min(100.0, final)), 1)

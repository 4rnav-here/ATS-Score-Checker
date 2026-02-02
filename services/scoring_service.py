from sklearn.metrics.pairwise import cosine_similarity
from core.config import SEMANTIC_WEIGHT, KEYWORD_WEIGHT

def semantic_score(resume_emb, jd_emb):
    score = cosine_similarity([resume_emb], [jd_emb])[0][0]
    return round(score * 100, 2)   # 0–100


def keyword_score(resume_keys, jd_keys):
    if not jd_keys:
        return 0
    return round((len(resume_keys & jd_keys) / len(jd_keys)) * 100, 2)


def final_score(semantic, keyword):
    return round((semantic * 0.7) + (keyword * 0.3), 2)



def is_valid_jd(jd_text):
    return len(jd_text.split()) >= 20

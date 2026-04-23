import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def tfidf_keyword_score(resume_norm: str, jd_norm: str) -> float:
    try:
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform([resume_norm, jd_norm])
        score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        return round(score * 100, 2)
    except Exception as e:
        return 0.0

jd_keys = "react ssr javascript communication troubleshooting"
resume_keys = "react javascript java python sql nodejs"

print("Score:", tfidf_keyword_score(resume_keys, jd_keys))

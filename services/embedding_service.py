from sentence_transformers import SentenceTransformer
from functools import lru_cache
from core.config import MODEL_NAME

@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(MODEL_NAME)

def embed(text):
    model = get_model()
    return model.encode(text)

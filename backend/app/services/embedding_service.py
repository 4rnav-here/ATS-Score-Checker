from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import MODEL_NAME


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load Sentence-BERT model once per process lifetime."""
    return SentenceTransformer(MODEL_NAME)


def embed(text: str) -> np.ndarray:
    """Embed a single text string → 384-dim vector."""
    return get_model().encode(text)


def embed_sections(sections: dict) -> dict:
    """
    Embed each detected resume section individually.

    Args:
        sections: {section_name: {"content": str, "confidence": float}}

    Returns:
        {section_name: np.ndarray}
    """
    model = get_model()
    return {
        name: model.encode(data["content"])
        for name, data in sections.items()
        if data.get("content", "").strip()
    }

import spacy
from nltk.corpus import stopwords
import nltk

nltk.download("stopwords")
STOPWORDS = set(stopwords.words("english"))

nlp = spacy.load("en_core_web_sm")

def preprocess(text):
    doc = nlp(text.lower())
    return " ".join(
        token.lemma_
        for token in doc
        if token.is_alpha and token.text not in STOPWORDS
    )

def extract_keywords(text):
    doc = nlp(text.lower())
    return {
        token.lemma_
        for token in doc
        if token.pos_ in ["NOUN", "PROPN", "VERB"]
    }

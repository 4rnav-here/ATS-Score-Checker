import pdfplumber
from core.logger import logger

def extract_text(file):
    try:
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""

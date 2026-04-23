import ollama

from app.core.config import LLM_MODEL
from app.core.logger import logger


def ask_llm(prompt: str, temperature: float = 0.3) -> str:
    """
    Send a prompt to the local Ollama LLM and return the text response.

    Phase 1 placeholder — no heavy usage expected yet.
    Requires Ollama running locally with the configured model pulled.
    """
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional resume and career assistant.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            options={"temperature": temperature},
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return f"LLM Error: {str(e)}"

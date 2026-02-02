import ollama

MODEL = "mistral:latest"   # or phi3 if RAM is low

def ask_llm(prompt, temperature=0.3):
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional resume and career assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": temperature
            }
        )

        return response["message"]["content"]

    except Exception as e:
        return f"LLM Error: {str(e)}"

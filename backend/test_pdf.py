from app.services.pdf_service import extract_text
with open("../Arnav Trivedi.pdf", "rb") as f:
    text = extract_text(f)
print(text[:2000])

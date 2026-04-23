import pdfplumber
with open("../Arnav Trivedi.pdf", "rb") as f:
    with pdfplumber.open(f) as pdf:
        words = pdf.pages[0].extract_words()
        for w in words[:40]:
            print(f"{w['text']}: x0={w['x0']:.1f}, right={w['x1']:.1f}")
        print(f"Page width: {pdf.pages[0].width}")

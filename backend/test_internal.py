import asyncio
import os
from app.core.database import AsyncSessionLocal
from app.routers.analyze import analyze_resume
from fastapi import UploadFile

JD_TEXT = """
Requirements:
Thorough understanding of React.js and its core principles.
Willingness to learn new frameworks and languages where required.
Interest and ability to work across the stack.
Familiarity with Server Side Rendering (SSR).
Must have good written and oral communication skills, be a fast learner
and have the ability to adapt quickly to a fast-paced development environment.

Responsibilities:
Collaborate with other developers and help in development of current system
and adding new features to the platform.
Active participate in troubleshooting, debugging and updating current live system.
Ensure unit and integration level verification plan are in place and adheres to
great quality of code at all time.
Comply with coding standards and technical design.
"""

async def run():
    pdf_path = "../Arnav Trivedi.pdf"
    print(f"Testing with {pdf_path}...")
    
    with open(pdf_path, "rb") as f:
        # Mock UploadFile
        class MockUploadFile:
            def __init__(self, file_obj):
                self.file_obj = file_obj
                self.filename = "resume.pdf"
            async def read(self):
                return self.file_obj.read()
            
        file_obj = MockUploadFile(f)
        
        async with AsyncSessionLocal() as db:
            result = await analyze_resume(file=file_obj, jd_text=JD_TEXT, db=db)
            
    scores = result.scores
    print("\n=== SCORE BREAKDOWN ===")
    print(f"Semantic Score:   {scores.semantic:.1f}")
    print(f"TF-IDF Score:     {scores.keyword:.1f}")
    print(f"Skill Bonus:      {scores.skill_bonus:.1f}")
    print(f"Format Penalty:   -{scores.format_penalty:.1f}")
    print(f"Content Score:    {scores.content_score:.1f}")
    print(f"FINAL SCORE:      {scores.final:.1f} / 100")

    print("\n=== SECTIONS FOUND ===")
    print(result.sections_found)

    print("\n=== SKILL GAPS (should be technical only) ===")
    print(result.skill_gaps)

    print("\n=== EXPERIENCE ===")
    print(result.experience)

    print("\n=== SECTION SCORES ===")
    print(result.section_scores)

    assert scores.final >= 45,      f"FAIL: Final score too low ({scores.final})"
    assert scores.semantic >= 45,   f"FAIL: Semantic score too low ({scores.semantic})"
    assert scores.keyword >= 20,    f"FAIL: TF-IDF score too low ({scores.keyword})"

    bad_gaps = {"willingness", "ability", "learner", "adapt", "have", "work", "help"}
    found_bad = bad_gaps & set(result.skill_gaps)
    assert not found_bad, f"FAIL: Soft skills still in gaps: {found_bad}"

    print("\n✅ ALL ASSERTIONS PASSED")

if __name__ == "__main__":
    asyncio.run(run())

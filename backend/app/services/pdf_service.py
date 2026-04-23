"""
PDF Service — column-aware text extraction + layout metadata.

Fix 1 from atsfix.md:
    pdfplumber's default extract_text() interleaves left/right columns,
    corrupting multi-column resumes before any NLP runs.
    This module detects columns per page and extracts each independently.
"""

import io

import pdfplumber

from app.core.logger import logger


def _extract_page_text_column_aware(page) -> str:
    """
    Extract text from a single pdfplumber page, handling multi-column layouts.

    Strategy:
    - Extract all words with bounding boxes.
    - If > 15% of words have x0 > page midpoint: treat as two-column.
    - Two-column: sort and join each column independently, then concatenate.
    - Single-column: sort by (top, x0) and join normally.

    This preserves sentence coherence within each column instead of
    interleaving words from both sides (the default pdfplumber behaviour).
    """
    words = page.extract_words(
        x_tolerance=3,
        y_tolerance=3,
        keep_blank_chars=False,
        use_text_flow=False,
    )

    if not words:
        return ""

    page_mid = page.width / 2

    left_words  = [w for w in words if float(w["x0"]) < page_mid]
    right_words = [w for w in words if float(w["x0"]) >= page_mid]

    # Group words into lines by top position to find line starts
    lines_by_top = {}
    for w in words:
        top = round(float(w["top"]) / 5) * 5
        if top not in lines_by_top:
            lines_by_top[top] = []
        lines_by_top[top].append(w)
        
    left_starts = 0
    right_starts = 0
    
    for top, line_words in lines_by_top.items():
        line_words.sort(key=lambda x: float(x["x0"]))
        first_word_x0 = float(line_words[0]["x0"])
        if first_word_x0 < page_mid - 20: # Use page_mid - 20 to be safe
            left_starts += 1
        elif first_word_x0 >= page_mid - 20:
            right_starts += 1

    # It's multi-column if > 15% of all lines *start* in the right half.
    # In single-column resumes, almost all lines start on the left.
    is_multi_column = (right_starts / max(len(lines_by_top), 1)) > 0.15

    def words_to_text(word_list: list) -> str:
        if not word_list:
            return ""
        # Group words into lines by vertical position (5px tolerance).
        sorted_words = sorted(
            word_list,
            key=lambda w: (round(float(w["top"]) / 5) * 5, float(w["x0"]))
        )
        lines = []
        current_line: list = []
        last_top = None

        for w in sorted_words:
            top = float(w["top"])
            if last_top is None or abs(top - last_top) > 5:
                if current_line:
                    lines.append(" ".join(t["text"] for t in current_line))
                current_line = [w]
                last_top = top
            else:
                current_line.append(w)

        if current_line:
            lines.append(" ".join(t["text"] for t in current_line))

        return "\n".join(lines)

    if is_multi_column:
        left_text  = words_to_text(left_words)
        right_text = words_to_text(right_words)
        return left_text + "\n\n" + right_text
    else:
        return words_to_text(left_words + right_words)


def extract_text(file: io.BytesIO) -> str:
    """
    Extract all text from every page of a PDF, column-aware.

    Returns the full resume text as a single string with pages separated
    by double newlines. Returns empty string on failure.
    """
    try:
        with pdfplumber.open(file) as pdf:
            page_texts = []
            for page in pdf.pages:
                text = _extract_page_text_column_aware(page)
                if text.strip():
                    page_texts.append(text)
            return "\n\n".join(page_texts)
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        return ""


def extract_layout_metadata(file: io.BytesIO) -> dict:
    """
    Inspect PDF layout to detect ATS-unfriendly formatting.

    Returns a dict consumed by improvement_service.compute_format_penalty().

    NOTE: The caller must seek(0) between extract_text() and this call
    because both need to open the same BytesIO from the start.
    """
    metadata = {
        "has_tables":       False,
        "is_multi_column":  False,
        "low_text_density": False,
        "page_count":       0,
    }

    try:
        with pdfplumber.open(file) as pdf:
            metadata["page_count"] = len(pdf.pages)

            for page in pdf.pages:
                # Table detection
                if page.find_tables():
                    metadata["has_tables"] = True

                # Multi-column detection
                words = page.extract_words()
                if words:
                    page_mid = page.width / 2
                    
                    lines_by_top = {}
                    for w in words:
                        top = round(float(w["top"]) / 5) * 5
                        if top not in lines_by_top:
                            lines_by_top[top] = []
                        lines_by_top[top].append(w)
                        
                    right_starts = 0
                    for top, line_words in lines_by_top.items():
                        line_words.sort(key=lambda x: float(x["x0"]))
                        first_word_x0 = float(line_words[0]["x0"])
                        if first_word_x0 >= page_mid - 20:
                            right_starts += 1

                    if (right_starts / max(len(lines_by_top), 1)) > 0.15:
                        metadata["is_multi_column"] = True

                # Text density detection
                chars = len(page.extract_text() or "")
                area  = float(page.width) * float(page.height)
                if area > 0 and (chars / area) < 0.05:
                    metadata["low_text_density"] = True

    except Exception as e:
        logger.error(f"Layout metadata extraction failed: {e}")

    return metadata

"""
Score Card Formatter — formats ATS analysis results for Telegram.

Target: under 600 characters. Uses Telegram MarkdownV2 escape-safe formatting.
"""


def _score_bar(score: float, width: int = 10) -> str:
    """Visual progress bar using Unicode blocks."""
    filled = round(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _score_emoji(score: float) -> str:
    """Color-coded emoji for score ranges."""
    if score >= 75:
        return "🟢"
    if score >= 50:
        return "🟡"
    return "🔴"


def format_score_card(result: dict) -> str:
    """
    Format a full ATS analysis result as a concise Telegram message.

    Args:
        result: The full AnalysisResponse dict from /api/analyze.

    Returns:
        Markdown-formatted string ready for Telegram.
    """
    scores = result.get("scores", {})
    score = scores.get("final", 0)
    sem = scores.get("semantic", 0)
    kw = scores.get("keyword", 0)
    penalty = scores.get("format_penalty", 0)

    gaps = result.get("skill_gaps", [])[:6]
    missing = result.get("sections_missing", [])

    experience = result.get("experience", {})
    level = experience.get("level", "")
    years = experience.get("total_years", 0)

    lines = [
        "*📊 ATS Analysis Complete*",
        "",
        f"{_score_emoji(score)} *Overall Score: {score:.0f}/100*",
        f"`{_score_bar(score)}`",
        "",
        f"• Semantic match: *{sem:.0f}*",
        f"• Keyword overlap: *{kw:.0f}*",
    ]

    if penalty > 0:
        lines.append(f"• Format penalty: *-{penalty:.0f}* ⚠️")

    if level:
        lines += ["", f"👤 *Experience: {level.capitalize()}* ({years:.0f}yr)"]

    if missing:
        missing_str = ", ".join(missing)
        lines += ["", f"❌ *Missing sections:* {missing_str}"]

    if gaps:
        lines += ["", "*🔍 Top skill gaps:*"]
        lines += [f"  • {g}" for g in gaps]

    lines += ["", "_Tap a button below to continue:_"]

    return "\n".join(lines)

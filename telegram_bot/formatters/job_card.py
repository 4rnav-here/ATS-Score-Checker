"""
Job Card Formatter — formats job search results for Telegram messages.
Handles pagination and individual job card rendering.
"""


def _match_bar(score: float) -> str:
    """Visual match bar for job scoring."""
    filled = round(score / 100 * 8)
    return "█" * filled + "░" * (8 - filled)


def format_single_job(job: dict, index: int) -> str:
    """
    Format a single job as a Telegram-readable card.

    Args:
        job: Job dict with title, company, location, match_score, url, etc.
        index: Display number (1-indexed).

    Returns:
        Markdown-formatted job card string.
    """
    title = job.get("title", "Unknown Position")
    company = job.get("company", "Unknown Company")
    location = job.get("location", "")
    score = job.get("match_score", 0)
    url = job.get("url", "")

    salary = ""
    if job.get("salary_min") and job.get("salary_max"):
        salary = f"\n💰 ₹{job['salary_min']:,.0f} - ₹{job['salary_max']:,.0f}"

    source_emoji = "🌐" if job.get("source") == "remotive" else "💼"

    card = (
        f"*{index}. {title}*\n"
        f"🏢 {company} · {location}\n"
        f"Match: `{_match_bar(score)}` {score:.0f}%{salary}\n"
        f"{source_emoji} [View Job]({url})"
    )
    return card


def format_job_page(jobs: list[dict], page: int, page_size: int) -> str:
    """
    Format a page of jobs for the paginated job list.

    Args:
        jobs: All job results.
        page: Current page number (0-indexed).
        page_size: Number of jobs per page.

    Returns:
        Markdown-formatted page of job cards.
    """
    start = page * page_size
    end = start + page_size
    page_jobs = jobs[start:end]

    header = f"*💼 Job Matches ({start + 1}-{min(end, len(jobs))} of {len(jobs)})*\n\n"
    cards = "\n\n---\n\n".join(
        format_single_job(j, start + i + 1) for i, j in enumerate(page_jobs)
    )
    return header + cards

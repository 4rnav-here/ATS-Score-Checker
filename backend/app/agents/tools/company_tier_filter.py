"""
Company Tier Filter — static quality tagging for Indian tech employers.

Tier 1: Top product companies, FAANG India offices, funded unicorns.
Tier 2: Mid-tier funded startups and well-known service companies.
Tier 3: Unknown / unranked (default).

Used by job_search_agent.py to boost match scores for quality employers.
"""

TIER_1_INDIA: set[str] = {
    # Global FAANG / Big Tech India offices
    "google", "microsoft", "amazon", "meta", "apple",
    "adobe", "salesforce", "oracle", "sap", "ibm",
    "intel", "qualcomm", "nvidia", "cisco", "vmware",
    # Indian product unicorns & top startups
    "zepto", "swiggy", "zomato", "razorpay", "cred",
    "phonepe", "groww", "meesho", "browserstack", "freshworks",
    "postman", "chargebee", "zoho", "druva", "clevertap",
    "inmobi", "ola", "dunzo", "slice", "jupiter",
    "dream11", "games24x7", "mpl", "unacademy", "byju",
    "vedantu", "testbook", "navi", "smallcase", "zerodha",
    "upstox", "fampay", "open", "setu", "m2p",
    "juspay", "cashfree", "signzy", "bureau", "perfios",
    "delhivery", "shiprocket", "loadshare", "blowhorn",
    "rapido", "yulu", "bounce", "ather", "ola electric",
    # Top service / consulting with product roles
    "thoughtworks", "atlassian", "walmart global tech",
    "goldman sachs", "morgan stanley", "deutsche bank",
    "jpmorgan", "barclays", "credit suisse", "ubs",
    "flipkart", "myntra", "paytm", "mswipe", "instamojo",
    "policybazaar", "acko", "digit", "coverfox",
    "lenskart", "nykaa", "mamaearth", "purplle",
    "urban company", "housejoy", "sulekha",
}

TIER_2_INDIA: set[str] = {
    # Mid-tier funded startups
    "leadsquared", "darwinbox", "mindtickle", "capillary",
    "greythr", "khatabook", "okcredit", "niyo", "fi money",
    "tartan", "decentro", "digio", "hyperface", "nadcab",
    "mfine", "portea", "pristyn care", "practo", "1mg",
    "pharmeasy", "netmeds", "tata 1mg", "healthifyme",
    "cult.fit", "plixxo", "sharechat", "moj", "josh",
    "lokal", "dailyhunt", "inshorts", "newslaundry",
    "spinny", "cars24", "cardekho", "droom", "acko",
    "infra.market", "zetwerk", "moglix", "industrybuying",
    "udaan", "jumbotail", "ninjacart", "dehaat",
    "beenext", "blume ventures", "stellaris",
    "sprinklr", "wingify", "exotel", "ozonetel", "knowlarity",
    "pepper content", "contentsquare", "helpshift",
    "zendesk india", "freshdesk", "kayako",
    # Tier-2 IT / consulting with dev roles
    "mphasis", "hexaware", "niit technologies", "mastech",
    "kpit", "cyient", "tata elxsi", "persistent systems",
    "zensar", "birlasoft", "mtx", "sonata software",
}


def get_company_tier(company_name: str) -> int:
    """
    Return quality tier for a company name.

    Returns:
        1 — Tier 1 (top product companies, unicorns, FAANG India)
        2 — Tier 2 (mid-tier funded startups, good service companies)
        3 — Unknown / unranked
    """
    normalized = company_name.strip().lower()
    for name in TIER_1_INDIA:
        if name in normalized or normalized in name:
            return 1
    for name in TIER_2_INDIA:
        if name in normalized or normalized in name:
            return 2
    return 3


def tier_score_boost(tier: int) -> float:
    """Return the match score boost for a given tier."""
    if tier == 1:
        return 15.0
    if tier == 2:
        return 7.0
    return 0.0


def tier_label(tier: int) -> str | None:
    """Return display label for a tier, or None for tier 3."""
    if tier == 1:
        return "⭐ Top Company"
    if tier == 2:
        return "✅ Quality Employer"
    return None

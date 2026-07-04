import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring rules (max = 10)
# ---------------------------------------------------------------------------
#   company_name exists   → +1
#   source exists         → +1
#   founded year exists   → +1
#   founder exists        → +3
#   website exists        → +2
#   website is a valid
#    company domain       → +2  (on top of the +2 above, capped at 10)
# ---------------------------------------------------------------------------

MAX_SCORE = 10

# Domains that are NOT valid company websites (aggregators / generic sites)
_NOISE_DOMAINS = {
    "crunchbase.com", "linkedin.com", "tracxn.com", "inc42.com",
    "f6s.com", "yourstory.com", "wikipedia.org", "twitter.com",
    "facebook.com", "instagram.com", "youtube.com",
    "moneycontrol.com", "economictimes.indiatimes.com",
    "allcourierguide.com", "cdlu.in", "grokipedia.com",
    "net-a-porter.com", "glassdoor.com", "ambitionbox.com",
}

_VALID_YEAR_RE = re.compile(r"^\d{4}$")


def _is_valid_company_domain(website: str) -> bool:
    """
    Return True when the website URL looks like a real company domain
    (not a noise/aggregator site, and structurally a proper URL).
    """
    if not website:
        return False
    try:
        parsed = urlparse(website)
        if not parsed.scheme or not parsed.netloc:
            return False
        netloc = parsed.netloc.lower().removeprefix("www.")
        # Reject if it matches any known noise domain
        for noise in _NOISE_DOMAINS:
            if netloc == noise or netloc.endswith("." + noise):
                return False
        return True
    except Exception:
        return False


def calculate_score(company) -> float:
    """
    Calculate a confidence score for a Company ORM object.

    Scoring rules
    -------------
    +1  company_name is non-empty
    +1  source is non-empty
    +1  founded is a valid 4-digit year
    +3  founder is non-empty
    +2  website is non-empty
    +2  website passes valid-company-domain check
    ─────────────────────────────────────────────
    10  maximum

    Returns a float in [0.0, 10.0].
    """
    score = 0.0

    # +1 — company name
    if company.company_name and company.company_name.strip():
        score += 1

    # +1 — source
    if company.source and company.source.strip():
        score += 1

    # +1 — founded year
    if company.founded and _VALID_YEAR_RE.match(company.founded.strip()):
        score += 1

    # +3 — founder
    if company.founder and company.founder.strip():
        score += 3

    # +2 — website exists
    if company.website and company.website.strip():
        score += 2

        # +2 additional — website is a valid company domain
        if _is_valid_company_domain(company.website):
            score += 2

    return min(score, MAX_SCORE)

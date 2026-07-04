import time
import logging
from urllib.parse import urlparse, urlunparse
from ddgs import DDGS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Blacklisted domains — aggregators, directories, social media, news sites
# ---------------------------------------------------------------------------
BLACKLISTED_DOMAINS = {
    # Business directories / aggregators
    "crunchbase.com",
    "tracxn.com",
    "inc42.com",
    "f6s.com",
    "yourstory.com",
    "angellist.com",
    "startupindia.gov.in",
    "zaubacorp.com",
    "tofler.in",
    "ambitionbox.com",
    "glassdoor.com",
    "justdial.com",
    "indiamart.com",
    "tradeindia.com",
    "clutch.co",
    "g2.com",
    "owler.com",
    "pitchbook.com",
    "zoominfo.com",
    # Professional networks
    "linkedin.com",
    # Encyclopaedias
    "wikipedia.org",
    "wikimedia.org",
    # Social / consumer platforms
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    # News / financial media
    "moneycontrol.com",
    "economictimes.indiatimes.com",
    "livemint.com",
    "business-standard.com",
    "thehindu.com",
    "ndtv.com",
    "techcrunch.com",
    "forbes.com",
    "reuters.com",
    "bloomberg.com",
    # Misc / false positives found in testing
    "zerodha.com",
    "amazon.com",
    "flipkart.com",
    "allcourierguide.com",
    "courierpoint.com",
    "net-a-porter.com",
    "cdlu.in",
    "grokipedia.com",
    "mojeek.com",
    "mail.google.com",
    "apps.apple.com",
    "play.google.com",
    # Tracking / carrier lookup pages (subdomain-level noise)
    "tracking.mahindralogistics.com",
}


def _extract_root_domain_url(raw_url: str) -> str | None:
    """
    Given any URL, return only scheme + netloc (root domain).

    Examples:
        https://www.delhivery.com/tracking  →  https://www.delhivery.com
        https://shiprocket.in/blog?q=1      →  https://shiprocket.in
    """
    try:
        parsed = urlparse(raw_url)
        if not parsed.scheme or not parsed.netloc:
            return None
        root = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
        return root
    except Exception:
        return None


def _is_blacklisted(url: str) -> bool:
    """Return True if the URL belongs to a blacklisted domain."""
    try:
        netloc = urlparse(url).netloc.lower().removeprefix("www.")
        return any(
            netloc == bl or netloc.endswith("." + bl)
            for bl in BLACKLISTED_DOMAINS
        )
    except Exception:
        return False


def _search(query: str, max_results: int = 10) -> list[dict]:
    """Run a DuckDuckGo text search and return results. Returns [] on failure."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as exc:
        logger.warning("[website_discovery] DDG search failed for '%s': %s", query, exc)
        return []


def _pick_best_root(results: list[dict], company_name: str) -> str | None:
    """
    From a list of DDG result dicts, pick the best root URL.
    Preference: first clean (non-blacklisted) candidate.
    Fallback: first blacklisted root if nothing clean found.
    """
    clean: list[str] = []
    dirty: list[str] = []

    for result in results:
        raw_url: str = result.get("href", "")
        if not raw_url:
            continue

        root = _extract_root_domain_url(raw_url)
        if not root:
            continue

        blacklisted = _is_blacklisted(raw_url)
        logger.debug(
            "[website_discovery] '%s' | %s | blacklisted=%s",
            company_name, raw_url, blacklisted,
        )

        if blacklisted:
            dirty.append(root)
        else:
            clean.append(root)

    # Return first unique clean result
    seen: set[str] = set()
    for candidate in clean:
        if candidate not in seen:
            seen.add(candidate)
            return candidate

    # Fallback to first dirty result
    if dirty:
        return dirty[0]

    return None


def discover_website(company_name: str) -> str | None:
    """
    Use DuckDuckGo to find the official root website domain for a company.

    Strategy:
      1. Primary query:  '<company_name> official website'
      2. Fallback query: '<company_name> India startup'
      3. Normalize winning URL to root domain only (strip all paths/params).
      4. Skip blacklisted aggregator / directory / social domains.
      5. Small sleep between queries to avoid rate-limiting.

    Logs:
      - Company name being searched
      - Each candidate URL and blacklist decision
      - Final selected domain

    Returns None only if both queries fail or return no usable results.
    """

    logger.info("[website_discovery] Searching website for: '%s'", company_name)

    queries = [
        f"{company_name} official website",
        f"{company_name} India logistics startup",
        f"{company_name} India company site",
    ]

    for i, query in enumerate(queries):
        if i > 0:
            # Brief pause between retry queries to avoid DDG rate-limiting
            time.sleep(1.5)

        results = _search(query, max_results=10)

        if not results:
            logger.debug(
                "[website_discovery] '%s' | query '%s' returned no results, trying next.",
                company_name, query,
            )
            continue

        selected = _pick_best_root(results, company_name)

        if selected:
            logger.info(
                "[website_discovery] '%s' → %s (via query: '%s')",
                company_name, selected, query,
            )
            return selected

        logger.debug(
            "[website_discovery] '%s' | query '%s' had results but all filtered out.",
            company_name, query,
        )

    logger.warning(
        "[website_discovery] '%s' → no usable result after all queries.", company_name
    )
    return None

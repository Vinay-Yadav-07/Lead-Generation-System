import logging
import re
import time
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from models.company import Company
from models.evidence import Evidence
from models.lead import Lead
from models.outreach import OutreachLog
from services.company_discovery import discover_companies
from services.website_discovery import BLACKLISTED_DOMAINS

logger = logging.getLogger(__name__)

EXTRA_NOISE_DOMAINS = {
    "bing.com",
    "imarcgroup.com",
    "iid.org.in",
    "infoisinfo.co.in",
    "startuptalky.com",
    "inventiva.co.in",
    "logisticsinsider.in",
    "theindianwire.com",
    "engati.ai",
    "startupgrantsindia.com",
    "indiaai.gov.in",
    "digitalindia.gov.in",
    "wellfound.com",
    "builtin.com",
    "zimyo.com",
    "skubiq.com",
    "themindstudios.com",
    "bvp.com",
    "reddit.com",
    "ensun.io",
    "visioncapital.co.in",
    "indianretailer.com",
    "launchlify.com",
    "godamwale.com",
    "wareiq.com",
    "logisticmart.com",
    "sitelike.org",
    "tradeholding.com",
    "clickpost.ai",
    "nimbuspost.com",
    "screener.in",
    "beststartup.in",
    "privatecircle.co",
    "dnb.com",
    "scribd.com",
    "marketinghack4u.com",
    "99datacd.com",
    "mumbai.startups-list.com",
    "builtinmumbai.in",
    "mumbaitech.team",
    "cutshort.io",
    "business-standard.com",
    "justdial.com",
    "sulekha.com",
    "yellowpages.in",
    "tradeindia.com",
    "indiamart.com",
    "fliarbi.com",
    "internshala.com",
    "apna.co",
    "pharmaceutical-technology.com",
    "webfrog.in",
    "tomumbai.com",
    "ycpauctus.com",
}

BAD_TITLE_RE = re.compile(
    r"^\s*(top|best|list of|how to|where are|what are|why|the rise|"
    r"find\b|startup and seed|companies,\s*company directory|\d+\+?\s+|"
    r".*\b(to know|updated list|alternatives|opportunities|b2b data|"
    r"for leads|companies list|startups list|based .* companies|"
    r"association of|built in|funded startups|top \d+ out of|"
    r"manufacturing companies .* top|page \d+|jobs? in|"
    r"manufacturing production jobs|facility,|consulting)\b)",
    re.I,
)

GENERIC_TITLE_RE = re.compile(
    r"(cargo company|best logistics|leading logistics|service provider|"
    r"global logistics|freight forwarding company|transport services companies|"
    r"cloud based erp|warehouse automation|automation solutions|"
    r"conveyor belt manufacturer|transforming the future|tracking whos got|"
    r"express parcel|courier|lower your costs|contact us|"
    r"mumbai,\s*india|regional headquarters|manufacturer from|"
    r"manufacturing company in|companies in|machinery manufacturers|"
    r"commercial kitchen equipment|about us)",
    re.I,
)

OFFICIAL_SITE_RE = re.compile(
    r"\b(about us|contact us|our company|our products|manufacturing|"
    r"factory|plant|private limited|pvt\.?\s*ltd|limited|solutions|"
    r"services|industries|leadership|management)\b",
    re.I,
)


def clear_pipeline_data(db: Session) -> None:
    db.query(OutreachLog).delete()
    db.query(Evidence).delete()
    db.query(Lead).delete()
    db.query(Company).delete()
    db.commit()


def _root_url(raw_url: str | None) -> str | None:
    if not raw_url:
        return None
    parsed = urlparse(raw_url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))


def _is_noise_domain(url: str | None) -> bool:
    if not url:
        return True
    netloc = urlparse(url).netloc.lower().removeprefix("www.")
    
    # Generic keywords in domains that usually indicate directories, news, blogs, and other noise
    noise_keywords = {
        "magazine", "newswire", "news", "tender", "directory", "bookmark", 
        "listing", "blog", "careers", "jobs", "forum", "press", "media", 
        "review", "guide", "database", "yellowpages", "justdial", "sulekha",
        "indiamart", "tradeindia", "wikipedia", "crunchbase", "linkedin",
        "facebook", "twitter", "x.com", "instagram", "youtube", "pinterest",
        "yookalo", "baltimorenewswire"
    }
    if any(keyword in netloc for keyword in noise_keywords):
        return True

    blocked = BLACKLISTED_DOMAINS | EXTRA_NOISE_DOMAINS
    return any(netloc == item or netloc.endswith("." + item) for item in blocked)


def _is_bad_title(title: str | None) -> bool:
    if not title:
        return False
    return bool(BAD_TITLE_RE.search(title))


def _is_valid_company_name(name: str | None) -> bool:
    if not name:
        return False
    name_clean = name.strip()
    if len(name_clean) < 3 or len(name_clean) > 60:
        return False
    excluded_keywords = {
        "contact", "senior manager", "article", "blog", "home", "careers", "jobs",
        "about", "services", "portfolio", "privacy", "terms", "conditions", "policy",
        "cookie", "login", "register", "signup", "signin", "logout", "admin", "dashboard",
        "faq", "help", "support", "news", "events", "gallery", "map", "location", "address",
        "search", "sitemap", "feed", "rss", "download", "upload", "file", "image", "video",
        "audio", "media", "press", "release", "releases", "newsletter", "subscribe", "unsubscribe",
        "cart", "checkout", "shop", "store", "product", "products", "price", "pricing", "plans",
        "billing", "payment", "invoice", "account", "profile", "settings", "messages", "notifications",
        "magazine", "journal", "gazette", "review", "guide", "list", "directory", "tenders", "bookmark",
        "mou to establish", "training centre"
    }
    name_lower = name_clean.lower()
    for word in excluded_keywords:
        if word in name_lower:
            return False
            
    # Enforce strict word count to filter out sentences, articles, or SEO descriptions
    words = name_clean.split()
    if len(words) > 5:
        return False

    if GENERIC_TITLE_RE.search(name_clean):
        return False
    return True


def _domain_token(url: str) -> str:
    netloc = urlparse(url).netloc.lower().removeprefix("www.")
    domain = netloc.split(":")[0]
    parts = domain.split(".")
    second_level_suffixes = {"co", "com", "net", "org", "ac", "edu", "gov"}
    if len(parts) >= 3 and parts[-2] in second_level_suffixes:
        return parts[-3]
    if len(parts) >= 2:
        return parts[-2]
    return domain


def _fetch_homepage_text(root: str) -> str:
    try:
        response = requests.get(
            root,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if response.status_code >= 400:
            return ""
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        body = soup.get_text(" ", strip=True)
        return f"{title} {body}"[:8000]
    except Exception:
        return ""


def _looks_like_official_company_site(root: str, title: str | None, industry: str) -> bool:
    if _is_bad_title(title):
        return False

    text = _fetch_homepage_text(root)
    if not text:
        return False

    lower = text.lower()
    domain_token = _domain_token(root).replace("-", "").replace("_", "")
    title_text = (title or "").lower()

    # Reject sites with directory, listing, article, blog, forum, or social bookmarking indicators
    noise_indicators = (
        "directory", "list of companies", "top companies", "submit your startup",
        "bookmark", "news", "magazine", "press release", "article", "blog", "careers",
        "job openings", "submit link", "add url", "submit story", "post comment",
        "tender", "tenders", "bidding", "procurement", "newswire", "classifieds",
        "social bookmarking", "submit a post", "bookmark submission", "create backlink"
    )
    if any(noise in lower[:2000] for noise in noise_indicators):
        return False

    industry_ok = not industry or industry.lower() in lower or industry.lower() in title_text
    official_ok = bool(OFFICIAL_SITE_RE.search(text))
    domain_ok = len(domain_token) >= 3 and domain_token in re.sub(r"[^a-z0-9]", "", lower[:2500])

    return official_ok and (industry_ok or domain_ok)


def _company_name_from_url(url: str) -> str:
    domain = _domain_token(url)
    known = {
        "abslogistics": "ABS Logistics",
        "mahindralogistics": "Mahindra Logistics",
        "sjlogistics": "SJ Logistics",
        "totallogistics": "Total Logistics",
        "omlogisticssupplychain": "Om Logistics Supply Chain",
        "apollosupplychain": "Apollo Supply Chain",
        "startuplogistics": "Startup Logistics",
        "allcargologistics": "Allcargo Logistics",
        "cglindia": "CG Logistics",
        "indianlogistics": "Indian Logistics",
        "tigerlogistics": "Tiger Logistics",
        "shipleeindia": "Shiplee India",
        "armstrongltd": "Armstrong",
        "armstrongdematic": "Armstrong Dematic",
        "aajenterprises": "AAJ Enterprises",
        "aioisystems": "AIOI Systems",
        "rhenus": "Rhenus Logistics",
        "dsv": "DSV",
        "falconautotech": "Falcon Autotech",
        "efl3pl": "EFL 3PL",
        "cevalogistics": "CEVA Logistics",
        "burnsmcd": "Burns & McDonnell",
        "ril": "Reliance Industries",
        "gmeindia": "GME India",
        "garimaglobal": "Garima Global",
        "raymerengineering": "Raymer Engineering",
        "protochem": "Proto Chemical Industries",
        "nouryon": "Nouryon",
        "empiremumbai": "Empire Industries",
        "gmtpharmainternational": "GMT Pharma International",
        "ketakiindustries": "Ketaki Industries",
        "perfecttubetools": "Perfect Tube Tools",
        "smcl": "Shree Manufacturing Company",
        "ravikiranindustries": "Ravikiran Industries",
        "uniconcontrols": "Unicon Controls",
        "vardhmantube": "Vardhman Tube",
        "kitchenequip": "Kitchen Equip",
        "vvfltd": "VVF Limited",
    }
    if domain in known:
        return known[domain]

    spaced = re.sub(r"[-_]+", " ", domain)
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", spaced)
    return spaced.title()


def _company_name_from_title(title: str | None, url: str) -> str:
    domain_name = _company_name_from_url(url)
    if not title:
        return domain_name
    if GENERIC_TITLE_RE.search(title):
        return domain_name

    # Split by common title separators: |, :, •, —, –, or hyphen/pipe/colon with whitespace
    parts = re.split(r"\s+[-:•—–|]\s*|\s*[-:•—–|]\s+|\s*\|\s*", title)
    first_part = parts[0].strip()
    
    first_part = re.sub(r"\b(official|website|homepage|home)\b", "", first_part, flags=re.I)
    first_part = first_part.encode("ascii", "ignore").decode("ascii")
    first_part = re.sub(r"\s+", " ", first_part).strip(" .,-|")

    # If first part is too long, it's likely a sentence or page title. Let's see if any other part matches the domain token.
    words = first_part.split()
    if len(words) > 4:
        domain_token = _domain_token(url).lower()
        for p in parts:
            p_clean = p.strip()
            if domain_token in p_clean.lower().replace(" ", "").replace("-", ""):
                p_clean = re.sub(r"\b(official|website|homepage|home)\b", "", p_clean, flags=re.I)
                p_clean = p_clean.encode("ascii", "ignore").decode("ascii")
                p_clean = re.sub(r"\s+", " ", p_clean).strip(" .,-|")
                if len(p_clean.split()) <= 4:
                    return p_clean
        return domain_name

    if len(first_part) < 3 or len(first_part) > 50 or first_part.lower() in {"co", "company", "corporation"}:
        return domain_name
    return first_part


def discover_and_save_icp_companies(db: Session, replace: bool = False) -> dict:
    if replace:
        clear_pipeline_data(db)

    from services.icp_loader import load_icp

    icp = load_icp()
    industry = icp.get("industry", "")
    raw_results = discover_companies()
    if isinstance(raw_results, dict) and raw_results.get("error"):
        return {
            "message": "ICP discovery failed.",
            "error": raw_results["error"],
            "imported": 0,
            "skipped": 0,
            "total_processed": 0,
        }

    imported = 0
    skipped = 0
    seen_domains: set[str] = set()
    seen_names: set[str] = set()
    saved = []

    for result in raw_results:
        root = _root_url(result.get("url"))
        if not root or _is_noise_domain(root):
            skipped += 1
            continue
        if _is_bad_title(result.get("title")):
            skipped += 1
            continue
        if not _looks_like_official_company_site(root, result.get("title"), industry):
            skipped += 1
            continue
        time.sleep(0.5)

        domain = urlparse(root).netloc.lower().removeprefix("www.")
        if domain in seen_domains:
            skipped += 1
            continue
        seen_domains.add(domain)

        company_name = _company_name_from_title(result.get("title"), root)
        if not _is_valid_company_name(company_name):
            skipped += 1
            continue
        name_key = company_name.casefold()
        if name_key in seen_names:
            skipped += 1
            continue
        seen_names.add(name_key)

        existing = (
            db.query(Company)
            .filter(Company.company_name == company_name)
            .first()
        )
        if existing:
            skipped += 1
            continue

        company = Company(
            company_name=company_name,
            founder=None,
            founded=str(icp.get("founding_year")) if icp.get("founding_year") else None,
            source=f"ICP search: {result.get('query')}",
            website=root,
            confidence_score=0.0,
            industry=industry,
            country=icp.get("country"),
            employee_count=icp.get("employee_min"),
        )
        db.add(company)
        imported += 1
        saved.append({"company_name": company_name, "website": root})

    db.commit()

    return {
        "message": "ICP company discovery complete.",
        "imported": imported,
        "skipped": skipped,
        "total_processed": len(raw_results),
        "replaced": replace,
        "results": saved,
    }

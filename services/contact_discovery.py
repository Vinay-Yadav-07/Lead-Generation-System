import logging
import re
import time
from urllib.parse import urlparse

from ddgs import DDGS

from scrapers.company_scraper import (
    extract_emails,
    extract_phone_numbers,
    scrape_company_pages,
)

logger = logging.getLogger(__name__)

FOUNDER_TITLES = (
    "Founder",
    "Co-Founder",
    "CEO",
    "Chief Executive Officer",
    "Managing Director",
    "Owner",
    "President",
)

COMMON_EMAIL_PATTERNS = (
    "{first}@{domain}",
    "{first}.{last}@{domain}",
    "{first}{last}@{domain}",
    "{first_initial}{last}@{domain}",
)

PERSON_ROLE_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*(?:,|-|\(|\s)+"
    r"\b(Founder|Co-Founder|CEO|Chief\s+Executive\s+Officer|Managing\s+Director|Owner|President|founder|co-founder|ceo|chief\s+executive\s+officer|managing\s+director|owner|president|CEO|CO-FOUNDER|MANAGING\s+DIRECTOR|OWNER|PRESIDENT)\b"
)

ROLE_PERSON_RE = re.compile(
    r"\b(Founder|Co-Founder|CEO|Chief\s+Executive\s+Officer|Managing\s+Director|Owner|President|founder|co-founder|ceo|chief\s+executive\s+officer|managing\s+director|owner|president|CEO|CO-FOUNDER|MANAGING\s+DIRECTOR|OWNER|PRESIDENT)\b"
    r"\s*(?:,|-|:|\))?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
)


def is_plausible_human_name(name: str | None) -> bool:
    if not name:
        return False
    name = name.strip()
    words = name.split()
    if len(words) < 2 or len(words) > 4:
        return False
    
    stop_words = {
        "or", "and", "of", "the", "a", "an", "in", "on", "at", "for", "to", "by", "with", "about", "from",
        "as", "is", "are", "was", "were", "be", "been", "have", "has", "had", "not", "but", "this", "that",
        "these", "those", "who", "which", "what", "where", "when", "why", "how", "all", "any", "both",
        "each", "few", "more", "most", "other", "some", "such", "no", "nor", "too", "very", "can", "will",
        "just", "should", "would", "could", "them", "their", "they", "we", "our", "us", "you", "your",
        "he", "him", "his", "she", "her", "it", "its", "i", "me", "my", "part", "new", "old", "good", "bad",
        "all", "out", "over", "under", "again", "then", "once", "here", "there"
    }
    
    for word in words:
        if word.lower() in stop_words:
            return False
            
    for word in words:
        cleaned_word = word.strip(".,;:()[]{}")
        if not cleaned_word:
            return False
        if not cleaned_word[0].isupper():
            return False
            
    return True


def clean_person_name(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip(" ,;|")
    if not value:
        return None
    # Inc42 sometimes returns multiple founders; use the first decision-maker
    # so the Lead table still has one person per row.
    value = re.split(r"\s+(?:and|&)\s+|,\s*", value, maxsplit=1)[0].strip()
    return value or None


def infer_job_title(founder_name: str | None) -> str:
    if founder_name:
        return "Founder"
    return "Founder / CEO"


def domain_from_website(website: str | None) -> str | None:
    if not website:
        return None
    parsed = urlparse(website if "://" in website else f"https://{website}")
    domain = parsed.netloc.lower().removeprefix("www.")
    return domain or None


def infer_email_candidates(full_name: str | None, website: str | None) -> list[str]:
    if not full_name or not website:
        return []

    domain = domain_from_website(website)
    if not domain:
        return []

    parts = re.findall(r"[a-zA-Z]+", full_name.lower())
    if not parts:
        return []

    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ""
    values = {
        "first": first,
        "last": last,
        "first_initial": first[:1],
        "domain": domain,
    }

    candidates = []
    for pattern in COMMON_EMAIL_PATTERNS:
        if "{last}" in pattern and not last:
            continue
        candidates.append(pattern.format(**values))
    return list(dict.fromkeys(candidates))


def discover_linkedin_profile(full_name: str | None, company_name: str) -> str | None:
    if not full_name:
        return None

    query = f'site:linkedin.com/in "{full_name}" "{company_name}" founder OR CEO'
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
    except Exception as exc:
        logger.warning("[contact_discovery] LinkedIn search failed for %s: %s", full_name, exc)
        return None

    for result in results:
        href = result.get("href", "")
        if "linkedin.com/in/" in href:
            return href.split("?")[0]
    return None


def extract_founder_from_text(text: str) -> tuple[str | None, str | None]:
    if not text:
        return None, None

    for match in PERSON_ROLE_RE.finditer(text):
        name = clean_person_name(match.group(1))
        role = match.group(2).strip()
        if name and not any(word.lower() in name.lower() for word in ("privacy policy", "terms conditions")):
            return name, role

    for match in ROLE_PERSON_RE.finditer(text):
        role = match.group(1).strip()
        name = clean_person_name(match.group(2))
        if name and not any(word.lower() in name.lower() for word in ("privacy policy", "terms conditions")):
            return name, role

    return None, None


def scrape_public_contacts(website: str | None) -> dict:
    if not website:
        return {"emails": [], "phones": [], "source": None, "text": ""}

    try:
        text = scrape_company_pages(website)
    except Exception as exc:
        logger.warning("[contact_discovery] Website scrape failed for %s: %s", website, exc)
        return {"emails": [], "phones": [], "source": website, "text": ""}

    return {
        "emails": extract_emails(text),
        "phones": extract_phone_numbers(text),
        "source": website,
        "text": text,
    }


def discover_crunchbase(company_name: str) -> str | None:
    query = f'site:crunchbase.com/organization "{company_name}"'
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for r in results:
                href = r.get("href", "")
                if "crunchbase.com/organization/" in href:
                    return href
    except Exception:
        pass
    return None


def discover_twitter(company_name: str) -> str | None:
    query = f'site:twitter.com OR site:x.com "{company_name}"'
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for r in results:
                href = r.get("href", "")
                if "twitter.com/" in href or "x.com/" in href:
                    if not any(x in href for x in ("/status/", "/hashtag/", "/search")):
                        return href
    except Exception:
        pass
    return None


def discover_press_release(company_name: str) -> str | None:
    query = f'"{company_name}" press release OR news'
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                return f"{results[0].get('title')}: {results[0].get('href')}"
    except Exception:
        pass
    return None


def discover_whois(website: str | None) -> str | None:
    if not website:
        return None
    try:
        domain = domain_from_website(website)
        if not domain:
            return None
        import socket
        ip = socket.gethostbyname(domain)
        return f"Domain: {domain} | Resolved IP: {ip} | Status: Active"
    except Exception as e:
        return f"Domain: {website} | Resolution failed: {str(e)}"


def build_lead_payload(company) -> tuple[dict, list[dict]]:
    from datetime import datetime

    founder_name = clean_person_name(company.founder)
    contacts = scrape_public_contacts(company.website)
    time.sleep(1)

    discovered_name = None
    discovered_role = None
    if not founder_name:
        discovered_name, discovered_role = extract_founder_from_text(contacts.get("text", ""))
        founder_name = discovered_name

    # Enforce strict human name validation
    is_human = is_plausible_human_name(founder_name)
    
    # Check if we should fallback to a company-level contact
    is_company_fallback = False
    if not is_human:
        # Perform one additional pass: explicitly crawl About, Team, Leadership, and Management pages
        from bs4 import BeautifulSoup
        import requests
        additional_pages = ["/about", "/about-us", "/team", "/leadership", "/management"]
        found_additional = False
        
        for path in additional_pages:
            try:
                url = company.website.rstrip("/") + path
                res = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    text = soup.get_text(" ", strip=True)
                    add_name, add_role = extract_founder_from_text(text)
                    if add_name and is_plausible_human_name(add_name):
                        invalid_words = {"company", "services", "solutions", "limited", "pvt", "ltd", "corp", "inc", "hvac", "engineering", "controls", "enterprises", "technologies"}
                        if not any(kw in add_name.lower() for kw in invalid_words):
                            founder_name = add_name
                            discovered_role = add_role
                            is_human = True
                            found_additional = True
                            break
            except Exception:
                pass
                
        if not found_additional:
            # Check if we have any valid contact information (email or phone)
            emails = contacts.get("emails", [])
            phones = contacts.get("phones", [])
            if emails or phones:
                founder_name = "Business Contact"
                discovered_role = "Business Contact"
                is_company_fallback = True
            else:
                # No contact info and no human founder -> cannot build a usable lead
                return {}, []

    # If it's not a company fallback, we also exclude names containing corporate keywords
    if not is_company_fallback:
        invalid_name_keywords = {
            "company", "services", "solutions", "limited", "pvt", "ltd", "corp", "inc", "hvac", "engineering",
            "contractor", "contractors", "consultant", "consultants", "support", "admin", "info", "sales",
            "careers", "jobs", "office", "team", "board", "management", "leadership", "customer", "client",
            "partner", "system", "systems", "department", "division", "agency", "group", "association",
            "institute", "organization", "university", "college", "school", "magazine", "journal", "press",
            "news", "newswire", "blog", "website", "domain", "page", "site", "online", "internet", "web",
            "controls", "enterprises", "technologies"
        }
        if any(keyword in founder_name.lower() for keyword in invalid_name_keywords):
            # Attempt the same additional pass if we hit a corporate keyword name collision
            from bs4 import BeautifulSoup
            import requests
            additional_pages = ["/about", "/about-us", "/team", "/leadership", "/management"]
            found_additional = False
            for path in additional_pages:
                try:
                    url = company.website.rstrip("/") + path
                    res = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, "html.parser")
                        text = soup.get_text(" ", strip=True)
                        add_name, add_role = extract_founder_from_text(text)
                        if add_name and is_plausible_human_name(add_name):
                            invalid_words = {"company", "services", "solutions", "limited", "pvt", "ltd", "corp", "inc", "hvac", "engineering", "controls", "enterprises", "technologies"}
                            if not any(kw in add_name.lower() for kw in invalid_words):
                                founder_name = add_name
                                discovered_role = add_role
                                found_additional = True
                                break
                except Exception:
                    pass
            
            if not found_additional:
                emails = contacts.get("emails", [])
                phones = contacts.get("phones", [])
                if emails or phones:
                    founder_name = "Business Contact"
                    discovered_role = "Business Contact"
                    is_company_fallback = True
                else:
                    return {}, []

    emails = contacts.get("emails", [])
    phones = contacts.get("phones", [])
    inferred_emails = infer_email_candidates(founder_name, company.website) if not is_company_fallback else []
    linkedin_url = discover_linkedin_profile(founder_name, company.company_name) if not is_company_fallback else None

    selected_email = emails[0] if emails else (inferred_emails[0] if inferred_emails else None)
    selected_phone = phones[0] if phones else None

    # Extra discovery sources
    crunchbase_url = None
    twitter_url = None
    press_release = None
    whois_info = None
    if not is_company_fallback:
        crunchbase_url = discover_crunchbase(company.company_name)
        time.sleep(0.5)
        twitter_url = discover_twitter(company.company_name)
        time.sleep(0.5)
        press_release = discover_press_release(company.company_name)
        time.sleep(0.5)
    whois_info = discover_whois(company.website)

    founding_year = None
    if company.founded:
        try:
            founding_year = int(company.founded.strip())
        except ValueError:
            pass

    lead = {
        "full_name": founder_name,
        "job_title": discovered_role or infer_job_title(founder_name),
        "company_name": company.company_name,
        "company_website": company.website,
        "linkedin_url": linkedin_url or company.linkedin_url,
        "email": selected_email,
        "email_status": "Found - Unverified" if emails else ("Inferred - Unverified" if selected_email else "Missing"),
        "email_source": "FOUND" if emails else ("INFERRED" if selected_email else None),
        "phone": selected_phone,
        "phone_status": "Found - Unverified" if selected_phone else "Missing",
        "phone_source": "FOUND" if selected_phone else None,
        "phone_verified": False,
        "line_type": None,
        "industry": company.industry,
        "employee_count": company.employee_count,
        "founding_year": founding_year,
        "source_url": company.source,
        "scraped_date": datetime.utcnow(),
        "role_verified": not is_company_fallback,
        "source": "Company DB enrichment",
        "status": "New",
    }

    evidence = [
        {"field_name": "full_name", "field_value": lead["full_name"], "source": company.source or "company_import"},
        {"field_name": "company_website", "field_value": company.website, "source": "website_discovery"},
    ]
    if discovered_name and not is_company_fallback:
        evidence.append({"field_name": "founder", "field_value": discovered_name, "source": contacts["source"]})
    if lead["linkedin_url"]:
        evidence.append({"field_name": "linkedin_url", "field_value": lead["linkedin_url"], "source": "DuckDuckGo public LinkedIn search"})
    if selected_email:
        evidence.append({"field_name": "email", "field_value": selected_email, "source": contacts["source"] if emails else "pattern_inference"})
    if selected_phone:
        evidence.append({"field_name": "phone", "field_value": selected_phone, "source": contacts["source"]})
    if crunchbase_url:
        evidence.append({"field_name": "crunchbase_url", "field_value": crunchbase_url, "source": "DuckDuckGo Crunchbase Search"})
    if twitter_url:
        evidence.append({"field_name": "twitter_url", "field_value": twitter_url, "source": "DuckDuckGo Twitter/X Search"})
    if press_release:
        evidence.append({"field_name": "press_release", "field_value": press_release, "source": "DuckDuckGo Press Release Search"})
    if whois_info:
        evidence.append({"field_name": "whois_info", "field_value": whois_info, "source": "WHOIS lookup"})

    return lead, [item for item in evidence if item.get("field_value")]

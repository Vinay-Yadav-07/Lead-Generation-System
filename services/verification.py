import re
import socket
import os

import requests

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?\d[\d\s().-]{8,}\d$")


def _domain_has_dns(domain: str) -> bool:
    try:
        socket.getaddrinfo(domain, None)
        return True
    except OSError:
        return False


def verify_email(email: str | None) -> tuple[str, bool]:
    """
    Returns (status_string, email_verified_bool).
    status_string values: Missing, Invalid Format, Deliverable Verified,
                          Undeliverable, Format + Domain Verified, Format Valid - Domain Unverified
    """
    if not email:
        return "Missing", False
    if not EMAIL_RE.match(email):
        return "Invalid Format", False

    abstract_key = os.getenv("ABSTRACT_EMAIL_API_KEY")
    if abstract_key:
        try:
            response = requests.get(
                "https://emailvalidation.abstractapi.com/v1/",
                params={"api_key": abstract_key, "email": email},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            deliverability = data.get("deliverability")
            quality_score = data.get("quality_score")
            if deliverability == "DELIVERABLE":
                return f"Deliverable Verified ({quality_score})", True
            if deliverability == "UNDELIVERABLE":
                return f"Undeliverable ({quality_score})", False
            if deliverability:
                return f"Verification Unknown ({deliverability})", False
        except Exception:
            pass

    hunter_key = os.getenv("HUNTER_API_KEY")
    if hunter_key:
        try:
            response = requests.get(
                "https://api.hunter.io/v2/email-verifier",
                params={"email": email, "api_key": hunter_key},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            status = data.get("status")
            score = data.get("score")
            if status == "valid":
                return f"Deliverable Verified ({score})", True
            if status == "invalid":
                return f"Undeliverable ({score})", False
            return f"Verification Unknown ({status or 'no status'})", False
        except Exception:
            pass

    domain = email.rsplit("@", 1)[1].lower()
    if _domain_has_dns(domain):
        return "Format + Domain Verified", False
    return "Format Valid - Domain Unverified", False


def verify_phone(phone: str | None) -> tuple[str, bool, str | None]:
    """
    Returns (status_string, phone_verified_bool, line_type_or_None).
    """
    if not phone:
        return "Missing", False, None

    # Try libphonenumber first (installed as phonenumbers package)
    try:
        import phonenumbers
        parsed = phonenumbers.parse(phone, None)
        if phonenumbers.is_valid_number(parsed):
            numverify_key = os.getenv("NUMVERIFY_API_KEY")
            if numverify_key:
                try:
                    response = requests.get(
                        "http://apilayer.net/api/validate",
                        params={
                            "access_key": numverify_key,
                            "number": phone,
                        },
                        timeout=20,
                    )
                    response.raise_for_status()
                    data = response.json()
                    if data.get("valid") is True:
                        lt = data.get("line_type") or "active"
                        return f"Active {lt.title()}", True, lt
                    if data.get("valid") is False:
                        return "Inactive or Invalid", False, None
                except Exception:
                    pass
            return "Format Verified", True, None
        else:
            return "Invalid Format", False, None
    except Exception:
        pass

    # Fallback: regex
    if PHONE_RE.match(phone.strip()):
        numverify_key = os.getenv("NUMVERIFY_API_KEY")
        if numverify_key:
            try:
                response = requests.get(
                    "http://apilayer.net/api/validate",
                    params={
                        "access_key": numverify_key,
                        "number": phone,
                    },
                    timeout=20,
                )
                response.raise_for_status()
                data = response.json()
                if data.get("valid") is True:
                    lt = data.get("line_type") or "active"
                    return f"Active {lt.title()}", True, lt
                if data.get("valid") is False:
                    return "Inactive or Invalid", False, None
            except Exception:
                pass
        return "Format Verified", True, None
    return "Invalid Format", False, None


def verify_role(lead) -> bool:
    name = (lead.full_name or "").strip()
    title = (lead.job_title or "").lower()

    if not name:
        return False

    from services.contact_discovery import is_plausible_human_name
    if not is_plausible_human_name(name):
        return False

    # Exclude names containing corporate keywords
    invalid_name_keywords = {
        "company", "services", "solutions", "limited", "pvt", "ltd", "corp", "inc", "hvac", "engineering",
        "contractor", "contractors", "consultant", "consultants", "support", "admin", "info", "sales",
        "careers", "jobs", "office", "team", "board", "management", "leadership", "customer", "client",
        "partner", "system", "systems", "department", "division", "agency", "group", "association",
        "org", "organization", "magazine", "journal", "news", "blog", "site", "web",
        "controls", "enterprises", "technologies"
    }
    if any(keyword in name.lower() for keyword in invalid_name_keywords):
        return False

    decision_maker_roles = {"founder", "ceo", "owner", "director", "president", "partner", "chief executive"}
    return any(role in title for role in decision_maker_roles)


def confidence_level(score: int) -> str:
    """Return uppercase confidence level: HIGH (8-10) / MEDIUM (5-7) / LOW (0-4)"""
    if score >= 8:
        return "HIGH"
    if score >= 5:
        return "MEDIUM"
    return "LOW"


def score_lead(lead) -> int:
    is_decision_maker = getattr(lead, "role_verified", False)
    has_verified_email = getattr(lead, "email_verified", False)
    has_verified_phone = getattr(lead, "phone_verified", False)

    # 10 = Decision maker + verified email + verified phone
    if is_decision_maker and has_verified_email and has_verified_phone:
        return 10

    # 8 = Decision maker + verified email
    if is_decision_maker and has_verified_email:
        return 8

    # 6 = Decision maker only
    if is_decision_maker:
        return 6

    # 4 = Generic business contact
    if lead.full_name and (lead.email or lead.phone):
        return 4

    # 2 = Website only
    if lead.company_website:
        return 2

    return 0


def verify_lead(lead):
    email_status, email_verified = verify_email(lead.email)
    phone_status, phone_verified, line_type = verify_phone(lead.phone)

    lead.email_status = email_status
    lead.email_verified = email_verified
    if email_verified:
        lead.email_source = "VERIFIED"

    lead.phone_status = phone_status
    lead.phone_verified = phone_verified
    lead.line_type = line_type
    if phone_verified:
        lead.phone_source = "VERIFIED"

    lead.role_verified = verify_role(lead)
    lead.confidence_score = score_lead(lead)
    lead.confidence_level = confidence_level(lead.confidence_score)
    return lead

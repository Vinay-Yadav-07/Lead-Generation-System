import csv
import io
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.db import engine, Base
from database.session import get_db

from models.lead import Lead
from models.evidence import Evidence
from models.company import Company
from models.outreach import OutreachLog

from schemas.lead_schema import LeadCreate, LeadStatusUpdate, LeadResponse
from schemas.icp_schema import ICPConfig

from scrapers.company_scraper import (
    scrape_page,
    extract_emails,
    discover_company_pages,
    scrape_company_pages,
)

from services.company_discovery import discover_companies
from services.company_parser import filter_companies
from services.tracxn_scraper import scrape_page as tracxn_scrape_page
from services.inc42_parser import extract_companies
from services.company_importer import save_companies
from services.website_discovery import discover_website
from services.confidence_scorer import calculate_score
from services.contact_discovery import build_lead_payload
from services.verification import verify_lead
from services.email_writer import generate_cold_email
from services.icp_loader import load_icp
from services.outreach import send_email_or_simulate
from services.icp_company_pipeline import discover_and_save_icp_companies

load_dotenv()

# Ensure all tables exist
Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ICP_PATH = BASE_DIR / "config" / "icp.json"


# ---------------------------------------------------------------------------
# Lightweight SQLite migration for columns added after initial DB creation
# ---------------------------------------------------------------------------

def ensure_sqlite_columns():
    """
    SQLite ALTER TABLE for new columns that may not exist in an existing DB.
    """
    with engine.begin() as conn:
        # --- leads table ---
        existing_leads = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(leads)")).fetchall()
        }
        lead_additions = {
            "confidence_level": "VARCHAR",
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
            "email_verified": "BOOLEAN DEFAULT 0",
            "email_source": "VARCHAR",
            "phone_verified": "BOOLEAN DEFAULT 0",
            "phone_source": "VARCHAR",
            "line_type": "VARCHAR",
            "employee_count": "INTEGER",
            "founding_year": "INTEGER",
            "source_url": "VARCHAR",
            "scraped_date": "DATETIME",
        }
        for column, col_type in lead_additions.items():
            if column not in existing_leads:
                conn.execute(text(f"ALTER TABLE leads ADD COLUMN {column} {col_type}"))

        # --- companies table ---
        existing_companies = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(companies)")).fetchall()
        }
        company_additions = {
            "industry": "VARCHAR",
            "employee_count": "INTEGER",
            "country": "VARCHAR",
            "linkedin_url": "VARCHAR",
        }
        for column, col_type in company_additions.items():
            if column not in existing_companies:
                conn.execute(text(f"ALTER TABLE companies ADD COLUMN {column} {col_type}"))


ensure_sqlite_columns()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(title="AutoNova Lead Generation System")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

DIST_DIR = BASE_DIR / "frontend" / "dist"
ASSETS_DIR = DIST_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def serialize_lead(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "full_name": lead.full_name,
        "job_title": lead.job_title,
        "company_name": lead.company_name,
        "company_website": lead.company_website,
        "linkedin_url": lead.linkedin_url,

        "email": lead.email,
        "email_status": lead.email_status,
        "email_verified": lead.email_verified,
        "email_source": lead.email_source,

        "phone": lead.phone,
        "phone_status": lead.phone_status,
        "phone_verified": lead.phone_verified,
        "phone_source": lead.phone_source,
        "line_type": lead.line_type,

        "industry": lead.industry,
        "employee_count": lead.employee_count,
        "founding_year": lead.founding_year,

        "source_url": lead.source_url,
        "scraped_date": lead.scraped_date.isoformat() if lead.scraped_date else None,

        "confidence_score": lead.confidence_score,
        "confidence_level": lead.confidence_level,
        "role_verified": lead.role_verified,

        "source": lead.source,
        "status": lead.status,

        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


def serialize_outreach_log(log: OutreachLog) -> dict:
    return {
        "id": log.id,
        "lead_id": log.lead_id,
        "channel": log.channel,
        "subject": log.subject,
        "body": log.body,
        "status": log.status,
        "provider_message": log.provider_message,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def save_evidence_items(db: Session, lead_id: int, evidence_items: list[dict]) -> None:
    for item in evidence_items:
        db.add(
            Evidence(
                lead_id=lead_id,
                source=item.get("source"),
                field_name=item.get("field_name"),
                field_value=item.get("field_value"),
            )
        )


# ---------------------------------------------------------------------------
# Root / health
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    dist_index = DIST_DIR / "index.html"
    if dist_index.exists():
        return FileResponse(dist_index)
    dashboard = STATIC_DIR / "index.html"
    if dashboard.exists():
        return FileResponse(dashboard)
    return {"message": "AutoNova Lead Generation API Running"}


@app.get("/api/health")
def health():
    return {"status": "ok", "message": "AutoNova Lead Generation API Running"}


@app.get("/api/integrations/status")
def integrations_status():
    return {
        "smtp": bool(
            os.getenv("SMTP_HOST")
            and os.getenv("SMTP_PORT")
            and os.getenv("SMTP_USERNAME")
            and os.getenv("SMTP_PASSWORD")
            and os.getenv("SMTP_FROM_EMAIL")
        ),
        "email_verification": bool(
            os.getenv("HUNTER_API_KEY") or os.getenv("ABSTRACT_EMAIL_API_KEY")
        ),
        "phone_verification": bool(os.getenv("NUMVERIFY_API_KEY")),
    }


@app.get("/integrations/status")
def integrations_status_legacy():
    return integrations_status()


# ---------------------------------------------------------------------------
# /api/leads — correct prefix, filters, search
# ---------------------------------------------------------------------------

@app.get("/api/leads")
def api_get_leads(
    industry: str = Query(None),
    country: str = Query(None),
    status: str = Query(None),
    confidence: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    GET /api/leads — with optional filters:
      ?industry=  ?country=  ?status=  ?confidence=HIGH|MEDIUM|LOW  ?search=
    """
    q = db.query(Lead)

    if industry and isinstance(industry, str):
        q = q.filter(Lead.industry.ilike(f"%{industry}%"))
    if country and isinstance(country, str):
        q = q.join(Company, Company.company_name == Lead.company_name).filter(Company.country.ilike(f"%{country}%"))
    if status and isinstance(status, str):
        q = q.filter(Lead.status == status)
    if confidence and isinstance(confidence, str):
        q = q.filter(Lead.confidence_level == confidence.upper())
    if search and isinstance(search, str):
        term = f"%{search}%"
        q = q.filter(
            Lead.full_name.ilike(term)
            | Lead.company_name.ilike(term)
            | Lead.email.ilike(term)
        )

    leads = q.order_by(Lead.confidence_score.desc(), Lead.id.asc()).all()
    return [serialize_lead(lead) for lead in leads]


@app.get("/api/leads/{lead_id}")
def api_get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    evidence = db.query(Evidence).filter(Evidence.lead_id == lead_id).all()
    outreach = (
        db.query(OutreachLog)
        .filter(OutreachLog.lead_id == lead_id)
        .order_by(OutreachLog.created_at.desc())
        .all()
    )
    return {
        "lead": serialize_lead(lead),
        "evidence": [
            {
                "id": e.id,
                "source": e.source,
                "field_name": e.field_name,
                "field_value": e.field_value,
            }
            for e in evidence
        ],
        "audit_trail": [serialize_outreach_log(log) for log in outreach],
    }


@app.put("/api/leads/{lead_id}/status")
def api_update_lead_status(
    lead_id: int,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
):
    allowed_statuses = {
        "New",
        "Reviewed",
        "Approved for Outreach",
        "Do Not Contact",
        "Contacted",
        "Replied",
    }
    if payload.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Allowed: {', '.join(sorted(allowed_statuses))}",
        )

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.status = payload.status
    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return {
        "message": "Status updated",
        "lead": serialize_lead(lead),
    }


# ---------------------------------------------------------------------------
# /api/icp
# ---------------------------------------------------------------------------

@app.get("/api/icp")
def api_get_icp():
    return load_icp()


@app.post("/api/icp")
def api_update_icp(payload: ICPConfig):
    ICP_PATH.parent.mkdir(parents=True, exist_ok=True)
    ICP_PATH.write_text(
        json.dumps(payload.model_dump(), indent=2),
        encoding="utf-8",
    )
    return {
        "message": "ICP config updated.",
        "icp": payload.model_dump(),
    }


# ---------------------------------------------------------------------------
# /api/pipeline-status — NEW endpoint (was completely missing)
# ---------------------------------------------------------------------------

@app.get("/api/pipeline-status")
def api_pipeline_status(db: Session = Depends(get_db)):
    """
    Returns per-stage counts for the pipeline dashboard page.
    Stages: Discovered → Websites Found → Leads Generated → Verified → High Confidence → Approved
    """
    raw_companies = db.query(Company).all()
    raw_leads = db.query(Lead).all()

    placeholders = {"contact", "placeholder", "customer", "support", "sales", "info", "admin", "office", "team", "manager", "article", "blog", "careers", "jobs", "home"}

    companies = [
        c for c in raw_companies
        if c.company_name and not any(p in c.company_name.lower() for p in placeholders)
    ]
    leads = [
        l for l in raw_leads
        if l.full_name and (l.full_name == "Business Contact" or not any(p in l.full_name.lower() for p in placeholders))
    ]

    discovered = len(companies)
    with_website = sum(1 for c in companies if c.website)

    total_leads = len(leads)
    verified_leads = sum(1 for l in leads if l.email_verified or l.phone_verified)
    leads_scored = sum(1 for l in leads if l.confidence_score is not None and l.confidence_score > 0)
    outreach = sum(1 for l in leads if l.status in ("Contacted", "Replied"))

    return {
        "stages": [
            {"name": "Discover Companies", "count": discovered, "icon": "database"},
            {"name": "Review Companies", "count": discovered, "icon": "star"},
            {"name": "Discover Websites", "count": with_website, "icon": "globe"},
            {"name": "Generate Leads", "count": total_leads, "icon": "users"},
            {"name": "Verify Leads", "count": verified_leads, "icon": "badge-check"},
            {"name": "Score Leads", "count": leads_scored, "icon": "thumbs-up"},
            {"name": "Outreach", "count": outreach, "icon": "send"},
        ],
        "summary": {
            "total_companies": discovered,
            "total_leads": total_leads,
            "verified": verified_leads,
            "scored": leads_scored,
            "outreach": outreach,
        },
    }


# ---------------------------------------------------------------------------
# /api/export
# ---------------------------------------------------------------------------

@app.get("/api/export/csv")
def api_export_csv(db: Session = Depends(get_db)):
    leads = [serialize_lead(lead) for lead in db.query(Lead).all()]
    output = io.StringIO()
    fieldnames = list(leads[0].keys()) if leads else list(serialize_lead(Lead()).keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(leads)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=autonova_leads.csv"},
    )


@app.get("/api/export/json")
def api_export_json(db: Session = Depends(get_db)):
    return [serialize_lead(lead) for lead in db.query(Lead).all()]


# ---------------------------------------------------------------------------
# /api/stats — dashboard overview cards
# ---------------------------------------------------------------------------

@app.get("/api/stats")
def api_stats(db: Session = Depends(get_db)):
    raw_leads = db.query(Lead).all()
    raw_companies = db.query(Company).all()
    outreach = db.query(OutreachLog).all()

    placeholders = {"contact", "placeholder", "customer", "support", "sales", "info", "admin", "office", "team", "manager", "article", "blog", "careers", "jobs", "home"}

    leads = [
        l for l in raw_leads
        if l.full_name and (l.full_name == "Business Contact" or not any(p in l.full_name.lower() for p in placeholders))
    ]
    companies = [
        c for c in raw_companies
        if c.company_name and not any(p in c.company_name.lower() for p in placeholders)
    ]

    total_leads = len(leads)
    verified_leads = sum(1 for l in leads if l.email_verified or l.phone_verified)
    high_confidence = sum(1 for l in leads if l.confidence_level == "HIGH")
    approved = sum(1 for l in leads if l.status == "Approved for Outreach")

    by_status = {}
    by_confidence = {}
    for lead in leads:
        by_status[lead.status or "Unknown"] = by_status.get(lead.status or "Unknown", 0) + 1
        by_confidence[lead.confidence_level or "Unscored"] = (
            by_confidence.get(lead.confidence_level or "Unscored", 0) + 1
        )

    return {
        "overview": {
            "total_leads": total_leads,
            "verified_leads": verified_leads,
            "high_confidence": high_confidence,
            "approved_for_outreach": approved,
        },
        "companies": {
            "total": len(companies),
            "with_website": sum(1 for c in companies if c.website),
            "with_founder": sum(1 for c in companies if c.founder),
        },
        "leads": {
            "total": total_leads,
            "with_email": sum(1 for lead in leads if lead.email),
            "with_phone": sum(1 for lead in leads if lead.phone),
            "email_verified": sum(1 for lead in leads if lead.email_verified),
            "phone_verified": sum(1 for lead in leads if lead.phone_verified),
            "role_verified": sum(1 for lead in leads if lead.role_verified),
            "by_status": by_status,
            "by_confidence": by_confidence,
        },
        "outreach": {
            "total": len(outreach),
            "sent": sum(1 for item in outreach if item.status == "Sent"),
            "simulated": sum(1 for item in outreach if item.status == "Simulated"),
            "drafted": sum(1 for item in outreach if item.status == "Drafted"),
            "failed": sum(1 for item in outreach if item.status == "Failed"),
        },
    }


# ---------------------------------------------------------------------------
# Legacy backward-compat aliases (old paths still work)
# ---------------------------------------------------------------------------

@app.get("/legacy-leads")
def get_leads_legacy(
    industry: str = Query(None),
    country: str = Query(None),
    status: str = Query(None),
    confidence: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    return api_get_leads(
        industry=industry,
        country=country,
        status=status,
        confidence=confidence,
        search=search,
        db=db,
    )


@app.get("/lead/{lead_id}")
def get_lead_legacy(lead_id: int, db: Session = Depends(get_db)):
    return api_get_lead(lead_id=lead_id, db=db)


@app.patch("/lead/{lead_id}/status")
def update_lead_status_legacy(
    lead_id: int,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
):
    return api_update_lead_status(lead_id=lead_id, payload=payload, db=db)


@app.get("/icp")
def get_icp_legacy():
    return api_get_icp()


@app.put("/icp")
def update_icp_legacy(payload: ICPConfig):
    return api_update_icp(payload)


@app.get("/export/csv")
def export_csv_legacy(db: Session = Depends(get_db)):
    return api_export_csv(db=db)


@app.get("/export/json")
def export_json_legacy(db: Session = Depends(get_db)):
    return api_export_json(db=db)


@app.get("/stats")
def stats_legacy(db: Session = Depends(get_db)):
    return api_stats(db=db)


# ---------------------------------------------------------------------------
# Company pipeline endpoints (preserved)
# ---------------------------------------------------------------------------

@app.post("/create-test-lead")
def create_test_lead(db: Session = Depends(get_db)):
    new_lead = Lead(
        full_name="John Doe",
        job_title="CEO",
        company_name="Acme Inc",
        email="john@acme.com",
        phone="+1234567890",
        confidence_score=8,
        source="Manual Test",
    )
    db.add(new_lead)
    db.commit()
    return {"message": "Lead created"}


@app.post("/add-lead")
def add_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    new_lead = Lead(
        full_name=lead.full_name,
        job_title=lead.job_title,
        company_name=lead.company_name,
        source="Manual Entry",
    )
    db.add(new_lead)
    db.commit()
    return {"message": "Lead added"}


@app.get("/scrape")
def test_scrape():
    data = scrape_page("https://openai.com")
    return {"content": data[:1000]}


@app.get("/emails")
def get_emails():
    text_content = scrape_page("https://openai.com")
    emails = extract_emails(text_content)
    return {"emails": emails}


@app.get("/discover-pages")
def discover_pages():
    pages = discover_company_pages("https://openai.com")
    return pages


@app.get("/scrape-company")
def scrape_company():
    content = scrape_company_pages("https://openai.com")
    return {"content": content[:3000]}


@app.get("/discover-companies")
def get_companies():
    return discover_companies()


@app.get("/legacy-companies")
def companies():
    results = discover_companies()
    filtered = filter_companies(results)
    return filtered


@app.post("/import-inc42")
def import_inc42(db: Session = Depends(get_db)):
    url = "https://inc42.com/lists/top-20-funded-logistics-startups-in-india-2026/"
    try:
        content = scrape_page(url)
    except Exception as exc:
        return {"error": f"Scrape failed: {exc}"}

    parsed_companies = extract_companies(content)

    if not parsed_companies:
        return {"message": "No companies parsed from Inc42 page.", "imported": 0, "skipped": 0}

    summary = save_companies(parsed_companies, db)
    return {"message": "Import complete.", **summary}


@app.post("/api/discover-companies-db")
def discover_companies_db(replace: bool = True, db: Session = Depends(get_db)):
    return discover_and_save_icp_companies(db, replace=replace)


@app.get("/api/companies-db")
def get_companies_db(db: Session = Depends(get_db)):
    companies_list = db.query(Company).all()
    return [
        {
            "id": c.id,
            "company_name": c.company_name,
            "founder": c.founder,
            "founded": c.founded,
            "source": c.source,
            "website": c.website,
            "confidence_score": c.confidence_score,
            "industry": c.industry,
            "employee_count": c.employee_count,
            "country": c.country,
            "linkedin_url": c.linkedin_url,
        }
        for c in companies_list
    ]


@app.post("/api/discover-websites")
def discover_websites_endpoint(db: Session = Depends(get_db)):
    companies_without_website = (
        db.query(Company)
        .filter((Company.website == None) | (Company.website == ""))  # noqa: E711
        .all()
    )

    if not companies_without_website:
        return {"message": "All companies already have websites.", "updated": 0}

    results = []
    updated = 0

    for company in companies_without_website:
        website = discover_website(company.company_name)
        try:
            company.website = website
            db.commit()
            db.refresh(company)
            updated += 1
            results.append({"company_name": company.company_name, "website": website, "status": "updated"})
        except Exception as exc:
            db.rollback()
            results.append({"company_name": company.company_name, "website": None, "status": f"error: {exc}"})

    return {"message": "Website discovery complete.", "updated": updated, "results": results}


@app.post("/api/generate-leads-from-companies")
def generate_leads_from_companies(limit: int = 30, db: Session = Depends(get_db)):
    companies_list = (
        db.query(Company)
        .order_by(Company.confidence_score.desc(), Company.id.asc())
        .limit(limit)
        .all()
    )
    created = 0
    updated = 0
    skipped = 0
    results = []

    for company in companies_list:
        if not company.company_name:
            skipped += 1
            continue

        lead_payload, evidence_items = build_lead_payload(company)
        if not lead_payload:
            skipped += 1
            continue

        existing = (
            db.query(Lead)
            .filter(
                Lead.full_name == lead_payload["full_name"],
                Lead.company_name == lead_payload["company_name"],
            )
            .first()
        )

        if existing:
            lead = existing
            updated += 1
        else:
            lead = Lead()
            created += 1

        for field, value in lead_payload.items():
            setattr(lead, field, value)

        verify_lead(lead)
        db.add(lead)
        db.commit()
        db.refresh(lead)
        save_evidence_items(db, lead.id, evidence_items)
        db.commit()

        results.append(serialize_lead(lead))

    return {
        "message": "Lead enrichment complete.",
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "limit": limit,
        "results": results,
    }


@app.post("/api/verify/{lead_id}")
def verify_lead_endpoint(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    verify_lead(lead)
    db.commit()
    db.refresh(lead)

    return {"message": "Verification complete.", "lead": serialize_lead(lead)}


@app.post("/api/verify-all")
def verify_all_leads(db: Session = Depends(get_db)):
    leads = db.query(Lead).all()
    for lead in leads:
        verify_lead(lead)
    db.commit()
    return {"message": "Verification complete.", "processed": len(leads)}


@app.post("/api/score-companies")
def score_companies(db: Session = Depends(get_db)):
    companies_list = db.query(Company).all()
    processed = 0
    updated = 0

    for company in companies_list:
        previous_score = company.confidence_score
        new_score = calculate_score(company)
        logger.info(
            "[score-companies] %-35s | prev: %4.1f → new: %4.1f",
            company.company_name,
            previous_score,
            new_score,
        )
        company.confidence_score = new_score
        processed += 1
        if new_score != previous_score:
            updated += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        return {"error": f"DB commit failed: {exc}"}

    return {"message": "Scoring complete.", "processed": processed, "updated": updated}


@app.get("/api/top-companies")
def top_companies(db: Session = Depends(get_db)):
    companies_list = (
        db.query(Company).order_by(Company.confidence_score.desc()).all()
    )
    return [
        {
            "id": c.id,
            "company_name": c.company_name,
            "founder": c.founder,
            "founded": c.founded,
            "source": c.source,
            "website": c.website,
            "confidence_score": c.confidence_score,
        }
        for c in companies_list
    ]


@app.get("/api/leads/{lead_id}/cold-email")
def cold_email(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return generate_cold_email(lead)


@app.post("/api/leads/{lead_id}/send-email")
def send_lead_email(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status in {"Contacted", "Do Not Contact"}:
        raise HTTPException(
            status_code=400,
            detail=f"Lead is already marked '{lead.status}'. Change status before sending again.",
        )

    draft = generate_cold_email(lead)
    try:
        result = send_email_or_simulate(
            to_email=lead.email,
            subject=draft["subject"],
            body=draft["body"],
        )
    except Exception as exc:
        result = {"status": "Failed", "provider_message": str(exc)}

    log = OutreachLog(
        lead_id=lead.id,
        channel="email",
        subject=draft["subject"],
        body=draft["body"],
        status=result["status"],
        provider_message=result["provider_message"],
    )
    db.add(log)

    if result["status"] in {"Sent", "Simulated"}:
        lead.status = "Contacted"

    db.commit()
    db.refresh(log)
    db.refresh(lead)

    return {
        "message": "Outreach processed.",
        "lead": serialize_lead(lead),
        "outreach": serialize_outreach_log(log),
    }


@app.post("/api/campaign/send-approved")
def send_approved_campaign(db: Session = Depends(get_db)):
    leads = (
        db.query(Lead).filter(Lead.status == "Approved for Outreach").all()
    )
    results = []

    for lead in leads:
        draft = generate_cold_email(lead)
        try:
            result = send_email_or_simulate(
                to_email=lead.email,
                subject=draft["subject"],
                body=draft["body"],
            )
        except Exception as exc:
            result = {"status": "Failed", "provider_message": str(exc)}

        log = OutreachLog(
            lead_id=lead.id,
            channel="email",
            subject=draft["subject"],
            body=draft["body"],
            status=result["status"],
            provider_message=result["provider_message"],
        )
        db.add(log)

        if result["status"] in {"Sent", "Simulated"}:
            lead.status = "Contacted"

        results.append(
            {
                "lead_id": lead.id,
                "lead_name": lead.full_name,
                "company_name": lead.company_name,
                **result,
            }
        )

    db.commit()
    return {"message": "Campaign processed.", "processed": len(results), "results": results}


@app.get("/api/outreach-logs")
def outreach_logs(db: Session = Depends(get_db)):
    logs = (
        db.query(OutreachLog)
        .order_by(OutreachLog.created_at.desc())
        .all()
    )
    return [serialize_outreach_log(log) for log in logs]


# ---------------------------------------------------------------------------
# Legacy compatibility wrappers
# ---------------------------------------------------------------------------

@app.post("/discover-companies-db")
def discover_companies_db_legacy(replace: bool = True, db: Session = Depends(get_db)):
    return discover_companies_db(replace=replace, db=db)


@app.get("/companies-db")
def get_companies_db_legacy(db: Session = Depends(get_db)):
    return get_companies_db(db=db)


@app.post("/discover-websites")
def discover_websites_legacy(db: Session = Depends(get_db)):
    return discover_websites_endpoint(db=db)


@app.post("/generate-leads-from-companies")
def generate_leads_from_companies_legacy(limit: int = 30, db: Session = Depends(get_db)):
    return generate_leads_from_companies(limit=limit, db=db)


@app.post("/verify/{lead_id}")
def verify_lead_legacy(lead_id: int, db: Session = Depends(get_db)):
    return verify_lead_endpoint(lead_id=lead_id, db=db)


@app.post("/verify-all")
def verify_all_leads_legacy(db: Session = Depends(get_db)):
    return verify_all_leads(db=db)


@app.post("/score-companies")
def score_companies_legacy(db: Session = Depends(get_db)):
    return score_companies(db=db)


@app.get("/top-companies")
def top_companies_legacy(db: Session = Depends(get_db)):
    return top_companies(db=db)


@app.get("/lead/{lead_id}/cold-email")
def cold_email_legacy(lead_id: int, db: Session = Depends(get_db)):
    return cold_email(lead_id=lead_id, db=db)


@app.post("/lead/{lead_id}/send-email")
def send_lead_email_legacy(lead_id: int, db: Session = Depends(get_db)):
    return send_lead_email(lead_id=lead_id, db=db)


@app.post("/campaign/send-approved")
def send_approved_campaign_legacy(db: Session = Depends(get_db)):
    return send_approved_campaign(db=db)


@app.get("/outreach-logs")
def outreach_logs_legacy(db: Session = Depends(get_db)):
    return outreach_logs(db=db)


@app.get("/{path_name:path}")
def catch_all(path_name: str):
    # Exclude API, Static, Docs, and Redoc routes from catch-all:
    if path_name.startswith(("api", "static", "docs", "redoc", "openapi.json")):
        raise HTTPException(status_code=404)
    dist_index = DIST_DIR / "index.html"
    if dist_index.exists():
        return FileResponse(dist_index)
    raise HTTPException(status_code=404)

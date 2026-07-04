import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.company import Company

logger = logging.getLogger(__name__)


def save_companies(companies: list[dict], db: Session) -> dict:
    """
    Insert a list of parsed company dicts into the database.
    Skips duplicates based on company_name (enforced by unique constraint).

    Returns a summary with imported and skipped counts.
    """

    imported = 0
    skipped = 0

    for record in companies:

        company_name = record.get("company_name", "").strip()

        if not company_name:
            logger.warning("Skipping record with empty company_name: %s", record)
            skipped += 1
            continue

        # Check if already exists to avoid IntegrityError noise
        existing = (
            db.query(Company)
            .filter(Company.company_name == company_name)
            .first()
        )

        if existing:
            logger.info("Duplicate skipped: %s", company_name)
            skipped += 1
            continue

        try:
            company = Company(
                company_name=company_name,
                founder=record.get("founder"),
                founded=record.get("founded"),
                source=record.get("source"),
                website=record.get("website"),
                confidence_score=0.0,
                industry=record.get("industry"),
                employee_count=record.get("employee_count"),
                country=record.get("country"),
                linkedin_url=record.get("linkedin_url"),
            )
            db.add(company)
            db.commit()
            db.refresh(company)
            imported += 1
            logger.info("Imported company: %s", company_name)

        except IntegrityError:
            db.rollback()
            logger.warning("IntegrityError on insert (race condition?): %s", company_name)
            skipped += 1

        except Exception as exc:
            db.rollback()
            logger.error("Unexpected error inserting %s: %s", company_name, exc)
            skipped += 1

    return {
        "imported": imported,
        "skipped": skipped,
        "total_processed": len(companies),
    }

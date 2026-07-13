import os
import smtplib
import logging
import datetime
from email.message import EmailMessage
from models.outreach import OutreachLog

logger = logging.getLogger("outreach")


def smtp_configured() -> bool:
    required = (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
    )
    return all(os.getenv(key) for key in required)


def send_email_or_simulate(to_email: str | None, subject: str, body: str) -> dict:
    if not to_email:
        return {
            "status": "Drafted",
            "provider_message": "No recipient email on lead. Draft saved only.",
        }

    if os.getenv("DRY_RUN", "true").lower() == "true":
        return {
            "status": "Simulated",
            "provider_message": "DRY_RUN is enabled — no real email was sent.",
        }

    if not smtp_configured():
        return {
            "status": "Simulated",
            "provider_message": "SMTP is not configured. Email was not sent.",
        }

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.getenv("SMTP_FROM_EMAIL")
    message["To"] = to_email
    message.set_content(body)

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(message)

    return {
        "status": "Sent",
        "provider_message": "Email sent through configured SMTP provider.",
    }


def business_days(start_date: datetime.datetime, n: int) -> datetime.datetime:
    """
    Adds n weekdays (skips Saturday and Sunday) to the start_date.
    """
    curr = start_date
    added = 0
    while added < n:
        curr += datetime.timedelta(days=1)
        if curr.weekday() < 5:  # Monday through Friday
            added += 1
    return curr


def process_send(lead, db, is_follow_up: bool = False) -> tuple[dict, OutreachLog]:
    """
    Shared outreach processing function. Generates email, sends/simulates,
    creates OutreachLog, and updates lead status to 'Contacted'.
    """
    from services.send_scheduler import load_send_state, save_send_state

    # Enforce daily cap
    state = load_send_state()
    sent_today = state.get("sent_today", 0)
    daily_cap = state.get("daily_cap", 10)

    if sent_today >= daily_cap:
        result = {"status": "Skipped", "provider_message": "Daily send cap reached."}
        log = OutreachLog(
            lead_id=lead.id,
            channel="email",
            subject="[Daily Cap Reached - Skipped]",
            body="[Email was not drafted or sent because the daily outreach cap was reached.]",
            status="Skipped",
            provider_message="Daily send cap reached.",
            template_variant=None,
            model_used=None,
            tokens_used=None,
        )
        db.add(log)
        db.commit()
        return result, log

    from services.email_writer import generate_cold_email

    # Draft the email using LLM or static variants
    draft = generate_cold_email(lead)

    try:
        result = send_email_or_simulate(
            to_email=lead.email,
            subject=draft["subject"],
            body=draft["body"],
        )
    except Exception as exc:
        logger.exception("Outreach sending failed")
        result = {"status": "Failed", "provider_message": str(exc)}

    # Create the outreach log record
    log = OutreachLog(
        lead_id=lead.id,
        channel="email",
        subject=draft["subject"],
        body=draft["body"],
        status=result["status"],
        provider_message=result["provider_message"],
        template_variant=draft.get("template_variant"),
        model_used=draft.get("model_used"),
        tokens_used=draft.get("tokens_used"),
    )
    db.add(log)

    if result["status"] in {"Sent", "Simulated"}:
        lead.status = "Contacted"
        now = datetime.datetime.utcnow()
        if not is_follow_up:
            lead.follow_up_step = 0
            lead.next_follow_up_at = business_days(now, 3)
        else:
            lead.follow_up_step += 1
            if lead.follow_up_step < 2:
                lead.next_follow_up_at = business_days(now, 3)
            else:
                lead.next_follow_up_at = None

        # Increment sent_today in send_state.json
        try:
            from services.send_scheduler import load_send_state, save_send_state
            state = load_send_state()
            state["sent_today"] = state.get("sent_today", 0) + 1
            save_send_state(state)
        except Exception as e:
            logger.error(f"Failed to update send state in process_send: {e}")

    return result, log

import os
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from models.lead import Lead
from services.timezone_lookup import infer_timezone
from services.outreach import process_send

logger = logging.getLogger("send_scheduler")

STATE_FILE = Path(__file__).resolve().parent.parent / "send_state.json"


def load_send_state() -> dict:
    today_str = date.today().isoformat()
    default_state = {"date": today_str, "sent_today": 0, "daily_cap": 10}
    if not STATE_FILE.exists():
        save_send_state(default_state)
        return default_state
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except Exception:
        state = default_state

    if state.get("date") != today_str:
        state["date"] = today_str
        state["sent_today"] = 0
        save_send_state(state)
    return state


def save_send_state(state: dict):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save send state: {e}")


def run_scheduled_sends(db_session_factory):
    logger.info("Scheduler job starting...")
    db = db_session_factory()
    try:
        state = load_send_state()
        sent_today = state.get("sent_today", 0)
        daily_cap = state.get("daily_cap", 10)

        if sent_today >= daily_cap:
            logger.info("Daily send cap reached. Skipping execution.")
            return

        now_utc = datetime.now(timezone.utc)
        now_naive_utc = datetime.utcnow()

        # Helper to check if lead is in business hours (Mon-Fri, 9am-5pm local time)
        def is_lead_in_business_hours(lead) -> bool:
            if not lead.timezone:
                tz_str, inferred = infer_timezone(lead)
                lead.timezone = tz_str
                lead.timezone_source = "inferred" if inferred else "default"
                db.commit()

            try:
                lead_tz = ZoneInfo(lead.timezone)
            except Exception:
                lead_tz = ZoneInfo("America/Chicago")

            local_time = now_utc.astimezone(lead_tz)
            # Skip if weekend (Saturday=5, Sunday=6)
            if local_time.weekday() in (5, 6):
                logger.info(f"Skipping lead {lead.id} because it is weekend local time ({local_time.strftime('%A')}).")
                return False
            # Skip if outside 9 <= hour < 17
            if not (9 <= local_time.hour < 17):
                logger.info(f"Skipping lead {lead.id} because it is outside business hours local time ({local_time.hour}:00).")
                return False
            return True

        # 2. Process New Sends (Approved for Outreach)
        approved_leads = (
            db.query(Lead)
            .filter(Lead.status == "Approved for Outreach")
            .all()
        )

        for lead in approved_leads:
            if not is_lead_in_business_hours(lead):
                continue

            logger.info(f"Sending first email to lead {lead.id} ({lead.full_name})")
            result, log = process_send(lead, db, is_follow_up=False)
            db.commit()

            if result.get("status") == "Skipped":
                logger.info("Daily send cap hit during approved sends batch.")
                break

        # 3. Process Follow-Ups (Contacted, follow_up_step < 2, next_follow_up_at <= now)
        followup_leads = (
            db.query(Lead)
            .filter(Lead.status == "Contacted")
            .filter(Lead.follow_up_step < 2)
            .filter(Lead.next_follow_up_at <= now_naive_utc)
            .all()
        )

        for lead in followup_leads:
            if not is_lead_in_business_hours(lead):
                continue

            logger.info(f"Sending follow-up email (step {lead.follow_up_step + 1}) to lead {lead.id} ({lead.full_name})")
            result, log = process_send(lead, db, is_follow_up=True)
            db.commit()

            if result.get("status") == "Skipped":
                logger.info("Daily send cap hit during follow-up sends batch.")
                break

    except Exception as e:
        logger.exception("Error in run_scheduled_sends job")
    finally:
        db.close()

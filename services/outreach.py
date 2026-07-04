import os
import smtplib
from email.message import EmailMessage


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

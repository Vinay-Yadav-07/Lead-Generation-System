from services.icp_loader import load_icp


def generate_cold_email(lead) -> dict:
    icp = load_icp()
    first_name = (lead.full_name or "there").split()[0]
    industry = icp.get("industry", "your space")

    subject = f"Quick idea for {lead.company_name}"
    body = (
        f"Hi {first_name},\n\n"
        f"I noticed {lead.company_name} while researching {industry} companies. "
        "AutoNova helps teams automate repetitive sales and operations workflows "
        "without adding manual overhead.\n\n"
        "If improving lead handling, follow-ups, or internal workflow speed is a "
        "priority this quarter, I can share a short automation map for your team.\n\n"
        "Would a 15-minute conversation next week make sense?\n\n"
        "Best,\n"
        "AutoNova Team"
    )
    return {"subject": subject, "body": body}

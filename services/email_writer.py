import os
import json
import logging
from pathlib import Path
from openai import OpenAI
from services.icp_loader import load_icp

# Setup Logging
logger = logging.getLogger("email_writer")
logging.basicConfig(level=logging.INFO)

EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "glm").lower()

SYSTEM_PROMPT = (
    "You are an expert B2B cold-email copywriter. Write a highly personalized, compelling "
    "cold email to a potential lead. Keep the email body strictly under 120 words. "
    "Use plain text only—do not use markdown formatting (no bold, no italics, no bullet points). "
    "Include exactly one clear Call to Action (CTA). Avoid corporate buzzwords and generic openings."
)

# Approximate token count log at import time
approx_tokens = int(len(SYSTEM_PROMPT.split()) * 1.3)
logger.info(f"System prompt token estimate: {approx_tokens}")


def load_templates() -> dict:
    config_path = Path(__file__).resolve().parent.parent / "config" / "email_templates.json"
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load email templates JSON: {e}")
        # Return fallback configuration
        return {
            "variants": [
                {
                    "id": "variant_1",
                    "hook": "Direct value prop",
                    "subject_template": "Quick idea for {company_name}",
                    "body_template": "Hi {first_name},\n\nI was looking at {company_name} and wanted to reach out. We help companies automate their key workflows.\n\nCould we chat next week?\n\nBest,\nAutoNova Team"
                }
            ],
            "active_static_variant": "variant_1"
        }


def select_variant(lead_id: int) -> dict:
    templates = load_templates()
    variants = templates.get("variants", [])
    if not variants:
        raise ValueError("No templates found in configuration")

    if EMAIL_PROVIDER == "static":
        active_id = templates.get("active_static_variant", "variant_1")
        for v in variants:
            if v["id"] == active_id:
                return v
        return variants[0]
    else:
        # Round-robin selection based on lead_id
        idx = lead_id % len(variants)
        return variants[idx]


def parse_llm_response(content: str, default_subject: str) -> tuple[str, str]:
    content = content.strip()
    subject = ""
    body = ""
    
    if "SUBJECT:" in content and "BODY:" in content:
        parts = content.split("BODY:")
        subj_part = parts[0].replace("SUBJECT:", "").strip()
        body_part = parts[1].strip()
        subject = subj_part
        body = body_part
    else:
        # Fallback line-by-line parser
        lines = content.split("\n")
        subject_lines = [l for l in lines if l.upper().startswith("SUBJECT:")]
        if subject_lines:
            subject = subject_lines[0].split(":", 1)[1].strip()
        else:
            subject = default_subject
        
        body_lines = [l for l in lines if not l.upper().startswith("SUBJECT:") and not l.upper().startswith("BODY:")]
        body = "\n".join(body_lines).strip()
        
    return subject, body


def generate_cold_email(lead) -> dict:
    first_name = (lead.full_name or "there").split()[0]
    company_name = lead.company_name or "your company"
    job_title = lead.job_title or "decision maker"
    
    # Prioritize lead's specific industry, fallback to global ICP config
    industry = lead.industry if (lead.industry and str(lead.industry).strip()) else load_icp().get("industry", "your space")

    # Select variant configuration
    variant = select_variant(lead.id)
    variant_id = variant["id"]
    hook = variant["hook"]

    default_subject = f"Quick idea for {company_name}"

    if EMAIL_PROVIDER == "static":
        subject = variant["subject_template"].format(first_name=first_name, company_name=company_name, industry=industry)
        body = variant["body_template"].format(first_name=first_name, company_name=company_name, industry=industry)
        return {
            "subject": subject,
            "body": body,
            "model_used": f"static:{variant_id}",
            "provider": "static",
            "tokens_used": None,
            "template_variant": variant_id,
        }

    # Construct LLM prompt
    user_prompt = (
        f"Write a cold email to {first_name}, the {job_title} of {company_name} in the {industry} industry.\n"
        f"Write in this style: {hook}.\n\n"
        "You must return your response in this exact format:\n"
        "SUBJECT: <subject_line>\n"
        "BODY:\n"
        "<email_body>"
    )

    # Append follow-up context if relevant
    follow_up_step = getattr(lead, "follow_up_step", 0)
    if follow_up_step > 0:
        user_prompt += f"\n\nNote: This is follow-up email #{follow_up_step}. Keep it brief and refer gently to the previous email."

    client = None
    response = None
    provider_used = EMAIL_PROVIDER
    model_used = ""
    tokens_used = None

    # Helper function to call OpenAI-compatible API
    def make_api_call(api_key, base_url, model):
        openai_client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        return openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
        )

    # 1. Main Provider Call
    if EMAIL_PROVIDER == "glm":
        try:
            logger.info("Attempting GLM completion via Z.ai...")
            model_used = "glm-4.5-flash"
            response = make_api_call(
                api_key=os.getenv("ZAI_API_KEY"),
                base_url="https://api.z.ai/api/paas/v4",
                model=model_used
            )
        except Exception as e:
            logger.warning(f"GLM completion failed: {e}. Retrying against OpenAI fallback...")
            provider_used = "openai"
            model_used = "gpt-4o-mini"
            try:
                response = make_api_call(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=None,
                    model=model_used
                )
            except Exception as e_fallback:
                logger.error(f"OpenAI fallback also failed: {e_fallback}. Falling back to static template.")
                provider_used = "static"

    elif EMAIL_PROVIDER == "openai":
        try:
            logger.info("Attempting OpenAI completion...")
            model_used = "gpt-4o-mini"
            response = make_api_call(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=None,
                model=model_used
            )
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}. Falling back to static template.")
            provider_used = "static"

    # 2. Return Payload Formulation
    if provider_used == "static" or response is None:
        subject = variant["subject_template"].format(first_name=first_name, company_name=company_name, industry=industry)
        body = variant["body_template"].format(first_name=first_name, company_name=company_name, industry=industry)
        return {
            "subject": subject,
            "body": body,
            "model_used": f"static:{variant_id}",
            "provider": "static",
            "tokens_used": None,
            "template_variant": variant_id,
        }

    # Extract subject & body from content
    content = response.choices[0].message.content
    subject, body = parse_llm_response(content, default_subject)
    
    if response.usage:
        tokens_used = response.usage.total_tokens

    return {
        "subject": subject,
        "body": body,
        "model_used": model_used,
        "provider": provider_used,
        "tokens_used": tokens_used,
        "template_variant": variant_id,
    }

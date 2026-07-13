import re

# Mapping of US State abbreviations and names to their majority IANA timezone strings.
US_STATE_TIMEZONES = {
    "AL": "America/Chicago",
    "AK": "America/Anchorage",
    "AZ": "America/Phoenix",
    "AR": "America/Chicago",
    "CA": "America/Los_Angeles",
    "CO": "America/Denver",
    "CT": "America/New_York",
    "DE": "America/New_York",
    "FL": "America/New_York",
    "GA": "America/New_York",
    "HI": "Pacific/Honolulu",
    "ID": "America/Denver",
    "IL": "America/Chicago",
    "IN": "America/New_York",
    "IA": "America/Chicago",
    "KS": "America/Chicago",
    "KY": "America/New_York",
    "LA": "America/Chicago",
    "ME": "America/New_York",
    "MD": "America/New_York",
    "MA": "America/New_York",
    "MI": "America/New_York",
    "MN": "America/Chicago",
    "MS": "America/Chicago",
    "MO": "America/Chicago",
    "MT": "America/Denver",
    "NE": "America/Chicago",
    "NV": "America/Los_Angeles",
    "NH": "America/New_York",
    "NJ": "America/New_York",
    "NM": "America/Denver",
    "NY": "America/New_York",
    "NC": "America/New_York",
    "ND": "America/Chicago",
    "OH": "America/New_York",
    "OK": "America/Chicago",
    "OR": "America/Los_Angeles",
    "PA": "America/New_York",
    "RI": "America/New_York",
    "SC": "America/New_York",
    "SD": "America/Chicago",
    "TN": "America/Chicago",
    "TX": "America/Chicago",
    "UT": "America/Denver",
    "VT": "America/New_York",
    "VA": "America/New_York",
    "WA": "America/Los_Angeles",
    "WV": "America/New_York",
    "WI": "America/Chicago",
    "WY": "America/Denver",

    # Full Names
    "ALABAMA": "America/Chicago",
    "ALASKA": "America/Anchorage",
    "ARIZONA": "America/Phoenix",
    "ARKANSAS": "America/Chicago",
    "CALIFORNIA": "America/Los_Angeles",
    "COLORADO": "America/Denver",
    "CONNECTICUT": "America/New_York",
    "DELAWARE": "America/New_York",
    "FLORIDA": "America/New_York",
    "GEORGIA": "America/New_York",
    "HAWAII": "Pacific/Honolulu",
    "IDAHO": "America/Denver",
    "ILLINOIS": "America/Chicago",
    "INDIANA": "America/New_York",
    "IOWA": "America/Chicago",
    "KANSAS": "America/Chicago",
    "KENTUCKY": "America/New_York",
    "LOUISIANA": "America/Chicago",
    "MAINE": "America/New_York",
    "MARYLAND": "America/New_York",
    "MASSACHUSETTS": "America/New_York",
    "MICHIGAN": "America/New_York",
    "MINNESOTA": "America/Chicago",
    "MISSISSIPPI": "America/Chicago",
    "MISSOURI": "America/Chicago",
    "MONTANA": "America/Denver",
    "NEBRASKA": "America/Chicago",
    "NEVADA": "America/Los_Angeles",
    "NEW HAMPSHIRE": "America/New_York",
    "NEW JERSEY": "America/New_York",
    "NEW MEXICO": "America/Denver",
    "NEW YORK": "America/New_York",
    "NORTH CAROLINA": "America/New_York",
    "NORTH DAKOTA": "America/Chicago",
    "OHIO": "America/New_York",
    "OKLAHOMA": "America/Chicago",
    "OREGON": "America/Los_Angeles",
    "PENNSYLVANIA": "America/New_York",
    "RHODE ISLAND": "America/New_York",
    "SOUTH CAROLINA": "America/New_York",
    "SOUTH DAKOTA": "America/Chicago",
    "TENNESSEE": "America/Chicago",
    "TEXAS": "America/Chicago",
    "UTAH": "America/Denver",
    "VERMONT": "America/New_York",
    "VIRGINIA": "America/New_York",
    "WASHINGTON": "America/Los_Angeles",
    "WEST VIRGINIA": "America/New_York",
    "WISCONSIN": "America/Chicago",
    "WYOMING": "America/Denver",
}

def infer_timezone(lead) -> tuple[str, bool]:
    """
    Infers the IANA timezone for a lead based on search texts (e.g. source URL).
    Returns (timezone_str, timezone_inferred).
    NOTE: This is a best-effort heuristic since the scraped data has no explicit geo field yet.
    Data Gap Flag: The scraper output should include a 'state' or 'address' field in future versions.
    """
    search_texts = []
    if getattr(lead, "source_url", None):
        search_texts.append(lead.source_url)
    if getattr(lead, "company_name", None):
        search_texts.append(lead.company_name)
    if getattr(lead, "industry", None):
        search_texts.append(lead.industry)

    combined_text = " ".join(search_texts).upper()

    # Match state tokens as whole words to avoid partial matches
    sorted_keys = sorted(US_STATE_TIMEZONES.keys(), key=len, reverse=True)
    for state_key in sorted_keys:
        pattern = r"\b" + re.escape(state_key) + r"\b"
        if re.search(pattern, combined_text):
            return US_STATE_TIMEZONES[state_key], True

    # Fallback to America/Chicago default
    return "America/Chicago", False

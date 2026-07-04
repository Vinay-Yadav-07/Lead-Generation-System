import re


def extract_companies(content):

    companies = []

    pattern = re.compile(
        r'(\d+\s*\.\s*)?'
        r'([A-Za-z0-9&\-\s]+?)'
        r'\s+Track\s+.*?'
        r'Founded\s+(\d{4})'
        r'\s+Founders\s+(.+?)'
        r'\s+Total funding amount',
        re.DOTALL
    )

    matches = pattern.finditer(content)

    for match in matches:

        company_name = match.group(2).strip()
        founded = match.group(3).strip()
        founder = match.group(4).strip()

        companies.append(
            {
                "company_name": company_name,
                "founder": founder,
                "founded": founded,
                "source": "inc42"
            }
        )

    return companies
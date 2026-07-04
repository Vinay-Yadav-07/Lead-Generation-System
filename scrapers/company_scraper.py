import requests
from bs4 import BeautifulSoup
import re


def scrape_page(url):
    try:
        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # separator=" " is critical — without it, adjacent HTML elements
        # have their text concatenated with no space, breaking regex parsers.
        return soup.get_text(
            separator=" ",
            strip=True
        )

    except Exception as e:
        return str(e)


def extract_emails(text):

    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    emails = re.findall(pattern, text)

    return list(set(emails))


def extract_phone_numbers(text):

    pattern = r"\+?\d[\d\s\-\(\)]{8,}\d"

    phones = re.findall(pattern, text)

    clean = []
    for phone in phones:
        digits = re.sub(r"\D", "", phone)
        # Reject year/date/navigation blobs that are common on websites.
        if len(digits) < 10 or len(digits) > 15:
            continue
        if re.fullmatch(r"(19|20)\d{2}(19|20)\d{2}.*", digits):
            continue
        clean.append(re.sub(r"\s+", " ", phone).strip())

    return list(dict.fromkeys(clean))


def discover_company_pages(base_url):

    pages = [
        "",
        "/about",
        "/about-us",
        "/team",
        "/leadership",
        "/management",
        "/contact"
    ]

    results = {}

    for page in pages:

        try:

            url = base_url.rstrip("/") + page

            response = requests.get(
                url,
                timeout=10
            )

            if response.status_code == 200:

                results[url] = "FOUND"

        except:
            pass

    return results


def scrape_company_pages(base_url):

    pages = discover_company_pages(base_url)

    content = ""

    for url in pages.keys():

        try:

            response = requests.get(
                url,
                timeout=10
            )

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            content += soup.get_text(
                separator=" ",
                strip=True
            )

            content += "\n\n"

        except:
            pass

    return content

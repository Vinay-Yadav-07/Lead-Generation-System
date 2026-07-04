import requests
from bs4 import BeautifulSoup


def scrape_page(url):

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

    return soup.get_text(
        separator=" ",
        strip=True
    )
from urllib.parse import urlparse


BLACKLIST = [
    "wikipedia.org",
    "geeksforgeeks.org",
    "investopedia.com",
    "tripadvisor.in",
    "booking.com",
    "cambridge.org",
    "merriam-webster.com"
]


def filter_companies(results):

    companies = []

    seen = set()

    for result in results:

        url = result.get("url")

        if not url:
            continue

        domain = urlparse(url).netloc.lower()

        if any(
            bad in domain
            for bad in BLACKLIST
        ):
            continue

        if domain in seen:
            continue

        seen.add(domain)

        companies.append(
            {
                "title": result["title"],
                "domain": domain,
                "url": url,
                "source_query": result["query"]
            }
        )

    return companies
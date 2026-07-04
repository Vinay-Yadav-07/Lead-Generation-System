from ddgs import DDGS
from services.icp_loader import load_icp


def build_queries():

    icp = load_icp()

    industry = icp.get("industry", "")
    geography = icp.get("country", "")

    queries = []

    if industry and geography:

        queries.extend([
            f'"{industry}" "{geography}" company official website contact',
            f'"{industry}" "{geography}" manufacturer official website',
            f'"{industry}" "{geography}" private limited official website',
            f'"{industry}" "{geography}" about us contact',
        ])

    return queries


def discover_companies():

    queries = build_queries()
    print("QUERIES:", queries)

    companies = []

    with DDGS() as ddgs:

        for query in queries:

            try:

                results = ddgs.text(
                    query,
                    max_results=20
                )

                for result in results:

                    companies.append(
                        {
                            "query": query,
                            "title": result.get("title"),
                            "url": result.get("href")
                        }
                    )

            except Exception as e:

                  return {
        "error": str(e)
    }

    return companies

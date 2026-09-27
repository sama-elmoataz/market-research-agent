import json

from langchain.tools import tool
from langsmith import traceable
from tavily import TavilyClient

from .config import TAVILY_API_KEY


tavily_client = TavilyClient(
    api_key=TAVILY_API_KEY
)


@traceable(
    name="tavily_search",
    run_type="tool",
)
def search_web(
    query: str,
    max_results: int = 3,
) -> list[dict]:

    response = tavily_client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
    )

    results = response.get(
        "results",
        []
    )

    cleaned_results = []

    for result in results:
        cleaned_results.append({
            "title": result.get(
                "title",
                ""
            ),
            "url": result.get(
                "url",
                ""
            ),
            "content": result.get(
                "content",
                ""
            )[:1500],
        })

    return cleaned_results


@tool
def web_search(
    query: str
) -> str:
    """
    Search the web for current market,
    competitor, industry, pricing,
    customer, and business information.
    """

    results = search_web(
        query=query,
        max_results=3,
    )

    return json.dumps(
        results,
        ensure_ascii=False,
    )


tools = [
    web_search
]
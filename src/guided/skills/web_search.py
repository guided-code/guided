from typing import Any, Dict, List, Optional

import requests
from ddgs import DDGS
from markdownify import markdownify as md


def search_web_text(
    query: str,
    region: str = "us-en",
    safesearch: str = "off",
    timelimit: Optional[str] = None,
    max_results: int = 5,
    page: int = 1,
    backend: str = "duckduckgo",
) -> List[Dict[str, Any]]:
    """
    Search the Internet for a information using a search engine.

    Args:
        query: text search query.
        region: us-en, uk-en, ru-ru, etc. Defaults to us-en.
        safesearch: on, moderate, off. Defaults to "off".
        timelimit: d, w, m, y. Defaults to None.
        max_results: maximum number of results. Defaults to 5.
        page: page of results. Defaults to 1.
        backend: A single or comma-delimited backends. Defaults to "duckduckgo".

    Returns:
        List of dictionaries with search results.
    """
    results = []
    try:
        raw_results = DDGS().text(
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
        )
        # Convert 'href' to 'url' for consistency
        results = [
            {"title": r.get("title", ""), "url": r.get("href", "")} for r in raw_results
        ]
    except Exception:
        # Fallback to empty list on error
        pass

    return results


def request_web(url: str, use_markdown: bool = True) -> str:
    """
    Request a Web page from the Internet to retrieve real-time data.

    Args:
        url: URL of the Web page.
        use_markdown: If True, return the page as markdown. Defaults to True.

    Returns:
        str: Web page content as markdown or HTML.
    """
    try:
        response = requests.get("https://www.example.com")
        response.raise_for_status()

        if use_markdown:
            return md(response.text)
        else:
            return response.text
    except Exception:
        return "Unable to retrieve "

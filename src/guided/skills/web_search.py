from typing import Any, Dict, List, Optional

from ddgs import DDGS


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

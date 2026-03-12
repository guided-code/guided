from typing import Any, Dict, List

from ddgs import DDGS


def search_text(
    query: str,
    region: str = "us-en",
    safesearch: str = "off",
    timelimit: str = "day",
    max_results: int = 5,
    page: int = 1,
    backend: str = "duckduckgo",
) -> List[Dict[str, Any]]:
    """Search the web using the duckduckgo-search package.

    Returns a list of result dicts with 'title' and 'url' keys.
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

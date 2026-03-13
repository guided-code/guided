from unittest.mock import MagicMock, patch

from guided.skills.web_search import search_web_text


def test_search_returns_results():
    mock_results = [
        {"title": "Result One", "href": "http://example.com/1", "body": "..."},
        {"title": "Result Two", "href": "http://example.com/2", "body": "..."},
    ]
    with patch("guided.skills.web_search.DDGS") as mock_ddgs_cls:
        mock_ddgs_cls.return_value.text.return_value = mock_results
        results = search_web_text("test query")

    assert len(results) == 2
    assert results[0]["title"] == "Result One"
    assert results[0]["url"] == "http://example.com/1"
    assert results[1]["title"] == "Result Two"
    assert results[1]["url"] == "http://example.com/2"


def test_search_converts_href_to_url():
    """Verifies that the 'href' key from DDGS is mapped to 'url'."""
    mock_results = [{"title": "Test", "href": "http://example.com", "body": "text"}]
    with patch("guided.skills.web_search.DDGS") as mock_ddgs_cls:
        mock_ddgs_cls.return_value.text.return_value = mock_results
        results = search_web_text("query")

    assert "url" in results[0]
    assert "href" not in results[0]
    assert results[0]["url"] == "http://example.com"


def test_search_handles_exception_returns_empty_list():
    with patch("guided.skills.web_search.DDGS") as mock_ddgs_cls:
        mock_ddgs_cls.return_value.text.side_effect = Exception("network error")
        results = search_web_text("test query")

    assert results == []


def test_search_passes_parameters_to_ddgs():
    with patch("guided.skills.web_search.DDGS") as mock_ddgs_cls:
        mock_ddgs_cls.return_value.text.return_value = []
        search_web_text(
            "query",
            region="uk-en",
            safesearch="moderate",
            timelimit="w",
            max_results=10,
            page=2,
        )
        mock_ddgs_cls.return_value.text.assert_called_once_with(
            "query",
            region="uk-en",
            safesearch="moderate",
            timelimit="w",
            max_results=10,
            page=2,
            backend="duckduckgo",
        )


def test_search_handles_missing_fields_gracefully():
    """Results missing 'title' or 'href' default to empty string."""
    mock_results = [{"body": "no title or href here"}]
    with patch("guided.skills.web_search.DDGS") as mock_ddgs_cls:
        mock_ddgs_cls.return_value.text.return_value = mock_results
        results = search_web_text("query")

    assert results[0]["title"] == ""
    assert results[0]["url"] == ""

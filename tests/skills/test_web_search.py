from unittest.mock import patch

from guided.skills.web_search import search_text

MOCK_RESULTS = [
    {
        "title": "Python (programming language) - Wikipedia",
        "href": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "body": "Pythonis a multi-paradigmprogramminglanguage. Object-orientedprogrammingand structuredprogrammingare fully supported, and many of their features support functionalprogrammingand aspect-orientedprogramming- including metaprogramming [62] and metaobjects. [63] Many other paradigms are supported via extensions, including design by contract [64][65] and logicprogramming. [66]Python...",
    },
    {
        "title": "Welcome to Python.org",
        "href": "https://www.python.org/",
        "body": "Pythonis a versatile and easy-to-learnprogramminglanguage that lets you work quickly and integrate systems more effectively. LearnPythonbasics, download the latest version, access documentation, find jobs, events, success stories and more on the official website.",
    },
    {
        "title": "Python Tutorial - W3Schools",
        "href": "https://www.w3schools.com/python/",
        "body": "LearnPythonPythonis a popularprogramminglanguage.Pythoncan be used on a server to create web applications. Start learningPythonnow »",
    },
    {
        "title": "How to Use Python: Your First Steps - Real Python",
        "href": "https://realpython.com/python-first-steps/",
        "body": "Learn how to use Python—install it, run code, and work with data types, functions, classes, and loops. Explore essential tools and build a solid foundation.",
    },
    {
        "title": "Learn Python: Complete Beginner Course | OpenPython",
        "href": "https://openpython.org/courses/learnpython",
        "body": "LearnPython: Complete Beginner Course MasterPythonprogrammingfrom scratch with hands-on interactive lessons. Practice coding directly in your browser with immediate feedback.",
    },
]


@patch("guided.skills.web_search.DDGS")
def test_search_returns_results(mock_ddgs):
    # Setup mock - DDGS().text() returns MOCK_RESULTS
    mock_ddgs.return_value.text.return_value = MOCK_RESULTS

    results = search_text("python programming")

    assert len(results) == 5
    assert "Python (programming language) - Wikipedia" in list(
        map(lambda r: r["title"], results)
    )
    mock_ddgs.return_value.text.assert_called_once_with(
        "python programming",
        region="us-en",
        safesearch="off",
        timelimit="day",
        max_results=5,
        page=1,
        backend="duckduckgo",
    )


@patch("guided.skills.web_search.DDGS")
def test_search_empty_results(mock_ddgs):
    mock_ddgs.return_value.text.return_value = []

    results = search_text("xyzzy_no_results")

    assert results == []


@patch("guided.skills.web_search.DDGS")
def test_search_exception_handled(mock_ddgs):
    mock_ddgs.return_value.text.side_effect = Exception("Network error")

    results = search_text("error_test")

    assert results == []

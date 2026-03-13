from guided.environment import get_logging_level, is_debug


def test_is_debug_false_by_default(monkeypatch):
    monkeypatch.delenv("DEBUG", raising=False)
    assert is_debug() is False


def test_is_debug_with_string_1(monkeypatch):
    monkeypatch.setenv("DEBUG", "1")
    assert is_debug() is True


def test_is_debug_with_true(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    assert is_debug() is True


def test_is_debug_with_yes(monkeypatch):
    monkeypatch.setenv("DEBUG", "yes")
    assert is_debug() is True


def test_is_debug_with_zero(monkeypatch):
    monkeypatch.setenv("DEBUG", "0")
    assert is_debug() is False


def test_is_debug_with_false(monkeypatch):
    monkeypatch.setenv("DEBUG", "false")
    assert is_debug() is False


def test_get_logging_level_default(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert get_logging_level() == "INFO"


def test_get_logging_level_custom(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    assert get_logging_level() == "DEBUG"


def test_get_logging_level_warning(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    assert get_logging_level() == "WARNING"

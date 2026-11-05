import pytest

from haver.config import Settings


def test_empty_api_key_is_treated_as_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    assert Settings(_env_file=None).gemini_api_key is None

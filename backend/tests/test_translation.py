"""Unit tests for the translation service (Phase 1.3.2).

All tests use a temporary dictionary file and a mock fallback so they run
fully offline without requiring argostranslate or spaCy models.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.translation import DictionaryTranslator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_dict(tmp_path: Path, data: dict[str, list[str]]) -> Path:
    """Write *data* as a JSON dict file and return its path."""
    p = tmp_path / "nl_en_dict.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def _mock_fallback(translations: list[str] | None = None) -> MagicMock:
    """Return a mock Translator whose translate() returns *translations*."""
    fallback = MagicMock()
    fallback.translate.return_value = translations or []
    return fallback


# ---------------------------------------------------------------------------
# DictionaryTranslator tests
# ---------------------------------------------------------------------------


class TestDictionaryTranslator:
    def test_word_in_dict_returns_dict_translations(self, tmp_path: Path) -> None:
        """A lemma present in the dictionary returns its stored translations."""
        dict_path = _write_dict(tmp_path, {"bank": ["bench", "couch"]})
        fallback = _mock_fallback(["bank"])
        translator = DictionaryTranslator(fallback=fallback, dict_path=dict_path)

        result = translator.translate("bank", "nl")

        assert result == ["bench", "couch"]
        fallback.translate.assert_not_called()

    def test_word_not_in_dict_falls_back_to_argos(self, tmp_path: Path) -> None:
        """A lemma absent from the dictionary delegates to the fallback translator."""
        dict_path = _write_dict(tmp_path, {"bank": ["bench"]})
        fallback = _mock_fallback(["run"])
        translator = DictionaryTranslator(fallback=fallback, dict_path=dict_path)

        result = translator.translate("lopen", "nl")

        assert result == ["run"]
        fallback.translate.assert_called_once_with("lopen", "nl")

    def test_dict_hit_does_not_call_fallback(self, tmp_path: Path) -> None:
        """Fallback is never invoked when the dictionary has the word."""
        dict_path = _write_dict(tmp_path, {"huis": ["house", "home"]})
        fallback = _mock_fallback()
        translator = DictionaryTranslator(fallback=fallback, dict_path=dict_path)

        translator.translate("huis", "nl")

        fallback.translate.assert_not_called()

    def test_corrupt_dict_file_falls_back_to_argos(self, tmp_path: Path) -> None:
        """A corrupt (unparseable) JSON file falls back to the fallback translator."""
        corrupt_path = tmp_path / "nl_en_dict.json"
        corrupt_path.write_text("{not valid json", encoding="utf-8")
        fallback = _mock_fallback(["house"])
        translator = DictionaryTranslator(fallback=fallback, dict_path=corrupt_path)

        result = translator.translate("huis", "nl")

        assert result == ["house"]
        fallback.translate.assert_called_once_with("huis", "nl")

    def test_dict_file_containing_list_falls_back_to_argos(self, tmp_path: Path) -> None:
        """A JSON file containing a list instead of a dict falls back gracefully."""
        list_path = tmp_path / "nl_en_dict.json"
        list_path.write_text('["huis", "bank"]', encoding="utf-8")
        fallback = _mock_fallback(["house"])
        translator = DictionaryTranslator(fallback=fallback, dict_path=list_path)

        result = translator.translate("huis", "nl")

        assert result == ["house"]
        fallback.translate.assert_called_once_with("huis", "nl")

    def test_missing_dict_file_falls_back_for_all_lookups(self, tmp_path: Path) -> None:
        """If the dictionary file does not exist, every lookup uses the fallback."""
        missing_path = tmp_path / "does_not_exist.json"
        fallback = _mock_fallback(["house"])
        translator = DictionaryTranslator(fallback=fallback, dict_path=missing_path)

        result = translator.translate("huis", "nl")

        assert result == ["house"]
        fallback.translate.assert_called_once_with("huis", "nl")

    def test_missing_file_warning_emitted_only_once(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The missing-dictionary warning is logged exactly once across multiple calls."""
        missing_path = tmp_path / "does_not_exist.json"
        fallback = _mock_fallback(["house"])
        translator = DictionaryTranslator(fallback=fallback, dict_path=missing_path)

        import logging

        with caplog.at_level(logging.WARNING, logger="app.services.translation"):
            translator.translate("huis", "nl")
            translator.translate("bank", "nl")

        warning_records = [r for r in caplog.records if "dictionary not found" in r.message]
        assert len(warning_records) == 1

    def test_dict_loaded_only_once(self, tmp_path: Path) -> None:
        """The dictionary file is read exactly once regardless of call count."""
        data = {"huis": ["house"], "bank": ["bench"]}
        dict_path = _write_dict(tmp_path, data)
        fallback = _mock_fallback()
        translator = DictionaryTranslator(fallback=fallback, dict_path=dict_path)

        original_load = json.load
        with patch("app.services.translation.json.load", side_effect=original_load) as mock_load:
            translator.translate("huis", "nl")
            translator.translate("bank", "nl")
            translator.translate("huis", "nl")

        mock_load.assert_called_once()

    def test_multiple_lookups_correct_results(self, tmp_path: Path) -> None:
        """Multiple successive lookups each return the correct translations."""
        dict_path = _write_dict(
            tmp_path,
            {
                "huis": ["house", "home"],
                "kat": ["cat"],
                "hond": ["dog"],
            },
        )
        fallback = _mock_fallback(["fallback"])
        translator = DictionaryTranslator(fallback=fallback, dict_path=dict_path)

        assert translator.translate("huis", "nl") == ["house", "home"]
        assert translator.translate("kat", "nl") == ["cat"]
        assert translator.translate("onbekend", "nl") == ["fallback"]

        # Only the miss hit the fallback.
        fallback.translate.assert_called_once_with("onbekend", "nl")

    def test_fallback_called_with_correct_language_code(self, tmp_path: Path) -> None:
        """The language_code is forwarded to the fallback unchanged."""
        dict_path = _write_dict(tmp_path, {})
        fallback = _mock_fallback(["result"])
        translator = DictionaryTranslator(fallback=fallback, dict_path=dict_path)

        translator.translate("woord", "nl")

        fallback.translate.assert_called_once_with("woord", "nl")

    def test_empty_dict_always_falls_back(self, tmp_path: Path) -> None:
        """An empty dictionary file causes every lookup to use the fallback."""
        dict_path = _write_dict(tmp_path, {})
        fallback = _mock_fallback(["word"])
        translator = DictionaryTranslator(fallback=fallback, dict_path=dict_path)

        result = translator.translate("woord", "nl")

        assert result == ["word"]
        fallback.translate.assert_called_once()

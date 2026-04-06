"""Unit tests for pure helper functions in scripts/build_nl_dict.py.

These functions are stateless and require no network access or external models.
"""

from __future__ import annotations

import build_nl_dict as bnd


class TestCleanGloss:
    def test_strips_parenthetical_qualifiers(self) -> None:
        assert bnd._clean_gloss("bank (financial institution)") == ["bank"]

    def test_splits_on_comma(self) -> None:
        assert bnd._clean_gloss("bench, sofa") == ["bench", "sofa"]

    def test_splits_on_semicolon(self) -> None:
        assert bnd._clean_gloss("cat; feline") == ["cat", "feline"]

    def test_filters_out_multi_word_glosses(self) -> None:
        # More than MAX_GLOSS_WORDS (3) words — not a translation, skip it.
        assert bnd._clean_gloss("to go to the store") == []

    def test_allows_up_to_max_gloss_words(self) -> None:
        assert bnd._clean_gloss("go to sleep") == ["go to sleep"]

    def test_empty_string_returns_empty_list(self) -> None:
        assert bnd._clean_gloss("") == []

    def test_whitespace_only_returns_empty_list(self) -> None:
        assert bnd._clean_gloss("   ") == []

    def test_lowercases_result(self) -> None:
        assert bnd._clean_gloss("House") == ["house"]

    def test_strips_surrounding_whitespace_from_parts(self) -> None:
        assert bnd._clean_gloss("  cat ,  dog  ") == ["cat", "dog"]

    def test_nested_parentheticals_stripped(self) -> None:
        assert bnd._clean_gloss("run (to run) fast") == ["run fast"]


class TestParseEntry:
    def _entry(self, word: str, senses: list) -> dict:  # type: ignore[type-arg]
        return {"word": word, "senses": senses}

    def _sense(self, *glosses: str) -> dict:  # type: ignore[type-arg]
        return {"glosses": list(glosses)}

    def test_returns_word_and_translations(self) -> None:
        entry = self._entry("kat", [self._sense("cat")])
        result = bnd._parse_entry(entry)
        assert result == ("kat", ["cat"])

    def test_empty_word_returns_none(self) -> None:
        entry = self._entry("", [self._sense("cat")])
        assert bnd._parse_entry(entry) is None

    def test_no_senses_returns_none(self) -> None:
        entry = self._entry("kat", [])
        assert bnd._parse_entry(entry) is None

    def test_senses_with_no_glosses_returns_none(self) -> None:
        entry = self._entry("kat", [{"glosses": []}])
        assert bnd._parse_entry(entry) is None

    def test_deduplicates_translations_across_senses(self) -> None:
        entry = self._entry("bank", [self._sense("bench"), self._sense("bench")])
        result = bnd._parse_entry(entry)
        assert result is not None
        assert result[1].count("bench") == 1

    def test_collects_translations_from_multiple_senses(self) -> None:
        entry = self._entry("bank", [self._sense("bench"), self._sense("sofa")])
        result = bnd._parse_entry(entry)
        assert result is not None
        assert "bench" in result[1]
        assert "sofa" in result[1]

    def test_caps_at_max_translations(self) -> None:
        senses = [self._sense(f"word{i}") for i in range(10)]
        entry = self._entry("foo", senses)
        result = bnd._parse_entry(entry)
        assert result is not None
        assert len(result[1]) == bnd.MAX_TRANSLATIONS

    def test_only_first_gloss_of_each_sense_used(self) -> None:
        # Second gloss in a sense should be ignored.
        entry = self._entry("kat", [self._sense("cat", "ignored")])
        result = bnd._parse_entry(entry)
        assert result is not None
        assert result[1] == ["cat"]

    def test_word_lowercased(self) -> None:
        entry = self._entry("Kat", [self._sense("cat")])
        result = bnd._parse_entry(entry)
        assert result is not None
        assert result[0] == "kat"

    def test_gloss_that_exceeds_word_limit_skipped(self) -> None:
        # A long gloss is not a useful translation.
        entry = self._entry("foo", [self._sense("this is a very long definition not useful")])
        assert bnd._parse_entry(entry) is None

"""Unit tests for the NLP service.

Tests cover:
  - _build_chunks: partitioning a spaCy doc into fixed-size token lists
  - extract_vocabulary: POS filtering, lemmatisation, and deduplication

All tests mock the spaCy model so no language model download is required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.nlp import (
    MIN_TOKEN_LENGTH,
    _build_chunks,
    extract_vocabulary,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_token(
    *,
    is_space: bool = False,
    pos_: str = "NOUN",
    is_punct: bool = False,
    like_num: bool = False,
    lemma_: str = "woord",
    text: str = "woord",
    i: int = 0,
) -> MagicMock:
    """Create a mock spaCy token with only the attributes read by nlp.py."""
    token = MagicMock()
    token.is_space = is_space
    token.pos_ = pos_
    token.is_punct = is_punct
    token.like_num = like_num
    token.lemma_ = lemma_
    token.text = text
    token.i = i
    return token


def _make_doc(tokens: list[MagicMock]) -> MagicMock:
    """Create a mock spaCy Doc that supports iteration and span slicing.

    Slices use ``token.i`` as the index key so chunk-text reconstruction
    (``doc[tokens[0].i : tokens[-1].i + 1].text``) returns the joined text
    of the tokens in that index range.
    """
    by_index: dict[int, MagicMock] = {t.i: t for t in tokens}

    doc = MagicMock()
    doc.__iter__ = lambda self: iter(tokens)

    def _getitem(_self: object, key: int | slice) -> MagicMock:
        # MagicMock calls magic methods as bound methods, passing self first.
        if isinstance(key, slice):
            start = key.start or 0
            stop = key.stop if key.stop is not None else (max(by_index) + 1 if by_index else 0)
            span_tokens = [by_index[idx] for idx in range(start, stop) if idx in by_index]
            span = MagicMock()
            span.text = " ".join(t.text for t in span_tokens)
            return span
        return tokens[key]

    doc.__getitem__ = _getitem
    return doc


def _run_extract(
    tokens: list[MagicMock],
    text: str = "test article text",
    language_code: str = "nl",
) -> list[dict]:
    """Run extract_vocabulary with mocked spaCy model and translator."""
    doc = _make_doc(tokens)
    mock_model = MagicMock(return_value=doc)
    mock_translator = MagicMock()
    mock_translator.translate.return_value = ["translation"]

    with (
        patch("app.services.nlp.get_model", return_value=mock_model),
        patch("app.services.nlp.translator", mock_translator),
    ):
        return extract_vocabulary(text, language_code)


# ---------------------------------------------------------------------------
# _build_chunks
# ---------------------------------------------------------------------------

DEFAULT_CHUNK_SIZE = 10

class TestBuildChunks:
    def test_empty_doc_returns_empty_list(self) -> None:
        doc = _make_doc([])
        assert _build_chunks(doc, DEFAULT_CHUNK_SIZE) == []

    def test_fewer_than_chunk_size_returns_single_chunk(self) -> None:
        tokens = [_make_token(i=i) for i in range(5)]
        chunks = _build_chunks(_make_doc(tokens), DEFAULT_CHUNK_SIZE)
        assert len(chunks) == 1
        assert chunks[0] == tokens

    def test_exactly_chunk_size_returns_single_chunk(self) -> None:
        tokens = [_make_token(i=i) for i in range(DEFAULT_CHUNK_SIZE)]
        chunks = _build_chunks(_make_doc(tokens), DEFAULT_CHUNK_SIZE)
        assert len(chunks) == 1
        assert len(chunks[0]) == DEFAULT_CHUNK_SIZE

    def test_fifteen_tokens_produces_two_chunks(self) -> None:
        tokens = [_make_token(i=i) for i in range(15)]
        chunks = _build_chunks(_make_doc(tokens), DEFAULT_CHUNK_SIZE)
        assert len(chunks) == 2
        assert len(chunks[0]) == 10
        assert len(chunks[1]) == 5

    def test_twenty_tokens_produces_two_equal_chunks(self) -> None:
        tokens = [_make_token(i=i) for i in range(20)]
        chunks = _build_chunks(_make_doc(tokens), DEFAULT_CHUNK_SIZE)
        assert len(chunks) == 2
        assert all(len(c) == DEFAULT_CHUNK_SIZE for c in chunks)

    def test_space_tokens_are_excluded_and_do_not_count_toward_chunk_size(self) -> None:
        word_tokens = [_make_token(is_space=False, i=i) for i in range(5)]
        space_tokens = [_make_token(is_space=True, i=5 + i) for i in range(5)]
        chunks = _build_chunks(_make_doc(word_tokens + space_tokens), DEFAULT_CHUNK_SIZE)
        assert len(chunks) == 1
        assert len(chunks[0]) == 5
        assert all(not t.is_space for t in chunks[0])

    def test_custom_chunk_size_is_respected(self) -> None:
        tokens = [_make_token(i=i) for i in range(9)]
        chunks = _build_chunks(_make_doc(tokens), chunk_size=3)
        assert len(chunks) == 3
        assert all(len(c) == 3 for c in chunks)

    def test_single_token_produces_single_chunk_of_one(self) -> None:
        tokens = [_make_token(i=0)]
        chunks = _build_chunks(_make_doc(tokens), DEFAULT_CHUNK_SIZE)
        assert len(chunks) == 1
        assert len(chunks[0]) == 1


# ---------------------------------------------------------------------------
# extract_vocabulary – POS filter
# ---------------------------------------------------------------------------


class TestPosFilter:
    @pytest.mark.parametrize(
        "pos_",
        ["NOUN", "VERB", "ADJ", "ADV", "ADP", "CCONJ", "SCONJ"],
    )
    def test_meaningful_pos_tags_are_included(self, pos_: str) -> None:
        token = _make_token(pos_=pos_, lemma_="woord", i=0)
        result = _run_extract([token])
        assert len(result[0]["vocabulary"]) == 1

    @pytest.mark.parametrize(
        "pos_",
        ["PUNCT", "SPACE", "NUM", "DET", "PRON", "PROPN", "SYM", "X"],
    )
    def test_non_meaningful_pos_tags_are_excluded(self, pos_: str) -> None:
        token = _make_token(pos_=pos_, lemma_="woord", i=0)
        result = _run_extract([token])
        assert result[0]["vocabulary"] == []

    def test_is_punct_token_is_excluded_even_with_meaningful_pos(self) -> None:
        # Guards the is_punct safety check independently of POS tagging.
        token = _make_token(pos_="NOUN", is_punct=True, lemma_="woord", i=0)
        result = _run_extract([token])
        assert result[0]["vocabulary"] == []

    def test_like_num_token_is_excluded(self) -> None:
        token = _make_token(pos_="NUM", like_num=True, lemma_="42", i=0)
        result = _run_extract([token])
        assert result[0]["vocabulary"] == []


# ---------------------------------------------------------------------------
# extract_vocabulary – lemmatisation
# ---------------------------------------------------------------------------


class TestLemmatisation:
    def test_lemma_is_used_as_source_not_surface_form(self) -> None:
        token = _make_token(pos_="VERB", lemma_="lopen", text="loopt", i=0)
        result = _run_extract([token])
        assert result[0]["vocabulary"][0]["source"] == "lopen"

    def test_lemma_is_lowercased(self) -> None:
        token = _make_token(pos_="NOUN", lemma_="Huis", i=0)
        result = _run_extract([token])
        assert result[0]["vocabulary"][0]["source"] == "huis"

    def test_lemma_is_stripped_of_whitespace(self) -> None:
        token = _make_token(pos_="NOUN", lemma_="  huis  ", i=0)
        result = _run_extract([token])
        assert result[0]["vocabulary"][0]["source"] == "huis"

    def test_lemma_shorter_than_min_length_is_excluded(self) -> None:
        short = "ab"  # len 2 < MIN_TOKEN_LENGTH (3)
        assert len(short) < MIN_TOKEN_LENGTH
        token = _make_token(pos_="NOUN", lemma_=short, i=0)
        result = _run_extract([token])
        assert result[0]["vocabulary"] == []

    def test_lemma_at_exactly_min_length_is_included(self) -> None:
        exact = "a" * MIN_TOKEN_LENGTH
        token = _make_token(pos_="NOUN", lemma_=exact, i=0)
        result = _run_extract([token])
        assert result[0]["vocabulary"] != []

    @pytest.mark.parametrize(
        "pos_, expected_label",
        [
            ("NOUN", "noun"),
            ("VERB", "verb"),
            ("ADJ", "adj"),
            ("ADV", "adv"),
            ("ADP", "adp"),
            ("CCONJ", "conj"),
            ("SCONJ", "conj"),
        ],
    )
    def test_pos_label_mapping_is_correct(self, pos_: str, expected_label: str) -> None:
        token = _make_token(pos_=pos_, lemma_="woord", i=0)
        result = _run_extract([token])
        assert result[0]["vocabulary"][0]["pos"] == expected_label


# ---------------------------------------------------------------------------
# extract_vocabulary – deduplication
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_duplicate_lemmas_within_same_chunk_are_deduplicated(self) -> None:
        tokens = [
            _make_token(pos_="NOUN", lemma_="huis", i=0),
            _make_token(pos_="NOUN", lemma_="huis", i=1),
        ]
        result = _run_extract(tokens)
        assert len(result[0]["vocabulary"]) == 1

    def test_same_lemma_in_different_chunks_appears_in_both(self) -> None:
        # Fill chunk 0 with 10 distinct words, then repeat one in chunk 1.
        chunk0 = [
            _make_token(pos_="NOUN", lemma_=f"word{i}", text=f"word{i}", i=i) for i in range(10)
        ]
        chunk1_token = _make_token(pos_="NOUN", lemma_="word0", text="word0", i=10)
        result = _run_extract(chunk0 + [chunk1_token])
        assert len(result) == 2
        chunk1_sources = [v["source"] for v in result[1]["vocabulary"]]
        assert "word0" in chunk1_sources

    def test_translation_is_called_with_normalised_lemma_and_language(self) -> None:
        token = _make_token(pos_="NOUN", lemma_="  Huis  ", i=0)
        doc = _make_doc([token])
        mock_model = MagicMock(return_value=doc)
        mock_translator = MagicMock()
        mock_translator.translate.return_value = ["house"]

        with (
            patch("app.services.nlp.get_model", return_value=mock_model),
            patch("app.services.nlp.translator", mock_translator),
        ):
            result = extract_vocabulary("Huis", "nl")

        mock_translator.translate.assert_called_once_with("huis", "nl")
        assert result[0]["vocabulary"][0]["translations"] == ["house"]

    def test_each_unique_lemma_in_chunk_calls_translate_once(self) -> None:
        tokens = [
            _make_token(pos_="NOUN", lemma_="huis", i=0),
            _make_token(pos_="NOUN", lemma_="huis", i=1),  # duplicate
            _make_token(pos_="NOUN", lemma_="kat", i=2),
        ]
        doc = _make_doc(tokens)
        mock_model = MagicMock(return_value=doc)
        mock_translator = MagicMock()
        mock_translator.translate.return_value = ["x"]

        with (
            patch("app.services.nlp.get_model", return_value=mock_model),
            patch("app.services.nlp.translator", mock_translator),
        ):
            extract_vocabulary("test", "nl")

        assert mock_translator.translate.call_count == 2


# ---------------------------------------------------------------------------
# extract_vocabulary – chunk metadata
# ---------------------------------------------------------------------------


class TestChunkMetadata:
    def test_chunk_index_is_zero_based_and_sequential(self) -> None:
        tokens = [_make_token(pos_="NOUN", lemma_=f"w{i}", text=f"w{i}", i=i) for i in range(15)]
        result = _run_extract(tokens)
        assert [c["index"] for c in result] == [0, 1]

    def test_chunk_text_is_populated(self) -> None:
        token = _make_token(pos_="NOUN", lemma_="huis", text="huis", i=0)
        result = _run_extract([token])
        assert isinstance(result[0]["text"], str)
        assert len(result[0]["text"]) > 0

    def test_empty_doc_produces_no_chunks(self) -> None:
        result = _run_extract([])
        assert result == []

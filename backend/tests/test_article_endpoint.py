"""Integration tests for POST /api/article (Phase 1.5).

Three test classes:
  - TestArticleValidation  – request validation enforced by Pydantic (no NLP needed)
  - TestArticleErrorHandling – endpoint maps ValueError → 422, RuntimeError → 503
  - TestArticleIntegration – full NLP pipeline with real spaCy model (skipped if not installed)
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from app.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_URL = "http://test"


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=_BASE_URL,
    )


# Detect whether the Dutch spaCy model is available without loading it.
try:
    import spacy.util as _spacy_util

    _NL_MODEL_AVAILABLE = "nl_core_news_sm" in _spacy_util.get_installed_models()
except Exception:
    _NL_MODEL_AVAILABLE = False

requires_nl_model = pytest.mark.skipif(
    not _NL_MODEL_AVAILABLE,
    reason="nl_core_news_sm is not installed – run: python -m spacy download nl_core_news_sm",
)

# Short Dutch sentences used across integration tests.
_SHORT_NL = "De kat zit op de mat naast het huis"  # < 10 words after filtering
_LONG_NL = (
    "De kat loopt snel naar het grote rode huis en de hond rent"
    " door het groene bos terwijl de kleine vogel vrolijk zingt op de hoge boom"
)  # > 20 words – guarantees multiple chunks


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------


class TestArticleValidation:
    @pytest.fixture
    async def client(self):
        async with _client() as ac:
            yield ac

    async def test_empty_text_returns_422(self, client: httpx.AsyncClient) -> None:
        resp = await client.post("/api/article", json={"text": "", "language_code": "nl"})
        assert resp.status_code == 422

    async def test_missing_text_field_returns_422(self, client: httpx.AsyncClient) -> None:
        resp = await client.post("/api/article", json={"language_code": "nl"})
        assert resp.status_code == 422

    async def test_missing_language_code_returns_422(self, client: httpx.AsyncClient) -> None:
        resp = await client.post("/api/article", json={"text": "some text"})
        assert resp.status_code == 422

    async def test_unsupported_language_code_returns_422(self, client: httpx.AsyncClient) -> None:
        # "fr" is not in the LanguageCode Literal → rejected by Pydantic before hitting NLP.
        resp = await client.post("/api/article", json={"text": "some text", "language_code": "fr"})
        assert resp.status_code == 422

    async def test_empty_body_returns_422(self, client: httpx.AsyncClient) -> None:
        resp = await client.post("/api/article")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Error-handling mapping
# ---------------------------------------------------------------------------


class TestArticleErrorHandling:
    @pytest.fixture
    async def client(self):
        async with _client() as ac:
            yield ac

    async def test_value_error_from_nlp_maps_to_422(self, client: httpx.AsyncClient) -> None:
        with patch(
            "app.api.article.extract_vocabulary",
            side_effect=ValueError("unsupported language"),
        ):
            resp = await client.post("/api/article", json={"text": "test", "language_code": "nl"})
        assert resp.status_code == 422
        assert "unsupported language" in resp.json()["detail"]

    async def test_runtime_error_from_nlp_maps_to_503(self, client: httpx.AsyncClient) -> None:
        with patch(
            "app.api.article.extract_vocabulary",
            side_effect=RuntimeError("spaCy model not installed"),
        ):
            resp = await client.post("/api/article", json={"text": "test", "language_code": "nl"})
        assert resp.status_code == 503
        assert "spaCy model not installed" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Full pipeline integration (requires nl_core_news_sm)
# ---------------------------------------------------------------------------


@requires_nl_model
class TestArticleIntegration:
    """End-to-end tests using the real spaCy pipeline.

    The translator is mocked so tests run offline and produce deterministic
    translations without depending on argostranslate or the dictionary file.
    """

    @pytest.fixture(autouse=True)
    def mock_translator(self):
        with patch("app.services.nlp.translator") as mock:
            mock.translate.return_value = ["[translation]"]
            yield mock

    @pytest.fixture
    async def client(self):
        async with _client() as ac:
            yield ac

    async def test_valid_request_returns_200(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _SHORT_NL, "language_code": "nl"}
        )
        assert resp.status_code == 200

    async def test_response_contains_chunks_key(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _SHORT_NL, "language_code": "nl"}
        )
        assert "chunks" in resp.json()

    async def test_short_article_produces_single_chunk(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _SHORT_NL, "language_code": "nl"}
        )
        assert len(resp.json()["chunks"]) == 1

    async def test_long_article_produces_multiple_chunks(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _LONG_NL, "language_code": "nl"}
        )
        assert len(resp.json()["chunks"]) > 1

    async def test_chunk_has_required_fields(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _SHORT_NL, "language_code": "nl"}
        )
        chunk = resp.json()["chunks"][0]
        assert "index" in chunk
        assert "text" in chunk
        assert "vocabulary" in chunk

    async def test_chunk_index_is_sequential_from_zero(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _LONG_NL, "language_code": "nl"}
        )
        indices = [c["index"] for c in resp.json()["chunks"]]
        assert indices == list[int](range(len(indices)))

    async def test_vocab_items_have_required_fields(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _SHORT_NL, "language_code": "nl"}
        )
        for chunk in resp.json()["chunks"]:
            for item in chunk["vocabulary"]:
                assert "source" in item
                assert "translations" in item
                assert "pos" in item

    async def test_vocab_translations_is_non_empty_list(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _SHORT_NL, "language_code": "nl"}
        )
        for chunk in resp.json()["chunks"]:
            for item in chunk["vocabulary"]:
                assert isinstance(item["translations"], list)
                assert len(item["translations"]) > 0

    async def test_vocab_pos_is_valid_label(self, client: httpx.AsyncClient) -> None:
        valid_labels = {"noun", "verb", "adj", "adv", "adp", "conj"}
        resp = await client.post(
            "/api/article", json={"text": _SHORT_NL, "language_code": "nl"}
        )
        for chunk in resp.json()["chunks"]:
            for item in chunk["vocabulary"]:
                assert item["pos"] in valid_labels

    async def test_chunk_text_is_non_empty_string(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _SHORT_NL, "language_code": "nl"}
        )
        for chunk in resp.json()["chunks"]:
            assert isinstance(chunk["text"], str)
            assert len(chunk["text"]) > 0

    async def test_vocab_sources_are_lowercase(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _SHORT_NL, "language_code": "nl"}
        )
        for chunk in resp.json()["chunks"]:
            for item in chunk["vocabulary"]:
                assert item["source"] == item["source"].lower()

    async def test_no_duplicate_sources_within_a_chunk(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/article", json={"text": _LONG_NL, "language_code": "nl"}
        )
        for chunk in resp.json()["chunks"]:
            sources = [item["source"] for item in chunk["vocabulary"]]
            assert len(sources) == len(set(sources))

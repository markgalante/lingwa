"""Translation service for vocabulary items.

The ``Translator`` protocol decouples the translation backend from the NLP
pipeline. Swap the implementation (e.g. DeepL, Google Translate) by providing
a different object that satisfies the protocol — no changes needed elsewhere.

Translation hierarchy (Phase 1.3.2):
1. ``DictionaryTranslator`` — looks up the lemma in a pre-built Wiktionary
   dictionary (``data/nl_en_dict.json``) and returns multiple translations.
2. Falls back to ``ArgosTranslator`` for lemmas not found in the dictionary.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Protocol

import argostranslate.package
import argostranslate.translate

logger = logging.getLogger(__name__)

_SUPPORTED: frozenset[str] = frozenset({"nl"})

# Resolved at import time; works for both local dev and Docker.
# backend/app/services/translation.py → parent×3 = backend/ → data/nl_en_dict.json
_DEFAULT_DICT_PATH = Path(__file__).parent.parent.parent / "data" / "nl_en_dict.json"


class Translator(Protocol):
    def translate(self, lemma: str, language_code: str) -> list[str]:
        """Return one or more English translations for *lemma*."""
        ...


# ---------------------------------------------------------------------------
# ArgosTranslator
# ---------------------------------------------------------------------------


def _ensure_package(from_code: str, to_code: str) -> None:
    """Download and install the argostranslate package if not already present."""
    installed = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed if lang.code == from_code), None)
    to_lang = next((lang for lang in installed if lang.code == to_code), None)

    if (
        from_lang is not None
        and to_lang is not None
        and from_lang.get_translation(to_lang) is not None
    ):
        return

    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    package = next(
        (pkg for pkg in available if pkg.from_code == from_code and pkg.to_code == to_code),
        None,
    )
    if package is None:
        raise RuntimeError(f"No argostranslate package found for {from_code}→{to_code}")
    argostranslate.package.install_from_path(package.download())


class ArgosTranslator:
    """Offline translator backed by argostranslate with an in-memory cache.

    Package installation is deferred to the first translate() call to avoid
    blocking network I/O at import time. Returns a single-item list per lemma.
    Used as the fallback inside ``DictionaryTranslator``.
    """

    def __init__(self) -> None:
        self._ready = False
        self._cache: dict[tuple[str, str], list[str]] = {}

    def _validate_language_code(self, language_code: str) -> None:
        if language_code not in _SUPPORTED:
            raise ValueError(f"Unsupported language: {language_code!r}")

    def _ensure_ready(self, language_code: str) -> None:
        if not self._ready:
            _ensure_package(language_code, "en")
            self._ready = True

    def translate(self, lemma: str, language_code: str) -> list[str]:
        self._validate_language_code(language_code)
        self._ensure_ready(language_code)
        key = (lemma, language_code)
        if key in self._cache:
            return self._cache[key]
        result = argostranslate.translate.translate(lemma, language_code, "en")
        # argostranslate returns an empty string when it cannot translate a word.
        # Cache the empty list too so untranslatable words don't hit argostranslate
        # on every request.
        translations = [] if not result else [result.lower()]
        self._cache[key] = translations
        return translations


# ---------------------------------------------------------------------------
# DictionaryTranslator
# ---------------------------------------------------------------------------


class DictionaryTranslator:
    """Wiktionary-backed translator with an ArgosTranslator fallback.

    On first use, loads a pre-built ``{lemma: [translations]}`` JSON
    (produced by ``scripts/build_nl_dict.py``). Returns multiple translations
    per lemma when available. Falls back to *fallback* for words not in the
    dictionary.

    If the dictionary file is missing (e.g. during development before the
    build script has been run), every lookup falls back to argostranslate and
    a warning is printed once.
    """

    def __init__(self, fallback: Translator, dict_path: Path | None = None) -> None:
        self._fallback = fallback
        self._dict_path = dict_path or _DEFAULT_DICT_PATH
        self._dict: dict[str, list[str]] | None = None
        self._warned_missing = False
        self._lock = threading.Lock()

    def _ensure_loaded(self) -> None:
        if self._dict is not None:  # fast path — no lock needed after first load
            return
        with self._lock:
            if self._dict is not None:  # re-check: another thread may have loaded it
                return
            if not self._dict_path.exists():
                if not self._warned_missing:
                    # TODO: replace with Sentry capture_message() once error reporting is integrated
                    logger.warning(
                        "DictionaryTranslator: dictionary not found at %s; "
                        "run scripts/build_nl_dict.py to build it. "
                        "Falling back to ArgosTranslator for all lookups.",
                        self._dict_path,
                    )
                    self._warned_missing = True
                self._dict = {}
                return
            try:
                with open(self._dict_path, encoding="utf-8") as f:
                    raw = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                # TODO: replace with Sentry capture_exception() once error reporting is integrated
                logger.warning(
                    "DictionaryTranslator: failed to parse %s (%s). "
                    "Falling back to ArgosTranslator for all lookups.",
                    self._dict_path,
                    exc,
                )
                self._dict = {}
                return
            if not isinstance(raw, dict):
                logger.warning(
                    "DictionaryTranslator: %s must contain a JSON object, got %s. "
                    "Falling back to ArgosTranslator for all lookups.",
                    self._dict_path,
                    type(raw).__name__,
                )
                self._dict = {}
                return
            self._dict = raw

    def translate(self, lemma: str, language_code: str) -> list[str]:
        self._ensure_loaded()
        if self._dict is None:
            raise RuntimeError("DictionaryTranslator._ensure_loaded failed to initialise _dict")
        translations = self._dict.get(lemma)
        if translations is not None:
            return translations
        else:
            return self._fallback.translate(lemma, language_code)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_argos: ArgosTranslator = ArgosTranslator()

# Singleton used throughout the application.
translator: Translator = DictionaryTranslator(fallback=_argos)

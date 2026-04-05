"""Translation service for vocabulary items.

The ``Translator`` protocol decouples the translation backend from the NLP
pipeline. Swap the implementation (e.g. DeepL, Google Translate) by providing
a different object that satisfies the protocol — no changes needed elsewhere.
"""

from typing import Protocol

import argostranslate.package
import argostranslate.translate

_SUPPORTED: frozenset[str] = frozenset({"nl"})


class Translator(Protocol):
    def translate(self, lemma: str, language_code: str) -> list[str]:
        """Return one or more English translations for *lemma*."""
        ...


def _ensure_package(from_code: str, to_code: str) -> None:
    """Download and install the argostranslate package if not already present."""
    installed = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed if lang.code == from_code), None)
    to_lang = next((lang for lang in installed if lang.code == to_code), None)

    if from_lang is not None and to_lang is not None:
        if from_lang.get_translation(to_lang) is not None:
            return

    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    package = next(
        (pkg for pkg in available if pkg.from_code == from_code and pkg.to_code == to_code),
        None,
    )
    if package is None:
        raise RuntimeError(
            f"No argostranslate package found for {from_code}→{to_code}"
        )
    argostranslate.package.install_from_path(package.download())


class ArgosTranslator:
    """Offline translator backed by argostranslate with an in-memory cache.

    Package installation is deferred to the first translate() call to avoid
    blocking network I/O at import time. Returns a single-item list per lemma.
    Phase 1.3.2 will extend this with a dictionary layer that returns multiple
    translations.
    """

    def __init__(self) -> None:
        self._ready = False
        self._cache: dict[tuple[str, str], list[str]] = {}

    def _validate_language_code(self, language_code: str) -> None:
        if language_code not in _SUPPORTED:
            raise ValueError(f"Unsupported language: {language_code!r}")

    def _ensure_ready(self) -> None:
        if not self._ready:
            _ensure_package("nl", "en")
            self._ready = True

    def translate(self, lemma: str, language_code: str) -> list[str]:
        self._validate_language_code(language_code)
        self._ensure_ready()
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


# Singleton used throughout the application.
translator: Translator = ArgosTranslator()

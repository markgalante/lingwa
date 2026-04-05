"""spaCy-based NLP service for vocabulary extraction."""

import functools
from typing import Literal, TypedDict

import spacy
from spacy.language import Language

from app.services.translation import translator

# Maps ISO 639-1 language codes to spaCy model names.
# Add a new entry here (alongside a new LanguageCode literal) to support an additional language.
LANGUAGE_MODELS: dict[str, str] = {
    "nl": "nl_core_news_sm",
}

# Exported so the API layer can use it as a schema type.
LanguageCode = Literal["nl"]

# Only these universal POS tags are extracted as meaningful vocabulary.
MEANINGFUL_POS: set[str] = {"NOUN", "VERB", "ADJ", "ADV", "ADP", "CCONJ", "SCONJ"}

MIN_TOKEN_LENGTH = 3

PosLabel = Literal["noun", "verb", "adj", "adv", "adp", "conj"]

POS_LABEL_MAP: dict[str, PosLabel] = {
    "NOUN": "noun",
    "VERB": "verb",
    "ADJ": "adj",
    "ADV": "adv",
    "ADP": "adp",
    "CCONJ": "conj",
    "SCONJ": "conj",
}


class VocabItem(TypedDict):
    source: str
    translations: list[str]
    pos: PosLabel


@functools.cache
def _load_model(model_name: str) -> Language:
    """Load and cache a spaCy model by name (loaded at most once per process)."""
    return spacy.load(model_name)


def get_model(language_code: str) -> Language:
    """Return the spaCy model for *language_code*, loading it on first call."""
    model_name = LANGUAGE_MODELS.get(language_code)
    if model_name is None:
        supported = ", ".join(LANGUAGE_MODELS)
        raise ValueError(f"Unsupported language '{language_code}'. Supported: {supported}")
    try:
        return _load_model(model_name)
    except OSError as exc:
        raise RuntimeError(
            f"spaCy model '{model_name}' is not installed. "
            f"Run: python -m spacy download {model_name}"
        ) from exc


def extract_vocabulary(text: str, language_code: str) -> list[VocabItem]:
    """Extract unique, lemmatised vocabulary from *text* with translations."""
    nlp = get_model(language_code)
    doc = nlp(text)

    seen: set[str] = set()
    items: list[VocabItem] = []

    for token in doc:
        # Keep only meaningful POS categories.
        if token.pos_ not in MEANINGFUL_POS:
            continue
        # Drop punctuation, spaces, and numbers.
        if token.is_punct or token.is_space or token.like_num:
            continue

        lemma = token.lemma_.strip().lower()

        # Drop short tokens and duplicates.
        if len(lemma) < MIN_TOKEN_LENGTH or lemma in seen:
            continue

        seen.add(lemma)
        # Safe: the MEANINGFUL_POS guard above ensures token.pos_ is always in the map.
        items.append(
            VocabItem(
                source=lemma,
                translations=translator.translate(lemma, language_code),
                pos=POS_LABEL_MAP[token.pos_],
            )
        )

    return items

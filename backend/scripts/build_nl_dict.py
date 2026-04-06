"""Build a compact nl→en translation dictionary from a kaikki.org Wiktionary dump.

Downloads the pre-parsed Dutch Wiktionary JSONL from kaikki.org, extracts
translations from each sense, and writes a compact ``{lemma: [translations]}``
JSON to ``backend/data/nl_en_dict.json`` (or the path given as the first CLI arg).

Run once during Docker image build or local setup:

    python scripts/build_nl_dict.py                        # default output path
    python scripts/build_nl_dict.py /app/data/nl_en_dict.json  # explicit path

The resulting file is generated and should NOT be committed to git.

Checksum verification
---------------------
After each successful download the SHA-256 of the raw source bytes is printed
and written to ``<output>.sha256``.  To lock builds to a known-good file, set
``EXPECTED_SHA256`` below to that hex digest.  Leave it empty to skip the check
(e.g. when intentionally updating to a new upstream snapshot).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

KAIKKI_URL = (
    "https://kaikki.org/dictionary/Dutch/kaikki.org-dictionary-Dutch.jsonl"
)

# SHA-256 of the raw kaikki.org JSONL source, used to detect silent upstream
# changes between builds.
#
# Workflow:
#   1. Run this script once (EXPECTED_SHA256 = ""); the digest is printed and
#      written to data/nl_en_dict.json.sha256.
#   2. Copy that digest here and commit.
#   3. Future builds will fail loudly if the upstream file changes.
#   4. To accept a new upstream snapshot: verify the change is intentional,
#      update the digest below, and commit.
#
# TODO: set this after the first successful build.
EXPECTED_SHA256 = ""

# Translations with more than this many words are likely definitions, not glosses.
MAX_GLOSS_WORDS = 3
# Maximum number of translations stored per lemma.
MAX_TRANSLATIONS = 3

_PAREN_RE = re.compile(r"\([^)]*\)")


def _clean_gloss(raw: str) -> list[str]:
    """Extract clean, short translation strings from a single Wiktionary gloss."""
    # Strip parenthetical qualifiers like "(informal)", "(archaic)", etc.
    cleaned = " ".join(_PAREN_RE.sub("", raw).split()).lower()
    # Some glosses pack multiple translations with commas or semicolons.
    parts = re.split(r"[,;]", cleaned)
    result: list[str] = []
    for part in parts:
        part = part.strip()
        if part and len(part.split()) <= MAX_GLOSS_WORDS:
            result.append(part)
    return result


def _parse_entry(entry: dict) -> tuple[str, list[str]] | None:  # type: ignore[type-arg]
    """Return (lemma, translations) for one JSONL entry, or None to skip."""
    word: str = entry.get("word", "").strip().lower()
    if not word:
        return None

    senses: list[dict] = entry.get("senses", [])  # type: ignore[type-arg]
    translations: list[str] = []
    seen: set[str] = set()

    for sense in senses:
        glosses: list[str] = sense.get("glosses", [])
        if not glosses:
            continue
        # Use only the first (primary) gloss of each sense.
        for t in _clean_gloss(glosses[0]):
            if t not in seen:
                seen.add(t)
                translations.append(t)
        if len(translations) >= MAX_TRANSLATIONS:
            break

    if not translations:
        return None
    return word, translations[:MAX_TRANSLATIONS]


def build_dict(source_url: str) -> tuple[dict[str, list[str]], str]:
    """Stream-download JSONL and build the lemma→translations mapping.

    Returns a ``(dictionary, sha256_hex_digest)`` tuple.  The digest is computed
    over the raw bytes received from the server so it can be compared against a
    pinned value for reproducibility checks.
    """
    if not source_url.startswith("https://"):
        raise ValueError(f"Only HTTPS URLs are allowed, got: {source_url!r}")

    result: dict[str, list[str]] = {}
    hasher = hashlib.sha256()
    print(f"Downloading {source_url} …", flush=True)

    with urllib.request.urlopen(source_url, timeout=120) as response:  # noqa: S310
        for i, raw_line in enumerate(response):
            hasher.update(raw_line)
            if i % 10_000 == 0 and i > 0:
                print(f"  processed {i:,} entries …", flush=True)
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            parsed = _parse_entry(entry)
            if parsed is None:
                continue
            lemma, translations = parsed

            # Merge translations from multiple POS entries for the same lemma.
            existing = result.get(lemma)
            if existing is None:
                result[lemma] = translations
            else:
                seen = set(existing)
                for t in translations:
                    if t not in seen and len(existing) < MAX_TRANSLATIONS:
                        seen.add(t)
                        existing.append(t)

    return result, hasher.hexdigest()


def main() -> None:
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).parent.parent / "data" / "nl_en_dict.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        dictionary, digest = build_dict(KAIKKI_URL)
    except Exception as exc:  # noqa: BLE001
        # Network failures during Docker builds are common (no internet in some
        # CI environments). Exit cleanly so the image build succeeds; the
        # DictionaryTranslator will fall back to ArgosTranslator at runtime.
        print(
            f"[build_nl_dict] WARNING: could not download dictionary ({exc}). "
            "The app will fall back to ArgosTranslator for all translations.",
            flush=True,
        )
        return

    print(f"SHA-256: {digest}", flush=True)

    if EXPECTED_SHA256 and digest != EXPECTED_SHA256:
        raise SystemExit(
            f"[build_nl_dict] FATAL: SHA-256 mismatch.\n"
            f"  expected: {EXPECTED_SHA256}\n"
            f"  got:      {digest}\n"
            "Upstream file has changed. Verify the new snapshot and update "
            "EXPECTED_SHA256 in scripts/build_nl_dict.py."
        )

    print(f"Built dictionary with {len(dictionary):,} entries.", flush=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, separators=(",", ":"))

    output_path.with_suffix(".json.sha256").write_text(digest + "\n", encoding="utf-8")

    size_kb = output_path.stat().st_size // 1024
    print(f"Saved to {output_path} ({size_kb:,} KB).", flush=True)


if __name__ == "__main__":
    main()

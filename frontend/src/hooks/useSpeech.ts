/** Maps ISO 639-1 language codes to BCP-47 locale tags used by the Web Speech API. */
const LOCALE_MAP: Record<string, string> = {
  nl: 'nl-NL',
}

/**
 * Provides text-to-speech playback via the browser's Web Speech API.
 *
 * @param languageCode - ISO 639-1 language code for the target language (e.g. `"nl"`).
 * @returns
 *   - `speak(word)` — pronounces the given word in the target language.
 *     Cancels any in-progress utterance before starting a new one.
 *     No-ops silently when `speechSynthesis` is unavailable or the language code is unsupported.
 *   - `isSupported` — `true` when the browser exposes `window.speechSynthesis`.
 *     Use this to conditionally render speaker icons or other TTS-dependent UI.
 */
export function useSpeech(languageCode: string) {
  const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window

  function speak(word: string) {
    if (!isSupported) return

    const locale = LOCALE_MAP[languageCode]
    if (!locale) return

    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(word)
    utterance.lang = locale
    window.speechSynthesis.speak(utterance)
  }

  return { speak, isSupported }
}

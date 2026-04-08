const LOCALE_MAP: Record<string, string> = {
  nl: 'nl-NL',
}

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

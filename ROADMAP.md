# Lingwa – Dutch Vocab Matching Quiz App: Roadmap

> **Goal**: A web app that helps users learn Dutch vocabulary through an adaptive matching quiz, followed by reading an interactive article with hover-tooltips and pronunciation support.

---

## Phase 0 – Foundation (Week 1)

**Goal**: Establish the project structure and developer tooling.

- [ ] Initialise a monorepo (e.g. with a `frontend/` and `backend/` directory at the repo root)
- [ ] Add `README.md` setup instructions (prerequisites, how to run locally)
- [ ] Configure `frontend/` with **Create React App** or **Vite** (React + TypeScript)
- [ ] Configure `backend/` as a **FastAPI** project with a `pyproject.toml` / `requirements.txt`
- [ ] Add **Tailwind CSS** to the frontend
- [ ] Set up **ESLint** + **Prettier** for the frontend
- [ ] Set up **Ruff** / **Black** + **mypy** for the backend
- [ ] Add a `.gitignore` covering `node_modules/`, Python virtual environments, and build artefacts
- [ ] Add a basic `docker-compose.yml` so both services can be started with one command

---

## Phase 1 – Backend: NLP & Vocabulary Extraction (Weeks 2–3)

**Goal**: Accept a pasted Dutch article and return structured vocabulary data.

### 1.1 – FastAPI skeleton
- [ ] `POST /api/article` – accepts raw Dutch text, returns extracted vocabulary
- [ ] `GET /api/health` – simple liveness check
- [ ] Add CORS middleware so the React dev server can call the API

### 1.2 – spaCy integration
- [ ] Install `spacy` and download the Dutch model (`nl_core_news_sm`)
- [ ] Extract **unique, meaningful tokens**: nouns, verbs, adjectives (POS filtering)
- [ ] Filter out stop-words, punctuation, numbers, and short tokens (< 3 chars)
- [ ] Lemmatise each token so inflected forms map to a single base word
- [ ] Return a list of `{ dutch: str, english: str, pos: str }` objects

### 1.3 – Translation
- [ ] Integrate a free/open-source translation layer (options: `argostranslate`, `Helsinki-NLP` via HuggingFace, or a local dictionary file)
- [ ] Cache translations in-memory (or SQLite) to avoid re-translating the same word

### 1.4 – Chunking logic
- [ ] Divide the article text into **chunks of 10 words** (by token index, not character count)
- [ ] Group vocabulary by chunk so the quiz can be scoped per chunk
- [ ] Return chunk metadata alongside the vocabulary list

### 1.5 – Tests
- [ ] Unit tests for the POS filter and lemmatiser
- [ ] Unit tests for the chunking helper
- [ ] Integration test for `POST /api/article` with a short fixture article

---

## Phase 2 – Backend: Text-to-Speech (Week 4)

**Goal**: Return audio pronunciation for individual Dutch words.

- [ ] Evaluate **Coqui TTS** (`tts` Python package) with a Dutch voice model
- [ ] `GET /api/tts/{word}` – streams back a WAV/MP3 clip for the given word
- [ ] Cache generated audio files on disk (keyed by word) to avoid re-synthesis
- [ ] Add a fallback to the **Web Speech API** (`SpeechSynthesis`) on the frontend if the backend TTS endpoint is unavailable
- [ ] Document how to download the Coqui Dutch model in the README

---

## Phase 3 – Frontend: Article Input (Week 5)

**Goal**: Provide a clean UI for pasting an article and triggering processing.

- [ ] `ArticleInput` component: `<textarea>` with a placeholder and a "Start Learning" button
- [ ] Show a loading spinner while the API processes the article
- [ ] Display a friendly error state if the API call fails
- [ ] Validate that the textarea is not empty before submitting
- [ ] Store the processed article data in React context (or a lightweight state manager like Zustand)

---

## Phase 4 – Frontend: Matching Quiz (Weeks 6–7)

**Goal**: Interactive, adaptive vocabulary matching game.

### 4.1 – Core quiz UI
- [ ] `QuizBoard` component: 5 Dutch words on the left, 5 shuffled English translations on the right
- [ ] Click-to-select logic: first click selects a Dutch word, second click selects an English word
- [ ] Highlight a **correct pair in green** and lock it (non-interactive)
- [ ] Highlight an **incorrect pair in red** briefly, then reset the selection
- [ ] Show a progress bar: "X / Y words mastered this chunk"

### 4.2 – Adaptive retesting
- [ ] Track which words were answered incorrectly in each round
- [ ] After completing a 5-word set, requeue missed words into the next set
- [ ] Only advance to the next chunk once all words in the current chunk are mastered
- [ ] Persist mastery state in `localStorage` so users can resume a session

### 4.3 – Transitions
- [ ] Animate completed pairs sliding off the board (CSS transition or Framer Motion)
- [ ] Display a brief "Well done!" screen between chunks

---

## Phase 5 – Frontend: Interactive Article View (Week 8)

**Goal**: Display the article with clickable, tooltip-enabled words.

- [ ] `ArticleView` component renders the article word-by-word as `<span>` elements
- [ ] On **hover**: show a tooltip with the English translation
- [ ] On **click**: play the TTS audio clip via the backend `/api/tts/{word}` endpoint
- [ ] "Add to review list" button inside the tooltip; maintain a `forgottenWords` list in state
- [ ] `ForgottenWordsList` sidebar/panel showing all added words with their translations
- [ ] Allow users to re-quiz themselves on forgotten words at any time
- [ ] Highlight words the user previously answered incorrectly during the quiz

---

## Phase 6 – UI / UX Polish (Week 9)

**Goal**: Make the app pleasant and accessible to use.

- [ ] Responsive layout (mobile-first, tested down to 375 px width)
- [ ] Dark-mode support via Tailwind's `dark:` variant
- [ ] Accessible keyboard navigation for the quiz (Tab to focus, Enter/Space to select)
- [ ] ARIA labels on all interactive elements
- [ ] Add a **favicon** and a page title (`<title>Lingwa</title>`)
- [ ] Smooth page transitions between Article Input → Quiz → Article View
- [ ] User-facing loading and empty states for every async operation

---

## Phase 7 – Integration, QA & Documentation (Week 10)

**Goal**: Production-ready prototype with clear docs.

- [ ] End-to-end test with a real Dutch article (happy path + edge cases: very short article, all stop-words, duplicate words)
- [ ] Fix any integration issues between frontend and backend
- [ ] Write a `CONTRIBUTING.md` with branch naming, commit style, and PR guidelines
- [ ] Expand `README.md`:  architecture diagram, environment variables, deployment notes
- [ ] Add GitHub Actions CI pipeline: lint + test on every PR (frontend and backend)
- [ ] Record a short demo screencast / GIF for the README

---

## Phase 8 – Optional Enhancements (Backlog)

> Features to consider after the core prototype is stable.

- [ ] **User accounts**: save progress across devices (PostgreSQL + JWT auth)
- [ ] **Multiple languages**: extend the NLP pipeline beyond Dutch (French, German, Spanish)
- [ ] **Spaced-repetition algorithm** (SM-2) to schedule word reviews over days/weeks
- [ ] **Difficulty levels**: beginner filters out verbs; advanced includes all POS
- [ ] **Browser extension**: highlight and quiz words directly on any webpage
- [ ] **Offline support**: PWA manifest + service worker for offline TTS cache
- [ ] **Analytics dashboard**: track accuracy over time with charts

---

## Milestone Summary

| Phase | Deliverable | Target Week |
|-------|-------------|-------------|
| 0 | Project skeleton & tooling | 1 |
| 1 | NLP vocabulary extraction API | 2–3 |
| 2 | Text-to-speech endpoint | 4 |
| 3 | Article input UI | 5 |
| 4 | Matching quiz with adaptive retesting | 6–7 |
| 5 | Interactive article view | 8 |
| 6 | UI/UX polish & accessibility | 9 |
| 7 | Integration, QA & docs | 10 |
| 8 | Optional enhancements | Post-launch |

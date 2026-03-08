# Lingwa – Vocab Matching Quiz App: Roadmap

> **Goal**: A web app that helps users learn vocabulary in a target language through an adaptive matching quiz, followed by reading an interactive article with hover-tooltips and pronunciation support. The initial version targets Dutch, with additional languages planned.

---

## Phase 0 – Foundation & Authentication

**Goal**: Establish the project structure, developer tooling, and the user authentication layer.

### 0.1 – Project scaffold
- [x] Initialise a monorepo (e.g. with a `frontend/` and `backend/` directory at the repo root)
- [x] Add `README.md` setup instructions (prerequisites, how to run locally)
- [x] Configure `frontend/` with **Vite** (React + TypeScript)
- [x] Configure `backend/` as a **FastAPI** project with a `pyproject.toml` / `requirements.txt`
- [x] Add **Tailwind CSS** to the frontend
- [x] Set up **ESLint** + **Prettier** for the frontend
- [x] Set up **Ruff** / **mypy** for the backend
- [x] Add a `.gitignore` covering `node_modules/`, Python virtual environments, and build artefacts
- [x] Add a basic `docker-compose.yml` so both services can be started with one command

### 0.2 – Data schemas ✓

**User** (stored in the database)

| Field | Type | Notes |
|---|---|---|
| `id` | UUID v7 | Time-sortable primary key |
| `email` | string (unique) | Used for login and verification |
| `name` | string (nullable) | Display name |
| `hashed_password` | string (nullable) | `null` until the user sets a password; always `null` for Google-only accounts |
| `is_verified` | boolean | `false` until the e-mail verification link is clicked |
| `verification_token` | string (nullable) | One-time URL-safe token e-mailed on signup; cleared after use |
| `verification_token_expires` | datetime | Expiry for the verification token (e.g. 24 hours) |
| `google_id` | string (nullable) | Google OAuth `sub` claim; `null` for email-only accounts |
| `avatar_url` | string (nullable) | Profile picture URL, populated from Google OAuth |
| `language_ids` | list of UUID v7 | References to languages the user is studying |
| `created_at` | datetime | Row creation timestamp (UTC) |
| `updated_at` | datetime | Last update timestamp (UTC) |

**Language** (seed data + user-selectable)

| Field | Type | Notes |
|---|---|---|
| `id` | UUID v7 | Time-sortable primary key |
| `name` | string (unique) | Full language name, e.g. `"Dutch"` |
| `code` | string (unique) | ISO 639-1 two-letter code, e.g. `"nl"` |
| `created_at` | datetime | Row creation timestamp (UTC) |

### 0.3 – Authentication flows

#### Email sign-up (3-step flow)
1. **Step 1 – Register** (`POST /auth/signup`): user submits their e-mail (and optionally a display name). The backend creates an unverified account, generates a one-time verification token, and sends a verification e-mail.
2. **Step 2 – Verify e-mail** (`POST /auth/verify-email`): user clicks the link in their inbox (or pastes the token). The backend validates the token and its expiry.
3. **Step 3 – Set password** (`POST /auth/set-password`): user chooses a password. The backend hashes it, marks the account as verified, clears the token, and issues a JWT access token.

#### Google OAuth sign-up / login
1. Frontend redirects to `GET /auth/google` → backend redirects user to Google consent screen.
2. Google calls `GET /auth/google/callback?code=…` → backend exchanges the code for an access token, fetches the user's profile (email, name, avatar), upserts the user record (linking by Google ID or e-mail), marks it verified, and issues a JWT.

#### Email login (returning users)
- `POST /auth/login`: validates e-mail + password, returns a JWT.

### 0.4 – Frontend auth screens ✓
- [x] **Google OAuth**: "Continue with Google" button → full OAuth flow → JWT issued
- [x] **Sign-up page**: e-mail input → verification email sent → check-your-inbox screen
- [x] **Login page**: e-mail + password for returning users

### 0.5 – Email provider integration ✓
- [x] Choose and configure an email provider (Resend)
- [x] Add provider credentials to `.env` and `config.py`
- [x] Create a `send_email` utility in the backend

### 0.6 – Email verification flow ✓
- [x] `POST /auth/register`: create unverified account (email only), generate token, send verification e-mail
- [x] **Check-your-inbox page**: shown after signup
- [x] **Verify & complete-registration page**: token read from link; password + name form to complete signup (`POST /auth/complete-registration`)

### 0.7 – Password recovery flow
> Requires Phase 0.5 to be complete.

#### Backend
- [x] `POST /auth/forgot-password`: accepts an e-mail address; if the account exists and has a password (i.e. is not Google-only), generate a short-lived reset token (e.g. 1 hour), store its hash in the database, and send a password-reset e-mail with a link containing the token
- [x] `POST /auth/reset-password`: accepts the reset token and a new password; validates the token (existence, hash match, expiry), hashes the new password, saves it, and invalidates the token
- [x] Add `password_reset_token` (nullable string) and `password_reset_token_expires` (nullable datetime) fields to the `User` model and a corresponding Alembic migration

#### Frontend
- [x] **Forgot-password page** (`/forgot-password`): e-mail input + submit button; on success show a "check your inbox" confirmation message
- [x] **Reset-password page** (`/reset-password?token=…`): reads the token from the query string; shows a new-password + confirm-password form; on success redirects to login with a success toast
- [x] Add a "Forgot password?" link on the login page pointing to `/forgot-password`
- [x] Handle error states: invalid/expired token (prompt user to request a new link), Google-only account (inform user no password is set)

---

## Phase 1 – Backend: NLP & Vocabulary Extraction

**Goal**: Accept a pasted article in the user's target language and return structured vocabulary data.

### 1.1 – FastAPI skeleton
- [ ] `POST /api/article` – accepts raw text and a `language_code`, returns extracted vocabulary
- [ ] `GET /api/health` – simple liveness check
- [ ] Add CORS middleware so the React dev server can call the API

### 1.2 – spaCy integration
- [ ] Install `spacy`; download the language model for the active language (e.g. `nl_core_news_sm` for Dutch)
- [ ] Load models on demand per language so adding a new language only requires pointing to its spaCy model
- [ ] Extract **unique, meaningful tokens**: nouns, verbs, adjectives (POS filtering)
- [ ] Filter out stop-words, punctuation, numbers, and short tokens (< 3 chars)
- [ ] Lemmatise each token so inflected forms map to a single base word
- [ ] Return a list of `{ source: str, translation: str, pos: str }` objects

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

## Phase 2 – Backend: Text-to-Speech

**Goal**: Return audio pronunciation for individual words in the user's target language.

- [ ] Evaluate **Coqui TTS** (`tts` Python package) with voice models for each supported language; start with Dutch
- [ ] `GET /api/tts/{language_code}/{word}` – streams back a WAV/MP3 clip for the given word
- [ ] Cache generated audio files on disk (keyed by language + word) to avoid re-synthesis
- [ ] Add a fallback to the **Web Speech API** (`SpeechSynthesis`) on the frontend if the backend TTS endpoint is unavailable
- [ ] Document how to download Coqui voice models for each supported language in the README

---

## Phase 3 – Frontend: Article Input

**Goal**: Provide a clean UI for pasting an article and triggering processing.

- [ ] `ArticleInput` component: `<textarea>` with a placeholder and a "Start Learning" button
- [ ] Show a loading spinner while the API processes the article
- [ ] Display a friendly error state if the API call fails
- [ ] Validate that the textarea is not empty before submitting
- [ ] Store the processed article data in React context (or a lightweight state manager like Zustand)

---

## Phase 4 – Frontend: Matching Quiz

**Goal**: Interactive, adaptive vocabulary matching game.

### 4.1 – Core quiz UI
- [ ] `QuizBoard` component: 5 target-language words on the left, 5 shuffled translations on the right
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

## Phase 5 – Frontend: Interactive Article View

**Goal**: Display the article with clickable, tooltip-enabled words.

- [ ] `ArticleView` component renders the article word-by-word as `<span>` elements
- [ ] On **hover**: show a tooltip with the English translation
- [ ] On **click**: play the TTS audio clip via the backend `/api/tts/{word}` endpoint
- [ ] "Add to review list" button inside the tooltip; maintain a `forgottenWords` list in state
- [ ] `ForgottenWordsList` sidebar/panel showing all added words with their translations
- [ ] Allow users to re-quiz themselves on forgotten words at any time
- [ ] Highlight words the user previously answered incorrectly during the quiz

---

## Phase 6 – UI / UX Polish

**Goal**: Make the app pleasant and accessible to use.

- [ ] Responsive layout (mobile-first, tested down to 375 px width)
- [ ] Dark-mode support via Tailwind's `dark:` variant
- [ ] Accessible keyboard navigation for the quiz (Tab to focus, Enter/Space to select)
- [ ] ARIA labels on all interactive elements
- [ ] Add a **favicon** and a page title (`<title>Lingwa</title>`)
- [ ] Smooth page transitions between Article Input → Quiz → Article View
- [ ] User-facing loading and empty states for every async operation

---

## Phase 7 – Integration, QA & Documentation

**Goal**: Production-ready prototype with clear docs.

- [ ] End-to-end test with a real article in the target language (happy path + edge cases: very short article, all stop-words, duplicate words)
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

| Phase | Deliverable |
|-------|-------------|
| 0 | Project skeleton, tooling & authentication |
| 1 | NLP vocabulary extraction API |
| 2 | Text-to-speech endpoint |
| 3 | Article input UI |
| 4 | Matching quiz with adaptive retesting |
| 5 | Interactive article view |
| 6 | UI/UX polish & accessibility |
| 7 | Integration, QA & docs |
| 8 | Optional enhancements |

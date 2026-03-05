# Lingwa

> **Learning vocab that's meaningful to you.**

Lingwa is a web app that helps users learn vocabulary in a target language through an adaptive matching quiz, followed by reading an interactive article with hover-tooltips and pronunciation support. The initial version targets Dutch, with additional languages planned.

---

## Tech stack (planned)

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript (Vite), Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL (SQLite for local dev) |
| Auth | Email/password + Google OAuth, JWT |
| NLP | spaCy (per-language models; starting with Dutch `nl_core_news_sm`) |
| TTS | Coqui TTS (per-language voice models) |

---

## Phase 0 – Authentication (planned)

The first milestone sets up the project scaffold and the user authentication layer.

### Sign-up flows

**Email sign-up**
1. User enters their e-mail address → receives a verification e-mail with a one-time link.
2. User clicks the link → verified; prompted to choose a password.
3. Backend issues a JWT access token; user is logged in.

**Google OAuth**
1. User clicks "Continue with Google" → redirected to Google consent screen.
2. On callback, backend upserts the user (linked by Google ID or e-mail), marks them verified, and issues a JWT.

### Data schemas

**User**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID v7 | Time-sortable primary key |
| `email` | string | Unique; used for login and verification |
| `name` | string | Display name (optional) |
| `hashed_password` | string | `null` for Google-only accounts |
| `is_verified` | boolean | Set to `true` after e-mail confirmation |
| `google_id` | string | Google OAuth subject; `null` for email-only accounts |
| `avatar_url` | string | Populated from Google profile (optional) |
| `language_ids` | UUID v7[] | Languages the user is currently studying |
| `created_at` | datetime | UTC |
| `updated_at` | datetime | UTC |

**Language**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID v7 | Time-sortable primary key |
| `name` | string | Full name, e.g. `"Dutch"` |
| `code` | string | ISO 639-1, e.g. `"nl"` |
| `created_at` | datetime | UTC |

See [ROADMAP.md](./ROADMAP.md) for the full development plan.

---

## Getting started

> Setup instructions will be added once the project scaffold is in place (Phase 0).

# Lingwa – Architecture

## Overview

Lingwa is a monorepo web application consisting of a React frontend and a FastAPI backend, connected to a PostgreSQL database.

```
┌─────────────────────────────────────────────────────────────┐
│                        Client (Browser)                      │
│                                                             │
│   React 19 + TypeScript + Vite                              │
│   Tailwind CSS v4  │  ESLint + Prettier                     │
│   localhost:5173                                            │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP / REST (JSON)
                            │ JWT in Authorization header
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│                                                             │
│   Python 3.11 + FastAPI + SQLAlchemy 2 (async)             │
│   Alembic migrations  │  Pydantic v2 schemas               │
│   Uvicorn ASGI server                                       │
│   localhost:8000                                            │
│                                                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │  /auth   │  │ /api/    │  │ /api/    │  │ /api/    │  │
│   │  routes  │  │ article  │  │   tts    │  │  health  │  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │ asyncpg (async driver)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      PostgreSQL 16                           │
│                                                             │
│   Tables: users, languages, user_languages                  │
│   localhost:5432  /  db:5432 (Docker)                       │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
lingwa/
├── frontend/                   # Vite + React 19 + TypeScript
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css           # Tailwind v4 import
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/                    # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── main.py             # FastAPI app instance, CORS, router mounts, Swagger config
│   │   ├── api/
│   │   │   ├── auth.py         # /auth/* routes
│   │   │   └── deps.py         # get_current_user dependency
│   │   ├── core/
│   │   │   ├── config.py       # Pydantic-settings (reads .env)
│   │   │   ├── database.py     # Async engine + session factory
│   │   │   └── security.py     # JWT creation, password hashing/verification
│   │   ├── crud/
│   │   │   └── user.py         # CRUD helpers for the User model
│   │   ├── models/
│   │   │   ├── base.py         # DeclarativeBase + uuid7() helper
│   │   │   ├── user.py         # User ORM model + UserLanguage association table
│   │   │   └── language.py     # Language ORM model
│   │   ├── schemas/
│   │   │   ├── user.py         # UserRegister / UserRead / CompleteRegistration / TokenResponse
│   │   │   └── language.py     # LanguageCreate / LanguageRead
│   │   └── services/
│   │       └── email.py        # Resend email service (send_verification_email)
│   ├── alembic/                # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/           # Auto-generated migration files
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
│
├── docs/                       # Project documentation
│   ├── architecture.md         # This file
│   └── database.md             # Database schema reference
│
├── docker-compose.yml          # PostgreSQL + backend + frontend
├── README.md
└── ROADMAP.md
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend framework | React 19 + TypeScript |
| Frontend build | Vite 7 |
| Styling | Tailwind CSS v4 |
| Backend framework | FastAPI 0.115+ |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy 2 (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Database | PostgreSQL 16 |
| Async DB driver | asyncpg |
| Auth tokens | JWT (python-jose) |
| Password hashing | passlib[bcrypt] |
| NLP (Phase 1) | spaCy |
| TTS (Phase 2) | Coqui TTS |

## API Documentation

FastAPI serves interactive docs automatically (no extra dependencies required):

| UI | URL |
|---|---|
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |

## Authentication Flow (Phase 0.3)

### Email sign-up (3-step)
1. `POST /auth/register` — create unverified user, send verification email
2. `GET /auth/check-verification-token?token=…` — validate token expiry (frontend checks before showing password form)
3. `POST /auth/complete-registration` — set name + password, mark verified, issue JWT

### Resend verification
- `POST /auth/resend-verification` — re-issue token and resend email (handles expired links)

### Google OAuth
1. `GET /auth/google/login` — redirect to Google consent screen
2. `GET /auth/google/callback?code=…` — exchange code, upsert/create user, redirect to frontend with JWT

### Email login
- `POST /auth/login` — validate credentials, return JWT

### Current user
- `GET /auth/me` — return authenticated user profile (requires `Authorization: Bearer <token>`)

## Configuration

All runtime configuration is loaded from environment variables (via `.env` file in development). See `backend/.env.example` for the full list.

Key variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://lingwa:lingwa@localhost:5432/lingwa` | Async PostgreSQL connection string |
| `SECRET_KEY` | *(must be set in prod)* | HMAC key for JWT signing |
| `GOOGLE_CLIENT_ID` | — | Google OAuth app credential |
| `GOOGLE_CLIENT_SECRET` | — | Google OAuth app credential |
| `FRONTEND_URL` | `http://localhost:5173` | Used for CORS and redirect URIs |

## Running Locally

```bash
# Start everything with Docker
docker compose up

# Or run services individually:
cd frontend && npm run dev        # http://localhost:5173
cd backend && uvicorn app.main:app --reload  # http://localhost:8000

# Apply migrations
cd backend && alembic upgrade head
```

# Lingwa – Database Schema

## Overview

The database uses **PostgreSQL 16**. All primary keys are **UUID v7** (time-sortable, lexicographically ordered by creation time). Migrations are managed with **Alembic**.

## Entity Relationship Diagram

```
┌──────────────────────────────────────────────┐
│                    users                      │
├──────────────────────────────────────────────┤
│ id                      UUID v7  PK          │
│ email                   VARCHAR(320)  UNIQUE │
│ name                    VARCHAR(200)  NULL   │
│ hashed_password         VARCHAR(255)  NULL   │
│ is_verified             BOOLEAN              │
│ verification_token      VARCHAR(255)  NULL   │
│ verification_token_expires  TIMESTAMPTZ NULL │
│ google_id               VARCHAR(255)  NULL   │
│ avatar_url              VARCHAR(2048) NULL   │
│ created_at              TIMESTAMPTZ          │
│ updated_at              TIMESTAMPTZ          │
└──────────────────┬───────────────────────────┘
                   │ M
                   │
           ┌───────┴──────────┐
           │  user_languages  │  (association table)
           ├──────────────────┤
           │ user_id     UUID FK → users.id     │
           │ language_id UUID FK → languages.id │
           └───────┬──────────┘
                   │ M
                   │ 1
┌──────────────────┴───────────────────────────┐
│                  languages                    │
├──────────────────────────────────────────────┤
│ id          UUID v7  PK                      │
│ name        VARCHAR(100)  UNIQUE             │
│ code        VARCHAR(10)   UNIQUE  INDEX      │
│ created_at  TIMESTAMPTZ                      │
└──────────────────────────────────────────────┘
```

## Tables

### `users`

Stores registered user accounts. Supports both email/password and Google OAuth sign-in; these can be linked on the same account via a shared email address.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK | UUID v7 (time-sortable) |
| `email` | `VARCHAR(320)` | NOT NULL, UNIQUE, INDEX | Login identifier and verification target |
| `name` | `VARCHAR(200)` | NULL | Display name (optional) |
| `hashed_password` | `VARCHAR(255)` | NULL | bcrypt hash; `NULL` for Google-only accounts |
| `is_verified` | `BOOLEAN` | NOT NULL, default `false` | `true` once email is verified |
| `verification_token` | `VARCHAR(255)` | NULL | URL-safe one-time token; cleared after use |
| `verification_token_expires` | `TIMESTAMPTZ` | NULL | Token expiry (24 h window) |
| `google_id` | `VARCHAR(255)` | NULL, UNIQUE | Google OAuth `sub` claim |
| `avatar_url` | `VARCHAR(2048)` | NULL | Profile picture from Google |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, server default `now()` | Row creation time (UTC) |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, server default `now()`, on-update `now()` | Last modification time (UTC) |

**Notes:**
- `hashed_password` is `NULL` for accounts created via Google OAuth that have never set a password.
- `verification_token` is cleared (set to `NULL`) after the user completes email verification and sets a password.
- A user can have both `google_id` and `hashed_password` set if they later link accounts.

### `languages`

Seed/reference data for supported target languages.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK | UUID v7 (time-sortable) |
| `name` | `VARCHAR(100)` | NOT NULL, UNIQUE | Full language name, e.g. `"Dutch"` |
| `code` | `VARCHAR(10)` | NOT NULL, UNIQUE, INDEX | ISO 639-1 code, e.g. `"nl"` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, server default `now()` | Row creation time (UTC) |

**Seed data (initial release):**

| name | code |
|---|---|
| Dutch | nl |

### `user_languages`

Association table implementing the many-to-many relationship between `users` and `languages`.

| Column | Type | Constraints |
|---|---|---|
| `user_id` | `UUID` | PK, FK → `users.id` ON DELETE CASCADE |
| `language_id` | `UUID` | PK, FK → `languages.id` ON DELETE CASCADE |

## Migrations

Migrations are managed with Alembic and stored in `backend/alembic/versions/`.

```bash
# Apply all pending migrations
cd backend
alembic upgrade head

# Create a new migration after changing models
alembic revision --autogenerate -m "describe your change"

# Roll back one step
alembic downgrade -1
```

The Alembic `env.py` uses the async SQLAlchemy engine and reads `DATABASE_URL` from the app settings, so migrations always target the same database as the running application.

## UUID v7

Primary keys use **UUID v7** rather than UUID v4 or sequential integers because:

- **Time-sortable**: rows are naturally ordered by creation time without a separate `created_at` index on the PK.
- **Globally unique**: safe for distributed inserts without a central sequence.
- **Opaque**: unlike auto-increment integers, UUIDs do not leak row counts to clients.

On Python 3.13+ `uuid.uuid7()` is used natively. On Python 3.11/3.12 the `uuid6` package provides an identical implementation.

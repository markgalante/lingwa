---
name: frontend-architecture
description: Frontend file and directory structure conventions for the Lingwa project. Use when creating new pages, components, hooks, or context — or when deciding where a new file belongs.
---

# Frontend Architecture

> **Keep this file up to date.** Whenever you add, move, or remove files that affect the structure below, update this document to reflect the current state of the tree.

## Directory structure

```
frontend/src/
├── api/                        # Fetch utilities and API client
├── components/                 # Shared UI components, grouped by feature
│   └── auth/                   # Auth-related components (ProtectedRoute, etc.)
├── context/                    # React context providers, grouped by feature
│   └── auth/                   # AuthContext.tsx (provider) + useAuth.ts (hook)
├── features/                   # Feature slices — pages and logic grouped by domain
│   ├── auth/                   # Login, OAuth callback
│   └── main/                   # Dashboard and core authenticated screens
├── hooks/                      # Shared hooks used across multiple features
└── App.tsx                     # Router and top-level providers
```

## Grouping rules

### `features/`
Pages live inside their feature directory, not in a separate `pages/` layer. A feature directory owns its page components, hooks, and types. Add a new feature directory for each distinct domain area (e.g. `features/quiz/`, `features/reader/`).

| Feature | Purpose |
|---|---|
| `features/auth/` | Login, OAuth callback, and unauthenticated screens |
| `features/main/` | Dashboard and core authenticated screens |

`App.tsx` remains the single source of routing truth — import page components from features directly. The route-config pattern (each feature exporting its own `<Route>` elements) is not used unless the route list becomes unwieldy.

### `context/`
Group by feature. Each feature subdirectory contains:
- A `*Context.tsx` file — exports the context object and types only, no hooks
- A `use*.ts` file — exports the hook(s) for that context

This separation is required for React fast refresh (files mixing provider exports and function exports break HMR).

### `components/`
Group by the feature they serve. Truly generic UI primitives (buttons, modals) can live at the top level of `components/`.

### `hooks/`
Hooks that are shared across multiple unrelated features live here. Feature-scoped hooks live alongside their feature in `features/<name>/` or `context/<name>/`.

## Naming

- Files and components: PascalCase (e.g. `DashboardPage.tsx`)
- Hooks: camelCase prefixed with `use` (e.g. `useAuth.ts`)
- Context files: PascalCase with `Context` suffix (e.g. `AuthContext.tsx`)

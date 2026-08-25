# Lab Platform

A self-hosted, KodeKloud-style interactive coding lab platform. Phase 0:
product flow end-to-end with a local-disk workspace per user — no
containers yet.

Built in phases; this is **Phase 0**. See the phase plan for what's next.

## Architecture

- **`pylabs/`** — the existing Python lab harness (`Ctx`, `Check`, `Task`)
  and 21 tasks across 5 phases, copied in unchanged. Not modified by any
  phase of this project — the backend imports it directly.
- **`backend/`** — FastAPI. Imports `pylabs` directly, exposes the task /
  file / auth API, stores users & progress in Postgres. Each user's
  workspace files live on local disk under `./data/workspace/{user_id}/`.
- **`frontend/`** — Next.js 15 (App Router) + TypeScript + Tailwind. Dark
  theme, indigo/green/red throughout. Monaco editor for code, a mocked
  terminal panel (real terminal lands in Phase 1).

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (for Postgres via `docker compose`) — or a local Postgres 16 you
  point `DATABASE_URL` at instead.

## Run it locally

**1. Start Postgres**

```bash
docker compose up -d
```

**2. Backend**

```bash
cd backend
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.example .env      # defaults match docker-compose.yml
./.venv/bin/uvicorn app.main:app --reload --port 8000
```

On first startup it creates the Postgres tables and seeds an admin user
(`ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env`, defaults to
`admin@example.com` / `changeme123`).

**3. Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** — Next.js proxies `/api/*` to the backend
(see `frontend/next.config.mjs`), so cookies stay same-origin.

## Verify Phase 0 works end to end

1. Go to `http://localhost:3000`, sign in with the seeded admin
   credentials.
2. You land on `/lab` with the task list, phase badge, and progress dots
   on the left, and a file tree + Monaco editor + mocked terminal on the
   right.
3. Pick task **p1-01** (or whatever's current) — its starter file
   materialises in your workspace and opens in the editor.
4. Edit the code (e.g. leave the bug in, hit **Check** — see the red
   checklist with the exact `CheckFailed` message from pylabs). Fix it,
   hit **Check** again — checklist turns green, **Next** unlocks, and the
   progress dot fills in.
5. Click a task with no starter files (e.g. **p4-01**, a terminal-only
   task) — the right pane switches to a full-width mocked terminal panel
   instead of the editor (real shell execution is Phase 1).
6. Confirm progress persists: refresh the page, or check
   `GET /api/tasks` — your pass/fail state survives (it's in Postgres).

## Repo layout

```
pylabs/            # unmodified: harness.py, labs/phase{1..5}.py, cli.py
backend/
  app/
    main.py        # FastAPI app, CORS, startup seeding
    config.py      # env-driven config
    db.py          # SQLAlchemy engine/session
    models.py      # User, Session, TaskProgress
    security.py    # bcrypt + session tokens
    deps.py        # get_current_user
    pylabs_bridge.py  # the only place that touches pylabs internals
    schemas.py
    routes/
      auth.py
      tasks.py
      files.py
frontend/
  app/
    login/page.tsx
    lab/page.tsx    # the main authenticated view
  components/       # TopBar, ProgressDots, Checklist, Editor, Terminal, ...
  lib/               # api.ts, types.ts
data/workspace/      # per-user files on disk (gitignored)
docker-compose.yml   # Postgres for local dev
```

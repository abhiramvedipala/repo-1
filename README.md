# Lab Platform

A self-hosted, KodeKloud-style interactive coding lab platform.

Built in phases. This is **Phase 1**: a real terminal, still single-host
with no container isolation (that's Phase 2). See the phase plan for
what's next.

## Architecture

- **`pylabs/`** — the existing Python lab harness (`Ctx`, `Check`, `Task`)
  and 21 tasks across 5 phases, copied in unchanged. Not modified by any
  phase of this project — the backend imports it directly.
- **`backend/`** — FastAPI. Imports `pylabs` directly, exposes the task /
  file / auth API, stores users & progress in Postgres. Each user's
  workspace files live on local disk under `./data/workspace/{user_id}/`.
  A WebSocket endpoint (`/ws/terminal`) spawns a real PTY-attached shell
  per connection, scoped to that user's workspace dir.
- **`frontend/`** — Next.js 15 (App Router) + TypeScript + Tailwind. Dark
  theme, indigo/green/red throughout. Monaco editor for code, xterm.js for
  a real terminal connected straight to the backend's WebSocket.

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
(see `frontend/next.config.mjs`), so cookies stay same-origin. The
terminal's WebSocket connects straight to the backend
(`ws://localhost:8000/ws/terminal` by default — override with
`NEXT_PUBLIC_TERMINAL_WS_URL` or `NEXT_PUBLIC_BACKEND_PORT` in
`frontend/.env.local`); this works because the session cookie is
host-only and browsers don't scope cookies by port, so it's sent
regardless. Next.js rewrites don't reliably proxy WebSocket upgrades, so
Phase 1 talks to the backend directly — Phase 2's reverse proxy will
front both.

## Verify Phase 0 (task flow) works end to end

1. Go to `http://localhost:3000`, sign in with the seeded admin
   credentials.
2. You land on `/lab` with the task list, phase badge, and progress dots
   on the left, and a file tree + Monaco editor + terminal on the right.
3. Pick task **p1-01** (or whatever's current) — its starter file
   materialises in your workspace and opens in the editor.
4. Edit the code (e.g. leave the bug in, hit **Check** — see the red
   checklist with the exact `CheckFailed` message from pylabs). Fix it,
   hit **Check** again — checklist turns green, **Next** unlocks, and the
   progress dot fills in.
5. Confirm progress persists: refresh the page, or check
   `GET /api/tasks` — your pass/fail state survives (it's in Postgres).

## Verify Phase 1 (real terminal) works end to end

1. In the terminal panel (bottom-right for file tasks), you should see
   **TERMINAL CONNECTED** and a live shell prompt — it's a real `bash`
   process, `cd`'d into your own `data/workspace/{user_id}/`.
2. Click a task with no starter files (**p4-01**, terminal-only) — the
   right pane switches to a full-width terminal. Run the commands the
   brief asks for (`mkdir -p data/raw && echo hello > data/raw/a.txt`,
   etc.) for real, then hit **Check** — it passes against files your
   shell actually created.
3. Switch back to a file-based task and back to a terminal task a few
   times — it's the *same* shell session throughout (try `export
   FOO=bar` on one task, `echo $FOO` after switching — it's still set).
   The file tree also picks up whatever the terminal creates.
4. Resize your browser window — the terminal reflows (`@xterm/addon-fit`)
   and the shell's `$COLUMNS`/`$LINES` update to match.
5. Refresh the page — a fresh shell reconnects (Phase 1 doesn't persist
   shell state across reloads, only the files it wrote to disk).

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
    deps.py        # get_current_user (HTTP) / resolve_session_user (shared)
    pylabs_bridge.py  # the only place that touches pylabs internals
    schemas.py
    routes/
      auth.py
      tasks.py
      files.py
      terminal.py  # WS /ws/terminal — PTY-attached shell per connection
frontend/
  app/
    login/page.tsx
    lab/page.tsx    # the main authenticated view
  components/       # TopBar, ProgressDots, Checklist, Editor, Terminal, ...
  lib/               # api.ts, types.ts, wsUrl.ts
data/workspace/      # per-user files on disk (gitignored)
docker-compose.yml   # Postgres for local dev
```

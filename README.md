# Lab Platform — LAB platform


A self-hosted, KodeKloud-style interactive coding lab platform.

Built in phases. This is **Phase 2**: real per-session isolation — an
actual `codercom/code-server` container per active lab, network-locked to
PyPI/npm only, with resource limits and a hard timeout. Phases 0/1 (the
in-browser Monaco editor + xterm.js terminal) are kept as an automatic
fallback for whenever no lab session is running. See the phase plan for
what's next (Phase 3: UI polish).

## Architecture

- **`pylabs/`** — the existing Python lab harness (`Ctx`, `Check`, `Task`)
  and 21 tasks across 5 phases, copied in unchanged. Not modified by any
  phase of this project — imported directly, both in-process by the
  backend and inside each session container (via `check_runner.py`).
- **`backend/`** — FastAPI. Exposes the task / file / auth / lab API,
  stores users, progress, and lab sessions in Postgres. Each user's
  workspace files live on local disk under `./data/workspace/{user_id}/`,
  bind-mounted into that user's container when a lab is running.
  - `/ws/terminal` — Phase 1's PTY-attached shell (fallback when no lab
    session is active).
  - `/api/lab/{start,stop,status}` — launches/stops a code-server
    container via the Docker SDK (`docker_manager.py`).
  - `/proxy/{token}/...` — reverse proxy (HTTP + WebSocket) fronting that
    container, so it's never exposed on a raw port.
- **`frontend/`** — Next.js 15 (App Router) + TypeScript + Tailwind. Dark
  theme, indigo/green/red throughout. When a lab is running, the right
  pane is an iframe onto the real VS Code; otherwise it's the Phase 0/1
  Monaco editor + xterm.js terminal.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker — for Postgres, and (Phase 2) for the actual lab session
  containers. A real Docker daemon is required; there's no non-Docker
  fallback for `/api/lab/start`.

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

The first time you click **Start Lab**, the backend builds two Docker
images itself (`lab-code-server` — code-server + Python; `lab-egress-proxy`
— the PyPI/npm-only egress proxy) and creates the `lab-internal` /
`lab-external` networks. That first build takes maybe 30s; every start
after that is instant (cached layers, and the proxy container stays up).
You can also pre-build them yourself:

```bash
docker build -t lab-code-server:local backend/docker/lab-code-server
docker build -t lab-egress-proxy:local backend/docker/proxy
```

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

## Verify Phase 2 (real per-session containers) works end to end

1. Pick a task, then click **Start Lab** (top-right of the right pane).
   Within a few seconds the pane switches to a real VS Code — this is
   `codercom/code-server` running in its own Docker container, reverse
   proxied through the backend. The countdown timer next to **Stop Lab**
   counts down from the session length (60 min by default).
2. Confirm it's really isolated: `docker ps` shows a
   `lab-session-{your user id}` container with only the `lab-internal`
   network attached, 1 CPU / 1GB memory limits
   (`docker inspect lab-session-1 | grep -i -E "memory|nanocpus"`).
3. Edit the file in the real VS Code and save it (`Cmd/Ctrl+S`) — hit
   **Check** on the left: it now runs via `docker exec` inside your
   container (same pylabs check code, unmodified), so it sees exactly
   what you just saved.
4. Confirm the network policy: open a terminal inside the VS Code
   (`` Ctrl+` ``) and try `curl -m 5 https://example.com` — it hangs/fails
   (no route out). Then `pip install six` — it succeeds, routed through
   the egress-only proxy to PyPI.
5. Click **Stop Lab** — the container is destroyed
   (`docker ps` no longer lists it) and the pane falls back to the
   Phase 0/1 editor. Start a new lab and confirm your files are still
   there (they live on disk under `data/workspace/`, independent of the
   container's lifecycle).
6. Confirm the timeout: start a lab with a short duration via
   `curl -X POST localhost:8000/api/lab/start -b <cookiejar> -d '{"minutes":1}'`
   and wait — the backend's reaper (runs every 30s) auto-stops and
   removes the container once it expires, without you touching anything.

## Repo layout

```
pylabs/            # unmodified: harness.py, labs/phase{1..5}.py, cli.py
backend/
  app/
    main.py        # FastAPI app, CORS, startup seeding, session reaper
    config.py      # env-driven config
    db.py          # SQLAlchemy engine/session
    models.py      # User, Session, TaskProgress, LabSession
    security.py    # bcrypt + session tokens
    deps.py        # get_current_user (HTTP) / *_ws (shared cookie auth)
    pylabs_bridge.py    # in-process pylabs integration (Phase 0/1 fallback)
    docker_manager.py   # Docker SDK: networks, proxy, session containers
    schemas.py
    routes/
      auth.py
      tasks.py     # /check picks docker-exec vs in-process automatically
      files.py
      terminal.py  # WS /ws/terminal — PTY-attached shell (fallback)
      lab.py       # /api/lab/{start,stop,status}
      proxy.py     # /proxy/{token}/... — HTTP + WS reverse proxy
  docker/
    lab-code-server/  # Dockerfile: code-server + Python
    proxy/            # Dockerfile + config: tinyproxy, PyPI/npm allowlist
    check_runner.py   # runs inside the session container via docker exec
frontend/
  app/
    login/page.tsx
    lab/page.tsx    # the main authenticated view
  components/       # TopBar, ProgressDots, Checklist, Editor, Terminal,
                     # LabControls (Start/Stop + countdown), LabFrame (iframe)
  lib/               # api.ts, types.ts, wsUrl.ts, backendUrl.ts
data/workspace/      # per-user files on disk (gitignored) — bind-mounted
                      # into that user's container when a lab is running
docker-compose.yml   # Postgres for local dev
```

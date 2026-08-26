# Changelog

All notable changes to this project, by phase.

## Phase 2 — Real per-session isolation (2026-08-25)

- Per-user `codercom/code-server` container launched via the Docker SDK on
  "Start Lab", torn down on "Stop Lab" or timeout.
- Network policy: containers run on a Docker network with no default
  route out; the only way out is a `tinyproxy` container allowlisting
  PyPI/npm (and their CDNs). Verified against a real daemon: direct
  egress times out, unlisted domains get a 403, `pip install` succeeds.
- Resource limits: 1 CPU, 1GB RAM per session.
- Reverse proxy (`/proxy/{token}/...`) fronts the container over HTTP
  and WebSocket so it's never exposed on a raw port.
- Check button runs pylabs checks via `docker exec` inside the running
  container when one exists, falling back to the Phase 0/1 in-process
  path otherwise — same harness code, unmodified either way.
- Background reaper auto-stops and destroys containers whose session
  timer has expired.

## Phase 1 — Real terminal (2026-08-25)

- Replaced the mocked terminal panel with a real WebSocket-backed shell:
  a PTY-attached `bash` process per connection, scoped to the user's own
  workspace directory, streamed to xterm.js in the browser.
- Terminal-only tasks (p4-01, p4-02) now genuinely completable — the
  real shell creates real files the Check endpoint can see.
- The terminal session persists across task switches (one continuous
  shell for the visit, not recreated per task).

## Phase 0 — Scaffold (2026-08-24)

- FastAPI backend importing `pylabs/` directly (unmodified) — task
  list, task detail, select, check, and file read/write endpoints.
- Email + password auth, bcrypt hashing, httpOnly cookie sessions.
- Next.js 15 + TypeScript + Tailwind frontend: dark theme, progress
  dots, difficulty stars, markdown briefs, live pass/fail checklist,
  Monaco editor, file tree.
- Per-user workspace files on local disk; progress tracked in Postgres.

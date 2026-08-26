# Deploying beyond localhost

**Nothing in this file has been executed.** It's a plan, written so you can
review and pick a path before anything costs money. Follow it yourself, or
tell me to run a specific section and I will — but I won't deploy or spend
anything without you explicitly saying so for that step.

## The one honest architectural constraint

`docker_manager.py` talks to a Docker daemon over the local Unix socket
(`docker.from_env()`), creates custom bridge networks, and has the backend
reach session containers directly by their bridge IP. That's exactly what
we verified against a real daemon throughout Phases 2–4. It assumes the
backend process has direct access to *a* Docker daemon it can create
arbitrary sibling containers on — which is true on a VM/VPS you control,
and is **not** how Railway or a standard Fly.io app works:

- **Railway** runs each service as its own fixed container. There's no API
  for a running service to spin up new arbitrary sibling containers for
  other users on demand — it isn't built for "one container per active
  user session," which is the entire point of this app's Phase 2 design.
  It's a fine fit for a normal multi-service app; it isn't a fit for this
  one's core mechanic.
- **Fly.io**, as a standard "Fly App," runs your image in a sandboxed
  Firecracker VM without a Docker socket either. Fly's actual answer to
  "dynamically create per-user compute on demand" is the **Fly Machines
  API** — a REST API for creating/starting/stopping lightweight VMs, each
  running an image, with private networking between them. It's the right
  tool for this job, but using it means **replacing `docker_manager.py`'s
  Docker-SDK calls with Fly Machines API calls** — a real adapter, not a
  config change. I have not written that adapter.

So: two honest paths below. Path A deploys the code exactly as it is
today, unmodified, on a plain VPS. Path B is the more "cloud-native" Fly.io
approach, but requires that adapter first — I've scoped what it involves
rather than pretending it's a `fly deploy` away.

---

## Path A — a plain VPS (ships today, zero code changes)

Any VPS with Docker installable works: Hetzner Cloud, DigitalOcean,
Linode, a Fly.io "Machine" provisioned as a bare VM. Hetzner's CX22
(~€4–5/mo, 2 vCPU/4GB) or DigitalOcean's equivalent droplet is plenty for
a personal instance plus a handful of concurrent labs.

1. **Provision the VPS**, Ubuntu 24.04, and point a DNS name at it if you
   want HTTPS via a real domain (recommended — see step 6).

2. **Install Docker** on it:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```

3. **Clone the repo** onto the VPS and check out this branch:
   ```bash
   git clone https://github.com/abhiramvedipala/repo-1 && cd repo-1
   ```

4. **Postgres**: use `docker compose up -d` as-is (it's already how local
   dev runs Postgres), or point `DATABASE_URL` at a managed Postgres
   (Neon, Supabase, Hetzner's managed DB) if you'd rather not run it
   yourself.

5. **Build the backend + frontend as containers** (not yet in this repo —
   needed for a real deploy; local dev runs them as bare processes).
   I'd add:
   - `backend/Dockerfile`: `python:3.11-slim`, copy `backend/` + `pylabs/`,
     `pip install -r requirements.txt`, run uvicorn. It needs the host's
     Docker socket mounted in (`-v /var/run/docker.sock:/var/run/docker.sock`)
     so `docker_manager.py` can keep talking to the *host's* daemon to
     launch sibling session containers — the backend itself can run
     containerized as long as it can still reach a real Docker socket.
   - `frontend/Dockerfile`: standard Next.js multi-stage build
     (`next build` → `next start`).
   - I have not written these Dockerfiles yet; say so and I will.

6. **Reverse proxy + HTTPS**: put Caddy or nginx in front of both
   (`frontend` on `/`, `backend` on `/api`, `/proxy`, `/ws`), terminating
   TLS via Let's Encrypt. Caddy does this in about 10 lines of Caddyfile
   and auto-renews certs — I'd default to Caddy unless you have an
   existing nginx setup.

7. **Environment variables** for production: set `COOKIE_SECURE=true`
   (you're on HTTPS now), a real `ADMIN_PASSWORD`, `FRONTEND_ORIGIN` to
   your real domain, and size `LAB_MAX_CONCURRENT_SESSIONS` to what the
   VPS can actually hold (each session is up to 1 CPU / 1GB — a 4GB box
   comfortably holds 2–3 concurrent, not more).

8. **Firewall**: only 80/443 need to be open publicly. Postgres and the
   Docker socket should never be internet-reachable.

This path costs real money the moment you provision the VPS (a few
dollars a month) — I will not do step 1 without you telling me to.

---

## Path B — Fly.io "native" (more scalable, needs the Machines adapter first)

If you want this to run the way Fly.io actually expects — the backend and
frontend as normal Fly Apps, Fly Postgres for the database, and each lab
session as its own **Fly Machine** created via API instead of a local
Docker container — here's what that actually involves, so you can decide
if it's worth it before I build it:

1. **A new `docker_manager`-equivalent module** using the
   [Fly Machines API](https://fly.io/docs/machines/) instead of the
   `docker` Python SDK: `POST /v1/apps/{app}/machines` to create a session
   machine from the `lab-code-server` image, Fly's private networking
   (6PN, IPv6) in place of our custom bridge network for the backend to
   reach it directly, `DELETE` to tear it down. Same shape as
   `docker_manager.py`, different backend.
2. **The egress restriction re-architected**: Fly doesn't have Docker's
   `internal: true` network flag. The PyPI/npm-only policy would need to
   be rebuilt as either a Fly app running the same tinyproxy image that
   session machines are pointed at via `HTTP_PROXY`/`HTTPS_PROXY` (same
   idea, different plumbing to make it the *only* egress path), or Fly's
   firewall/network policies if your plan tier supports them.
3. **`check_runner.py` via Fly's exec API** in place of `docker exec`
   (Fly Machines support remote exec over their API too).
4. Backend + frontend as two ordinary `fly launch` apps; `fly postgres
   create` for the database.

I'd estimate this as its own focused piece of work — a real adapter, not
a config swap. If you want it, say so explicitly and I'll scope and build
it as a next step, still without deploying anything until you confirm.

---

## Either path: what I will not do without you saying so

- Provision any paid resource (VPS, Fly app, managed Postgres).
- Point a real domain at anything.
- Spend any money, including a platform's free-tier trial that requires a
  card on file.

Tell me which path (A, B, or "figure out something cheaper") and I'll
start on the concrete parts — Dockerfiles, the Fly Machines adapter, or
whatever the chosen path needs — before touching anything that costs
money or goes live.

"""Central config, all overridable via env vars."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

# Make the repo-root `pylabs/` package importable regardless of how/where
# uvicorn was launched from (it is a sibling of backend/, not inside it).
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://labs:labs@localhost:5432/labs"
)

# Resolved to absolute: Docker bind mounts (Phase 2) reject relative paths.
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", REPO_ROOT / "data" / "workspace")).resolve()

SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "labs_session")
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(60 * 60 * 24 * 30)))  # 30 days

# CORS: the Next.js dev server origin
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

# Seeded admin user (created on startup if it doesn't exist yet)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme123")

# Set secure=True once served over HTTPS
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

# ── Phase 2: per-session code-server containers ────────────────────────
DOCKER_DIR = BACKEND_DIR / "docker"
LAB_IMAGE = os.environ.get("LAB_IMAGE", "lab-code-server:local")
LAB_PROXY_IMAGE = os.environ.get("LAB_PROXY_IMAGE", "lab-egress-proxy:local")

LAB_NETWORK_INTERNAL = os.environ.get("LAB_NETWORK_INTERNAL", "lab-internal")
LAB_NETWORK_EXTERNAL = os.environ.get("LAB_NETWORK_EXTERNAL", "lab-external")
LAB_PROXY_CONTAINER_NAME = os.environ.get("LAB_PROXY_CONTAINER_NAME", "lab-egress-proxy")
LAB_PROXY_PORT = 8888

LAB_CONTAINER_PREFIX = os.environ.get("LAB_CONTAINER_PREFIX", "lab-session-")
LAB_CONTAINER_PORT = 8080  # code-server's own listen port inside the container

LAB_SESSION_MINUTES_DEFAULT = int(os.environ.get("LAB_SESSION_MINUTES_DEFAULT", "60"))
LAB_SESSION_MINUTES_MAX = int(os.environ.get("LAB_SESSION_MINUTES_MAX", "180"))
LAB_CPU_LIMIT = float(os.environ.get("LAB_CPU_LIMIT", "1.0"))
LAB_MEM_LIMIT = os.environ.get("LAB_MEM_LIMIT", "1g")

# How often the background reaper checks for expired sessions to stop.
LAB_REAPER_INTERVAL_SECONDS = int(os.environ.get("LAB_REAPER_INTERVAL_SECONDS", "30"))

# ── Phase 4: multi-tenant hosting ───────────────────────────────────────
# Global cap on concurrent *running* containers, across all users — real
# resource limits (CPU/RAM), so this bounds a single host's total load.
# Sessions requested beyond this wait in a FIFO queue (see routes/lab.py)
# and the reaper promotes the oldest one whenever a slot frees up.
LAB_MAX_CONCURRENT_SESSIONS = int(os.environ.get("LAB_MAX_CONCURRENT_SESSIONS", "3"))

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

WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", REPO_ROOT / "data" / "workspace"))

SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "labs_session")
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(60 * 60 * 24 * 30)))  # 30 days

# CORS: the Next.js dev server origin
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

# Seeded admin user (created on startup if it doesn't exist yet)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme123")

# Set secure=True once served over HTTPS
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

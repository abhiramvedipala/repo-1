#!/usr/bin/env bash
# Runs once when the Codespace is created. Gets everything to the point
# where you only need to start the backend and frontend dev servers.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Starting Postgres"
docker compose up -d

echo "==> Backend: venv + deps"
cd backend
python3 -m venv .venv
./.venv/bin/pip install -q -r requirements.txt
cp -n .env.example .env
cd ..

echo "==> Frontend: npm install"
cd frontend
npm install
cd ..

echo ""
echo "Setup complete. Open two terminals:"
echo "  1) cd backend  && ./.venv/bin/uvicorn app.main:app --reload --port 8000"
echo "  2) cd frontend && npm run dev"
echo "Then open the forwarded port 3000 (Codespaces will prompt you, or check the PORTS tab)."

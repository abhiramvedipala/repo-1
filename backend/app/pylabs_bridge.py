"""Bridge between pylabs (single-workspace CLI tool) and the multi-user API.

We import pylabs.harness and pylabs.labs UNCHANGED. The harness's Ctx class
just holds a `self.ws` Path attribute pointed at a hardcoded single-user
`workspace/` dir designed for the CLI. To reuse it for many users' isolated
workspaces without touching harness.py, we build a Ctx the normal way and
then repoint `ctx.ws` at that user's own workspace directory before running
any check or file helper against it — every Ctx method (`read`, `load`,
`require_file`, `run`, ...) already resolves paths through `self.ws`, so
this is enough to isolate users with zero edits to pylabs itself.

The only logic re-implemented here is harness.run_checks' loop (which
prints to a terminal) — rewritten to return structured JSON instead of
printing. The checks themselves (task.checks[i].fn) and CheckFailed
messages are called and surfaced completely verbatim.
"""
import sys
from pathlib import Path

from app.config import WORKSPACE_ROOT  # imported first: patches sys.path for pylabs/

# Ctx.load() (pylabs/harness.py) imports learner files via importlib, which
# would otherwise litter each user's workspace with __pycache__/*.pyc next
# to their solution files every time a check runs.
sys.dont_write_bytecode = True

from pylabs.harness import Ctx, CheckFailed, Task  # noqa: F401  (Task re-exported for typing)
from pylabs.labs import ALL_TASKS, BY_ID  # noqa: F401  (ALL_TASKS re-exported for routes)


def task_index(task: Task) -> int:
    """1-based position of a task in the full ordered task list."""
    return ALL_TASKS.index(task) + 1


def total_tasks() -> int:
    return len(ALL_TASKS)


def get_task(task_id: str) -> Task | None:
    return BY_ID.get(task_id)


def workspace_dir_for(user_id: int) -> Path:
    ws = WORKSPACE_ROOT / str(user_id)
    ws.mkdir(parents=True, exist_ok=True)
    return ws


def make_ctx(task: Task, ws_dir: Path) -> Ctx:
    ctx = Ctx(task)
    ctx.ws = ws_dir  # repoint at this user's isolated workspace, see module docstring
    return ctx


def materialize_starter_files(task: Task, ws_dir: Path) -> list[str]:
    """Write starter files for a task into ws_dir, without clobbering existing work.

    Mirrors pylabs/cli.py's _materialise(), adapted for a per-user directory.
    """
    created = []
    for rel, content in task.files.items():
        p = ws_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text(content, encoding="utf-8")
            created.append(rel)
    return created


def run_checks(task: Task, ws_dir: Path) -> tuple[bool, list[dict]]:
    """Run task.checks against ws_dir. Mirrors harness.run_checks' semantics
    (same success/failure/message logic) but returns data instead of printing.
    """
    ctx = make_ctx(task, ws_dir)
    results = []
    for chk in task.checks:
        try:
            out = chk.fn(ctx)
            ok = True if out is None else bool(out)
            msg = "" if ok else "check returned False"
        except CheckFailed as e:
            ok, msg = False, str(e)
        except Exception as e:
            ok, msg = False, f"{type(e).__name__}: {e}"
        results.append({"label": chk.label, "passed": ok, "message": msg})
    passed = all(r["passed"] for r in results)
    return passed, results


def _safe_join(ws_dir: Path, rel: str) -> Path:
    """Resolve rel under ws_dir, refusing to escape it (path traversal guard)."""
    target = (ws_dir / rel).resolve()
    ws_resolved = ws_dir.resolve()
    if target != ws_resolved and ws_resolved not in target.parents:
        raise ValueError("path escapes workspace")
    return target


def list_files(ws_dir: Path) -> list[dict]:
    """Recursive file tree for the whole user workspace, as a flat list of
    {path, type} entries (type: 'file' | 'dir'), relative to ws_dir.
    """
    entries = []
    if not ws_dir.exists():
        return entries
    for p in sorted(ws_dir.rglob("*")):
        if "__pycache__" in p.parts or p.name.startswith("."):
            continue
        rel = p.relative_to(ws_dir).as_posix()
        entries.append({"path": rel, "type": "dir" if p.is_dir() else "file"})
    return entries


def read_file(ws_dir: Path, rel: str) -> str:
    p = _safe_join(ws_dir, rel)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(rel)
    return p.read_text(encoding="utf-8")


def write_file(ws_dir: Path, rel: str, content: str) -> None:
    p = _safe_join(ws_dir, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

#!/usr/bin/env python3
"""Runs inside a lab session container via `docker exec`, invoked by the
backend's check endpoint. Reads task checks from a read-only mount of
pylabs/ and runs them against this container's own workspace directory —
so a check sees exactly what's on disk in the learner's real VS Code.

Reuses pylabs.harness/pylabs.labs completely unmodified (same as the
in-process path used before a lab session exists); this file is only the
thinnest possible wrapper to run them in this process and print JSON.

Usage: python3 check_runner.py <task_id> <workspace_dir> <pylabs_dir>
"""
import json
import sys
from pathlib import Path

# Match pylabs_bridge.py's in-process path: don't litter the learner's real
# workspace with __pycache__/*.pyc every time a check imports their file.
sys.dont_write_bytecode = True


def main():
    if len(sys.argv) != 4:
        print(json.dumps({"error": "usage: check_runner.py <task_id> <workspace_dir> <pylabs_dir>"}))
        return 2

    task_id, workspace_dir, pylabs_dir = sys.argv[1], sys.argv[2], sys.argv[3]

    sys.path.insert(0, pylabs_dir)
    from pylabs.harness import Ctx, CheckFailed  # noqa: E402
    from pylabs.labs import BY_ID  # noqa: E402

    task = BY_ID.get(task_id)
    if task is None:
        print(json.dumps({"error": f"no such task: {task_id}"}))
        return 2

    ctx = Ctx(task)
    ctx.ws = Path(workspace_dir)

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
    print(json.dumps({"passed": passed, "results": results}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

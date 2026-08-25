"""labctl — the lab runner CLI."""
from __future__ import annotations
import sys
import textwrap
from pathlib import Path

from pylabs.harness import (C, TICK, CROSS, DOT, WORKSPACE, ROOT,
                            load_progress, save_progress, render_brief,
                            run_checks, rule, _term_width)
from pylabs.labs import ALL_TASKS, BY_ID


def _task_index(task):
    return ALL_TASKS.index(task) + 1


def _current():
    p = load_progress()
    tid = p.get("current")
    if tid and tid in BY_ID:
        return BY_ID[tid]
    return None


def _first_incomplete():
    done = set(load_progress().get("completed", []))
    for t in ALL_TASKS:
        if t.id not in done:
            return t
    return None


def _materialise(task):
    WORKSPACE.mkdir(exist_ok=True)
    created = []
    for rel, content in task.files.items():
        p = WORKSPACE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text(content, encoding="utf-8")
            created.append(rel)
    return created


# ─────────────────────────── commands ───────────────────────────
def cmd_list(args):
    done = set(load_progress().get("completed", []))
    cur = load_progress().get("current")
    phase = None
    print()
    for t in ALL_TASKS:
        if t.phase != phase:
            phase = t.phase
            names = {1: "Foundations", 2: "Idiomatic Python", 3: "Structure",
                     4: "Ecosystem", 5: "The Stack"}
            print(f"\n{C.BOLD(C.CYAN(f'  PHASE {phase}'))}  {C.GREY(names[phase])}")
            print(C.GREY("  " + "─" * (_term_width() - 4)))
        mark = C.GREEN(TICK) if t.id in done else (C.YELLOW("▸") if t.id == cur else C.GREY(DOT))
        stars = C.GREY("●" * t.difficulty)
        print(f"   {mark} {C.GREY(t.id)}  {t.title:<44} {stars}")
    n, total = len(done), len(ALL_TASKS)
    bar_w = 30
    filled = int(bar_w * n / total) if total else 0
    bar = C.GREEN("█" * filled) + C.GREY("░" * (bar_w - filled))
    print(f"\n  {bar}  {n}/{total} complete\n")


def cmd_start(args):
    if args:
        tid = args[0]
        if tid not in BY_ID:
            print(C.RED(f"  no such task: {tid}"))
            print(C.GREY("  see them with:  ./labctl list"))
            return 1
        task = BY_ID[tid]
    else:
        task = _current() or _first_incomplete()
        if task is None:
            print(C.GREEN("\n  All tasks complete. \n"))
            return 0
    p = load_progress()
    p["current"] = task.id
    save_progress(p)
    created = _materialise(task)
    render_brief(task, _task_index(task), len(ALL_TASKS))
    if created:
        print(C.GREY("  starter files created in workspace/:"))
        for f in created:
            print(C.GREEN(f"    + {f}"))
        print()
    elif task.files:
        print(C.GREY("  your existing files in workspace/ were kept\n"))
    return 0


def cmd_check(args):
    task = _current()
    if task is None:
        print(C.YELLOW("\n  no active task — run:  ./labctl start\n"))
        return 1
    print(f"\n{C.BOLD('Checking')} {C.GREY(task.id)} {task.title}")
    ok = run_checks(task)
    if ok:
        p = load_progress()
        if task.id not in p["completed"]:
            p["completed"].append(task.id)
        save_progress(p)
    return 0 if ok else 1


def cmd_next(args):
    p = load_progress()
    cur = _current()
    if cur and cur.id not in p.get("completed", []):
        print(C.YELLOW(f"\n  '{cur.id}' isn't passing yet."))
        print(C.GREY("  run ./labctl check, or ./labctl skip to move on anyway\n"))
        return 1
    nxt = _first_incomplete()
    if nxt is None:
        print(C.GREEN(C.BOLD("\n  Every task complete. Go build something real.\n")))
        return 0
    p["current"] = nxt.id
    save_progress(p)
    return cmd_start([nxt.id])


def cmd_skip(args):
    nxt = _first_incomplete()
    cur = _current()
    order = [t for t in ALL_TASKS]
    if cur:
        i = order.index(cur)
        for t in order[i + 1:]:
            if t.id not in load_progress().get("completed", []):
                return cmd_start([t.id])
    return cmd_start([nxt.id]) if nxt else 0


def cmd_hint(args):
    task = _current()
    if task is None:
        print(C.YELLOW("\n  no active task\n"))
        return 1
    print(f"\n{C.YELLOW(C.BOLD('  HINT'))}  {C.GREY(task.id)}")
    for line in task.hint.split("\n"):
        for w in textwrap.wrap(line, _term_width() - 4) or [""]:
            print(f"  {w}")
    print()
    return 0


def cmd_brief(args):
    task = _current()
    if task is None:
        print(C.YELLOW("\n  no active task\n"))
        return 1
    render_brief(task, _task_index(task), len(ALL_TASKS))
    return 0


def cmd_reset(args):
    if not args:
        print(C.YELLOW("\n  usage: ./labctl reset <task-id>   (restores starter files)\n"))
        return 1
    tid = args[0]
    if tid not in BY_ID:
        print(C.RED(f"  no such task: {tid}"))
        return 1
    task = BY_ID[tid]
    for rel, content in task.files.items():
        p = WORKSPACE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        print(C.GREEN(f"  restored {rel}"))
    print()
    return 0


def cmd_progress(args):
    return cmd_list(args)


HELP = f"""
{C.BOLD('labctl')} — Python labs, phase by phase

  {C.BOLD('./labctl start')}          begin (or re-open) the current task
  {C.BOLD('./labctl start p2-03')}    jump to a specific task
  {C.BOLD('./labctl check')}          run the automated checks
  {C.BOLD('./labctl hint')}           get a nudge
  {C.BOLD('./labctl brief')}          re-print the current instructions
  {C.BOLD('./labctl next')}           advance after passing
  {C.BOLD('./labctl skip')}           move on without passing
  {C.BOLD('./labctl list')}           all tasks + progress
  {C.BOLD('./labctl reset p1-01')}    restore a task's starter file

  You write code in {C.CYAN('workspace/')}. Checks run against it.
"""

COMMANDS = {
    "start": cmd_start, "check": cmd_check, "next": cmd_next, "skip": cmd_skip,
    "hint": cmd_hint, "brief": cmd_brief, "list": cmd_list,
    "progress": cmd_progress, "reset": cmd_reset,
}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(HELP)
        return 0
    cmd, rest = argv[0], argv[1:]
    fn = COMMANDS.get(cmd)
    if fn is None:
        print(C.RED(f"\n  unknown command: {cmd}"))
        print(HELP)
        return 1
    return fn(rest) or 0

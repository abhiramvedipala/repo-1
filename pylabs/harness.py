"""Core lab harness: task model, checking engine, terminal rendering."""
from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import contextlib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / "workspace"
PROGRESS = ROOT / ".labprogress.json"

# ─────────────────────────────── colours ───────────────────────────────
_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _mk(code):
    def wrap(s):
        return f"\033[{code}m{s}\033[0m" if _COLOR else str(s)
    return wrap


class C:
    BOLD = staticmethod(_mk("1"))
    DIM = staticmethod(_mk("2"))
    RED = staticmethod(_mk("31"))
    GREEN = staticmethod(_mk("32"))
    YELLOW = staticmethod(_mk("33"))
    BLUE = staticmethod(_mk("34"))
    CYAN = staticmethod(_mk("36"))
    GREY = staticmethod(_mk("90"))


TICK = "✓"
CROSS = "✗"
DOT = "○"


# ─────────────────────────────── model ───────────────────────────────
class CheckFailed(Exception):
    """Raised inside a check to report a specific failure message."""


@dataclass
class Check:
    label: str
    fn: object          # callable(ctx) -> None | bool ; raises CheckFailed on failure


@dataclass
class Task:
    id: str
    phase: int
    title: str
    difficulty: int                       # 1..5
    brief: str
    checks: list
    files: dict = field(default_factory=dict)   # relative path -> starter content
    hint: str = ""
    concepts: str = ""


# ─────────────────────────────── context ───────────────────────────────
class Ctx:
    """Helpers a check can use to inspect the learner's workspace."""

    def __init__(self, task: Task):
        self.task = task
        self.ws = WORKSPACE

    # -- files ---------------------------------------------------------
    def path(self, rel: str) -> Path:
        return self.ws / rel

    def exists(self, rel: str) -> bool:
        return (self.ws / rel).exists()

    def require_file(self, rel: str) -> Path:
        p = self.ws / rel
        if not p.exists():
            raise CheckFailed(f"expected file '{rel}' does not exist")
        return p

    def read(self, rel: str) -> str:
        return self.require_file(rel).read_text(encoding="utf-8")

    def contains(self, rel: str, pattern: str, regex: bool = False):
        src = self.read(rel)
        ok = re.search(pattern, src) if regex else (pattern in src)
        if not ok:
            raise CheckFailed(f"'{rel}' does not contain {pattern!r}")

    def not_contains(self, rel: str, pattern: str, why: str = ""):
        if pattern in self.read(rel):
            raise CheckFailed(f"'{rel}' should not contain {pattern!r}. {why}")

    # -- python --------------------------------------------------------
    def load(self, rel: str):
        """Import a workspace .py file as a fresh module."""
        p = self.require_file(rel)
        name = f"_lab_{p.stem}"
        sys.modules.pop(name, None)
        spec = importlib.util.spec_from_file_location(name, p)
        mod = importlib.util.module_from_spec(spec)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                spec.loader.exec_module(mod)
        except Exception as e:
            raise CheckFailed(f"importing '{rel}' raised {type(e).__name__}: {e}")
        mod._stdout = buf.getvalue()
        return mod

    def func(self, mod, name):
        fn = getattr(mod, name, None)
        if fn is None:
            raise CheckFailed(f"function '{name}' is not defined")
        if not callable(fn):
            raise CheckFailed(f"'{name}' exists but is not callable")
        return fn

    def call(self, mod, name, *args, **kw):
        fn = self.func(mod, name)
        try:
            return fn(*args, **kw)
        except Exception as e:
            shown = ", ".join(repr(a) for a in args)
            raise CheckFailed(f"{name}({shown}) raised {type(e).__name__}: {e}")

    def expect(self, got, want, label=""):
        if got != want:
            raise CheckFailed(f"{label or 'value'}: expected {want!r}, got {got!r}")

    def expect_close(self, got, want, tol=1e-6, label=""):
        try:
            if abs(got - want) > tol:
                raise CheckFailed(f"{label or 'value'}: expected ~{want}, got {got}")
        except TypeError:
            raise CheckFailed(f"{label or 'value'}: expected a number, got {got!r}")

    def raises(self, mod, name, exc, *args, **kw):
        fn = self.func(mod, name)
        try:
            fn(*args, **kw)
        except exc:
            return
        except Exception as e:
            raise CheckFailed(f"{name} raised {type(e).__name__}, expected {exc.__name__}")
        raise CheckFailed(f"{name} did not raise {exc.__name__}")

    # -- shell ---------------------------------------------------------
    def run(self, cmd: str, cwd: Path | None = None, timeout=30):
        r = subprocess.run(cmd, shell=True, cwd=str(cwd or self.ws),
                           capture_output=True, text=True, timeout=timeout)
        return r

    def which(self, prog: str):
        if shutil.which(prog) is None:
            raise CheckFailed(f"'{prog}' is not installed or not on PATH")


# ─────────────────────────────── progress ───────────────────────────────
def load_progress() -> dict:
    if PROGRESS.exists():
        try:
            return json.loads(PROGRESS.read_text())
        except Exception:
            pass
    return {"completed": [], "current": None}


def save_progress(p: dict):
    PROGRESS.write_text(json.dumps(p, indent=2))


# ─────────────────────────────── rendering ───────────────────────────────
def _term_width(default=76):
    try:
        return min(shutil.get_terminal_size().columns, 88)
    except Exception:
        return default


def rule(char="─"):
    return C.GREY(char * _term_width())


def render_brief(task: Task, index: int, total: int):
    w = _term_width()
    stars = "●" * task.difficulty + C.GREY("○" * (5 - task.difficulty))
    print()
    print(rule("━"))
    print(f"{C.BOLD(C.CYAN(f'PHASE {task.phase}'))}  {C.GREY(f'task {index}/{total}')}"
          f"   {C.GREY('difficulty')} {stars}")
    print(f"{C.BOLD(task.title)}  {C.GREY('[' + task.id + ']')}")
    if task.concepts:
        print(C.GREY(f"concepts: {task.concepts}"))
    print(rule("━"))
    print()
    for para in textwrap.dedent(task.brief).strip().split("\n"):
        if para.startswith("    ") or para.startswith("\t"):
            print(C.CYAN(para))
        else:
            print("\n".join(textwrap.wrap(para, w)) if para.strip() else "")
    print()
    print(rule())
    print(C.GREY("verify with:  ") + C.BOLD("./labctl check"))
    print(rule())
    print()


def run_checks(task: Task, quiet=False) -> bool:
    ctx = Ctx(task)
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
        results.append((chk.label, ok, msg))

    if not quiet:
        print()
        for label, ok, msg in results:
            mark = C.GREEN(TICK) if ok else C.RED(CROSS)
            line = f"  {mark} {label}"
            print(line)
            if not ok and msg:
                for l in textwrap.wrap(msg, _term_width() - 8):
                    print(C.GREY(f"      {l}"))
        print()

    passed = all(ok for _, ok, _ in results)
    if not quiet:
        n = sum(1 for _, ok, _ in results if ok)
        if passed:
            print(C.GREEN(C.BOLD(f"  PASSED  {n}/{len(results)} checks")))
            print(C.GREY("  next task:  ./labctl next"))
        else:
            print(C.RED(C.BOLD(f"  FAILED  {n}/{len(results)} checks")))
            print(C.GREY("  stuck?      ./labctl hint"))
        print()
    return passed

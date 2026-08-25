"""Phase 3 — Structure: OOP, dunders, errors, context managers, modules."""
from pylabs.harness import Task, Check, CheckFailed

TASKS = [

Task(
    id="p3-01", phase=3, difficulty=2,
    title="Build a Dataset with __len__ and __getitem__",
    concepts="dunders · the DataLoader contract",
    files={"p3_01.py": '''"""Task p3-01."""


class TextDataset:
    """A minimal Dataset: len(), indexing, iteration, and a useful repr."""

    def __init__(self, texts, labels):
        ...
'''},
    brief="""
    Build `TextDataset(texts, labels)` — the exact contract PyTorch's DataLoader
    requires (Phase 3 §9.8).

    Required behaviour:
        ds = TextDataset(["a","b","c"], [0,1,0])
        len(ds)        -> 3
        ds[1]          -> ("b", 1)        a (text, label) tuple
        ds[-1]         -> ("c", 0)        negative indexing works
        list(ds)       -> [("a",0),("b",1),("c",0)]     iteration for free
        repr(ds)       -> "TextDataset(n=3)"

    Raise ValueError from __init__ if texts and labels have different lengths.
    You do NOT need to write __iter__ — __getitem__ alone makes it iterable.
    """,
    hint="__len__ returns len(self.texts). __getitem__(self, i) returns a tuple. "
         "Python's own list indexing already handles negatives if you index the list.",
    checks=[
        Check("len() works", lambda c: _p3_01(c, "len")),
        Check("indexing returns (text, label)", lambda c: _p3_01(c, "index")),
        Check("negative indexing works", lambda c: _p3_01(c, "neg")),
        Check("iterable via __getitem__", lambda c: _p3_01(c, "iter")),
        Check("__repr__ is informative", lambda c: _p3_01(c, "repr")),
        Check("mismatched lengths raise ValueError", lambda c: _p3_01(c, "raise")),
    ],
),

Task(
    id="p3-02", phase=3, difficulty=2,
    title="Validate with @property and a custom exception",
    concepts="@property · setters · exception hierarchies",
    files={"p3_02.py": '''"""Task p3-02."""


class ConfigError(Exception):
    """Base for configuration problems."""


class Config:
    def __init__(self, lr=0.001, epochs=10):
        ...
'''},
    brief="""
    Build a `Config` class whose `lr` is validated on every assignment,
    including in __init__.

        cfg = Config(lr=0.01)
        cfg.lr            -> 0.01
        cfg.lr = 0.5      -> ok
        cfg.lr = -1       -> raises InvalidLearningRate
        Config(lr=0)      -> raises InvalidLearningRate

    Requirements:
      - `lr` must be a @property with a setter that rejects values <= 0.
      - Define `InvalidLearningRate` as a SUBCLASS of `ConfigError`, so a caller
        can write `except ConfigError:` and catch it (Phase 3 §10.6).
      - The error message must contain the offending value.
      - Assignment in __init__ must go through the setter — don't bypass it.
    """,
    hint="self.lr = lr in __init__ calls the setter. Store the real value in self._lr.",
    checks=[
        Check("valid lr is stored", lambda c: _p3_02(c, "ok")),
        Check("negative lr raises", lambda c: _p3_02(c, "neg")),
        Check("zero lr raises", lambda c: _p3_02(c, "zero")),
        Check("__init__ validates too", lambda c: _p3_02(c, "init")),
        Check("InvalidLearningRate subclasses ConfigError", lambda c: _p3_02(c, "sub")),
        Check("message includes the bad value", lambda c: _p3_02(c, "msg")),
    ],
),

Task(
    id="p3-03", phase=3, difficulty=3,
    title="A Timer context manager, two ways",
    concepts="__enter__/__exit__ · @contextmanager · try/finally",
    files={"p3_03.py": '''"""Task p3-03."""
import time
from contextlib import contextmanager


class Timer:
    """Class-based context manager. Expose .elapsed after the block."""
    ...


@contextmanager
def timer():
    """Generator-based equivalent. Yield a dict with an 'elapsed' key."""
    ...
'''},
    brief="""
    Implement the SAME context manager twice — once as a class, once with
    @contextmanager (Phase 3 §11.6).

        with Timer() as t:
            work()
        t.elapsed            -> float seconds

        with timer() as t:
            work()
        t["elapsed"]         -> float seconds

    Critically: the elapsed time must still be recorded when the block raises.
    The exception must NOT be swallowed — it has to propagate.
    """,
    hint="Class: __exit__ sets self.elapsed and returns False. "
         "Generator: wrap the yield in try/finally.",
    checks=[
        Check("class Timer records elapsed", lambda c: _p3_03(c, "cls")),
        Check("class Timer records on exception too", lambda c: _p3_03(c, "cls_exc")),
        Check("class Timer does NOT swallow the exception", lambda c: _p3_03(c, "cls_prop")),
        Check("@contextmanager version works", lambda c: _p3_03(c, "gen")),
        Check("@contextmanager records on exception", lambda c: _p3_03(c, "gen_exc")),
    ],
),

Task(
    id="p3-04", phase=3, difficulty=3,
    title="Build a real package",
    concepts="modules · __init__.py · __main__ guard",
    files={},
    brief="""
    No starter file for this one — you're creating the structure yourself.

    Inside `workspace/`, build exactly this:

        mypkg/
        ├── __init__.py
        ├── text.py
        └── cli.py

    Requirements:
      1. `text.py` defines `normalize(s)` — lowercases, strips whitespace,
         and collapses internal runs of whitespace to a single space.
             normalize("  Hello   WORLD ")  ->  "hello world"

      2. `__init__.py` re-exports it, so `from mypkg import normalize` works.

      3. `cli.py` defines `main()` which prints "cli ran", and guards it with
             if __name__ == "__main__":
                 main()
         Importing cli must print NOTHING (Phase 3 §12.4).

    Create the files however you like — editor, `touch`, `cat >`, whatever.
    """,
    hint="mkdir mypkg && touch mypkg/__init__.py — then in __init__.py: "
         "from .text import normalize",
    checks=[
        Check("mypkg/ package layout exists", lambda c: _p3_04(c, "files")),
        Check("normalize() collapses whitespace", lambda c: _p3_04(c, "norm")),
        Check("from mypkg import normalize works", lambda c: _p3_04(c, "export")),
        Check("importing cli prints nothing (__main__ guard)", lambda c: _p3_04(c, "guard")),
        Check("running cli.py directly prints 'cli ran'", lambda c: _p3_04(c, "run")),
    ],
),
]


def _p3_01(c, which):
    m = c.load("p3_01.py")
    DS = getattr(m, "TextDataset", None)
    if DS is None:
        raise CheckFailed("class TextDataset is not defined")
    if which == "raise":
        try:
            DS(["a", "b"], [0])
        except ValueError:
            return
        raise CheckFailed("mismatched lengths should raise ValueError")
    ds = DS(["a", "b", "c"], [0, 1, 0])
    if which == "len":
        c.expect(len(ds), 3, "len(ds)")
    elif which == "index":
        c.expect(tuple(ds[1]), ("b", 1), "ds[1]")
    elif which == "neg":
        c.expect(tuple(ds[-1]), ("c", 0), "ds[-1]")
    elif which == "iter":
        c.expect([tuple(x) for x in ds], [("a", 0), ("b", 1), ("c", 0)], "list(ds)")
    elif which == "repr":
        r = repr(ds)
        if "TextDataset" not in r or "3" not in r:
            raise CheckFailed(f"repr is {r!r} — should name the class and the size")


def _p3_02(c, which):
    m = c.load("p3_02.py")
    Config = getattr(m, "Config", None)
    ConfigError = getattr(m, "ConfigError", None)
    Bad = getattr(m, "InvalidLearningRate", None)
    if Config is None:
        raise CheckFailed("class Config is not defined")
    if Bad is None:
        raise CheckFailed("class InvalidLearningRate is not defined")
    if which == "sub":
        if not issubclass(Bad, ConfigError):
            raise CheckFailed("InvalidLearningRate must subclass ConfigError")
        return
    if which == "ok":
        cfg = Config(lr=0.01)
        c.expect(cfg.lr, 0.01, "cfg.lr")
        cfg.lr = 0.5
        c.expect(cfg.lr, 0.5, "after assignment")
        return
    if which == "neg":
        cfg = Config()
        try:
            cfg.lr = -1
        except Bad:
            return
        raise CheckFailed("assigning a negative lr should raise InvalidLearningRate")
    if which == "zero":
        cfg = Config()
        try:
            cfg.lr = 0
        except Bad:
            return
        raise CheckFailed("lr = 0 should raise (it's <= 0)")
    if which == "init":
        try:
            Config(lr=-5)
        except Bad:
            return
        raise CheckFailed("Config(lr=-5) should raise — route __init__ through the setter")
    if which == "msg":
        try:
            Config(lr=-7)
        except Bad as e:
            if "-7" not in str(e):
                raise CheckFailed(f"message {str(e)!r} should include the bad value")
            return
        raise CheckFailed("expected InvalidLearningRate")


def _p3_03(c, which):
    m = c.load("p3_03.py")
    if which.startswith("cls"):
        Timer = getattr(m, "Timer", None)
        if Timer is None:
            raise CheckFailed("class Timer is not defined")
        if which == "cls":
            with Timer() as t:
                sum(range(10000))
            if not isinstance(getattr(t, "elapsed", None), float):
                raise CheckFailed("t.elapsed should be a float after the block")
            return
        if which == "cls_exc":
            t = Timer()
            try:
                with t:
                    raise ValueError("boom")
            except ValueError:
                pass
            if not isinstance(getattr(t, "elapsed", None), float):
                raise CheckFailed("elapsed must be recorded even when the block raises")
            return
        if which == "cls_prop":
            try:
                with Timer():
                    raise ValueError("boom")
            except ValueError:
                return
            raise CheckFailed("__exit__ must return False so the exception propagates")
    tm = c.func(m, "timer")
    if which == "gen":
        with tm() as t:
            sum(range(10000))
        if not isinstance(t, dict) or "elapsed" not in t:
            raise CheckFailed("timer() should yield a dict containing 'elapsed'")
        if not isinstance(t["elapsed"], float):
            raise CheckFailed("t['elapsed'] should be a float")
        return
    if which == "gen_exc":
        holder = {}
        try:
            with tm() as t:
                holder["t"] = t
                raise ValueError("boom")
        except ValueError:
            pass
        t = holder.get("t")
        if not isinstance(t, dict) or not isinstance(t.get("elapsed"), float):
            raise CheckFailed("use try/finally around the yield so elapsed is always set")


def _p3_04(c, which):
    import subprocess, sys
    if which == "files":
        for f in ("mypkg/__init__.py", "mypkg/text.py", "mypkg/cli.py"):
            c.require_file(f)
        return
    code = {
        "norm": "from mypkg.text import normalize; print(repr(normalize('  Hello   WORLD ')))",
        "export": "from mypkg import normalize; print(repr(normalize('A  B')))",
        "guard": "import mypkg.cli; print('IMPORT_DONE')",
    }
    if which in code:
        r = c.run(f'{sys.executable} -c "{code[which]}"')
        if r.returncode != 0:
            raise CheckFailed(r.stderr.strip().splitlines()[-1] if r.stderr else "failed")
        out = r.stdout.strip()
        if which == "norm" and out != "'hello world'":
            raise CheckFailed(f"normalize('  Hello   WORLD ') gave {out}, expected 'hello world'")
        if which == "export" and out != "'a b'":
            raise CheckFailed(f"expected 'a b' via `from mypkg import normalize`, got {out}")
        if which == "guard" and out != "IMPORT_DONE":
            raise CheckFailed(f"importing cli printed {out!r} — add the __main__ guard")
        return
    if which == "run":
        r = c.run(f"{sys.executable} mypkg/cli.py")
        if "cli ran" not in r.stdout:
            raise CheckFailed(f"running cli.py should print 'cli ran', got {r.stdout!r}")

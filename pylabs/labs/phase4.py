"""Phase 4 — Ecosystem: uv, stdlib, shell, git, pytest."""
import sys
from pylabs.harness import Task, Check, CheckFailed

TASKS = [

Task(
    id="p4-01", phase=4, difficulty=1,
    title="Terminal navigation and file creation",
    concepts="shell · mkdir · redirection · find",
    files={},
    brief="""
    Pure terminal task — do all of this from the command line, not an editor.
    This is the shell fluency you said you were missing.

    Create, inside `workspace/`:

        data/
        ├── raw/
        │   ├── a.txt      containing exactly:  hello
        │   └── b.txt      containing exactly:  world
        └── notes.md       containing a line starting with '# '

    Useful commands:
        mkdir -p data/raw          create nested directories in one shot
        echo "hello" > data/raw/a.txt      write (overwrites!)
        echo "more" >> file                append
        cat file                   print a file
        ls -la                     list, long form, including hidden
        find . -name "*.txt"       search recursively

    Remember Phase 4 §11.2: `>` truncates instantly. `>>` appends.
    """,
    hint='mkdir -p data/raw && echo "hello" > data/raw/a.txt && echo "world" > data/raw/b.txt && echo "# Notes" > data/notes.md',
    checks=[
        Check("data/raw/ exists", lambda c: c.require_file("data/raw")),
        Check("a.txt contains 'hello'", lambda c: _p4_txt(c, "data/raw/a.txt", "hello")),
        Check("b.txt contains 'world'", lambda c: _p4_txt(c, "data/raw/b.txt", "world")),
        Check("notes.md has a markdown heading", lambda c: _p4_head(c)),
    ],
),

Task(
    id="p4-02", phase=4, difficulty=2,
    title="Set up a uv project",
    concepts="uv · pyproject.toml · lockfiles · .gitignore",
    files={},
    brief="""
    Create a real, isolated project using uv (Phase 4 §14.2).

    Inside `workspace/`, create a directory `proj/` and in it:

      1. Initialise a uv project:      uv init
      2. Add a real dependency:        uv add rich
      3. Confirm the lock file exists: uv.lock
      4. Write a .gitignore that ignores  .venv/  and  __pycache__/

    If uv isn't installed:
        curl -LsSf https://astral.sh/uv/install.sh | sh          (macOS/Linux)
        powershell -c "irm https://astral.sh/uv/install.ps1|iex" (Windows)

    Fallback if you truly can't install uv: create proj/ with a hand-written
    pyproject.toml declaring a dependency on rich, plus the .gitignore. The
    checks accept either route.
    """,
    hint="mkdir proj && cd proj && uv init && uv add rich",
    checks=[
        Check("proj/ exists", lambda c: c.require_file("proj")),
        Check("pyproject.toml exists", lambda c: c.require_file("proj/pyproject.toml")),
        Check("declares a dependency on rich",
              lambda c: c.contains("proj/pyproject.toml", "rich")),
        Check(".gitignore ignores .venv/", lambda c: c.contains("proj/.gitignore", ".venv")),
        Check(".gitignore ignores __pycache__/",
              lambda c: c.contains("proj/.gitignore", "__pycache__")),
    ],
),

Task(
    id="p4-03", phase=4, difficulty=2,
    title="Replace hand-rolled loops with the stdlib",
    concepts="Counter · defaultdict · itertools.product",
    files={"p4_03.py": '''"""Task p4-03."""
from collections import Counter, defaultdict
from itertools import product


def word_counts(words, n):
    """Top n (word, count) pairs. Use Counter."""
    ...


def group_by_first_letter(words):
    """{'a': ['apple','ant'], ...} — use defaultdict, no `if key not in`."""
    ...


def hyperparam_grid(lrs, batches):
    """All (lr, batch) combinations, in product() order."""
    ...
'''},
    brief="""
    Three one-liners that replace loops you'd otherwise write by hand
    (Phase 4 §16.1–16.2).

        word_counts(["a","b","a"], 1)          -> [("a", 2)]
        group_by_first_letter(["ant","bee","apple"])
                                               -> {"a": ["ant","apple"], "b": ["bee"]}
        hyperparam_grid([1e-3, 1e-4], [16, 32])
                                               -> [(0.001,16),(0.001,32),(0.0001,16),(0.0001,32)]

    Constraints:
      - word_counts must use Counter.
      - group_by_first_letter must use defaultdict — no membership test.
      - hyperparam_grid must use itertools.product — no nested for loops.
    """,
    hint="Counter(words).most_common(n) · defaultdict(list) · list(product(lrs, batches))",
    checks=[
        Check("word_counts uses Counter and is correct", lambda c: _p4_03(c, "count")),
        Check("group_by_first_letter groups correctly", lambda c: _p4_03(c, "group")),
        Check("no membership test in the grouping",
              lambda c: c.not_contains("p4_03.py", "not in", "Let defaultdict handle it.")),
        Check("hyperparam_grid produces all combinations", lambda c: _p4_03(c, "grid")),
        Check("uses itertools.product",
              lambda c: c.contains("p4_03.py", "product(")),
    ],
),

Task(
    id="p4-04", phase=4, difficulty=3,
    title="Write tests that actually catch bugs",
    concepts="pytest · fixtures · parametrize · raises · approx",
    files={"scale.py": '''"""Module under test — do not change this file."""


def scale(values, lo=0.0, hi=1.0):
    """Min-max scale a list of numbers into [lo, hi]."""
    if not values:
        return []
    if lo >= hi:
        raise ValueError("lo must be less than hi")
    mn, mx = min(values), max(values)
    if mn == mx:
        return [lo for _ in values]
    span = mx - mn
    return [lo + (v - mn) / span * (hi - lo) for v in values]
''',
           "test_scale.py": '''"""Write your tests here. Run them with:  pytest -v"""
import pytest
from scale import scale


def test_placeholder():
    assert True
'''},
    brief="""
    `scale.py` is given. Write `test_scale.py` covering it properly
    (Phase 4 §19).

    Your test file must contain, at minimum:
      1. A basic case: scale([0,5,10]) == [0.0, 0.5, 1.0]
      2. An empty-input case returning []
      3. The degenerate case where all values are identical
      4. A pytest.raises test for lo >= hi
      5. At least one @pytest.mark.parametrize
      6. At least one float comparison using pytest.approx

    Delete test_placeholder. Every test must genuinely pass.
    """,
    hint="Use == pytest.approx([0.0, 0.5, 1.0]) for the list comparison.",
    checks=[
        Check("pytest is available", lambda c: _p4_04(c, "have")),
        Check("uses @pytest.mark.parametrize",
              lambda c: c.contains("test_scale.py", "parametrize")),
        Check("uses pytest.raises", lambda c: c.contains("test_scale.py", "pytest.raises")),
        Check("uses pytest.approx", lambda c: c.contains("test_scale.py", "approx")),
        Check("placeholder removed",
              lambda c: c.not_contains("test_scale.py", "test_placeholder", "Write real tests.")),
        Check("at least 4 tests collected", lambda c: _p4_04(c, "count")),
        Check("all tests pass", lambda c: _p4_04(c, "pass")),
    ],
),
]


def _p4_txt(c, rel, want):
    got = c.read(rel).strip()
    if got != want:
        raise CheckFailed(f"{rel} contains {got!r}, expected {want!r}")


def _p4_head(c):
    txt = c.read("data/notes.md")
    if not any(l.startswith("# ") for l in txt.splitlines()):
        raise CheckFailed("notes.md needs a line starting with '# '")


def _p4_03(c, which):
    m = c.load("p4_03.py")
    if which == "count":
        c.expect(list(c.call(m, "word_counts", ["a", "b", "a"], 1)), [("a", 2)])
        c.contains("p4_03.py", "Counter(")
    elif which == "group":
        got = c.call(m, "group_by_first_letter", ["ant", "bee", "apple"])
        c.expect(dict(got), {"a": ["ant", "apple"], "b": ["bee"]})
    elif which == "grid":
        got = [tuple(x) for x in c.call(m, "hyperparam_grid", [1e-3, 1e-4], [16, 32])]
        c.expect(got, [(1e-3, 16), (1e-3, 32), (1e-4, 16), (1e-4, 32)])


def _p4_04(c, which):
    if which == "have":
        r = c.run(f"{sys.executable} -m pytest --version")
        if r.returncode != 0:
            raise CheckFailed("pytest not installed. Run:  uv pip install pytest   "
                              "(or: pip install pytest)")
        return
    r = c.run(f"{sys.executable} -m pytest test_scale.py -q --no-header")
    out = (r.stdout or "") + (r.stderr or "")
    if which == "count":
        import re
        nums = [int(n) for n in re.findall(r"(\d+) passed", out)]
        total = nums[0] if nums else 0
        if total < 4:
            raise CheckFailed(f"only {total} tests passed — write at least 4 real tests")
        return
    if which == "pass":
        if r.returncode != 0:
            tail = "\n".join(out.strip().splitlines()[-6:])
            raise CheckFailed("pytest reported failures:\n" + tail)

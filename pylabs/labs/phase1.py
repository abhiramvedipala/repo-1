"""Phase 1 — Foundations: variables, operators, data structures, loops, mutability."""
from pylabs.harness import Task, Check, CheckFailed

TASKS = [

Task(
    id="p1-01", phase=1, difficulty=1,
    title="Falsy values and the `is None` fix",
    concepts="truthiness · is vs == · default arguments",
    files={"p1_01.py": '''"""Task p1-01 — write your solution here."""


def apply_discount(price, discount=None):
    # TODO: if no discount was supplied, use 0.10
    # Careful: a discount of 0 is a LEGITIMATE value.
    ...
'''},
    brief="""
    `apply_discount(price, discount)` should return the price after applying
    a discount fraction.

    Rules:
      - If `discount` is not supplied at all, default to 0.10 (10% off).
      - If `discount` is supplied as 0, apply NO discount (return the full price).
      - Return a float.

    This is the exact bug from Phase 1 §1.6: writing `if not discount:` treats
    a legitimate 0 as "missing" and silently overrides it.

    Examples:
        apply_discount(100)        -> 90.0
        apply_discount(100, 0.5)   -> 50.0
        apply_discount(100, 0)     -> 100.0
    """,
    hint="Use `if discount is None:` — not `if not discount:`. 0 is falsy but valid.",
    checks=[
        Check("file p1_01.py exists", lambda c: c.require_file("p1_01.py")),
        Check("default discount is 10%",
              lambda c: c.expect_close(c.call(c.load("p1_01.py"), "apply_discount", 100), 90.0)),
        Check("explicit discount works",
              lambda c: c.expect_close(c.call(c.load("p1_01.py"), "apply_discount", 100, 0.5), 50.0)),
        Check("discount=0 means NO discount (the trap)",
              lambda c: c.expect_close(c.call(c.load("p1_01.py"), "apply_discount", 100, 0), 100.0)),
        Check("does not use `if not discount`",
              lambda c: c.not_contains("p1_01.py", "if not discount",
                                       "That treats 0 as missing.")),
    ],
),

Task(
    id="p1-02", phase=1, difficulty=1,
    title="Pick the right data structure",
    concepts="set vs list · O(1) membership · dict lookup",
    files={"p1_02.py": '''"""Task p1-02."""


def count_known_words(words, vocabulary):
    """Return how many items of `words` appear in `vocabulary`."""
    ...
'''},
    brief="""
    `count_known_words(words, vocabulary)` returns how many entries of the list
    `words` appear in `vocabulary` (a list, possibly with duplicates).

    It must be FAST: this is called with ~200,000 words against a ~50,000-entry
    vocabulary. A naive `in` against a list is O(n) per lookup and will time out.

    Phase 1 §2.8: converting the vocabulary to a set once makes each lookup O(1).

    Examples:
        count_known_words(["a","b","z"], ["a","b","c"])  -> 2
        count_known_words([], ["a"])                     -> 0
    """,
    hint="Build `vocab = set(vocabulary)` ONCE, before the loop. Then `w in vocab`.",
    checks=[
        Check("correct on a small case",
              lambda c: c.expect(c.call(c.load("p1_02.py"), "count_known_words",
                                        ["a","b","z"], ["a","b","c"]), 2)),
        Check("handles empty input",
              lambda c: c.expect(c.call(c.load("p1_02.py"), "count_known_words", [], ["a"]), 0)),
        Check("counts duplicates in `words`",
              lambda c: c.expect(c.call(c.load("p1_02.py"), "count_known_words",
                                        ["a","a","a"], ["a"]), 3)),
        Check("fast enough on 200k x 50k (uses a set)", lambda c: _p1_02_perf(c)),
    ],
),

Task(
    id="p1-03", phase=1, difficulty=2,
    title="The mutable default argument",
    concepts="mutability · references · def f(x=[])",
    files={"p1_03.py": '''"""Task p1-03."""


def add_reading(value, log=[]):
    """BROKEN: fix the shared-state bug without changing the call signature shape."""
    log.append(value)
    return log
'''},
    brief="""
    `add_reading(value, log)` appends a value to a log and returns it.
    If no log is given it should start a FRESH empty list every call.

    The starter code has the classic Phase 1 §4.6 bug: the default list is
    created once, at def time, and shared by every call that omits it.

    Required behaviour:
        add_reading(1)        -> [1]
        add_reading(2)        -> [2]        (not [1, 2])
        add_reading(3, [9])   -> [9, 3]

    A caller-supplied list must still be mutated in place.
    """,
    hint="Default to None, then `if log is None: log = []` inside the function.",
    checks=[
        Check("first call returns [1]",
              lambda c: c.expect(c.call(c.load("p1_03.py"), "add_reading", 1), [1])),
        Check("calls do not share state (the bug)", lambda c: _p1_03_fresh(c)),
        Check("supplied list is mutated in place", lambda c: _p1_03_inplace(c)),
        Check("no mutable default in the signature",
              lambda c: c.not_contains("p1_03.py", "log=[]",
                                       "The default is still a shared list.")),
    ],
),

Task(
    id="p1-04", phase=1, difficulty=2,
    title="Shallow vs deep copy",
    concepts="views · aliasing · copy.deepcopy",
    files={"p1_04.py": '''"""Task p1-04."""


def duplicate_config(config):
    """Return a copy that shares NOTHING with the original."""
    ...
'''},
    brief="""
    `duplicate_config(config)` takes a nested dict like:

        {"lr": 0.01, "layers": [64, 32], "meta": {"tags": ["a"]}}

    and returns a copy that is fully independent. Mutating anything at any depth
    in the copy must leave the original untouched, and vice versa.

    `dict(config)` and `config.copy()` are NOT enough — they are shallow, and the
    inner list and dict stay shared (Phase 1 §4.5).
    """,
    hint="`import copy` then `return copy.deepcopy(config)`.",
    checks=[
        Check("returns an equal dict", lambda c: _p1_04_equal(c)),
        Check("top level is independent", lambda c: _p1_04_top(c)),
        Check("nested list is independent", lambda c: _p1_04_nested(c)),
        Check("deeply nested dict is independent", lambda c: _p1_04_deep(c)),
    ],
),

Task(
    id="p1-05", phase=1, difficulty=3,
    title="Word frequency — build it by hand",
    concepts="dict · loops · sorting with key",
    files={"p1_05.py": '''"""Task p1-05."""


def top_words(text, n=3):
    """Return the n most common words as a list of (word, count) tuples."""
    ...
'''},
    brief="""
    `top_words(text, n)` returns the `n` most frequent words as a list of
    `(word, count)` tuples, ordered by count descending.

    Rules:
      - Case-insensitive: "The" and "the" are the same word.
      - Split on whitespace.
      - Strip surrounding punctuation: . , ! ? ; : " '
      - Ties broken alphabetically (ascending) so results are deterministic.
      - Do NOT use collections.Counter — build the dict yourself. You get Counter
        in Phase 4; the point here is to feel what it replaces.

    Example:
        top_words("the cat the dog THE bird cat", 2)
        -> [("the", 3), ("cat", 2)]
    """,
    hint="Sort with a tuple key: sorted(items, key=lambda kv: (-kv[1], kv[0]))",
    checks=[
        Check("basic counting",
              lambda c: c.expect(c.call(c.load("p1_05.py"), "top_words",
                                        "the cat the dog THE bird cat", 2),
                                 [("the", 3), ("cat", 2)])),
        Check("strips punctuation",
              lambda c: c.expect(c.call(c.load("p1_05.py"), "top_words", "hi! hi, hi. bye", 1),
                                 [("hi", 3)])),
        Check("ties broken alphabetically",
              lambda c: c.expect(c.call(c.load("p1_05.py"), "top_words", "b a c", 3),
                                 [("a", 1), ("b", 1), ("c", 1)])),
        Check("handles empty text",
              lambda c: c.expect(c.call(c.load("p1_05.py"), "top_words", "", 3), [])),
        Check("does not use collections.Counter",
              lambda c: c.not_contains("p1_05.py", "Counter", "Build the dict manually.")),
    ],
),
]


# ── helper check bodies ────────────────────────────────────────────────
def _p1_02_perf(c):
    import random, string, time
    rnd = random.Random(0)
    vocab = ["".join(rnd.choices(string.ascii_lowercase, k=6)) for _ in range(50_000)]
    words = [rnd.choice(vocab) for _ in range(200_000)]
    mod = c.load("p1_02.py")
    t = time.perf_counter()
    got = c.call(mod, "count_known_words", words, vocab)
    dt = time.perf_counter() - t
    if got != 200_000:
        raise CheckFailed(f"expected 200000 matches, got {got}")
    if dt > 3.0:
        raise CheckFailed(f"took {dt:.1f}s — too slow. Convert vocabulary to a set once.")


def _p1_03_fresh(c):
    mod = c.load("p1_03.py")
    c.call(mod, "add_reading", 1)
    second = c.call(mod, "add_reading", 2)
    if second != [2]:
        raise CheckFailed(f"second call returned {second!r} — state leaked between calls")


def _p1_03_inplace(c):
    mod = c.load("p1_03.py")
    mine = [9]
    out = c.call(mod, "add_reading", 3, mine)
    if mine != [9, 3]:
        raise CheckFailed(f"caller's list should be mutated in place, got {mine!r}")
    if out != [9, 3]:
        raise CheckFailed(f"expected [9, 3], got {out!r}")


def _cfg():
    return {"lr": 0.01, "layers": [64, 32], "meta": {"tags": ["a"]}}


def _p1_04_equal(c):
    mod = c.load("p1_04.py")
    src = _cfg()
    out = c.call(mod, "duplicate_config", src)
    if out != src:
        raise CheckFailed(f"copy should equal the original, got {out!r}")


def _p1_04_top(c):
    mod = c.load("p1_04.py")
    src = _cfg()
    out = c.call(mod, "duplicate_config", src)
    out["lr"] = 999
    if src["lr"] != 0.01:
        raise CheckFailed("changing the copy changed the original at the top level")


def _p1_04_nested(c):
    mod = c.load("p1_04.py")
    src = _cfg()
    out = c.call(mod, "duplicate_config", src)
    out["layers"].append(16)
    if src["layers"] != [64, 32]:
        raise CheckFailed("the nested list is still shared — you made a SHALLOW copy")


def _p1_04_deep(c):
    mod = c.load("p1_04.py")
    src = _cfg()
    out = c.call(mod, "duplicate_config", src)
    out["meta"]["tags"].append("b")
    if src["meta"]["tags"] != ["a"]:
        raise CheckFailed("the deeply nested list is still shared — use copy.deepcopy")

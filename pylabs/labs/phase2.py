"""Phase 2 — Idiomatic Python: comprehensions, generators, decorators, closures."""
from pylabs.harness import Task, Check, CheckFailed

TASKS = [

Task(
    id="p2-01", phase=2, difficulty=1,
    title="Filter vs transform in a comprehension",
    concepts="comprehensions · the two `if` positions",
    files={"p2_01.py": '''"""Task p2-01."""


def keep_positive(nums):
    """Return only the positive numbers, each squared."""
    ...


def floor_at_zero(nums):
    """Return EVERY number: negatives become 0, others squared."""
    ...
'''},
    brief="""
    Two functions, one comprehension each. They look similar and behave
    completely differently — this is Phase 2 §6.3.

      keep_positive([-2,-1,0,1,2])  -> [1, 4]           filter: fewer items out
      floor_at_zero([-2,-1,0,1,2])  -> [0,0,0,1,4]      transform: same count out

    `keep_positive` must use a filter (`if` AFTER the for).
    `floor_at_zero` must use a ternary (`if/else` BEFORE the for).
    Both must be a single comprehension — no explicit `for` loop statements.
    """,
    hint="[x**2 for x in nums if x > 0]   vs   [x**2 if x > 0 else 0 for x in nums]",
    checks=[
        Check("keep_positive filters",
              lambda c: c.expect(c.call(c.load("p2_01.py"), "keep_positive", [-2,-1,0,1,2]), [1,4])),
        Check("floor_at_zero keeps length",
              lambda c: c.expect(c.call(c.load("p2_01.py"), "floor_at_zero", [-2,-1,0,1,2]),
                                 [0,0,0,1,4])),
        Check("both handle empty lists", lambda c: _p2_01_empty(c)),
        Check("uses comprehensions, not loops",
              lambda c: c.not_contains("p2_01.py", "append(",
                                       "Use a comprehension, not an accumulator loop.")),
    ],
),

Task(
    id="p2-02", phase=2, difficulty=2,
    title="A batching generator",
    concepts="yield · laziness · the DataLoader idea",
    files={"p2_02.py": '''"""Task p2-02."""


def batches(items, size):
    """Yield successive lists of `size` items. Last batch may be shorter."""
    ...
'''},
    brief="""
    `batches(items, size)` yields successive chunks of `items` as lists.
    The final chunk may be shorter. This is a miniature DataLoader.

        list(batches([1,2,3,4,5], 2))  ->  [[1,2],[3,4],[5]]

    It MUST be a generator (use `yield`), not a function that builds and
    returns a list. The check calls it on a 10-million item range — if you
    materialise everything you will blow up memory.
    """,
    hint="for i in range(0, len(items), size): yield items[i:i+size]",
    checks=[
        Check("correct chunking",
              lambda c: c.expect([list(b) for b in c.call(c.load("p2_02.py"), "batches", [1,2,3,4,5], 2)],
                                 [[1,2],[3,4],[5]])),
        Check("exact division leaves no empty batch",
              lambda c: c.expect([list(b) for b in c.call(c.load("p2_02.py"), "batches", [1,2,3,4], 2)],
                                 [[1,2],[3,4]])),
        Check("is a generator, not a list", lambda c: _p2_02_isgen(c)),
        Check("lazy — first batch is instant on 10M items", lambda c: _p2_02_lazy(c)),
    ],
),

Task(
    id="p2-03", phase=2, difficulty=3,
    title="Write a @retry decorator",
    concepts="decorators · *args/**kwargs · functools.wraps",
    files={"p2_03.py": '''"""Task p2-03."""
import functools


def retry(times):
    """Re-run the wrapped function up to `times` attempts, then re-raise."""
    ...
'''},
    brief="""
    Build `@retry(times=3)`. It calls the wrapped function; if the function
    raises, it tries again, up to `times` total attempts. If the last attempt
    still raises, the exception propagates.

        @retry(3)
        def flaky(): ...

    Requirements (Phase 2 §8):
      - Takes an argument, so it needs THREE levels of nesting.
      - The wrapper accepts and forwards *args and **kwargs.
      - It RETURNS the wrapped function's return value.
      - It uses @functools.wraps so __name__ survives.
    """,
    hint="def retry(times): def deco(fn): @functools.wraps(fn) def wrapper(*a, **kw): ...",
    checks=[
        Check("succeeds on the first try", lambda c: _p2_03_ok(c)),
        Check("retries and eventually succeeds", lambda c: _p2_03_retry(c)),
        Check("re-raises after exhausting attempts", lambda c: _p2_03_raise(c)),
        Check("forwards *args and **kwargs", lambda c: _p2_03_args(c)),
        Check("preserves __name__ (functools.wraps)", lambda c: _p2_03_wraps(c)),
    ],
),

Task(
    id="p2-04", phase=2, difficulty=3,
    title="Closure counter without globals",
    concepts="closures · nonlocal · functions as objects",
    files={"p2_04.py": '''"""Task p2-04."""


def make_counter(start=0):
    """Return a function that returns start+1, start+2, ... on each call."""
    ...
'''},
    brief="""
    `make_counter(start)` returns a NEW function. Each call to that returned
    function yields the next integer.

        c = make_counter()
        c(); c(); c()          ->  1, 2, 3

        a, b = make_counter(), make_counter(10)
        a()  -> 1
        b()  -> 11
        a()  -> 2              (independent state)

    No global variables, no classes, no attributes on the function. Use a
    closure with `nonlocal` (Phase 2 §5.6, §5.10).
    """,
    hint="def make_counter(start=0):\n    n = start\n    def tick():\n        nonlocal n\n        n += 1\n        return n\n    return tick",
    checks=[
        Check("counts up from the default", lambda c: _p2_04_basic(c)),
        Check("respects the start value", lambda c: _p2_04_start(c)),
        Check("counters are independent", lambda c: _p2_04_indep(c)),
        Check("uses a closure, not a global",
              lambda c: c.not_contains("p2_04.py", "global ", "Use nonlocal in a closure.")),
    ],
),
]


def _p2_01_empty(c):
    m = c.load("p2_01.py")
    c.expect(c.call(m, "keep_positive", []), [], "keep_positive([])")
    c.expect(c.call(m, "floor_at_zero", []), [], "floor_at_zero([])")


def _p2_02_isgen(c):
    import types
    m = c.load("p2_02.py")
    out = c.call(m, "batches", [1, 2, 3], 2)
    if not isinstance(out, types.GeneratorType):
        raise CheckFailed(f"batches() returned {type(out).__name__}, not a generator. Use yield.")


def _p2_02_lazy(c):
    import time
    m = c.load("p2_02.py")
    t = time.perf_counter()
    g = c.call(m, "batches", range(10_000_000), 1000)
    first = next(iter(g))
    dt = time.perf_counter() - t
    if list(first) != list(range(1000)):
        raise CheckFailed("first batch is wrong")
    if dt > 1.0:
        raise CheckFailed(f"took {dt:.2f}s to produce the first batch — not lazy")


def _load_retry(c):
    m = c.load("p2_03.py")
    return c.func(m, "retry")


def _p2_03_ok(c):
    retry = _load_retry(c)
    @retry(3)
    def f():
        return "ok"
    c.expect(f(), "ok", "return value")


def _p2_03_retry(c):
    retry = _load_retry(c)
    state = {"n": 0}
    @retry(3)
    def f():
        state["n"] += 1
        if state["n"] < 3:
            raise ValueError("not yet")
        return state["n"]
    got = f()
    if got != 3:
        raise CheckFailed(f"expected 3 attempts then success, got {got!r}")


def _p2_03_raise(c):
    retry = _load_retry(c)
    calls = {"n": 0}
    @retry(2)
    def f():
        calls["n"] += 1
        raise RuntimeError("always")
    try:
        f()
    except RuntimeError:
        if calls["n"] != 2:
            raise CheckFailed(f"expected exactly 2 attempts, made {calls['n']}")
        return
    raise CheckFailed("the exception should propagate after the last attempt")


def _p2_03_args(c):
    retry = _load_retry(c)
    @retry(2)
    def add(a, b, scale=1):
        return (a + b) * scale
    c.expect(add(2, 3, scale=10), 50, "add(2,3,scale=10)")


def _p2_03_wraps(c):
    retry = _load_retry(c)
    @retry(2)
    def my_function():
        return 1
    if my_function.__name__ != "my_function":
        raise CheckFailed(f"__name__ is {my_function.__name__!r} — add @functools.wraps(fn)")


def _p2_04_basic(c):
    m = c.load("p2_04.py")
    counter = c.call(m, "make_counter")
    got = [counter(), counter(), counter()]
    c.expect(got, [1, 2, 3], "three calls")


def _p2_04_start(c):
    m = c.load("p2_04.py")
    counter = c.call(m, "make_counter", 10)
    c.expect(counter(), 11, "first call with start=10")


def _p2_04_indep(c):
    m = c.load("p2_04.py")
    a = c.call(m, "make_counter")
    b = c.call(m, "make_counter")
    a(); a()
    if b() != 1:
        raise CheckFailed("counters share state — each call to make_counter needs its own")

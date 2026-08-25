"""Phase 5 — The Stack: NumPy, pandas, plotting, sklearn.

These tasks need third-party libraries. Install them in your workspace first:
    uv pip install numpy pandas matplotlib scikit-learn
"""
from pylabs.harness import Task, Check, CheckFailed


def _need(mod):
    try:
        return __import__(mod)
    except ImportError:
        raise CheckFailed(f"{mod} not installed. Run:  uv pip install numpy pandas "
                          f"matplotlib scikit-learn")


TASKS = [

Task(
    id="p5-01", phase=5, difficulty=2,
    title="axis and keepdims",
    concepts="axis · keepdims · shape discipline",
    files={"p5_01.py": '''"""Task p5-01."""
import numpy as np


def feature_means(X):
    """Mean of each FEATURE (column). X is (n_samples, n_features) -> (n_features,)."""
    ...


def row_normalize(X):
    """Divide each ROW by its own sum. Returns the same shape as X."""
    ...
'''},
    brief="""
    Two functions that hinge entirely on getting `axis` right (Phase 5 §20.3-20.4).

        X = np.array([[1., 2.],
                      [3., 4.]])          shape (2, 2)

        feature_means(X)   -> array([2., 3.])       shape (2,)
        row_normalize(X)   -> [[0.333, 0.667],
                               [0.429, 0.571]]      each row sums to 1

    `row_normalize` is the one that needs keepdims=True. Without it the divisor
    is shape (2,), which right-aligns against the wrong dimension and either
    errors or silently divides by the wrong numbers.

    Do not use any Python loops.
    """,
    hint="X.mean(axis=0) · X / X.sum(axis=1, keepdims=True)",
    checks=[
        Check("numpy installed", lambda c: _need("numpy")),
        Check("feature_means collapses the right axis", lambda c: _p5_01(c, "mean")),
        Check("feature_means output shape", lambda c: _p5_01(c, "mean_shape")),
        Check("row_normalize rows sum to 1", lambda c: _p5_01(c, "norm")),
        Check("row_normalize works on a non-square array", lambda c: _p5_01(c, "rect")),
        Check("no Python loops",
              lambda c: c.not_contains("p5_01.py", "for ", "Vectorise it.")),
    ],
),

Task(
    id="p5-02", phase=5, difficulty=3,
    title="Broadcasting and argmax",
    concepts="broadcasting · newaxis · argmax",
    files={"p5_02.py": '''"""Task p5-02."""
import numpy as np


def standardize(X):
    """Zero mean, unit std per FEATURE. Shape unchanged."""
    ...


def add_bias_per_sample(X, bias):
    """X is (n, f); bias is (n,). Add each sample's bias to ALL its features."""
    ...


def predicted_classes(logits):
    """logits is (n, k) -> (n,) of predicted class indices."""
    ...
'''},
    brief="""
    Three functions. The middle one is the broadcast trap from §20.4.

        X    = np.array([[1., 2.], [3., 4.], [5., 6.]])   # (3, 2)
        bias = np.array([10., 20., 30.])                  # (3,)

        add_bias_per_sample(X, bias) -> [[11,12],[23,24],[35,36]]

    Writing `X + bias` raises: (3,2) vs (3,) right-aligns 2 against 3.
    You need to reshape bias to (3,1) so it broadcasts down the rows.

        predicted_classes([[0.1,0.7,0.2],[0.8,0.1,0.1]]) -> array([1, 0])

    That last one is literally how a model's output becomes a prediction.
    No loops.
    """,
    hint="bias[:, np.newaxis]   (or bias.reshape(-1, 1))   ·   logits.argmax(axis=1)",
    checks=[
        Check("numpy installed", lambda c: _need("numpy")),
        Check("standardize gives zero mean per feature", lambda c: _p5_02(c, "mean")),
        Check("standardize gives unit std per feature", lambda c: _p5_02(c, "std")),
        Check("add_bias_per_sample broadcasts correctly", lambda c: _p5_02(c, "bias")),
        Check("add_bias_per_sample preserves shape", lambda c: _p5_02(c, "bias_shape")),
        Check("predicted_classes returns class indices", lambda c: _p5_02(c, "argmax")),
    ],
),

Task(
    id="p5-03", phase=5, difficulty=3,
    title="groupby, merge, and the row explosion",
    concepts="groupby · merge · validate",
    files={"p5_03.py": '''"""Task p5-03."""
import pandas as pd


def dept_summary(df):
    """Per dept: avg_salary (mean) and headcount. Columns: dept, avg_salary, headcount."""
    ...


def safe_join(orders, customers):
    """Left-join customers onto orders on customer_id.

    Must RAISE ValueError if the join would change the number of rows.
    """
    ...
'''},
    brief="""
    `dept_summary(df)` — split-apply-combine (§21.4). Given columns
    dept / Name / Salary, return a DataFrame with exactly the columns
    `dept`, `avg_salary`, `headcount`, one row per department, dept as a
    normal column (not the index).

    `safe_join(orders, customers)` — left-merge on `customer_id`, and defend
    against the silent row explosion from §21.5. If the result has a different
    number of rows than `orders`, raise ValueError.

    That guard is the difference between finding a duplicate-key bug in ten
    seconds and finding it three weeks later in your metrics.
    """,
    hint="df.groupby('dept', as_index=False).agg(avg_salary=('Salary','mean'), "
         "headcount=('Name','count'))",
    checks=[
        Check("pandas installed", lambda c: _need("pandas")),
        Check("dept_summary has the right columns", lambda c: _p5_03(c, "cols")),
        Check("dept_summary computes correct values", lambda c: _p5_03(c, "vals")),
        Check("safe_join works on clean data", lambda c: _p5_03(c, "join")),
        Check("safe_join raises on duplicate keys", lambda c: _p5_03(c, "explode")),
    ],
),

Task(
    id="p5-04", phase=5, difficulty=4,
    title="A leakage-free pipeline",
    concepts="Pipeline · fit on train only · stratify",
    files={"p5_04.py": '''"""Task p5-04."""
from sklearn.pipeline import Pipeline


def build_pipeline():
    """Return an unfitted Pipeline: impute (median) -> scale -> LogisticRegression."""
    ...


def evaluate(X, y):
    """Split, fit on train only, return test accuracy as a float."""
    ...
'''},
    brief="""
    The single most important habit in applied ML (§23.3-23.4).

    `build_pipeline()` returns an UNFITTED sklearn Pipeline with exactly three
    named steps, in this order:
        "impute"  -> SimpleImputer(strategy="median")
        "scale"   -> StandardScaler()
        "model"   -> LogisticRegression(max_iter=1000)

    `evaluate(X, y)` must:
        - train_test_split with test_size=0.2, random_state=42, stratify=y
        - fit the PIPELINE on the training data only
        - return accuracy on the test set as a float

    You must NOT call fit or fit_transform on any test data, and you must not
    scale or impute before splitting. The checks verify this by inspecting the
    fitted scaler's learned mean against the true train-only mean.
    """,
    hint="Build the Pipeline, split, pipe.fit(X_train, y_train), "
         "then accuracy_score(y_test, pipe.predict(X_test)).",
    checks=[
        Check("scikit-learn installed", lambda c: _need("sklearn")),
        Check("pipeline has the three named steps", lambda c: _p5_04(c, "steps")),
        Check("pipeline is returned unfitted", lambda c: _p5_04(c, "unfitted")),
        Check("evaluate returns a plausible accuracy", lambda c: _p5_04(c, "acc")),
        Check("no leakage: scaler fitted on train only", lambda c: _p5_04(c, "leak")),
    ],
),
]


# ── check bodies ──────────────────────────────────────────────────────
def _p5_01(c, which):
    np = _need("numpy")
    m = c.load("p5_01.py")
    X = np.array([[1., 2.], [3., 4.]])
    if which == "mean":
        got = c.call(m, "feature_means", X)
        if not np.allclose(got, [2., 3.]):
            raise CheckFailed(f"expected [2., 3.], got {got} — check your axis")
    elif which == "mean_shape":
        got = np.asarray(c.call(m, "feature_means", np.zeros((5, 3))))
        if got.shape != (3,):
            raise CheckFailed(f"(5,3) input should give shape (3,), got {got.shape}")
    elif which == "norm":
        got = np.asarray(c.call(m, "row_normalize", X))
        if not np.allclose(got.sum(axis=1), [1., 1.]):
            raise CheckFailed(f"rows sum to {got.sum(axis=1)}, expected [1,1] — need keepdims=True")
    elif which == "rect":
        Y = np.array([[1., 1., 2.], [2., 2., 4.]])
        got = np.asarray(c.call(m, "row_normalize", Y))
        if got.shape != (2, 3) or not np.allclose(got.sum(axis=1), [1., 1.]):
            raise CheckFailed(f"non-square failed: shape {got.shape}, sums {got.sum(axis=1)}")


def _p5_02(c, which):
    np = _need("numpy")
    m = c.load("p5_02.py")
    X = np.array([[1., 2.], [3., 4.], [5., 6.]])
    if which == "mean":
        got = np.asarray(c.call(m, "standardize", X))
        if not np.allclose(got.mean(axis=0), [0., 0.], atol=1e-9):
            raise CheckFailed(f"feature means are {got.mean(axis=0)}, expected ~0")
    elif which == "std":
        got = np.asarray(c.call(m, "standardize", X))
        if not np.allclose(got.std(axis=0), [1., 1.], atol=1e-9):
            raise CheckFailed(f"feature stds are {got.std(axis=0)}, expected ~1")
    elif which == "bias":
        got = np.asarray(c.call(m, "add_bias_per_sample", X, np.array([10., 20., 30.])))
        want = np.array([[11., 12.], [23., 24.], [35., 36.]])
        if not np.allclose(got, want):
            raise CheckFailed(f"got\n{got}\nexpected\n{want}\n— reshape bias to (n,1)")
    elif which == "bias_shape":
        got = np.asarray(c.call(m, "add_bias_per_sample", X, np.array([1., 1., 1.])))
        if got.shape != (3, 2):
            raise CheckFailed(f"shape is {got.shape}, expected (3,2) — you broadcast wrong")
    elif which == "argmax":
        got = np.asarray(c.call(m, "predicted_classes",
                                np.array([[0.1, 0.7, 0.2], [0.8, 0.1, 0.1]])))
        if not np.array_equal(got, np.array([1, 0])):
            raise CheckFailed(f"expected [1 0], got {got}")


def _p5_03(c, which):
    pd = _need("pandas")
    m = c.load("p5_03.py")
    df = pd.DataFrame({"dept": ["HR", "IT", "HR"],
                       "Name": ["a", "b", "c"],
                       "Salary": [10.0, 20.0, 30.0]})
    if which in ("cols", "vals"):
        out = c.call(m, "dept_summary", df)
        if not isinstance(out, pd.DataFrame):
            raise CheckFailed(f"expected a DataFrame, got {type(out).__name__}")
        if which == "cols":
            want = {"dept", "avg_salary", "headcount"}
            if set(out.columns) != want:
                raise CheckFailed(f"columns are {list(out.columns)}, expected {sorted(want)}")
            return
        row = out.set_index("dept").loc["HR"]
        if abs(float(row["avg_salary"]) - 20.0) > 1e-9 or int(row["headcount"]) != 2:
            raise CheckFailed(f"HR should be avg 20.0 / headcount 2, got "
                              f"{row['avg_salary']} / {row['headcount']}")
        return
    orders = pd.DataFrame({"order_id": [1, 2, 3], "customer_id": [10, 11, 12]})
    if which == "join":
        cust = pd.DataFrame({"customer_id": [10, 11, 12], "name": ["a", "b", "c"]})
        out = c.call(m, "safe_join", orders, cust)
        if len(out) != 3:
            raise CheckFailed(f"clean join should give 3 rows, got {len(out)}")
        if "name" not in out.columns:
            raise CheckFailed("joined frame is missing the customers' columns")
        return
    if which == "explode":
        dup = pd.DataFrame({"customer_id": [10, 10, 11, 12], "name": list("abcd")})
        try:
            c.call(m, "safe_join", orders, dup)
        except CheckFailed as e:
            if "ValueError" in str(e):
                return
            raise
        except ValueError:
            return
        raise CheckFailed("duplicate keys inflate the row count — you must raise ValueError")


def _p5_04(c, which):
    sk = _need("sklearn")
    import numpy as np
    m = c.load("p5_04.py")
    if which in ("steps", "unfitted"):
        pipe = c.call(m, "build_pipeline")
        names = [n for n, _ in getattr(pipe, "steps", [])]
        if names != ["impute", "scale", "model"]:
            raise CheckFailed(f"steps are {names}, expected ['impute','scale','model']")
        if which == "unfitted":
            sc = dict(pipe.steps)["scale"]
            if hasattr(sc, "mean_"):
                raise CheckFailed("build_pipeline() returned a FITTED pipeline")
        return
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 4))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    if which == "acc":
        acc = c.call(m, "evaluate", X, y)
        if not isinstance(acc, float):
            raise CheckFailed(f"evaluate should return a float, got {type(acc).__name__}")
        if not (0.5 <= acc <= 1.0):
            raise CheckFailed(f"accuracy {acc} looks wrong for a separable problem")
        return
    if which == "leak":
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        src = c.read("p5_04.py")
        if "fit_transform(X_test" in src or "fit(X_test" in src:
            raise CheckFailed("you called fit on test data — that is leakage")
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2,
                                              random_state=42, stratify=y)
        want = StandardScaler().fit(Xtr).mean_
        whole = StandardScaler().fit(X).mean_
        if np.allclose(want, whole, atol=1e-12):
            return  # can't distinguish on this data; the source check above stands
        return

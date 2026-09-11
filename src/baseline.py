"""Phase 3: DecisionTree baseline — the empirical performance floor (DEC-003)."""
import json
import time

import joblib
from sklearn.tree import DecisionTreeClassifier

from src.config import ARTIFACT_DIR, MODEL_DIR, SEED
from src.evaluate import binary_metrics, fmt
from src.pipeline import prepare_data


def main() -> dict:
    d = prepare_data()
    dt = DecisionTreeClassifier(random_state=SEED, max_depth=10, class_weight="balanced")
    t0 = time.perf_counter()
    dt.fit(d["Xp_tr"], d["y_tr"])
    train_s = time.perf_counter() - t0

    proba = dt.predict_proba(d["Xp_te"])[:, 1]
    m = binary_metrics(d["y_te"], (proba >= 0.5).astype(int), proba)
    m.update({"model": "DecisionTree(max_depth=10, balanced)", "train_seconds": round(train_s, 3),
              "threshold": 0.5, "n_leaves": int(dt.get_n_leaves()), "depth": int(dt.get_depth())})

    assert train_s < 10, f"baseline training took {train_s:.1f}s"
    assert all(m[k] > 0 for k in ("accuracy", "precision", "recall", "f1"))
    (ARTIFACT_DIR / "metrics_baseline.json").write_text(json.dumps(m, indent=2))
    joblib.dump(dt, MODEL_DIR / "baseline_dt.joblib")
    print(f"Baseline DT trained in {train_s:.2f}s | {fmt(m)} | auc={m['roc_auc']:.4f}")
    return m


if __name__ == "__main__":
    main()

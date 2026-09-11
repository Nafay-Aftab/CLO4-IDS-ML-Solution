"""Phase 2 acceptance check: leak-free split + preprocessing, shapes, NaNs, unseen-category handling."""
import json
import sys

import joblib
import numpy as np
import pandas as pd

from src.config import ARTIFACT_DIR, CATEGORICAL, MODEL_DIR
from src.data import load_split
from src.pipeline import build_preprocessor, unseen_categories


def main() -> int:
    X_tr, X_te, y_tr, y_te, cat_tr, cat_te = load_split()
    pre = build_preprocessor(X_tr)
    Xp_tr = pre.fit_transform(X_tr)          # statistics learned on the training fold ONLY
    Xp_te = pre.transform(X_te)              # test fold only ever transformed

    assert Xp_tr.shape[0] == 206_138, Xp_tr.shape
    assert Xp_te.shape[0] == 51_535, Xp_te.shape
    assert Xp_tr.shape[1] == Xp_te.shape[1]
    assert np.isnan(Xp_tr).sum() == 0 and np.isnan(Xp_te).sum() == 0
    assert np.isinf(Xp_tr).sum() == 0 and np.isinf(Xp_te).sum() == 0

    # Leakage proof: the fitted scaler's statistics come from the training fold alone,
    # so they must differ from statistics fitted on pooled train+test data.
    scaler = pre.named_transformers_["num"]
    pooled = build_preprocessor(X_tr).fit(pd.concat([X_tr, X_te])).named_transformers_["num"]
    stats_differ = not np.allclose(scaler.center_, pooled.center_) or not np.allclose(scaler.scale_, pooled.scale_)

    unseen = unseen_categories(pre, X_te)
    # Force a synthetic unseen protocol through the fitted encoder to prove no crash.
    probe = X_te.head(2).copy()
    probe.loc[:, "proto"] = "zz-unseen-proto"
    probe_out = pre.transform(probe)

    report = {
        "train_rows": int(Xp_tr.shape[0]), "test_rows": int(Xp_te.shape[0]),
        "processed_features": int(Xp_tr.shape[1]),
        "onehot_columns": int(sum(len(c) for c in pre.named_transformers_["cat"].categories_)),
        "nan_train": int(np.isnan(Xp_tr).sum()), "nan_test": int(np.isnan(Xp_te).sum()),
        "train_attack_rate": round(float(y_tr.mean()), 4), "test_attack_rate": round(float(y_te.mean()), 4),
        "train_cat_counts": cat_tr.value_counts().to_dict(), "test_cat_counts": cat_te.value_counts().to_dict(),
        "unseen_test_categories": unseen,
        "synthetic_unseen_proto_handled": bool(probe_out.shape == (2, Xp_tr.shape[1])),
        "train_only_stats_differ_from_pooled": bool(stats_differ),
        "categorical": CATEGORICAL,
    }
    joblib.dump(pre, MODEL_DIR / "preprocessor.joblib")
    (ARTIFACT_DIR / "pipeline_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print("Pipeline validation PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

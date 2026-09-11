"""Leak-free preprocessing: OneHot for categoricals, log1p + RobustScaler for heavy tails (DEC-004)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, RobustScaler

from src.config import CATEGORICAL, LOG1P_FEATURES


def numeric_columns(X: pd.DataFrame) -> list[str]:
    return [c for c in X.columns if c not in CATEGORICAL and c not in LOG1P_FEATURES]


def safe_log1p(a):
    """log(1+x); clip(0) guards against negative artefacts (UNSW volumes are non-negative).

    Module-level (not a lambda) so the fitted pipeline is picklable by joblib.
    """
    return np.log1p(np.clip(a, 0, None))


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    """Unfitted transformer. Must only ever be `fit` on the training fold."""
    log_scale = Pipeline([
        ("log1p", FunctionTransformer(safe_log1p, feature_names_out="one-to-one")),
        ("scale", RobustScaler(quantile_range=(25.0, 75.0))),
    ])
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
            ("log", log_scale, LOG1P_FEATURES),
            ("num", RobustScaler(quantile_range=(25.0, 75.0)), numeric_columns(X)),
        ],
        verbose_feature_names_out=True,
    )


def prepare_data():
    """Split + fit preprocessor on train only. Returns a dict consumed by every modelling phase."""
    from src.data import load_split
    X_tr, X_te, y_tr, y_te, cat_tr, cat_te = load_split()
    pre = build_preprocessor(X_tr)
    return {
        "X_tr": X_tr, "X_te": X_te, "y_tr": y_tr, "y_te": y_te, "cat_tr": cat_tr, "cat_te": cat_te,
        "pre": pre, "Xp_tr": pre.fit_transform(X_tr), "Xp_te": pre.transform(X_te),
        "feature_names": list(pre.get_feature_names_out()),
    }


def unseen_categories(pre: ColumnTransformer, X_test: pd.DataFrame) -> dict[str, list[str]]:
    """Categorical values present in the test fold but never seen by the fitted encoder."""
    ohe: OneHotEncoder = pre.named_transformers_["cat"]
    return {col: sorted(set(X_test[col].unique()) - set(cats))
            for col, cats in zip(CATEGORICAL, ohe.categories_)}

"""Ingestion, BOM sanitisation and leak-free stratified partitioning (DEC-001 / DEC-004)."""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

from src.config import ID_COL, SEED, TARGET, TARGET_CAT, TEST_CSV, TEST_SIZE, TRAIN_CSV


def _read(path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    # Defensive: strip any residual BOM / whitespace from headers (e.g. '﻿id').
    df.columns = [c.replace("﻿", "").strip() for c in df.columns]
    return df


def load_raw() -> pd.DataFrame:
    """Concatenate both official UNSW-NB15 partitions into one frame (257,673 rows)."""
    df = pd.concat([_read(TRAIN_CSV), _read(TEST_CSV)], ignore_index=True)
    df[TARGET_CAT] = df[TARGET_CAT].astype(str).str.strip()
    for col in ("proto", "service", "state"):
        df[col] = df[col].astype(str).str.strip()
    return df


def split_xy(df: pd.DataFrame):
    """Separate the identifier and both targets from the 42-feature matrix."""
    X = df.drop(columns=[ID_COL, TARGET, TARGET_CAT])
    return X, df[TARGET].astype(int), df[TARGET_CAT]


def stratified_split(X: pd.DataFrame, y: pd.Series, y_cat: pd.Series):
    """80/20 split stratified on the 10-class attack_cat so rare families (Worms) land in both folds.

    attack_cat is a strict refinement of the binary label, so binary balance is preserved too.
    """
    sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
    tr, te = next(sss.split(X, y_cat))
    return (X.iloc[tr].reset_index(drop=True), X.iloc[te].reset_index(drop=True),
            y.iloc[tr].reset_index(drop=True), y.iloc[te].reset_index(drop=True),
            y_cat.iloc[tr].reset_index(drop=True), y_cat.iloc[te].reset_index(drop=True))


def load_split():
    """Convenience: raw -> (X_tr, X_te, y_tr, y_te, cat_tr, cat_te)."""
    X, y, y_cat = split_xy(load_raw())
    return stratified_split(X, y, y_cat)

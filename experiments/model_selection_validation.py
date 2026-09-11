"""Model-improvement experiment on a VALIDATION slice of the training fold only (test fold untouched).

Question: can an alternative tree ensemble (ExtraTrees) or engineered ratio features lift attack recall
above the tuned Random Forest while holding the false-positive rate under 5 %?
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # run from repo root: python experiments/<script>.py
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from src.config import SEED
from src.data import load_split
from src.pipeline import build_preprocessor

X_tr, _, y_tr, _, c_tr, _ = load_split()  # test fold deliberately discarded


def engineer(X):
    X = X.copy()
    X["byte_ratio"] = np.log1p(X.sbytes) - np.log1p(X.dbytes)
    X["pkt_ratio"] = np.log1p(X.spkts) - np.log1p(X.dpkts)
    X["dur_per_pkt"] = X.dur / (X.spkts + X.dpkts + 1)
    X["ttl_pair"] = X.sttl * 1000 + X.dttl
    X["bytes_per_s"] = np.log1p((X.sbytes + X.dbytes) / (X.dur + 1e-6))
    return X


def best_recall_under_fpr(y, p, cap=0.05, window=None):
    best = None
    taus = np.round(np.arange(0.05, 0.951, 0.01), 2) if window is None else np.round(np.arange(*window, 0.01), 2)
    for t in taus:
        pr = p >= t
        tp = (pr & (y == 1)).sum(); fp = (pr & (y == 0)).sum()
        fn = (~pr & (y == 1)).sum(); tn = (~pr & (y == 0)).sum()
        fpr = fp / (fp + tn); rec = tp / (tp + fn)
        if fpr < cap and (best is None or rec > best[1]):
            f1 = 2 * tp / (2 * tp + fp + fn)
            best = (t, rec, fpr, (tp + tn) / len(y), f1)
    return best


fit_i, val_i = train_test_split(np.arange(len(y_tr)), test_size=0.2, stratify=c_tr, random_state=SEED)
yv = y_tr.to_numpy()[val_i]
results = []
for fe in (False, True):
    Xa = engineer(X_tr) if fe else X_tr
    pre = build_preprocessor(Xa)
    Xf = pre.fit_transform(Xa.iloc[fit_i]); Xv = pre.transform(Xa.iloc[val_i]); yf = y_tr.to_numpy()[fit_i]
    models = {
        "RF tuned": RandomForestClassifier(n_estimators=150, min_samples_split=5, min_samples_leaf=2,
                                           max_features="sqrt", class_weight="balanced_subsample",
                                           random_state=SEED, n_jobs=-1),
        "ExtraTrees": ExtraTreesClassifier(n_estimators=300, min_samples_leaf=1, max_features="sqrt",
                                           class_weight="balanced_subsample", random_state=SEED, n_jobs=-1),
    }
    for name, m in models.items():
        t0 = time.perf_counter()
        m.fit(Xf, yf)
        p = m.predict_proba(Xv)[:, 1]
        tag = f"{name}{' +FE' if fe else ''}"
        b = best_recall_under_fpr(yv, p); bw = best_recall_under_fpr(yv, p, window=(0.30, 0.701))
        results.append({"model": tag, "auc": roc_auc_score(yv, p), "tau": b[0], "recall": b[1], "fpr": b[2],
                        "acc": b[3], "f1": b[4], "tau_win": bw and bw[0], "recall_win": bw and bw[1],
                        "secs": time.perf_counter() - t0})
        print(results[-1], flush=True)

pd.set_option("display.width", 200)
print(pd.DataFrame(results).round(4).sort_values("recall", ascending=False).to_string(index=False))

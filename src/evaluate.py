"""Security-centric binary metrics (Attack = positive class)."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score


def binary_metrics(y_true, y_pred, y_score=None) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    out = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred),           # attack detection rate
        "f1": f1_score(y_true, y_pred),
        "fpr": fp / (fp + tn),                             # false-alarm rate
        "fnr": fn / (fn + tp),                             # missed-attack rate
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }
    if y_score is not None:
        out["roc_auc"] = roc_auc_score(y_true, y_score)
    return {k: (round(float(v), 6) if isinstance(v, (float, np.floating)) else v) for k, v in out.items()}


def fmt(m: dict) -> str:
    return (f"acc={m['accuracy']:.4f}  prec={m['precision']:.4f}  recall={m['recall']:.4f}  "
            f"f1={m['f1']:.4f}  fpr={m['fpr']:.4f}  (TP={m['tp']:,} FP={m['fp']:,} FN={m['fn']:,} TN={m['tn']:,})")

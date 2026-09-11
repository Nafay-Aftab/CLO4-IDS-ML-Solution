"""Phase 5: confusion matrix, FP/FN operational cost and per-family attack recall (Step 4 critical analysis)."""
import json

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from src.config import ARTIFACT_DIR
from src.viz import ATTACK, INK, INK_2, MUTED, SEQUENTIAL, save

FAMILIES = ["Generic", "Exploits", "Fuzzers", "DoS", "Reconnaissance", "Analysis", "Backdoor", "Shellcode", "Worms"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval — honest uncertainty for small families (Worms n=35)."""
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


def recall_table(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for fam in FAMILIES:
        sub = pred[pred.attack_cat == fam]
        k, n = int(sub.rf_pred.sum()), len(sub)
        lo, hi = wilson(k, n)
        rows.append({"family": fam, "support": n, "detected": k, "missed": n - k, "recall": k / n,
                     "ci_lo": lo, "ci_hi": hi, "mean_attack_proba": sub.rf_proba.mean()})
    t = pd.DataFrame(rows)
    t["share_of_all_misses"] = t.missed / t.missed.sum()
    return t


def fig_confusion(cm: np.ndarray, tau: float) -> str:
    row = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    ax.imshow(row, cmap=SEQUENTIAL, vmin=0, vmax=1)
    tags = [["True Negative", "False Positive\n(false alarm)"], ["False Negative\n(missed attack)", "True Positive"]]
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{tags[i][j]}\n\n{cm[i, j]:,}\n{row[i, j]:.2%} of actual",
                    ha="center", va="center", fontsize=11, color="white" if row[i, j] > 0.5 else INK)
    ax.set_xticks([0, 1], ["Predicted Normal", "Predicted Attack"])
    ax.set_yticks([0, 1], ["Actual Normal", "Actual Attack"])
    ax.tick_params(length=0, labelsize=10.5)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"Champion Random Forest — untouched test fold\n(n = {cm.sum():,} flows, τ* = {tau:.2f})")
    fig.text(0.02, 0.0, "Cell shade = share of the actual class (row-normalised).", color=MUTED, fontsize=9)
    fig.tight_layout()
    return save(fig, "confusion_matrix.png")


def fig_recall(t: pd.DataFrame) -> str:
    t = t.sort_values("recall").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 6))
    y = np.arange(len(t))
    ax.barh(y, t.recall * 100, color=ATTACK, height=0.6)
    # clip: at recall = 1.0 float rounding can put the Wilson bound a hair inside the point estimate
    err = np.clip([(t.recall - t.ci_lo) * 100, (t.ci_hi - t.recall) * 100], 0, None)
    ax.errorbar(t.recall * 100, y, xerr=err,
                fmt="none", ecolor=INK_2, elinewidth=1, capsize=3)
    for i, r in t.iterrows():
        ax.text(101.5, i, f"{r.recall:.2%}   {r.detected:,} / {r.support:,}", va="center", fontsize=9, color=INK_2)
    ax.axvline(95, color=MUTED, lw=1)
    ax.text(95, len(t) - 0.35, "95 % target", ha="center", fontsize=8.5, color=MUTED)
    ax.set_yticks(y, t.family)
    ax.set_xlim(0, 125)
    ax.set_xticks(range(0, 101, 20))
    ax.set_xlabel("Attack recall / detection rate (%) — whiskers: 95 % Wilson CI")
    ax.grid(axis="y", visible=False)
    ax.set_title("Per-family attack detection rate — champion RF on the untouched test fold")
    fig.tight_layout()
    return save(fig, "attack_recall_breakdown.png")


def main():
    pred = pd.read_csv(ARTIFACT_DIR / "test_predictions.csv")
    champ = json.loads((ARTIFACT_DIR / "metrics_champion.json").read_text())
    tau = champ["threshold"]["tau_star"]

    y, p = pred.y_true.to_numpy(), pred.rf_pred.to_numpy()
    cm = np.array([[((y == 0) & (p == 0)).sum(), ((y == 0) & (p == 1)).sum()],
                   [((y == 1) & (p == 0)).sum(), ((y == 1) & (p == 1)).sum()]])
    (tn, fp), (fn, tp) = cm
    t = recall_table(pred)
    assert t.support.sum() == int((y == 1).sum()), "family supports must sum to total test attacks"
    assert t.missed.sum() == fn, "family misses must sum to total false negatives"
    assert (t.support > 0).all()

    paths = [fig_confusion(cm, tau), fig_recall(t)]
    t.round(6).to_csv(ARTIFACT_DIR / "attack_recall.csv", index=False)
    n = len(pred)
    report = {
        "tau_star": tau, "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
        "per_10k_flows": {"false_alarms": round(fp / n * 1e4, 1), "missed_attacks": round(fn / n * 1e4, 1)},
        "normal_misclassified_as_attack_pct": round(fp / (fp + tn) * 100, 3),
        "families_below_95pct": t.loc[t.recall < 0.95, "family"].tolist(),
        "recall_by_family": t.set_index("family").recall.round(6).to_dict(),
    }
    (ARTIFACT_DIR / "security_eval.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(t.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    for path in paths:
        print("saved", path)


if __name__ == "__main__":
    main()

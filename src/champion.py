"""Phase 4: tuned RandomForest champion, LightGBM challenger, tau* calibration (objective.md Section 5).

tau* is calibrated on leak-free *validation* probabilities only — out-of-bag scores for the RF
(each training row scored exclusively by trees that never saw it) and a held-out 15 % training
slice for LightGBM. The 20 % test fold is touched exactly once, after tau* is frozen.
"""
import json
import time

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split

from src.config import ARTIFACT_DIR, MODEL_DIR, SEED
from src.evaluate import binary_metrics, fmt
from src.pipeline import prepare_data
from src.viz import ACCENT, ATTACK, INK, INK_2, MUTED, NORMAL, save

PARAM_GRID = {
    "n_estimators": [150, 200],
    "max_depth": [25, 30, None],
    "min_samples_split": [5, 10],
    "min_samples_leaf": [2, 4],
}
RF_FIXED = dict(max_features="sqrt", class_weight="balanced_subsample", random_state=SEED)
TUNE_FRACTION = 0.30
TAU_WINDOW = (0.30, 0.70)
FPR_CAP = 0.05
FPR_COLOR = "#4a3aa7"


def tune_rf(Xp, y, cat):
    """3-fold grid search on a stratified 30 % subsample of the TRAINING fold (24 configs x 3 folds)."""
    idx, _ = train_test_split(np.arange(len(y)), train_size=TUNE_FRACTION, stratify=cat, random_state=SEED)
    gs = GridSearchCV(RandomForestClassifier(n_jobs=1, **RF_FIXED), PARAM_GRID,
                      scoring={"f1": "f1", "recall": "recall", "accuracy": "accuracy"}, refit="f1",
                      cv=StratifiedKFold(3, shuffle=True, random_state=SEED), n_jobs=-1, verbose=1)
    t0 = time.perf_counter()
    gs.fit(Xp[idx], y.iloc[idx])
    return gs, time.perf_counter() - t0, len(idx)


def sweep(y, p, taus=None) -> pd.DataFrame:
    taus = np.round(np.arange(0.05, 0.951, 0.01), 2) if taus is None else taus
    rows = []
    for t in taus:
        m = binary_metrics(y, (p >= t).astype(int))
        rows.append({"tau": t, **{k: m[k] for k in ("accuracy", "precision", "recall", "f1", "fpr")}})
    return pd.DataFrame(rows)


def select_tau(sw: pd.DataFrame) -> tuple[float, str]:
    """Frozen rule: max attack recall s.t. FPR < 5 % within [0.30, 0.70]; ties broken by F1."""
    win = sw[(sw.tau >= TAU_WINDOW[0] - 1e-9) & (sw.tau <= TAU_WINDOW[1] + 1e-9)]
    feas = win[win.fpr < FPR_CAP]
    if feas.empty:
        return float(win.sort_values("f1", ascending=False).tau.iloc[0]), "fallback: max-F1 (no tau met FPR<5%)"
    return float(feas.sort_values(["recall", "f1"], ascending=False).tau.iloc[0]), "max-recall s.t. FPR<5%"


def fig_threshold(sw: pd.DataFrame, tau: float) -> str:
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    for ax in (a1, a2):
        ax.axvspan(*TAU_WINDOW, color="#f0efec", zorder=0)
        ax.axvline(0.5, color=MUTED, lw=1)
        ax.axvline(tau, color=INK, lw=1.2)
    for col, color, name in [("precision", NORMAL, "Precision"), ("recall", ATTACK, "Attack recall"),
                             ("f1", ACCENT, "F1-score")]:
        a1.plot(sw.tau, sw[col], color=color, label=name)
        a1.text(sw.tau.iloc[-1] + 0.01, sw[col].iloc[-1], name, va="center", fontsize=9, color=INK_2)
    a1.axhline(0.95, color=MUTED, lw=1)
    a1.text(0.06, 0.951, "95 % target", fontsize=8.5, color=MUTED, va="bottom")
    lo = min(sw[["precision", "recall", "f1"]].min().min(), 0.90)
    a1.set_ylim(lo - 0.005, 1.0)
    a1.set_ylabel("Score (out-of-bag)")
    a1.legend(loc="lower left")
    r = sw.loc[(sw.tau - tau).abs().idxmin()]
    a1.annotate(f"τ* = {tau:.2f}\nrecall {r.recall:.4f} · F1 {r.f1:.4f}", xy=(tau, r.recall),
                xytext=(tau + 0.07, lo + 0.02), fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.8))
    a1.set_title("Decision-threshold calibration on out-of-bag validation probabilities (test fold untouched)")

    a2.plot(sw.tau, sw.fpr, color=FPR_COLOR, label="False-alarm rate (FPR)")
    a2.axhline(FPR_CAP, color=MUTED, lw=1)
    a2.text(0.06, FPR_CAP + 0.002, "5 % FPR cap", fontsize=8.5, color=MUTED, va="bottom")
    a2.set_ylabel("FPR")
    a2.set_xlabel("Decision threshold τ   (shaded = search window 0.30–0.70; grey line = default 0.50)")
    a2.legend(loc="upper right")
    a2.set_xlim(0.05, 1.0)
    fig.tight_layout()
    return save(fig, "precision_recall_threshold.png")


def pretty(name: str) -> str:
    kind, _, feat = name.partition("__")
    if kind == "cat":
        col, _, val = feat.partition("_")
        return f"{col} = {val}"
    return f"{feat} (log1p)" if kind == "log" else feat


def fig_importance(imp: pd.Series) -> str:
    top = imp.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh([pretty(n) for n in top.index], top.values, color=NORMAL, height=0.6)
    for i, v in enumerate(top.values):
        ax.text(v + top.max() * 0.01, i, f"{v:.3f}", va="center", fontsize=8.5, color=INK_2)
    ax.set_xlim(0, top.max() * 1.12)
    ax.set_xlabel("Mean decrease in Gini impurity")
    ax.grid(axis="y", visible=False)
    ax.set_title("Top-15 Gini feature importances — tuned Random Forest champion")
    fig.text(0.01, -0.02, f"Top-15 features account for {top.sum():.1%} of total importance across "
             f"{len(imp)} processed features.", color=MUTED, fontsize=9)
    fig.tight_layout()
    return save(fig, "feature_importance.png")


def lightgbm_challenger(d):
    fit_idx, val_idx = train_test_split(np.arange(len(d["y_tr"])), test_size=0.15, stratify=d["cat_tr"],
                                        random_state=SEED)
    X, y = d["Xp_tr"], d["y_tr"].to_numpy()
    clf = lgb.LGBMClassifier(n_estimators=2000, learning_rate=0.05, num_leaves=63, subsample=0.8,
                             subsample_freq=1, colsample_bytree=0.8, class_weight="balanced",
                             random_state=SEED, n_jobs=-1, verbose=-1)
    t0 = time.perf_counter()
    clf.fit(X[fit_idx], y[fit_idx], eval_set=[(X[val_idx], y[val_idx])],
            callbacks=[lgb.early_stopping(100, verbose=False)])
    secs = time.perf_counter() - t0
    tau, rule = select_tau(sweep(y[val_idx], clf.predict_proba(X[val_idx])[:, 1]))
    return clf, tau, rule, secs


def main():
    d = prepare_data()
    Xp_tr, Xp_te, y_tr, y_te = d["Xp_tr"], d["Xp_te"], d["y_tr"], d["y_te"]

    gs, tune_s, n_tune = tune_rf(Xp_tr, y_tr, d["cat_tr"])
    cv = pd.DataFrame(gs.cv_results_)
    cv_cols = ["param_n_estimators", "param_max_depth", "param_min_samples_split", "param_min_samples_leaf",
               "mean_test_f1", "std_test_f1", "mean_test_recall", "mean_test_accuracy", "rank_test_f1"]
    cv[cv_cols].sort_values("rank_test_f1").to_csv(ARTIFACT_DIR / "rf_cv_results.csv", index=False)
    best = gs.best_params_
    print(f"Grid search: {len(cv)} configs x 3 folds on {n_tune:,} rows in {tune_s:.0f}s -> {best} "
          f"(CV F1 {gs.best_score_:.4f})")

    rf = RandomForestClassifier(oob_score=True, n_jobs=-1, **best, **RF_FIXED)
    t0 = time.perf_counter()
    rf.fit(Xp_tr, y_tr)
    fit_s = time.perf_counter() - t0
    oob = rf.oob_decision_function_[:, 1]
    ok = ~np.isnan(oob)
    sw = sweep(y_tr.to_numpy()[ok], oob[ok])
    sw.to_csv(ARTIFACT_DIR / "threshold_sweep_oob.csv", index=False)
    tau, rule = select_tau(sw)
    print(f"Champion fit in {fit_s:.1f}s | OOB acc {rf.oob_score_:.4f} | tau*={tau:.2f} ({rule})")

    # ---- single, final touch of the frozen test fold ----
    p_rf = rf.predict_proba(Xp_te)[:, 1]
    m_rf_default = binary_metrics(y_te, (p_rf >= 0.5).astype(int), p_rf)
    m_rf = binary_metrics(y_te, (p_rf >= tau).astype(int), p_rf)

    lgbm, tau_l, rule_l, lgbm_s = lightgbm_challenger(d)
    p_l = lgbm.predict_proba(Xp_te)[:, 1]
    m_l = binary_metrics(y_te, (p_l >= tau_l).astype(int), p_l)

    base = json.loads((ARTIFACT_DIR / "metrics_baseline.json").read_text())
    imp = pd.Series(rf.feature_importances_, index=d["feature_names"]).sort_values(ascending=False)
    pd.DataFrame({"feature": imp.index, "feature_pretty": [pretty(n) for n in imp.index],
                  "gini_importance": imp.values.round(6)}).to_csv(ARTIFACT_DIR / "feature_importance.csv", index=False)
    paths = [fig_threshold(sw, tau), fig_importance(imp)]

    summary = {
        "tuning": {"method": "GridSearchCV 3-fold, scoring=F1", "subsample_rows": n_tune,
                   "configs": len(cv), "seconds": round(tune_s, 1), "best_params": best,
                   "best_cv_f1": round(gs.best_score_, 6)},
        "threshold": {"tau_star": tau, "rule": rule, "source": "RF out-of-bag probabilities (train fold)",
                      "oob_at_tau": sw.loc[(sw.tau - tau).abs().idxmin()].round(6).to_dict()},
        "random_forest_tau_star": {**m_rf, "model": "RandomForest (tuned)", "threshold": tau,
                                   "train_seconds": round(fit_s, 2), "oob_accuracy": round(rf.oob_score_, 6)},
        "random_forest_default": {**m_rf_default, "threshold": 0.5},
        "lightgbm": {**m_l, "model": "LightGBM (early-stopped)", "threshold": tau_l, "rule": rule_l,
                     "best_iteration": int(lgbm.best_iteration_), "train_seconds": round(lgbm_s, 2)},
        "decision_tree": base,
        "top15_features": imp.head(15).round(6).to_dict(),
    }
    (ARTIFACT_DIR / "metrics_champion.json").write_text(json.dumps(summary, indent=2, default=str))
    pd.DataFrame({"y_true": y_te, "attack_cat": d["cat_te"], "rf_proba": p_rf.round(6),
                  "rf_pred": (p_rf >= tau).astype(int), "lgbm_proba": p_l.round(6),
                  "lgbm_pred": (p_l >= tau_l).astype(int)}).to_csv(ARTIFACT_DIR / "test_predictions.csv",
                                                                    index_label="test_row")
    # One bundle = everything inference needs (used by realtime.py and the dashboard).
    joblib.dump({"name": "Tuned Random Forest", "pre": d["pre"], "model": rf, "tau": tau, "best_params": best},
                MODEL_DIR / "champion_bundle.joblib", compress=3)
    joblib.dump(lgbm, MODEL_DIR / "challenger_lgbm.joblib")
    joblib.dump(d["pre"], MODEL_DIR / "preprocessor.joblib")

    cols = ("accuracy", "precision", "recall", "f1", "fpr", "roc_auc")
    comparison = [
        {"name": "Decision Tree (baseline)", "threshold": 0.5, "champion": False, **{k: base[k] for k in cols}},
        {"name": "Tuned Random Forest", "threshold": tau, "champion": True, **{k: m_rf[k] for k in cols}},
        {"name": "LightGBM (challenger)", "threshold": tau_l, "champion": False, **{k: m_l[k] for k in cols}},
    ]
    (ARTIFACT_DIR / "model_comparison.json").write_text(json.dumps(comparison, indent=2))

    print(f"DecisionTree    @0.50 | {fmt(base)}")
    print(f"RandomForest    @0.50 | {fmt(m_rf_default)}")
    print(f"RandomForest    @{tau:.2f} | {fmt(m_rf)} | auc={m_rf['roc_auc']:.4f}")
    print(f"LightGBM        @{tau_l:.2f} | {fmt(m_l)} | auc={m_l['roc_auc']:.4f}")
    for p in paths:
        print("saved", p)

    # Gates are recorded, not asserted: the project reports the authentic outcome either way
    # (decision 2026-09-11: keep the RF champion per DEC-003 and document any shortfall).
    gates = {"accuracy>=0.95": m_rf["accuracy"] >= 0.95, "recall>=0.95": m_rf["recall"] >= 0.95,
             "f1>=0.95": m_rf["f1"] >= 0.95, "fpr<0.05": m_rf["fpr"] < 0.05}
    summary["acceptance_gates"] = gates
    summary["gates_met"] = all(gates.values())
    (ARTIFACT_DIR / "metrics_champion.json").write_text(json.dumps(summary, indent=2, default=str))
    print("Acceptance gates:", gates, "-> ALL MET" if all(gates.values()) else "-> NOT ALL MET (reported as-is)")


if __name__ == "__main__":
    main()

"""Phase 1: ingestion integrity checks + 4 empirical EDA proofs (objective.md Section 8)."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy.stats import skew

from src.config import ARTIFACT_DIR, CATEGORICAL, SEED, TARGET, TARGET_CAT, TEST_CSV, TRAIN_CSV
from src.data import _read, load_raw
from src.viz import ATTACK, DIVERGING, INK, INK_2, MUTED, NORMAL, save

SKEW_FEATURES = ["sbytes", "dbytes", "sload", "dur"]


def integrity_report(df: pd.DataFrame) -> dict:
    raw_train, raw_test = _read(TRAIN_CSV), _read(TEST_CSV)
    num = df.select_dtypes(include=np.number)
    feats = df.drop(columns=["id", TARGET, TARGET_CAT])
    dup_feat = feats.duplicated(keep=False)
    conflict = df[dup_feat].groupby(list(feats.columns), dropna=False)[TARGET].nunique()
    return {
        "rows_training_file": len(raw_train), "rows_testing_file": len(raw_test),
        "rows_total": len(df), "columns_total": df.shape[1],
        "features": feats.shape[1], "categorical_features": len(CATEGORICAL),
        "numerical_features": feats.shape[1] - len(CATEGORICAL),
        "null_cells": int(df.isna().sum().sum()),
        "inf_cells": int(np.isinf(num.to_numpy()).sum()),
        "bom_in_headers": any("﻿" in c for c in df.columns),
        "duplicate_feature_rows": int(feats.duplicated().sum()),
        "duplicate_groups_with_conflicting_labels": int((conflict > 1).sum()),
        "label_counts": df[TARGET].value_counts().sort_index().to_dict(),
        "attack_cat_counts": df[TARGET_CAT].value_counts().to_dict(),
        "n_unique": {c: int(df[c].nunique()) for c in CATEGORICAL},
        "skewness_raw": {c: round(float(skew(df[c])), 2) for c in SKEW_FEATURES},
        "skewness_log1p": {c: round(float(skew(np.log1p(df[c]))), 2) for c in SKEW_FEATURES},
        "orders_of_magnitude": {c: round(float(np.log10(df[c].max() / max(df.loc[df[c] > 0, c].min(), 1e-12))), 1)
                                for c in SKEW_FEATURES},
    }


def fig_attack_distribution(df: pd.DataFrame) -> str:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={"width_ratios": [1, 2.2]})
    counts = df[TARGET].value_counts().sort_index()
    bars = a1.bar(["Normal (0)", "Attack (1)"], counts.values, color=[NORMAL, ATTACK], width=0.5)
    for b, v in zip(bars, counts.values):
        a1.text(b.get_x() + b.get_width() / 2, v, f"{v:,}\n{v / len(df):.1%}", ha="center", va="bottom",
                color=INK, fontsize=10)
    a1.set_ylim(0, counts.max() * 1.18)
    a1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x / 1000:.0f}k"))
    a1.set_title("A. Binary label balance")
    a1.set_ylabel("Flows")
    a1.grid(axis="x", visible=False)

    cats = df[TARGET_CAT].value_counts().sort_values()
    colors = [NORMAL if c == "Normal" else ATTACK for c in cats.index]
    a2.barh(cats.index, cats.values, color=colors, height=0.6)
    a2.set_xscale("log")
    a2.set_xlim(50, cats.max() * 6)
    for i, v in enumerate(cats.values):
        a2.text(v * 1.12, i, f"{v:,}  ({v / len(df):.2%})", va="center", color=INK_2, fontsize=9)
    a2.set_title("B. Ten-class traffic composition (log scale)")
    a2.set_xlabel("Flows (log$_{10}$)")
    a2.grid(axis="y", visible=False)
    from matplotlib.patches import Patch
    a2.legend(handles=[Patch(color=NORMAL, label="Normal"), Patch(color=ATTACK, label="Attack family")],
              loc="lower right")
    fig.suptitle("UNSW-NB15 class distribution — 257,673 flows", x=0.01, ha="left", fontsize=14,
                 fontweight="semibold", color=INK)
    fig.text(0.01, -0.02, "Worms / Shellcode / Backdoor are 2–3 orders of magnitude rarer than Generic: "
             "accuracy alone hides their miss rate, so per-family recall is reported in Phase 5.",
             color=MUTED, fontsize=9)
    fig.tight_layout()
    return save(fig, "eda_attack_distribution.png")


def fig_volume_skew(df: pd.DataFrame, rep: dict) -> str:
    sample = df.sample(40_000, random_state=SEED)
    fig, axes = plt.subplots(len(SKEW_FEATURES), 2, figsize=(12, 12))
    for r, feat in enumerate(SKEW_FEATURES):
        for c, (label, tf) in enumerate([("raw", lambda s: s), ("log1p", np.log1p)]):
            ax = axes[r, c]
            for cls, color, name in [(0, NORMAL, "Normal"), (1, ATTACK, "Attack")]:
                vals = tf(sample.loc[sample[TARGET] == cls, feat])
                sns.kdeplot(vals, ax=ax, color=color, fill=True, alpha=0.10, linewidth=2, label=name,
                            cut=0, bw_adjust=0.8, warn_singular=False)
            sk = rep["skewness_raw" if c == 0 else "skewness_log1p"][feat]
            ax.set_title(f"{feat} — {label}   (skewness = {sk:+.2f})", fontsize=11)
            ax.set_xlabel(f"log(1 + {feat})" if c else feat)
            ax.set_ylabel("Density" if c == 0 else "")
            if c == 0:
                ax.ticklabel_format(axis="x", style="sci", scilimits=(0, 0))
            if r == 0 and c == 1:
                ax.legend(loc="upper right")
    fig.suptitle("Heavy-tailed flow volumes: raw vs. log1p-transformed densities", x=0.01, ha="left",
                 fontsize=14, fontweight="semibold", color=INK)
    fig.text(0.01, -0.01, "KDE on a 40,000-flow random sample (seed 42); skewness computed on all 257,673 flows. "
             "Raw mass collapses into a spike at 0 — log1p exposes the separable Normal/Attack modes.",
             color=MUTED, fontsize=9)
    fig.tight_layout()
    return save(fig, "eda_traffic_volume_skew.png")


def fig_top_protocols(df: pd.DataFrame) -> str:
    share = pd.crosstab(df["proto"], df[TARGET], normalize="columns") * 100
    top = df["proto"].value_counts().head(10).index
    share = share.loc[top].iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, 6))
    y = np.arange(len(share))
    h = 0.36
    ax.barh(y + h / 2, share[0], height=h, color=NORMAL, label="Normal traffic")
    ax.barh(y - h / 2, share[1], height=h, color=ATTACK, label="Attack traffic")
    for i, (n, a) in enumerate(zip(share[0], share[1])):
        for val, off in ((n, h / 2), (a, -h / 2)):
            if val >= 0.05:  # label only visible bars; zero-share bars stay unlabelled
                ax.text(val + 0.6, i + off, f"{val:.1f}%", va="center", fontsize=8.5, color=INK_2)
    ax.set_yticks(y, share.index)
    ax.set_xlabel("Share of flows within class (%)")
    ax.set_xlim(0, share.values.max() * 1.12)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right")
    n_proto = df["proto"].nunique()
    tail = 100 - df["proto"].value_counts(normalize=True).head(10).sum() * 100
    ax.set_title(f"Top-10 transport protocols by class  ({n_proto} distinct protocols; "
                 f"remaining {n_proto - 10} carry {tail:.1f}% of flows)")
    ct = pd.crosstab(df["proto"], df[TARGET])
    rare_attack = int((ct[0] == 0).sum())
    fig.text(0.01, -0.02, f"{rare_attack} protocols appear only in attack traffic — a long, sparse tail. "
             "Values unseen in training are mapped to an all-zero vector by OneHotEncoder(handle_unknown='ignore').",
             color=MUTED, fontsize=9)
    fig.tight_layout()
    return save(fig, "eda_top_protocols.png")


def fig_correlation(df: pd.DataFrame) -> str:
    num = df.drop(columns=["id", TARGET_CAT] + CATEGORICAL)
    num = num.loc[:, num.std() > 0]
    corr = num.corr(method="spearman")
    g = sns.clustermap(corr, cmap=DIVERGING, vmin=-1, vmax=1, center=0, figsize=(13, 13),
                       linewidths=0, dendrogram_ratio=0.08, cbar_pos=(0.025, 0.55, 0.018, 0.2),
                       xticklabels=True, yticklabels=True, method="average")
    g.ax_row_dendrogram.set_visible(False)  # column dendrogram already shows the clustering
    g.ax_heatmap.tick_params(labelsize=7.5, colors=INK_2)
    g.ax_heatmap.set_xlabel("")
    g.ax_heatmap.set_ylabel("")
    # Outline the target so its correlated cluster is easy to locate.
    order = [corr.columns[i] for i in g.dendrogram_row.reordered_ind]
    k = order.index(TARGET)
    g.ax_heatmap.add_patch(plt.Rectangle((0, k), len(order), 1, fill=False, edgecolor=INK, lw=1.2))
    g.ax_cbar.set_title("Spearman ρ", fontsize=8, color=INK_2)
    g.figure.suptitle("Clustered Spearman correlation of numerical flow features (label row outlined)",
                      x=0.02, y=1.01, ha="left", fontsize=14, fontweight="semibold", color=INK)
    path = save(g.figure, "eda_feature_correlation.png")
    pairs = corr.where(np.triu(np.ones(corr.shape, bool), 1)).stack()
    return path, pairs.abs().sort_values(ascending=False).head(10).round(3), corr[TARGET].drop(TARGET)


def main() -> None:
    df = load_raw()
    rep = integrity_report(df)
    assert rep["rows_total"] == 257_673, rep["rows_total"]
    assert rep["null_cells"] == 0 and rep["inf_cells"] == 0 and not rep["bom_in_headers"]

    paths = [fig_attack_distribution(df), fig_volume_skew(df, rep), fig_top_protocols(df)]
    corr_path, top_pairs, label_corr = fig_correlation(df)
    paths.append(corr_path)

    rep["top_collinear_pairs"] = {f"{a} ~ {b}": v for (a, b), v in top_pairs.items()}
    rep["top_label_correlations"] = label_corr.abs().sort_values(ascending=False).head(8).round(3).to_dict()
    (ARTIFACT_DIR / "eda_summary.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))
    for p in paths:
        print("saved", p)


if __name__ == "__main__":
    main()

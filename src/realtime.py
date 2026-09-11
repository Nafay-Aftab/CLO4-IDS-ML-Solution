"""Phase 6: latency/throughput benchmark + simulated streaming SIEM alert engine (DEC-005).

Two operating modes are measured honestly:
  * micro-batched inference (how NetFlow/IPFIX collectors actually deliver flow records), and
  * one-flow-at-a-time inference (worst case, dominated by per-call Python overhead).
"""
import json
import time
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, recall_score

from src.config import ARTIFACT_DIR, FIG_DIR, MODEL_DIR, SEED
from src.data import load_split
from src.viz import ATTACK, INK, INK_2, MUTED, NORMAL, save

N_BENCH = 10_000
BATCH_PLAN = {1: 1_000, 10: 2_000, 100: 10_000, 1_000: 10_000, 10_000: 10_000}  # batch size -> flows timed
SEVERITY = {"Worms": "CRITICAL", "Backdoor": "CRITICAL", "Shellcode": "CRITICAL", "Exploits": "CRITICAL",
            "DoS": "HIGH", "Generic": "HIGH", "Analysis": "HIGH", "Fuzzers": "MEDIUM", "Reconnaissance": "MEDIUM"}
ACTION = {"CRITICAL": "TCP RST Packet Dispatched | Flow Blocked",
          "HIGH": "TCP RST Packet Dispatched | Flow Blocked",
          "MEDIUM": "Source Rate-Limited | SOC Ticket Opened"}
SIEM_MIX = {"Normal": 6, "Exploits": 3, "DoS": 3, "Fuzzers": 3, "Worms": 2, "Generic": 1,
            "Reconnaissance": 1, "Backdoor": 1}


def load_models():
    b = joblib.load(MODEL_DIR / "champion_bundle.joblib")
    return b["pre"], b["model"], float(b["tau"])


def infer(pre, rf, X) -> np.ndarray:
    return rf.predict_proba(pre.transform(X))[:, 1]


def benchmark(pre, rf, X: pd.DataFrame) -> tuple[pd.DataFrame, dict, dict]:
    """End-to-end (preprocess + predict_proba) timing on ONE core, per batch size."""
    rf.n_jobs = 1
    infer(pre, rf, X.iloc[:100])  # warm-up
    rows, per_call = [], {}
    for bs, n in BATCH_PLAN.items():
        times = []
        for s in range(0, n, bs):
            t0 = time.perf_counter()
            infer(pre, rf, X.iloc[s:s + bs])
            times.append(time.perf_counter() - t0)
        times = np.array(times)
        per_call[bs] = times
        rows.append({"batch_size": bs, "flows": n, "calls": len(times), "total_s": times.sum(),
                     "us_per_flow_mean": times.sum() / n * 1e6,
                     "us_per_flow_p50": np.median(times / bs) * 1e6,
                     "us_per_flow_p95": np.percentile(times / bs, 95) * 1e6,
                     "flows_per_s": n / times.sum()})
    rf.n_jobs = -1
    infer(pre, rf, X.iloc[:1000])
    full = []
    for _ in range(5):
        t0 = time.perf_counter()
        infer(pre, rf, X.iloc[:N_BENCH])
        full.append(time.perf_counter() - t0)
    all_cores = {"flows": N_BENCH, "repeats": 5, "median_s": float(np.median(full)),
                 "us_per_flow": float(np.median(full) / N_BENCH * 1e6),
                 "flows_per_s": float(N_BENCH / np.median(full))}
    return pd.DataFrame(rows), per_call, all_cores


def fig_latency(tab: pd.DataFrame, per_call: dict, all_cores: dict) -> str:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2), gridspec_kw={"width_ratios": [1.2, 1, 1]})
    a, b, c = axes
    x = np.arange(len(tab))
    a.bar(x, tab.flows_per_s, color=NORMAL, width=0.55)
    a.set_yscale("log")
    for i, v in enumerate(tab.flows_per_s):
        a.text(i, v * 1.15, f"{v:,.0f}", ha="center", fontsize=9, color=INK_2)
    a.set_xticks(x, [f"{b:,}" for b in tab.batch_size])
    a.set_xlabel("Micro-batch size (flows per inference call)")
    a.set_ylabel("Throughput (flows / s, log scale) — 1 CPU core")
    a.axhline(10_000, color=MUTED, lw=1)
    a.text(-0.4, 10_000 * 1.1, "10k flows/s target", fontsize=8.5, color=MUTED)
    a.set_ylim(tab.flows_per_s.min() / 2, tab.flows_per_s.max() * 4)
    a.grid(axis="x", visible=False)
    a.set_title("A. Throughput vs. micro-batch size")

    us = per_call[100] / 100 * 1e6
    b.hist(us, bins=25, color=NORMAL)
    b.axvline(np.median(us), color=INK, lw=1.2)
    b.text(np.median(us), b.get_ylim()[1] * 0.92, f"  median {np.median(us):.1f} µs/flow", fontsize=9, color=INK)
    b.set_xlabel("Amortised latency per flow (µs), batch = 100")
    b.set_ylabel("Inference calls")
    b.set_title("B. Micro-batched latency distribution")

    ms = per_call[1] * 1e3
    c.hist(ms, bins=30, color=ATTACK)
    c.axvline(np.median(ms), color=INK, lw=1.2)
    c.text(np.median(ms), c.get_ylim()[1] * 0.92, f"  median {np.median(ms):.2f} ms", fontsize=9, color=INK)
    c.set_xlabel("Single-flow latency (ms), batch = 1")
    c.set_ylabel("Flows")
    c.set_title("C. One-at-a-time latency (worst case)")
    fig.suptitle("Real-time feasibility of the champion pipeline (preprocessing + Random Forest inference)",
                 x=0.01, ha="left", fontsize=14, fontweight="semibold", color=INK)
    fig.text(0.01, -0.03, f"All 16 cores, single 10,000-flow batch: {all_cores['us_per_flow']:.2f} µs/flow · "
             f"{all_cores['flows_per_s']:,.0f} flows/s (median of 5).  Timings are wall-clock, end-to-end, "
             "on an Intel i7-11800H.", color=MUTED, fontsize=9)
    fig.tight_layout()
    return save(fig, "latency_throughput.png")


def train_family_classifier(pre, X_tr, cat_tr, X_te, cat_te):
    """Stage-2 SIEM enrichment: which attack family, given the flow was flagged malicious."""
    tr, te = cat_tr != "Normal", cat_te != "Normal"
    clf = RandomForestClassifier(n_estimators=100, min_samples_leaf=2, class_weight="balanced_subsample",
                                 random_state=SEED, n_jobs=-1)
    t0 = time.perf_counter()
    clf.fit(pre.transform(X_tr[tr]), cat_tr[tr])
    secs = time.perf_counter() - t0
    pred = clf.predict(pre.transform(X_te[te]))
    rep = {"train_attack_rows": int(tr.sum()), "test_attack_rows": int(te.sum()), "train_seconds": round(secs, 1),
           "accuracy": round(accuracy_score(cat_te[te], pred), 4),
           "macro_f1": round(f1_score(cat_te[te], pred, average="macro"), 4),
           "recall_by_family": {f: round(float(v), 4) for f, v in zip(
               clf.classes_, recall_score(cat_te[te], pred, average=None, labels=clf.classes_))}}
    return clf, rep


def siem_stream(pre, rf, fam, tau, X_te, cat_te) -> list[str]:
    rng = np.random.default_rng(SEED)
    idx = np.concatenate([rng.choice(np.flatnonzero(cat_te.to_numpy() == c), k, replace=False)
                          for c, k in SIEM_MIX.items()])
    rng.shuffle(idx)
    rf.n_jobs = fam.n_jobs = 1  # single-flow scoring: a thread pool per call costs ~20 ms of pure overhead
    lines = []
    for i in idx:
        row = X_te.iloc[[i]]
        t0 = time.perf_counter()
        z = pre.transform(row)
        p = rf.predict_proba(z)[0, 1]
        family = fam.predict(z)[0] if p >= tau else None
        lat_us = (time.perf_counter() - t0) * 1e6
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        truth = cat_te.iloc[i]
        head = f"{row.proto.iloc[0]}/{row.service.iloc[0]}/{row.state.iloc[0]}"
        if family is not None:
            sev = SEVERITY[family]
            verdict = "TP" if truth != "Normal" else "FP — FALSE ALARM"
            fam_ok = "match" if family == truth else "MISMATCH"  # ASCII: Consolas lacks check-mark glyphs
            lines += [f"[{ts}] [ALERT] [{sev}] Malicious Flow #{i} Detected!  ({head})",
                      f"  ├─ Attack Category : {family}   (stage-2 guess: {fam_ok}; ground truth: {truth})",
                      f"  ├─ Detection       : {verdict}",
                      f"  ├─ Confidence Score: {p:.2%}   (τ* = {tau:.2f})",
                      f"  ├─ Latency         : {lat_us:,.2f} microseconds",
                      f"  └─ Action Taken    : {ACTION[sev]}"]
        else:
            verdict = "TN" if truth == "Normal" else "FN — MISSED ATTACK"
            lines += [f"[{ts}] [INFO ] [ALLOW] Flow #{i} classified benign  ({head})",
                      f"  └─ P(attack) {p:.2%} · latency {lat_us:,.2f} µs · ground truth: {truth} → {verdict}"]
        time.sleep(0.05)  # simulated inter-arrival gap on the feed
    return lines


def fig_siem(lines: list[str], n_lines: int = 44) -> str:
    shown = lines[:n_lines]
    fig = plt.figure(figsize=(13, 0.24 * len(shown) + 0.8))
    fig.patch.set_facecolor("#0B132B")
    for k, ln in enumerate(shown):
        color = "#EF4444" if "[ALERT]" in ln else "#10B981" if "[INFO" in ln else "#cbd5e1"
        fig.text(0.01, 1 - (k + 1) / (len(shown) + 1), ln, family="Consolas", fontsize=9.5, color=color)
    return save(fig, "siem_alert_log.png")


def main():
    X_tr, X_te, _, y_te, cat_tr, cat_te = load_split()
    pre, rf, tau = load_models()

    tab, per_call, all_cores = benchmark(pre, rf, X_te.iloc[:N_BENCH])
    tab.round(3).to_csv(ARTIFACT_DIR / "latency_benchmark.csv", index=False)
    fam, fam_rep = train_family_classifier(pre, X_tr, cat_tr, X_te, cat_te)
    joblib.dump(fam, MODEL_DIR / "family_rf.joblib", compress=3)

    lines = siem_stream(pre, rf, fam, tau, X_te, cat_te)
    (ARTIFACT_DIR / "siem_alert_log.txt").write_text("\n".join(lines), encoding="utf-8")
    paths = [fig_latency(tab, per_call, all_cores), fig_siem(lines)]

    b1000 = tab.set_index("batch_size").loc[1000]
    b1 = tab.set_index("batch_size").loc[1]
    report = {"single_core_by_batch": tab.round(3).to_dict(orient="records"), "all_cores_10k_batch": all_cores,
              "family_classifier": fam_rep, "siem_events": sum(SIEM_MIX.values())}
    (ARTIFACT_DIR / "realtime_report.json").write_text(json.dumps(report, indent=2))

    print(tab.round(2).to_string(index=False))
    print("all cores 10k batch:", json.dumps(all_cores))
    print("family classifier:", json.dumps(fam_rep))
    print("\n".join(lines))
    for p in paths:
        print("saved", p)
    gates = {"batched_latency<100us": all_cores["us_per_flow"] < 100,
             "batched_throughput>10k": all_cores["flows_per_s"] > 10_000,
             "single_core_b1000_latency<100us": b1000.us_per_flow_mean < 100,
             "single_flow_latency_ms": round(b1.us_per_flow_mean / 1000, 3)}
    print("Acceptance gates:", gates)
    assert gates["batched_latency<100us"] and gates["batched_throughput>10k"], gates


if __name__ == "__main__":
    main()

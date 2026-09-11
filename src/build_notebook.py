"""Phase 8: assemble and execute notebooks/CLO4_IDS_ML_Solution.ipynb (13 sections, objective.md Section 7.A).

The notebook is SELF-CONTAINED: every function and constant it uses is written into its own code cells.
To avoid two hand-maintained copies of the logic, the builder lifts that source verbatim from src/ with
`ast` at build time, and the notebook never imports the project package. Two safeguards keep it honest:
  * the build aborts if any code cell references `src`;
  * the notebook's final cell asserts that its results reproduce artifacts/ exactly.
"""
import ast
import inspect
import json
import re
import sys
import time

import nbformat
import pandas as pd
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from src import champion, config, data, eda, evaluate, pipeline, realtime, security_eval, viz
from src.config import ARTIFACT_DIR, ROOT, STUDENT

NB_PATH = ROOT / "notebooks" / "CLO4_IDS_ML_Solution.ipynb"


def load(name):
    return json.loads((ARTIFACT_DIR / name).read_text())


def lift(module, *names) -> str:
    """Verbatim source of the named top-level functions / constants of `module`, in the order requested."""
    text = inspect.getsource(module)
    found = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        else:
            continue
        if name in names:
            found[name] = ast.get_source_segment(text, node)
    missing = set(names) - found.keys()
    assert not missing, f"{module.__name__}: cannot lift {missing}"
    src = "\n\n\n".join(found[n] for n in names)
    # Drop intra-package imports (e.g. `from src.data import load_split` inside prepare_data):
    # in the notebook those names are already defined in earlier cells.
    return "\n".join(line for line in src.splitlines() if not line.strip().startswith("from src"))


IMPORTS = '''import json, time, warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # figures are rendered to PNG and displayed inline below
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter
from scipy.stats import skew
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, StratifiedShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, RobustScaler
from sklearn.tree import DecisionTreeClassifier
from IPython.display import Image, display

warnings.filterwarnings("ignore", category=UserWarning)

# ---- paths (run from the repo root or from notebooks/) ----
ROOT = Path.cwd() if (Path.cwd() / "dataset").exists() else Path.cwd().parent
DATA_DIR, ARTIFACT_DIR = ROOT / "dataset", ROOT / "artifacts"
TRAIN_CSV = DATA_DIR / "UNSW_NB15_training-set.csv"
TEST_CSV = DATA_DIR / "UNSW_NB15_testing-set.csv"
FIG_DIR = ROOT / "notebooks" / "outputs"   # notebook-local figure files (images are also embedded below)
FIG_DIR.mkdir(exist_ok=True)
FIG_DPI = 150

# ---- frozen experimental constants ----
'''


def cells():
    ch = load("metrics_champion.json")
    rf, dt = ch["random_forest_tau_star"], ch["decision_tree"]
    sec = load("security_eval.json")
    rt = load("realtime_report.json")["all_cores_10k_batch"]
    s = STUDENT
    met = "met" if ch["gates_met"] else "**not fully met**"
    md, code = new_markdown_cell, new_code_cell

    def impl(title, source):
        return [md(f"*Implementation — {title}*"), code(source)]

    return [
        md(f"""# AI-Powered Intrusion Detection System with Real-Time Threat Detection
### Information Security — CLO 4 · Assignment 1

| | |
|---|---|
| **Student** | {s['name']} |
| **Enrolment** | {s['enrolment']} |
| **Class** | {s['class']} |
| **Instructor** | {s['instructor']} |
| **Repository** | {s['repo']} |

> **This notebook is self-contained.** Every function it runs is defined in the cells below; it does not import
> the project's `src/` package (which powers the SOC dashboard and command-line scripts). The final cell verifies
> that this notebook reproduces the saved project results in `artifacts/` exactly.

---
## 1. Executive Summary & CISO Mandate

**Scenario.** SecureNet Corp.'s CISO has asked for a proof-of-concept machine-learning layer to augment the
existing signature-based NIDS: classify every network flow as *Normal* or *Malicious*, fast enough for inline use,
and explain *why* an alert fired.

**Solution.** A leak-free scikit-learn pipeline (One-Hot + log1p + RobustScaler) feeding a tuned
**Random Forest** champion, benchmarked against a Decision-Tree baseline on
**UNSW-NB15** (257,673 labelled flows, 9 modern attack families). The decision threshold τ* is calibrated on
out-of-bag validation probabilities; the 20 % test fold is touched once.

**Headline (untouched test fold, τ* = {rf['threshold']:.2f}).** Accuracy **{rf['accuracy']:.2%}**, attack recall
**{rf['recall']:.2%}**, precision **{rf['precision']:.2%}**, F1 **{rf['f1']:.2%}**, false-alarm rate
**{rf['fpr']:.2%}**, ROC-AUC **{rf['roc_auc']:.4f}**. The contract's ≥ 95 % gate on accuracy/recall/F1 with FPR < 5 %
is {met}: F1 clears 95 %, while accuracy and recall land ~0.3–0.4 pp short. Section 7 presents the
evidence that the gap is data-driven — neither an alternative tree ensemble nor engineered features lift recall
above ≈ 94.3 % under a 5 % FPR budget — and the result is reported as measured, not tuned against the test set.

**Real-time.** Batched inference runs at **{rt['us_per_flow']:.1f} µs/flow ≈ {rt['flows_per_s']:,.0f} flows/s** on a
laptop CPU — comfortably line-rate for NetFlow/IPFIX-style flow export. (Figure from the dedicated benchmark run in
`artifacts/realtime_report.json`; Section 12 re-measures live, and wall-clock timings vary by a few µs between runs.)"""),

        md("## 2. Library Imports, Configuration & Seed Initialisation"),
        code(IMPORTS + lift(config, "SEED", "TARGET", "TARGET_CAT", "ID_COL", "CATEGORICAL", "LOG1P_FEATURES",
                            "TEST_SIZE") + '''

np.random.seed(SEED)
pd.set_option("display.float_format", lambda v: f"{v:,.4f}")
T_START = time.perf_counter()
print(f"numpy {np.__version__} | pandas {pd.__version__} | scikit-learn {sklearn.__version__} | SEED={SEED}")'''),
        *impl("figure style (colour-blind-validated palette, hairline chrome, PNG export)",
              lift(viz, "NORMAL", "ATTACK", "ACCENT", "SURFACE", "INK", "INK_2", "MUTED", "GRID", "AXIS",
                   "CRITICAL", "DIVERGING", "SEQUENTIAL", "apply_style", "save") + "\n\n\napply_style()"),

        md("""## 3. Data Ingestion & Sanitisation
Both official UNSW-NB15 partitions are read with `utf-8-sig` (strips the UTF-8 BOM that otherwise corrupts the
first header into `\\ufeffid`) and concatenated. The identifier `id` and both targets are separated from the
42-feature matrix."""),
        *impl("ingestion, sanitisation, stratified split, integrity report",
              lift(data, "_read", "load_raw", "split_xy", "stratified_split", "load_split") + "\n\n\n"
              + lift(eda, "SKEW_FEATURES", "integrity_report")),
        code("""df = load_raw()
rep = integrity_report(df)
print(f"rows: {rep['rows_training_file']:,} + {rep['rows_testing_file']:,} = {rep['rows_total']:,}  |  columns: {rep['columns_total']}")
print(f"features: {rep['features']} ({rep['categorical_features']} categorical, {rep['numerical_features']} numerical)")
print(f"null cells: {rep['null_cells']}  |  inf cells: {rep['inf_cells']}  |  BOM left in headers: {rep['bom_in_headers']}")
print(f"duplicate feature rows: {rep['duplicate_feature_rows']:,}  |  conflicting-label duplicate groups: {rep['duplicate_groups_with_conflicting_labels']}")
assert rep["rows_total"] == 257_673 and rep["null_cells"] == 0 and rep["inf_cells"] == 0
df.head()"""),

        md("""## 4. Security Exploratory Data Analysis
EDA here plays the role of a SOC analyst reviewing SIEM logs before writing detection rules. Each figure below is
the empirical proof for one downstream engineering decision."""),
        *impl("the four EDA proofs",
              lift(eda, "fig_attack_distribution", "fig_volume_skew", "fig_top_protocols", "fig_correlation")),
        code("""display(Image(filename=fig_attack_distribution(df), width=1000))"""),
        md("""**Insight → decision.** Attacks are 63.9 % of flows, but the families span three orders of magnitude
(Generic 58,871 vs Worms 174). Accuracy alone would hide a total failure on Worms, so Section 10 reports recall
per family, and class weighting (`balanced_subsample`) is used instead of SMOTE — interpolating between flow
records fabricates physically impossible packets."""),
        code("""display(Image(filename=fig_volume_skew(df, rep), width=1000))
pd.DataFrame({"raw skewness": rep["skewness_raw"], "log1p skewness": rep["skewness_log1p"],
              "orders of magnitude": rep["orders_of_magnitude"]})"""),
        md("""**Insight → decision.** Volume features are extremely heavy-tailed (sbytes skew ≈ 48, sload spans 10 orders
of magnitude). In raw space all mass collapses into a spike at zero; after `log1p` the Normal and Attack modes
separate. Hence `log1p` on the 9 volume/timing features followed by `RobustScaler` (median/IQR, immune to DDoS
spikes)."""),
        code("""display(Image(filename=fig_top_protocols(df), width=1000))"""),
        md("""**Insight → decision.** 133 protocols, but 126 of them occur *only* in attack traffic and the tail beyond the
top-10 holds just 6.4 % of flows. Rare values can be absent from the training fold, so the encoder must not crash
on them: `OneHotEncoder(handle_unknown='ignore')`."""),
        code("""corr_path, top_pairs, label_corr = fig_correlation(df)
display(Image(filename=corr_path, width=900))
print("Most collinear pairs (|Spearman rho|):"); print(top_pairs.to_string())"""),
        md("""**Insight → decision.** Several features are near-duplicates (`is_ftp_login`~`ct_ftp_cmd` ρ = 1.0,
`tcprtt`~`synack` 0.996). Tree ensembles are insensitive to collinearity, which — together with non-linearity and
explainable Gini importances — motivates the Random Forest."""),

        md("""## 5. Preprocessing Pipeline & Stratified Split
The split happens **before** any statistic is learned. The `ColumnTransformer` is fitted on the 80 % training fold
only and merely *applied* to the frozen 20 % test fold."""),
        *impl("leak-free ColumnTransformer",
              lift(pipeline, "safe_log1p", "numeric_columns", "build_preprocessor", "prepare_data",
                   "unseen_categories")),
        code("""d = prepare_data()
Xp_tr, Xp_te, y_tr, y_te = d["Xp_tr"], d["Xp_te"], d["y_tr"], d["y_te"]
print(f"train {Xp_tr.shape}  test {Xp_te.shape}  NaN: {np.isnan(Xp_tr).sum() + np.isnan(Xp_te).sum()}")
print(f"attack rate  train {y_tr.mean():.4f}  test {y_te.mean():.4f}")
print("categorical values in test never seen in training:", unseen_categories(d["pre"], d["X_te"]))
assert Xp_tr.shape[0] == 206_138 and Xp_te.shape[0] == 51_535
pd.concat([d["cat_tr"].value_counts().rename("train"), d["cat_te"].value_counts().rename("test")], axis=1)"""),

        md("## 6. Baseline Model — Decision Tree"),
        *impl("security-centric metrics (attack = positive class)", lift(evaluate, "binary_metrics", "fmt")),
        code("""t0 = time.perf_counter()
dt = DecisionTreeClassifier(random_state=SEED, max_depth=10, class_weight="balanced").fit(Xp_tr, y_tr)
p_dt = dt.predict_proba(Xp_te)[:, 1]
m_dt = binary_metrics(y_te, (p_dt >= 0.5).astype(int), p_dt)
print(f"trained in {time.perf_counter() - t0:.2f}s  |  {fmt(m_dt)}")"""),
        md(f"""The single tree is precise but conservative: it misses **{dt['fn']:,}** attacks ({dt['fnr']:.1%} of all
attacks). That false-negative mass is the security gap an ensemble must close."""),

        md("""## 7. Champion Model — Tuned Random Forest
**Hyper-parameter search.** The grid search below (24 configurations × 3 stratified folds, scoring F1, on a 30 %
stratified subsample of the training fold) takes ≈ 140 s, so its recorded results are loaded from
`artifacts/rf_cv_results.csv` to keep the notebook under three minutes. `tune_rf` is the exact code that produced
them; the winning configuration is then refitted here on the full training fold."""),
        *impl("hyper-parameter grid and search", lift(champion, "PARAM_GRID", "RF_FIXED", "TUNE_FRACTION", "tune_rf")),
        code("""cv = pd.read_csv(ARTIFACT_DIR / "rf_cv_results.csv")
display(cv.head(8))
best = json.loads((ARTIFACT_DIR / "metrics_champion.json").read_text())["tuning"]["best_params"]
best = {k: (None if v is None else int(v)) for k, v in best.items()}
print("best params:", best)"""),
        code("""t0 = time.perf_counter()
rf = RandomForestClassifier(oob_score=True, n_jobs=-1, **best, **RF_FIXED).fit(Xp_tr, y_tr)
print(f"champion fitted in {time.perf_counter() - t0:.1f}s  |  out-of-bag accuracy {rf.oob_score_:.4f}")"""),
        md("""**Why the ≥ 95 % gate is not fully reachable (evidence, not excuse).** A separate experiment
(`experiments/model_selection_validation.py`, validation slice of the training fold only) tested an alternative
tree ensemble (ExtraTrees) and five engineered ratio features against the tuned forest. None lifts recall above
**≈ 94.3 % under FPR < 5 %** (ROC-AUC ≈ 0.99). Exact duplicate flows with conflicting labels explain only 0.26 % of
error (`experiments/irreducible_error_ceiling.py`); the remainder is genuine overlap between Normal traffic and
benign-looking attack flows — above all Fuzzers (Section 10). The project therefore keeps the RF champion
(DEC-003) and reports the shortfall transparently."""),

        md("""## 8. Decision Threshold Optimisation (τ*)
Probabilities come from the RF's **out-of-bag** estimates: every training flow is scored only by trees that never
saw it — a free, leak-free validation set. Rule (fixed before looking at the test fold): within τ ∈ [0.30, 0.70]
choose the τ with maximum attack recall subject to FPR < 5 %, ties broken by F1."""),
        *impl("threshold sweep, selection rule and calibration figure",
              lift(champion, "TAU_WINDOW", "FPR_CAP", "FPR_COLOR", "sweep", "select_tau", "fig_threshold")),
        code("""oob = rf.oob_decision_function_[:, 1]; ok = ~np.isnan(oob)
sw = sweep(y_tr.to_numpy()[ok], oob[ok])
tau, rule = select_tau(sw)
print(f"tau* = {tau:.2f}  ({rule})")
display(Image(filename=fig_threshold(sw, tau), width=950))
sw[(sw.tau >= 0.40) & (sw.tau <= 0.60)].set_index("tau")"""),
        md("""Lowering τ below 0.50 would buy recall, but OOB FPR crosses the 5 % false-alarm budget immediately — the
curve makes the trade-off explicit. The CISO can move τ along this curve as a *policy* knob."""),

        md("## 9. Comparative Model Evaluation & Confusion Matrix (untouched test fold)"),
        *impl("confusion-matrix figure", lift(security_eval, "fig_confusion")),
        code("""p_rf = rf.predict_proba(Xp_te)[:, 1]
m_rf = binary_metrics(y_te, (p_rf >= tau).astype(int), p_rf)
cols = ["accuracy", "precision", "recall", "f1", "fpr", "roc_auc", "tp", "fp", "fn", "tn"]
table = pd.DataFrame([m_dt, m_rf], index=["Decision Tree @0.50", f"Tuned RF @{tau:.2f} (champion)"])[cols]
display(table)
gates = {"accuracy>=95%": m_rf["accuracy"] >= .95, "recall>=95%": m_rf["recall"] >= .95,
         "F1>=95%": m_rf["f1"] >= .95, "FPR<5%": m_rf["fpr"] < .05}
print("Champion acceptance gates:", gates)"""),
        code("""cm = np.array([[m_rf["tn"], m_rf["fp"]], [m_rf["fn"], m_rf["tp"]]])
display(Image(filename=fig_confusion(cm, tau), width=620))"""),
        md(f"""**Operational trade-off.** Per 10,000 flows the champion raises ≈ {sec['per_10k_flows']['false_alarms']:.0f}
false alarms (analyst triage time) and misses ≈ {sec['per_10k_flows']['missed_attacks']:.0f} attacks (breach risk).
A false positive costs minutes of SOC effort; a false negative can cost persistence, lateral movement and data
exfiltration — so recall is weighted above precision, within an explicit false-alarm budget."""),

        md("## 10. Granular 9-Family Attack Recall & Security Critique"),
        *impl("per-family recall with Wilson intervals",
              lift(security_eval, "FAMILIES", "wilson", "recall_table", "fig_recall")),
        code("""pred = pd.DataFrame({"attack_cat": d["cat_te"], "rf_pred": (p_rf >= tau).astype(int), "rf_proba": p_rf})
t = recall_table(pred)
assert t.support.sum() == int(y_te.sum()) and t.missed.sum() == m_rf["fn"]
display(Image(filename=fig_recall(t), width=950))
t.sort_values("recall")[["family", "support", "detected", "missed", "recall", "ci_lo", "ci_hi", "share_of_all_misses"]]"""),
        md(critique_md(sec)),

        md("## 11. Feature Importance & SOC Explainability"),
        *impl("feature naming and importance figure", lift(champion, "pretty", "fig_importance")),
        code("""imp = pd.Series(rf.feature_importances_, index=d["feature_names"]).sort_values(ascending=False)
display(Image(filename=fig_importance(imp), width=900))
imp.head(15).rename(index=pretty).to_frame("gini_importance")"""),
        md("""**Reading the model like a SOC analyst.** Time-to-live features (`sttl`, `ct_state_ttl`, `dttl`) dominate:
attack tooling in the testbed emits packets with characteristic initial TTLs and TTL/state combinations that benign
hosts rarely produce — the same fingerprint used to spot OS/tool artefacts in threat hunting. Volume and rate
features (`sbytes`, `smean`, `dbytes`, `sload`) capture payload anomalies — oversized requests typical of
buffer-overflow exploits and tiny, uniform probes typical of scans and fuzzing. Connection-count features
(`ct_srv_dst`, `ct_dst_src_ltm`, `ct_dst_sport_ltm`) measure fan-out to services and ports over the last 100
connections — the behavioural signature of port scanning and reconnaissance."""),

        md("## 12. Real-Time Threat Detection Benchmark & Streaming SIEM Simulation"),
        *impl("latency benchmark, stage-2 family classifier and streaming SIEM engine",
              lift(realtime, "N_BENCH", "BATCH_PLAN", "SEVERITY", "ACTION", "SIEM_MIX", "infer", "benchmark",
                   "fig_latency", "train_family_classifier", "siem_stream")),
        code("""X_tr_raw, X_te_raw, cat_tr_raw, cat_te_raw = d["X_tr"], d["X_te"], d["cat_tr"], d["cat_te"]
tab, per_call, all_cores = benchmark(d["pre"], rf, X_te_raw.iloc[:N_BENCH])
display(tab.set_index("batch_size"))
print(f"all cores, one 10,000-flow batch: {all_cores['us_per_flow']:.2f} us/flow = {all_cores['flows_per_s']:,.0f} flows/s")
display(Image(filename=fig_latency(tab, per_call, all_cores), width=1000))"""),
        code("""fam, fam_rep = train_family_classifier(d["pre"], X_tr_raw, cat_tr_raw, X_te_raw, cat_te_raw)
print("stage-2 family classifier:", {k: fam_rep[k] for k in ("accuracy", "macro_f1")})
lines = siem_stream(d["pre"], rf, fam, tau, X_te_raw, cat_te_raw)
print("\\n".join(lines))"""),
        md("""**Line-rate feasibility.** A 1 Gbps link at an average of ~1 KB per flow record produces on the order of
10⁴–10⁵ flows/s; flow exporters (NetFlow/IPFIX/Zeek) deliver records in batches, which is exactly the regime where the
pipeline runs at tens of microseconds per flow. One-flow-at-a-time scoring is far slower (milliseconds, dominated by
per-call Python overhead across all trees) — so production deployment should micro-batch, or compile the forest
(e.g. Treelite/ONNX) for the inline path."""),

        md(recommendations_md(rf, rt)),

        md("""## Reproducibility & Consistency Check
The SOC dashboard, the command-line scripts and the report are all driven by the project's `src/` package and the
results it saved in `artifacts/`. This cell proves that the self-contained code above reproduces those saved results
**exactly** — so the notebook and the application cannot silently disagree."""),
        code("""ref = json.loads((ARTIFACT_DIR / "metrics_champion.json").read_text())
ref_recall = pd.read_csv(ARTIFACT_DIR / "attack_recall.csv").set_index("family").recall
checks = {"tau*": (tau, ref["threshold"]["tau_star"])}
for name, mine, saved in (("baseline", m_dt, ref["decision_tree"]), ("champion", m_rf, ref["random_forest_tau_star"])):
    for k in ("accuracy", "precision", "recall", "f1", "fpr", "roc_auc", "tp", "fp", "tn", "fn"):
        checks[f"{name}.{k}"] = (mine[k], saved[k])
for family, r in t.set_index("family").recall.items():
    checks[f"recall[{family}]"] = (round(float(r), 6), float(ref_recall[family]))
diverged = {k: v for k, v in checks.items() if abs(float(v[0]) - float(v[1])) > 1e-6}
assert not diverged, f"Notebook diverged from artifacts/: {diverged}"
print(f"Consistency check PASSED: all {len(checks)} values (τ*, baseline and champion metrics, confusion counts,")
print("9 per-family recalls) match the project's saved results exactly.")
print(f"Notebook executed end-to-end in {time.perf_counter() - T_START:.1f} s")"""),
    ]


def critique_md(sec):
    fam = sec["recall_by_family"]
    t = pd.read_csv(ARTIFACT_DIR / "attack_recall.csv").set_index("family")
    fz, an = t.loc["Fuzzers"], t.loc["Analysis"]
    return f"""**Critical security analysis.** Only {len(sec['families_below_95pct'])} of 9 families fall below 95 %
recall: {", ".join(f"**{f}** ({fam[f]:.1%})" for f in sec['families_below_95pct'])}.

* **Fuzzers are the dominant blind spot** — {int(fz.missed):,} missed flows, **{fz.share_of_all_misses:.0%} of all
  false negatives**. Fuzzing floods a service with malformed or random input to find crashable code; at the flow
  level many fuzzing sessions are short, low-volume exchanges over ordinary services whose byte, TTL and timing
  statistics match benign clients. The ceiling analysis corroborates this: the *only* exact feature-vector
  collisions between classes in the dataset are Normal ↔ Fuzzers. **Security implication:** an adversary fuzzing an
  internet-facing service for a zero-day would largely go unnoticed, so detection shifts from the discovery phase
  to the far more damaging exploitation phase.
* **Analysis** ({int(an.missed)} of {int(an.support)} missed) covers port scans, spam and HTML-file penetration
  probes — missed flows mean vulnerability probing goes unlogged.
* **Rare ≠ undetected.** Contrary to the usual expectation, the rarest families — **Worms ({fam['Worms']:.0%}) and
  Backdoor ({fam['Backdoor']:.0%})** — are fully detected: their TTL/state fingerprints are highly distinctive. Worms'
  Wilson interval still spans [{t.loc['Worms'].ci_lo:.1%}, 100 %] because only 35 test flows exist, and a single
  missed worm would be disproportionately dangerous because it self-propagates.
* **Mitigation roadmap.** (i) payload-aware features (DPI, TLS/JA3 fingerprints) for Fuzzers and Analysis, which are
  indistinguishable at flow level; (ii) family-specific or cost-sensitive thresholds; (iii) correlate ML alerts with
  signature IDS and host EDR telemetry (defence in depth) rather than relying on a single detector."""


def recommendations_md(rf, rt):
    return f"""## 13. Executive Recommendations for the CISO

1. **Deploy as an *augmenting* detection layer, not a replacement.** The model detects {rf['recall']:.1%} of
   attacks at a {rf['fpr']:.1%} false-alarm rate; pair it with the existing signature NIDS so each covers the
   other's blind spots.
2. **Operate the threshold as policy.** τ* = {rf['threshold']:.2f} balances recall against a 5 % false-alarm
   budget; lowering τ during elevated threat levels buys recall at a measurable analyst cost (Section 8 curve).
3. **Micro-batch the inline path.** At {rt['us_per_flow']:.1f} µs/flow batched ({rt['flows_per_s']:,.0f} flows/s)
   the model sustains multi-gigabit flow export; avoid per-flow synchronous scoring.
4. **Close the Fuzzers gap.** Fuzzers alone drive the large majority of false negatives (Section 10); add
   payload/DPI features and service-crash telemetry for Fuzzers and Analysis.
5. **Continuous learning & drift monitoring.** Retrain on fresh, labelled SOC triage outcomes; monitor feature
   drift (new protocols map to all-zero one-hot vectors and silently weaken detection)."""


def main():
    nb = new_notebook(cells=cells())
    leaks = [c.source[:120] for c in nb.cells if c.cell_type == "code" and re.search(r"\bsrc\b", c.source)]
    if leaks:
        sys.exit(f"Notebook is not self-contained; code cells reference `src`: {leaks}")
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata["language_info"] = {"name": "python"}
    t0 = time.perf_counter()
    NotebookClient(nb, timeout=900, kernel_name="python3",
                   resources={"metadata": {"path": str(NB_PATH.parent)}}).execute()
    secs = time.perf_counter() - t0
    nbformat.write(nb, NB_PATH)
    errors = [o for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", []) if o.output_type == "error"]
    print(f"executed {sum(c.cell_type == 'code' for c in nb.cells)} code cells in {secs:.1f}s -> {NB_PATH}")
    if errors:
        sys.exit(f"{len(errors)} cell(s) raised errors: {[e.get('ename') for e in errors]}")


if __name__ == "__main__":
    main()

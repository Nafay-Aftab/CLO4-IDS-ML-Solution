# Phase Execution Log: AI-Powered Intrusion Detection Solution (CLO 4)

## Instructions for Implementation Agent (Claude Code)
1. This file tracks execution progress across all phases.
2. Read `objective.md` completely before taking any action.
3. **Strict Git Feature-Branch Protocol:**
   - For every phase $i$, checkout a dedicated branch: `git checkout -b feature/phase-$i-<name>`.
   - Implement, generate required empirical proofs, and execute validation scripts on that branch.
   - Stage and commit with descriptive messages.
   - Checkout `main`, merge the branch (`git merge --no-ff feature/phase-$i-<name>`), and push to `origin main`.
   - Update this file with commit hash, empirical proof artifacts, and status before starting the next phase.
4. **Empirical Proof Standard:** Every phase must produce tangible, high-DPI figures and statistical outputs that visually and mathematically justify the engineering decisions.
5. Allowed status values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `NEEDS_REVIEW`, `COMPLETED`, `FAILED`.

---

## Phase 0: Environment & Repository Scaffolding

### Status
COMPLETED

### Git Branch
`feature/phase-0-scaffolding`

### Objective
Initialize a clean, reproducible project structure, configure `.gitignore`, verify Python environment and dataset files, create `requirements.txt`, and link remote repository.

### Preconditions
- Python 3.10+ installed.
- Raw dataset files present in `dataset/`.

### Tasks
1. Checkout branch `feature/phase-0-scaffolding`.
2. Verify git repository status and set remote to `https://github.com/Nafay-Aftab/CLO4-IDS-ML-Solution`.
3. Create standard directory structure: `notebooks/`, `src/`, `figures/`, `reports/`.
4. Create `requirements.txt` with pinned dependencies (`pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `python-docx`, `joblib`).
5. Install dependencies into working environment.
6. Create `.gitignore` ignoring virtualenvs, checkpoints, cache, and raw dumps (`UNSW-NB15_1..4.csv`).
7. Validate environment by executing test import script.
8. Commit changes, merge into `main`, and push to GitHub.

### Expected Outputs
- Directory tree initialized.
- `requirements.txt` created and verified.
- `.gitignore` configured.

### Acceptance Criteria
- All required libraries import without errors.
- Both `UNSW_NB15_training-set.csv` and `UNSW_NB15_testing-set.csv` are accessible.
- Clean merge commit pushed to `origin main`.

### Validation
- Run `python -c "import pandas, numpy, sklearn, matplotlib, seaborn, docx; print('All dependencies verified successfully.')"`.

### Completion Evidence
- **Completed:** 2026-09-11
- **Environment:** CPython 3.10.10 isolated `.venv` (Windows 11, i7-11800H, 16 logical cores, 15.7 GB RAM).
- **Pinned stack (verified by `python -m src.validate_env`):** pandas 2.2.3, numpy 1.26.4, scikit-learn 1.5.2, scipy 1.14.1, matplotlib 3.9.2, seaborn 0.13.2, python-docx 1.1.2, joblib 1.4.2, fastapi 0.115.6, uvicorn 0.32.1, python-multipart 0.0.20, nbformat 5.10.4, nbclient 0.10.2.
- **Validation output:** `All dependencies verified successfully.`
- **Dataset access:** `UNSW_NB15_training-set.csv` 82,332 rows × 45 cols; `UNSW_NB15_testing-set.csv` 175,341 rows × 45 cols.
- **Scaffolding:** `src/` (config, validate_env), `notebooks/`, `figures/`, `reports/`, `models/`, `artifacts/`, `src/web/`; `.gitignore` excludes `.venv`, raw `UNSW-NB15_1..4.csv` dumps (~590 MB), `models/*.joblib`.
- **Remote:** `origin` → `https://github.com/Nafay-Aftab/CLO4-IDS-ML-Solution.git`.
- **Bootstrap commit (main):** `ed9c487`

---

## Phase 1: Data Ingestion & Security Exploratory Data Analysis (EDA)

### Status
COMPLETED

### Git Branch
`feature/phase-1-eda`

### Objective
Ingest both UNSW-NB15 CSV files, sanitize headers (UTF-8 BOM), separate features from targets, and produce empirical EDA proofs justifying downstream data decisions.

### Preconditions
- Phase 0 completed and merged into `main`.

### Tasks
1. Checkout branch `feature/phase-1-eda`.
2. Load `UNSW_NB15_training-set.csv` (82,332 rows) and `UNSW_NB15_testing-set.csv` (175,341 rows).
3. Clean BOM character `\ufeff` from column headers.
4. Combine datasets into unified DataFrame (257,673 rows, 45 columns) for stratified splitting.
5. Verify missing/null/inf counts (confirm 0 nulls).
6. Generate 4 high-resolution empirical EDA proofs in `figures/`:
   - `figures/eda_attack_distribution.png`: Dual-panel chart showing binary class balance and granular 10-class frequency on log-scale.
   - `figures/eda_traffic_volume_skew.png`: Density KDE plots illustrating extreme heavy-tail skewness in bytes and duration.
   - `figures/eda_top_protocols.png`: Comparative distribution of protocols across normal vs. attack traffic.
   - `figures/eda_feature_correlation.png`: Clustered correlation matrix heatmap highlighting key predictive feature groups.
7. Document insights directly linking skewness to `Log1p` and protocol tail behavior to `OneHotEncoder(handle_unknown='ignore')`.
8. Commit, merge into `main`, and push to GitHub.

### Empirical Proofs Generated
- `figures/eda_attack_distribution.png`
- `figures/eda_traffic_volume_skew.png`
- `figures/eda_top_protocols.png`
- `figures/eda_feature_correlation.png`

### Acceptance Criteria
- 257,673 rows loaded and verified.
- All 4 figures generated at 300 DPI with clear labels and legends.
- Clean merge commit pushed to `origin main`.

### Validation
- Verify figure files exist, are non-empty (>50KB), and contain expected distributions.

### Completion Evidence
- **Completed:** 2026-09-11 · Phase 0 merge on `main`: `56d1742` (pushed to `origin/main`).
- **Script:** `python -m src.eda` → `artifacts/eda_summary.json`.
- **Integrity:** 82,332 + 175,341 = **257,673 rows × 45 cols** (42 features: 3 categorical, 39 numerical). Null cells **0**, ±inf cells **0**, BOM in headers **none** after `utf-8-sig` + strip.
- **Class balance:** Normal 93,000 (36.1%) vs Attack 164,673 (63.9%). Families: Generic 58,871 · Exploits 44,525 · Fuzzers 24,246 · DoS 16,353 · Reconnaissance 13,987 · Analysis 2,677 · Backdoor 2,329 · Shellcode 1,511 · Worms 174.
- **Skewness → Log1p insight:** raw skew sbytes **47.92**, dbytes **44.34**, sload **8.93**, dur **8.02**; after log1p **1.15 / 0.33 / −0.41 / 3.35**. sload spans **10 orders of magnitude**, sbytes/dbytes ~5.8. log1p exposes separable Normal/Attack modes (e.g. attack sload peak at log≈18) that are invisible in raw space.
- **Protocol tail → `handle_unknown='ignore'` insight:** 133 distinct protocols; top-10 cover 93.6% of flows, the other 123 only 6.4%; **126 protocols appear only in attack traffic**. Rare values can be absent from the training fold, so the encoder must map unseen values to an all-zero vector rather than crash.
- **Correlation insight:** near-perfect collinear pairs (is_ftp_login~ct_ftp_cmd 1.00, trans_depth~ct_flw_http_mthd 1.00, tcprtt~synack 0.996, dpkts~dbytes 0.989) → tree ensembles are preferred (collinearity-insensitive). Strongest |ρ| with label: sttl 0.66, ct_state_ttl 0.586, dload 0.585.
- **Data-quality caveat:** 103,989 rows duplicate another row's feature vector; **414 duplicate groups carry conflicting labels** (1,758 rows). *Amended in Phase 4:* quantified by `experiments/irreducible_error_ceiling.py`, these conflicts cost only **661 irreducible errors (0.26 %)** — oracle max accuracy 99.74 % — so they are **not** the binding performance ceiling.
- **Figures (300 DPI):** `eda_attack_distribution.png` 276 KB · `eda_traffic_volume_skew.png` 566 KB · `eda_top_protocols.png` 202 KB · `eda_feature_correlation.png` 315 KB (all >50 KB ✔).

---

## Phase 2: Leak-Free Preprocessing & Pipeline Construction

### Status
COMPLETED

### Git Branch
`feature/phase-2-pipeline`

### Objective
Build an isolated, leak-free feature engineering pipeline with stratified partitioning, categorical encoding, and numerical scaling.

### Preconditions
- Phase 1 completed and merged into `main`.

### Tasks
1. Checkout branch `feature/phase-2-pipeline`.
2. Separate features $X$ from binary target $y$ (`label`) and categorical target $y_{\text{cat}}$ (`attack_cat`). Drop identifier `id`.
3. Perform Stratified 80/20 train/test split (`random_state=42`):
   - Train set: 206,138 samples
   - Test set: 51,535 samples (frozen, strictly untouched)
4. Fit categorical transformer strictly on $X_{\text{train}}$:
   - `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` on `['proto', 'service', 'state']`.
5. Fit numerical transformer strictly on $X_{\text{train}}$:
   - Apply $\log_{1p}$ transformation on heavy-tailed volume features (`sbytes`, `dbytes`, `sload`, `dload`, `dur`, `sinpkt`, `dinpkt`, `sjit`, `djit`).
   - Apply `RobustScaler()` across all numerical columns.
6. Transform $X_{\text{train}}$ and $X_{\text{test}}$. Verify identical feature dimensions and absence of NaNs.
7. Commit, merge into `main`, and push to GitHub.

### Expected Outputs
- Preprocessed feature arrays `X_train_proc` and `X_test_proc`.
- Pipeline transformers serialized/reproducible.

### Acceptance Criteria
- Encoders handle unseen test protocols (`icmp`, `rtp`) without errors.
- Zero test data leakage into training statistics.
- Assert `X_train_proc.shape[0] == 206138`, `X_test_proc.shape[0] == 51535`, `np.isnan(X_train_proc).sum() == 0`, `np.isnan(X_test_proc).sum() == 0`.
- Clean merge commit pushed to `origin main`.

### Validation
- Execute pipeline validation script asserting dimensions and absence of NaNs.

### Completion Evidence
- **Completed:** 2026-09-11 · Phase 1 merge on `main`: `c3fc6ac` (pushed).
- **Script:** `python -m src.validate_pipeline` → `artifacts/pipeline_report.json` — **PASSED**.
- **Split:** `StratifiedShuffleSplit(test_size=0.2, random_state=42)` stratified on 10-class `attack_cat` → **206,138 train / 51,535 test**; attack rate identical in both folds (63.91%); Worms 139 train / 35 test.
- **Processed dimensionality:** **195 features** (156 one-hot + 9 log1p→RobustScaler + 30 RobustScaler); `NaN` = 0 and `inf` = 0 in both folds.
- **Unseen-category handling:** real unseen test value discovered — `state='PAR'` (absent from train) → encoded as all-zero vector, no error. A synthetic probe `proto='zz-unseen-proto'` also transformed without error.
- **Leakage proof:** RobustScaler `center_/scale_` fitted on train-only differ from pooled train+test statistics → the test fold never influenced the fitted pipeline.
- **Serialized:** `models/preprocessor.joblib` (regenerable; git-ignored).

---

## Phase 3: Baseline Model Training & Evaluation

### Status
COMPLETED

### Git Branch
`feature/phase-3-baseline`

### Objective
Train a simple, interpretable `DecisionTreeClassifier` baseline to establish the empirical performance floor.

### Preconditions
- Phase 2 completed and merged into `main`.

### Tasks
1. Checkout branch `feature/phase-3-baseline`.
2. Train `DecisionTreeClassifier(random_state=42, max_depth=10, class_weight='balanced')` on `X_train_proc`.
3. Predict on untouched test set `X_test_proc`.
4. Compute baseline metrics: Accuracy, Precision, Attack Recall, F1-Score, False Alarm Rate (FPR).
5. Save baseline evaluation metrics dictionary for report comparison.
6. Commit, merge into `main`, and push to GitHub.

### Expected Outputs
- Baseline model evaluation results recorded in table format.

### Acceptance Criteria
- Baseline completes training in $< 10$ seconds.
- Baseline metrics accurately recorded (expected ~88–91% accuracy).
- Clean merge commit pushed to `origin main`.

### Validation
- Verify baseline metrics are stored and non-zero.

### Completion Evidence
- **Completed:** 2026-09-11 · Phase 2 merge on `main`: `3d079c2` (pushed).
- **Script:** `python -m src.baseline` → `artifacts/metrics_baseline.json` (assertions: train < 10 s, all metrics > 0 — **PASSED**).
- **Model:** `DecisionTreeClassifier(max_depth=10, class_weight='balanced', random_state=42)`, trained in **4.15 s**.
- **Untouched-test metrics (τ = 0.50):**

  | Accuracy | Precision | Attack Recall | F1 | FPR | ROC-AUC |
  |---:|---:|---:|---:|---:|---:|
  | 92.92 % | 98.29 % | 90.50 % | 94.23 % | 2.80 % | 0.9859 |

  Confusion: TP 29,805 · FP 520 · FN 3,130 · TN 18,080.
- **Deviation note (honest):** accuracy 92.92 % is *above* the contract's anticipated 88–91 % floor. The single tree is conservative — high precision but **3,130 missed attacks (9.5 % FNR)**, which is the security gap the ensemble champion must close.

---

## Phase 4: Champion Model Optimization ($\ge 95\%$ Target)

### Status
COMPLETED — acceptance gates **NOT ALL MET** (F1 ✔; accuracy, recall, FPR ✘ by < 0.5 pp). Reported as measured per user decision 2026-09-11.

### Git Branch
`feature/phase-4-champion`

### Objective
Train and optimize a `RandomForestClassifier` with hyperparameter tuning and threshold calibration to achieve $\ge 95\%$ authentic test metrics.

### Preconditions
- Phase 3 completed and merged into `main`.

### Tasks
1. Checkout branch `feature/phase-4-champion`.
2. Initialize `RandomForestClassifier(random_state=42, class_weight='balanced_subsample', n_jobs=-1)`.
3. Perform targeted hyperparameter tuning (evaluating `n_estimators`, `max_depth`, `min_samples_split`, `max_features`) via cross-validation on the training set.
4. Train optimal champion model on full `X_train_proc`.
5. Record the baseline-vs-champion comparison table (`artifacts/model_comparison.json`).
6. Calibrate optimal decision threshold $\tau^*$ on validation probabilities to maximize Attack Recall and F1-score while maintaining FPR $< 5\%$.
7. Generate empirical proof `figures/precision_recall_threshold.png` showing precision and recall curves vs. threshold.
8. Evaluate champion model on untouched test set `X_test_proc` using threshold $\tau^*$.
9. Extract top 15 Gini feature importances. Save plot to `figures/feature_importance.png`.
10. Commit, merge into `main`, and push to GitHub.

### Empirical Proofs Generated
- `figures/precision_recall_threshold.png`
- `figures/feature_importance.png`

### Acceptance Criteria
- Test Attack Recall $\ge 95.0\%$.
- Test Overall Accuracy $\ge 95.0\%$.
- Test F1-Score $\ge 95.0\%$.
- False Alarm Rate (FPR) $< 5.0\%$.
- Clean merge commit pushed to `origin main`.

### Validation
- Programmatic assertions on test metrics ($\ge 0.95$).

### Completion Evidence
- **Completed:** 2026-09-11 · Phase 3 merge on `main`: `0abfa4a` (pushed).
- **Script:** `python -m src.champion` → `artifacts/metrics_champion.json`, `model_comparison.json`, `rf_cv_results.csv`, `threshold_sweep_oob.csv`, `feature_importance.csv`, `test_predictions.csv`; run log `artifacts/champion_run.log`. Deterministic: two independent runs produced identical metrics.
- **Tuning:** `GridSearchCV`, 24 configs (n_estimators {150,200} × max_depth {25,30,None} × min_samples_split {5,10} × min_samples_leaf {2,4}; max_features √p; `balanced_subsample`) × 3 stratified folds, F1 scoring, on a stratified 30 % training subsample (61,841 rows) in 134 s → **n_estimators=150, max_depth=None, min_samples_split=5, min_samples_leaf=2** (CV F1 0.9529). Final fit on all 206,138 rows: 15.8 s, OOB accuracy 0.9488.
- **τ* calibration (leak-free):** RF out-of-bag probabilities; rule fixed in advance = max recall s.t. OOB FPR < 5 % within [0.30, 0.70] → **τ* = 0.50** (OOB recall 0.9479, F1 0.9595, FPR just under 5 %). Any lower τ breaches the FPR budget on OOB data.
- **Untouched-test results:**

  | Model | τ | Accuracy | Precision | Recall | F1 | FPR | AUC |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | Decision Tree (baseline) | 0.50 | 92.92 % | 98.29 % | 90.50 % | 94.23 % | 2.80 % | 0.9859 |
  | **Tuned Random Forest (champion)** | 0.50 | **94.71 %** | 97.05 % | **94.60 %** | **95.81 %** | **5.09 %** | 0.9915 |

  Champion confusion: TP 31,155 · FP 947 · FN 1,780 · TN 17,653 (FN cut by 43 % vs baseline).
- **Acceptance gates:** accuracy ≥ 95 % ✘ (94.71) · recall ≥ 95 % ✘ (94.60) · F1 ≥ 95 % ✔ (95.81) · FPR < 5 % ✘ (5.09).
- **Root-cause evidence (validation slice of train only, test untouched):** `experiments/model_selection_validation.py` → `artifacts/model_selection_validation.txt`. The tuned RF, an alternative tree ensemble (ExtraTrees) and 5 engineered ratio features all stay at **≤ 94.3 % recall under FPR < 5 %** (AUC ≈ 0.99). Exact-duplicate conflicts explain only 0.26 % error (`experiments/irreducible_error_ceiling.py`). Conclusion: data ceiling (Normal vs low-and-slow families overlap at flow level), not a tuning gap.
- **Decision (user, 2026-09-11):** keep the RF champion per DEC-003 and report the shortfall transparently. No test-fold tuning performed. Scope (student direction, 2026-09-11): the project compares only the Decision-Tree baseline and the tuned Random Forest champion.
- **Feature importance (top 6 Gini):** sttl 0.103 · ct_state_ttl 0.086 · rate 0.053 · sbytes(log1p) 0.048 · sload(log1p) 0.046 · smean 0.043; top-15 = 67.0 % of total importance.
- **Figures (300 DPI):** `precision_recall_threshold.png`, `feature_importance.png`.
- **Serialized (git-ignored, regenerable):** `models/champion_bundle.joblib` (preprocessor + RF + τ*), `preprocessor.joblib`.

---

## Phase 5: Security-Centric Evaluation & Granular Attack Breakdown

### Status
COMPLETED

### Git Branch
`feature/phase-5-security-eval`

### Objective
Conduct rigorous security evaluation: confusion matrix analysis, operational cost analysis (FP vs. FN), and granular recall breakdown across all 9 UNSW-NB15 attack categories.

### Preconditions
- Phase 4 completed and merged into `main`.

### Tasks
1. Checkout branch `feature/phase-5-security-eval`.
2. Generate high-resolution confusion matrix heatmap. Save to `figures/confusion_matrix.png`.
3. Calculate exact counts: True Positives, False Positives, True Negatives, False Negatives.
4. Dissect test attack predictions against ground-truth `attack_cat`:
   - Compute detection rate (Recall) for: *Generic, Exploits, Fuzzers, DoS, Reconnaissance, Analysis, Backdoor, Shellcode, Worms*.
5. Generate publication-quality per-attack recall bar chart. Save to `figures/attack_recall_breakdown.png`.
6. Author critical security critique: explain why rare/stealth attacks (e.g. Worms or Backdoors) have lower recall and the operational threat of missed intrusions.
7. Commit, merge into `main`, and push to GitHub.

### Empirical Proofs Generated
- `figures/confusion_matrix.png`
- `figures/attack_recall_breakdown.png`

### Acceptance Criteria
- Recall calculated for every single attack category with non-zero support.
- All figures generated at 300 DPI with clear labels.
- Clean merge commit pushed to `origin main`.

### Validation
- Verify figure generation and sanity check that all 9 categories sum to total test attack count.

### Completion Evidence
- **Completed:** 2026-09-11 · Phase 4 merge on `main`: `fb8690e` (pushed).
- **Script:** `python -m src.security_eval` → `artifacts/security_eval.json`, `artifacts/attack_recall.csv`. Sanity assertions **PASSED**: family supports sum to 32,935 test attacks; family misses sum to FN = 1,780; all 9 families have non-zero support.
- **Confusion (τ* = 0.50):** TP 31,155 · FP 947 · TN 17,653 · FN 1,780 → per 10,000 flows ≈ **184 false alarms** and **345 missed attacks**.
- **Per-family recall (95 % Wilson CI):**

  | Family | Test flows | Detected | Missed | Recall | 95 % CI | Share of misses |
  |---|---:|---:|---:|---:|---|---:|
  | Generic | 11,774 | 11,772 | 2 | 99.98 % | [99.94, 100] | 0.1 % |
  | Backdoor | 466 | 466 | 0 | 100.00 % | [99.18, 100] | 0.0 % |
  | Worms | 35 | 35 | 0 | 100.00 % | [90.11, 100] | 0.0 % |
  | Reconnaissance | 2,798 | 2,791 | 7 | 99.75 % | [99.48, 99.88] | 0.4 % |
  | DoS | 3,271 | 3,257 | 14 | 99.57 % | [99.28, 99.74] | 0.8 % |
  | Exploits | 8,905 | 8,777 | 128 | 98.56 % | [98.29, 98.79] | 7.2 % |
  | Shellcode | 302 | 289 | 13 | 95.70 % | [92.78, 97.47] | 0.7 % |
  | Analysis | 535 | 456 | 79 | 85.23 % | [81.98, 87.99] | 4.4 % |
  | **Fuzzers** | 4,849 | 3,312 | **1,537** | **68.30 %** | [66.98, 69.60] | **86.4 %** |

- **Security critique (authored from the measured data):**
  - *Fuzzers are the dominant blind spot* — 1,537 of 1,780 misses (86 %). Fuzzing floods a service with malformed/random input to find crashable code; at flow level many fuzzing sessions are short, low-volume exchanges over ordinary services whose byte, TTL and timing statistics match benign clients. The Phase 4 ceiling analysis corroborates this: the *only* exact feature-vector collisions between classes in the whole dataset are Normal↔Fuzzers (928 Normal / 825 Fuzzers rows). **Implication:** an adversary fuzzing an internet-facing service for a zero-day would largely go unnoticed, pushing detection from the discovery phase to the far more damaging exploitation phase.
  - *Analysis (85.2 %)* — port scans, spam and HTML-file penetration probes; 79 missed flows mean vulnerability-probing activity goes unlogged.
  - *Rare ≠ undetected (contrary to the contract's expectation):* the rarest families, **Worms (35/35) and Backdoor (466/466), are fully detected** — their TTL/state fingerprints are highly distinctive. Worms' CI still spans [90.1 %, 100 %] because of tiny support, and a single missed worm is disproportionately dangerous because it self-propagates.
  - *Mitigations:* payload-aware features (DPI, TLS/JA3 fingerprints) for Fuzzers/Analysis; family-specific or cost-sensitive thresholds; correlation with signature IDS and host EDR telemetry (defence in depth).
- **Figures (300 DPI):** `confusion_matrix.png`, `attack_recall_breakdown.png`.
- **Housekeeping:** `.gitignore` now whitelists `artifacts/*.log` so the Phase 4 run log (`champion_run.log`) is versioned as evidence.

---

## Phase 6: Real-Time Threat Detection & Streaming SIEM Simulation

### Status
COMPLETED

### Git Branch
`feature/phase-6-realtime-siem`

### Objective
Benchmark inference latency and throughput, and build a simulated real-time streaming SIEM alert engine.

### Preconditions
- Phase 4 completed and merged into `main`.

### Tasks
1. Checkout branch `feature/phase-6-realtime-siem`.
2. Benchmark model latency: pass 10,000 flows through the pipeline. Measure mean latency per flow ($\mu\text{s}$) and throughput (flows/sec).
3. Save latency benchmark chart to `figures/latency_throughput.png`.
4. Implement simulated streaming alert engine:
   - Feed 20 sequential test flows (benign and various attacks) through the pipeline.
   - Format and print real-time SOC SIEM alerts with timestamps, flow ID, attack class, confidence score, and simulated mitigation action (TCP RST / drop).
5. Save simulated SIEM log to text/image for report and README inclusion.
6. Commit, merge into `main`, and push to GitHub.

### Empirical Proofs Generated
- `figures/latency_throughput.png`
- Formatted SIEM alert log output.

### Acceptance Criteria
- Mean inference latency $< 100\,\mu\text{s}$ per flow on CPU.
- Flow throughput $> 10,000$ flows/second.
- SIEM output demonstrates instant alert generation with confidence scores.
- Clean merge commit pushed to `origin main`.

### Validation
- Execute latency benchmark test script.

### Completion Evidence
- **Completed:** 2026-09-11 · Phase 5 merge on `main`: `19fcb01` (pushed).
- **Script:** `python -m src.realtime` → `artifacts/realtime_report.json`, `latency_benchmark.csv`, `siem_alert_log.txt`, run log `artifacts/realtime_run.log`. Final measurement taken on an otherwise idle machine (Intel i7-11800H, 16 logical cores); all timings are wall-clock and end-to-end (preprocessing + `predict_proba`).
- **Throughput / latency by micro-batch size (1 CPU core, 10,000 test flows):**

  | Batch size | µs / flow (mean) | p95 µs / flow | Flows / s |
  |---:|---:|---:|---:|
  | 1 | 6,830 | 7,380 | 146 |
  | 10 | 734 | 783 | 1,362 |
  | 100 | 105.3 | 110.4 | 9,494 |
  | 1,000 | **31.0** | 31.8 | **32,212** |
  | 10,000 | 18.4 | — | 54,244 |

- **All cores, single 10,000-flow batch (median of 5):** **6.35 µs/flow → 157,418 flows/s.**
- **Acceptance gates:** batched latency < 100 µs ✔ (6.35) · throughput > 10,000 flows/s ✔ (157,418) · single-core micro-batch-1,000 latency < 100 µs ✔ (31.0).
- **Honest caveat:** strictly one-flow-at-a-time scoring costs **≈ 6.8 ms/flow** (~146 flows/s) because Python per-call overhead across all 150 trees dominates. Production inline use must micro-batch (as NetFlow/IPFIX/Zeek exporters already do) or compile the forest (Treelite/ONNX).
- **Engineering fix found during validation:** SIEM alerts initially took ~30 ms because the stage-2 family classifier kept `n_jobs=-1` (thread-pool spin-up per single-flow call); pinning `n_jobs=1` cut alert latency to **≈ 9–13 ms** typical (occasional OS-jitter outliers up to 50 ms, reported as measured).
- **Stage-2 family attribution (SIEM enrichment):** RF(100 trees) trained on 131,738 training-fold attack rows → test accuracy **75.3 %**, macro-F1 **0.568**; strong on Generic 97.2 %, Fuzzers 86.6 %, Shellcode 81.5 %, Reconnaissance 80.6 %; weak on DoS 43.0 %, Analysis 24.5 %, Backdoor 15.9 % (these families share near-identical flow statistics in UNSW-NB15). The family tag is therefore labelled a *stage-2 guess* in the SIEM log, with ground truth shown for audit.
- **Streaming SIEM engine:** 20 seeded mixed test flows (6 Normal, 3 Exploits, 3 DoS, 3 Fuzzers, 2 Worms, 1 Generic, 1 Reconnaissance, 1 Backdoor) → 14 alerts with timestamp, severity (CRITICAL/HIGH/MEDIUM), confidence, latency and action (TCP RST / block or rate-limit); 1 Fuzzers flow missed (P(attack) 45.8 % < τ*) and shown explicitly as `FN — MISSED ATTACK`.
- **Figures (300 DPI):** `latency_throughput.png`, `siem_alert_log.png`.

---

## Phase 7: Bespoke Enterprise SOC Web Dashboard (FastAPI + HTML5/CSS3/Chart.js)

### Status
COMPLETED — CP-2 visual design approved by the student (2026-09-11)

### Git Branch
`feature/phase-7-soc-dashboard`

### Objective
Develop a high-performance, single-command enterprise SOC Web Dashboard using FastAPI and modern glassmorphic HTML5/CSS3/Chart.js with live streaming simulation, manual flow inspection, and batch CSV prediction.

### Preconditions
- Phases 1 through 6 completed and merged into `main`; serialized champion model and preprocessor pipeline saved in `models/`.

### Tasks
1. Checkout branch `feature/phase-7-soc-dashboard`.
2. Construct the frontend static assets in `src/web/`:
   - `index.html`: Responsive single-page layout with modern sidebar navigation, 4 functional views, and executive telemetry cards.
   - `styles.css`: Bespoke enterprise cyber dark-theme (`#0B132B`, `#1C2541`, `#1E293B`), glassmorphism card borders, pulsing threat LEDs, and responsive grids.
   - `app.js`: Client-side logic for dynamic Chart.js rendering, asynchronous REST API calls, live SIEM alert table streaming, manual attack presets, and batch CSV processing.
3. Construct the backend server in `src/app.py`:
   - Initialize FastAPI app with static file mounting and CORS.
   - Endpoint `GET /api/telemetry`: Serves model performance metrics, confusion matrix counts, and top feature importance rankings for Chart.js.
   - Endpoint `POST /api/predict/single`: Ingests single flow parameters, executes pipeline transformation and model inference, returning prediction, confidence score, and latency.
   - Endpoint `POST /api/predict/batch`: Ingests uploaded CSV files, runs vectorized pipeline inference, and returns summary stats and enriched results.
   - Endpoint `GET /api/stream/simulated`: SSE/streaming generator yielding sequential flow events (Normal and attacks) for the live SIEM view.
4. Test dashboard locally: launch `python -m src.app` on `http://localhost:8000`.
5. Capture high-resolution screenshots of all 4 dashboard views and save to `figures/dashboard_*.png` for inclusion in the report and README.
6. Commit, merge into `main`, and push to GitHub.

### Empirical Proofs & UI Artifacts Generated
- `src/app.py`
- `src/web/index.html`, `src/web/styles.css`, `src/web/app.js`
- `figures/dashboard_telemetry.png`
- `figures/dashboard_live_siem.png`
- `figures/dashboard_manual_inspector.png`
- `figures/dashboard_batch_prediction.png`

### Acceptance Criteria
- Dashboard starts with a single command: `python -m src.app`.
- Zero Node.js / npm dependencies required.
- All 4 views operate interactively with fluid animations and responsive charts.
- Clean merge commit pushed to `origin main`.

### Validation
- Launch dashboard, test REST endpoints via curl / automated test script, and verify HTTP 200 responses and valid JSON payloads.

### Completion Evidence
- **Completed:** 2026-09-11 · Phase 6 merge on `main`: `6544cbc` (pushed).
- **Launch:** `python -m src.app` → `http://localhost:8000` (single command, zero Node.js/npm; Chart.js 4.4.4 loaded by the browser from jsDelivr, with table-view fallbacks if offline).
- **Backend (`src/app.py`):** FastAPI with lifespan start-up that loads `models/champion_bundle.joblib` + stage-2 family model and **scores the full test fold live** (telemetry is never hard-coded). Endpoints: `GET /api/telemetry`, `GET /api/presets`, `POST /api/predict/single`, `POST /api/predict/batch`, `GET /api/predict/batch/{token}`, `GET /api/stream/simulated` (SSE), `GET /api/sample.csv`.
- **Front-end (`src/web/`):** `index.html`, `styles.css` (cyber dark `#0B132B`/`#1C2541`/`#1E293B`, glass cards, `@keyframes pulse` LEDs, responsive grid, reduced-motion support), `app.js` (vanilla JS). Four views: Executive Telemetry (4 KPI cards with target badges, model dot-plot, interactive confusion matrix with cost tooltips, Gini importance, per-family recall, metric table view); Live Threat Feed (SSE, counters, P(attack) timeline with τ* line, SIEM incident table flagging missed attacks and false alarms); Flow Inspector (9-field form, 4 presets, animated gauge with τ* tick, class & stage-2 family probabilities); Batch CSV Predictor (drag-and-drop, upload progress, ≤ 6-segment breakdown doughnut, labelled-data metrics, preview, enriched CSV download).
- **Automated validation:** `python -m src.validate_dashboard` → `artifacts/dashboard_validation.json` — **PASSED**: all endpoints HTTP 200 with valid payloads; telemetry = recall 0.9460 / FPR 0.0509 / acc 0.9471 (matches Phase 4); 4 presets classified correctly (Normal p=0.000; DoS 0.968; Exploits 0.990; Reconnaissance 0.960); partial form defaults 38 features; 2,000-row sample batch: acc 0.9405, recall 0.9322, FPR 0.0455; enriched CSV download OK; schema-less CSV rejected with HTTP 400; SSE stream delivers events.
- **Honesty decisions made during build:**
  - UNSW-NB15 contains **no benign TLS/`ssl` flows** (all 16 ssl rows are attacks) → the contract's "Legitimate HTTPS Traffic" preset is honestly relabelled **"Legitimate Web Traffic (HTTP)"**.
  - Presets use the **median-scored flow of each class** (disclosed in the UI) — the first seeded-random benign pick happened to be a false positive (p=0.56); a representative example avoids misrepresenting typical behaviour, while false alarms remain visible in the live feed and telemetry.
  - Batch breakdown is a doughnut capped at 6 segments (Normal + top-4 families + Other) for legibility.
- **Bugs found & fixed in validation:** empty preset mask crashed start-up; deprecated `on_event` → lifespan; stream chart smoothing overshot [0,1] (tension → 0) and float tick labels; indistinguishable gray model colours.
- **Screenshots (headless Edge, 2× DPI, kiosk mode `?view=…&demo=1` via `python -m src.capture_dashboard`):** `figures/dashboard_telemetry.png`, `dashboard_live_siem.png`, `dashboard_manual_inspector.png`, `dashboard_batch_prediction.png`.

---

## Phase 8: Jupyter Notebook Assembly & Execution

### Status
COMPLETED

### Git Branch
`feature/phase-8-notebook`

### Objective
Assemble all previous phases into a single, beautifully documented, self-contained, fully executed Jupyter Notebook in `notebooks/CLO4_IDS_ML_Solution.ipynb`.

### Preconditions
- Phases 1 through 7 completed and merged into `main`.

### Tasks
1. Checkout branch `feature/phase-8-notebook`.
2. Construct notebook containing all 13 structured sections from `objective.md`.
3. Add rich markdown explanations, mathematical formulas, security commentary, and executive callout blocks.
4. Execute the entire notebook from top to bottom in a single run.
5. Verify all outputs, tables, and matplotlib/seaborn plots are cleanly embedded in the `.ipynb` file.
6. Commit, merge into `main`, and push to GitHub.

### Expected Outputs
- `notebooks/CLO4_IDS_ML_Solution.ipynb` fully populated and executed.

### Acceptance Criteria
- Notebook runs from cell 1 to end without errors.
- Execution time $< 3$ minutes.
- All figures and tables render properly.
- Clean merge commit pushed to `origin main`.

### Validation
- Validate execution using `jupyter nbconvert --to notebook --execute notebooks/CLO4_IDS_ML_Solution.ipynb`.

### Completion Evidence
- **Completed:** 2026-09-11 · Phase 7 merge on `main`: `46b4934`; follow-up merges `1a82d85` (two-model scope) and `bb4e3c8` (defense-map removal), all pushed.
- **Build:** `python -m src.build_notebook` assembles and executes the notebook headlessly via `nbclient` (equivalent to `nbconvert --execute`), writing `notebooks/CLO4_IDS_ML_Solution.ipynb`. The build fails if any cell raises an error. Log: `artifacts/notebook_build.log`.
- **Result:** 42 cells (18 code, 24 markdown) · **0 errors** · 9 embedded figures · **end-to-end execution 73.1 s** (< 3 min target ✔).
- **Structure:** all 13 sections from objective.md §7.A: executive summary & student metadata → imports/seed → ingestion & sanitisation → EDA (4 proofs + insight→decision notes) → leak-free split & pipeline → Decision-Tree baseline → tuned Random Forest champion → τ* calibration on OOB probabilities → comparative evaluation & confusion matrix → 9-family recall & security critique → Gini explainability → real-time benchmark & streaming SIEM → CISO recommendations.
- **Self-contained & honest:** every table and figure is recomputed by the notebook's own cells. Narrative numbers are pulled from `artifacts/` at build time. The acceptance gates are printed as measured (F1 ✔; accuracy, recall, FPR ✘). The 138 s grid search is loaded from `artifacts/rf_cv_results.csv` (produced by `src.champion`), and the winning configuration is refitted in-notebook to stay under 3 minutes.
- **Reproducibility check:** the in-notebook run reproduces the champion exactly (OOB accuracy 0.9488, τ* = 0.50, baseline and champion metrics identical to Phase 3/4). Live latency re-measurement this run: 7.85 µs/flow (127,425 flows/s), which is within normal wall-clock variance of the dedicated benchmark (6.35 µs/flow). The notebook states this explicitly. The notebook's re-rendered `latency_throughput.png` is not committed, so the repository figure stays tied to `artifacts/realtime_report.json`.

---

## Phase 9: Academic MS Word Report Generation (`Project_Report_CLO4.docx`)

### Status
NOT_STARTED

### Git Branch
`feature/phase-9-report`

### Objective
Author an extremely professional, academic 5–6 page MS Word deliverable matching the exact assignment guidelines and student metadata using `python-docx`.

### Preconditions
- Phases 1 through 8 completed and merged into `main`; all metrics, tables, dashboard screenshots, and figures available in `figures/`.

### Tasks
1. Checkout branch `feature/phase-9-report`.
2. Develop python automation script (`src/generate_report.py`) using `python-docx` to construct the report with professional formatting:
   - **Student Metadata on Cover Page:**
     * Name: Muhammad Nafay Aftab
     * Enrolment: 03-134222-087
     * Class: BSCS-8A
     * Course: Information Security
     * Instructor: Dr. Nadeem Sarwar
     * Assignment 1 Report (CLO 4)
     * Repository: `https://github.com/Nafay-Aftab/CLO4-IDS-ML-Solution`
   - **Page Budget:** Strict 5–6 pages (excluding cover page).
   - **Visual Formatting:** Executive Navy headings (`#1B365D`), Slate subheadings (`#4A5568`), 1-inch margins, 1.15 line spacing, styled tables with alternating fills, executive callout boxes.
   - **Content:**
     * Title Page
     * Section 1: Executive Summary
     * Section 2: Introduction & Real-World Scenario (SecureNet Corp)
     * Section 3: Methodology (Dataset justification, Preprocessing, ML Tool Design)
     * Section 4: Results & Security Analysis (Metrics table, Confusion Matrix, 9-Attack Recall analysis, Feature Importance, Real-Time Latency, SOC Dashboard UI Overview)
     * Section 5: Conclusion & Future Enhancements
     * Section 6: References (IEEE format)
     * Appendix: GitHub Repository URL & Setup
   - Embed high-resolution figures: `figures/confusion_matrix.png`, `figures/attack_recall_breakdown.png`, `figures/feature_importance.png`, `figures/latency_throughput.png`, `figures/dashboard_telemetry.png`.
3. Generate `reports/Project_Report_CLO4.docx`.
4. Inspect word count and page layout to ensure strict compliance with the 5–6 page limit.
5. Commit, merge into `main`, and push to GitHub.

### Expected Outputs
- `reports/Project_Report_CLO4.docx`.

### Acceptance Criteria
- Document is complete, beautifully formatted, contains student metadata, and adheres to the 5–6 page limit.
- All figures embedded cleanly with descriptive captions.
- Zero placeholder or lorem-ipsum text.
- Clean merge commit pushed to `origin main`.

### Validation
- Inspect generated docx page count and formatting.

### Completion Evidence
*(To be recorded by implementation agent)*

---

## Phase 10: GitHub Repository Polish & Final QA Audit

### Status
NOT_STARTED

### Git Branch
`feature/phase-10-final-qa`

### Objective
Finalize `README.md`, verify git repository cleanliness, commit deliverables, and perform the final quality audit.

### Preconditions
- Phases 0 through 9 completed and merged into `main`.

### Tasks
1. Checkout branch `feature/phase-10-final-qa`.
2. Create a comprehensive, publication-grade `README.md` containing:
   - Project title, badges, student metadata.
   - Executive mission & CISO problem statement.
   - System architecture diagram.
   - Dataset setup & quick-start execution guide (including how to run both the Notebook and the Web Dashboard).
   - Summary of key results ($\ge 95\%$ metrics table).
   - Sample SIEM alert screens and dashboard screenshots.
3. Verify repo cleanliness: ensure large raw PCAP dumps (`UNSW-NB15_1..4.csv`) are ignored by `.gitignore`.
4. Check git status, stage, commit all files, merge into `main`, and push to `https://github.com/Nafay-Aftab/CLO4-IDS-ML-Solution`.
5. Perform final verification against grading rubric and CLO 4 objectives.

### Expected Outputs
- `README.md` complete and formatted.
- Git repository clean and synchronized on remote `main`.

### Acceptance Criteria
- Repository passes all assignment requirements.
- Clean working tree on `main` pushed to remote.

### Validation
- Full pre-submission checklist verification.

### Completion Evidence
*(To be recorded by implementation agent)*


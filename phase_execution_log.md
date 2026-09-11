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
4. Create `requirements.txt` with pinned dependencies (`pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `python-docx`, `joblib`, `lightgbm`).
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
- Run `python -c "import pandas, numpy, sklearn, matplotlib, seaborn, docx, lightgbm; print('All dependencies verified successfully.')"`.

### Completion Evidence
- **Completed:** 2026-09-11
- **Environment:** CPython 3.10.10 isolated `.venv` (Windows 11, i7-11800H, 16 logical cores, 15.7 GB RAM).
- **Pinned stack (verified by `python -m src.validate_env`):** pandas 2.2.3, numpy 1.26.4, scikit-learn 1.5.2, scipy 1.14.1, matplotlib 3.9.2, seaborn 0.13.2, python-docx 1.1.2, joblib 1.4.2, lightgbm 4.5.0, fastapi 0.115.6, uvicorn 0.32.1, python-multipart 0.0.20, nbformat 5.10.4, nbclient 0.10.2.
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
- **Data-quality caveat (honest ceiling):** 103,989 rows duplicate another row's feature vector; **414 duplicate groups carry conflicting labels** → irreducible error floor for any classifier.
- **Figures (300 DPI):** `eda_attack_distribution.png` 276 KB · `eda_traffic_volume_skew.png` 566 KB · `eda_top_protocols.png` 202 KB · `eda_feature_correlation.png` 315 KB (all >50 KB ✔).

---

## Phase 2: Leak-Free Preprocessing & Pipeline Construction

### Status
NOT_STARTED

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
*(To be recorded by implementation agent)*

---

## Phase 3: Baseline Model Training & Evaluation

### Status
NOT_STARTED

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
*(To be recorded by implementation agent)*

---

## Phase 4: Champion Model Optimization ($\ge 95\%$ Target)

### Status
NOT_STARTED

### Git Branch
`feature/phase-4-champion`

### Objective
Train and optimize a `RandomForestClassifier` (and benchmark a `LightGBMClassifier`) with hyperparameter tuning and threshold calibration to achieve $\ge 95\%$ authentic test metrics.

### Preconditions
- Phase 3 completed and merged into `main`.

### Tasks
1. Checkout branch `feature/phase-4-champion`.
2. Initialize `RandomForestClassifier(random_state=42, class_weight='balanced_subsample', n_jobs=-1)`.
3. Perform targeted hyperparameter tuning (evaluating `n_estimators`, `max_depth`, `min_samples_split`, `max_features`) via cross-validation on the training set.
4. Train optimal champion model on full `X_train_proc`.
5. Train challenger `LGBMClassifier` for comparison.
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
*(To be recorded by implementation agent)*

---

## Phase 5: Security-Centric Evaluation & Granular Attack Breakdown

### Status
NOT_STARTED

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
*(To be recorded by implementation agent)*

---

## Phase 6: Real-Time Threat Detection & Streaming SIEM Simulation

### Status
NOT_STARTED

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
*(To be recorded by implementation agent)*

---

## Phase 7: Bespoke Enterprise SOC Web Dashboard (FastAPI + HTML5/CSS3/Chart.js)

### Status
NOT_STARTED

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
*(To be recorded by implementation agent)*

---

## Phase 8: Jupyter Notebook Assembly & Execution

### Status
NOT_STARTED

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
*(To be recorded by implementation agent)*

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
Finalize `README.md`, verify git repository cleanliness, commit deliverables, and perform final viva audit.

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
   - Viva defense summary map.
3. Verify repo cleanliness: ensure large raw PCAP dumps (`UNSW-NB15_1..4.csv`) are ignored by `.gitignore`.
4. Check git status, stage, commit all files, merge into `main`, and push to `https://github.com/Nafay-Aftab/CLO4-IDS-ML-Solution`.
5. Perform final verification against grading rubric and CLO 4 objectives.

### Expected Outputs
- `README.md` complete and formatted.
- Git repository clean and synchronized on remote `main`.

### Acceptance Criteria
- Repository passes all assignment requirements.
- Viva defense map ready.
- Clean working tree on `main` pushed to remote.

### Validation
- Full pre-submission checklist verification.

### Completion Evidence
*(To be recorded by implementation agent)*


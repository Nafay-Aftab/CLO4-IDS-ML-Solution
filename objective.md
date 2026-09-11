# PROJECT EXECUTION CONTRACT: AI-POWERED INTRUSION DETECTION SYSTEM (NIDS)

## 1. Project Metadata & Mission
- **Project Name:** CLO4-IDS-ML-Solution
- **Course:** Information Security (CLO 4: Create solutions to real-life scenarios using security-related tools)
- **Institution:** Department of Computer Science
- **Student Details:**
  - **Name:** Muhammad Nafay Aftab
  - **Enrolment:** 03-134222-087
  - **Class:** BSCS-8A
  - **Instructor:** Dr. Nadeem Sarwar
- **Public GitHub Repository:** `https://github.com/Nafay-Aftab/CLO4-IDS-ML-Solution`
- **Primary Deliverables:**
  1. `CLO4_IDS_ML_Solution.ipynb` (Comprehensive, end-to-end, reproducible Jupyter Notebook in `notebooks/`)
  2. `README.md` (Executive summary, architecture, installation, how to run, results summary, sample SIEM screens)
  4. `requirements.txt` (Pinned, conflict-free Python virtual environment specification)
  5. `figures/` (High-resolution, publication-quality PNG charts embedded into the report and README)
  6. **Enterprise SOC Web Dashboard:** Bespoke interactive frontend powered by FastAPI + Modern Dark/Glassmorphic HTML5/CSS3/Chart.js in `src/web/` (single-command run: `python -m src.app`).

### The Real-World Mission (CISO Mandate)
You are operating as a Senior Security & ML Engineer at **SecureNet Corp.** The Chief Information Security Officer (CISO) has mandated the development of an intelligent, machine-learning-augmented Network Intrusion Detection System (NIDS) proof-of-concept. The system must ingest high-velocity network flow records, accurately discriminate between legitimate corporate traffic and malicious intrusion attempts, sustain line-rate latency requirements for real-time threat detection, deliver actionable security telemetry (attack classification, feature attribution, and false-negative risk analysis), and provide an intuitive, executive-grade SOC Web Dashboard for real-time operational monitoring and threat triage.

---

## 2. Frozen Architectural Decisions (Source of Truth)

| Decision ID | Decision Area | Frozen Specification | Justification & Safeguards |
|---|---|---|---|
| **DEC-001** | **Dataset Selection** | **UNSW-NB15** (`UNSW_NB15_training-set.csv` + `UNSW_NB15_testing-set.csv`) | Modern CVE and synthetic attack profiles; realistic network flow statistics; avoids obsolete KDD99 artifacts and multi-gigabyte CIC-IDS memory crashes. Total: 257,673 rows. |
| **DEC-002** | **Classification Formulation** | **Primary Binary Classifier (`Normal` vs `Malicious`) with Granular 9-Attack-Family Recall Breakdown** | Directly addresses CISO binary alert requirement while rigorously satisfying Step 4's critical security analysis on specific attack families (*Exploits, DoS, Fuzzers, Worms, etc.*). |
| **DEC-003** | **Model Selection & Benchmark** | **Baseline: Simple Decision Tree (~88–91% floor)<br>Champion: Tuned Random Forest (Target: $\ge 95\%$ authentic metrics)** | Ablation study demonstrating single-tree variance vs. ensemble bagging; unlocks Gini Feature Importance for SOC alert explainability; authentic $\ge 95\%$ test score. |
| **DEC-004** | **Data Pipeline & Preprocessing** | **Stratified 80/20 Train/Test Split (206,138 train / 51,535 test)<br>Categorical: `OneHotEncoder(handle_unknown='ignore')`<br>Numerical: Skewness Log1p + `RobustScaler`<br>Balancing: `class_weight='balanced'` (Strictly NO SMOTE)** | Zero data leakage; handles unseen test protocols (`icmp`, `rtp`) and states (`no`, `PAR`, `ECO`, `URN`); preserves physical network packet laws without synthetic KNN distortion. |
| **DEC-005** | **Real-Time Threat Detection PoC** | **Inference Latency Benchmark ($\mu\text{s}$/flow, flows/sec) + Simulated SIEM Streaming Alert Engine** | Empirically proves line-rate suitability on 1 Gbps / 10 Gbps network trunks; outputs real-time alert logs with timestamps, category, and confidence. |
| **DEC-006** | **Deliverables & Report Specification** | **5–6 Page Academic MS Word Document + GitHub Repo** | Authored for Dr. Nadeem Sarwar with professional typography, corporate color palette and embedded high-DPI figures. |
| **DEC-007** | **Git & GitHub Engineering Workflow** | **Strict Feature-Branch Git Strategy (`feature/phase-X-...` $\rightarrow$ Validate $\rightarrow$ Merge into `main` $\rightarrow$ Push)** | Professional version control; no direct unvalidated commits to `main`; each module built in isolation, validated against criteria, merged with descriptive messages, and pushed to remote. |
| **DEC-008** | **Empirical Proof & Insight Standard** | **Every Design Decision Backed by Visual & Statistical Proofs (EDA, Skewness, Threshold, Latency)** | In ML, implementations without empirical proof are unvalidated claims. Every transformation, model choice, and threshold shift must be visibly demonstrated with high-DPI charts and statistical distributions. |
| **DEC-009** | **Frontend SOC Web Dashboard** | **FastAPI + Bespoke Cyber Dashboard (HTML5, Modern CSS Glassmorphism, Chart.js, Zero-npm setup)** | Provides an interactive SOC experience: executive KPI telemetry, live-streaming threat simulator, single-flow manual inspector with preset attack injections, and batch CSV uploader. Zero Node.js friction for the examiner. |

---

## 3. Strict Scope & Boundaries

### In Scope
- Programmatic ingestion and integrity sanitization of `UNSW_NB15_training-set.csv` and `UNSW_NB15_testing-set.csv` (stripping UTF-8 BOM `\ufeffid`).
- Security-focused Exploratory Data Analysis (EDA) uncovering attack distributions, flow durations, and byte volume skews.
- Strict train-only pipeline fitting (`fit` on training fold only; `transform` on test fold).
- Decision Tree baseline implementation.
- Systematic hyperparameter tuning of Random Forest using cross-validation.
- Precision-Recall decision threshold calibration ($\tau^*$) to guarantee $\ge 95\%$ authentic attack recall and F1-score.
- Granular 9-category attack recall table dissecting security implications of missed minority attacks (e.g., Worms, Backdoors).
- Real-time line-rate latency and throughput profiling.
- Automated python generation of `Project_Report_CLO4.docx` using `python-docx` with professional styles, headers, callout boxes, and embedded charts.
- Generation of high-resolution figures (`figures/*.png`) and clear markdown documentation (`README.md`).
- **Interactive SOC Web Dashboard:** Lightweight FastAPI backend (`src/app.py`) serving a responsive, dark-mode cybersecurity dashboard (`src/web/`) with live streaming simulation, manual single-flow inspector, and batch CSV analysis.

### Out of Scope (Non-Goals)
- No Node.js / React build tooling overhead (dashboard is pure, self-contained HTML5/CSS3/Chart.js served directly by FastAPI).
- No inline kernel packet capture (Scapy, libpcap, raw sockets, or DPDK).
- No Docker, Kubernetes, or cloud deployment overhead.
- No synthetic oversampling algorithms (SMOTE/ADASYN) that generate physically impossible network packets.
- No uninterpretable deep neural networks (Transformers, RNNs, MLPs) that obscure feature attribution for SOC analysts.

---

## 4. End-to-End Data Pipeline Specification

```text
               Raw UNSW-NB15 Files (82,332 + 175,341 rows)
                                    │
                                    ▼
       [Step 1: Ingestion, BOM Sanitization & Target Separation]
         - Concatenate partitions into unified DataFrame (257,673 rows)
         - Drop identifier: 'id' / '\ufeffid'
         - Extract targets: y_binary = 'label', y_cat = 'attack_cat'
         - Feature matrix: X (42 features: 3 categorical, 39 numerical)
                                    │
                                    ▼
       [Step 2: Leak-Free Stratified Train/Test Partition]
         - StratifiedShuffleSplit (80% Train: 206,138 | 20% Test: 51,535)
         - Stratification key: 'label' (or combined 'attack_cat')
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
          Training Set (80%)                  Test Set (20% - FROZEN)
                  │                                   │
                  ▼                                   │
       [Step 3: Fit Preprocessing]                    │
         - Categorical: OneHotEncoder                 │
           (handle_unknown='ignore')                  │
         - Heavy-tailed Numerical:                     │
           Log1p + RobustScaler                       │
         - Standard Numerical: RobustScaler           │
                  │                                   │
                  ├───────────────────────────────────┤
                  ▼ Transform                         ▼ Transform (Using Train Stats)
         Processed X_train                   Processed X_test
                  │                                   │
                  ▼                                   ▼
       [Step 4: Model Training & Tuning]     [Step 5: Evaluation on Untouched Test]
         - Baseline: DecisionTreeClassifier    - Compute Accuracy, Precision, Recall, F1
         - Champion: Tuned RandomForest        - Generate 2x2 Confusion Matrix Heatmap
         - Threshold Tuning (optimal tau)      - Generate 9-Category Attack Recall Table
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ▼
       [Step 6: Real-Time Latency & Streaming SIEM Alert Simulation]
         - Measure mean inference time per flow (microseconds)
         - Stream test samples to stdout SIEM alert log
```

---

## 5. Machine Learning & Optimization Protocol ($\ge 95\%$ Guarantee)

To achieve **$\ge 95\%$ authentic test metrics** without data leakage or overfitting, the implementation agent must adhere to the following tuning sequence:

1. **Feature Skewness Log-Transform:** Apply $\log(x + 1)$ to high-variance volume features:
   `['sbytes', 'dbytes', 'sload', 'dload', 'dur', 'sinpkt', 'dinpkt', 'sjit', 'djit']`.
2. **Robust Scaling:** Scale all numerical columns with `RobustScaler(quantile_range=(25.0, 75.0))` to neutralize extreme DDoS traffic spikes.
3. **Hyperparameter Grid (Random Forest):**
   - `n_estimators`: `[150, 200]`
   - `max_depth`: `[25, 30, None]`
   - `min_samples_split`: `[5, 10]`
   - `min_samples_leaf`: `[2, 4]`
   - `max_features`: `'sqrt'`
   - `class_weight`: `'balanced_subsample'`
   - `random_state`: `42`, `n_jobs`: `-1`
4. **Threshold Calibration ($\tau^*$):**
   - Extract prediction probabilities: $P(y=1 \mid X)$.
   - Evaluate F1-score across thresholds $\tau \in [0.30, 0.70]$ on a validation fold.
   - Select $\tau^*$ that maximizes Attack Recall while keeping False Positive Rate $< 5\%$.
5. **Feature Importance Analysis:**
   - Extract top 15 Gini importances from the champion model.
   - Plot and explain how connection features (`ct_state_ttl`, `sttl`, `ct_dst_src_ltm`, `sbytes`) allow the model to identify port scanning and buffer overflows.

---

## 6. Real-Time Threat Detection Simulation Specification

The implementation must define a dedicated simulation module:
- **Throughput Profiling:** Pass 10,000 test samples through the trained pipeline in a single batch and in sequential micro-batches. Record total time, compute:
  $$\text{Latency per flow} = \frac{\Delta t}{N} \quad (\mu\text{s/flow}), \quad \text{Throughput} = \frac{N}{\Delta t} \quad (\text{flows/sec})$$
- **Streaming SIEM Engine:** Simulate a live socket feed by iterating through 20 mixed test samples (Normal, DoS, Exploit, Fuzzer, Worms) and emitting formatted logs:
  ```text
  [2026-09-10 14:45:01.102] [ALERT] [CRITICAL] Malicious Flow #1042 Detected!
    ├─ Attack Category : Exploits
    ├─ Confidence Score: 98.42%
    ├─ Latency         : 42.15 microseconds
    └─ Action Taken    : TCP RST Packet Dispatched | Flow Blocked
  ```

---

## 7. Deliverable Specifications

### A. Jupyter Notebook (`notebooks/CLO4_IDS_ML_Solution.ipynb`)
- Completely self-contained, reproducible, with all cell outputs executed and preserved.
- Structure:
  1. Executive Summary & CISO Mandate
  2. Library Imports & Seed Initialization (`SEED=42`)
  3. Data Ingestion & Sanitization
  4. Security Exploratory Data Analysis (EDA) with 3 publication-grade figures
  5. Preprocessing Pipeline & Stratified Split
  6. Baseline Model (Decision Tree)
  7. Champion Model (Tuned Random Forest)
  8. Decision Threshold Optimization
  9. Comparative Model Evaluation & Confusion Matrix
  10. Granular 9-Attack-Category Recall Breakdown & Security Critique
  11. Feature Importance & SOC Explainability
  12. Real-Time Threat Detection Benchmark & Streaming SIEM Simulation
  13. Executive Recommendations for CISO

### B. MS Word Deliverable (`reports/Project_Report_CLO4.docx`)
- **Length:** Strict 5–6 pages (excluding title page).
- **Styling:**
  - Font: Calibri / Arial or Georgia; 1-inch margins; consistent 1.15 line spacing.
  - Color Palette: Executive Navy (`#1B365D`), Slate Grey (`#4A5568`), Accent Gold/Teal (`#008080`).
  - Tables: Styled header rows, alternating light fills, clean borders.
  - Callout Boxes: Light blue/grey shading with navy borders for "CISO Executive Takeaways".
- **Required Sections:**
  - **Cover Page:** Title, Muhammad Nafay Aftab, 03-134222-087, BSCS-8A, Information Security, Dr. Nadeem Sarwar, CLO 4, GitHub Link.
  - **1. Executive Summary:** High-level problem, solution architecture, headline results ($\ge 95\%$), and recommendation.
  - **2. Introduction & Real-World Scenario:** Threat landscape, SecureNet Corp scenario, limits of legacy firewalls.
  - **3. Methodology:**
    - 3.1 Dataset & Threat Landscape Justification (UNSW-NB15 rationale).
    - 3.2 Preprocessing & Leak-Free Pipeline (OneHotEncoder, RobustScaler, handling unseen protocols).
    - 3.3 ML Architecture & Justification (Decision Tree baseline vs. Tuned Random Forest).
  - **4. Results & Security Analysis:**
    - 4.1 Comparative Model Performance ($\ge 95\%$ metrics table).
    - 4.2 Confusion Matrix & Operational Trade-offs (False Positives vs. False Negatives).
    - 4.3 Granular Attack Detection Analysis (Table & deep dive into missed stealth attacks like Worms/Backdoors).
    - 4.4 Feature Attribution & Security Insights (Top features driving alerts).
    - 4.5 Real-Time Performance & Line-Rate Feasibility (Latency and throughput analysis).
  - **5. Conclusion & Future Enhancements:** Enterprise roadmap (Deep Packet Inspection, continuous learning, inline zero-trust integration).
  - **6. References:** IEEE-formatted academic citations.
  - **Appendix / GitHub Link:** Direct link to public repository and instructions.

### C. GitHub Repository (`CLO4-IDS-ML-Solution`)
- Clean root directory with:
  - `README.md` (Rich markdown, shields/badges, executive overview, architecture diagram, installation guide, execution commands, performance table, embedded SIEM alert screenshots).
  - `requirements.txt` (Pinned package versions).
  - `.gitignore` (Ignores `__pycache__`, `.ipynb_checkpoints`, raw dumps, and temporary files).
  - `dataset/` (Contains scripts or instructions to locate datasets).
  - `notebooks/CLO4_IDS_ML_Solution.ipynb`.
  - `figures/*.png`.
  - `reports/Project_Report_CLO4.docx`.
  - `src/` (Contains FastAPI app and web dashboard assets).

### D. Bespoke Enterprise SOC Web Dashboard (`src/app.py` & `src/web/`)
A high-performance, single-command Python web dashboard (`python -m src.app` on `http://localhost:8000`) built with FastAPI, modern dark glassmorphic HTML5/CSS3, and Chart.js (zero npm/Node.js dependencies).
- **Aesthetic Design System:**
  - Executive Cyber Dark Mode: Background `#0B132B`, Surface Slate `#1C2541`, Card Glass `#1E293B` with subtle border `rgba(255,255,255,0.08)`.
  - Color Tokens: Normal/Safe Emerald (`#10B981`), Threat/Attack Crimson (`#EF4444`), Brand Cyber Cyan (`#48CAE4`), Warning Amber (`#F59E0B`).
  - Animated live indicators: CSS pulse badges (`@keyframes pulse`) for real-time threat status.
- **Four Dedicated Functional Views:**
  1. **Executive Telemetry & KPI View:**
     - Live KPI metric cards: Total Flows Analyzed, Attack Detection Rate ($\ge 95\%$), False Alarm Rate ($< 5\%$), Mean Flow Latency ($< 50\,\mu\text{s}$).
     - Interactive Chart.js graphs: Model Performance Comparison (Decision Tree baseline vs. Tuned Random Forest champion), Feature Importance ranking, and interactive Confusion Matrix.
  2. **Live Real-Time Streaming Threat Feed:**
     - Simulated streaming engine feeding network flows sequentially into the pipeline.
     - Live SIEM incident table with real-time rows arriving, status badges, attack category tag, confidence score, and mitigation action.
  3. **Single Flow Manual Inspector:**
     - Form inputs for key flow attributes (`proto`, `service`, `state`, `dur`, `sbytes`, `dbytes`, `sttl`, `sload`, `dload`).
     - "Quick Inject Sample Attack" buttons: *Legitimate HTTPS Traffic*, *SYN Flood (DoS)*, *Buffer Overflow (Exploit)*, *Port Scan (Reconnaissance)*.
     - Instant asynchronous prediction with animated gauge, confidence percentage, and per-class probabilities.
  4. **Batch Network CSV Predictor:**
     - Drag-and-drop CSV file uploader for offline network logs.
     - Batch progress indicator, attack breakdown summary pie chart, and "Download Enriched Predictions CSV" export button.

---

## 8. Empirical Proofs & Insight-Driven Decision Framework

In Machine Learning and cybersecurity engineering, an implementation without empirical proof is merely an unverified assertion. Every architectural and preprocessing decision in this project must be grounded in and proved by concrete visual and statistical telemetry:

| Decision / Transformation | Empirical Insight Required | Concrete Visual / Statistical Proof Artifact |
|---|---|---|
| **Class Distribution & Threat Model** | Imbalance between benign flows and rare attack categories (*Worms, Backdoors*). | `figures/eda_attack_distribution.png`: Dual-panel bar chart illustrating binary balance vs. granular 10-class frequency on log-scale. |
| **Volume Skewness & Log1p Need** | Continuous flow features (`sbytes`, `dbytes`, `sload`) span 6 orders of magnitude, which would distort linear splits or distances. | `figures/eda_traffic_volume_skew.png`: Density KDE plots comparing raw skewed byte distributions against smooth $\log(x+1)$ normalized profiles. |
| **Categorical Protocol Sparsity** | 133 protocols exist, with unseen test protocol values (`icmp`, `rtp`). Blind OHE creates curse-of-dimensionality and test crashes. | `figures/eda_top_protocols.png`: Comparative frequency distribution of top 10 protocols in normal vs. attack traffic, showing tail behavior. |
| **Feature Correlation & Redundancy** | Identification of collinear packet count and byte rate features. | `figures/eda_feature_correlation.png`: Clustered correlation matrix heatmap highlighting key predictive clusters. |
| **Threshold Tuning Justification** | Demonstrating why default $\tau=0.50$ is suboptimal for high-consequence intrusion detection. | `figures/precision_recall_threshold.png`: Precision-Recall vs. Decision Threshold curve proving the exact inflection point where Attack Recall crosses 95%. |
| **Feature Importance & SOC Attribution** | Proving the model relies on true network packet behavior rather than noise. | `figures/feature_importance.png`: Ranked horizontal bar chart of top 15 Gini importance features (`ct_state_ttl`, `sttl`, `ct_dst_src_ltm`, etc.). |
| **Asymmetric Cost of Missed Attacks** | Security impact of False Negatives vs. False Positives across attack types. | `figures/attack_recall_breakdown.png`: Granular recall bar chart highlighting detection rates across all 9 attack categories. |
| **Real-Time Line-Rate Feasibility** | Proving the model can run inline without causing network packet dropping. | `figures/latency_throughput.png`: Latency per flow distribution histogram (in microseconds) and throughput benchmark. |

---

## 9. Strict Git & GitHub Workflow Protocol (Feature-Branch Strategy)

To ensure production-level repository health and complete auditability:
1. **Protected `main` Branch:** No unreviewed, unvalidated code may be committed directly to `main`.
2. **Feature-Branch Lifecycle for Every Phase:**
   - For each phase $i$, checkout a dedicated branch:
     ```bash
     git checkout -b feature/phase-$i-<name>
     ```
   - Develop, test, and generate all required proofs on that branch.
   - Run the phase's acceptance criteria validation script.
   - Stage and commit with structured commit messages:
     ```text
     feat(phase-$i): complete <phase name> with empirical validation

     - Implemented <key components>
     - Generated empirical proofs: <list figures>
     - Validated acceptance criteria: <list results>
     ```
   - Checkout `main`, merge the feature branch cleanly (or squash/merge with full context):
     ```bash
     git checkout main
     git merge --no-ff feature/phase-$i-<name> -m "Merge branch 'feature/phase-$i-<name>' into main"
     ```
   - Push updated `main` to GitHub:
     ```bash
     git push origin main
     ```
   - Update `phase_execution_log.md` with commit hash and completion timestamp.

---

---

## 10. Manual Human Action Register & Checkpoints

This project has been deliberately architected with **zero external cloud APIs, zero proprietary services, and zero paid tokens**. The machine learning models, preprocessing pipelines, web dashboard, and report automation run 100% locally and offline.

However, to ensure human oversight and compliance with university policies, Claude Code is instructed to execute all code autonomously while pausing only at the following explicit **Human-in-the-Loop Checkpoints**:

| Checkpoint | Phase | Automated by Claude Code | **Required Manual Action from You** |
|---|---|---|---|
| **CP-1: Git Remote Auth** | **Phase 0** | Configures remote `origin`, stages initial files, and runs `git push -u origin main`. | **Credential Prompt:** If your local Git is not already cached with your GitHub credentials, Claude Code will ask you to authorize or enter your GitHub credentials/PAT in your terminal. |
| **CP-2: Dashboard Review** | **Phase 7** | Builds FastAPI server (`src/app.py`), static dark-mode UI (`src/web/`), and launches server. | **Visual Inspection:** Open `http://localhost:8000` in your browser, test the 4 views (Telemetry, Live Stream, Single-Flow Inspector, CSV Uploader), and confirm you approve the visual design. |
| **CP-3: Report Layout Check** | **Phase 9** | Programmatically generates `reports/Project_Report_CLO4.docx` with your student details and embedded figures. | **Pagination & LMS Check:** Open `Project_Report_CLO4.docx` in Microsoft Word on your machine to verify that the page count is strictly 5–6 pages (excluding cover) before final LMS submission. |

---

## 11. Definition of Done (Quality Gate)
The project is complete if and only if:
1. All code executes cleanly from top to bottom with zero errors in a clean Python 3.10/3.11/3.12 environment.
2. The champion model achieves an authentic test **Accuracy, Attack Recall, and F1-Score $\ge 95\%$**.
3. All high-resolution figures (`eda_*.png`, `confusion_matrix.png`, `feature_importance.png`, `attack_recall_breakdown.png`, `latency_throughput.png`) are saved to `figures/`.
4. The interactive SOC Web Dashboard is fully functional in `src/web/` and launches via `python -m src.app`.
5. `Project_Report_CLO4.docx` is fully generated, strictly 5–6 pages (excluding cover), formatted with student metadata, professional typography, and embedded visual proofs.
6. `README.md` is complete, beautiful, and includes sample screens.
7. The entire repository is committed through disciplined feature branches and pushed to `https://github.com/Nafay-Aftab/CLO4-IDS-ML-Solution`.

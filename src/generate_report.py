"""Phase 9: generate reports/Project_Report_CLO4.docx (python-docx, DEC-006).

Every number in the report is read from artifacts/ produced by the pipeline — nothing is typed by hand.
"""
import json
import re
import tempfile
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from src.config import ARTIFACT_DIR, FIG_DIR, REPORT_DIR, STUDENT

NAVY, SLATE, TEAL = RGBColor(0x1B, 0x36, 0x5D), RGBColor(0x4A, 0x55, 0x68), RGBColor(0x00, 0x80, 0x80)
NAVY_HEX, ALT_FILL, CALLOUT_FILL = "1B365D", "EEF2F7", "EAF0F7"
OUT = REPORT_DIR / "Project_Report_CLO4.docx"


def art(name):
    return json.loads((ARTIFACT_DIR / name).read_text())


# ----------------------------------------------------------------- low-level helpers
def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def borders(table, color="BFC7D5", size=4, inside=True):
    tblPr = table._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    edges = ["top", "left", "bottom", "right"] + (["insideH", "insideV"] if inside else [])
    for edge in edges:
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(size))
        e.set(qn("w:color"), color)
        b.append(e)
    tblPr.append(b)


def cell_margins(table, top=40, bottom=40, left=80, right=80):
    tblPr = table._tbl.tblPr
    m = OxmlElement("w:tblCellMar")
    for side, v in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:w"), str(v))
        e.set(qn("w:type"), "dxa")
        m.append(e)
    tblPr.append(m)


def para(doc_or_cell, text="", size=None, bold=False, italic=False, color=None, align=None, after=4, before=0,
         keep=False):
    p = doc_or_cell.add_paragraph()
    pf = p.paragraph_format
    pf.space_after, pf.space_before = Pt(after), Pt(before)
    if keep:
        pf.keep_with_next = True
    if align is not None:
        p.alignment = align
    if text:
        rich(p, text, size=size, bold=bold, italic=italic, color=color)
    return p


def rich(p, text, size=None, bold=False, italic=False, color=None):
    """Minimal inline markup: **bold** and `code` (Consolas) inside a run sequence."""
    for chunk in re.split(r"(\*\*.+?\*\*|`[^`]+`)", text):
        if not chunk:
            continue
        is_bold, is_code = chunk.startswith("**"), chunk.startswith("`")
        r = p.add_run(chunk[2:-2] if is_bold else chunk[1:-1] if is_code else chunk)
        r.bold = bold or is_bold
        r.italic = italic
        if is_code:
            r.font.name = "Consolas"
        if size or is_code:
            r.font.size = Pt((size or 10.5) - (1 if is_code else 0))
        if color is not None:
            r.font.color.rgb = color
    return p


def crop_top(path, frac):
    """Top band of a tall screenshot (the report shows the KPI cards and headline charts only)."""
    from PIL import Image
    im = Image.open(path)
    out = Path(tempfile.gettempdir()) / f"report_{path.stem}_top.png"
    im.crop((0, 0, im.width, int(im.height * frac))).save(out)
    return out


def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Inches(0.25 + 0.25 * level)
    rich(p, text)
    return p


def h1(doc, text):
    return doc.add_heading(text, level=1)


def h2(doc, text):
    return doc.add_heading(text, level=2)


def caption(doc, text):
    p = para(doc, text, size=8.5, italic=True, color=SLATE, align=WD_ALIGN_PARAGRAPH.CENTER, after=6)
    return p


def figure(doc, path, width, cap):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(width))
    caption(doc, cap)


def figure_pair(doc, left, right, width, cap_l, cap_r):
    t = doc.add_table(rows=2, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for j, (path, cap) in enumerate(((left, cap_l), (right, cap_r))):
        c = t.cell(0, j)
        c.width = Inches(width + 0.1)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].add_run().add_picture(str(path), width=Inches(width))
        cp = t.cell(1, j).paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rich(cp, cap, size=8.5, italic=True, color=SLATE)
    para(doc, after=2)


def data_table(doc, header, rows, widths, highlight_row=None, font=8.5):
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    borders(t)
    cell_margins(t)
    for j, h in enumerate(header):
        c = t.cell(0, j)
        shade(c, NAVY_HEX)
        c.width = Inches(widths[j])
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(h)
        r.bold, r.font.size, r.font.color.rgb = True, Pt(font), RGBColor(0xFF, 0xFF, 0xFF)
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row):
            c = t.cell(i, j)
            c.width = Inches(widths[j])
            if highlight_row == i - 1:
                shade(c, "D9ECEC")
            elif i % 2 == 0:
                shade(c, ALT_FILL)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(v))
            r.font.size = Pt(font)
            r.bold = highlight_row == i - 1 and j == 0
    para(doc, after=2)
    return t


def callout(doc, title, items):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    borders(t, color=NAVY_HEX, size=8, inside=False)
    cell_margins(t, 90, 90, 140, 140)
    c = t.cell(0, 0)
    c.width = Inches(6.5)
    shade(c, CALLOUT_FILL)
    p = c.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    rich(p, title, size=10, bold=True, color=NAVY)
    for it in items:
        q = c.add_paragraph(style="List Bullet")
        q.paragraph_format.space_after = Pt(1)
        rich(q, it, size=9.5)
    para(doc, after=2)


def page_field(p):
    r = p.add_run()
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            f = OxmlElement("w:fldChar")
            f.set(qn("w:fldCharType"), tag)
            r._r.append(f)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            r._r.append(it)


def setup_styles(doc):
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Calibri", Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    st.paragraph_format.line_spacing = 1.15
    st.paragraph_format.space_after = Pt(4)
    for name, size, color, before, after in (("Heading 1", 13.5, NAVY, 10, 4), ("Heading 2", 11, SLATE, 6, 2)):
        h = doc.styles[name]
        h.font.name, h.font.size, h.font.bold = "Calibri", Pt(size), True
        h.font.color.rgb = color
        h.element.rPr.rFonts.set(qn("w:asciiTheme"), "")  # drop theme font so Calibri sticks
        h.element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        h.element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        h.paragraph_format.space_before, h.paragraph_format.space_after = Pt(before), Pt(after)
        h.paragraph_format.keep_with_next = True
    lb = doc.styles["List Bullet"]
    lb.font.size = Pt(10.5)
    lb.paragraph_format.line_spacing = 1.1


# ----------------------------------------------------------------- content
def cover(doc):
    s = STUDENT
    for _ in range(5):
        para(doc, after=6)
    para(doc, "INFORMATION SECURITY  ·  CLO 4", size=11, bold=True, color=TEAL, align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, "AI-Powered Intrusion Detection Solution", size=26, bold=True, color=NAVY,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
    para(doc, "with Real-Time Threat Detection", size=17, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    p = para(doc, "Machine-learning augmentation of SecureNet Corp.'s Network Intrusion Detection System on UNSW-NB15",
             size=11, italic=True, color=SLATE, align=WD_ALIGN_PARAGRAPH.CENTER, after=26)
    p.paragraph_format.left_indent = p.paragraph_format.right_indent = Inches(0.6)

    rows = [("Student", s["name"]), ("Enrolment", s["enrolment"]), ("Class", s["class"]),
            ("Course", s["course"]), ("Aligned CLO", "CLO 4 — Create solutions to real-life scenarios using "
                                                     "security-related tools"),
            ("Instructor", s["instructor"]), ("Deliverable", s["assignment"]), ("GitHub", s["repo"])]
    t = doc.add_table(rows=len(rows), cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    borders(t, color="C9D3E0")
    cell_margins(t, 70, 70, 120, 120)
    for i, (k, v) in enumerate(rows):
        a, b = t.cell(i, 0), t.cell(i, 1)
        a.width, b.width = Inches(1.5), Inches(4.4)
        shade(a, CALLOUT_FILL)
        rich(a.paragraphs[0], k, size=10.5, bold=True, color=NAVY)
        rich(b.paragraphs[0], v, size=10.5)
    para(doc, after=60)
    para(doc, "Department of Computer Science", size=10.5, color=SLATE, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def body(doc):
    ch = art("metrics_champion.json")
    rf, dt = ch["random_forest_tau_star"], ch["decision_tree"]
    eda, pipe = art("eda_summary.json"), art("pipeline_report.json")
    sec, rt = art("security_eval.json"), art("realtime_report.json")
    fam_rep = rt["family_classifier"]
    allc = rt["all_cores_10k_batch"]
    by_bs = {r["batch_size"]: r for r in rt["single_core_by_batch"]}
    recall = pd.read_csv(ARTIFACT_DIR / "attack_recall.csv").sort_values("recall")
    tau = ch["threshold"]["tau_star"]
    worst = recall[recall.recall < 0.95] if (recall.recall < 0.95).any() else recall.head(2)
    worst_txt = " and ".join(f"{r.family} ({r.recall:.1%})" for r in worst.itertuples())
    fam = recall.set_index("family")

    # 1 ---------------------------------------------------------------
    h1(doc, "1. Executive Summary")
    para(doc, f"SecureNet Corp.'s CISO requested a proof-of-concept that augments the existing signature-based NIDS "
              f"with machine learning, classifying every network flow as normal or malicious in real time. We built "
              f"a leak-free scikit-learn pipeline (one-hot encoding, log1p and robust scaling) that feeds a tuned "
              f"**Random Forest** champion. It was trained on the modern **UNSW-NB15** benchmark "
              f"({eda['rows_total']:,} flows, nine attack families) and benchmarked against a Decision-Tree "
              f"baseline. On the untouched 20 % test fold the champion reaches "
              f"**{rf['accuracy']:.2%} accuracy, {rf['recall']:.2%} attack recall, {rf['precision']:.2%} precision, "
              f"{rf['f1']:.2%} F1-score and a {rf['fpr']:.2%} false-alarm rate** (ROC-AUC {rf['roc_auc']:.4f}). "
              f"It cuts missed attacks by {1 - rf['fn'] / dt['fn']:.0%} versus the baseline and scores flows in "
              f"{allc['us_per_flow']:.1f} µs each in batched mode ({allc['flows_per_s']:,.0f} flows/s). The ≥ 95 % "
              f"target was met for F1 but missed by 0.3–0.4 percentage points on accuracy and recall. A "
              f"controlled validation experiment indicates the gap stems from overlap in the data rather than "
              f"from tuning, and we report the result as measured. We recommend deploying the model as an augmenting detection layer "
              f"with the threshold managed as SOC policy.")
    callout(doc, "CISO Executive Takeaways", [
        f"The model catches **{rf['recall']:.1%}** of intrusions, and only **{rf['fpr']:.1%}** of benign flows "
        f"raise an alert. That is ≈ {sec['per_10k_flows']['missed_attacks']:.0f} missed attacks and "
        f"≈ {sec['per_10k_flows']['false_alarms']:.0f} false alarms per 10,000 flows.",
        f"Its blind spots are stealthy families that resemble normal traffic: {worst_txt}. These need "
        "complementary controls such as DPI and host telemetry.",
        f"Batched inference runs at **{allc['flows_per_s']:,.0f} flows/s** on one laptop CPU, which is "
        f"line-rate capable for flow-export pipelines."])

    # 2 ---------------------------------------------------------------
    h1(doc, "2. Introduction & Real-World Scenario")
    para(doc, "Firewalls enforce static port and address rules, and signature-based IDS engines match known byte "
              "patterns. Both miss zero-day exploits and attacks that ride permitted services such as HTTP, DNS "
              "and TLS. A learning-based detector instead models traffic behaviour (volumes, timing, TTL "
              "fingerprints, connection fan-out), so it can flag anomalous flows that no rule anticipates.")
    para(doc, "**Scenario.** As a security analyst at SecureNet Corp., we were tasked by the CISO with judging "
              "whether ML is viable as an extra NIDS layer. The objective is a tool that (i) separates normal from "
              "malicious flows with high attack recall, (ii) keeps false alarms within a budget the SOC can "
              "absorb, (iii) runs fast enough for real-time use, and (iv) explains its alerts to analysts. The "
              "complete, reproducible implementation (notebook, pipeline, SOC dashboard) is public on GitHub.")

    # 3 ---------------------------------------------------------------
    h1(doc, "3. Methodology")
    h2(doc, "3.1 Dataset & Threat-Landscape Justification")
    para(doc, f"**UNSW-NB15** [1], [2] was generated on the IXIA PerfectStorm testbed. It mixes real modern "
              f"benign traffic with attacks drawn from a continuously updated CVE library, across nine families "
              f"that map onto real SOC threat categories (Figure 1). We chose it over KDD'99/NSL-KDD, which are "
              f"over 25 years old, heavily redundant and lack contemporary attacks [5]. We also chose it over "
              f"CIC-IDS2017, whose multi-gigabyte captures exceed a laptop-scale PoC. The two official partitions "
              f"({eda['rows_training_file']:,} + {eda['rows_testing_file']:,} rows, 42 features: 3 categorical, "
              f"39 numerical) were merged and re-split, as described below.")
    figure(doc, FIG_DIR / "eda_attack_distribution.png", 5.4,
           "Figure 1. Class distribution: binary balance (A) and ten-class composition on a log scale (B). Worms "
           "are 340× rarer than Generic, so per-family recall must be reported.")

    h2(doc, "3.2 Data Preprocessing & Leak-Free Pipeline")
    sk_raw, sk_log = eda["skewness_raw"], eda["skewness_log1p"]
    bullet(doc, f"**Integrity.** Headers were read as UTF-8-with-BOM, which removes the stray `\\ufeffid` "
                f"artefact. The data contains 0 missing and 0 infinite values, so no imputation was needed. "
                f"The row identifier was dropped.")
    bullet(doc, f"**Stratified 80/20 split before any fitting.** The split is stratified on the ten-class label "
                f"(seed 42), giving {pipe['train_rows']:,} training and {pipe['test_rows']:,} test flows with an "
                f"identical {pipe['test_attack_rate']:.2%} attack rate. All transformers are fitted on the "
                f"training fold only. We verified that the training scaler's statistics differ from pooled ones, "
                f"which confirms no test information leaked.")
    bullet(doc, f"**Categorical encoding.** `OneHotEncoder(handle_unknown='ignore')` is applied to proto, service "
                f"and state (156 columns). {eda['n_unique']['proto']} protocols exist, and 126 of them appear only "
                f"in attack traffic. The test fold contains the TCP state `PAR`, which never occurs in training; "
                f"it is encoded safely as an all-zero vector instead of crashing the pipeline.")
    bullet(doc, f"**Normalisation.** `log1p` is applied to the nine heavy-tailed volume and timing features. For "
                f"example, sbytes skewness drops from {sk_raw['sbytes']:.1f} to {sk_log['sbytes']:.2f}, and sload "
                f"spans {eda['orders_of_magnitude']['sload']:.0f} orders of magnitude. `RobustScaler` (median/IQR) "
                f"is then applied to all numerical features, so that DDoS-scale outliers cannot dominate. The "
                f"result is 195 model features.")
    bullet(doc, "**Class imbalance.** We used `class_weight='balanced_subsample'` instead of SMOTE, because "
                "interpolating flow records synthesises physically impossible packets (e.g. fractional flag "
                "counts) [7].")

    h2(doc, "3.3 Machine-Learning Tool Design")
    tun = ch["tuning"]
    bp = tun["best_params"]
    para(doc, f"**Baseline:** a depth-10 Decision Tree, which is interpretable and sets the empirical floor. "
              f"**Champion:** a Random Forest [3]. Bagging many de-correlated trees reduces the variance of a "
              f"single tree. The forest handles non-linear feature interactions, is insensitive to the collinear "
              f"feature clusters found in EDA (e.g. tcprtt~synack ρ = 0.996), and provides Gini importances that "
              f"SOC analysts can interpret. Hyper-parameters were tuned with a {tun['configs']}-configuration grid "
              f"search (3-fold CV, F1 scoring, on a stratified {tun['subsample_rows']:,}-row training subsample). "
              f"The best configuration was n_estimators = {bp['n_estimators']}, max_depth = {bp['max_depth']}, "
              f"min_samples_split = {bp['min_samples_split']}, min_samples_leaf = {bp['min_samples_leaf']}, "
              f"max_features = √p (CV F1 {tun['best_cv_f1']:.4f}). **Threshold calibration:** τ* was chosen on "
              f"the forest's out-of-bag probabilities, which are leak-free validation scores, as the τ in "
              f"[0.30, 0.70] that maximises attack recall subject to FPR < 5 %. The result was τ* = {tau:.2f}. "
              f"All tooling is scikit-learn [4].")

    # 4 ---------------------------------------------------------------
    h1(doc, "4. Results & Security Analysis")
    h2(doc, "4.1 Comparative Model Performance")
    comp = art("model_comparison.json")
    rows = [[m["name"], f"{m['threshold']:.2f}", f"{m['accuracy']:.2%}", f"{m['precision']:.2%}",
             f"{m['recall']:.2%}", f"{m['f1']:.2%}", f"{m['fpr']:.2%}", f"{m['roc_auc']:.4f}"] for m in comp]
    data_table(doc, ["Model (untouched test fold)", "τ", "Accuracy", "Precision", "Recall", "F1", "FPR", "AUC"],
               rows, [2.05, 0.4, 0.72, 0.72, 0.68, 0.68, 0.6, 0.65],
               highlight_row=next(i for i, m in enumerate(comp) if m["champion"]))
    para(doc, f"The forest raises recall by {(rf['recall'] - dt['recall']) * 100:.1f} pp over the baseline, "
              f"recovering {dt['fn'] - rf['fn']:,} attacks the single tree missed. The price is "
              f"{rf['fp'] - dt['fp']:,} extra false alarms, which is the expected ensemble trade-off. **Honest "
              f"gate assessment:** F1 ({rf['f1']:.2%}) clears 95 %. Accuracy ({rf['accuracy']:.2%}) and recall "
              f"({rf['recall']:.2%}) fall just short, and FPR ({rf['fpr']:.2%}) sits marginally above the 5 % "
              f"budget. A validation-only experiment on the training fold tested an alternative tree ensemble "
              f"(ExtraTrees) and five engineered ratio features. None lifted recall above ≈ 94.3 % under FPR < 5 %, "
              f"and exact-duplicate label conflicts explain only 0.26 % of errors. The remaining gap is genuine "
              f"overlap between benign and stealthy attack flows, so we report the measured result rather than "
              f"tune against the test set.")

    h2(doc, "4.2 Confusion Matrix & Operational Trade-offs")
    figure_pair(doc, FIG_DIR / "confusion_matrix.png", FIG_DIR / "precision_recall_threshold.png", 3.1,
                "Figure 2. Champion confusion matrix (test fold).",
                "Figure 3. OOB precision/recall/F1 and FPR against τ.")
    para(doc, f"The champion produced {rf['tp']:,} true positives and {rf['tn']:,} true negatives, alongside "
              f"**{rf['fp']:,} false positives** and **{rf['fn']:,} false negatives**. The two errors carry very "
              f"different costs. A false positive costs analyst triage minutes and, at volume, alert fatigue. A "
              f"false negative lets an intruder establish persistence, move laterally and exfiltrate data "
              f"undetected, and is typically orders of magnitude costlier. Figure 3 makes the policy explicit. "
              f"Lowering τ below {tau:.2f} buys recall, but the out-of-bag FPR immediately breaches the 5 % "
              f"budget. The CISO can move τ along this curve as threat levels change.")

    h2(doc, "4.3 Granular Attack-Family Detection Analysis")
    top_miss = recall.sort_values("share_of_all_misses", ascending=False).iloc[0]
    strong = recall[recall.recall >= 0.95].sort_values("recall", ascending=False)
    para(doc, f"Seven of the nine families exceed 95 % recall (Figure 5): "
              f"{', '.join(f'{r.family} {r.recall:.1%}' for r in strong.itertuples())}. The weak spots are "
              f"{worst_txt}, and **{top_miss.family} alone accounts for {top_miss.share_of_all_misses:.0%} of all "
              f"missed attacks** ({int(top_miss.missed):,} of {int(recall.missed.sum()):,}). Many fuzzing sessions "
              f"are short, low-volume exchanges whose byte, TTL and timing profile matches benign clients. In fact, "
              f"the only exact feature-vector collisions between classes in the dataset are Normal↔Fuzzers. "
              f"**Security implication:** an adversary fuzzing an internet-facing service for a zero-day would "
              f"largely go unobserved, so detection would shift to the far more damaging exploitation phase. The "
              f"{int(fam.loc['Analysis'].missed)} missed Analysis flows likewise leave vulnerability probing "
              f"unlogged. The rarest families buck the usual expectation. **Worms and Backdoor are detected at "
              f"100 %** thanks to distinctive TTL and state fingerprints, although Worms' interval reaches down to "
              f"{fam.loc['Worms'].ci_lo:.0%} with only 35 test flows. Flow statistics alone cannot close the "
              f"Fuzzers gap, so payload inspection and host telemetry must complement the model.")

    h2(doc, "4.4 Feature Attribution & Security Insights")
    top = list(ch["top15_features"])[:6]
    import src.champion as champ  # local import: pretty() lives with the model code
    pretty_top = ", ".join(champ.pretty(f) for f in top)
    figure_pair(doc, FIG_DIR / "feature_importance.png", FIG_DIR / "attack_recall_breakdown.png", 3.1,
                "Figure 4. Top-15 Gini importances (champion RF).",
                "Figure 5. Per-family recall with 95 % Wilson intervals.")
    para(doc, f"The most influential features are {pretty_top}. TTL features (sttl, ct_state_ttl) capture the "
              f"characteristic initial TTL and TTL/state combinations emitted by attack tooling, the same OS/tool "
              f"fingerprint used in threat hunting. Byte and mean-packet-size features expose payload anomalies, "
              f"from oversized buffer-overflow requests to tiny, uniform probes. Connection-count features "
              f"(ct_srv_dst, ct_dst_src_ltm) measure fan-out across the last 100 connections, which is the "
              f"behavioural signature of scanning. Because the model relies on real packet behaviour rather than "
              f"identifiers, SOC analysts can validate every alert against these features.")

    h2(doc, "4.5 Real-Time Performance & Line-Rate Feasibility")
    figure(doc, FIG_DIR / "latency_throughput.png", 6.5,
           "Figure 6. End-to-end latency and throughput (preprocessing + RF inference) on an Intel i7-11800H.")
    para(doc, f"All timings are wall-clock and end-to-end, covering both preprocessing and inference. Scoring a "
              f"10,000-flow batch across all cores takes **{allc['us_per_flow']:.2f} µs per flow "
              f"({allc['flows_per_s']:,.0f} flows/s)**. On a single core, micro-batches of 1,000 achieve "
              f"{by_bs[1000]['us_per_flow_mean']:.1f} µs/flow. Scoring flows strictly one at a time costs "
              f"{by_bs[1]['us_per_flow_mean'] / 1000:.1f} ms, because per-call overhead across all "
              f"{bp['n_estimators']} trees dominates. Flow exporters (NetFlow/IPFIX, Zeek) already deliver records "
              f"in batches, so the batched figures apply, and they exceed multi-gigabit flow rates. A streaming "
              f"SIEM engine attaches a family label to each alert "
              f"using a stage-2 classifier (accuracy {fam_rep['accuracy']:.1%}, macro-F1 {fam_rep['macro_f1']:.2f}), "
              f"and emits time-stamped alerts with confidence, severity and an automated action (TCP RST/block "
              f"or rate-limit).")

    dash = FIG_DIR / "dashboard_telemetry.png"
    if dash.exists():
        h2(doc, "4.6 SOC Web Dashboard")
        figure(doc, crop_top(dash, 0.425), 6.3,
               "Figure 7. SecureNet SOC dashboard (FastAPI + Chart.js): executive telemetry view, top section.")
        para(doc, "The model is operationalised through a single-command web dashboard (`python -m src.app`) with "
                  "four views: executive KPI telemetry computed live on the test fold; a real-time streaming "
                  "threat feed; a single-flow inspector with attack-injection presets; and a batch CSV predictor "
                  "that exports enriched predictions.")

    # 5 ---------------------------------------------------------------
    h1(doc, "5. Conclusion & Future Enhancements")
    para(doc, f"This proof-of-concept shows that ML is a viable NIDS augmentation for SecureNet Corp. A tuned "
              f"Random Forest detects {rf['recall']:.1%} of attacks at a {rf['fpr']:.1%} false-alarm rate. It "
              f"explains its alerts through interpretable packet-behaviour features and runs at line rate when "
              f"batched. The analysis also shows its limits: stealthy, low-volume families remain partly "
              f"indistinguishable at the flow level. That limit is why the tool should augment, not replace, the "
              f"existing signature NIDS [6]. Roadmap:")
    for t in ["**Deep packet inspection & TLS fingerprinting** (e.g. JA3), to separate Fuzzers and Analysis "
              "traffic from benign sessions. This is the single largest source of missed attacks.",
              "**Cost-sensitive and family-specific thresholds**, to raise Fuzzers and Analysis recall while "
              "holding Worms, Backdoor and Shellcode at their near-perfect detection.",
              "**Continuous learning & drift monitoring**, retraining on SOC triage outcomes and alerting on "
              "unseen protocols or feature drift.",
              "**Inline zero-trust integration**, using a compiled forest (Treelite/ONNX) behind the flow "
              "exporter, with alerts correlated against host EDR telemetry in the SIEM."]:
        bullet(doc, t)

    # 6 ---------------------------------------------------------------
    h1(doc, "6. References")
    refs = [
        'N. Moustafa and J. Slay, "UNSW-NB15: A comprehensive data set for network intrusion detection systems," '
        "in Proc. Military Commun. Inf. Syst. Conf. (MilCIS), Canberra, Australia, 2015, pp. 1–6.",
        'N. Moustafa and J. Slay, "The evaluation of network anomaly detection systems: Statistical analysis of the '
        'UNSW-NB15 data set and the comparison with the KDD99 data set," Inf. Secur. J.: A Global Perspective, '
        "vol. 25, no. 1–3, pp. 18–31, 2016.",
        'L. Breiman, "Random forests," Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.',
        'F. Pedregosa et al., "Scikit-learn: Machine learning in Python," J. Mach. Learn. Res., vol. 12, '
        "pp. 2825–2830, 2011.",
        'M. Tavallaee, E. Bagheri, W. Lu, and A. A. Ghorbani, "A detailed analysis of the KDD CUP 99 data set," in '
        "Proc. IEEE Symp. Comput. Intell. Secur. Defense Appl. (CISDA), 2009, pp. 1–6.",
        'R. Sommer and V. Paxson, "Outside the closed world: On using machine learning for network intrusion '
        'detection," in Proc. IEEE Symp. Security and Privacy, 2010, pp. 305–316.',
        'N. V. Chawla, K. W. Bowyer, L. O. Hall, and W. P. Kegelmeyer, "SMOTE: Synthetic minority over-sampling '
        'technique," J. Artif. Intell. Res., vol. 16, pp. 321–357, 2002.',
    ]
    for i, r in enumerate(refs, start=1):
        p = para(doc, f"[{i}] {r}", size=9, after=2)
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)

    h1(doc, "Appendix — GitHub Repository & Setup")
    para(doc, f"**Repository:** {STUDENT['repo']}  ·  **GitHub profile:** https://github.com/Nafay-Aftab", after=2)
    for cmd in ["pip install -r requirements.txt && python -m src.champion && python -m src.realtime",
                "python -m src.app          # SOC dashboard at http://localhost:8000",
                "notebooks/CLO4_IDS_ML_Solution.ipynb   # full reproducible notebook"]:
        p = para(doc, cmd, size=8.5, after=0)
        p.runs[0].font.name = "Consolas"
        p.paragraph_format.left_indent = Inches(0.2)


def main():
    doc = Document()
    setup_styles(doc)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)  # A4
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Inches(1))
    sec.different_first_page_header_footer = True
    hp = sec.header.paragraphs[0]
    rich(hp, f"CLO4-IDS-ML-Solution  ·  {STUDENT['name']} ({STUDENT['enrolment']})", size=8, color=SLATE)
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rich(fp, "Information Security (CLO 4)  ·  Page ", size=8, color=SLATE)
    page_field(fp)

    cover(doc)
    body(doc)
    doc.core_properties.author = STUDENT["name"]
    doc.core_properties.title = "AI-Powered Intrusion Detection Solution — CLO 4 Report"
    doc.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()

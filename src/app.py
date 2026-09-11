"""Phase 7: FastAPI backend for the SecureNet SOC dashboard.

Run:  python -m src.app   ->   http://localhost:8000

All telemetry is computed live at start-up by scoring the untouched test fold with the serialized
champion bundle, so the numbers on screen are always the model's authentic behaviour.
"""
from __future__ import annotations

import asyncio
import io
import json
import time
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from src.config import ARTIFACT_DIR, CATEGORICAL, MODEL_DIR, ROOT, SEED, STUDENT, TARGET, TARGET_CAT
from src.data import load_split
from src.evaluate import binary_metrics
from src.realtime import ACTION, SEVERITY

WEB = ROOT / "src" / "web"
MAX_BATCH_ROWS = 500_000
FORM_FIELDS = ["proto", "service", "state", "dur", "sbytes", "dbytes", "sttl", "sload", "dload"]


class Engine:
    """Champion bundle + stage-2 family classifier + test-fold context for the dashboard."""

    def __init__(self):
        bundle_path = MODEL_DIR / "champion_bundle.joblib"
        if not bundle_path.exists():
            raise SystemExit("models/champion_bundle.joblib missing — run `python -m src.champion` first.")
        b = joblib.load(bundle_path)
        self.name, self.pre, self.model, self.tau = b["name"], b["pre"], b["model"], float(b["tau"])
        self.family = joblib.load(MODEL_DIR / "family_rf.joblib")
        for m in (self.model, self.family):
            if hasattr(m, "n_jobs"):
                m.n_jobs = 1  # single-flow requests: avoid thread-pool spin-up per call

        X_tr, self.X_te, _, self.y_te, _, self.cat_te = load_split()
        self.features = list(X_tr.columns)
        self.numeric = [c for c in self.features if c not in CATEGORICAL]
        self.defaults = {**{c: X_tr[c].mode().iat[0] for c in CATEGORICAL},
                         **{c: float(X_tr[c].median()) for c in self.numeric}}
        ohe = self.pre.named_transformers_["cat"]
        self.categories = {c: sorted(map(str, cats)) for c, cats in zip(CATEGORICAL, ohe.categories_)}

        t0 = time.perf_counter()
        self.p_te = self.proba(self.X_te)
        self.score_seconds = time.perf_counter() - t0
        self.telemetry = self._telemetry()
        self.presets = self._presets()
        self.batches: OrderedDict[str, tuple[str, bytes]] = OrderedDict()

    # ---------- inference ----------
    def proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(self.pre.transform(X))[:, 1]

    def frame(self, records: list[dict]) -> tuple[pd.DataFrame, list[str]]:
        df = pd.DataFrame.from_records(records)
        missing = [c for c in self.features if c not in df.columns]
        for c in self.features:
            if c not in df.columns:
                df[c] = self.defaults[c]
        df = df[self.features].copy()
        for c in CATEGORICAL:
            df[c] = df[c].fillna(self.defaults[c]).astype(str).str.strip()
        for c in self.numeric:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(self.defaults[c]).clip(lower=0)
        return df, missing

    def enrich(self, p: float, Z=None) -> dict:
        if p < self.tau:
            return {"verdict": "NORMAL", "family": None, "severity": "INFO", "action": "Flow Allowed",
                    "confidence": 1 - p}
        fam = self.family.predict(Z)[0]
        sev = SEVERITY[fam]
        return {"verdict": "ATTACK", "family": fam, "severity": sev, "action": ACTION[sev], "confidence": p}

    # ---------- start-up telemetry ----------
    def _telemetry(self) -> dict:
        y, p = self.y_te.to_numpy(), self.p_te
        m = binary_metrics(y, (p >= self.tau).astype(int), p)
        pred = p >= self.tau
        families = []
        for fam in sorted(set(self.cat_te) - {"Normal"}):
            mask = (self.cat_te == fam).to_numpy()
            families.append({"family": fam, "support": int(mask.sum()), "detected": int(pred[mask].sum()),
                             "recall": float(pred[mask].mean())})

        models = json.loads((ARTIFACT_DIR / "model_comparison.json").read_text())
        for mm in models:
            mm["specificity"] = 1 - mm["fpr"]
        imp = pd.read_csv(ARTIFACT_DIR / "feature_importance.csv").head(15)
        rt_path = ARTIFACT_DIR / "realtime_report.json"
        rt = json.loads(rt_path.read_text())["all_cores_10k_batch"] if rt_path.exists() else {}
        return {
            "model_name": self.name, "student": STUDENT,
            "kpis": {"total_flows": len(y), "test_attacks": int(y.sum()), "test_normal": int((y == 0).sum()),
                     "recall": m["recall"], "fpr": m["fpr"], "accuracy": m["accuracy"], "f1": m["f1"],
                     "tau": self.tau, "latency_us": rt.get("us_per_flow"), "flows_per_s": rt.get("flows_per_s"),
                     "startup_scoring_seconds": round(self.score_seconds, 3)},
            "confusion": {k: m[k] for k in ("tp", "fp", "tn", "fn")},
            "models": models,
            "features": [{"name": r.feature_pretty, "importance": r.gini_importance} for r in imp.itertuples()],
            "families": families,
        }

    def _presets(self) -> list[dict]:
        """Real test-fold flows: for each preset, the *median-scored* flow of its class (its most
        representative example — neither cherry-picked nor an outlier). Masks are tried in order and
        the description states exactly what was drawn."""
        X, cat = self.X_te, self.cat_te
        spec = [
            # UNSW-NB15 contains no benign TLS ('ssl') flows — all 16 ssl rows are attacks — so the
            # benign web preset is honestly an HTTP session.
            ("Legitimate Web Traffic (HTTP)", [(cat == "Normal") & (X.service == "http"), cat == "Normal"]),
            ("SYN Flood (DoS)", [(cat == "DoS") & (X.proto == "tcp"), cat == "DoS"]),
            ("Buffer Overflow (Exploit)", [(cat == "Exploits") & (X.proto == "tcp"), cat == "Exploits"]),
            ("Port Scan (Reconnaissance)", [(cat == "Reconnaissance") & (X.proto == "tcp"),
                                            cat == "Reconnaissance"]),
        ]
        out = []
        for label, masks in spec:
            idx = next(ix for m in masks if (ix := np.flatnonzero(m.to_numpy())).size)
            i = int(idx[np.argsort(self.p_te[idx], kind="stable")[len(idx) // 2]])  # median P(attack)
            row = X.iloc[i]
            flow = {k: (v.item() if hasattr(v, "item") else v) for k, v in row.to_dict().items()}
            desc = (f"Median-scored UNSW-NB15 '{cat.iat[i]}' flow · {row.proto}/{row.service}/{row.state}"
                    f" · test #{i}")
            out.append({"label": label, "description": desc, "flow": flow, "flow_id": i, "truth": cat.iat[i]})
        return out


engine: Engine | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global engine
    engine = Engine()
    k = engine.telemetry["kpis"]
    print(f"[SOC] {engine.name} loaded | test fold scored in {engine.score_seconds:.2f}s | "
          f"recall {k['recall']:.4f} FPR {k['fpr']:.4f} | http://localhost:8000", flush=True)
    yield


app = FastAPI(title="SecureNet SOC — ML-NIDS", version="1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
                   allow_methods=["GET", "POST"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


@app.get("/api/telemetry")
def telemetry():
    return engine.telemetry


@app.get("/api/presets")
def presets():
    return {"presets": engine.presets, "categories": engine.categories,
            "defaults": {k: engine.defaults[k] for k in FORM_FIELDS}}


@app.post("/api/predict/single")
def predict_single(flow: dict):
    df, missing = engine.frame([flow])
    t0 = time.perf_counter()
    Z = engine.pre.transform(df)
    p = float(engine.model.predict_proba(Z)[0, 1])
    res = engine.enrich(p, Z)
    lat = (time.perf_counter() - t0) * 1e6
    fam_p = None
    if res["verdict"] == "ATTACK":
        probs = engine.family.predict_proba(Z)[0]
        fam_p = sorted(({"family": c, "p": float(v)} for c, v in zip(engine.family.classes_, probs)),
                       key=lambda d: -d["p"])
    return {**res, "p_attack": p, "tau": engine.tau, "latency_us": lat, "family_proba": fam_p,
            "defaulted": len(missing)}


@app.post("/api/predict/batch")
async def predict_batch(file: UploadFile = File(...)):
    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig", low_memory=False)
    except Exception as exc:  # noqa: BLE001 — surface parser errors to the analyst
        raise HTTPException(400, f"Could not parse CSV: {exc}") from exc
    df.columns = [str(c).replace("﻿", "").strip() for c in df.columns]
    if df.empty:
        raise HTTPException(400, "CSV contains no rows.")
    if len(df) > MAX_BATCH_ROWS:
        raise HTTPException(413, f"CSV exceeds {MAX_BATCH_ROWS:,} rows.")
    if not set(engine.features) & set(df.columns):
        raise HTTPException(400, "No UNSW-NB15 feature columns found (expected e.g. proto, service, sbytes…).")

    X, missing = engine.frame(df.to_dict(orient="records"))
    t0 = time.perf_counter()
    Z = engine.pre.transform(X)
    p = engine.model.predict_proba(Z)[:, 1]
    attack = p >= engine.tau
    fam = np.full(len(df), "", dtype=object)
    if attack.any():
        fam[attack] = engine.family.predict(Z[attack])
    secs = time.perf_counter() - t0

    out = df.copy()
    out["p_attack"] = p.round(6)
    out["prediction"] = np.where(attack, "ATTACK", "NORMAL")
    out["predicted_family"] = np.where(attack, fam, "Normal")
    out["severity"] = [SEVERITY.get(f, "INFO") if a else "INFO" for f, a in zip(fam, attack)]
    out["action"] = [ACTION[SEVERITY[f]] if a else "Flow Allowed" for f, a in zip(fam, attack)]

    metrics = None
    labels = None
    if TARGET in df.columns:
        labels = pd.to_numeric(df[TARGET], errors="coerce")
    elif TARGET_CAT in df.columns:
        labels = (df[TARGET_CAT].astype(str).str.strip() != "Normal").astype(int)
    if labels is not None and labels.notna().all() and labels.nunique() == 2:
        metrics = binary_metrics(labels.astype(int).to_numpy(), attack.astype(int), p)

    counts = out["predicted_family"].value_counts()
    fams = counts.drop("Normal", errors="ignore")
    breakdown = [{"label": "Normal", "count": int(counts.get("Normal", 0))}]
    breakdown += [{"label": f, "count": int(n)} for f, n in fams.head(4).items()]
    if len(fams) > 4:
        breakdown.append({"label": "Other attacks", "count": int(fams.iloc[4:].sum())})

    token = uuid.uuid4().hex
    name = (file.filename or "flows.csv").rsplit(".", 1)[0] + "_enriched.csv"
    engine.batches[token] = (name, out.to_csv(index=False).encode())
    while len(engine.batches) > 5:
        engine.batches.popitem(last=False)

    preview_cols = [c for c in ["proto", "service", "state", "sbytes", "dbytes", TARGET_CAT] if c in out.columns]
    preview_cols += ["p_attack", "prediction", "predicted_family", "action"]
    preview = out[preview_cols].head(200).replace({np.nan: None}).to_dict(orient="records")
    return {"token": token, "download_name": name, "rows": len(out), "attacks": int(attack.sum()),
            "normal": int((~attack).sum()), "seconds": secs, "flows_per_s": len(out) / max(secs, 1e-9),
            "metrics": metrics, "breakdown": breakdown, "missing_filled": missing,
            "preview_columns": preview_cols, "preview": preview}


@app.get("/api/predict/batch/{token}")
def download_batch(token: str):
    if token not in engine.batches:
        raise HTTPException(404, "Result expired — re-upload the CSV.")
    name, data = engine.batches[token]
    return Response(data, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@app.get("/api/sample.csv")
def sample_csv():
    rng = np.random.default_rng(SEED)
    idx = np.sort(rng.choice(len(engine.X_te), 2000, replace=False))
    df = engine.X_te.iloc[idx].copy()
    df[TARGET_CAT] = engine.cat_te.iloc[idx].to_numpy()
    df[TARGET] = engine.y_te.iloc[idx].to_numpy()
    return Response(df.to_csv(index=False), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="unsw_nb15_sample_2000.csv"'})


@app.get("/api/stream/simulated")
async def stream(request: Request, rate: float = 5.0):
    rate = float(np.clip(rate, 0.5, 30))
    order = np.random.default_rng().permutation(len(engine.X_te))  # fresh replay order per connection

    def score(i: int) -> dict:
        row = engine.X_te.iloc[[i]]
        t0 = time.perf_counter()
        Z = engine.pre.transform(row)
        p = float(engine.model.predict_proba(Z)[0, 1])
        res = engine.enrich(p, Z)
        lat = (time.perf_counter() - t0) * 1e6
        return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], "flow_id": int(i),
                "proto": row.proto.iat[0], "service": row.service.iat[0], "state": row.state.iat[0],
                "p_attack": p, "tau": engine.tau, "latency_us": lat, "truth": engine.cat_te.iat[i], **res}

    async def gen():
        for i in order:
            if await request.is_disconnected():
                break
            ev = await asyncio.to_thread(score, int(i))
            yield f"data: {json.dumps(ev)}\n\n"
            await asyncio.sleep(1 / rate)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def main():
    uvicorn.run("src.app:app", host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()

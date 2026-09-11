"""Phase 7 acceptance check: every dashboard endpoint returns HTTP 200 and a valid payload.

Run against a live server:  python -m src.app   (then, in another shell)   python -m src.validate_dashboard
"""
import json
import sys
import urllib.error
import urllib.request
import uuid

from src.config import ARTIFACT_DIR

BASE = "http://127.0.0.1:8000"


def _open(req, timeout=120):
    r = urllib.request.urlopen(req, timeout=timeout)
    assert r.status == 200, (getattr(req, "full_url", req), r.status)
    return r


def get(path, raw=False):
    with _open(BASE + path) as r:
        body = r.read()
    return body if raw else json.loads(body)


def post_json(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with _open(req) as r:
        return json.loads(r.read())


def post_file(path, name, data: bytes):
    b = uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f"Content-Type: text/csv\r\n\r\n").encode() + data + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(BASE + path, data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with _open(req) as r:
        return json.loads(r.read())


def stream_events(n):
    events = []
    with _open(BASE + "/api/stream/simulated?rate=20", timeout=60) as r:
        assert r.headers.get_content_type() == "text/event-stream"
        for line in r:
            line = line.decode().strip()
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
                if len(events) >= n:
                    break
    return events


def main() -> int:
    log = {}
    html = get("/", raw=True)
    assert b"SecureNet SOC" in html
    for asset in ("styles.css", "app.js"):
        assert len(get(f"/static/{asset}", raw=True)) > 1000
    log["GET / + static assets"] = "200 OK"

    t = get("/api/telemetry")
    k = t["kpis"]
    assert k["total_flows"] == 51_535 and len(t["models"]) == 3 and len(t["families"]) == 9
    assert len(t["features"]) == 15 and sum(t["confusion"].values()) == 51_535
    log["GET /api/telemetry"] = {"recall": round(k["recall"], 4), "fpr": round(k["fpr"], 4),
                                 "accuracy": round(k["accuracy"], 4), "latency_us": round(k["latency_us"], 2)}

    p = get("/api/presets")
    assert len(p["presets"]) == 4 and all(p["categories"][c] for c in ("proto", "service", "state"))
    preset_results = []
    for pr in p["presets"]:
        r = post_json("/api/predict/single", pr["flow"])
        assert 0 <= r["p_attack"] <= 1 and r["defaulted"] == 0 and r["verdict"] in ("ATTACK", "NORMAL")
        preset_results.append({"preset": pr["label"], "truth": pr["truth"], "verdict": r["verdict"],
                               "p_attack": round(r["p_attack"], 4), "family": r["family"],
                               "latency_ms": round(r["latency_us"] / 1000, 2)})
    log["POST /api/predict/single (4 presets)"] = preset_results

    partial = post_json("/api/predict/single", {"proto": "tcp", "service": "http", "state": "FIN", "sbytes": 1500})
    assert partial["defaulted"] == 42 - 4
    log["POST /api/predict/single (partial form)"] = {"defaulted_features": partial["defaulted"],
                                                      "verdict": partial["verdict"]}

    sample = get("/api/sample.csv", raw=True)
    b = post_file("/api/predict/batch", "sample.csv", sample)
    assert b["rows"] == 2000 and b["metrics"] is not None and b["attacks"] + b["normal"] == 2000
    enriched = get(f"/api/predict/batch/{b['token']}", raw=True).decode()
    header = enriched.splitlines()[0].split(",")
    assert {"p_attack", "prediction", "predicted_family", "action"} <= set(header)
    log["POST /api/predict/batch (2,000-row sample)"] = {
        "attacks": b["attacks"], "normal": b["normal"], "flows_per_s": round(b["flows_per_s"]),
        "accuracy": round(b["metrics"]["accuracy"], 4), "recall": round(b["metrics"]["recall"], 4),
        "fpr": round(b["metrics"]["fpr"], 4)}
    log["GET /api/predict/batch/{token}"] = f"{len(enriched.splitlines()) - 1} enriched rows"

    try:
        post_file("/api/predict/batch", "bad.csv", b"foo,bar\n1,2\n")
        raise AssertionError("malformed CSV was accepted")
    except urllib.error.HTTPError as e:
        assert e.code == 400
    log["POST /api/predict/batch (schema-less CSV)"] = "400 rejected as expected"

    ev = stream_events(5)
    assert len(ev) == 5 and all({"verdict", "p_attack", "latency_us", "truth"} <= set(e) for e in ev)
    log["GET /api/stream/simulated (SSE)"] = [f"#{e['flow_id']} {e['verdict']} p={e['p_attack']:.3f} "
                                              f"truth={e['truth']}" for e in ev]

    (ARTIFACT_DIR / "dashboard_validation.json").write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    print("Dashboard validation PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

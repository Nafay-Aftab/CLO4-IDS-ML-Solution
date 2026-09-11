/* SecureNet SOC dashboard client — vanilla JS + Chart.js (no build step). */
"use strict";

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const pct = (v, d = 2) => (v * 100).toFixed(d) + "%";
const int = (v) => Number(v).toLocaleString("en-US");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const C = {
  safe: "#10B981", threat: "#EF4444", cyan: "#48CAE4", amber: "#F59E0B", violet: "#a78bfa",
  muted: "#94A3B8", faint: "#64748B", grid: "rgba(255,255,255,0.06)", text: "#CBD5E1",
};
// Batch doughnut: Normal + top-4 families + Other (<= 6 segments).
const SEGMENT = [C.safe, "#d95926", "#c98500", "#d55181", "#9085e9", C.faint];

const VIEWS = {
  telemetry: ["Executive Telemetry", "Champion model KPIs measured on the untouched 20 % test fold"],
  stream: ["Live Real-Time Threat Feed", "Streaming flows scored one-by-one by the production pipeline"],
  inspector: ["Single Flow Inspector", "Craft or inject a flow and inspect the model's verdict"],
  batch: ["Batch Network CSV Predictor", "Vectorised offline scoring of exported flow logs"],
};

const state = { t: null, charts: {}, es: null, preset: null, stream: { total: 0, alerts: 0, allowed: 0, missed: 0, latSum: 0 } };
const hasChart = () => typeof Chart !== "undefined";

function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove("show"), 3200);
}

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) {
    let msg = r.statusText;
    try { msg = (await r.json()).detail || msg; } catch (_) { /* non-JSON */ }
    throw new Error(msg);
  }
  return r.json();
}

function countUp(el, to, fmt, ms = 900) {
  if (state.demo) { el.textContent = fmt(to); return; }  // kiosk capture: render final values instantly
  const t0 = performance.now();
  const step = (now) => {
    const k = Math.min(1, (now - t0) / ms);
    el.textContent = fmt(to * (1 - Math.pow(1 - k, 3)));
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* ---------------- navigation ---------------- */
function showView(v) {
  if (!VIEWS[v]) v = "telemetry";
  $$(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.view === v));
  $$(".view").forEach((s) => s.classList.toggle("active", s.id === "view-" + v));
  $("#view-title").textContent = VIEWS[v][0];
  $("#view-sub").textContent = VIEWS[v][1];
  history.replaceState(null, "", "#" + v);
  Object.values(state.charts).forEach((c) => c && c.resize());
}
$$(".nav-item").forEach((b) => b.addEventListener("click", () => showView(b.dataset.view)));

/* ---------------- Chart.js defaults & helpers ---------------- */
function chartDefaults() {
  Chart.defaults.color = C.muted;
  Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
  Chart.defaults.font.size = 12;
  Chart.defaults.borderColor = C.grid;
  Chart.defaults.plugins.legend.labels.boxWidth = 10;
  Chart.defaults.plugins.legend.labels.boxHeight = 10;
  Chart.defaults.plugins.tooltip.backgroundColor = "#0f172a";
  Chart.defaults.plugins.tooltip.borderColor = "rgba(255,255,255,0.14)";
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.maintainAspectRatio = false;
}

// Solid hairline reference line (target / threshold) drawn at a value on one axis.
const refLine = {
  id: "refLine",
  afterDatasetsDraw(chart, _args, opts) {
    if (opts == null || opts.value == null) return;
    const scale = chart.scales[opts.axis || "y"];
    const { ctx, chartArea: a } = chart;
    const p = scale.getPixelForValue(opts.value);
    ctx.save();
    ctx.strokeStyle = opts.color || C.amber;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    if ((opts.axis || "y") === "y") { ctx.moveTo(a.left, p); ctx.lineTo(a.right, p); }
    else { ctx.moveTo(p, a.top); ctx.lineTo(p, a.bottom); }
    ctx.stroke();
    ctx.fillStyle = opts.color || C.amber;
    ctx.font = "11px " + Chart.defaults.font.family;
    if ((opts.axis || "y") === "y") ctx.fillText(opts.label || "", a.left + 6, p - 5);
    else ctx.fillText(opts.label || "", p + 5, a.top + 10);
    ctx.restore();
  },
};

function fallback(canvasId, msg = "Chart.js could not be loaded (offline?) — see the table view.") {
  const box = document.getElementById(canvasId).parentElement;
  box.innerHTML = `<div class="chart-fallback">${esc(msg)}</div>`;
}

/* ---------------- 1. telemetry ---------------- */
async function initTelemetry() {
  const t = await api("/api/telemetry");
  state.t = t;
  $("#model-name").textContent = t.model_name;
  $("#tau").textContent = t.kpis.tau.toFixed(2);
  if (t.student) {
    $("#st-name").textContent = t.student.name;
    $("#st-meta").textContent = `${t.student.enrolment} · ${t.student.class} · ${t.student.course} (CLO 4) · ${t.student.instructor}`;
  }
  const k = t.kpis;
  countUp($("#kpi-flows"), k.total_flows, (v) => int(Math.round(v)));
  $("#kpi-flows-foot").textContent = `${int(k.test_attacks)} attacks · ${int(k.test_normal)} benign`;
  countUp($("#kpi-recall"), k.recall * 100, (v) => v.toFixed(2) + "%");
  $("#kpi-recall-foot").innerHTML = k.recall >= 0.95
    ? `<span class="badge badge-safe">✔ meets ≥ 95 % target</span>`
    : `<span class="badge badge-warn">▲ below 95 % target</span>`;
  countUp($("#kpi-fpr"), k.fpr * 100, (v) => v.toFixed(2) + "%");
  $("#kpi-fpr-foot").innerHTML = k.fpr < 0.05
    ? `<span class="badge badge-safe">✔ within &lt; 5 % budget</span>`
    : `<span class="badge badge-warn">▲ above 5 % budget</span>`;
  if (k.latency_us != null) {
    countUp($("#kpi-lat"), k.latency_us, (v) => v.toFixed(1) + " µs");
    $("#kpi-lat-foot").innerHTML = `<span class="badge badge-info">${int(Math.round(k.flows_per_s))} flows/s</span><span class="muted">10k-flow batch</span>`;
  } else {
    $("#kpi-lat").textContent = "n/a";
  }

  renderCM(t.confusion);
  renderMetricTable(t.models);
  if (!hasChart()) { ["chart-models", "chart-features", "chart-families"].forEach((id) => fallback(id)); return; }
  renderModels(t.models);
  renderFeatures(t.features);
  renderFamilies(t.families);
}

function renderModels(models) {
  const metrics = [["accuracy", "Accuracy"], ["precision", "Precision"], ["recall", "Attack recall"], ["f1", "F1-score"], ["specificity", "Specificity"]];
  // Champion emphasised in cyan; baseline recessive gray.
  const colorOf = (m) => (m.champion ? C.cyan : C.muted);
  const datasets = models.map((m) => ({
    label: m.name + (m.champion ? "  (champion)" : ""),
    data: metrics.map(([key]) => m[key] * 100),
    showLine: false,
    pointRadius: m.champion ? 7 : 5,
    pointHoverRadius: 9,
    pointBorderColor: "#1E293B",
    pointBorderWidth: 2,
    pointBackgroundColor: colorOf(m),
    borderColor: colorOf(m),
    backgroundColor: colorOf(m),
  }));
  const lo = Math.floor(Math.min(...models.flatMap((m) => metrics.map(([k]) => m[k] * 100))) - 1);
  state.charts.models = new Chart($("#chart-models"), {
    type: "line",
    data: { labels: metrics.map(([, l]) => l), datasets },
    options: {
      interaction: { mode: "index", intersect: false },
      scales: {
        y: { min: Math.min(lo, 90), max: 100, ticks: { callback: (v) => v + "%" }, title: { display: true, text: "Score (dot plot, axis not zero-based)" } },
        x: { grid: { display: false } },
      },
      plugins: {
        legend: { position: "bottom" },
        tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${c.parsed.y.toFixed(2)}%` } },
        refLine: { value: 95, axis: "y", label: "95 % target" },
      },
    },
    plugins: [refLine],
  });
}

function renderFeatures(features) {
  state.charts.features = new Chart($("#chart-features"), {
    type: "bar",
    data: {
      labels: features.map((f) => f.name),
      datasets: [{ data: features.map((f) => f.importance), backgroundColor: C.cyan, borderRadius: 4, maxBarThickness: 16 }],
    },
    options: {
      indexAxis: "y",
      scales: { x: { title: { display: true, text: "Mean decrease in Gini impurity" } }, y: { grid: { display: false }, ticks: { color: C.text } } },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => `importance ${c.parsed.x.toFixed(4)}` } } },
    },
  });
}

function renderFamilies(fams) {
  const sorted = [...fams].sort((a, b) => b.recall - a.recall);
  state.charts.families = new Chart($("#chart-families"), {
    type: "bar",
    data: {
      labels: sorted.map((f) => f.family),
      datasets: [{ data: sorted.map((f) => f.recall * 100), backgroundColor: sorted.map((f) => (f.recall >= 0.95 ? C.cyan : C.amber)), borderRadius: 4, maxBarThickness: 16 }],
    },
    options: {
      indexAxis: "y",
      scales: { x: { min: 0, max: 100, ticks: { callback: (v) => v + "%" } }, y: { grid: { display: false }, ticks: { color: C.text } } },
      plugins: {
        legend: { display: false },
        refLine: { value: 95, axis: "x", label: "95 %" },
        tooltip: { callbacks: { label: (c) => { const f = sorted[c.dataIndex]; return `${f.recall >= 0.95 ? "✔" : "▲ below target —"} recall ${pct(f.recall)} (${int(f.detected)} / ${int(f.support)})`; } } },
      },
    },
    plugins: [refLine],
  });
}

function renderCM(cm) {
  const nN = cm.tn + cm.fp, nA = cm.fn + cm.tp;
  const cell = (n, of, label, tone, tip) => {
    const share = n / of;
    const bg = tone === "good" ? `rgba(16,185,129,${0.1 + share * 0.35})` : `rgba(239,68,68,${0.1 + share * 3})`;
    return `<div class="cm-cell" style="background:${bg}"><div class="t">${label}</div><div class="n">${int(n)}</div><div class="p">${pct(share)} of actual</div><div class="tip">${tip}</div></div>`;
  };
  $("#cm").innerHTML = `
    <div></div><div class="cm-axis">Predicted Normal</div><div class="cm-axis">Predicted Attack</div>
    <div class="cm-axis">Actual Normal</div>
    ${cell(cm.tn, nN, "True negative", "good", "Benign flows correctly allowed. No analyst effort, no business disruption.")}
    ${cell(cm.fp, nN, "False positive", "bad", `False alarms: ${int(cm.fp)} benign flows raised an alert — SOC triage time (alert fatigue), never a breach.`)}
    <div class="cm-axis">Actual Attack</div>
    ${cell(cm.fn, nA, "False negative", "bad", `Missed attacks: ${int(cm.fn)} malicious flows passed silently — the costly error (persistence, lateral movement, exfiltration).`)}
    ${cell(cm.tp, nA, "True positive", "good", "Attacks correctly detected and blocked in real time.")}`;
}

function renderMetricTable(models) {
  const cols = [["accuracy", "Accuracy"], ["precision", "Precision"], ["recall", "Attack recall"], ["f1", "F1"], ["fpr", "FPR"], ["roc_auc", "ROC-AUC"]];
  $("#metric-table").innerHTML = `<thead><tr><th>Model</th><th class="num">τ</th>${cols.map(([, l]) => `<th class="num">${l}</th>`).join("")}</tr></thead>
    <tbody>${models.map((m) => `<tr class="${m.champion ? "champ" : ""}"><td>${esc(m.name)}${m.champion ? ' <span class="badge badge-info">champion</span>' : ""}</td><td class="num">${m.threshold.toFixed(2)}</td>${cols.map(([k]) => `<td class="num">${k === "roc_auc" ? m[k].toFixed(4) : pct(m[k])}</td>`).join("")}</tr>`).join("")}</tbody>`;
}

/* ---------------- 2. live stream ---------------- */
function initStreamChart() {
  if (!hasChart()) { fallback("chart-stream"); return; }
  state.charts.stream = new Chart($("#chart-stream"), {
    type: "line",
    data: { labels: [], datasets: [{ label: "P(attack)", data: [], borderColor: C.cyan, borderWidth: 2, tension: 0, pointRadius: 3.5, pointBackgroundColor: [], pointBorderColor: "#1E293B", fill: { target: "origin", above: "rgba(72,202,228,0.08)" } }] },
    options: {
      animation: { duration: 250 },
      scales: { y: { min: 0, max: 1, ticks: { stepSize: 0.25, callback: (v) => Math.round(v * 100) + "%" } }, x: { ticks: { maxTicksLimit: 8 }, grid: { display: false } } },
      plugins: { legend: { display: false }, refLine: { value: 0.5, axis: "y", label: "τ*" }, tooltip: { callbacks: { label: (c) => `P(attack) ${pct(c.parsed.y)}` } } },
    },
    plugins: [refLine],
  });
}

function setStreamUI(on) {
  $("#stream-toggle").textContent = on ? "❚❚ Pause feed" : "▶ Start live feed";
  $("#stream-toggle").classList.toggle("btn-danger", on);
  $("#stream-toggle").classList.toggle("btn-primary", !on);
  $("#nav-live-dot").classList.toggle("on", on);
}

function startStream() {
  if (state.es) return;
  const speed = $("#stream-speed").value;
  state.es = new EventSource(`/api/stream/simulated?rate=${speed}`);
  state.es.onmessage = (e) => onFlow(JSON.parse(e.data));
  state.es.onerror = () => { stopStream(); toast("Live feed disconnected."); };
  setStreamUI(true);
  if ($("#siem-body td[colspan]")) $("#siem-body").innerHTML = "";
}
function stopStream() {
  if (state.es) state.es.close();
  state.es = null;
  setStreamUI(false);
}

function onFlow(ev) {
  const s = state.stream;
  s.total++; s.latSum += ev.latency_us;
  if (ev.verdict === "ATTACK") s.alerts++; else s.allowed++;
  if (ev.verdict === "NORMAL" && ev.truth !== "Normal") s.missed++;
  $("#c-total").textContent = int(s.total);
  $("#c-alerts").textContent = int(s.alerts);
  $("#c-allowed").textContent = int(s.allowed);
  $("#c-missed").textContent = int(s.missed);
  $("#c-lat").textContent = (s.latSum / s.total / 1000).toFixed(2) + " ms";

  const ch = state.charts.stream;
  if (ch) {
    ch.options.plugins.refLine.value = ev.tau;
    ch.data.labels.push("#" + ev.flow_id);
    ch.data.datasets[0].data.push(ev.p_attack);
    ch.data.datasets[0].pointBackgroundColor.push(ev.verdict === "ATTACK" ? C.threat : C.safe);
    if (ch.data.labels.length > 60) { ch.data.labels.shift(); ch.data.datasets[0].data.shift(); ch.data.datasets[0].pointBackgroundColor.shift(); }
    ch.update();
  }

  const isAttack = ev.verdict === "ATTACK";
  const missed = !isAttack && ev.truth !== "Normal";
  const fpos = isAttack && ev.truth === "Normal";
  const sevBadge = isAttack
    ? `<span class="badge ${ev.severity === "MEDIUM" ? "badge-warn" : "badge-threat"}">● ${ev.severity}</span>`
    : `<span class="badge badge-safe">✔ ALLOW</span>`;
  const truth = missed ? `<span class="badge badge-warn">▲ ${esc(ev.truth)} · missed</span>`
    : fpos ? `<span class="badge badge-muted">Normal · false alarm</span>`
    : `<span class="muted">${esc(ev.truth)}</span>`;
  const tr = document.createElement("tr");
  tr.className = missed ? "missed" : isAttack ? "alert" : "allow";
  tr.innerHTML = `<td class="mono small">${esc(ev.ts)}</td><td class="mono">#${ev.flow_id}</td><td class="mono small">${esc(ev.proto)} / ${esc(ev.service)} / ${esc(ev.state)}</td>
    <td>${sevBadge}</td><td>${isAttack ? esc(ev.family) : '<span class="muted">—</span>'}</td><td class="num">${pct(ev.confidence)}</td>
    <td>${truth}</td><td class="small wrap">${esc(ev.action)}</td><td class="num mono small">${(ev.latency_us / 1000).toFixed(2)} ms</td>`;
  const body = $("#siem-body");
  body.prepend(tr);
  while (body.children.length > 150) body.lastElementChild.remove();
  if (state.demoStop && s.total >= state.demoStop) { state.demoStop = 0; stopStream(); }
}

$("#stream-toggle").addEventListener("click", () => (state.es ? stopStream() : startStream()));
$("#stream-speed").addEventListener("change", () => { if (state.es) { stopStream(); startStream(); } });
$("#stream-clear").addEventListener("click", () => {
  Object.assign(state.stream, { total: 0, alerts: 0, allowed: 0, missed: 0, latSum: 0 });
  ["#c-total", "#c-alerts", "#c-allowed", "#c-missed"].forEach((id) => ($(id).textContent = "0"));
  $("#c-lat").textContent = "–";
  $("#siem-body").innerHTML = "";
  const ch = state.charts.stream;
  if (ch) { ch.data.labels = []; ch.data.datasets[0].data = []; ch.data.datasets[0].pointBackgroundColor = []; ch.update(); }
});

/* ---------------- 3. inspector ---------------- */
const FORM_NUM = ["dur", "sbytes", "dbytes", "sttl", "sload", "dload"];

async function initInspector() {
  const meta = await api("/api/presets");
  const opt = (arr) => arr.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
  $("#f-proto").innerHTML = opt(meta.categories.proto);
  $("#f-service").innerHTML = opt(meta.categories.service);
  $("#f-state").innerHTML = opt(meta.categories.state);
  state.defaults = meta.defaults;
  fillForm(meta.defaults);
  $("#presets").innerHTML = meta.presets.map((p, i) => `<button class="preset" data-i="${i}"><b>${esc(p.label)}</b><span>${esc(p.description)}</span></button>`).join("");
  $$(".preset").forEach((b) => b.addEventListener("click", () => {
    const p = meta.presets[+b.dataset.i];
    state.preset = p;
    $$(".preset").forEach((x) => x.classList.toggle("active", x === b));
    fillForm(p.flow);
    $("#insp-note").textContent = `Loaded flow #${p.flow_id} (ground truth: ${p.truth}). All 42 features are sent.`;
    runInspector();
  }));
}

function fillForm(flow) {
  ["proto", "service", "state"].forEach((k) => ($("#f-" + k).value = flow[k]));
  FORM_NUM.forEach((k) => ($("#f-" + k).value = +(+flow[k]).toPrecision(8)));
}

function readForm() {
  const out = {};
  ["proto", "service", "state"].forEach((k) => (out[k] = $("#f-" + k).value));
  FORM_NUM.forEach((k) => { const v = $("#f-" + k).value; if (v !== "") out[k] = Number(v); });
  return out;
}

async function runInspector() {
  const btn = $("#insp-run");
  btn.disabled = true;
  try {
    const payload = { ...(state.preset ? state.preset.flow : {}), ...readForm() };
    const r = await api("/api/predict/single", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    showResult(r);
  } catch (e) {
    toast("Prediction failed: " + e.message);
  } finally {
    btn.disabled = false;
  }
}

function showResult(r) {
  const arc = $("#gauge-arc");
  const len = arc.getTotalLength();
  const color = r.verdict === "ATTACK" ? C.threat : C.safe;
  arc.style.transition = "stroke-dasharray .8s cubic-bezier(.2,.8,.2,1), stroke .3s";
  arc.setAttribute("stroke", color);
  arc.setAttribute("stroke-dasharray", `${len * r.p_attack} ${len}`);
  const ang = Math.PI * (1 - r.tau);
  const [cx, cy, r1, r2] = [110, 110, 78, 102];
  const tau = $("#gauge-tau");
  tau.setAttribute("x1", cx + r1 * Math.cos(ang)); tau.setAttribute("y1", cy - r1 * Math.sin(ang));
  tau.setAttribute("x2", cx + r2 * Math.cos(ang)); tau.setAttribute("y2", cy - r2 * Math.sin(ang));
  countUp($("#gauge-num"), r.p_attack * 100, (v) => v.toFixed(1) + "%", 700);

  const v = $("#verdict");
  v.className = "verdict " + (r.verdict === "ATTACK" ? "attack" : "normal");
  v.textContent = r.verdict === "ATTACK" ? `⚠ MALICIOUS — ${r.severity} · ${r.family}` : "✔ BENIGN — FLOW ALLOWED";
  $("#pb-normal").style.width = pct(1 - r.p_attack, 1);
  $("#pb-attack").style.width = pct(r.p_attack, 1);
  $("#pv-normal").textContent = pct(1 - r.p_attack, 1);
  $("#pv-attack").textContent = pct(r.p_attack, 1);

  const fb = $("#fam-box");
  if (r.family_proba) {
    fb.classList.remove("hidden");
    $("#fam-rows").innerHTML = r.family_proba.slice(0, 4).map((f) => `<div class="prob-row"><span>${esc(f.family)}</span><div class="prob-track"><div class="prob-fill" style="background:${C.violet}; width:${pct(f.p, 1)}"></div></div><span class="mono">${pct(f.p, 1)}</span></div>`).join("");
  } else fb.classList.add("hidden");

  $("#insp-lat").textContent = `inference ${(r.latency_us / 1000).toFixed(2)} ms`;
  const kv = [["Confidence in verdict", pct(r.confidence)], ["Decision threshold τ*", r.tau.toFixed(2)], ["Recommended action", r.action], ["Features defaulted to train median", r.defaulted]];
  if (state.preset) kv.push(["Ground truth (dataset label)", state.preset.truth]);
  $("#insp-kv").innerHTML = kv.map(([k, val]) => `<dt>${esc(k)}</dt><dd>${esc(val)}</dd>`).join("");
}

$("#insp-run").addEventListener("click", runInspector);
$("#insp-form").addEventListener("input", () => { $$(".preset").forEach((x) => x.classList.remove("active")); });
$("#insp-reset").addEventListener("click", () => {
  state.preset = null;
  $$(".preset").forEach((x) => x.classList.remove("active"));
  fillForm(state.defaults);
  $("#insp-note").textContent = "Unspecified features are filled with training-fold medians.";
});

/* ---------------- 4. batch ---------------- */
function uploadCSV(file) {
  const fd = new FormData();
  fd.append("file", file);
  const xhr = new XMLHttpRequest();
  const bar = $("#batch-progress");
  $("#batch-status").textContent = `Uploading ${file.name} (${(file.size / 1024).toFixed(0)} KB)…`;
  bar.style.width = "0%";
  xhr.upload.onprogress = (e) => { if (e.lengthComputable) bar.style.width = (e.loaded / e.total) * 70 + "%"; };
  xhr.upload.onload = () => { $("#batch-status").textContent = "Scoring flows…"; bar.style.width = "85%"; };
  xhr.onload = () => {
    bar.style.width = "100%";
    if (xhr.status !== 200) {
      let msg = xhr.statusText;
      try { msg = JSON.parse(xhr.responseText).detail; } catch (_) { /* keep statusText */ }
      $("#batch-status").textContent = "Error: " + msg;
      toast("Batch scoring failed: " + msg);
      return;
    }
    showBatch(JSON.parse(xhr.responseText), file.name);
  };
  xhr.onerror = () => toast("Upload failed.");
  xhr.open("POST", "/api/predict/batch");
  xhr.send(fd);
}

function showBatch(r, name) {
  $("#batch-status").textContent = `${name}: ${int(r.rows)} flows scored in ${r.seconds.toFixed(2)} s.`;
  $("#batch-results").classList.remove("hidden");
  countUp($("#b-rows"), r.rows, (v) => int(Math.round(v)));
  $("#b-speed").textContent = `${int(Math.round(r.flows_per_s))} flows/s end-to-end`;
  countUp($("#b-attacks"), r.attacks, (v) => int(Math.round(v)));
  $("#b-attack-rate").textContent = pct(r.attacks / r.rows, 1) + " of flows";
  countUp($("#b-normal"), r.normal, (v) => int(Math.round(v)));
  if (r.metrics) {
    $("#b-acc").textContent = pct(r.metrics.accuracy);
    $("#b-acc-foot").textContent = `recall ${pct(r.metrics.recall)} · FPR ${pct(r.metrics.fpr)}`;
  } else {
    $("#b-acc").textContent = "n/a";
    $("#b-acc-foot").textContent = "no label column supplied";
  }
  $("#b-download").href = `/api/predict/batch/${r.token}`;
  $("#b-download").setAttribute("download", r.download_name);
  const cols = r.preview_columns;
  $("#b-preview").innerHTML = `<thead><tr>${cols.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${r.preview.map((row) => `<tr>${cols.map((c) => {
    const v = row[c];
    if (c === "prediction") return `<td>${v === "ATTACK" ? '<span class="badge badge-threat">ATTACK</span>' : '<span class="badge badge-safe">NORMAL</span>'}</td>`;
    if (c === "p_attack") return `<td class="num">${pct(v)}</td>`;
    return `<td>${esc(v)}</td>`;
  }).join("")}</tr>`).join("")}</tbody>`;
  $("#b-note").textContent = r.missing_filled.length ? `Missing columns filled with training medians/modes: ${r.missing_filled.join(", ")}` : "All 42 model features present.";

  const segs = r.breakdown;
  if (!hasChart()) { fallback("chart-batch"); return; }
  if (state.charts.batch) state.charts.batch.destroy();
  state.charts.batch = new Chart($("#chart-batch"), {
    type: "doughnut",
    data: { labels: segs.map((s) => s.label), datasets: [{ data: segs.map((s) => s.count), backgroundColor: segs.map((_, i) => SEGMENT[i]), borderColor: "#1E293B", borderWidth: 2 }] },
    options: {
      cutout: "62%",
      plugins: {
        legend: { position: "bottom", labels: { color: C.text, padding: 12 } },
        tooltip: { callbacks: { label: (c) => `${c.label}: ${int(c.parsed)} (${pct(c.parsed / r.rows, 1)})` } },
      },
    },
  });
}

const dz = $("#dropzone");
dz.addEventListener("click", () => $("#file-input").click());
dz.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") $("#file-input").click(); });
["dragenter", "dragover"].forEach((t) => dz.addEventListener(t, (e) => { e.preventDefault(); dz.classList.add("drag"); }));
["dragleave", "drop"].forEach((t) => dz.addEventListener(t, (e) => { e.preventDefault(); dz.classList.remove("drag"); }));
dz.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) uploadCSV(f); });
$("#file-input").addEventListener("change", (e) => { const f = e.target.files[0]; if (f) uploadCSV(f); e.target.value = ""; });
$("#sample-btn").addEventListener("click", async () => {
  const blob = await (await fetch("/api/sample.csv")).blob();
  uploadCSV(new File([blob], "unsw_nb15_sample_2000.csv", { type: "text/csv" }));
});

/* ---------------- boot ---------------- */
// Kiosk / demo mode (?view=<view>&demo=1[&preset=N]) drives a view automatically;
// used to capture the report screenshots with headless Edge.
function runDemo(view, q) {
  if (view === "stream") {
    if (q.get("rate")) $("#stream-speed").value = q.get("rate");
    state.demoStop = +(q.get("events") || 0);  // auto-pause after N events so headless capture can settle
    startStream();
  }
  if (view === "inspector") { const b = $$(".preset")[+(q.get("preset") || 1)]; if (b) b.click(); }
  if (view === "batch") $("#sample-btn").click();
}

(async function boot() {
  if (hasChart()) chartDefaults();
  initStreamChart();
  const q = new URLSearchParams(location.search);
  const view = q.get("view") || location.hash.slice(1) || "telemetry";
  if (q.has("demo") || q.has("static")) {
    state.demo = true;
    document.body.classList.add("no-anim");
    if (hasChart()) Chart.defaults.animation = false;
  }
  showView(view);
  try {
    await Promise.all([initTelemetry(), initInspector()]);
  } catch (e) {
    toast("Backend error: " + e.message);
    console.error(e);
  }
  if (q.has("demo")) runDemo(view, q);
})();

/* ====== GSBGEN390 dashboard — data loader + Chart.js renderers ======
   Loads metrics from ./data/ if present, otherwise renders mock data so the
   skeleton is immediately viewable. To refresh after a pipeline run:
     cp metrics_per_respondent.json metrics_aggregate.json docs/data/
     git add docs/data && git commit -m "update metrics" && git push
*/

// ---------- MOCK DATA (replace with real metrics once pipeline runs) ----------
const MOCK_PER_RESPONDENT = [
  // Study 1 R1
  { arm: "study1", respondent: "R1", condition: "A_demographic_only",   likert_mae: 1.42, likert_within1_pct: 55, categorical_acc_pct: 50, bfi_trait_rmse: 1.28, self_likert_mae: 0.65, self_cat_match_pct: 70 },
  { arm: "study1", respondent: "R1", condition: "B_persona_description",likert_mae: 1.05, likert_within1_pct: 70, categorical_acc_pct: 60, bfi_trait_rmse: 0.98, self_likert_mae: 0.50, self_cat_match_pct: 80 },
  { arm: "study1", respondent: "R1", condition: "C_interview",          likert_mae: 0.78, likert_within1_pct: 82, categorical_acc_pct: 75, bfi_trait_rmse: 0.72, self_likert_mae: 0.42, self_cat_match_pct: 85 },
  // Study 1 R2
  { arm: "study1", respondent: "R2", condition: "A_demographic_only",   likert_mae: 1.55, likert_within1_pct: 50, categorical_acc_pct: 50, bfi_trait_rmse: 1.42, self_likert_mae: 0.70, self_cat_match_pct: 65 },
  { arm: "study1", respondent: "R2", condition: "B_persona_description",likert_mae: 1.18, likert_within1_pct: 65, categorical_acc_pct: 60, bfi_trait_rmse: 1.10, self_likert_mae: 0.55, self_cat_match_pct: 75 },
  { arm: "study1", respondent: "R2", condition: "C_interview",          likert_mae: 0.90, likert_within1_pct: 78, categorical_acc_pct: 75, bfi_trait_rmse: 0.85, self_likert_mae: 0.45, self_cat_match_pct: 85 },
  // Study 2 R1
  { arm: "study2", respondent: "R1", condition: "A_demographic_only",   likert_mae: 1.50, likert_within1_pct: 52, categorical_acc_pct: 50, bfi_trait_rmse: 1.35, self_likert_mae: 0.62, self_cat_match_pct: 70 },
  { arm: "study2", respondent: "R1", condition: "D_survey_conditioned", likert_mae: 0.82, likert_within1_pct: 80, categorical_acc_pct: 75, bfi_trait_rmse: 0.78, self_likert_mae: 0.40, self_cat_match_pct: 85 },
  { arm: "study2", respondent: "R1", condition: "D_loo_drop_demographic",  likert_mae: 0.86, likert_within1_pct: 78, categorical_acc_pct: 75, bfi_trait_rmse: 0.80, self_likert_mae: 0.42, self_cat_match_pct: 85 },
  { arm: "study2", respondent: "R1", condition: "D_loo_drop_behavioral",   likert_mae: 0.92, likert_within1_pct: 75, categorical_acc_pct: 75, bfi_trait_rmse: 0.84, self_likert_mae: 0.42, self_cat_match_pct: 85 },
  { arm: "study2", respondent: "R1", condition: "D_loo_drop_psychological",likert_mae: 1.10, likert_within1_pct: 68, categorical_acc_pct: 65, bfi_trait_rmse: 0.98, self_likert_mae: 0.45, self_cat_match_pct: 80 },
  { arm: "study2", respondent: "R1", condition: "D_loo_drop_attitudinal",  likert_mae: 1.18, likert_within1_pct: 62, categorical_acc_pct: 60, bfi_trait_rmse: 1.05, self_likert_mae: 0.48, self_cat_match_pct: 80 },
];

const MOCK_DRILLDOWN = {
  "Study 1 R1": [
    { item: "bfi_e_r (reserved)",     truth: "3", A: "4", B: "3", C: "3" },
    { item: "bfi_a (trusting)",       truth: "2", A: "4", B: "3", C: "2" },
    { item: "bfi_c (thorough job)",   truth: "4", A: "4", B: "4", C: "4" },
    { item: "happy",                   truth: "Pretty happy", A: "Pretty happy", B: "Pretty happy", C: "Pretty happy" },
    { item: "trust",                   truth: "You can't be too careful", A: "Most people can be trusted", B: "Most people can be trusted", C: "You can't be too careful" },
    { item: "polviews (1-7)",          truth: "7", A: "4", B: "5", C: "6" },
    { item: "satjob",                  truth: "Moderately satisfied", A: "Moderately satisfied", B: "Moderately satisfied", C: "Moderately satisfied" },
    { item: "loyal (brand stickiness)",truth: "4", A: "3", B: "4", C: "4" },
  ],
  "Study 1 R2": [
    { item: "bfi_e_r (reserved)",     truth: "5", A: "3", B: "4", C: "5" },
    { item: "bfi_a (trusting)",       truth: "4", A: "3", B: "4", C: "4" },
    { item: "bfi_c (thorough job)",   truth: "5", A: "4", B: "5", C: "5" },
    { item: "happy",                   truth: "Pretty happy", A: "Pretty happy", B: "Pretty happy", C: "Pretty happy" },
    { item: "trust",                   truth: "Most people can be trusted", A: "Most people can be trusted", B: "Most people can be trusted", C: "Most people can be trusted" },
    { item: "polviews (1-7)",          truth: "5", A: "4", B: "4", C: "5" },
    { item: "satjob",                  truth: "Moderately satisfied", A: "Very satisfied", B: "Moderately satisfied", C: "Moderately satisfied" },
    { item: "loyal (brand stickiness)",truth: "4", A: "3", B: "4", C: "4" },
  ],
  "Study 2 R1": [
    { item: "bfi_e_r (reserved)",     truth: "4", A: "3", D: "4" },
    { item: "bfi_a (trusting)",       truth: "4", A: "4", D: "4" },
    { item: "bfi_c (thorough job)",   truth: "4", A: "4", D: "4" },
    { item: "happy",                   truth: "Pretty happy", A: "Pretty happy", D: "Pretty happy" },
    { item: "trust",                   truth: "Depends", A: "Most people can be trusted", D: "Depends" },
    { item: "polviews (1-7)",          truth: "4", A: "4", D: "4" },
    { item: "satjob",                  truth: "Very satisfied", A: "Moderately satisfied", D: "Very satisfied" },
    { item: "loyal (brand stickiness)",truth: "4", A: "3", D: "4" },
  ],
};

// ---------- DATA LOADING ----------
async function loadMetrics() {
  try {
    const r1 = await fetch("./data/metrics_per_respondent.json");
    if (!r1.ok) throw new Error("not found");
    return await r1.json();
  } catch (e) {
    console.warn("Real metrics not found at ./data/metrics_per_respondent.json — using mock data.");
    return MOCK_PER_RESPONDENT;
  }
}

async function loadDrilldown() {
  // For now, drill-down uses mock. When real data lands, build from
  // persona_answers/{arm}/R*_*.json + eval_answers_extracted.csv.
  return MOCK_DRILLDOWN;
}

async function loadLeakageAudit() {
  try {
    const r = await fetch("./data/metrics_with_leakage_audit.json");
    if (!r.ok) throw new Error("not found");
    return await r.json();
  } catch (e) {
    console.warn("Leakage audit not found at ./data/metrics_with_leakage_audit.json — section will be skipped.");
    return null;
  }
}

// ---------- HELPERS ----------
const COND_LABEL = {
  A_demographic_only: "A · Demographics",
  B_persona_description: "B · Description",
  C_interview: "C · Interview",
  D_survey_conditioned: "D · Survey",
  D_loo_drop_demographic: "D − demographic",
  D_loo_drop_behavioral: "D − behavioral",
  D_loo_drop_psychological: "D − psychological",
  D_loo_drop_attitudinal: "D − attitudinal",
};

const CONDITION_ORDER = [
  "A_demographic_only",
  "B_persona_description",
  "C_interview",
  "D_survey_conditioned",
  "D_loo_drop_demographic",
  "D_loo_drop_behavioral",
  "D_loo_drop_psychological",
  "D_loo_drop_attitudinal",
];

const RESPONDENT_COLOR = {
  R1_study1: "#58a6ff",
  R2_study1: "#3fb950",
  R1_study2: "#f78166",
};

function respondentKey(row) { return `${row.respondent}_${row.arm}`; }
function respondentLabel(row) { return `${row.arm === "study1" ? "S1" : "S2"} · ${row.respondent}`; }

// ---------- CHART RENDERERS ----------
function renderMaeChart(metrics) {
  const ctx = document.getElementById("chart-mae");
  if (!ctx) return;

  const conditionsPresent = [...new Set(metrics.map(m => m.condition))]
    .sort((a, b) => CONDITION_ORDER.indexOf(a) - CONDITION_ORDER.indexOf(b));
  const respondents = [...new Set(metrics.map(m => respondentKey(m)))];

  const datasets = respondents.map(rkey => {
    const rowsForR = metrics.filter(m => respondentKey(m) === rkey);
    const exemplar = rowsForR[0];
    return {
      label: respondentLabel(exemplar),
      backgroundColor: RESPONDENT_COLOR[rkey] || "#888",
      data: conditionsPresent.map(c => {
        const row = rowsForR.find(m => m.condition === c);
        return row ? row.likert_mae : null;
      }),
    };
  });

  new Chart(ctx, {
    type: "bar",
    data: { labels: conditionsPresent.map(c => COND_LABEL[c] || c), datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: "Likert MAE per condition (lower = persona closer to truth)", color: "#e6edf3", font: { size: 14 } },
        legend: { labels: { color: "#e6edf3" } },
        tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(2)}` } },
      },
      scales: {
        x: { ticks: { color: "#8b949e", maxRotation: 30, minRotation: 30 } },
        y: { title: { display: true, text: "Likert MAE", color: "#8b949e" }, ticks: { color: "#8b949e" }, beginAtZero: true },
      },
    },
  });
}

function renderCategoricalChart(metrics) {
  const ctx = document.getElementById("chart-categorical");
  if (!ctx) return;

  const conditionsPresent = [...new Set(metrics.map(m => m.condition))]
    .sort((a, b) => CONDITION_ORDER.indexOf(a) - CONDITION_ORDER.indexOf(b));
  const respondents = [...new Set(metrics.map(m => respondentKey(m)))];

  const datasets = respondents.map(rkey => {
    const rowsForR = metrics.filter(m => respondentKey(m) === rkey);
    const exemplar = rowsForR[0];
    return {
      label: respondentLabel(exemplar),
      backgroundColor: RESPONDENT_COLOR[rkey] || "#888",
      data: conditionsPresent.map(c => {
        const row = rowsForR.find(m => m.condition === c);
        return row ? row.categorical_acc_pct : null;
      }),
    };
  });

  new Chart(ctx, {
    type: "bar",
    data: { labels: conditionsPresent.map(c => COND_LABEL[c] || c), datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: "Categorical accuracy % (higher = better)", color: "#e6edf3", font: { size: 14 } },
        legend: { labels: { color: "#e6edf3" } },
      },
      scales: {
        x: { ticks: { color: "#8b949e", maxRotation: 30, minRotation: 30 } },
        y: { title: { display: true, text: "Accuracy (%)", color: "#8b949e" }, ticks: { color: "#8b949e" }, beginAtZero: true, max: 100 },
      },
    },
  });
}

function renderSelfConsistencyChart(metrics) {
  const ctx = document.getElementById("chart-self-consistency");
  if (!ctx) return;

  const conditionsPresent = [...new Set(metrics.map(m => m.condition))]
    .sort((a, b) => CONDITION_ORDER.indexOf(a) - CONDITION_ORDER.indexOf(b));
  const respondents = [...new Set(metrics.map(m => respondentKey(m)))];

  const datasets = respondents.map(rkey => {
    const rowsForR = metrics.filter(m => respondentKey(m) === rkey);
    const exemplar = rowsForR[0];
    return {
      label: respondentLabel(exemplar),
      backgroundColor: RESPONDENT_COLOR[rkey] || "#888",
      data: conditionsPresent.map(c => {
        const row = rowsForR.find(m => m.condition === c);
        return row ? row.self_likert_mae : null;
      }),
    };
  });

  new Chart(ctx, {
    type: "bar",
    data: { labels: conditionsPresent.map(c => COND_LABEL[c] || c), datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: "Self-consistency (Likert MAE between sample 1 vs sample 2 — lower = more stable)", color: "#e6edf3", font: { size: 14 } },
        legend: { labels: { color: "#e6edf3" } },
      },
      scales: {
        x: { ticks: { color: "#8b949e", maxRotation: 30, minRotation: 30 } },
        y: { title: { display: true, text: "Self-MAE", color: "#8b949e" }, ticks: { color: "#8b949e" }, beginAtZero: true },
      },
    },
  });
}

function renderLooChart(metrics) {
  const ctx = document.getElementById("chart-loo");
  if (!ctx) return;

  // Only Study 2 LOO conditions
  const baselineRow = metrics.find(m => m.arm === "study2" && m.condition === "D_survey_conditioned");
  if (!baselineRow) {
    ctx.parentElement.innerHTML = '<p style="color:var(--text-dim);text-align:center;padding:120px 0;">Pending pipeline run — LOO chart will populate once Study 2 D and LOO conditions are run.</p>';
    return;
  }
  const looRows = metrics.filter(m => m.arm === "study2" && m.condition.startsWith("D_loo_drop_"));
  if (looRows.length === 0) {
    ctx.parentElement.innerHTML = '<p style="color:var(--text-dim);text-align:center;padding:120px 0;">Pending pipeline run — LOO chart will populate once Study 2 LOO conditions are run.</p>';
    return;
  }

  const labels = looRows.map(r => r.condition.replace("D_loo_drop_", ""));
  const deltas = looRows.map(r => r.likert_mae - baselineRow.likert_mae);

  // Sort by impact descending
  const indexed = labels.map((l, i) => ({ label: l, delta: deltas[i] }));
  indexed.sort((a, b) => b.delta - a.delta);

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: indexed.map(x => x.label),
      datasets: [{
        label: "Δ Likert MAE (vs full-survey baseline)",
        data: indexed.map(x => x.delta),
        backgroundColor: indexed.map(x => x.delta > 0.15 ? "#f78166" : x.delta > 0.05 ? "#fbcd60" : "#8b949e"),
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true, maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: "Feature-category importance (Δ MAE when category dropped — bigger = more important)", color: "#e6edf3", font: { size: 14 } },
        legend: { display: false },
      },
      scales: {
        x: { title: { display: true, text: "Δ Likert MAE", color: "#8b949e" }, ticks: { color: "#8b949e" }, beginAtZero: true },
        y: { ticks: { color: "#8b949e" } },
      },
    },
  });
}

// ---------- DRILL-DOWN ----------
function renderDrilldown(drilldownData) {
  const select = document.getElementById("drilldown-respondent");
  const tbody = document.querySelector("#drilldown-table tbody");
  const thead = document.querySelector("#drilldown-table thead tr");

  function paint() {
    const which = select.value;
    const rows = drilldownData[which] || [];
    if (rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-dim);padding:24px;">No drilldown data yet — populates after pipeline run.</td></tr>';
      return;
    }
    // Reshape header to match condition columns of this respondent
    const sample = rows[0];
    const cols = Object.keys(sample).filter(k => k !== "item" && k !== "truth");
    thead.innerHTML = "<th>Item</th><th>Truth</th>" + cols.map(c => `<th>${c}</th>`).join("");

    tbody.innerHTML = rows.map(row => {
      const truth = row.truth;
      const cells = cols.map(c => {
        const val = row[c] || "—";
        let cls = "";
        if (val === "—") cls = "match-bad";
        else if (val === truth) cls = "match-good";
        else {
          // For Likert items try numeric distance
          const tn = parseFloat(truth), vn = parseFloat(val);
          if (!isNaN(tn) && !isNaN(vn)) {
            const d = Math.abs(tn - vn);
            cls = d <= 1 ? "match-close" : "match-bad";
          } else cls = "match-bad";
        }
        return `<td class="${cls}">${val}</td>`;
      }).join("");
      return `<tr><td>${row.item}</td><td class="truth-cell">${truth}</td>${cells}</tr>`;
    }).join("");
  }

  select.addEventListener("change", paint);
  paint();
}

function renderLeakageChart(audit) {
  const ctx = document.getElementById("chart-leakage");
  if (!ctx) return;
  if (!audit || audit.length === 0) {
    ctx.parentElement.innerHTML = '<p style="color:var(--text-dim);text-align:center;padding:120px 0;">Leakage audit data not loaded.</p>';
    return;
  }
  // Build matrix: row = (arm/respondent/condition); cols = three filters
  const wantedConditions = ["A_demographic_only", "B_persona_description", "C_interview", "D_survey_conditioned"];
  const filters = ["full_eval", "strict_clean", "broad_clean"];
  const filterLabels = ["Full (15 items)", "Strict-clean (drop STRONG leaks)", "Broad-clean (drop STRONG + SOFT)"];
  const filterColors = ["#4a7ab5", "#7fb069", "#e07a5f"];

  // Filter to baseline conditions (skip LOO rows for clarity)
  const rows = audit.filter(a => wantedConditions.includes(a.condition));
  const labels = [...new Set(rows.map(a => `${a.arm === "study1" ? "S1" : "S2"}/${a.respondent}/${a.condition.split("_")[0]}`))];
  // Group by labelKey
  const groups = {};
  for (const a of rows) {
    const key = `${a.arm === "study1" ? "S1" : "S2"}/${a.respondent}/${a.condition.split("_")[0]}`;
    groups[key] = groups[key] || {};
    groups[key][a.filter] = a.likert_mae;
  }
  const orderedLabels = labels;  // preserve insertion order
  const datasets = filters.map((f, i) => ({
    label: filterLabels[i],
    data: orderedLabels.map(l => (groups[l] && groups[l][f] != null) ? groups[l][f] : null),
    backgroundColor: filterColors[i],
    borderColor: filterColors[i],
    borderWidth: 1,
  }));
  new Chart(ctx, {
    type: "bar",
    data: { labels: orderedLabels, datasets },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: "Likert MAE per condition × leakage filter (lower is better)" },
        legend: { position: "top" },
        tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: MAE ${ctx.parsed.y?.toFixed(2) ?? "—"}` } },
      },
      scales: {
        x: { ticks: { autoSkip: false, maxRotation: 45, minRotation: 30 } },
        y: { title: { display: true, text: "Likert MAE" }, beginAtZero: true },
      },
    },
  });
}

// ---------- BOOT ----------
(async function init() {
  const metrics = await loadMetrics();
  renderMaeChart(metrics);
  renderCategoricalChart(metrics);
  renderSelfConsistencyChart(metrics);
  renderLooChart(metrics);

  const audit = await loadLeakageAudit();
  renderLeakageChart(audit);

  const drilldown = await loadDrilldown();
  renderDrilldown(drilldown);

  // Update status banner if real data is loaded
  if (metrics !== MOCK_PER_RESPONDENT) {
    document.getElementById("status-banner").innerHTML =
      'Status: <strong style="color:var(--good);">Pipeline ran successfully — live metrics displayed below.</strong>';
    document.getElementById("results-intro").textContent =
      "Per-condition Likert MAE, lower = persona is closer to the real person.";
  }

  document.getElementById("last-updated").textContent = new Date().toISOString().slice(0, 10);
})();

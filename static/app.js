const state = {
  companies: [],
  leads: [],
  outreach: [],
  selectedLead: null,
};

const statuses = [
  "New",
  "Reviewed",
  "Approved for Outreach",
  "Do Not Contact",
  "Contacted",
  "Replied",
];

const actionInfo = {
  "discover-companies-db?replace=true": {
    title: "Discovering companies",
    estimate: "Usually 20-60 seconds. It searches the web using the saved ICP and replaces old company/lead data.",
  },
  "discover-websites": {
    title: "Discovering websites",
    estimate: "Usually 1-3 minutes depending on company count. It fills missing official websites.",
  },
  "score-companies": {
    title: "Scoring companies",
    estimate: "Usually under 10 seconds. It recalculates company confidence scores.",
  },
  "generate-leads-from-companies?limit=30": {
    title: "Generating leads",
    estimate: "Usually 1-4 minutes for the top 30 companies. It scrapes public pages and searches LinkedIn profiles.",
  },
  "verify-all": {
    title: "Verifying leads",
    estimate: "Usually 30 seconds to 3 minutes. It checks email and phone status using configured APIs or fallback checks.",
  },
  "campaign/send-approved": {
    title: "Sending approved leads",
    estimate: "Usually under 1 minute. It sends or simulates outreach only for leads marked Approved for Outreach.",
  },
};

let runTimer = null;
let runStartedAt = null;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}

function setBusy(button, busy) {
  if (!button) return;
  button.disabled = busy;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function confidenceClass(value) {
  const text = String(value || "Low").toLowerCase();
  if (text.includes("high")) return "high";
  if (text.includes("medium")) return "medium";
  return "low";
}

function outreachClass(value) {
  const text = String(value || "").toLowerCase();
  if (text === "sent") return "sent";
  if (text === "simulated" || text === "drafted") return "simulated";
  return "failed";
}

function updateIcons() {
  if (window.lucide) window.lucide.createIcons();
}

function formatDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleString();
}

function addActivity(message) {
  const log = $("#activity-log");
  const item = document.createElement("div");
  item.textContent = `${new Date().toLocaleTimeString()} - ${message}`;
  log.prepend(item);
}

function startRunStatus(action) {
  const info = actionInfo[action] || { title: "Running action", estimate: "Please wait while the action completes." };
  runStartedAt = Date.now();
  $("#run-title").textContent = info.title;
  $("#run-message").textContent = info.estimate;
  $("#run-elapsed").textContent = "0s";
  $("#run-status-panel").classList.remove("hidden");
  clearInterval(runTimer);
  runTimer = setInterval(() => {
    const seconds = Math.floor((Date.now() - runStartedAt) / 1000);
    const minutes = Math.floor(seconds / 60);
    const rest = seconds % 60;
    $("#run-elapsed").textContent = minutes > 0 ? `${minutes}m ${rest}s` : `${seconds}s`;
  }, 1000);
}

function stopRunStatus(message) {
  clearInterval(runTimer);
  runTimer = null;
  if (message) $("#run-message").textContent = message;
  setTimeout(() => $("#run-status-panel").classList.add("hidden"), 3500);
}

async function loadStats() {
  const stats = await api("/stats");
  $("#stat-companies").textContent = stats.companies.total;
  $("#stat-company-detail").textContent = `${stats.companies.with_website} with websites`;
  $("#stat-leads").textContent = stats.leads.total;
  $("#stat-lead-detail").textContent = `${stats.leads.with_email} with email`;
  $("#stat-roles").textContent = stats.leads.role_verified;
  $("#stat-confidence").textContent = `${stats.leads.by_confidence.High || 0} high confidence`;
  $("#stat-outreach").textContent = stats.outreach.total;
  $("#stat-outreach-detail").textContent = `${stats.outreach.sent} sent, ${stats.outreach.simulated} simulated`;
}

async function loadIntegrations() {
  const status = await api("/integrations/status");
  const target = $("#integration-status");
  target.innerHTML = "";
  const rows = [
    ["SMTP Email", status.smtp],
    ["Email API", status.email_verification],
    ["Phone API", status.phone_verification],
  ];
  for (const [label, active] of rows) {
    const item = document.createElement("div");
    item.innerHTML = `<span>${label}</span><span class="pill ${active ? "high" : "medium"}">${active ? "Connected" : "Fallback"}</span>`;
    target.appendChild(item);
  }
}

async function loadIcp() {
  const icp = await api("/icp");
  $("#icp-industry").value = icp.industry || "";
  $("#icp-country").value = icp.country || "";
  $("#icp-min").value = icp.employee_min ?? "";
  $("#icp-max").value = icp.employee_max ?? "";
  $("#icp-titles").value = (icp.job_titles || []).join("\n");
}

async function saveIcp() {
  const country = $("#icp-country").value.trim();
  const payload = {
    industry: $("#icp-industry").value.trim(),
    country: country.toLowerCase() === "inida" ? "India" : country,
    employee_min: Number($("#icp-min").value || 0),
    employee_max: Number($("#icp-max").value || 0),
    job_titles: $("#icp-titles")
      .value.split(/\n|,/)
      .map((item) => item.trim())
      .filter(Boolean),
  };
  await api("/icp", { method: "PUT", body: JSON.stringify(payload) });
  toast("ICP saved");
  addActivity("ICP updated. Run Discover Companies to replace the dataset.");
  await refreshAll();
}

async function loadCompanies() {
  state.companies = await api("/companies-db");
  renderCompanies();
}

async function loadLeads() {
  state.leads = await api("/export/json");
  renderLeads();
}

async function loadOutreach() {
  state.outreach = await api("/outreach-logs");
  renderOutreach();
}

function renderCompanies() {
  const body = $("#companies-body");
  body.innerHTML = "";
  if (!state.companies.length) {
    body.innerHTML = `<tr><td colspan="5">No companies yet.</td></tr>`;
    return;
  }
  for (const company of state.companies) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${company.company_name || ""}</td>
      <td>${company.founder || ""}</td>
      <td>${company.founded || ""}</td>
      <td>${company.website ? `<a href="${company.website}" target="_blank" rel="noreferrer">${company.website}</a>` : ""}</td>
      <td>${company.confidence_score ?? 0}</td>
    `;
    body.appendChild(tr);
  }
}

function renderLeads() {
  const query = $("#lead-search").value.toLowerCase();
  const status = $("#status-filter").value;
  const body = $("#leads-body");
  body.innerHTML = "";

  const filtered = state.leads.filter((lead) => {
    const haystack = `${lead.full_name} ${lead.company_name} ${lead.email}`.toLowerCase();
    return (!query || haystack.includes(query)) && (!status || lead.status === status);
  });

  if (!filtered.length) {
    body.innerHTML = `<tr><td colspan="7">No leads found.</td></tr>`;
    return;
  }

  for (const lead of filtered) {
    const tr = document.createElement("tr");
    const level = lead.confidence_level || "Low";
    tr.innerHTML = `
      <td><strong>${lead.full_name || ""}</strong><br><small>${lead.job_title || ""}</small></td>
      <td>${lead.company_name || ""}</td>
      <td>${lead.email || ""}<br><small>${lead.email_status || ""}</small></td>
      <td>${lead.phone || ""}<br><small>${lead.phone_status || ""}</small></td>
      <td><span class="pill ${confidenceClass(level)}">${lead.confidence_score ?? 0} ${level}</span></td>
      <td>${statusSelect(lead)}</td>
      <td><button class="icon-button" title="Open lead" data-open-lead="${lead.id}"><i data-lucide="panel-right-open"></i></button></td>
    `;
    body.appendChild(tr);
  }
  updateIcons();
}

function statusSelect(lead) {
  return `
    <select data-status-lead="${lead.id}">
      ${statuses.map((item) => `<option ${lead.status === item ? "selected" : ""}>${item}</option>`).join("")}
    </select>
  `;
}

function renderOutreach() {
  const body = $("#outreach-body");
  body.innerHTML = "";
  if (!state.outreach.length) {
    body.innerHTML = `<tr><td colspan="5">No outreach events yet.</td></tr>`;
    return;
  }
  for (const item of state.outreach) {
    const lead = state.leads.find((entry) => entry.id === item.lead_id);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${lead ? lead.full_name : `Lead ${item.lead_id}`}</td>
      <td><span class="pill ${outreachClass(item.status)}">${item.status}</span></td>
      <td>${item.subject || ""}</td>
      <td>${formatDate(item.created_at)}</td>
      <td>${item.provider_message || ""}</td>
    `;
    body.appendChild(tr);
  }
}

async function refreshAll() {
  await Promise.all([loadStats(), loadIcp(), loadCompanies(), loadLeads(), loadOutreach(), loadIntegrations()]);
  $("#last-refresh").textContent = `Updated ${new Date().toLocaleTimeString()}`;
  updateIcons();
}

async function runPipelineAction(action, button) {
  setBusy(button, true);
  startRunStatus(action);
  try {
    const result = await api(`/${action}`, { method: "POST" });
    const count = result.processed ?? result.updated ?? result.created ?? result.imported ?? 0;
    toast(result.message || "Done");
    addActivity(`${action} completed (${count})`);
    stopRunStatus(`${result.message || "Completed"} Count: ${count}.`);
    await refreshAll();
  } catch (error) {
    toast("Action failed");
    addActivity(`${action} failed`);
    stopRunStatus("Action failed. Check terminal logs or API response.");
    console.error(error);
  } finally {
    setBusy(button, false);
  }
}

async function openLead(id) {
  const detail = await api(`/lead/${id}`);
  const lead = detail.lead;
  state.selectedLead = lead;
  $("#detail-name").textContent = lead.full_name || "Lead";
  $("#detail-company").textContent = `${lead.job_title || ""} at ${lead.company_name || ""}`;
  $("#detail-email").textContent = lead.email || "Missing";
  $("#detail-email-status").textContent = lead.email_status || "";
  $("#detail-phone").textContent = lead.phone || "Missing";
  $("#detail-phone-status").textContent = lead.phone_status || "";
  $("#detail-score").textContent = `${lead.confidence_score ?? 0} ${lead.confidence_level || ""}`;
  $("#detail-role").textContent = lead.role_verified ? "Role verified" : "Role unverified";
  $("#detail-website").textContent = lead.company_website || "Missing";
  $("#detail-linkedin").textContent = lead.linkedin_url || "";

  const evidence = $("#evidence-list");
  evidence.innerHTML = "";
  if (detail.evidence.length) {
    for (const item of detail.evidence) {
      const row = document.createElement("div");
      row.textContent = `${item.field_name}: ${item.field_value} (${item.source})`;
      evidence.appendChild(row);
    }
  } else {
    evidence.innerHTML = "<div>No evidence recorded.</div>";
  }

  const draft = await api(`/lead/${id}/cold-email`);
  $("#email-subject").value = draft.subject;
  $("#email-body").value = draft.body;
  $("#lead-dialog").showModal();
  updateIcons();
}

async function updateLeadStatus(id, status) {
  await api(`/lead/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  toast("Status updated");
  await refreshAll();
}

async function sendSelectedLead() {
  if (!state.selectedLead) return;
  const result = await api(`/lead/${state.selectedLead.id}/send-email`, { method: "POST" });
  toast(result.outreach.status === "Sent" ? "Email sent" : result.outreach.status);
  addActivity(`Outreach ${result.outreach.status.toLowerCase()} for ${state.selectedLead.full_name}`);
  await refreshAll();
}

function bindEvents() {
  $("#refresh-btn").addEventListener("click", refreshAll);
  $("#save-icp-btn").addEventListener("click", saveIcp);
  $("#lead-search").addEventListener("input", renderLeads);
  $("#status-filter").addEventListener("change", renderLeads);
  $("#approve-btn").addEventListener("click", () => {
    if (state.selectedLead) updateLeadStatus(state.selectedLead.id, "Approved for Outreach");
  });
  $("#send-btn").addEventListener("click", sendSelectedLead);

  $$(".action-list button").forEach((button) => {
    button.addEventListener("click", () => runPipelineAction(button.dataset.action, button));
  });

  $$(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      $$(".tab").forEach((item) => item.classList.remove("active"));
      $$(".tab-panel").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      $(`#${button.dataset.tab}-tab`).classList.add("active");
    });
  });

  document.body.addEventListener("click", (event) => {
    const openButton = event.target.closest("[data-open-lead]");
    if (openButton) openLead(Number(openButton.dataset.openLead));
  });

  document.body.addEventListener("change", (event) => {
    const select = event.target.closest("[data-status-lead]");
    if (select) updateLeadStatus(Number(select.dataset.statusLead), select.value);
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  await refreshAll();
});

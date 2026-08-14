// IWPAS Admin Panel - talks directly to the FastAPI backend.
// No mock data anywhere: every list below is populated from a real fetch()
// call, and every empty state means the backend genuinely returned nothing.

let API_BASE = "http://localhost:8000";

// Theme toggle
const themeToggle = document.getElementById("themeToggle");
const savedTheme = localStorage.getItem("tk_theme") || "light";
document.documentElement.setAttribute("data-theme", savedTheme);
themeToggle.textContent = savedTheme === "dark" ? "☀️" : "🌙";

themeToggle.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("tk_theme", next);
  themeToggle.textContent = next === "dark" ? "☀️" : "🌙";
});

// Logout handler
document.getElementById("logoutBtn").addEventListener("click", () => {
  sessionStorage.removeItem("tk_auth");
  window.location.href = "login.html";
});

// ---------------- Tabs ----------------
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

// ---------------- Helpers ----------------
async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  const contentType = res.headers.get("content-type") || "";
  return contentType.includes("json") ? res.json() : res.text();
}

function toast(message, type = "info") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  document.getElementById("toastRoot").appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

function openModal(html) {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `<div class="modal-box">${html}</div>`;
  overlay.addEventListener("click", e => { if (e.target === overlay) overlay.remove(); });
  document.getElementById("modalRoot").appendChild(overlay);
  return overlay;
}

function closeModal(overlay) { overlay.remove(); }

// ---------------- Presets (for dropdowns) ----------------
let _presetsCache = [];

async function loadPresetsForSelect() {
  try {
    _presetsCache = await api("/api/presets") || [];
  } catch {
    _presetsCache = [];
  }
}

function presetsOptionsHtml(selectedId = null) {
  if (!_presetsCache.length) return `<option value="">No presets configured</option>`;
  return `<option value="">— none —</option>` +
    _presetsCache.map(p => `<option value="${p.id}" ${p.id === selectedId ? 'selected' : ''}>${p.name} (${p.target_weight.toFixed(2)} kg)</option>`).join("");
}

// ---------------- Stations ----------------
async function loadStations() {
  const container = document.getElementById("stationsList");
  await loadPresetsForSelect();
  try {
    const stations = await api("/api/stations");
    if (!stations.length) {
      container.innerHTML = `<div class="empty-state">No stations configured yet. Add one to connect a real scale + printer pair.</div>`;
      return;
    }
    container.innerHTML = stations.map(stationCardHtml).join("");
    stations.forEach(s => {
      document.getElementById(`edit-scale-${s.id}`)?.addEventListener("click", () => openScaleModal(s));
      document.getElementById(`edit-printer-${s.id}`)?.addEventListener("click", () => openPrinterModal(s));
      document.getElementById(`edit-station-${s.id}`)?.addEventListener("click", () => openStationEditModal(s));
      document.getElementById(`delete-station-${s.id}`)?.addEventListener("click", () => confirmDeleteStation(s));
    });

    const sel = document.getElementById("filterStation");
    sel.innerHTML = `<option value="">All Stations</option>` +
      stations.map(s => `<option value="${s.id}">${s.name}</option>`).join("");
  } catch (e) {
    container.innerHTML = `<div class="empty-state">Could not reach the API at ${API_BASE}. ${e.message}</div>`;
  }
}

function stationCardHtml(s) {
  const scaleOk = !!(s.scale && s.scale.ip_address) || !!(s.scale && s.scale.serial_port);
  const printerOk = !!(s.printer && s.printer.ip_address);
  const preset = _presetsCache.find(p => p.id === s.active_preset_id);
  const presetName = preset ? preset.name : 'None';
  const isMonitored = s.is_enabled && scaleOk && printerOk;
  
  return `
  <div class="station-card">
    <h3>${s.name}</h3>
    <div class="machine-id">MACHINE ID: ${s.machine_id}</div>
    ${isMonitored ? '<div class="auto-status">🟢 AUTO-MONITORING ACTIVE</div>' : '<div class="auto-status warn">⚠️ Auto-monitoring disabled</div>'}
    <div class="device-row">
      <span class="device-label"><span class="status-dot ${scaleOk ? 'ok' : 'warn'}"></span>Scale</span>
      <span class="device-val">${s.scale ? (s.scale.brand || 'Unnamed') + ' · ' + (s.scale.connection_type === 'tcp' ? s.scale.ip_address + ':' + s.scale.port : s.scale.serial_port) : 'Not configured'}</span>
    </div>
    <div class="device-row">
      <span class="device-label"><span class="status-dot ${printerOk ? 'ok' : 'warn'}"></span>Printer</span>
      <span class="device-val">${s.printer ? (s.printer.brand || 'Unnamed') + ' · ' + s.printer.ip_address + ':' + s.printer.port : 'Not configured'}</span>
    </div>
    <div class="device-row">
      <span class="device-label">Preset</span>
      <span class="device-val">${presetName}</span>
    </div>
    <div class="card-actions">
      <button id="edit-station-${s.id}">Edit</button>
      <button id="delete-station-${s.id}" class="danger-btn">Delete</button>
      <button id="edit-scale-${s.id}">Scale</button>
      <button id="edit-printer-${s.id}">Printer</button>
    </div>
    <div class="info-text">When enabled, this station automatically weighs and prints when a box is placed on the scale. No button press needed.</div>
  </div>`;
}

document.getElementById("newStationBtn").addEventListener("click", () => {
  const overlay = openModal(`
    <h3>New Station</h3>
    <div class="form-row"><label>Station Name</label><input id="f-name" placeholder="Line 1" /></div>
    <div class="form-row"><label>Machine ID (printed on box)</label><input id="f-machine" placeholder="L1" /></div>
    <div class="form-row"><label>Weight Preset</label><select id="f-preset">${presetsOptionsHtml()}</select></div>
    <div class="modal-actions">
      <button class="cancel">Cancel</button>
      <button class="confirm">Create</button>
    </div>`);
  overlay.querySelector(".cancel").addEventListener("click", () => closeModal(overlay));
  overlay.querySelector(".confirm").addEventListener("click", async () => {
    const name = document.getElementById("f-name").value.trim();
    const machine_id = document.getElementById("f-machine").value.trim();
    const active_preset_id = document.getElementById("f-preset").value ? parseInt(document.getElementById("f-preset").value) : null;
    if (!name || !machine_id) { toast("Name and Machine ID are required", "error"); return; }
    try {
      await api("/api/stations", { method: "POST", body: JSON.stringify({ name, machine_id, active_preset_id, is_enabled: true }) });
      toast("Station created", "success");
      closeModal(overlay);
      loadStations();
    } catch (e) { toast(e.message, "error"); }
  });
});

function openStationEditModal(station) {
  const overlay = openModal(`
    <h3>Edit Station</h3>
    <div class="form-row"><label>Station Name</label><input id="f-name" value="${station.name}" /></div>
    <div class="form-row"><label>Machine ID</label><input id="f-machine" value="${station.machine_id}" /></div>
    <div class="form-row"><label>Weight Preset</label><select id="f-preset">${presetsOptionsHtml(station.active_preset_id)}</select></div>
    <div class="form-row"><label>Enabled</label><input type="checkbox" id="f-enabled" ${station.is_enabled ? 'checked' : ''} /></div>
    <div class="modal-actions">
      <button class="cancel">Cancel</button>
      <button class="confirm">Save</button>
    </div>`);
  overlay.querySelector(".cancel").addEventListener("click", () => closeModal(overlay));
  overlay.querySelector(".confirm").addEventListener("click", async () => {
    const name = document.getElementById("f-name").value.trim();
    const machine_id = document.getElementById("f-machine").value.trim();
    const active_preset_id = document.getElementById("f-preset").value ? parseInt(document.getElementById("f-preset").value) : null;
    const is_enabled = document.getElementById("f-enabled").checked;
    if (!name || !machine_id) { toast("Name and Machine ID are required", "error"); return; }
    try {
      await api(`/api/stations/${station.id}`, { method: "PUT", body: JSON.stringify({ name, machine_id, active_preset_id, is_enabled }) });
      toast("Station updated", "success");
      closeModal(overlay);
      loadStations();
    } catch (e) { toast(e.message, "error"); }
  });
}

function confirmDeleteStation(station) {
  const overlay = openModal(`
    <h3>Delete Station</h3>
    <p>Are you sure you want to delete <strong>${station.name}</strong>? This cannot be undone.</p>
    <div class="form-row">
      <label>Type <strong>${station.name}</strong> to confirm deletion:</label>
      <input id="f-confirm-name" placeholder="${station.name}" />
    </div>
    <div class="modal-actions">
      <button class="cancel">Cancel</button>
      <button class="confirm danger-btn">Delete</button>
    </div>`);
  overlay.querySelector(".cancel").addEventListener("click", () => closeModal(overlay));
  const confirmBtn = overlay.querySelector(".confirm");
  confirmBtn.addEventListener("click", async () => {
    const typed = document.getElementById("f-confirm-name").value.trim();
    if (typed !== station.name) {
      toast("Station name does not match", "error");
      return;
    }
    try {
      await api(`/api/stations/${station.id}`, { method: "DELETE" });
      toast("Station deleted", "success");
      closeModal(overlay);
      loadStations();
    } catch (e) { toast(e.message, "error"); }
  });
}

function openScaleModal(station) {
  const sc = station.scale || {};
  const overlay = openModal(`
    <h3>Scale — ${station.name}</h3>
    <div class="form-row two-col">
      <div><label>Brand</label><input id="f-brand" value="${sc.brand || ''}" placeholder="e.g. Essae" /></div>
      <div><label>Model</label><input id="f-model" value="${sc.model || ''}" placeholder="e.g. DS-252" /></div>
    </div>
    <div class="form-row">
      <label>Connection Type</label>
      <select id="f-conn">
        <option value="tcp" ${sc.connection_type !== 'serial' ? 'selected' : ''}>TCP (WiFi bridge)</option>
        <option value="serial" ${sc.connection_type === 'serial' ? 'selected' : ''}>Serial (direct RS232/RS485)</option>
      </select>
    </div>
    <div class="form-row two-col">
      <div><label>IP Address</label><input id="f-ip" value="${sc.ip_address || ''}" placeholder="192.168.1.50" /></div>
      <div><label>Port</label><input id="f-port" value="${sc.port || 4001}" /></div>
    </div>
    <div class="form-row two-col">
      <div><label>Serial Port</label><input id="f-serial" value="${sc.serial_port || ''}" placeholder="COM3 or /dev/ttyUSB0" /></div>
      <div><label>Baud Rate</label><input id="f-baud" value="${sc.baud_rate || 9600}" /></div>
    </div>
    <div class="form-row">
      <label>Parse Pattern (regex to extract the weight number)</label>
      <input id="f-pattern" value="${(sc.parse_pattern || '([-+]?\\d+\\.?\\d*)').replace(/"/g,'&quot;')}" />
    </div>
    <div class="form-row two-col">
      <div><label>Unit</label><input id="f-unit" value="${sc.unit || 'kg'}" /></div>
      <div><label>Timeout (sec)</label><input id="f-timeout" value="${sc.timeout_sec || 3.0}" /></div>
    </div>
    <div class="modal-actions">
      <button class="cancel">Cancel</button>
      <button class="confirm">Save</button>
    </div>`);
  overlay.querySelector(".cancel").addEventListener("click", () => closeModal(overlay));
  overlay.querySelector(".confirm").addEventListener("click", async () => {
    const payload = {
      brand: val("f-brand"), model: val("f-model"),
      connection_type: val("f-conn"),
      ip_address: val("f-ip"), port: parseInt(val("f-port")) || 4001,
      serial_port: val("f-serial"), baud_rate: parseInt(val("f-baud")) || 9600,
      parity: "N", stopbits: 1, bytesize: 8,
      parse_pattern: val("f-pattern"), unit: val("f-unit"),
      timeout_sec: parseFloat(val("f-timeout")) || 3.0,
    };
    try {
      await api(`/api/stations/${station.id}/scale`, { method: "PUT", body: JSON.stringify(payload) });
      toast("Scale settings saved", "success");
      closeModal(overlay);
      loadStations();
    } catch (e) { toast(e.message, "error"); }
  });
}

function openPrinterModal(station) {
  const pr = station.printer || {};
  const overlay = openModal(`
    <h3>Printer — ${station.name}</h3>
    <div class="form-row two-col">
      <div><label>Brand</label><input id="f-brand" value="${pr.brand || ''}" placeholder="e.g. Linx" /></div>
      <div><label>Model</label><input id="f-model" value="${pr.model || ''}" placeholder="e.g. CJ400" /></div>
    </div>
    <div class="form-row">
      <label>Protocol</label>
      <select id="f-proto">
        <option value="tcp_text" ${pr.protocol !== 'linx_rci' ? 'selected' : ''}>TCP Text (generic message field)</option>
        <option value="linx_rci" ${pr.protocol === 'linx_rci' ? 'selected' : ''}>Linx RCI (binary protocol)</option>
      </select>
    </div>
    <div class="form-row two-col">
      <div><label>IP Address</label><input id="f-ip" value="${pr.ip_address || ''}" placeholder="192.168.1.60" /></div>
      <div><label>Port</label><input id="f-port" value="${pr.port || 9100}" /></div>
    </div>
    <div class="form-row">
      <label>Timeout (sec)</label><input id="f-timeout" value="${pr.timeout_sec || 3.0}" />
    </div>
    <div class="modal-actions">
      <button class="cancel">Cancel</button>
      <button class="confirm">Save</button>
    </div>`);
  overlay.querySelector(".cancel").addEventListener("click", () => closeModal(overlay));
  overlay.querySelector(".confirm").addEventListener("click", async () => {
    const payload = {
      brand: val("f-brand"), model: val("f-model"),
      protocol: val("f-proto"),
      ip_address: val("f-ip"), port: parseInt(val("f-port")) || 9100,
      timeout_sec: parseFloat(val("f-timeout")) || 3.0,
      rci_message_slot: 1, rci_field_map: "{}",
    };
    try {
      await api(`/api/stations/${station.id}/printer`, { method: "PUT", body: JSON.stringify(payload) });
      toast("Printer settings saved", "success");
      closeModal(overlay);
      loadStations();
    } catch (e) { toast(e.message, "error"); }
  });
}

async function triggerWeigh(station) {
  toast(`Waiting for stable weight on ${station.name}...`, "info");
  try {
    const result = await api(`/api/stations/${station.id}/weigh`, {
      method: "POST",
      body: JSON.stringify({ station_id: station.id, batch_number: "", operator: "" }),
    });
    toast(`${result.box_id} — ${result.weight} ${result.unit} — print: ${result.print_status}`,
      result.print_status === "printed" ? "success" : "error");
    loadRecords();
  } catch (e) {
    toast(`Weigh failed on ${station.name}: ${e.message}`, "error");
  }
}

function val(id) { return document.getElementById(id).value.trim(); }

// ---------------- Presets ----------------
async function loadPresets() {
  const tbody = document.querySelector("#presetsTable tbody");
  try {
    const presets = await api("/api/presets");
    if (!presets.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No weight presets yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = presets.map(p => `
      <tr>
        <td>${p.name}</td><td class="mono">${p.product_code}</td>
        <td class="mono">${p.target_weight.toFixed(3)}</td>
        <td class="mono">${p.min_weight.toFixed(3)}</td>
        <td class="mono">${p.max_weight.toFixed(3)}</td>
        <td><button class="icon-btn" data-del-preset="${p.id}">Delete</button></td>
      </tr>`).join("");
    tbody.querySelectorAll("[data-del-preset]").forEach(btn => {
      btn.addEventListener("click", async () => {
        await api(`/api/presets/${btn.dataset.delPreset}`, { method: "DELETE" });
        await loadPresetsForSelect();
        loadPresets();
      });
    });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${e.message}</td></tr>`;
  }
}

document.getElementById("newPresetBtn").addEventListener("click", () => {
  const overlay = openModal(`
    <h3>New Weight Preset</h3>
    <div class="form-row"><label>Name</label><input id="f-name" placeholder="1kg x 12" /></div>
    <div class="form-row"><label>Product Code (2 chars)</label><input id="f-code" maxlength="2" placeholder="AB" /></div>
    <div class="form-row two-col">
      <div><label>Target (kg)</label><input id="f-target" placeholder="12.000" /></div>
      <div><label>Min (kg)</label><input id="f-min" placeholder="12.000" /></div>
    </div>
    <div class="form-row"><label>Max (kg)</label><input id="f-max" placeholder="12.250" /></div>
    <div class="modal-actions">
      <button class="cancel">Cancel</button>
      <button class="confirm">Create</button>
    </div>`);
  overlay.querySelector(".cancel").addEventListener("click", () => closeModal(overlay));
  overlay.querySelector(".confirm").addEventListener("click", async () => {
    const payload = {
      name: val("f-name"), product_code: val("f-code"),
      target_weight: parseFloat(val("f-target")),
      min_weight: parseFloat(val("f-min")),
      max_weight: parseFloat(val("f-max")),
    };
    if (!payload.name || isNaN(payload.target_weight)) { toast("Fill all fields", "error"); return; }
    try {
      await api("/api/presets", { method: "POST", body: JSON.stringify(payload) });
      toast("Preset created", "success");
      closeModal(overlay);
      await loadPresetsForSelect();
      loadPresets();
    } catch (e) { toast(e.message, "error"); }
  });
});

// ---------------- Recipients ----------------
async function loadRecipients() {
  const tbody = document.querySelector("#recipientsTable tbody");
  try {
    const recipients = await api("/api/recipients");
    if (!recipients.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="empty-state">No recipients yet. Weekly reports won't be emailed until you add at least one.</td></tr>`;
      return;
    }
    tbody.innerHTML = recipients.map(r => `
      <tr>
        <td>${r.name || '—'}</td><td class="mono">${r.email}</td>
        <td><span class="badge ${r.is_active ? 'yes' : 'no'}">${r.is_active ? 'Active' : 'Inactive'}</span></td>
        <td><button class="icon-btn" data-del-recipient="${r.id}">Remove</button></td>
      </tr>`).join("");
    tbody.querySelectorAll("[data-del-recipient]").forEach(btn => {
      btn.addEventListener("click", async () => {
        await api(`/api/recipients/${btn.dataset.delRecipient}`, { method: "DELETE" });
        loadRecipients();
      });
    });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-state">${e.message}</td></tr>`;
  }
}

document.getElementById("newRecipientBtn").addEventListener("click", () => {
  const overlay = openModal(`
    <h3>Add Email Recipient</h3>
    <div class="form-row"><label>Name</label><input id="f-name" placeholder="QA Manager" /></div>
    <div class="form-row"><label>Email</label><input id="f-email" placeholder="qa@example.com" /></div>
    <div class="modal-actions">
      <button class="cancel">Cancel</button>
      <button class="confirm">Add</button>
    </div>`);
  overlay.querySelector(".cancel").addEventListener("click", () => closeModal(overlay));
  overlay.querySelector(".confirm").addEventListener("click", async () => {
    try {
      await api("/api/recipients", { method: "POST", body: JSON.stringify({ name: val("f-name"), email: val("f-email"), is_active: true }) });
      toast("Recipient added", "success");
      closeModal(overlay);
      loadRecipients();
    } catch (e) { toast(e.message, "error"); }
  });
});

// ---------------- Records ----------------
async function loadRecords() {
  const tbody = document.querySelector("#recordsTable tbody");
  const stationId = document.getElementById("filterStation").value;
  const status = document.getElementById("filterStatus").value;
  const params = new URLSearchParams();
  if (stationId) params.set("station_id", stationId);
  if (status) params.set("print_status", status);
  try {
    const records = await api(`/api/records?${params.toString()}`);
    if (!records.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No box records match these filters.</td></tr>`;
      return;
    }
    tbody.innerHTML = records.map(r => `
      <tr>
        <td class="mono">${r.box_id}</td>
        <td>${new Date(r.created_at).toLocaleString()}</td>
        <td>${r.machine_id}</td>
        <td class="mono">${r.weight.toFixed(3)} ${r.unit}</td>
        <td>${r.within_tolerance === null ? '—' : `<span class="badge ${r.within_tolerance ? 'yes' : 'no'}">${r.within_tolerance ? 'OK' : 'Out'}</span>`}</td>
        <td><span class="badge ${r.print_status}">${r.print_status}</span></td>
        <td>${r.print_status === 'failed' ? `<button class="icon-btn" data-reprint="${r.box_id}" data-station="${r.station_id}">Reprint</button>` : ''}</td>
      </tr>`).join("");
    tbody.querySelectorAll("[data-reprint]").forEach(btn => {
      btn.addEventListener("click", async () => {
        try {
          await api(`/api/stations/${btn.dataset.station}/reprint/${btn.dataset.reprint}`, { method: "POST" });
          toast(`Reprinted ${btn.dataset.reprint}`, "success");
          loadRecords();
        } catch (e) { toast(e.message, "error"); }
      });
    });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">${e.message}</td></tr>`;
  }
}
document.getElementById("refreshRecordsBtn").addEventListener("click", loadRecords);
document.getElementById("filterStation").addEventListener("change", loadRecords);
document.getElementById("filterStatus").addEventListener("change", loadRecords);

// ---------------- Reports ----------------
async function loadReports() {
  const tbody = document.querySelector("#reportsTable tbody");
  try {
    const logs = await api("/api/reports/logs");
    if (!logs.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No reports have run yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = logs.map(l => `
      <tr>
        <td>${new Date(l.period_start).toLocaleDateString()} – ${new Date(l.period_end).toLocaleDateString()}</td>
        <td>${l.recipients || '—'}</td>
        <td class="mono">${l.box_count}</td>
        <td>${new Date(l.sent_at).toLocaleString()}</td>
        <td><span class="badge ${l.status}">${l.status}</span></td>
        <td><a class="icon-btn" href="${API_BASE}/api/reports/download/${l.id}">Download</a></td>
      </tr>`).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${e.message}</td></tr>`;
  }
}

document.getElementById("runReportBtn").addEventListener("click", async () => {
  toast("Generating report and sending email...", "info");
  try {
    const result = await api("/api/reports/run-now", { method: "POST" });
    toast(`Report sent to ${result.recipients.length} recipient(s) — ${result.box_count} boxes`, "success");
  } catch (e) {
    toast(`Report failed: ${e.message}`, "error");
  }
  loadReports();
});

// ---------------- Init ----------------
async function loadAll() {
  await loadPresetsForSelect();  // load once for dropdowns
  loadStations();
  loadPresets();
  loadRecipients();
  loadRecords();
  loadReports();
}
loadAll();

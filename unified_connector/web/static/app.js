/* Unified Connector Web UI (vanilla JS) */

// Global state for current user and permissions
let currentUser = null;
let userPermissions = [];

function $(sel) {
  const el = document.querySelector(sel);
  if (!el) throw new Error(`Missing element: ${sel}`);
  return el;
}

function safeJsonStringify(v) {
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

let toastTimer = null;
function toast(message, kind = "ok") {
  const el = $("#toast");
  el.className = `toast show ${kind}`;
  el.textContent = message;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.className = "toast";
  }, 2600);
}

async function apiFetch(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "include", // Important for session cookies
    ...options,
  });

  // Handle 401 Unauthorized - throw error but don't redirect
  // (let checkAuth() handle the redirect logic based on auth_enabled)
  if (resp.status === 401) {
    throw new Error("Authentication required");
  }

  const contentType = resp.headers.get("content-type") || "";
  let body = null;
  if (contentType.includes("application/json")) body = await resp.json();
  else body = await resp.text();

  if (!resp.ok) {
    const msg =
      (body && body.message) ||
      (typeof body === "string" ? body : null) ||
      `HTTP ${resp.status}`;
    throw new Error(msg);
  }
  return body;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setKVs(containerSel, obj) {
  const container = $(containerSel);
  container.innerHTML = "";
  if (!obj || typeof obj !== "object") {
    container.innerHTML = `<div class="muted">No data</div>`;
    return;
  }

  const entries = Object.entries(obj);
  if (entries.length === 0) {
    container.innerHTML = `<div class="muted">No data</div>`;
    return;
  }

  for (const [k, v] of entries) {
    const div = document.createElement("div");
    div.className = "kv";
    div.innerHTML = `<div class="k">${escapeHtml(k)}</div><div class="v">${escapeHtml(
      typeof v === "string" ? v : safeJsonStringify(v)
    )}</div>`;
    container.appendChild(div);
  }
}

function setBadge(sel, value, kind = "ok") {
  const el = $(sel);
  el.className = `pill ${kind}`;
  el.innerHTML = `<strong>${escapeHtml(value)}</strong>`;
}

function buildFqn(catalog, schema, table) {
  const c = (catalog || "").trim();
  const s = (schema || "").trim();
  const t = (table || "").trim();
  return [c, s, t].filter(Boolean).join(".");
}

function parseFqn(fqn) {
  const parts = (fqn || "").split(".").map((p) => p.trim()).filter(Boolean);
  if (parts.length !== 3) return null;
  return { catalog: parts[0], schema: parts[1], table: parts[2] };
}

function normalizeZerobusConfigForForm(cfg) {
  const catalog = cfg?.default_target?.catalog || "";
  const schema = cfg?.default_target?.schema || "";
  const table = cfg?.default_target?.table || "";

  return {
    enabled: Boolean(cfg?.enabled),
    workspace_host: cfg?.workspace_host || cfg?.default_target?.workspace_host || "",
    zerobus_endpoint: cfg?.zerobus_endpoint || "",
    table_fqn: buildFqn(catalog, schema, table),
    auth: {
      client_id: cfg?.auth?.client_id || "",
      client_secret: "",
      has_secret: cfg?.auth?.client_secret === "***",
    },
  };
}

async function refreshStatus() {
  const status = await apiFetch("/api/status");
  setKVs("#statusKVs", status);

  const zerobusConnected =
    status?.zerobus_connected ?? status?.zerobus?.connected ?? status?.zerobusConnected;
  if (typeof zerobusConnected === "boolean") {
    setBadge(
      "#badgeZerobus",
      zerobusConnected ? "ZeroBus: connected" : "ZeroBus: disconnected",
      zerobusConnected ? "ok" : "bad"
    );
  } else {
    setBadge("#badgeZerobus", "ZeroBus: unknown", "warn");
  }

  const configured = status?.configured_sources;
  const active = status?.active_sources;
  if (typeof configured === "number" && typeof active === "number") {
    setBadge("#badgeSources", `Sources: ${configured} configured (${active} active)`, active > 0 ? "ok" : "warn");
  } else if (typeof configured === "number") {
    setBadge("#badgeSources", `Sources: ${configured} configured`, "ok");
  } else {
    setBadge("#badgeSources", "Sources: unknown", "warn");
  }

  const discoveryCount = status?.discovery_count;
  if (typeof discoveryCount === "number") {
    setBadge("#badgeDiscovery", `Discovery: ${discoveryCount} found`, discoveryCount > 0 ? "ok" : "warn");
  } else {
    const discoveryOn = status?.discovery?.enabled ?? status?.discovery_enabled;
    if (typeof discoveryOn === "boolean")
      setBadge(
        "#badgeDiscovery",
        discoveryOn ? "Discovery: on" : "Discovery: off",
        discoveryOn ? "ok" : "warn"
      );
    else setBadge("#badgeDiscovery", "Discovery: unknown", "warn");
  }

}

async function refreshMetrics() {
  const metrics = await apiFetch("/api/metrics");
  setKVs("#metricsKVs", metrics);
}

async function refreshSources() {
  const [data, status] = await Promise.all([apiFetch("/api/sources"), apiFetch("/api/status")]);
  const sources = Array.isArray(data?.sources) ? data.sources : [];
  const clients = status?.metrics?.clients || {};
  const activeMap = new Set(Object.keys(clients));

  const tbody = $("#sourcesTbody");
  tbody.innerHTML = "";

  if (sources.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="8" class="muted">No sources configured yet.</td>`;
    tbody.appendChild(tr);
    return;
  }

  for (const s of sources) {
    const name = s?.name ?? "";
    const protocol = s?.protocol ?? "";
    const endpoint = s?.endpoint ?? "";
    const enabled = s?.enabled;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="checkbox" data-select="source" data-name="${escapeHtml(name)}" /></td>
      <td><code>${escapeHtml(name)}</code></td>
      <td>${escapeHtml(protocol)}</td>
      <td><code>${escapeHtml(endpoint)}</code></td>
      <td>${activeMap.has(name) ? "<strong>yes</strong>" : "<span class='muted'>no</span>"}</td>
      <td>${typeof enabled === "boolean" ? (enabled ? "true" : "false") : "<span class='muted'>n/a</span>"}</td>
      <td>
        <span class="actions">
        ${activeMap.has(name)
          ? `<button class="btn btn-warning" data-action="stop" data-name="${escapeHtml(name)}">Stop</button>`
          : `<button class="btn btn-good" data-action="start" data-name="${escapeHtml(name)}">Start</button>`
        }
        <button class="btn btn-secondary" data-action="edit" data-name="${escapeHtml(name)}">Edit</button>
        </span>
      </td>
      <td style="text-align:right">
        <button class="iconbtn danger" title="Delete" aria-label="Delete" data-action="delete" data-name="${escapeHtml(name)}">x</button>
      </td>
    `;
    tbody.appendChild(tr);
  }
}

async function refreshDiscovered() {
  const data = await apiFetch(`/api/discovery/servers`);
  const servers = Array.isArray(data?.servers) ? data.servers : [];

  const groups = { opcua: [], mqtt: [], modbus: [] };
  for (const s of servers) {
    const p = (s?.protocol || "").toLowerCase();
    if (p === "opcua") groups.opcua.push(s);
    else if (p === "mqtt") groups.mqtt.push(s);
    else if (p === "modbus") groups.modbus.push(s);
  }

  const renderGroup = (tbodySel, list, countSel) => {
    const tbody = $(tbodySel);
    tbody.innerHTML = "";
    const countEl = document.querySelector(countSel);
    if (countEl) countEl.textContent = `${list.length} found`;

    if (list.length === 0) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td colspan="5" class="muted">None discovered yet. Click “Scan”.</td>`;
      tbody.appendChild(tr);
      return;
    }

    for (const s of list) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code>${escapeHtml(s?.host ?? "")}</code></td>
        <td>${escapeHtml(String(s?.port ?? ""))}</td>
        <td><code>${escapeHtml(s?.endpoint ?? "")}</code></td>
        <td>${s?.reachable === true ? "yes" : s?.reachable === false ? "no" : "<span class='muted'>n/a</span>"}</td>
        <td>
          <span class="actions">
          <button class="btn btn-secondary" data-action="test" data-protocol="${escapeHtml(
            s?.protocol ?? ""
          )}" data-host="${escapeHtml(s?.host ?? "")}" data-port="${escapeHtml(String(s?.port ?? ""))}">Test</button>
          <button class="btn btn-primary" data-action="add" data-protocol="${escapeHtml(
            s?.protocol ?? ""
          )}" data-endpoint="${escapeHtml(s?.endpoint ?? "")}" data-host="${escapeHtml(
            s?.host ?? ""
          )}" data-port="${escapeHtml(String(s?.port ?? ""))}">Add as source</button>
          </span>
        </td>
      `;
      tbody.appendChild(tr);
    }
  };

  renderGroup("#discoveryTbodyOpcua", groups.opcua, "#discoveryCountOpcua");
  renderGroup("#discoveryTbodyMqtt", groups.mqtt, "#discoveryCountMqtt");
  renderGroup("#discoveryTbodyModbus", groups.modbus, "#discoveryCountModbus");
}

async function loadZerobus() {
  const cfg = await apiFetch("/api/zerobus/config");
  const z = normalizeZerobusConfigForForm(cfg);

  $("#zbEnabled").checked = z.enabled;
  $("#zbWorkspace").value = z.workspace_host;
  $("#zbZerobusEndpoint").value = z.zerobus_endpoint;
  $("#zbTableFqn").value = z.table_fqn;
  $("#zbClientId").value = z.auth.client_id;
  $("#zbClientSecret").value = "";
  $("#zbSecretHint").textContent = z.auth.has_secret
    ? "A secret is already stored (leave blank to keep it)."
    : "No secret stored yet.";

  // Load proxy settings
  const proxy = z.proxy || {};
  $("#zbProxyEnabled").checked = proxy.enabled || false;
  $("#zbProxyUseEnv").checked = proxy.use_env_vars !== false; // default true
  $("#zbProxyHttp").value = proxy.http_proxy || "";
  $("#zbProxyHttps").value = proxy.https_proxy || "";
  $("#zbProxyNoProxy").value = proxy.no_proxy || "localhost,127.0.0.1";
}

async function saveZerobus() {
  const fqn = $("#zbTableFqn").value.trim();
  const parsed = parseFqn(fqn);
  if (!parsed) {
    toast("Table must be catalog.schema.table", "bad");
    return;
  }

  const payload = {
    enabled: $("#zbEnabled").checked,
    workspace_host: $("#zbWorkspace").value.trim(),
    zerobus_endpoint: $("#zbZerobusEndpoint").value.trim(),
    default_target: {
      workspace_host: $("#zbWorkspace").value.trim(),
      catalog: parsed.catalog,
      schema: parsed.schema,
      table: parsed.table,
    },
    auth: {
      client_id: $("#zbClientId").value.trim(),
    },
    proxy: {
      enabled: $("#zbProxyEnabled").checked,
      use_env_vars: $("#zbProxyUseEnv").checked,
      http_proxy: $("#zbProxyHttp").value.trim(),
      https_proxy: $("#zbProxyHttps").value.trim(),
      no_proxy: $("#zbProxyNoProxy").value.trim(),
    },
  };

  const secret = $("#zbClientSecret").value;
  if (secret && secret.trim()) payload.auth.client_secret = secret.trim();

  const res = await apiFetch("/api/zerobus/config", { method: "POST", body: JSON.stringify(payload) });
  if (res?.warning) toast(res.warning, "warn");
  else toast("ZeroBus config saved", "ok");
  await loadZerobus();
  await refreshStatus();
}


async function runZerobusDiagnostics() {
  const deep = document.getElementById('zbDiagDeep')?.checked ? 'true' : 'false';
  const data = await apiFetch(`/api/zerobus/diagnostics?deep=${deep}`);
  const el = document.getElementById('zbDiag');
  if (el) el.textContent = JSON.stringify(data, null, 2);
  toast(data?.checks?.deep_stream_create_ok === false ? 'ZeroBus diagnostics: issues found' : 'ZeroBus diagnostics: ok', data?.checks?.deep_stream_create_ok === false ? 'warn' : 'ok');
}


async function startBridge() {
  const res = await apiFetch("/api/bridge/start", { method: "POST", body: "{}" });
  toast(res?.message || "Bridge start requested", "ok");
  // Give it a moment to connect sources, then refresh
  setTimeout(() => refreshStatus().catch(() => {}), 800);
}

async function stopBridge() {
  const res = await apiFetch("/api/bridge/stop", { method: "POST", body: "{}" });
  toast(res?.message || "Bridge stop requested", "warn");
  await refreshStatus();
}

async function startZerobus() {
  const res = await apiFetch("/api/zerobus/start", { method: "POST", body: "{}" });
  toast(res?.message || "ZeroBus start requested", "ok");
  await refreshStatus();
}

async function stopZerobus() {
  const res = await apiFetch("/api/zerobus/stop", { method: "POST", body: "{}" });
  toast(res?.message || "ZeroBus stop requested", "warn");
  await refreshStatus();
}

function fillSourceForm(source) {
  $("#srcName").value = source?.name ?? "";
  $("#srcProtocol").value = source?.protocol ?? "opcua";
  $("#srcEndpoint").value = source?.endpoint ?? "";
  $("#srcEnabled").checked = Boolean(source?.enabled ?? true);

  $("#srcSite").value = source?.site ?? "";
  $("#srcArea").value = source?.area ?? "";
  $("#srcLine").value = source?.line ?? "";
  $("#srcEquipment").value = source?.equipment ?? "";

  $("#srcMode").value = "edit";
  $("#srcOriginalName").value = source?.name ?? "";
  $("#srcSubmit").textContent = "Save source";
}

function resetSourceForm() {
  $("#srcName").value = "";
  $("#srcProtocol").value = "opcua";
  $("#srcEndpoint").value = "";
  $("#srcEnabled").checked = true;
  $("#srcSite").value = "";
  $("#srcArea").value = "";
  $("#srcLine").value = "";
  $("#srcEquipment").value = "";
  $("#srcMode").value = "create";
  $("#srcOriginalName").value = "";
  $("#srcSubmit").textContent = "Add source";
}

async function submitSourceForm(e) {
  e.preventDefault();

  const payload = {
    name: $("#srcName").value.trim(),
    protocol: $("#srcProtocol").value,
    endpoint: $("#srcEndpoint").value.trim(),
    enabled: $("#srcEnabled").checked,
  };

  for (const [id, key] of [
    ["#srcSite", "site"],
    ["#srcArea", "area"],
    ["#srcLine", "line"],
    ["#srcEquipment", "equipment"],
  ]) {
    const v = $(id).value.trim();
    if (v) payload[key] = v;
  }

  const mode = $("#srcMode").value;
  if (mode === "edit") {
    const originalName = $("#srcOriginalName").value;
    await apiFetch(`/api/sources/${encodeURIComponent(originalName)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    toast(`Source updated: ${payload.name}`, "ok");
  } else {
    await apiFetch("/api/sources", { method: "POST", body: JSON.stringify(payload) });
    toast(`Source added: ${payload.name}`, "ok");
  }

  resetSourceForm();
  await refreshSources();
  await refreshStatus();
}



function getSelectedSourceNames() {
  return Array.from(document.querySelectorAll('input[data-select="source"]:checked'))
    .map((el) => el.getAttribute('data-name'))
    .filter(Boolean);
}

async function startSelectedSources() {
  const names = getSelectedSourceNames();
  if (names.length === 0) {
    toast('Select at least one source', 'warn');
    return;
  }
  for (const n of names) {
    await apiFetch(`/api/sources/${encodeURIComponent(n)}/start`, { method: 'POST', body: '{}' });
  }
  toast(`Started ${names.length} source(s)`, 'ok');
  await refreshSources();
  await refreshStatus();
}

async function stopSelectedSources() {
  const names = getSelectedSourceNames();
  if (names.length === 0) {
    toast('Select at least one source', 'warn');
    return;
  }
  for (const n of names) {
    await apiFetch(`/api/sources/${encodeURIComponent(n)}/stop`, { method: 'POST', body: '{}' });
  }
  toast(`Stopped ${names.length} source(s)`, 'warn');
  await refreshSources();
  await refreshStatus();
}

async function startSource(name) {
  const res = await apiFetch(`/api/sources/${encodeURIComponent(name)}/start`, { method: "POST", body: "{}" });
  toast(res?.message || `Started: ${name}`, "ok");
  await refreshSources();
  await refreshStatus();
}

async function stopSource(name) {
  const res = await apiFetch(`/api/sources/${encodeURIComponent(name)}/stop`, { method: "POST", body: "{}" });
  toast(res?.message || `Stopped: ${name}`, "warn");
  await refreshSources();
  await refreshStatus();
}

async function deleteSource(name) {
  if (!confirm(`Delete source "${name}"?`)) return;
  await apiFetch(`/api/sources/${encodeURIComponent(name)}`, { method: "DELETE" });
  toast(`Deleted source: ${name}`, "warn");
  await refreshSources();
  await refreshStatus();
}

async function editSource(name) {
  const data = await apiFetch("/api/sources");
  const sources = Array.isArray(data?.sources) ? data.sources : [];
  const s = sources.find((x) => x?.name === name);
  if (!s) throw new Error(`Source not found: ${name}`);
  fillSourceForm(s);
  toast(`Editing source: ${name}`, "ok");
}


function suggestSourceName(protocol, host, port) {
  const base = `${protocol || 'src'}-${host || 'host'}-${port || '0'}`;
  return base.replaceAll(/[^a-zA-Z0-9_-]/g, "-").toLowerCase();
}

function prefillCreateSourceFromDiscovery(protocol, endpoint, host, port) {
  resetSourceForm();
  $("#srcName").value = suggestSourceName(protocol, host, port);
  $("#srcProtocol").value = protocol || "opcua";
  $("#srcEndpoint").value = endpoint || "";
  $("#srcEnabled").checked = true;
  toast(`Prefilled source from discovery: ${protocol} ${host}:${port}`, "ok");
  // Scroll into view
  document.getElementById('sourceForm')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function scanDiscovery() {
  await apiFetch("/api/discovery/scan", { method: "POST", body: "{}" });
  toast("Discovery scan started", "ok");
  setTimeout(() => refreshDiscovered().catch(() => {}), 1200);
}

async function testDiscoveredServer(protocol, host, port) {
  const res = await apiFetch("/api/discovery/test", {
    method: "POST",
    body: JSON.stringify({ protocol, host, port: Number(port) }),
  });
  const out = document.getElementById("discoveryTestResult");
  if (out) out.textContent = JSON.stringify(res, null, 2);
  toast(res?.ok === true ? "Discovery test: ok" : "Discovery test: failed", res?.ok === true ? "ok" : "warn");
}

function onError(err) {
  console.error(err);
  toast(err?.message || String(err), "bad");
}

function wireEvents() {
  $("#btnRefresh").addEventListener("click", () => refreshAll().catch(onError));
  $("#btnRefreshStatus").addEventListener("click", () => refreshStatus().catch(onError));
  const srcRefresh = document.getElementById("btnRefreshSources");
  if (srcRefresh) srcRefresh.addEventListener("click", () => refreshSources().catch(onError));
  $("#btnRefreshMetrics").addEventListener("click", () => refreshMetrics().catch(onError));

  const selectAll = document.getElementById('srcSelectAll');
  if (selectAll) {
    selectAll.addEventListener('change', () => {
      const checked = selectAll.checked;
      for (const cb of document.querySelectorAll('input[data-select="source"]')) {
        cb.checked = checked;
      }
    });
  }

  const startBridgeBtn = document.getElementById('btnStartBridge');
  if (startBridgeBtn) startBridgeBtn.addEventListener('click', () => startBridge().catch(onError));
  const startSel = document.getElementById('btnStartSelected');
  if (startSel) startSel.addEventListener('click', () => startSelectedSources().catch(onError));
  const stopSel = document.getElementById('btnStopSelected');
  if (stopSel) stopSel.addEventListener('click', () => stopSelectedSources().catch(onError));

  $("#btnDiscoveryScan").addEventListener("click", () => scanDiscovery().catch(onError));

  const onDiscoveryClick = (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    if (btn.getAttribute("data-action") === "test") {
      testDiscoveredServer(
        btn.getAttribute("data-protocol"),
        btn.getAttribute("data-host"),
        btn.getAttribute("data-port")
      ).catch(onError);
    }
    if (btn.getAttribute("data-action") === "add") {
      prefillCreateSourceFromDiscovery(
        btn.getAttribute("data-protocol"),
        btn.getAttribute("data-endpoint"),
        btn.getAttribute("data-host"),
        btn.getAttribute("data-port")
      );
    }
  };
  // Three protocol tbodies
  document.getElementById("discoveryTbodyOpcua")?.addEventListener("click", onDiscoveryClick);
  document.getElementById("discoveryTbodyMqtt")?.addEventListener("click", onDiscoveryClick);
  document.getElementById("discoveryTbodyModbus")?.addEventListener("click", onDiscoveryClick);

  $("#sourcesTbody").addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const action = btn.getAttribute("data-action");
    const name = btn.getAttribute("data-name");
    if (action === "start") startSource(name).catch(onError);
    if (action === "stop") stopSource(name).catch(onError);
    if (action === "delete") deleteSource(name).catch(onError);
    if (action === "edit") editSource(name).catch(onError);
  });

  $("#sourceForm").addEventListener("submit", (e) => submitSourceForm(e).catch(onError));
  $("#srcReset").addEventListener("click", (e) => {
    e.preventDefault();
    resetSourceForm();
  });

  $("#btnLoadZerobus").addEventListener("click", () => loadZerobus().catch(onError));
  $("#btnSaveZerobus").addEventListener("click", () => saveZerobus().catch(onError));
  $("#btnStartZerobus").addEventListener("click", () => startZerobus().catch(onError));
  $("#btnStopZerobus").addEventListener("click", () => stopZerobus().catch(onError));

  const diagBtn = document.getElementById('btnZerobusDiag');
  if (diagBtn) diagBtn.addEventListener('click', () => runZerobusDiagnostics().catch(onError));

  // Collapsible cards (ZeroBus / Status / Metrics)
  for (const btn of document.querySelectorAll('button[data-toggle="collapse"]')) {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const target = btn.getAttribute("data-target");
      if (!target) return;
      const body = document.querySelector(target);
      if (!body) return;
      const isOpen = body.style.display !== "none";
      body.style.display = isOpen ? "none" : "block";
      btn.textContent = isOpen ? "▾" : "▴";
    });
  }

  // Allow clicking the header to expand/collapse (except when clicking buttons/inputs)
  for (const header of document.querySelectorAll(".card.collapsible .card-header")) {
    header.addEventListener("click", (e) => {
      const t = e.target;
      if (t && (t.closest("button") || t.closest("input") || t.closest("select") || t.closest("a"))) return;
      const btn = header.querySelector('button[data-toggle="collapse"][data-target]');
      if (btn) btn.click();
    });
  }
  for (const header of document.querySelectorAll(".subcard .subcard-header")) {
    header.addEventListener("click", (e) => {
      const t = e.target;
      if (t && (t.closest("button") || t.closest("input") || t.closest("select") || t.closest("a"))) return;
      const btn = header.querySelector('button[data-toggle="collapse"][data-target]');
      if (btn) btn.click();
    });
  }
}

async function refreshAll() {
  await Promise.allSettled([
    refreshStatus(),
    refreshMetrics(),
    refreshSources(),
    refreshDiscovered(),
  ]);
}

// Authentication functions

async function checkAuth() {
  try {
    const authStatus = await apiFetch("/api/auth/status");

    // If authentication is disabled, skip auth check
    if (!authStatus.auth_enabled) {
      console.log("Authentication disabled - bypassing auth check");
      return true;
    }

    // If authentication is enabled, check if user is authenticated
    if (!authStatus.authenticated) {
      window.location.href = "/static/login.html";
      return false;
    }
    currentUser = authStatus.user;
    return true;
  } catch (error) {
    console.error("Auth check failed:", error);
    window.location.href = "/static/login.html";
    return false;
  }
}

async function loadUserPermissions() {
  try {
    const authStatus = await apiFetch("/api/auth/status");

    // If authentication is disabled, grant all permissions
    if (!authStatus.auth_enabled) {
      userPermissions = ["read", "write", "configure", "start_stop", "delete", "manage_users"];
      console.log("Authentication disabled - granting all permissions");
      return true;
    }

    // If authentication is enabled, load user permissions
    const permData = await apiFetch("/api/auth/permissions");
    userPermissions = permData.permissions || [];
    return true;
  } catch (error) {
    console.error("Failed to load permissions:", error);
    return false;
  }
}

function hasPermission(permission) {
  return userPermissions.includes(permission);
}

function canRead() {
  return hasPermission("read");
}

function canWrite() {
  return hasPermission("write");
}

function canConfigure() {
  return hasPermission("configure");
}

function canStartStop() {
  return hasPermission("start_stop");
}

function canDelete() {
  return hasPermission("delete");
}

function adaptUIForPermissions() {
  // Disable/hide buttons based on permissions

  // Discovery scan requires WRITE
  const btnDiscoveryScan = document.getElementById("btnDiscoveryScan");
  if (btnDiscoveryScan && !canWrite()) {
    btnDiscoveryScan.disabled = true;
    btnDiscoveryScan.title = "Requires write permission";
  }

  // Source add/edit requires WRITE
  const srcSubmit = document.getElementById("srcSubmit");
  if (srcSubmit && !canWrite()) {
    srcSubmit.disabled = true;
    srcSubmit.title = "Requires write permission";
  }

  // Start/stop buttons require START_STOP
  for (const btn of document.querySelectorAll('[data-action="start"], [data-action="stop"]')) {
    if (!canStartStop()) {
      btn.disabled = true;
      btn.title = "Requires start/stop permission";
    }
  }

  const btnStartBridge = document.getElementById("btnStartBridge");
  if (btnStartBridge && !canStartStop()) {
    btnStartBridge.disabled = true;
    btnStartBridge.title = "Requires start/stop permission";
  }

  const btnStartSelected = document.getElementById("btnStartSelected");
  if (btnStartSelected && !canStartStop()) {
    btnStartSelected.disabled = true;
    btnStartSelected.title = "Requires start/stop permission";
  }

  const btnStopSelected = document.getElementById("btnStopSelected");
  if (btnStopSelected && !canStartStop()) {
    btnStopSelected.disabled = true;
    btnStopSelected.title = "Requires start/stop permission";
  }

  const btnStartZerobus = document.getElementById("btnStartZerobus");
  if (btnStartZerobus && !canStartStop()) {
    btnStartZerobus.disabled = true;
    btnStartZerobus.title = "Requires start/stop permission";
  }

  const btnStopZerobus = document.getElementById("btnStopZerobus");
  if (btnStopZerobus && !canStartStop()) {
    btnStopZerobus.disabled = true;
    btnStopZerobus.title = "Requires start/stop permission";
  }

  // ZeroBus config save requires CONFIGURE
  const btnSaveZerobus = document.getElementById("btnSaveZerobus");
  if (btnSaveZerobus && !canConfigure()) {
    btnSaveZerobus.disabled = true;
    btnSaveZerobus.title = "Requires configure permission (admin only)";
  }

  // Delete buttons require DELETE
  for (const btn of document.querySelectorAll('[data-action="delete"]')) {
    if (!canDelete()) {
      btn.disabled = true;
      btn.title = "Requires delete permission (admin only)";
    }
  }

  // If viewer role (read only), add visual indicator
  if (canRead() && !canWrite()) {
    const title = document.querySelector(".topbar .title h1");
    if (title) {
      const badge = document.createElement("span");
      badge.style.cssText = "font-size: 14px; color: #666; margin-left: 12px; font-weight: normal;";
      badge.textContent = "(Read-Only)";
      title.appendChild(badge);
    }
  }
}

function displayUserInfo() {
  if (!currentUser) return;

  // Add user info to topbar
  const topbar = document.querySelector(".topbar .title");
  if (!topbar) return;

  const userInfo = document.createElement("div");
  userInfo.style.cssText = "display: flex; align-items: center; gap: 12px; font-size: 14px;";
  userInfo.innerHTML = `
    <span style="color: #666;">
      <strong>${escapeHtml(currentUser.name || currentUser.email)}</strong>
      <span style="margin-left: 8px; color: #999;">(${escapeHtml(currentUser.role)})</span>
    </span>
    <button id="btnLogout" class="btn btn-secondary" style="padding: 6px 12px; font-size: 13px;">Logout</button>
  `;

  topbar.appendChild(userInfo);

  // Wire logout button
  const btnLogout = document.getElementById("btnLogout");
  if (btnLogout) {
    btnLogout.addEventListener("click", async () => {
      try {
        await fetch("/logout", {
          method: "POST",
          credentials: "include"
        });
        window.location.href = "/static/login.html";
      } catch (error) {
        console.error("Logout failed:", error);
        toast("Logout failed", "bad");
      }
    });
  }
}

async function boot() {
  try {
    // Check authentication first
    const authenticated = await checkAuth();
    if (!authenticated) return;

    // Load user permissions
    await loadUserPermissions();

    // Display user info in header
    displayUserInfo();

    // Wire up event handlers
    wireEvents();
    resetSourceForm();

    // Load data
    await loadZerobus();
    await refreshAll();

    // Adapt UI based on permissions (must be after wireEvents and refreshAll)
    adaptUIForPermissions();

    toast("UI ready", "ok");
  } catch (e) {
    onError(e);
  }
}

window.addEventListener("DOMContentLoaded", boot);

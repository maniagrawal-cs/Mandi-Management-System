/* =========================================================
   common.js
   Small set of helper functions shared by every page.
   Since this is a simple prototype, we keep "sessions" in the
   browser's localStorage instead of building a full login system.
   ========================================================= */

// Because index.html is served by the same FastAPI app, the API is
// simply on the same origin. Using a relative path also means the
// project keeps working if you change the port.
const API_BASE = "/api";

/** Wrapper around fetch() that talks JSON and throws a readable error. */
async function apiRequest(path, options = {}) {
  const response = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    // FastAPI puts validation/HTTPException messages in `detail`.
    const message = data.detail || "Something went wrong. Please try again.";
    throw new Error(message);
  }

  return data;
}

function apiGet(path) {
  return apiRequest(path, { method: "GET" });
}

function apiPost(path, body) {
  return apiRequest(path, { method: "POST", body: JSON.stringify(body) });
}

/** Shows a message box (error / success / info) inside a container element. */
function showMessage(containerEl, text, type = "error") {
  containerEl.innerHTML = `<div class="message ${type}">${text}</div>`;
}

function clearMessage(containerEl) {
  containerEl.innerHTML = "";
}

/* ---------------- Farmer "session" helpers ---------------- */

function saveFarmerSession(farmer) {
  localStorage.setItem("farmer", JSON.stringify(farmer));
}

function getFarmerSession() {
  const raw = localStorage.getItem("farmer");
  return raw ? JSON.parse(raw) : null;
}

function clearFarmerSession() {
  localStorage.removeItem("farmer");
}

/** Redirects to the login page if no farmer is logged in. Call at the
 *  top of every farmer-only page. */
function requireFarmerLogin() {
  const farmer = getFarmerSession();
  if (!farmer) {
    window.location.href = "index.html";
    return null;
  }
  return farmer;
}

/* ---------------- Officer "session" helpers ---------------- */

function saveOfficerSession(officer) {
  localStorage.setItem("officer", JSON.stringify(officer));
}

function getOfficerSession() {
  const raw = localStorage.getItem("officer");
  return raw ? JSON.parse(raw) : null;
}

function clearOfficerSession() {
  localStorage.removeItem("officer");
}

function requireOfficerLogin() {
  const officer = getOfficerSession();
  if (!officer) {
    window.location.href = "index.html";
    return null;
  }
  return officer;
}

/* ---------------- Shared display helpers ---------------- */

// Human-friendly labels + the fixed order stages happen in.
const STAGES = [
  { key: "GATE_PASS_GENERATED", label: "Gate Pass" },
  { key: "ARRIVED", label: "Arrived" },
  { key: "QUALITY", label: "Quality" },
  { key: "WEIGHT", label: "Weight" },
  { key: "STORAGE", label: "Storage" },
  { key: "PAYMENT", label: "Payment" },
  { key: "COMPLETED", label: "Completed" },
];

function stageLabel(stageKey) {
  const found = STAGES.find((s) => s.key === stageKey);
  return found ? found.label : stageKey;
}

function stageBadgeHtml(stageKey) {
  return `<span class="stage-badge stage-${stageKey}">${stageLabel(stageKey)}</span>`;
}

function logout() {
  clearFarmerSession();
  clearOfficerSession();
  window.location.href = "index.html";
}

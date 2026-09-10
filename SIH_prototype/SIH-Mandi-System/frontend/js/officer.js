/* =========================================================
   officer.js
   Logic for officer.html: lets the officer pick a date, see all
   farmers scheduled for that date as a colour-coded grid, open
   details for one farmer, and move them to the next stage.
   ========================================================= */

const officer = requireOfficerLogin();

if (officer) {
  document.getElementById("welcome-text").textContent = `Welcome, ${officer.name}`;
}

// Default to the seeded demo date so the grid isn't empty on first load.
document.getElementById("queue-date").value = "2026-09-15";

let selectedFarmerId = null;

async function loadFarmers() {
  const date = document.getElementById("queue-date").value;
  const msgBox = document.getElementById("grid-message");
  const grid = document.getElementById("farmer-grid");

  if (!date) return;

  clearMessage(msgBox);
  grid.innerHTML = `<p class="page-subtitle">Loading...</p>`;

  try {
    const entries = await apiGet(`/officer/farmers/${date}`);

    if (entries.length === 0) {
      grid.innerHTML = "";
      showMessage(msgBox, "No farmers are scheduled for this date.", "info");
      return;
    }

    grid.innerHTML = entries.map((e) => `
      <div class="farmer-card stage-${e.stage}" onclick="openDetails('${e.farmer_id}')">
        <div class="fc-name">${e.farmer_name}</div>
        <div class="fc-id">${e.gate_pass_id}</div>
        <div class="fc-stage">${stageLabel(e.stage)}</div>
      </div>
    `).join("");
  } catch (err) {
    grid.innerHTML = "";
    showMessage(msgBox, err.message);
  }
}

async function openDetails(farmerId) {
  selectedFarmerId = farmerId;
  const panel = document.getElementById("detail-panel");
  const body = document.getElementById("detail-body");
  const msgBox = document.getElementById("detail-message");

  clearMessage(msgBox);
  panel.style.display = "block";
  body.innerHTML = `<p class="page-subtitle">Loading...</p>`;
  panel.scrollIntoView({ behavior: "smooth" });

  try {
    const data = await apiGet(`/officer/farmer/${farmerId}`);
    renderDetails(data);
  } catch (err) {
    body.innerHTML = "";
    showMessage(msgBox, err.message);
  }
}

function renderDetails(data) {
  const { farmer, gate_pass, stage, position } = data;

  document.getElementById("detail-body").innerHTML = `
    <div class="field-row"><span class="field-label">Name</span><span class="field-value">${farmer.name}</span></div>
    <div class="field-row"><span class="field-label">Mobile</span><span class="field-value">${farmer.mobile}</span></div>
    <div class="field-row"><span class="field-label">Father Name</span><span class="field-value">${farmer.father_name || "-"}</span></div>
    <div class="field-row"><span class="field-label">Farmer ID</span><span class="field-value">${farmer.farmer_id}</span></div>
    <div class="field-row"><span class="field-label">Gate Pass</span><span class="field-value">${gate_pass.gate_pass_id}</span></div>
    <div class="field-row"><span class="field-label">Crop</span><span class="field-value">${gate_pass.crop_name}</span></div>
    <div class="field-row"><span class="field-label">Crop Type</span><span class="field-value">${gate_pass.crop_type}</span></div>
    <div class="field-row"><span class="field-label">Estimated Weight</span><span class="field-value">${gate_pass.estimated_weight} Quintals</span></div>
    <div class="field-row"><span class="field-label">Vehicle Number</span><span class="field-value">${gate_pass.vehicle_number}</span></div>
    <div class="field-row"><span class="field-label">Selected Date</span><span class="field-value">${gate_pass.desired_date}</span></div>
    <div class="field-row"><span class="field-label">Queue Position</span><span class="field-value">${position ?? "-"}</span></div>
    <div class="field-row"><span class="field-label">Current Stage</span><span class="field-value">${stageBadgeHtml(stage)}</span></div>
  `;

  window.currentDetail = data;
  updateAdvanceButton(stage);
}

function updateAdvanceButton(currentStage) {
  const btn = document.getElementById("advance-btn");
  const currentIndex = STAGES.findIndex((s) => s.key === currentStage);

  if (currentIndex === STAGES.length - 1) {
    btn.style.display = "none";
    return;
  }

  const nextStage = STAGES[currentIndex + 1];
  btn.style.display = "block";
  btn.textContent = nextStage.key === "COMPLETED"
    ? "Mark as Completed"
    : `Move to ${nextStage.label}`;
}

async function advanceStage() {
  const msgBox = document.getElementById("detail-message");
  clearMessage(msgBox);

  const { gate_pass, stage } = window.currentDetail;
  const currentIndex = STAGES.findIndex((s) => s.key === stage);
  const nextStage = STAGES[currentIndex + 1];

  try {
    await apiPost("/stage/update", {
      gate_pass_id: gate_pass.gate_pass_id,
      new_stage: nextStage.key,
    });
    showMessage(msgBox, `Moved to ${nextStage.label}.`, "success");
    await openDetails(selectedFarmerId);
    await loadFarmers();
  } catch (err) {
    showMessage(msgBox, err.message);
  }
}

function closeDetails() {
  document.getElementById("detail-panel").style.display = "none";
  selectedFarmerId = null;
}

loadFarmers();

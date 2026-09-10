/* =========================================================
   queue.js
   Logic for queue.html: shows the farmer's live position and
   stage, and keeps it up to date using simple polling (no need
   for WebSockets in a prototype like this).
   ========================================================= */

const farmer = requireFarmerLogin();
const POLL_INTERVAL_MS = 5000;

async function loadQueue() {
  const msgBox = document.getElementById("queue-message");

  try {
    const data = await apiGet(`/queue/farmer/${farmer.farmer_id}`);
    clearMessage(msgBox);
    renderQueue(data);
  } catch (err) {
    document.getElementById("queue-card").style.display = "none";
    document.getElementById("progress-card").style.display = "none";
    showMessage(msgBox, err.message, "info");
  }
}

function renderQueue(data) {
  document.getElementById("queue-card").style.display = "block";
  document.getElementById("progress-card").style.display = "block";

  document.getElementById("q-gate-pass-id").textContent = data.gate_pass_id;
  document.getElementById("q-stage").innerHTML = stageBadgeHtml(data.stage);
  document.getElementById("q-ahead").textContent = data.farmers_ahead;
  document.getElementById("q-waiting").textContent = data.farmers_waiting;
  document.getElementById("q-position").textContent = data.position;

  renderProgress(data.stage);
}

function renderProgress(currentStage) {
  const currentIndex = STAGES.findIndex((s) => s.key === currentStage);
  const track = document.getElementById("progress-track");

  track.innerHTML = STAGES.map((stage, index) => {
    let stateClass = "";
    let symbol = String(index + 1);

    if (index < currentIndex) {
      stateClass = "done";
      symbol = "✓";
    } else if (index === currentIndex) {
      stateClass = "current";
      symbol = "●";
    }

    return `
      <div class="progress-step ${stateClass}">
        <div class="dot">${symbol}</div>
        <div class="label">${stage.label}</div>
      </div>
    `;
  }).join("");
}

loadQueue();
setInterval(loadQueue, POLL_INTERVAL_MS);

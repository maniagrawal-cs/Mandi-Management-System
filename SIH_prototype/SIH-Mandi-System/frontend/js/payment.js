/* =========================================================
   payment.js
   Logic for payment.html: shows payment status for the current
   gate pass, lets the farmer trigger a *simulated* payment once
   their crop has reached the STORAGE stage, shows payment
   history, and can display/print a receipt.

   NOTE: There is no real payment gateway here on purpose — this
   is a hackathon prototype. We use a simple dummy rate per
   quintal just so the demo has a realistic-looking amount.
   ========================================================= */

const farmer = requireFarmerLogin();
const DUMMY_RATE_PER_QUINTAL = 2000; // ₹ per quintal, for demo purposes only

let currentGatePass = null;
let currentPayment = null;

async function loadPaymentPage() {
  const msgBox = document.getElementById("payment-message");
  clearMessage(msgBox);

  // 1) Find the farmer's latest gate pass + stage.
  let queueInfo;
  try {
    queueInfo = await apiGet(`/queue/farmer/${farmer.farmer_id}`);
  } catch (err) {
    showMessage(msgBox, "You don't have a gate pass yet. Generate one first.", "info");
    document.getElementById("current-payment-card").style.display = "none";
  }

  if (queueInfo) {
    currentGatePass = await apiGet(`/gate-pass/${queueInfo.gate_pass_id}`);
    currentGatePass.stage = queueInfo.stage;
    renderCurrentPayment();
  }

  // 2) Load full payment history.
  await loadHistory();
}

function renderCurrentPayment() {
  const card = document.getElementById("current-payment-card");
  const body = document.getElementById("current-payment-body");
  card.style.display = "block";

  const estimatedAmount = Math.round(currentGatePass.estimated_weight * DUMMY_RATE_PER_QUINTAL);

  if (currentPayment) {
    body.innerHTML = `
      <div class="field-row"><span class="field-label">Payment Status</span>
        <span class="field-value" style="color: var(--green-dark);">Completed</span></div>
      <div class="field-row"><span class="field-label">Amount</span>
        <span class="field-value">₹${currentPayment.amount.toLocaleString("en-IN")}</span></div>
      <div class="field-row"><span class="field-label">Payment Date</span>
        <span class="field-value">${currentPayment.payment_date}</span></div>
      <div class="field-row"><span class="field-label">Transaction ID</span>
        <span class="field-value">${currentPayment.transaction_id}</span></div>
      <button class="btn" style="margin-top:14px;" onclick="showReceipt()">View Receipt</button>
    `;
  } else if (currentGatePass.stage === "STORAGE") {
    body.innerHTML = `
      <div class="field-row"><span class="field-label">Payment Status</span>
        <span class="field-value" style="color: var(--orange);">Pending</span></div>
      <div class="field-row"><span class="field-label">Estimated Amount</span>
        <span class="field-value">₹${estimatedAmount.toLocaleString("en-IN")}</span></div>
      <p class="page-subtitle">Your crop has reached the storage stage. Payment can now be processed.</p>
      <button class="btn" onclick="simulatePayment(${estimatedAmount})">Simulate Payment</button>
    `;
  } else {
    body.innerHTML = `
      <div class="field-row"><span class="field-label">Payment Status</span>
        <span class="field-value" style="color: var(--grey);">Not yet available</span></div>
      <p class="page-subtitle">
        Payment becomes available once your gate pass reaches the
        <b>Storage</b> stage. Current stage: ${stageBadgeHtml(currentGatePass.stage)}
      </p>
    `;
  }
}

async function simulatePayment(amount) {
  const msgBox = document.getElementById("payment-message");
  clearMessage(msgBox);
  try {
    const result = await apiPost("/payment", {
      gate_pass_id: currentGatePass.gate_pass_id,
      amount: amount,
    });
    currentPayment = result.payment;
    showMessage(msgBox, "Payment completed successfully!", "success");
    currentGatePass.stage = "PAYMENT";
    renderCurrentPayment();
    await loadHistory();
  } catch (err) {
    showMessage(msgBox, err.message);
  }
}

async function loadHistory() {
  const tbody = document.getElementById("history-body");
  try {
    const history = await apiGet(`/payment/history/${farmer.farmer_id}`);

    if (currentGatePass) {
      currentPayment = history.find((p) => p.gate_pass_id === currentGatePass.gate_pass_id) || null;
    }

    if (history.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="page-subtitle">No payments yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = history.map((p) => `
      <tr>
        <td>${p.payment_date}</td>
        <td>₹${p.amount.toLocaleString("en-IN")}</td>
        <td>${p.status}</td>
        <td>${p.transaction_id}</td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="page-subtitle">Could not load payment history.</td></tr>`;
  }
}

function showReceipt() {
  const receiptCard = document.getElementById("receipt-card");
  const body = document.getElementById("receipt-body");

  body.innerHTML = `
    <div class="field-row"><span class="field-label">Farmer Name</span><span class="field-value">${farmer.name}</span></div>
    <div class="field-row"><span class="field-label">Farmer ID</span><span class="field-value">${farmer.farmer_id}</span></div>
    <div class="field-row"><span class="field-label">Gate Pass ID</span><span class="field-value">${currentGatePass.gate_pass_id}</span></div>
    <div class="field-row"><span class="field-label">Crop Name</span><span class="field-value">${currentGatePass.crop_name}</span></div>
    <div class="field-row"><span class="field-label">Crop Type</span><span class="field-value">${currentGatePass.crop_type}</span></div>
    <div class="field-row"><span class="field-label">Estimated Weight</span><span class="field-value">${currentGatePass.estimated_weight} Quintals</span></div>
    <div class="field-row"><span class="field-label">Amount Paid</span><span class="field-value">₹${currentPayment.amount.toLocaleString("en-IN")}</span></div>
    <div class="field-row"><span class="field-label">Payment Date</span><span class="field-value">${currentPayment.payment_date}</span></div>
    <div class="field-row"><span class="field-label">Transaction ID</span><span class="field-value">${currentPayment.transaction_id}</span></div>
  `;

  receiptCard.style.display = "block";
  receiptCard.scrollIntoView({ behavior: "smooth" });
}

loadPaymentPage();

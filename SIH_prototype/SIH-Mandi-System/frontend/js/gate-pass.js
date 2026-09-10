/* =========================================================
   gate-pass.js
   Logic for gate-pass.html: pre-fills known farmer details,
   submits the form, checks storage capacity (server-side),
   and displays the resulting QR code.
   ========================================================= */

const farmer = requireFarmerLogin();

if (farmer) {
  document.getElementById("name").value = farmer.name;
  document.getElementById("mobile").value = farmer.mobile;
  document.getElementById("father_name").value = farmer.father_name || "";
}

async function submitGatePass() {
  const msgBox = document.getElementById("form-message");
  clearMessage(msgBox);

  const payload = {
    farmer_id: farmer.farmer_id,
    crop_type: document.getElementById("crop_type").value,
    crop_name: document.getElementById("crop_name").value.trim(),
    mandi: document.getElementById("mandi").value,
    vehicle_number: document.getElementById("vehicle_number").value.trim(),
    vehicle_type: document.getElementById("vehicle_type").value,
    desired_date: document.getElementById("desired_date").value,
    estimated_weight: parseFloat(document.getElementById("estimated_weight").value),
  };

  // Basic client-side checks (the backend validates everything again).
  if (!payload.crop_name || !payload.vehicle_number || !payload.desired_date) {
    showMessage(msgBox, "Please fill in all required fields.");
    return;
  }
  if (!payload.estimated_weight || payload.estimated_weight <= 0) {
    showMessage(msgBox, "Please enter a valid estimated weight.");
    return;
  }

  try {
    const result = await apiPost("/gate-pass", payload);
    await showSuccess(result.gate_pass_id);
  } catch (err) {
    showMessage(msgBox, err.message);
  }
}

async function showSuccess(gatePassId) {
  document.getElementById("form-section").style.display = "none";
  document.getElementById("success-section").style.display = "block";
  document.getElementById("result-gate-pass-id").textContent = gatePassId;

  try {
    const qrData = await apiGet(`/gate-pass/${gatePassId}/qr`);
    document.getElementById("qr-image").src = qrData.qr_code;
  } catch (err) {
    // Non-fatal: the gate pass was still created successfully.
    console.error("Could not load QR code:", err);
  }
}

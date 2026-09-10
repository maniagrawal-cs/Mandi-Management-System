/* =========================================================
   farmer.js
   Logic for farmer.html (the farmer dashboard landing page).
   ========================================================= */

const farmer = requireFarmerLogin();

if (farmer) {
  document.getElementById("welcome-text").textContent = `Welcome, ${farmer.name}`;
}

// dashboard.js
import { supabase } from "./supabaseClient.js";

/**
 * Fetch farmer and field data for the logged-in user
 */
async function getFarmerFieldData() {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    console.warn("No user logged in");
    return null;
  }

  const { data: farmer } = await supabase
    .from("farmers")
    .select("id, name, language")
    .eq("user_id", user.id)
    .single();

  const { data: field } = await supabase
    .from("fields")
    .select("id, area, soil_type, latitude, longitude")
    .eq("farmer_id", farmer.id)
    .single();

  return { farmer, field };
}

/**
 * Handle crop recommendation
 */
async function handleRecommend() {
  const cropType = document.getElementById("recCropType").value;
  const sowingDate = document.getElementById("recSowingDate").value;
  const n = document.getElementById("recNitrogen").value || null;
  const p = document.getElementById("recPhosphorus").value || null;
  const k = document.getElementById("recPotassium").value || null;

  const { field } = await getFarmerFieldData();
  if (!field) {
    alert("No field info found. Please re-register your field.");
    return;
  }

  const payload = {
    crop_type: cropType,
    lat: field.latitude,
    lon: field.longitude,
    sowing_date: sowingDate,
    n: n ? parseFloat(n) : null,
    p: p ? parseFloat(p) : null,
    k: k ? parseFloat(k) : null,
  };

  try {
    const res = await fetch("http://127.0.0.1:8000/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    const recDiv = document.getElementById("recResult");
    recDiv.innerHTML = `
      <h3>Crop Recommendation Result</h3>
      <p><strong>Recommended Crop:</strong> ${data.recommended_crop}</p>
      <p><strong>NDVI:</strong> ${data.ndvi ?? "N/A"}</p>
      <p><strong>Temperature:</strong> ${data.weather.temperature ?? "N/A"} °C</p>
      <p><strong>Humidity:</strong> ${data.weather.humidity ?? "N/A"}%</p>
      <p><strong>Rainfall:</strong> ${data.weather.rainfall ?? "N/A"} mm</p>
      <p><strong>Conditions:</strong> ${data.weather.description ?? "N/A"}</p>
    `;
    recDiv.classList.remove("hidden");
  } catch (err) {
    console.error("Recommendation error:", err);
    alert("Could not get recommendation. Check backend connection.");
  }
}

/**
 * Handle suitability check
 */
async function handleSuitability() {
  const cropType = document.getElementById("suitCropType").value;
  if (!cropType) {
    alert("Select a crop type first!");
    return;
  }

  const { field } = await getFarmerFieldData();

  try {
    const res = await fetch("http://127.0.0.1:8000/suitability", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        crop_type: cropType,
        lat: field.latitude,
        lon: field.longitude,
      }),
    });
    const data = await res.json();

    const suitDiv = document.getElementById("suitResult");
    suitDiv.innerHTML = `
      <h3>Suitability Result</h3>
      <p><strong>Suitability:</strong> ${data.suitability ?? "N/A"}</p>
      <p><strong>Score:</strong> ${data.score ?? "N/A"}%</p>
      <p><strong>Reason:</strong> ${data.reason ?? "N/A"}</p>
    `;
    suitDiv.classList.remove("hidden");
  } catch (err) {
    console.error("Suitability error:", err);
    alert("Could not get suitability. Check backend connection.");
  }
}

/**
 * Dashboard initialization
 */
document.addEventListener("DOMContentLoaded", async () => {
  const { farmer, field } = (await getFarmerFieldData()) || {};

  if (farmer) {
    document.getElementById("userName").textContent = farmer.name;
  }

  if (field) {
    const info = document.createElement("div");
    info.classList.add("field-summary");
    info.innerHTML = `
      <p><strong>Soil Type:</strong> ${field.soil_type}</p>
      <p><strong>Area:</strong> ${field.area}</p>
      <p><strong>Coordinates:</strong> ${field.latitude}, ${field.longitude}</p>
    `;
    const container = document.querySelector(".dashboard-container");
    container.prepend(info);
  }

  // attach event listeners
  document
    .getElementById("recommendBtn")
    ?.addEventListener("click", handleRecommend);
  document
    .getElementById("suitabilityBtn")
    ?.addEventListener("click", handleSuitability);
});

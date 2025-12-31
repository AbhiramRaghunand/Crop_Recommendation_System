import { supabase } from './supabaseClient.js';
// import { loadAdviceOnLogin } from "./dashboard.js";   // ✅ IMPORTANT FIX

// Helper to switch sections
function showPage(pageId) {
  const pages = ['landingPage', 'signupPage', 'loginPage', 'dashboardPage'];
  pages.forEach(page => {
    const el = document.getElementById(page);
    if (el) el.classList.toggle('hidden', page !== pageId);
  });
}

// SIGNUP
export async function handleSignup() {
  const name = document.getElementById('signupName').value;
  const phone = document.getElementById('signupPhone').value;
  const password = document.getElementById('signupPassword').value;
  const language = document.getElementById('signupLanguage').value;
  const latitude = document.getElementById('signupLatitude').value;
  const longitude = document.getElementById('signupLongitude').value;
  const soilType = document.getElementById('signupSoilType').value;
  const area = document.getElementById('signupFarmArea').value;
  const errorDiv = document.getElementById('signupError');

  errorDiv.classList.add('hidden');

  // REQUIRED FIELDS (Option 2)
  if (!name || !phone || !password || !soilType || !area || !latitude || !longitude) {
    errorDiv.textContent = "All fields including location must be filled.";
    errorDiv.classList.remove('hidden');
    return;
  }

  if (!/^\d{10}$/.test(phone)) {
    errorDiv.textContent = "Phone number must be exactly 10 digits.";
    errorDiv.classList.remove('hidden');
    return;
  }

  const email = `${phone}@cropwise.local`;

  // Supabase signup
  const { data, error } = await supabase.auth.signUp({ email, password });
  if (error) {
    errorDiv.textContent = error.message;
    errorDiv.classList.remove('hidden');
    return;
  }

  const user = data.user;

  // Insert farmer
  const { error: insertError } = await supabase.from('farmers').insert([
    { user_id: user.id, name, phone, language }
  ]);

  if (insertError) {
    errorDiv.textContent = insertError.message;
    errorDiv.classList.remove('hidden');
    return;
  }

  // Create default field
  const { data: farmer } = await supabase
    .from('farmers')
    .select('id')
    .eq('user_id', user.id)
    .single();

  await supabase.from('fields').insert([
    {
      farmer_id: farmer.id,
      area,
      soil_type: soilType,
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude)
    }
  ]);

  alert("Signup successful! Please log in.");
  showPage("loginPage");
}

// LOGIN
export async function handleLogin() {
  const phone = document.getElementById('loginPhone').value;
  const password = document.getElementById('loginPassword').value;
  const errorDiv = document.getElementById('loginError');
  errorDiv.classList.add('hidden');

  if (!phone || !password) {
    errorDiv.textContent = "Please fill all fields.";
    errorDiv.classList.remove('hidden');
    return;
  }

  const email = `${phone}@cropwise.local`;

  const { data, error } = await supabase.auth.signInWithPassword({ email, password });

  if (error) {
    errorDiv.textContent = error.message;
    errorDiv.classList.remove('hidden');
    return;
  }

  const accessToken = data.session?.access_token;
  const user = data.user;

  localStorage.setItem("token", accessToken);
  localStorage.setItem("user_id", user.id);

  // Fetch farmer name for dashboard
  const { data: farmer } = await supabase
    .from("farmers")
    .select("name")
    .eq("user_id", user.id)
    .single();

  if (farmer?.language) {
  localStorage.setItem("language", farmer.language);
}
  document.getElementById("userName").textContent = farmer?.name || "Farmer";

  showPage("dashboardPage");

  // 🔥 Ensure advice loads once dashboard is visible
localStorage.setItem("just_logged_in", "true");

}

// LOGOUT
export async function handleLogout() {
  await supabase.auth.signOut();
  localStorage.clear();
  showPage("landingPage");
}

// AUTO LOGIN ON REFRESH
document.addEventListener("DOMContentLoaded", async () => {
  const { data: { user } } = await supabase.auth.getUser();
  if (user) {
    const { data: farmer } = await supabase
      .from("farmers")
      .select("name")
      .eq("user_id", user.id)
      .single();

    document.getElementById("userName").textContent = farmer?.name || "";
    showPage("dashboardPage");

    // Load advice on refresh
    // setTimeout(() => loadAdviceOnLogin(), 200);
  }

  // LOCATION HANDLER
  const detectBtn = document.getElementById("detectLocationBtn");
  const statusDiv = document.getElementById("locationStatus");

  if (detectBtn) {
    detectBtn.addEventListener('click', () => {
      statusDiv.textContent = "Requesting location...";
      statusDiv.style.color = "#374151";

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude.toFixed(6);
          const lon = pos.coords.longitude.toFixed(6);

          document.getElementById("signupLatitude").value = lat;
          document.getElementById("signupLongitude").value = lon;

          statusDiv.textContent = `✅ Detected (Lat: ${lat}, Lon: ${lon})`;
          statusDiv.style.color = "#16a34a";
        },
        () => {
          statusDiv.textContent = "Unable to detect location. Try again.";
          statusDiv.style.color = "#dc2626";
        }
      );
    });
  }
});

// NAV BUTTONS
window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("navSignupBtn")?.addEventListener("click", () => showPage("signupPage"));
  document.getElementById("navLoginBtn")?.addEventListener("click", () => showPage("loginPage"));
  document.getElementById("getStartedBtn")?.addEventListener("click", () => showPage("signupPage"));
  document.getElementById("goToLoginBtn")?.addEventListener("click", () => showPage("loginPage"));
  document.getElementById("goToSignupBtn")?.addEventListener("click", () => showPage("signupPage"));

  document.getElementById("signupBtn")?.addEventListener("click", handleSignup);
  document.getElementById("loginBtn")?.addEventListener("click", handleLogin);
  document.getElementById("logoutBtn")?.addEventListener("click", handleLogout);
});

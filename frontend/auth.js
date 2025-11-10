// auth.js
import { supabase } from './supabaseClient.js';

// Helper to switch visible page sections
function showPage(pageId) {
  const pages = ['landingPage', 'signupPage', 'loginPage', 'dashboardPage'];
  pages.forEach(page => {
    const element = document.getElementById(page);
    if (element) element.classList.toggle('hidden', page !== pageId);
  });
}

// ✅ SIGNUP
export async function handleSignup() {
  const name = document.getElementById('signupName').value;
  const phone = document.getElementById('signupPhone').value;
  const password = document.getElementById('signupPassword').value;
  const language = document.getElementById('signupLanguage').value;
  const latitude = document.getElementById('signupLatitude').value || null;
  const longitude = document.getElementById('signupLongitude').value || null;
  const soilType = document.getElementById('signupSoilType').value;
  const area = document.getElementById('signupFarmArea').value;
  const errorDiv = document.getElementById('signupError');

  errorDiv.classList.add('hidden');

  // 🧩 Check for missing fields
  if (!name || !phone || !password || !location || !soilType || !area) {
    errorDiv.textContent = 'Please fill all fields';
    errorDiv.classList.remove('hidden');
    return;
  }

  // 🧩 Phone validation (10 digits only)
  if (!/^\d{10}$/.test(phone)) {
    errorDiv.textContent = 'Phone number must be exactly 10 digits';
    errorDiv.classList.remove('hidden');
    return;
  }

  const email = `${phone}@cropwise.local`;

  // 1️⃣ Sign up user
  const { data, error } = await supabase.auth.signUp({ email, password });
  if (error) {
    errorDiv.textContent = error.message;
    errorDiv.classList.remove('hidden');
    return;
  }

  const user = data.user;

  // 2️⃣ Insert into farmers table
  const { error: insertError } = await supabase.from('farmers').insert([{
    user_id: user.id,
    name,
    phone,
    // region: location,
    language: language,
  }]);

  if (insertError) {
    errorDiv.textContent = insertError.message;
    errorDiv.classList.remove('hidden');
    return;
  }

  // 3️⃣ Create default field for farmer
  const { data: farmer } = await supabase
    .from('farmers')
    .select('id')
    .eq('user_id', user.id)
    .single();

  await supabase.from('fields').insert([{
    farmer_id: farmer.id,
    area: area,
    soil_type: soilType,
    latitude: latitude ? parseFloat(latitude) : null,
    longitude: longitude ? parseFloat(longitude) : null
  }]);

  alert('Signup successful! You can now log in.');
  showPage('loginPage');
}


// ✅ LOGIN
export async function handleLogin() {
  const phone = document.getElementById('loginPhone').value;
  const password = document.getElementById('loginPassword').value;
  const errorDiv = document.getElementById('loginError');

  errorDiv.classList.add('hidden');

  if (!phone || !password) {
    errorDiv.textContent = 'Please fill all fields';
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

  const user = data.user;

  // Fetch farmer info for dashboard
  const { data: farmer } = await supabase
    .from('farmers')
    .select('name')
    .eq('user_id', user.id)
    .single();

  document.getElementById('userName').textContent = farmer.name;
  showPage('dashboardPage');
}

// ✅ LOGOUT
export async function handleLogout() {
  await supabase.auth.signOut();
  showPage('landingPage');
}

// ✅ AUTO LOGIN CHECK
document.addEventListener('DOMContentLoaded', async () => {
  const { data: { user } } = await supabase.auth.getUser();

  if (user) {
    const { data: farmer } = await supabase
      .from('farmers')
      .select('name')
      .eq('user_id', user.id)
      .single();

    document.getElementById('userName').textContent = farmer?.name || '';
    showPage('dashboardPage');
  } else {
    showPage('landingPage');
  }

  // 🌍 Detect user's current location when button is clicked
  const detectBtn = document.getElementById('detectLocationBtn');
  const statusDiv = document.getElementById('locationStatus');
  const latInput = document.getElementById('signupLatitude');
  const lonInput = document.getElementById('signupLongitude');

  if (detectBtn) {
    detectBtn.addEventListener('click', () => {
      statusDiv.textContent = 'Requesting location permission…';
      statusDiv.style.color = '#374151';

      if (!navigator.geolocation) {
        statusDiv.textContent = 'Geolocation not supported by this browser.';
        statusDiv.style.color = '#dc2626';
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude.toFixed(6);
          const lon = pos.coords.longitude.toFixed(6);

          latInput.value = lat;
          lonInput.value = lon;

          statusDiv.textContent = `✅ Location detected (Lat: ${lat}, Lon: ${lon})`;
          statusDiv.style.color = '#16a34a';
        },
        (err) => {
          console.error('Geolocation error', err);
          if (err.code === err.PERMISSION_DENIED) {
            statusDiv.textContent = 'Permission denied. Please allow location access.';
          } else {
            statusDiv.textContent = 'Unable to detect location. Try again.';
          }
          statusDiv.style.color = '#dc2626';
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    });
  }
});


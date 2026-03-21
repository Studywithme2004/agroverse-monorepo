// AgroVerse v6 - frontend-only

const USERS_KEY='ag_users', CROPS_KEY='ag_crops', REPORTS_KEY='ag_reports', SESSION_KEY='ag_session';
const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from((r||document).querySelectorAll(s));
const read = k => JSON.parse(localStorage.getItem(k)||'null');
const write = (k,v) => localStorage.setItem(k, JSON.stringify(v));
const uid = (p='id') => p + '-' + Math.floor(1000+Math.random()*9000);

function seedAll() {
  console.log("Seeding data...");

  if (!localStorage.getItem(USERS_KEY)) {
    write(USERS_KEY, [
      { email: "farmer@example.com", password: "12345", role: "farmer", name: "Demo Farmer" },
      { email: "admin@example.com", password: "admin123", role: "admin", name: "Demo Admin" }
    ]);
  }

  let crops = window.defaultCrops || [];

  if (!localStorage.getItem(CROPS_KEY) || read(CROPS_KEY)?.length === 0) {
    write(CROPS_KEY, crops);
  }

  if (!localStorage.getItem(REPORTS_KEY)) {
    write(REPORTS_KEY, []);
  }
}

// ------------------ FARMER DASHBOARD ------------------

function initFarmer(){
  seedAll();

  const sess = read(SESSION_KEY);
  if(!sess) return location.href='login.html';

  $('#logout').addEventListener('click', ()=> {
    localStorage.removeItem(SESSION_KEY);
    location.href='index.html';
  });

  renderCropGrid();
}

// ✅ KEEP YOUR ORIGINAL CARDS (ONLY FIX LINK)
function renderCropGrid(){
  const grid = $('#cropGrid');
  if (!grid) return;

  grid.innerHTML = '';
  const crops = read(CROPS_KEY) || [];

  crops.forEach(c=>{
    const card = document.createElement('div');
    card.className = 'card crop-card';

    card.innerHTML = `
      <img src="${c.image}" alt="${c.name}">
      <div class="body">
        <div class="crop-title">${c.name}</div>
        <div class="muted small">
          Health: ${rand(60,99)}% · Moisture: ${rand(20,90)}% · Temp: ${rand(18,32)}°C
        </div>
        <div class="controls">
          <!-- ✅ PASS NAME INSTEAD OF ID -->
          <a class="btn" href="crop-report.html?crop=${encodeURIComponent(c.name)}">
            View Report
          </a>
        </div>
      </div>
    `;

    grid.appendChild(card);
  });
}

// ------------------ REPORT PAGE ------------------

function initReport(){
  seedAll();

  const params = new URLSearchParams(location.search);
  const plant = params.get('crop') || "Tomato";

  loadAIReport(plant);
}

// ✅ FETCH AI + SENSOR DATA
async function loadAIReport(plant){
  const API = "https://agroverse-monorepo.onrender.com";

  try{
    const res = await fetch(`${API}/api/analyze-crop`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ plant })
    });

    const data = await res.json();

    if(!data.sensor_data){
      throw new Error("No sensor data");
    }

    // ✅ UPDATE UI
    document.getElementById("cropName").innerText = `${plant} Crop Report`;

    document.getElementById("cropHealth").innerText =
      `Temperature: ${data.sensor_data.temperature}°C | ` +
      `Humidity: ${data.sensor_data.humidity}% | ` +
      `Soil: ${data.sensor_data.soil_moisture} | ` +
      `Sunlight: ${data.sensor_data.sunlight} lux`;

    document.getElementById("cropSuggestion").innerText =
      data.analysis || "No AI response";

  }catch(err){
    console.error(err);

    document.getElementById("cropName").innerText = "Error loading report";
    document.getElementById("cropSuggestion").innerText = "AI unavailable";
  }
}

// ------------------ ADMIN ------------------

function initAdmin(){
  seedAll();

  const sess = read(SESSION_KEY);
  if(!sess) return location.href='login.html';

  $('#alogout').addEventListener('click', ()=> {
    localStorage.removeItem(SESSION_KEY);
    location.href='index.html';
  });

  renderAdmin();
}

function renderAdmin(){
  const list = $('#adminCropList');
  if (!list) return;

  list.innerHTML='';

  const crops = read(CROPS_KEY)||[];

  crops.forEach(c=>{
    const d=document.createElement('div');
    d.className='card';

    d.innerHTML = `
      <div style="display:flex;justify-content:space-between">
        <strong>${c.name}</strong>
        <button class="btn rem" data-id="${c.id}">Delete</button>
      </div>
    `;

    list.appendChild(d);
  });

  $$('.rem').forEach(b=>{
    b.addEventListener('click', ()=>{
      let crops=read(CROPS_KEY)||[];
      crops=crops.filter(x=>x.id!==b.dataset.id);
      write(CROPS_KEY,crops);
      renderAdmin();
      renderCropGrid();
    });
  });
}

// ------------------ UTILS ------------------

function rand(a,b){
  return Math.floor(a + Math.random()*(b-a+1));
}

// ------------------ INIT ------------------

document.addEventListener('DOMContentLoaded', ()=>{
  seedAll();

  const path = location.pathname.split('/').pop();

  if(path === '' || path === 'farmer-dashboard.html') initFarmer();
  if(path === 'admin-dashboard.html') initAdmin();
  if(path === 'crop-report.html') initReport();
});

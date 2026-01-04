// AgroVerse v6 - frontend-only
//window.onload = function() {
    // your script.js code here


const USERS_KEY='ag_users', CROPS_KEY='ag_crops', REPORTS_KEY='ag_reports', SESSION_KEY='ag_session';
const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from((r||document).querySelectorAll(s));
const read = k => JSON.parse(localStorage.getItem(k)||'null');
const write = (k,v) => localStorage.setItem(k, JSON.stringify(v));
const uid = (p='id') => p + '-' + Math.floor(1000+Math.random()*9000);
const now = ()=> new Date().toISOString();
let corps = [];
let crops = window.defaultCrops || [];

console.log(corps);




function seedAll(){
  if(!localStorage.getItem(USERS_KEY)){
    write(USERS_KEY, [
      {email:'farmer@example.com', password:'12345', role:'farmer', name:'Demo Farmer'},
      {email:'admin@example.com', password:'admin123', role:'admin', name:'Demo Admin'}
    ]);
  }
     if (!localStorage.getItem(CROPS_KEY)) {
  let crops = window.defaultCrops || [];
  write(CROPS_KEY, crops);


   //if(!localStorage.getItem(CROPS_KEY)){
  //write(CROPS_KEY, defaultCrops);
}

  }
  if(!localStorage.getItem(REPORTS_KEY)){
    write(REPORTS_KEY, []);
  }


function fetchSync(path){
  try{
    const xhr = new XMLHttpRequest();
    xhr.open('GET', path, false);
    xhr.send(null);
    if(xhr.status === 200 || xhr.status === 0) return xhr.responseText;
    return '[]';
  }catch(e){ return '[]'; }
}

(function bindAuth(){
  const login = $('#loginForm');
  if(login){
    login.addEventListener('submit', e=>{
      e.preventDefault();
      const em = $('#email').value.trim();
      const pw = $('#password').value;
      const users = read(USERS_KEY) || [];
      const u = users.find(x=> x.email === em && x.password === pw);
      if(!u){ alert('Invalid credentials'); return; }
      write(SESSION_KEY, {email:u.email, role:u.role, name:u.name});
      if(u.role === 'admin') location.href = 'admin-dashboard.html';
      else location.href = 'farmer-dashboard.html';
    });
  }
  const signup = $('#signupForm');
  if(signup){
    signup.addEventListener('submit', e=>{
      e.preventDefault();
      const name = $('#fullname').value.trim();
      const email = $('#su_email').value.trim();
      const pw = $('#su_password').value;
      let users = read(USERS_KEY) || [];
      if(users.find(x=>x.email === email)){ $('#signupMsg').textContent = 'Email exists'; return; }
      users.push({email, password: pw, role:'farmer', name});
      write(USERS_KEY, users);
      $('#signupMsg').textContent = 'Account created. Redirecting...';
      setTimeout(()=> location.href = 'login.html', 800);
    });
  }
})();

function initFarmer(){
  seedAll();
  const sess = read(SESSION_KEY); if(!sess) return location.href='login.html';
  $('#logout').addEventListener('click', ()=> { localStorage.removeItem(SESSION_KEY); location.href='index.html'; });
  renderCropGrid();
  bindChat('#chatToggle','#chatPanel','#chatBody','#chatInput','#sendChat');
}
function initAdmin(){
  seedAll();
  const sess = read(SESSION_KEY); if(!sess) return location.href='login.html';
  $('#alogout').addEventListener('click', ()=> { localStorage.removeItem(SESSION_KEY); location.href='index.html'; });
  renderAdmin();
  bindChat('#chatToggleAdmin','#chatPanelAdmin','#chatBodyAdmin','#chatInputAdmin','#sendChatAdmin');
  $('#addCrop').addEventListener('click', ()=>{
    const name = $('#adminCropName').value.trim(); const img = $('#adminCropImage').value.trim();
    if(!name) return alert('Name required');
    const crops = read(CROPS_KEY) || []; crops.push({id: uid('crop'), name, image: img}); write(CROPS_KEY, crops); renderAdmin(); renderCropGrid();
  });
  $('#resetData').addEventListener('click', ()=>{ if(confirm('Reset demo data?')){ localStorage.removeItem(CROPS_KEY); localStorage.removeItem(REPORTS_KEY); seedAll(); renderAdmin(); renderCropGrid(); } });
}

function renderCropGrid(){
  const grid = $('#cropGrid');
  grid.innerHTML = '';
  const crops = read(CROPS_KEY) || [];
  crops.forEach(c=>{
    const card = document.createElement('div'); card.className = 'card crop-card';
    card.innerHTML = `<img src="${c.image}" alt="${c.name}"><div class="body"><div class="crop-title">${c.name}</div><div class="muted small">Health: ${rand(60,99)}% · Moisture: ${rand(20,90)}% · Temp: ${rand(18,32)}°C</div><div class="controls"><a class="btn" href="crop-report.html?crop=${encodeURIComponent(c.id)}">View Report</a></div></div>`;
    grid.appendChild(card);
  });
}

function renderAdmin(){
  const list = $('#adminCropList'); list.innerHTML=''; const crops = read(CROPS_KEY)||[];
  crops.forEach(c=>{ const d=document.createElement('div'); d.className='card'; d.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center"><div><strong>${c.name}</strong></div><div class="row"><button class="btn ghost rem" data-id="${c.id}">Delete</button></div></div>`; list.appendChild(d); });
  $$('.rem').forEach(b=> b.addEventListener('click', ()=>{ if(confirm('Delete crop?')){ let crops=read(CROPS_KEY)||[]; crops=crops.filter(x=>x.id!==b.dataset.id); write(CROPS_KEY,crops); renderAdmin(); renderCropGrid(); } }));
}

function initReport(){
  seedAll();
  const params = new URLSearchParams(location.search); const cropId = params.get('crop');
  const crops = read(CROPS_KEY)||[]; const crop = crops.find(c=>c.id===cropId) || crops[0];
  document.getElementById('reportHeader').innerHTML = `<h3>${crop.name} — Report</h3><p class="muted">Generated sample data</p>`;
  const days = 30; const labels = []; const moisture=[]; const temp=[];
  for(let i=days-1;i>=0;i--){ const d = new Date(); d.setDate(d.getDate()-i); labels.push(d.toLocaleDateString()); moisture.push(rand(20,90)); temp.push(rand(16,34)); }
  try{
    const ctx1 = document.getElementById('chart1').getContext('2d'); new Chart(ctx1,{type:'line',data:{labels, datasets:[{label:'Moisture %',data:moisture,borderColor:'#19a34a',backgroundColor:'rgba(25,163,74,0.12)'}]}, options:{animation:false}});
    const ctx2 = document.getElementById('chart2').getContext('2d'); new Chart(ctx2,{type:'line',data:{labels, datasets:[{label:'Temperature °C',data:temp,borderColor:'#ff8a3d'}]}, options:{animation:false}});
  }catch(e){}
  bindChat('#chatToggleRpt','#chatPanelRpt','#chatBodyRpt','#chatInputRpt','#sendChatRpt');
  document.getElementById('downloadPdf')?.addEventListener('click', ()=>{ try{ const { jsPDF } = window.jspdf; const doc = new jsPDF(); doc.text('AgroVerse Report',14,20); doc.text(`${crop.name} report`,14,30); doc.save(`${crop.id}-report.pdf`); }catch(e){alert('PDF error');} });
}

function bindChat(toggleSel, panelSel, bodySel, inputSel, sendSel){
  const toggle = document.querySelector(toggleSel); const panel = document.querySelector(panelSel); const body = document.querySelector(bodySel); const input = document.querySelector(inputSel); const send = document.querySelector(sendSel);
  if(!toggle) return;
  toggle.addEventListener('click', ()=> { panel.style.display = panel.style.display === 'none' ? 'block' : 'none'; });
  if(send) send.addEventListener('click', async ()=> { const q = input.value.trim(); if(!q) return; appendUser(body,q); input.value=''; appendBot(body,'Thinking...'); const ctx = { latest: [], crop: null }; try{ const ans = await window.Ai.ask(q, ctx); replaceLastBot(body, ans); }catch(e){ replaceLastBot(body, 'AI error'); } });
}

function appendUser(body,text){ const el = document.createElement('div'); el.className='msg-user'; el.textContent = text; body.appendChild(el); body.scrollTop = body.scrollHeight; }
function appendBot(body,text){ const el = document.createElement('div'); el.className='msg-bot'; el.textContent = text; body.appendChild(el); body.scrollTop = body.scrollHeight; }
function replaceLastBot(body,text){ const bots = body.querySelectorAll('.msg-bot'); if(!bots.length) appendBot(body,text); else bots[bots.length-1].textContent = text; body.scrollTop = body.scrollHeight; }
function rand(a,b){ return Math.floor(a + Math.random()*(b-a+1)); }

document.addEventListener('DOMContentLoaded', ()=>{
  seedAll();
  if(document.body.classList.contains('auth-page')) return;
  const path = location.pathname.split('/').pop();
  if(path === '' || path === 'farmer-dashboard1.html') initFarmer();
  if(path === 'admin-dashboard.html') initAdmin();
  if(path === 'crop-report.html') initReport();
});

document.addEventListener('DOMContentLoaded', () => {
  // Bind new AI chat panel
  const aiBtn = document.getElementById('ai-chat-button');
  const aiPanel = document.getElementById('ai-chat-panel');
  const aiClose = document.getElementById('ai-chat-close');
  const aiMessages = document.getElementById('ai-chat-messages');
  const aiInput = document.getElementById('ai-chat-input');
  const aiSend = document.getElementById('ai-chat-send');

  if (!aiBtn || !aiPanel || !aiClose || !aiMessages || !aiInput || !aiSend) {
    console.warn('AI chat elements not found in DOM');
    return; // exit if any element is missing
  }

  aiBtn.addEventListener('click', () => { aiPanel.style.display = 'block'; });
  aiClose.addEventListener('click', () => { aiPanel.style.display = 'none'; });

  aiSend.addEventListener('click', async () => {
    const msg = aiInput.value.trim();
    if (!msg) return;

    const userMsg = document.createElement('div');
    userMsg.className = 'msg-user';
    userMsg.textContent = msg;
    aiMessages.appendChild(userMsg);
    aiMessages.scrollTop = aiMessages.scrollHeight;
    aiInput.value = '';

    const botMsg = document.createElement('div');
    botMsg.className = 'msg-bot';
    botMsg.textContent = 'Thinking...';
    aiMessages.appendChild(botMsg);
    aiMessages.scrollTop = aiMessages.scrollHeight;

    try {
      if (window.Ai && typeof window.Ai.ask === 'function') {
        const ans = await window.Ai.ask(msg, { latest: [], crop: null });
        botMsg.textContent = ans;
      } else {
        botMsg.textContent = 'AI not loaded';
      }
    } catch (e) {
      botMsg.textContent = 'AI error';
    }
  });
});




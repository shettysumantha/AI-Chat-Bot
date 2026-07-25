const messages = document.getElementById('chatMessages');
const form = document.getElementById('chatForm');
const input = document.getElementById('messageInput');
let messageCount = 2;

function safeText(text) { const el = document.createElement('div'); el.textContent = text; return el.innerHTML; }
function clock() { return new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }); }
function addMessage(text, type, name = type === 'bot' ? 'Nexa AI' : 'You') {
  const article = document.createElement('article'); article.className = `message ${type}-message`;
  const avatar = type === 'bot' ? '<div class="bot-avatar">✦</div>' : '<div class="avatar small">SK</div>';
  article.innerHTML = `${avatar}<div class="message-content"><div class="message-meta"><strong>${name}</strong><time>${clock()}</time></div><div class="bubble">${safeText(text)}</div></div>`;
  messages.appendChild(article); messages.scrollTop = messages.scrollHeight;
}
function updateStats(amount = 1) { messageCount += amount; document.getElementById('messageCount').textContent = messageCount; }
async function sendMessage(text) {
  const message = (text || input.value).trim(); if (!message) return;
  addMessage(message, 'user'); updateStats(); input.value = ''; input.style.height = '23px';
  const button = form.querySelector('.send-button'); button.disabled = true;
  const typing = document.createElement('article'); typing.className = 'message bot-message'; typing.innerHTML = '<div class="bot-avatar">✦</div><div class="message-content"><div class="message-meta"><strong>Nexa AI</strong><time>Thinking…</time></div><div class="bubble">•••</div></div>'; messages.appendChild(typing); messages.scrollTop = messages.scrollHeight;
  try { const response = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message})}); const data = await response.json(); typing.remove(); addMessage(data.response || 'I’m here to help. Could you try again?', 'bot'); }
  catch { typing.remove(); addMessage('I’m having trouble connecting right now. Please try again in a moment.', 'bot'); }
  finally { button.disabled = false; updateStats(); input.focus(); }
}
form.addEventListener('submit', e => { e.preventDefault(); sendMessage(); });
input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
input.addEventListener('input', () => { input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 90) + 'px'; });
document.querySelectorAll('[data-prompt]').forEach(btn => btn.addEventListener('click', () => sendMessage(btn.dataset.prompt)));
document.getElementById('newChat').addEventListener('click', () => { messages.innerHTML = ''; addMessage('Fresh start! What would you like to explore today?', 'bot'); document.getElementById('conversationCount').textContent = Number(document.getElementById('conversationCount').textContent) + 1; input.focus(); });
document.querySelectorAll('[data-view]').forEach(link => link.addEventListener('click', e => {
  e.preventDefault();
  const view = link.dataset.view || 'chat';
  const available = ['chat','analytics','knowledge','settings'];
  available.forEach(v => {
    const el = document.getElementById(`${v}View`);
    if (el) el.classList.toggle('hidden', v !== view);
  });
  document.querySelectorAll('[data-view]').forEach(x => x.classList.toggle('active', x === link));
}));

// Auth UI and actions
async function loadCurrentUser(){
  try{
    const res = await fetch('/me');
    const data = await res.json();
    const user = data.user;
    const userBar = document.getElementById('userBar');
    if(user){
      userBar.innerHTML = `<div class="profile-inline"><img src="${user.photo||'/static/default-avatar.png'}" alt="avatar" class="avatar small"> <strong>${user.name}</strong> <button id="logoutBtn">Logout</button></div>`;
      document.getElementById('settingsView').querySelector('.card').innerHTML = `<h3>Settings</h3><div class="profile-card"><img src="${user.photo||'/static/default-avatar.png'}" class="avatar large"><p><strong>${user.name}</strong></p><p>${user.email}</p><p>${user.phone||''}</p><form id="photoForm"><input type="file" name="photo" id="photoInput"><button type="submit">Upload photo</button></form></div>`;
      document.getElementById('logoutBtn').addEventListener('click', async ()=>{ await fetch('/logout',{method:'POST'}); window.location.reload(); });
      // photo upload
      const photoForm = document.getElementById('photoForm');
      if(photoForm){
        photoForm.addEventListener('submit', async e=>{ e.preventDefault(); const file = document.getElementById('photoInput').files[0]; if(!file) return; const fd=new FormData(); fd.append('photo',file); const r = await fetch('/upload_photo',{method:'POST', body:fd}); const j=await r.json(); if(j.photo){ loadCurrentUser(); }
        });
      }
    } else {
      userBar.innerHTML = `<div class="profile-inline"><button id="openLogin">Login</button> <button id="openRegister">Register</button></div>`;
      document.getElementById('openLogin').addEventListener('click', ()=>{ document.getElementById('loginView').classList.remove('hidden'); });
      document.getElementById('openRegister').addEventListener('click', ()=>{ document.getElementById('registerView').classList.remove('hidden'); });
    }
  }catch(e){ console.log(e); }
}

document.getElementById('showRegister')?.addEventListener('click', e=>{ e.preventDefault(); document.getElementById('loginView').classList.add('hidden'); document.getElementById('registerView').classList.remove('hidden'); });
document.getElementById('showLogin')?.addEventListener('click', e=>{ e.preventDefault(); document.getElementById('registerView').classList.add('hidden'); document.getElementById('loginView').classList.remove('hidden'); });

document.getElementById('loginForm')?.addEventListener('submit', async e=>{
  e.preventDefault();
  const email = document.getElementById('loginEmail').value;
  const password = document.getElementById('loginPassword').value;
  const res = await fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
  const j = await res.json();
  if(j.error){ alert(j.error); } else { document.getElementById('loginView').classList.add('hidden'); loadCurrentUser(); }
});

document.getElementById('registerForm')?.addEventListener('submit', async e=>{
  e.preventDefault();
  const name=document.getElementById('regName').value;
  const email=document.getElementById('regEmail').value;
  const phone=document.getElementById('regPhone').value;
  const password=document.getElementById('regPassword').value;
  const res = await fetch('/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,email,phone,password})});
  const j = await res.json();
  if(j.error){ alert(j.error); } else { document.getElementById('registerView').classList.add('hidden'); loadCurrentUser(); }
});

// initialize
loadCurrentUser();

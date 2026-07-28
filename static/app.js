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
  const view = link.dataset.view || 'chat';
  e.preventDefault();
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
    const authButtons = document.getElementById('authButtons');
    if(user){
      authButtons.innerHTML = `<div class="profile-inline"><img src="${user.photo||'/static/default-avatar.png'}" alt="avatar" class="avatar small"> <strong>${user.name}</strong> <button id="logoutBtn" class="auth-logout">Logout</button></div>`;
      document.getElementById('logoutBtn').addEventListener('click', async ()=>{ await fetch('/logout',{method:'POST'}); window.location.reload(); });
    
    } else {
      authButtons.innerHTML = `<div class="auth-actions"><button id="openLogin" class="auth-btn auth-btn-outline">Login</button> <button id="openRegister" class="auth-btn auth-btn-primary">Register</button></div>`;
      document.getElementById('openLogin').addEventListener('click', ()=>{ window.location.href = '/login'; });
      document.getElementById('openRegister').addEventListener('click', ()=>{ window.location.href = '/register'; });
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

const kbFileInput = document.getElementById('kbFileInput');
const kbDropzone = document.getElementById('kbDropzone');
const kbUploadStatus = document.getElementById('kbUploadStatus');
const kbUploadedFiles = document.getElementById('kbUploadedFiles');
const kbConversationList = document.getElementById('kbConversationList');
const kbChatWindow = document.getElementById('kbChatWindow');
const kbChatForm = document.getElementById('kbChatForm');
const kbChatInput = document.getElementById('kbChatInput');
const kbRefresh = document.getElementById('kbRefresh');
const kbConversationTitle = document.getElementById('kbConversationTitle');
const kbCreateModal = document.getElementById('kbCreateModal');
const kbConversationName = document.getElementById('kbConversationName');
const createKbConversation = document.getElementById('createKbConversation');
const kbUploadSection = document.getElementById('kbUploadSection');
let activeConversationId = null;
let kbMode = 'upload';

function showKbStatus(message, isError = false) {
  kbUploadStatus.textContent = message;
  kbUploadStatus.style.color = isError ? '#c0392b' : '#5d4ed7';
}

function renderUploadedFiles(files) {
  kbUploadedFiles.innerHTML = '';
  if (!files.length) {
    kbUploadedFiles.innerHTML = '<div class="kb-empty">No documents uploaded yet.</div>';
    return;
  }
  const fragment = document.createDocumentFragment();
  files.forEach(file => {
    const item = document.createElement('div'); item.className = 'kb-file-item'; item.innerHTML = `<strong>${file.file_name}</strong><div>${file.file_type} · ${(file.file_size / 1024).toFixed(1)} KB</div>`;
    fragment.appendChild(item);
  });
  kbUploadedFiles.appendChild(fragment);
}

function renderConversations(conversations) {
  kbConversationList.innerHTML = '';
  if (!conversations.length) {
    kbConversationList.innerHTML = '<div class="kb-empty">No conversations yet.</div>';
    return;
  }
  const fragment = document.createDocumentFragment();
  conversations.forEach(conversation => {
    const item = document.createElement('button'); item.type = 'button'; item.className = `kb-conversation-item ${activeConversationId === conversation.id ? 'active' : ''}`;
    item.innerHTML = `<strong>${conversation.title}</strong><div>${conversation.status || 'waiting_for_documents'}</div>`;
    item.addEventListener('click', () => loadConversation(conversation.id));
    fragment.appendChild(item);
  });
  kbConversationList.appendChild(fragment);
}

function renderHistory(history) {
  kbChatWindow.innerHTML = '';
  if (!history.length) {
    kbChatWindow.innerHTML = '<div class="kb-empty">Start asking questions about your uploaded documents.</div>';
    return;
  }
  const fragment = document.createDocumentFragment();
  history.forEach(entry => {
    const bubble = document.createElement('div'); bubble.className = `kb-chat-bubble ${entry.role === 'user' ? 'user' : 'assistant'}`; bubble.textContent = entry.message;
    fragment.appendChild(bubble);
  });
  kbChatWindow.appendChild(fragment);
  kbChatWindow.scrollTop = kbChatWindow.scrollHeight;
}

function showKbUploadState() {
  kbUploadSection.classList.remove('hidden');
  kbMode = 'upload';
}

function showKbChatState() {
  kbUploadSection.classList.add('hidden');
  kbMode = 'chat';
}

async function refreshKnowledgeBase() {
  try {
    const res = await fetch('/api/kb/conversations');
    const data = await res.json();
    if (data.error) {
      showKbStatus(data.error, true);
      return;
    }
    if (!activeConversationId && data.conversations.length) {
      activeConversationId = data.conversations[0].id;
    }
    renderConversations(data.conversations);
    if (activeConversationId) {
      await loadConversation(activeConversationId);
    }
  } catch (e) {
    showKbStatus('Unable to load conversations right now.', true);
  }
}

async function loadConversation(conversationId) {
  activeConversationId = conversationId;
  try {
    const res = await fetch(`/api/kb/conversation/${conversationId}`);
    const data = await res.json();
    if (data.error) {
      showKbStatus(data.error, true);
      return;
    }
    const conversation = data.conversation || {};
    kbConversationTitle.textContent = conversation.title || 'Conversation';
    if (conversation.status === 'ready_for_chat') {
      showKbChatState();
    } else {
      showKbUploadState();
    }
    renderUploadedFiles(data.documents || []);
    renderHistory(data.history || []);
    const convRes = await fetch('/api/kb/conversations');
    const convData = await convRes.json();
    renderConversations(convData.conversations || []);
  } catch (e) {
    showKbStatus('Unable to load conversation.', true);
  }
}

async function createConversation() {
  const title = kbConversationName.value.trim();
  if (!title || title.length < 3) {
    alert('Please enter a conversation name with at least 3 characters.');
    return;
  }
  try {
    const res = await fetch('/api/kb/conversation', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({title})});
    const data = await res.json();
    if (!res.ok || data.error) {
      alert(data.error || 'Unable to create conversation');
      return;
    }
    activeConversationId = data.conversation.id;
    kbConversationTitle.textContent = data.conversation.title;
    kbConversationName.value = '';
    kbCreateModal.classList.add('hidden');
    showKbUploadState();
    showKbStatus('New conversation is ready for documents.');
    await refreshKnowledgeBase();
    document.querySelector('[data-view="knowledge"]').click();
  } catch (e) {
    alert('Unable to create conversation.');
  }
}

kbRefresh.addEventListener('click', refreshKnowledgeBase);

kbDropzone.addEventListener('dragover', e => { e.preventDefault(); kbDropzone.classList.add('drag-over'); });
kbDropzone.addEventListener('dragleave', () => kbDropzone.classList.remove('drag-over'));
kbDropzone.addEventListener('drop', e => { e.preventDefault(); kbDropzone.classList.remove('drag-over'); const dt = new DataTransfer(); Array.from(e.dataTransfer.files).forEach(file => dt.items.add(file)); kbFileInput.files = dt.files; uploadKnowledgeFiles(); });
kbDropzone.addEventListener('click', () => kbFileInput.click());
kbFileInput.addEventListener('change', uploadKnowledgeFiles);

async function uploadKnowledgeFiles() {
  const files = Array.from(kbFileInput.files || []);
  if (!files.length || !activeConversationId) return;
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('conversation_id', activeConversationId);
  showKbStatus('Uploading documents...');
  try {
    const res = await fetch('/api/kb/upload', {method:'POST', body: formData});
    const data = await res.json();
    if (!res.ok || data.error) {
      showKbStatus(data.error || 'Upload failed', true);
      return;
    }
    showKbStatus('Processing complete. You can now chat.');
    showKbChatState();
    await refreshKnowledgeBase();
  } catch (e) {
    showKbStatus('Upload failed. Please try again.', true);
  }
}

kbChatForm.addEventListener('submit', async e => {
  e.preventDefault();
  const message = kbChatInput.value.trim();
  if (!message || !activeConversationId) return;
  kbChatInput.value = '';
  const bubble = document.createElement('div'); bubble.className = 'kb-chat-bubble user'; bubble.textContent = message; kbChatWindow.appendChild(bubble);
  showKbStatus('Thinking...');
  try {
    const res = await fetch('/api/kb/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({conversation_id: activeConversationId, message})});
    const data = await res.json();
    const assistantBubble = document.createElement('div'); assistantBubble.className = 'kb-chat-bubble assistant'; assistantBubble.textContent = data.answer || 'I could not answer from the uploaded documents.'; kbChatWindow.appendChild(assistantBubble);
    kbChatWindow.scrollTop = kbChatWindow.scrollHeight;
    showKbStatus('Answer ready.');
  } catch (e) {
    showKbStatus('Unable to answer right now.', true);
  }
});

document.getElementById('newChat').addEventListener('click', () => {
  kbConversationName.value = '';
  kbCreateModal.classList.remove('hidden');
  kbConversationName.focus();
});

createKbConversation.addEventListener('click', createConversation);
Array.from(document.querySelectorAll('[data-close="kbCreateModal"]')).forEach(btn => btn.addEventListener('click', () => kbCreateModal.classList.add('hidden')));

// initialize
loadCurrentUser();
refreshKnowledgeBase();

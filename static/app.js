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
document.querySelectorAll('[data-view]').forEach(link => link.addEventListener('click', e => { e.preventDefault(); const analytics = link.dataset.view === 'analytics'; document.getElementById('chatView').classList.toggle('hidden', analytics); document.getElementById('analyticsView').classList.toggle('hidden', !analytics); document.querySelectorAll('[data-view]').forEach(x => x.classList.toggle('active', x === link)); }));

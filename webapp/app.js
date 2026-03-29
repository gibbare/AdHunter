// ── Constants ──────────────────────────────────────────────────────────────

const WORKER = 'https://aurora-push.gibbare.workers.dev';
const VAPID_KEY = 'BOkPa5xxrv4_txqeqZ6Dx5KDgfAlxdWG5LGyV1V76oFFzAqtzhww-VSsOiz1CMDxCJA8zAC1Z6yvhGhyGMo4qvs';

const SITES = [
  { id: 'blocket',           name: 'Blocket',             emoji: '🇸🇪' },
  { id: 'mpb',               name: 'MPB',                 emoji: '📦' },
  { id: 'kamerastore',       name: 'Kamerastore',         emoji: '📷' },
  { id: 'scandinavianphoto', name: 'Scandinavian Photo',  emoji: '📸' },
  { id: 'cyberphoto',        name: 'Cyberphoto',          emoji: '💻' },
  { id: 'goecker',           name: 'Goecker',             emoji: '🎞️' },
];

const DEFAULT_CONFIG = {
  terms: [],
  sites: {
    blocket: true,
    mpb: true,
    kamerastore: true,
    scandinavianphoto: true,
    cyberphoto: true,
    goecker: true,
  },
  interval: 20,
};

// ── State ──────────────────────────────────────────────────────────────────

let secret = localStorage.getItem('ah_secret') || '';
let config = null;
let currentView = 'searches';

// ── API ────────────────────────────────────────────────────────────────────

async function getConfig() {
  try {
    const res = await fetch(`${WORKER}/config?secret=${encodeURIComponent(secret)}`);
    if (res.status === 401) return null;
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    setStatusDot(true);
    throw e;
  }
}

async function saveConfig(cfg) {
  try {
    const res = await fetch(`${WORKER}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ secret, ...cfg }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    showToast('Sparat ✓');
    setStatusDot(false);
    return true;
  } catch (e) {
    showToast('Fel vid sparande', true);
    setStatusDot(true);
    return false;
  }
}

// ── Auth ───────────────────────────────────────────────────────────────────

function showAuth(errorMsg = '') {
  document.getElementById('auth-screen').classList.remove('hidden');
  document.getElementById('app').classList.add('hidden');
  document.getElementById('auth-error').textContent = errorMsg;
  document.getElementById('auth-input').value = '';
}

function hideAuth() {
  document.getElementById('auth-screen').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
}

// ── Navigation ─────────────────────────────────────────────────────────────

function switchView(viewId) {
  currentView = viewId;

  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.view === viewId);
  });

  document.querySelectorAll('.view').forEach(view => {
    view.classList.toggle('active', view.id === `view-${viewId}`);
  });

  switch (viewId) {
    case 'searches': renderSearches(); break;
    case 'sites':    renderSites();    break;
    case 'notify':   renderNotify();   break;
    case 'settings': renderSettings(); break;
  }
}

// ── Searches view ──────────────────────────────────────────────────────────

function renderSearches() {
  const container = document.getElementById('view-searches');
  container.innerHTML = '';

  if (config.terms.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.innerHTML = `
      <div class="icon">🔍</div>
      <div>Inga söktermer än.<br>Lägg till din första sökning nedan.</div>
    `;
    container.appendChild(empty);
  } else {
    config.terms.forEach((term, idx) => {
      const card = document.createElement('div');
      card.className = 'card card-row';

      const priceLabel = (term.min_price || term.max_price)
        ? [
            term.min_price ? `${term.min_price} kr` : null,
            term.max_price ? `${term.max_price} kr` : null,
          ].filter(Boolean).join(' – ')
        : 'Alla priser';

      card.innerHTML = `
        <div class="term-left">
          <div class="term-query">${escHtml(term.query)}</div>
          <div class="term-meta">${escHtml(priceLabel)}</div>
        </div>
        <div class="term-right">
          <label class="toggle">
            <input type="checkbox" ${term.active ? 'checked' : ''} data-idx="${idx}" class="term-toggle">
            <span class="thumb"></span>
          </label>
          <button class="btn btn-danger term-delete" data-idx="${idx}">×</button>
        </div>
      `;
      container.appendChild(card);
    });
  }

  // Add form
  const addForm = document.createElement('div');
  addForm.className = 'add-form';
  addForm.innerHTML = `
    <div class="section-title">Lägg till sökning</div>
    <input type="text" id="add-query" placeholder="T.ex. Sony A7, Leica M6...">
    <div class="form-row">
      <input type="number" id="add-min" placeholder="Min pris (kr)" min="0">
      <input type="number" id="add-max" placeholder="Max pris (kr)" min="0">
    </div>
    <button class="btn btn-primary" id="add-btn">Lägg till</button>
  `;
  container.appendChild(addForm);

  // Events: toggle
  container.querySelectorAll('.term-toggle').forEach(cb => {
    cb.addEventListener('change', async () => {
      const idx = parseInt(cb.dataset.idx);
      config.terms[idx].active = cb.checked;
      await saveConfig(config);
    });
  });

  // Events: delete
  container.querySelectorAll('.term-delete').forEach(btn => {
    btn.addEventListener('click', async () => {
      const idx = parseInt(btn.dataset.idx);
      config.terms.splice(idx, 1);
      await saveConfig(config);
      renderSearches();
    });
  });

  // Events: add form
  document.getElementById('add-btn').addEventListener('click', async () => {
    const queryInput = document.getElementById('add-query');
    const query = queryInput.value.trim();

    if (!query) {
      queryInput.classList.add('error');
      setTimeout(() => queryInput.classList.remove('error'), 400);
      return;
    }

    const minVal = document.getElementById('add-min').value;
    const maxVal = document.getElementById('add-max').value;

    config.terms.push({
      id: Date.now().toString(36),
      query,
      active: true,
      min_price: minVal ? parseInt(minVal) : null,
      max_price: maxVal ? parseInt(maxVal) : null,
    });

    document.getElementById('add-query').value = '';
    document.getElementById('add-min').value = '';
    document.getElementById('add-max').value = '';

    await saveConfig(config);
    renderSearches();
  });
}

// ── Sites view ─────────────────────────────────────────────────────────────

function renderSites() {
  const container = document.getElementById('view-sites');
  container.innerHTML = '';

  const titleEl = document.createElement('div');
  titleEl.className = 'section-title';
  titleEl.textContent = 'Aktiva sajter';
  container.appendChild(titleEl);

  const grid = document.createElement('div');
  grid.className = 'site-grid';

  SITES.forEach(site => {
    const isActive = config.sites[site.id] !== false;
    const card = document.createElement('div');
    card.className = `site-card${isActive ? '' : ' inactive'}`;
    card.dataset.siteId = site.id;

    card.innerHTML = `
      <div class="site-info">
        <div class="site-emoji">${site.emoji}</div>
        <div class="site-name">${escHtml(site.name)}</div>
      </div>
      <label class="toggle">
        <input type="checkbox" ${isActive ? 'checked' : ''} class="site-toggle" data-site="${site.id}">
        <span class="thumb"></span>
      </label>
    `;
    grid.appendChild(card);
  });

  container.appendChild(grid);

  // Events: site toggle
  grid.querySelectorAll('.site-toggle').forEach(cb => {
    cb.addEventListener('change', async () => {
      const siteId = cb.dataset.site;
      config.sites[siteId] = cb.checked;
      const card = grid.querySelector(`[data-site-id="${siteId}"]`);
      if (card) card.classList.toggle('inactive', !cb.checked);
      await saveConfig(config);
    });
  });
}

// ── Notify view ────────────────────────────────────────────────────────────

async function renderNotify() {
  const container = document.getElementById('view-notify');
  container.innerHTML = '';

  let subscribed = false;
  try {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      const reg = await navigator.serviceWorker.getRegistration('./ad-sw.js');
      if (reg) {
        const sub = await reg.pushManager.getSubscription();
        subscribed = !!sub;
      }
    }
  } catch {}

  const statusCard = document.createElement('div');
  statusCard.className = 'notify-status';
  statusCard.innerHTML = `
    <div class="status-dot ${subscribed ? 'active' : 'inactive'}"></div>
    <span>${subscribed ? 'Notiser aktiverade' : 'Notiser ej aktiverade'}</span>
  `;
  container.appendChild(statusCard);

  const btn = document.createElement('button');
  if (subscribed) {
    btn.className = 'btn btn-ghost';
    btn.textContent = 'Avaktivera notiser';
    btn.addEventListener('click', async () => {
      await deactivateNotify();
    });
  } else {
    btn.className = 'btn btn-primary';
    btn.textContent = 'Aktivera notiser';
    btn.addEventListener('click', async () => {
      await activateNotify();
    });
  }
  container.appendChild(btn);

  const hint = document.createElement('p');
  hint.className = 'notify-hint';
  hint.textContent = 'Notiser levereras till den här enheten när en ny annons hittas.';
  container.appendChild(hint);
}

async function activateNotify() {
  try {
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      showToast('Notiser nekades', true);
      return;
    }

    const reg = await navigator.serviceWorker.register('./ad-sw.js');
    await navigator.serviceWorker.ready;

    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_KEY),
    });

    const res = await fetch(`${WORKER}/subscribe-ads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subscription: sub }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    showToast('Notiser aktiverade ✓');
    renderNotify();
  } catch (e) {
    showToast('Fel: ' + e.message, true);
  }
}

async function deactivateNotify() {
  try {
    const reg = await navigator.serviceWorker.getRegistration('./ad-sw.js');
    if (!reg) { renderNotify(); return; }

    const sub = await reg.pushManager.getSubscription();
    if (sub) {
      await fetch(`${WORKER}/unsubscribe-ads`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subscription: sub }),
      });
      await sub.unsubscribe();
    }
    showToast('Notiser avaktiverade');
    renderNotify();
  } catch (e) {
    showToast('Fel: ' + e.message, true);
  }
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  return Uint8Array.from(rawData, c => c.charCodeAt(0));
}

// ── Settings view ──────────────────────────────────────────────────────────

function renderSettings() {
  const container = document.getElementById('view-settings');
  container.innerHTML = '';

  const intervalRow = document.createElement('div');
  intervalRow.className = 'interval-row';
  intervalRow.innerHTML = `
    <label>Sökintervall</label>
    <select id="interval-select">
      <option value="10" ${config.interval === 10 ? 'selected' : ''}>10 min</option>
      <option value="15" ${config.interval === 15 ? 'selected' : ''}>15 min</option>
      <option value="20" ${config.interval === 20 ? 'selected' : ''}>20 min</option>
      <option value="30" ${config.interval === 30 ? 'selected' : ''}>30 min</option>
      <option value="60" ${config.interval === 60 ? 'selected' : ''}>60 min</option>
    </select>
  `;
  container.appendChild(intervalRow);

  const logoutCard = document.createElement('div');
  logoutCard.className = 'card';
  logoutCard.innerHTML = `
    <button class="btn btn-ghost" id="logout-btn" style="width:100%">Logga ut</button>
  `;
  container.appendChild(logoutCard);

  document.getElementById('interval-select').addEventListener('change', async (e) => {
    config.interval = parseInt(e.target.value);
    await saveConfig(config);
  });

  document.getElementById('logout-btn').addEventListener('click', () => {
    localStorage.removeItem('ah_secret');
    location.reload();
  });
}

// ── Toast ──────────────────────────────────────────────────────────────────

let toastTimer = null;

function showToast(msg, isError = false) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.style.color = isError ? 'var(--danger)' : 'var(--text)';
  toast.classList.add('show');

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, 2500);
}

// ── Status dot ─────────────────────────────────────────────────────────────

function setStatusDot(isError) {
  const dot = document.getElementById('status-dot');
  if (dot) dot.classList.toggle('error', isError);
}

// ── Helpers ────────────────────────────────────────────────────────────────

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Render all ─────────────────────────────────────────────────────────────

function renderAll() {
  renderSearches();
  renderSites();
  renderNotify();
  renderSettings();
  switchView(currentView);
}

// ── Init ───────────────────────────────────────────────────────────────────

async function init() {
  // Nav tab click handlers
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => switchView(tab.dataset.view));
  });

  // Auth button handler
  document.getElementById('auth-btn').addEventListener('click', async () => {
    const input = document.getElementById('auth-input');
    secret = input.value.trim();

    if (!secret) {
      document.getElementById('auth-error').textContent = 'Ange ett lösenord';
      return;
    }

    const btn = document.getElementById('auth-btn');
    btn.disabled = true;
    btn.textContent = 'Loggar in...';

    try {
      const cfg = await getConfig();
      if (cfg === null) {
        showAuth('Felaktigt lösenord');
      } else {
        localStorage.setItem('ah_secret', secret);
        config = cfg;
        hideAuth();
        renderAll();
      }
    } catch (e) {
      showAuth('Nätverksfel: ' + e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Logga in';
    }
  });

  // Allow Enter key in password field
  document.getElementById('auth-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById('auth-btn').click();
  });

  // Try to restore session
  if (secret) {
    try {
      const cfg = await getConfig();
      if (cfg) {
        config = cfg;
        hideAuth();
        renderAll();
      } else {
        showAuth('Session utgången');
      }
    } catch (e) {
      showAuth('Nätverksfel');
    }
  } else {
    showAuth();
  }
}

document.addEventListener('DOMContentLoaded', init);

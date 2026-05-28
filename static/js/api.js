// Shared API client + auth state

const auth = {
  get user() {
    try { return JSON.parse(localStorage.getItem('lf_user')); } catch { return null; }
  },
  set user(val) {
    if (val) localStorage.setItem('lf_user', JSON.stringify(val));
    else localStorage.removeItem('lf_user');
  },
  logout() { localStorage.removeItem('lf_user'); location.href = '/'; },
  require() {
    if (!this.user) {
      location.href = '/auth?next=' + encodeURIComponent(location.pathname + location.search);
    }
  },
};

async function apiFetch(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.detail || data.message || data.error || `HTTP ${res.status}`;
    throw Object.assign(new Error(msg), { status: res.status });
  }
  return data;
}

const api = {
  register:     (b) => apiFetch('POST', '/api/register', b),
  login:        (b) => apiFetch('POST', '/api/login', b),
  categories:   ()  => apiFetch('GET',  '/api/categories'),
  reports(p = {}) {
    const clean = Object.fromEntries(Object.entries(p).filter(([,v]) => v != null && v !== ''));
    const q = Object.keys(clean).length ? '?' + new URLSearchParams(clean) : '';
    return apiFetch('GET', `/api/reports${q}`);
  },
  createReport: (b) => apiFetch('POST', '/api/reports', b),
  messages:     (id) => apiFetch('GET',  `/api/messages/${id}`),
  sendMessage:  (b) => apiFetch('POST', '/api/messages', b),
  sentMessages: (id) => apiFetch('GET',  `/api/messages/${id}?box=sent`),
  createMatch:  (b) => apiFetch('POST', '/api/matches', b),
};

// ── Shared helpers ─────────────────────────────────────────

function escHtml(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

function fmtDate(s) {
  if (!s) return '';
  try {
    const iso = s.includes('T') ? s : s.replace(' ', 'T') + 'Z';
    return new Date(iso).toLocaleDateString('tr-TR', {
      day: 'numeric', month: 'long', year: 'numeric',
    });
  } catch { return s; }
}

function showAlert(id, msg, type = 'error') {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `alert alert-${type}`;
}

function hideAlert(id) {
  const el = document.getElementById(id);
  if (el) el.className = 'alert alert-hidden';
}

// ── Navbar init ───────────────────────────────────────────

function initNav() {
  const el = document.getElementById('navAuth');
  if (!el) return;
  const user = auth.user;
  if (user) {
    el.innerHTML = `
      <span class="nav-username">${escHtml(user.full_name.split(' ')[0])}</span>
      <a href="/create" class="btn btn-primary btn-sm">+ İlan Ver</a>
      <button class="btn btn-ghost btn-sm" onclick="auth.logout()">Çıkış</button>
    `;
  } else {
    el.innerHTML = `
      <a href="/auth" class="btn btn-outline btn-sm">Giriş Yap</a>
      <a href="/auth?tab=register" class="btn btn-primary btn-sm">Üye Ol</a>
    `;
  }
}

// ── Report card renderer (shared) ─────────────────────────

function reportCard(r) {
  const typeBadge = r.type === 'found'
    ? `<span class="badge badge-found">Bulundu</span>`
    : `<span class="badge badge-lost">Kayıp</span>`;

  const desc = r.description
    ? `<div class="card-desc mt-8">${escHtml(r.description.slice(0, 140))}${r.description.length > 140 ? '…' : ''}</div>`
    : '';

  const currentUser = auth.user;
  const isOwn = currentUser && currentUser.id === r.user_id;
  const msgUrl = `/messages?to=${r.user_id}&item=${encodeURIComponent(r.item_name)}`;

  const footer = isOwn
    ? `<span style="font-size:12px;color:var(--text-3);padding:4px 0;">Benim ilanım</span>`
    : `<a href="${msgUrl}" class="btn btn-outline btn-sm">Mesaj Gönder</a>`;

  return `
    <div class="card">
      <div class="card-header">
        <span class="card-title">${escHtml(r.item_name)}</span>
        ${typeBadge}
      </div>
      <div class="card-meta">
        ${r.location      ? `<span>📍 ${escHtml(r.location)}</span>`      : ''}
        ${r.category_name ? `<span>🏷 ${escHtml(r.category_name)}</span>` : ''}
        <span>👤 ${escHtml(r.reported_by || '—')}</span>
        <span>🗓 ${fmtDate(r.date)}</span>
      </div>
      ${desc}
      <div class="card-footer">${footer}</div>
    </div>`;
}

document.addEventListener('DOMContentLoaded', initNav);

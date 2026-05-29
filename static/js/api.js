// Shared API client + auth state

const auth = {
  get user() {
    try { return JSON.parse(localStorage.getItem('user')); } catch { return null; }
  },
  set user(val) {
    if (val) localStorage.setItem('user', JSON.stringify(val));
    else localStorage.removeItem('user');
  },
  logout() { localStorage.removeItem('user'); location.href = '/'; },
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
  register: (b) => apiFetch('POST', '/api/register', b),
  login: (b) => apiFetch('POST', '/api/login', b),
  categories: () => apiFetch('GET', '/api/categories'),
  reports(p = {}) {
    const clean = Object.fromEntries(Object.entries(p).filter(([, v]) => v != null && v !== ''));
    const q = Object.keys(clean).length ? '?' + new URLSearchParams(clean) : '';
    return apiFetch('GET', `/api/reports${q}`);
  },
  createReport: (b) => apiFetch('POST', '/api/reports', b),
  messages: (id) => apiFetch('GET', `/api/messages/${id}`),
  sendMessage: (b) => apiFetch('POST', '/api/messages', b),
  sentMessages: (id) => apiFetch('GET', `/api/messages/${id}?box=sent`),
  createMatch: (b) => apiFetch('POST', '/api/matches', b),
};

// ── Shared helpers ─────────────────────────────────────────

function escHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
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

// ── Gelişmiş Eşleşme Alanı (Çirkin Prompt Kutusu Kaldırıldı!) ─────────────────

window.openMatchModal = async function (targetId, targetType, event) {
  event.stopPropagation(); // Kartın genişlemesini engellemek için
  if (!auth.user) {
    alert("Eşleştirme yapmak için lütfen önce giriş yapın.");
    return;
  }

  // Tıklanan kartın içindeki eşleştirme alanını yakala
  const cardEl = event.target.closest('.card');
  const footerEl = cardEl.querySelector('.match-selector-area');
  
  const oppositeType = targetType === 'lost' ? 'found' : 'lost';
  const oppositeTypeName = oppositeType === 'lost' ? 'Kayıp' : 'Bulundu';

  // Butona basıldığında yükleniyor efekti verelim
  event.target.disabled = true;
  event.target.textContent = 'Yükleniyor...';

  try {
    const allReports = await api.reports();
    // Kullanıcının ID'sini güvenli şekilde al ve eşleştirebileceği ters türdeki ilanlarını filtrele
    const userId = auth.user.kullanici_id ?? auth.user.id;
    const myMatches = allReports.filter(r => r.user_id === userId && r.type === oppositeType);

    if (myMatches.length === 0) {
      alert(`Bu ilanla eşleştirebileceğiniz aktif bir "${oppositeTypeName}" ilanınız bulunmamaktadır.\nÖnce bu eşya için bir ilan oluşturmalısınız.`);
      event.target.disabled = false;
      event.target.textContent = 'Eşleştir';
      return;
    }

    // Çirkin Opera mesajı yerine kartın altında şık bir HTML select alanı açıyoruz!
    let selectHtml = `
      <div style="margin-top: 10px; width: 100%; text-align: left; background: var(--surface); padding: 10px; border-radius: var(--radius-sm); border: 1px solid var(--border-strong);">
        <label style="font-size: 12px; font-weight: 600; color: var(--text-2); display: block; margin-bottom: 6px;">Eşleşecek Kendi İlanınızı Seçin:</label>
        <select class="form-select" id="myReportSelect-${targetId}" style="padding: 6px; font-size: 13px; margin-bottom: 8px;">
    `;

    myMatches.forEach(r => {
      // app.py'den 'id' alanı dönüyor, onu güvenle alıyoruz kanka
      selectHtml += `<option value="${r.id}">İlan No: #${r.id} - ${escHtml(r.item_name)}</option>`;
    });

    selectHtml += `
        </select>
        <div style="display: flex; gap: 6px; justify-content: flex-end;">
          <button class="btn btn-sm btn-ghost" onclick="cancelMatchSelect(${targetId}, event)">İptal</button>
          <button class="btn btn-sm btn-primary" onclick="submitMatchSelect(${targetId}, '${targetType}', event)" style="background: var(--found);">Eşleşmeyi Tamamla</button>
        </div>
      </div>
    `;

    footerEl.innerHTML = selectHtml;
    footerEl.style.display = 'block';

  } catch (e) {
    alert("İlanlarınız çekilirken bir hata oluştu: " + (e.message || "Bilinmeyen hata."));
    event.target.disabled = false;
    event.target.textContent = 'Eşleştir';
  }
}

// Seçim alanını iptal etme fonksiyonu
window.cancelMatchSelect = function(targetId, event) {
  event.stopPropagation();
  const area = event.target.closest('.match-selector-area');
  area.style.display = 'none';
  area.innerHTML = '';
  
  // Ana eşleştir butonunu tekrar eski haline getir
  const cardEl = area.closest('.card');
  const matchBtn = cardEl.querySelector('.main-match-btn');
  if (matchBtn) {
    matchBtn.disabled = false;
    matchBtn.textContent = 'Eşleştir';
  }
}

// Seçilen ilanı backend'e gönderme fonksiyonu (Hatalı ID problemi kökten çözüldü!)
window.submitMatchSelect = async function(targetId, targetType, event) {
  event.stopPropagation();
  const selectEl = document.getElementById(`myReportSelect-${targetId}`);
  const selectedMyId = parseInt(selectEl.value);

  if (!selectedMyId) {
    alert("Lütfen bir ilan seçin!");
    return;
  }

  const payload = {
    lost_report_id: targetType === 'lost' ? targetId : selectedMyId,
    found_report_id: targetType === 'found' ? targetId : selectedMyId
  };

  try {
    await api.createMatch(payload);
    alert("✨ Eşleşme başarıyla oluşturuldu! \nDurumu 'Eşleşmelerim' sekmesinden onaylandığında ilanlar kapatılacaktır.");
    location.reload(); // Sayfayı yenile ki butonlar güncellensin
  } catch (e) {
    alert("Eşleşme oluşturulamadı kanka: " + (e.message || "Veritabanı hatası."));
  }
}

// ── İlan Kartı Tasarımı (İlan No Eklendi kanka!) ─────────────────────────

function reportCard(r) {
  const typeBadge = r.type === 'found'
    ? `<span class="badge badge-found">Bulundu</span>`
    : `<span class="badge badge-lost">Kayıp</span>`;

  const fullDesc = r.description ? escHtml(r.description) : 'Açıklama belirtilmemiş.';
  const shortDesc = r.description ? escHtml(r.description.slice(0, 140)) + (r.description.length > 140 ? '…' : '') : '';

  const currentUser = auth.user;
  const userId = currentUser ? (currentUser.kullanici_id ?? currentUser.id) : null;
  const isOwn = currentUser && userId === r.user_id;
  const msgUrl = `/messages?to=${r.user_id}&item=${encodeURIComponent(r.item_name)}`;

  // Kartın en üstüne sırıtmaması için İlan No (#ID) ekledik kanka
  const footer = isOwn
    ? `<span style="font-size:12px;color:var(--text-3);padding:4px 0;">Benim ilanım</span>`
    : `<button class="btn btn-ghost btn-sm main-match-btn" onclick="openMatchModal(${r.id}, '${r.type}', event)" style="margin-right:auto; color:var(--accent); font-weight:700;">Eşleştir</button>
       <a href="${msgUrl}" class="btn btn-outline btn-sm" onclick="event.stopPropagation();">Mesaj Gönder</a>`;

  return `
    <div class="card clickable-card" onclick="toggleCardDetail(this)">
      <div class="card-header">
        <div style="display:flex; flex-direction:column; gap:2px; flex:1;">
          <span style="font-size:11px; font-weight:700; color:var(--text-3);">İLAN NO: #${r.id}</span>
          <span class="card-title">${escHtml(r.item_name)}</span>
        </div>
        ${typeBadge}
      </div>
      <div class="card-meta">
        ${r.location ? `<span>📍 ${escHtml(r.location)}</span>` : ''}
        ${r.category_name ? `<span>🏷 ${escHtml(r.category_name)}</span>` : ''}
        <span>👤 ${escHtml(r.reported_by || '—')}</span>
        <span>🗓 ${fmtDate(r.date)}</span>
      </div>
      ${shortDesc ? `<div class="card-desc mt-8 card-desc-short">${shortDesc}</div>` : ''}
      <div class="card-desc mt-8 card-desc-full" style="display:none; line-height: 1.6;"><strong>Detay: </strong>${fullDesc}</div>
      
      <div class="match-selector-area" style="display:none; width:100%;"></div>
      
      <div class="card-footer" style="padding-top:1rem; border-top:1px solid var(--border); margin-top:1rem;">${footer}</div>
    </div>`;
}

function toggleCardDetail(cardEl) {
  // Toggle the expanded class
  const isExpanded = cardEl.classList.toggle('expanded');

  const shortDesc = cardEl.querySelector('.card-desc-short');
  const fullDesc = cardEl.querySelector('.card-desc-full');

  if (isExpanded) {
    if (shortDesc) shortDesc.style.display = 'none';
    if (fullDesc) fullDesc.style.display = 'block';
  } else {
    if (shortDesc) shortDesc.style.display = 'block';
    if (fullDesc) fullDesc.style.display = 'none';
  }
}

document.addEventListener('DOMContentLoaded', initNav);

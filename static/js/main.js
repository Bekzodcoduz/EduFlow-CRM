/* ===== EDUFLOW — MAIN JS ===== */

// ===== CSRF =====
function getCsrf() {
  const v = '; ' + document.cookie;
  const p = v.split('; csrftoken=');
  if (p.length === 2) return p.pop().split(';').shift();
  return '';
}

// ===== MODAL =====
function _teleportModal(el) {
  if (el && el.parentElement !== document.body) {
    document.body.appendChild(el);
  }
}

function openModal(id) {
  const el = document.getElementById(id);
  if (!el) return;
  _teleportModal(el);
  el.classList.add('open');
  document.body.style.overflow = 'hidden';

  requestAnimationFrame(function () {
    const inp = el.querySelector('input:not([type=hidden]), select, textarea');
    if (inp) inp.focus();
  });
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove('open');

  if (!document.querySelector('.modal-backdrop.open')) {
    document.body.style.overflow = '';
  }
}

// Backdrop click
document.addEventListener('click', function (e) {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// ESC close
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.open').forEach(function (m) {
      m.classList.remove('open');
    });
    closeSidebar(); // 🔥 sidebar ham yopiladi
    document.body.style.overflow = '';
  }
});

// ===== SIDEBAR =====
function toggleSidebar() {
  const sb = document.querySelector('.sidebar');
  const ov = document.querySelector('.sidebar-overlay');
  if (!sb) return;

  if (window.innerWidth > 768) {
    return;
  }

  sb.classList.toggle('open');
  if (ov) ov.classList.toggle('open');

  if (sb.classList.contains('open')) {
    document.body.style.overflow = 'hidden';
  } else if (!document.querySelector('.modal-backdrop.open')) {
    document.body.style.overflow = '';
  }
}

function closeSidebar() {
  const sb = document.querySelector('.sidebar');
  const ov = document.querySelector('.sidebar-overlay');

  if (sb) sb.classList.remove('open');
  if (ov) ov.classList.remove('open');

  if (!document.querySelector('.modal-backdrop.open')) {
    document.body.style.overflow = '';
  }
}

/** base.html hamburger — mobil drawer ochish */
function openSidebar() {
  toggleSidebar();
}

// 🔥 Resize fix (eng muhim)
window.addEventListener('resize', function () {
  if (window.innerWidth > 768) {
    closeSidebar();
    document.body.style.overflow = '';
  }
});

// ===== BAR CHART =====
function renderBarChart(containerId, labelsId, data, valueKey, labelKey, color) {
  const c = document.getElementById(containerId);
  const l = document.getElementById(labelsId);
  if (!c || !data || !data.length) return;

  const max = Math.max(...data.map(d => d[valueKey]));

  c.innerHTML = data.map(d => {
    const h = max > 0 ? Math.round(d[valueKey] / max * 110) : 3;
    const v = d[valueKey] >= 1000000
      ? (d[valueKey] / 1000000).toFixed(1) + 'M'
      : d[valueKey].toLocaleString();

    return `
      <div class="bar-col">
        <div class="bar-value">${v}</div>
        <div class="bar-fill" style="height:${h}px;background:${color};opacity:.85"></div>
      </div>
    `;
  }).join('');

  if (l) {
    l.innerHTML = data.map(d =>
      `<div class="bar-label" style="flex:1">${d[labelKey]}</div>`
    ).join('');
  }
}

// ===== DAVOMAT: keldi <-> kelmadi =====
function davCellInnerHTML(cellState) {
  if (cellState === 'present') {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>';
  }
  if (cellState === 'absent') {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  }
  return '';
}

function applyDavCellState(btn, cellState) {
  if (!btn) return;
  btn.classList.remove('present', 'absent');
  btn.dataset.cellState = cellState || 'empty';
  if (cellState === 'present') btn.classList.add('present');
  else if (cellState === 'absent') btn.classList.add('absent');
  btn.innerHTML = davCellInnerHTML(cellState || 'empty');
}

function applyDavCellStateForSync(studentId, dateStr, cellState) {
  const sel = '[data-dav-sync="' + String(studentId) + '|' + String(dateStr) + '"]';
  document.querySelectorAll(sel).forEach(function (root) {
    const btn = root.querySelector('.dav-cell[data-role="presence"]');
    if (btn) {
      applyDavCellState(btn, cellState);
    }
  });
}

function nextPresenceState(prev) {
  if (prev === 'empty') return 'present';
  if (prev === 'present') return 'absent';
  return 'present';
}

function toggleDavPresenceBtn(btn) {
  const studentId = btn.dataset.student;
  const dateStr = btn.dataset.date;
  const prev = btn.dataset.cellState || 'empty';
  const optimistic = nextPresenceState(prev);
  const url = window.DAV_TOGGLE_URL;
  if (!url) {
    console.error('DAV_TOGGLE_URL sozlanmagan');
    return;
  }

  applyDavCellStateForSync(studentId, dateStr, optimistic);

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrf()
    },
    body: JSON.stringify({ student_id: studentId, date: dateStr }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.error) throw new Error(data.error);
      applyDavCellStateForSync(studentId, dateStr, data.cell_state);
      document.dispatchEvent(new CustomEvent('davomatUpdated', { detail: { studentId: studentId, dateStr: dateStr } }));
    })
    .catch(function (err) {
      applyDavCellStateForSync(studentId, dateStr, prev);
      console.error('Davomat xatosi:', err);
    });
}

window.applyDavCellState = applyDavCellState;
window.applyDavCellStateForSync = applyDavCellStateForSync;
window.davCellInnerHTML = davCellInnerHTML;
window.toggleDavPresenceBtn = toggleDavPresenceBtn;

/** @deprecated url param — DAV_TOGGLE_URL ishlating */
function toggleAttendance(btn, studentId, dateStr, url) {
  if (url && !window.DAV_TOGGLE_URL) window.DAV_TOGGLE_URL = url;
  toggleDavPresenceBtn(btn);
}

// ===== ALERT =====
function dismissMessages() {
  setTimeout(function () {
    document.querySelectorAll('.alert').forEach(function (a) {
      a.style.opacity = '0';
      a.style.transform = 'translateY(-8px)';
      setTimeout(() => a.remove(), 500);
    });
  }, 4000);
}

// ===== HISOBOT EKSPORT: guruh tanlansa talaba ro'yxati =====
function initExportScopeFilter() {
  const fg = document.querySelector('[data-export-group]');
  const fs = document.querySelector('[data-export-student]');
  if (!fg || !fs) return;
  function sync() {
    const g = fg.value;
    Array.from(fs.options).forEach((opt) => {
      if (!opt.value) {
        opt.hidden = false;
        return;
      }
      const og = opt.getAttribute('data-group') || '';
      opt.hidden = Boolean(g && og !== g);
    });
    const sel = fs.selectedOptions[0];
    if (fs.value && sel && sel.hidden) fs.value = '';
  }
  fg.addEventListener('change', sync);
  sync();
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', function () {

  initExportScopeFilter();

  // Modallarni body ga o'tkazish
  document.querySelectorAll('.modal-backdrop').forEach(_teleportModal);

  // Overlay click
  const overlay = document.querySelector('.sidebar-overlay');
  if (overlay) overlay.addEventListener('click', closeSidebar);

  // Nav link bosilsa yopish
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function () {
      if (window.innerWidth <= 768) {
        closeSidebar();
      }
    });
  });

  // Swipe close
  let touchStartX = 0;

  document.addEventListener('touchstart', e => {
    touchStartX = e.changedTouches[0].screenX;
  }, { passive: true });

  document.addEventListener('touchend', e => {
    const deltaX = touchStartX - e.changedTouches[0].screenX;
    if (deltaX > 60) closeSidebar();
  }, { passive: true });

  dismissMessages();
});
// ── DATA ──
const STATES = ['verde','naranja','rojo'];
const STATE_LABELS = { verde:'Funcional', naranja:'Con falla', rojo:'Requiere tecnico' };
const ROUTER_NAMES = [
  'Router-Alpha','Router-Bravo','Router-Charlie','Router-Delta','Router-Echo',
  'Router-Foxtrot','Router-Golf','Router-Hotel','Router-India','Router-Juliet'
];

let currentUser = null;
let currentRole = null;
let routers = [];
let eventLog = [];
let alertStack = [];
let stats = { totalUpTime: 0, totalChecks: 0 };
let autoInterval = null;
let socket = null;
let wsConnected = false;

// ── WEBSOCKET ──
function connectWebSocket() {
  if (socket && socket.connected) return;

  socket = io('http://127.0.0.1:5000', {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 2000,
    reconnectionAttempts: 10
  });

  socket.on('connect', () => {
    wsConnected = true;
    console.log('[WS] Conectado al servidor');
    showToast('Conectado al servidor novaNet', false);
    socket.emit('conectar_simulador');
  });

  socket.on('disconnect', () => {
    wsConnected = false;
    console.log('[WS] Desconectado del servidor');
  });

  socket.on('estado_completo', (data) => {
    console.log('[WS] Estado completo recibido:', data.routers.length, 'routers');
    syncRoutersFromBackend(data.routers);
  });

  socket.on('estado_actualizado', (event) => {
    console.log('[WS] Estado actualizado:', event.nombre, event.estado_anterior, '->', event.estado_nuevo);
    handleBackendStateChange(event);
  });

  socket.on('estado_cambiado', (data) => {
    if (!data.success) {
      showToast('Error: ' + data.mensaje, true);
    }
  });

  socket.on('falla_simulada', (data) => {
    if (data.error) {
      showToast(data.error, false);
    }
  });

  socket.on('connect_error', (err) => {
    console.log('[WS] Error de conexión:', err.message);
  });
}

function syncRoutersFromBackend(backendRouters) {
  backendRouters.forEach(br => {
    const local = routers.find(r => r.ip === br.ip);
    if (local) {
      const oldState = local.estado;
      local.estado = br.estado;
      local.backendData = br;
      if (oldState !== br.estado) {
        const entry = {
          time: Date.now(),
          router: br.nombre,
          routerId: local.id,
          from: oldState,
          to: br.estado,
          reason: 'Sincronización desde servidor',
        };
        eventLog.unshift(entry);
        if (br.estado === 'rojo') {
          showAlert(local, entry);
        }
      }
    }
  });
  updateAll();
}

function handleBackendStateChange(event) {
  const local = routers.find(r => r.ip === event.ip);
  if (local) {
    const oldState = local.estado;
    local.estado = event.estado_nuevo;
    local.backendData = event.router;

    if (oldState !== event.estado_nuevo) {
      const entry = {
        time: Date.now(),
        router: event.nombre,
        routerId: local.id,
        from: oldState,
        to: event.estado_nuevo,
        reason: event.razon || 'Cambio desde servidor',
      };
      eventLog.unshift(entry);

      if (event.estado_nuevo === 'rojo') {
        showAlert(local, entry);
      }
      showToast(`${event.nombre}: ${STATE_LABELS[oldState]} → ${STATE_LABELS[event.estado_nuevo]}`, event.estado_nuevo === 'rojo');
    }
  }
  updateAll();
}

function sendStateToBackend(ip, nuevoEstado, reason) {
  if (socket && socket.connected) {
    socket.emit('cambiar_estado', { ip, nuevo_estado: nuevoEstado, reason });
  }
}

// ── INIT ──
function initRouters() {
  routers = ROUTER_NAMES.map((name, i) => ({
    id: i + 1,
    name,
    ip: `192.168.${i + 1}.1`,
    estado: 'verde',
    lastChange: Date.now(),
    upSince: Date.now(),
    failCount: 0,
    totalFailTime: 0,
    backendData: null,
  }));
  updateAll();
}

// ── LOGIN / LOGOUT ──
// Clave de acceso del simulador.
// -> Configura aquí la clave que deseas usar (cámbiala antes de desplegar).
const CLAVE_DEFAULT = 'cambia_esta_clave';

function doLogin() {
  const user = document.getElementById('loginUser').value.trim();
  const pass = document.getElementById('loginPass').value.trim();
  const errorEl = document.getElementById('loginError');

  if (!user) {
    document.getElementById('loginUser').style.borderColor='var(--red)';
    return;
  }

  if (pass !== CLAVE_DEFAULT) {
    errorEl.style.display = 'block';
    document.getElementById('loginPass').style.borderColor='var(--red)';
    return;
  }

  errorEl.style.display = 'none';
  currentUser = user;
  currentRole = 'tecnico';
  document.getElementById('loginModal').classList.remove('active');
  document.getElementById('roleBadge').textContent = 'Tecnico';
  document.getElementById('roleBadge').className = 'role-badge role-tecnico';
  document.getElementById('userLabel').textContent = user;
  initRouters();
  startClock();
  startAutoSimulation();
  connectWebSocket();
}

function doLogout() {
  currentUser = null;
  currentRole = null;
  clearInterval(autoInterval);
  if (socket) {
    socket.disconnect();
    socket = null;
    wsConnected = false;
  }
  document.getElementById('loginModal').classList.add('active');
}

// ── CLOCK ──
function startClock() {
  const tick = () => {
    const d = new Date();
    document.getElementById('clock').textContent = d.toLocaleTimeString('es-ES') + ' · ' + d.toLocaleDateString('es-ES');
  };
  tick(); setInterval(tick, 1000);
}

// ── SIDEBAR TABS ──
function switchTab(id, el) {
  document.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.sidebar-panel').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('panel-' + id).classList.add('active');
}

// ── STATE CHANGES ──
function changeRouterState(id, newState, reason) {
  const r = routers.find(x => x.id === id);
  if (!r) return;
  const old = r.estado;
  if (old === newState) return;

  if (old !== 'verde') {
    r.totalFailTime += Date.now() - r.lastChange;
  }
  if (newState !== 'verde') {
    r.failCount++;
  } else {
    r.upSince = Date.now();
  }

  r.estado = newState;
  r.lastChange = Date.now();

  const entry = {
    time: Date.now(),
    router: r.name,
    routerId: r.id,
    from: old,
    to: newState,
    reason: reason || 'Cambio manual',
  };
  eventLog.unshift(entry);

  if (newState === 'rojo') {
    showAlert(r, entry);
  }

  sendStateToBackend(r.ip, newState, reason);
  updateAll();
}

function showAlert(router, entry) {
  const a = { router: router.name, time: entry.time, id: Date.now() + Math.random() };
  alertStack.unshift(a);
  renderAlerts();
  showToast(`ALERTA: ${router.name} requiere atencion tecnica`, true);
}

function showToast(msg, isAlert) {
  const c = document.getElementById('toastContainer');
  const t = document.createElement('div');
  t.className = 'toast' + (isAlert ? ' alert' : '');
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 5000);
}

// ── AUTO SIMULATION (30 min) ──
function startAutoSimulation() {
  scheduleNextFailure();
}

function scheduleNextFailure() {
  const delay = 1800000;
  autoInterval = setTimeout(() => {
    simulateRandomFailure();
    scheduleNextFailure();
  }, delay);

  setTimeout(() => simulateRandomFailure(), 30000);
}

function simulateRandomFailure() {
  const available = routers.filter(r => r.estado === 'verde');
  if (available.length === 0) { showToast('Todos los routers ya tienen fallas', false); return; }

  const victim = available[Math.floor(Math.random() * available.length)];
  const newState = Math.random() < 0.4 ? 'rojo' : 'naranja';
  changeRouterState(victim.id, newState, 'Falla automatica simulada en la red');
  showToast(`Simulacion: ${victim.name} cambio a ${STATE_LABELS[newState]}`, newState === 'rojo');
}

function simulateMultipleFailures() {
  let count = 0;
  const interval = setInterval(() => {
    const available = routers.filter(r => r.estado === 'verde');
    if (available.length === 0 || count >= 3) { clearInterval(interval); return; }
    simulateRandomFailure();
    count++;
  }, 500);
}

function resetAllRouters() {
  routers.forEach(r => {
    if (r.estado !== 'verde') {
      changeRouterState(r.id, 'verde', 'Restablecimiento masivo de la red');
    }
  });
  showToast('Todos los routers han sido restablecidos a funcional', false);
}

function reportIssue(id) {
  const r = routers.find(x => x.id === id);
  if (r) showToast(`Reporte enviado: ${r.name} — Un tecnico revisara el problema`, false);
}

// ── RENDERING ──
function updateAll() {
  renderRouterGrid();
  renderStats();
  renderAlerts();
  renderTimeline();
  renderFilterOptions();

  const progressSection = document.querySelector('.progress-section');
  const timelineControls = document.querySelector('.timeline-controls');
  if (progressSection) progressSection.style.display = 'block';
  if (timelineControls) timelineControls.style.display = 'flex';
}

function renderRouterGrid() {
  const grid = document.getElementById('routerGrid');
  grid.innerHTML = '';

  const notice = document.getElementById('clientNotice');
  const simControls = document.getElementById('simControls');
  notice.style.display = 'none';
  simControls.style.display = 'flex';

  routers.forEach(r => {
    const uptime = r.estado === 'verde'
      ? formatDuration(Date.now() - r.upSince)
      : formatDuration(Date.now() - r.lastChange) + ' en falla';

    const barColor = r.estado === 'verde' ? 'var(--green)' : r.estado === 'naranja' ? 'var(--orange)' : 'var(--red)';
    const barWidth = r.estado === 'verde' ? '100%' : r.estado === 'naranja' ? '60%' : '20%';

    let actionsHTML = '';
    if (r.estado === 'rojo') {
      actionsHTML += `<button class="btn-small btn-repair" onclick="event.stopPropagation();changeRouterState(${r.id},'verde','Reparado por tecnico')">Reparar</button>`;
    }
    STATES.forEach(s => {
      if (s !== r.estado) {
        actionsHTML += `<button class="btn-small" onclick="event.stopPropagation();changeRouterState(${r.id},'${s}','Cambio manual desde panel')">${STATE_LABELS[s]}</button>`;
      }
    });

    const card = document.createElement('div');
    card.className = `router-card state-${r.estado}`;
    card.innerHTML = `
      <div class="router-header">
        <div>
          <div class="router-name">${r.name}</div>
          <div class="router-id">ID: ${String(r.id).padStart(3,'0')} · IP: ${r.ip}</div>
        </div>
        <div class="status-dot ${r.estado}"></div>
      </div>
      <div class="router-status-text ${r.estado}">${STATE_LABELS[r.estado]}</div>
      <div class="router-info">
        Uptime: ${uptime}<br>
        Fallos totales: ${r.failCount}
      </div>
      <div class="router-bar"><div class="router-bar-fill" style="width:${barWidth};background:${barColor}"></div></div>
      <div class="router-actions">${actionsHTML}</div>
    `;
    grid.appendChild(card);
  });
}

function renderStats() {
  const verde = routers.filter(r => r.estado === 'verde').length;
  const naranja = routers.filter(r => r.estado === 'naranja').length;
  const rojo = routers.filter(r => r.estado === 'rojo').length;
  const n = routers.length;

  document.getElementById('statVerde').textContent = verde;
  document.getElementById('statNaranja').textContent = naranja;
  document.getElementById('statRojo').textContent = rojo;
  document.getElementById('statVerdePct').textContent = `${((verde/n)*100).toFixed(0)}% de la red`;
  document.getElementById('statNaranjaPct').textContent = `${((naranja/n)*100).toFixed(0)}% de la red`;
  document.getElementById('statRojoPct').textContent = `${((rojo/n)*100).toFixed(0)}% de la red`;

  const disp = ((verde / n) * 100).toFixed(1);
  document.getElementById('statDisp').textContent = disp + '%';

  const failedRouters = routers.filter(r => r.totalFailTime > 0);
  if (failedRouters.length > 0) {
    const avg = failedRouters.reduce((s,r) => s + r.totalFailTime, 0) / failedRouters.length;
    document.getElementById('statDisp').parentElement.querySelector('.sub').textContent =
      'Tiempo prom. en falla: ' + formatDuration(avg);
  }

  document.getElementById('barVerde').style.width = ((verde/n)*100) + '%';
  document.getElementById('barNaranja').style.width = ((naranja/n)*100) + '%';
  document.getElementById('barRojo').style.width = ((rojo/n)*100) + '%';
  document.getElementById('pctVerde').textContent = ((verde/n)*100).toFixed(0) + '%';
  document.getElementById('pctNaranja').textContent = ((naranja/n)*100).toFixed(0) + '%';
  document.getElementById('pctRojo').textContent = ((rojo/n)*100).toFixed(0) + '%';
}

function renderAlerts() {
  const list = document.getElementById('alertsList');
  const empty = document.getElementById('alertsEmpty');
  const rojoRouters = routers.filter(r => r.estado === 'rojo');

  if (rojoRouters.length === 0) {
    list.innerHTML = '';
    empty.style.display = 'block';
    empty.textContent = 'No hay alertas activas.';
    return;
  }
  empty.style.display = 'none';

  list.innerHTML = rojoRouters.map(r => {
    const since = formatDuration(Date.now() - r.lastChange);
    return `<div class="alert-item">
      <div class="alert-title">${r.name} — REQUIERE TECNICO</div>
      <div>En estado rojo desde hace ${since}</div>
      <div class="alert-time">IP: ${r.ip} · Fallos acumulados: ${r.failCount}</div>
    </div>`;
  }).join('');
}

function renderTimeline() {
  const filter = document.getElementById('timelineFilter').value;
  const list = document.getElementById('historyList');
  const empty = document.getElementById('historyEmpty');

  let events = eventLog;
  if (filter !== 'all') {
    events = events.filter(e => e.routerId === parseInt(filter));
  }

  if (events.length === 0) {
    list.innerHTML = '';
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';

  list.innerHTML = events.slice(0, 100).map(e => {
    const time = new Date(e.time).toLocaleTimeString('es-ES');
    return `<div class="history-item">
      <div class="history-time">${time}</div>
      <div class="history-msg">
        <strong>${e.router}</strong>:
        <span class="tag tag-${e.from}">${STATE_LABELS[e.from]}</span> →
        <span class="tag tag-${e.to}">${STATE_LABELS[e.to]}</span>
        <span style="color:var(--text-dim);font-size:10px;"> — ${e.reason}</span>
      </div>
    </div>`;
  }).join('');
}

function renderFilterOptions() {
  const sel = document.getElementById('timelineFilter');
  const current = sel.value;
  sel.innerHTML = '<option value="all">Todos los routers</option>';
  routers.forEach(r => {
    sel.innerHTML += `<option value="${r.id}">${r.name}</option>`;
  });
  sel.value = current;
}

// ── UTILS ──
function formatDuration(ms) {
  if (ms < 1000) return '0s';
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  const d = Math.floor(h / 24);
  if (d > 0) return `${d}d ${h % 24}h`;
  if (h > 0) return `${h}h ${m % 60}m`;
  if (m > 0) return `${m}m ${s % 60}s`;
  return `${s}s`;
}

// ── KEYBOARD ──
document.getElementById('loginUser').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});
document.getElementById('loginPass').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

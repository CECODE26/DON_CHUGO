(function () {
  const liveMeta = document.querySelector('meta[name="don-chugo-bills-live-url"]');
  const listMeta = document.querySelector('meta[name="don-chugo-bills-url"]');
  if (!liveMeta || !listMeta) return;

  let knownIds = null;
  let knownHelpIds = null;
  let polling = false;
  const dismissedKey = 'don-chugo-dismissed-bills';
  const dismissedHelpKey = 'don-chugo-dismissed-help';
  let dismissedIds = new Set(JSON.parse(sessionStorage.getItem(dismissedKey) || '[]'));
  let dismissedHelp = new Set(JSON.parse(sessionStorage.getItem(dismissedHelpKey) || '[]'));

  function beep() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const context = new AudioContext();
      [0, .18].forEach(delay => {
        const oscillator = context.createOscillator();
        const gain = context.createGain();
        oscillator.frequency.value = 740;
        gain.gain.setValueAtTime(.09, context.currentTime + delay);
        gain.gain.exponentialRampToValueAtTime(.001, context.currentTime + delay + .14);
        oscillator.connect(gain).connect(context.destination);
        oscillator.start(context.currentTime + delay);
        oscillator.stop(context.currentTime + delay + .14);
      });
    } catch (_) {}
  }

  function renderPending(solicitudes, hasNew) {
    const visible = solicitudes.filter(item => !dismissedIds.has(item.id));
    let alert = document.getElementById('dc-bills-live-alert');
    if (!visible.length) {
      if (alert) alert.remove();
      return;
    }

    const latest = visible[visible.length - 1];
    if (!alert) {
      alert = document.createElement('a');
      alert.id = 'dc-bills-live-alert';
      alert.className = 'dc-bills-live-alert';
      alert.href = listMeta.content;
      alert.addEventListener('click', () => {
        visible.forEach(item => dismissedIds.add(item.id));
        sessionStorage.setItem(dismissedKey, JSON.stringify([...dismissedIds]));
        alert.remove();
      });
      document.body.appendChild(alert);
    }
    alert.classList.toggle('has-new', hasNew);
    alert.innerHTML = `
      <span class="material-symbols-outlined">point_of_sale</span>
      <div>
        <strong>${visible.length} cuenta${visible.length === 1 ? '' : 's'} pendiente${visible.length === 1 ? '' : 's'}</strong>
        <small>Mesa ${latest.mesa ?? '—'} · ${latest.tipo} · $${latest.total.toFixed(2)}</small>
      </div>
      <span class="material-symbols-outlined dc-bills-arrow">arrow_forward</span>`;
  }

  // Llamadas de asistencia del cliente ("llamar mesero" desde el menú QR):
  // alerta flotante propia en la esquina inferior izquierda.
  function renderHelp(alertas, hasNew) {
    const visible = alertas.filter(item => !dismissedHelp.has(item.id));
    let alert = document.getElementById('dc-help-live-alert');
    if (!visible.length) {
      if (alert) alert.remove();
      return;
    }
    const latest = visible[visible.length - 1];
    if (!alert) {
      alert = document.createElement('a');
      alert.id = 'dc-help-live-alert';
      alert.className = 'dc-bills-live-alert dc-help-live-alert';
      alert.href = '/gerente/floor-plan/';
      alert.addEventListener('click', () => {
        visible.forEach(item => dismissedHelp.add(item.id));
        sessionStorage.setItem(dismissedHelpKey, JSON.stringify([...dismissedHelp]));
        alert.remove();
      });
      document.body.appendChild(alert);
    }
    alert.classList.toggle('has-new', hasNew);
    const titulo = visible.length === 1
      ? `Mesa ${latest.mesa ?? '—'} pide asistencia`
      : `${visible.length} mesas piden asistencia`;
    alert.innerHTML = `
      <span class="material-symbols-outlined">notifications_active</span>
      <div>
        <strong>${titulo}</strong>
        <small>${latest.mensaje || latest.tipo} · ${latest.fecha}</small>
      </div>
      <span class="material-symbols-outlined dc-bills-arrow">arrow_forward</span>`;
  }

  async function pollBills() {
    if (polling || document.hidden) return;
    polling = true;
    try {
      const response = await fetch(`${liveMeta.content}?_=${Date.now()}`, {
        cache: 'no-store',
        headers: { Accept: 'application/json', 'Cache-Control': 'no-cache' }
      });
      if (!response.ok) return;
      const data = await response.json();
      const solicitudes = data.solicitudes || [];
      const ids = new Set(solicitudes.map(item => item.id));
      const hasNew = knownIds !== null && solicitudes.some(item => !knownIds.has(item.id));
      renderPending(solicitudes, hasNew);
      const alertas = data.alertas || [];
      const helpIds = new Set(alertas.map(item => item.id));
      const hasNewHelp = knownHelpIds !== null && alertas.some(item => !knownHelpIds.has(item.id));
      renderHelp(alertas, hasNewHelp);
      if (hasNew || hasNewHelp) beep();
      knownIds = ids;
      knownHelpIds = helpIds;
    } catch (_) {
      // Se reintentará automáticamente sin interrumpir el trabajo de caja.
    } finally {
      polling = false;
    }
  }

  pollBills();
  window.setInterval(pollBills, 2000);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) pollBills();
  });
}());

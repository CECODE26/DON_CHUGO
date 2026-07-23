(function () {
  const signatureMeta = document.querySelector('meta[name="don-chugo-orders-signature"]');
  const maxIdMeta = document.querySelector('meta[name="don-chugo-orders-max-id"]');
  const urlMeta = document.querySelector('meta[name="don-chugo-orders-live-url"]');
  const statusUrlMeta = document.querySelector('meta[name="don-chugo-orders-status-url"]');
  if (!signatureMeta || !maxIdMeta || !urlMeta || !statusUrlMeta) return;

  let signature = signatureMeta.content;
  let maxId = parseInt(maxIdMeta.content, 10) || 0;
  let refreshing = false;

  function getCsrf() {
    const part = document.cookie.split(';').find(item => item.trim().startsWith('csrftoken='));
    return part ? decodeURIComponent(part.trim().split('=')[1]) : '';
  }

  function showNewOrderAlert() {
    const pendingAlert = sessionStorage.getItem('don-chugo-new-order-alert');
    if (!pendingAlert) return;
    sessionStorage.removeItem('don-chugo-new-order-alert');

    const alert = document.createElement('div');
    alert.className = 'dc-new-order-alert';
    alert.innerHTML = '<span class="material-symbols-outlined">notifications_active</span><div><strong>Nuevo pedido recibido</strong><small>El cliente añadió productos. Revisa la primera fila.</small></div>';
    document.body.appendChild(alert);
    window.setTimeout(() => alert.remove(), 7000);

    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const context = new AudioContext();
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.frequency.value = 880;
      gain.gain.setValueAtTime(.08, context.currentTime);
      gain.gain.exponentialRampToValueAtTime(.001, context.currentTime + .35);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start();
      oscillator.stop(context.currentTime + .35);
    } catch (_) {}
  }

  async function checkOrders() {
    if (refreshing || document.hidden) return;
    try {
      const response = await fetch(urlMeta.content, {
        headers: { Accept: 'application/json' },
        cache: 'no-store'
      });
      if (!response.ok) return;
      const data = await response.json();
      if (data.signature !== signature) {
        if ((parseInt(data.max_id, 10) || 0) > maxId) {
          sessionStorage.setItem('don-chugo-new-order-alert', '1');
        }
        refreshing = true;
        window.location.reload();
      }
    } catch (_) {
      // Un corte temporal de red no debe interrumpir el trabajo en la bandeja.
    }
  }

  async function changeOrderStatus(select) {
    const previous = select.dataset.current;
    select.disabled = true;
    select.classList.add('is-saving');
    try {
      const response = await fetch(statusUrlMeta.content, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrf(),
          Accept: 'application/json'
        },
        body: JSON.stringify({
          pedido_id: parseInt(select.dataset.orderId, 10),
          estado: select.value
        })
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo cambiar el estado');
      select.dataset.current = data.estado;
      select.classList.add('is-saved');
      const saved = document.createElement('span');
      saved.className = 'dc-order-status-saved-label';
      saved.textContent = 'Guardado';
      select.insertAdjacentElement('afterend', saved);
      window.setTimeout(() => saved.remove(), 1400);
      window.setTimeout(() => select.classList.remove('is-saved'), 1200);
      signature = '';
    } catch (error) {
      select.value = previous;
      window.alert(error.message);
    } finally {
      select.disabled = false;
      select.classList.remove('is-saving');
    }
  }

  document.addEventListener('change', event => {
    const select = event.target.closest('.dc-order-status-select');
    if (select) changeOrderStatus(select);
  });

  showNewOrderAlert();
  window.setInterval(checkOrders, 2000);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) checkOrders();
  });
}());

document.addEventListener('DOMContentLoaded', function () {
  const btn = document.querySelector('.mm-help-btn');
  if (!btn) return;
  const role = btn.dataset.role || 'cliente';
  const modalEl = document.getElementById('_mmHelpModal');
  const helpBody = document.getElementById('_mmHelpBody');
  const helpAction = document.getElementById('_mmHelpAction');
  const modal = new bootstrap.Modal(modalEl);

  const contents = {
    cliente: `Cómo usar el menú:
• Escanea el QR de la mesa para iniciar sesión.
• Navega en "Menú" y añade productos al carrito.
• Ve a "Carrito" para revisar y confirmar el pedido.
• Para pedir ayuda, pulsa "Ayuda" y el mesero será notificado.`,
    staff: `Panel de staff:
• Menú → Productos: administrar productos y precios.
• Pedidos: ver pedidos en curso y marcar como listos/entregados.
• Mesas: generar QR físicos y cerrar mesas.
• Usa la barra superior para filtrar y ver notificaciones.`
  };

  const actions = {
    cliente: { label: 'Solicitar mesero', handler: solicitarAyudaGlobal },
    staff: { label: 'Abrir Admin', handler: () => { window.location.href = '/admin/'; } }
  };

  btn.addEventListener('click', () => {
    helpBody.textContent = contents[role] || contents['cliente'];
    const action = actions[role] || actions['cliente'];
    helpAction.textContent = action.label;
    // remove previous listeners
    helpAction.replaceWith(helpAction.cloneNode(true));
    const newAction = document.getElementById('_mmHelpAction');
    newAction.addEventListener('click', () => {
      modal.hide();
      try { action.handler(); } catch (e) { console.warn('Help action failed', e); }
    }, { once: true });
    modal.show();
  });

  // If the cliente action refers to solicitarAyudaGlobal and it's not defined,
  // provide a safe fallback that shows a toast.
  function solicitarAyudaGlobal() {
    if (typeof window.solicitarAyudaGlobal === 'function') return window.solicitarAyudaGlobal(new Event('click'));
    if (typeof window.showToast === 'function') return window.showToast('Se solicitó ayuda', 'success');
    alert('Se solicitó ayuda al mesero');
  }
});

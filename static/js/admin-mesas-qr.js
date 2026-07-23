(function () {
  'use strict';

  function ensureModal() {
    let overlay = document.getElementById('donchugoQrOverlay');
    if (overlay) return overlay;

    overlay = document.createElement('div');
    overlay.id = 'donchugoQrOverlay';
    overlay.innerHTML = `
      <div class="donchugo-qr-modal" role="dialog" aria-modal="true" aria-labelledby="donchugoQrTitle">
        <button type="button" class="donchugo-qr-close" aria-label="Cerrar">×</button>
        <div class="donchugo-qr-brand">DON CHUGO</div>
        <div class="donchugo-qr-subtitle">CAFÉ · BAR</div>
        <h2 id="donchugoQrTitle">QR Mesa</h2>
        <img id="donchugoQrLarge" alt="Código QR de la mesa">
        <p id="donchugoQrUrl"></p>
        <div class="donchugo-qr-actions">
          <button type="button" id="donchugoQrPrint">🖨 Imprimir QR</button>
          <button type="button" id="donchugoQrDownload">↓ Descargar</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    const close = () => overlay.classList.remove('is-open');
    overlay.querySelector('.donchugo-qr-close').addEventListener('click', close);
    overlay.addEventListener('click', (event) => { if (event.target === overlay) close(); });
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape') close(); });
    overlay.querySelector('#donchugoQrDownload').addEventListener('click', downloadQR);
    overlay.querySelector('#donchugoQrPrint').addEventListener('click', printQR);
    return overlay;
  }

  function openQR(trigger) {
    const overlay = ensureModal();
    const numero = trigger.dataset.mesaNumero;
    const mesaId = trigger.dataset.mesaId;
    const src = `data:image/png;base64,${trigger.dataset.qr}`;
    const url = trigger.dataset.qrUrl || `${window.location.origin}/bienvenida/?mesa=${mesaId}`;
    overlay.querySelector('#donchugoQrTitle').textContent = `Mesa ${numero}`;
    overlay.querySelector('#donchugoQrTitle').dataset.numero = numero;
    overlay.querySelector('#donchugoQrLarge').src = src;
    overlay.querySelector('#donchugoQrUrl').textContent = url;
    overlay.classList.add('is-open');
  }

  function downloadQR() {
    const overlay = ensureModal();
    const numero = overlay.querySelector('#donchugoQrTitle').dataset.numero;
    const link = document.createElement('a');
    link.download = `qr-mesa-${numero}.png`;
    link.href = overlay.querySelector('#donchugoQrLarge').src;
    link.click();
  }

  function printQR() {
    const overlay = ensureModal();
    const numero = overlay.querySelector('#donchugoQrTitle').dataset.numero;
    const src = overlay.querySelector('#donchugoQrLarge').src;
    const url = overlay.querySelector('#donchugoQrUrl').textContent;
    const win = window.open('', '_blank', 'width=520,height=700');
    if (!win) return window.alert('Permite las ventanas emergentes para imprimir.');
    win.document.write(`<!doctype html><html><head><title>QR Mesa ${numero}</title><style>
      @page{margin:8mm}body{font-family:Arial,sans-serif;text-align:center;color:#302724;padding:20px}.brand{color:#991b1b;font-size:25px;font-weight:800;letter-spacing:1px}.sub{font-size:12px;letter-spacing:4px}.mesa{font-size:30px;font-weight:800;margin:22px 0 10px}.qr{width:300px;max-width:90%}.hint{font-size:17px;font-weight:700;margin-top:15px}.url{font-size:9px;color:#777;margin-top:12px;overflow-wrap:anywhere}</style></head><body>
      <div class="brand">DON CHUGO</div><div class="sub">CAFÉ · BAR</div><div class="mesa">MESA ${numero}</div><img class="qr" src="${src}"><div class="hint">Escanea para ordenar</div><div class="url">${url}</div>
      <script>window.onload=()=>{window.print();window.onafterprint=()=>window.close();}<\/script></body></html>`);
    win.document.close();
  }

  document.addEventListener('click', function (event) {
    const trigger = event.target.closest('.donchugo-qr-trigger');
    if (trigger) openQR(trigger);
  });
})();

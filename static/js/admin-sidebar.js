(function () {
  // v2: el sidebar arranca ABIERTO y solo se cierra si el administrador lo
  // cierra con la flechita; su elección persiste entre páginas y sesiones.
  // (La clave cambió de nombre para descartar el estado "cerrado" que la
  // versión anterior forzaba en cada carga.)
  const desktopKey = 'don-chugo-admin-sidebar-v2';

  function restoreDesktopState() {
    if (localStorage.getItem(desktopKey) === 'closed') {
      document.body.classList.add('dc-sidebar-closed');
    }
  }

  window.toggleDonChugoSidebar = function () {
    const closed = document.body.classList.toggle('dc-sidebar-closed');
    localStorage.setItem(desktopKey, closed ? 'closed' : 'open');
  };

  window.toggleDonChugoMobileSidebar = function () {
    document.body.classList.toggle('dc-mobile-sidebar-open');
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', restoreDesktopState);
  } else {
    restoreDesktopState();
  }
}());

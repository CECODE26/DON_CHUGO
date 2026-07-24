(function () {
  const desktopKey = 'don-chugo-admin-sidebar-closed';

  function restoreDesktopState() {
    // Sidebar SIEMPRE cerrado por defecto
    document.body.classList.add('dc-sidebar-closed');
    localStorage.setItem(desktopKey, '1');
  }

  window.toggleDonChugoSidebar = function () {
    const closed = document.body.classList.toggle('dc-sidebar-closed');
    localStorage.setItem(desktopKey, closed ? '1' : '0');
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

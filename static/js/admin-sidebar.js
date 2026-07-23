(function () {
  const desktopKey = 'don-chugo-admin-sidebar-closed';

  function restoreDesktopState() {
    if (localStorage.getItem(desktopKey) === '1') {
      document.body.classList.add('dc-sidebar-closed');
    }
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

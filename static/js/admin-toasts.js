document.addEventListener('DOMContentLoaded', () => {
  const toasts = document.querySelectorAll('.dc-toast');

  const dismiss = (toast) => {
    if (!toast || toast.classList.contains('is-leaving')) return;
    toast.classList.add('is-leaving');
    window.setTimeout(() => toast.remove(), 320);
  };

  toasts.forEach((toast, index) => {
    const rawMessage = toast.querySelector('.dc-toast-raw')?.textContent.trim() || '';
    const normalized = rawMessage.toLocaleLowerCase('es');
    const isError = toast.classList.contains('dc-toast--error');
    const isWarning = toast.classList.contains('dc-toast--warning');
    const isSuccess = toast.classList.contains('dc-toast--success');
    const icon = toast.querySelector('.dc-toast-icon');
    const title = toast.querySelector('.dc-toast-copy strong');
    const detail = toast.querySelector('.dc-toast-copy small');

    if (isError) {
      icon.textContent = 'error';
      title.textContent = 'No se pudo completar';
      detail.textContent = rawMessage;
    } else if (isWarning) {
      icon.textContent = 'warning';
      title.textContent = 'Atención';
      detail.textContent = rawMessage;
    } else if (isSuccess && /(elimin|borr|delete)/.test(normalized)) {
      icon.textContent = 'delete_sweep';
      title.textContent = 'Registro eliminado exitosamente';
      detail.textContent = 'La información se actualizó correctamente.';
    } else if (isSuccess) {
      icon.textContent = 'check_circle';
      title.textContent = 'Registro guardado exitosamente';
      detail.textContent = 'Los cambios se aplicaron correctamente.';
    } else {
      icon.textContent = 'info';
      title.textContent = 'Información';
      detail.textContent = rawMessage;
    }

    window.setTimeout(() => toast.classList.add('is-visible'), 60 + (index * 90));
    const timer = window.setTimeout(() => dismiss(toast), isError ? 7000 : 4200);
    toast.querySelector('.dc-toast-close')?.addEventListener('click', () => {
      window.clearTimeout(timer);
      dismiss(toast);
    });
  });
});

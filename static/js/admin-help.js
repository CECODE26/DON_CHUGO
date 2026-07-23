(function () {
  const root = document.getElementById('dc-help');
  if (!root) return;

  const panel = document.getElementById('dc-help-panel');
  const trigger = document.getElementById('dc-help-trigger');
  const closeButton = document.getElementById('dc-help-close');
  const overlay = document.getElementById('dc-help-overlay');
  const search = document.getElementById('dc-help-search');
  const topics = document.getElementById('dc-help-topics');
  const answer = document.getElementById('dc-help-answer');
  const back = document.getElementById('dc-help-back');

  const guides = {
    productos: {
      title: 'Agregar un producto',
      steps: ['Abre Menú y selecciona Productos.', 'Pulsa Agregar producto.', 'Completa nombre, precio y categoría.', 'Activa Disponible y guarda los cambios.'],
      url: '/admin/menu/producto/add/'
    },
    mesas: {
      title: 'Crear una mesa y ver su QR',
      steps: ['Abre Mesas y selecciona Mesas.', 'Pulsa Agregar mesa.', 'Indica número y capacidad.', 'Guarda; el código QR aparecerá automáticamente.'],
      url: '/admin/mesas/mesa/add/'
    },
    empleados: {
      title: 'Administrar empleados',
      steps: ['Abre Accounts y selecciona Empleados.', 'Pulsa Agregar empleado.', 'Asigna usuario, nombre y rol.', 'Define una contraseña segura y guarda.'],
      url: '/admin/accounts/empleado/'
    },
    pedidos: {
      title: 'Revisar pedidos',
      steps: ['Abre Pedidos.', 'Usa los filtros para localizar el pedido.', 'Abre el registro para consultar sus datos.', 'Evita borrar pedidos que formen parte del historial.'],
      url: '/admin/pedidos/pedido/'
    }
  };

  const contexts = [
    ['/admin/menu/producto', 'Productos', 'Aquí puedes crear productos, cambiar precios y controlar su disponibilidad.'],
    ['/admin/mesas/mesa', 'Mesas y códigos QR', 'Crea mesas y consulta el QR que utilizarán tus clientes.'],
    ['/admin/accounts/empleado', 'Empleados', 'Administra usuarios, roles y acceso al sistema.'],
    ['/admin/pedidos', 'Pedidos', 'Consulta el historial y estado de los pedidos.']
  ];

  const path = root.dataset.currentPath || '';
  const context = contexts.find(item => path.startsWith(item[0]));
  if (context) {
    document.getElementById('dc-help-context-title').textContent = context[1];
    document.getElementById('dc-help-context-text').textContent = context[2];
  }

  function setOpen(open) {
    panel.classList.toggle('is-open', open);
    panel.setAttribute('aria-hidden', String(!open));
    trigger.setAttribute('aria-expanded', String(open));
    overlay.hidden = !open;
    if (open) search.focus();
  }

  function showGuide(key) {
    const guide = guides[key];
    if (!guide) return;
    document.getElementById('dc-help-answer-title').textContent = guide.title;
    const steps = document.getElementById('dc-help-answer-steps');
    steps.replaceChildren(...guide.steps.map(text => {
      const item = document.createElement('li');
      item.textContent = text;
      return item;
    }));
    document.getElementById('dc-help-action').href = guide.url;
    topics.hidden = true;
    search.parentElement.querySelector('.dc-help-search-label').hidden = true;
    search.hidden = true;
    answer.hidden = false;
  }

  function showTopics() {
    answer.hidden = true;
    topics.hidden = false;
    search.hidden = false;
    search.parentElement.querySelector('.dc-help-search-label').hidden = false;
    search.value = '';
    topics.querySelectorAll('button').forEach(button => button.hidden = false);
  }

  trigger.addEventListener('click', () => setOpen(!panel.classList.contains('is-open')));
  closeButton.addEventListener('click', () => setOpen(false));
  overlay.addEventListener('click', () => setOpen(false));
  back.addEventListener('click', showTopics);
  topics.addEventListener('click', event => {
    const button = event.target.closest('[data-topic]');
    if (button) showGuide(button.dataset.topic);
  });
  search.addEventListener('input', () => {
    const term = search.value.trim().toLowerCase();
    topics.querySelectorAll('button').forEach(button => {
      button.hidden = term && !button.textContent.toLowerCase().includes(term);
    });
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') setOpen(false);
  });
}());

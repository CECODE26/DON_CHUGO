# 🎨 Guía de Personalización de Django Unfold - Don Chugo Café Bar

## Descripción General
Django Unfold es un moderno reemplazo del admin de Django con soporte completo para personalización mediante:
1. **Configuración en Python** (`UNFOLD` dict en settings.py)
2. **CSS personalizado** (static/css/unfold-custom.css)
3. **Plantillas HTML** (templates/admin/)

## Colores Actuales de Don Chugo

```
Rojo Vino (Primary):    #8B2E2E
Rojo Vino Dark:         #6B1F1F  
Dorado (Secondary):     #C9A961
Beige Claro:            #F5E6D3
Blanco Cálido:          #FEFDFB
```

## 📝 Archivo de Configuración: `config/settings.py`

La configuración de Unfold está en el diccionario `UNFOLD`:

### Variables Editables:

```python
UNFOLD = {
    # Encabezado del sitio
    "SITE_HEADER": "☕ Don Chugo",           # Cambiar nombre/emoji
    "SITE_TITLE": "Don Chugo Café Bar",      # Título en pestaña
    "SITE_SYMBOL": "☕",                      # Emoji/símbolo
    
    # Paleta de colores completa
    "COLORS": {
        "primary": {
            "50": "#f8f6f3",      # Más claro
            "100": "#ede5db",
            "200": "#dcc9b7",
            "300": "#c9a961",
            "400": "#b08d4d",
            "500": "#8B2E2E",     # Color principal (rojo vino)
            "600": "#7a2626",
            "700": "#6B1F1F",     # Más oscuro
            "800": "#5a1818",
            "900": "#491010",     # Más oscuro aún
        },
        "secondary": {
            "50": "#faf8f6",
            "100": "#f5e6d3",
            "200": "#ebc9a7",
            "300": "#e0ac7b",
            "400": "#d5934f",
            "500": "#C9A961",     # Dorado
            "600": "#b89553",
            "700": "#a78145",
            "800": "#966d37",
            "900": "#855929",
        },
    },
}
```

## 🎨 Archivo CSS: `static/css/unfold-custom.css`

Este archivo contiene TODAS las personalizaciones CSS y es completamente editable.

### Variables CSS Principales:

```css
:root {
  --don-chugo-primary: #8B2E2E;      /* Rojo vino */
  --don-chugo-primary-dark: #6B1F1F;
  --don-chugo-gold: #C9A961;         /* Dorado */
  --don-chugo-light: #F5E6D3;        /* Beige claro */
  --don-chugo-white: #FEFDFB;        /* Blanco cálido */
}
```

### Elementos Personalizables:

| Elemento | Selector CSS | Cambios Frecuentes |
|----------|-------------|-------------------|
| Header | `.unfold-header` | Color de fondo, altura, sombra |
| Sidebar | `.unfold-sidebar` | Ancho, color fondo, bordes |
| Botones | `.unfold-btn-primary`, `input[type="submit"]` | Color, tamaño, bordes redondeados |
| Campos | `input[type="text"]`, `textarea` | Borde, padding, hover, focus |
| Tablas | `table`, `thead`, `tbody` | Colores, espaciado, hover |
| Badges | `.unfold-badge`, `.unfold-badge-*` | Colores, tamaño fuente |
| Alertas | `.unfold-alert`, `.unfold-alert-*` | Estilos por tipo (success, error, warning, info) |

## 🔧 Cómo Personalizar

### Cambio 1: Modificar Color Principal

**Opción A - En settings.py:**
```python
"primary": {
    "500": "#C41E3A",  # Cambiar rojo a otro tono
}
```

**Opción B - En CSS:**
```css
:root {
  --don-chugo-primary: #C41E3A;
}
```

### Cambio 2: Cambiar Colores de Botones

En `static/css/unfold-custom.css`:

```css
.unfold-btn-primary,
input[type="submit"] {
  background: linear-gradient(135deg, #C41E3A 0%, #A01830 100%);
  /* Cambiar gradient según desees */
}
```

### Cambio 3: Personalizar Header/Logo

En `config/settings.py`:
```python
"SITE_HEADER": "🍕 Mi Nuevo Nombre",
"SITE_SYMBOL": "🍕",
```

### Cambio 4: Cambiar Ancho/Altura de Elementos

En `static/css/unfold-custom.css`:

```css
.unfold-sidebar {
  width: 280px;  /* Cambiar ancho del sidebar */
}

.unfold-header {
  padding: 20px;  /* Cambiar espaciado del header */
}

input[type="text"] {
  padding: 14px 16px;  /* Cambiar espaciado de campos */
}
```

### Cambio 5: Cambiar Estilos de Tablas

En `static/css/unfold-custom.css`:

```css
thead {
  background: linear-gradient(90deg, #C41E3A, #FFD700);
  /* Cambiar gradient para encabezados */
}

tbody tr:nth-child(even) {
  background-color: #FFF8E7;  /* Color alterno de filas */
}

tbody tr:hover {
  background-color: #FFE4B5;  /* Color al pasar mouse */
}
```

## 📱 Responsive Design

Todas las personalizaciones ya incluyen breakpoints para dispositivos móviles:

```css
@media (max-width: 768px) {
  /* Estilos para tablets y móviles */
}
```

Si necesitas ajustar tamaños en móvil, modifica esta sección.

## 🎯 Plantillas HTML

Ubicadas en `templates/admin/`:

- **`login.html`** - Página de login
- **`base_site.html`** - Base para todas las páginas
- **Otros archivos** - Se pueden crear para personalizar vistas específicas

### Editar Login:

En `templates/admin/login.html`, busca la sección `<style>` para cambiar:
- Colores de fondo
- Tamaño de formulario
- Espaciado y bordes
- Sombras

## 🚀 Pasos para Aplicar Cambios

### Cambios en CSS:
1. Edita `static/css/unfold-custom.css`
2. Guarda el archivo
3. Recarga el navegador (Cmd+Shift+R en Mac para limpiar caché)
4. Los cambios son inmediatos

### Cambios en Python (settings.py):
1. Edita `config/settings.py`
2. Guarda el archivo
3. **Reinicia el contenedor Docker**:
   ```bash
   docker compose restart web
   ```
4. Recarga el navegador

### Cambios en HTML (templates):
1. Edita `templates/admin/login.html` o `templates/admin/base_site.html`
2. Guarda el archivo
3. Recarga el navegador inmediatamente

## 📊 Variables Controlables en CSS

```css
/* Colores */
--don-chugo-primary: #8B2E2E;
--don-chugo-primary-dark: #6B1F1F;
--don-chugo-gold: #C9A961;
--don-chugo-light: #F5E6D3;
--don-chugo-white: #FEFDFB;

/* Espaciado (padding) */
padding: 12px 16px;

/* Bordes redondeados */
border-radius: 6px;

/* Sombras */
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

/* Transiciones y animaciones */
transition: all 0.2s ease;
```

## ✅ Checklist de Personalización Completa

- [ ] Colores primarios ajustados a marca
- [ ] Colores secundarios ajustados a marca
- [ ] Header/Logo personalizado
- [ ] Botones con estilos correctos
- [ ] Tablas con colores apropiados
- [ ] Formularios con estilos alineados
- [ ] Responsive design verificado en móvil
- [ ] Badges y alertas con colores correctos
- [ ] Hover effects funcionales
- [ ] Animaciones suave (transitions)

## 🎓 Recursos Útiles

- **Colors Unfold**: Los 10 valores en cada sección (50-900) van de más claro a más oscuro
- **Gradientes CSS**: `linear-gradient(dirección, color1, color2)`
- **Selectores CSS útiles**:
  - `.unfold-header` - Header/navbar
  - `.unfold-sidebar` - Menu lateral
  - `.unfold-btn-primary` - Botones principales
  - `input[type="text"]` - Campos de texto
  - `table` - Tablas
  - `.unfold-badge` - Etiquetas pequeñas
  - `.unfold-alert` - Mensajes de alerta

## 💡 Tips de Diseño

1. **Consistencia**: Usa siempre los mismos colores rojo vino y dorado
2. **Contraste**: Asegura que el texto sea legible sobre fondos
3. **Espaciado**: Mantén espaciado consistente (12px, 16px, 24px)
4. **Bordes**: Usa siempre `border-radius: 6px` para apariencia moderna
5. **Sombras**: Las sombras suaves (`0 2px 8px rgba(0,0,0,0.1)`) se ven profesionales

## 🆘 Solución de Problemas

**Cambios no aparecen:**
- Limpia caché del navegador (Cmd+Shift+R)
- Reconstruye el contenedor: `docker compose restart web`

**Estilos rotos:**
- Verifica sintaxis CSS (busca errores en herramientas de desarrollo)
- Abre inspector de elementos (F12) para debuggear

**Colores extraños:**
- Verifica valores hex (#RRGGBB)
- Usa herramientas online para validar colores

---

**Última actualización**: Configuración completa para Django Unfold v0.20.0
**Colores de marca**: Rojo Vino (#8B2E2E) + Dorado (#C9A961)

# ✅ Django Unfold Instalado y Configurado

## 🎉 ¿Qué se instaló?

Se ha reemplazado el admin básico de Django con **Django Unfold v0.20.0**, un admin moderno y completamente personalizable.

## 🎨 Características de Personalización

### 1. **Configuración Python** (`config/settings.py`)
- ✅ Diccionario `UNFOLD` con todos los parámetros
- ✅ Colores primarios y secundarios completamente editables
- ✅ Sitio header personalizado: `☕ Don Chugo`

### 2. **CSS Personalizado** (`static/css/unfold-custom.css`)
- ✅ Archivo CSS 100% editable con variables temáticas
- ✅ Estilos para header, sidebar, botones, tablas, formularios
- ✅ Responsive design incluido
- ✅ Animaciones suaves

### 3. **Plantillas HTML** (`templates/admin/`)
- ✅ `login.html` - Página de login personalizada
- ✅ `base_site.html` - Base para todas las páginas

## 🎯 Cambios de Color Rápidos

### Opción 1: Cambiar Color Principal
**Archivo**: `config/settings.py` (línea ~176)

```python
"primary": {
    "500": "#8B2E2E",  # ← Cambiar este hex
}
```

**Archivo**: `static/css/unfold-custom.css` (línea ~8)
```css
--don-chugo-primary: #8B2E2E;  /* ← O cambiar aquí */
```

### Opción 2: Cambiar Color de Dorado
**Archivo**: `config/settings.py` (línea ~185)
```python
"secondary": {
    "500": "#C9A961",  # ← Cambiar este hex
}
```

### Opción 3: Cambiar Estilo de Botones
**Archivo**: `static/css/unfold-custom.css` (línea ~51)
```css
.unfold-btn-primary {
  background: linear-gradient(135deg, #8B2E2E 0%, #6B1F1F 100%);  /* ← Cambiar colores */
}
```

## 📋 Próximos Pasos

### Para Cambios CSS (Inmediatos):
1. Edita `static/css/unfold-custom.css`
2. Guarda el archivo
3. Recarga el navegador (Cmd+Shift+R en Mac)

### Para Cambios Python (Requiere Restart):
1. Edita `config/settings.py`
2. Guarda el archivo
3. Ejecuta: `docker compose restart web`
4. Recarga el navegador

### Para Cambios HTML (Inmediatos):
1. Edita `templates/admin/login.html` o `templates/admin/base_site.html`
2. Guarda el archivo
3. Recarga el navegador

## 🔐 Admin Credentials
```
URL: http://localhost:8002/admin/
Usuario: admin
Contraseña: admin123
```

## 📖 Documentación Completa
Ver archivo: **`UNFOLD_CUSTOMIZATION.md`** para guía completa de personalización

## 🎨 Colores Actuales
| Elemento | Color | Hex |
|----------|-------|-----|
| Primario (Rojo Vino) | Rojo Vino | #8B2E2E |
| Primario Oscuro | Rojo Oscuro | #6B1F1F |
| Secundario (Dorado) | Dorado | #C9A961 |
| Fondo Claro | Beige | #F5E6D3 |
| Blanco Cálido | Blanco | #FEFDFB |

## 💡 Tips

1. **Busca visual**: Usa Chrome DevTools (F12) → Inspector para seleccionar elementos
2. **Nombres CSS**: Todos comienzan con `.unfold-` o son selectores HTML estándar
3. **Variables CSS**: `:root { --variable-name: value; }` se usa en todo el archivo
4. **Prueba colores**: Usa https://htmlcolorcodes.com/ para obtener hex codes

## ⚙️ Archivos Editables

```
mochi-matcha-main/
├── config/settings.py                 ← Configuración UNFOLD dict
├── static/css/
│   ├── admin.css                      ← CSS viejo (opcional)
│   └── unfold-custom.css              ← CSS personalizado (PRINCIPAL)
└── templates/admin/
    ├── login.html                     ← Página login personalizada
    ├── base_site.html                 ← Base template
    └── ... (otros templates)

UNFOLD_CUSTOMIZATION.md                 ← Guía completa (este archivo)
```

## 🆘 Problemas Comunes

**Problema**: Cambios no aparecen
```bash
# Solución 1: Limpiar caché navegador (Cmd+Shift+R)
# Solución 2: Reiniciar Docker
docker compose restart web
```

**Problema**: Error al editar colores
```
Verificar:
- Hex code válido (#RRGGBB)
- Comas correctas en listas Python
- Comillas correctas en CSS
```

---

**¡Listo para personalizar!** Todos los archivos están listos para editar.

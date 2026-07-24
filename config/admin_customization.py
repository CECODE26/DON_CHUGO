"""
config/admin_customization.py — Personalización global del Django Admin.

Cambia el título, header, pie de página e incluye CSS personalizado
para darle un look más moderno a la interfaz administrativa.
"""
from django.contrib import admin
from django.urls import reverse
from types import MethodType


def _prioritize_orders(admin_site):
    """Muestra Pedidos y Mesas al inicio del menú administrativo."""
    if getattr(admin_site, "_don_chugo_orders_first", False):
        return

    original_get_app_list = admin_site.get_app_list

    def get_app_list(self, request, app_label=None):
        app_list = original_get_app_list(request, app_label)
        # Caja no es una tabla editable: se agrega como módulo nativo para que
        # Unfold lo muestre y lo despliegue igual que Pedidos y Mesas.
        if app_label is None and not any(a.get("app_label") == "caja" for a in app_list):
            reporte_url = reverse("admin_reporte_caja_diario")
            facturar_url = reverse("admin:pedidos_solicitudpago_facturar_desde_caja")
            app_list.append({
                "name": "Caja",
                "app_label": "caja",
                "app_url": facturar_url,
                "has_module_perms": True,
                "models": [
                    {
                        # Cuentas abiertas por mesa: revisar el consumo y facturar
                        # de forma individual (por comensal) o la mesa completa.
                        "name": "Pedidos",
                        "object_name": "PedidosFacturar",
                        "admin_url": facturar_url,
                        "add_url": None,
                        "view_only": True,
                    },
                    {
                        "name": "Reporte y cierre diario",
                        "object_name": "ReporteCajaDiario",
                        "admin_url": reporte_url,
                        "add_url": None,
                        "view_only": True,
                    },
                ],
            })
        priority = {"pedidos": 0, "mesas": 1, "caja": 2}
        return sorted(
            app_list,
            key=lambda app: (
                priority.get(app.get("app_label"), 3),
                app.get("name", ""),
            ),
        )

    admin_site.get_app_list = MethodType(get_app_list, admin_site)
    admin_site._don_chugo_orders_first = True


def customize_admin():
    """Aplica personalizaciones al sitio del admin."""
    admin.site.site_header = "☕ Don Chugo — Panel de Administración"
    admin.site.site_title = "Don Chugo Admin"
    admin.site.index_title = "Bienvenido a la Gestión de Don Chugo Café Bar"
    admin.site.enable_nav_sidebar = True
    _prioritize_orders(admin.site)


customize_admin()

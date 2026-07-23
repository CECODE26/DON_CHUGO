from django.contrib import admin
from django.conf import settings
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter
import os
import uuid
from .models import Categoria, Producto, GrupoModificador, OpcionModificador, Promocion, TipoPromocion


class CategoriaFilter(SimpleListFilter):
    title = "Categoría"
    parameter_name = "categoria"

    def lookups(self, request, model_admin):
        return [(c.id, c.nombre) for c in Categoria.objects.order_by("orden")]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(categoria_id=self.value())
        return queryset

admin.site.register(Categoria)
admin.site.register(GrupoModificador)
admin.site.register(OpcionModificador)
admin.site.register(Promocion)
admin.site.register(TipoPromocion)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Formulario de productos organizado en tarjetas temáticas."""

    change_form_template = "admin/menu/producto/change_form.html"
    change_list_template = "admin/menu/producto/change_list.html"
    list_display = (
        "foto_lista", "nombre", "categoria", "precio", "disponible", "accion_foto",
        "accion_eliminar",
    )
    list_filter = (CategoriaFilter, "disponible")
    search_fields = ("nombre", "descripcion")
    list_editable = ("precio", "disponible")
    readonly_fields = ("vista_previa",)
    ordering = ("categoria", "nombre")
    actions = None  # sin acciones masivas: cada fila tiene su botón de eliminar

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["categorias"] = Categoria.objects.order_by("orden")
        return super().changelist_view(request, extra_context)

    @admin.display(description="Foto")
    def foto_lista(self, obj):
        if obj.imagen_url:
            return format_html(
                '<img class="dc-product-list-photo" src="{}" alt="Foto de {}">',
                obj.imagen_url,
                obj.nombre,
            )
        return format_html(
            '<span class="dc-product-list-photo dc-product-list-photo--empty" '
            'aria-label="Sin foto">photo_camera</span>'
        )

    @admin.display(description="Imagen")
    def accion_foto(self, obj):
        url = reverse("admin:menu_producto_change", args=[obj.pk])
        etiqueta = "Cambiar foto" if obj.imagen_url else "Subir foto"
        return format_html(
            '<a class="dc-product-photo-action" href="{}">'
            '<span class="material-symbols-outlined">add_a_photo</span>{}</a>',
            url,
            etiqueta,
        )

    @admin.display(description="Eliminar")
    def accion_eliminar(self, obj):
        url = reverse("admin:menu_producto_delete", args=[obj.pk])
        return format_html(
            '<a class="dc-product-delete-action" href="{}" title="Eliminar {}">'
            '<span class="material-symbols-outlined">delete</span></a>',
            url,
            obj.nombre,
        )

    def get_urls(self):
        custom = [
            path(
                "subir-imagen/",
                self.admin_site.admin_view(self.subir_imagen_view),
                name="menu_producto_subir_imagen",
            ),
        ]
        return custom + super().get_urls()

    def subir_imagen_view(self, request):
        """Guarda una foto de producto desde el formulario del administrador."""
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "Método no permitido."}, status=405)
        if not self.has_change_permission(request):
            return JsonResponse({"ok": False, "error": "Sin permiso."}, status=403)
        archivo = request.FILES.get("imagen")
        if not archivo:
            return JsonResponse({"ok": False, "error": "Selecciona una imagen."}, status=400)

        extensiones = {".jpg", ".jpeg", ".png", ".webp"}
        ext = os.path.splitext(archivo.name or "")[1].lower()
        if ext not in extensiones or not (archivo.content_type or "").startswith("image/"):
            return JsonResponse({"ok": False, "error": "Usa una imagen JPG, PNG o WEBP."}, status=400)
        if archivo.size > 5 * 1024 * 1024:
            return JsonResponse({"ok": False, "error": "La imagen supera el máximo de 5 MB."}, status=400)

        destino = os.path.join(settings.MEDIA_ROOT, "images")
        os.makedirs(destino, exist_ok=True)
        nombre = f"producto-{uuid.uuid4().hex[:12]}{ext}"
        with open(os.path.join(destino, nombre), "wb") as salida:
            for chunk in archivo.chunks():
                salida.write(chunk)
        return JsonResponse({"ok": True, "url": f"{settings.MEDIA_URL}images/{nombre}"})

    fieldsets = (
        ("Información del producto", {
            "fields": (
                "nombre",
                "descripcion",
                ("precio", "disponible"),
                "categoria",
                "imagen_url",
                "vista_previa",
            ),
            "description": "Completa los datos, precio, categoría e imagen del producto.",
            "classes": ("don-product-card", "don-card-info"),
        }),
    )

    @admin.display(description="Vista previa")
    def vista_previa(self, obj):
        if not obj or not obj.imagen_url:
            return "La vista previa aparecerá cuando guardes una imagen."
        return format_html(
            '<img src="{}" alt="Vista previa de {}" '
            'style="width:120px;height:90px;object-fit:cover;border-radius:12px;" />',
            obj.imagen_url,
            obj.nombre,
        )

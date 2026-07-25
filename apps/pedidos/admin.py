import json
import inspect

from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join

from .models import DetallePedido, Pedido, SolicitudPago
from apps.mesas.models import Mesa


class RangoFechaPedidoFilter(admin.SimpleListFilter):
    """Por defecto la bandeja muestra solo los pedidos de HOY (evita el ruido
    del historial). 'Historial completo' habilita ver todo lo anterior."""
    title = "rango de fechas"
    parameter_name = "rango"

    def lookups(self, request, model_admin):
        return (("todos", "Historial completo"),)

    def queryset(self, request, queryset):
        if self.value() == "todos":
            return queryset
        hoy = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return queryset.filter(fecha_hora_ingreso__gte=hoy)

    def choices(self, changelist):
        # Renombra la opción por defecto ("Todo") a "Solo hoy" para que sea claro.
        for choice in super().choices(changelist):
            if choice["query_string"] == changelist.get_query_string(remove=[self.parameter_name]):
                choice["display"] = "Solo hoy"
            yield choice


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """Bandeja de Caja con acceso al ticket térmico de cocina."""

    list_display = (
        "numero", "alerta_pedido", "mesa", "origen_pedido", "fecha_hora_ingreso",
        "cambio_estado_rapido", "total", "imprimir_cocina",
    )
    list_filter = (RangoFechaPedidoFilter, "estado", "modalidad", "fecha_hora_ingreso")
    search_fields = ("id", "sesion__mesa__numero_mesa", "sesion__alias")
    list_select_related = ("sesion", "sesion__mesa", "modalidad")
    ordering = ("-fecha_hora_ingreso",)
    change_list_template = "admin/pedidos/pedido/change_list.html"
    readonly_fields = ("contenido_del_pedido", "fecha_hora_ingreso")
    fieldsets = (
        ("Contenido del pedido", {
            "fields": ("contenido_del_pedido",),
        }),
        ("Información del pedido", {
            "fields": (
                "sesion", "modalidad", "estado", "empleado_entrega",
                "fecha_hora_ingreso", "fecha_hora_entrega",
                "motivo_cancelacion", "token_idempotencia",
            ),
        }),
    )

    @admin.display(description="Origen", ordering="modalidad__descripcion")
    def origen_pedido(self, obj):
        """Distingue el origen: para llevar, asistido en mesa, o QR del cliente."""
        if obj.sesion and obj.sesion.mesa.es_para_llevar:
            return format_html(
                '<span style="display:inline-flex;align-items:center;gap:4px;'
                'padding:3px 10px;border-radius:999px;background:#fdeee0;'
                'color:#a4570f;font-size:11px;font-weight:800;white-space:nowrap;">'
                '🥡 Para llevar</span>'
            )
        if obj.modalidad and obj.modalidad.descripcion == "asistido":
            return format_html(
                '<span style="display:inline-flex;align-items:center;gap:4px;'
                'padding:3px 10px;border-radius:999px;background:#fbf0dd;'
                'color:#8d5517;font-size:11px;font-weight:800;white-space:nowrap;">'
                '🤝 Asistido</span>'
            )
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;'
            'padding:3px 10px;border-radius:999px;background:#eef1f4;'
            'color:#5b6770;font-size:11px;font-weight:700;white-space:nowrap;">'
            '📱 QR</span>'
        )

    def get_queryset(self, request):
        # El recorte a "solo hoy" vive en RangoFechaPedidoFilter (list_filter):
        # un GET param propio aquí rompía el changelist de Django (redirect ?e=1).
        return super().get_queryset(request).prefetch_related(
            "detalles__producto", "detalles__modificadores"
        )

    def _live_signature(self):
        return "|".join(
            f"{pedido_id}:{estado}:{adiciones}:{actualizacion.isoformat()}"
            for pedido_id, estado, adiciones, actualizacion in Pedido.objects.order_by("id").values_list(
                "id", "estado", "cantidad_adiciones", "fecha_hora_actualizacion"
            )
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["pedidos_live_signature"] = self._live_signature()
        extra_context["pedidos_live_max_id"] = Pedido.objects.order_by("-id").values_list("id", flat=True).first() or 0
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description="Pedido", ordering="id")
    def numero(self, obj):
        return f"#{obj.pk:06d}"

    @admin.display(description="Alerta")
    def alerta_pedido(self, obj):
        if obj.cantidad_adiciones > 0:
            return format_html(
                '<span class="dc-order-extra-badge"><i></i> {} adición{}</span>',
                obj.cantidad_adiciones,
                "" if obj.cantidad_adiciones == 1 else "es",
            )
        return "—"

    @admin.display(description="Mesa", ordering="sesion__mesa__numero_mesa")
    def mesa(self, obj):
        m = obj.sesion.mesa
        return "—" if m.es_para_llevar else m.numero_mesa

    @admin.display(description="Total")
    def total(self, obj):
        return f"${sum(d.subtotal_calculado for d in obj.detalles.all()):.2f}"

    @admin.display(description="Estado")
    def cambio_estado_rapido(self, obj):
        opciones = format_html_join(
            "",
            '<option value="{}" {}>{}</option>',
            (
                (value, "selected" if value == obj.estado else "", label)
                for value, label in Pedido.ESTADOS
            ),
        )
        return format_html(
            '<select class="dc-order-status-select" data-order-id="{}" data-current="{}">{}</select>',
            obj.pk,
            obj.estado,
            opciones,
        )

    @admin.display(description="Desglose completo")
    def contenido_del_pedido(self, obj):
        if not obj or not obj.pk:
            return "El contenido aparecerá después de guardar el pedido."

        detalles = list(obj.detalles.all())
        if not detalles:
            return "Este pedido no contiene productos."

        filas = []
        for detalle in detalles:
            modificadores = ", ".join(
                f"{mod.nombre_display} ×{mod.cantidad}"
                for mod in detalle.modificadores.all()
            ) or "—"
            filas.append((
                detalle.cantidad,
                detalle.producto.nombre,
                modificadores,
                detalle.notas or "—",
                f"${detalle.subtotal_calculado:.2f}",
            ))

        cuerpo = format_html_join(
            "",
            "<tr><td>{}</td><td><strong>{}</strong></td><td>{}</td><td>{}</td><td class='dc-order-money'>{}</td></tr>",
            filas,
        )
        total = sum(detalle.subtotal_calculado for detalle in detalles)
        return format_html(
            "<div class='dc-order-breakdown'>"
            "<table><thead><tr><th>Cant.</th><th>Producto</th><th>Opciones / sabores</th><th>Notas</th><th>Subtotal</th></tr></thead>"
            "<tbody>{}</tbody><tfoot><tr><td colspan='4'>Total del pedido</td><td class='dc-order-money'>{}</td></tr></tfoot></table>"
            "</div>",
            cuerpo,
            f"${total:.2f}",
        )

    @admin.display(description="Cocina")
    def imprimir_cocina(self, obj):
        url = reverse("admin:pedidos_pedido_ticket_cocina", args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" class="button dc-kitchen-print">'
            '<span class="material-symbols-outlined">print</span>Imprimir cocina</a>', url
        )

    def get_urls(self):
        custom = [
            path(
                "estado-en-vivo/",
                self.admin_site.admin_view(self.estado_en_vivo_view),
                name="pedidos_pedido_estado_en_vivo",
            ),
            path(
                "cambiar-estado/",
                self.admin_site.admin_view(self.cambiar_estado_view),
                name="pedidos_pedido_cambiar_estado",
            ),
            path(
                "<int:pedido_id>/ticket-cocina/impreso/",
                self.admin_site.admin_view(self.ticket_cocina_impreso_view),
                name="pedidos_pedido_ticket_cocina_impreso",
            ),
            path(
                "<int:pedido_id>/ticket-cocina/",
                self.admin_site.admin_view(self.ticket_cocina_view),
                name="pedidos_pedido_ticket_cocina",
            ),
        ]
        return custom + super().get_urls()

    def estado_en_vivo_view(self, request):
        if not self.has_view_permission(request):
            return JsonResponse({"detail": "Sin permiso"}, status=403)
        return JsonResponse({
            "signature": self._live_signature(),
            "max_id": Pedido.objects.order_by("-id").values_list("id", flat=True).first() or 0,
        })

    def ticket_cocina_impreso_view(self, request, pedido_id):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        if not self.has_change_permission(request, pedido):
            return JsonResponse({"ok": False, "error": "Sin permiso"}, status=403)
        # Solo avanza desde Recibido. Reimprimir nunca hace retroceder un pedido
        # que ya esté Listo, Entregado, Pagado o Cancelado.
        if pedido.estado == "recibido":
            pedido.estado = "preparando"
            pedido.save(update_fields=["estado", "fecha_hora_actualizacion"])
        return JsonResponse({
            "ok": True,
            "estado": pedido.estado,
            "estado_display": pedido.get_estado_display(),
        })

    def cambiar_estado_view(self, request):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "Datos inválidos"}, status=400)

        pedido = get_object_or_404(Pedido, pk=data.get("pedido_id"))
        if not self.has_change_permission(request, pedido):
            return JsonResponse({"ok": False, "error": "Sin permiso"}, status=403)

        nuevo_estado = data.get("estado")
        estados_validos = dict(Pedido.ESTADOS)
        if nuevo_estado not in estados_validos:
            return JsonResponse({"ok": False, "error": "Estado inválido"}, status=400)

        pedido.estado = nuevo_estado
        update_fields = ["estado"]
        if nuevo_estado == "entregado":
            pedido.fecha_hora_entrega = timezone.now()
            pedido.empleado_entrega = request.user
            update_fields.extend(["fecha_hora_entrega", "empleado_entrega"])
        pedido.save(update_fields=update_fields)
        return JsonResponse({
            "ok": True,
            "estado": nuevo_estado,
            "estado_display": estados_validos[nuevo_estado],
        })

    def ticket_cocina_view(self, request, pedido_id):
        pedido = get_object_or_404(
            Pedido.objects.select_related("sesion__mesa").prefetch_related(
                "detalles__producto", "detalles__modificadores"
            ),
            pk=pedido_id,
        )
        return render(request, "admin/pedidos/ticket_cocina.html", {"pedido": pedido})


@admin.register(SolicitudPago)
class SolicitudPagoAdmin(admin.ModelAdmin):
    """Solicitudes de Caja con acceso al comprobante térmico del cliente."""

    list_display = (
        "id", "mesa_display", "cliente_display", "fecha_hora", "tipo", "estado_solicitud",
        "resumen_consumo", "total_display", "acciones_caja",
    )
    list_filter = ("estado_solicitud", "metodo_pago", "tipo", "fecha_hora")
    search_fields = ("id", "mesa__numero_mesa", "sesion__alias", "referencia_externa")
    list_select_related = ("mesa", "sesion", "estado_solicitud", "metodo_pago")
    change_list_template = "admin/pedidos/solicitudpago/change_list.html"
    readonly_fields = ("desglose_cuenta", "fecha_hora")
    fieldsets = (
        ("Cuenta y pedidos", {"fields": ("desglose_cuenta",)}),
        ("Información de cobro", {"fields": (
            "fecha_hora", "tipo", "sesion", "mesa", "sesiones_cubiertas",
            "estado_solicitud", "metodo_pago", "total_individual", "total_mesa",
            "propina_sugerida", "monto_efectivo", "monto_tarjeta",
            "monto_recibido", "cambio", "detalle_pago", "referencia_externa",
        )}),
    )

    def has_add_permission(self, request):
        return False

    def _pedidos_de_solicitud(self, obj):
        if obj.tipo == "individual" and obj.sesion_id:
            sesiones = [obj.sesion]
        else:
            cubiertas = list(obj.sesiones_cubiertas.all())
            if cubiertas:
                sesiones = cubiertas
            elif obj.mesa_id:
                sesiones = list(obj.mesa.sesiones.filter(estado="activa"))
            else:
                sesiones = []
        return list(
            Pedido.objects.filter(sesion__in=sesiones)
            .exclude(estado="cancelado")
            .select_related("sesion")
            .prefetch_related("detalles__producto", "detalles__modificadores")
            .order_by("fecha_hora_ingreso")
        )

    def _total_actual(self, obj):
        return sum(
            detalle.subtotal_calculado
            for pedido in self._pedidos_de_solicitud(obj)
            for detalle in pedido.detalles.all()
        )

    @admin.display(description="Mesa", ordering="mesa__numero_mesa")
    def mesa_display(self, obj):
        if not obj.mesa:
            return "—"
        return "🥡 Llevar" if obj.mesa.es_para_llevar else obj.mesa.numero_mesa

    @admin.display(description="Cliente")
    def cliente_display(self, obj):
        if obj.sesion_id:
            return obj.sesion.alias
        sesiones = list(obj.sesiones_cubiertas.all())
        if not sesiones and obj.mesa_id:
            sesiones = list(obj.mesa.sesiones.filter(estado="activa"))
        return ", ".join(s.alias for s in sesiones) or "Mesa completa"

    @admin.display(description="Total")
    def total_display(self, obj):
        return f"${self._total_actual(obj):.2f}"

    @admin.display(description="Pedidos")
    def resumen_consumo(self, obj):
        pedidos = self._pedidos_de_solicitud(obj)
        cantidad = sum(d.cantidad for p in pedidos for d in p.detalles.all())
        return f"{len(pedidos)} pedido(s) · {cantidad} producto(s)"

    @admin.display(description="Caja")
    def acciones_caja(self, obj):
        mesa = obj.mesa or (obj.sesion.mesa if obj.sesion else None)
        if not mesa:
            return "—"
        if obj.tipo == "individual" and obj.sesion_id:
            pago_url = (
                reverse("admin:pedidos_solicitudpago_cobrar_desde_caja")
                + f"?mesa={mesa.pk}&sesion={obj.sesion_id}"
            )
            accion_label = "Cobrar"
        else:
            pago_url = (
                reverse("admin:pedidos_solicitudpago_facturar_desde_caja")
                + f"?mesa={mesa.pk}"
            )
            accion_label = "Ver personas"
        comprobante_url = reverse("admin:pedidos_solicitudpago_comprobante", args=[obj.pk])
        return format_html(
            '<div class="dc-cash-actions">'
            '<a href="{}" class="dc-cash-charge"><span class="material-symbols-outlined">{}</span>{}</a>'
            '<a href="{}" target="_blank" class="dc-cash-print">'
            '<span class="material-symbols-outlined">receipt_long</span>Comprobante</a></div>',
            pago_url,
            "groups" if obj.tipo != "individual" else "point_of_sale",
            accion_label,
            comprobante_url,
        )

    @admin.display(description="Desglose completo")
    def desglose_cuenta(self, obj):
        if not obj or not obj.pk:
            return "El desglose aparecerá después de crear la solicitud."
        filas = []
        for pedido in self._pedidos_de_solicitud(obj):
            for detalle in pedido.detalles.all():
                opciones = ", ".join(m.nombre_display for m in detalle.modificadores.all()) or "—"
                filas.append((
                    f"#{pedido.pk}", pedido.sesion.alias, detalle.cantidad,
                    detalle.producto.nombre, opciones, f"${detalle.subtotal_calculado:.2f}",
                ))
        if not filas:
            return "No hay productos pendientes en esta cuenta."
        cuerpo = format_html_join(
            "",
            "<tr><td>{}</td><td>{}</td><td>{}</td><td><strong>{}</strong></td><td>{}</td><td class='dc-order-money'>{}</td></tr>",
            filas,
        )
        return format_html(
            "<div class='dc-order-breakdown'><table>"
            "<thead><tr><th>Pedido</th><th>Invitado</th><th>Cant.</th><th>Producto</th><th>Opciones</th><th>Subtotal</th></tr></thead>"
            "<tbody>{}</tbody><tfoot><tr><td colspan='5'>Total a cancelar</td><td class='dc-order-money'>{}</td></tr></tfoot>"
            "</table></div>", cuerpo, f"${self._total_actual(obj):.2f}"
        )

    @admin.display(description="Cliente")
    def imprimir_comprobante(self, obj):
        url = reverse("admin:pedidos_solicitudpago_comprobante", args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" class="button">Imprimir comprobante</a>', url
        )

    def get_urls(self):
        custom = [
            path(
                "cuentas-pendientes-en-vivo/",
                self.admin_site.admin_view(self.cuentas_pendientes_en_vivo_view),
                name="pedidos_solicitudpago_cuentas_pendientes_en_vivo",
            ),
            path(
                "facturar-desde-caja/",
                self.admin_site.admin_view(self.facturar_desde_caja_view),
                name="pedidos_solicitudpago_facturar_desde_caja",
            ),
            path(
                "cobrar/",
                self.admin_site.admin_view(self.cobrar_desde_caja_view),
                name="pedidos_solicitudpago_cobrar_desde_caja",
            ),
            path(
                "<int:solicitud_id>/comprobante/",
                self.admin_site.admin_view(self.comprobante_view),
                name="pedidos_solicitudpago_comprobante",
            ),
        ]
        return custom + super().get_urls()

    def facturar_desde_caja_view(self, request):
        if not self.has_view_permission(request):
            return JsonResponse({"detail": "Sin permiso"}, status=403)
        mesas = Mesa.objects.filter(sesiones__estado="activa")
        mesa_id = request.GET.get("mesa")
        if mesa_id:
            mesas = mesas.filter(pk=mesa_id)
        mesas = mesas.distinct().order_by("numero_mesa")
        filas = []
        for mesa in mesas:
            sesiones_data = []
            total_mesa = 0
            for sesion in mesa.sesiones.filter(estado="activa"):
                pedidos = sesion.pedidos.exclude(estado="cancelado").prefetch_related(
                    "detalles__producto", "detalles__modificadores"
                )
                # Detalle del consumo para que caja pueda revisar el pedido
                # antes de cobrar (expandible en la tarjeta del invitado).
                items = []
                for p in pedidos:
                    for d in p.detalles.all():
                        items.append({
                            "pedido_id": p.pk,
                            "estado": p.get_estado_display(),
                            "cantidad": d.cantidad,
                            "producto": d.producto.nombre,
                            "opciones": ", ".join(m.nombre_display for m in d.modificadores.all()),
                            "notas": d.notas,
                            "subtotal": d.subtotal_calculado,
                        })
                total = sum(i["subtotal"] for i in items)
                productos = sum(i["cantidad"] for i in items)
                total_mesa += total
                sesiones_data.append({
                    "sesion": sesion, "total": total,
                    "pedidos": pedidos.count(), "productos": productos,
                    "items": items,
                })
            # Agrupar comensales por grupo ("vengo con ellos"): cada grupo se
            # factura junto; grupos distintos (desconocidos compartiendo mesa)
            # jamás se mezclan en el cobro.
            grupos_map = {}
            for dato in sesiones_data:
                clave = dato["sesion"].grupo_key
                grupos_map.setdefault(clave, []).append(dato)
            grupos = [
                {
                    "key": clave,
                    "sesiones": datos,
                    "aliases": ", ".join(d["sesion"].alias for d in datos),
                    "total": sum(d["total"] for d in datos),
                }
                for clave, datos in grupos_map.items()
            ]
            filas.append({
                "mesa": mesa, "sesiones": sesiones_data, "total": total_mesa,
                "grupos": grupos, "un_solo_grupo": len(grupos) == 1,
            })
        context = {
            **self.admin_site.each_context(request),
            "title": "Facturar desde caja", "filas": filas, "opts": self.model._meta,
        }
        return render(request, "admin/pedidos/solicitudpago/facturar.html", context)

    def cobrar_desde_caja_view(self, request):
        if not self.has_change_permission(request):
            return JsonResponse({"detail": "Sin permiso"}, status=403)
        from apps.mesero import views as mesero_views
        request.pago_action_url = reverse("admin:pedidos_solicitudpago_cobrar_desde_caja")
        request.pago_redirect_admin = True
        if request.method == "POST":
            return inspect.unwrap(mesero_views.procesar_pago)(request)
        return inspect.unwrap(mesero_views.pago)(request)

    def cuentas_pendientes_en_vivo_view(self, request):
        if not self.has_view_permission(request):
            return JsonResponse({"detail": "Sin permiso"}, status=403)

        solicitudes = (
            SolicitudPago.objects
            .filter(estado_solicitud__descripcion__iexact="pendiente")
            .select_related("mesa", "sesion")
            .order_by("fecha_hora")
        )
        data = []
        for solicitud in solicitudes:
            total = self._total_actual(solicitud)
            mesa = solicitud.mesa or (solicitud.sesion.mesa if solicitud.sesion else None)
            data.append({
                "id": solicitud.pk,
                "mesa": mesa.numero_mesa if mesa else None,
                "tipo": solicitud.get_tipo_display(),
                "total": float(total),
                "fecha": timezone.localtime(solicitud.fecha_hora).strftime("%H:%M"),
            })

        # Llamadas de asistencia del cliente (botón "llamar mesero" del menú QR):
        # se notifican en el admin junto con las cuentas pendientes.
        from apps.mesas.models import AlertaMesero
        alertas = [
            {
                "id": alerta.pk,
                "mesa": alerta.mesa.numero_mesa if alerta.mesa else None,
                "tipo": alerta.get_tipo_display(),
                "mensaje": alerta.mensaje or "",
                "fecha": timezone.localtime(alerta.fecha_creacion).strftime("%H:%M"),
            }
            for alerta in AlertaMesero.objects.filter(atendida=False, tipo="ayuda")
            .select_related("mesa").order_by("fecha_creacion")
        ]
        return JsonResponse({"ok": True, "solicitudes": data, "alertas": alertas})

    def comprobante_view(self, request, solicitud_id):
        from apps.mesero.views import _ticket_context

        solicitud = get_object_or_404(SolicitudPago, pk=solicitud_id)
        context = _ticket_context(solicitud, request.user)
        return render(request, "admin/pedidos/comprobante.html", context)


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "producto", "cantidad", "subtotal_calculado", "listo")
    list_filter = ("listo", "producto__categoria")
    search_fields = ("pedido__id", "producto__nombre", "notas")

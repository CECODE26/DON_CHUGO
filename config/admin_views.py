from datetime import datetime
from decimal import Decimal

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from apps.pedidos.models import DetallePedido, Pedido, SolicitudPago


def _monto_cobrado(solicitud):
    """Monto real de la venta: consumo registrado más propina."""
    consumo = (
        solicitud.total_individual
        if solicitud.tipo == "individual"
        else solicitud.total_mesa
    ) or Decimal("0.00")
    return consumo + (solicitud.propina_sugerida or Decimal("0.00"))


@staff_member_required
def reporte_caja_diario(request):
    """Reporte imprimible de todos los cobros de una fecha local."""
    hoy = timezone.localdate()
    fecha_texto = request.GET.get("fecha", "")
    try:
        fecha = datetime.strptime(fecha_texto, "%Y-%m-%d").date() if fecha_texto else hoy
    except ValueError:
        fecha = hoy

    cobros = list(
        SolicitudPago.objects.filter(
            fecha_hora__date=fecha,
            estado_solicitud__descripcion__iexact="procesada",
            metodo_pago__isnull=False,
        )
        .select_related("mesa", "sesion", "metodo_pago")
        .order_by("fecha_hora", "pk")
    )

    total_consumo = Decimal("0.00")
    total_propinas = Decimal("0.00")
    total_efectivo = Decimal("0.00")
    total_tarjeta = Decimal("0.00")
    por_metodo = {}
    movimientos = []

    for cobro in cobros:
        consumo = (
            cobro.total_individual if cobro.tipo == "individual" else cobro.total_mesa
        ) or Decimal("0.00")
        propina = cobro.propina_sugerida or Decimal("0.00")
        total = _monto_cobrado(cobro)
        metodo = cobro.metodo_pago.descripcion if cobro.metodo_pago else "Sin método"
        metodo_upper = metodo.upper()

        total_consumo += consumo
        total_propinas += propina
        por_metodo[metodo] = por_metodo.get(metodo, Decimal("0.00")) + total

        if cobro.monto_efectivo is not None or cobro.monto_tarjeta is not None:
            total_efectivo += cobro.monto_efectivo or Decimal("0.00")
            total_tarjeta += cobro.monto_tarjeta or Decimal("0.00")
        elif "EFECTIVO" in metodo_upper:
            total_efectivo += total
        elif "TARJETA" in metodo_upper or "PAYPAL" in metodo_upper:
            total_tarjeta += total

        cliente = cobro.sesion.alias if cobro.sesion_id else "Mesa completa"
        movimientos.append({
            "cobro": cobro,
            "cliente": cliente,
            "consumo": consumo,
            "propina": propina,
            "total": total,
        })

    # El cierre debe detallar lo efectivamente cobrado, no todos los pedidos
    # creados ese día. Las sesiones cubiertas quedan congeladas al procesar el
    # pago y permiten reconstruir con precisión los productos de cada cobro.
    sesiones_cobradas_ids = set()
    for cobro in cobros:
        cubiertas = set(cobro.sesiones_cubiertas.values_list("pk", flat=True))
        if not cubiertas and cobro.sesion_id:
            cubiertas.add(cobro.sesion_id)
        sesiones_cobradas_ids.update(cubiertas)

    productos_vendidos = list(
        DetallePedido.objects
        .filter(pedido__sesion_id__in=sesiones_cobradas_ids)
        .exclude(pedido__estado="cancelado")
        .values("producto_id", "producto__nombre", "producto__categoria__nombre")
        .annotate(cantidad=Sum("cantidad"), total=Sum("subtotal_calculado"))
        .order_by("producto__categoria__nombre", "producto__nombre")
    )
    for producto in productos_vendidos:
        cantidad = producto["cantidad"] or 0
        producto["precio_promedio"] = (
            (producto["total"] / cantidad).quantize(Decimal("0.01"))
            if cantidad else Decimal("0.00")
        )

    pedidos_dia = Pedido.objects.filter(fecha_hora_ingreso__date=fecha)
    resumen_pedidos = pedidos_dia.aggregate(
        total=Count("id", distinct=True),
        cancelados=Count("id", filter=Q(estado="cancelado"), distinct=True),
        pagados=Count("id", filter=Q(estado="pagado"), distinct=True),
        productos=Sum(
            "detalles__cantidad",
            filter=Q(sesion_id__in=sesiones_cobradas_ids) & ~Q(estado="cancelado"),
        ),
    )

    context = {
        **admin.site.each_context(request),
        "title": "Reporte diario de caja",
        "fecha": fecha,
        "hoy": hoy,
        "movimientos": movimientos,
        "productos_vendidos": productos_vendidos,
        "por_metodo": sorted(por_metodo.items()),
        "total_consumo": total_consumo,
        "total_propinas": total_propinas,
        "total_cobrado": total_consumo + total_propinas,
        "total_efectivo": total_efectivo,
        "total_tarjeta": total_tarjeta,
        "resumen_pedidos": resumen_pedidos,
    }
    return render(request, "admin/caja/reporte_diario.html", context)

"""Servicios transaccionales para el ciclo de vida de mesas y sesiones."""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

from apps.mesas.models import Mesa, SesionCliente


def cerrar_sesiones_inactivas(ahora=None):
    """Cierra sesiones sin pedidos que superaron el límite de inactividad.

    La búsqueda inicial es global para permitir que el panel del mesero o el
    siguiente escaneo de QR limpien sesiones aunque el dispositivo abandonado ya
    no vuelva a conectarse. Cada candidato se valida de nuevo bajo bloqueo para
    no competir con la creación simultánea de un pedido.

    Retorna la cantidad de sesiones cerradas.
    """
    from apps.pedidos.models import Pedido

    ahora = ahora or timezone.now()
    minutos = max(1, int(getattr(settings, "CLIENT_INACTIVITY_MINUTES", 15)))
    limite = ahora - timedelta(minutes=minutos)

    pedido_vigente = Pedido.objects.filter(
        sesion_id=OuterRef("pk"),
    ).exclude(estado="cancelado")
    candidatas = list(
        SesionCliente.objects
        .filter(estado="activa", ultima_actividad__lt=limite)
        .annotate(tiene_pedido=Exists(pedido_vigente))
        .filter(tiene_pedido=False)
        .values_list("pk", flat=True)
    )

    cerradas = 0
    for sesion_id in candidatas:
        with transaction.atomic():
            sesion = (
                SesionCliente.objects
                .select_for_update()
                .filter(
                    pk=sesion_id,
                    estado="activa",
                    ultima_actividad__lt=limite,
                )
                .first()
            )
            if sesion is None:
                continue
            if sesion.pedidos.exclude(estado="cancelado").exists():
                continue

            mesa = Mesa.objects.select_for_update().get(pk=sesion.mesa_id)
            sesion.estado = "cerrada"
            sesion.save(update_fields=["estado"])
            cerradas += 1

            if not mesa.sesiones.filter(estado="activa").exists():
                mesa.estado = "libre"
                mesa.pin_actual = None
                mesa.nota_cierre = ""
                mesa.save(update_fields=["estado", "pin_actual", "nota_cierre"])

    return cerradas

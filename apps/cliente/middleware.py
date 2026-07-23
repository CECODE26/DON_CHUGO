"""Autenticación de clientes y cierre de sesiones abandonadas."""
import logging
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

CLIENT_COOKIE_NAME = "mm_session"
SESSION_DURATION_HOURS = 2
CLEANUP_INTERVAL_SECONDS = 60
CLEANUP_CACHE_KEY = "cliente:limpieza_sesiones_inactivas:v1"
POLLING_PATHS = ("/pedidos/estado/", "/sesion/estado/")

# Prefijos de ruta que no necesitan cookie de cliente: bienvenida (creación de sesión),
# áreas de staff (mesero, cocina, gerente) y recursos estáticos.
EXEMPT_PATHS = [
    "/bienvenida/",
    "/admin/",
    "/mesero/",
    "/cocina/",
    "/gerente/",
    "/accounts/",
    "/static/",
    "/media/",
]


class ClienteSessionMiddleware:
    """
    Middleware que resuelve la cookie mm_session en una instancia de SesionCliente
    y la adjunta a request.sesion_cliente antes de llamar a la vista.

    También expone request.sesion_pagada (bool) y request.carrito_count (int)
    para que las plantillas los usen sin consultas adicionales.
    Las rutas en EXEMPT_PATHS se dejan pasar sin verificar la cookie.
    """

    def __init__(self, get_response):
        """Almacena el callable de la siguiente capa del stack de middlewares."""
        self.get_response = get_response

    def __call__(self, request):
        """
        Procesa la request entrante:
        1. Inicializa los atributos de sesión en None/0/False.
        2. Omite la verificación en rutas exentas (staff, bienvenida, estáticos).
        3. Si existe la cookie mm_session, carga la SesionCliente correspondiente,
           verifica que no haya expirado (2 h desde fecha_inicio) y la asigna.
        4. En caso de token inválido o sesión expirada, elimina la cookie.
        """
        request.sesion_cliente = None
        request.carrito_count = 0
        request.sesion_pagada = False

        path = request.path

        # Ejecutar una limpieza global como máximo una vez por minuto. El mapa
        # del mesero y el siguiente escaneo QR también pasan por este middleware,
        # de modo que una app cerrada no necesita volver a conectarse.
        debe_limpiar = path.startswith(("/bienvenida/", "/mesero/")) or not any(
            path.startswith(p) for p in EXEMPT_PATHS
        )
        if debe_limpiar and cache.add(
            CLEANUP_CACHE_KEY, True, timeout=CLEANUP_INTERVAL_SECONDS
        ):
            try:
                from apps.mesas.services import cerrar_sesiones_inactivas
                cerrar_sesiones_inactivas()
            except Exception:
                logger.exception("No se pudieron limpiar las sesiones inactivas")

        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return self.get_response(request)

        token = request.COOKIES.get(CLIENT_COOKIE_NAME)
        if token:
            try:
                from apps.mesas.models import SesionCliente
                # Las sesiones cerradas tras el cobro siguen siendo reconocibles
                # por su cookie para mostrar el comprobante en modo solo lectura.
                # Ya no pueden crear pedidos porque las vistas exigen estado activa;
                # al pulsar "Salir" se elimina definitivamente la cookie.
                sesion = SesionCliente.objects.select_related("mesa").get(
                    token_cookie=token,
                    estado__in=("activa", "pagada", "cerrada"),
                )

                ahora = timezone.now()

                # La limpieza global está limitada a una vez por minuto; para la
                # sesión del request revalidamos siempre, evitando que una acción
                # tardía reviva una sesión que ya superó los 15 minutos.
                minutos = max(
                    1, int(getattr(settings, "CLIENT_INACTIVITY_MINUTES", 15))
                )
                limite_inactividad = ahora - timedelta(minutes=minutos)
                if (
                    sesion.estado == "activa"
                    and sesion.ultima_actividad < limite_inactividad
                    and not sesion.pedidos.exclude(estado="cancelado").exists()
                ):
                    from apps.mesas.services import cerrar_sesiones_inactivas
                    cerrar_sesiones_inactivas(ahora=ahora)
                    sesion.refresh_from_db()

                # Las cookies de comprobantes antiguos se eliminan a las 2 horas.
                # Una sesión activa con pedidos nunca se cierra por tiempo.
                expira_en = sesion.fecha_inicio + timedelta(hours=SESSION_DURATION_HOURS)
                if ahora > expira_en and sesion.estado != "activa":
                    response = self.get_response(request)
                    response.delete_cookie(CLIENT_COOKIE_NAME)
                    return response

                fue_pagada = sesion.estado == "pagada"
                if sesion.estado == "cerrada":
                    fue_pagada = (
                        sesion.solicitudes_pago.filter(
                            estado_solicitud__descripcion="procesada"
                        ).exists()
                        or sesion.solicitudes_que_la_cubren.filter(
                            estado_solicitud__descripcion="procesada"
                        ).exists()
                    )

                # Una sesión abandonada termina de verdad: no se carga como
                # autenticada, se limpia el carrito y la vista redirige al QR.
                if sesion.estado == "cerrada" and not fue_pagada:
                    request.session.pop("carrito", None)
                    response = self.get_response(request)
                    response.delete_cookie(CLIENT_COOKIE_NAME)
                    return response

                request.sesion_cliente = sesion
                # Bandera para vistas/plantillas: la cuenta ya se saldó. La
                # sesión sigue navegable en modo solo-lectura (sin nuevos
                # pedidos) hasta que el cliente decida salir.
                request.sesion_pagada = fue_pagada

                # Los endpoints de polling no representan actividad humana. El
                # resto de navegación/acciones renueva el límite de 15 minutos.
                if sesion.estado == "activa" and not path.startswith(POLLING_PATHS):
                    SesionCliente.objects.filter(pk=sesion.pk).update(
                        ultima_actividad=ahora
                    )
                    sesion.ultima_actividad = ahora

                carrito = request.session.get("carrito", [])
                request.carrito_count = len(carrito)

            except Exception:
                response = self.get_response(request)
                response.delete_cookie(CLIENT_COOKIE_NAME)
                return response

        return self.get_response(request)

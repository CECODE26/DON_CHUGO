from django.db import transaction
from django.http import JsonResponse
from django.test import RequestFactory, TestCase

from apps.catalogs.models import EstadoSolicitud, ModalidadIngreso
from apps.cliente.middleware import ClienteSessionMiddleware
from apps.mesas.models import AlertaMesero, Mesa, SesionCliente
from apps.mesero.views import _post_pago_mesa
from apps.pedidos.models import SolicitudPago


class CierreAutomaticoDespuesDePagoTests(TestCase):
    def setUp(self):
        self.modalidad = ModalidadIngreso.objects.create(descripcion="qr")
        self.mesa = Mesa.objects.create(
            numero_mesa=91,
            capacidad=4,
            codigo_qr="mesa-91-test",
            estado="ocupada",
            pin_actual="1234",
        )

    def crear_sesion(self, alias, estado):
        return SesionCliente.objects.create(
            alias=alias,
            token_cookie=f"token-{alias}",
            estado=estado,
            mesa=self.mesa,
            modalidad_ingreso=self.modalidad,
        )

    def test_ultimo_pago_cierra_sesion_y_libera_mesa(self):
        sesion = self.crear_sesion("cliente-pagado", "pagada")

        with transaction.atomic():
            _post_pago_mesa(self.mesa)

        sesion.refresh_from_db()
        self.mesa.refresh_from_db()
        self.assertEqual(sesion.estado, "cerrada")
        self.assertEqual(self.mesa.estado, "libre")
        self.assertIsNone(self.mesa.pin_actual)
        self.assertEqual(self.mesa.nota_cierre, "")
        self.assertTrue(
            AlertaMesero.objects.filter(
                mesa=self.mesa,
                mensaje__icontains="liberada automáticamente",
            ).exists()
        )

    def test_pago_individual_no_cierra_otras_sesiones_activas(self):
        pagada = self.crear_sesion("cliente-pagado", "pagada")
        activa = self.crear_sesion("cliente-activo", "activa")

        with transaction.atomic():
            _post_pago_mesa(self.mesa)

        pagada.refresh_from_db()
        activa.refresh_from_db()
        self.mesa.refresh_from_db()
        self.assertEqual(pagada.estado, "cerrada")
        self.assertEqual(activa.estado, "activa")
        self.assertEqual(self.mesa.estado, "ocupada")
        self.assertEqual(self.mesa.pin_actual, "1234")
        self.assertIn("1 sesión(es) activa(s)", self.mesa.nota_cierre)

    def test_cliente_cerrado_conserva_acceso_de_solo_lectura_al_comprobante(self):
        sesion = self.crear_sesion("cliente-cerrado", "cerrada")
        procesada = EstadoSolicitud.objects.create(descripcion="procesada")
        SolicitudPago.objects.create(
            tipo="individual",
            sesion=sesion,
            mesa=self.mesa,
            estado_solicitud=procesada,
        )
        request = RequestFactory().get("/sesion/estado/")
        request.COOKIES["mm_session"] = sesion.token_cookie
        request.session = {}

        middleware = ClienteSessionMiddleware(
            lambda req: JsonResponse({
                "sesion_id": req.sesion_cliente.pk if req.sesion_cliente else None,
                "sesion_pagada": req.sesion_pagada,
            })
        )
        response = middleware(request)

        self.assertJSONEqual(response.content, {
            "sesion_id": sesion.pk,
            "sesion_pagada": True,
        })

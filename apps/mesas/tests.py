from datetime import timedelta

from django.test import RequestFactory, TestCase, override_settings
from django.http import JsonResponse
from django.utils import timezone

from apps.catalogs.models import ModalidadIngreso
from apps.cliente.middleware import ClienteSessionMiddleware
from apps.mesas.models import Mesa, SesionCliente
from apps.mesas.services import cerrar_sesiones_inactivas
from apps.pedidos.models import Pedido


@override_settings(CLIENT_INACTIVITY_MINUTES=15)
class CierrePorInactividadTests(TestCase):
    def setUp(self):
        self.modalidad = ModalidadIngreso.objects.create(descripcion="qr")
        self.mesa = Mesa.objects.create(
            numero_mesa=93,
            capacidad=4,
            codigo_qr="mesa-93-test",
            estado="ocupada",
            pin_actual="4321",
        )

    def crear_sesion(self, alias, minutos_inactiva=16):
        sesion = SesionCliente.objects.create(
            alias=alias,
            token_cookie=f"token-{alias}",
            estado="activa",
            mesa=self.mesa,
            modalidad_ingreso=self.modalidad,
        )
        SesionCliente.objects.filter(pk=sesion.pk).update(
            ultima_actividad=timezone.now() - timedelta(minutes=minutos_inactiva)
        )
        sesion.refresh_from_db()
        return sesion

    def test_sesion_sin_pedidos_se_cierra_y_libera_mesa(self):
        sesion = self.crear_sesion("abandono")

        cerradas = cerrar_sesiones_inactivas()

        sesion.refresh_from_db()
        self.mesa.refresh_from_db()
        self.assertEqual(cerradas, 1)
        self.assertEqual(sesion.estado, "cerrada")
        self.assertEqual(self.mesa.estado, "libre")
        self.assertIsNone(self.mesa.pin_actual)

    def test_sesion_con_pedido_nunca_se_cierra_por_inactividad(self):
        sesion = self.crear_sesion("con-pedido", minutos_inactiva=120)
        Pedido.objects.create(sesion=sesion, modalidad=self.modalidad)

        cerradas = cerrar_sesiones_inactivas()

        sesion.refresh_from_db()
        self.mesa.refresh_from_db()
        self.assertEqual(cerradas, 0)
        self.assertEqual(sesion.estado, "activa")
        self.assertEqual(self.mesa.estado, "ocupada")

    def test_no_libera_mesa_si_queda_otro_cliente_activo(self):
        abandonada = self.crear_sesion("abandono-parcial")
        activa = self.crear_sesion("cliente-presente", minutos_inactiva=1)

        cerrar_sesiones_inactivas()

        abandonada.refresh_from_db()
        activa.refresh_from_db()
        self.mesa.refresh_from_db()
        self.assertEqual(abandonada.estado, "cerrada")
        self.assertEqual(activa.estado, "activa")
        self.assertEqual(self.mesa.estado, "ocupada")

    def test_cookie_abandonada_se_elimina_y_no_simula_pago(self):
        sesion = self.crear_sesion("cookie-abandonada")
        cerrar_sesiones_inactivas()
        request = RequestFactory().get("/menu/")
        request.COOKIES["mm_session"] = sesion.token_cookie
        request.session = {"carrito": [{"producto_id": 1}]}

        middleware = ClienteSessionMiddleware(
            lambda req: JsonResponse({
                "autenticada": req.sesion_cliente is not None,
                "pagada": req.sesion_pagada,
                "carrito": req.session.get("carrito"),
            })
        )
        response = middleware(request)

        self.assertJSONEqual(response.content, {
            "autenticada": False,
            "pagada": False,
            "carrito": None,
        })

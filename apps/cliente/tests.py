from django.test import TestCase

from apps.catalogs.models import ModalidadIngreso
from apps.mesas.models import Mesa, SesionCliente


class BienvenidaMesaTests(TestCase):
    def setUp(self):
        self.modalidad = ModalidadIngreso.objects.create(descripcion="qr")
        self.mesa = Mesa.objects.create(
            numero_mesa=92,
            capacidad=4,
            codigo_qr="mesa-92-test",
            estado="ocupada",
        )

    def test_ignora_step_cerrando_obsoleto_si_no_hay_sesiones_pagadas(self):
        SesionCliente.objects.create(
            alias="cliente-activo",
            token_cookie="token-cliente-activo",
            estado="activa",
            mesa=self.mesa,
            modalidad_ingreso=self.modalidad,
        )

        response = self.client.get(
            f"/bienvenida/?mesa={self.mesa.pk}&step=mesa_cerrando"
        )

        self.assertContains(response, "¡Bienvenido!")
        self.assertNotContains(response, "Estamos preparando tu mesa")

    def test_muestra_cerrando_si_realmente_hay_sesion_pagada(self):
        SesionCliente.objects.create(
            alias="cliente-pagado",
            token_cookie="token-cliente-pagado",
            estado="pagada",
            mesa=self.mesa,
            modalidad_ingreso=self.modalidad,
        )

        response = self.client.get(f"/bienvenida/?mesa={self.mesa.pk}")

        self.assertContains(response, "Estamos preparando tu mesa")

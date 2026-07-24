#!/usr/bin/env python
"""
Crea (o recrea) el superusuario admin.

La contraseña ya NO va en el código: es obligatorio pasarla por variable de
entorno para no dejar claves débiles en el repositorio ni resetear producción
por accidente.

Uso:
    ADMIN_PASSWORD='clave-fuerte' python create_admin.py
    ADMIN_USUARIO=otro ADMIN_PASSWORD='clave-fuerte' python create_admin.py
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import Empleado

usuario = os.environ.get('ADMIN_USUARIO', 'admin')
password = os.environ.get('ADMIN_PASSWORD')

if not password:
    sys.exit(
        "ERROR: define ADMIN_PASSWORD en el entorno.\n"
        "  Ejemplo: ADMIN_PASSWORD='clave-fuerte' python create_admin.py"
    )

if Empleado.objects.filter(usuario=usuario).exists():
    respuesta = input(f"El usuario '{usuario}' ya existe. ¿Recrearlo? [s/N]: ")
    if respuesta.strip().lower() != 's':
        sys.exit("Cancelado.")
    Empleado.objects.filter(usuario=usuario).delete()

e = Empleado.objects.create_user(
    username=usuario,
    password=password,
    nombre='Administrador',
    rol='admin',
)
e.is_superuser = True
e.is_staff = True
e.save()

print(f"✓ Superusuario creado: usuario={usuario} (contraseña: la que definiste en ADMIN_PASSWORD)")

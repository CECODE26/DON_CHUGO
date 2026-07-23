#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import Empleado

# Eliminar admin anterior si existe
Empleado.objects.filter(usuario='admin').delete()

# Crear nuevo admin
# create_user espera (username, password, **extra_fields)
# y mapea username → usuario internamente
e = Empleado.objects.create_user(
    username='admin',
    password='admin123',
    nombre='Admin Local',
    rol='admin'
)
e.is_superuser = True
e.is_staff = True
e.save()

print(f"✓ Superuser created: usuario=admin, password=admin123")

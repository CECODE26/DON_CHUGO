"""
config/settings.py — Configuración central del proyecto Django "Mochi Matcha".

Todas las variables sensibles se leen desde variables de entorno para separar
configuración del código (12-factor app). Si una variable no está definida,
se usa un valor por defecto apropiado para desarrollo local.

Variables de entorno relevantes:
  SECRET_KEY, DEBUG, ALLOWED_HOSTS, SITE_BASE_URL
  MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT
  PAYPAL_CLIENT_ID, PAYPAL_SECRET, PAYPAL_MODO
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# FIX: DEBUG default False (era 'True')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# SECRET_KEY obligatoria en producción: sin fallback inseguro. En desarrollo
# (DEBUG=True) se permite una clave dummy para no exigir .env completo.
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-solo-para-desarrollo-local'
    else:
        raise ImproperlyConfigured(
            'SECRET_KEY no está definida. Agrega SECRET_KEY=... al archivo .env.'
        )

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

# URL base del sitio para generación de QR y links absolutos
SITE_BASE_URL = os.environ.get('SITE_BASE_URL', 'http://localhost:8000')

# Sesiones que solo navegaron el menú se cierran después de este tiempo. Las
# sesiones con pedidos confirmados quedan protegidas hasta el cobro o cierre manual.
CLIENT_INACTIVITY_MINUTES = int(os.environ.get('CLIENT_INACTIVITY_MINUTES', '15'))

# PayPal
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_SECRET    = os.environ.get('PAYPAL_SECRET', '')
PAYPAL_MODO      = os.environ.get('PAYPAL_MODO', 'sandbox')

INSTALLED_APPS = [
    'unfold',  # Django Unfold admin moderno
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # FIX: rutas actualizadas a apps.*
    # Módulos de datos (núcleo)
    'apps.accounts',   # modelo Empleado (AUTH_USER_MODEL)
    'apps.catalogs',   # catálogos auxiliares (ModalidadIngreso, MetodoPago, etc.)
    'apps.menu',       # Categoria, Producto, Modificadores, Promociones
    'apps.mesas',      # Mesa, SesionCliente, AlertaMesero
    'apps.pedidos',    # Pedido, DetallePedido, SolicitudPago
    'apps.auditoria',  # log de acciones del sistema
    # Módulos de interfaz (por rol)
    'apps.cliente',    # menú digital del cliente (QR)
    'apps.mesero',     # panel de mesero (mapa de mesas, alertas, entregas)
    'apps.cocina',     # KDS (Kitchen Display System) para cocina y bar
    'apps.gerente',    # dashboard, reportes, configuración
]

# FIX: apunta a apps.accounts
AUTH_USER_MODEL = 'accounts.Empleado'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # Debe ir ANTES de SessionMiddleware: reescribe la cookie de sesión por módulo.
    'config.middleware.StaffSessionIsolationMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # FIX: ruta actualizada a apps.cliente
    # Inyecta request.sesion_cliente para las vistas del menú digital.
    'apps.cliente.middleware.ClienteSessionMiddleware',
    # Modo mantenimiento (después de auth para detectar staff)
    'config.middleware.MaintenanceModeMiddleware',
    # Horarios de atención (3.1): bloquea clientes fuera de horario
    'config.middleware.HorarioAtencionMiddleware',
]

# Permite visualizar la app dentro de VS Code Simple Browser durante desarrollo.
# En producción mantenemos protección anti-clickjacking.
if not DEBUG:
    MIDDLEWARE.append('django.middleware.clickjacking.XFrameOptionsMiddleware')

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DATABASE', 'mochi_matcha'),
        'USER': os.environ.get('MYSQL_USER', 'root'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD', ''),
        'HOST': os.environ.get('MYSQL_HOST', 'db'),
        'PORT': os.environ.get('MYSQL_PORT', '3306'),
        'OPTIONS': {
            # utf8mb4 = UTF-8 completo (incluye emojis 4-byte). Sin esto, la
            # conexión cae a utf8mb3 y los INSERT con 🍵, etc. revientan con
            # OperationalError 1366 "Incorrect string value".
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', NAMES utf8mb4",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Guayaquil'  # Hora local de Don Chugo, Ecuador
USE_I18N = True
USE_TZ = True  # Usar fechas con timezone en la BD; timezone.now() devuelve UTC

# FIX: STATIC_URL con slashes correctas
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF_TRUSTED_ORIGINS: dominios desde los que Django acepta POST con el header Origin.
# ngrok-free.app se incluye para pruebas con túnel público en desarrollo.
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'CSRF_TRUSTED_ORIGINS',
        'http://localhost:8002,http://127.0.0.1:8002',
    ).split(',')
    if origin.strip()
]

# ── Producción detrás de proxy HTTPS (Nginx + Certbot) ───────────────────────
# Activar con HTTPS_ENABLED=True en el .env del servidor. En local queda apagado
# para que HTTP plano siga funcionando. Nginx envía X-Forwarded-Proto y hace la
# redirección HTTP→HTTPS, por eso SECURE_SSL_REDIRECT no es necesario aquí.
HTTPS_ENABLED = os.environ.get('HTTPS_ENABLED', 'False') == 'True'
if HTTPS_ENABLED:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ===== Django Unfold Configuration =====
UNFOLD = {
    "SITE_HEADER": "☕ Don Chugo",
    "SITE_TITLE": "Don Chugo Café Bar",
    "SITE_SYMBOL": "☕",  # Unicode symbol
    # Registro global: algunas vistas de Unfold 0.20 no heredan base_site.html.
    "STYLES": [lambda request: "/static/css/unfold-custom.css"],
    "COLORS": {
        "primary": {
            "50": "#fdf0f1",
            "100": "#fbe1e4",
            "200": "#f7bac1",
            "300": "#ef8290",
            "400": "#e33f54",
            "500": "#C81024",
            "600": "#aa101f",
            "700": "#861714",
            "800": "#651715",
            "900": "#451011",
        },
        "secondary": {
            "50": "#faf8f6",
            "100": "#f5e6d3",
            "200": "#ebc9a7",
            "300": "#e0ac7b",
            "400": "#d5934f",
            "500": "#A96B1F",
            "600": "#8d5517",
            "700": "#713f11",
            "800": "#51240C",
            "900": "#351707",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_logout": True,
    },
    "CSS": {
        "vars": {
            "colors": {
                "primary": {
                    "50": "#f8f6f3",
                    "500": "#8B2E2E",
                    "600": "#7a2626",
                    "700": "#6B1F1F",
                },
                "accent": {
                    "500": "#C9A961",
                    "600": "#b89553",
                },
            },
        },
    },
}

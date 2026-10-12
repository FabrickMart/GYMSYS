"""
Django settings for gymsys project.

GYMSYS-MMA — Sistema de Gestión y Control Administrativo
para un Gimnasio de Artes Marciales Mixtas.
"""

from pathlib import Path

from decouple import config
from django.contrib.messages import constants as messages


# ============================================================
# Rutas base
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# Seguridad
# ============================================================

SECRET_KEY = config('DJANGO_SECRET_KEY')

DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = []


# ============================================================
# Aplicaciones
# ============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps del proyecto
    'apps.usuarios',
    'apps.auditoria',
]


# ============================================================
# Middleware
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ============================================================
# URLs y WSGI
# ============================================================

ROOT_URLCONF = 'gymsys.urls'

WSGI_APPLICATION = 'gymsys.wsgi.application'


# ============================================================
# Templates
# ============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ============================================================
# Base de datos (MySQL)
# ============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# ============================================================
# Validación de contraseñas
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 10},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ============================================================
# Internacionalización
# ============================================================

LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_TZ = True


# ============================================================
# Archivos estáticos
# ============================================================

STATIC_URL = 'static/'

STATICFILES_DIRS = [BASE_DIR / 'static']

STATIC_ROOT = BASE_DIR / 'staticfiles'


# ============================================================
# Configuración por defecto de modelos
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# ============================================================
# CONFIGURACIÓN ESPECÍFICA DE GYMSYS-MMA
# ============================================================
# ============================================================

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'usuarios.Usuario'

# Sesión expira tras 15 min de inactividad
SESSION_COOKIE_AGE = 900
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Cookies seguras (en producción con HTTPS se activan solas)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Redirecciones de autenticación
LOGIN_URL = 'usuarios:login'
LOGIN_REDIRECT_URL = 'usuarios:dashboard'
LOGOUT_REDIRECT_URL = 'usuarios:login'

# Parámetros de bloqueo por intentos fallidos
MAX_INTENTOS_LOGIN = 3
MINUTOS_BLOQUEO = 15

# Mapeo de niveles de mensajes de Django a clases de Bootstrap
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# ============================================================
# Configuración de seguridad y sesiones — GYMSYS-MMA
# ============================================================

# Sesión expira tras 15 min de inactividad
SESSION_COOKIE_AGE = 900
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Cookies seguras (en desarrollo con HTTP no aplican, en producción sí)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Redirecciones de auth
LOGIN_URL = 'usuarios:login'
LOGIN_REDIRECT_URL = 'usuarios:dashboard'
LOGOUT_REDIRECT_URL = 'usuarios:login'

# Parámetros del bloqueo por intentos fallidos
MAX_INTENTOS_LOGIN = 3
MINUTOS_BLOQUEO = 15

# Directorio de templates a nivel proyecto
TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']

# Archivos estáticos
STATICFILES_DIRS = [BASE_DIR / 'static']

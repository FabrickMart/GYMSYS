from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from apps.auditoria.models import Evento
from apps.auditoria.utils import registrar_evento


def rol_requerido(*roles_permitidos):
    """
    Decorador que verifica que el usuario tenga uno de los roles indicados.
    Uso:
        @rol_requerido('admin')
        def mi_vista(request): ...

        @rol_requerido('admin', 'personal')
        def otra_vista(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.rol not in roles_permitidos and not request.user.is_superuser:
                registrar_evento(
                    Evento.Accion.ACCESO_DENEGADO,
                    request=request,
                    usuario=request.user,
                    descripcion=f'Intento de acceso a {request.path} sin permisos',
                    exitoso=False,
                )
                raise PermissionDenied('No tienes permisos para acceder a esta sección.')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def solo_admin(view_func):
    """Atajo: solo administradores."""
    return rol_requerido('admin')(view_func)


def admin_o_personal(view_func):
    """Atajo: cualquier usuario autenticado con rol válido."""
    return rol_requerido('admin', 'personal')(view_func)


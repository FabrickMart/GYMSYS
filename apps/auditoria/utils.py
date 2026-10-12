import logging

from .models import Evento

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    """Obtiene la IP real del cliente, considerando proxies."""
    if request is None:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def registrar_evento(
    accion,
    request=None,
    usuario=None,
    usuario_afectado=None,
    descripcion='',
    exitoso=True,
    metadata=None,
):
    """
    Registra un evento de auditoría. Nunca lanza excepción al caller:
    si falla el log, se anota en el logger de Python pero no rompe la operación.

    Uso típico:
        registrar_evento(Evento.Accion.LOGIN_OK, request=request, usuario=u)
    """
    try:
        Evento.objects.create(
            accion=accion,
            usuario=usuario,
            usuario_afectado=usuario_afectado,
            descripcion=descripcion,
            ip=_get_client_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT', '')[:255] if request else ''),
            exitoso=exitoso,
            metadata=metadata,
        )
    except Exception as e:
        logger.exception(f'Error registrando evento de auditoría: {e}')

"""
Servicio de recibos: genera PDF y envía por email.
"""
import logging
from io import BytesIO

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from apps.pagos.models import Suscripcion
from apps.auditoria.models import Evento
from apps.auditoria.utils import registrar_evento

logger = logging.getLogger(__name__)


def _contexto_recibo(pago):
    """Contexto común para el HTML del recibo."""
    alumno = pago.alumno
    suscripcion, _ = Suscripcion.objects.get_or_create(alumno=alumno)
    suscripcion.recalcular()

    return {
        'pago': pago,
        'alumno': alumno,
        'suscripcion': suscripcion,
        'gym': settings.GYM_DATOS_FISCALES,
        'fecha_emision': timezone.now(),
        'modo_impresion': False,
    }


def generar_pdf_pago(pago):
    """Genera el PDF del recibo. Devuelve BytesIO."""
    from weasyprint import HTML

    html_string = render_to_string('recibos/recibo_pago.html', _contexto_recibo(pago))
    buffer = BytesIO()
    HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf(buffer)
    buffer.seek(0)
    return buffer


def enviar_pdf_pago(pago, request=None, destinatario=None, mensaje_custom=None):
    """Envía el recibo por email. Devuelve (ok, error)."""
    alumno = pago.alumno
    destinatario = destinatario or alumno.email

    if not destinatario:
        return False, 'El alumno no tiene email registrado.'

    try:
        pdf_buffer = generar_pdf_pago(pago)

        asunto = f'Recibo de pago {pago.folio} — {settings.GYM_DATOS_FISCALES["nombre"]}'
        cuerpo = mensaje_custom or (
            f'Hola {alumno.nombre_completo()},\n\n'
            f'Adjuntamos el recibo de tu pago con folio {pago.folio} '
            f'por ${pago.monto_final}.\n\n'
            f'¡Gracias por seguir entrenando con nosotros!\n\n'
            f'— El equipo de {settings.GYM_DATOS_FISCALES["nombre"]}'
        )

        email = EmailMessage(
            subject=asunto,
            body=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario],
        )
        email.attach(f'recibo_{pago.folio}.pdf', pdf_buffer.getvalue(), 'application/pdf')
        email.send(fail_silently=False)

        registrar_evento(
            Evento.Accion.OTRO,
            request=request,
            usuario=getattr(request, 'user', None),
            descripcion=f'Recibo {pago.folio} enviado a {destinatario}',
            metadata={'pago_id': pago.id, 'folio': pago.folio, 'destinatario': destinatario},
        )
        return True, ''

    except Exception as e:
        logger.exception(f'Error enviando recibo {pago.folio}: {e}')
        return False, str(e)

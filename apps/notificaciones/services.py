"""
Servicio de notificaciones.
Encapsula la lógica de decidir a quién enviar, qué mensaje, y registrar
el resultado. Los emails se envían con el backend configurado en settings
(console en desarrollo, smtp en producción).
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.pagos.models import Suscripcion, ConfiguracionDescuento

from .models import ConfiguracionNotificacion, Plantilla, Notificacion

logger = logging.getLogger(__name__)


class NotificacionService:
    """
    Orquesta el envío de notificaciones por email.
    """

    def __init__(self):
        self.config = ConfiguracionNotificacion.get()

    # ============================================================
    # Render de plantillas
    # ============================================================

    def _render(self, texto, contexto):
        """Reemplaza variables {nombre} etc. con sus valores."""
        try:
            return texto.format(**contexto)
        except KeyError as e:
            logger.warning(f'Variable faltante en plantilla: {e}')
            return texto

    def _construir_contexto(self, suscripcion, dias_diferencia=None):
        """Contexto para las plantillas."""
        alumno = suscripcion.alumno
        gym = getattr(settings, 'GYM_NOMBRE', 'MG Team')
        ctx = {
            'nombre': alumno.nombre_completo(),
            'gym': gym,
            'fecha_vencimiento': suscripcion.fecha_vencimiento.strftime('%d/%m/%Y')
            if suscripcion.fecha_vencimiento else '—',
            'plan': suscripcion.plan_actual.nombre if suscripcion.plan_actual else '—',
        }
        if dias_diferencia is not None:
            ctx['dias'] = abs(dias_diferencia)
        return ctx

    # ============================================================
    # Envío
    # ============================================================

    def _enviar_email(self, destino, asunto, mensaje):
        """
        Envía el email usando el backend configurado.
        Devuelve (ok: bool, error: str).
        """
        try:
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destino],
                fail_silently=False,
            )
            return True, ''
        except Exception as e:
            logger.exception(f'Error enviando email a {destino}: {e}')
            return False, str(e)

    def _crear_y_enviar(self, suscripcion, tipo, dias_diferencia=None):
        """
        Crea el registro de la Notificacion y envía el email.
        Devuelve la Notificacion creada (o None si no aplica).
        """
        alumno = suscripcion.alumno

        # 1) Verificar idempotencia: ¿ya se envió hoy este tipo?
        if Notificacion.ya_enviada_hoy(alumno, suscripcion, tipo):
            logger.info(f'Ya se envió {tipo} hoy a {alumno.matricula}')
            return None

        # 2) Verificar que tenga email
        if not alumno.email:
            logger.info(f'Alumno {alumno.matricula} sin email, no se envía')
            return None

        # 3) Obtener plantilla
        try:
            plantilla = Plantilla.objects.get(codigo=tipo, activa=True)
        except Plantilla.DoesNotExist:
            logger.warning(f'No hay plantilla activa para {tipo}')
            return None

        # 4) Renderizar
        contexto = self._construir_contexto(suscripcion, dias_diferencia)
        asunto = self._render(plantilla.asunto, contexto)
        mensaje = self._render(plantilla.cuerpo, contexto)

        # 5) Crear la Notificacion en estado pendiente
        notif = Notificacion.objects.create(
            alumno=alumno,
            suscripcion=suscripcion,
            tipo=tipo,
            canal=Notificacion.Canal.EMAIL,
            destino=alumno.email,
            asunto=asunto,
            mensaje=mensaje,
            estado=Notificacion.Estado.PENDIENTE,
        )

        # 6) Enviar
        ok, error = self._enviar_email(alumno.email, asunto, mensaje)

        # 7) Actualizar estado
        notif.intentos += 1
        if ok:
            notif.estado = Notificacion.Estado.ENVIADO
            notif.enviado_en = timezone.now()
        else:
            notif.estado = Notificacion.Estado.FALLIDO
            notif.error_mensaje = error
        notif.save()

        return notif

    # ============================================================
    # Flujos por tipo
    # ============================================================

    def enviar_por_vencer(self):
        """Envía recordatorios a suscripciones que vencen en N días."""
        if not self.config.activo:
            return []

        hoy = timezone.now().date()
        fecha_objetivo = hoy + timedelta(days=self.config.dias_antes_por_vencer)

        suscripciones = Suscripcion.objects.filter(
            fecha_vencimiento=fecha_objetivo,
            estado__in=[
                Suscripcion.Estado.ACTIVO,
                Suscripcion.Estado.POR_VENCER,
            ],
        ).select_related('alumno', 'plan_actual')

        resultados = []
        for s in suscripciones:
            dias = (s.fecha_vencimiento - hoy).days
            notif = self._crear_y_enviar(s, Plantilla.Codigo.POR_VENCER, dias_diferencia=dias)
            if notif:
                resultados.append(notif)
        return resultados

    def enviar_vencidos(self):
        """Envía aviso diario a suscripciones vencidas hasta el límite."""
        if not self.config.activo:
            return []

        hoy = timezone.now().date()
        fecha_minima = hoy - timedelta(days=self.config.dias_despues_vencido_max)

        suscripciones = Suscripcion.objects.filter(
            estado__in=[
                Suscripcion.Estado.VENCIDO,
                Suscripcion.Estado.EN_GRACIA,
            ],
            fecha_vencimiento__gte=fecha_minima,
            fecha_vencimiento__lt=hoy,
        ).select_related('alumno', 'plan_actual')

        resultados = []
        for s in suscripciones:
            dias = (hoy - s.fecha_vencimiento).days
            notif = self._crear_y_enviar(s, Plantilla.Codigo.VENCIDO, dias_diferencia=dias)
            if notif:
                resultados.append(notif)
        return resultados

    def enviar_todos(self):
        """Ejecuta todos los flujos. Devuelve un resumen."""
        por_vencer = self.enviar_por_vencer()
        vencidos = self.enviar_vencidos()
        return {
            'por_vencer': por_vencer,
            'vencidos': vencidos,
            'total': len(por_vencer) + len(vencidos),
        }

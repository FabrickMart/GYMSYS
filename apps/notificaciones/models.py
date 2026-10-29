from django.db import models
from django.utils import timezone


class ConfiguracionNotificacion(models.Model):
    """
    Configuración global del módulo de notificaciones (singleton).
    """
    activo = models.BooleanField(default=True, verbose_name='Notificaciones activas')
    dias_antes_por_vencer = models.PositiveSmallIntegerField(
        default=5,
        verbose_name='Días antes del vencimiento para avisar',
    )
    dias_despues_vencido_max = models.PositiveSmallIntegerField(
        default=5,
        verbose_name='Días después del vencimiento para dejar de avisar',
    )
    hora_envio = models.TimeField(
        default='10:00',
        verbose_name='Hora de envío',
        help_text='Hora sugerida para ejecutar el cron.',
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de notificaciones'
        verbose_name_plural = 'Configuración de notificaciones'

    def __str__(self):
        return 'Configuración de notificaciones'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Plantilla(models.Model):
    """
    Plantillas de email para las notificaciones.
    Las variables disponibles se marcan con {nombre}, {fecha}, {gym}, etc.
    """
    class Codigo(models.TextChoices):
        POR_VENCER = 'por_vencer', 'Por vencer'
        VENCIDO = 'vencido', 'Vencido'
        INSCRIPCION_PENDIENTE = 'inscripcion_pendiente', 'Inscripción pendiente'

    codigo = models.CharField(
        max_length=30,
        choices=Codigo.choices,
        unique=True,
        verbose_name='Código',
    )
    asunto = models.CharField(max_length=200, verbose_name='Asunto')
    cuerpo = models.TextField(
        verbose_name='Cuerpo',
        help_text='Variables: {nombre}, {fecha_vencimiento}, {dias}, {gym}, {plan}.',
    )
    activa = models.BooleanField(default=True, verbose_name='Activa')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plantilla'
        verbose_name_plural = 'Plantillas'
        ordering = ['codigo']

    def __str__(self):
        return self.get_codigo_display()


class Notificacion(models.Model):
    """
    Registro de cada notificación enviada (o intentada).
    Es la fuente de verdad para auditoría: TODO se guarda aquí.
    """
    class Tipo(models.TextChoices):
        POR_VENCER = 'por_vencer', 'Por vencer'
        VENCIDO = 'vencido', 'Vencido'
        INSCRIPCION_PENDIENTE = 'inscripcion_pendiente', 'Inscripción pendiente'

    class Canal(models.TextChoices):
        EMAIL = 'email', 'Email'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        ENVIADO = 'enviado', 'Enviado'
        FALLIDO = 'fallido', 'Fallido'

    alumno = models.ForeignKey(
        'alumnos.Alumno',
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Alumno',
    )
    suscripcion = models.ForeignKey(
        'pagos.Suscripcion',
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Suscripción',
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices, db_index=True, verbose_name='Tipo')
    canal = models.CharField(max_length=15, choices=Canal.choices, default=Canal.EMAIL, verbose_name='Canal')
    destino = models.CharField(max_length=120, verbose_name='Destino (email)')
    asunto = models.CharField(max_length=200, blank=True, default='', verbose_name='Asunto')
    mensaje = models.TextField(verbose_name='Mensaje')
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE, db_index=True, verbose_name='Estado')
    error_mensaje = models.TextField(blank=True, default='', verbose_name='Error')
    intentos = models.PositiveSmallIntegerField(default=0, verbose_name='Intentos')
    enviado_en = models.DateTimeField(null=True, blank=True, verbose_name='Enviado en')
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Creado en')

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['alumno', '-creado_en']),
            models.Index(fields=['tipo', '-creado_en']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} → {self.alumno.nombre_completo()} ({self.get_estado_display()})'

    @classmethod
    def ya_enviada_hoy(cls, alumno, suscripcion, tipo):
        """True si ya se envió esta notificación hoy (idempotencia)."""
        hoy = timezone.now().date()
        return cls.objects.filter(
            alumno=alumno,
            suscripcion=suscripcion,
            tipo=tipo,
            creado_en__date=hoy,
            estado=cls.Estado.ENVIADO,
        ).exists()

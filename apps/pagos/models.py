from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ============================================================
# Configuración de descuentos (singleton)
# ============================================================

class ConfiguracionDescuento(models.Model):
    """
    Configuración global del módulo de pagos.
    Es un singleton: siempre existe una sola fila (pk=1).
    """

    descuento_inscripcion_estudiante_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=50.00,
        verbose_name='Descuento en inscripción para estudiante (%)',
    )
    descuento_mensualidad_estudiante_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=20.00,
        verbose_name='Descuento en mensualidad para estudiante (%)',
    )
    dias_alerta_por_vencer = models.PositiveSmallIntegerField(
        default=7,
        verbose_name='Días antes del vencimiento para alertar',
    )
    dias_gracia = models.PositiveSmallIntegerField(
        default=5,
        verbose_name='Días de gracia después del vencimiento',
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de descuentos'
        verbose_name_plural = 'Configuración de descuentos'

    def __str__(self):
        return 'Configuración global de pagos'

    def save(self, *args, **kwargs):
        # Forzar singleton
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        """Devuelve la configuración, creándola si no existe."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ============================================================
# Planes
# ============================================================

class Plan(models.Model):
    """
    Catálogo de planes: inscripción o mensualidades (mensual, trimestral, semestral).
    """

    class Tipo(models.TextChoices):
        INSCRIPCION = 'inscripcion', 'Inscripción'
        MENSUALIDAD = 'mensualidad', 'Mensualidad'

    nombre = models.CharField(max_length=80, unique=True, verbose_name='Nombre')
    tipo = models.CharField(
        max_length=15,
        choices=Tipo.choices,
        default=Tipo.MENSUALIDAD,
        verbose_name='Tipo',
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio (MXN)')
    duracion_dias = models.PositiveIntegerField(
        default=0,
        verbose_name='Duración (días)',
        help_text='0 para inscripción.',
    )
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'
        ordering = ['tipo', 'precio']

    def __str__(self):
        return f'{self.nombre} — ${self.precio} ({self.duracion_dias} días)'

    def clean(self):
        if self.precio <= 0:
            raise ValidationError({'precio': 'El precio debe ser mayor a 0.'})
        if self.tipo == self.Tipo.MENSUALIDAD and self.duracion_dias <= 0:
            raise ValidationError({'duracion_dias': 'Los planes de mensualidad deben tener duración mayor a 0.'})
        if self.tipo == self.Tipo.INSCRIPCION and self.duracion_dias != 0:
            raise ValidationError({'duracion_dias': 'La inscripción debe tener duración 0.'})

    def es_inscripcion(self):
        return self.tipo == self.Tipo.INSCRIPCION


# ============================================================
# Pagos
# ============================================================

class Pago(models.Model):
    """
    Registro de cada pago. NUNCA se elimina: solo se anula (baja lógica).
    """

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'efectivo', 'Efectivo'
        TRANSFERENCIA = 'transferencia', 'Transferencia'
        TARJETA = 'tarjeta', 'Tarjeta'

    folio = models.CharField(max_length=12, unique=True, editable=False, verbose_name='Folio')
    alumno = models.ForeignKey(
        'alumnos.Alumno',
        on_delete=models.PROTECT,
        related_name='pagos',
        verbose_name='Alumno',
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='pagos',
        verbose_name='Plan',
    )

    es_inscripcion = models.BooleanField(default=False, verbose_name='¿Es pago de inscripción?')

    monto_base = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto base')
    descuento_aplicado = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Descuento aplicado',
    )
    motivo_descuento = models.CharField(max_length=80, blank=True, default='', verbose_name='Motivo del descuento')
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto final')

    metodo_pago = models.CharField(
        max_length=15, choices=MetodoPago.choices, default=MetodoPago.EFECTIVO,
        verbose_name='Método de pago',
    )
    referencia = models.CharField(max_length=60, blank=True, default='', verbose_name='Referencia')
    notas = models.TextField(blank=True, default='', verbose_name='Notas')

    fecha_pago = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de pago')
    periodo_inicio = models.DateField(verbose_name='Inicio del periodo cubierto')
    periodo_fin = models.DateField(null=True, blank=True, verbose_name='Fin del periodo cubierto')

    # Anulación (baja lógica)
    anulado = models.BooleanField(default=False, verbose_name='Anulado')
    anulado_motivo = models.TextField(blank=True, default='', verbose_name='Motivo de anulación')
    anulado_en = models.DateTimeField(null=True, blank=True, verbose_name='Anulado en')
    anulado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pagos_anulados',
        verbose_name='Anulado por',
    )

    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pagos_registrados',
        verbose_name='Registrado por',
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['alumno', '-fecha_pago']),
            models.Index(fields=['anulado']),
        ]

    def __str__(self):
        return f'{self.folio} — {self.alumno.nombre_completo()} — ${self.monto_final}'

    def save(self, *args, **kwargs):
        # Generar folio si no existe
        if not self.folio:
            ultimo = Pago.objects.order_by('-id').first()
            siguiente = 1 if not ultimo else ultimo.id + 1
            self.folio = f'PAGO-{siguiente:05d}'

        # Calcular monto final
        self.monto_final = self.monto_base - self.descuento_aplicado

        # Calcular periodo_fin si es mensualidad
        if not self.es_inscripcion and self.plan and self.plan.duracion_dias > 0:
            self.periodo_fin = self.periodo_inicio + timedelta(days=self.plan.duracion_dias)

        super().save(*args, **kwargs)

    def anular(self, motivo, usuario):
        """Anula el pago (baja lógica). Recalcula la suscripción del alumno."""
        self.anulado = True
        self.anulado_motivo = motivo
        self.anulado_en = timezone.now()
        self.anulado_por = usuario
        self.save(update_fields=['anulado', 'anulado_motivo', 'anulado_en', 'anulado_por', 'actualizado_en'])

        # Recalcular suscripción
        suscripcion, _ = Suscripcion.objects.get_or_create(alumno=self.alumno)
        suscripcion.recalcular()


# ============================================================
# Suscripciones
# ============================================================

class Suscripcion(models.Model):
    """
    Estado actual del servicio del alumno. Se recalcula cada vez que
    se registra o anula un pago.
    """

    class Estado(models.TextChoices):
        PENDIENTE_INSCRIPCION = 'pendiente_inscripcion', 'Pendiente de inscripción'
        ACTIVO = 'activo', 'Activo'
        POR_VENCER = 'por_vencer', 'Por vencer'
        EN_GRACIA = 'en_gracia', 'En periodo de gracia'
        VENCIDO = 'vencido', 'Vencido'

    alumno = models.OneToOneField(
        'alumnos.Alumno',
        on_delete=models.CASCADE,
        related_name='suscripcion',
        verbose_name='Alumno',
    )
    plan_actual = models.ForeignKey(
        Plan, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='suscripciones_actuales',
        verbose_name='Plan actual',
    )
    inscripcion_pagada = models.BooleanField(default=False, verbose_name='Inscripción pagada')
    fecha_inscripcion = models.DateField(null=True, blank=True, verbose_name='Fecha de inscripción')

    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Inicio del periodo actual')
    fecha_vencimiento = models.DateField(null=True, blank=True, db_index=True, verbose_name='Vencimiento')

    estado = models.CharField(
        max_length=25,
        choices=Estado.choices,
        default=Estado.PENDIENTE_INSCRIPCION,
        db_index=True,
        verbose_name='Estado',
    )

    ultimo_pago = models.ForeignKey(
        Pago, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='suscripciones_resultantes',
        verbose_name='Último pago',
    )

    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['fecha_vencimiento']

    def __str__(self):
        return f'Suscripción de {self.alumno.nombre_completo()} — {self.get_estado_display()}'

    def recalcular(self):
        """
        Recalcula el estado completo a partir de los pagos no anulados del alumno.
        """
        pagos = Pago.objects.filter(alumno=self.alumno, anulado=False).order_by('periodo_inicio', 'fecha_pago')

        if not pagos.exists():
            self.inscripcion_pagada = False
            self.fecha_inscripcion = None
            self.fecha_inicio = None
            self.fecha_vencimiento = None
            self.plan_actual = None
            self.ultimo_pago = None
            self.estado = self.Estado.PENDIENTE_INSCRIPCION
            self.save()
            return

        # ¿Hay pago de inscripción?
        pago_inscripcion = pagos.filter(es_inscripcion=True).order_by('fecha_pago').first()
        if pago_inscripcion:
            self.inscripcion_pagada = True
            self.fecha_inscripcion = pago_inscripcion.fecha_pago.date()

        # Último pago de mensualidad (no inscripción) vigente
        ultimo_mensualidad = pagos.filter(es_inscripcion=False).order_by('-periodo_fin').first()
        if ultimo_mensualidad:
            self.fecha_inicio = ultimo_mensualidad.periodo_inicio
            self.fecha_vencimiento = ultimo_mensualidad.periodo_fin
            self.plan_actual = ultimo_mensualidad.plan
            self.ultimo_pago = ultimo_mensualidad
        else:
            # Solo pagó inscripción, aún no mensualidad
            self.fecha_inicio = None
            self.fecha_vencimiento = None
            self.plan_actual = pago_inscripcion.plan if pago_inscripcion else None
            self.ultimo_pago = pago_inscripcion

        # Calcular estado
        self.estado = self._calcular_estado()
        self.save()

    def _calcular_estado(self):
        """Devuelve el estado actual según el vencimiento y la configuración."""
        if not self.inscripcion_pagada:
            return self.Estado.PENDIENTE_INSCRIPCION

        if not self.fecha_vencimiento:
            # Pagó inscripción pero no mensualidad aún
            return self.Estado.PENDIENTE_INSCRIPCION

        config = ConfiguracionDescuento.get()
        hoy = timezone.now().date()
        dias_para_vencer = (self.fecha_vencimiento - hoy).days

        if dias_para_vencer < -config.dias_gracia:
            return self.Estado.VENCIDO
        if dias_para_vencer < 0:
            return self.Estado.EN_GRACIA
        if dias_para_vencer <= config.dias_alerta_por_vencer:
            return self.Estado.POR_VENCER
        return self.Estado.ACTIVO

    def puede_ingresar(self):
        """True si el alumno puede ingresar al gimnasio."""
        return self.estado in [
            self.Estado.ACTIVO,
            self.Estado.POR_VENCER,
            self.Estado.EN_GRACIA,
        ]

    def dias_para_vencer(self):
        """Días hasta el vencimiento (negativo si ya venció)."""
        if not self.fecha_vencimiento:
            return None
        return (self.fecha_vencimiento - timezone.now().date()).days

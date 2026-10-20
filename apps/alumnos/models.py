from datetime import date

from django.conf import settings
from django.db import models
from django.utils import timezone


class Alumno(models.Model):
    """
    Alumno del gimnasio. Baja lógica (nunca se borra físicamente).
    """

    class Sexo(models.TextChoices):
        MASCULINO = 'M', 'Masculino'
        FEMENINO = 'F', 'Femenino'
        OTRO = 'X', 'Otro'

    class Categoria(models.TextChoices):
        INFANTIL = 'infantil', 'Infantil'
        JUVENIL = 'juvenil', 'Juvenil'
        ADULTO = 'adulto', 'Adulto'
        MASTER = 'master', 'Máster'

    class TipoSangre(models.TextChoices):
        A_POS = 'A+', 'A+'
        A_NEG = 'A-', 'A-'
        B_POS = 'B+', 'B+'
        B_NEG = 'B-', 'B-'
        AB_POS = 'AB+', 'AB+'
        AB_NEG = 'AB-', 'AB-'
        O_POS = 'O+', 'O+'
        O_NEG = 'O-', 'O-'

    # --- Identificación ---
    matricula = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        verbose_name='Matrícula',
        help_text='Se genera automáticamente (MMA-0001, MMA-0002, ...).',
    )

    nombre = models.CharField(max_length=80, verbose_name='Nombre(s)')
    apellido_paterno = models.CharField(max_length=80, verbose_name='Apellido paterno')
    apellido_materno = models.CharField(max_length=80, verbose_name='Apellido materno')

    curp = models.CharField(
        max_length=18,
        blank=True,
        default='',
        verbose_name='CURP',
        help_text='Dato sensible. Se cifrará en la Fase 2 (ISO 27001).',
    )

    fecha_nacimiento = models.DateField(verbose_name='Fecha de nacimiento')

    sexo = models.CharField(
        max_length=1,
        choices=Sexo.choices,
        verbose_name='Sexo',
    )

    # --- Contacto ---
    telefono = models.CharField(
        max_length=15,
        verbose_name='Teléfono',
        help_text='Se usa para notificaciones por SMS.',
    )
    email = models.EmailField(blank=True, default='', verbose_name='Correo electrónico')
    direccion = models.TextField(blank=True, default='', verbose_name='Dirección')

    # --- Tutor (obligatorio si el alumno es menor de edad) ---
    tutor_nombre = models.CharField(
        max_length=120, blank=True, default='',
        verbose_name='Nombre del tutor',
    )
    tutor_telefono = models.CharField(
        max_length=15, blank=True, default='',
        verbose_name='Teléfono del tutor',
    )
    tutor_parentesco = models.CharField(
        max_length=40, blank=True, default='',
        verbose_name='Parentesco del tutor',
    )

    # --- Contacto de emergencia ---
    contacto_emergencia_nombre = models.CharField(
        max_length=120, blank=True, default='',
        verbose_name='Contacto de emergencia',
    )
    contacto_emergencia_telefono = models.CharField(
        max_length=15, blank=True, default='',
        verbose_name='Teléfono de emergencia',
    )

    # --- Datos del gimnasio ---
    fecha_ingreso = models.DateField(
        default=date.today,
        verbose_name='Fecha de ingreso',
    )

    categoria = models.CharField(
        max_length=15,
        choices=Categoria.choices,
        default=Categoria.ADULTO,
        verbose_name='Categoría',
    )
    es_estudiante = models.BooleanField(
        default=False,
        verbose_name='¿Es estudiante?',
        help_text='Si está marcado, aplica descuentos configurados por el administrador (solo en plan mensual).',
    )

    peso_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Peso (kg)',
    )

    tipo_sangre = models.CharField(
        max_length=3,
        choices=TipoSangre.choices,
        blank=True,
        default='',
        verbose_name='Tipo de sangre',
    )

    alergias = models.TextField(
        blank=True, default='',
        verbose_name='Alergias o condiciones médicas',
    )

    # --- Baja lógica ---
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Baja lógica: los registros no se eliminan.',
    )
    fecha_baja = models.DateField(null=True, blank=True, verbose_name='Fecha de baja')
    motivo_baja = models.TextField(blank=True, default='', verbose_name='Motivo de baja')

    # --- Auditoría ---
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Creado en')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Actualizado en')

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='alumnos_creados',
        verbose_name='Creado por',
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='alumnos_actualizados',
        verbose_name='Actualizado por',
    )

    class Meta:
        verbose_name = 'Alumno'
        verbose_name_plural = 'Alumnos'
        ordering = ['apellido_paterno', 'apellido_materno', 'nombre']
        indexes = [
            models.Index(fields=['activo']),
            models.Index(fields=['apellido_paterno', 'apellido_materno']),
            models.Index(fields=['telefono']),
        ]

    def __str__(self):
        return f'{self.apellido_paterno} {self.apellido_materno}, {self.nombre} ({self.matricula})'

    def nombre_completo(self):
        return f'{self.nombre} {self.apellido_paterno} {self.apellido_materno}'.strip()

    def edad(self):
        """Edad en años cumplidos."""
        if not self.fecha_nacimiento:
            return None
        hoy = timezone.now().date()
        return (
            hoy.year - self.fecha_nacimiento.year
            - ((hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        )

    def es_menor(self):
        """True si es menor de 18 años."""
        edad = self.edad()
        return edad is not None and edad < 18

    def save(self, *args, **kwargs):
        """Genera la matrícula si es el primer guardado."""
        if not self.matricula:
            ultimo = Alumno.objects.order_by('-id').first()
            siguiente = 1 if not ultimo else ultimo.id + 1
            self.matricula = f'MMA-{siguiente:04d}'
        super().save(*args, **kwargs)

    def dar_de_baja(self, motivo='', usuario=None):
        """Baja lógica: no borra, solo marca como inactivo."""
        self.activo = False
        self.fecha_baja = timezone.now().date()
        self.motivo_baja = motivo
        self.actualizado_por = usuario
        self.save(update_fields=['activo', 'fecha_baja', 'motivo_baja', 'actualizado_por', 'actualizado_en'])

    def reactivar(self, usuario=None):
        self.activo = True
        self.fecha_baja = None
        self.motivo_baja = ''
        self.actualizado_por = usuario
        self.save(update_fields=['activo', 'fecha_baja', 'motivo_baja', 'actualizado_por', 'actualizado_en'])

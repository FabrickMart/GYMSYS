
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado para GYMSYS-MMA.
    Extiende AbstractUser con rol, control de intentos fallidos,
    bloqueo temporal y baja lógica.
    """

    class Rol(models.TextChoices):
        ADMINISTRADOR = 'admin', 'Administrador'
        PERSONAL = 'personal', 'Personal administrativo'

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.PERSONAL,
        verbose_name='Rol',
    )

    intentos_fallidos = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Intentos fallidos consecutivos',
    )

    bloqueado_hasta = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Bloqueado hasta',
    )

    ultimo_login_fallido = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último login fallido',
    )

    debe_cambiar_password = models.BooleanField(
        default=False,
        verbose_name='Debe cambiar contraseña',
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Baja lógica: los registros no se eliminan.',
    )

    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Creado en')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Actualizado en')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['username']

    def __str__(self):
        return f'{self.username} ({self.get_rol_display()})'

    # --- Métodos de negocio ---

    def esta_bloqueado(self):
        if self.bloqueado_hasta and self.bloqueado_hasta > timezone.now():
            return True
        return False

    def minutos_restantes_bloqueo(self):
        if not self.esta_bloqueado():
            return 0
        delta = self.bloqueado_hasta - timezone.now()
        return max(1, int(delta.total_seconds() // 60) + 1)

    def registrar_intento_fallido(self, max_intentos, minutos_bloqueo):
        self.intentos_fallidos += 1
        self.ultimo_login_fallido = timezone.now()

        if self.intentos_fallidos >= max_intentos:
            self.bloqueado_hasta = timezone.now() + timedelta(minutes=minutos_bloqueo)
            self.save(update_fields=['intentos_fallidos', 'ultimo_login_fallido', 'bloqueado_hasta'])
            return True

        self.save(update_fields=['intentos_fallidos', 'ultimo_login_fallido'])
        return False

    def resetear_intentos(self):
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None
        self.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])

    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR or self.is_superuser

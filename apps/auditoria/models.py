from django.conf import settings
from django.db import models


class Evento(models.Model):
    """
    Registro de auditoría. Cada operación crítica del sistema deja aquí
    una fila: login, logout, alta/baja/modificación de usuarios, pagos, etc.
    NUNCA se elimina (no hay delete). Solo se consulta.
    """

    class Accion(models.TextChoices):
        # Autenticación
        LOGIN_OK = 'login_ok', 'Login exitoso'
        LOGIN_FAIL = 'login_fail', 'Login fallido'
        LOGIN_BLOQUEADO = 'login_bloqueado', 'Login bloqueado por intentos'
        LOGOUT = 'logout', 'Logout'

        # Usuarios
        USUARIO_CREADO = 'usuario_creado', 'Usuario creado'
        USUARIO_ACTUALIZADO = 'usuario_actualizado', 'Usuario actualizado'
        USUARIO_BAJA = 'usuario_baja', 'Usuario dado de baja'
        USUARIO_REACTIVADO = 'usuario_reactivado', 'Usuario reactivado'
        PASSWORD_RESET = 'password_reset', 'Contraseña reseteada por admin'
        PASSWORD_CAMBIADA = 'password_cambiada', 'Contraseña cambiada por el usuario'

        # Alumnos (para después)
        ALUMNO_CREADO = 'alumno_creado', 'Alumno creado'
        ALUMNO_ACTUALIZADO = 'alumno_actualizado', 'Alumno actualizado'
        ALUMNO_BAJA = 'alumno_baja', 'Alumno dado de baja'

        # Pagos (para después)
        PAGO_REGISTRADO = 'pago_registrado', 'Pago registrado'
        PAGO_ANULADO = 'pago_anulado', 'Pago anulado'

        # Otros
        ACCESO_DENEGADO = 'acceso_denegado', 'Acceso denegado por permisos'
        OTRO = 'otro', 'Otro evento'

    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Fecha y hora',
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='eventos_como_actor',
        verbose_name='Usuario que ejecuta',
    )

    usuario_afectado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='eventos_como_afectado',
        verbose_name='Usuario afectado',
    )

    accion = models.CharField(
        max_length=40,
        choices=Accion.choices,
        db_index=True,
        verbose_name='Acción',
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
    )

    ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP',
    )

    user_agent = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='User-Agent',
    )

    exitoso = models.BooleanField(
        default=True,
        verbose_name='Exitoso',
    )

    metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Metadatos',
        help_text='Información adicional en formato JSON.',
    )

    class Meta:
        verbose_name = 'Evento de auditoría'
        verbose_name_plural = 'Eventos de auditoría'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['-fecha_hora']),
            models.Index(fields=['accion', '-fecha_hora']),
            models.Index(fields=['usuario', '-fecha_hora']),
        ]

    def __str__(self):
        return f'[{self.fecha_hora:%Y-%m-%d %H:%M:%S}] {self.get_accion_display()}'

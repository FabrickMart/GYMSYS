from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# ============================================================
# Entrenador
# ============================================================

class Entrenador(models.Model):
    class Especialidad(models.TextChoices):
        MMA = 'mma', 'MMA'
        BOXEO = 'boxeo', 'Boxeo'
        JIU_JITSU = 'jiu_jitsu', 'Jiu-Jitsu'
        MUAY_THAI = 'muay_thai', 'Muay Thai'
        KICKBOXING = 'kickboxing', 'Kickboxing'
        OTRO = 'otro', 'Otro'

    nombre = models.CharField(max_length=80, verbose_name='Nombre(s)')
    apellido_paterno = models.CharField(max_length=80, verbose_name='Apellido paterno')
    apellido_materno = models.CharField(max_length=80, verbose_name='Apellido materno')
    telefono = models.CharField(max_length=15, verbose_name='Teléfono')
    email = models.EmailField(blank=True, default='', verbose_name='Correo electrónico')
    fecha_ingreso = models.DateField(verbose_name='Fecha de ingreso')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    notas = models.TextField(blank=True, default='', verbose_name='Notas')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entrenador'
        verbose_name_plural = 'Entrenadores'
        ordering = ['apellido_paterno', 'apellido_materno', 'nombre']

    def __str__(self):
        return f'{self.apellido_paterno} {self.apellido_materno}, {self.nombre}'

    def nombre_completo(self):
        return f'{self.nombre} {self.apellido_paterno} {self.apellido_materno}'.strip()


# ============================================================
# Clase
# ============================================================

class Clase(models.Model):
    class Disciplina(models.TextChoices):
        MMA = 'mma', 'MMA'
        BOXEO = 'boxeo', 'Boxeo'
        JIU_JITSU = 'jiu_jitsu', 'Jiu-Jitsu'
        MUAY_THAI = 'muay_thai', 'Muay Thai'
        KICKBOXING = 'kickboxing', 'Kickboxing'
        OTRO = 'otro', 'Otro'

    class Nivel(models.TextChoices):
        PRINCIPIANTE = 'principiante', 'Principiante'
        INTERMEDIO = 'intermedio', 'Intermedio'
        AVANZADO = 'avanzado', 'Avanzado'
        TODOS = 'todos', 'Todos los niveles'

    nombre = models.CharField(max_length=80, verbose_name='Nombre de la clase')
    disciplina = models.CharField(max_length=20, choices=Disciplina.choices, verbose_name='Disciplina')
    nivel = models.CharField(max_length=20, choices=Nivel.choices, default=Nivel.TODOS, verbose_name='Nivel')
    entrenador = models.ForeignKey(
        Entrenador,
        on_delete=models.PROTECT,
        related_name='clases',
        verbose_name='Entrenador',
    )
    cupo_maximo = models.PositiveSmallIntegerField(default=15, verbose_name='Cupo máximo')
    duracion_minutos = models.PositiveSmallIntegerField(default=60, verbose_name='Duración (min)')
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción')
    activo = models.BooleanField(default=True, verbose_name='Activa')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Clase'
        verbose_name_plural = 'Clases'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.get_nivel_display()})'

    def inscritos_activos(self):
        return self.inscripciones.filter(activo=True).count()

    def cupo_disponible(self):
        return max(0, self.cupo_maximo - self.inscritos_activos())


# ============================================================
# Horario
# ============================================================

class Horario(models.Model):
    """
    Un horario de una clase en días específicos de la semana.
    Se guarda `dias_semana` como JSON: ["lunes", "miercoles", "viernes"].
    La hora_fin se calcula automáticamente según la duración de la clase.
    """

    class Dia(models.TextChoices):
        LUNES = 'lunes', 'Lunes'
        MARTES = 'martes', 'Martes'
        MIERCOLES = 'miercoles', 'Miércoles'
        JUEVES = 'jueves', 'Jueves'
        VIERNES = 'viernes', 'Viernes'
        SABADO = 'sabado', 'Sábado'
        DOMINGO = 'domingo', 'Domingo'

    clase = models.ForeignKey(
        Clase,
        on_delete=models.CASCADE,
        related_name='horarios',
        verbose_name='Clase',
    )
    dias_semana = models.JSONField(
        default=list,
        verbose_name='Días de la semana',
        help_text='Lista de días, ej. ["lunes", "miercoles", "viernes"].',
    )
    hora_inicio = models.TimeField(verbose_name='Hora de inicio')
    hora_fin = models.TimeField(verbose_name='Hora de fin')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'
        ordering = ['hora_inicio']

    def __str__(self):
        dias = ', '.join(d.capitalize() for d in self.dias_semana)
        return f'{self.clase.nombre} — {dias} {self.hora_inicio:%H:%M}-{self.hora_fin:%H:%M}'

    def clean(self):
        if not isinstance(self.dias_semana, list) or len(self.dias_semana) == 0:
            raise ValidationError({'dias_semana': 'Debes seleccionar al menos un día.'})
        validos = {d[0] for d in self.Dia.choices}
        for d in self.dias_semana:
            if d not in validos:
                raise ValidationError({'dias_semana': f'Día inválido: {d}'})

    def save(self, *args, **kwargs):
        """
        Calcula hora_fin automáticamente según la duración de la clase.
        La hora de inicio es lo único que el usuario edita.
        """
        if self.hora_inicio and self.clase_id:
            from datetime import datetime, timedelta
            duracion = self.clase.duracion_minutos or 60
            inicio_dt = datetime.combine(datetime.today(), self.hora_inicio)
            fin_dt = inicio_dt + timedelta(minutes=duracion)
            self.hora_fin = fin_dt.time()
        super().save(*args, **kwargs)

    def dias_display(self):
        mapa = dict(self.Dia.choices)
        return ', '.join(mapa.get(d, d) for d in self.dias_semana)

# ============================================================
# Inscripción a clase
# ============================================================

class InscripcionClase(models.Model):
    """
    Inscripción de un alumno a una clase (con cupo limitado).
    """

    clase = models.ForeignKey(
        Clase,
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name='Clase',
    )
    alumno = models.ForeignKey(
        'alumnos.Alumno',
        on_delete=models.CASCADE,
        related_name='inscripciones_clases',
        verbose_name='Alumno',
    )
    fecha_inscripcion = models.DateField(auto_now_add=True, verbose_name='Fecha de inscripción')
    activo = models.BooleanField(default=True, verbose_name='Activa')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Inscripción a clase'
        verbose_name_plural = 'Inscripciones a clases'
        ordering = ['-fecha_inscripcion']
        constraints = [
            models.UniqueConstraint(
                fields=['clase', 'alumno'],
                condition=models.Q(activo=True),
                name='inscripcion_unica_activa',
            ),
        ]

    def __str__(self):
        return f'{self.alumno.nombre_completo()} → {self.clase.nombre}'

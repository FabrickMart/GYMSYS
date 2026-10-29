from django.contrib import admin
from .models import Entrenador, Clase, Horario, InscripcionClase


@admin.register(Entrenador)
class EntrenadorAdmin(admin.ModelAdmin):
    list_display = ('apellido_paterno', 'apellido_materno', 'nombre', 'telefono', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'apellido_paterno', 'apellido_materno', 'telefono', 'email')


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'disciplina', 'nivel', 'entrenador', 'cupo_maximo', 'activo')
    list_filter = ('disciplina', 'nivel', 'activo')
    search_fields = ('nombre', 'entrenador__nombre', 'entrenador__apellido_paterno')


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('clase', 'hora_inicio', 'hora_fin', 'activo')
    list_filter = ('activo',)
    search_fields = ('clase__nombre',)
    filter_horizontal = ()


@admin.register(InscripcionClase)
class InscripcionClaseAdmin(admin.ModelAdmin):
    list_display = ('clase', 'alumno', 'fecha_inscripcion', 'activo')
    list_filter = ('activo', 'clase')
    search_fields = ('alumno__nombre', 'alumno__apellido_paterno', 'alumno__matricula', 'clase__nombre')
    date_hierarchy = 'fecha_inscripcion'

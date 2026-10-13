from django.contrib import admin
from .models import Alumno


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'apellido_paterno', 'apellido_materno', 'nombre',
                    'categoria', 'telefono', 'activo')
    list_filter = ('activo', 'categoria', 'sexo', 'tipo_sangre')
    search_fields = ('matricula', 'nombre', 'apellido_paterno', 'apellido_materno', 'telefono', 'curp')
    readonly_fields = ('matricula', 'creado_en', 'actualizado_en', 'creado_por', 'actualizado_por')
    date_hierarchy = 'fecha_ingreso'

    fieldsets = (
        ('Identificación', {
            'fields': ('matricula', 'nombre', 'apellido_paterno', 'apellido_materno',
                       'curp', 'fecha_nacimiento', 'sexo'),
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'direccion'),
        }),
        ('Tutor (obligatorio si es menor de edad)', {
            'fields': ('tutor_nombre', 'tutor_telefono', 'tutor_parentesco'),
        }),
        ('Contacto de emergencia', {
            'fields': ('contacto_emergencia_nombre', 'contacto_emergencia_telefono'),
        }),
        ('Datos del gimnasio', {
            'fields': ('fecha_ingreso', 'categoria', 'peso_kg', 'tipo_sangre', 'alergias'),
        }),
        ('Estado', {
            'fields': ('activo', 'fecha_baja', 'motivo_baja'),
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'actualizado_en', 'creado_por', 'actualizado_por'),
            'classes': ('collapse',),
        }),
    )

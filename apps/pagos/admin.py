from django.contrib import admin
from .models import Plan, Pago, Suscripcion, ConfiguracionDescuento


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'precio', 'duracion_dias', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre',)
    ordering = ('tipo', 'precio')


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('folio', 'alumno', 'plan', 'es_inscripcion', 'monto_final',
                    'metodo_pago', 'fecha_pago', 'anulado')
    list_filter = ('anulado', 'metodo_pago', 'es_inscripcion', 'fecha_pago')
    search_fields = ('folio', 'alumno__nombre', 'alumno__apellido_paterno',
                     'alumno__apellido_materno', 'alumno__matricula', 'referencia')
    readonly_fields = ('folio', 'fecha_pago', 'creado_en', 'actualizado_en',
                       'anulado_en', 'anulado_por')
    date_hierarchy = 'fecha_pago'

    fieldsets = (
        ('Identificación', {
            'fields': ('folio', 'alumno', 'plan', 'es_inscripcion'),
        }),
        ('Montos', {
            'fields': ('monto_base', 'descuento_aplicado', 'motivo_descuento', 'monto_final'),
        }),
        ('Pago', {
            'fields': ('metodo_pago', 'referencia', 'notas', 'fecha_pago', 'registrado_por'),
        }),
        ('Periodo cubierto', {
            'fields': ('periodo_inicio', 'periodo_fin'),
        }),
        ('Anulación', {
            'fields': ('anulado', 'anulado_motivo', 'anulado_en', 'anulado_por'),
            'classes': ('collapse',),
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'plan_actual', 'inscripcion_pagada', 'fecha_vencimiento', 'estado')
    list_filter = ('estado', 'inscripcion_pagada')
    search_fields = ('alumno__nombre', 'alumno__apellido_paterno', 'alumno__apellido_materno',
                     'alumno__matricula')
    readonly_fields = ('actualizado_en',)
    date_hierarchy = 'fecha_vencimiento'


@admin.register(ConfiguracionDescuento)
class ConfiguracionDescuentoAdmin(admin.ModelAdmin):
    list_display = ('descuento_inscripcion_estudiante_pct',
                    'descuento_mensualidad_estudiante_pct',
                    'dias_alerta_por_vencer', 'dias_gracia')

    def has_add_permission(self, request):
        # Singleton: solo puede existir una fila
        return not ConfiguracionDescuento.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

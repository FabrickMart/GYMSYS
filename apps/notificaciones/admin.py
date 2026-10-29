from django.contrib import admin
from .models import ConfiguracionNotificacion, Plantilla, Notificacion


@admin.register(ConfiguracionNotificacion)
class ConfiguracionNotificacionAdmin(admin.ModelAdmin):
    list_display = ('activo', 'dias_antes_por_vencer', 'dias_despues_vencido_max', 'hora_envio')

    def has_add_permission(self, request):
        return not ConfiguracionNotificacion.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Plantilla)
class PlantillaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'asunto', 'activa')
    list_filter = ('activa',)
    search_fields = ('codigo', 'asunto')


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('creado_en', 'tipo', 'alumno', 'canal', 'estado', 'enviado_en')
    list_filter = ('tipo', 'canal', 'estado', 'creado_en')
    search_fields = ('alumno__nombre', 'alumno__apellido_paterno', 'alumno__matricula', 'destino', 'asunto')
    readonly_fields = ('creado_en', 'enviado_en', 'error_mensaje', 'intentos')
    date_hierarchy = 'creado_en'
# Register your models here.

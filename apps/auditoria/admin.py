from django.contrib import admin
from .models import Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'accion', 'usuario', 'usuario_afectado', 'ip', 'exitoso')
    list_filter = ('accion', 'exitoso', 'fecha_hora')
    search_fields = ('descripcion', 'usuario__username', 'usuario_afectado__username', 'ip')
    readonly_fields = (
        'fecha_hora', 'usuario', 'usuario_afectado', 'accion',
        'descripcion', 'ip', 'user_agent', 'exitoso', 'metadata',
    )
    date_hierarchy = 'fecha_hora'

    def has_add_permission(self, request):
        # No se pueden crear eventos manualmente
        return False

    def has_change_permission(self, request, obj=None):
        # No se pueden editar eventos (son inmutables)
        return False

    def has_delete_permission(self, request, obj=None):
        # No se pueden borrar eventos (trazabilidad)
        return False

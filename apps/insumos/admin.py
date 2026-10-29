from django.contrib import admin
from .models import Producto, Movimiento


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'precio_venta', 'stock_actual', 'stock_minimo', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion')
    readonly_fields = ('codigo', 'creado_en', 'actualizado_en')

    fieldsets = (
        ('Identificación', {
            'fields': ('codigo', 'nombre', 'categoria', 'descripcion'),
        }),
        ('Precios e inventario', {
            'fields': ('precio_compra', 'precio_venta', 'stock_actual', 'stock_minimo'),
        }),
        ('Estado', {
            'fields': ('activo',),
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'producto', 'tipo', 'motivo', 'cantidad', 'monto_total', 'registrado_por')
    list_filter = ('tipo', 'motivo', 'fecha')
    search_fields = ('producto__nombre', 'producto__codigo', 'notas')
    readonly_fields = ('fecha', 'creado_en', 'monto_total')
    date_hierarchy = 'fecha'

    def has_change_permission(self, request, obj=None):
        # Los movimientos son inmutables
        return False

    def has_delete_permission(self, request, obj=None):
        return False

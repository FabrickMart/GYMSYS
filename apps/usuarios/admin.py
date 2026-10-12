from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'activo', 'is_staff')
    list_filter = ('rol', 'activo', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = UserAdmin.fieldsets + (
        ('GYMSYS-MMA', {
            'fields': (
                'rol', 'activo', 'debe_cambiar_password',
                'intentos_fallidos', 'bloqueado_hasta', 'ultimo_login_fallido',
            ),
        }),
    )

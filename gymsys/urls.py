from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', RedirectView.as_view(pattern_name='usuarios:login', permanent=False)),

    path('', include('apps.usuarios.urls')),
    path('alumnos/', include('apps.alumnos.urls')),
    path('pagos/', include('apps.pagos.urls')),
    path('notificaciones/', include('apps.notificaciones.urls')),
    path('clases/', include('apps.clases.urls')),
    path('insumos/', include('apps.insumos.urls')),

]

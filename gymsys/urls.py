from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Raíz → redirige al login (que a su vez redirige al dashboard si ya está logueado)
    path('', RedirectView.as_view(pattern_name='usuarios:login', permanent=False)),

    # URLs de las apps
    path('', include('apps.usuarios.urls')),
    path('alumnos/', include('apps.alumnos.urls')),
]

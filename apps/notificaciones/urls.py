from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.lista_notificaciones, name='lista'),
    path('enviar-ahora/', views.enviar_recordatorios_ahora, name='enviar_ahora'),
]

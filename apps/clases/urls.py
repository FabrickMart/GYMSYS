from django.urls import path
from . import views

app_name = 'clases'

urlpatterns = [
    # Entrenadores
    path('entrenadores/', views.lista_entrenadores, name='lista_entrenadores'),
    path('entrenadores/nuevo/', views.crear_entrenador, name='crear_entrenador'),
    path('entrenadores/<int:pk>/', views.detalle_entrenador, name='detalle_entrenador'),
    path('entrenadores/<int:pk>/editar/', views.editar_entrenador, name='editar_entrenador'),
    path('entrenadores/<int:pk>/baja/', views.baja_entrenador, name='baja_entrenador'),
    path('entrenadores/<int:pk>/reactivar/', views.reactivar_entrenador, name='reactivar_entrenador'),

    # Clases
    path('', views.lista_clases, name='lista_clases'),
    path('nuevo/', views.crear_clase, name='crear_clase'),
    path('<int:pk>/', views.detalle_clase, name='detalle_clase'),
    path('<int:pk>/editar/', views.editar_clase, name='editar_clase'),
    path('<int:pk>/baja/', views.baja_clase, name='baja_clase'),
    path('<int:pk>/reactivar/', views.reactivar_clase, name='reactivar_clase'),

    # Horario semanal
    path('horario/', views.horario_semanal, name='horario_semanal'),
]

from django.urls import path
from . import views

app_name = 'alumnos'

urlpatterns = [
    path('', views.lista_alumnos, name='lista'),
    path('nuevo/', views.crear_alumno, name='crear'),
    path('<int:pk>/', views.detalle_alumno, name='detalle'),
    path('<int:pk>/editar/', views.editar_alumno, name='editar'),
    path('<int:pk>/baja/', views.baja_alumno, name='baja'),
    path('<int:pk>/reactivar/', views.reactivar_alumno, name='reactivar'),
]

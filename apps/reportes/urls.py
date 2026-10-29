from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.dashboard_reportes, name='dashboard'),
    path('ingresos/', views.reporte_ingresos, name='ingresos'),
    path('ingresos/csv/', views.exportar_ingresos_csv, name='ingresos_csv'),
    path('suscripciones/', views.reporte_suscripciones, name='suscripciones'),
    path('suscripciones/csv/', views.exportar_suscripciones_csv, name='suscripciones_csv'),
    path('alumnos/', views.reporte_alumnos, name='alumnos'),
    path('alumnos/csv/', views.exportar_alumnos_csv, name='alumnos_csv'),
    path('ventas-insumos/', views.reporte_ventas_insumos, name='ventas_insumos'),
    path('ventas-insumos/csv/', views.exportar_ventas_insumos_csv, name='ventas_insumos_csv'),
]

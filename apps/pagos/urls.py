from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
    # Planes (solo admin) — específicas primero
    path('planes/', views.lista_planes, name='lista_planes'),
    path('planes/nuevo/', views.crear_plan, name='crear_plan'),
    path('planes/<int:pk>/editar/', views.editar_plan, name='editar_plan'),

    # Suscripciones
    path('suscripciones/', views.lista_suscripciones, name='lista_suscripciones'),
    path('alumno/<int:alumno_pk>/', views.detalle_alumno, name='detalle_alumno'),

    # API interna (AJAX) — antes de <int:pk>/
    path('api/alumno/<int:alumno_pk>/info/', views.api_info_alumno, name='api_info_alumno'),
    path('api/plan/<int:plan_pk>/info/', views.api_info_plan, name='api_info_plan'),
    path('api/config/', views.api_config_descuentos, name='api_config'),
    path('api/plan-inscripcion/', views.api_plan_inscripcion, name='api_plan_inscripcion'),

    # Pagos específicos
    path('nuevo/', views.registrar_pago, name='registrar'),
    path('nuevo/<int:alumno_pk>/', views.registrar_pago, name='registrar_para_alumno'),

    # Listado y detalle (al final)
    path('', views.lista_pagos, name='lista'),
    path('<int:pk>/', views.detalle_pago, name='detalle_pago'),
    path('<int:pk>/anular/', views.anular_pago, name='anular'),
]

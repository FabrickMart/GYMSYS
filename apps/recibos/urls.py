from django.urls import path
from . import views

app_name = 'recibos'

urlpatterns = [
    path('pago/<int:pk>/', views.recibo_pago_html, name='recibo_pago_html'),
    path('pago/<int:pk>/pdf/', views.recibo_pago_pdf, name='recibo_pago_pdf'),
    path('pago/<int:pk>/enviar/', views.recibo_pago_enviar, name='recibo_pago_enviar'),
]


from django.urls import path
from . import views

app_name = 'insumos'

urlpatterns = [
    # Productos
    path('', views.lista_productos, name='lista_productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('productos/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:pk>/baja/', views.baja_producto, name='baja_producto'),
    path('productos/<int:pk>/reactivar/', views.reactivar_producto, name='reactivar_producto'),
       path('venta-rapida/', views.venta_rapida, name='venta_rapida'),

    # Movimientos
    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimientos/nuevo/', views.registrar_movimiento, name='registrar_movimiento'),
    path('movimientos/nuevo/<int:producto_pk>/', views.registrar_movimiento, name='registrar_movimiento_para_producto'),
     

#api interna
path('api/producto/<int:producto_pk>/', views.api_info_producto, name='api_info_producto'),

]

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from CarritoApp.views import * 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', tienda, name="Tienda"),
    path('agregar/<int:producto_id>/', agregar_producto, name="Add"),
    path('eliminar/<int:producto_id>/', eliminar_producto, name="Del"),
    path('restar/<int:producto_id>/', restar_producto, name="Sub"),
    path('limpiar/', limpiar_carrito, name="CLS"),
    #ORDENES 
    path('mis-ordenes/', ver_ordenes_cliente, name='ver_ordenes_cliente'),
    path('admin/ordenes/', ver_ordenes_admin, name='ver_ordenes_admin'),
    path('orden/crear/<int:producto_id>/', crear_orden, name='crear_orden'),
    path('procesar-pago/<int:orden_id>/',procesar_pago, name='procesar_pago'),
    path('estado-deuda/<int:orden_id>/', estado_deuda, name='estado_deuda'),
    path('eliminar-orden/<int:orden_id>/', eliminar_orden, name='eliminar_orden'),
    path('comprar/', comprar_carrito, name='comprar_carrito'),
    path('info-app/', info_app, name='info_app'),

    #login
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', register, name='register'),

    #Compras
    path('mis-ordenes/', ver_ordenes_cliente, name='ver_ordenes_cliente'),
    path('admin/ordenes/', ver_ordenes_admin, name='ver_ordenes_admin'),
]

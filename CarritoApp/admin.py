from django.contrib import admin
from .models import Producto
# Register your models here.

admin.site.register(Producto)
class productosadmin(admin.ModelAdmin):
    list_display=('nombre','categoria','precio')

from django.db import models
from django.contrib.auth.models import User 

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=64)
    email = models.EmailField()

    def __str__(self):
        return self.nombre
    

class Producto(models.Model):
    nombre = models.CharField(max_length=64)
    categoria = models.CharField(max_length=32)
    precio = models.IntegerField()

    def __str__(self):
        txt="{0} {1} {2}".format(self.nombre,self.categoria,self.precio)
        return txt

class Orden(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)  
    productos = models.ManyToManyField(Producto)  
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado')], default='pendiente')
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Orden #{self.id} - {self.cliente.nombre} ({self.estado})"

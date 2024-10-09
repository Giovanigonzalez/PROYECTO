from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Cliente, Orden, Producto
import requests
import http.client
import json
import datetime
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.
from CarritoApp.Carrito import Carrito
from CarritoApp.models import Producto

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Iniciar sesión automáticamente después de registrarse
            messages.success(request, 'Tu cuenta ha sido creada exitosamente.')
            return redirect('Tienda')  # Redirige a la página de la tienda
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})

def tienda(request):
    #return HttpResponse("Hola Pythonizando")
    productos = Producto.objects.all()
    return render(request, "tienda.html", {'productos':productos})

def agregar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = Producto.objects.get(id=producto_id)
    carrito.agregar(producto)
    return redirect("Tienda")

def eliminar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = Producto.objects.get(id=producto_id)
    carrito.eliminar(producto)
    return redirect("Tienda")

def restar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = Producto.objects.get(id=producto_id)
    carrito.restar(producto)
    return redirect("Tienda")

def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    return redirect("Tienda")

def error_de_pago(request):
    return render(request, 'error_de_pago.html')

def crear_deuda_adamspay(orden, total_carrito):
    apiKey = "ap-2823a2205aaa3e84df18dd40"
    host = "staging.adamspay.com"
    path = "/api/v1/debts"
    
    # Hora en UTC para la validez de la deuda
    inicio_validez = datetime.datetime.utcnow().replace()
    fin_validez = inicio_validez + datetime.timedelta(days=2)  # Validez de 2 días

    # Crear la deuda con el monto total del carrito
    deuda = {
        "docId": f"orden-{orden.id}",  # Identificador único de la deuda, basado en la orden
        "amount": {"currency": "PYG", "value": str(total_carrito)},  # Total del carrito
        "label": "Pago de Carrito de Compras",
        "validPeriod": {
            "start": inicio_validez.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": fin_validez.strftime("%Y-%m-%dT%H:%M:%S")
        }
    }

    # Preparar la petición
    payload = json.JSONEncoder().encode({"debt": deuda}).encode("utf-8")
    headers = {"apikey": apiKey, "Content-Type": "application/json", "x-if-exists": "update"}
    
    # Hacer la solicitud a AdamsPay
    conn = http.client.HTTPSConnection(host)
    conn.request("POST", path, payload, headers)
    data = conn.getresponse().read().decode("utf-8")
    response = json.JSONDecoder().decode(data)

    # Verificar la respuesta
    if "debt" in response:
        return response["debt"]["payUrl"]  # Devuelve la URL de pago
    else:
        raise Exception("Error al crear la deuda en AdamsPay")


def crear_orden(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Crear o obtener el cliente
    cliente, created = Cliente.objects.get_or_create(
        email=request.POST['email'],
        defaults={'nombre': request.POST['nombre']}
    )

    # Crear la orden en Django
    orden = Orden.objects.create(
        cliente=cliente,
        producto=producto,
        monto=producto.precio,
        estado='pendiente'
    )

    try:
        # Intentar crear la deuda en AdamsPay
        pay_url = crear_deuda_adamspay(orden)
        
        # Redirigir al cliente a la URL de pago
        return redirect(pay_url)

    except Exception as e:
        # Manejar errores en caso de fallos en la creación de la deuda
        return redirect('error_de_pago')  # Redirige a una página de error de pago

def ver_ordenes_cliente(request):
    ordenes = Orden.objects.filter(cliente=request.user)
    return render(request, 'ordenes_cliente.html', {'ordenes': ordenes})

def ver_ordenes_admin(request):
    ordenes = Orden.objects.all()  
    return render(request, 'ordenes_admin.html', {'ordenes': ordenes})

def procesar_pago(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    if request.method == 'POST':
    
        response = requests.post('https://api.adamspay.com/payment', data={
            'amount': orden.monto,
            'order_id': orden.id,
            
        })
        
        if response.status_code == 200:
            # Si el pago fue exitoso
            orden.estado = 'pagado'
            orden.save()
            return redirect('pago_exitoso')
        else:
            # Si hubo un error en el pago
            return redirect('pago_error')

    return render(request, 'procesar_pago.html', {'orden': orden})

def leer_deuda_adamspay(orden):
    apiKey = "ap-2823a2205aaa3e84df18dd40"
    idDeuda = f"orden-{orden.id}"  # ID de la deuda (usamos la ID de la orden)
    host = "staging.adamspay.com"
    path = "/api/v1/debts/" + idDeuda
    headers = {"apikey": apiKey}
    
    # Hacer la petición a AdamsPay
    conn = http.client.HTTPSConnection(host)
    conn.request("GET", path, "", headers)
    data = conn.getresponse().read().decode("utf-8")
    response = json.JSONDecoder().decode(data)

    if "debt" in response:
        debt = response["debt"]
        payUrl = debt["payUrl"]
        label = debt["label"]
        objStatus = debt["objStatus"]["status"]
        payStatus = debt["payStatus"]["status"]
        isPaid = payStatus == "paid"
        isActive = objStatus == "active" or objStatus == "alert" or objStatus == "success"

        return {
            "payUrl": payUrl,
            "label": label,
            "isPaid": isPaid,
            "isActive": isActive,
            "payDate": debt["payStatus"]["time"] if isPaid else None
        }
    else:
        raise Exception("Error al leer la deuda en AdamsPay")

# Vista para verificar el estado de una deuda
def estado_deuda(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)

    try:
        # Leer el estado de la deuda en AdamsPay
        estado_deuda = leer_deuda_adamspay(orden)

        # Pasar el estado de la deuda a la plantilla
        return render(request, 'estado_deuda.html', {'orden': orden, 'estado_deuda': estado_deuda})

    except Exception as e:
        return render(request, 'error.html', {'mensaje': str(e)})
    
def eliminar_deuda_adamspay(orden):
    apiKey = "ap-2823a2205aaa3e84df18dd40"
    idDeuda = f"orden-{orden.id}"  # El ID de la deuda es el ID de la orden
    notificarAlWebhook = "true"  # O "false" si no quieres notificar al webhook
    host = "staging.adamspay.com"
    path = "/api/v1/debts/" + idDeuda
    headers = {"apikey": apiKey, "x-should-notify": notificarAlWebhook}
    
    # Hacer la petición DELETE a AdamsPay
    conn = http.client.HTTPSConnection(host)
    conn.request("DELETE", path, "", headers)
    data = conn.getresponse().read().decode("utf-8")
    
    # Decodificar la respuesta
    response = json.JSONDecoder().decode(data)

    # Verificar la respuesta
    if "debt" in response:
        return True, response["debt"]  # Deuda eliminada exitosamente
    else:
        return False, response.get("meta", "Error desconocido")

# Vista para eliminar una deuda
def eliminar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)

    try:
        # Llamar a la función para eliminar la deuda en AdamsPay
        success, resultado = eliminar_deuda_adamspay(orden)
        
        if success:
            # Si la deuda fue eliminada borrar la orden 
            orden.delete()
            return redirect('orden_eliminada')  # Redirigir a una página de confirmación
        else:
            # Si hubo un error
            return render(request, 'error.html', {'mensaje': resultado})
    
    except Exception as e:
        return render(request, 'error.html', {'mensaje': str(e)})

@login_required(login_url='login')    
def comprar_carrito(request):
    carrito = Carrito(request)  # Obtener el carrito actual
    total_carrito = carrito.get_total_precio()  # Calcular el total del carrito

    # Obtener el cliente basado en el usuario autenticado
    cliente = Cliente.objects.get(user=request.user)

    # Crear una nueva orden
    orden = Orden.objects.create(
        cliente=cliente,
        monto=total_carrito,
        estado='pendiente'
    )

    # Agregar todos los productos del carrito a la orden
    for key, item in carrito.carrito.items():
        producto = Producto.objects.get(id=item['producto_id'])
        orden.productos.add(producto)  # Relacionar los productos con la orden

    # Limpiar el carrito después de la compra
    carrito.limpiar()

    try:
        # Generar la deuda en AdamsPay o redirigir al cliente después de la compra
        url_pago = crear_deuda_adamspay(orden, total_carrito)

        return redirect(url_pago)

    except Exception as e:
        return render(request, 'error.html', {'mensaje': str(e)})
    

def obtener_info_app_adamspay():
    apiKey = "ap-2823a2205aaa3e84df18dd40"
    host = "staging.adamspay.com"
    path = "/api/v1/self"
    headers = {"apikey": apiKey}

    # Hacer la solicitud GET a AdamsPay
    conn = http.client.HTTPSConnection(host)
    conn.request("GET", path, "", headers)
    data = conn.getresponse().read().decode("utf-8")
    
    # Decodificar la respuesta
    response = json.JSONDecoder().decode(data)
    
    # Verificar si la respuesta contiene la información de la aplicación
    if "app" in response:
        return response["app"]  # Devolver la información de la aplicación
    else:
        raise Exception("Error al obtener la información de la aplicación")


def info_app(request):
    try:
        # Obtener la información de la aplicación desde AdamsPay
        info_app = obtener_info_app_adamspay()

        # Renderizar la información en la plantilla
        return render(request, 'info_app.html', {'info_app': info_app})

    except Exception as e:
        return render(request, 'error.html', {'mensaje': str(e)})

    
    
import base64
from io import BytesIO

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .forms import *
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserChangeForm
from transbank.webpay.webpay_plus.transaction import Transaction
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from django.shortcuts import render
from django.db.models import Count, Sum, Avg
from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models.functions import ExtractMonth
import calendar, locale
from django.http import HttpResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from django.http import HttpResponse
from django.template.loader import render_to_string
import os
import tempfile
from xhtml2pdf import pisa
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
import time
from django.template.defaultfilters import register
from weasyprint import HTML



def index(request):
    habitaciones = Habitacion.objects.filter(disponible=True)[:3]  #limito la vista previa a 3
    return render(request, 'app/index.html', {'habitaciones': habitaciones})  

def hospedaje(request):
    habitaciones = Habitacion.objects.all()
    return render(request, 'app/hospedaje.html', {'habitaciones': habitaciones})

@login_required
def solicitud(request):
    if request.method == 'POST':
        form = SolicitudForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.usuario = request.user  
            solicitud.correo_contacto = request.user.email 
            solicitud.save()
            return redirect('index') 
    else:
        form = SolicitudForm()

    return render(request, 'app/solicitud.html', {'form': form})
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# REGISTRO, LOGIN Y LOGOUT
def registro(request):
    form = None  
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user) 
            return redirect('index')  
    else:
        form = RegistroForm()  
    
    return render(request, 'registration/registro.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


@require_POST
def logoutView(request):
    logout(request)
    return redirect('index')
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#GESTIÓN DE HABITACIONES
def habitacion_detalle(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, habitacion_id=habitacion_id)
    return render(request, 'app/habitacion_detalle.html', {'habitacion': habitacion})

@login_required
@staff_member_required
@permission_required('app.change_habitacion')
def mod_room(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, habitacion_id=habitacion_id)
    if request.method == 'POST':
        habitacion_form = HabitacionForm(request.POST, instance=habitacion, files=request.FILES)
        imagen_form = ImagenDirectaForm(request.POST, request.FILES)
        if habitacion_form.is_valid():
            habitacion_form.save()
            return redirect("list_room")
        if imagen_form.is_valid():
            imagen = imagen_form.save(commit=False)
            imagen.habitacion = habitacion
            imagen.save()
            return redirect("list_room")
    else:
        habitacion_form = HabitacionForm(instance=habitacion)
        imagen_form = ImagenDirectaForm()

    return render(request, 'hospedaje/mod_room.html', {
        'form': habitacion_form,
        'imagen_form': imagen_form,
    })

@login_required
@staff_member_required
def list_room(request):
    habitaciones = Habitacion.objects.all() 
    return render(request, 'hospedaje/list_room.html', {'habitaciones': habitaciones})

@login_required
@staff_member_required
def add_room(request):
    if request.method == 'POST':
        habitacion_form = HabitacionForm(request.POST)
        if habitacion_form.is_valid():
            habitacion_form.save()
            return redirect('list_room')
    else:
        habitacion_form = HabitacionForm()
    
    return render(request, 'hospedaje/add_room.html', {
        'habitacion_form': habitacion_form
    })


@login_required
@staff_member_required
def erase_room(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, habitacion_id=habitacion_id)
    if request.method == 'POST':
        habitacion.delete()
        return redirect('list_room')
    return redirect('list_room')
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
# GESTIÓN DE IMÁGENES
@login_required
@staff_member_required
def add_image_to_room(request):
    if request.method == 'POST':
        form = ImagenDirectaForm(request.POST, request.FILES)
        if form.is_valid():
            imagen = form.save(commit=False)
            habitacion_id = request.POST.get('habitacion_id')
            imagen.habitacion = get_object_or_404(Habitacion, habitacion_id=habitacion_id)
            imagen.save()
            return redirect('list_room') 
    else:
        form = ImagenDirectaForm()

    return render(request, 'app/add_image_to_room.html', {'form': form})


def list_images(request):
    if request.method == 'POST':
        form = ImagenDirectaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    else:
        form = ImagenDirectaForm()
    habitaciones = Habitacion.objects.all()
    context = {
        'form': form,
        'habitaciones': habitaciones,
    }
    return render(request, 'hospedaje/list_room.html', context)
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#GESTIÓN DE RESERVAS
from django.http import JsonResponse

# Función para obtener las reservas de una habitación específica
@login_required
def get_reservas_habitacion(request, habitacion_id):
    reservas = Reserva.objects.filter(habitacion_id=habitacion_id).values('fecha_entrada', 'fecha_salida')

    # Bloque de depuración para verificar las fechas
    for reserva in reservas:
        print(f"Reserva encontrada: desde {reserva['fecha_entrada']} hasta {reserva['fecha_salida']}")
    
    return JsonResponse(list(reservas), safe=False)

@login_required
def habitacion_detalle(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, habitacion_id=habitacion_id)
    precio_final = None

    # Obtener las fechas ocupadas de la habitación
    reservas = habitacion.reservas.all()  # Asegúrate de que la relación está definida en el modelo
    fechas_ocupadas = []
    for reserva in reservas:
        fecha_actual = reserva.fecha_entrada
        while fecha_actual <= reserva.fecha_salida:
            fechas_ocupadas.append(fecha_actual.strftime('%Y-%m-%d'))
            fecha_actual += timedelta(days=1)

    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            # Crear y guardar la reserva en la base de datos
            reserva = form.save(commit=False)
            reserva.cliente = request.user
            reserva.habitacion = habitacion
            fecha_entrada_str = request.POST.get("fecha_entrada")
            fecha_salida_str = request.POST.get("fecha_salida")
            
            # Convertir las fechas de string a datetime
            fecha_entrada = datetime.strptime(fecha_entrada_str, "%Y-%m-%d")
            fecha_salida = datetime.strptime(fecha_salida_str, "%Y-%m-%d")
            
            reserva.fecha_entrada = fecha_entrada
            reserva.fecha_salida = fecha_salida
            reserva.total_dias = (fecha_salida - fecha_entrada).days
            reserva.precio_final = reserva.total_dias * habitacion.precio_noche
            reserva.save()

            # Redirigir a la vista de iniciar el pago con el ID de la reserva
            return redirect('iniciar_pago', reserva_id=reserva.reserva_id)
    else:
        form = ReservaForm()

    return render(request, 'app/habitacion_detalle.html', {
        'habitacion': habitacion,
        'form': form,
        'precio_final': precio_final,
        'fechas_ocupadas': fechas_ocupadas,  # Agregar las fechas ocupadas al contexto
    })


@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, reserva_id=reserva_id, cliente=request.user)
    if request.method == 'POST':
        reserva.delete()
        return redirect('my_room')
    return render(request, 'app/cancelar_reserva.html', {'reserva': reserva})



@login_required
def confirmar_entrega(request, reserva_id):
    reserva = get_object_or_404(Reserva, reserva_id=reserva_id, cliente=request.user)
    return redirect('opinion_form', reserva_id=reserva_id)

@login_required
def opinion_form(request, reserva_id):
    reserva = get_object_or_404(Reserva, reserva_id=reserva_id, cliente=request.user)
    if request.method == 'POST':
        calificacion = request.POST.get('calificacion')
        comentario = request.POST.get('comentario')
        Opinion.objects.create(
            reserva=reserva,
            cliente=request.user,
            calificacion=calificacion,
            comentario=comentario
        )
        return redirect('my_room')
    return render(request, 'profile/opinion_form.html', {'reserva': reserva})
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#GESTIÓN DE USUARIOS
@login_required
@staff_member_required
def add_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_user') 
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'usuarios/add_user.html', {'form': form})


@login_required
@staff_member_required
def list_user(request):
    usuarios = User.objects.all()
    return render(request, 'usuarios/list_user.html', {'usuarios': usuarios})


@login_required
@staff_member_required
@permission_required('auth.delete_user', raise_exception=True)
def erase_user(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if usuario.is_superuser:
        #messages.error(request, "No puedes eliminar a otro administrador.")
        return redirect('list_user')
    
    if request.method == 'POST':
        usuario.delete()
        #messages.success(request, "Usuario eliminado correctamente.")
        return redirect('list_user')
    
    return render(request, 'usuarios/erase_user.html', {'usuario': usuario})


@login_required
@staff_member_required
@permission_required('auth.change_user', raise_exception=True)
def mod_user(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('list_user')
    else:
        form = CustomUserChangeForm(instance=usuario)
    
    return render(request, 'usuarios/mod_user.html', {'form': form, 'usuario': usuario})
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#PERFIL DE USUARIO
@login_required
def perfil(request):
    perfil, created = Perfil.objects.get_or_create(user=request.user)
    
    context = {
        'user': request.user,
        'perfil': perfil
    }
    return render(request, 'profile/perfil.html', context)


@login_required
def mod_perfil(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('perfil') 
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'profile/mod_perfil.html', context)
#####################################
# / / / / / / / / / / / / / / / / / #
#####################################
#GESTIÓN DE SOLICITUDES
@login_required
def list_soli(request):
    if request.user.is_staff:
        solicitudes = Solicitud.objects.all()
    else:
        solicitudes = Solicitud.objects.filter(usuario=request.user)
    
    context = {
        'solicitudes': solicitudes
    }
    return render(request, 'solicitud/list_soli.html', context)


@login_required
@permission_required('app.change_solicitud', raise_exception=True)
def mod_soli(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, solicitud_id=solicitud_id)
    
    if request.method == 'POST':
        form = ModificarSolicitudForm(request.POST, instance=solicitud)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de solicitudes después de guardar
            return redirect('list_soli')  # Ajusta este nombre de URL si es necesario
    else:
        form = ModificarSolicitudForm(instance=solicitud)
    
    context = {
        'form': form,
        'solicitud': solicitud
    }
    return render(request, 'solicitud/mod_soli.html', context)

#SOLICITUDES DE USUARIO
@login_required
def my_soli(request):
    solicitudes = Solicitud.objects.filter(usuario=request.user)
    
    context = {
        'solicitudes': solicitudes
    }
    return render(request, 'profile/my_soli.html', context)


def my_soli_det(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, solicitud_id=solicitud_id, usuario=request.user)
    
    context = {
        'solicitud': solicitud
    }
    return render(request, 'profile/my_soli_det.html', context)


@login_required
def my_room(request):
    reservas = Reserva.objects.filter(cliente=request.user)
    return render(request, 'profile/my_room.html', {'reservas': reservas})


@login_required
def my_room_det(request, reserva_id):
    reserva = get_object_or_404(Reserva, reserva_id=reserva_id, cliente=request.user)
    return render(request, 'profile/my_room_det.html', {'reserva': reserva})

def iniciar_pago(request, reserva_id):
    reserva = get_object_or_404(Reserva, reserva_id=reserva_id)
    transaction = Transaction()

    try:
        # Usa el total de la reserva para el monto de la transacción
        amount = float(reserva.precio_final)

        response = transaction.create(
            buy_order=f"orden_{request.user.id}_{reserva_id}",
            session_id=request.session.session_key,
            amount=amount,
            return_url=request.build_absolute_uri(reverse("pago_completado"))
        )

        return redirect(response["url"] + "?token_ws=" + response["token"])

    except Exception as e:
        return render(request, 'pago/error_pago.html', {'error': str(e), 'reserva': reserva})
    

def pago_completado(request):
    token = request.GET.get("token_ws")  # Token retornado por Transbank
    transaction = Transaction()

    try:
        # Confirma la transacción con Transbank
        response = transaction.commit(token)

        if response['status'] == "AUTHORIZED":
            # Manejo de pago exitoso
            return render(request, 'pago/pago_exitoso.html', {'response': response})
        else:
            # Manejo de pago rechazado
            return render(request, 'pago/pago_fallido.html', {'response': response})

    except Exception as e:
        # Manejo de errores
        return render(request, 'pago/error_pago.html', {'error': str(e)})
    
    

def generar_contexto_reporte():
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    # Métricas existentes
    total_clientes = User.objects.count()
    total_reservas = Reserva.objects.count()
    ingresos_totales = Reserva.objects.aggregate(Sum('precio_final'))['precio_final__sum'] or 0

    habitaciones_mas_reservadas = (
        Reserva.objects.values('habitacion__nombre')
        .annotate(total=Count('reserva_id'))
        .order_by('-total')[:5]
    )

    reservas_por_mes = (
        Reserva.objects.annotate(mes=ExtractMonth('fecha_entrada'))
        .values('mes')
        .annotate(total=Count('reserva_id'))
        .order_by('mes')
    )

    # Nuevas métricas
    reservas_por_tipo = (
        Reserva.objects.values('habitacion__tipo_hab')
        .annotate(total=Count('reserva_id'))
        .order_by('-total')
    )

    duracion_promedio_reservas = (
        Reserva.objects.aggregate(promedio=Avg('total_dias'))['promedio'] or 0
    )

    habitaciones_menos_reservadas = (
        Reserva.objects.values('habitacion__nombre')
        .annotate(total=Count('reserva_id'))
        .order_by('total')[:1]
    )

    ingresos_por_mes = (
        Reserva.objects.annotate(mes=ExtractMonth('fecha_entrada'))
        .values('mes')
        .annotate(total_ingresos=Sum('precio_final'))
        .order_by('mes')
    )

    for ingreso in ingresos_por_mes:
        ingreso['mes_nombre'] = calendar.month_name[ingreso['mes']].capitalize()

    habitaciones_mejor_calificadas = (
        Opinion.objects.values('habitacion__nombre')
        .annotate(promedio_calificacion=Avg('calificacion'))
        .order_by('-promedio_calificacion')[:5]
    )

    # Generar gráficos con Matplotlib
    # Gráfico de Barras: Ingresos Totales por Mes
    meses = [calendar.month_name[ingreso['mes']] for ingreso in ingresos_por_mes]
    ingresos = [ingreso['total_ingresos'] for ingreso in ingresos_por_mes]

    fig1, ax1 = plt.subplots()
    ax1.bar(meses, ingresos, color="skyblue")
    ax1.set_title("Ingresos Totales por Mes")
    ax1.set_ylabel("Ingresos (CLP)")
    ax1.set_xlabel("Mes")
    plt.xticks(rotation=45, ha="right")

    buffer1 = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer1, format="png")
    buffer1.seek(0)
    grafico_barras = base64.b64encode(buffer1.getvalue()).decode("utf-8")
    buffer1.close()
    plt.close(fig1)

    # Gráfico Circular: Reservas por Tipo de Habitación
    tipos_habitacion = [tipo["habitacion__tipo_hab"] for tipo in reservas_por_tipo]
    reservas = [tipo["total"] for tipo in reservas_por_tipo]

    fig2, ax2 = plt.subplots()
    ax2.pie(
        reservas,
        labels=tipos_habitacion,
        autopct="%1.1f%%",
        startangle=90,
        colors=plt.cm.Paired.colors,
    )
    ax2.set_title("Reservas por Tipo de Habitación")

    buffer2 = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer2, format="png")
    buffer2.seek(0)
    grafico_circular = base64.b64encode(buffer2.getvalue()).decode("utf-8")
    buffer2.close()
    plt.close(fig2)

    context = {
        # Métricas existentes
        'total_clientes': total_clientes,
        'total_reservas': total_reservas,
        'ingresos_totales': ingresos_totales,
        'habitaciones_mas_reservadas': habitaciones_mas_reservadas,
        'reservas_por_mes': reservas_por_mes,

        # Nuevas métricas
        'reservas_por_tipo': reservas_por_tipo,
        'duracion_promedio_reservas': duracion_promedio_reservas,
        'habitaciones_menos_reservadas': habitaciones_menos_reservadas,
        'ingresos_por_mes': ingresos_por_mes,
        'habitaciones_mejor_calificadas': habitaciones_mejor_calificadas,

        # Gráficos
        'grafico_barras': grafico_barras,
        'grafico_circular': grafico_circular,
    }

    return context

@login_required
def mostrar_reporte(request):
    context = generar_contexto_reporte()
    return render(request, 'app/reporte.html', context)

@login_required
def generar_reporte(request):
    context = generar_contexto_reporte()

    # Renderizar el template HTML a string
    html_string = render_to_string('app/reporte.html', context)

    # Convertir HTML a PDF usando WeasyPrint
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    # Enviar el archivo PDF como respuesta
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte.pdf"'

    return response
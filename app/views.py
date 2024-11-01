from .forms import *
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserChangeForm


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
    return render(request, 'app/index.html')
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

    # Obtener todas las reservas para la habitación
    reservas = Reserva.objects.filter(habitacion=habitacion)

    # Obtener las fechas ocupadas en formato 'YYYY-MM-DD'
    fechas_ocupadas = [
        {
            'fecha_entrada': reserva.fecha_entrada.strftime('%Y-%m-%d'),
            'fecha_salida': reserva.fecha_salida.strftime('%Y-%m-%d')
        }
        for reserva in reservas
    ]

    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.cliente = request.user
            reserva.habitacion = habitacion
            total_dias = (reserva.fecha_salida - reserva.fecha_entrada).days
            reserva.precio_final = total_dias * habitacion.precio_noche
            reserva.save()
            return redirect('my_room')
    else:
        form = ReservaForm()

    return render(request, 'app/habitacion_detalle.html', {
        'habitacion': habitacion,
        'form': form,
        'fechas_ocupadas': fechas_ocupadas  # Pasar las fechas ocupadas al template
    })



@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, reserva_id=reserva_id, cliente=request.user)
    if request.method == 'POST':
        reserva.delete()
        return redirect('my_room')
    return render(request, 'app/cancelar_reserva.html', {'reserva': reserva})


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
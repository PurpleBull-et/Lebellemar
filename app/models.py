from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.utils import timezone
import os

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    direccion = models.CharField(max_length=255, blank=False, null=False)
    telefono = models.CharField(max_length=15, blank=False, null=False)

    def __str__(self):
        return f'{self.user.username} - {self.direccion}'


class Habitacion(models.Model):
    habitacion_id = models.AutoField(primary_key=True)  # AutoField ID
    num_hab = models.CharField(max_length=10)
    tipo_hab = models.CharField(max_length=50)
    precio_noche = models.DecimalField(max_digits=10, decimal_places=2)  # DecimalField para precios
    nombre = models.TextField() 
    descripcion = models.TextField()
    disponible = models.BooleanField(default=True)   

    def __str__(self):
        return f'Habitación {self.num_hab} ({self.tipo_hab})'
    
    def precio_noche_clp(self):
        return f"CLP {self.precio_noche:,.0f}"



class Imagen(models.Model):
    habitacion = models.ForeignKey(Habitacion, related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='app/static/app/img/imagenes_habitaciones/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:  
            extension = os.path.splitext(self.imagen.name)[1]
            nuevo_nombre = f"{self.habitacion.num_hab}_{now().strftime('%Y%m%d_%H%M%S')}{extension}"
            self.imagen.name = nuevo_nombre
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Imagen para {self.habitacion.num_hab}'


class Reserva(models.Model):
    reserva_id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE,related_name='reservas')
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField()
    precio_final = models.DecimalField(max_digits=10, decimal_places=2)
    total_dias = models.IntegerField(blank=True, null=True)
    fecha_reservacion = models.DateTimeField(default=timezone.now)  

    def save(self, *args, **kwargs):
        # Calcular el total de días antes de guardar
        if self.fecha_entrada and self.fecha_salida:
            self.total_dias = (self.fecha_salida - self.fecha_entrada).days
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Reserva {self.reserva_id} - {self.cliente} en {self.habitacion}'


class Solicitud(models.Model):
    solicitud_id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    asunto = models.CharField(max_length=100)
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    correo_contacto = models.EmailField(max_length=254)
    estado = models.BooleanField(default=True)
    respuesta = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'Solicitud {self.solicitud_id} - {self.usuario.username}'
    

class Opinion(models.Model):
    habitacion = models.ForeignKey(
        'Habitacion', 
        on_delete=models.CASCADE, 
        related_name='opiniones'
    )
    cliente = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='opiniones'
    )
    reserva = models.ForeignKey(
        'Reserva', 
        on_delete=models.CASCADE, 
        related_name='opiniones'
    )  # Vincular con la reserva
    calificacion = models.PositiveSmallIntegerField()  # Número entre 1 y 10
    comentario = models.TextField()  # Comentario del cliente
    fecha_opinion = models.DateTimeField(default=now)  # Fecha de la opinión

    def str(self):
        return f'Opinión de {self.cliente.username} para Habitación {self.habitacion.num_hab}'

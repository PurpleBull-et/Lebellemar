from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from django.forms.widgets import DateInput


class RegistroForm(UserCreationForm):
    direccion = forms.CharField(
        max_length=255, 
        required=True, 
        help_text='Introduce tu dirección.',
        label='Dirección'
    )
    telefono = forms.CharField(
        max_length=15, 
        required=True, 
        help_text='Introduce tu número de teléfono.',
        label='Teléfono'
    )
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'direccion', 'telefono']
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Primer nombre',
            'last_name': 'Apellido',
            'email': 'Correo',
            'password1': 'Contraseña',
            'password2': 'Confirmar Contraseña',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            Perfil.objects.create(
                user=user,
                direccion=self.cleaned_data['direccion'],
                telefono=self.cleaned_data['telefono']
            )
        return user
    
#AÑADIR HABITACIONES
class HabitacionForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['num_hab', 'tipo_hab', 'precio_noche', 'nombre', 'descripcion', 'disponible']
        labels = {
            'num_hab': 'Número de Habitación',
            'tipo_hab': 'Tipo de Habitación',
            'precio_noche': 'Precio por Noche',
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'disponible': 'Disponible',
        }

class ImagenForm(forms.ModelForm):
    class Meta:
        model = Imagen
        fields = ['imagen']
        labels = {
            'imagen': 'Imagen de la Habitación',
        }
        widgets = {
            'imagen': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
        
class ImagenDirectaForm(forms.ModelForm):
    class Meta:
        model = Imagen
        fields = ['imagen']

#SOLICITUD
class SolicitudForm(forms.ModelForm):
    ASUNTO_CHOICES = [
        ('Reserva', 'Problemas con la reserva'),
        ('Habitacion', 'Problemas con la habitación'),
        ('Pago', 'Problemas con el pago'),
        ('Otros', 'Otros'),
    ]

    asunto = forms.ChoiceField(
        choices=ASUNTO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Solicitud
        fields = ['asunto', 'mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'placeholder': 'Escribe tu mensaje aquí...', 'class': 'form-control'}),
        }

#GEST. DE SOLICITUD
class ModificarSolicitudForm(forms.ModelForm):
    respuesta = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Escribe la respuesta aquí...'}),
        required=False,
        label='Respuesta'
    )

    class Meta:
        model = Solicitud
        fields = ['asunto', 'mensaje', 'correo_contacto', 'estado', 'respuesta']
        labels = {
            'asunto': 'Asunto',
            'mensaje': 'Mensaje',
            'correo_contacto': 'Correo de Contacto',
            'estado': 'Estado de la Solicitud',
        }
        widgets = {
            'mensaje': forms.Textarea(attrs={'readonly': 'readonly'}),
            'asunto': forms.TextInput(attrs={'readonly': 'readonly'}),
            'correo_contacto': forms.EmailInput(attrs={'readonly': 'readonly'}),
        }


#RESERVAR HABITACIÓN
class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['fecha_entrada', 'fecha_salida']


#MODIFICAR USUARIOS
class CustomUserChangeForm(forms.ModelForm):
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    direccion = forms.CharField(label="Dirección", max_length=255, required=False)
    telefono = forms.CharField(label="Teléfono", max_length=15, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'perfil'):
            self.fields['direccion'].initial = self.instance.perfil.direccion
            self.fields['telefono'].initial = self.instance.perfil.telefono

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()

        if hasattr(user, 'perfil'):
            perfil = user.perfil
            perfil.direccion = self.cleaned_data['direccion']
            perfil.telefono = self.cleaned_data['telefono']
            perfil.save()

        return user

#CREAR USUARIOS COMO ADMIN
class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar Contraseña', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class OpinionForm(forms.ModelForm):
    class Meta:
        model = Opinion
        fields = ['calificacion', 'comentario']  # Campos que el usuario puede llenar
        widgets = {
            'calificacion': forms.NumberInput(attrs={'min': 1, 'max': 10, 'class': 'form-control', 'placeholder': 'Calificación (1-10)'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Escribe tu comentario aquí...'}),
        }
        labels = {
            'calificacion': 'Calificación',
            'comentario': 'Comentario',
        }
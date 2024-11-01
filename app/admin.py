from django.contrib import admin
from .models import *

class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'direccion', 'telefono')

admin.site.register(Perfil, PerfilAdmin)

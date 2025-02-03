from django.contrib import admin
from .models import Persona, RegistroAcceso,Cliente

admin.site.register(Persona)
admin.site.register(RegistroAcceso)
admin.site.register(Cliente)
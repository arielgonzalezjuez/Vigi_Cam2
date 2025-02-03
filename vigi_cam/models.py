from django.db import models
from django.contrib.auth.models import AbstractUser

class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    carnet_identidad = models.CharField(max_length=20)
    cargo = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='imagenes_personas/')
    horaE = models.TimeField()
    horaS = models.TimeField()

    def _str_(self):
        return self.nombre

class Camara(models.Model):
    nombreC = models.CharField(max_length=50)
    numero_ip = models.CharField(max_length=100)
    puerto = models.IntegerField()
    usuario = models.CharField(max_length=100, default='admin')
    password = models.CharField(max_length=100, default='123456')

    def _str_(self):
        return self.nombreC

class RegistroAcceso(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    imagen_capturada = models.ImageField(upload_to='imagenes_capturadas/')

    def __str__(self):
        return f"{self.persona or 'Desconocido'} - {self.fecha_hora}"


    def _str_(self):
        return f'{self.persona.nombre} - {self.fecha_hora}'

class Cliente(AbstractUser):
      direccion = models.CharField(max_length=200)
      telefono = models.CharField(max_length=20)
      
      def __str__(self):
          return self.first_name
      
from django.db import models

class Video(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='videos_capturados/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
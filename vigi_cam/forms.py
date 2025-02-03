from django import forms
from .models import Persona, Camara
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['nombre', 'carnet_identidad', 'cargo', 'imagen', 'horaE','horaS']

class CamaraForm(forms.ModelForm):
    class Meta:
        model = Camara
        fields = ['nombreC', 'numero_ip', 'puerto']

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Cliente

class ClienteRegistrarForm(UserCreationForm):
    class Meta:
        model = Cliente
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 'direccion', 'password1', 'password2')

class ClienteActualizarForm(UserChangeForm):
    class Meta:
        model = Cliente
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 'direccion')
   

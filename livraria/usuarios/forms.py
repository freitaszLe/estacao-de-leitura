# usuarios/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Cliente

class ClienteCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Cliente
        fields = ('username', 'cpf', 'first_name', 'last_name') # Campos pedidos no cadastro
        labels = {
            'username': 'Nome de Usuário',
            'cpf': 'CPF',
            'first_name': 'Primeiro Nome',
            'last_name': 'Sobrenome',
        }

class ClienteLoginForm(forms.Form):
    cpf = forms.CharField(max_length=14, label='CPF')
    password = forms.CharField(widget=forms.PasswordInput, label='Senha')
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required # Importe o decorador
from .forms import ClienteCreationForm, ClienteLoginForm
from .models import Pedido, ItemPedido
from livros.models import Livro

def cadastro_view(request):
    if request.method == 'POST':
        form = ClienteCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect('livros:home')
    else:
        form = ClienteCreationForm()
    return render(request, 'registration/cadastro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = ClienteLoginForm(request.POST)
        if form.is_valid():
            cpf = form.cleaned_data.get('cpf')
            password = form.cleaned_data.get('password')
            user = authenticate(request, cpf=cpf, password=password)
            if user is not None:
                login(request, user)
                return redirect('livros:home')
            else:
                messages.error(request, "CPF ou senha inválidos.")
    else:
        form = ClienteLoginForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('livros:home')

@login_required
def estante_view(request):
    # Passo 1: Pegue todos os IDs de livros dos pedidos do usuário.
    # O values_list('livro', flat=True) retorna uma lista de IDs, como: [1, 5, 2, 5, 1]
    livros_ids = ItemPedido.objects.filter(pedido__usuario=request.user).values_list('livro', flat=True)
    
    # Passo 2: Remova os IDs duplicados.
    # O set() transforma a lista em um conjunto, removendo duplicatas: {1, 2, 5}
    unique_livros_ids = set(livros_ids)
    
    # Passo 3: Busque os objetos Livro correspondentes a esses IDs únicos.
    livros_na_estante = Livro.objects.filter(id__in=unique_livros_ids)
    
    context = {
        # Enviamos os objetos Livro diretamente para o template
        'livros_na_estante': livros_na_estante
    }
    return render(request, 'estante.html', context)
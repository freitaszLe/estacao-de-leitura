from django.shortcuts import render, redirect
from django.shortcuts import render, redirect, get_object_or_404

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
    # 1. Busca todos os itens de pedidos do usuário, otimizando a busca com select_related
    todos_os_itens = ItemPedido.objects.filter(pedido__usuario=request.user).order_by('-pedido__data_pedido').select_related('livro')
    
    # Listas e conjuntos para separar os itens e evitar duplicatas
    itens_comprados = []
    ids_livros_comprados = set()
    
    itens_alugados = []
    ids_livros_alugados = set()

    # 2. Itera sobre todos os itens e os separa nas listas corretas
    for item in todos_os_itens:
        # Adiciona à lista de COMPRADOS se for 'venda' e ainda não estiver na lista
        if item.tipo_transacao == 'venda' and item.livro.id not in ids_livros_comprados:
            itens_comprados.append(item)
            ids_livros_comprados.add(item.livro.id)
        # Adiciona à lista de ALUGADOS se for 'aluguel' e ainda não estiver na lista
        elif item.tipo_transacao == 'aluguel' and item.livro.id not in ids_livros_alugados:
            itens_alugados.append(item)
            ids_livros_alugados.add(item.livro.id)

    # 3. Envia as duas listas separadas para o template
    context = {
        'itens_comprados': itens_comprados,
        'itens_alugados': itens_alugados
    }
    return render(request, 'estante.html', context)

@login_required
def devolver_livro(request, item_id):
    # Adicionamos uma verificação para garantir que a ação só ocorra via POST, por segurança
    if request.method == 'POST':
        # Garante que o usuário só possa devolver um item que lhe pertence
        item_pedido = get_object_or_404(ItemPedido, id=item_id, pedido__usuario=request.user)
        
        # Marca o item como devolvido e salva
        if not item_pedido.devolvido:
            item_pedido.devolvido = True
            item_pedido.save()
            messages.success(request, f"O livro '{item_pedido.livro.titulo}' foi marcado como devolvido.")
        else:
            messages.info(request, "Este livro já foi devolvido.")

    # Redireciona de volta para a estante em qualquer caso
    return redirect('usuarios:estante')
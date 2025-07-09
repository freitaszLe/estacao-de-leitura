# livros/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Livro, Genero

def home(request):
    livros_destaque = Livro.objects.filter(em_destaque=True)
    livros_mais_vendidos = Livro.objects.filter(disponivel_para_venda=True).order_by('-total_vendas')[:10]
    livros_mais_alugados = Livro.objects.filter(disponivel_para_aluguel=True).order_by('-total_alugueis')[:10]
    generos = Genero.objects.all()
    context = {
        'livros_destaque': livros_destaque, 'livros_mais_vendidos': livros_mais_vendidos,
        'livros_mais_alugados': livros_mais_alugados, 'generos': generos
    }
    return render(request, 'home.html', context)

def comprar(request):
    livros = Livro.objects.filter(disponivel_para_venda=True)
    generos = Genero.objects.all()
    return render(request, 'comprar.html', {'livros': livros, 'generos': generos})

def alugar(request):
    livros = Livro.objects.filter(disponivel_para_aluguel=True)
    generos = Genero.objects.all()
    return render(request, 'alugar.html', {'livros': livros, 'generos': generos})

def detalhes_livro(request, id):
    livro = get_object_or_404(Livro, id=id)
    return render(request, 'detalhes_livro.html', {'livro': livro})

# --- Lógica do Carrinho (Pode ficar aqui, pois não depende do usuário logado) ---
def adicionar_ao_carrinho(request, livro_id, tipo):
    carrinho = request.session.get('carrinho', {})
    if not isinstance(carrinho, dict): carrinho = {}
    livro_id_str = str(livro_id)
    livro = get_object_or_404(Livro, id=livro_id)
    if tipo == 'venda' and livro.disponivel_para_venda:
        carrinho[livro_id_str] = {'tipo': 'venda'}
        messages.success(request, f"'{livro.titulo}' foi adicionado para compra.")
    elif tipo == 'aluguel' and livro.disponivel_para_aluguel:
        carrinho[livro_id_str] = {'tipo': 'aluguel'}
        messages.success(request, f"'{livro.titulo}' foi adicionado para aluguel.")
    else:
        messages.error(request, "Ação inválida ou livro indisponível.")
    request.session['carrinho'] = carrinho
    request.session.modified = True
    return redirect('livros:ver_carrinho')

def remover_do_carrinho(request, livro_id):
    carrinho = request.session.get('carrinho', {})
    livro_id_str = str(livro_id)
    if livro_id_str in carrinho:
        del carrinho[livro_id_str]
        messages.info(request, "Livro removido do carrinho.")
    request.session['carrinho'] = carrinho
    request.session.modified = True
    return redirect('livros:ver_carrinho')

def ver_carrinho(request):
    carrinho = request.session.get('carrinho', {})
    if not isinstance(carrinho, dict): carrinho = {}
    itens_venda, itens_aluguel = [], []
    total_venda, total_aluguel = 0, 0
    for livro_id_str, info in carrinho.items():
        livro = get_object_or_404(Livro, id=int(livro_id_str))
        if info['tipo'] == 'venda':
            itens_venda.append(livro)
            total_venda += livro.preco_venda or 0
        elif info['tipo'] == 'aluguel':
            itens_aluguel.append(livro)
            total_aluguel += livro.preco_aluguel or 0
    context = {
        'itens_venda': itens_venda, 'itens_aluguel': itens_aluguel,
        'total_venda': total_venda, 'total_aluguel': total_aluguel,
    }
    return render(request, 'carrinho.html', context)
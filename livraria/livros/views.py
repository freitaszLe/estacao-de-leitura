from django.shortcuts import redirect, render, get_object_or_404
from .models import Livro, Genero
from django.contrib import messages
from django.db.models import F

def home(request):

    
    # Busca livros marcados como "em_destaque" para o carrossel
    livros_destaque = Livro.objects.filter(em_destaque=True)

    # Busca os 10 livros mais vendidos, ordenando pelo campo total_vendas
    livros_mais_vendidos = Livro.objects.filter(disponivel_para_venda=True).order_by('-total_vendas')[:10]

    # Busca os 10 livros mais alugados, ordenando pelo campo total_alugueis
    livros_mais_alugados = Livro.objects.filter(disponivel_para_aluguel=True).order_by('-total_alugueis')[:10]
    
    generos = Genero.objects.all()

    context = {
        'livros_destaque': livros_destaque,
        'livros_mais_vendidos': livros_mais_vendidos,
        'livros_mais_alugados': livros_mais_alugados,
        'generos': generos
    }
    return render(request, 'home.html', context)




def comprar(request):
    genero_id = request.GET.get('genero')
    livros = Livro.objects.filter(disponivel_para_venda=True)
    if genero_id:
        livros = livros.filter(genero_id=genero_id)

    generos = Genero.objects.all()
    return render(request, 'comprar.html', {
        'livros': livros,
        'generos': generos
    })

def alugar(request):
    genero_id = request.GET.get('genero')
    livros = Livro.objects.filter(disponivel_para_aluguel=True)
    if genero_id:
        livros = livros.filter(genero_id=genero_id)

    generos = Genero.objects.all()
    return render(request, 'alugar.html', {
        'livros': livros,
        'generos': generos
    })

def detalhes_livro(request, id):
    livro = get_object_or_404(Livro, id=id)
    return render(request, 'detalhes_livro.html', {
        'livro': livro
    })



def adicionar_ao_carrinho(request, livro_id):
    carrinho = request.session.get('carrinho', [])
    if livro_id not in carrinho:
        carrinho.append(livro_id)
        request.session['carrinho'] = carrinho
    return redirect('livros:ver_carrinho')

def remover_do_carrinho(request, livro_id):
    carrinho = request.session.get('carrinho', [])
    if livro_id in carrinho:
        carrinho.remove(livro_id)
        request.session['carrinho'] = carrinho
    return redirect('livros:ver_carrinho')

def ver_carrinho(request):
    carrinho = request.session.get('carrinho', [])
    livros = Livro.objects.filter(id__in=carrinho)
    total = sum(livro.preco_venda for livro in livros)
    return render(request, 'carrinho.html', {
        'livros': livros,
        'total': total
    })


def finalizar_compra(request):
    if request.method == 'POST':
        carrinho_ids = request.session.get('carrinho', [])
        livros_comprados = Livro.objects.filter(id__in=carrinho_ids)

        # Atualiza os contadores
        for livro in livros_comprados:
            livro.total_vendas = F('total_vendas') + 1
            livro.estoque = F('estoque') - 1 # Diminui o estoque
            livro.save()

        request.session['carrinho'] = []
        messages.success(request, "Compra finalizada com sucesso!")
        return redirect('livros:comprar')
from django.shortcuts import redirect, render, get_object_or_404
from .models import Livro, Genero
from django.contrib import messages

def home(request):
    livros_venda = Livro.objects.filter(preco_venda__isnull=False)
    livros_aluguel = Livro.objects.filter(preco_aluguel__isnull=False)
    generos = Genero.objects.all()
    return render(request, 'home.html', {
        'livros_venda': livros_venda,
        'livros_aluguel': livros_aluguel,
        'generos': generos
    })


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
        request.session['carrinho'] = []
        messages.success(request, "Compra finalizada com sucesso!")
        return redirect('livros:comprar')
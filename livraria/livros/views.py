from django.shortcuts import render, get_object_or_404
from .models import Livro, Genero

def livros_para_compra(request):
    genero_id = request.GET.get('genero')
    livros = Livro.objects.filter(disponivel_para_venda=True)
    if genero_id:
        livros = livros.filter(genero_id=genero_id)
    generos = Genero.objects.all()
    return render(request, 'comprar.html', {'livros': livros, 'generos': generos})

def livros_para_aluguel(request):
    genero_id = request.GET.get('genero')
    livros = Livro.objects.filter(disponivel_para_aluguel=True)
    if genero_id:
        livros = livros.filter(genero_id=genero_id)
    generos = Genero.objects.all()
    return render(request, 'livros/alugar.html', {'livros': livros, 'generos': generos})

def detalhes_livro(request, id):
    livro = get_object_or_404(Livro, id=id)
    return render(request, 'livros/detalhes.html', {'livro': livro})

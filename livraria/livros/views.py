from django.shortcuts import redirect, render, get_object_or_404
from .models import Livro, Genero
from django.contrib import messages
from django.db.models import F
from usuarios.models import Pedido, ItemPedido

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



def adicionar_ao_carrinho(request, livro_id, tipo):
    carrinho = request.session.get('carrinho', {})

    # ===== VERIFICAÇÃO DE SEGURANÇA ADICIONADA =====
    # Se o carrinho da sessão não for um dicionário, força a criação de um novo.
    if not isinstance(carrinho, dict):
        carrinho = {}
    # ===============================================

    livro_id_str = str(livro_id)
    livro = get_object_or_404(Livro, id=livro_id)

    # O resto da função continua igual...
    if tipo == 'venda' and livro.disponivel_para_venda:
        carrinho[livro_id_str] = {'tipo': 'venda'}
        messages.success(request, f"'{livro.titulo}' foi adicionado ao carrinho para compra.")
    
    elif tipo == 'aluguel' and livro.disponivel_para_aluguel:
        carrinho[livro_id_str] = {'tipo': 'aluguel'}
        messages.success(request, f"'{livro.titulo}' foi adicionado ao carrinho para aluguel.")
        
    else:
        messages.error(request, "Ação inválida ou livro indisponível para esta operação.")

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
        carrinho = request.session.get('carrinho', {})
        # Pega apenas os itens de venda do carrinho
        itens_venda_carrinho = {k: v for k, v in carrinho.items() if v['tipo'] == 'venda'}

        if not itens_venda_carrinho:
            messages.error(request, "Não há itens para comprar no seu carrinho.")
            return redirect('livros:ver_carrinho')

        # Calcula o total apenas dos itens de venda
        total_pedido = sum((get_object_or_404(Livro, id=int(k))).preco_venda or 0 for k in itens_venda_carrinho)
        
        # 1. CRIA O PEDIDO GERAL NO BANCO DE DADOS
        pedido = Pedido.objects.create(usuario=request.user, total=total_pedido)
        
        # 2. CRIA OS ITENS DO PEDIDO, LIGANDO CADA LIVRO AO PEDIDO CRIADO
        for livro_id_str, info in itens_venda_carrinho.items():
            livro = get_object_or_404(Livro, id=int(livro_id_str))
            ItemPedido.objects.create(
                pedido=pedido, 
                livro=livro, 
                tipo_transacao='venda', 
                preco=livro.preco_venda
            )
            # Atualiza estoque e contadores do livro
            livro.estoque = F('estoque') - 1
            livro.total_vendas = F('total_vendas') + 1
            livro.save()
        
        # 3. Limpa apenas os itens comprados do carrinho na sessão
        request.session['carrinho'] = {k: v for k, v in carrinho.items() if v['tipo'] != 'venda'}
        messages.success(request, f"Compra do Pedido #{pedido.id} finalizada com sucesso!")
        return redirect('usuarios:estante') # Redireciona para a estante para ver o resultado!


def finalizar_aluguel(request):
    if request.method == 'POST':
        carrinho = request.session.get('carrinho', {})
        itens_aluguel_carrinho = {k: v for k, v in carrinho.items() if v['tipo'] == 'aluguel'}

        if not itens_aluguel_carrinho:
            messages.error(request, "Não há itens para alugar no seu carrinho.")
            return redirect('livros:ver_carrinho')
            
        total_pedido = sum((get_object_or_404(Livro, id=int(k))).preco_aluguel or 0 for k in itens_aluguel_carrinho)

        # 1. CRIA O PEDIDO
        pedido = Pedido.objects.create(usuario=request.user, total=total_pedido)
        
        # 2. CRIA OS ITENS DO PEDIDO
        for livro_id_str, info in itens_aluguel_carrinho.items():
            livro = get_object_or_404(Livro, id=int(livro_id_str))
            ItemPedido.objects.create(
                pedido=pedido, 
                livro=livro, 
                tipo_transacao='aluguel', 
                preco=livro.preco_aluguel
            )
            livro.total_alugueis = F('total_alugueis') + 1
            livro.save()

        # 3. LIMPA OS ITENS DE ALUGUEL DO CARRINHO
        request.session['carrinho'] = {k: v for k, v in carrinho.items() if v['tipo'] != 'aluguel'}
        messages.success(request, f"Aluguel do Pedido #{pedido.id} finalizado com sucesso!")
        return redirect('usuarios:estante')
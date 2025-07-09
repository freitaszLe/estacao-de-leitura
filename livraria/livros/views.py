from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.db.models import F
from django.contrib.auth.decorators import login_required # <-- IMPORTAÇÃO ADICIONADA

# Importação dos modelos de ambos os aplicativos
from .models import Livro, Genero
from usuarios.models import Pedido, ItemPedido
from datetime import timedelta
from django.utils import timezone

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
    return render(request, 'comprar.html', {'livros': livros, 'generos': generos})

def alugar(request):
    genero_id = request.GET.get('genero')
    livros = Livro.objects.filter(disponivel_para_aluguel=True)
    if genero_id:
        livros = livros.filter(genero_id=genero_id)
    generos = Genero.objects.all()
    return render(request, 'alugar.html', {'livros': livros, 'generos': generos})

def detalhes_livro(request, id):
    livro = get_object_or_404(Livro, id=id)
    return render(request, 'detalhes_livro.html', {'livro': livro})

def ver_carrinho(request):
    carrinho = request.session.get('carrinho', {})
    if not isinstance(carrinho, dict):
        carrinho = {}
        request.session['carrinho'] = carrinho
    
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
        'itens_venda': itens_venda,
        'itens_aluguel': itens_aluguel,
        'total_venda': total_venda,
        'total_aluguel': total_aluguel,
    }
    return render(request, 'carrinho.html', context)

def adicionar_ao_carrinho(request, livro_id, tipo):
    carrinho = request.session.get('carrinho', {})
    if not isinstance(carrinho, dict):
        carrinho = {}
        
    livro_id_str = str(livro_id)
    livro = get_object_or_404(Livro, id=livro_id)

    if tipo == 'venda' and livro.disponivel_para_venda:
        carrinho[livro_id_str] = {'tipo': 'venda'}
        messages.success(request, f"'{livro.titulo}' foi adicionado para compra.")
    elif tipo == 'aluguel' and livro.disponivel_para_aluguel:
        carrinho[livro_id_str] = {'tipo': 'aluguel'}
        messages.success(request, f"'{livro.titulo}' foi adicionado para aluguel.")
    else:
        messages.error(request, "Ação inválida ou livro indisponível para esta operação.")

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

# CORREÇÃO: Adicionado o decorador de segurança
@login_required
def finalizar_compra(request):
    if request.method == 'POST':
        carrinho = request.session.get('carrinho', {})
        itens_venda_carrinho = {k: v for k, v in carrinho.items() if v['tipo'] == 'venda'}

        if not itens_venda_carrinho:
            messages.error(request, "Não há itens para comprar no seu carrinho.")
            return redirect('livros:ver_carrinho')

        total_pedido = sum((get_object_or_404(Livro, id=int(k))).preco_venda or 0 for k in itens_venda_carrinho)
        
        pedido = Pedido.objects.create(usuario=request.user, total=total_pedido)
        
        for livro_id_str, info in itens_venda_carrinho.items():
            livro = get_object_or_404(Livro, id=int(livro_id_str))
            ItemPedido.objects.create(
                pedido=pedido, 
                livro=livro, 
                tipo_transacao='venda', 
                preco=livro.preco_venda
            )
            livro.estoque = F('estoque') - 1
            livro.total_vendas = F('total_vendas') + 1
            livro.save()
        
        request.session['carrinho'] = {k: v for k, v in carrinho.items() if v['tipo'] != 'venda'}
        request.session.modified = True
        messages.success(request, f"Compra do Pedido #{pedido.id} finalizada com sucesso!")
        return redirect('usuarios:estante')

# CORREÇÃO: Adicionado o decorador de segurança
@login_required
def finalizar_aluguel(request):
    if request.method == 'POST':
        # ... (código existente para pegar o carrinho e calcular o total) ...
        carrinho = request.session.get('carrinho', {})
        itens_aluguel_carrinho = {k: v for k, v in carrinho.items() if v['tipo'] == 'aluguel'}

        if not itens_aluguel_carrinho:
            messages.error(request, "Não há itens para alugar no seu carrinho.")
            return redirect('livros:ver_carrinho')
            
        total_pedido = sum((get_object_or_404(Livro, id=int(k))).preco_aluguel or 0 for k in itens_aluguel_carrinho)

        pedido = Pedido.objects.create(usuario=request.user, total=total_pedido)
        
        # --- ALTERAÇÃO PRINCIPAL AQUI ---
        for livro_id_str, info in itens_aluguel_carrinho.items():
            livro = get_object_or_404(Livro, id=int(livro_id_str))
            
            # Calcula a data de devolução para 30 dias a partir de hoje
            data_devolucao = timezone.now().date() + timedelta(days=30)

            ItemPedido.objects.create(
                pedido=pedido, 
                livro=livro, 
                tipo_transacao='aluguel', 
                preco=livro.preco_aluguel,
                data_devolucao_prevista=data_devolucao, # Salva a data de devolução
                devolvido=False # Marca como não devolvido
            )
            livro.total_alugueis = F('total_alugueis') + 1
            livro.save(update_fields=['total_alugueis'])

        # ... (resto da função para limpar o carrinho e redirecionar) ...
        request.session['carrinho'] = {k: v for k, v in carrinho.items() if v['tipo'] != 'aluguel'}
        request.session.modified = True
        messages.success(request, f"Aluguel (Pedido #{pedido.id}) finalizado com sucesso!")
        return redirect('usuarios:estante')
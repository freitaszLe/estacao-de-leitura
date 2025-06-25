from django.shortcuts import redirect, render, get_object_or_404
from .models import ItemPedido, Livro, Genero, Pedido
from django.contrib import messages
from django.db.models import F
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views import generic


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
    # Pega o carrinho da sessão ou cria um dicionário vazio
    carrinho = request.session.get('carrinho', {})
    
    # Converte o ID para string, pois as chaves da sessão são strings
    livro_id_str = str(livro_id)

    # Adiciona o livro com o tipo de transação
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
    return redirect('livros:ver_carrinho')

def remover_do_carrinho(request, livro_id):
    carrinho = request.session.get('carrinho', {})
    livro_id_str = str(livro_id)

    if livro_id_str in carrinho:
        del carrinho[livro_id_str]
        messages.info(request, "Livro removido do carrinho.")
    
    request.session['carrinho'] = carrinho
    return redirect('livros:ver_carrinho')

def ver_carrinho(request):
    carrinho = request.session.get('carrinho', {})

    # ADICIONE ESTA VERIFICAÇÃO AQUI
    if not isinstance(carrinho, dict):
        # Se o carrinho encontrado não for um dicionário (é do formato antigo),
        # esvazia ele para recomeçar com o formato correto.
        carrinho = {}
        request.session['carrinho'] = carrinho

    # O resto do código continua exatamente igual...
    itens_venda = []
    itens_aluguel = []
    total_venda = 0
    total_aluguel = 0

    for livro_id_str, info in carrinho.items():
        livro = get_object_or_404(Livro, id=int(livro_id_str))
        if info['tipo'] == 'venda':
            itens_venda.append(livro)
            total_venda += livro.preco_venda
        elif info['tipo'] == 'aluguel':
            itens_aluguel.append(livro)
            total_aluguel += livro.preco_aluguel

    context = {
        'itens_venda': itens_venda,
        'itens_aluguel': itens_aluguel,
        'total_venda': total_venda,
        'total_aluguel': total_aluguel,
    }
    return render(request, 'carrinho.html', context)

# livros/views.py

# ... (outras views) ...

@login_required
def finalizar_compra(request):
    if request.method == 'POST':
        carrinho = request.session.get('carrinho', {})
        itens_venda_no_carrinho = {k: v for k, v in carrinho.items() if v['tipo'] == 'venda'}

        if not itens_venda_no_carrinho:
            messages.error(request, "Não há itens para comprar no seu carrinho.")
            return redirect('livros:ver_carrinho')

        total_pedido = 0
        livros_do_pedido = []
        for livro_id_str, info in itens_venda_no_carrinho.items():
            livro = get_object_or_404(Livro, id=int(livro_id_str))
            total_pedido += livro.preco_venda
            livros_do_pedido.append({'livro': livro, 'tipo': 'venda', 'preco': livro.preco_venda})

        # Criar o Pedido
        pedido = Pedido.objects.create(usuario=request.user, total=total_pedido)
        # Criar os Itens do Pedido
        for item in livros_do_pedido:
            ItemPedido.objects.create(
                pedido=pedido,
                livro=item['livro'],
                tipo_transacao=item['tipo'],
                preco=item['preco']
            )
            # Atualizar estoque e contadores
            item['livro'].estoque -= 1
            item['livro'].total_vendas += 1
            item['livro'].save()

        # Limpar apenas os itens de venda do carrinho
        request.session['carrinho'] = {k: v for k, v in carrinho.items() if v['tipo'] != 'venda'}
        messages.success(request, f"Compra do Pedido #{pedido.id} finalizada com sucesso!")
        return redirect('livros:historico_pedidos')

@login_required
def finalizar_aluguel(request):
    # Lógica similar à de finalizar_compra, mas para aluguel
    # (Pode ser implementado seguindo o mesmo padrão)
    if request.method == 'POST':
        carrinho = request.session.get('carrinho', {})
        itens_aluguel_no_carrinho = {k: v for k, v in carrinho.items() if v['tipo'] == 'aluguel'}

        if not itens_aluguel_no_carrinho:
            messages.error(request, "Não há itens para alugar no seu carrinho.")
            return redirect('livros:ver_carrinho')

        total_pedido = 0
        livros_do_pedido = []
        for livro_id_str, info in itens_aluguel_no_carrinho.items():
            livro = get_object_or_404(Livro, id=int(livro_id_str))
            total_pedido += livro.preco_aluguel
            livros_do_pedido.append({'livro': livro, 'tipo': 'aluguel', 'preco': livro.preco_aluguel})
        
        pedido = Pedido.objects.create(usuario=request.user, total=total_pedido)
        for item in livros_do_pedido:
            ItemPedido.objects.create(
                pedido=pedido,
                livro=item['livro'],
                tipo_transacao=item['tipo'],
                preco=item['preco']
            )
            item['livro'].total_alugueis += 1
            item['livro'].save()
        
        request.session['carrinho'] = {k: v for k, v in carrinho.items() if v['tipo'] != 'aluguel'}
        messages.success(request, f"Aluguel do Pedido #{pedido.id} finalizado com sucesso!")
        return redirect('livros:historico_pedidos')
    

@login_required
def historico_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-data_pedido').prefetch_related('itens__livro')
    return render(request, 'historico_pedidos.html', {'pedidos': pedidos})



class RegistrarView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login') # Redireciona para a página de login após o sucesso
    template_name = 'registration/register.html'
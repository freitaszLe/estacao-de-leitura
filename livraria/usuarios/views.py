# usuarios/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
import mercadopago
import json

from .forms import ClienteCreationForm, ClienteLoginForm
from .models import Pedido, ItemPedido
from livros.models import Livro, Genero


# --- Views de Autenticação ---
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


# --- Views de Pedidos e Estante do Usuário ---
@login_required
def historico_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-data_pedido').prefetch_related('itens__livro')
    return render(request, 'historico_pedidos.html', {'pedidos': pedidos})
@login_required

def estante_view(request):
    # Busca todos os itens de pedidos PAGOS do usuário
    todos_os_itens = ItemPedido.objects.filter(
        pedido__usuario=request.user, 
        pedido__status='PAGO'
    ).order_by('-pedido__data_pedido').select_related('livro')
    
    itens_comprados, ids_livros_comprados = [], set()
    itens_alugados = []
    
    for item in todos_os_itens:
        if item.tipo_transacao == 'venda' and item.livro.id not in ids_livros_comprados:
            itens_comprados.append(item)
            ids_livros_comprados.add(item.livro.id)
        elif item.tipo_transacao == 'aluguel':
            itens_alugados.append(item)

    context = {
        'itens_comprados': itens_comprados,
        'itens_alugados': itens_alugados
    }
    return render(request, 'estante.html', context)

@login_required
def devolver_livro(request, item_id):
    if request.method == 'POST':
        item_pedido = get_object_or_404(ItemPedido, id=item_id, pedido__usuario=request.user)
        if not item_pedido.devolvido:
            item_pedido.devolvido = True
            item_pedido.save()
            messages.success(request, f"O livro '{item_pedido.livro.titulo}' foi marcado como devolvido.")
        else:
            messages.info(request, "Este livro já foi devolvido.")
    return redirect('usuarios:estante')


# --- Lógica de Pagamento (Centralizada aqui) ---
@login_required
def finalizar_compra(request):
    return iniciar_pagamento(request, 'venda')

@login_required
def finalizar_aluguel(request):
    return iniciar_pagamento(request, 'aluguel')

@login_required
def iniciar_pagamento(request, tipo_transacao):
    carrinho = request.session.get('carrinho', {})
    itens_no_carrinho = {k: v for k, v in carrinho.items() if v['tipo'] == tipo_transacao}
    if not itens_no_carrinho:
        messages.error(request, f"Não há itens para '{tipo_transacao}' no seu carrinho.")
        return redirect('livros:ver_carrinho')

    total_pedido = 0
    for livro_id_str in itens_no_carrinho:
        livro = get_object_or_404(Livro, id=int(livro_id_str))
        total_pedido += (livro.preco_venda or 0) if tipo_transacao == 'venda' else (livro.preco_aluguel or 0)
    
    # Verificação de segurança: não gerar pix para valor zerado
    if total_pedido <= 0:
        messages.error(request, "Não é possível processar um pedido com valor total zero.")
        return redirect('livros:ver_carrinho')

    pedido = Pedido.objects.create(usuario=request.user, total=total_pedido, status='PENDENTE')
    for livro_id_str in itens_no_carrinho:
        livro = get_object_or_404(Livro, id=int(livro_id_str))
        preco = livro.preco_venda if tipo_transacao == 'venda' else livro.preco_aluguel
        data_devolucao = timezone.now().date() + timedelta(days=30) if tipo_transacao == 'aluguel' else None
        ItemPedido.objects.create(pedido=pedido, livro=livro, tipo_transacao=tipo_transacao, preco=preco, data_devolucao_prevista=data_devolucao)

    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    
    payment_data = {
        "transaction_amount": round(float(total_pedido), 2), # Garante 2 casas decimais
        "description": f"Pedido #{pedido.id} da Estação Literária",
        "payment_method_id": "pix",
        "payer": {
            "email": request.user.email or 'test_user@test.com', # MP exige um email
            "first_name": request.user.first_name or 'Test',
            "last_name": request.user.last_name or 'User',
        },
        "notification_url": settings.SITE_URL + reverse('usuarios:webhook_mercado_pago'),
    }

    # --- INÍCIO DO DEBUG ---
    print("--- DADOS ENVIADOS PARA O MERCADO PAGO ---")
    print(json.dumps(payment_data, indent=4))
    
    payment_response = sdk.payment().create(payment_data)
    payment = payment_response["response"]
    
    print("\n--- RESPOSTA RECEBIDA DO MERCADO PAGO ---")
    print(json.dumps(payment, indent=4))
    # --- FIM DO DEBUG ---
    
    # Verifica se a resposta contém os dados do PIX
    if "point_of_interaction" in payment and "transaction_data" in payment["point_of_interaction"]:
        pedido.payment_id = payment.get("id")
        pedido.pix_qr_code = payment["point_of_interaction"]["transaction_data"].get("qr_code_base64")
        pedido.pix_copia_cola = payment["point_of_interaction"]["transaction_data"].get("qr_code")
        pedido.save()

        request.session['carrinho'] = {k: v for k, v in carrinho.items() if k not in itens_no_carrinho}
        request.session.modified = True
        return redirect('usuarios:pagina_pagamento', pedido_id=pedido.id)
    else:
        # Se não houver dados do PIX, algo deu errado
        messages.error(request, "Não foi possível gerar o PIX. Verifique os logs do servidor.")
        # Opcional: cancelar o pedido que ficou pendente
        pedido.status = 'CANCELADO'
        pedido.save()
        return redirect('livros:ver_carrinho')
    
@login_required
def pagina_pagamento(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return render(request, 'pagamento.html', {'pedido': pedido})

@csrf_exempt
def webhook_mercado_pago(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if data.get("type") == "payment":
            payment_id = data.get("data", {}).get("id")
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            payment_info = sdk.payment().get(payment_id)["response"]
            pedido = Pedido.objects.get(payment_id=payment_info.get("id"))
            if payment_info.get("status") == "approved":
                pedido.status = 'PAGO'
                pedido.save()
    return JsonResponse({"status": "ok"})
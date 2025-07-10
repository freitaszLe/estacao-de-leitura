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


# usuarios/views.py

@login_required
def processar_checkout(request):
    if request.method == 'POST':
        # ... (toda a lógica para pegar os itens e calcular o total continua igual) ...
        livro_ids_selecionados = request.POST.get('checkout_ids', '').split(',')
        if not livro_ids_selecionados or livro_ids_selecionados == ['']:
            messages.error(request, "Nenhum item selecionado para o pagamento.")
            return redirect('livros:ver_carrinho')

        carrinho = request.session.get('carrinho', {})
        total_pedido = 0
        items_list_para_mp = []
        itens_para_processar = {}

        for livro_id_str in livro_ids_selecionados:
            if livro_id_str in carrinho:
                info = carrinho[livro_id_str]
                livro = get_object_or_404(Livro, id=int(livro_id_str))
                preco_unitario = (livro.preco_venda or 0) if info['tipo'] == 'venda' else (livro.preco_aluguel or 0)
                total_pedido += preco_unitario
                itens_para_processar[livro_id_str] = info
                items_list_para_mp.append({
                    "id": str(livro.id), "title": livro.titulo,
                    "description": f"Tipo: {info['tipo'].capitalize()}",
                    "category_id": "books", "quantity": 1,
                    "unit_price": float(preco_unitario)
                })
        
        if total_pedido <= 0:
            messages.error(request, "O valor do pedido deve ser maior que zero.")
            return redirect('livros:ver_carrinho')

        pedido = Pedido.objects.create(usuario=request.user, total=total_pedido, status='PENDENTE')
        for livro_id_str, info in itens_para_processar.items():
            livro = get_object_or_404(Livro, id=int(livro_id_str))
            preco = livro.preco_venda if info['tipo'] == 'venda' else livro.preco_aluguel
            data_devolucao = timezone.now().date() + timedelta(days=30) if info['tipo'] == 'aluguel' else None
            ItemPedido.objects.create(pedido=pedido, livro=livro, tipo_transacao=info['tipo'], preco=preco, data_devolucao_prevista=data_devolucao)

        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        
        # --- CORREÇÃO NA ESTRUTURA DO payment_data ---
        payment_data = {
            "transaction_amount": round(float(total_pedido), 2),
            "description": f"Pedido #{pedido.id} da Estação Literária",
            "payment_method_id": "pix",
            "payer": {
                "email": request.user.email or 'test_user@test.com',
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
            },
            "notification_url": settings.SITE_URL + reverse('usuarios:webhook_mercado_pago'),
            # A lista de 'items' agora vai dentro de 'additional_info'
            "additional_info": {
                "items": items_list_para_mp
            }
        }
        # --- FIM DA CORREÇÃO ---

        payment_response = sdk.payment().create(payment_data)
        
        if payment_response and payment_response.get("status") == 201:
            # ... (resto da lógica de sucesso continua igual) ...
            payment = payment_response.get("response", {})
            pedido.payment_id = payment.get("id")
            pedido.pix_qr_code = payment.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64")
            pedido.pix_copia_cola = payment.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code")
            pedido.save()
            request.session['carrinho'] = {k: v for k, v in carrinho.items() if k not in itens_para_processar}
            request.session.modified = True
            return redirect('usuarios:pagina_pagamento', pedido_id=pedido.id)
        else:
            # ... (resto da lógica de erro continua igual) ...
            pedido.status = 'CANCELADO'
            pedido.save()
            error_message = "Provedor de pagamento recusou a transação. Verifique sua conta Mercado Pago ou tente com um valor maior."
            if payment_response and isinstance(payment_response.get("response"), dict):
                error_message = payment_response["response"].get("message", error_message)
            messages.error(request, f"Falha no pagamento: {error_message}")
            return redirect('livros:ver_carrinho')
            
    return redirect('livros:ver_carrinho')
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
    # --- NOVA LÓGICA PARA CRIAR A LISTA DE ITENS DETALHADA ---
    items_list_para_mp = []
    
    for livro_id_str, info in itens_no_carrinho.items():
        livro = get_object_or_404(Livro, id=int(livro_id_str))
        preco_unitario = (livro.preco_venda or 0) if tipo_transacao == 'venda' else (livro.preco_aluguel or 0)
        total_pedido += preco_unitario

        # Adiciona um dicionário detalhado para cada livro na lista
        items_list_para_mp.append({
            "id": str(livro.id),
            "title": livro.titulo,
            "description": f"Autor: {livro.autor} - Tipo: {info['tipo'].capitalize()}",
            "category_id": "books", # Categoria genérica para livros
            "quantity": 1,
            "unit_price": float(preco_unitario)
        })
    
    if total_pedido <= 0:
        messages.error(request, "Não é possível processar um pedido com valor total zero.")
        return redirect('livros:ver_carrinho')

    # Cria nosso pedido interno
    pedido = Pedido.objects.create(usuario=request.user, total=total_pedido, status='PENDENTE')
    for livro_id_str in itens_no_carrinho:
        # ... (lógica para criar os ItemPedido continua a mesma)
        livro = get_object_or_404(Livro, id=int(livro_id_str))
        preco = livro.preco_venda if carrinho[livro_id_str]['tipo'] == 'venda' else livro.preco_aluguel
        data_devolucao = timezone.now().date() + timedelta(days=30) if carrinho[livro_id_str]['tipo'] == 'aluguel' else None
        ItemPedido.objects.create(pedido=pedido, livro=livro, tipo_transacao=carrinho[livro_id_str]['tipo'], preco=preco, data_devolucao_prevista=data_devolucao)

    # Configura a chamada para a API do Mercado Pago
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    
    payment_data = {
        "transaction_amount": round(float(total_pedido), 2),
        "description": f"Pedido #{pedido.id} da Estação Literária",
        "items": items_list_para_mp, # <-- ADICIONAMOS A LISTA DETALHADA AQUI
        "payment_method_id": "pix",
        "payer": {
            "email": request.user.email or "test_user@test.com",
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
        },
        "notification_url": settings.SITE_URL + reverse('usuarios:webhook_mercado_pago'),
    }

    # O resto da função continua exatamente igual...
    payment_response = sdk.payment().create(payment_data)
    payment = payment_response["response"]
    
    if "point_of_interaction" in payment:
        pedido.payment_id = payment.get("id")
        pedido.pix_qr_code = payment["point_of_interaction"]["transaction_data"].get("qr_code_base64")
        pedido.pix_copia_cola = payment["point_of_interaction"]["transaction_data"].get("qr_code")
        pedido.save()
        request.session['carrinho'] = {k: v for k, v in carrinho.items() if k not in itens_no_carrinho}
        request.session.modified = True
        return redirect('usuarios:pagina_pagamento', pedido_id=pedido.id)
    else:
        # ... (lógica de erro)
        messages.error(request, "Não foi possível gerar o PIX. Verifique os logs do servidor.")
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
        try:
            data = json.loads(request.body)
            
            # A lógica agora verifica 'topic' em vez de 'type'
            if data.get("topic") == "payment":
                
                # O ID do pagamento agora é extraído da URL do campo 'resource'
                resource_url = data.get("resource")
                if resource_url:
                    payment_id = resource_url.split('/')[-1] # Pega a última parte da URL

                    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
                    payment_info = sdk.payment().get(payment_id)["response"]
                    
                    # Encontra nosso pedido pelo ID do pagamento
                    # Usamos 'get' dentro de um try-except para mais segurança
                    try:
                        pedido = Pedido.objects.get(payment_id=payment_info.get("id"))
                        
                        # Se o pagamento foi aprovado, atualiza o status do nosso pedido
                        if payment_info.get("status") == "approved":
                            if pedido.status != 'PAGO':
                                pedido.status = 'PAGO'
                                pedido.save()
                                # Aqui é um ótimo lugar para enviar um e-mail de confirmação!
                    except Pedido.DoesNotExist:
                        # Opcional: Lidar com o caso de não encontrar o pedido
                        pass

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    # Sempre retorne uma resposta 200 OK para o Mercado Pago
    return JsonResponse({"status": "ok"})
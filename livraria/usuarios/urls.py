from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # URLs de autenticação
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # URLs de páginas do usuário logado
    path('estante/', views.estante_view, name='estante'),
    path('historico/', views.historico_pedidos, name='historico_pedidos'),
    path('devolver/<int:item_id>/', views.devolver_livro, name='devolver_livro'),
    
    # URLs de finalização de pedido e pagamento
    path('pagamento/<int:pedido_id>/', views.pagina_pagamento, name='pagina_pagamento'),
    path('webhook-mp/', views.webhook_mercado_pago, name='webhook_mercado_pago'),
    path('processar-checkout/', views.processar_checkout, name='processar_checkout'),
    path('processar-checkout/', views.processar_checkout, name='processar_checkout'),

]
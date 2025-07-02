# livros/urls.py

from django.urls import path
from . import views

app_name = 'livros'

urlpatterns = [
    # URLs Principais
    path('', views.home, name='home'),
    path('comprar/', views.comprar, name='comprar'),
    path('alugar/', views.alugar, name='alugar'),
    path('livro/<int:id>/', views.detalhes_livro, name='detalhes_livro'),

    # URLs do Carrinho
    path('carrinho/', views.ver_carrinho, name='ver_carrinho'),
    
    # --- A CORREÇÃO ESTÁ AQUI ---
    # A rota agora aceita o livro_id E o tipo da transação
    path('carrinho/adicionar/<int:livro_id>/<str:tipo>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    
    path('carrinho/remover/<int:livro_id>/', views.remover_do_carrinho, name='remover_do_carrinho'),
    path('carrinho/finalizar_compra/', views.finalizar_compra, name='finalizar_compra'),
    path('carrinho/finalizar_aluguel/', views.finalizar_aluguel, name='finalizar_aluguel'),
]

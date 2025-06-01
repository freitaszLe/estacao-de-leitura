from django.urls import path
from . import views

app_name = 'livros'

urlpatterns = [
    
    path('home/', views.home, name='home'),
    path('comprar/', views.comprar, name='comprar'),
    path('alugar/', views.alugar, name='alugar'),
    path('livro/<int:id>/', views.detalhes_livro, name='detalhes_livro'),
    path('carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path('carrinho/adicionar/<int:livro_id>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('carrinho/remover/<int:livro_id>/', views.remover_do_carrinho, name='remover_do_carrinho'),
    path('carrinho/finalizar/', views.finalizar_compra, name='finalizar_compra'),

]

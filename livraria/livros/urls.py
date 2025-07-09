from django.urls import path
from . import views

app_name = 'livros'

urlpatterns = [
    # URLs de visualização do catálogo
    path('', views.home, name='home'),
    path('comprar/', views.comprar, name='comprar'),
    path('alugar/', views.alugar, name='alugar'),
    path('livro/<int:id>/', views.detalhes_livro, name='detalhes_livro'),

    # URLs de gerenciamento do carrinho (que usa a sessão)
    path('carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path('carrinho/adicionar/<int:livro_id>/<str:tipo>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('carrinho/remover/<int:livro_id>/', views.remover_do_carrinho, name='remover_do_carrinho'),
]
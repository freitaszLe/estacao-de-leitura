from django.urls import path
from . import views

urlpatterns = [
    path('comprar/', views.livros_para_compra, name='comprar'),   # URL: /livros/comprar/
    path('alugar/', views.livros_para_aluguel, name='alugar'),    # URL: /livros/alugar/
    path('livro/<int:id>/', views.detalhes_livro, name='detalhes_livro'),
]

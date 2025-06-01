from django.urls import path
from . import views

app_name = 'livros'

urlpatterns = [
    path('home/', views.comprar, name='home'),
    path('comprar/', views.comprar, name='comprar'),
    path('alugar/', views.alugar, name='alugar'),
    path('livro/<int:id>/', views.detalhes_livro, name='detalhes_livro'),
]

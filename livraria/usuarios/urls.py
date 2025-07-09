from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('estante/', views.estante_view, name='estante'),
    path('devolver/<int:item_id>/', views.devolver_livro, name='devolver_livro'),

]
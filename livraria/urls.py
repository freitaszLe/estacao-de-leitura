from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('livros/', include(('livros.urls', 'livros'), namespace='livros')),
    path('', views.home, name='home'),
    path('sobre/', views.about, name='about'),
    path('book/', views.book, name='cadastro'),
]

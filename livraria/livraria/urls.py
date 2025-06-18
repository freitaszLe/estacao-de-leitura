from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # CORREÇÃO:
    # Esta única linha agora controla a home e todas as outras páginas de livros.
    # Removemos as linhas separadas para 'livros/' e a home errada.
    path('', include('livros.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
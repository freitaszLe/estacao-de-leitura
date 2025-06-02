from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('livros/', include(('livros.urls', 'livros'), namespace='livros')),
    path('', views.home, name='home'),
    path('sobre/', views.about, name='about'),
    path('book/', views.book, name='cadastro'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

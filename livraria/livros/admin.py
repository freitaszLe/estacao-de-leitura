from django.contrib import admin
from .models import Genero, Livro


@admin.register(Genero)
class GeneroAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome']
    search_fields = ['nome']


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'autor', 'genero', 'preco_do_livro', 'estoque']
    list_filter = ['genero', 'disponivel_para_aluguel', 'disponivel_para_venda']
    search_fields = ['titulo', 'autor']

    def preco_do_livro(self, obj):
        if obj.disponivel_para_venda:
            return f"R$ {obj.preco_venda}"
        elif obj.disponivel_para_aluguel:
            return f"R$ {obj.preco_aluguel}"
        return "-"
    preco_do_livro.short_description = 'Preço'

from django.contrib import admin
from .models import Cliente, Pedido, ItemPedido

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'data_pedido', 'total']
    inlines = [ItemPedidoInline]

# Registra o seu modelo de usuário personalizado
admin.site.register(Cliente)
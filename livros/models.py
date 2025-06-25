from django.db import models
from django.contrib.auth.models import User 

class Genero(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Livro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    genero = models.ForeignKey(Genero, on_delete=models.SET_NULL, null=True)
    capa = models.ImageField(upload_to='capas/', blank=True, null=True)
    preco_venda = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    preco_aluguel = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    disponivel_para_venda = models.BooleanField(default=True)
    disponivel_para_aluguel = models.BooleanField(default=True)
    estoque = models.PositiveIntegerField(default=0)  # Quantidade disponível

    # --- NOVOS CAMPOS ---
    em_destaque = models.BooleanField(default=False)
    total_vendas = models.PositiveIntegerField(default=0)
    total_alugueis = models.PositiveIntegerField(default=0)
    # --------------------

class Pedido(models.Model):
    """Representa um pedido geral feito por um usuário."""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data_pedido = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Pedido {self.id} de {self.usuario.username}"

class ItemPedido(models.Model):
    """Representa um item específico dentro de um pedido."""
    TIPO_CHOICES = [
        ('venda', 'Venda'),
        ('aluguel', 'Aluguel'),
    ]
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    livro = models.ForeignKey(Livro, on_delete=models.PROTECT) # Proteger o livro de ser deletado se estiver em um pedido
    tipo_transacao = models.CharField(max_length=7, choices=TIPO_CHOICES)
    preco = models.DecimalField(max_digits=8, decimal_places=2) # Preço no momento da transação

    def __str__(self):
        return f"{self.livro.titulo} no Pedido {self.pedido.id}"

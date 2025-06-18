from django.db import models

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

    def __str__(self):
        return self.titulo

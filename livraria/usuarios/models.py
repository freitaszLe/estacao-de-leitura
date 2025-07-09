from django.db import models
from django.contrib.auth.models import AbstractUser
from livros.models import Livro # IMPORTANTE: Precisamos saber o que é um Livro
from django.utils import timezone 

class Cliente(AbstractUser):
    cpf = models.CharField(max_length=14, unique=True)
    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username

# --- ADICIONE OS MODELOS DE PEDIDO ABAIXO ---

class Pedido(models.Model):
    """Representa a 'capa' de um pedido, ligada a um usuário."""
    # O ForeignKey agora aponta para o seu modelo Cliente
    usuario = models.ForeignKey(Cliente, on_delete=models.CASCADE)
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
    livro = models.ForeignKey(Livro, on_delete=models.PROTECT)
    tipo_transacao = models.CharField(max_length=7, choices=TIPO_CHOICES)
    preco = models.DecimalField(max_digits=8, decimal_places=2)

    # --- NOVOS CAMPOS PARA O ALUGUEL ---
    data_devolucao_prevista = models.DateField(null=True, blank=True)
    devolvido = models.BooleanField(default=False)
    # ------------------------------------

    def __str__(self):
        return f"{self.livro.titulo} no Pedido {self.pedido.id}"

    # --- NOVA FUNÇÃO PARA CALCULAR A MULTA ---
    @property
    def calcular_multa(self):
        # A multa só se aplica a aluguéis não devolvidos e com prazo vencido
        if self.tipo_transacao == 'aluguel' and not self.devolvido and self.data_devolucao_prevista:
            hoje = timezone.now().date()
            if hoje > self.data_devolucao_prevista:
                dias_atraso = (hoje - self.data_devolucao_prevista).days
                multa = dias_atraso * 10.00 # R$ 10,00 por dia de atraso
                return multa
        return 0 # Retorna 0 se não houver multa
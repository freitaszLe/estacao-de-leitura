from django.db import models
from django.contrib.auth.models import AbstractUser
from livros.models import Livro 
from django.utils import timezone 

class Cliente(AbstractUser):
    cpf = models.CharField(max_length=14, unique=True)
    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username


class Pedido(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PAGO', 'Pago'),
        ('CANCELADO', 'Cancelado'),
    ]
    usuario = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    data_pedido = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDENTE')
    payment_id = models.CharField(max_length=100, null=True, blank=True) # ID do pagamento no Mercado Pago
    pix_qr_code = models.TextField(null=True, blank=True) # QR Code em base64
    pix_copia_cola = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Pedido {self.id} de {self.usuario.username} - {self.status}"

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

    data_devolucao_prevista = models.DateField(null=True, blank=True)
    devolvido = models.BooleanField(default=False)
    # ------------------------------------

    def __str__(self):
        return f"{self.livro.titulo} no Pedido {self.pedido.id}"

    @property
    def calcular_multa(self):
        # A multa só se aplica a aluguéis não devolvidos e com prazo vencido
        if self.tipo_transacao == 'aluguel' and not self.devolvido and self.data_devolucao_prevista:
            hoje = timezone.now().date()
            if hoje > self.data_devolucao_prevista:
                dias_atraso = (hoje - self.data_devolucao_prevista).days
                multa = dias_atraso * 10.00 # R$ 10,00 por dia de atraso
                return multa
        return 0 
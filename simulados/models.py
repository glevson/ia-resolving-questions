from django.db import models
from django.contrib.auth.models import User

class Assunto(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

class Questao(models.Model):
    assunto = models.ForeignKey(Assunto, on_delete=models.CASCADE)
    enunciado = models.TextField()
    opcao_a = models.CharField(max_length=255)
    opcao_b = models.CharField(max_length=255)
    opcao_c = models.CharField(max_length=255)
    opcao_d = models.CharField(max_length=255)
    resposta_correta = models.CharField(max_length=1, choices=[('A','A'), ('B','B'), ('C','C'), ('D','D')])
    resposta_correta = models.CharField(max_length=1, choices=[('A','A'), ('B','B'), ('C','C'), ('D','D')])
    
    # ADICIONE ESTA LINHA:
    justificativa = models.TextField(blank=True, null=True, help_text="Explicação do gabarito")

    def __str__(self):
        return self.enunciado[:50]

class RespostaUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE)
    opcao_escolhida = models.CharField(max_length=1)
    acertou = models.BooleanField(default=False)
    data_resposta = models.DateTimeField(auto_now_add=True)
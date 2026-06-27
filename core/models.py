"""
Definição dos modelos de dados do sistema de Cápsulas do Tempo.

Este módulo contém as entidades principais: Usuario, Capsula e ItemTexto,
além da lógica de validação de datas e proteção de integridade dos registros.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password


class Usuario(AbstractUser):
    """Modelo de usuário personalizado que estende o AbstractUser do Django."""
    email = models.EmailField(unique=True)
    nome = models.CharField(max_length=255)

    def __str__(self):
        """Retorna o nome do usuário para representação legível em logs e interface administrativa."""
        return self.nome


class Capsula(models.Model):
    """Representa uma cápsula do tempo."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='capsulas')
    titulo = models.CharField(max_length=100)
    data_abertura = models.DateField()
    criada_em = models.DateField(auto_now_add=True)
    senha = models.CharField(max_length=128, null=True, blank=True)
    
    def esta_aberta(self):
        """Verifica se a cápsula já atingiu a data de abertura definida."""
        return timezone.localdate() >= self.data_abertura
    
    def pode_ser_editada(self):
        """Determina se a cápsula ainda permite modificações (apenas se não estiver aberta)."""
        return not self.esta_aberta()
    
    def __str__(self):
        """Retorna o título da cápsula para exibição textual do objeto."""
        return self.titulo

    def clean(self):
        """Valida se a data de abertura é válida (não permite datas no passado)."""
        if not self.data_abertura:
            return 
            
        if self.data_abertura < timezone.localdate():
            raise ValidationError({
                'data_abertura': 'A data de abertura não pode estar no passado.'
            })

    def save(self, *args, **kwargs):
        """
        Executa validações completas e protege campos imutáveis antes de salvar.

        Garante que o usuário original e a senha não sejam alterados 
        após a criação da cápsula, mantendo a integridade do registro.
        """
        self.full_clean()

        if self.pk:
            original = Capsula.objects.filter(pk=self.pk).first()

            if original is not None:
                if original.usuario_id != self.usuario_id:
                    raise ValueError('Usuário da cápsula não pode ser alterado.')

                if original.senha and self.senha != original.senha:
                    self.senha = original.senha

        super().save(*args, **kwargs)

    def set_senha(self, raw_password):
        """Gera um hash seguro para a senha bruta fornecida e o armazena no campo senha."""
        if raw_password:
            self.senha = make_password(raw_password)

    def check_senha(self, raw_password):
        """Compara uma senha bruta com o hash armazenado para validar o acesso."""
        if not self.senha:
            return False
        return check_password(raw_password, self.senha)
    
class ItemTexto(models.Model):
    """Conteúdo textual armazenado dentro de uma cápsula específica."""
    capsula = models.ForeignKey(Capsula, on_delete=models.CASCADE, related_name='textos')
    criado_em = models.DateField(auto_now_add=True)
    texto = models.TextField()

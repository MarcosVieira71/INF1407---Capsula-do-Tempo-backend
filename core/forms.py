"""
Módulo de formulários para criação e edição de usuários e cápsulas.

Este módulo define formulários de entrada para cadastro, atualização de perfil,
criação de cápsulas e edição de conteúdo textual associado.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Capsula, Usuario, ItemTexto


class CapsulaForm(forms.ModelForm):
    texto = forms.CharField(widget=forms.Textarea, required=True, label="Texto")
    senha = forms.CharField(widget=forms.PasswordInput, required=True, label="Senha de edição")
    data_abertura = forms.DateField(
        input_formats=[
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d/%m/%y",
        ],
        label="Data de Abertura",
        error_messages={
            'invalid': 'Digite uma data válida (DD/MM/AAAA).',
            'required': 'Informe uma data.',
        }
    )

    class Meta:
        model = Capsula
        fields = ['titulo', 'data_abertura']

    def clean(self):
        """Valida se o texto obrigatório da cápsula foi informado antes de persistir os dados."""
        cleaned_data = super().clean()
        texto = cleaned_data.get('texto')

        if not texto:
            raise forms.ValidationError("Você deve adicionar um texto à cápsula.")

        return cleaned_data


class UsuarioCriarForm(UserCreationForm):
    username = forms.CharField(
        help_text = ''
    )

    password1 = forms.CharField(
    label = "Senha",
    widget = forms.PasswordInput,
    help_text = ''
    )

    password2 = forms.CharField(
        label ="Confirme a senha",
        widget =forms.PasswordInput,
        help_text=''
    )

    class Meta:
        model = Usuario
        fields = ['username', 'nome', 'email']


class UsuarioAtualizarForm(UserChangeForm):
    password = None 

    class Meta:
        model = Usuario
        fields = ['username', 'nome', 'email']


class CapsulaEdicaoForm(forms.ModelForm):
    texto = forms.CharField(widget=forms.Textarea, required=True, label="Texto")
    data_abertura = forms.DateField(
        input_formats=[
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d/%m/%y",
        ],
        label="Data de Abertura",
        error_messages={
            'invalid': 'Digite uma data válida (DD/MM/AAAA).',
            'required': 'Informe uma data.',
        }
    )

    class Meta:
        model = Capsula
        fields = ['titulo', 'data_abertura']

    def clean(self):
        """Garante que o texto editado da cápsula não seja submetido vazio."""
        cleaned_data = super().clean()
        texto = cleaned_data.get('texto')

        if not texto:
            raise forms.ValidationError("Você deve adicionar um texto à cápsula.")

        return cleaned_data

    def save(self, commit=True, item=None):
        """Salva alterações da cápsula e atualiza ou cria o ItemTexto correspondente."""
        capsula = super().save(commit=False)

        if commit:
            capsula.save()

        texto = self.cleaned_data.get('texto')

        if item and getattr(item, 'pk', None):
            item.texto = texto
            item.save()
        else:
            ItemTexto.objects.create(capsula=capsula, texto=texto)

        return capsula

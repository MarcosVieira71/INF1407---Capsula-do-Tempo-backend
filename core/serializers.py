from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import serializers
from .models import Usuario, Capsula, ItemTexto

from drf_spectacular.utils import (
    extend_schema_serializer,
    OpenApiExample,
)

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Cadastro de usuário",
            value={
                "username": "user",
                "nome": "User",
                "email": "user@email.com",
                "password": "12345678",
            },
        )
    ]
)
class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = ('id', 'username', 'nome', 'email', 'password')

    def validate(self, attrs):
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'A senha é obrigatória.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class DeleteUsuarioSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha inválida para excluir a conta.')
        return value


class ItemTextoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemTexto
        fields = ('id', 'texto', 'criado_em')

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Criar cápsula",
            value={
                "titulo": "Minha cápsula",
                "data_abertura": "2027-01-01",
                "senha": "1234",
                "texto": "Mensagem para o futuro"
            },
            request_only=True,
        ),
        OpenApiExample(
            "Resposta",
            value={
                "id": 1,
                "titulo": "Minha cápsula",
                "data_abertura": "2027-01-01",
                "criada_em": "2026-06-25T20:10:00Z",
                "textos": [
                    {
                        "id": 1,
                        "texto": "Mensagem para o futuro",
                        "criado_em": "2026-06-25T20:10:00Z"
                    }
                ]
            },
            response_only=True,
        )
    ]
)
class CapsulaSerializer(serializers.ModelSerializer):
    textos = ItemTextoSerializer(many=True, read_only=True)
    senha = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Capsula
        fields = ('id', 'titulo', 'data_abertura', 'criada_em', 'senha', 'textos')

    def create(self, validated_data):
        request = self.context.get('request')
        texto = None
        if request is not None:
            texto = request.data.get('texto')
        if not texto:
            raise serializers.ValidationError({'texto': 'Este campo é obrigatório.'})

        senha_raw = validated_data.pop('senha', None)
        capsula = Capsula(**validated_data)
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            capsula.usuario = request.user
        if senha_raw:
            capsula.set_senha(senha_raw)
        capsula.save()
        if texto:
            ItemTexto.objects.create(capsula=capsula, texto=texto)
        return capsula

    def update(self, instance, validated_data):
        validated_data.pop('usuario', None)

        if not instance.pode_ser_editada():
            raise serializers.ValidationError({'detail': 'Capsula já está aberta e não pode ser editada.'})

        if instance.senha:
            provided = self.context['request'].data.get('senha')
            if not provided or not instance.check_senha(provided):
                raise serializers.ValidationError({'senha': 'Senha inválida para editar esta cápsula.'})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        texto = self.context['request'].data.get('texto')
        if texto is not None:
            item = instance.textos.first()
            if item:
                item.texto = texto
                item.save()
            else:
                ItemTexto.objects.create(capsula=instance, texto=texto)

        return instance

class AuthorizeSerializer(serializers.Serializer):
    senha = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data['email']
        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_mail(
                'Recuperação de senha',
                f'Use estas informações para redefinir sua senha:\nUID: {uid}\nToken: {token}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

        return user


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user_model = get_user_model()
        user = None

        uid = attrs.get('uid')
        email = attrs.get('email')

        if uid:
            try:
                decoded_uid = force_str(urlsafe_base64_decode(uid))
                user = user_model.objects.get(pk=decoded_uid)
            except (TypeError, ValueError, OverflowError, user_model.DoesNotExist):
                raise serializers.ValidationError({'uid': 'UID inválido.'})
        elif email:
            user = user_model.objects.filter(email__iexact=email).first()
            if not user:
                raise serializers.ValidationError({'email': 'E-mail não encontrado.'})
        else:
            raise serializers.ValidationError({'detail': 'UID ou e-mail precisam ser informados.'})

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({'token': 'Token inválido.'})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

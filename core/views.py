"""
Módulo de views da API para usuários, autenticação e cápsulas.

Este módulo centraliza os endpoints REST responsáveis por registro,
gestão de perfil, fluxo de redefinição de senha e operações completas
de CRUD das cápsulas vinculadas ao usuário autenticado.
"""

from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .models import Capsula, Usuario
from .serializers import (
    CapsulaSerializer,
    DeleteUsuarioSerializer,
    UsuarioSerializer,
    AuthorizeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)

@extend_schema(tags=["Usuários"])
class UsuarioCreateView(generics.CreateAPIView):
    """Endpoint para registro de novos usuários."""
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=["Usuários"])
class CurrentUserView(generics.RetrieveUpdateAPIView):
    """Endpoint para recuperar e atualizar o perfil do usuário autenticado."""
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retorna o usuário autenticado da requisição atual para leitura e atualização do próprio perfil."""
        return self.request.user

    def delete(self, request, *args, **kwargs):
        """Valida a senha informada e remove definitivamente a conta do usuário autenticado."""
        serializer = DeleteUsuarioSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)

        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Autenticação"])
class PasswordResetRequestView(generics.GenericAPIView):
    """Solicita a redefinição de senha para um usuário existente."""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """Processa a solicitação de recuperação de senha e dispara as instruções por e-mail quando aplicável."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Se o e-mail estiver cadastrado, as instruções de recuperação serão enviadas.'},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Autenticação"])
class PasswordResetConfirmView(generics.GenericAPIView):
    """Confirma a redefinição de senha usando UID e token recebidos por e-mail."""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """Valida UID/token recebidos e efetiva a alteração para a nova senha enviada no payload."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Senha redefinida com sucesso.'}, status=status.HTTP_200_OK)


@extend_schema(tags=["Cápsulas"])
class CapsulaViewSet(viewsets.ModelViewSet):
    """Gerencia listagem, criação, edição e remoção de cápsulas do usuário autenticado."""
    queryset = Capsula.objects.all()
    serializer_class = CapsulaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filtra as cápsulas para retornar somente registros pertencentes ao usuário autenticado."""
        return Capsula.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        """Associa automaticamente o usuário logado ao criar uma nova cápsula."""
        serializer.save(usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        """Atualiza uma cápsula apenas quando ela ainda está no período permitido de edição."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if not instance.pode_ser_editada():
            return Response({'detail': 'Capsula já está aberta e não pode ser editada.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


    @extend_schema(
        request=AuthorizeSerializer,
        responses={200: None},
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def authorize(self, request, pk=None):
        """Verifica se a senha informada autoriza edição da cápsula."""
        capsula = self.get_object()
        senha = request.data.get('senha')
        if capsula.check_senha(senha):
            return Response({'authorized': True})
        return Response({'authorized': False}, status=status.HTTP_400_BAD_REQUEST)

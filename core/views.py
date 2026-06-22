from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .models import Capsula, Usuario
from .serializers import (
    CapsulaSerializer,
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
        return self.request.user


@extend_schema(tags=["Autenticação"])
class PasswordResetRequestView(generics.GenericAPIView):
    """Solicita a redefinição de senha para um usuário existente."""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
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
        return Capsula.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def update(self, request, *args, **kwargs):
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

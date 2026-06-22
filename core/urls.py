from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CapsulaViewSet,
    UsuarioCreateView,
    CurrentUserView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
)

router = DefaultRouter()
router.register(r'capsulas', CapsulaViewSet, basename='capsula')

urlpatterns = [
    path('register/', UsuarioCreateView.as_view(), name='register'),
    path('user/', CurrentUserView.as_view(), name='current-user'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('', include(router.urls)),
]

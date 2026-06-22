from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from ..models import Capsula, Usuario


class CapsulaModelTest(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(username='teste', password='123')

    def test_nao_permite_data_no_passado(self):
        capsula = Capsula(
            usuario=self.user,
            titulo="Teste",
            data_abertura=timezone.localdate() - timedelta(days=1)
        )

        with self.assertRaises(ValidationError):
            capsula.full_clean()

    def test_capsula_fechada(self):
        capsula = Capsula.objects.create(
            usuario=self.user,
            titulo="Teste",
            data_abertura=timezone.localdate() + timedelta(days=1)
        )
        self.assertFalse(capsula.esta_aberta())

    def test_capsula_aberta(self):
        capsula = Capsula.objects.create(
            usuario=self.user,
            titulo="Teste",
            data_abertura=timezone.localdate() + timedelta(days=1)
        )

        capsula.data_abertura = timezone.localdate() - timedelta(days=1)

        self.assertTrue(capsula.esta_aberta())

    def test_password_cannot_be_changed(self):
        capsula = Capsula.objects.create(
            usuario=self.user,
            titulo='SenhaTest',
            data_abertura=timezone.localdate()+ timedelta(days=1)
        )

        capsula.set_senha('orig')
        capsula.save()

        capsula.refresh_from_db()
        original_hash = capsula.senha

        capsula.senha = 'tampered'
        capsula.save()
        capsula.refresh_from_db()

        self.assertEqual(capsula.senha, original_hash)
        self.assertTrue(capsula.check_senha('orig'))
        self.assertFalse(capsula.check_senha('tampered'))

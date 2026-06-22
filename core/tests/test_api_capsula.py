from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta
from ..models import Usuario, Capsula, ItemTexto


class CapsulaAPITest(APITestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(username='apiuser', password='apipass', email='api@example.com', nome='API User')
        token_resp = self.client.post('/api/token/', {'username': 'apiuser', 'password': 'apipass'})
        self.access = token_resp.data['access']

    def auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')

    def test_create_capsule_authenticated(self):
        self.auth()
        data = {
            'titulo': 'Minha cápsula',
            'data_abertura': (timezone.localdate() + timedelta(days=1)).isoformat(),
            'texto': 'Conteúdo inicial',
            'senha': 'segredo123'
        }
        resp = self.client.post('/api/capsulas/', data)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Capsula.objects.count(), 1)

    def test_does_not_create_capsule_without_texto(self):
        self.auth()
        data = {
            'titulo': 'Minha cápsula',
            'data_abertura': (timezone.localdate() + timedelta(days=1)).isoformat(),
            'senha': 'segredo123'
        }
        resp = self.client.post('/api/capsulas/', data)
        self.assertEqual(resp.status_code, 400)
        self.assertIn('texto', resp.data)

    def test_post_capsule_not_logged_in(self):
        data = {
            'titulo': 'Teste',
            'data_abertura': (timezone.localdate() + timedelta(days=1)).isoformat(),
            'texto': 'Conteúdo'
        }
        resp = self.client.post('/api/capsulas/', data)
        self.assertEqual(resp.status_code, 401)

    def test_capsule_associated_with_user(self):
        self.auth()
        data = {
            'titulo': 'Teste',
            'data_abertura': (timezone.localdate() + timedelta(days=1)).isoformat(),
            'texto': 'Conteúdo',
            'senha': 'segredo123'
        }
        self.client.post('/api/capsulas/', data)
        capsula = Capsula.objects.first()
        self.assertEqual(capsula.usuario, self.user)

    def test_authorize_action(self):
        # create capsule via model (simulate creation)
        capsula = Capsula.objects.create(usuario=self.user, titulo='Teste', data_abertura=timezone.localdate()+timedelta(days=1))
        capsula.set_senha('mypass')
        capsula.save()

        self.auth()
        resp_wrong = self.client.post(f'/api/capsulas/{capsula.pk}/authorize/', {'senha': 'wrong'})
        self.assertEqual(resp_wrong.status_code, 400)

        resp_ok = self.client.post(f'/api/capsulas/{capsula.pk}/authorize/', {'senha': 'mypass'})
        self.assertEqual(resp_ok.status_code, 200)
        self.assertEqual(resp_ok.data.get('authorized'), True)

    def test_update_requires_password(self):
        self.auth()
        # create with password
        resp = self.client.post('/api/capsulas/', {
            'titulo': 'EditTest',
            'data_abertura': (timezone.localdate()+ timedelta(days=1)).isoformat(),
            'texto': 'Original',
            'senha': 'mypass'
        })
        self.assertEqual(resp.status_code, 201)
        capsula_id = resp.data['id']

        # attempt update without senha
        update_resp = self.client.patch(f'/api/capsulas/{capsula_id}/', {'titulo': 'Novo Titulo', 'texto': 'Novo Texto'}, format='json')
        self.assertEqual(update_resp.status_code, 400)

        # update with correct senha
        ok_resp = self.client.patch(f'/api/capsulas/{capsula_id}/', {'titulo': 'Titulo Editado', 'texto': 'Texto Editado', 'senha': 'mypass'}, format='json')
        self.assertEqual(ok_resp.status_code, 200)

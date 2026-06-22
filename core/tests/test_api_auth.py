from rest_framework.test import APITestCase
from django.urls import reverse
from ..models import Usuario
from django.utils import timezone
from datetime import timedelta
from django.core import mail


class AuthAPITest(APITestCase):
    def test_register_success(self):
        data = {
            'username': 'testuser',
            'nome': 'Test User',
            'email': 'test@example.com',
            'password': 'testpass123'
        }

        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Usuario.objects.filter(username='testuser').exists())

    def test_token_obtain_and_access_protected(self):
        user = Usuario.objects.create_user(username='existing', password='oldpass123', email='existing@example.com', nome='Existing')

        token_resp = self.client.post('/api/token/', {'username': 'existing', 'password': 'oldpass123'})
        self.assertEqual(token_resp.status_code, 200)
        self.assertIn('access', token_resp.data)

        access = token_resp.data['access']

        # access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.get('/api/capsulas/')
        self.assertEqual(resp.status_code, 200)

    def test_protected_requires_auth(self):
        resp = self.client.get('/api/capsulas/')
        self.assertEqual(resp.status_code, 401)

    def test_password_reset_request_and_confirm(self):
        user = Usuario.objects.create_user(
            username='recover',
            password='oldpass123',
            email='recover@example.com',
            nome='Recover User'
        )

        with self.settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            request_resp = self.client.post('/api/password-reset/', {'email': user.email})

        self.assertEqual(request_resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        body = mail.outbox[0].body
        uid = body.split('UID: ')[1].splitlines()[0]
        token = body.split('Token: ')[1].strip()

        confirm_resp = self.client.post('/api/password-reset/confirm/', {
            'uid': uid,
            'token': token,
            'new_password': 'newpass123'
        })

        self.assertEqual(confirm_resp.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass123'))

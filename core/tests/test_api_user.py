from rest_framework.test import APITestCase
from ..models import Usuario


class UserAPITest(APITestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username='profileuser',
            password='profilepass123',
            email='profile@example.com',
            nome='Profile User'
        )
        token_resp = self.client.post('/api/token/', {'username': 'profileuser', 'password': 'profilepass123'})
        self.access = token_resp.data['access']

    def auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')

    def test_get_current_user_requires_authentication(self):
        resp = self.client.get('/api/user/')
        self.assertEqual(resp.status_code, 401)

    def test_get_current_user_returns_profile_data(self):
        self.auth()
        resp = self.client.get('/api/user/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], self.user.username)
        self.assertEqual(resp.data['email'], self.user.email)
        self.assertEqual(resp.data['nome'], self.user.nome)
        self.assertNotIn('password', resp.data)

    def test_update_current_user_with_put(self):
        self.auth()
        data = {
            'username': 'editeduser',
            'nome': 'Edited User',
            'email': 'edited@example.com',
            'password': 'newpass456'
        }
        resp = self.client.put('/api/user/', data, format='json')
        self.assertEqual(resp.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'editeduser')
        self.assertEqual(self.user.nome, 'Edited User')
        self.assertEqual(self.user.email, 'edited@example.com')
        self.assertTrue(self.user.check_password('newpass456'))

    def test_update_current_user_without_password_keeps_existing_password(self):
        self.auth()
        data = {
            'username': 'editeduser2',
            'nome': 'Edited User 2',
            'email': 'edited2@example.com'
        }
        resp = self.client.put('/api/user/', data, format='json')
        self.assertEqual(resp.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'editeduser2')
        self.assertEqual(self.user.nome, 'Edited User 2')
        self.assertEqual(self.user.email, 'edited2@example.com')
        self.assertTrue(self.user.check_password('profilepass123'))

    def test_delete_current_user_requires_authentication(self):
        resp = self.client.delete('/api/user/', {'password': 'profilepass123'}, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_delete_current_user_with_valid_password(self):
        self.auth()
        resp = self.client.delete('/api/user/', {'password': 'profilepass123'}, format='json')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Usuario.objects.filter(pk=self.user.pk).exists())

    def test_delete_current_user_with_invalid_password(self):
        self.auth()
        resp = self.client.delete('/api/user/', {'password': 'wrong-password'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(Usuario.objects.filter(pk=self.user.pk).exists())

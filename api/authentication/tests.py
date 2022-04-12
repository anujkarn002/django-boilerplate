from django.urls import reverse

from core.tests import BaseAPITestCase


class AuthenticationAPITestCase(BaseAPITestCase):

    def setUp(self):
        super().setUp()

    def test_user_can_login(self):
        """
        Test that a user can login
        """
        url = reverse('jwt-create')
        data = {
            "username": self.roger_user.username,
            "password": "2424df22"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        expected = ['refresh', 'access']
        for key in expected:
            self.assertIn(key, response.data.get('data'))

    def test_user_can_login_with_email(self):
        """
        Test that a user can login
        """
        url = reverse('jwt-create')
        data = {
            "username": self.roger_user.email,
            "password": "2424df22"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        expected = ['refresh', 'access']
        for key in expected:
            self.assertIn(key, response.data.get('data'))

    def test_user_can_login_with_phone(self):
        """
        Test that a user can login
        """

        # save phone number
        self.roger_user.phone = '8090872323'
        self.roger_user.save()

        url = reverse('jwt-create')
        data = {
            "username": self.roger_user.phone,
            "password": "2424df22"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        expected = ['refresh', 'access']
        for key in expected:
            self.assertIn(key, response.data.get('data'))

    def test_user_can_refresh_token(self):
        """
        Test that a user can refresh token
        """
        url = reverse('jwt-create')
        data = {
            "username": self.roger_user.username,
            "password": "2424df22"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        expected = ['refresh', 'access']
        for key in expected:
            self.assertIn(key, response.data.get('data'))

        url = reverse('jwt-refresh')
        data = {
            "refresh": response.data.get('data')['refresh']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        expected = ['access']
        for key in expected:
            self.assertIn(key, response.data.get('data'))

    def test_user_can_revoke_token(self):
        """
        Test that a user can revoke token
        """
        url = reverse('jwt-create')
        data = {
            "username": self.roger_user.username,
            "password": "2424df22"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        expected = ['refresh', 'access']
        for key in expected:
            self.assertIn(key, response.data.get('data'))

        url = reverse('jwt-revoke')
        data = {
            "refresh": response.data.get('data')['refresh']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        expected = ['detail']
        for key in expected:
            self.assertIn(key, response.data)
            self.assertEqual(response.data.get('detail'), 'Successfully revoked token')


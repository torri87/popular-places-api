from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase
from django.core import mail


User = get_user_model()

REGISTER_URL = '/api/auth/register/'
LOGIN_URL = '/api/auth/login/'
LOGOUT_URL = '/api/auth/logout/'
ME_URL = '/api/auth/me/'
RESET_URL = '/api/auth/password-reset/'
RESET_CONFIRM_URL = '/api/auth/password-reset/confirm/'

PASSWORD = 'StrongPass123!'


class RegisterTests(APITestCase):
    def test_register_success(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "tom", "email": "tom@example.com", "password": PASSWORD},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        self.assertTrue(User.objects.filter(username="tom").exists())

    def test_register_duplicate_email(self):
        User.objects.create_user('bob', 'bob@example.com', PASSWORD)
        response = self.client.post(
            REGISTER_URL,
            {"username": "tom", "email": "BOB@example.com", "password": PASSWORD},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "tom", "email": "tom@example.com", "password": "12345678"},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginLogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("alex", "alex@example.com", PASSWORD)

    def test_login_success(self):
        response = self.client.post(
            LOGIN_URL,
            {"username": "alex", "password": PASSWORD},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        me = self.client.get(ME_URL)
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data['username'], 'alex')

    def test_login_wrong_password(self):
        response = self.client.post(
            LOGIN_URL,
            {"username": "alex", "password": "wrong"},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        self.client.login(username="alex", password=PASSWORD)
        response = self.client.post(
            LOGOUT_URL,
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        me_response = self.client.get(ME_URL)
        self.assertIn(me_response.status_code, [401, 403])


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("alex", "alex@example.com", PASSWORD)
        self.uid = urlsafe_base64_encode(force_bytes(self.user.id))
        self.token = default_token_generator.make_token(self.user)

    def test_request_sends_email_existing_user(self):
        response = self.client.post(
            RESET_URL,
            {"email": "alex@example.com"},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_request_for_unknown_email(self):
        response = self.client.post(
            RESET_URL,
            {"email": "unknow@example.com"},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_password_token_one_time(self):
        payload = {"uid": self.uid, "token": self.token, "new_password": "NewPas!@#123"}
        first_response = self.client.post(
            RESET_CONFIRM_URL,
            payload,
            format='json',
        )
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPas!@#123"))

        second_response = self.client.post(
            RESET_CONFIRM_URL,
            payload,
            format='json',
        )
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_fake_uid(self):
        response = self.client.post(
            RESET_CONFIRM_URL,
            {"uid": "fake_uid", "token": self.token, "new_password": "NewPas!@#123"},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
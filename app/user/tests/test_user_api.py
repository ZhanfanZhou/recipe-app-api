"""
User Api tests.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """Create a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public user Apis (registeration not required)."""

    def setUp(self):
        """Override to setup client for each test."""
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user successfully."""
        payload = {
            'email': 'test@example.com',
            'password': 'password',
            'name': 'Test username',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_create_user_email_exists_error(self):
        """Test raising error if creating a user with a existing email."""
        payload = {
            'email': 'test@example.com',
            'password': 'password',
            'name': 'Test username',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_password_too_short_error(self):
        """Test raising error if creating a user with a weak password."""
        payload = {
            'email': 'test@example.com',
            'password': 'short',
            'name': 'Test username',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        exist = get_user_model().objects \
            .filter(email=payload['email']) \
            .exists()
        self.assertFalse(exist)

    def test_create_token(self):
        """Test generating token for valid credentials."""
        user_info = {
            'email': 'test@example.com',
            'password': 'password',
            'name': 'Test username',
        }
        create_user(**user_info)
        payload = {
            'email': user_info['email'],
            'password': user_info['password'],
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_bad_credentials(self):
        """Test raising error if bad credentials"""
        user_info = {
            'email': 'test@example.com',
            'password': 'password',
            'name': 'Test username',
        }
        create_user(**user_info)
        payload = {
            'email': user_info['email'],
            'password': 'invalid_password',
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {'email': 'test@example.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for the ME endpoint."""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test Api endpoints that requires authentication."""

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='password',
            name='Test username',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the me endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {'name': 'Updated name', 'password': 'newpassword123'}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        # self.user = get_user_model().objects.get(email=self.user.email)
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

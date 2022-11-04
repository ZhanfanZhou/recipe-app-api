"""
Test custom user model.
"""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email='text@example.com', password='password'):
    return get_user_model().objects.create(email=email, password=password)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test successfully creating a user with an email"""
        email = 'test@example.com'
        password = 'password!'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(email, user.email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'testpassword')
            self.assertEqual(user.email, expected)

    def test_create_new_user_without_email_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'testpassword')

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test a user creating a recipe."""
        user = get_user_model().objects.create_user(
            email='test@example.com',
            password='password'
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe',
            time_minutes=4,
            price=Decimal('6.98'),
            description='sample description.',
        )
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test creating a tag."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='test tag')

        self.assertEqual(tag.name, str(tag))

    def test_create_ingredient(self):
        """Test creating a ingredient."""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Test ingredient',
        )

        self.assertEqual(ingredient.name, str(ingredient))

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_path_uuid(self, patched_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        patched_uuid.return_value = uuid

        file_path = models.recipe_image_file_path(None, 'example.jpg')
        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')

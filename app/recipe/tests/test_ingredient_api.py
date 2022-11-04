"""
Tests for Ingredient APIs.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='test@example.com', password='password'):
    return get_user_model().objects.create(email=email, password=password)


def create_ingredient(user, name):
    return Ingredient.objects.create(user=user, name=name)


class PublicIngredientAPITests(TestCase):
    """Test for public ingredient API."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITests(TestCase):
    """Test authenticated ingredient API requests."""

    def setUp(self) -> None:
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retreiving_ingredients(self):
        """Test get list of ingredients."""
        create_ingredient(self.user, name='Test ingredient 1')
        create_ingredient(self.user, name='Test ingredient 2')

        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test user access to ingredients of the user."""
        other_user = create_user(email='other@ez.gg')
        create_ingredient(other_user, name='Test other ingredient')
        ingredient = create_ingredient(self.user, name='Test ingredient')

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_updating_ingredient(self):
        """Test user updating the ingredient of a recipe."""
        ingredient = create_ingredient(self.user, name='Test ingredient')
        payload = {'name': 'Updated ingredient'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, res.data['name'])
        self.assertEqual(ingredient.name, payload['name'])

    def test_deleting_ingredient(self):
        """Test user deleting the ingredient of a recipe."""
        ingredient = create_ingredient(self.user, name='Test ingredient')
        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredient = Ingredient.objects.filter(id=ingredient.id)
        self.assertFalse(ingredient.exists())

    def test_creating_ingredient_raise_error(self):
        """Test creating a ingredient in database not allowed."""
        payload = {
            'name': 'Vermouth Rosso',
        }
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test filtering ingredient by assigned recipe."""
        ing1 = create_ingredient(user=self.user, name='Limes')
        ing2 = create_ingredient(user=self.user, name='Simple syrup')
        recipe = Recipe.objects.create(
            title='Whiskey sour',
            time_minutes=3,
            price=Decimal(12.00),
            user=self.user
        )
        recipe.ingredients.add(ing1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(ing1)
        s2 = IngredientSerializer(ing2)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ingredients_unique(self):
        """Test filtering result list unique."""
        ingredient = create_ingredient(user=self.user, name='Egg white')
        create_ingredient(user=self.user, name='Cream')
        recipe1 = Recipe.objects.create(
            title='New York sour',
            time_minutes=3,
            price=Decimal('12.00'),
            user=self.user
        )
        recipe2 = Recipe.objects.create(
            title='Gin fizz',
            time_minutes=3,
            price=Decimal('15.00'),
            user=self.user
        )
        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)

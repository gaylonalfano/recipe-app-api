# recipe/tests/test_ingredients_api.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

#  Also going to use a DefaultRouter for this API
INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the endpoint"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the private ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@londonappdev.com',
            password='testpass'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving a list of ingredients"""
        # Create some sample ingredients with auth user
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        # Make GET request
        res = self.client.get(INGREDIENTS_URL)

        # Verify by retrieving all ingredients, serialize them, compare result
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        # Verify HTTP status is OK
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Assert that data matches
        self.assertEqual(res.data, serializer.data)

    # MY VERSION READ Section 13 notes!
    def test_ingredients_limited_to_user(self):
        """Test that ingredients for authenticated user are returned"""
        # Create an unauthorized user2
        user2 = get_user_model().objects.create_user(
            email='other@londonappdev.com',
            password='test12345'
        )
        # Create an ingredient using user2
        Ingredient.objects.create(user=user2, name='Vinegar')
        # Create ingredient with authorized user
        Ingredient.objects.create(user=self.user, name='Tumeric')

        # Serialize the ingredients
        ingredients = Ingredient.objects.all().filter(user=self.user)
        serializer = IngredientSerializer(ingredients, many=True)

        # Make the request with authenticated user
        res = self.client.get(INGREDIENTS_URL)

        # Probably should add an HTTP check
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Not sure if need this. Assert that only 1 ingredient returned
        # UPDATE: removed this and test still passed!
        # self.assertEqual(len(res.data), 1)

        # Assert that data matches is specific to auth user
        self.assertEqual(res.data, serializer.data)


"""
    INSTRUCTORS VERSION
    def test_ingredients_limited_to_user(self):
        user2 = get_user_model().objects.create(
            email='other@londonappdev.com',
            password='test12345'
        )
        Ingredient.objects.create(user=user2, name='Vinegar')
        ingredient = Ingredient.objects.create(user=self.user, name='Tumeric')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
"""

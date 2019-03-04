# recipe/tests/test_recipe_api.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URLS = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create and return sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create and return sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    # Use .update() to override defaults if passed. Accepts dict object
    defaults.update(params)

    # Use **defaults to convert dict to arguments for Recipe object
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        # Make unauthenticated request
        res = self.client.get(RECIPES_URLS)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()
        # Create test user
        self.user = get_user_model().objects.create_user(
            email='test@londonappdev.com',
            password='testpass'
        )
        # Force authenticate our user to the client
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        # Create two sample recipes using our helper function
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        # Make the request
        res = self.client.get(RECIPES_URLS)
        # Retrieve recipes from database and order by 'id' sequentially
        recipes = Recipe.objects.all().order_by('-id')
        # Pass recipes to our serializer and set many=True to return list
        serializer = RecipeSerializer(recipes, many=True)
        # Assert good status code and data matches
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""
        # Create test user
        user2 = get_user_model().objects.create_user(
            email='other@londonappdev.com',
            password='password123'
        )
        # Create recipe with test user
        sample_recipe(user=user2)
        # Create recipe with authenticated user
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URLS)
        # Filter recipes to our authenticated user only
        recipes = Recipe.objects.filter(user=self.user)
        # Pass recipes queryset to our serializer and set many=True for list
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        # Add a tag to our recipe using helper function
        recipe.tags.add(sample_tag(user=self.user))
        # Add an ingredient to our recipe user helper function
        recipe.ingredients.add(sample_ingredient(user=self.user))
        # Generale the recipe detail URL we're going to call
        url = detail_url(recipe.id)
        # Make the request
        res = self.client.get(url)
        # Serialize the recipe with our new RecipeDetailSerializer
        serializer = RecipeDetailSerializer(recipe)
        # Make assertions
        self.assertEqual(res.data, serializer.data)

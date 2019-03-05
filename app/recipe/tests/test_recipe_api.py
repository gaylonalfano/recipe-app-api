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

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }
        res = self.client.post(RECIPES_URLS, payload)
        # Assert that object was created with HTTP_201_CREATED
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Retrieve the recipe we just created from our model
        recipe = Recipe.objects.get(id=res.data['id'])
        # Loop keys in payload and assert they match recipe use getattr()
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        # Create a couple of sample tags
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Dessert')
        # Create recipe and assign tags
        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 60,
            'price': 20.00
        }
        # Make POST request to create recipe via API
        res = self.client.post(RECIPES_URLS, payload)
        # Assert that the request was successful and created object
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Retrieve the recipe that was created
        recipe = Recipe.objects.get(id=res.data['id'])
        # Retrieve the tags assigned to our recipe
        tags = recipe.tags.all()
        # Verify that the number of tags in our recipe is two using .count()
        self.assertEqual(tags.count(), 2)
        # Check sample tags match those in tags queryset using assertIn()
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        # Create a couple of ingredients
        ingredient1 = sample_ingredient(user=self.user, name='Prawns')
        ingredient2 = sample_ingredient(user=self.user, name='Ginger')

        # Create recipe and assign ingredients
        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 20,
            'price': 7.00
        }
        # Make POST to create recipe via API
        res = self.client.post(RECIPES_URLS, payload)
        # Assert that the object was successfully created via API
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Retrieve the recipe we just created
        recipe = Recipe.objects.get(id=res.data['id'])
        # Retrieve the ingredients we assigned to recipe. Returns queryset
        ingredients = recipe.ingredients.all()
        # Confirm/check that our recipe has two ingredients
        self.assertEqual(ingredients.count(), 2)
        # Check that sample ingredients match those in ingredients queryset
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

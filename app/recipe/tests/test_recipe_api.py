# recipe/tests/test_recipe_api.py
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URLS = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        # Create a sample recipe
        recipe = sample_recipe(user=self.user)
        # Add a tag to the recipe
        recipe.tags.add(sample_tag(user=self.user))
        # Create a new tag that will replace the original tag
        new_tag = sample_tag(user=self.user, name='Curry')
        # Create our payload with the updated values we want to use
        payload = {'title': 'Chicken Tikka', 'tags': [new_tag.id]}
        # Update objects using DRF ViewSets by using detail_url
        url = detail_url(recipe.id)
        # Make patch request to update our recipe. Don't need 'res' var
        self.client.patch(url, payload)
        # Now we've updated the db value we need to refresh_from_db()
        recipe.refresh_from_db()
        # Assert that the title has been updated to 'Chicken Tikka'
        self.assertEqual(recipe.title, payload['title'])
        # Retrieve tags associated to recipe
        tags = recipe.tags.all()
        # Assert that the length of tags is 1. Can use len() or count()
        self.assertEqual(tags.count(), 1)
        # Assert that new_tag is in our tags that we retrieved
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        # Create a sample recipe
        recipe = sample_recipe(user=self.user)
        # Add a tag to the recipe. Will exclude later with PUT
        recipe.tags.add(sample_tag(user=self.user))
        # Create our payload
        payload = {
            'title': 'Spaghetti cabonara',
            'time_minutes': 25,
            'price': 5.00
        }
        # Create our detail url
        url = detail_url(recipe.id)
        # Make the PUT request. Don't need to use 'res' var
        self.client.put(url, payload)
        # refresh_from_db now that changes have been made in db
        recipe.refresh_from_db()
        # Assert that title, time_minutes and price match payload values
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        # Retrieve tags assigned to recipe
        tags = recipe.tags.all()
        # Assert that there are zero tags since our PUT didn't have tags
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):
    """Test uploading images to recipes"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='user@londonappdev.com',
            password='testpass'
        )
        # Authenticate our user
        self.client.force_authenticate(self.user)
        # Create sample recipe to test uploading images to
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        # Clean up all image files created when running our tests
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to recipe"""
        # Create the URL for our sample recipe we created
        url = image_upload_url(self.recipe.id)
        # Use context manager to create temp file
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            # Create a 10x10 black image using Image from PIL
            img = Image.new('RGB', (10, 10))
            # Save to our NamedTemporaryFile (ntf) in JPEG format
            img.save(ntf, format='JPEG')
            # Move cursor/pointer to beginning of file using seek
            ntf.seek(0)
            # Make POST request using multipart form request to post data
            res = self.client.post(url, {'image': ntf}, format='multipart')

        # Refresh the database for our recipe so we can do some assertions
        self.recipe.refresh_from_db()
        # Assert that we get a HTTP_200_OK status
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Check that image is in the response so path to image is accessible
        self.assertIn('image', res.data)
        # Check path exists for image on our file system using os.path.exists
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        # Create our image upload URL
        url = image_upload_url(self.recipe.id)
        # Make our POST but send a string object instead of an image file
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')
        # Check that we get a 400_BAD_REQUEST as a response
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        # Create some sample recipes w/ and w/o tags
        recipe1 = sample_recipe(user=self.user, title='Thai vegetable curry')
        recipe2 = sample_recipe(user=self.user, title='Aubergine with tahini')
        recipe3 = sample_recipe(user=self.user, title='Fish and chips')

        # Create sample tags
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Vegetarian')

        # Add tags to our first two recipes
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        # Make request for 'Vegan' and 'Vegetarian' recipes in db using tag id
        res = self.client.get(RECIPES_URLS, {'tags': f'{tag1.id},{tag2.id}'})

        # Serialize our recipes and check they exist in responses returned
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specific ingredients"""
        # Create some sample recipes w/ and w/o ingredients
        recipe1 = sample_recipe(user=self.user, title='Posh beans on toast')
        recipe2 = sample_recipe(user=self.user, title='Chicken cacciatore')
        recipe3 = sample_recipe(user=self.user, title='Steak and mushrooms')

        # Create sample ingredients
        ingredient1 = sample_ingredient(user=self.user, name='Feta cheese')
        ingredient2 = sample_ingredient(user=self.user, name='Chicken')

        # Add ingredients to our first two recipes
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        # Make our request pass ingredient id inside GET parameters. Notes!
        res = self.client.get(
            RECIPES_URLS,
            {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        )

        # Serializer our recipes
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        # Check that they exist in responses returned
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

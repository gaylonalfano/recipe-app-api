# recipe/tests/test_tags_api.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer


# Going to use ViewSet that will append action to end of URL
TAGS_URL = reverse('recipe:tag-list')


# Optional helper function for creating a sample user
def sample_user(email='test@londonappdev.com', password='password123'):
    """Create a sample user for help with testing authorized user tags API"""
    return get_user_model().objects.create_user(email, password)


class PublicTagsApiTests(TestCase):
    """Test the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        # I created sample_user() helper but it's optional
        self.user = sample_user()
        self.client = APIClient()
        # Setup our reusable client but force authenticate method
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags NOT limited to user"""
        # Create sample tags
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        # Make GET request with authorized user
        res = self.client.get(TAGS_URL)

        # Make a query on the model that we expect to compare results against
        # tags = Tag.objects.all().filter(user=self.user)
        # Return tags in reverse alphabetical order
        tags = Tag.objects.all().order_by('-name')
        # Serialize our tags object. Be sure to include many=True
        # I believe serializing converts fields to JSON
        serializer = TagSerializer(tags, many=True)

        # Assert the HTTP status is correct
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Assert values are what we expect. serializer.data is new! see notes
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user"""
        # Create another user to compare against
        user2 = get_user_model().objects.create_user(
            email='other@londonappdev.com',
            password='testpass'
        )
        # Create a Tag object using this new user2
        Tag.objects.create(user=user2, name='Fruity')

        # Create a Tag object assigned to authenticated user save to tag var
        tag = Tag.objects.create(user=self.user, name='Comfort Food')

        # Make our request
        res = self.client.get(TAGS_URL)

        # Assert that HTTP response is HTTP_200_OK
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Create QuerySet to compare against? Or just objects.all().filter()?
        # Nope! Instructor goes straight to assertions. See notes.
        self.assertEqual(len(res.data), 1)

        # Assert that name of tag matches tag.name
        self.assertEqual(res.data[0]['name'], tag.name)


"""
    This is what I attempted before instructor. READ NOTES!
    def test_tags_limited_to_user(self):
        #Test that tags returned are for the authenticated user#
        user2 = get_user_model().objects.create_user(
            email='other@londonappdev.com',
            password='testpass'
        )
        # Create a Tag object using this new user2
        Tag.objects.create(user=user2, name='Dairy')

        # Create a Tag object assigned to authenticated user
        Tag.objects.create(user=self.user, name='Nuts')

        # Make our request
        res = self.client.get(TAGS_URL)

        # Create tags var that returns only auth user using filter()
        tags = Tag.objects.all().filter(user=self.user)

        # Create serializer var. Why exactly? Need to research.
        serializer = TagSerializer(tags, many=True)

        # Check that values match between res.data and serializer.data
        self.assertEqual(res.data['name'], serializer.data['name'])
"""

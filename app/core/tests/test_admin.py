# app/core/tests/test_admin.py
# Test client that allows us to make test requests to our application
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
# Helper function to generate URLs for Django admin page
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self):
        """Ran before all other tests. Going to consist of creating \
        our test client. Also going to create a new user we can use for \
        testing and make sure they're logged into our cli ent. Last, we're \
        going to create a regular user that is not authenticated to be \
        listed in our admin page."""

        # Set a Client variable that is accessible to the other tests
        self.client = Client()

        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@gmail.com',
            password='password12345'
        )
        # Use Client() helper function to log in user w/ Django authentication
        # Makes our tests easier to write since we don't have to manually log
        # the user in.
        self.client.force_login(self.admin_user)
        # Spare user can use for testing listings, etc.
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='test12345',
            name='Test user full name'
        )

    def test_users_listed(self):
        """Test that users are listed on user page"""
        # reverse(app:URL you want)
        url = reverse("admin:core_user_changelist")
        # response ('res')
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_page(self):
        """Test that the user edit page works"""
        # Create a URL like: /admin/core/user/id(1)/
        url = reverse("admin:core_user_change", args=[self.user.id])
        # Test client is gonna perform HTTP GET on url
        res = self.client.get(url)
        # Test that page renders okay
        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """Test that the create user page works"""
        # Create a URL: /admin/core/user/add???
        url = reverse("admin:core_user_add")
        # Test client is gonna perform HTTP GET on url
        res = self.client.get(url)
        # Test that page renders okay
        self.assertEqual(res.status_code, 200)

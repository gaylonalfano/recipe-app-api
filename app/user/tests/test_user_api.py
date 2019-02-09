# user/tests/test_user_api.py
from django.test import TestCase
# Need the user model for our tests
from django.contrib.auth import get_user_model
# Help generate API URLs
from django.urls import reverse

# Import some REST framework helper tools.
# Test client we can use to make requests to our API
from rest_framework.test import APIClient
# Status codes in human-readable format
from rest_framework import status


# BEFORE creating tests, good practice to add helper functions
# and/or constant variables for the URL we're testing
# Create the user/create URL and assign to constant var
CREATE_USER_URL = reverse('user:create')
# URL we use to make HTTP POST request to generate token
TOKEN_URL = reverse('user:token')
# URL we're going to use for update user endpoint '/user/me/'
ME_URL = reverse('user:me')


# Helper function for creating a new user since we do it multiple times
def create_user(**params):
    return get_user_model().objects.create_user(**params)


# Create our Public API test
class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        # Make it easier to call our client in our tests that we can resuse
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        # Create payload object that is passed to API
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'Test name'
        }
        # Make post request to our create user api url
        res = self.client.post(CREATE_USER_URL, payload)

        # Expecting an HTTP_201_CREATED response from API
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Confirm that user was actually created by unwinding response
        user = get_user_model().objects.get(**res.data)
        # Confirm that our password is correct
        self.assertTrue(user.check_password(payload['password']))
        # Check that password field isn't returned in request object
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test creating a user that already exists fails"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
        }
        # Use our helper function to create_user with payload fields
        # Creating this user first before trying to POST again below
        create_user(**payload)

        # Make post request to our create user api url
        res = self.client.post(CREATE_USER_URL, payload)
        # Expect an HTTP_400_BAD_REQUEST because user already exists
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """test that the password must be more than 5 characters"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'pw'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        # Make sure that it returns HTTP_400_BAD_REQUEST
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # Check that user was NOT created using filter().exists()
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        # Confirm that user was NOT created (i.e., .exists() = False)
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        # Create a payload to use for testing our API
        payload = {'email': 'test@gmail.com', 'password': 'testpass'}
        # Create user that matches this authentication to test against user
        create_user(**payload)
        # Make our request and store it in response variables
        res = self.client.post(TOKEN_URL, payload)

        # Assert that token was created and 'token' key in response data
        self.assertIn('token', res.data)
        # Assert that we get HTTP_200_OK
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created if invalid credentials are given"""
        # Create user FIRST then we'll create payload. They'll be different
        create_user(email='test@gmail.com', password='invalidpass')
        payload = {'email': 'test@gmail.com', 'password': 'testpass'}
        res = self.client.post(TOKEN_URL, payload)

        # Assert that 'token' key is not in response data
        self.assertNotIn('token', res.data)
        # Assert that HTTP_400_BAD_REQUEST is returned
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is  not created if user doesn't exist"""
        # Here the INPUT is valid. Django validates input FIRST. See notes.
        payload = {'email': 'test@gmail.com', 'password': 'testpass'}
        # Don't need to create a user for this test. Make request immediately
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are required"""
        # Don't need to create a user. Just sending an incomplete login
        # We're testing the that INPUT is not valid. See notes.
        payload = {'email': 'test@gmail.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""
    # Set authentication for each subsequent test
    def setUp(self):
        self.user = create_user(
            email='test@gmail.com',
            password='testpass',
            name='name'
        )
        # Setup our reusable client but force authenticate method
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        # Already authenticated in setUp() so just make request
        res = self.client.get(ME_URL)

        # Assert that the response is good
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Assert that the user object returned is what we expected
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name
        })

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me url"""
        # Make POST request and pass empty object
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {'name': 'new name', 'password': 'newpassword123'}
        res = self.client.patch(ME_URL, payload)

        # Use the helper function refresh_from_db() to update the user
        self.user.refresh_from_db()

        # Verify that the values we provided were updated
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
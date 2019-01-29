# app/core/tests/test_models.py
from django.test import TestCase
# Import get_user_model() instead of User model directly
from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""
        email = "test@gmail.com"
        password = "test12345"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        # Now we have our user (above), we can create some assertions
        self.assertEqual(user.email, email)
        # Passwords are encrypted so we have to use check_password()
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email (domain) for a new user is normalized (lowercase)"""
        email = "test@GMAIL.com"
        # We don't need to test the password again
        user = get_user_model().objects.create_user(email, "test12345")
        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            # Anything in here should raise a ValueError
            # If not, then the test will fail
            get_user_model().objects.create_user(None, 'test12345')

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser(
            'test@gmail.com',
            'test12345'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

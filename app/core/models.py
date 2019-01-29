# app/core/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin


class UserManager(BaseUserManager):

    # extra_fields isn't required but makes our function a little more
    # flexible. Every time we add new fields to our user we do NOT have
    # to add them in here. We can add them ad-hoc to our model.
    def create_user(self, email, password=None, **extra_fields):
        """Creates and saves a new user"""
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        # using=self._db is good for supporting multiple databases
        user.save(using=self._db)

        return user

    # Adding create_superuser function. Don't need extra_fields
    # Also can reuse (DRY) create_user method
    def create_superuser(self, email, password):
        """Creates and saves a new superuser"""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that supports using email instead of username"""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Assign our UserManager to the objects attribute
    objects = UserManager()

    USERNAME_FIELD = 'email'  # default is 'username'

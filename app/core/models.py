"""
Database models
"""
from distutils.command.upload import upload
import uuid
import os

from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


def recipe_image_file_path(instance, file_name):
    """Generate path for an uploaded image."""
    extention = os.path.splitext(file_name)[1]
    file_name = f'{uuid.uuid4()}{extention}'

    # Return the path wrt. os.
    return os.path.join('uploads', 'recipe', file_name)


class UserManager(BaseUserManager):
    """Define manager for user"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('User email address is required.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Define the user model"""
    email = models.EmailField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Recipe(models.Model):
    """Define the recipe object."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=32)
    description = models.CharField(max_length=128, blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField('Tag')
    ingredients = models.ManyToManyField('Ingredient')
    image = models.ImageField(null=True, upload_to=recipe_image_file_path)

    def __str__(self) -> str:
        return str(self.title)


class Tag(models.Model):
    """Define the tags fror filetering recipes."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=16)

    def __str__(self) -> str:
        return str(self.name)


class Ingredient(models.Model):
    """Define ingredient for recipes."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=128)

    def __str__(self) -> str:
        return str(self.name)

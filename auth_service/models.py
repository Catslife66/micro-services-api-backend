from django.db import models
from django.contrib.auth.models import AbstractUser


class AppUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=20, unique=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
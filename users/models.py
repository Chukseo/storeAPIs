from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)

    # Use email as unique identifier; username still exists but can be optional in forms
    REQUIRED_FIELDS = ['username'] 
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

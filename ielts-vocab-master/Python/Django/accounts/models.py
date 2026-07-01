from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        USER  = 'user',  'User'
        STAFF = 'staff', 'Staff'
        ADMIN = 'admin', 'Admin'

    email    = models.EmailField(unique=True)
    username = models.CharField(max_length=20, unique=True)
    name     = models.CharField(max_length=60, blank=True)
    picture  = models.ImageField(upload_to='avatars/', blank=True)
    role     = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    learn_map = models.JSONField(default=dict)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

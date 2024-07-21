from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    birth_date = models.DateField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to='users', default='default/user.png')

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username
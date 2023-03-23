from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    user = models.OneToOneField(
        User, on_delete=models.CASCADE)
    is_pi = models.BooleanField(default=False, verbose_name='是否为项目负责人')

    class Meta:
        verbose_name = "账户"
        verbose_name_plural = "账户"

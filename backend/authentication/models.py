from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.email


class UserHubCredentials(models.Model):
    """
    Model to store user's Hub XP credentials
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hub_credentials')
    hub_login = models.CharField(max_length=255, verbose_name='Login Hub XP')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        db_table = 'user_hub_credentials'
        verbose_name = 'Credencial Hub XP'
        verbose_name_plural = 'Credenciais Hub XP'
        unique_together = ['user', 'hub_login']

    def __str__(self):
        return f"{self.user.email} - {self.hub_login}"

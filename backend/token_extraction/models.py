from django.db import models
from authentication.models import User


class HubToken(models.Model):
    """
    Model to store Hub XP tokens - extends existing hub_tokens table
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hub_tokens', null=True, blank=True)
    user_login = models.CharField(max_length=255, verbose_name='Login do Usuário')
    token = models.TextField(verbose_name='Token')
    expires_at = models.DateTimeField(verbose_name='Expira em')
    extracted_at = models.DateTimeField(verbose_name='Extraído em')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        db_table = 'hub_tokens'
        verbose_name = 'Token Hub XP'
        verbose_name_plural = 'Tokens Hub XP'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_login']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"Token {self.user_login} - {self.expires_at.strftime('%d/%m/%Y %H:%M')}"

    @property
    def is_expired(self):
        """Check if token is expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    @property
    def time_until_expiry(self):
        """Get time until token expires"""
        from django.utils import timezone
        if self.is_expired:
            return None
        return self.expires_at - timezone.now()


class TokenExtractionLog(models.Model):
    """
    Model to log token extraction attempts
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('in_progress', 'Em Progresso'),
        ('success', 'Sucesso'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='extraction_logs')
    hub_login = models.CharField(max_length=255, verbose_name='Login Hub XP')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Iniciado em')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completado em')
    error_message = models.TextField(null=True, blank=True, verbose_name='Mensagem de Erro')
    token = models.ForeignKey(HubToken, on_delete=models.SET_NULL, null=True, blank=True, related_name='extraction_logs')

    class Meta:
        db_table = 'token_extraction_logs'
        verbose_name = 'Log de Extração'
        verbose_name_plural = 'Logs de Extração'
        ordering = ['-started_at']

    def __str__(self):
        return f"Extração {self.hub_login} - {self.get_status_display()}"

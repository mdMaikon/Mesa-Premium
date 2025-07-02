# 🛡️ Security Guide

## 🔒 Recursos de Segurança Implementados

### ✅ Práticas de Segurança Ativas

- **Rate Limiting**: Proteção anti-DDoS por endpoint
- **CORS Específico**: Apenas domínios autorizados
- **Log Sanitization**: Dados sensíveis mascarados automaticamente
- **Command Injection Prevention**: Subprocess securizado
- **Dependency Security**: Auditoria automática de CVEs
- **API Key Management**: Variáveis de ambiente protegidas
- **Pre-commit Hooks**: Validação automática de código (Ruff + Bandit)
- **Exception Chaining**: Preservação de stack traces para debugging
- **Code Quality**: Linting automatizado com padrões de segurança

### 🔒 Rate Limits por Endpoint

```python
# Rate limits configurados
- Token extraction: 3 requests/minuto
- Fixed income: 5 requests/hora
- Health checks: 120 requests/minuto
- Structured data: 10 requests/hora
```

### 📋 Headers de Segurança

```http
X-RateLimit-Limit: 3
X-RateLimit-Window: 60
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

## 🔧 Configuração Segura

### Variáveis de Ambiente Obrigatórias

```bash
# Database (NUNCA commitar)
DATABASE_HOST=seu-host-mysql
DATABASE_PASSWORD=sua-senha-forte
DATABASE_USER=usuario-limitado

# API Keys (NUNCA commitar)
HUB_XP_API_KEY=sua-chave-hub-xp
HUB_XP_STRUCTURED_API_KEY=sua-chave-estruturadas

# Security Settings
RATE_LIMIT_ENABLED=true
SELENIUM_HEADLESS=true
CORS_ORIGINS=https://seu-dominio.com
```

### Docker Security

```dockerfile
# Usuário não-root
USER appuser

# Permissões mínimas
RUN chmod -R 755 /home/appuser/.cache
RUN chmod -R 777 /tmp  # Apenas para Selenium

# Variáveis seguras
ENV HOME=/home/appuser
ENV SELENIUM_CACHE_PATH=/home/appuser/.cache/selenium
```

## 🛡️ Práticas de Desenvolvimento Seguro

### Pre-commit Hooks Automáticos

```bash
# Instalar hooks de segurança
poetry run task pre-commit-install

# Executar auditoria
poetry run task security

# Verificações incluídas:
- Ruff: Linting + formatação
- Bandit: Detecção de vulnerabilidades
- Commitizen: Mensagens padronizadas
```

### Sanitização de Logs

```python
# Implementado em utils/log_sanitizer.py
def mask_sensitive_data(message: str) -> str:
    """Mascara dados sensíveis em logs"""
    # Remove senhas, tokens, etc.
    patterns = [
        (r'password["\s]*[:=]["\s]*[^"\\s]+', 'password=***'),
        (r'token["\s]*[:=]["\s]*[^"\\s]+', 'token=***'),
        (r'Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*', 'Bearer ***'),
    ]
    for pattern, replacement in patterns:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
    return message
```

### Subprocess Seguro

```python
# Implementado em utils/secure_subprocess.py
def run_secure_command(command: list) -> str:
    """Executa comandos de forma segura"""
    # Validação de entrada
    if not isinstance(command, list):
        raise ValueError("Command must be a list")

    # Prevenção de injection
    safe_chars = re.compile(r'^[a-zA-Z0-9\-\._/]+$')
    for arg in command:
        if not safe_chars.match(str(arg)):
            raise ValueError(f"Unsafe argument: {arg}")

    return subprocess.run(command, capture_output=True, text=True)
```

## 🔍 Auditoria de Segurança

### Comandos de Verificação

```bash
# Auditoria completa
poetry run python fastapi/scripts/security_audit.py

# Verificar dependências vulneráveis
poetry audit

# Scan de vulnerabilidades
poetry run bandit -r fastapi/ -f json

# Verificação de secrets
poetry run detect-secrets scan --all-files
```

### Monitoramento Contínuo

```bash
# Logs de segurança
docker-compose logs -f api | grep -E "(WARN|ERROR|SECURITY)"

# Rate limit status
curl -I http://localhost/api/health

# Health check de segurança
curl http://localhost/api/health | jq '.security'
```

## 🚨 Incidentes de Segurança

### Processo de Resposta

1. **Identificação**: Monitoramento automático via logs
2. **Contenção**: Rate limiting automático
3. **Análise**: Logs estruturados para forensics
4. **Correção**: Deploy automatizado de patches
5. **Prevenção**: Atualização de regras de segurança

### Contatos de Emergência

- **Logs críticos**: `docker-compose logs -f api | grep CRITICAL`
- **Rate limit exceeded**: Verificar X-RateLimit headers
- **Database issues**: Verificar credenciais em .env
- **Selenium failures**: Consultar TROUBLESHOOTING.md

## 📊 Métricas de Segurança

### KPIs Monitorados

- **Zero** vulnerabilidades críticas conhecidas
- **100%** requests passam por rate limiting
- **100%** logs passam por sanitização
- **<1%** false positives em detecção de threats
- **99.9%** uptime com proteção ativa

### Relatórios Automáticos

```bash
# Relatório semanal de segurança
poetry run python fastapi/scripts/security_report.py

# Dashboard de métricas
curl http://localhost/api/health | jq '.security_metrics'
```

## ⚡ Quick Security Checklist

### Deploy Checklist

- [ ] Variáveis .env configuradas (sem valores default)
- [ ] Rate limiting habilitado
- [ ] CORS configurado para produção
- [ ] Logs sanitizados
- [ ] Pre-commit hooks ativos
- [ ] Dependências atualizadas
- [ ] Selenium em modo headless
- [ ] User não-root no Docker
- [ ] SSL/TLS configurado
- [ ] Backup database configurado

### Desenvolvimento Checklist

- [ ] Pre-commit hooks instalados
- [ ] Nunca commitar credenciais
- [ ] Usar variáveis de ambiente
- [ ] Validar inputs com Pydantic
- [ ] Exception chaining implementado
- [ ] Logs estruturados
- [ ] Testes de segurança passando
- [ ] Code review focado em segurança

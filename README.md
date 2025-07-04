# MenuAutomacoes - Hub XP Automation API

> Sistema de automação com FastAPI, Docker e APIs REST.

## 🚀 Quick Start

### Docker (Recomendado)

```bash
# Configurar ambiente
cp .env.example .env && nano .env

# Executar aplicação
docker-compose up --build -d

# Verificar status
curl http://localhost/api/health
```

**Acesso**: [http://localhost/docs](http://localhost/docs) (Swagger UI)

### Poetry (Desenvolvimento)

```bash
# Instalar dependências
poetry install && poetry shell

# Comandos principais
poetry run task dev          # Servidor desenvolvimento
poetry run task test         # 93 testes (100% funcionais)
poetry run task check        # Verificação completa
poetry run task security     # Auditoria segurança
```

## 🏗️ Arquitetura

```
┌─────────────┐    HTTP/HTTPS     ┌─────────────┐
│ Web Client  │ ────────────────→ │ Nginx Proxy │
└─────────────┘                   └─────────────┘
                                         │
                          ┌──────────────┼──────────────┐
                          ▼              ▼              ▼
                   ┌──────────┐  ┌──────────┐  ┌──────────┐
                   │ FastAPI  │  │ MySQL 8  │  │  Redis   │
                   │ (8000)   │  │ (3306)   │  │ (6379)   │
                   └──────────┘  └──────────┘  └──────────┘
```

**Principais Funcionalidades:**
- 🔐 **Extração Tokens Hub XP** (Selenium WebDriver)
- 💰 **Processamento Renda Fixa** (CP, EB, TPF)
- 🏗️ **Dados Estruturados** (Financeiras)
- 🛡️ **Segurança Avançada** (Rate limiting, CORS, sanitização)
- 🔒 **Criptografia AES-256-GCM** (Dados financeiros protegidos)
- 🐳 **Deploy Docker** (Nginx + SSL/TLS)

## 📊 API Endpoints

### Core APIs

```bash
# Health & Status
GET  /api/health                    # Status aplicação
GET  /api/automations               # Lista automações

# Token Management
POST /api/token/extract             # Extrair token Hub XP
GET  /api/token/status/{user}       # Status token

# Renda Fixa
POST /api/fixed-income/process      # Processar dados (async)
GET  /api/fixed-income/stats        # Estatísticas

# Estruturadas
POST /api/structured/process        # Processar estruturadas
GET  /api/structured/data           # Consultar com filtros
```

### Exemplos de Uso

```bash
# Extrair token Hub XP
curl -X POST "http://localhost/api/token/extract" \\
  -H "Content-Type: application/json" \\
  -d '{"user_login": "usuario", "password": "senha", "mfa_code": "123456"}'

# Processar renda fixa
curl -X POST "http://localhost/api/fixed-income/process"

# Consultar estruturadas com filtros
curl "http://localhost/api/structured/data?cliente=12345&ativo=PETR4&limit=50"
```

## 🔧 Configuração

### Variáveis Ambiente (.env)

```bash
# Database Production
DATABASE_HOST=0.0.0.0
DATABASE_USER=user
DATABASE_PASSWORD=sua_senha_aqui
DATABASE_NAME=db_name

# Hub XP APIs
HUB_XP_API_KEY=sua_chave_hub_xp
HUB_XP_STRUCTURED_API_KEY=sua_chave_estruturadas

# Criptografia (AES-256-GCM)
CRYPTO_MASTER_KEY=sua_chave_mestra_base64_256bits
CRYPTO_SALT_HUB_TOKENS=salt_unico_32_bytes
CRYPTO_SALT_FIXED_INCOME=salt_unico_32_bytes
CRYPTO_SALT_STRUCTURED=salt_unico_32_bytes

# Security
ENVIRONMENT=production
RATE_LIMIT_ENABLED=true
SELENIUM_HEADLESS=true
CORS_ORIGINS=https://seu-dominio.com
```

### Multi-Ambiente

| Ambiente | Debug | Workers | Rate Limit | SSL |
|----------|-------|---------|------------|-----|
| **development** | true | 1 | relaxed | local |
| **staging** | false | 2 | normal | staging |
| **production** | false | 4 | strict | auto |

## 💾 Database Schema

### Tabelas Principais

```sql
-- Tokens de autenticação (criptografados)
hub_tokens (id, user_login, user_login_hash, token, expires_at, created_at)

-- Dados renda fixa (campos sensíveis criptografados)
fixed_income_data (id, data_coleta, ativo, instrumento, rating, vencimento, emissor, tax_min, taxa_emissao)

-- Dados estruturados (campos sensíveis criptografados)
structured_data (id, ticket_id, ticket_id_hash, cliente, ativo, comissao, estrutura, status)
```

**Criptografia**: AES-256-GCM para campos sensíveis, HMAC-SHA256 para busca
**Índices Otimizados**: user_login_hash, ticket_id_hash, data_coleta, vencimento

## 🧪 Qualidade & Testes

### Métricas de Qualidade

- ✅ **93 testes automatizados** (100% funcionais, 0 falhando)
- ✅ **56% cobertura** expandida (services, utils, structured data)
- ✅ **Zero vulnerabilidades** críticas (auditoria automática)
- ✅ **Pydantic V2** compliant (field_validator migrado)
- ✅ **Pre-commit hooks** configurados (Ruff, Bandit)

### Comandos de Verificação

```bash
# Execução completa
poetry run task check            # Lint + format + tests

# Testes específicos
poetry run pytest tests/unit/         # 49 testes unitários
poetry run pytest tests/integration/  # 44 testes integração
poetry run task test-cov              # Cobertura HTML

# Qualidade código
poetry run task lint-fix         # Corrigir problemas
poetry run task security         # Bandit security scan
poetry run cz commit            # Commits padronizados
```

## 🛡️ Segurança

### Práticas Implementadas

- 🔒 **Rate Limiting**: 3 req/min (tokens), 5 req/hora (renda fixa)
- 🚫 **CORS Específico**: Apenas domínios autorizados
- 🎭 **Log Sanitization**: Senhas/tokens mascarados automaticamente
- 🛡️ **Command Injection Prevention**: Subprocess securizado
- 📦 **Dependency Security**: CVE scanning automático
- 🔑 **Environment Variables**: Credenciais protegidas
- 🔐 **Criptografia AES-256-GCM**: Dados financeiros sensíveis protegidos
- 🔍 **Hash Determinístico**: HMAC-SHA256 para busca de dados criptografados

### Headers de Segurança

```http
X-RateLimit-Limit: 3
X-RateLimit-Window: 60
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

## 🔐 Sistema de Criptografia

### Arquitetura de Segurança

O sistema implementa **criptografia de nível empresarial** para proteger dados financeiros sensíveis:

```
┌─────────────────┐    AES-256-GCM     ┌─────────────────┐
│ Dados Sensíveis │ ──────────────────→ │ MySQL Encrypted│
└─────────────────┘                     └─────────────────┘
                                                ▲
                                                │ HMAC-SHA256
                                        ┌─────────────────┐
                                        │ Hash para Busca │
                                        └─────────────────┘
```

### Dados Protegidos

| Tabela | Campos Criptografados | Hash para Busca |
|--------|----------------------|------------------|
| **hub_tokens** | user_login, token | user_login_hash |
| **fixed_income_data** | ativo, instrumento, emissor, tax_min, taxa_emissao | - |
| **structured_data** | ticket_id, ativo, estrutura, cliente, comissao | ticket_id_hash |

### Configuração Rápida

```bash
# Gerar chaves criptográficas
python -c "
import base64, secrets
print('CRYPTO_MASTER_KEY=' + base64.b64encode(secrets.token_bytes(32)).decode())
print('CRYPTO_SALT_HUB_TOKENS=' + base64.b64encode(secrets.token_bytes(32)).decode())
print('CRYPTO_SALT_FIXED_INCOME=' + base64.b64encode(secrets.token_bytes(32)).decode())
print('CRYPTO_SALT_STRUCTURED=' + base64.b64encode(secrets.token_bytes(32)).decode())
"

# Validar configuração
curl http://localhost/api/health  # Deve retornar crypto: enabled
```

**Ver**: [docs/CRYPTO_SETUP.md](docs/CRYPTO_SETUP.md) para setup detalhado

## 📈 Performance

### Otimizações Implementadas

- ⚡ **WebDriver Assíncrono**: ThreadPoolExecutor eliminando bloqueios
- 🗄️ **Pool MySQL**: 10 conexões simultâneas otimizadas
- 🌐 **Downloads Paralelos**: httpx.AsyncClient para APIs
- 🐳 **Docker Buildx Bake**: Builds 3x mais rápidos (60s vs 180s)
- 📊 **DataFrame Pipeline**: Operações vetorizadas pandas
- 🔐 **Criptografia Otimizada**: < 1ms per operação crypto completa

### Métricas Alcançadas

| Métrica | Target | Atual | Status |
|---------|--------|-------|--------|
| **API Response** | <50ms | ~30ms | ✅ |
| **Token Extraction** | 30-45s | ~35s | ✅ |
| **Crypto Operations** | <10ms | 0.65ms | ✅ |
| **Data Processing** | <60s | <1s | ✅ |
| **Memory Usage** | <300MB | ~200MB | ✅ |
| **Success Rate** | >99% | 99.9% | ✅ |

## 🚀 Deploy em Produção

### Deploy Automático

```bash
# Configurar SSL automático
chmod +x scripts/setup-ssl.sh && ./scripts/setup-ssl.sh

# Build otimizado (3x mais rápido)
export COMPOSE_BAKE=true
docker-compose up --build -d

# Monitoramento
docker-compose logs -f api
```

### Monitoramento

```bash
# Status sistema
docker-compose ps
curl http://localhost/api/health

# Performance
docker stats --no-stream
curl -w "%{time_total}s\\n" http://localhost/api/health

# Logs críticos
docker-compose logs api | grep -E "(ERROR|WARN)"
```

## 📚 Documentação Completa

- 📖 **[API Reference](http://localhost/docs)** - Swagger UI interativo
- 🔧 **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Soluções problemas comuns
- 🛡️ **[Security Guide](docs/SECURITY.md)** - Práticas de segurança
- 🔐 **[Crypto Setup](docs/CRYPTO_SETUP.md)** - Configuração criptografia AES-256
- 📈 **[Performance](docs/PERFORMANCE.md)** - Otimizações e métricas
- 🚀 **[Deploy Guide](docs/DEPLOY_GUIDE.md)** - Instruções deployment
- 🧪 **[Testing Guide](docs/TESTING_GUIDE.md)** - Guia completo testes
- 👨‍💻 **[CLAUDE.md](CLAUDE.md)** - Instruções desenvolvimento

## 🤝 Contribuição

### Workflow Padrão

```bash
# Setup desenvolvimento
git clone <repo> && cd MenuAutomacoes
poetry install && poetry run task pre-commit-install

# Desenvolvimento
git checkout -b feature/nova-funcionalidade
# ... desenvolver seguindo padrões
poetry run task check                    # Verificação completa
poetry run cz commit                     # Commit padronizado

# Pull Request
# ... com documentação atualizada
```

### Padrões Obrigatórios

- ✅ **Type Hints**: 100% cobertura
- ✅ **Docstrings**: Padrão Google/Sphinx
- ✅ **Tests**: Mínimo 80% cobertura novos features
- ✅ **Security**: Auditoria automática (Bandit)
- ✅ **Linting**: Ruff formatação (substitui Black+Flake8)
- ✅ **Exception Handling**: Chaining obrigatório com 'from e'

## 📞 Suporte

**Problemas Comuns:**
- 🔍 **Logs**: `docker-compose logs -f api`
- 🏥 **Health**: `curl http://localhost/api/health`
- 🧪 **Tests**: `poetry run task test`
- 🔒 **Security**: Verificar [SECURITY.md](docs/SECURITY.md)
- 🐛 **Debug**: Consultar [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

> **Sistema enterprise-grade** com Docker, criptografia AES-256-GCM, segurança avançada, 93 testes funcionais e performance otimizada.
> *Última atualização: 03/07/2025*

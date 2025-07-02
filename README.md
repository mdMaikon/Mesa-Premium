# MenuAutomacoes - Hub XP Automation API

> Sistema enterprise-grade para automação Hub XP com FastAPI, Docker e APIs REST robustas.

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
│ Web Client  │ ─────────────────→ │ Nginx Proxy │
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
DATABASE_HOST=srv719.hstgr.io
DATABASE_USER=u272626296_mesapremium
DATABASE_PASSWORD=sua_senha_aqui
DATABASE_NAME=u272626296_automacoes

# Hub XP APIs
HUB_XP_API_KEY=sua_chave_hub_xp
HUB_XP_STRUCTURED_API_KEY=sua_chave_estruturadas

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
-- Tokens de autenticação
hub_tokens (id, user_login, token, expires_at, created_at)

-- Dados renda fixa
fixed_income_data (id, data_coleta, ativo, instrumento, rating, vencimento, emissor)

-- Dados estruturados
structured_data (id, ticket_id, cliente, ativo, comissao, estrutura, status)
```

**Índices Otimizados**: user_login, data_coleta, vencimento, cliente, ativo

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

### Headers de Segurança

```http
X-RateLimit-Limit: 3
X-RateLimit-Window: 60
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

## 📈 Performance

### Otimizações Implementadas

- ⚡ **WebDriver Assíncrono**: ThreadPoolExecutor eliminando bloqueios
- 🗄️ **Pool MySQL**: 10 conexões simultâneas otimizadas
- 🌐 **Downloads Paralelos**: httpx.AsyncClient para APIs
- 🐳 **Docker Buildx Bake**: Builds 3x mais rápidos (60s vs 180s)
- 📊 **DataFrame Pipeline**: Operações vetorizadas pandas

### Métricas Alcançadas

| Métrica | Target | Atual | Status |
|---------|--------|-------|--------|
| **API Response** | <50ms | ~30ms | ✅ |
| **Token Extraction** | 30-45s | ~35s | ✅ |
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

> **Sistema enterprise-grade** com Docker, segurança avançada, 93 testes funcionais e performance otimizada.
> *Última atualização: 01/07/2025*

# 🧪 Guia de Teste Local - MenuAutomacoes API

## 📋 Atualizado para Poetry + Docker Compose V2

### 🎯 **Workflow Poetry + Docker**
Poetry gerencia dependências no host → export para requirements.txt → Docker usa pip

## 🚀 Como Executar o Teste Local

### **Opção 1: Com Poetry (Desenvolvimento - Recomendado)**
```bash
# 1. Preparar ambiente Poetry
poetry install --only=main
poetry run task check  # Verificação completa

# 2. Gerar requirements.txt para Docker
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes

# 3. Habilitar Docker Buildx Bake (RECOMENDADO)
export COMPOSE_BAKE=true

# 4. Build e deploy Docker com performance otimizada
docker compose build
docker compose up -d

# 5. Verificar status
docker compose ps
curl http://localhost/api/health
```

### **Opção 2: Script Automatizado**
```bash
# Executar script completo de teste (se existir)
chmod +x scripts/test-local-deploy.sh
./scripts/test-local-deploy.sh
```

### **Opção 3: Desenvolvimento Puro Poetry (Sem Docker)**
```bash
# Para desenvolvimento rápido
poetry install
poetry run task run_dev  # Servidor local na porta 8000
```

## 🔧 **Pré-requisitos**

### **Sistema**
- Python 3.12+
- Poetry instalado
- Docker + Docker Compose V2
- Configuração `.env` adequada

### **Verificações**
```bash
# Verificar ferramentas
poetry --version          # Deve retornar v2.1.3+
docker compose version    # Deve retornar v2.36.2+
python --version          # Deve retornar 3.12+

# Verificar projeto
poetry check              # Valida pyproject.toml
poetry env info           # Info do ambiente virtual
```

## 🔍 **Endpoints de Teste**

| Endpoint | URL | Descrição |
|----------|-----|-----------|
| **Health** | http://localhost/api/health | Status da aplicação |
| **Docs** | http://localhost/docs | Documentação Swagger |
| **ReDoc** | http://localhost/redoc | Documentação ReDoc |
| **API** | http://localhost/api/automations | Lista automações |
| **Tokens** | http://localhost/api/token/status/usuario | Status tokens |
| **Fixed Income** | http://localhost/api/fixed-income/stats | Estatísticas RF |

## 🛠️ **Comandos Úteis**

### **Poetry + Docker Workflow**
```bash
# Habilitar Buildx Bake para performance
export COMPOSE_BAKE=true

# Atualizar dependências
poetry update
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes

# Rebuild com novas dependências (performance otimizada)
docker compose build api --no-cache
docker compose up -d api

# Verificar logs
docker compose logs -f api
```

### **Monitoramento**
```bash
# Logs em tempo real (Docker Compose V2)
docker compose logs -f

# Logs específicos
docker compose logs api
docker compose logs nginx
docker compose logs mysql

# Status dos containers
docker compose ps

# Uso de recursos
docker stats
```

### **Troubleshooting**
```bash
# Reiniciar serviço específico
docker compose restart api

# Parar tudo
docker compose down

# Reset completo (limpa volumes)
docker compose down -v
docker system prune -f

# Rebuild forçado
docker compose build --no-cache
docker compose up -d
```

## 📊 **Validações Esperadas**

### ✅ **Sucesso**
- Todos os containers rodando (`docker compose ps`)
- Health check retorna `{"status": "healthy", "database": "connected"}`
- Docs acessível em http://localhost/docs
- API responde em http://localhost/api/automations
- 48 testes passando (`poetry run task test`)

### ❌ **Problemas Comuns**

#### **1. Requirements.txt não existe**
```bash
# Gerar requirements.txt
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes

# Verificar se foi criado
ls -la fastapi/requirements.txt
```

#### **2. Container API não inicia**
```bash
# Verificar logs
docker compose logs api

# Problema comum: dependências desatualizadas
# Solução: Regenerar requirements.txt e rebuild
poetry update
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes
docker compose build api --no-cache
```

#### **3. Nginx 502 Bad Gateway**
```bash
# Verificar se API está rodando
docker compose ps
curl http://localhost:8000/api/health

# Verificar conectividade entre containers
docker compose exec nginx curl http://api:8000/api/health
```

#### **4. MySQL não conecta**
```bash
# Verificar se MySQL inicializou
docker compose logs mysql

# Para produção (Hostinger), verificar .env
grep DATABASE_ .env

# Para desenvolvimento local, aguardar inicialização
docker compose restart mysql
sleep 20
docker compose restart api
```

#### **5. Poetry não encontrado**
```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# Verificar instalação
poetry --version
```

## 🎯 **Cenários de Teste**

### **1. Teste Completo de Produção (Docker)**
```bash
# Usar configuração de produção
cp .env.production .env

# Ajustar para teste local
sed -i 's/srv719.hstgr.io/mysql/g' .env  # Se usar MySQL local

# Build e deploy
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes
docker compose build
docker compose up -d

# Validar
curl http://localhost/api/health
curl http://localhost/api/automations
```

### **2. Teste de Desenvolvimento (Poetry)**
```bash
# Ambiente desenvolvimento
poetry install
poetry run task test
poetry run task run_dev  # Porta 8000

# Em outro terminal
curl http://localhost:8000/api/health
```

### **3. Teste de Token Extraction**
```bash
# POST para extrair token (requer credenciais válidas)
curl -X POST "http://localhost/api/token/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "user_login": "seu.usuario",
    "password": "sua.senha",
    "mfa_code": "123456"
  }'
```

### **4. Teste de Rate Limiting**
```bash
# Testar limites (definidos por endpoint)
for i in {1..5}; do curl http://localhost/api/health; done
```

## 🔐 **Configurações de Ambiente**

### **Para Teste Local (.env)**
```bash
# Database (escolher uma opção)
# OPÇÃO A: MySQL Local (Docker)
DATABASE_HOST=mysql
DATABASE_PORT=3306
DATABASE_USER=mesa_user
DATABASE_PASSWORD=secure_password
DATABASE_NAME=mesa_premium_db

# OPÇÃO B: MySQL Hostinger (Produção)
DATABASE_HOST=your-mysql-server.com
DATABASE_PORT=3306
DATABASE_USER=your_database_user
DATABASE_PASSWORD=YOUR_SECURE_PASSWORD_HERE
DATABASE_NAME=your_database_name

# Application
ENVIRONMENT=development
DEBUG=True
CORS_ORIGINS=http://localhost,http://localhost:8000,http://localhost:80
```

### **Configuração MySQL Local (se usar)**
```bash
# Descomentar variáveis MySQL no .env
MYSQL_ROOT_PASSWORD=secure_root_password_2024
MYSQL_DATABASE=db_name
MYSQL_USER=db_user
MYSQL_PASSWORD=secure_password
```

## ✅ **Checklist de Teste Local Atualizado**

### **Preparação Poetry**
- [ ] Poetry v2.1.3+ instalado
- [ ] `poetry install --only=main` executado
- [ ] `poetry run task check` passou
- [ ] `poetry export` gerou requirements.txt

### **Deploy Docker**
- [ ] Docker Compose V2 funcionando
- [ ] `docker compose build` executado sem erro
- [ ] Containers iniciados (`docker compose up -d`)
- [ ] Status OK (`docker compose ps`)

### **Validação Endpoints**
- [ ] Health check: http://localhost/api/health
- [ ] Documentação: http://localhost/docs
- [ ] API automações: http://localhost/api/automations
- [ ] Status 200 em todos os endpoints

### **Testes Funcionais**
- [ ] 48 testes passando (`poetry run task test`)
- [ ] Logs sendo gerados sem erro
- [ ] Rate limiting funcionando
- [ ] Database conectado (MySQL local ou Hostinger)

## 📈 **Métricas de Performance**

### **Build Time**
- **Poetry export**: ~2 segundos
- **Docker build**: ~3 minutos (primeira vez), ~10 segundos (com cache)
- **Startup time**: ~15 segundos para todos os serviços

### **Resource Usage**
- **API Container**: ~150MB RAM
- **MySQL Container**: ~200MB RAM (se local)
- **Nginx Container**: ~10MB RAM
- **Total**: ~360MB RAM

## 🎯 **Próximos Passos Após Teste Local**

### **Se Teste Local OK ✅**
1. **Deploy VPS**: Seguir `DEPLOY_GUIDE.md`
2. **Configurar SSL**: `./scripts/setup-ssl.sh yourdomain.com`
3. **Ajustar domínio**: Editar configurações para produção

### **Para Produção**
```bash
# Usar configuração de produção
cp .env.production .env

# Configurar domínio real
sed -i 's/localhost/yourdomain.com/g' nginx/sites-available/mesa_premium.conf

# Deploy no VPS
git push origin main
# Seguir DEPLOY_GUIDE.md no servidor
```

## 🚀 **Comandos Rápidos**

### **Teste Rápido Completo**
```bash
# Comando único para testar tudo (com Buildx Bake)
export COMPOSE_BAKE=true && \
poetry install --only=main && \
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes && \
docker compose build && \
docker compose up -d && \
sleep 15 && \
curl http://localhost/api/health
```

### **Desenvolvimento Iterativo**
```bash
# Para mudanças no código (com Buildx Bake)
export COMPOSE_BAKE=true
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes
docker compose build api
docker compose up -d api
docker compose logs -f api
```

### **Reset Completo**
```bash
# Limpar tudo e recomeçar (com Buildx Bake)
docker compose down -v
docker system prune -f
export COMPOSE_BAKE=true
poetry install --only=main
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes
docker compose build --no-cache
docker compose up -d
```

---

## 📋 **FAQ - Poetry + Docker**

### **P: Poetry fica dentro do Docker?**
**R:** NÃO. Poetry gerencia dependências no host, gera requirements.txt, e o Docker usa pip.

### **P: Como atualizar dependências?**
**R:** `poetry update` → `poetry export` → `docker compose build`

### **P: Posso rodar sem Docker?**
**R:** SIM. `poetry run task run_dev` para desenvolvimento local na porta 8000.

### **P: Qual é mais rápido para desenvolvimento?**
**R:** Poetry direto (`poetry run task run_dev`) é mais rápido para mudanças frequentes.

### **P: Quando usar Docker?**
**R:** Para testes de produção, nginx proxy, ou ambiente idêntico ao deploy.

### **P: O que é Docker Buildx Bake?**
**R:** Sistema de build mais moderno e rápido. Use `export COMPOSE_BAKE=true` antes de builds.

---

## 🎉 **CONCLUSÃO**

**✅ GUIA ATUALIZADO PARA POETRY + DOCKER COMPOSE V2**

O LOCAL_TEST_GUIDE.md agora está alinhado com:
- Workflow Poetry + Docker
- Docker Compose V2 (sem hífen)
- Requirements.txt gerado automaticamente
- Troubleshooting específico para Poetry
- Comandos atualizados

**🚀 Pronto para testar!**

*Guia atualizado em 26/06/2025 - MenuAutomacoes API v2.0 com Poetry*

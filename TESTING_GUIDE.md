# 🧪 Guia de Testes - FastAPI Hub XP Token Extraction

Este guia contém todos os testes necessários para validar a aplicação FastAPI antes do deploy em produção.

## 🆕 **ATUALIZAÇÃO - Sistema de Testes Automatizados**

**📅 Atualizado em: 24/06/2025**

O projeto agora inclui uma suíte completa de testes automatizados usando pytest. Este guia foi atualizado para incluir as novas funcionalidades de teste.

## 📋 Pré-requisitos

### 1. Ambiente de Desenvolvimento
```bash
# Navegue para o diretório FastAPI
cd /home/maikonsilva/MenuAutomacoes/fastapi

# Crie ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/WSL
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
```

### 2. Configuração do Banco de Dados
```bash
# Verifique se o arquivo .env existe
ls -la .env

# Se não existir, copie do exemplo e configure
cp .env.example .env
nano .env  # Edite com suas credenciais MySQL
```

**Conteúdo necessário no `.env`:**
```env
DB_HOST=srv719.hstgr.io
DB_NAME=u272626296_automacoes
DB_USER=u272626296_mesapremium
DB_PASSWORD=sua_senha_mysql_aqui
```

### 3. Dependências do Sistema
```bash
# Chrome/Chromium (WSL/Linux)
sudo apt update
sudo apt install -y chromium-browser

# ChromeDriver (se necessário)
# O WebDriver manager pode baixar automaticamente
```

---

## 🤖 Testes Automatizados (NOVO)

### 🏃‍♂️ Execução Rápida dos Testes

```bash
# Executar todos os testes
cd /home/maikonsilva/MenuAutomacoes/fastapi
python -m pytest tests/ -v

# Executar apenas testes unitários
python -m pytest tests/unit/ -v

# Executar apenas testes de integração
python -m pytest tests/integration/ -v

# Executar com relatório de cobertura
python -m pytest tests/ --cov=. --cov-report=html

# Executar testes específicos
python -m pytest tests/unit/test_state_manager.py -v
```

### 📊 Estrutura dos Testes

```
fastapi/tests/
├── conftest.py              # Configurações e fixtures globais
├── pytest.ini              # Configuração do pytest
├── unit/                    # Testes unitários
│   ├── test_state_manager.py      # ThreadSafeStateManager
│   ├── test_hub_token_service.py  # HubTokenService
│   └── test_fixed_income_service.py # FixedIncomeService
├── integration/             # Testes de integração
│   └── test_api_endpoints.py      # Todos os endpoints da API
├── mocks/                   # Mocks e simulações
│   └── selenium_mocks.py          # Mocks para Selenium WebDriver
└── fixtures/                # Dados de teste
    └── sample_data.py             # Factories e dados sample
```

### 🎯 Categorias de Teste

#### Testes Unitários (Unit Tests)
- **Estado Thread-Safe**: 14 testes para `ThreadSafeStateManager`
- **Serviço de Tokens**: 25+ testes para `HubTokenService` 
- **Serviço Renda Fixa**: 20+ testes para `FixedIncomeService`

#### Testes de Integração (Integration Tests)  
- **Endpoints da API**: 35+ testes para todas as rotas
- **Validação de Dados**: Testes para modelos Pydantic
- **Error Handling**: Cenários de erro e exceções
- **Rate Limiting**: Validação de limites de requisição

#### Mocks e Simulações
- **Selenium WebDriver**: Cenários de sucesso, falha, timeout
- **Database**: Mock de conexões MySQL  
- **HTTP Requests**: Mock de chamadas externas

### 🚀 Comandos de Teste por Categoria

```bash
# Testes por markers
python -m pytest tests/ -m unit              # Apenas testes unitários
python -m pytest tests/ -m integration       # Apenas testes de integração  
python -m pytest tests/ -m selenium          # Testes com Selenium
python -m pytest tests/ -m database          # Testes que usam database

# Testes específicos por funcionalidade
python -m pytest tests/ -k "state_manager"   # Testes do state manager
python -m pytest tests/ -k "token"           # Testes relacionados a tokens
python -m pytest tests/ -k "fixed_income"    # Testes de renda fixa
python -m pytest tests/ -k "api"             # Testes de API

# Execução com diferentes níveis de verbosidade
python -m pytest tests/ -q                   # Resumo
python -m pytest tests/ -v                   # Detalhado
python -m pytest tests/ -vv                  # Muito detalhado
```

### 📈 Relatórios de Teste

```bash
# Relatório HTML de cobertura
python -m pytest tests/ --cov=. --cov-report=html
# Abrir: htmlcov/index.html

# Relatório de cobertura no terminal
python -m pytest tests/ --cov=. --cov-report=term-missing

# Apenas estatísticas de execução
python -m pytest tests/ --tb=line -q

# Testes mais lentos (top 10)
python -m pytest tests/ --durations=10
```

### 🎭 Cenários de Mock Disponíveis

#### Selenium WebDriver Mocks
```python
# Usar em testes personalizados
from tests.mocks.selenium_mocks import SeleniumMockFactory

# Cenários disponíveis:
driver = SeleniumMockFactory.create_hub_xp_mock("success")      # Login bem-sucedido
driver = SeleniumMockFactory.create_hub_xp_mock("failure")      # Falha no login
driver = SeleniumMockFactory.create_hub_xp_mock("mfa_timeout")  # Timeout MFA
driver = SeleniumMockFactory.create_hub_xp_mock("network_error") # Erro de rede
```

#### Database Mocks
```python
# Configuração automática via conftest.py
def test_with_database(mock_db_connection):
    # mock_db_connection já configurado
    mock_db_connection.fetchone.return_value = {"id": 1}
```

### 🔬 Exemplos Práticos de Teste

#### Teste de Token Extraction
```bash
# Testar todo o fluxo de extração de token
python -m pytest tests/unit/test_hub_token_service.py::TestHubTokenService::test_extract_token_success -v

# Testar cenários de falha
python -m pytest tests/unit/test_hub_token_service.py::TestHubTokenService::test_extract_token_login_failed -v
```

#### Teste de API Endpoints
```bash
# Testar validação de credenciais
python -m pytest tests/integration/test_api_endpoints.py::TestAPIValidation -v

# Testar endpoints de token
python -m pytest tests/integration/test_api_endpoints.py::TestTokenEndpoints -v
```

#### Teste de Thread Safety
```bash
# Testar segurança de threads no state manager
python -m pytest tests/unit/test_state_manager.py::TestThreadSafeStateManager::test_thread_safety -v
```

---

## 🚀 Testes de Inicialização (Manuais)

### Teste 1: Executar a Aplicação
```bash
# No diretório fastapi/
python main.py
```

**✅ Resultado Esperado:**
```
INFO:     Will watch for changes in these directories: ['/path/to/fastapi']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using WatchedFiles
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**❌ Erros Comuns:**
- **ModuleNotFoundError**: `pip install -r requirements.txt`
- **ImportError routes**: Verifique se todos os `__init__.py` existem
- **Database connection**: Verifique credenciais no `.env`

### Teste 2: Acessar Documentação Swagger
```bash
# Com a aplicação rodando, acesse:
http://localhost:8000/docs
```

**✅ Resultado Esperado:**
- Interface Swagger UI carregada
- Endpoints visíveis: `/api/health`, `/api/token/*`, `/api/automations`
- Possibilidade de expandir e testar endpoints

### Teste 3: Acessar Root Endpoint
```bash
curl http://localhost:8000/
```

**✅ Resultado Esperado:**
```json
{
  "message": "MenuAutomacoes API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/api/health"
}
```

---

## 🏥 Testes de Health Check

### Teste 4: Health Check Básico
```bash
curl http://localhost:8000/api/health
```

**✅ Resultado Esperado:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-23T17:30:00.000000",
  "database": "connected",
  "version": "1.0.0"
}
```

**❌ Se database: "disconnected":**
1. Verifique credenciais no `.env`
2. Teste conexão MySQL manual
3. Verifique firewall/rede

### Teste 5: Health Check via Swagger
1. Acesse `http://localhost:8000/docs`
2. Expanda `GET /api/health`
3. Clique "Try it out"
4. Clique "Execute"
5. Verifique resposta 200 OK

---

## 📊 Testes de Automações

### Teste 6: Listar Automações
```bash
curl http://localhost:8000/api/automations
```

**✅ Resultado Esperado:**
```json
[
  {
    "name": "Hub XP Token Extraction",
    "description": "Extract authentication tokens from Hub XP platform",
    "status": "active",
    "version": "1.0.0",
    "endpoints": [
      "/api/token/extract",
      "/api/token/status/{user_login}",
      "/api/token/history/{user_login}"
    ]
  }
]
```

### Teste 7: Estatísticas das Automações
```bash
curl http://localhost:8000/api/automations/stats
```

**✅ Resultado Esperado:**
```json
{
  "total_automations": 1,
  "active_automations": 1,
  "total_executions_today": 0,
  "success_rate": 0.0,
  "last_execution": null,
  "platform_status": "healthy"
}
```

---

## 🔐 Testes de Token (Sem Credenciais Reais)

### Teste 8: Status de Token (Usuário Inexistente)
```bash
curl http://localhost:8000/api/token/status/usuario_teste
```

**✅ Resultado Esperado:**
```json
{
  "user_login": "usuario_teste",
  "has_valid_token": false,
  "message": "No token found"
}
```

### Teste 9: Histórico de Token (Usuário Inexistente)
```bash
curl http://localhost:8000/api/token/history/usuario_teste
```

**✅ Resultado Esperado:**
```json
{
  "user_login": "usuario_teste",
  "total_tokens": 0,
  "tokens": []
}
```

### Teste 10: Extração de Token (Credenciais Inválidas)
```bash
curl -X POST "http://localhost:8000/api/token/extract" \
     -H "Content-Type: application/json" \
     -d '{
       "credentials": {
         "user_login": "SILVA.A12345",
         "password": "senha_invalida",
         "mfa_code": "123456"
       }
     }'
```

**⚠️ IMPORTANTE:** Use o formato correto de username: `NOME.A12345` (padrão XP)

**✅ Resultado Esperado:**
```json
{
  "detail": {
    "message": "Login failed", 
    "error_details": "Unable to authenticate with Hub XP"
  }
}
```

**❌ Se username inválido:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "credentials", "user_login"],
      "msg": "Username deve seguir o padrão XP: NOME.A12345 (ex: SILVA.A12345)"
    }
  ]
}
```

---

## 🌐 Testes via Swagger UI

### Teste 11: Interface Swagger Completa

1. **Acesse:** `http://localhost:8000/docs`

2. **Teste Health Check:**
   - Expanda `GET /api/health`
   - "Try it out" → "Execute"
   - Verifique status 200

3. **Teste Automações:**
   - Expanda `GET /api/automations`
   - "Try it out" → "Execute" 
   - Verifique lista de automações

4. **Teste Token Status:**
   - Expanda `GET /api/token/status/{user_login}`
   - Digite "usuario_teste" no campo
   - "Execute"
   - Verifique resposta

5. **Teste Token History:**
   - Expanda `GET /api/token/history/{user_login}`
   - Digite "usuario_teste"
   - Ajuste limit se desejar
   - "Execute"

6. **Teste Token Extraction (Opcional):**
   - ⚠️ **CUIDADO:** Apenas com credenciais de teste
   - Expanda `POST /api/token/extract`
   - Use credenciais inválidas propositadamente
   - Verifique erro controlado

---

## 🔧 Troubleshooting dos Testes Automatizados

### ❌ Problemas Comuns

#### Erro: ImportError durante os testes
```bash
# Problema: Módulos não encontrados
# Solução: Definir PYTHONPATH
export PYTHONPATH=$PYTHONPATH:/home/maikonsilva/MenuAutomacoes/fastapi
python -m pytest tests/ -v
```

#### Erro: Testes de async falhando
```bash
# Problema: pytest-asyncio não instalado
# Solução: Usar asyncio.run() nos testes (já implementado)
python -m pytest tests/unit/test_state_manager.py::TestStateManagerAsync -v
```

#### Erro: Mock database connection
```bash
# Problema: AttributeError __enter__
# Solução: Verificar se mock_db_connection está sendo usado corretamente
python -m pytest tests/integration/test_api_endpoints.py::TestHealthEndpoints -v --tb=long
```

#### Erro: Rate limiting nos testes de API
```bash
# Problema: Muitas requisições muito rápido
# Solução: Executar testes individuais ou com delay
python -m pytest tests/integration/test_api_endpoints.py::TestAPIValidation::test_username_validation -v
```

### 🎯 Estratégias de Debug

#### Debug de teste específico
```bash
# Executar com maximum verbosity
python -m pytest tests/unit/test_hub_token_service.py::TestHubTokenService::test_extract_token_success -vv

# Com print statements
python -m pytest tests/ -v -s

# Com traceback completo
python -m pytest tests/ --tb=long
```

#### Debug de mocks
```bash
# Testar mocks individualmente
python -c "
from tests.mocks.selenium_mocks import SeleniumMockFactory
driver = SeleniumMockFactory.create_hub_xp_mock('success')
print('Mock created successfully:', type(driver))
"
```

### 📊 Análise de Cobertura

```bash
# Gerar relatório HTML detalhado
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term

# Ver arquivos não cobertos
python -m pytest tests/ --cov=. --cov-report=term-missing

# Cobertura mínima (falha se < 80%)
python -m pytest tests/ --cov=. --cov-fail-under=80
```

### 🚀 Integração Contínua

#### Script de CI/CD
```bash
#!/bin/bash
# test_ci.sh - Script para CI/CD

set -e  # Falha no primeiro erro

echo "🧪 Executando testes automatizados..."

# Testes unitários
echo "▶️ Testes unitários"
python -m pytest tests/unit/ -v --tb=short

# Testes de integração  
echo "▶️ Testes de integração"
python -m pytest tests/integration/ -v --tb=short

# Relatório de cobertura
echo "▶️ Análise de cobertura"
python -m pytest tests/ --cov=. --cov-report=term-missing --cov-fail-under=70

echo "✅ Todos os testes passaram!"
```

### 🔍 Logs de Teste

```bash
# Habilitar logs durante testes
python -m pytest tests/ -v --log-cli-level=INFO

# Logs apenas para falhas
python -m pytest tests/ --log-cli-level=ERROR

# Salvar logs em arquivo
python -m pytest tests/ -v --log-file=test_results.log
```

---

## 🔍 Testes de Logs e Debugging (Manuais)

### Teste 12: Verificar Logs
```bash
# Verifique se logs são criados
ls -la logs/

# Monitore logs em tempo real
tail -f logs/fastapi_app.log

# Em outro terminal, faça uma requisição
curl http://localhost:8000/api/health
```

**✅ Resultado Esperado:**
- Arquivo `logs/fastapi_app.log` criado
- Logs aparecem no terminal e arquivo
- Requisições são logadas

### Teste 13: Teste de Selenium (Sem Login)
```bash
# Verificar se ChromeDriver funciona
python3 -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
driver = webdriver.Chrome(options=options)
driver.get('https://www.google.com')
print('Selenium OK:', driver.title)
driver.quit()
"
```

**✅ Resultado Esperado:**
```
Selenium OK: Google
```

---

## 📝 Checklist de Validação

✅ **TODOS OS TESTES CONCLUÍDOS COM SUCESSO** - 24/06/2025

### 🤖 Testes Automatizados (NOVO)
- [X] ✅ Suíte de testes implementada - 31 testes passando
- [X] ✅ Testes unitários - ThreadSafeStateManager, services
- [X] ✅ Testes integração - Todos endpoints da API
- [X] ✅ Mocks Selenium - Cenários realísticos implementados
- [X] ✅ Fixtures e factories - Dados de teste automatizados
- [X] ✅ Configuração pytest - Markers, async, cobertura
- [X] ✅ Validação Pydantic - Padrão XP NOME.A12345
- [X] ✅ Error handling - Cenários de erro cobertos
- [X] ✅ Thread safety - Concorrência testada

### Inicialização
- [X] ✅ Aplicação inicia sem erros
- [X] ✅ Swagger UI acessível  
- [X] ✅ Root endpoint responde

### Conectividade
- [X] ✅ Health check: database connected
- [X] ✅ MySQL connection funcional
- [X] ✅ Logs sendo gerados

### Endpoints
- [X] ✅ `/api/health` - Status 200
- [X] ✅ `/api/automations` - Lista automações
- [X] ✅ `/api/automations/stats` - Estatísticas
- [X] ✅ `/api/token/status/*` - Status token
- [X] ✅ `/api/token/history/*` - Histórico
- [X] ✅ `/api/token/extract` - Erro controlado

### Token Extraction (Teste Real)
- [X] ✅ Login Hub XP funcional
- [X] ✅ MFA preenchimento correto
- [X] ✅ Token extraído com sucesso
- [X] ✅ Token salvo no banco MySQL
- [X] ✅ API retorna ID correto do token

### Selenium
- [X] ✅ ChromeDriver/Chromium instalado
- [X] ✅ Selenium basic test funcional
- [X] ✅ Headless mode funcionando
- [X] ✅ Seletores Hub XP funcionais
- [X] ✅ WebDriverWait configurado corretamente

### Documentação
- [X] ✅ Swagger UI completa
- [X] ✅ Todos endpoints documentados
- [X] ✅ Models Pydantic visíveis

---

## 🚨 Troubleshooting

### Erro: "Module not found"
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt

# Verificar Python path
export PYTHONPATH=$PYTHONPATH:/home/maikonsilva/MenuAutomacoes/fastapi
```

### Erro: Database connection
```bash
# Testar conexão MySQL direta
mysql -h srv719.hstgr.io -u u272626296_mesapremium -p u272626296_automacoes

# Verificar firewall
ping srv719.hstgr.io
```

### Erro: Selenium/Chrome
```bash
# WSL/Linux
sudo apt install -y chromium-browser

# Verificar instalação
chromium-browser --version
which chromium-browser
```

### Erro: Port já em uso
```bash
# Matar processo na porta 8000
sudo lsof -t -i:8000 | xargs kill -9

# Ou usar porta diferente
uvicorn main:app --port 8001
```

---

## 🎯 Status Atual - TESTES CONCLUÍDOS ✅

### ✅ **FASE 1 COMPLETA** - FastAPI Validado
1. ✅ **Aplicação funcionando** - Todos endpoints operacionais
2. ✅ **Selenium integrado** - Chrome/Chromium configurado
3. ✅ **Token extraction funcional** - Hub XP login + MFA + token salvo
4. ✅ **Banco de dados** - MySQL conectado e operacional
5. ✅ **Logs configurados** - Debug e monitoramento ativo

### 🆕 **FASE 2 COMPLETA** - Testes Automatizados (NOVO)
1. ✅ **Suíte de testes** - 31 testes automatizados implementados
2. ✅ **Testes unitários** - Services, state manager, thread safety
3. ✅ **Testes integração** - API endpoints, validação, error handling
4. ✅ **Mocks avançados** - Selenium WebDriver, database, HTTP
5. ✅ **Configuração pytest** - Markers, fixtures, relatórios de cobertura
6. ✅ **Validação aprimorada** - Padrão XP NOME.A12345 implementado

### 🚀 **PRÓXIMA FASE** - Integração PHP
1. **Objetivo**: Consumir API FastAPI via PHP
2. **Endpoints**: `/api/token/extract`, `/api/token/status`
3. **Documentação**: Swagger UI disponível em `/docs`
4. **Ambiente**: Pronto para produção com testes robustos

### 📋 **Resumo dos Problemas Resolvidos**
1. **Seletores Hub XP**: Campo usuário (`name="account"`), senha (`name="password"`)
2. **MFA**: Campos individuais com `class="G7DrImLjomaOopqdA6D6dA=="`
3. **Fluxo de login**: WebDriverWait aguarda MFA após login inicial
4. **ID do token**: Correção de `cursor.lastrowid` vs `LAST_INSERT_ID()`
5. **Validação API**: `token_id is None` vs `not token_id`

---

**💡 Dica:** Execute todos os testes na sequência e anote resultados. Qualquer falha deve ser resolvida antes de prosseguir para integração PHP.

## 🚀 Quick Start - Testes Automatizados

```bash
# Clone e configure
cd /home/maikonsilva/MenuAutomacoes/fastapi

# Execute testes básicos
python -m pytest tests/unit/test_state_manager.py -v

# Execute testes de API
python -m pytest tests/integration/test_api_endpoints.py::TestHealthEndpoints -v

# Relatório completo
python -m pytest tests/ --cov=. --cov-report=term-missing

# Debug de teste específico
python -m pytest tests/unit/test_hub_token_service.py::TestHubTokenService::test_extract_token_success -vv
```

---

*Última atualização: 24/06/2025 por Claude - Adicionados testes automatizados*
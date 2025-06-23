# 🧪 Guia de Testes - FastAPI Hub XP Token Extraction

Este guia contém todos os testes necessários para validar a aplicação FastAPI antes do deploy em produção.

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

## 🚀 Testes de Inicialização

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
         "user_login": "teste",
         "password": "senha_invalida"
       }
     }'
```

**✅ Resultado Esperado:**
```json
{
  "detail": {
    "message": "Login failed",
    "error_details": "Unable to authenticate with Hub XP"
  }
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

## 🔍 Testes de Logs e Debugging

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

Marque cada item após teste bem-sucedido:

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

### Selenium
- [X] ✅ ChromeDriver/Chromium instalado
- [X] ✅ Selenium basic test funcional
- [X] ✅ Headless mode funcionando

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

## 🎯 Próximos Passos Após Testes

### Se todos os testes passaram:
1. ✅ **Fase 1 Concluída** - FastAPI funcionando
2. 🚀 **Iniciar Fase 2** - Integração PHP
3. 📋 **Documentar resultados** no README.md

### Se algum teste falhou:
1. 🔍 **Debug specific issue**
2. 🔧 **Fix and retest**
3. 📝 **Update documentation**

---

**💡 Dica:** Execute todos os testes na sequência e anote resultados. Qualquer falha deve ser resolvida antes de prosseguir para integração PHP.

---

*Última atualização: 23/06/2025 por Claude*
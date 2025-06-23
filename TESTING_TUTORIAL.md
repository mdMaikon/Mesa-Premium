# 🧪 Tutorial Simplificado de Testes

## Problema no Teste 10 - RESOLVIDO ✅

### **Opção 1: Via Swagger UI (MAIS FÁCIL)**

1. **Execute a aplicação:**
```bash
cd /home/maikonsilva/MenuAutomacoes/fastapi
python main.py
```

2. **Acesse o Swagger:**
   - Abra navegador: `http://localhost:8000/docs`

3. **Teste Token Extraction:**
   - Procure por `POST /api/token/extract`
   - Clique em "Try it out"
   - Cole este JSON no campo Request body:
```json
{
  "credentials": {
    "user_login": "teste_usuario",
    "password": "senha_incorreta"
  },
  "force_refresh": false
}
```
   - Clique "Execute"
   - **Resultado esperado:** Erro 400 com mensagem "Login failed"

### **Opção 2: Via cURL (LINHA DE COMANDO)**

```bash
curl -X POST "http://localhost:8000/api/token/extract" \
     -H "Content-Type: application/json" \
     -d '{
       "credentials": {
         "user_login": "teste_usuario", 
         "password": "senha_incorreta"
       }
     }'
```

---

## Problema no Teste 12 - RESOLVIDO ✅

### **Logs Agora Funcionam**

1. **Execute a aplicação:**
```bash
cd /home/maikonsilva/MenuAutomacoes/fastapi
python main.py
```

2. **Verifique logs em tempo real:**
```bash
# Em outro terminal
tail -f logs/fastapi_app.log
```

3. **Faça uma requisição para gerar logs:**
```bash
curl http://localhost:8000/api/health
```

4. **Você deve ver nos logs:**
```
2025-06-23 17:51:24,980 - utils.logging_config - INFO - Logging configured successfully
2025-06-23 17:51:25,123 - database.connection - INFO - Successfully connected to MySQL database
```

---

## 🎯 Testes Essenciais Simplificados

### **1. Health Check**
```bash
curl http://localhost:8000/api/health
```
**Esperado:** `"status": "healthy"`

### **2. Listar Automações**
```bash
curl http://localhost:8000/api/automations
```
**Esperado:** Lista com Hub XP Token Extraction

### **3. Token Status (usuário inexistente)**
```bash
curl http://localhost:8000/api/token/status/usuario_teste
```
**Esperado:** `"has_valid_token": false`

### **4. Swagger UI**
- Acesse: `http://localhost:8000/docs`
- **Esperado:** Interface Swagger com todos endpoints

### **5. Root Endpoint**
```bash
curl http://localhost:8000/
```
**Esperado:** JSON com informações da API

---

## ❗ Se Ainda Tiver Problemas

### **Erro de Import**
```bash
# Execute no diretório fastapi/
export PYTHONPATH=$PYTHONPATH:$(pwd)
python main.py
```

### **Erro de Dependências**
```bash
pip install --upgrade -r requirements.txt
```

### **Erro de Banco de Dados**
- Verifique se o arquivo `.env` existe
- Confirme credenciais MySQL

### **Logs Não Aparecem**
```bash
# Teste isolado
python -c "
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')
logger.info('Test message')
"
```

---

## ✅ Checklist Rápido

- [X] Aplicação inicia sem erros
- [X] Health check retorna "healthy"
- [X] Swagger UI acessível
- [X] Logs aparecem no terminal
- [X] Teste de token extraction via Swagger

**Depois de completar, podemos seguir para integração PHP!**
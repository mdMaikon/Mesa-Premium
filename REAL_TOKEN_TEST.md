# 🔐 Teste de Token Real - Hub XP

## ⚠️ **IMPORTANTE - PROTOCOLO DE SEGURANÇA**

### **Antes de Começar:**
1. **Credenciais Seguras**: Use apenas credenciais de desenvolvimento/teste
2. **Backup**: Faça backup do banco antes do teste
3. **Ambiente**: Execute apenas em ambiente local
4. **Logs**: Monitore logs para debug
5. **Cleanup**: Remova tokens de teste após validação

---

## 🧪 **Método 1: Via Swagger UI (Recomendado)**

### **1. Preparação**
```bash
cd /home/maikonsilva/MenuAutomacoes/fastapi
python main.py
```

### **2. Monitoramento de Logs**
```bash
# Terminal separado para logs
tail -f logs/fastapi_app.log
```

### **3. Teste via Swagger**
1. **Acesse:** `http://localhost:8000/docs`
2. **Endpoint:** `POST /api/token/extract`
3. **Clique:** "Try it out"
4. **JSON Request:**
```json
{
  "credentials": {
    "user_login": "SEU_LOGIN_REAL",
    "password": "SUA_SENHA_REAL"
  },
  "force_refresh": false
}
```

### **4. Observar Processo**
- **Logs em tempo real:** Acompanhe no terminal de logs
- **Selenium:** ChromeDriver abrirá (se não headless)
- **Tempo:** Processo pode levar 30-60 segundos
- **MFA:** Se necessário, será solicitado

### **5. Resultado Esperado**
```json
{
  "success": true,
  "message": "Token extracted successfully",
  "token_id": 123,
  "user_login": "seu_login",
  "expires_at": "2025-06-24T18:00:00.000000"
}
```

---

## 🧪 **Método 2: Via cURL (Avançado)**

```bash
curl -X POST "http://localhost:8000/api/token/extract" \
     -H "Content-Type: application/json" \
     -d '{
       "credentials": {
         "user_login": "SEU_LOGIN",
         "password": "SUA_SENHA"
       }
     }'
```

---

## 🔍 **Verificação de Sucesso**

### **1. Verificar Token no Banco**
```bash
# Conecte ao MySQL e verifique
mysql -h srv719.hstgr.io -u u272626296_mesapremium -p u272626296_automacoes

# No MySQL:
SELECT user_login, expires_at, extracted_at, created_at 
FROM hub_tokens 
WHERE user_login = 'SEU_LOGIN' 
ORDER BY created_at DESC 
LIMIT 1;
```

### **2. Testar Status via API**
```bash
curl http://localhost:8000/api/token/status/SEU_LOGIN
```

**Esperado:**
```json
{
  "user_login": "SEU_LOGIN",
  "has_valid_token": true,
  "expires_at": "2025-06-24T18:00:00.000000",
  "extracted_at": "2025-06-23T18:00:00.000000",
  "time_until_expiry": "23:59:45"
}
```

### **3. Testar Histórico**
```bash
curl http://localhost:8000/api/token/history/SEU_LOGIN
```

---

## 🐛 **Troubleshooting - Problemas Comuns**

### **Erro: Login Failed**
```json
{
  "detail": {
    "message": "Login failed",
    "error_details": "Unable to authenticate with Hub XP"
  }
}
```

**Soluções:**
1. **Credenciais:** Verifique username/password
2. **MFA:** Se Hub XP solicitar MFA, adicione ao JSON:
```json
{
  "credentials": {
    "user_login": "SEU_LOGIN",
    "password": "SUA_SENHA",
    "mfa_code": "123456"
  }
}
```
3. **Captcha:** Hub XP pode ter captcha (verificar logs)

### **Erro: Selenium WebDriver**
```
WebDriverException: chrome not reachable
```

**Soluções:**
```bash
# Verificar Chrome
which chromium-browser
chromium-browser --version

# Instalar se necessário
sudo apt update
sudo apt install -y chromium-browser
```

### **Erro: Database Connection**
```
Failed to save token to database
```

**Soluções:**
1. **Verificar .env:** Credenciais MySQL corretas
2. **Testar conexão:**
```bash
curl http://localhost:8000/api/health
```

### **Timeout no Selenium**
**Aumentar timeout no service:**
```python
# Se necessário, editar hub_token_service.py
wait = WebDriverWait(self.driver, 60)  # Aumentar de 30 para 60
```

---

## 📊 **Checklist de Teste Real**

### **Pré-teste**
- [ ] Credenciais Hub XP válidas
- [ ] FastAPI rodando local
- [ ] Logs monitorados
- [ ] Chrome/Chromium instalado

### **Durante o Teste**
- [ ] Request enviado via Swagger
- [ ] Logs acompanhados em tempo real
- [ ] Selenium executando (se visível)
- [ ] Sem erros críticos nos logs

### **Pós-teste**
- [ ] Response HTTP 200 recebido
- [ ] Token salvo no banco MySQL
- [ ] Status API retorna token válido
- [ ] Histórico API mostra extração

### **Limpeza**
- [ ] Token de teste removido (se necessário)
- [ ] Logs revisados para issues
- [ ] Credenciais não expostas em logs

---

## 🔒 **Medidas de Segurança**

### **Durante Desenvolvimento**
1. **Nunca commitar** credenciais reais
2. **Usar .env** para credenciais
3. **Logs mascarados** para senhas
4. **Ambiente local** apenas

### **Limpeza Pós-teste**
```bash
# Remover token de teste se necessário
curl -X DELETE "http://localhost:8000/api/token/SEU_LOGIN"
```

### **Verificar Logs Seguros**
```bash
# Verificar se senhas não aparecem em logs
grep -i "password" logs/fastapi_app.log
# Não deve mostrar senhas em texto claro
```

---

## 🎯 **Próximo Passo Após Sucesso**

Se o teste real funcionar:
1. ✅ **FastAPI validado** com credenciais reais
2. 🚀 **Prosseguir** para integração PHP
3. 📋 **Documentar** resultados no README.md

---

## 📞 **Suporte**

**Se tiver problemas:**
1. **Logs detalhados:** Copie logs completos do erro
2. **Screenshots:** Se Selenium abrir browser
3. **Response:** JSON de resposta da API
4. **Database:** Status da tabela hub_tokens

**Pronto para testar? Execute o método 1 (Swagger UI) primeiro!**

---

*⚠️ Lembre-se: Use apenas credenciais de teste/desenvolvimento*
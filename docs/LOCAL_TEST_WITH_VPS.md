# 🧪 Testando Localmente com Banco VPS

Este guia explica como testar a aplicação na sua máquina local conectando ao banco MySQL do VPS.

## 📋 Pré-requisitos

- Python 3.12+ instalado localmente
- Poetry instalado
- Acesso de rede ao VPS (IP: YOUR_VPS_IP_ADDRESS)
- MySQL do VPS configurado para aceitar conexões externas

## 🔧 Configuração Local

### 1. Preparar Ambiente
```bash
# Clonar repositório (se ainda não tiver)
git clone https://github.com/seu-usuario/MenuAutomacoes.git
cd MenuAutomacoes

# Instalar dependências
poetry install

# Ativar ambiente virtual
poetry shell
```

### 2. Configurar Conexão com VPS
```bash
# Copiar template de configuração VPS
cp .env.vps-external .env

# Verificar configuração
cat .env
```

O arquivo `.env` deve conter:
```env
# Database Configuration (VPS MySQL External Access)
DB_HOST=YOUR_VPS_IP_ADDRESS
DB_PORT=3306
DB_NAME=mesa_premium_db
DB_USER=mesa_user
DB_PASSWORD=YOUR_SECURE_PASSWORD_HERE
```

### 3. Testar Conexão com Banco
```bash
# Testar conectividade com o VPS
ping YOUR_VPS_IP_ADDRESS

# Testar porta MySQL (se telnet disponível)
telnet YOUR_VPS_IP_ADDRESS 3306

# Ou usar nc (netcat)
nc -zv YOUR_VPS_IP_ADDRESS 3306
```

### 4. Executar Aplicação Local
```bash
# Executar API FastAPI
poetry run task dev

# Ou executar diretamente
poetry run uvicorn fastapi.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Testar Endpoints
```bash
# Health check
curl http://localhost:8000/api/health

# Listar automações
curl http://localhost:8000/api/automations

# Verificar documentação
# http://localhost:8000/docs
```

## 🔒 Configuração de Segurança no VPS

Para permitir conexões externas ao MySQL (necessário para teste local):

### 1. Configurar MySQL no VPS
```bash
# SSH no VPS
ssh root@YOUR_VPS_IP_ADDRESS

# Editar configuração MySQL
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# Comentar ou alterar bind-address
# bind-address = 127.0.0.1  # Comentar esta linha
bind-address = 0.0.0.0      # Ou usar esta configuração

# Reiniciar MySQL
sudo systemctl restart mysql

# Verificar se está ouvindo em todas as interfaces
sudo netstat -tlnp | grep 3306
```

### 2. Configurar Usuário MySQL para Acesso Externo
```bash
# Acessar MySQL no VPS
sudo mysql -u root -p

# Permitir acesso externo ao usuário
GRANT ALL PRIVILEGES ON mesa_premium_db.* TO 'mesa_user'@'%';
FLUSH PRIVILEGES;

# Verificar usuários
SELECT user, host FROM mysql.user WHERE user='mesa_user';
EXIT;
```

### 3. Configurar Firewall no VPS
```bash
# Permitir conexões MySQL (porta 3306)
sudo ufw allow 3306/tcp

# Verificar regras do firewall
sudo ufw status
```

## 🚨 Considerações de Segurança

### ⚠️ IMPORTANTE: Acesso Externo ao MySQL

Permitir acesso externo ao MySQL pode ser um risco de segurança. Considere:

1. **Para Desenvolvimento:** OK temporariamente
2. **Para Produção:** Use conexão SSH tunnel ou VPN

### 🔐 Alternativa Segura: SSH Tunnel
```bash
# Criar túnel SSH (mais seguro)
ssh -L 3306:localhost:3306 root@YOUR_VPS_IP_ADDRESS

# Em outro terminal, usar localhost na aplicação
# DB_HOST=localhost (no .env)
```

## 🐛 Troubleshooting

### Erro: "Can't connect to MySQL server"
```bash
# 1. Verificar conectividade
ping YOUR_VPS_IP_ADDRESS
nc -zv YOUR_VPS_IP_ADDRESS 3306

# 2. Verificar firewall no VPS
sudo ufw status

# 3. Verificar MySQL está rodando no VPS
sudo systemctl status mysql

# 4. Verificar bind-address no VPS
sudo grep bind-address /etc/mysql/mysql.conf.d/mysqld.cnf
```

### Erro: "Access denied for user"
```bash
# Verificar permissões no VPS
sudo mysql -u root -p
SELECT user, host FROM mysql.user WHERE user='mesa_user';
SHOW GRANTS FOR 'mesa_user'@'%';
```

### Erro: "Host is not allowed to connect"
```bash
# Recriar usuário com acesso externo no VPS
sudo mysql -u root -p
DROP USER 'mesa_user'@'%';
CREATE USER 'mesa_user'@'%' IDENTIFIED BY 'YOUR_SECURE_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON mesa_premium_db.* TO 'mesa_user'@'%';
FLUSH PRIVILEGES;
```

## 📊 Comandos de Teste

### Testar Extração de Token
```bash
curl -X POST "http://localhost:8000/api/token/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "user_login": "seu.usuario",
    "password": "sua.senha",
    "mfa_code": "123456"
  }'
```

### Testar Processamento Renda Fixa
```bash
# Processar dados
curl -X POST "http://localhost:8000/api/fixed-income/process"

# Verificar status
curl "http://localhost:8000/api/fixed-income/status"

# Ver estatísticas
curl "http://localhost:8000/api/fixed-income/stats"
```

---

## 🔄 Fluxo Completo de Teste

```bash
# 1. Configurar ambiente local
poetry install
cp .env.vps-external .env

# 2. Configurar VPS (uma vez só)
ssh root@YOUR_VPS_IP_ADDRESS
# ... configurar MySQL para acesso externo

# 3. Testar conectividade
nc -zv YOUR_VPS_IP_ADDRESS 3306

# 4. Executar aplicação
poetry run task dev

# 5. Testar endpoints
curl http://localhost:8000/api/health
```

---

*Última atualização: 30/06/2025 - VPS MySQL Configuration*

# Guia de Configuração do VPS Hostinger

Este guia detalha os passos necessários para configurar o projeto Mesa Premium no VPS da Hostinger com banco MySQL local.

## 📋 Pré-requisitos

- Acesso root ao VPS
- MySQL instalado e rodando
- Python 3.8+ instalado
- Poetry instalado (gerenciador de dependências)

## 🗄️ 1. Configuração do MySQL

### 1.1 Executar Script de Configuração

Execute o script SQL fornecido no MySQL:

```bash
# Conectar como root
mysql -u root -p

# Executar script de configuração
source /path/to/setup_mysql_vps.sql
```

**Ou execute linha por linha:**

```sql
-- Criar banco de dados
CREATE DATABASE IF NOT EXISTS mesa_premium_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Criar usuário
CREATE USER IF NOT EXISTS 'mesa_user'@'localhost' IDENTIFIED BY 'Blue@@10';
CREATE USER IF NOT EXISTS 'mesa_user'@'%' IDENTIFIED BY 'Blue@@10;


-- Conceder permissões
GRANT ALL PRIVILEGES ON mesa_premium_db.* TO 'mesa_user'@'localhost';
GRANT ALL PRIVILEGES ON mesa_premium_db.* TO 'mesa_user'@'%';
FLUSH PRIVILEGES;
```

### 1.2 Verificar Configuração

```sql
-- Verificar se o banco foi criado
SHOW DATABASES LIKE 'mesa_premium_db';

-- Verificar usuário
SELECT User, Host FROM mysql.user WHERE User = 'mesa_user';

-- Testar conexão
mysql -u mesa_user -p mesa_premium_db
```

## 🔧 2. Configuração da Aplicação

### 2.1 Clonar Repositório

```bash
cd /var/www
git clone https://github.com/seu-usuario/MenuAutomacoes.git
cd MenuAutomacoes
```

### 2.2 Configurar Ambiente

```bash
# Instalar dependências
poetry install --only=main

# Ativar ambiente virtual
poetry shell

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com as configurações do VPS
```

### 2.3 Arquivo `.env` para VPS

```bash
# PRODUÇÃO (VPS Hostinger) - Configuração ativa
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=mesa_user
DATABASE_PASSWORD=Mesa@Premium2024!
DATABASE_NAME=mesa_premium_db

# Configurações adicionais do banco
DB_HOST=localhost
DB_USER=mesa_user
DB_PASSWORD=Mesa@Premium2024!
DB_NAME=mesa_premium_db
DB_PORT=3306
DB_CHARSET=utf8mb4
DB_AUTOCOMMIT=True
DB_CONNECTION_TIMEOUT=10
DB_POOL_SIZE=5

# HUB XP API CONFIGURATION
HUB_XP_API_KEY=3923e12297e7448398ba9a9046c4fced
HUB_XP_STRUCTURED_API_KEY=4099b36f826749e1acab295989795688

# APPLICATION CONFIGURATION
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost,http://localhost:8000,http://vps-ip

# SELENIUM CONFIGURATION
CHROME_HEADLESS=True
SELENIUM_TIMEOUT=30
```

## 🧪 3. Testar Configuração

### 3.1 Teste de Conexão com Banco

```bash
# Executar script de teste
poetry run python test_mysql_connection.py
```

**Saída esperada:**
```
=== TESTE DE CONEXÃO MYSQL VPS ===
Host: localhost
Porta: 3306
Usuário: mesa_user
Banco: mesa_premium_db
========================================
Conectando ao MySQL...
✅ Conexão estabelecida com sucesso!
Versão do MySQL: 8.0.x
Banco atual: mesa_premium_db
Nenhuma tabela encontrada no banco
✅ Teste de inserção/remoção concluído com sucesso!
```

### 3.2 Testar API

```bash
# Iniciar aplicação
poetry run uvicorn fastapi.main:app --host 0.0.0.0 --port 8000

# Em outro terminal, testar endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/automations
```

## 🚀 4. Deploy em Produção

### 4.1 Configuração com Nginx

Criar arquivo `/etc/nginx/sites-available/mesa-premium`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ativar site:
```bash
sudo ln -s /etc/nginx/sites-available/mesa-premium /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4.2 Configuração com Systemd

Criar arquivo `/etc/systemd/system/mesa-premium.service`:

```ini
[Unit]
Description=Mesa Premium API
After=network.target mysql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/MenuAutomacoes
Environment=PATH=/var/www/MenuAutomacoes/.venv/bin
ExecStart=/var/www/MenuAutomacoes/.venv/bin/uvicorn fastapi.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mesa-premium
sudo systemctl start mesa-premium
sudo systemctl status mesa-premium
```

### 4.3 Deploy com Docker (Alternativo)

```bash
# Gerar requirements.txt
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes

# Build e deploy
export COMPOSE_BAKE=true
docker compose build
docker compose up -d
```

## 📊 5. Monitoramento

### 5.1 Logs da Aplicação

```bash
# Logs do systemd
sudo journalctl -u mesa-premium -f

# Logs diretos
tail -f /var/www/MenuAutomacoes/logs/app.log
```

### 5.2 Status do Banco

```bash
# Status do MySQL
sudo systemctl status mysql

# Conexões ativas
mysql -u root -p -e "SHOW PROCESSLIST;"

# Uso de espaço
mysql -u root -p -e "SELECT table_schema, ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'DB Size in MB' FROM information_schema.tables WHERE table_schema='mesa_premium_db';"
```

## 🔒 6. Segurança

### 6.1 Firewall

```bash
# Permitir apenas portas necessárias
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 6.2 Backup do Banco

```bash
# Script de backup diário
cat > /etc/cron.daily/mesa-premium-backup << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u mesa_user -p'Mesa@Premium2024!' mesa_premium_db > /var/backups/mesa_premium_${DATE}.sql
find /var/backups -name "mesa_premium_*.sql" -mtime +7 -delete
EOF

chmod +x /etc/cron.daily/mesa-premium-backup
```

## 🔧 7. Comandos Úteis

### 7.1 Gerenciamento da Aplicação

```bash
# Reiniciar aplicação
sudo systemctl restart mesa-premium

# Ver logs em tempo real
sudo journalctl -u mesa-premium -f

# Verificar status
sudo systemctl status mesa-premium
```

### 7.2 Gerenciamento do Banco

```bash
# Conectar ao banco
mysql -u mesa_user -p mesa_premium_db

# Backup manual
mysqldump -u mesa_user -p mesa_premium_db > backup_$(date +%Y%m%d).sql

# Restaurar backup
mysql -u mesa_user -p mesa_premium_db < backup_file.sql
```

### 7.3 Manutenção

```bash
# Atualizar código
cd /var/www/MenuAutomacoes
git pull origin main
poetry install --only=main
sudo systemctl restart mesa-premium

# Limpar logs antigos
sudo journalctl --vacuum-time=30d

# Verificar espaço em disco
df -h
```

## ❓ 8. Troubleshooting

### 8.1 Problemas de Conexão com Banco

```bash
# Verificar se MySQL está rodando
sudo systemctl status mysql

# Verificar logs do MySQL
sudo tail -f /var/log/mysql/error.log

# Testar conexão manual
mysql -u mesa_user -p mesa_premium_db
```

### 8.2 Problemas da Aplicação

```bash
# Verificar logs
sudo journalctl -u mesa-premium -n 100

# Testar configuração
cd /var/www/MenuAutomacoes
poetry run python test_mysql_connection.py

# Verificar variáveis de ambiente
poetry run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'DB_HOST: {os.getenv(\"DB_HOST\")}')"
```

### 8.3 Problemas de Permissão

```bash
# Ajustar permissões dos arquivos
sudo chown -R www-data:www-data /var/www/MenuAutomacoes
sudo chmod -R 755 /var/www/MenuAutomacoes

# Verificar permissões do banco
mysql -u root -p -e "SHOW GRANTS FOR 'mesa_user'@'localhost';"
```

## 📞 Suporte

Para problemas específicos:

1. Verificar logs da aplicação
2. Testar conexão com banco
3. Verificar configurações do `.env`
4. Consultar documentação do projeto

---

**Importante:** Mantenha sempre backups atualizados e monitore os logs regularmente.

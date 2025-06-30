# 🚀 Guia de Deploy VPS - MenuAutomacoes API

## 📋 Pré-requisitos VPS

### 🖥️ Servidor Requirements
- Ubuntu 22.04+ ou Rocky Linux 9+
- 4GB RAM mínimo (8GB recomendado para produção)
- 40GB storage SSD
- Python 3.12+
- Docker + Docker Compose V2
- Poetry para gerenciamento de dependências

### 🌐 Domínio Configurado
- Domínio apontando para IP do VPS
- Subdomain www também configurado

## 🔧 Setup Inicial no VPS

### 1. Instalar Dependências do Sistema
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.12+
sudo apt install -y python3.12 python3.12-venv python3-pip curl git

# Instalar Docker (método oficial)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Verificar Docker Compose V2 (já incluso no Docker moderno)
docker compose version
```

### 2. Instalar Poetry
```bash
# Instalar Poetry (gerenciador de dependências)
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verificar instalação
poetry --version
```

### 3. Clonar e Configurar Projeto
```bash
# Clonar repositório
git clone https://github.com/seu-usuario/MenuAutomacoes.git
cd MenuAutomacoes

# Instalar dependências com Poetry
poetry install --only=main --no-dev

# Verificar ambiente Poetry
poetry env info
```

### 4. Configurar Environment
```bash
# Copiar template de produção
cp .env.production .env

# Editar com suas configurações específicas
nano .env

# Configurar variáveis Docker (se usar MySQL local)
cp .env.docker .env.docker.local
nano .env.docker.local
```

## ⚙️ Configuração de Produção

### 1. Preparar Dockerfile para Poetry
```bash
# Criar requirements.txt temporário para Docker (Poetry não está no container)
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes

# Verificar se requirements.txt foi criado
ls -la fastapi/requirements.txt
```

### 2. Configurar Domínio no Nginx
```bash
# Editar configuração com seu domínio real
sed -i 's/yourdomain.com/seudominio.com/g' nginx/sites-available/mesa_premium.conf
```

### 3. Build e Deploy Inicial
```bash
# RECOMENDADO: Habilitar Docker Buildx Bake para performance otimizada
export COMPOSE_BAKE=true

# Build das imagens com Docker Compose V2 + Buildx Bake
docker compose build

# Subir serviços (produção com Hostinger MySQL)
docker compose up -d api redis nginx

# Verificar status dos containers
docker compose ps

# Verificar logs da API
docker compose logs -f api
```

## 🔒 Configurar SSL/TLS

### 1. Executar Script de SSL
```bash
# Tornar script executável
chmod +x scripts/setup-ssl.sh

# Configurar SSL automaticamente
./scripts/setup-ssl.sh seudominio.com seu-email@domain.com
```

### 2. Verificar SSL
```bash
# Testar certificado
curl -I https://seudominio.com/api/health

# Testar documentação
curl -I https://seudominio.com/docs

# Verificar grade SSL (A+ esperado)
# https://www.ssllabs.com/ssltest/analyze.html?d=seudominio.com
```

## 🧪 Validação do Deploy

### 1. Health Checks
```bash
# API Health (deve retornar status OK)
curl https://seudominio.com/api/health

# Lista de automações
curl https://seudominio.com/api/automations

# Documentação Swagger
curl -I https://seudominio.com/docs

# Documentação ReDoc
curl -I https://seudominio.com/redoc
```

### 2. Testes de API
```bash
# Teste de extração de token Hub XP
curl -X POST "https://seudominio.com/api/token/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "user_login": "seu.usuario",
    "password": "sua.senha",
    "mfa_code": "123456"
  }'

# Status de processamento de renda fixa
curl https://seudominio.com/api/fixed-income/status

# Estatísticas dos dados
curl https://seudominio.com/api/fixed-income/stats
```

## 📊 Monitoramento

### 1. Logs Centralizados
```bash
# Logs em tempo real
docker compose logs -f

# Logs específicos
docker compose logs api
docker compose logs nginx
```

### 2. Métricas do Sistema
```bash
# Uso de recursos
docker stats

# Disk usage
df -h
du -sh /var/lib/docker/
```

### 3. Scripts de Monitoramento
```bash
# Status dos containers (Docker Compose V2)
docker compose ps

# Reiniciar serviço específico
docker compose restart api

# Update e redeploy com Poetry
git pull
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes
docker compose build api
docker compose up -d api

# Verificar se tudo está funcionando
docker compose logs -f api
```

## 🔄 Backup e Manutenção

### 1. Backup de Dados
```bash
# Backup da configuração Poetry
cp pyproject.toml pyproject.toml.backup
cp poetry.lock poetry.lock.backup

# Backup de configurações
tar czf config_backup_$(date +%Y%m%d).tar.gz .env* docker-compose.yml nginx/ mysql/

# Backup de logs
tar czf logs_backup_$(date +%Y%m%d).tar.gz logs/ fastapi/logs/

# Backup do banco Hostinger (se aplicável)
# mysqldump -h srv719.hstgr.io -u usuario -p base_dados > backup_$(date +%Y%m%d).sql
```

### 2. Atualizações com Poetry
```bash
# Atualizar dependências
poetry update

# Exportar requirements.txt atualizado
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes

# Verificar segurança
poetry run task security

# Executar testes
poetry run task test

# Script de atualização segura (se existir)
./scripts/update_production.sh
```

### 3. Renovação SSL Automática
```bash
# Verificar cron job (já configurado pelo setup-ssl.sh)
sudo crontab -l | grep certbot
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Container não inicia
```bash
# Verificar logs detalhados (Docker Compose V2)
docker compose logs --details api

# Verificar configuração
docker compose config

# Verificar se requirements.txt existe
ls -la fastapi/requirements.txt

# Recriar requirements.txt se necessário
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes
```

#### 2. Nginx 502 Bad Gateway
```bash
# Verificar se API está rodando
docker compose ps
curl http://localhost:8000/api/health

# Verificar configuração Nginx
docker compose exec nginx nginx -t

# Verificar conectividade entre containers
docker compose exec nginx curl http://api:8000/api/health
```

#### 3. SSL não funciona
```bash
# Verificar certificados
ls -la nginx/ssl/
openssl x509 -in nginx/ssl/fullchain.pem -text -noout

# Renovar SSL manualmente
sudo certbot renew --dry-run
```

#### 4. Performance Issues
```bash
# Verificar recursos
docker stats
htop

# Ajustar workers FastAPI
# Editar docker-compose.yml: --workers 2 (para 2GB RAM)
```

### Comandos de Emergência

```bash
# Parar tudo (Docker Compose V2)
docker compose down

# Reset completo (CUIDADO: perde dados locais)
docker compose down -v
docker system prune -af

# Restart específico
docker compose restart api
docker compose restart nginx

# Rebuild forçado
docker compose build --no-cache api
docker compose up -d api
```

## 📈 Otimização de Performance

### 1. Configuração FastAPI
```yaml
# No docker-compose.yml
command: ["python", "-m", "uvicorn", "main:app",
          "--host", "0.0.0.0", "--port", "8000",
          "--workers", "4",  # Ajustar conforme RAM
          "--worker-class", "uvicorn.workers.UvicornWorker",
          "--access-log", "--no-server-header"]
```

### 2. Nginx Tuning
```nginx
# No nginx.conf
worker_processes auto;
worker_connections 2048;
keepalive_timeout 30;
client_max_body_size 100M;
```

### 3. Sistema Operacional
```bash
# Limpar cache periodicamente
echo 3 | sudo tee /proc/sys/vm/drop_caches

# Monitorar I/O
sudo iotop
```

## 🔐 Segurança Adicional

### 1. Firewall
```bash
# Configurar UFW
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Bloquear acessos indevidos
sudo ufw deny from IP_MALICIOSO
```

### 2. Updates Automáticos
```bash
# Configurar updates automáticos de segurança
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. Monitoramento de Logs
```bash
# Instalar fail2ban para proteção SSH
sudo apt install fail2ban

# Configurar alerts por email (opcional)
```

---

## 🎯 Comandos Essenciais Poetry + Docker

### Workflow Completo de Deploy
```bash
# 1. Preparar ambiente
poetry install --only=main
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes

# 2. Habilitar Docker Buildx Bake (RECOMENDADO)
export COMPOSE_BAKE=true

# 3. Build e deploy com performance otimizada
docker compose build
docker compose up -d

# 4. Verificar
docker compose ps
curl https://seudominio.com/api/health

# 5. Monitorar
docker compose logs -f api
```

### Comandos de Manutenção
```bash
# Habilitar Buildx Bake para performance
export COMPOSE_BAKE=true

# Atualizar dependências
poetry update
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes
docker compose build api
docker compose up -d api

# Verificar segurança
poetry run task security

# Executar testes
poetry run task test
```

## ✅ Checklist de Deploy Atualizado

### Pré-Deploy
- [ ] VPS com Python 3.12+ e Docker
- [ ] Poetry instalado e configurado
- [ ] Domínio apontando para VPS
- [ ] Repositório clonado
- [ ] .env configurado para produção

### Preparação Poetry
- [ ] `poetry install --only=main` executado
- [ ] `poetry export` gerou requirements.txt
- [ ] `poetry run task check` passou
- [ ] Testes executados com sucesso

### Deploy Docker
- [ ] `docker compose build` executado
- [ ] Serviços iniciados sem erro
- [ ] SSL configurado via script
- [ ] Health checks passando

### Validação Final
- [ ] https://seudominio.com/api/health retorna 200
- [ ] https://seudominio.com/docs acessível
- [ ] https://seudominio.com/api/automations lista 4+ automações
- [ ] Token extraction funcional (teste real)
- [ ] SSL Grade A+ no SSL Labs
- [ ] Logs sendo gerados corretamente

---

## 🚨 Notas Importantes

**Poetry + Docker**: O Dockerfile ainda usa requirements.txt, então sempre execute `poetry export` antes de fazer build.

**Docker Compose V2**: Use `docker compose` (sem hífen) em vez de `docker-compose`.

**Docker Buildx Bake**: Para performance otimizada, sempre use `export COMPOSE_BAKE=true` antes de builds.

**Hostinger MySQL**: Configuração já está no .env.production para usar banco externo.

---

*Guia atualizado em 26/06/2025 - MenuAutomacoes API v2.0 com Poetry*

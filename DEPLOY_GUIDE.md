# 🚀 Guia de Deploy VPS - Mesa Premium API

## 📋 Pré-requisitos VPS

### 🖥️ Servidor Requirements
- Ubuntu 20.04+ ou CentOS 8+
- 2GB RAM mínimo (4GB recomendado)
- 20GB storage
- Docker + Docker Compose instalados

### 🌐 Domínio Configurado
- Domínio apontando para IP do VPS
- Subdomain www também configurado

## 🔧 Setup Inicial no VPS

### 1. Instalar Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo systemctl enable docker

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Clonar Repositório
```bash
git clone https://github.com/seu-usuario/MenuAutomacoes.git
cd MenuAutomacoes
```

### 3. Configurar Environment
```bash
# Copiar template de configuração
cp .env.docker .env

# Editar com suas configurações
nano .env
```

## ⚙️ Configuração de Produção

### 1. Ajustar docker-compose.yml
```bash
# Para produção com MySQL Hostinger, comentar serviço mysql local
# e usar configurações do .env para conectar na Hostinger
nano docker-compose.yml
```

### 2. Configurar Domínio no Nginx
```bash
# Editar configuração com seu domínio real
sed -i 's/yourdomain.com/seudominio.com/g' nginx/sites-available/mesa_premium.conf
```

### 3. Build e Deploy Inicial
```bash
# Build das imagens
docker-compose build

# Subir serviços (sem SSL ainda)
docker-compose up -d api redis

# Verificar logs
docker-compose logs -f api
```

## 🔒 Configurar SSL/TLS

### 1. Executar Script de SSL
```bash
# Configurar SSL automaticamente
./scripts/setup-ssl.sh seudominio.com seu-email@domain.com
```

### 2. Verificar SSL
```bash
# Testar certificado
curl -I https://seudominio.com/health

# Verificar grade SSL
# https://www.ssllabs.com/ssltest/analyze.html?d=seudominio.com
```

## 🧪 Validação do Deploy

### 1. Health Checks
```bash
# API Health
curl https://seudominio.com/health

# Documentação
curl https://seudominio.com/docs
```

### 2. Teste de Token Extraction
```bash
# Teste completo via API
curl -X POST "https://seudominio.com/api/token/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "user_login": "teste.usuario",
    "password": "senha123",
    "mfa_code": "123456"
  }'
```

## 📊 Monitoramento

### 1. Logs Centralizados
```bash
# Logs em tempo real
docker-compose logs -f

# Logs específicos
docker-compose logs api
docker-compose logs nginx
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
# Status dos containers
docker-compose ps

# Reiniciar serviço específico
docker-compose restart api

# Update e redeploy
git pull
docker-compose build api
docker-compose up -d api
```

## 🔄 Backup e Manutenção

### 1. Backup de Dados
```bash
# Backup volumes Docker
docker run --rm -v mesa_premium_mysql_data:/data -v $(pwd):/backup ubuntu tar czf /backup/mysql_backup_$(date +%Y%m%d).tar.gz /data

# Backup de logs
tar czf logs_backup_$(date +%Y%m%d).tar.gz nginx/logs/ fastapi/logs/
```

### 2. Atualizações
```bash
# Script de atualização segura
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
# Verificar logs detalhados
docker-compose logs --details api

# Verificar configuração
docker-compose config
```

#### 2. Nginx 502 Bad Gateway
```bash
# Verificar se API está rodando
docker-compose ps
curl http://localhost:8000/health

# Verificar configuração Nginx
docker-compose exec nginx nginx -t
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
# Parar tudo
docker-compose down

# Reset completo (CUIDADO: perde dados locais)
docker-compose down -v
docker system prune -af

# Restart específico
docker-compose restart api
docker-compose restart nginx
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

## ✅ Checklist de Deploy

### Pré-Deploy
- [ ] VPS configurado com Docker
- [ ] Domínio apontando para VPS
- [ ] Repositório clonado
- [ ] .env configurado

### Deploy
- [ ] docker-compose build executado
- [ ] Serviços iniciados sem erro
- [ ] SSL configurado via script
- [ ] Health checks passando

### Pós-Deploy
- [ ] Testes de API funcionando
- [ ] Logs sendo gerados
- [ ] Monitoramento ativo
- [ ] Backup configurado

### Validação Final
- [ ] https://seudominio.com/health retorna 200
- [ ] https://seudominio.com/docs acessível
- [ ] Token extraction testado
- [ ] SSL Grade A+ no SSL Labs

---

*Guia criado em 24/06/2025 - Mesa Premium API v1.0*
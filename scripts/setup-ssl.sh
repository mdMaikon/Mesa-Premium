#!/bin/bash

# Script para configurar SSL com Let's Encrypt
# Execute no servidor VPS após deploy

set -e

DOMAIN=${1:-"yourdomain.com"}
EMAIL=${2:-"your-email@domain.com"}

echo "🔒 Configurando SSL para domínio: $DOMAIN"
echo "📧 Email para Let's Encrypt: $EMAIL"

# 1. Instalar certbot
echo "📦 Instalando Certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# 2. Parar nginx temporariamente
echo "⏸️  Parando Nginx..."
sudo docker-compose stop nginx

# 3. Obter certificado Let's Encrypt
echo "🔐 Obtendo certificado SSL..."
sudo certbot certonly --standalone \
    --preferred-challenges http \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# 4. Copiar certificados para volume Docker
echo "📋 Copiando certificados..."
sudo mkdir -p ./nginx/ssl
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ./nginx/ssl/
sudo chown -R $USER:$USER ./nginx/ssl/

# 5. Atualizar configuração Nginx com domínio real
echo "⚙️  Atualizando configuração Nginx..."
sed -i "s/yourdomain.com/$DOMAIN/g" ./nginx/sites-available/mesa_premium.conf

# 6. Reiniciar serviços
echo "🚀 Reiniciando serviços..."
sudo docker-compose up -d

# 7. Configurar renovação automática
echo "🔄 Configurando renovação automática..."
sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet && docker-compose restart nginx"; } | sudo crontab -

echo "✅ SSL configurado com sucesso!"
echo "🌐 Acesse: https://$DOMAIN/docs"
echo "🔍 Verificar certificado: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"

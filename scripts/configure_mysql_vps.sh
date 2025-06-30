#!/bin/bash

# Script para configurar MySQL no VPS para aceitar conexões externas
# Execute este script no VPS via SSH

echo "🔧 Configurando MySQL para aceitar conexões externas..."

# 1. Instalar MySQL (se não estiver instalado)
echo "📦 Verificando instalação do MySQL..."
if ! command -v mysql &> /dev/null; then
    echo "Instalando MySQL Server..."
    sudo apt update
    sudo apt install -y mysql-server mysql-client
    sudo mysql_secure_installation
fi

# 2. Configurar bind-address para aceitar conexões externas
echo "🌐 Configurando bind-address..."
sudo sed -i 's/bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf

# 3. Reiniciar MySQL
echo "🔄 Reiniciando MySQL..."
sudo systemctl restart mysql

# 4. Verificar se MySQL está rodando
echo "✅ Verificando status do MySQL..."
sudo systemctl status mysql --no-pager

# 5. Criar database e usuário
echo "🗄️ Configurando database e usuário..."
echo "⚠️  Execute os comandos SQL manualmente:"
echo "   sudo mysql -u root -p"
echo "   CREATE DATABASE IF NOT EXISTS mesa_premium_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "   CREATE USER IF NOT EXISTS 'mesa_user'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';"
echo "   CREATE USER IF NOT EXISTS 'mesa_user'@'%' IDENTIFIED BY 'YOUR_PASSWORD';"
echo "   GRANT ALL PRIVILEGES ON mesa_premium_db.* TO 'mesa_user'@'localhost';"
echo "   GRANT ALL PRIVILEGES ON mesa_premium_db.* TO 'mesa_user'@'%';"
echo "   FLUSH PRIVILEGES;"

# 6. Configurar firewall
echo "🔥 Configurando firewall..."
sudo ufw allow 3306/tcp

# 7. Verificar configuração
echo "🔍 Verificando configuração..."
sudo netstat -tlnp | grep 3306
echo "📊 Testando conexão local..."
mysql -u mesa_user -p -e "SELECT 'MySQL funcionando!' as status;" mesa_premium_db

echo "✅ Configuração concluída!"
echo "📝 Configure estas informações no seu .env:"
echo "   - Host: YOUR_VPS_IP"
echo "   - Port: 3306"
echo "   - Database: mesa_premium_db"
echo "   - User: mesa_user"
echo "   - Password: YOUR_PASSWORD"

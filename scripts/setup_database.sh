#!/bin/bash

# Script para configurar o banco de dados MySQL no VPS
# Execute este script no VPS via SSH

echo "🗄️ Configurando banco de dados MySQL..."

# Verificar se o MySQL está rodando
if ! systemctl is-active --quiet mysql; then
    echo "❌ MySQL não está rodando. Iniciando..."
    sudo systemctl start mysql
fi

# Executar script SQL para criar tabelas
echo "📊 Criando tabelas no banco mesa_premium_db..."
mysql -u mesa_user -p -h localhost mesa_premium_db < create_tables.sql

if [ $? -eq 0 ]; then
    echo "✅ Tabelas criadas com sucesso!"

    # Verificar tabelas criadas
    echo "📋 Verificando tabelas criadas..."
    mysql -u mesa_user -p -h localhost mesa_premium_db -e "SHOW TABLES;"

    echo "🔍 Verificando estrutura da tabela hub_tokens..."
    mysql -u mesa_user -p -h localhost mesa_premium_db -e "DESCRIBE hub_tokens;"

    echo "🔍 Verificando estrutura da tabela fixed_income_data..."
    mysql -u mesa_user -p -h localhost mesa_premium_db -e "DESCRIBE fixed_income_data;"

else
    echo "❌ Erro ao criar tabelas. Verifique o arquivo create_tables.sql"
    exit 1
fi

echo "🎉 Banco de dados configurado com sucesso!"
echo "📝 Agora você pode testar as APIs na sua aplicação local."

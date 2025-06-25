#!/bin/bash

# Script para testar deploy local Docker
set -e

echo "🚀 Testando Deploy Local - Mesa Premium API"
echo "============================================="

# 1. Validar configurações
echo "📋 1. Validando configurações..."
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Arquivo docker-compose.yml não encontrado!"
    exit 1
fi

echo "✅ Arquivos de configuração OK"

# 2. Validar configuração Docker Compose
echo "📋 2. Validando docker-compose.yml..."
if ! sg docker -c "docker compose config" > /dev/null 2>&1; then
    echo "❌ Erro na configuração docker-compose.yml!"
    exit 1
fi
echo "✅ docker-compose.yml válido"

# 3. Build das imagens
echo "📋 3. Fazendo build das imagens..."
sg docker -c "docker compose build api" || {
    echo "❌ Erro no build da imagem API!"
    exit 1
}
echo "✅ Build da API concluído"

# 4. Iniciar serviços
echo "📋 4. Iniciando serviços..."
sg docker -c "docker compose up -d mysql redis" || {
    echo "❌ Erro ao iniciar MySQL e Redis!"
    exit 1
}

# Aguardar MySQL inicializar
echo "⏳ Aguardando MySQL inicializar..."
sleep 10

sg docker -c "docker compose up -d api" || {
    echo "❌ Erro ao iniciar API!"
    exit 1
}

echo "⏳ Aguardando API inicializar..."
sleep 15

sg docker -c "docker compose up -d nginx" || {
    echo "❌ Erro ao iniciar Nginx!"
    exit 1
}

echo "✅ Todos os serviços iniciados"

# 5. Testes de conectividade
echo "📋 5. Testando conectividade..."

# Testar se containers estão rodando
echo "📊 Status dos containers:"
sg docker -c "docker compose ps"

# Testar API diretamente
echo "🔍 Testando API direta (porta 8000)..."
timeout 10 bash -c 'until curl -s http://localhost:8000/api/health; do sleep 1; done' || {
    echo "❌ API não responde na porta 8000"
    echo "📊 Logs da API:"
    sg docker -c "docker compose logs api"
    exit 1
}
echo "✅ API respondendo na porta 8000"

# Testar Nginx
echo "🔍 Testando Nginx (porta 80)..."
timeout 10 bash -c 'until curl -s http://localhost/health; do sleep 1; done' || {
    echo "❌ Nginx não responde na porta 80"
    echo "📊 Logs do Nginx:"
    sg docker -c "docker compose logs nginx"
    exit 1
}
echo "✅ Nginx respondendo na porta 80"

# 6. Testes funcionais
echo "📋 6. Executando testes funcionais..."

# Health check
HEALTH_RESPONSE=$(curl -s http://localhost/health)
if [[ "$HEALTH_RESPONSE" != *"healthy"* ]]; then
    echo "❌ Health check falhou: $HEALTH_RESPONSE"
    exit 1
fi
echo "✅ Health check passou"

# Docs endpoint
if ! curl -s http://localhost/docs | grep -q "FastAPI"; then
    echo "❌ Endpoint /docs não está funcionando"
    exit 1
fi
echo "✅ Documentação acessível"

# API automations endpoint
if ! curl -s http://localhost/api/automations | grep -q "token"; then
    echo "❌ Endpoint /api/automations não está funcionando"
    exit 1
fi
echo "✅ API endpoints funcionando"

# 7. Relatório final
echo ""
echo "🎉 TESTE LOCAL CONCLUÍDO COM SUCESSO!"
echo "=================================="
echo "✅ Todas as validações passaram"
echo "🌐 Acesse: http://localhost/docs"
echo "🔍 Health: http://localhost/health"
echo "📊 Status: sg docker -c 'docker compose ps'"
echo "📝 Logs: sg docker -c 'docker compose logs -f'"
echo ""
echo "Para parar os serviços:"
echo "sg docker -c 'docker compose down'"
echo ""
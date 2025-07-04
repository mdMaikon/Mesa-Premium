# Plano de Ação: Remoção do Nginx do Docker para Deploy VPS

## Contexto
O projeto será deployado em VPS Hostinger que já possui Nginx configurado. O Nginx containerizado do projeto causará conflito de portas (80/443) com o Nginx do sistema.

## Situação Atual ✅ ATUALIZADA
- ✅ `docker-compose.yml` - Desenvolvimento (SEM MySQL local + Nginx) - usa .env.dev
- ✅ `docker-compose.staging.yml` - Staging (SEM Nginx + SEM MySQL local) - usa .env.staging
- ✅ `docker-compose.prod.yml` - Produção (SEM Nginx + SEM MySQL local) - usa .env.production
- ✅ 3 Bancos MySQL VPS criados: mesa_premium_dev, mesa_premium_staging, mesa_premium_db
- ✅ Conflito resolvido: Nginx removido dos ambientes staging/prod

## Estratégia: 3 Ambientes Separados

### 1. docker-compose.yml (Desenvolvimento - ✅ IMPLEMENTADO)
**Finalidade**: Desenvolvimento local completo
- ✅ MySQL VPS (mesa_premium_dev) - SEM MySQL local
- ✅ Nginx containerizado (OK localmente - sem conflito)
- ✅ Redis para cache
- ✅ Logs e debug habilitados
- ✅ Arquivo .env.dev específico
- **Porta**: 80 (localhost apenas)

### 2. docker-compose.staging.yml (Staging - ✅ CRIADO)
**Finalidade**: Homologação/testes pré-produção
- ✅ Banco remoto (mesa_premium_staging)
- ✅ SEM Nginx (usa Nginx do servidor)
- ✅ Redis para cache
- ✅ Configurações similares à produção
- ✅ Arquivo .env.staging específico
- **Porta**: API exposta em porta interna (8000)

### 3. docker-compose.prod.yml (Produção - ✅ MODIFICADO)
**Finalidade**: Produção no VPS
- ✅ Banco remoto (mesa_premium_db)
- ✅ SEM Nginx (usa Nginx do VPS) - REMOVIDO
- ✅ Redis para cache
- ✅ Configurações otimizadas
- ✅ Logs reduzidos
- ✅ Arquivo .env.production específico
- **Porta**: API exposta em porta interna (8000)

## Plano de Execução

### Fase 1: Estruturação dos Ambientes ✅ CONCLUÍDA
- [x] **1.1** - Criar `docker-compose.staging.yml` baseado no prod atual, sem Nginx
- [x] **1.2** - Modificar `docker-compose.prod.yml` removendo serviço Nginx
- [x] **1.3** - Modificar `docker-compose.yml` para usar MySQL VPS (mesa_premium_dev)
- [x] **1.4** - Criar arquivos .env específicos (.env.dev, .env.staging, .env.production)
- [x] **1.5** - Remover MySQL local do docker-compose.yml
- [x] **1.6** - Criar 3 bancos no MySQL VPS (dev, staging, prod)
- [x] **1.7** - Testar ambiente de desenvolvimento - SUCESSO

### Fase 2: Configuração Nginx VPS
- [ ] **2.1** - Criar arquivo de configuração Nginx para VPS (`/etc/nginx/sites-available/mesa-premium`)
- [ ] **2.2** - Adaptar configuração atual do projeto para sintaxe padrão do sistema
- [ ] **2.3** - Configurar SSL/HTTPS se necessário
- [ ] **2.4** - Documentar comandos de ativação do site no VPS

### Fase 3: Testes e Validação
- [ ] **3.1** - Testar ambiente staging localmente
- [ ] **3.2** - Validar exposição correta da API (porta 8000)
- [ ] **3.3** - Verificar conectividade com banco remoto
- [ ] **3.4** - Testar todos os endpoints via proxy

### Fase 4: Documentação
- [x] **4.1** - Atualizar CLAUDE.md com novos comandos - CONCLUÍDO
- [x] **4.2** - Documentar estrutura de 3 ambientes - CONCLUÍDO
- [x] **4.3** - Documentar bancos MySQL VPS - CONCLUÍDO
- [ ] **4.4** - Criar guia de configuração do Nginx no servidor (Fase 2)
- [ ] **4.5** - Limpar arquivos temporários (remover este arquivo)

## Comandos de Deploy por Ambiente

### Desenvolvimento (Local) ✅ TESTADO
```bash
# Com MySQL VPS (mesa_premium_dev) + Nginx containerizado
docker compose up -d
# Acesso: http://localhost/docs
# Status: FUNCIONANDO - API conectada ao banco mesa_premium_dev
```

### Staging (Servidor de Homologação)
```bash
# Sem Nginx, banco remoto
docker compose -f docker-compose.staging.yml up -d
# Acesso via Nginx do servidor: http://staging.domain.com/docs
```

### Produção (VPS Hostinger)
```bash
# Sem Nginx, banco remoto, otimizado
docker compose -f docker-compose.prod.yml up -d
# Acesso via Nginx do VPS: https://domain.com/docs
```

## Vantagens desta Abordagem

### ✅ Benefícios
1. **Sem Conflitos**: Eliminação do conflito de portas 80/443
2. **Otimização**: Usa Nginx nativo do VPS (melhor performance)
3. **Flexibilidade**: Cada ambiente com suas especificidades
4. **Manutenção**: Mudanças isoladas por ambiente
5. **Segurança**: Configurações sensíveis separadas
6. **CI/CD**: Deploy automatizado por ambiente

### 🔧 Configurações por Ambiente
- **Dev**: Desenvolvimento completo isolado
- **Staging**: Réplica da produção para testes
- **Prod**: Otimizado para performance e segurança

## Estrutura Final de Arquivos

```
MenuAutomacoes/
├── docker-compose.yml              # Desenvolvimento (mantém Nginx) ✅
├── docker-compose.staging.yml      # Staging (sem Nginx) ✅ CRIADO
├── docker-compose.prod.yml         # Produção (sem Nginx) ✅ MODIFICADO
├── .env.dev                        # Config desenvolvimento ✅ CRIADO
├── .env.staging                    # Config staging ✅ CRIADO
├── .env.production                 # Config produção ✅ CRIADO
├── .env.example                    # Template ✅ MANTIDO
├── nginx/                          # Configurações Docker (só dev)
│   ├── nginx.conf
│   └── sites-available/
└── vps-nginx/                      # Configurações VPS - PENDENTE FASE 2
    └── mesa-premium.conf
```

## ✅ Resultados dos Testes (Fase 1)

### Ambiente de Desenvolvimento - SUCESSO
```bash
# Comando executado
docker compose up -d

# Resultados
✅ API iniciada corretamente
✅ Conectividade com MySQL VPS (mesa_premium_dev)
✅ Tabelas criadas automaticamente: hub_tokens, fixed_income_data, structured_data
✅ Health check: {"status":"healthy","database":"connected"}
✅ Endpoints funcionando: /docs, /api/health, /api/automations
✅ Nginx containerizado funcionando em localhost:80
```

### Bancos MySQL VPS - CONFIGURADOS
```sql
-- Bancos criados e configurados
✅ mesa_premium_dev      - Desenvolvimento (testado)
✅ mesa_premium_staging  - Staging (criado)
✅ mesa_premium_db       - Produção (criado)

-- Usuário: mesa_user com permissões em todos os bancos
```

## Próximos Passos
1. ✅ ~~Executar Fase 1 (estruturação)~~ - CONCLUÍDO
2. ✅ ~~Testar localmente os novos arquivos~~ - SUCESSO
3. 🔄 **ATUAL**: Executar Fase 2 - Configuração Nginx VPS
4. Documentar processo de deploy VPS
5. Remover este arquivo após conclusão completa

## Status Geral: FASE 1 CONCLUÍDA ✅
**Pronto para Fase 2**: Configuração do Nginx no VPS

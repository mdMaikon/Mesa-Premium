# Mesa Premium Web - Projeto de Migração

## 📋 Visão Geral

Migração de automações Python desktop para uma aplicação web Django + React, mantendo a funcionalidade de extração automatizada de tokens do Hub XP.

## 🎯 Plano de Migração - 4 Fases

### **FASE 1: Setup Django Backend** ✅ CONCLUÍDA
- ✅ Estrutura Django com apps: `authentication`, `token_extraction`, `dashboard`, `api`
- ✅ Configuração MySQL Hostinger existente
- ✅ Models para usuários e extensão da estrutura de tokens
- ✅ Admin panels configurados

### **FASE 2: API REST + Background Tasks** 🔄 PRÓXIMA
- [ ] Endpoints para extração de tokens, dashboard, autenticação
- [ ] Implementação Celery + Redis para processamento assíncrono
- [ ] Sistema de usuários com JWT authentication
- [ ] Migração da lógica Selenium para Django services

### **FASE 3: Frontend React** ⏳ PENDENTE
- [ ] Interface para login/gestão de credenciais Hub XP
- [ ] Dashboard em tempo real com status dos tokens
- [ ] Controle das automações via web interface

### **FASE 4: Deploy + Produção** ⏳ PENDENTE
- [ ] Configuração VPS com Docker
- [ ] CI/CD pipeline
- [ ] Monitoramento e logs

## 🏗️ Estrutura Atual do Projeto

```
projeto_mesa/
├── Mesa-Premium/                    # Automações Python originais
│   ├── renovar_token_simplified.py # Script principal de extração
│   ├── requirements.txt             # Dependencies originais
│   └── .env                        # Credenciais banco MySQL
├── backend/                        # Django Backend ✅
│   ├── mesa_premium_web/           # Projeto Django
│   ├── authentication/             # App de usuários
│   ├── token_extraction/           # App de extração de tokens
│   ├── dashboard/                  # App de dashboard
│   ├── api/                        # App de API REST
│   ├── core/                       # Utilitários compartilhados
│   ├── templates/                  # Templates Django
│   ├── static/                     # Arquivos estáticos
│   ├── requirements.txt            # Dependencies Django
│   └── .env                        # Environment variables
└── README.md                       # Este arquivo
```

## 💾 Database

**Configuração atual:**
- **Host**: srv719.hstgr.io (Hostinger MySQL)
- **Database**: u272626296_automacoes
- **User**: u272626296_mesapremium

**Tabelas existentes:**
- `hub_tokens` - Tokens extraídos (já existente)

**Tabelas planejadas:**
- `users` - Usuários da aplicação
- `user_hub_credentials` - Credenciais Hub XP dos usuários
- `token_extraction_logs` - Logs das extrações

## 🔧 Tecnologias

### **Backend (Django)**
- Django 5.2.3
- Django REST Framework
- MySQL Connector Python
- Celery (planejado)
- Selenium (migração)

### **Frontend (React) - Planejado**
- React 18
- Material-UI ou Tailwind CSS
- Axios para API calls
- Socket.io para real-time updates

## 📈 Status Atual - Fase 1 Completa

### ✅ **Concluído**
1. **Estrutura Django criada**
   - 4 apps Django configurados
   - Models User customizado, HubToken, UserHubCredentials
   - Admin panels funcionais
   
2. **Database configurado**
   - Conexão MySQL Hostinger estabelecida
   - Models sincronizados com tabela existente `hub_tokens`
   - Environment variables carregadas

3. **Configurações base**
   - Settings.py configurado para produção
   - Localização PT-BR, timezone São Paulo
   - Static files e templates configurados

### 🎯 **Próximos Passos Imediatos**
1. Criar migrations para as novas tabelas
2. Testar conexão e criação de tabelas no MySQL
3. Implementar serializers DRF
4. Criar endpoints básicos de autenticação

---

## 📝 Log de Desenvolvimento

### 20/06/2025 - Início do Projeto

#### ✅ **Sucessos**
- Django project criado com estrutura de 4 apps
- Conexão MySQL configurada usando `mysql.connector.django`
- Models customizados criados mantendo compatibilidade com tabela existente
- Admin interface configurada para todos os models

#### ⚠️ **Problemas Encontrados**
1. **MySQL Client Installation**
   - **Erro**: `mysqlclient` falhava ao instalar por falta de `pkg-config`
   - **Solução**: Usado `mysql-connector-python` que já estava no projeto original
   - **Engine**: Mudado para `mysql.connector.django`

#### 💡 **Decisões Técnicas**
- Mantido MySQL Hostinger existente para continuidade
- User model customizado usando `AbstractUser` para flexibilidade
- Tabela `hub_tokens` mantida com mesmo nome para compatibilidade
- Adicionado campo `user` nullable para migração gradual

#### 🔍 **Observações**
- Sistema atual funciona apenas localmente
- Necessário instalar Chrome/Chromium para Selenium
- Token extration ainda depende da GUI original
- Database já possui dados que devem ser preservados

#### 📋 **TODOs Próxima Sessão**
1. [ ] Executar `python manage.py makemigrations`
2. [ ] Executar `python manage.py migrate` 
3. [ ] Criar superuser para admin
4. [ ] Testar admin interface
5. [ ] Implementar serializers DRF
6. [ ] Criar view básica de listagem de tokens

---

*Última atualização: 20/06/2025 por Claude*
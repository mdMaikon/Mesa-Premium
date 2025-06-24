# Mesa Premium Web - Projeto de Automação

## 📋 Visão Geral

Projeto de automação para extração de tokens do Hub XP, evoluindo de uma aplicação desktop para uma arquitetura híbrida **FastAPI + PHP**, mantendo a base PHP existente e criando APIs Python para funcionalidades específicas.

## 🎯 Roadmap de Desenvolvimento - FastAPI + PHP

### **FASE 1: FastAPI Core** ✅ CONCLUÍDA - 24/06/2025
- ✅ Migrar `renovar_token_simplified.py` → FastAPI endpoints
- ✅ Configurar estrutura FastAPI com Pydantic models
- ✅ Implementar endpoints essenciais: `/token/extract`, `/token/status`, `/token/history`
- ✅ Manter conexão MySQL Hostinger existente
- ✅ Estrutura completa pronta para testes locais (localhost:8000)
- ✅ **TESTES REAIS CONCLUÍDOS**: Token extraction funcionando 100%
- ✅ **Hub XP Integration**: Login + MFA + Token extraction + Database save

### **FASE 2: PHP Integration** 🚀 EM PROGRESSO
- ✅ Testes FastAPI locais completos (TESTING_GUIDE.md)
- ✅ Logging corrigido e funcionando
- ✅ Token extraction real validado com credenciais Hub XP
- ✅ Seletores Hub XP corrigidos (account, password, MFA)
- ✅ Selenium WebDriver funcionando em WSL
- [ ] Criar funções PHP para consumir APIs FastAPI
- [ ] Integrar formulários PHP com endpoints de extração
- [ ] Dashboard PHP consumindo dados via API
- [ ] Tratamento de erros e timeouts

### **FASE 3: VPS Deployment** ⏳ FUTURO
- [ ] Deploy FastAPI no VPS com Docker
- [ ] Configurar Nginx reverse proxy
- [ ] SSL/TLS para APIs
- [ ] Monitoramento e logs

### **FASE 4: Otimizações** ⏳ FUTURO
- [ ] Background tasks com Celery (opcional)
- [ ] Cache Redis para performance
- [ ] Rate limiting e segurança
- [ ] Monitoring e alertas

## 🏗️ Arquitetura Final - FastAPI + PHP

```
┌─────────────────┐    HTTP API calls    ┌─────────────────┐
│   PHP Website   │ ──────────────────→  │   FastAPI VPS   │
│   (Hostinger)   │                      │                 │
│                 │                      │ • Token Extract │
│ • User Auth     │                      │ • Selenium      │
│ • Dashboard     │                      │ • Background    │
│ • Forms         │                      │ • MySQL Conn    │
└─────────────────┘                      └─────────────────┘
         │                                        │
         └──────────── MySQL Database ────────────┘
                    (Hostinger Shared)
```

### **Estrutura do Projeto**

```
MenuAutomacoes/
├── 🖥️ DESKTOP APP (Atual - Base para migração)
│   ├── renovar_token_simplified.py # Script principal → FastAPI
│   ├── requirements.txt             # Dependencies Python
│   ├── user_config.json            # Config usuário
│   └── .env                        # Credenciais MySQL
│
├── 🚀 FASTAPI (Em desenvolvimento)
│   ├── main.py                     # FastAPI application
│   ├── models/                     # Pydantic models
│   ├── services/                   # Business logic + Selenium
│   ├── database/                   # MySQL connection
│   ├── requirements.txt            # FastAPI dependencies
│   └── Dockerfile                  # Container deployment
│
├── 🗄️ BACKEND (Django - Análise/Ref)
│   └── backend/                    # Django exploration (referência)
│
└── 📋 DOCS
    ├── README.md                   # Este arquivo
    ├── CLAUDE.md                   # Instruções Claude
    └── TESTING_GUIDE.md            # Guia completo de testes
```

## 💾 Database

**Configuração atual:**
- **Host**: srv719.hstgr.io (Hostinger MySQL)

**Tabelas existentes:**
- `hub_tokens` - Tokens extraídos (já existente)

**Tabelas planejadas:**
- `users` - Usuários da aplicação
- `user_hub_credentials` - Credenciais Hub XP dos usuários
- `token_extraction_logs` - Logs das extrações

## 🔧 Stack Tecnológico

### **FastAPI Backend**
- FastAPI 0.104+ (High performance async API)
- Pydantic (Data validation and serialization)
- MySQL Connector Python (Database connectivity)
- Selenium 4.x (Web automation)
- Uvicorn (ASGI server)

### **PHP Frontend** (Existente - Hostinger)
- PHP 8.x (Sistema atual mantido)
- MySQL PDO (Database queries)
- cURL/file_get_contents (API consumption)
- Existing authentication system

### **Infrastructure**
- **Development**: Local testing (localhost:8000)
- **Production**: VPS + Docker containers
- **Database**: MySQL Hostinger (shared)
- **Web Server**: Nginx (reverse proxy)

## 📈 Status Atual

### ✅ **Concluído**
1. **Análise Arquitetural Completa**
   - Decisão: FastAPI + PHP híbrido
   - Roadmap de 4 fases definido
   - Estrutura de projeto planejada
   
2. **Base Desktop Funcional**
   - `renovar_token_simplified.py` funcionando
   - Conexão MySQL Hostinger estabelecida
   - Selenium multi-platform configurado
   - GUI CustomTkinter operacional

3. **Exploração Django** (Referência)
   - Estrutura Django analisada
   - Models e database schema definidos
   - Experiência adquirida para FastAPI

### 🎯 **Status Atual - FASE 1 COMPLETA** ✅
1. ✅ **Estrutura FastAPI** criada e funcional
2. ✅ **Testes locais completos** (ver `TESTING_GUIDE.md`)
3. ✅ **Token extraction real** validado com Hub XP
4. ✅ **Selenium integrado** com WSL/Chrome
5. ✅ **Banco MySQL** funcionando (tokens salvos)

### 🚀 **Próximos Passos - FASE 2 PHP**
1. 🔗 **Criar funções PHP** para consumir APIs FastAPI
2. 📊 **Dashboard PHP** consumindo dados via API
3. 🧪 **Testes integração** PHP → FastAPI
4. 🚀 **Deploy VPS** quando integração testada

---

## 🧠 Decisões Arquiteturais

### **23/06/2025 - Decisão Crítica: FastAPI + PHP vs Django Full Stack**

#### **🤔 Problema**
Cliente possui sistema PHP funcional na Hostinger com autenticação, dashboard e usuários. Questão: integrar com Django ou usar outra abordagem?

#### **⚖️ Opções Analisadas**

1. **Django + PHP Híbrido**
   - ❌ Sessions incompatíveis (PHP vs Django)
   - ❌ Deployment complexo (dois sistemas)
   - ❌ Sincronização de usuários problemática

2. **Django Full Migration**
   - ✅ Stack única Python
   - ❌ Perda investimento PHP existente
   - ❌ Recriar todas funcionalidades

3. **FastAPI + PHP** ⭐ **ESCOLHIDA**
   - ✅ Mantém sistema PHP existente
   - ✅ APIs independentes e escaláveis
   - ✅ Reutiliza 90% código Python
   - ✅ Deploy VPS separado (zero impacto PHP)

#### **🎯 Justificativa da Decisão**

**Por que FastAPI + PHP:**
- **Separation of Concerns**: PHP para UI/users, Python para processing
- **Zero Impacto**: Sistema PHP continua funcionando
- **Performance**: FastAPI assíncrono para Selenium
- **Simplicidade**: APIs REST simples vs Django complexo
- **Timeline**: 3 semanas vs 6+ semanas para outras opções

#### **📐 Arquitetura Final**
```
PHP (Hostinger) → HTTP API calls → FastAPI (VPS) → MySQL (Shared)
```

### **20/06/2025 - Exploração Django (Background Research)**

#### **✅ Sucessos da Análise**
- Django project estruturado com 4 apps
- MySQL connector funcionando
- Models customizados compatíveis
- Admin interface configurada

#### **💡 Aprendizados Aplicados ao FastAPI**
- Database schema bem definido
- Necessidade de async processing
- Importância da API-first approach
- Complexidade desnecessária para casos de uso específicos

#### **🔄 Pivot Decision**
Após análise completa, Django foi descartado em favor do FastAPI por:
- Over-engineering para necessidades específicas
- FastAPI mais apropriado para microservices
- Melhor integração com sistema PHP existente

---

## 📝 Log de Desenvolvimento

### 24/06/2025 - Fase 1 FastAPI COMPLETA ✅

#### ✅ **Concluído - FASE 1**
- ✅ Análise completa de 3 abordagens arquiteturais
- ✅ Decisão fundamentada: FastAPI + PHP
- ✅ Roadmap de 4 fases definido
- ✅ README.md atualizado com nova arquitetura
- ✅ **Estrutura FastAPI completa criada**
- ✅ **Código desktop migrado para FastAPI services**
- ✅ **Endpoints funcionais implementados**
- ✅ **TESTING_GUIDE.md criado e executado**
- ✅ **Testes reais com Hub XP - SUCESSO TOTAL**
- ✅ **Token extraction funcionando 100%**

#### 🔧 **Problemas Resolvidos**
- 🔧 Seletores Hub XP: `name="account"`, `name="password"`
- 🔧 MFA individual fields: `class="G7DrImLjomaOopqdA6D6dA=="`
- 🔧 WebDriverWait para campos MFA
- 🔧 Token ID correto: `cursor.lastrowid`
- 🔧 API validation: `token_id is None`

#### 🚀 **Próxima Fase - PHP Integration**
FastAPI validado, testado e pronto para integração PHP.

---

### 20/06/2025 - Exploração Inicial (Django Research)

#### ✅ **Sucessos**
- Django project criado para análise
- Conexão MySQL Hostinger estabelecida
- Models e schema definidos
- Experiência adquirida para FastAPI

#### 💡 **Decisões Técnicas Transferidas**
- MySQL Hostinger mantido
- Tabela `hub_tokens` preservada
- Environment variables pattern
- Multi-platform support requirement

---

*Última atualização: 23/06/2025 por Claude*
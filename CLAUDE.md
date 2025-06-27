# CLAUDE.md

Este arquivo fornece orientações para o Claude Code (claude.ai/code) quando trabalhando com código neste repositório.

## Visão Geral do Projeto

Este é um projeto de automação Python que oferece múltiplas funcionalidades integradas através de uma API FastAPI moderna:

1. **Extração de Tokens Hub XP**: Extrai tokens de autenticação do Hub XP (https://hub.xpi.com.br/) usando Selenium WebDriver
2. **Processamento de Renda Fixa**: Automatiza download e processamento de dados de renda fixa do Hub XP
3. **Armazenamento Centralizado**: Todos os dados são armazenados em banco de dados MySQL hospedado na Hostinger
4. **Interface Moderna**: GUI construída com CustomTkinter e API REST com FastAPI
5. **Suporte Multiplataforma**: Execução em Windows, Linux e WSL

## Comandos Comuns

### Configuração do Ambiente (Poetry)
```bash
# Instalar dependências do projeto
poetry install

# Instalar apenas dependências de produção
poetry install --only main

# Instalar apenas dependências de desenvolvimento
poetry install --only dev

# Ativar ambiente virtual
poetry shell

# Configurar ambiente (Windows - opcional)
setup_menu.bat

# Instalar Chrome/ChromeDriver (WSL/Linux)
chmod +x install_chrome_wsl.sh
./install_chrome_wsl.sh
```

### Pre-commit Hooks (Qualidade de Código)
```bash
# Instalar hooks do pre-commit
poetry run task pre-commit-install

# Executar hooks em todos os arquivos
poetry run task pre-commit-run

# Verificação de segurança com Bandit
poetry run task security

# Commitizen para commits padronizados
poetry run cz commit
```

### Executando as Aplicações

#### API FastAPI (Recomendado)
```bash
# Executar API completa com Poetry
poetry run task dev

# Ou executar diretamente
poetry run uvicorn fastapi.main:app --host 0.0.0.0 --port 8000 --reload

# Para Docker: Gerar requirements.txt e build
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes
export COMPOSE_BAKE=true  # Para performance otimizada
docker compose build
docker compose up -d

# Acesso à documentação: http://localhost:8000/docs (Poetry) ou http://localhost/docs (Docker)
```

#### Desenvolvimento e Testes
```bash
# Executar testes
poetry run task test

# Executar testes com cobertura
poetry run task test-cov

# Formatar código
poetry run task format

# Verificar lint
poetry run task lint

# Corrigir problemas de lint
poetry run task lint-fix

# Executar verificação completa (lint + format + tests)
poetry run task check
```

#### GUI Tradicional (Legacy)
```bash
# Aplicação principal GUI
poetry run python renovar_token.py

# Importar como módulo
poetry run python -c "from renovar_token import extract_hub_token; extract_hub_token()"
```

### Operações do Banco de Dados

#### Tabela `hub_tokens` (Tokens de Autenticação)
- `id` (INT, AUTO_INCREMENT, PRIMARY KEY)
- `user_login` (VARCHAR(255), indexado)
- `token` (TEXT)
- `expires_at` (DATETIME, indexado)
- `extracted_at` (DATETIME)
- `created_at` (TIMESTAMP)

#### Tabela `fixed_income_data` (Dados de Renda Fixa)
- `id` (INT, AUTO_INCREMENT, PRIMARY KEY)
- `data_coleta` (DATETIME, indexado)
- `ativo` (VARCHAR(255), indexado)
- `instrumento` (VARCHAR(100))
- `duration` (DECIMAL(10,6))
- `indexador` (VARCHAR(100), indexado)
- `juros` (VARCHAR(50))
- `primeira_data_juros` (DATE)
- `isento` (VARCHAR(10))
- `rating` (VARCHAR(50), indexado)
- `vencimento` (DATE, indexado)
- `tax_min` (VARCHAR(255))
- `tax_min_clean` (DECIMAL(8,4))
- `roa_aprox` (DECIMAL(8,4))
- `taxa_emissao` (DECIMAL(8,4))
- `publico` (VARCHAR(100))
- `publico_resumido` (VARCHAR(10))
- `emissor` (VARCHAR(255), indexado)
- `cupom` (VARCHAR(100))
- `classificar_vencimento` (TEXT)
- `created_at` / `updated_at` (TIMESTAMP)

## Arquitetura

### API FastAPI (`/fastapi/`)

#### Estrutura da API
```
fastapi/
├── main.py                 # Aplicação principal FastAPI
├── routes/                 # Endpoints da API
│   ├── health.py          # Health checks
│   ├── tokens.py          # Gerenciamento de tokens
│   ├── automations.py     # Lista de automações
│   └── fixed_income.py    # Processamento renda fixa
├── services/              # Lógica de negócio
│   ├── hub_token_service.py    # Extração de tokens
│   └── fixed_income_service.py # Processamento renda fixa
├── models/                # Modelos de dados
├── database/              # Conexão com banco
└── utils/                 # Utilitários
```

#### Endpoints Disponíveis

**Tokens Hub XP:**
- `POST /api/token/extract` - Extrair token via Selenium
- `GET /api/token/status/{user_login}` - Status do token
- `GET /api/token/history/{user_login}` - Histórico de tokens

**Renda Fixa:**
- `POST /api/fixed-income/process` - Processar dados (assíncrono)
- `GET /api/fixed-income/process-sync` - Processar dados (síncrono)
- `GET /api/fixed-income/status` - Status do processamento
- `GET /api/fixed-income/stats` - Estatísticas dos dados
- `GET /api/fixed-income/categories` - Categorias disponíveis
- `DELETE /api/fixed-income/clear` - Limpar todos os dados

**Geral:**
- `GET /api/health` - Status da aplicação
- `GET /api/automations` - Lista de automações disponíveis

### Componentes Principais

#### Serviço de Tokens: `HubTokenService`
- **Detecção de Ambiente**: Detecta automaticamente Windows, Linux ou WSL
- **Gerenciamento WebDriver**: Configura Chrome/Chromium com opções apropriadas para cada plataforma
- **Fluxo de Autenticação**: Gerencia login, MFA e extração de token
- **Integração com Banco**: Operações MySQL com pool de conexões

#### Serviço de Renda Fixa: `FixedIncomeService`
- **Extração de Token**: Busca tokens válidos automaticamente do banco
- **Download de Dados**: Baixa dados das categorias CP, EB e TPF do Hub XP
- **Processamento**: Aplica filtros, regras de negócio e transformações
- **Armazenamento**: Persiste dados processados no MySQL

#### Métodos Principais (Tokens)
- `extract_token()`: Extração completa de token via Selenium
- `get_token_status()`: Verifica status e validade de tokens
- `_perform_login()`: Login automatizado no Hub XP com suporte MFA
- `_extract_token_from_browser()`: Extração de token do localStorage

#### Métodos Principais (Renda Fixa)
- `process_and_store_data()`: Processamento completo de todas as categorias
- `get_valid_token()`: Busca token válido automaticamente do banco
- `download_and_process_category()`: Download e processamento por categoria
- `apply_ntn_rules()`: Aplica regras específicas para títulos NTN
- `create_new_columns()`: Cria colunas derivadas (Emissor, Cupom, etc.)

### Configuração do Banco de Dados
Credenciais do banco são carregadas do arquivo `.env`:
- Host: Servidor MySQL da Hostinger
- Pool de conexões e gerenciamento de timeout
- Criação automática de tabelas e rotação de tokens (remove tokens antigos por usuário)

### Suporte Multiplataforma
A aplicação adapta comportamento baseado no ambiente detectado:
- **Windows**: Usa caminhos padrão de instalação do Chrome
- **WSL/Linux**: Prefere Chromium, inclui configurações headless adicionais
- **ChromeDriver**: Auto-detecção com caminhos de fallback

### Framework GUI
- **CustomTkinter**: Interface moderna e temática
- **Esquema de Cores**: Paleta azul corporativa (`#071d5c`, `#810b0b`, `#3a75ce`)
- **Design Responsivo**: Centralização e dimensionamento automático de janelas
- **Experiência do Usuário**: Rastreamento de progresso, notificações de sucesso, persistência de credenciais

## Arquivos de Configuração

### `.env`
Contém credenciais MySQL da Hostinger e configurações de conexão. Criado automaticamente pelo `setup_menu.bat` ou manualmente.

### `user_config.json`
Armazena preferências do usuário (último login usado) para conveniência.

### `requirements.txt`
**IMPORTANTE**: Gerado automaticamente via Poetry export para compatibilidade Docker.
```bash
# Gerar requirements.txt para Docker
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes
```

Dependências principais (gerenciadas via Poetry):
- `selenium`: Automação web
- `mysql-connector-python`: Conectividade com banco de dados
- `fastapi`: Framework web moderno para APIs
- `uvicorn`: Servidor ASGI para FastAPI
- `pandas`: Manipulação e análise de dados
- `requests`: Cliente HTTP para APIs
- `pydantic`: Validação de dados e serialização
- `python-dotenv`: Gerenciamento de variáveis de ambiente

## Exemplos de Uso da API

### Extração de Token
```bash
# Extrair token do Hub XP
curl -X POST "http://localhost:8000/api/token/extract" \
  -H "Content-Type: application/json" \
  -d '{"user_login": "usuario", "password": "senha", "mfa_code": "123456"}'

# Verificar status do token
curl "http://localhost:8000/api/token/status/usuario"
```

### Processamento de Renda Fixa
```bash
# Processar dados de renda fixa (assíncrono)
curl -X POST "http://localhost:8000/api/fixed-income/process"

# Verificar status do processamento
curl "http://localhost:8000/api/fixed-income/status"

# Obter estatísticas dos dados
curl "http://localhost:8000/api/fixed-income/stats"

# Listar categorias disponíveis
curl "http://localhost:8000/api/fixed-income/categories"
```

### Automações Disponíveis
```bash
# Listar todas as automações
curl "http://localhost:8000/api/automations"

# Health check da aplicação
curl "http://localhost:8000/api/health"
```

## Notas de Desenvolvimento

### Configuração WebDriver
A aplicação inclui configuração sofisticada do WebDriver que manipula:
- Detecção de caminho binário para Chrome/Chromium
- Verificação de compatibilidade do ChromeDriver
- Otimização específica por ambiente (modo headless para WSL/Linux)
- Mecanismos de fallback para dependências ausentes

### Build e Deploy com Poetry + Docker
```bash
# 1. Preparar ambiente Poetry
poetry install --only=main

# 2. Gerar requirements.txt para Docker
poetry export -f requirements.txt --output fastapi/requirements.txt --without-hashes

# 3. Build com performance otimizada
export COMPOSE_BAKE=true
docker compose build

# 4. Deploy
docker compose up -d
```

### Gerenciamento de Tokens
- Tokens são automaticamente rotacionados (tokens antigos deletados antes de inserir novos)
- Timestamps de expiração são preservados do Hub XP
- Extração de token usa inspeção do localStorage via execução JavaScript

### Tratamento de Erros
- Log abrangente em `hub_extractor.log`
- Mensagens de erro específicas por plataforma para dependências ausentes
- Degradação graciosa e relatórios de erro amigáveis ao usuário

### Regras de Negócio - Renda Fixa

#### Filtros Aplicados
1. **Filtro IGP-M**: Remove todos os ativos com indexador IGP-M
2. **Filtro de Juros**: Mantém apenas ativos com juros "Mensal" ou "Semestral"

#### Regras Específicas
1. **NTN Rating**: Todos os ativos que começam com "NTN" recebem Rating "AAA"
2. **NTN-F Taxa**: Ativos "NTN-F" recebem Taxa de Emissão de 10%
3. **Rating Vazio**: Ratings vazios ou inválidos tornam-se "Sem Rating"

#### Colunas Derivadas
- **Público Resumido**: R (Geral), Q (Qualificado), P (Profissional)
- **Emissor**: Extrai emissor removendo prefixos (CDB, CRI, etc.) e sufixos
- **Cupom**: Para juros semestrais, calcula meses de pagamento baseado no vencimento
- **Classificar Vencimento**: Categoriza por anos até vencimento ([1 Ano], [2 Anos], etc.)

#### Transformações de Dados
- **Tax.Mín_Clean**: Versão numérica de Tax.Mín para cálculos
- **Percentuais**: ROA e Taxa de Emissão convertidos para formato decimal
- **Datas**: Normalizadas para formato MySQL DATETIME/DATE

### Considerações de Segurança
- Credenciais do banco armazenadas em `.env` (no gitignore)
- Senhas mascaradas em logs e UI
- Tokens manipulados com segurança sem armazenamento persistente no código
- API protegida com CORS configurável
- Logs detalhados para auditoria de operações

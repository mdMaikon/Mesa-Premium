# Mudanças no Ambiente de Desenvolvimento

## Objetivo
Implementar boas práticas de desenvolvimento Python no projeto MenuAutomacoes:
- Usar pipx para ferramentas globais
- Migrar para Poetry para gerenciamento de dependências
- Definir versões mínima e máxima do Python

## Estado Atual (✅ IMPLEMENTADO)
- ✅ Python 3.12.3 instalado
- ✅ Pipx 1.7.1 instalado e funcionando
- ✅ Poetry 2.1.3 instalado e configurado
- ✅ pyproject.toml criado com todas as dependências
- ✅ Ambiente Poetry funcionando
- ✅ Ferramentas de desenvolvimento integradas (Ruff, Taskipy)
- ✅ CLAUDE.md atualizado com novos comandos

## Plano de Implementação

### 1. Instalação do Pipx
```bash
# Instalar pipx
python -m pip install --user pipx
python -m pipx ensurepath

# Reiniciar terminal ou executar:
source ~/.bashrc
```

### 2. Instalação de Ferramentas Globais via Pipx
```bash
# Ferramentas essenciais
pipx install poetry
pipx install black
pipx install flake8
pipx install pytest
pipx install pip-audit
pipx install mypy
```

### 3. Migração para Poetry

#### 3.1 Inicializar Poetry
```bash
poetry init
# Ou criar pyproject.toml manualmente
```

#### 3.2 Estrutura do pyproject.toml (✅ IMPLEMENTADO)
```toml
[tool.poetry]
name = "menu-automacoes"
version = "1.0.0"
description = "Sistema de automação para Hub XP e processamento de renda fixa"
authors = ["Maikon Silva <maikondp0@gmail.com>"]
readme = "README.md"
packages = [{include = "fastapi"}, {include = "services"}]

[tool.poetry.dependencies]
python = "^3.12,<4.0"  # Atualizado para Python 3.12+
# FastAPI Core
fastapi = "^0.115.6"
uvicorn = {extras = ["standard"], version = "^0.34.0"}
pydantic = "^2.10.4"

# Database
mysql-connector-python = "^9.3.0"
python-dotenv = "^1.1.0"

# Web Automation
selenium = "^4.33.0"

# Data Processing
pandas = "^2.3.0"

# HTTP Client
requests = "^2.32.4"
httpx = "^0.28.1"

# Utils
python-dateutil = "^2.9.0"
pytz = "^2025.2"

[tool.poetry.group.dev.dependencies]
pytest = "^8.4.1"
pytest-cov = "^6.2.1"
pytest-asyncio = "^1.0.0"
pytest-mock = "^3.14.1"
ruff = "^0.12.0"  # Substitui Black + Flake8
taskipy = "^1.14.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

# Configurações Ruff (substitui Black + Flake8)
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501", "B008", "C901"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# Configurações Pytest
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]

# Configurações Coverage
[tool.coverage.run]
source = ["fastapi", "services"]
omit = ["*/tests/*", "*/test_*", "*/__pycache__/*"]

# Tasks do Taskipy
[tool.taskipy.tasks]
test = "pytest"
test-cov = "pytest --cov=fastapi --cov=services --cov-report=html --cov-report=term"
lint = "ruff check ."
format = "ruff format ."
format-check = "ruff format --check ."
lint-fix = "ruff check --fix ."
dev = "uvicorn fastapi.main:app --reload --host 0.0.0.0 --port 8000"
check = "ruff check . && ruff format --check . && pytest"
```

### 4. Processo de Migração

#### 4.1 Backup dos requirements atuais
```bash
cp requirements.txt requirements_backup.txt
cp fastapi/requirements.txt fastapi/requirements_backup.txt
```

#### 4.2 Migrar dependências
```bash
# No diretório raiz
poetry add $(cat requirements.txt | grep -v "^#" | tr '\n' ' ')
poetry add --group dev $(cat fastapi/requirements.txt | grep -E "pytest|black|flake8" | tr '\n' ' ')
```

#### 4.3 Criar ambiente virtual Poetry
```bash
poetry install
poetry shell  # Ativar ambiente virtual
```

### 5. Atualização de Scripts e Documentação

#### 5.1 Atualizar CLAUDE.md
- Adicionar comandos Poetry
- Atualizar instruções de setup
- Documentar grupos de dependências

#### 5.2 Atualizar scripts de setup
- `setup_menu.bat` para Windows
- Criar `setup_poetry.sh` para Linux/WSL

#### 5.3 Atualizar Docker
- Modificar Dockerfile para usar Poetry
- Atualizar docker-compose.yml se necessário

### 6. Comandos Poetry Essenciais

```bash
# Gestão do ambiente
poetry shell              # Ativar ambiente virtual
poetry install            # Instalar dependências
poetry install --only dev # Instalar apenas dev
poetry install --only security # Instalar apenas security

# Gestão de dependências
poetry add package         # Adicionar dependência
poetry add --group dev package # Adicionar dependência dev
poetry remove package      # Remover dependência
poetry update             # Atualizar todas as dependências
poetry show               # Listar dependências

# Execução
poetry run python script.py # Executar script
poetry run uvicorn main:app  # Executar FastAPI
poetry run pytest          # Executar testes
```

### 7. Benefícios Esperados

- **Isolamento**: Ambientes virtuais automáticos
- **Reprodutibilidade**: Lock file garante versões exatas
- **Organização**: Grupos de dependências (dev, prod, security)
- **Segurança**: Melhor controle de versões vulneráveis
- **Performance**: Resolução de dependências mais eficiente
- **Ferramentas**: Pipx mantém ferramentas globais separadas

### 8. Checklist de Implementação

- [x] Instalar pipx
- [x] Instalar ferramentas via pipx
- [x] Criar pyproject.toml
- [x] Migrar dependências
- [x] Testar ambiente Poetry
- [x] Atualizar documentação (CLAUDE.md)
- [x] Configurar Ruff (substitui Black + Flake8)
- [x] Configurar Taskipy para automação
- [x] Testar pipeline completo
- [ ] Atualizar scripts de deploy
- [ ] Remover requirements.txt antigos (após validação completa)

## Notas Importantes

1. **Compatibilidade**: Manter suporte para Python 3.10+ (Ubuntu 22.04 LTS)
2. **Docker**: Adaptar Dockerfile para usar Poetry
3. **CI/CD**: Atualizar scripts de deploy
4. **Backup**: Manter requirements.txt como backup durante transição
5. **Testes**: Validar todas as funcionalidades após migração

## Status da Implementação ✅

**MIGRAÇÃO CONCLUÍDA COM SUCESSO!**

### ✅ Implementado:
1. ✅ Pipx 1.7.1 instalado e configurado
2. ✅ Poetry 2.1.3 instalado e funcionando
3. ✅ pyproject.toml criado com todas as dependências
4. ✅ Dependências migradas e organizadas em grupos
5. ✅ Ruff configurado (substitui Black + Flake8)
6. ✅ Taskipy configurado para automação de tarefas
7. ✅ Ambiente virtual Poetry funcionando
8. ✅ CLAUDE.md atualizado com novos comandos
9. ✅ Código formatado e lint aplicado

### 🎯 Comandos principais agora disponíveis:
```bash
# Desenvolvimento
poetry run task dev          # Executar FastAPI
poetry run task test         # Executar testes
poetry run task lint         # Verificar código
poetry run task format      # Formatar código
poetry run task check       # Verificação completa

# Gestão de dependências
poetry add package           # Adicionar dependência
poetry add --group dev package  # Adicionar dep de desenvolvimento
```

### 📋 Próximas melhorias opcionais:
1. Atualizar scripts de deploy para usar Poetry
2. Configurar CI/CD com Poetry
3. Remover requirements.txt antigos após validação completa
4. Configurar pre-commit hooks com Ruff

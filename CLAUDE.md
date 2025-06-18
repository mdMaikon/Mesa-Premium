# CLAUDE.md

Este arquivo fornece orientações para o Claude Code (claude.ai/code) quando trabalhando com código neste repositório.

## Visão Geral do Projeto

Este é um projeto de automação Python que extrai tokens de autenticação do Hub XP (https://hub.xpi.com.br/) usando Selenium WebDriver e os armazena em um banco de dados MySQL hospedado na Hostinger. O projeto possui uma GUI moderna construída com CustomTkinter e suporta execução multiplataforma (Windows, Linux, WSL).

## Comandos Comuns

### Configuração do Ambiente
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente (Windows)
setup_menu.bat

# Instalar Chrome/ChromeDriver (WSL/Linux)
chmod +x install_chrome_wsl.sh
./install_chrome_wsl.sh
```

### Executando a Aplicação
```bash
# Aplicação principal
python renovar_token.py

# Importar como módulo
python -c "from renovar_token import extract_hub_token; extract_hub_token()"
```

### Operações do Banco de Dados
A aplicação cria automaticamente a tabela `hub_tokens` com a seguinte estrutura:
- `id` (INT, AUTO_INCREMENT, PRIMARY KEY)
- `user_login` (VARCHAR(255), indexado)
- `token` (TEXT)
- `expires_at` (DATETIME, indexado)
- `extracted_at` (DATETIME)
- `created_at` (TIMESTAMP)

## Arquitetura

### Componentes Principais

#### Classe Principal: `HubXPTokenExtractor`
- **Detecção de Ambiente**: Detecta automaticamente Windows, Linux ou WSL
- **Gerenciamento WebDriver**: Configura Chrome/Chromium com opções apropriadas para cada plataforma
- **Fluxo de Autenticação**: Gerencia login, MFA e extração de token
- **Integração com Banco**: Operações MySQL com pool de conexões
- **Interface GUI**: Interface moderna baseada em CustomTkinter

#### Métodos Principais
- `detect_environment()`: Auto-detecta ambiente de execução
- `get_chrome_binary_path()` / `get_chromedriver_path()`: Configuração específica do navegador por plataforma
- `get_credentials()`: Coleta de credenciais via GUI com persistência de configuração do usuário
- `perform_login()`: Login automatizado no Hub XP com suporte MFA
- `extract_token()`: Extração de token do localStorage
- `save_token_to_db()`: Operações do banco de dados MySQL

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
Dependências principais:
- `selenium`: Automação web
- `mysql-connector-python`: Conectividade com banco de dados
- `customtkinter`: Framework GUI moderno
- `python-dotenv`: Gerenciamento de variáveis de ambiente
- `pillow`: Manipulação de imagens para ícones

## Notas de Desenvolvimento

### Configuração WebDriver
A aplicação inclui configuração sofisticada do WebDriver que manipula:
- Detecção de caminho binário para Chrome/Chromium
- Verificação de compatibilidade do ChromeDriver
- Otimização específica por ambiente (modo headless para WSL/Linux)
- Mecanismos de fallback para dependências ausentes

### Gerenciamento de Tokens
- Tokens são automaticamente rotacionados (tokens antigos deletados antes de inserir novos)
- Timestamps de expiração são preservados do Hub XP
- Extração de token usa inspeção do localStorage via execução JavaScript

### Tratamento de Erros
- Log abrangente em `hub_token.log`
- Mensagens de erro específicas por plataforma para dependências ausentes
- Degradação graciosa e relatórios de erro amigáveis ao usuário

### Considerações de Segurança
- Credenciais do banco armazenadas em `.env` (no gitignore)
- Senhas mascaradas em logs e UI
- Tokens manipulados com segurança sem armazenamento persistente no código
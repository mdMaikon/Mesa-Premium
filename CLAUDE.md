# CLAUDE.md

Este arquivo fornece orientações para o Claude Code (claude.ai/code) quando trabalhando com código neste repositório.

## Visão Geral do Projeto

Este é um projeto de automação Python profissional que extrai tokens de autenticação do Hub XP (https://hub.xpi.com.br/) usando Selenium WebDriver e os armazena em um banco de dados MySQL hospedado na Hostinger. O projeto possui uma arquitetura modular baseada em princípios de Clean Architecture, com uma GUI moderna construída com CustomTkinter e suporta execução multiplataforma (Windows, Linux, WSL).

### Arquitetura Modular Implementada

O projeto foi refatorado de uma classe monolítica (1047 linhas) para uma arquitetura modular distribuída em 5 componentes especializados:

- **UIConfig**: Configurações centralizadas de UI (cores, fontes, constantes)
- **MessageManager**: Gerenciamento de mensagens e sistema de logs
- **ExecutionManager**: Coordenação da execução de automações
- **UIManager**: Criação e gerenciamento da interface do usuário
- **MenuAutomacoes**: Orquestração principal (reduzida para 280 linhas)

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
# Interface principal do menu
python menu_principal.py

# Extração direta de token
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

#### 1. **UIConfig** (`ui_config.py`)
- **Configurações de UI**: Cores, fontes e constantes centralizadas
- **Paleta de Cores**: Esquema corporativo (`#071d5c`, `#810b0b`, `#3a75ce`)
- **Padronização**: Estilos consistentes em toda a aplicação

#### 2. **MessageManager** (`message_manager.py`)
- **Sistema de Logs**: Controle de mensagens com tipos (info, success, error, warning)
- **Auto-scroll**: Navegação automática para mensagens recentes
- **Exportação**: Funcionalidade de exportar logs
- **Controle de Volume**: Limitação automática de quantidade de mensagens

#### 3. **ExecutionManager** (`execution_manager.py`)
- **Coordenação de Automações**: Execução via AutomacaoManager
- **Gerenciamento de Token**: Execução específica de renovação de token
- **Controle de Processos**: Monitoramento de execuções ativas
- **Callbacks**: Sistema de retorno para atualização da UI

#### 4. **UIManager** (`ui_manager.py`)
- **Interface Completa**: Criação e gerenciamento da GUI
- **Cards Dinâmicos**: Sistema de cards para automações
- **Estados Visuais**: Controle de seleção e feedback visual
- **Atalhos**: Sistema de atalhos de teclado integrado

#### 5. **MenuAutomacoes** (`menu_principal.py`)
- **Orquestração**: Coordenação entre todos os managers
- **Integração**: Configuração de callbacks e comunicação entre componentes
- **Simplicidade**: Classe principal reduzida de 1047 para 280 linhas

#### 6. **HubXPTokenExtractor** (`renovar_token.py`)
- **Detecção de Ambiente**: Detecta automaticamente Windows, Linux ou WSL
- **Gerenciamento WebDriver**: Configura Chrome/Chromium com opções apropriadas para cada plataforma
- **Fluxo de Autenticação**: Gerencia login, MFA e extração de token
- **Integração com Banco**: Operações MySQL com pool de conexões

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
- **Arquitetura Modular**: UI gerenciada pelo UIManager com configurações centralizadas
- **Esquema de Cores**: Paleta azul corporativa (`#071d5c`, `#810b0b`, `#3a75ce`)
- **Design Responsivo**: Centralização e dimensionamento automático de janelas
- **Sistema de Mensagens**: MessageManager para logs e notificações
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

## Benefícios da Arquitetura Modular

### Manutenibilidade
- Código organizado por responsabilidades específicas
- Fácil localização e correção de bugs
- Adição de novas funcionalidades simplificada

### Testabilidade
- Managers independentes podem ser testados isoladamente
- Mocking e injeção de dependências facilitados
- Cobertura de testes mais eficiente

### Reutilização
- Managers podem ser reutilizados em outras partes do sistema
- Componentes de UI padronizados através do UIConfig
- Configurações centralizadas

### Escalabilidade
- Fácil adição de novos tipos de mensagem no MessageManager
- Extensão de funcionalidades de execução no ExecutionManager
- Novos estilos e temas através do UIConfig

## Estrutura de Arquivos Refatorada

```
/MenuAutomacoes/
├── menu_principal.py          # Orquestração principal (280 linhas)
├── ui_config.py              # Configurações centralizadas da UI
├── message_manager.py        # Gerenciador de mensagens e logs
├── execution_manager.py      # Gerenciador de execução de automações
├── ui_manager.py            # Gerenciador da interface do usuário
├── renovar_token.py         # Extrator de tokens Hub XP
└── ...outros arquivos existentes
```
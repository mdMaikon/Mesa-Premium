# CLAUDE.md

Este arquivo fornece orientações para o Claude Code (claude.ai/code) quando trabalhando com código neste repositório.

## Visão Geral do Projeto

Este é um projeto de automação Python **enterprise-grade** que extrai tokens de autenticação do Hub XP (https://hub.xpi.com.br/) usando Selenium WebDriver e os armazena em um banco de dados MySQL hospedado na Hostinger. O projeto possui uma **arquitetura moderna** baseada em **CQRS Pattern**, **DI Container** e princípios de Clean Architecture, com uma GUI moderna construída com CustomTkinter e suporta execução multiplataforma (Windows, Linux, WSL).

### **Padrões Arquiteturais Implementados:**
- ✅ **CQRS (Command Query Responsibility Segregation)** - Separação entre operações de escrita e leitura
- ✅ **Dependency Injection Container** - Desacoplamento máximo entre componentes  
- ✅ **Mediator Pattern** - Orquestração centralizada via CQRSMediator
- ✅ **Registry Pattern** - Registro seguro de automações e serviços
- ✅ **Clean Architecture** - Separação clara de responsabilidades por camadas

### Arquitetura Enterprise Implementada

O projeto evoluiu de uma classe monolítica (1047 linhas) para uma **arquitetura enterprise** com padrões modernos distribuída em múltiplas camadas:

#### **Camada de Apresentação:**
- **UIConfig**: Configurações centralizadas de UI (cores, fontes, constantes)
- **UIManager**: Criação e gerenciamento da interface do usuário
- **MessageManager**: Gerenciamento de mensagens e sistema de logs

#### **Camada de Aplicação (CQRS):**
- **Commands**: Operações de escrita (`ExecuteAutomationCommand`, `ExecuteTokenRenewalCommand`)
- **Queries**: Operações de leitura (`GetActiveProcessesCountQuery`, `IsProcessActiveQuery`)  
- **Handlers**: Processadores especializados (`ExecuteAutomationCommandHandler`, `ProcessStatusQueryHandler`)
- **Mediator**: Orquestração centralizada (`CQRSMediator`)

#### **Camada de Infraestrutura:**
- **DIContainer**: Injeção de dependência com detecção de ciclos (`di_container.py`)
- **ServiceRegistry**: Configuração centralizada de serviços (`service_registry.py`)
- **ExecutionManagerCQRS**: Nova implementação baseada em CQRS (`execution_manager_cqrs.py`)
- **AutomationRegistry**: Sistema seguro de registro de automações (`automation_registry.py`)
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
# Interface principal do menu (nova arquitetura CQRS)
python menu_principal.py

# Extração direta de token
python renovar_token.py

# Importar como módulo
python -c "from renovar_token import extract_hub_token; extract_hub_token()"

# Testar DI Container
python -c "from service_registry import get_configured_container; print('DI OK!')"

# Executar testes unitários
python test_di_container.py
python test_cqrs.py

# Testar CQRS Mediator
python -c "from execution_manager_cqrs import ExecutionManagerCQRS; print('CQRS OK!')"
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

## Estrutura de Arquivos Enterprise

```
/MenuAutomacoes/
# Camada de Apresentação
├── menu_principal.py          # Orquestração principal (280 linhas)
├── ui_config.py              # Configurações centralizadas da UI
├── ui_manager.py            # Gerenciador da interface do usuário
├── message_manager.py        # Gerenciador de mensagens e logs

# Camada de Aplicação (CQRS)
├── cqrs_commands.py          # Commands (operações de escrita)
├── cqrs_queries.py           # Queries (operações de leitura)
├── cqrs_handlers.py          # Handlers especializados
├── cqrs_mediator.py          # Mediator para orquestração

# Camada de Infraestrutura
├── di_container.py           # DI Container com detecção de ciclos
├── service_registry.py       # Registro centralizado de serviços
├── execution_manager_cqrs.py # Nova implementação CQRS
├── execution_manager.py      # Implementação legacy (compatibilidade)
├── automation_registry.py    # Registro seguro de automações
├── secure_logging.py         # Sistema de logging seguro

# Funcionalidades de Negócio
├── renovar_token.py         # Extrator de tokens Hub XP
├── renovar_token_simplified.py # Versão simplificada
├── database.py              # Gerenciador de banco MySQL
├── path_manager.py          # Gerenciador de caminhos
├── automacao_manager.py     # Gerenciador de automações

# Testes
├── test_di_container.py     # Testes do DI Container (11 testes)
├── test_cqrs.py            # Testes do CQRS (18 testes)

# Configuração
├── requirements.txt         # Dependências
├── setup_menu.bat          # Setup Windows
└── install_chrome_wsl.sh   # Setup Linux/WSL
```

## Migração de Automações para Nova Arquitetura

### Como Migrar Automações Existentes

Com a nova arquitetura CQRS implementada, as automações devem seguir os padrões enterprise:

#### **1. Criação via Commands/Queries:**
```python
# Para automações que modificam estado (Commands)
from cqrs_commands import ExecuteAutomationCommand
from cqrs_mediator import CQRSMediator

def executar_nova_automacao():
    mediator = CQRSMediator()
    command = ExecuteAutomationCommand(
        automation_name="minha_nova_automacao",
        parameters={"param1": "valor"}
    )
    result = mediator.send_command(command)
    return result

# Para consultas de status (Queries)  
from cqrs_queries import GetActiveProcessesCountQuery

def verificar_processos_ativos():
    mediator = CQRSMediator()
    query = GetActiveProcessesCountQuery()
    result = mediator.send_query(query)
    return result.data
```

#### **2. Registro via DI Container:**
```python
# service_registry.py - adicionar nova automação
def configure_new_automation(container: DIContainer):
    container.register_transient(
        MinhaNovaAutomacao,
        lambda: MinhaNovaAutomacao(
            container.resolve(DatabaseManager),
            container.resolve(PathManager)
        )
    )
```

#### **3. Handler Especializado:**
```python
# handlers/minha_automacao_handler.py
class MinhaAutomacaoHandler(CommandHandler):
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def handle(self, command: ExecuteMinhaAutomacaoCommand) -> CommandResult:
        try:
            # Lógica da automação
            resultado = self._executar_logica(command.parameters)
            
            return CommandResult(
                success=True,
                message="Automação concluída",
                data=resultado
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Erro: {str(e)}"
            )
```

### **Benefícios da Nova Arquitetura para Automações:**

1. **Testabilidade Máxima:** Cada automação pode ser testada isoladamente
2. **Desacoplamento:** Dependências injetadas automaticamente via DI
3. **Padronização:** Todas seguem o mesmo padrão Command/Query
4. **Monitoramento:** Execuções rastreadas automaticamente
5. **Escalabilidade:** Fácil adição de novas automações
6. **Manutenibilidade:** Lógica de negócio isolada em handlers

### **Estrutura Recomendada para Novas Automações:**
```
automacoes/
├── commands/
│   └── execute_minha_automacao_command.py
├── queries/  
│   └── get_minha_automacao_status_query.py
├── handlers/
│   ├── minha_automacao_command_handler.py
│   └── minha_automacao_query_handler.py
└── entities/
    └── minha_automacao_entity.py
```
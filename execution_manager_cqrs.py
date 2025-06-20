"""
Execution Manager CQRS - Versão refatorada usando CQRS Pattern
Separa responsabilidades entre commands (write) e queries (read)
"""

from typing import Dict, Any, Optional, Callable

# Importar CQRS components
from cqrs_mediator import CQRSMediator
from cqrs_commands import (
    ExecuteAutomationCommand, ExecuteTokenRenewalCommand, 
    SetUICallbacksCommand, CommandResult
)
from cqrs_queries import (
    GetActiveProcessesCountQuery, IsProcessActiveQuery,
    GetLastExecutionQuery, QueryResult
)
from cqrs_handlers import (
    ExecuteAutomationCommandHandler, ExecuteTokenRenewalCommandHandler,
    ProcessStatusQueryHandler, ExecutionInfoQueryHandler
)

# Importar managers necessários
from automacao_manager import AutomacaoManager
from database import DatabaseManager
from path_manager import PathManager
from message_manager import MessageManager

class ExecutionManagerCQRS:
    """Execution Manager usando CQRS Pattern"""
    
    def __init__(self, 
                 automacao_manager: AutomacaoManager,
                 db_manager: DatabaseManager,
                 path_manager: PathManager,
                 message_manager: Optional[MessageManager] = None):
        
        # Dependências
        self.automacao_manager = automacao_manager
        self.db_manager = db_manager
        self.path_manager = path_manager
        self.message_manager = message_manager
        
        # CQRS Mediator
        self.mediator = CQRSMediator()
        
        # Handlers
        self.automation_handler = ExecuteAutomationCommandHandler(
            automacao_manager, db_manager, path_manager, message_manager
        )
        self.token_handler = ExecuteTokenRenewalCommandHandler(db_manager, message_manager)
        self.status_handler = ProcessStatusQueryHandler(self.automation_handler.active_processes)
        self.info_handler = ExecutionInfoQueryHandler(automacao_manager)
        
        # Registrar handlers no mediator
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Registra todos os handlers no mediator"""
        # Command handlers
        self.mediator.register_command_handler(ExecuteAutomationCommand, self.automation_handler)
        self.mediator.register_command_handler(ExecuteTokenRenewalCommand, self.token_handler)
        
        # Query handlers
        self.mediator.register_query_handler(GetActiveProcessesCountQuery, self.status_handler)
        self.mediator.register_query_handler(IsProcessActiveQuery, self.status_handler)
        self.mediator.register_query_handler(GetLastExecutionQuery, self.info_handler)
    
    # Command Methods (Write Operations)
    def execute_automation(self, automation_name: str, parameters: Optional[Dict[str, Any]] = None) -> CommandResult:
        """Executa uma automação via command"""
        command = ExecuteAutomationCommand(
            automation_name=automation_name,
            parameters=parameters
        )
        return self.mediator.send_command(command)
    
    def execute_token_renewal(self, headless: bool = True) -> CommandResult:
        """Executa renovação de token via command"""
        command = ExecuteTokenRenewalCommand(headless=headless)
        return self.mediator.send_command(command)
    
    def set_ui_callbacks(self, 
                        status_update: Callable = None,
                        process_counter: Callable = None,
                        button_state: Callable = None) -> CommandResult:
        """Define callbacks da UI via command"""
        command = SetUICallbacksCommand(
            status_update_callback=status_update,
            process_counter_callback=process_counter,
            button_state_callback=button_state
        )
        return self.automation_handler.set_ui_callbacks(command)
    
    # Query Methods (Read Operations)
    def get_active_processes_count(self) -> int:
        """Obtém número de processos ativos via query"""
        query = GetActiveProcessesCountQuery()
        result = self.mediator.send_query(query)
        return result.data if result.success else 0
    
    def is_process_active(self, automation_name: str) -> bool:
        """Verifica se processo está ativo via query"""
        query = IsProcessActiveQuery(automation_name=automation_name)
        result = self.mediator.send_query(query)
        return result.data if result.success else False
    
    def get_last_execution(self, automation_name: str) -> str:
        """Obtém informações da última execução via query"""
        query = GetLastExecutionQuery(automation_name=automation_name)
        result = self.mediator.send_query(query)
        return result.data if result.success else 'Nunca executado'
    
    # Compatibility Methods (para manter interface existente)
    def execute_automation_legacy(self, automation_name: str) -> None:
        """Método de compatibilidade com interface antiga"""
        result = self.execute_automation(automation_name)
        if not result.success:
            if self.message_manager:
                self.message_manager.add_message(result.message, 'error')
    
    def execute_token_renewal_legacy(self) -> None:
        """Método de compatibilidade com interface antiga"""
        result = self.execute_token_renewal()
        if not result.success:
            if self.message_manager:
                self.message_manager.add_message(result.message, 'error')
    
    # Debugging and Monitoring
    def get_cqrs_status(self) -> Dict[str, Any]:
        """Obtém status do sistema CQRS"""
        return {
            'registered_commands': self.mediator.get_registered_commands(),
            'registered_queries': self.mediator.get_registered_queries(),
            'active_processes': len(self.automation_handler.active_processes),
            'handlers_status': {
                'automation_handler': self.automation_handler.__class__.__name__,
                'token_handler': self.token_handler.__class__.__name__,
                'status_handler': self.status_handler.__class__.__name__,
                'info_handler': self.info_handler.__class__.__name__
            }
        }
"""
CQRS Handlers - Processadores de Commands e Queries
Handlers implementam a lógica de negócio para cada operação
"""

import threading
import datetime
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from cqrs_commands import (
    BaseCommand, ExecuteAutomationCommand, ExecuteTokenRenewalCommand,
    StopAutomationCommand, SetUICallbacksCommand, CommandResult, ExecutionResult
)
from cqrs_queries import (
    BaseQuery, GetActiveProcessesCountQuery, IsProcessActiveQuery,
    GetLastExecutionQuery, GetExecutionStatusQuery, GetAvailableAutomationsQuery,
    QueryResult, ProcessCountResult, ProcessStatusResult, ExecutionInfoResult, AutomationListResult
)

# Importar managers necessários
from automacao_manager import AutomacaoManager
from database import DatabaseManager
from path_manager import PathManager
from message_manager import MessageManager
from automation_registry import TokenExecutorWrapper

class CommandHandler(ABC):
    """Handler base para commands"""
    
    @abstractmethod
    def handle(self, command: BaseCommand) -> CommandResult:
        pass

class QueryHandler(ABC):
    """Handler base para queries"""
    
    @abstractmethod
    def handle(self, query: BaseQuery) -> QueryResult:
        pass

class ExecuteAutomationCommandHandler(CommandHandler):
    """Handler para executar automações"""
    
    def __init__(self, 
                 automacao_manager: AutomacaoManager,
                 db_manager: DatabaseManager,
                 path_manager: PathManager,
                 message_manager: Optional[MessageManager] = None):
        self.automacao_manager = automacao_manager
        self.db_manager = db_manager
        self.path_manager = path_manager
        self.message_manager = message_manager
        self.active_processes: Dict[str, bool] = {}
        
        # Callbacks para UI
        self.status_update_callback = None
        self.process_counter_callback = None
        self.button_state_callback = None
    
    def set_ui_callbacks(self, command: SetUICallbacksCommand) -> CommandResult:
        """Configura callbacks da UI"""
        self.status_update_callback = command.status_update_callback
        self.process_counter_callback = command.process_counter_callback
        self.button_state_callback = command.button_state_callback
        
        return CommandResult(
            success=True,
            message="Callbacks configurados com sucesso"
        )
    
    def handle(self, command: ExecuteAutomationCommand) -> ExecutionResult:
        """Executa uma automação"""
        automation_name = command.automation_name
        
        # Verificar se já está em execução
        if automation_name in self.active_processes:
            return ExecutionResult(
                success=False,
                message=f"Automação '{automation_name}' já está em execução",
                automation_name=automation_name,
                process_active=True
            )
        
        # Verificar se automação existe
        if not self.automacao_manager.obter_automacao(automation_name):
            return ExecutionResult(
                success=False,
                message=f"Automação não encontrada: {automation_name}",
                automation_name=automation_name
            )
        
        # Desabilitar botão se callback disponível
        if self.button_state_callback:
            self.button_state_callback(automation_name, False)
        
        # Executar em thread separada
        thread = threading.Thread(
            target=self._execute_automation_thread,
            args=(command,)
        )
        thread.daemon = True
        thread.start()
        
        return ExecutionResult(
            success=True,
            message=f"Automação '{automation_name}' iniciada",
            automation_name=automation_name,
            started_at=datetime.datetime.now().strftime("%H:%M:%S"),
            process_active=True
        )
    
    def _execute_automation_thread(self, command: ExecuteAutomationCommand) -> None:
        """Thread para execução da automação"""
        automation_name = command.automation_name
        
        try:
            self._safe_log(f"Iniciando execução CQRS: {automation_name}")
            self._safe_message(f"Iniciando {automation_name}...", 'info')
            
            # Atualizar status visual
            if self.status_update_callback:
                self.status_update_callback(automation_name, "Executando", 'warning')
            
            # Registrar processo ativo
            self.active_processes[automation_name] = True
            if self.process_counter_callback:
                self.process_counter_callback()
            
            # Executar via AutomacaoManager
            resultado = self.automacao_manager.executar_automacao(automation_name)
            
            # Processar resultado
            self._process_result(automation_name, resultado)
            
        except Exception as e:
            self._handle_error(automation_name, e)
        finally:
            self._cleanup_execution(automation_name)
    
    def _safe_message(self, message: str, msg_type: str = 'info') -> None:
        """Adiciona mensagem de forma segura"""
        if self.message_manager:
            self.message_manager.add_message(message, msg_type)
    
    def _safe_log(self, message: str) -> None:
        """Adiciona log de forma segura"""
        if self.message_manager:
            self.message_manager.add_log_entry(message)
    
    def _process_result(self, automation_name: str, resultado: Any) -> None:
        """Processa resultado da execução"""
        if resultado and isinstance(resultado, dict) and resultado.get('success', False):
            mensagem_sucesso = resultado.get('message', f"{automation_name} concluído")
            self._safe_message(f"✅ {mensagem_sucesso}", 'success')
            if self.status_update_callback:
                self.status_update_callback(automation_name, "Concluído", 'success')
        else:
            mensagem_erro = resultado.get('message', 'Erro na execução') if resultado else 'Falha'
            self._safe_message(f"❌ {mensagem_erro}", 'error')
            if self.status_update_callback:
                self.status_update_callback(automation_name, "Erro", 'error')
    
    def _handle_error(self, automation_name: str, error: Exception) -> None:
        """Trata erro na execução"""
        self._safe_log(f"Erro CQRS em {automation_name}: {str(error)}")
        self._safe_message(f"❌ Erro inesperado em {automation_name}", 'error')
        if self.status_update_callback:
            self.status_update_callback(automation_name, "Erro", 'error')
    
    def _cleanup_execution(self, automation_name: str) -> None:
        """Limpa recursos após execução"""
        if automation_name in self.active_processes:
            del self.active_processes[automation_name]
        
        if self.process_counter_callback:
            self.process_counter_callback()
        
        if self.button_state_callback:
            self.button_state_callback(automation_name, True)

class ExecuteTokenRenewalCommandHandler(CommandHandler):
    """Handler para renovação de token"""
    
    def __init__(self, 
                 db_manager: DatabaseManager,
                 message_manager: Optional[MessageManager] = None):
        self.db_manager = db_manager
        self.message_manager = message_manager
    
    def handle(self, command: ExecuteTokenRenewalCommand) -> CommandResult:
        """Executa renovação de token"""
        self._safe_message("🔑 Iniciando renovação de token...", 'info')
        
        # Executar em thread separada
        thread = threading.Thread(target=self._execute_token_thread, args=(command,))
        thread.daemon = True
        thread.start()
        
        return CommandResult(
            success=True,
            message="Renovação de token iniciada"
        )
    
    def _execute_token_thread(self, command: ExecuteTokenRenewalCommand) -> None:
        """Thread para execução de token"""
        execution_id = None
        
        try:
            self._safe_log("Iniciando renovação via CQRS")
            
            # Registrar no banco
            execution_id = self.db_manager.registrar_inicio_execucao("renovar_token_cqrs")
            
            # Usar wrapper seguro
            token_executor = TokenExecutorWrapper()
            resultado = token_executor.run(headless=command.headless)
            
            # Processar resultado
            self._process_token_result(resultado, execution_id)
            
        except Exception as e:
            self._handle_token_error(e, execution_id)
    
    def _safe_message(self, message: str, msg_type: str = 'info') -> None:
        if self.message_manager:
            self.message_manager.add_message(message, msg_type)
    
    def _safe_log(self, message: str) -> None:
        if self.message_manager:
            self.message_manager.add_log_entry(message)
    
    def _process_token_result(self, resultado: Dict[str, Any], execution_id: Optional[int]) -> None:
        if resultado and resultado.get('success', False):
            mensagem = resultado.get('message', 'Token renovado com sucesso')
            self._safe_message(f"✅ {mensagem}", 'success')
            if execution_id:
                self.db_manager.registrar_fim_execucao(execution_id, 'CONCLUIDO', dados_resultado=resultado)
        else:
            mensagem = resultado.get('message', 'Erro na renovação') if resultado else 'Falha'
            self._safe_message(f"❌ {mensagem}", 'error')
            if execution_id:
                self.db_manager.registrar_fim_execucao(execution_id, 'ERRO', mensagem_erro=mensagem)
    
    def _handle_token_error(self, error: Exception, execution_id: Optional[int]) -> None:
        self._safe_log(f"Erro token CQRS: {str(error)}")
        self._safe_message(f"❌ Erro na renovação: {str(error)}", 'error')
        if execution_id:
            try:
                self.db_manager.registrar_fim_execucao(execution_id, 'ERRO', mensagem_erro=str(error))
            except:
                pass

# Query Handlers
class ProcessStatusQueryHandler(QueryHandler):
    """Handler para queries de status de processos"""
    
    def __init__(self, active_processes: Dict[str, bool]):
        self.active_processes = active_processes
    
    def handle(self, query: BaseQuery) -> QueryResult:
        """Processa queries de status"""
        if isinstance(query, GetActiveProcessesCountQuery):
            return ProcessCountResult(
                success=True,
                data=len(self.active_processes),
                active_count=len(self.active_processes)
            )
        
        elif isinstance(query, IsProcessActiveQuery):
            is_active = query.automation_name in self.active_processes
            return ProcessStatusResult(
                success=True,
                data=is_active,
                automation_name=query.automation_name,
                is_active=is_active
            )
        
        return QueryResult(success=False, data=None, message="Query não suportada")

class ExecutionInfoQueryHandler(QueryHandler):
    """Handler para informações de execução"""
    
    def __init__(self, automacao_manager: AutomacaoManager):
        self.automacao_manager = automacao_manager
    
    def handle(self, query: GetLastExecutionQuery) -> ExecutionInfoResult:
        """Obtém informações da última execução"""
        try:
            ultima_exec = self.automacao_manager.obter_ultima_execucao(query.automation_name)
            if ultima_exec:
                data_exec = ultima_exec['inicio']
                status = ultima_exec['status']
                execution_info = f"{data_exec.strftime('%d/%m/%Y %H:%M:%S')} ({status})"
            else:
                execution_info = 'Nunca executado'
            
            return ExecutionInfoResult(
                success=True,
                data=execution_info,
                automation_name=query.automation_name,
                last_execution=execution_info
            )
        except Exception as e:
            return ExecutionInfoResult(
                success=False,
                data='Erro ao obter execução',
                automation_name=query.automation_name,
                message=str(e)
            )
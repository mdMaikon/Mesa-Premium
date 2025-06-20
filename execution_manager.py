"""
Execution Manager
Gerencia a execução de automações e tokens
"""

import threading
import datetime
from typing import Dict, Any, Optional, Callable

from automacao_manager import AutomacaoManager
from database import DatabaseManager
from path_manager import PathManager
from message_manager import MessageManager
from automation_registry import AutomationRegistry, TokenExecutorWrapper

class ExecutionManager:
    """Gerenciador de execuções de automações"""
    
    def __init__(self, 
                 automacao_manager: AutomacaoManager,
                 db_manager: DatabaseManager,
                 path_manager: PathManager,
                 message_manager: Optional[MessageManager] = None):
        self.automacao_manager = automacao_manager
        self.db_manager = db_manager
        self.path_manager = path_manager
        self.message_manager = message_manager
        
        # Controle de processos ativos
        self.active_processes: Dict[str, bool] = {}
        
        # Callbacks para atualização da UI
        self.status_update_callback: Optional[Callable] = None
        self.process_counter_callback: Optional[Callable] = None
        self.button_state_callback: Optional[Callable] = None
    
    def _safe_message(self, message: str, msg_type: str = 'info') -> None:
        """Adiciona mensagem de forma segura"""
        if self.message_manager:
            self.message_manager.add_message(message, msg_type)
    
    def _safe_log(self, message: str) -> None:
        """Adiciona log de forma segura"""
        if self.message_manager:
            self.message_manager.add_log_entry(message)
    
    def set_ui_callbacks(self, 
                        status_update: Callable = None,
                        process_counter: Callable = None,
                        button_state: Callable = None):
        """Define callbacks para atualização da UI"""
        self.status_update_callback = status_update
        self.process_counter_callback = process_counter
        self.button_state_callback = button_state
    
    def execute_automation(self, automation_name: str) -> None:
        """Executa uma automação via AutomacaoManager"""
        if automation_name in self.active_processes:
            self._safe_message(f"Automação '{automation_name}' já está em execução", 'warning')
            return
        
        # Verificar se automação existe
        if not self.automacao_manager.obter_automacao(automation_name):
            self._safe_message(f"Automação não encontrada: {automation_name}", 'error')
            return
        
        # Desabilitar botão de execução
        if self.button_state_callback:
            self.button_state_callback(automation_name, False)
        
        # Executar em thread separada
        thread = threading.Thread(
            target=self._execute_automation_thread,
            args=(automation_name,)
        )
        thread.daemon = True
        thread.start()
    
    def execute_token_renewal(self) -> None:
        """Executa renovação de token usando versão simplificada"""
        self._safe_message("🔑 Iniciando renovação de token...", 'info')
        
        # Executar em thread separada
        thread = threading.Thread(target=self._execute_token_thread)
        thread.daemon = True
        thread.start()
    
    def _execute_automation_thread(self, automation_name: str) -> None:
        """Thread para execução de automação via AutomacaoManager"""
        try:
            self._safe_log(f"Iniciando execução modular: {automation_name}")
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
            self._process_automation_result(automation_name, resultado)
            
        except Exception as e:
            self._handle_automation_error(automation_name, e)
        finally:
            self._cleanup_automation_execution(automation_name)
    
    def _execute_token_thread(self) -> None:
        """Thread para execução de renovação de token usando Registry seguro"""
        automation_name = "renovar_token_simplificado"
        execution_id = None
        
        try:
            self._safe_log("Iniciando execução de token via AutomationRegistry")
            
            # Registrar início da execução no banco
            execution_id = self.db_manager.registrar_inicio_execucao(automation_name)
            
            # Usar o wrapper seguro para compatibilidade
            token_executor = TokenExecutorWrapper()
            
            # Executar de forma segura
            resultado = token_executor.run(headless=True)
            
            # Processar resultado
            self._process_token_result(resultado, execution_id)
            
        except Exception as e:
            self._handle_token_error(e, execution_id)
    
    def _load_token_module(self):
        """DEPRECATED: Método removido por questões de segurança
        
        Este método foi removido porque usava exec_module() que permite
        execução de código arbitrário. Use AutomationRegistry em vez disso.
        """
        self._safe_log("AVISO: _load_token_module() está deprecado. Use AutomationRegistry.")
        raise DeprecationWarning("Método _load_token_module removido por questões de segurança")
    
    def _process_automation_result(self, automation_name: str, resultado: Any) -> None:
        """Processa resultado da execução de automação"""
        if resultado and isinstance(resultado, dict) and resultado.get('success', False):
            mensagem_sucesso = resultado.get('message', f"{automation_name} concluído com sucesso")
            self._safe_message(f"✅ {mensagem_sucesso}", 'success')
            if self.status_update_callback:
                self.status_update_callback(automation_name, "Concluído", 'success')
                
        elif resultado and isinstance(resultado, dict) and not resultado.get('success', True):
            mensagem_erro = resultado.get('message', 'Erro na execução')
            self._safe_message(f"❌ {mensagem_erro}", 'error')
            if self.status_update_callback:
                self.status_update_callback(automation_name, "Erro", 'error')
        else:
            # Para automações que não retornam estrutura de sucesso/falha padrão
            self._safe_message(f"✅ {automation_name} executado", 'success')
            if self.status_update_callback:
                self.status_update_callback(automation_name, "Concluído", 'success')
    
    def _process_token_result(self, resultado: Dict[str, Any], execution_id: Optional[int]) -> None:
        """Processa resultado da execução de token"""
        if resultado and isinstance(resultado, dict) and resultado.get('success', False):
            mensagem_sucesso = resultado.get('message', 'Token renovado com sucesso')
            self._safe_message(f"✅ {mensagem_sucesso}", 'success')
            
            # Registrar sucesso no banco
            if execution_id:
                self.db_manager.registrar_fim_execucao(
                    execution_id, 'CONCLUIDO', dados_resultado=resultado
                )
        else:
            mensagem_erro = resultado.get('message', 'Erro na renovação do token') if resultado else 'Falha na execução'
            self._safe_message(f"❌ {mensagem_erro}", 'error')
            
            # Registrar erro no banco
            if execution_id:
                self.db_manager.registrar_fim_execucao(
                    execution_id, 'ERRO', mensagem_erro=mensagem_erro
                )
    
    def _handle_automation_error(self, automation_name: str, error: Exception) -> None:
        """Trata erro na execução de automação"""
        self._safe_log(f"Erro durante execução modular de {automation_name}: {str(error)}")
        self._safe_message(f"❌ Erro inesperado em {automation_name}", 'error')
        
        if self.status_update_callback:
            self.status_update_callback(automation_name, "Erro", 'error')
    
    def _handle_token_error(self, error: Exception, execution_id: Optional[int]) -> None:
        """Trata erro na execução de token"""
        self._safe_log(f"Erro durante execução de token: {str(error)}")
        self._safe_message(f"❌ Erro inesperado na renovação de token: {str(error)}", 'error')
        
        # Registrar erro no banco
        if execution_id:
            try:
                self.db_manager.registrar_fim_execucao(
                    execution_id, 'ERRO', mensagem_erro=str(error)
                )
            except:
                pass
    
    def _cleanup_automation_execution(self, automation_name: str) -> None:
        """Limpa recursos após execução de automação"""
        # Remover processo ativo
        if automation_name in self.active_processes:
            del self.active_processes[automation_name]
        
        # Atualizar contador de processos
        if self.process_counter_callback:
            self.process_counter_callback()
        
        # Reabilitar botão de execução
        if self.button_state_callback:
            self.button_state_callback(automation_name, True)
    
    def get_active_processes_count(self) -> int:
        """Retorna número de processos ativos"""
        return len(self.active_processes)
    
    def is_process_active(self, automation_name: str) -> bool:
        """Verifica se um processo específico está ativo"""
        return automation_name in self.active_processes
    
    def get_last_execution(self, automation_name: str) -> str:
        """Obtém informações da última execução"""
        try:
            ultima_exec = self.automacao_manager.obter_ultima_execucao(automation_name)
            if ultima_exec:
                data_exec = ultima_exec['inicio']
                status = ultima_exec['status']
                return f"{data_exec.strftime('%d/%m/%Y %H:%M:%S')} ({status})"
        except Exception as e:
            self._safe_log(f"Erro ao obter última execução: {str(e)}")
        
        return 'Nunca executado'
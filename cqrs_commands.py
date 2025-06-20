"""
CQRS Commands - Operações de Escrita
Commands representam intenções de mudança de estado
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable

@dataclass
class BaseCommand:
    """Comando base para todas as operações de escrita"""
    pass

@dataclass 
class ExecuteAutomationCommand(BaseCommand):
    """Comando para executar uma automação"""
    automation_name: str
    parameters: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

@dataclass
class ExecuteTokenRenewalCommand(BaseCommand):
    """Comando para renovar token"""
    headless: bool = True
    user_id: Optional[str] = None

@dataclass
class StopAutomationCommand(BaseCommand):
    """Comando para parar uma automação em execução"""
    automation_name: str
    user_id: Optional[str] = None

@dataclass
class SetUICallbacksCommand(BaseCommand):
    """Comando para configurar callbacks da UI"""
    status_update_callback: Optional[Callable] = None
    process_counter_callback: Optional[Callable] = None
    button_state_callback: Optional[Callable] = None

# Result objects para responses dos commands
@dataclass
class CommandResult:
    """Resultado base de execução de comando"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_id: Optional[int] = None

@dataclass 
class ExecutionResult(CommandResult):
    """Resultado específico de execução de automação"""
    automation_name: str = ""
    started_at: Optional[str] = None
    process_active: bool = False
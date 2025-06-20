"""
CQRS Queries - Operações de Leitura
Queries representam solicitações de informação sem mudança de estado
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

@dataclass
class BaseQuery:
    """Query base para todas as operações de leitura"""
    pass

@dataclass
class GetActiveProcessesCountQuery(BaseQuery):
    """Query para obter número de processos ativos"""
    pass

@dataclass
class IsProcessActiveQuery(BaseQuery):
    """Query para verificar se um processo específico está ativo"""
    automation_name: str

@dataclass
class GetLastExecutionQuery(BaseQuery):
    """Query para obter informações da última execução"""
    automation_name: str

@dataclass
class GetExecutionStatusQuery(BaseQuery):
    """Query para obter status detalhado de execução"""
    automation_name: str

@dataclass
class GetAvailableAutomationsQuery(BaseQuery):
    """Query para listar automações disponíveis"""
    filter_tokens: bool = True

# Result objects para responses das queries
@dataclass
class QueryResult:
    """Resultado base de execução de query"""
    success: bool
    data: Any
    message: Optional[str] = None

@dataclass
class ProcessCountResult(QueryResult):
    """Resultado para contagem de processos"""
    active_count: int = 0

@dataclass
class ProcessStatusResult(QueryResult):
    """Resultado para status de processo"""
    automation_name: str = ""
    is_active: bool = False

@dataclass
class ExecutionInfoResult(QueryResult):
    """Resultado para informações de execução"""
    automation_name: str = ""
    last_execution: Optional[str] = None
    status: Optional[str] = None
    execution_time: Optional[str] = None

@dataclass
class AutomationListResult(QueryResult):
    """Resultado para lista de automações"""
    automations: List[Dict[str, str]] = None
    total_count: int = 0
    
    def __post_init__(self):
        if self.automations is None:
            self.automations = []
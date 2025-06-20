"""
Automation Registry
Sistema seguro de registro e criação de automações
"""

from typing import Dict, Type, Protocol, Any, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class TokenExecutor(Protocol):
    """Interface para executores de token"""
    
    def run(self, headless: bool = True) -> Dict[str, Any]:
        """Executa a extração de token"""
        ...

class AutomationExecutor(ABC):
    """Classe base abstrata para executores de automação"""
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Executa a automação"""
        pass

class AutomationRegistry:
    """Registry seguro para automações"""
    
    _token_executors: Dict[str, Type[TokenExecutor]] = {}
    _automation_executors: Dict[str, Type[AutomationExecutor]] = {}
    
    @classmethod
    def register_token_executor(cls, name: str, executor_class: Type[TokenExecutor]) -> None:
        """Registra um executor de token"""
        if not hasattr(executor_class, 'run'):
            raise ValueError(f"Token executor {executor_class.__name__} deve implementar método 'run'")
            
        cls._token_executors[name] = executor_class
        logger.info(f"Token executor registrado: {name} -> {executor_class.__name__}")
    
    @classmethod
    def register_automation_executor(cls, name: str, executor_class: Type[AutomationExecutor]) -> None:
        """Registra um executor de automação"""
        if not issubclass(executor_class, AutomationExecutor):
            raise ValueError(f"Executor {executor_class.__name__} deve herdar de AutomationExecutor")
            
        cls._automation_executors[name] = executor_class
        logger.info(f"Automation executor registrado: {name} -> {executor_class.__name__}")
    
    @classmethod
    def create_token_executor(cls, name: str) -> Optional[TokenExecutor]:
        """Cria uma instância segura de executor de token"""
        executor_class = cls._token_executors.get(name)
        if executor_class:
            try:
                return executor_class()
            except Exception as e:
                logger.error(f"Erro ao criar token executor {name}: {e}")
                return None
        
        logger.warning(f"Token executor não encontrado: {name}")
        return None
    
    @classmethod
    def create_automation_executor(cls, name: str) -> Optional[AutomationExecutor]:
        """Cria uma instância segura de executor de automação"""
        executor_class = cls._automation_executors.get(name)
        if executor_class:
            try:
                return executor_class()
            except Exception as e:
                logger.error(f"Erro ao criar automation executor {name}: {e}")
                return None
        
        logger.warning(f"Automation executor não encontrado: {name}")
        return None
    
    @classmethod
    def list_token_executors(cls) -> Dict[str, str]:
        """Lista executores de token disponíveis"""
        return {name: cls_type.__name__ for name, cls_type in cls._token_executors.items()}
    
    @classmethod
    def list_automation_executors(cls) -> Dict[str, str]:
        """Lista executores de automação disponíveis"""
        return {name: cls_type.__name__ for name, cls_type in cls._automation_executors.items()}
    
    @classmethod
    def is_token_executor_registered(cls, name: str) -> bool:
        """Verifica se um executor de token está registrado"""
        return name in cls._token_executors
    
    @classmethod
    def is_automation_executor_registered(cls, name: str) -> bool:
        """Verifica se um executor de automação está registrado"""
        return name in cls._automation_executors


# Wrapper para compatibilidade com sistema atual
class TokenExecutorWrapper:
    """Wrapper para integração com renovar_token_simplified.py"""
    
    def __init__(self, executor_class_name: str = "HubXPTokenExtractorSimplified"):
        self.executor_class_name = executor_class_name
        self._executor = None
    
    def _import_legacy_executor(self):
        """Importa o executor legado de forma controlada"""
        try:
            # Importação direta e segura (sem exec_module)
            from renovar_token_simplified import HubXPTokenExtractorSimplified
            return HubXPTokenExtractorSimplified
        except ImportError as e:
            logger.error(f"Erro ao importar {self.executor_class_name}: {e}")
            return None
    
    def get_executor(self) -> Optional[TokenExecutor]:
        """Obtém o executor de forma segura"""
        if self._executor is None:
            executor_class = self._import_legacy_executor()
            if executor_class:
                self._executor = executor_class()
        
        return self._executor
    
    def run(self, headless: bool = True) -> Dict[str, Any]:
        """Executa o token executor de forma segura"""
        executor = self.get_executor()
        if executor:
            return executor.run(headless=headless)
        else:
            return {
                'success': False,
                'message': f'Falha ao carregar executor {self.executor_class_name}'
            }
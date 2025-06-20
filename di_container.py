"""
DI Container - Injeção de Dependência
Sistema crítico e focado para desacoplamento de managers
"""

from typing import Type, TypeVar, Dict, Any, Callable, Optional, Protocol
from abc import ABC, abstractmethod
import logging
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ServiceLifetime:
    """Enum para tempo de vida dos serviços"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"

class ServiceRegistration:
    """Registro de um serviço no container"""
    
    def __init__(self, 
                 service_type: Type[T], 
                 implementation: Any,
                 lifetime: str = ServiceLifetime.TRANSIENT):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.instance = None

class DIContainer:
    """Container de Injeção de Dependência focado e crítico"""
    
    def __init__(self):
        self._services: Dict[Type, ServiceRegistration] = {}
        self._singletons: Dict[Type, Any] = {}
        self._building: set = set()  # Detectar dependências circulares
    
    def register_singleton(self, service_type: Type[T], implementation: T) -> 'DIContainer':
        """Registra serviço como singleton"""
        if service_type in self._services:
            logger.warning(f"Serviço {service_type.__name__} já registrado, sobrescrevendo")
        
        self._services[service_type] = ServiceRegistration(
            service_type, implementation, ServiceLifetime.SINGLETON
        )
        logger.debug(f"Singleton registrado: {service_type.__name__}")
        return self
    
    def register_transient(self, service_type: Type[T], factory: Callable[[], T]) -> 'DIContainer':
        """Registra serviço como transient"""
        if service_type in self._services:
            logger.warning(f"Serviço {service_type.__name__} já registrado, sobrescrevendo")
        
        self._services[service_type] = ServiceRegistration(
            service_type, factory, ServiceLifetime.TRANSIENT
        )
        logger.debug(f"Transient registrado: {service_type.__name__}")
        return self
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """Registra instância específica como singleton"""
        self._singletons[service_type] = instance
        logger.debug(f"Instância registrada: {service_type.__name__}")
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve uma dependência"""
        # Detectar dependência circular
        if service_type in self._building:
            raise RuntimeError(f"Dependência circular detectada: {service_type.__name__}")
        
        # Verificar singleton em cache
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        # Verificar registro
        if service_type not in self._services:
            raise ValueError(f"Serviço não registrado: {service_type.__name__}")
        
        registration = self._services[service_type]
        
        try:
            self._building.add(service_type)
            
            if registration.lifetime == ServiceLifetime.SINGLETON:
                if registration.instance is None:
                    registration.instance = self._create_instance(registration)
                instance = registration.instance
                self._singletons[service_type] = instance
            else:
                instance = self._create_instance(registration)
            
            return instance
            
        finally:
            self._building.discard(service_type)
    
    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """Cria instância baseada no registro"""
        implementation = registration.implementation
        
        if callable(implementation):
            # Se é factory function, chama diretamente
            if hasattr(implementation, '__annotations__'):
                return self._inject_dependencies(implementation)
            else:
                return implementation()
        else:
            # Se é classe, instancia
            return self._inject_dependencies(implementation)
    
    def _inject_dependencies(self, target: Callable) -> Any:
        """Injeta dependências no construtor"""
        if not hasattr(target, '__annotations__'):
            return target() if callable(target) else target
        
        annotations = getattr(target, '__annotations__', {})
        
        # Para classes, pegar __init__ annotations
        if hasattr(target, '__init__') and hasattr(target.__init__, '__annotations__'):
            annotations = target.__init__.__annotations__
        
        kwargs = {}
        for param_name, param_type in annotations.items():
            if param_name == 'return':
                continue
            
            if param_type in self._services or param_type in self._singletons:
                kwargs[param_name] = self.resolve(param_type)
        
        return target(**kwargs)
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """Verifica se um serviço está registrado"""
        return service_type in self._services or service_type in self._singletons
    
    def clear(self) -> None:
        """Limpa todos os registros"""
        self._services.clear()
        self._singletons.clear()
        self._building.clear()
        logger.debug("Container limpo")
    
    def get_registered_services(self) -> Dict[str, str]:
        """Lista serviços registrados (para debug)"""
        services = {}
        for service_type, registration in self._services.items():
            services[service_type.__name__] = registration.lifetime
        for service_type in self._singletons.keys():
            services[service_type.__name__] = "instance"
        return services

def inject(container: DIContainer):
    """Decorator para injeção automática de dependências"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Resolver dependências baseado nas annotations
            if hasattr(func, '__annotations__'):
                for param_name, param_type in func.__annotations__.items():
                    if param_name != 'return' and param_name not in kwargs:
                        if container.is_registered(param_type):
                            kwargs[param_name] = container.resolve(param_type)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Container global para facilitar uso
container = DIContainer()
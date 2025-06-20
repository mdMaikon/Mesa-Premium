"""
Service Registry - Configuração de Serviços
Registro centralizado e crítico dos managers existentes
"""

from di_container import DIContainer
from path_manager import PathManager
from database import DatabaseManager
from automacao_config import AutomacaoConfig
from automacao_manager import AutomacaoManager
from message_manager import MessageManager
from execution_manager import ExecutionManager
import logging

logger = logging.getLogger(__name__)

def configure_services(container: DIContainer) -> DIContainer:
    """Configura todos os serviços no DIContainer de forma crítica"""
    
    # 1. SINGLETONS - Serviços que devem ter única instância
    logger.info("Configurando singletons...")
    
    # PathManager - Singleton (gerencia caminhos globais)
    path_manager = PathManager()
    container.register_instance(PathManager, path_manager)
    
    # DatabaseManager - Singleton (conexão única)
    # Durante build, não validar configuração
    import sys
    is_building = getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS')
    db_manager = DatabaseManager(validate_on_init=not is_building)
    container.register_instance(DatabaseManager, db_manager)
    
    # AutomacaoConfig - Singleton (configuração global)
    automacao_config = AutomacaoConfig(path_manager)
    container.register_instance(AutomacaoConfig, automacao_config)
    
    # 2. TRANSIENTS - Serviços que podem ter múltiplas instâncias
    logger.info("Configurando transients...")
    
    # AutomacaoManager - Depende de PathManager e DatabaseManager
    container.register_transient(
        AutomacaoManager,
        lambda: AutomacaoManager(
            container.resolve(PathManager),
            container.resolve(DatabaseManager)
        )
    )
    
    # MessageManager - REMOVIDO do DI (requer UI component)
    # MessageManager será instanciado diretamente pelo UIManager
    
    # ExecutionManager - Depende de múltiplos serviços (MessageManager injetado após)
    container.register_transient(
        ExecutionManager,
        lambda: ExecutionManager(
            container.resolve(AutomacaoManager),
            container.resolve(DatabaseManager),
            container.resolve(PathManager),
            None  # MessageManager será injetado depois
        )
    )
    
    logger.info(f"Serviços configurados: {list(container.get_registered_services().keys())}")
    return container

def get_configured_container() -> DIContainer:
    """Retorna container pré-configurado"""
    container = DIContainer()
    return configure_services(container)

# Para compatibilidade - container global configurado apenas quando necessário
configured_container = None

def get_global_container():
    """Obtém container global, inicializando se necessário"""
    global configured_container
    if configured_container is None:
        configured_container = get_configured_container()
    return configured_container
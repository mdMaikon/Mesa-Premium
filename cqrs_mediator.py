"""
CQRS Mediator - Orquestrador de Commands e Queries
Implementa o padrão Mediator para coordenar operações CQRS
"""

from typing import Dict, Type, Optional
import logging

from cqrs_commands import BaseCommand, CommandResult
from cqrs_queries import BaseQuery, QueryResult
from cqrs_handlers import CommandHandler, QueryHandler

logger = logging.getLogger(__name__)

class CQRSMediator:
    """Mediator para operações CQRS"""
    
    def __init__(self):
        self._command_handlers: Dict[Type[BaseCommand], CommandHandler] = {}
        self._query_handlers: Dict[Type[BaseQuery], QueryHandler] = {}
    
    def register_command_handler(self, command_type: Type[BaseCommand], handler: CommandHandler) -> None:
        """Registra handler para um tipo de command"""
        self._command_handlers[command_type] = handler
        logger.debug(f"Command handler registrado: {command_type.__name__} -> {handler.__class__.__name__}")
    
    def register_query_handler(self, query_type: Type[BaseQuery], handler: QueryHandler) -> None:
        """Registra handler para um tipo de query"""
        self._query_handlers[query_type] = handler
        logger.debug(f"Query handler registrado: {query_type.__name__} -> {handler.__class__.__name__}")
    
    def send_command(self, command: BaseCommand) -> CommandResult:
        """Executa um command através do handler apropriado"""
        command_type = type(command)
        
        if command_type not in self._command_handlers:
            return CommandResult(
                success=False,
                message=f"Nenhum handler registrado para {command_type.__name__}"
            )
        
        try:
            handler = self._command_handlers[command_type]
            logger.debug(f"Executando command: {command_type.__name__}")
            return handler.handle(command)
        except Exception as e:
            logger.error(f"Erro ao executar command {command_type.__name__}: {e}")
            return CommandResult(
                success=False,
                message=f"Erro interno: {str(e)}"
            )
    
    def send_query(self, query: BaseQuery) -> QueryResult:
        """Executa uma query através do handler apropriado"""
        query_type = type(query)
        
        if query_type not in self._query_handlers:
            return QueryResult(
                success=False,
                data=None,
                message=f"Nenhum handler registrado para {query_type.__name__}"
            )
        
        try:
            handler = self._query_handlers[query_type]
            logger.debug(f"Executando query: {query_type.__name__}")
            return handler.handle(query)
        except Exception as e:
            logger.error(f"Erro ao executar query {query_type.__name__}: {e}")
            return QueryResult(
                success=False,
                data=None,
                message=f"Erro interno: {str(e)}"
            )
    
    def get_registered_commands(self) -> Dict[str, str]:
        """Lista commands registrados"""
        return {cmd.__name__: handler.__class__.__name__ 
                for cmd, handler in self._command_handlers.items()}
    
    def get_registered_queries(self) -> Dict[str, str]:
        """Lista queries registradas"""
        return {query.__name__: handler.__class__.__name__ 
                for query, handler in self._query_handlers.items()}
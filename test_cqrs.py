"""
Testes críticos do CQRS Pattern
Valida funcionalidade de separação command/query
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from cqrs_commands import ExecuteAutomationCommand, ExecuteTokenRenewalCommand, SetUICallbacksCommand
from cqrs_queries import GetActiveProcessesCountQuery, IsProcessActiveQuery, GetLastExecutionQuery
from cqrs_mediator import CQRSMediator
from cqrs_handlers import ExecuteAutomationCommandHandler, ProcessStatusQueryHandler
from execution_manager_cqrs import ExecutionManagerCQRS

class TestCQRSCommands(unittest.TestCase):
    """Testes dos Commands"""
    
    def test_execute_automation_command_creation(self):
        """Testa criação de ExecuteAutomationCommand"""
        command = ExecuteAutomationCommand(
            automation_name="test_automation",
            parameters={"param1": "value1"}
        )
        
        self.assertEqual(command.automation_name, "test_automation")
        self.assertEqual(command.parameters["param1"], "value1")
    
    def test_execute_token_renewal_command_creation(self):
        """Testa criação de ExecuteTokenRenewalCommand"""
        command = ExecuteTokenRenewalCommand(headless=False)
        
        self.assertEqual(command.headless, False)
    
    def test_set_ui_callbacks_command_creation(self):
        """Testa criação de SetUICallbacksCommand"""
        mock_callback = Mock()
        command = SetUICallbacksCommand(status_update_callback=mock_callback)
        
        self.assertEqual(command.status_update_callback, mock_callback)

class TestCQRSQueries(unittest.TestCase):
    """Testes das Queries"""
    
    def test_get_active_processes_count_query(self):
        """Testa GetActiveProcessesCountQuery"""
        query = GetActiveProcessesCountQuery()
        self.assertIsNotNone(query)
    
    def test_is_process_active_query(self):
        """Testa IsProcessActiveQuery"""
        query = IsProcessActiveQuery(automation_name="test_automation")
        self.assertEqual(query.automation_name, "test_automation")
    
    def test_get_last_execution_query(self):
        """Testa GetLastExecutionQuery"""
        query = GetLastExecutionQuery(automation_name="test_automation")
        self.assertEqual(query.automation_name, "test_automation")

class TestCQRSMediator(unittest.TestCase):
    """Testes críticos do Mediator"""
    
    def setUp(self):
        self.mediator = CQRSMediator()
        self.mock_command_handler = Mock()
        self.mock_query_handler = Mock()
    
    def test_register_command_handler(self):
        """Testa registro de command handler"""
        self.mediator.register_command_handler(ExecuteAutomationCommand, self.mock_command_handler)
        
        registered = self.mediator.get_registered_commands()
        self.assertIn("ExecuteAutomationCommand", registered)
    
    def test_register_query_handler(self):
        """Testa registro de query handler"""
        self.mediator.register_query_handler(GetActiveProcessesCountQuery, self.mock_query_handler)
        
        registered = self.mediator.get_registered_queries()
        self.assertIn("GetActiveProcessesCountQuery", registered)
    
    def test_send_command_success(self):
        """Testa execução bem-sucedida de command"""
        # Arrange
        from cqrs_commands import CommandResult
        expected_result = CommandResult(success=True, message="Success")
        self.mock_command_handler.handle.return_value = expected_result
        
        self.mediator.register_command_handler(ExecuteAutomationCommand, self.mock_command_handler)
        command = ExecuteAutomationCommand(automation_name="test")
        
        # Act
        result = self.mediator.send_command(command)
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Success")
        self.mock_command_handler.handle.assert_called_once_with(command)
    
    def test_send_command_no_handler(self):
        """Testa command sem handler registrado"""
        command = ExecuteAutomationCommand(automation_name="test")
        result = self.mediator.send_command(command)
        
        self.assertFalse(result.success)
        self.assertIn("Nenhum handler registrado", result.message)
    
    def test_send_query_success(self):
        """Testa execução bem-sucedida de query"""
        # Arrange
        from cqrs_queries import QueryResult
        expected_result = QueryResult(success=True, data=5)
        self.mock_query_handler.handle.return_value = expected_result
        
        self.mediator.register_query_handler(GetActiveProcessesCountQuery, self.mock_query_handler)
        query = GetActiveProcessesCountQuery()
        
        # Act
        result = self.mediator.send_query(query)
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.data, 5)
        self.mock_query_handler.handle.assert_called_once_with(query)

class TestProcessStatusQueryHandler(unittest.TestCase):
    """Testes do ProcessStatusQueryHandler"""
    
    def setUp(self):
        self.active_processes = {"automation1": True, "automation2": True}
        self.handler = ProcessStatusQueryHandler(self.active_processes)
    
    def test_get_active_processes_count(self):
        """Testa contagem de processos ativos"""
        query = GetActiveProcessesCountQuery()
        result = self.handler.handle(query)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data, 2)
    
    def test_is_process_active_true(self):
        """Testa verificação de processo ativo (verdadeiro)"""
        query = IsProcessActiveQuery(automation_name="automation1")
        result = self.handler.handle(query)
        
        self.assertTrue(result.success)
        self.assertTrue(result.data)
    
    def test_is_process_active_false(self):
        """Testa verificação de processo ativo (falso)"""
        query = IsProcessActiveQuery(automation_name="automation3")
        result = self.handler.handle(query)
        
        self.assertTrue(result.success)
        self.assertFalse(result.data)

class TestExecutionManagerCQRS(unittest.TestCase):
    """Testes críticos do ExecutionManagerCQRS"""
    
    @patch('execution_manager_cqrs.AutomacaoManager')
    @patch('execution_manager_cqrs.DatabaseManager')
    @patch('execution_manager_cqrs.PathManager')
    def setUp(self, mock_path, mock_db, mock_automacao):
        self.mock_automacao_manager = mock_automacao()
        self.mock_db_manager = mock_db()
        self.mock_path_manager = mock_path()
        self.mock_message_manager = Mock()
        
        self.execution_manager = ExecutionManagerCQRS(
            self.mock_automacao_manager,
            self.mock_db_manager,
            self.mock_path_manager,
            self.mock_message_manager
        )
    
    def test_execute_automation_command_flow(self):
        """Testa fluxo de execução via command"""
        # Arrange
        self.mock_automacao_manager.obter_automacao.return_value = {"nome": "test"}
        
        # Act
        result = self.execution_manager.execute_automation("test_automation")
        
        # Assert
        self.assertTrue(result.success)
        self.assertIn("iniciada", result.message)
    
    def test_get_active_processes_count_query_flow(self):
        """Testa fluxo de consulta via query"""
        # Act
        count = self.execution_manager.get_active_processes_count()
        
        # Assert
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)
    
    def test_is_process_active_query_flow(self):
        """Testa verificação de processo ativo via query"""
        # Act
        is_active = self.execution_manager.is_process_active("test_automation")
        
        # Assert
        self.assertIsInstance(is_active, bool)
    
    def test_get_cqrs_status(self):
        """Testa status do sistema CQRS"""
        # Act
        status = self.execution_manager.get_cqrs_status()
        
        # Assert
        self.assertIn('registered_commands', status)
        self.assertIn('registered_queries', status)
        self.assertIn('active_processes', status)
        self.assertIn('handlers_status', status)
        
        # Verificar se handlers estão registrados
        self.assertIn('ExecuteAutomationCommand', status['registered_commands'])
        self.assertIn('ExecuteTokenRenewalCommand', status['registered_commands'])
        self.assertIn('GetActiveProcessesCountQuery', status['registered_queries'])

if __name__ == '__main__':
    # Executar testes
    unittest.main(verbosity=2)
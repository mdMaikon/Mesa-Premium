"""
Testes críticos do DI Container
Valida funcionalidade core de injeção de dependência
"""

import unittest
from unittest.mock import Mock, patch
from di_container import DIContainer, ServiceLifetime, inject
from service_registry import configure_services

class MockService:
    """Mock service para testes"""
    def __init__(self, name: str = "test"):
        self.name = name

class MockDependentService:
    """Mock service com dependência"""
    def __init__(self, mock_service: MockService):
        self.dependency = mock_service

class TestDIContainer(unittest.TestCase):
    """Testes críticos do DIContainer"""
    
    def setUp(self):
        """Setup para cada teste"""
        self.container = DIContainer()
    
    def test_register_and_resolve_singleton(self):
        """Testa registro e resolução de singleton"""
        # Arrange
        instance = MockService("singleton")
        
        # Act
        self.container.register_instance(MockService, instance)
        resolved = self.container.resolve(MockService)
        
        # Assert
        self.assertIs(resolved, instance)
        self.assertEqual(resolved.name, "singleton")
    
    def test_register_and_resolve_transient(self):
        """Testa registro e resolução de transient"""
        # Arrange
        factory = lambda: MockService("transient")
        
        # Act
        self.container.register_transient(MockService, factory)
        resolved1 = self.container.resolve(MockService)
        resolved2 = self.container.resolve(MockService)
        
        # Assert
        self.assertIsNot(resolved1, resolved2)  # Instâncias diferentes
        self.assertEqual(resolved1.name, "transient")
        self.assertEqual(resolved2.name, "transient")
    
    def test_singleton_same_instance(self):
        """Testa que singleton retorna mesma instância"""
        # Arrange
        self.container.register_singleton(MockService, MockService("singleton"))
        
        # Act
        instance1 = self.container.resolve(MockService)
        instance2 = self.container.resolve(MockService)
        
        # Assert
        self.assertIs(instance1, instance2)
    
    def test_dependency_injection(self):
        """Testa injeção de dependência"""
        # Arrange
        self.container.register_singleton(MockService, MockService("dependency"))
        self.container.register_transient(
            MockDependentService,
            lambda: MockDependentService(self.container.resolve(MockService))
        )
        
        # Act
        resolved = self.container.resolve(MockDependentService)
        
        # Assert
        self.assertIsInstance(resolved.dependency, MockService)
        self.assertEqual(resolved.dependency.name, "dependency")
    
    def test_circular_dependency_detection(self):
        """Testa detecção de dependência circular"""
        # Arrange - criar dependência circular via factory
        def create_circular():
            return self.container.resolve(MockService)
        
        self.container.register_transient(MockService, create_circular)
        
        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            self.container.resolve(MockService)
        
        self.assertIn("Dependência circular", str(context.exception))
    
    def test_unregistered_service_error(self):
        """Testa erro para serviço não registrado"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.container.resolve(MockService)
        
        self.assertIn("Serviço não registrado", str(context.exception))
    
    def test_is_registered(self):
        """Testa verificação de registro"""
        # Arrange
        self.container.register_instance(MockService, MockService())
        
        # Act & Assert
        self.assertTrue(self.container.is_registered(MockService))
        self.assertFalse(self.container.is_registered(MockDependentService))
    
    def test_clear_container(self):
        """Testa limpeza do container"""
        # Arrange
        self.container.register_instance(MockService, MockService())
        
        # Act
        self.container.clear()
        
        # Assert
        self.assertFalse(self.container.is_registered(MockService))
    
    def test_get_registered_services(self):
        """Testa listagem de serviços registrados"""
        # Arrange
        self.container.register_instance(MockService, MockService())
        self.container.register_transient(MockDependentService, MockDependentService)
        
        # Act
        services = self.container.get_registered_services()
        
        # Assert
        self.assertIn("MockService", services)
        self.assertIn("MockDependentService", services)

class TestServiceRegistry(unittest.TestCase):
    """Testes críticos do Service Registry"""
    
    def test_configure_services_integration(self):
        """Testa configuração de serviços (teste de integração)"""
        # Arrange
        container = DIContainer()
        
        # Act
        configured_container = configure_services(container)
        
        # Assert
        self.assertIsInstance(configured_container, DIContainer)
        services = configured_container.get_registered_services()
        
        # Verificar serviços essenciais (MessageManager removido - requer UI)
        expected_services = [
            'PathManager', 'DatabaseManager', 'AutomacaoConfig',
            'AutomacaoManager', 'ExecutionManager'
        ]
        
        for service in expected_services:
            self.assertIn(service, services, f"Serviço {service} não encontrado")

class TestInjectDecorator(unittest.TestCase):
    """Testes do decorator de injeção"""
    
    def setUp(self):
        self.container = DIContainer()
        self.container.register_instance(MockService, MockService("injected"))
    
    def test_inject_decorator(self):
        """Testa decorator de injeção"""
        # Arrange
        @inject(self.container)
        def test_function(mock_service: MockService):
            return mock_service.name
        
        # Act
        result = test_function()
        
        # Assert
        self.assertEqual(result, "injected")

if __name__ == '__main__':
    # Executar testes
    unittest.main(verbosity=2)
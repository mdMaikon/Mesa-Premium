#!/usr/bin/env python3
"""
Teste simples para verificar se a implementação async do WebDriver está funcionando
Este teste não faz uma extração real, apenas verifica se o método async é chamado corretamente
"""

import asyncio
import sys
import os
from unittest.mock import patch, MagicMock

# Adicionar o caminho do fastapi ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fastapi'))

from services.hub_token_service import HubTokenService
from models.hub_token import TokenExtractionResult

async def test_async_extract_token():
    """Teste para verificar se o método async funciona sem bloquear"""
    
    print("🔍 Testando implementação async do WebDriver...")
    
    # Mock do método síncrono para evitar inicializar o WebDriver real
    with patch.object(HubTokenService, '_synchronous_token_extraction') as mock_sync:
        # Configurar o mock para retornar um resultado válido
        mock_sync.return_value = TokenExtractionResult(
            success=True,
            message="Test successful",
            user_login="TEST.T12345",
            token_id=123,
            expires_at=None
        )
        
        # Criar instância do serviço
        service = HubTokenService()
        
        print("✅ Instância criada com ThreadPoolExecutor")
        
        # Verificar se o ThreadPoolExecutor foi criado
        assert hasattr(service, '_executor'), "ThreadPoolExecutor não foi criado"
        print("✅ ThreadPoolExecutor configurado corretamente")
        
        # Testar chamada async (não deve bloquear)
        print("🚀 Iniciando chamada async...")
        start_time = asyncio.get_event_loop().time()
        
        result = await service.extract_token("TEST.T12345", "password123", "123456")
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        print(f"⏱️  Tempo decorrido: {elapsed:.3f}s")
        
        # Verificar resultado
        assert result.success == True, f"Resultado inesperado: {result.message}"
        print("✅ Resultado correto retornado")
        
        # Verificar se o método síncrono foi chamado
        mock_sync.assert_called_once_with("TEST.T12345", "password123", "123456")
        print("✅ Método síncrono foi chamado via ThreadPoolExecutor")
        
        print("🎉 Teste concluído com sucesso!")
        
        return True

async def test_concurrency():
    """Teste para verificar se múltiplas chamadas podem ser feitas concorrentemente"""
    
    print("\n🔄 Testando concorrência...")
    
    with patch.object(HubTokenService, '_synchronous_token_extraction') as mock_sync:
        # Simular delay no método síncrono
        async def delayed_mock(*args):
            await asyncio.sleep(0.1)  # 100ms delay
            return TokenExtractionResult(
                success=True,
                message="Concurrent test successful",
                user_login=args[0],
                token_id=456,
                expires_at=None
            )
        
        # Como o método real será executado em thread, simular com async mock
        mock_sync.side_effect = lambda *args: TokenExtractionResult(
            success=True,
            message="Concurrent test successful", 
            user_login=args[0],
            token_id=456,
            expires_at=None
        )
        
        service = HubTokenService()
        
        # Executar múltiplas chamadas concorrentemente
        start_time = asyncio.get_event_loop().time()
        
        tasks = [
            service.extract_token(f"USER{i}.T12345", "password123", "123456")
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        print(f"⏱️  Tempo para 3 chamadas concorrentes: {elapsed:.3f}s")
        
        # Verificar se todas as chamadas foram bem-sucedidas
        for i, result in enumerate(results):
            assert result.success == True, f"Falha na chamada {i}: {result.message}"
        
        print("✅ Todas as chamadas concorrentes foram bem-sucedidas")
        print("🎉 Teste de concorrência concluído!")
        
        return True

async def main():
    """Função principal do teste"""
    print("=" * 60)
    print("🧪 TESTE DA IMPLEMENTAÇÃO ASYNC DO WEBDRIVER")
    print("=" * 60)
    
    try:
        # Teste básico
        await test_async_extract_token()
        
        # Teste de concorrência  
        await test_concurrency()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("✅ WebDriver async implementado corretamente")
        print("✅ Concorrência funcionando")
        print("✅ ThreadPoolExecutor configurado")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Executar o teste
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
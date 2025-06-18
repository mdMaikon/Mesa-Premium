"""
Exemplo de como criar uma automação modular
Template para novas automações
"""

from datetime import datetime
import time

__tags__ = ['exemplo', 'template']

def exemplo_simples(mensagem: str = "Olá Mundo", delay: int = 1):
    """
    Exemplo de automação simples que apenas imprime uma mensagem
    
    Args:
        mensagem: Mensagem a ser exibida
        delay: Delay em segundos antes de finalizar
    
    Returns:
        dict: Resultado da operação
    """
    print(f"Executando automação: {mensagem}")
    time.sleep(delay)
    
    return {
        'success': True,
        'message': f'Automação executada com sucesso: {mensagem}',
        'timestamp': datetime.now().isoformat(),
        'dados': {
            'mensagem_processada': mensagem,
            'delay_usado': delay
        }
    }

class ExemploAutomacaoAvancada:
    """
    Exemplo de automação como classe para casos mais complexos
    """
    
    __tags__ = ['exemplo', 'avancado', 'classe']
    
    def __init__(self):
        self.estado = "inicializado"
        self.contador = 0
    
    def run(self, numero_iteracoes: int = 3, prefixo: str = "Iteração"):
        """
        Executa automação com múltiplas iterações
        
        Args:
            numero_iteracoes: Número de iterações a executar
            prefixo: Prefixo para cada iteração
        
        Returns:
            dict: Resultado com dados de todas as iterações
        """
        resultados = []
        
        for i in range(numero_iteracoes):
            self.contador += 1
            resultado_iteracao = f"{prefixo} {i+1}"
            print(resultado_iteracao)
            resultados.append(resultado_iteracao)
            time.sleep(0.5)
        
        self.estado = "concluído"
        
        return {
            'success': True,
            'message': f'Automação avançada concluída com {numero_iteracoes} iterações',
            'estado_final': self.estado,
            'contador_total': self.contador,
            'resultados_iteracoes': resultados,
            'timestamp': datetime.now().isoformat()
        }
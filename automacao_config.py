import os
from pathlib import Path


class AutomacaoConfig:
    """Gerenciador simplificado para funções utilitárias das automações"""

    def __init__(self, path_manager):
        self.path_manager = path_manager

    def abrir_pasta_automacao(self, nome_automacao, log_callback=None):
        """Abre a pasta específica de uma automação"""
        try:
            # Definir pastas padrão baseadas no nome da automação
            pastas_padrao = {
                "contratos_a_termo": "Contratos a Termo",
                "contratos_termo": "Contratos a Termo", 
                "ordens_estruturadas": "Histórico Estruturadas",
                "ordens_op_estruturadas": "Histórico Estruturadas",
                "processar_cetipados": "Cetipados",
                "cetipados": "Cetipados",
                "renovar_token": "TOKEN",
                "renovar_token_hub_xp": "TOKEN",
                "renovar_token_simplificado": "TOKEN",
                "token": "TOKEN",
                "minimo_por_ordem": "Minimo por Ordem",
                "minimo": "Minimo por Ordem",
                "exemplo_simples": "temp",
                "exemplo_automacao_avancada": "temp"
            }

            # Normalizar nome da automação (converter para snake_case)
            nome_normalizado = nome_automacao.lower().replace(" ", "_").replace("-", "_")
            
            # Buscar pasta correspondente
            pasta_padrao = pastas_padrao.get(nome_normalizado, nome_automacao)
            pasta_trabalho = self.path_manager.get_path('base') / pasta_padrao

            # Criar pasta se não existir
            if not pasta_trabalho.exists():
                pasta_trabalho.mkdir(parents=True, exist_ok=True)
                if log_callback:
                    log_callback(f"📁 Pasta criada: {pasta_trabalho}")

            # Abrir pasta no explorer/file manager
            self._abrir_pasta_sistema(pasta_trabalho)

            if log_callback:
                log_callback(f"📁 Pasta aberta: {pasta_trabalho}")

            return True

        except Exception as e:
            if log_callback:
                log_callback(f"❌ Erro ao abrir pasta: {str(e)}")
            return False

    def _abrir_pasta_sistema(self, caminho_pasta):
        """Abre pasta no gerenciador de arquivos do sistema operacional"""
        import subprocess
        import platform
        
        sistema = platform.system()
        
        try:
            if sistema == "Windows":
                os.startfile(str(caminho_pasta))
            elif sistema == "Darwin":  # macOS
                subprocess.Popen(["open", str(caminho_pasta)])
            else:  # Linux e outros Unix
                subprocess.Popen(["xdg-open", str(caminho_pasta)])
        except Exception as e:
            # Fallback para sistemas que não suportam os métodos acima
            print(f"Não foi possível abrir a pasta automaticamente: {e}")
            print(f"Pasta localizada em: {caminho_pasta}")

    def obter_pasta_automacao(self, nome_automacao):
        """Retorna o caminho da pasta de uma automação sem abrir"""
        try:
            pastas_padrao = {
                "contratos_a_termo": "Contratos a Termo",
                "contratos_termo": "Contratos a Termo", 
                "ordens_estruturadas": "Histórico Estruturadas",
                "ordens_op_estruturadas": "Histórico Estruturadas",
                "processar_cetipados": "Cetipados",
                "cetipados": "Cetipados",
                "renovar_token": "TOKEN",
                "renovar_token_hub_xp": "TOKEN",
                "renovar_token_simplificado": "TOKEN",
                "token": "TOKEN",
                "minimo_por_ordem": "Minimo por Ordem",
                "minimo": "Minimo por Ordem",
                "exemplo_simples": "temp",
                "exemplo_automacao_avancada": "temp"
            }

            nome_normalizado = nome_automacao.lower().replace(" ", "_").replace("-", "_")
            pasta_padrao = pastas_padrao.get(nome_normalizado, nome_automacao)
            return self.path_manager.get_path('base') / pasta_padrao

        except Exception:
            return self.path_manager.get_path('base') / nome_automacao
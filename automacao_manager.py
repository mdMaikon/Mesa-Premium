import os
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Callable, Any
import logging
from datetime import datetime
from database import DatabaseManager

logger = logging.getLogger(__name__)

class AutomacaoManager:
    """Gerenciador de automações modulares"""
    
    def __init__(self, path_manager, db_manager: DatabaseManager):
        self.path_manager = path_manager
        self.db_manager = db_manager
        self.automacoes_registradas = {}
        self.automacoes_meta = {}
        self._carregar_automacoes()
    
    def _carregar_automacoes(self):
        """Carrega todas as automações disponíveis"""
        automacoes_dir = self.path_manager.get_path('automacoes')
        
        if not automacoes_dir.exists():
            logger.warning("Diretório de automações não encontrado")
            return
        
        # Carregar automações Python
        for arquivo_py in automacoes_dir.glob("*.py"):
            if arquivo_py.name == "__init__.py":
                continue
                
            try:
                self._carregar_modulo_automacao(arquivo_py)
            except Exception as e:
                logger.error(f"Erro ao carregar {arquivo_py.name}: {e}")
    
    def _carregar_modulo_automacao(self, arquivo_py):
        """Carrega um módulo de automação específico"""
        module_name = arquivo_py.stem
        spec = importlib.util.spec_from_file_location(module_name, arquivo_py)
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
            
            # Procurar por funções ou classes de automação
            for nome, obj in inspect.getmembers(module):
                if self._e_automacao_valida(obj):
                    self._registrar_automacao(nome, obj, module_name)
                    
        except Exception as e:
            logger.error(f"Erro ao executar módulo {module_name}: {e}")
    
    def _e_automacao_valida(self, obj):
        """Verifica se um objeto é uma automação válida"""
        # Verificar se é função
        if inspect.isfunction(obj):
            return True
            
        # Verificar se é classe com método run
        if inspect.isclass(obj) and hasattr(obj, 'run'):
            return True
            
        return False
    
    def _registrar_automacao(self, nome, obj, module_name):
        """Registra uma automação"""
        # Extrair metadados da docstring ou atributos
        meta = {
            'nome': nome,
            'modulo': module_name,
            'tipo': 'funcao' if inspect.isfunction(obj) else 'classe',
            'descricao': self._extrair_descricao(obj),
            'parametros': self._extrair_parametros(obj),
            'tags': self._extrair_tags(obj)
        }
        
        self.automacoes_registradas[nome] = obj
        self.automacoes_meta[nome] = meta
        
        logger.info(f"Automação registrada: {nome} ({meta['tipo']})")
    
    def _extrair_descricao(self, obj):
        """Extrai descrição da docstring"""
        if obj.__doc__:
            return obj.__doc__.strip().split('\n')[0]
        return "Sem descrição"
    
    def _extrair_parametros(self, obj):
        """Extrai parâmetros da função/método"""
        try:
            if inspect.isfunction(obj):
                sig = inspect.signature(obj)
            elif inspect.isclass(obj) and hasattr(obj, 'run'):
                sig = inspect.signature(obj.run)
            else:
                return []
            
            parametros = []
            for nome, param in sig.parameters.items():
                if nome == 'self':
                    continue
                    
                parametros.append({
                    'nome': nome,
                    'tipo': param.annotation if param.annotation != param.empty else 'any',
                    'padrao': param.default if param.default != param.empty else None,
                    'obrigatorio': param.default == param.empty
                })
            
            return parametros
        except Exception as e:
            logger.warning(f"Erro ao extrair parâmetros: {e}")
            return []
    
    def _extrair_tags(self, obj):
        """Extrai tags do objeto (convenção: atributo __tags__)"""
        return getattr(obj, '__tags__', [])
    
    def listar_automacoes(self, filtrar_token=True) -> List[Dict[str, Any]]:
        """Lista todas as automações disponíveis"""
        automacoes = list(self.automacoes_meta.values())
        
        if filtrar_token:
            # Filtrar automações de token que devem ser chamadas apenas pelo botão
            nomes_token = ['renovar_token', 'renovar_token_hub_xp', 'renovar_token_simplificado', 'renovar_token_gui']
            automacoes = [auto for auto in automacoes if auto['nome'] not in nomes_token]
        
        return automacoes
    
    def obter_automacao(self, nome: str):
        """Obtém uma automação específica"""
        return self.automacoes_registradas.get(nome)
    
    def obter_meta_automacao(self, nome: str):
        """Obtém metadados de uma automação"""
        return self.automacoes_meta.get(nome)
    
    def executar_automacao(self, nome: str, **kwargs):
        """Executa uma automação específica"""
        if nome not in self.automacoes_registradas:
            raise ValueError(f"Automação '{nome}' não encontrada")
        
        automacao = self.automacoes_registradas[nome]
        meta = self.automacoes_meta[nome]
        
        # Registrar início da execução
        execucao_id = self.db_manager.registrar_inicio_execucao(nome)
        
        try:
            logger.info(f"Iniciando execução: {nome}")
            
            if meta['tipo'] == 'funcao':
                resultado = automacao(**kwargs)
            else:  # classe
                instancia = automacao()
                resultado = instancia.run(**kwargs)
            
            # Registrar sucesso
            self.db_manager.registrar_fim_execucao(
                execucao_id, 'CONCLUIDO', dados_resultado=resultado
            )
            
            logger.info(f"Execução concluída: {nome}")
            return resultado
            
        except Exception as e:
            # Registrar erro
            self.db_manager.registrar_fim_execucao(
                execucao_id, 'ERRO', mensagem_erro=str(e)
            )
            logger.error(f"Erro na execução de {nome}: {e}")
            raise
    
    def validar_parametros(self, nome: str, parametros: dict) -> bool:
        """Valida parâmetros antes da execução"""
        meta = self.automacoes_meta.get(nome)
        if not meta:
            return False
        
        params_esperados = meta['parametros']
        
        # Verificar parâmetros obrigatórios
        for param in params_esperados:
            if param['obrigatorio'] and param['nome'] not in parametros:
                logger.error(f"Parâmetro obrigatório '{param['nome']}' não fornecido")
                return False
        
        return True
    
    def obter_historico_execucoes(self, nome: str = None, limite: int = 50):
        """Obtém histórico de execuções"""
        return self.db_manager.obter_historico_execucoes(nome, limite)
    
    def obter_ultima_execucao(self, nome: str):
        """Obtém última execução de uma automação"""
        return self.db_manager.obter_ultima_execucao(nome)
    
    def recarregar_automacoes(self):
        """Recarrega todas as automações"""
        self.automacoes_registradas.clear()
        self.automacoes_meta.clear()
        self._carregar_automacoes()
        logger.info("Automações recarregadas")
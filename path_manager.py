import os
import sys
from pathlib import Path


class PathManager:
    """Gerenciador de caminhos para arquitetura modular"""

    def __init__(self, base_path=None):
        # Detectar ambiente automaticamente
        if base_path:
            self.base_dir = Path(base_path)
        else:
            self.base_dir = self._detect_base_directory()
        
        self.paths = self._setup_paths()
        self._create_directories()

    def _detect_base_directory(self):
        """Detecta o diretório base baseado no ambiente"""
        # Primeira tentativa: usar diretório do projeto
        project_dir = Path(__file__).parent
        
        # Se estiver em WSL ou Linux, usar diretório local
        if os.name == 'posix':
            return project_dir
            
        # No Windows, tentar usar OneDrive se existir
        try:
            userprofile = os.environ.get('USERPROFILE')
            if userprofile:
                onedrive_path = Path(userprofile) / "OneDrive - BLUE3 INVESTIMENTOS ASSESSOR DE INVESTIMENTOS S S LTDA (1)" / "MESA RV" / "AUTOMAÇÕES"
                if onedrive_path.exists():
                    return onedrive_path
        except:
            pass
            
        # Fallback: usar diretório do projeto
        return project_dir

    def _get_base_directory(self):
        """Detecta o diretório base independente de ser script ou .exe"""
        if getattr(sys, 'frozen', False):
            # Executando como .exe (PyInstaller)
            return Path(sys.executable).parent
        else:
            # Executando como script Python
            return Path(__file__).parent

    def _setup_paths(self):
        """Configura todos os caminhos do sistema"""
        return {
            'base': self.base_dir,
            'automacoes': self.base_dir / "automacoes",  # Mudança: pasta para módulos Python
            'configs': self.base_dir / "configs",
            'logs': self.base_dir / "logs", 
            'data': self.base_dir / "data",  # Nova pasta para dados
            'temp': self.base_dir / "temp",  # Nova pasta para arquivos temporários
            'config': self.base_dir / "configs" / "config.json",
            'config_automacoes': self.base_dir / "configs" / "config_automacoes.json"
        }

    def _create_directories(self):
        """Cria diretórios necessários se não existirem"""
        dirs_to_create = ['automacoes', 'logs', 'configs', 'data', 'temp']
        for dir_key in dirs_to_create:
            if dir_key in self.paths and self.paths[dir_key] is not None:
                self.paths[dir_key].mkdir(exist_ok=True, parents=True)

    def get_path(self, key):
        """Retorna caminho seguro"""
        return self.paths.get(key)

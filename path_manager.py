import os
import sys
from pathlib import Path


class PathManager:
    """Gerenciador de caminhos robusto para funcionamento como .exe"""

    def __init__(self):
        self.base_dir = Path(os.environ['USERPROFILE']) / "OneDrive - BLUE3 INVESTIMENTOS ASSESSOR DE INVESTIMENTOS S S LTDA (1)" / \
            "MESA RV" / "AUTOMAÇÕES"
        self.paths = self._setup_paths()
        self._create_directories()

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
            'automacoes': self.base_dir / "Menu",
            'configs': self.base_dir / "Menu" / "configs",
            'logs': self.base_dir / "Menu" / "logs",
            'config': self.base_dir / "Menu" / "configs" / "config.json",
            'config_automacoes': self.base_dir / "Menu" / "configs" / "config_automacoes.json"
        }

    def _create_directories(self):
        """Cria diretórios necessários se não existirem"""
        dirs_to_create = ['automacoes', 'logs', 'configs']
        for dir_key in dirs_to_create:
            if dir_key in self.paths and self.paths[dir_key] is not None:
                self.paths[dir_key].mkdir(exist_ok=True, parents=True)

    def get_path(self, key):
        """Retorna caminho seguro"""
        return self.paths.get(key)

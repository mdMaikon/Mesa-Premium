
# Hook para reduzir tamanho do executável
from PyInstaller.utils.hooks import collect_submodules

# Excluir módulos desnecessários
excludedimports = [
    'matplotlib',
    'scipy',
    'numpy.distutils',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
    'unittest',
    'doctest',
    'pdb',
    'cProfile',
    'profile',
]

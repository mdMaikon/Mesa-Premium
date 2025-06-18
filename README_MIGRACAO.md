# 🚀 Migração para Arquitetura Modular

Este documento descreve a migração do sistema de automações de múltiplos executáveis para uma arquitetura modular baseada em Python + MySQL.

## 📋 O que Mudou

### ❌ Antes (Arquitetura Antiga)
- Múltiplos arquivos `.exe` na pasta "Menu"
- Armazenamento em planilhas Excel locais
- Execução independente de cada automação
- Configurações dispersas em JSON locais

### ✅ Agora (Arquitetura Modular)
- **Ponto único de entrada**: `menu_principal.py`
- **Módulos Python** na pasta `automacoes/`
- **Banco MySQL** centralizado (Hostinger)
- **Gerenciamento unificado** de execuções e dados
- **Histórico completo** de execuções no banco

## 🏗️ Nova Estrutura de Arquivos

```
MenuAutomacoes/
├── menu_principal.py          # 🎯 Aplicação principal
├── database.py                # 🗄️ Gerenciador MySQL  
├── automacao_manager.py       # 🔧 Gerenciador de automações
├── path_manager.py            # 📁 Gerenciador de caminhos
├── automacao_config.py        # ⚙️ Configurações (mantido para compatibilidade)
├── renovar_token.py           # 🔑 Funcionalidade existente
├── requirements.txt           # 📦 Dependências
├── setup_modular.py          # 🛠️ Script de migração
├── .env                      # 🔐 Credenciais MySQL
├── automacoes/               # 📂 Módulos de automação
│   ├── __init__.py
│   ├── renovar_token.py      # 🔄 Token modularizado  
│   └── exemplo_automacao.py  # 📝 Template
├── configs/                  # ⚙️ Configurações
├── logs/                     # 📋 Logs do sistema
├── data/                     # 💾 Dados temporários
└── temp/                     # 🗂️ Arquivos temporários
```

## 🗄️ Estrutura do Banco de Dados

### Tabela: `automacoes_execucoes`
Registra todas as execuções de automações:
- `id` - ID único da execução
- `nome_automacao` - Nome da automação executada
- `status` - Status (EXECUTANDO, CONCLUIDO, ERRO)
- `inicio_execucao` / `fim_execucao` - Timestamps
- `tempo_execucao` - Duração em segundos
- `mensagem_erro` - Erros se houver
- `dados_resultado` - Resultado em JSON
- `usuario` - Usuário que executou

### Tabela: `automacoes_dados`
Armazena dados específicos de cada automação:
- `automacao_id` - Referência à execução
- `tipo_dado` - Tipo dos dados salvos
- `dados` - Dados em formato JSON
- `hash_dados` - Hash para evitar duplicatas

### Tabela: `configuracoes_sistema`
Configurações centralizadas:
- `chave` / `valor` - Pares chave-valor
- `categoria` - Agrupamento de configurações

## 🔧 Como Migrar

### 1. Executar Setup Automático
```bash
python setup_modular.py
```

### 2. Configurar Banco MySQL
1. Copie `.env.exemplo` para `.env`
2. Configure suas credenciais da Hostinger:
```env
DB_HOST=seu_host_hostinger
DB_USER=seu_usuario
DB_PASSWORD=sua_senha  
DB_NAME=seu_banco
DB_PORT=3306
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Testar Conexão
```bash
python -c "from database import DatabaseManager; print('OK' if DatabaseManager().test_connection() else 'ERRO')"
```

### 5. Executar Nova Interface
```bash
python menu_principal.py
```

## 📝 Como Criar Novas Automações

### Método 1: Função Simples
```python
# automacoes/minha_automacao.py

def minha_automacao(parametro1: str, parametro2: int = 10):
    """
    Descrição da automação
    
    Args:
        parametro1: Descrição do parâmetro
        parametro2: Parâmetro opcional com valor padrão
    
    Returns:
        dict: Resultado da operação
    """
    # Sua lógica aqui
    
    return {
        'success': True,
        'message': 'Automação executada com sucesso',
        'dados': {'resultado': 'exemplo'}
    }
```

### Método 2: Classe Avançada
```python
# automacoes/automacao_complexa.py

class AutomacaoComplexa:
    """Automação complexa com estado"""
    
    def __init__(self):
        self.estado = {}
    
    def run(self, **kwargs):
        """Método principal de execução"""
        # Sua lógica aqui
        return {'success': True, 'message': 'Concluído'}
```

## 🔄 Migração de Automações Existentes

Para cada `.exe` antigo:

1. **Identifique a lógica**: O que o executável fazia?
2. **Crie módulo Python**: Converta a lógica para função/classe
3. **Integre com banco**: Use `database.py` para salvar dados
4. **Teste isoladamente**: Execute via `AutomacaoManager`
5. **Registre no menu**: Aparecerá automaticamente

## 🎯 Benefícios da Nova Arquitetura

### ✅ Para Desenvolvimento
- **Código unificado** em um repositório
- **Versionamento** completo com Git
- **Debugging** mais fácil
- **Reutilização** de código entre automações

### ✅ Para Operação  
- **Histórico completo** no banco MySQL
- **Monitoramento** de execuções em tempo real
- **Dados centralizados** e seguros
- **Backup** automático na nuvem

### ✅ Para Manutenção
- **Atualizações** sem recompilar executáveis
- **Configuração** centralizada
- **Logs** estruturados e pesquisáveis
- **Diagnóstico** rápido de problemas

## 🚨 Pontos de Atenção

1. **Backup**: Faça backup dos `.exe` antigos antes de migrar
2. **Dependências**: Algumas automações podem precisar de bibliotecas específicas
3. **Credenciais**: Configure corretamente o `.env` 
4. **Testes**: Teste cada automação migrada individualmente
5. **Performance**: Monitor o desempenho do banco MySQL

## 🆘 Solução de Problemas

### Erro de Conexão MySQL
```bash
# Verificar se credenciais estão corretas
cat .env

# Testar conexão manual
python -c "import mysql.connector; mysql.connector.connect(host='HOST', user='USER', password='PASS')"
```

### Automação Não Aparece no Menu
1. Verifique se o arquivo está em `automacoes/`
2. Verifique se a função tem `def` ou classe tem `run()`
3. Restart o menu: F5 ou botão "Atualizar"

### Erro de Import
```bash
# Verificar dependências faltando
pip install -r requirements.txt

# Verificar estrutura de pastas
ls -la automacoes/
```

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs em `logs/`
2. Execute `setup_modular.py` novamente
3. Consulte este README
4. Verifique se todas as dependências estão instaladas

---

*Migração concluída com sucesso! 🎉*
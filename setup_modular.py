#!/usr/bin/env python3
"""
Script de setup e migração para a nova arquitetura modular
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def criar_estrutura_diretorios():
    """Cria estrutura de diretórios necessária"""
    diretorios = [
        'automacoes',
        'configs', 
        'logs',
        'data',
        'temp'
    ]
    
    base_dir = Path(__file__).parent
    
    for diretorio in diretorios:
        caminho = base_dir / diretorio
        caminho.mkdir(exist_ok=True, parents=True)
        print(f"✓ Diretório criado/verificado: {caminho}")

def criar_arquivo_env_exemplo():
    """Cria arquivo .env.exemplo com template"""
    env_exemplo = """# Configurações do banco de dados MySQL (Hostinger)
DB_HOST=localhost
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=nome_do_banco
DB_PORT=3306

# Configurações opcionais
DEBUG=False
LOG_LEVEL=INFO
"""
    
    arquivo_env = Path(__file__).parent / '.env.exemplo'
    with open(arquivo_env, 'w', encoding='utf-8') as f:
        f.write(env_exemplo)
    
    print(f"✓ Arquivo criado: {arquivo_env}")
    print("  IMPORTANTE: Copie .env.exemplo para .env e configure suas credenciais MySQL")

def migrar_configuracoes_antigas():
    """Migra configurações do formato antigo se existirem"""
    base_dir = Path(__file__).parent
    
    # Verificar se existe estrutura antiga
    pasta_antiga = None
    try:
        userprofile = os.environ.get('USERPROFILE')
        if userprofile:
            pasta_antiga = Path(userprofile) / "OneDrive - BLUE3 INVESTIMENTOS ASSESSOR DE INVESTIMENTOS S S LTDA (1)" / "MESA RV" / "AUTOMAÇÕES" / "Menu"
    except:
        pass
    
    if pasta_antiga and pasta_antiga.exists():
        print(f"📁 Encontrada estrutura antiga em: {pasta_antiga}")
        
        # Migrar configurações
        configs_antigas = [
            'configs/config.json',
            'configs/config_automacoes.json'
        ]
        
        for config_path in configs_antigas:
            arquivo_antigo = pasta_antiga / config_path
            if arquivo_antigo.exists():
                arquivo_novo = base_dir / config_path
                
                try:
                    with open(arquivo_antigo, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    with open(arquivo_novo, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✓ Migrado: {config_path}")
                except Exception as e:
                    print(f"⚠️  Erro ao migrar {config_path}: {e}")
        
        # Migrar logs se existirem
        logs_antigos = pasta_antiga / 'logs'
        if logs_antigos.exists():
            logs_novos = base_dir / 'logs'
            print(f"📋 Logs antigos encontrados em: {logs_antigos}")
            print(f"   Você pode copiar manualmente para: {logs_novos}")
    else:
        print("ℹ️  Nenhuma estrutura antiga encontrada")

def verificar_dependencias():
    """Verifica se dependências críticas estão instaladas"""
    dependencias_criticas = [
        'customtkinter',
        'mysql.connector',
        'dotenv',
        'selenium'
    ]
    
    dependencias_faltando = []
    
    for dep in dependencias_criticas:
        try:
            __import__(dep.replace('.', '_') if '.' in dep else dep)
            print(f"✓ {dep}")
        except ImportError:
            dependencias_faltando.append(dep)
            print(f"✗ {dep} - FALTANDO")
    
    if dependencias_faltando:
        print(f"\n⚠️  Dependências faltando: {', '.join(dependencias_faltando)}")
        print("   Execute: pip install -r requirements.txt")
        return False
    
    print("\n✓ Todas as dependências críticas estão instaladas")
    return True

def testar_conexao_banco():
    """Testa conexão com banco de dados se .env existir"""
    env_file = Path(__file__).parent / '.env'
    
    if not env_file.exists():
        print("ℹ️  Arquivo .env não encontrado - configuração do banco pendente")
        return False
    
    try:
        from dotenv import load_dotenv
        from database import DatabaseManager
        
        load_dotenv(env_file)
        
        db = DatabaseManager()
        if db.test_connection():
            print("✓ Conexão com banco de dados MySQL funcionando")
            return True
        else:
            print("✗ Falha na conexão com banco de dados")
            return False
            
    except Exception as e:
        print(f"✗ Erro ao testar banco: {e}")
        return False

def criar_automacao_exemplo():
    """Cria arquivo de exemplo se não existir"""
    arquivo_exemplo = Path(__file__).parent / 'automacoes' / 'exemplo_automacao.py'
    
    if not arquivo_exemplo.exists():
        print("ℹ️  Arquivo de exemplo já foi criado anteriormente")
    else:
        print("✓ Arquivo de exemplo de automação disponível")

def main():
    """Função principal do setup"""
    print("🚀 Setup da Nova Arquitetura Modular - MenuAutomacoes\n")
    
    print("1️⃣  Criando estrutura de diretórios...")
    criar_estrutura_diretorios()
    
    print("\n2️⃣  Criando arquivo de configuração...")
    criar_arquivo_env_exemplo()
    
    print("\n3️⃣  Verificando migração de configurações antigas...")
    migrar_configuracoes_antigas()
    
    print("\n4️⃣  Verificando dependências...")
    deps_ok = verificar_dependencias()
    
    print("\n5️⃣  Testando conexão com banco de dados...")
    db_ok = testar_conexao_banco()
    
    print("\n6️⃣  Verificando arquivos de exemplo...")
    criar_automacao_exemplo()
    
    print("\n" + "="*60)
    print("📋 RESUMO DO SETUP")
    print("="*60)
    
    if deps_ok:
        print("✓ Dependências: OK")
    else:
        print("✗ Dependências: INSTALAR")
    
    if db_ok:
        print("✓ Banco de dados: OK")
    else:
        print("✗ Banco de dados: CONFIGURAR")
    
    print("\n📚 PRÓXIMOS PASSOS:")
    
    if not deps_ok:
        print("1. Instalar dependências: pip install -r requirements.txt")
    
    if not db_ok:
        print("2. Configurar .env com credenciais MySQL da Hostinger")
        print("3. Testar conexão: python -c \"from database import DatabaseManager; DatabaseManager().test_connection()\"")
    
    print("4. Executar aplicação: python menu_principal.py")
    
    print(f"\n✅ Setup concluído em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

if __name__ == "__main__":
    main()
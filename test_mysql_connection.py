#!/usr/bin/env python3
"""
Script para testar conexão com o banco MySQL no VPS
"""

import os

from dotenv import load_dotenv

import mysql.connector
from mysql.connector import Error


def test_mysql_connection():
    """Testa conexão com o banco MySQL do VPS"""

    # Carregar variáveis de ambiente
    load_dotenv()

    # Configurações do banco
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "charset": os.getenv("DB_CHARSET", "utf8mb4"),
        "connection_timeout": int(os.getenv("DB_CONNECTION_TIMEOUT", 10)),
        "autocommit": os.getenv("DB_AUTOCOMMIT", "True").lower() == "true",
    }

    print("=== TESTE DE CONEXÃO MYSQL VPS ===")
    print(f"Host: {config['host']}")
    print(f"Porta: {config['port']}")
    print(f"Usuário: {config['user']}")
    print(f"Banco: {config['database']}")
    print(f"Charset: {config['charset']}")
    print("=" * 40)

    connection = None

    try:
        # Tentar conexão
        print("Conectando ao MySQL...")
        connection = mysql.connector.connect(**config)

        if connection.is_connected():
            print("✅ Conexão estabelecida com sucesso!")

            # Informações do servidor
            db_info = connection.get_server_info()
            print(f"Versão do MySQL: {db_info}")

            # Executar query de teste
            cursor = connection.cursor()

            # Verificar se estamos no banco correto
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()[0]
            print(f"Banco atual: {current_db}")

            # Listar tabelas existentes
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            if tables:
                print(f"Tabelas encontradas ({len(tables)}):")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("Nenhuma tabela encontrada no banco")

            # Testar inserção simples
            print("\nTestando inserção...")
            test_query = """
            CREATE TABLE IF NOT EXISTS connection_test (
                id INT AUTO_INCREMENT PRIMARY KEY,
                test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50)
            )
            """
            cursor.execute(test_query)

            insert_query = "INSERT INTO connection_test (status) VALUES ('Teste de conexão OK')"
            cursor.execute(insert_query)
            connection.commit()

            # Verificar inserção
            cursor.execute("SELECT COUNT(*) FROM connection_test")
            count = cursor.fetchone()[0]
            print(f"Registros na tabela de teste: {count}")

            # Limpar tabela de teste
            cursor.execute("DROP TABLE connection_test")
            connection.commit()

            print("✅ Teste de inserção/remoção concluído com sucesso!")

            cursor.close()

    except Error as e:
        print(f"❌ Erro ao conectar com MySQL: {e}")

        # Diagnósticos adicionais
        if "Access denied" in str(e):
            print("\n🔍 Possíveis causas:")
            print("- Usuário ou senha incorretos")
            print("- Usuário não criado ou sem permissões")
            print("- Verificar se o usuário tem acesso de 'localhost'")

        elif "Can't connect" in str(e):
            print("\n🔍 Possíveis causas:")
            print("- MySQL não está rodando")
            print("- Firewall bloqueando conexão")
            print("- Host/porta incorretos")

        elif "Unknown database" in str(e):
            print("\n🔍 Possíveis causas:")
            print("- Banco de dados não foi criado")
            print("- Nome do banco incorreto")

        return False

    finally:
        if connection and connection.is_connected():
            connection.close()
            print("Conexão fechada.")

    return True


def check_mysql_service():
    """Verifica se o serviço MySQL está rodando"""
    print("\n=== VERIFICAÇÃO DO SERVIÇO MYSQL ===")

    try:
        import subprocess

        # Verificar status do MySQL
        result = subprocess.run(  # nosec B607
            ["/usr/bin/systemctl", "status", "mysql"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Serviço MySQL está rodando")
            return True
        else:
            print("❌ Serviço MySQL não está rodando")
            print("Execute: sudo systemctl start mysql")
            return False

    except Exception as e:
        print(f"Erro ao verificar serviço: {e}")
        return False


if __name__ == "__main__":
    print("TESTE DE CONEXÃO COM BANCO MYSQL VPS")
    print("=" * 50)

    # Verificar se o MySQL está rodando
    mysql_running = check_mysql_service()

    if mysql_running:
        # Testar conexão
        success = test_mysql_connection()

        if success:
            print(
                "\n🎉 Todos os testes passaram! Banco configurado corretamente."
            )
        else:
            print("\n⚠️  Há problemas na configuração do banco.")
    else:
        print("\n⚠️  MySQL não está rodando. Inicie o serviço primeiro.")

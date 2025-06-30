#!/usr/bin/env python3
"""
Script para testar conexão com MySQL via Docker
"""

import os
import time

from dotenv import load_dotenv

import mysql.connector
from mysql.connector import Error


def test_docker_mysql():
    """Testa conexão com MySQL no Docker"""

    load_dotenv()

    config = {
        "host": os.getenv("DB_HOST", "mysql"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "charset": os.getenv("DB_CHARSET", "utf8mb4"),
        "connection_timeout": int(os.getenv("DB_CONNECTION_TIMEOUT", 10)),
    }

    # Para Docker, precisamos resolver o host
    if config["host"] == "mysql":
        config["host"] = "localhost"

    print("=== TESTE CONEXÃO MYSQL DOCKER ===")
    print(f"Host: {config['host']}")
    print(f"Porta: {config['port']}")
    print(f"Usuário: {config['user']}")
    print(f"Banco: {config['database']}")
    print("=" * 35)

    # Tentar algumas vezes (MySQL pode estar inicializando)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Tentativa {attempt + 1}/{max_retries}...")
            connection = mysql.connector.connect(**config)

            if connection.is_connected():
                print("✅ Conexão estabelecida!")

                cursor = connection.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                print(f"Versão MySQL: {version}")

                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"Tabelas: {len(tables)}")

                cursor.close()
                connection.close()
                return True

        except Error as e:
            print(f"❌ Erro tentativa {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print("Aguardando 5 segundos...")
                time.sleep(5)

    return False


if __name__ == "__main__":
    success = test_docker_mysql()
    if success:
        print("\n🎉 MySQL Docker funcionando!")
    else:
        print("\n⚠️ Falha na conexão com MySQL Docker")

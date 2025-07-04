#!/usr/bin/env python3
"""
Script de migração para criptografar dados existentes na tabela hub_tokens.

Este script:
1. Verifica se há dados não criptografados na tabela
2. Criptografa user_login e token existentes
3. Gera hash de busca para user_login
4. Atualiza os registros com dados criptografados
5. Remove registros antigos/inválidos após migração

IMPORTANTE:
- Execute este script apenas uma vez após implementar a criptografia
- Faça backup da tabela hub_tokens antes de executar
- Configure as variáveis de ambiente CRYPTO_MASTER_KEY e CRYPTO_SALT_HUB_TOKENS
"""

import os
import sys
from typing import Any

# Add fastapi to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fastapi"))

from database.connection import execute_query
from utils.crypto_utils import (
    encrypt_token_data,
    encrypt_user_login_with_hash,
    validate_crypto_environment,
)
from utils.log_sanitizer import get_sanitized_logger

logger = get_sanitized_logger(__name__)


def check_crypto_environment() -> bool:
    """Verifica se o ambiente de criptografia está configurado."""
    try:
        return validate_crypto_environment()
    except Exception as e:
        logger.error(f"Erro validando ambiente de criptografia: {e}")
        return False


def get_existing_tokens() -> list[dict[str, Any]]:
    """Obtém tokens existentes da tabela."""
    try:
        query = """
            SELECT id, user_login, token, expires_at, extracted_at, created_at
            FROM hub_tokens
            WHERE user_login_hash IS NULL OR user_login_hash = ''
            ORDER BY created_at DESC
        """

        result = execute_query(query, fetch=True)
        return result if result else []

    except Exception as e:
        logger.error(f"Erro obtendo tokens existentes: {e}")
        return []


def migrate_token_record(token_record: dict[str, Any]) -> bool:
    """Migra um registro de token para formato criptografado."""
    try:
        user_login = token_record["user_login"]
        token = token_record["token"]

        # Preparar dados criptografados (usado como referência)

        # Criptografar dados
        encrypted_login, user_hash = encrypt_user_login_with_hash(user_login)
        encrypted_token = encrypt_token_data(token)

        # Atualizar registro
        update_query = """
            UPDATE hub_tokens
            SET user_login = %s, user_login_hash = %s, token = %s
            WHERE id = %s
        """

        execute_query(
            update_query,
            (encrypted_login, user_hash, encrypted_token, token_record["id"]),
        )

        logger.info(f"Token migrado com sucesso - ID: {token_record['id']}")
        return True

    except Exception as e:
        logger.error(f"Erro migrando token ID {token_record['id']}: {e}")
        return False


def verify_migration() -> bool:
    """Verifica se a migração foi bem-sucedida."""
    try:
        # Contar registros não migrados
        query = """
            SELECT COUNT(*) as count
            FROM hub_tokens
            WHERE user_login_hash IS NULL OR user_login_hash = ''
        """

        result = execute_query(query, fetch=True)
        unmigrated_count = result[0]["count"] if result else 0

        # Contar registros migrados
        query = """
            SELECT COUNT(*) as count
            FROM hub_tokens
            WHERE user_login_hash IS NOT NULL AND user_login_hash != ''
        """

        result = execute_query(query, fetch=True)
        migrated_count = result[0]["count"] if result else 0

        logger.info(f"Registros migrados: {migrated_count}")
        logger.info(f"Registros não migrados: {unmigrated_count}")

        return unmigrated_count == 0

    except Exception as e:
        logger.error(f"Erro verificando migração: {e}")
        return False


def cleanup_old_records() -> bool:
    """Remove registros antigos/inválidos após migração."""
    try:
        # Remove registros duplicados mantendo apenas o mais recente por usuário
        cleanup_query = """
            DELETE t1 FROM hub_tokens t1
            INNER JOIN hub_tokens t2
            WHERE t1.user_login_hash = t2.user_login_hash
            AND t1.created_at < t2.created_at
        """

        execute_query(cleanup_query)
        logger.info("Registros duplicados removidos com sucesso")

        # Remove registros muito antigos (mais de 1 ano)
        cleanup_query = """
            DELETE FROM hub_tokens
            WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR)
        """

        execute_query(cleanup_query)
        logger.info("Registros antigos removidos com sucesso")

        return True

    except Exception as e:
        logger.error(f"Erro durante limpeza: {e}")
        return False


def main():
    """Função principal de migração."""
    logger.info("=== Iniciando Migração de Criptografia ===")

    # Verificar ambiente
    if not check_crypto_environment():
        logger.error("❌ Ambiente de criptografia não configurado!")
        logger.error("Configure CRYPTO_MASTER_KEY e CRYPTO_SALT_HUB_TOKENS")
        return False

    logger.info("✅ Ambiente de criptografia validado")

    # Obter tokens existentes
    existing_tokens = get_existing_tokens()

    if not existing_tokens:
        logger.info(
            "✅ Nenhum token para migrar - todos já estão criptografados"
        )
        return True

    logger.info(f"📋 Encontrados {len(existing_tokens)} tokens para migrar")

    # Migrar cada token
    success_count = 0
    failed_count = 0

    for token_record in existing_tokens:
        if migrate_token_record(token_record):
            success_count += 1
        else:
            failed_count += 1

    logger.info(
        f"✅ Migração concluída: {success_count} sucessos, {failed_count} falhas"
    )

    # Verificar migração
    if verify_migration():
        logger.info("✅ Migração verificada com sucesso")

        # Limpeza opcional
        if cleanup_old_records():
            logger.info("✅ Limpeza concluída")
        else:
            logger.warning(
                "⚠️ Falha na limpeza - mas migração foi bem-sucedida"
            )

        return True
    else:
        logger.error("❌ Verificação de migração falhou")
        return False


if __name__ == "__main__":
    print("Migração de Criptografia - Hub Tokens")
    print("=" * 50)

    # Verificar se as variáveis de ambiente estão configuradas
    if not os.getenv("CRYPTO_MASTER_KEY"):
        print("❌ CRYPTO_MASTER_KEY não configurada!")
        print(
            "Configure as variáveis de ambiente antes de executar a migração."
        )
        sys.exit(1)

    if not os.getenv("CRYPTO_SALT_HUB_TOKENS"):
        print("❌ CRYPTO_SALT_HUB_TOKENS não configurada!")
        print(
            "Configure as variáveis de ambiente antes de executar a migração."
        )
        sys.exit(1)

    # Executar migração
    success = main()

    print("=" * 50)
    if success:
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("Todos os tokens foram criptografados e estão seguros.")
    else:
        print("❌ FALHA NA MIGRAÇÃO!")
        print("Verifique os logs para mais detalhes.")

    sys.exit(0 if success else 1)

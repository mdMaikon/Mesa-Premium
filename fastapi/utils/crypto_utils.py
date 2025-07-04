"""
Utilitários de criptografia específicos para os serviços.

Este módulo fornece funções de conveniência para os serviços específicos,
encapsulando a funcionalidade do módulo crypto.py principal.
"""

try:
    from .crypto import (
        CryptoError,
        decrypt_field,
        encrypt_field,
        encrypt_with_hash,
        generate_search_hash,
    )
except ImportError:
    try:
        # Para testes diretos e desenvolvimento
        from crypto import (
            CryptoError,
            decrypt_field,
            encrypt_field,
            encrypt_with_hash,
            generate_search_hash,
        )
    except ImportError:
        # Para container Docker
        from utils.crypto import (
            CryptoError,
            decrypt_field,
            encrypt_field,
            encrypt_with_hash,
            generate_search_hash,
        )


def encrypt_token_data(data: str) -> str:
    """
    Criptografa dados da tabela hub_tokens.

    Args:
        data: Dados a serem criptografados (user_login ou token).

    Returns:
        Dados criptografados em base64.

    Raises:
        CryptoError: Se houver erro na criptografia.
    """
    return encrypt_field(data, "hub_tokens")


def decrypt_token_data(encrypted_data: str) -> str:
    """
    Descriptografa dados da tabela hub_tokens.

    Args:
        encrypted_data: Dados criptografados em base64.

    Returns:
        Dados descriptografados.

    Raises:
        CryptoError: Se houver erro na descriptografia.
    """
    return decrypt_field(encrypted_data, "hub_tokens")


def generate_user_hash(user_login: str) -> str:
    """
    Gera hash determinístico para user_login (hub_tokens).

    Args:
        user_login: Login do usuário.

    Returns:
        Hash determinístico em hexadecimal.
    """
    return generate_search_hash(user_login, "hub_tokens")


def encrypt_user_with_hash(user_login: str) -> tuple[str, str]:
    """
    Criptografa user_login e gera hash para busca.

    Args:
        user_login: Login do usuário.

    Returns:
        Tupla (user_login_criptografado, user_login_hash).
    """
    return encrypt_with_hash(user_login, "hub_tokens")


def encrypt_fixed_income_data(data: str) -> str:
    """
    Criptografa dados da tabela fixed_income_data.

    Args:
        data: Dados a serem criptografados.

    Returns:
        Dados criptografados em base64.
    """
    return encrypt_field(data, "fixed_income_data")


def decrypt_fixed_income_data(encrypted_data: str) -> str:
    """
    Descriptografa dados da tabela fixed_income_data.

    Args:
        encrypted_data: Dados criptografados.

    Returns:
        Dados descriptografados.
    """
    return decrypt_field(encrypted_data, "fixed_income_data")


def encrypt_structured_data(data: str) -> str:
    """
    Criptografa dados da tabela structured_data.

    Args:
        data: Dados a serem criptografados.

    Returns:
        Dados criptografados em base64.
    """
    return encrypt_field(data, "structured_data")


def decrypt_structured_data(encrypted_data: str) -> str:
    """
    Descriptografa dados da tabela structured_data.

    Args:
        encrypted_data: Dados criptografados.

    Returns:
        Dados descriptografados.
    """
    return decrypt_field(encrypted_data, "structured_data")


def generate_ticket_hash(ticket_id: str) -> str:
    """
    Gera hash determinístico para ticket_id (structured_data).

    Args:
        ticket_id: ID do ticket.

    Returns:
        Hash determinístico em hexadecimal.
    """
    return generate_search_hash(ticket_id, "structured_data")


def encrypt_ticket_with_hash(ticket_id: str) -> tuple[str, str]:
    """
    Criptografa ticket_id e gera hash para busca.

    Args:
        ticket_id: ID do ticket.

    Returns:
        Tupla (ticket_id_criptografado, ticket_id_hash).
    """
    return encrypt_with_hash(ticket_id, "structured_data")


# Funções de conveniência para tratamento de erros
def safe_encrypt(data: str, table_name: str, default: str = "") -> str:
    """
    Criptografia segura com tratamento de erro.

    Args:
        data: Dados a serem criptografados.
        table_name: Nome da tabela.
        default: Valor padrão em caso de erro.

    Returns:
        Dados criptografados ou valor padrão.
    """
    try:
        if not data:
            return default
        return encrypt_field(data, table_name)
    except CryptoError:
        return default


def safe_decrypt(
    encrypted_data: str, table_name: str, default: str = ""
) -> str:
    """
    Descriptografia segura com tratamento de erro.

    Args:
        encrypted_data: Dados criptografados.
        table_name: Nome da tabela.
        default: Valor padrão em caso de erro.

    Returns:
        Dados descriptografados ou valor padrão.
    """
    try:
        if not encrypted_data:
            return default
        return decrypt_field(encrypted_data, table_name)
    except CryptoError:
        return default


def validate_crypto_environment() -> bool:
    """
    Valida se o ambiente de criptografia está configurado corretamente.

    Returns:
        bool: True se o ambiente está válido, False caso contrário.
    """
    import os

    try:
        # Verifica se as variáveis de ambiente necessárias estão definidas
        required_vars = [
            "CRYPTO_MASTER_KEY",
            "CRYPTO_SALT_HUB_TOKENS",
            "CRYPTO_SALT_FIXED_INCOME_DATA",
            "CRYPTO_SALT_STRUCTURED_DATA",
        ]

        for var in required_vars:
            if not os.getenv(var):
                return False

        # Testa uma operação básica de criptografia
        test_data = "test_validation"
        encrypted = encrypt_token_data(test_data)
        decrypted = decrypt_token_data(encrypted)

        return decrypted == test_data
    except Exception:
        return False


def prepare_token_for_storage(user_login: str, token_data: dict) -> dict:
    """
    Prepara dados de token para armazenamento criptografado.

    Args:
        user_login: Login do usuário.
        token_data: Dados do token.

    Returns:
        dict: Dados preparados para armazenamento com criptografia.
    """
    # Criptografa user_login e gera hash
    encrypted_user_login, user_login_hash = encrypt_user_with_hash(user_login)

    # Criptografa token
    encrypted_token = encrypt_token_data(token_data["token"])

    return {
        "user_login": encrypted_user_login,
        "user_login_hash": user_login_hash,
        "token": encrypted_token,
        "expires_at": token_data["expires_at"],
        "extracted_at": token_data["extracted_at"],
    }


def prepare_token_from_storage(encrypted_data: dict) -> dict:
    """
    Prepara dados de token descriptografados vindos do armazenamento.

    Args:
        encrypted_data: Dados criptografados do banco.

    Returns:
        dict: Dados descriptografados.
    """
    # Descriptografa dados
    decrypted_user_login = decrypt_token_data(encrypted_data["user_login"])
    decrypted_token = decrypt_token_data(encrypted_data["token"])

    return {
        "user_login": decrypted_user_login,
        "token": decrypted_token,
        "expires_at": encrypted_data["expires_at"],
        "extracted_at": encrypted_data["extracted_at"],
        "created_at": encrypted_data["created_at"],
    }


def prepare_structured_for_storage(record_data: dict) -> dict:
    """
    Prepara dados de structured_data para armazenamento criptografado.

    Args:
        record_data: Dados do registro structured.

    Returns:
        dict: Dados preparados para armazenamento com criptografia.
    """
    prepared_data = record_data.copy()

    # Criptografa ticket_id e gera hash
    if record_data.get("ticket_id"):
        encrypted_ticket_id, ticket_id_hash = encrypt_ticket_with_hash(
            str(record_data["ticket_id"])
        )
        prepared_data["ticket_id"] = encrypted_ticket_id
        prepared_data["ticket_id_hash"] = ticket_id_hash

    # Criptografa outros campos sensíveis
    sensitive_fields = ["ativo", "estrutura", "aai_ordem"]
    for field in sensitive_fields:
        if record_data.get(field):
            prepared_data[field] = encrypt_structured_data(
                str(record_data[field])
            )

    # Criptografa cliente (convertido para string)
    if record_data.get("cliente") is not None:
        prepared_data["cliente"] = encrypt_structured_data(
            str(record_data["cliente"])
        )

    # Criptografa comissao (convertido para string)
    if record_data.get("comissao") is not None:
        prepared_data["comissao"] = encrypt_structured_data(
            str(record_data["comissao"])
        )

    return prepared_data


def prepare_structured_from_storage(encrypted_data: dict) -> dict:
    """
    Prepara dados de structured_data descriptografados vindos do armazenamento.

    Args:
        encrypted_data: Dados criptografados do banco.

    Returns:
        dict: Dados descriptografados.
    """
    decrypted_data = encrypted_data.copy()

    # Descriptografa ticket_id
    if encrypted_data.get("ticket_id"):
        decrypted_data["ticket_id"] = decrypt_structured_data(
            encrypted_data["ticket_id"]
        )

    # Descriptografa outros campos sensíveis
    sensitive_fields = ["ativo", "estrutura", "aai_ordem"]
    for field in sensitive_fields:
        if encrypted_data.get(field):
            decrypted_data[field] = decrypt_structured_data(
                encrypted_data[field]
            )

    # Descriptografa e converte cliente para int
    if encrypted_data.get("cliente"):
        try:
            cliente_str = decrypt_structured_data(encrypted_data["cliente"])
            decrypted_data["cliente"] = (
                int(cliente_str) if cliente_str != "None" else None
            )
        except (ValueError, CryptoError):
            decrypted_data["cliente"] = None

    # Descriptografa e converte comissao para Decimal
    if encrypted_data.get("comissao"):
        try:
            from decimal import Decimal

            comissao_str = decrypt_structured_data(encrypted_data["comissao"])
            decrypted_data["comissao"] = (
                Decimal(comissao_str) if comissao_str != "None" else None
            )
        except (ValueError, CryptoError):
            decrypted_data["comissao"] = None

    return decrypted_data


def mask_structured_data(data: dict) -> dict:
    """
    Mascarar dados sensíveis de structured_data para logs e respostas.

    Args:
        data: Dados a serem mascarados.

    Returns:
        dict: Dados com campos sensíveis mascarados.
    """
    if not data:
        return data

    masked_data = data.copy()

    # Mascarar campos sensíveis
    if "ticket_id" in masked_data and masked_data["ticket_id"]:
        ticket_id = str(masked_data["ticket_id"])
        if len(ticket_id) > 4:
            masked_data["ticket_id"] = (
                ticket_id[:2] + "*" * (len(ticket_id) - 4) + ticket_id[-2:]
            )
        else:
            masked_data["ticket_id"] = "*" * len(ticket_id)

    if "ativo" in masked_data and masked_data["ativo"]:
        ativo = str(masked_data["ativo"])
        if len(ativo) > 4:
            masked_data["ativo"] = (
                ativo[:2] + "*" * (len(ativo) - 4) + ativo[-2:]
            )
        else:
            masked_data["ativo"] = "*" * len(ativo)

    if "aai_ordem" in masked_data and masked_data["aai_ordem"]:
        masked_data["aai_ordem"] = "***MASKED***"

    if "cliente" in masked_data and masked_data["cliente"]:
        # Manter o tipo int mas mascarar o valor
        masked_data["cliente"] = 999999  # Valor mascarado genérico

    if "comissao" in masked_data and masked_data["comissao"]:
        # Manter o tipo Decimal mas mascarar o valor
        from decimal import Decimal

        masked_data["comissao"] = Decimal("0.00")  # Valor mascarado genérico

    return masked_data


def prepare_fixed_income_for_storage(record_data: dict) -> dict:
    """
    Prepara dados de fixed_income_data para armazenamento criptografado.

    Args:
        record_data: Dados do registro fixed income.

    Returns:
        dict: Dados preparados para armazenamento com criptografia.
    """
    prepared_data = record_data.copy()

    # Criptografa campos sensíveis
    sensitive_fields = ["ativo", "instrumento", "emissor", "tax_min"]
    for field in sensitive_fields:
        if record_data.get(field):
            prepared_data[field] = encrypt_fixed_income_data(
                str(record_data[field])
            )

    # Criptografa taxa_emissao (convertido para string)
    if record_data.get("taxa_emissao") is not None:
        prepared_data["taxa_emissao"] = encrypt_fixed_income_data(
            str(record_data["taxa_emissao"])
        )

    return prepared_data


def prepare_fixed_income_from_storage(encrypted_data: dict) -> dict:
    """
    Prepara dados de fixed_income_data descriptografados vindos do armazenamento.

    Args:
        encrypted_data: Dados criptografados do banco.

    Returns:
        dict: Dados descriptografados.
    """
    decrypted_data = encrypted_data.copy()

    # Descriptografa campos sensíveis
    sensitive_fields = ["ativo", "instrumento", "emissor", "tax_min"]
    for field in sensitive_fields:
        if encrypted_data.get(field):
            decrypted_data[field] = decrypt_fixed_income_data(
                encrypted_data[field]
            )

    # Descriptografa e converte taxa_emissao para float
    if encrypted_data.get("taxa_emissao"):
        try:
            taxa_emissao_str = decrypt_fixed_income_data(
                encrypted_data["taxa_emissao"]
            )
            decrypted_data["taxa_emissao"] = (
                float(taxa_emissao_str) if taxa_emissao_str != "None" else None
            )
        except (ValueError, CryptoError):
            decrypted_data["taxa_emissao"] = None

    return decrypted_data


def mask_fixed_income_data(data: dict) -> dict:
    """
    Mascarar dados sensíveis de fixed_income_data para logs e respostas.

    Args:
        data: Dados a serem mascarados.

    Returns:
        dict: Dados com campos sensíveis mascarados.
    """
    if not data:
        return data

    masked_data = data.copy()

    # Mascarar campos sensíveis
    if "ativo" in masked_data and masked_data["ativo"]:
        ativo = str(masked_data["ativo"])
        if len(ativo) > 4:
            masked_data["ativo"] = (
                ativo[:2] + "*" * (len(ativo) - 4) + ativo[-2:]
            )
        else:
            masked_data["ativo"] = "*" * len(ativo)

    if "emissor" in masked_data and masked_data["emissor"]:
        emissor = str(masked_data["emissor"])
        if len(emissor) > 6:
            masked_data["emissor"] = (
                emissor[:3] + "*" * (len(emissor) - 6) + emissor[-3:]
            )
        else:
            masked_data["emissor"] = "*" * len(emissor)

    if "tax_min" in masked_data and masked_data["tax_min"]:
        masked_data["tax_min"] = "***MASKED***"

    if "taxa_emissao" in masked_data and masked_data["taxa_emissao"]:
        masked_data["taxa_emissao"] = "***MASKED***"

    return masked_data

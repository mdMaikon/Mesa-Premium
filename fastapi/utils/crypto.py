"""
Módulo de criptografia para proteção de dados sensíveis no banco de dados.

Este módulo implementa criptografia AES-256-GCM para proteger dados financeiros
e oferece funcionalidades para:
- Criptografia/descriptografia de campos sensíveis
- Geração de hash determinístico para busca
- Gerenciamento de chaves por tabela
- Rotação de chaves com versionamento

Segurança:
- AES-256-GCM (criptografia autenticada)
- Chaves derivadas com PBKDF2
- IV único por operação
- Hash determinístico com HMAC-SHA256
"""

import base64
import hashlib
import hmac
import os
import secrets

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptoError(Exception):
    """Exceção base para erros de criptografia."""

    pass


class DataCrypto:
    """
    Classe principal para operações de criptografia de dados.

    Implementa criptografia AES-256-GCM com chaves derivadas por tabela
    e hash determinístico para campos de busca.
    """

    # Constantes de configuração
    KEY_SIZE = 32  # 256 bits
    IV_SIZE = 12  # 96 bits para GCM
    TAG_SIZE = 16  # 128 bits
    PBKDF2_ITERATIONS = 100000  # Recomendado pelo NIST

    def __init__(self, master_key: str | None = None):
        """
        Inicializa o sistema de criptografia.

        Args:
            master_key: Chave mestra em base64. Se None, carrega de env.
        """
        self.master_key = self._load_master_key(master_key)
        self.key_cache = {}  # Cache das chaves derivadas

    def _load_master_key(self, master_key: str | None) -> bytes:
        """
        Carrega a chave mestra da variável de ambiente ou parâmetro.

        Args:
            master_key: Chave mestra em base64 ou None para carregar de env.

        Returns:
            Chave mestra em bytes.

        Raises:
            CryptoError: Se a chave não for encontrada ou inválida.
        """
        if master_key is None:
            master_key = os.getenv("CRYPTO_MASTER_KEY")

        if not master_key:
            raise CryptoError(
                "Chave mestra não encontrada. Configure CRYPTO_MASTER_KEY."
            )

        try:
            key_bytes = base64.b64decode(master_key)
            if len(key_bytes) != self.KEY_SIZE:
                raise CryptoError(
                    f"Chave mestra deve ter {self.KEY_SIZE} bytes."
                )
            return key_bytes
        except Exception as e:
            raise CryptoError(f"Erro ao decodificar chave mestra: {e}") from e

    def _derive_table_key(self, table_name: str) -> bytes:
        """
        Deriva uma chave específica para uma tabela.

        Args:
            table_name: Nome da tabela.

        Returns:
            Chave derivada para a tabela.
        """
        if table_name in self.key_cache:
            return self.key_cache[table_name]

        # Carrega salt específico da tabela
        salt_env_name = f"CRYPTO_SALT_{table_name.upper()}"
        salt_b64 = os.getenv(salt_env_name)

        if not salt_b64:
            raise CryptoError(
                f"Salt não encontrado para tabela '{table_name}'. "
                f"Configure {salt_env_name}."
            )

        try:
            salt = base64.b64decode(salt_b64)
        except Exception as e:
            raise CryptoError(f"Erro ao decodificar salt: {e}") from e

        # Deriva chave usando PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
            backend=default_backend(),
        )

        table_key = kdf.derive(self.master_key)
        self.key_cache[table_name] = table_key

        return table_key

    def _derive_hash_key(self, table_name: str) -> bytes:
        """
        Deriva uma chave específica para hash determinístico.

        Args:
            table_name: Nome da tabela.

        Returns:
            Chave para hash determinístico.
        """
        table_key = self._derive_table_key(table_name)
        # Deriva chave de hash usando HMAC
        return hmac.new(table_key, b"hash_key", hashlib.sha256).digest()

    def encrypt_field(self, data: str, table_name: str) -> str:
        """
        Criptografa um campo de dados.

        Args:
            data: Dados a serem criptografados.
            table_name: Nome da tabela para derivação de chave.

        Returns:
            Dados criptografados em formato base64.

        Raises:
            CryptoError: Se houver erro na criptografia.
        """
        if not data:
            return ""

        try:
            # Deriva chave da tabela
            table_key = self._derive_table_key(table_name)

            # Gera IV aleatório
            iv = secrets.token_bytes(self.IV_SIZE)

            # Criptografa com AES-256-GCM
            cipher = Cipher(
                algorithms.AES(table_key),
                modes.GCM(iv),
                backend=default_backend(),
            )
            encryptor = cipher.encryptor()

            ciphertext = encryptor.update(data.encode("utf-8"))
            encryptor.finalize()

            # Obtém tag de autenticação
            tag = encryptor.tag

            # Formato: iv:ciphertext:tag (tudo em base64)
            encrypted_data = base64.b64encode(iv + ciphertext + tag).decode(
                "utf-8"
            )

            return encrypted_data

        except Exception as e:
            raise CryptoError(f"Erro na criptografia: {e}") from e

    def decrypt_field(self, encrypted_data: str, table_name: str) -> str:
        """
        Descriptografa um campo de dados.

        Args:
            encrypted_data: Dados criptografados em base64.
            table_name: Nome da tabela para derivação de chave.

        Returns:
            Dados descriptografados.

        Raises:
            CryptoError: Se houver erro na descriptografia.
        """
        if not encrypted_data:
            return ""

        try:
            # Deriva chave da tabela
            table_key = self._derive_table_key(table_name)

            # Decodifica dados
            encrypted_bytes = base64.b64decode(encrypted_data)

            # Extrai IV, ciphertext e tag
            iv = encrypted_bytes[: self.IV_SIZE]
            tag = encrypted_bytes[-self.TAG_SIZE :]
            ciphertext = encrypted_bytes[self.IV_SIZE : -self.TAG_SIZE]

            # Descriptografa com AES-256-GCM
            cipher = Cipher(
                algorithms.AES(table_key),
                modes.GCM(iv, tag),
                backend=default_backend(),
            )
            decryptor = cipher.decryptor()

            plaintext = decryptor.update(ciphertext)
            decryptor.finalize()

            return plaintext.decode("utf-8")

        except Exception as e:
            raise CryptoError(f"Erro na descriptografia: {e}") from e

    def generate_search_hash(self, data: str, table_name: str) -> str:
        """
        Gera hash determinístico para busca.

        Args:
            data: Dados para gerar hash.
            table_name: Nome da tabela para derivação de chave.

        Returns:
            Hash determinístico em hexadecimal.
        """
        if not data:
            return ""

        # Deriva chave de hash
        hash_key = self._derive_hash_key(table_name)

        # Gera HMAC-SHA256
        hash_digest = hmac.new(
            hash_key, data.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return hash_digest

    def encrypt_with_hash(self, data: str, table_name: str) -> tuple[str, str]:
        """
        Criptografa dados e gera hash para busca.

        Args:
            data: Dados a serem criptografados.
            table_name: Nome da tabela.

        Returns:
            Tupla (dados_criptografados, hash_busca).
        """
        encrypted = self.encrypt_field(data, table_name)
        search_hash = self.generate_search_hash(data, table_name)

        return encrypted, search_hash

    @staticmethod
    def generate_master_key() -> str:
        """
        Gera uma nova chave mestra segura.

        Returns:
            Chave mestra em base64.
        """
        key = secrets.token_bytes(32)  # 256 bits
        return base64.b64encode(key).decode("utf-8")

    @staticmethod
    def generate_salt() -> str:
        """
        Gera um novo salt seguro.

        Returns:
            Salt em base64.
        """
        salt = secrets.token_bytes(32)  # 256 bits
        return base64.b64encode(salt).decode("utf-8")


# Instância global para uso em toda a aplicação
# Será inicializada sob demanda para evitar erros durante importação
crypto_instance = None


def _get_crypto_instance():
    """Obtém a instância global de criptografia, inicializando se necessário."""
    global crypto_instance
    if crypto_instance is None:
        crypto_instance = DataCrypto()
    return crypto_instance


def encrypt_field(data: str, table_name: str) -> str:
    """
    Função de conveniência para criptografar campo.

    Args:
        data: Dados a serem criptografados.
        table_name: Nome da tabela.

    Returns:
        Dados criptografados.
    """
    return _get_crypto_instance().encrypt_field(data, table_name)


def decrypt_field(encrypted_data: str, table_name: str) -> str:
    """
    Função de conveniência para descriptografar campo.

    Args:
        encrypted_data: Dados criptografados.
        table_name: Nome da tabela.

    Returns:
        Dados descriptografados.
    """
    return _get_crypto_instance().decrypt_field(encrypted_data, table_name)


def generate_search_hash(data: str, table_name: str) -> str:
    """
    Função de conveniência para gerar hash de busca.

    Args:
        data: Dados para hash.
        table_name: Nome da tabela.

    Returns:
        Hash determinístico.
    """
    return _get_crypto_instance().generate_search_hash(data, table_name)


def encrypt_with_hash(data: str, table_name: str) -> tuple[str, str]:
    """
    Função de conveniência para criptografar com hash.

    Args:
        data: Dados a serem criptografados.
        table_name: Nome da tabela.

    Returns:
        Tupla (dados_criptografados, hash_busca).
    """
    return _get_crypto_instance().encrypt_with_hash(data, table_name)


# Configuração de tabelas e campos
ENCRYPTED_FIELDS = {
    "hub_tokens": ["user_login", "token"],
    "fixed_income_data": [
        "ativo",
        "instrumento",
        "emissor",
        "tax_min",
        "taxa_emissao",
    ],
    "structured_data": [
        "ticket_id",
        "ativo",
        "estrutura",
        "aai_ordem",
        "cliente",
        "comissao",
    ],
}

SEARCHABLE_FIELDS = {
    "hub_tokens": ["user_login"],
    "structured_data": ["ticket_id"],
}

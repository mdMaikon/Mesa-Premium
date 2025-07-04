"""
Testes unitários para o módulo de criptografia.

Testa todas as funcionalidades do módulo crypto.py incluindo:
- Criptografia/descriptografia de campos
- Geração de hash determinístico
- Derivação de chaves
- Tratamento de erros
- Casos extremos
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Adiciona o diretório do projeto ao PATH para importação
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "fastapi" / "utils"))

from crypto import (
    CryptoError,
    DataCrypto,
    decrypt_field,
    encrypt_field,
    encrypt_with_hash,
    generate_search_hash,
)


class TestDataCrypto:
    """Testes para a classe DataCrypto."""

    @pytest.fixture
    def master_key(self):
        """Chave mestra para testes."""
        return "dHS6yyjywFpArF2AVldASXj2tCbEn1uOoEDV8eI7QyY="

    @pytest.fixture
    def salt_hub_tokens(self):
        """Salt para tabela hub_tokens."""
        return "Fex295Bd0i+/D9HGuazQ2NLMnfIuDQ45riQ5F9WTK7A="

    @pytest.fixture
    def salt_structured_data(self):
        """Salt para tabela structured_data."""
        return "JLS+fs+i0SguYqUmO/o3okYVwaMmhkgGCY8PaMc1FPQ="

    @pytest.fixture
    def crypto_instance(
        self, master_key, salt_hub_tokens, salt_structured_data
    ):
        """Instância de DataCrypto para testes."""
        with patch.dict(
            os.environ,
            {
                "CRYPTO_MASTER_KEY": master_key,
                "CRYPTO_SALT_HUB_TOKENS": salt_hub_tokens,
                "CRYPTO_SALT_STRUCTURED_DATA": salt_structured_data,
            },
        ):
            return DataCrypto()

    def test_init_with_master_key(self, master_key):
        """Testa inicialização com chave mestra fornecida."""
        crypto = DataCrypto(master_key)
        assert crypto.master_key is not None
        assert len(crypto.master_key) == 32  # 256 bits

    def test_init_without_master_key(self, master_key):
        """Testa inicialização carregando chave do ambiente."""
        with patch.dict(os.environ, {"CRYPTO_MASTER_KEY": master_key}):
            crypto = DataCrypto()
            assert crypto.master_key is not None
            assert len(crypto.master_key) == 32

    def test_init_missing_master_key(self):
        """Testa erro quando chave mestra não está disponível."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(CryptoError) as exc_info:
                DataCrypto()
            assert "Chave mestra não encontrada" in str(exc_info.value)

    def test_init_invalid_master_key(self):
        """Testa erro quando chave mestra é inválida."""
        with patch.dict(os.environ, {"CRYPTO_MASTER_KEY": "invalid_key"}):
            with pytest.raises(CryptoError) as exc_info:
                DataCrypto()
            assert "Erro ao decodificar chave mestra" in str(exc_info.value)

    def test_encrypt_decrypt_field(self, crypto_instance):
        """Testa criptografia e descriptografia de campo."""
        original_data = "dados_sensíveis_123"
        table_name = "hub_tokens"

        # Criptografa
        encrypted = crypto_instance.encrypt_field(original_data, table_name)

        # Verifica que foi criptografado
        assert encrypted != original_data
        assert len(encrypted) > 0

        # Descriptografa
        decrypted = crypto_instance.decrypt_field(encrypted, table_name)

        # Verifica que foi descriptografado corretamente
        assert decrypted == original_data

    def test_encrypt_empty_string(self, crypto_instance):
        """Testa criptografia de string vazia."""
        encrypted = crypto_instance.encrypt_field("", "hub_tokens")
        assert encrypted == ""

        decrypted = crypto_instance.decrypt_field("", "hub_tokens")
        assert decrypted == ""

    def test_encrypt_different_tables(self, crypto_instance):
        """Testa que tabelas diferentes geram criptografias diferentes."""
        data = "mesmo_dado"

        encrypted1 = crypto_instance.encrypt_field(data, "hub_tokens")
        encrypted2 = crypto_instance.encrypt_field(data, "structured_data")

        # Mesmo dado, tabelas diferentes = criptografias diferentes
        assert encrypted1 != encrypted2

        # Ambas descriptografam para o mesmo valor
        assert crypto_instance.decrypt_field(encrypted1, "hub_tokens") == data
        assert (
            crypto_instance.decrypt_field(encrypted2, "structured_data")
            == data
        )

    def test_encrypt_same_data_different_iv(self, crypto_instance):
        """Testa que mesmos dados geram criptografias diferentes (IV único)."""
        data = "mesmo_dado"
        table_name = "hub_tokens"

        encrypted1 = crypto_instance.encrypt_field(data, table_name)
        encrypted2 = crypto_instance.encrypt_field(data, table_name)

        # Mesmo dado, mesmo tabela = criptografias diferentes (IV único)
        assert encrypted1 != encrypted2

        # Ambas descriptografam para o mesmo valor
        assert crypto_instance.decrypt_field(encrypted1, table_name) == data
        assert crypto_instance.decrypt_field(encrypted2, table_name) == data

    def test_generate_search_hash(self, crypto_instance):
        """Testa geração de hash determinístico."""
        data = "usuario_teste"
        table_name = "hub_tokens"

        hash1 = crypto_instance.generate_search_hash(data, table_name)
        hash2 = crypto_instance.generate_search_hash(data, table_name)

        # Hash determinístico = sempre igual
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex = 64 chars

    def test_generate_search_hash_different_tables(self, crypto_instance):
        """Testa que hash para tabelas diferentes são diferentes."""
        data = "mesmo_dado"

        hash1 = crypto_instance.generate_search_hash(data, "hub_tokens")
        hash2 = crypto_instance.generate_search_hash(data, "structured_data")

        # Mesmo dado, tabelas diferentes = hashes diferentes
        assert hash1 != hash2

    def test_generate_search_hash_empty_string(self, crypto_instance):
        """Testa hash de string vazia."""
        hash_result = crypto_instance.generate_search_hash("", "hub_tokens")
        assert hash_result == ""

    def test_encrypt_with_hash(self, crypto_instance):
        """Testa criptografia com hash simultâneo."""
        data = "usuario_teste"
        table_name = "hub_tokens"

        encrypted, hash_result = crypto_instance.encrypt_with_hash(
            data, table_name
        )

        # Verifica criptografia
        assert encrypted != data
        decrypted = crypto_instance.decrypt_field(encrypted, table_name)
        assert decrypted == data

        # Verifica hash
        expected_hash = crypto_instance.generate_search_hash(data, table_name)
        assert hash_result == expected_hash

    def test_decrypt_invalid_data(self, crypto_instance):
        """Testa erro na descriptografia de dados inválidos."""
        with pytest.raises(CryptoError) as exc_info:
            crypto_instance.decrypt_field("dados_invalidos", "hub_tokens")
        assert "Erro na descriptografia" in str(exc_info.value)

    def test_missing_salt(self, master_key):
        """Testa erro quando salt da tabela não está disponível."""
        with patch.dict(os.environ, {"CRYPTO_MASTER_KEY": master_key}):
            crypto = DataCrypto()
            with pytest.raises(CryptoError) as exc_info:
                crypto.encrypt_field("test", "tabela_inexistente")
            assert "Salt não encontrado" in str(exc_info.value)

    def test_key_caching(self, crypto_instance):
        """Testa cache de chaves derivadas."""
        # Primeira chamada deriva a chave
        crypto_instance.encrypt_field("test", "hub_tokens")
        assert "hub_tokens" in crypto_instance.key_cache

        # Segunda chamada usa o cache
        original_derive = crypto_instance._derive_table_key
        with patch.object(
            crypto_instance, "_derive_table_key", wraps=original_derive
        ) as mock_derive:
            crypto_instance.encrypt_field("test2", "hub_tokens")
            # Não deve chamar _derive_table_key novamente
            mock_derive.assert_not_called()

    def test_unicode_data(self, crypto_instance):
        """Testa criptografia com dados unicode."""
        unicode_data = "Dados com acentos: ção, ã, ñ, emoji: 🔐"
        table_name = "hub_tokens"

        encrypted = crypto_instance.encrypt_field(unicode_data, table_name)
        decrypted = crypto_instance.decrypt_field(encrypted, table_name)

        assert decrypted == unicode_data

    def test_large_data(self, crypto_instance):
        """Testa criptografia com dados grandes."""
        large_data = "A" * 10000  # 10KB
        table_name = "hub_tokens"

        encrypted = crypto_instance.encrypt_field(large_data, table_name)
        decrypted = crypto_instance.decrypt_field(encrypted, table_name)

        assert decrypted == large_data

    def test_generate_master_key(self):
        """Testa geração de chave mestra."""
        key1 = DataCrypto.generate_master_key()
        key2 = DataCrypto.generate_master_key()

        # Chaves diferentes
        assert key1 != key2

        # Formato válido (base64)
        import base64

        decoded = base64.b64decode(key1)
        assert len(decoded) == 32  # 256 bits

    def test_generate_salt(self):
        """Testa geração de salt."""
        salt1 = DataCrypto.generate_salt()
        salt2 = DataCrypto.generate_salt()

        # Salts diferentes
        assert salt1 != salt2

        # Formato válido (base64)
        import base64

        decoded = base64.b64decode(salt1)
        assert len(decoded) == 32  # 256 bits


class TestConvenienceFunctions:
    """Testes para as funções de conveniência."""

    @pytest.fixture
    def mock_crypto_instance(self):
        """Mock da instância global de crypto."""
        with patch("crypto._get_crypto_instance") as mock:
            yield mock.return_value

    def test_encrypt_field_function(self, mock_crypto_instance):
        """Testa função encrypt_field."""
        mock_crypto_instance.encrypt_field.return_value = "encrypted_data"

        result = encrypt_field("test_data", "test_table")

        mock_crypto_instance.encrypt_field.assert_called_once_with(
            "test_data", "test_table"
        )
        assert result == "encrypted_data"

    def test_decrypt_field_function(self, mock_crypto_instance):
        """Testa função decrypt_field."""
        mock_crypto_instance.decrypt_field.return_value = "decrypted_data"

        result = decrypt_field("encrypted_data", "test_table")

        mock_crypto_instance.decrypt_field.assert_called_once_with(
            "encrypted_data", "test_table"
        )
        assert result == "decrypted_data"

    def test_generate_search_hash_function(self, mock_crypto_instance):
        """Testa função generate_search_hash."""
        mock_crypto_instance.generate_search_hash.return_value = "hash_result"

        result = generate_search_hash("test_data", "test_table")

        mock_crypto_instance.generate_search_hash.assert_called_once_with(
            "test_data", "test_table"
        )
        assert result == "hash_result"

    def test_encrypt_with_hash_function(self, mock_crypto_instance):
        """Testa função encrypt_with_hash."""
        mock_crypto_instance.encrypt_with_hash.return_value = (
            "encrypted",
            "hash",
        )

        result = encrypt_with_hash("test_data", "test_table")

        mock_crypto_instance.encrypt_with_hash.assert_called_once_with(
            "test_data", "test_table"
        )
        assert result == ("encrypted", "hash")


class TestConfiguration:
    """Testes para configuração de campos criptografados."""

    def test_encrypted_fields_configuration(self):
        """Testa configuração de campos criptografados."""
        from crypto import ENCRYPTED_FIELDS

        # Verifica se as tabelas esperadas estão configuradas
        assert "hub_tokens" in ENCRYPTED_FIELDS
        assert "fixed_income_data" in ENCRYPTED_FIELDS
        assert "structured_data" in ENCRYPTED_FIELDS

        # Verifica campos específicos
        assert "user_login" in ENCRYPTED_FIELDS["hub_tokens"]
        assert "token" in ENCRYPTED_FIELDS["hub_tokens"]
        assert "ativo" in ENCRYPTED_FIELDS["fixed_income_data"]
        assert "ticket_id" in ENCRYPTED_FIELDS["structured_data"]

    def test_searchable_fields_configuration(self):
        """Testa configuração de campos pesquisáveis."""
        from crypto import SEARCHABLE_FIELDS

        # Verifica se as tabelas com busca estão configuradas
        assert "hub_tokens" in SEARCHABLE_FIELDS
        assert "structured_data" in SEARCHABLE_FIELDS

        # Verifica campos específicos
        assert "user_login" in SEARCHABLE_FIELDS["hub_tokens"]
        assert "ticket_id" in SEARCHABLE_FIELDS["structured_data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

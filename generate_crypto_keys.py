#!/usr/bin/env python3
"""
Script para gerar chaves criptográficas seguras.

Este script gera:
- Chave mestra para criptografia AES-256
- Salts únicos para cada tabela
- Arquivo .env com as configurações

Uso:
    python generate_crypto_keys.py
    python generate_crypto_keys.py --output .env.dev
"""

import argparse
import os
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao PATH
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi.utils.crypto import DataCrypto
except ImportError:
    # Tenta import direto caso não esteja como pacote
    import sys

    sys.path.insert(0, str(Path(__file__).parent / "fastapi" / "utils"))
    from crypto import DataCrypto


def generate_keys():
    """
    Gera chaves criptográficas seguras.

    Returns:
        dict: Dicionário com as chaves geradas.
    """
    print("🔐 Gerando chaves criptográficas seguras...")

    # Gera chave mestra
    master_key = DataCrypto.generate_master_key()
    print("✅ Chave mestra gerada")

    # Gera salts para cada tabela
    salt_hub_tokens = DataCrypto.generate_salt()
    salt_fixed_income = DataCrypto.generate_salt()
    salt_structured = DataCrypto.generate_salt()
    print("✅ Salts por tabela gerados")

    keys = {
        "CRYPTO_MASTER_KEY": master_key,
        "CRYPTO_SALT_HUB_TOKENS": salt_hub_tokens,
        "CRYPTO_SALT_FIXED_INCOME_DATA": salt_fixed_income,
        "CRYPTO_SALT_STRUCTURED_DATA": salt_structured,
    }

    print("✅ Todas as chaves geradas com sucesso!")
    return keys


def save_to_env_file(keys, output_file):
    """
    Salva as chaves em um arquivo .env.

    Args:
        keys (dict): Chaves geradas.
        output_file (str): Caminho do arquivo de saída.
    """
    print(f"💾 Salvando chaves em {output_file}...")

    # Lê o arquivo existente se houver
    env_content = ""
    if os.path.exists(output_file):
        with open(output_file) as f:
            env_content = f.read()
        print(f"📄 Arquivo existente encontrado: {output_file}")

    # Adiciona/atualiza as chaves
    lines = env_content.splitlines() if env_content else []
    updated_lines = []
    crypto_keys_added = set()

    for line in lines:
        # Verifica se é uma linha de chave criptográfica
        if line.startswith("CRYPTO_"):
            key_name = line.split("=")[0]
            if key_name in keys:
                # Atualiza a linha existente
                updated_lines.append(f"{key_name}={keys[key_name]}")
                crypto_keys_added.add(key_name)
            else:
                # Mantém a linha original se não for uma chave que geramos
                updated_lines.append(line)
        else:
            # Mantém outras linhas
            updated_lines.append(line)

    # Adiciona chaves que não estavam no arquivo
    for key_name, key_value in keys.items():
        if key_name not in crypto_keys_added:
            updated_lines.append(f"{key_name}={key_value}")

    # Salva o arquivo atualizado
    with open(output_file, "w") as f:
        f.write("\n".join(updated_lines))
        if updated_lines:  # Adiciona nova linha no final se há conteúdo
            f.write("\n")

    print(f"✅ Chaves salvas em {output_file}")


def create_env_files(keys):
    """
    Cria arquivos .env para cada ambiente.

    Args:
        keys (dict): Chaves geradas.
    """
    environments = [".env.dev", ".env.staging", ".env.production"]

    for env_file in environments:
        if not os.path.exists(env_file):
            # Cria arquivo baseado no .env.example
            if os.path.exists(".env.example"):
                with open(".env.example") as f:
                    example_content = f.read()

                # Substitui placeholders pelas chaves reais
                content = example_content
                for key_name, key_value in keys.items():
                    placeholder = f"{key_name.lower()}_base64_here"
                    content = content.replace(placeholder, key_value)

                with open(env_file, "w") as f:
                    f.write(content)

                print(f"✅ Arquivo {env_file} criado")
            else:
                print(
                    f"⚠️  .env.example não encontrado, criando {env_file} apenas com chaves crypto"
                )
                with open(env_file, "w") as f:
                    f.write("# CRYPTOGRAPHY CONFIGURATION\n")
                    for key_name, key_value in keys.items():
                        f.write(f"{key_name}={key_value}\n")
                print(f"✅ Arquivo {env_file} criado")
        else:
            # Atualiza arquivo existente
            save_to_env_file(keys, env_file)


def print_summary(keys):
    """
    Imprime resumo das chaves geradas.

    Args:
        keys (dict): Chaves geradas.
    """
    print("\n" + "=" * 60)
    print("📋 RESUMO DAS CHAVES GERADAS")
    print("=" * 60)

    for key_name, key_value in keys.items():
        print(f"🔑 {key_name}:")
        print(f"   {key_value[:20]}...{key_value[-20:]}")
        print()

    print("⚠️  IMPORTANTE:")
    print("   - Mantenha essas chaves em segurança")
    print("   - Não commite arquivos .env no git")
    print("   - Faça backup seguro das chaves")
    print("   - Use chaves diferentes para cada ambiente")
    print("=" * 60)


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Gera chaves criptográficas seguras para o projeto"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Arquivo de saída específico (ex: .env.dev)",
    )
    parser.add_argument(
        "--all-envs",
        action="store_true",
        help="Criar/atualizar todos os arquivos .env",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Apenas imprimir as chaves sem salvar",
    )

    args = parser.parse_args()

    # Gera as chaves
    keys = generate_keys()

    if args.print_only:
        # Apenas imprime as chaves
        print_summary(keys)
    elif args.output:
        # Salva em arquivo específico
        save_to_env_file(keys, args.output)
        print_summary(keys)
    elif args.all_envs:
        # Cria/atualiza todos os arquivos .env
        create_env_files(keys)
        print_summary(keys)
    else:
        # Comportamento padrão: criar/atualizar .env.dev
        save_to_env_file(keys, ".env.dev")
        print_summary(keys)

        print("\n💡 DICAS:")
        print("   - Use --all-envs para criar todos os arquivos .env")
        print("   - Use --output arquivo.env para arquivo específico")
        print("   - Use --print-only para apenas visualizar as chaves")


if __name__ == "__main__":
    main()

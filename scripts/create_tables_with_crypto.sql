-- Script para criar todas as tabelas necessárias no MySQL com suporte a criptografia
-- Execute este script no VPS: mysql -u mesa_user -p mesa_premium_db < create_tables_with_crypto.sql

USE mesa_premium_db;

-- Criar tabela hub_tokens (Tokens de Autenticação) - COM CRIPTOGRAFIA
CREATE TABLE IF NOT EXISTS hub_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Campos criptografados
    user_login TEXT NOT NULL,              -- Criptografado (era VARCHAR(255))
    token TEXT NOT NULL,                   -- Criptografado (já era TEXT)

    -- Campos hash para busca (determinístico)
    user_login_hash VARCHAR(64) NOT NULL,  -- Hash SHA256 do user_login

    -- Campos não criptografados
    expires_at DATETIME,
    extracted_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices ajustados para campos hash
    INDEX idx_user_login_hash (user_login_hash),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Criar tabela fixed_income_data (Dados de Renda Fixa) - COM CRIPTOGRAFIA
CREATE TABLE IF NOT EXISTS fixed_income_data (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Campos criptografados
    ativo TEXT,                           -- Criptografado (era VARCHAR(255))
    instrumento TEXT,                     -- Criptografado (era VARCHAR(100))
    emissor TEXT,                         -- Criptografado (era VARCHAR(255))
    tax_min TEXT,                         -- Criptografado (era VARCHAR(255))
    taxa_emissao TEXT,                    -- Criptografado (valor sensível)

    -- Campos não criptografados (dados técnicos/estatísticos)
    data_coleta DATETIME NOT NULL,
    duration DECIMAL(10,6),
    indexador VARCHAR(100),
    juros VARCHAR(50),
    primeira_data_juros DATE,
    isento VARCHAR(10),
    rating VARCHAR(50),
    vencimento DATE,
    tax_min_clean DECIMAL(8,4),           -- Mantido para cálculos
    roa_aprox DECIMAL(8,4),               -- Mantido para cálculos
    publico VARCHAR(100),
    publico_resumido VARCHAR(10),
    cupom VARCHAR(100),
    classificar_vencimento TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Índices ajustados (removidos campos criptografados)
    INDEX idx_data_coleta (data_coleta),
    INDEX idx_indexador (indexador),
    INDEX idx_rating (rating),
    INDEX idx_vencimento (vencimento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Criar tabela structured_data (Produtos Estruturados) - COM CRIPTOGRAFIA
CREATE TABLE IF NOT EXISTS structured_data (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Campos criptografados
    ticket_id TEXT NOT NULL,              -- Criptografado (era VARCHAR(50))
    ativo TEXT,                           -- Criptografado (era VARCHAR(255))
    estrutura TEXT,                       -- Criptografado (era VARCHAR(255))
    aai_ordem TEXT,                       -- Criptografado (era VARCHAR(100))
    cliente TEXT,                         -- Criptografado (dado sensível)
    comissao TEXT,                        -- Criptografado (valor financeiro)

    -- Campos hash para busca (determinístico)
    ticket_id_hash VARCHAR(64) NOT NULL,  -- Hash SHA256 do ticket_id

    -- Campos não criptografados
    data_coleta DATETIME NOT NULL,
    data_envio DATETIME,
    quantidade DECIMAL(15,4),
    fixing DECIMAL(8,4),
    status VARCHAR(50),
    detalhes TEXT,
    operacao VARCHAR(100),
    underlying VARCHAR(255),
    rating VARCHAR(50),
    vencimento DATE,
    taxa_retorno DECIMAL(8,4),
    protecao DECIMAL(8,4),
    publico VARCHAR(100),
    publico_resumido VARCHAR(10),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Índices ajustados para campos hash
    INDEX idx_data_coleta (data_coleta),
    INDEX idx_ticket_id_hash (ticket_id_hash),
    INDEX idx_status (status),
    INDEX idx_vencimento (vencimento),
    UNIQUE KEY uk_ticket_id_hash (ticket_id_hash)  -- Unique constraint no hash
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- SCRIPT DE MIGRAÇÃO DE DADOS EXISTENTES
-- ====================================

-- Verificar se há dados nas tabelas originais
SELECT
    'hub_tokens' as tabela,
    COUNT(*) as registros
FROM hub_tokens
UNION ALL
SELECT
    'fixed_income_data' as tabela,
    COUNT(*) as registros
FROM fixed_income_data
UNION ALL
SELECT
    'structured_data' as tabela,
    COUNT(*) as registros
FROM structured_data;

-- AVISO: Execute o script Python de migração após criar as tabelas
-- python migrate_existing_data.py

-- ====================================
-- VERIFICAÇÃO DAS TABELAS CRIADAS
-- ====================================

-- Mostrar tabelas criadas
SHOW TABLES;

-- Mostrar estrutura das tabelas
DESCRIBE hub_tokens;
DESCRIBE fixed_income_data;
DESCRIBE structured_data;

-- Verificar índices
SHOW INDEX FROM hub_tokens;
SHOW INDEX FROM fixed_income_data;
SHOW INDEX FROM structured_data;

-- Confirmar criação
SELECT 'Tabelas com criptografia criadas com sucesso!' as status;

-- ====================================
-- NOTAS IMPORTANTES
-- ====================================

/*
CAMPOS CRIPTOGRAFADOS:

1. hub_tokens:
   - user_login (TEXT) - Hash: user_login_hash
   - token (TEXT) - Sem hash (não usado em WHERE)

2. fixed_income_data:
   - ativo (TEXT) - Sem hash (não usado em WHERE)
   - instrumento (TEXT) - Sem hash
   - emissor (TEXT) - Sem hash
   - tax_min (TEXT) - Sem hash
   - taxa_emissao (TEXT) - Sem hash

3. structured_data:
   - ticket_id (TEXT) - Hash: ticket_id_hash
   - ativo (TEXT) - Sem hash
   - estrutura (TEXT) - Sem hash
   - aai_ordem (TEXT) - Sem hash
   - cliente (TEXT) - Sem hash
   - comissao (TEXT) - Sem hash

MIGRAÇÃO NECESSÁRIA:
- Dados existentes precisam ser criptografados
- Campos hash precisam ser populados
- Índices antigos podem ser removidos
- Aplicação precisa ser atualizada para usar novos campos

PERFORMANCE:
- Campos criptografados são TEXT (maior que VARCHAR)
- Índices removidos de campos criptografados
- Busca apenas por campos hash determinísticos
- Impacto mínimo em queries por timestamp/status
*/

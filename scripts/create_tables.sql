-- Script para criar todas as tabelas necessárias no MySQL
-- Execute este script no VPS: mysql -u mesa_user -p mesa_premium_db < create_tables.sql

USE mesa_premium_db;

-- Criar tabela hub_tokens (Tokens de Autenticação)
CREATE TABLE IF NOT EXISTS hub_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_login VARCHAR(255) NOT NULL,
    token TEXT NOT NULL,
    expires_at DATETIME,
    extracted_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_login (user_login),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Criar tabela fixed_income_data (Dados de Renda Fixa)
CREATE TABLE IF NOT EXISTS fixed_income_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_coleta DATETIME NOT NULL,
    ativo VARCHAR(255) NOT NULL,
    instrumento VARCHAR(100),
    duration DECIMAL(10,6),
    indexador VARCHAR(100),
    juros VARCHAR(50),
    primeira_data_juros DATE,
    isento VARCHAR(10),
    rating VARCHAR(50),
    vencimento DATE,
    tax_min VARCHAR(255),
    tax_min_clean DECIMAL(8,4),
    roa_aprox DECIMAL(8,4),
    taxa_emissao DECIMAL(8,4),
    publico VARCHAR(100),
    publico_resumido VARCHAR(10),
    emissor VARCHAR(255),
    cupom VARCHAR(100),
    classificar_vencimento TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_data_coleta (data_coleta),
    INDEX idx_ativo (ativo),
    INDEX idx_indexador (indexador),
    INDEX idx_rating (rating),
    INDEX idx_vencimento (vencimento),
    INDEX idx_emissor (emissor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Criar tabela structured_products_data (Produtos Estruturados)
CREATE TABLE IF NOT EXISTS structured_products_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_coleta DATETIME NOT NULL,
    ticket VARCHAR(50) NOT NULL,
    tipo VARCHAR(100),
    descricao TEXT,
    underlying VARCHAR(255),
    rating VARCHAR(50),
    vencimento DATE,
    taxa_retorno DECIMAL(8,4),
    protecao DECIMAL(8,4),
    emissor VARCHAR(255),
    publico VARCHAR(100),
    publico_resumido VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_data_coleta (data_coleta),
    INDEX idx_ticket (ticket),
    INDEX idx_tipo (tipo),
    INDEX idx_emissor (emissor),
    INDEX idx_vencimento (vencimento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Mostrar tabelas criadas
SHOW TABLES;

-- Mostrar estrutura das tabelas
DESCRIBE hub_tokens;
DESCRIBE fixed_income_data;
DESCRIBE structured_products_data;

-- Confirmar criação
SELECT 'Tabelas criadas com sucesso!' as status;

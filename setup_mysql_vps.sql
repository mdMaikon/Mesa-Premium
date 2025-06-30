-- =========================================
-- SETUP MYSQL VPS HOSTINGER
-- Script para configurar banco de dados no VPS
-- =========================================

-- 1. Criar banco de dados
CREATE DATABASE IF NOT EXISTS mesa_premium_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. Criar usuário específico para a aplicação
CREATE USER IF NOT EXISTS 'mesa_user'@'localhost' IDENTIFIED BY 'Mesa@Premium2024!';
CREATE USER IF NOT EXISTS 'mesa_user'@'%' IDENTIFIED BY 'Mesa@Premium2024!';

-- 3. Conceder permissões ao usuário
GRANT ALL PRIVILEGES ON mesa_premium_db.* TO 'mesa_user'@'localhost';
GRANT ALL PRIVILEGES ON mesa_premium_db.* TO 'mesa_user'@'%';

-- 4. Aplicar mudanças
FLUSH PRIVILEGES;

-- 5. Usar o banco criado
USE mesa_premium_db;

-- =========================================
-- CRIAÇÃO DAS TABELAS
-- =========================================

-- Tabela para armazenar tokens do Hub XP
CREATE TABLE IF NOT EXISTS hub_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_login VARCHAR(255) NOT NULL,
    token TEXT NOT NULL,
    expires_at DATETIME,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_login (user_login),
    INDEX idx_expires_at (expires_at)
);

-- Tabela para dados de renda fixa
CREATE TABLE IF NOT EXISTS fixed_income_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_coleta DATETIME NOT NULL,
    ativo VARCHAR(255),
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
    INDEX idx_emissor (emissor),
    INDEX idx_vencimento (vencimento),
    INDEX idx_rating (rating),
    INDEX idx_indexador (indexador)
);

-- Tabela para dados estruturados
CREATE TABLE IF NOT EXISTS structured_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_coleta DATETIME NOT NULL,
    ticket_id VARCHAR(255) NOT NULL UNIQUE,
    data_envio DATETIME,
    cliente INT,
    ativo VARCHAR(255),
    comissao DECIMAL(15,4),
    estrutura VARCHAR(255),
    quantidade INT,
    fixing DATETIME,
    status VARCHAR(100),
    detalhes TEXT,
    operacao VARCHAR(100),
    aai_ordem VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_data_coleta (data_coleta),
    INDEX idx_ticket_id (ticket_id),
    INDEX idx_cliente (cliente),
    INDEX idx_ativo (ativo),
    INDEX idx_status (status),
    INDEX idx_data_envio (data_envio)
);

-- =========================================
-- VERIFICAÇÕES
-- =========================================

-- Verificar se as tabelas foram criadas
SHOW TABLES;

-- Verificar estrutura das tabelas
DESCRIBE hub_tokens;
DESCRIBE fixed_income_data;
DESCRIBE structured_data;

-- Verificar usuários e permissões
SELECT User, Host FROM mysql.user WHERE User = 'mesa_user';

-- Verificar charset do banco
SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = 'mesa_premium_db';

-- Migração para adicionar campo user_login_hash na tabela hub_tokens
-- Esta migração é necessária para suportar criptografia de dados

-- Adicionar nova coluna user_login_hash
ALTER TABLE hub_tokens
ADD COLUMN user_login_hash VARCHAR(64) NULL
AFTER user_login;

-- Adicionar índice para otimizar buscas por hash
CREATE INDEX idx_hub_tokens_user_login_hash ON hub_tokens(user_login_hash);

-- Comentários explicativos
ALTER TABLE hub_tokens
MODIFY COLUMN user_login TEXT COMMENT 'User login criptografado',
MODIFY COLUMN user_login_hash VARCHAR(64) COMMENT 'Hash determinístico para busca do user_login',
MODIFY COLUMN token TEXT COMMENT 'Token de acesso criptografado';

-- Verificar estrutura da tabela
DESCRIBE hub_tokens;

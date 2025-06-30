-- Comandos SQL para executar no VPS MySQL
-- sudo mysql -u root -p < mysql_commands.sql

-- Verificar usuários existentes
SELECT user, host FROM mysql.user WHERE user='mesa_user';

-- Remover usuários existentes (se houver)
DROP USER IF EXISTS 'mesa_user'@'localhost';
DROP USER IF EXISTS 'mesa_user'@'%';
-- DROP USER IF EXISTS 'mesa_user'@'SPECIFIC_IP';

-- Criar database se não existir
CREATE DATABASE IF NOT EXISTS mesa_premium_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Criar usuário com acesso de qualquer IP (% = wildcard)
CREATE USER 'mesa_user'@'%' IDENTIFIED BY 'YOUR_PASSWORD';

-- Conceder todas as permissões no banco específico
GRANT ALL PRIVILEGES ON mesa_premium_db.* TO 'mesa_user'@'%';

-- Aplicar as mudanças
FLUSH PRIVILEGES;

-- Verificar se o usuário foi criado corretamente
SELECT user, host FROM mysql.user WHERE user='mesa_user';

-- Mostrar as permissões concedidas
SHOW GRANTS FOR 'mesa_user'@'%';

-- Testar uma query simples
USE mesa_premium_db;
SELECT 'MySQL configurado com sucesso!' as status;

@echo off
chcp 65001 >nul

REM ================================================================
REM  🚀 SETUP AUTOMAÇÃO MYSQL HOSTINGER
REM ================================================================
REM  EDITE AS CREDENCIAIS ABAIXO E EXECUTE ESTE ARQUIVO
REM ================================================================

REM ┌─────────────────────────────────────────────────┐
REM │  📝 EDITE SUAS CREDENCIAIS AQUI:                │
REM └─────────────────────────────────────────────────┘
set HOST=srv719.hstgr.io
set USER=u272626296_mesapremium
set PASS=Blue@@10
set DB=u272626296_automacoes
set PORT=3306

REM ┌─────────────────────────────────────────────────┐
REM │  ⚙️ CONFIGURAÇÕES:                              │
REM └─────────────────────────────────────────────────┘
set PASTA=MenuAutomacoes
set CHARSET=utf8mb4

REM 💡 EXEMPLOS DE NOMES DE PASTA:
REM set PASTA=MeuProjeto
REM set PASTA=AutomacaoVendas  
REM set PASTA=SistemaEstoque
REM set PASTA=C:\Projetos\MinhaAutomacao (caminho completo)

REM ================================================================
REM  🛠️ INSTALADOR - NÃO EDITE ABAIXO
REM ================================================================

title Setup MySQL Environment

echo.
echo  ╔════════════════════════════════════════════════╗
echo  ║           🚀 SETUP MYSQL HOSTINGER             ║
echo  ╚════════════════════════════════════════════════╝
echo.

REM Validar credenciais
if "%USER%"=="seu_usuario" (
    echo  ❌ CREDENCIAIS NÃO CONFIGURADAS!
    echo.
    echo  💡 Para configurar:
    echo     1. Botão direito neste arquivo → Editar
    echo     2. Altere as linhas no topo do arquivo:
    echo        set HOST=seu_host_hostinger.com
    echo        set USER=seu_usuario_real
    echo        set PASS=sua_senha_real
    echo        set DB=nome_do_banco
    echo     3. Salve e execute novamente
    echo.
    pause
    exit /b 1
)

echo  📋 Configurações:
echo     🏠 Host: %HOST%
echo     👤 User: %USER%
echo     🔑 Pass: %PASS:~0,2%***
echo     🗄️  DB: %DB%
echo     📁 Pasta: %PASTA%
echo.

set /p OK="  ✅ Configurações corretas? (S/n): "
if /i "%OK%"=="n" exit /b 0

echo.
echo  🏗️ Criando ambiente...

REM Criar pasta
if exist "%PASTA%" (
    echo     ⚠️ Pasta existe! Limpando...
    rmdir /s /q "%PASTA%" 2>nul
)
mkdir "%PASTA%" && cd "%PASTA%" || (
    echo     ❌ Erro ao criar pasta!
    pause & exit /b 1
)

echo     ✅ Pasta: %CD%

REM Criar .env
echo     📝 Criando .env...
(
echo # MySQL Hostinger - %DATE% %TIME%
echo DB_HOST=%HOST%
echo DB_USER=%USER%
echo DB_PASSWORD=%PASS%
echo DB_NAME=%DB%
echo DB_PORT=%PORT%
echo DB_CHARSET=%CHARSET%
echo DB_AUTOCOMMIT=True
echo DB_CONNECTION_TIMEOUT=10
echo DB_POOL_SIZE=5
) > .env

REM Criar .gitignore
(echo .env && echo __pycache__/ && echo *.pyc && echo *.log) > .gitignore

echo     ✅ Configuração concluída!

echo.
echo  ╔════════════════════════════════════════════════╗
echo  ║              ✅ SETUP COMPLETO!                ║
echo  ╚════════════════════════════════════════════════╝
echo.
echo  📍 Local: %CD%
echo  📄 Arquivos: .env, .gitignore
echo.
echo  🚀 Pronto para usar com Python:
echo     from dotenv import load_dotenv
echo     import os
echo     load_dotenv()
echo     host = os.getenv('DB_HOST')
echo.
echo  🔒 IMPORTANTE: .env contém suas credenciais!
echo.
pause
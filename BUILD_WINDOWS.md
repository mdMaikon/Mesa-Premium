# 🚀 Instruções para Build Windows

## 📋 Como Criar Executável no Windows

### 1. Preparar Ambiente Windows

```cmd
# 1. Instalar Python 3.11+ no Windows
# Baixar de: https://python.org

# 2. Abrir Command Prompt como Administrador
# 3. Navegar para a pasta do projeto
cd C:\caminho\para\MenuAutomacoes

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Instalar PyInstaller
pip install pyinstaller
```

### 2. Criar Executável Principal

```cmd
# Executável GUI (sem console)
pyinstaller --onefile --windowed --name=MenuAutomacoes ^
    --icon=icone.png ^
    --add-data="configs;configs" ^
    --add-data="automacoes;automacoes" ^
    --add-data=".env.template;." ^
    --hidden-import=mysql.connector ^
    --hidden-import=selenium ^
    --hidden-import=customtkinter ^
    --hidden-import=cqrs_commands ^
    --hidden-import=cqrs_queries ^
    --hidden-import=cqrs_handlers ^
    --hidden-import=cqrs_mediator ^
    --hidden-import=di_container ^
    --hidden-import=service_registry ^
    --clean --noconfirm ^
    menu_principal.py
```

### 3. Criar Executável Debug

```cmd
# Executável console (para debug)
pyinstaller --onefile --console --name=MenuAutomacoes_Debug ^
    --add-data="configs;configs" ^
    --add-data="automacoes;automacoes" ^
    --add-data=".env.template;." ^
    --hidden-import=mysql.connector ^
    --hidden-import=selenium ^
    --hidden-import=customtkinter ^
    --hidden-import=cqrs_commands ^
    --hidden-import=cqrs_queries ^
    --hidden-import=cqrs_handlers ^
    --hidden-import=cqrs_mediator ^
    --hidden-import=di_container ^
    --hidden-import=service_registry ^
    --clean --noconfirm ^
    menu_principal.py
```

### 4. Estrutura Final

Após o build, você terá:

```
dist/
├── MenuAutomacoes.exe        # Executável principal (GUI)
└── MenuAutomacoes_Debug.exe  # Executável debug (console)
```

### 5. Criar Pacote de Distribuição

```cmd
# Criar pasta final
mkdir MenuAutomacoes_Windows_Final
cd MenuAutomacoes_Windows_Final

# Copiar executáveis
copy ..\dist\MenuAutomacoes.exe .
copy ..\dist\MenuAutomacoes_Debug.exe .

# Copiar arquivos necessários
copy ..\.env.template .
copy ..\README.md .

# Criar diretórios
mkdir logs
mkdir data
mkdir temp
mkdir configs
```

### 6. Criar Script de Inicialização

Criar arquivo `INICIAR.bat`:

```batch
@echo off
title MenuAutomacoes Enterprise - Windows
cls
echo ==========================================
echo   MenuAutomacoes Enterprise v1.0.0
echo   Executavel Windows Standalone
echo ==========================================
echo.

echo [1/3] Verificando configuracao...
if not exist .env (
    echo [AVISO] Arquivo .env nao encontrado
    echo         Criando do template...
    if exist .env.template (
        copy .env.template .env >nul 2>&1
        echo [OK] Template .env criado
        echo      CONFIGURE suas credenciais MySQL em .env
        echo.
        echo [PAUSE] Configure .env e execute novamente
        pause
        exit /b 1
    ) else (
        echo [ERRO] Template .env.template nao encontrado!
        pause
        exit /b 1
    )
)

echo [2/3] Verificando Chrome...
where chrome >nul 2>&1 || where "C:\Program Files\Google\Chrome\Application\chrome.exe" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Chrome nao encontrado
    echo         Instale Google Chrome para funcionamento completo
    echo.
)

echo [3/3] Iniciando MenuAutomacoes...
echo         Aguarde carregamento dos componentes...
echo.

start "" "MenuAutomacoes.exe"

timeout /t 3 /nobreak >nul
echo [OK] MenuAutomacoes iniciado!
echo      Se houver erros, execute MenuAutomacoes_Debug.exe
echo.
```

### 7. Criar README para Usuário

Criar arquivo `LEIA-ME.txt`:

```text
# MenuAutomacoes Enterprise - Windows Standalone

## Início Rápido (2 minutos)

1. Extrair este ZIP em qualquer pasta
2. Configurar arquivo .env com MySQL 
3. Duplo clique em INICIAR.bat

## Configuração MySQL

Edite .env com suas credenciais:

DB_HOST=seu_servidor_mysql.hostinger.com
DB_USER=seu_usuario_mysql
DB_PASSWORD=sua_senha_mysql
DB_NAME=nome_do_seu_banco
DB_PORT=3306

## Arquivos Incluídos

- MenuAutomacoes.exe - Executável principal
- MenuAutomacoes_Debug.exe - Versão console (diagnóstico)
- INICIAR.bat - Script de inicialização
- .env.template - Template de configuração

## Características

✅ Zero dependências - Funciona sem Python  
✅ Autocontido - Todas bibliotecas incluídas  
✅ Debug integrado - Console para erros  
✅ Portátil - Funciona de pen drive  

## Resolução de Problemas

### Erro de inicialização:
1. Execute MenuAutomacoes_Debug.exe
2. Verifique logs na pasta logs/
3. Confirme configuração .env

### Chrome não encontrado:
- Instale Google Chrome
- Sistema detecta automaticamente
```

### 8. Compactar em ZIP

```cmd
# Compactar tudo em um ZIP
# Use WinRAR, 7-Zip ou ferramenta de sua preferência
# Nome sugerido: MenuAutomacoes_Windows_v1.0.0.zip
```

## ✅ Vantagens desta Abordagem

1. **Build nativo Windows** - Executável criado no Windows
2. **Compatibilidade total** - Sem problemas de arquitetura
3. **Controle completo** - Você vê exatamente o que acontece
4. **Debug fácil** - Console Windows para erros
5. **Distribuição simples** - ZIP pronto para uso

## 🎯 Resultado Final

- **MenuAutomacoes.exe** - ~50MB, GUI limpa
- **MenuAutomacoes_Debug.exe** - Console para troubleshooting
- **INICIAR.bat** - Launcher inteligente
- **Zero dependências** - Funciona em qualquer Windows

---

**Esta abordagem é muito mais confiável que cross-compilation!** ✅
# Plano de Projeto: Evolução de Automações Python com Banco de Dados MySQL

Este documento descreve um plano para migrar um projeto de automações em Python, atualmente baseado em scripts locais e planilhas Excel, para uma arquitetura centralizada utilizando um banco de dados MySQL, visando maior profissionalismo, escalabilidade e facilidade de manutenção.

---

## Fase 1: Fundação e Refatoração do Código 🔧

O objetivo desta fase é abandonar o formato de múltiplos executáveis (`.exe`) e organizar o código de forma modular e profissional, preparando-o para futuras integrações.

### 1. Centralize o Código com Controle de Versão (Git)
* **Ação:** Criar um único repositório de projeto. Iniciar o controle de versão com `git init` e utilizar uma plataforma como GitHub ou GitLab para hospedar o código na nuvem.
* **Benefício:** Garante um histórico completo de alterações, facilita a colaboração e previne a perda de código.

### 2. Modularize suas Automações
* **Ação:** Converter cada script de automação em uma função ou classe dentro de módulos Python. Isso centraliza a lógica de negócio em arquivos específicos.
* **Exemplo (`automacoes.py`):**
    ```python
    # Em um arquivo chamado automacoes.py
    def capturar_dados_site_a():
        """Captura informações do site A."""
        print("Capturando dados do site A...")
        dados = "..." # Lógica de captura de dados
        return dados

    def tratar_dados_fiscais(dados_brutos):
        """Aplica regras de negócio para tratar dados fiscais."""
        print("Tratando dados fiscais...")
        dados_tratados = "..." # Lógica de tratamento de dados
        return dados_tratados
    ```
* **Benefício:** Código mais limpo, reutilizável e muito mais fácil de manter. Uma alteração na lógica é feita em um único lugar.

### 3. Crie um Ponto de Entrada Único (`main.py`)
* **Ação:** Desenvolver um script principal (`main.py`) que sirva como um controlador ou menu para executar as diferentes automações importadas dos módulos.
* **Exemplo (`main.py`):**
    ```python
    import automacoes

    def exibir_menu():
        print("\n--- Menu de Automações ---")
        print("1 - Capturar Dados Site A")
        print("2 - Tratar Dados Fiscais")
        print("0 - Sair")
        return input("Selecione a opção desejada: ")

    if __name__ == "__main__":
        while True:
            opcao = exibir_menu()
            if opcao == '1':
                dados_capturados = automacoes.capturar_dados_site_a()
                print("Dados capturados com sucesso!")
                # Futuramente: salvar_no_banco(dados_capturados)
            elif opcao == '2':
                # Lógica para chamar o tratamento
                print("Função de tratamento a ser implementada.")
            elif opcao == '0':
                print("Encerrando o programa.")
                break
            else:
                print("Opção inválida. Tente novamente.")
    ```
* **Benefício:** Elimina a necessidade de compilar um `.exe` para cada script, centralizando a execução em um único ponto.

---

## Fase 2: Integração com o Banco de Dados MySQL 🗃️

Esta fase foca em substituir o armazenamento em planilhas Excel pelo banco de dados MySQL da Hostinger, centralizando a informação.

### 1. Modele o Banco de Dados (Schema)
* **Ação:** Planejar e desenhar a estrutura das tabelas, colunas, tipos de dados e relacionamentos. Traduzir a estrutura das planilhas para um modelo relacional.
* **Exemplo:** Criar uma tabela `produtos` com colunas como `id INT AUTO_INCREMENT PRIMARY KEY`, `nome_produto VARCHAR(255)`, `preco DECIMAL(10, 2)` e `data_coleta DATETIME`.
* **Benefício:** Dados estruturados, consistentes, indexados e prontos para consultas complexas e eficientes.

### 2. Crie um Módulo de Conexão Segura
* **Ação:** Desenvolver um módulo (`database.py`) para encapsular a lógica de conexão com o MySQL. As credenciais (host, usuário, senha, banco) devem ser lidas de variáveis de ambiente ou de um arquivo de configuração (`config.ini`), nunca escritas diretamente no código.
* **Biblioteca Recomendada:** `mysql-connector-python`.
* **Benefício:** Segurança aprimorada e facilidade para gerenciar as credenciais de diferentes ambientes (desenvolvimento, produção).

### 3. Substitua a Lógica do Excel pela do Banco de Dados
* **Ação:** Modificar as funções de automação para, em vez de salvar em arquivos `.xlsx`, chamar funções do módulo de banco de dados para executar operações de `INSERT`, `UPDATE`, etc.
* **Exemplo de função em `database.py`:**
    ```python
    import mysql.connector
    from mysql.connector import Error

    def get_connection():
        # Lógica para ler config e retornar uma conexão
        pass

    def salvar_dados_produto(nome, preco, data):
        """Insere um novo registro de produto no banco de dados."""
        conn = get_connection()
        if conn is None:
            return
        
        try:
            cursor = conn.cursor()
            query = "INSERT INTO produtos (nome_produto, preco, data_coleta) VALUES (%s, %s, %s)"
            cursor.execute(query, (nome, preco, data))
            conn.commit()
            print("Dados salvos no banco de dados com sucesso.")
        except Error as e:
            print(f"Erro ao salvar no banco de dados: {e}")
        finally:
            cursor.close()
            conn.close()
    ```
* **Benefício:** Dados centralizados, seguros, com alta disponibilidade e integridade.

---

## Fase 3: Novas Ideias e Evolução do Projeto 🚀

Com a base sólida implementada, o projeto pode evoluir com funcionalidades avançadas.

### Ideia 1: Crie uma API com Flask ou FastAPI
* **Conceito:** Expor cada automação como um "endpoint" de uma API web. A execução seria acionada por uma requisição HTTP.
* **Benefício:** Desacopla a lógica da execução. Permite acionar as automações a partir de qualquer sistema, agendador ou interface que possa fazer uma chamada web, abrindo portas para integrações futuras.

### Ideia 2: Painel de Controle Web (Dashboard)
* **Conceito:** Criar uma interface web para visualizar os dados armazenados no banco de dados em tempo real.
* **Ferramentas Sugeridas:**
    * **Python:** Usar bibliotecas como **Streamlit** ou **Dash** para criar dashboards interativos rapidamente.
    * **BI Externo:** Conectar o banco de dados MySQL a ferramentas como **Metabase** (código aberto), **Looker Studio** ou **Power BI** para criar relatórios e gráficos profissionais.
* **Benefício:** Transforma dados brutos em informação visual e acionável, agregando enorme valor ao projeto e facilitando a tomada de decisões.

### Ideia 3: Agendamento Automático de Tarefas
* **Conceito:** Automatizar a execução das rotinas em horários pré-definidos.
* **Implementação:**
    * **Nível de SO:** Usar o **Agendador de Tarefas (Windows)** ou **cron (Linux)** para executar o script `main.py`.
    * **Nível de Aplicação:** Integrar a biblioteca **APScheduler** ao projeto Python para ter controle total sobre os agendamentos via código.
* **Benefício:** Operação autônoma do sistema, eliminando a necessidade de execução manual e garantindo a consistência da coleta de dados.
````
# Plano de Projeto: Evolução de Automações Python com Banco de Dados MySQL

Este documento descreve um plano para migrar um projeto de automações em Python, atualmente baseado em scripts locais e planilhas Excel, para uma arquitetura centralizada utilizando um banco de dados MySQL, visando maior profissionalismo, escalabilidade e facilidade de manutenção.

---

## Fase 1: Fundação e Refatoração do Código 🔧 ✅ CONCLUÍDA

~~O objetivo desta fase é abandonar o formato de múltiplos executáveis (`.exe`) e organizar o código de forma modular e profissional, preparando-o para futuras integrações.~~

**STATUS: CONCLUÍDA** - O código foi completamente refatorado seguindo princípios de arquitetura limpa e separação de responsabilidades.

### ✅ 1. Controle de Versão (Git) - CONCLUÍDO
* ~~**Ação:** Criar um único repositório de projeto~~
* **STATUS:** Repositório Git configurado e ativo

### ✅ 2. Modularização - CONCLUÍDO
* ~~**Ação:** Converter cada script de automação em uma função ou classe~~
* **STATUS:** Arquitetura modular implementada:
  - `ui_config.py`: Configurações centralizadas da UI
  - `message_manager.py`: Gerenciamento de mensagens e logs
  - `execution_manager.py`: Gerenciamento de execução de automações
  - `ui_manager.py`: Gerenciamento da interface do usuário
  - `menu_principal.py`: Orquestração principal (280 linhas vs 1047 originais)

* **Exemplo da arquitetura implementada:**
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

### ✅ 3. Ponto de Entrada Único - CONCLUÍDO
* ~~**Ação:** Desenvolver um script principal~~
* **STATUS:** `menu_principal.py` implementado como controlador principal com arquitetura modular

* **Exemplo da implementação atual:**
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
* **Benefícios Alcançados:**
  - ✅ Eliminação da necessidade de múltiplos `.exe`
  - ✅ Centralização da execução em um único ponto
  - ✅ Interface gráfica moderna com CustomTkinter
  - ✅ Separação clara de responsabilidades
  - ✅ Manutenibilidade e testabilidade aprimoradas

---

## Fase 2: Integração com o Banco de Dados MySQL 🗃️ ✅ PARCIALMENTE CONCLUÍDA

~~Esta fase foca em substituir o armazenamento em planilhas Excel pelo banco de dados MySQL da Hostinger, centralizando a informação.~~

**STATUS: PARCIALMENTE CONCLUÍDA** - Integração com MySQL implementada para extração de tokens do Hub XP. Estrutura preparada para expansão para outras automações.

### ✅ 1. Modelagem do Banco - CONCLUÍDO
* ~~**Ação:** Planejar e desenhar a estrutura das tabelas~~
* **STATUS:** Tabela `hub_tokens` implementada:
  - `id` (INT, AUTO_INCREMENT, PRIMARY KEY)
  - `user_login` (VARCHAR(255), indexado)
  - `token` (TEXT)
  - `expires_at` (DATETIME, indexado)
  - `extracted_at` (DATETIME)
  - `created_at` (TIMESTAMP)

### ✅ 2. Módulo de Conexão Segura - CONCLUÍDO
* ~~**Ação:** Desenvolver um módulo de conexão~~
* **STATUS:** Implementado em `renovar_token.py`:
  - Credenciais via arquivo `.env`
  - Pool de conexões MySQL
  - Biblioteca `mysql-connector-python`
  - Tratamento de erros robusto

### 🔄 3. Expansão para Outras Automações - EM ANDAMENTO
* **STATUS ATUAL:** Integração completa para tokens Hub XP
* **PRÓXIMOS PASSOS:** Expandir para outras automações conforme necessário
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
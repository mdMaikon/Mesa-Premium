import os
import json
import datetime
import shutil
from pathlib import Path
from io import BytesIO


class AutomacaoConfig:
    """Gerenciador de configurações específicas por automação - FASE 3.1"""

    def __init__(self, path_manager):
        self.path_manager = path_manager
        self.config_file = path_manager.get_path('config_automacoes')
        self.configuracoes = self._carregar_configuracoes()

    def _carregar_configuracoes(self):
        """Carrega configurações específicas do arquivo JSON"""
        configuracoes_padrao = {
            "Contratos a Termo": {
                "ativo": True,
                "pasta_trabalho": "",
                "arquivo_padrao": "Termos_Rolagem_YYYY-MM-DD.xlsx",
                "arquivo_png": "Termos_Rolagem_YYYY-MM-DD.png",
                "gera_png": True,
                "move_historico": True,
                "copia_clipboard": True
            },
            "Ordens - Op. Estruturadas": {
                "ativo": True,
                "pasta_trabalho": "",
                "arquivo_padrao": "Estruturadas_YYYY-MM-DD.xlsx",
                "gera_png": False,
                "move_historico": True,
                "copia_clipboard": False
            },
            "Processar Cetipados": {
                "ativo": True,
                "pasta_trabalho": "",
                "arquivo_padrao": "Posicoes_Cetipados_YYYY-MM-DD.xlsx",
                "arquivo_png": "Desagios_Cetipados_YYYY-MM-DD.png",
                "gera_png": True,
                "move_historico": True,
                "copia_clipboard": True
            },
            "Renovar Token": {
                "ativo": True,
                "pasta_trabalho": "",
                "arquivo_verificar": "hub_config.json",
                "verificar_atualizacao": True
            },
            "Minimo por Ordem": {
                "ativo": True,
                "pasta_trabalho": "",
                "arquivo_limpar": "Minimo.xlsx",
                "limpar_colunas": True,
                "manter_coluna": "A"
            }
        }

        try:
            if self.config_file is not None and self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_salva = json.load(f)
                    # Mesclar com padrões para garantir que novos campos existam
                    for nome_auto, config_padrao in configuracoes_padrao.items():
                        if nome_auto not in config_salva:
                            config_salva[nome_auto] = config_padrao
                        else:
                            # Adicionar campos que podem estar faltando
                            for campo, valor in config_padrao.items():
                                if campo not in config_salva[nome_auto]:
                                    config_salva[nome_auto][campo] = valor
                    return config_salva
            else:
                # Criar arquivo inicial
                self._salvar_configuracoes(configuracoes_padrao)
                return configuracoes_padrao
        except Exception as e:
            print(f"Erro ao carregar configurações de automações: {e}")
            return configuracoes_padrao

    def _salvar_configuracoes(self, configuracoes=None):
        """Salva configurações no arquivo JSON"""
        try:
            config_para_salvar = configuracoes or self.configuracoes
            if self.config_file is not None:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_para_salvar, f,
                              indent=2, ensure_ascii=False)
            else:
                print(
                    "Erro: Caminho do arquivo de configuração de automações não definido.")
        except Exception as e:
            print(f"Erro ao salvar configurações de automações: {e}")

    def obter_config(self, nome_automacao):
        """Obtém configuração específica de uma automação"""
        return self.configuracoes.get(nome_automacao, {})

    def tem_pos_processamento(self, nome_automacao):
        """Verifica se uma automação tem pós-processamento configurado"""
        config = self.obter_config(nome_automacao)

        # ATUALIZADO - Adicionar "Processar Cetipados"
        automacoes_com_pos = [
            "Contratos a Termo",          # Gestão de arquivos e cópia PNG
            "Ordens - Op. Estruturadas",  # Gestão de arquivos diários
            "Processar Cetipados"         # NOVO - Gestão de arquivos e cópia PNG
        ]

        return nome_automacao in automacoes_com_pos and config.get('ativo', False)

    def executar_pos_processamento(self, nome_automacao, log_callback=None):
        """Executa pós-processamento específico - CORRIGIDO com log_callback"""
        if nome_automacao == "Renovar Token":
            # Fase 3.2 - Verificação do hub_config.json
            if log_callback:
                log_callback(
                    f"[TOKEN] Pós-processamento não necessário para esta automação")

        elif nome_automacao == "Contratos a Termo":
            # Fase 3.4 - Gestão de arquivos e cópia PNG
            if log_callback:
                log_callback(f"[TERMO-PÓS] Iniciando pós-processamento")
            self._pos_processar_contratos_termo(log_callback)

        elif nome_automacao == "Ordens - Op. Estruturadas":
            # Fase 3.4 - Gestão de arquivos diários
            if log_callback:
                log_callback(f"[ESTRUT-PÓS] Iniciando pós-processamento")
            self._pos_processar_ordens_estruturadas(log_callback)

        elif nome_automacao == "Processar Cetipados":
            # NOVO - Fase 3.4 - Gestão de arquivos e cópia PNG
            if log_callback:
                log_callback(f"[CETIP-PÓS] Iniciando pós-processamento")
            self._pos_processar_cetipados(log_callback)

    def tem_pre_processamento(self, nome_automacao):
        """Verifica se uma automação tem pré-processamento configurado"""
        config = self.obter_config(nome_automacao)

        # ATUALIZADO - Adicionar "Processar Cetipados"
        automacoes_com_pre = [
            "Renovar Token",              # Verifica o hub_config.json
            "Contratos a Termo",          # Verifica e move arquivos anteriores
            "Ordens - Op. Estruturadas",  # Verifica e move arquivos anteriores
            "Processar Cetipados"         # NOVO - Verifica e move arquivos anteriores
        ]
        return nome_automacao in automacoes_com_pre and config.get('ativo', False)

    def executar_pre_processamento(self, nome_automacao, log_callback=None):
        """Executa pré-processamento específico - ANTES da execução do .exe"""
        if not self.tem_pre_processamento(nome_automacao):
            return True

        if log_callback:
            log_callback(
                f"[PRÉ] Iniciando pré-processamento: {nome_automacao}")

        try:
            if nome_automacao == "Renovar Token":
                return self._pre_processar_renovar_token(log_callback)
            elif nome_automacao == "Contratos a Termo":
                return self._pre_processar_contratos_termo(log_callback)
            elif nome_automacao == "Ordens - Op. Estruturadas":
                return self._pre_processar_ordens_estruturadas(log_callback)
            elif nome_automacao == "Processar Cetipados":
                # NOVO - Pré-processamento para Cetipados
                return self._pre_processar_cetipados(log_callback)

        except Exception as e:
            if log_callback:
                log_callback(f"[PRÉ] Erro no pré-processamento: {str(e)}")
            return False

        return True

    def _pre_processar_renovar_token(self, log_callback=None):
        """Verifica o hub_config.json ANTES da execução"""
        config = self.obter_config("Renovar Token")
        pasta_trabalho = config.get('pasta_trabalho', '')
        if not pasta_trabalho:
            pasta_trabalho = self.path_manager.get_path(
                'base') / "TOKEN"
        else:
            pasta_trabalho = Path(pasta_trabalho)

        arquivo_config = pasta_trabalho / "hub_config.json"

        if log_callback:
            log_callback(f"[TOKEN] Verificando hub_config.json")

        try:
            if arquivo_config is not None and arquivo_config.exists():
                stat_info = arquivo_config.stat()
                data_modificacao = datetime.datetime.fromtimestamp(
                    stat_info.st_mtime)
                agora = datetime.datetime.now()
                diferenca = agora - data_modificacao
                horas_diferenca = diferenca.total_seconds() / 3600
                data_formatada = data_modificacao.strftime(
                    "%d/%m/%Y às %H:%M:%S")

                if log_callback:
                    log_callback(f"[TOKEN] ✓ Arquivo encontrado")
                    log_callback(
                        f"[TOKEN] Última atualização: {data_formatada}")

                    # NOVA LÓGICA: Verificar se token está atualizado
                    if horas_diferenca < 6:  # ou o limite que você preferir
                        return False  # Retorna False para indicar que não deve executar o .exe
                    else:
                        log_callback(
                            f"[TOKEN] ⚠️ Token desatualizado - Prosseguindo com execução")
                        return True  # Retorna True para executar o .exe

                return True
            else:
                if log_callback:
                    log_callback(
                        f"[TOKEN] ✗ Arquivo {arquivo_config.name} não encontrado")
                    log_callback(
                        f"[TOKEN] Prosseguindo com execução para gerar token")
                return True  # Se não existe, precisa executar para criar

        except Exception as e:
            if log_callback:
                log_callback(f"[TOKEN] Erro ao verificar arquivo: {str(e)}")
            return True  # Em caso de erro, executar por segurança

    def _pre_processar_contratos_termo(self, log_callback=None):
        """Verifica e move arquivos de dias anteriores para Histórico"""
        config = self.obter_config("Contratos a Termo")
        pasta_trabalho_str = config.get('pasta_trabalho', '')

        if not pasta_trabalho_str:
            # Usar pasta padrão se não configurada
            pasta_trabalho = self.path_manager.get_path(
                'base') / "Contratos a Termo"
        else:
            pasta_trabalho = Path(pasta_trabalho_str)

        try:
            # Criar pasta se não existir
            if not pasta_trabalho.exists():
                pasta_trabalho.mkdir(parents=True, exist_ok=True)
                if log_callback:
                    log_callback(
                        f"[TERMO-PRÉ] ✓ Pasta criada: {pasta_trabalho}")
                return True  # Retorna True para continuar com execução

            # Verificar pasta de histórico
            pasta_historico = pasta_trabalho / "Histórico"
            if not pasta_historico.exists():
                pasta_historico.mkdir(parents=True, exist_ok=True)
                if log_callback:
                    log_callback(
                        f"[TERMO-PRÉ] ✓ Pasta histórico criada: {pasta_historico}")

            # Obter data de hoje para comparação
            hoje = datetime.datetime.now().date()
            if log_callback:
                log_callback(f"[TERMO-PRÉ] Data atual: {hoje}")

            # CORREÇÃO 1: Buscar todos os arquivos Excel na pasta
            # Não usar padrão específico, buscar todos os .xlsx
            arquivos_xlsx = list(pasta_trabalho.glob("*.xlsx"))

            if log_callback:
                log_callback(
                    f"[TERMO-PRÉ] Encontrados {len(arquivos_xlsx)} arquivos Excel para verificação")

            # Verificar quais são de dias anteriores
            arquivos_movidos = 0
            for arquivo in arquivos_xlsx:
                try:
                    nome = arquivo.name

                    # CORREÇÃO 2: Buscar padrão de data mais flexível
                    # Procurar por padrão YYYY-MM-DD no nome do arquivo
                    import re
                    padrao_data = r'(\d{4}-\d{2}-\d{2})'
                    match = re.search(padrao_data, nome)

                    if match:
                        data_str = match.group(1)

                        try:
                            data_arquivo = datetime.datetime.strptime(
                                data_str, '%Y-%m-%d').date()

                            # CORREÇÃO 3: Verificar se é de dia anterior ou mais antigo
                            if data_arquivo < hoje:  # Qualquer dia anterior ao hoje
                                # Mover para histórico
                                arquivo_destino = pasta_historico / nome
                                arquivo_renomeado = False

                                # Verificar se já existe arquivo com mesmo nome no histórico
                                if arquivo_destino.exists():
                                    # Adicionar timestamp para evitar conflito
                                    timestamp = datetime.datetime.now().strftime("%H%M%S")
                                    nome_sem_ext = arquivo_destino.stem
                                    extensao = arquivo_destino.suffix
                                    arquivo_destino = pasta_historico / \
                                        f"{nome_sem_ext}_{timestamp}{extensao}"
                                    arquivo_renomeado = True

                                shutil.move(str(arquivo), str(arquivo_destino))
                                arquivos_movidos += 1

                                if arquivo_renomeado:
                                    log_callback(
                                        f"[TERMO-PRÉ] ℹ️ Renomeado para evitar conflito: {arquivo_destino.name}")
                            else:
                                if log_callback:
                                    log_callback(
                                        f"[TERMO-PRÉ] ℹ️ Arquivo mantido (data atual): {nome}")

                        except ValueError as ve:
                            if log_callback:
                                log_callback(
                                    f"[TERMO-PRÉ] ⚠️ Erro ao converter data '{data_str}': {str(ve)}")
                    else:
                        if log_callback:
                            log_callback(
                                f"[TERMO-PRÉ] ℹ️ Arquivo sem padrão de data reconhecido: {nome}")

                except Exception as e:
                    if log_callback:
                        log_callback(
                            f"[TERMO-PRÉ] ⚠️ Erro ao processar arquivo {arquivo.name}: {str(e)}")

            # CORREÇÃO 4: Mesma lógica para arquivos PNG
            if config.get('gera_png', True):
                arquivos_png = list(pasta_trabalho.glob("*.png"))

                if log_callback:
                    log_callback(
                        f"[TERMO-PRÉ] Encontrados {len(arquivos_png)} arquivos PNG para verificação")

                for arquivo in arquivos_png:
                    try:
                        nome = arquivo.name
                        if log_callback:
                            log_callback(
                                f"[TERMO-PRÉ] Processando PNG: {nome}")

                        # Buscar padrão de data no PNG
                        import re
                        padrao_data = r'(\d{4}-\d{2}-\d{2})'
                        match = re.search(padrao_data, nome)

                        if match:
                            data_str = match.group(1)

                            try:
                                data_arquivo = datetime.datetime.strptime(
                                    data_str, '%Y-%m-%d').date()

                                # Verificar se é de dia anterior ou mais antigo
                                if data_arquivo < hoje:
                                    # Mover para histórico
                                    arquivo_destino = pasta_historico / nome
                                    arquivo_renomeado = False

                                    # Verificar se já existe arquivo com mesmo nome no histórico
                                    if arquivo_destino.exists():
                                        # Adicionar timestamp para evitar conflito
                                        timestamp = datetime.datetime.now().strftime("%H%M%S")
                                        nome_sem_ext = arquivo_destino.stem
                                        extensao = arquivo_destino.suffix
                                        arquivo_destino = pasta_historico / \
                                            f"{nome_sem_ext}_{timestamp}{extensao}"
                                        arquivo_renomeado = True

                                    shutil.move(
                                        str(arquivo), str(arquivo_destino))
                                    arquivos_movidos += 1

                                    if arquivo_renomeado:
                                        log_callback(
                                            f"[TERMO-PRÉ] ℹ️ PNG renomeado para evitar conflito: {arquivo_destino.name}")
                                else:
                                    if log_callback:
                                        log_callback(
                                            f"[TERMO-PRÉ] ℹ️ PNG mantido (data atual): {nome}")

                            except ValueError as ve:
                                if log_callback:
                                    log_callback(
                                        f"[TERMO-PRÉ] ⚠️ Erro ao converter data do PNG '{data_str}': {str(ve)}")
                        else:
                            if log_callback:
                                log_callback(
                                    f"[TERMO-PRÉ] ℹ️ PNG sem padrão de data reconhecido: {nome}")

                    except Exception as e:
                        if log_callback:
                            log_callback(
                                f"[TERMO-PRÉ] ⚠️ Erro ao processar PNG {arquivo.name}: {str(e)}")

            if log_callback:
                log_callback(f"[TERMO-PRÉ] ✓ Pré-processamento concluído")
                log_callback(
                    f"[TERMO-PRÉ] Total de arquivos movidos: {arquivos_movidos}")

            return True  # Continuar com a execução normal

        except Exception as e:
            if log_callback:
                log_callback(f"[TERMO-PRÉ] Erro geral: {str(e)}")
            return True  # Mesmo com erro, continua a execução

    def _pre_processar_ordens_estruturadas(self, log_callback=None):
        """Verifica e move arquivos de dias anteriores para Histórico - Ordens Estruturadas"""
        config = self.obter_config("Ordens - Op. Estruturadas")
        pasta_trabalho_str = config.get('pasta_trabalho', '')

        if not pasta_trabalho_str:
            pasta_trabalho = self.path_manager.get_path(
                'base') / "Histórico Estruturadas"
        else:
            pasta_trabalho = Path(pasta_trabalho_str)

        try:
            if not pasta_trabalho.exists():
                pasta_trabalho.mkdir(parents=True, exist_ok=True)
                if log_callback:
                    log_callback(
                        f"[ESTRUT-PRÉ] ✓ Pasta criada: {pasta_trabalho}")
                return True

            pasta_historico = pasta_trabalho / "Histórico"
            if not pasta_historico.exists():
                pasta_historico.mkdir(parents=True, exist_ok=True)
                if log_callback:
                    log_callback(
                        f"[ESTRUT-PRÉ] ✓ Pasta histórico criada: {pasta_historico}")

            hoje = datetime.datetime.now().date()
            if log_callback:
                log_callback(f"[ESTRUT-PRÉ] Data atual: {hoje}")

            # Buscar arquivos Excel na pasta principal
            arquivos_xlsx = list(pasta_trabalho.glob("*.xlsx"))
            if log_callback:
                log_callback(
                    f"[ESTRUT-PRÉ] Encontrados {len(arquivos_xlsx)} arquivos Excel para verificação")

            arquivos_movidos = 0
            for arquivo in arquivos_xlsx:
                try:
                    nome = arquivo.name
                    import re
                    # Buscar padrão de data YYYY-MM-DD no nome do arquivo
                    padrao_data = r'(\d{4}-\d{2}-\d{2})'
                    match = re.search(padrao_data, nome)

                    if match:
                        data_str = match.group(1)
                        try:
                            data_arquivo = datetime.datetime.strptime(
                                data_str, '%Y-%m-%d').date()

                            # Se é de dia anterior, mover para histórico
                            if data_arquivo < hoje:
                                arquivo_destino = pasta_historico / nome

                                # Verificar se já existe arquivo com mesmo nome no histórico
                                if arquivo_destino.exists():
                                    timestamp = datetime.datetime.now().strftime("%H%M%S")
                                    nome_sem_ext = arquivo_destino.stem
                                    extensao = arquivo_destino.suffix
                                    arquivo_destino = pasta_historico / \
                                        f"{nome_sem_ext}_{timestamp}{extensao}"
                                    if log_callback:
                                        log_callback(
                                            f"[ESTRUT-PRÉ] ℹ️ Renomeado para evitar conflito: {arquivo_destino.name}")

                                shutil.move(str(arquivo), str(arquivo_destino))
                                arquivos_movidos += 1

                                if log_callback:
                                    log_callback(
                                        f"[ESTRUT-PRÉ] ℹ️ Arquivo mantido (data atual): {nome}")

                        except ValueError as ve:
                            if log_callback:
                                log_callback(
                                    f"[ESTRUT-PRÉ] ⚠️ Erro ao converter data '{data_str}': {str(ve)}")
                    else:
                        if log_callback:
                            log_callback(
                                f"[ESTRUT-PRÉ] ℹ️ Arquivo sem padrão de data reconhecido: {nome}")

                except Exception as e:
                    if log_callback:
                        log_callback(
                            f"[ESTRUT-PRÉ] ⚠️ Erro ao processar arquivo {arquivo.name}: {str(e)}")

            if log_callback:
                log_callback(
                    f"[ESTRUT-PRÉ] Total de arquivos movidos: {arquivos_movidos}")

            return True

        except Exception as e:
            if log_callback:
                log_callback(f"[ESTRUT-PRÉ] Erro geral: {str(e)}")
            return True  # Continua execução mesmo com erro

    def _pre_processar_cetipados(self, log_callback=None):
        """Verifica e move arquivos de dias anteriores para Histórico - Cetipados"""
        config = self.obter_config("Processar Cetipados")
        pasta_trabalho_str = config.get('pasta_trabalho', '')

        if not pasta_trabalho_str:
            pasta_trabalho = self.path_manager.get_path('base') / "Cetipados"
        else:
            pasta_trabalho = Path(pasta_trabalho_str)

        try:
            if not pasta_trabalho.exists():
                pasta_trabalho.mkdir(parents=True, exist_ok=True)
                if log_callback:
                    log_callback(
                        f"[CETIP-PRÉ] ✓ Pasta criada: {pasta_trabalho}")
                return True

            pasta_historico = pasta_trabalho / "Histórico"
            if not pasta_historico.exists():
                pasta_historico.mkdir(parents=True, exist_ok=True)
                if log_callback:
                    log_callback(
                        f"[CETIP-PRÉ] ✓ Pasta histórico criada: {pasta_historico}")

            hoje = datetime.datetime.now().date()
            if log_callback:
                log_callback(f"[CETIP-PRÉ] Data atual: {hoje}")

            # Buscar arquivos Excel na pasta principal
            arquivos_xlsx = list(pasta_trabalho.glob("*.xlsx"))
            if log_callback:
                log_callback(
                    f"[CETIP-PRÉ] Encontrados {len(arquivos_xlsx)} arquivos Excel para verificação")

            arquivos_movidos = 0
            for arquivo in arquivos_xlsx:
                try:
                    nome = arquivo.name
                    import re
                    # Buscar padrão de data YYYY-MM-DD no nome do arquivo
                    padrao_data = r'(\d{4}-\d{2}-\d{2})'
                    match = re.search(padrao_data, nome)

                    if match:
                        data_str = match.group(1)
                        try:
                            data_arquivo = datetime.datetime.strptime(
                                data_str, '%Y-%m-%d').date()

                            # Se é de dia anterior, mover para histórico
                            if data_arquivo < hoje:
                                arquivo_destino = pasta_historico / nome

                                # Verificar se já existe arquivo com mesmo nome no histórico
                                if arquivo_destino.exists():
                                    timestamp = datetime.datetime.now().strftime("%H%M%S")
                                    nome_sem_ext = arquivo_destino.stem
                                    extensao = arquivo_destino.suffix
                                    arquivo_destino = pasta_historico / \
                                        f"{nome_sem_ext}_{timestamp}{extensao}"
                                    if log_callback:
                                        log_callback(
                                            f"[CETIP-PRÉ] ℹ️ Renomeado para evitar conflito: {arquivo_destino.name}")

                                shutil.move(str(arquivo), str(arquivo_destino))
                                arquivos_movidos += 1
                                if log_callback:
                                    log_callback(
                                        f"[CETIP-PRÉ] ✓ Movido: {nome} → Histórico/")
                            else:
                                if log_callback:
                                    log_callback(
                                        f"[CETIP-PRÉ] ℹ️ Arquivo mantido (data atual): {nome}")

                        except ValueError as ve:
                            if log_callback:
                                log_callback(
                                    f"[CETIP-PRÉ] ⚠️ Erro ao converter data '{data_str}': {str(ve)}")
                    else:
                        if log_callback:
                            log_callback(
                                f"[CETIP-PRÉ] ℹ️ Arquivo sem padrão de data reconhecido: {nome}")

                except Exception as e:
                    if log_callback:
                        log_callback(
                            f"[CETIP-PRÉ] ⚠️ Erro ao processar arquivo {arquivo.name}: {str(e)}")

            # Processar arquivos PNG também
            if config.get('gera_png', True):
                arquivos_png = list(pasta_trabalho.glob("*.png"))
                if log_callback:
                    log_callback(
                        f"[CETIP-PRÉ] Encontrados {len(arquivos_png)} arquivos PNG para verificação")

                for arquivo in arquivos_png:
                    try:
                        nome = arquivo.name
                        import re
                        padrao_data = r'(\d{4}-\d{2}-\d{2})'
                        match = re.search(padrao_data, nome)

                        if match:
                            data_str = match.group(1)
                            try:
                                data_arquivo = datetime.datetime.strptime(
                                    data_str, '%Y-%m-%d').date()

                                if data_arquivo < hoje:
                                    arquivo_destino = pasta_historico / nome
                                    if arquivo_destino.exists():
                                        timestamp = datetime.datetime.now().strftime("%H%M%S")
                                        nome_sem_ext = arquivo_destino.stem
                                        extensao = arquivo_destino.suffix
                                        arquivo_destino = pasta_historico / \
                                            f"{nome_sem_ext}_{timestamp}{extensao}"

                                    shutil.move(
                                        str(arquivo), str(arquivo_destino))
                                    arquivos_movidos += 1
                                    if log_callback:
                                        log_callback(
                                            f"[CETIP-PRÉ] ✓ PNG movido: {nome} → Histórico/")
                                else:
                                    if log_callback:
                                        log_callback(
                                            f"[CETIP-PRÉ] ℹ️ PNG mantido (data atual): {nome}")

                            except ValueError as ve:
                                if log_callback:
                                    log_callback(
                                        f"[CETIP-PRÉ] ⚠️ Erro ao converter data do PNG '{data_str}': {str(ve)}")
                        else:
                            if log_callback:
                                log_callback(
                                    f"[CETIP-PRÉ] ℹ️ PNG sem padrão de data reconhecido: {nome}")

                    except Exception as e:
                        if log_callback:
                            log_callback(
                                f"[CETIP-PRÉ] ⚠️ Erro ao processar PNG {arquivo.name}: {str(e)}")

            if log_callback:
                log_callback(f"[CETIP-PRÉ] ✓ Pré-processamento concluído")
                log_callback(
                    f"[CETIP-PRÉ] Total de arquivos movidos: {arquivos_movidos}")

            return True

        except Exception as e:
            if log_callback:
                log_callback(f"[CETIP-PRÉ] Erro geral: {str(e)}")
            return True  # Continua execução mesmo com erro

    def _pos_processar_contratos_termo(self, log_callback=None):
        """Processa arquivos gerados e copia PNG para área de transferência"""
        config = self.obter_config("Contratos a Termo")
        pasta_trabalho_str = config.get('pasta_trabalho', '')

        if not pasta_trabalho_str:
            # Usar pasta padrão se não configurada
            pasta_trabalho = self.path_manager.get_path(
                'base') / "Contratos a Termo"
        else:
            pasta_trabalho = Path(pasta_trabalho_str)

        if log_callback:
            log_callback(f"[TERMO-PÓS] Verificando arquivos gerados")

        try:
            # Verificar se a pasta existe
            if not pasta_trabalho.exists():
                if log_callback:
                    log_callback(
                        f"[TERMO-PÓS] ✗ Pasta não encontrada: {pasta_trabalho}")
                return False

            # Obter data de hoje formatada
            hoje = datetime.datetime.now().strftime('%Y-%m-%d')

            # Montar nomes de arquivos esperados
            padrao_arquivo = config.get(
                'arquivo_padrao', 'Termos_Rolagem_YYYY-MM-DD.xlsx')
            arquivo_hoje = padrao_arquivo.replace('YYYY-MM-DD', hoje)

            arquivo_excel = pasta_trabalho / arquivo_hoje

            # Verificar se o arquivo Excel foi gerado
            if not arquivo_excel.exists():
                if log_callback:
                    log_callback(
                        f"[TERMO-PÓS] ⚠️ Arquivo Excel não encontrado: {arquivo_hoje}")
                    log_callback(
                        f"[TERMO-PÓS] Verifique se a automação gerou o arquivo corretamente")
                return False

            if log_callback:
                log_callback(
                    f"[TERMO-PÓS] ✓ Arquivo Excel encontrado: {arquivo_hoje}")

            # Se gera PNG, verificar arquivo PNG
            if config.get('gera_png', True):
                padrao_png = config.get(
                    'arquivo_png', 'Termos_Rolagem_YYYY-MM-DD.png')
                png_hoje = padrao_png.replace('YYYY-MM-DD', hoje)

                arquivo_png = pasta_trabalho / png_hoje

                if not arquivo_png.exists():
                    if log_callback:
                        log_callback(
                            f"[TERMO-PÓS] ⚠️ Arquivo PNG não encontrado: {png_hoje}")
                        log_callback(
                            f"[TERMO-PÓS] Verifique se a automação gerou o PNG corretamente")
                else:
                    if log_callback:
                        log_callback(
                            f"[TERMO-PÓS] ✓ Arquivo PNG encontrado: {png_hoje}")

                    # Copiar PNG para área de transferência se configurado
                    if config.get('copia_clipboard', True):
                        success = self._copiar_imagem_clipboard(
                            arquivo_png, log_callback)
                        if success:
                            if log_callback:
                                log_callback(
                                    f"[TERMO-PÓS] ✓ PNG copiado para área de transferência")
                        else:
                            if log_callback:
                                log_callback(
                                    f"[TERMO-PÓS] ✗ Falha ao copiar PNG para área de transferência")

            if log_callback:
                log_callback(f"[TERMO-PÓS] ✓ Pós-processamento concluído")

            return True

        except Exception as e:
            if log_callback:
                log_callback(f"[TERMO-PÓS] Erro geral: {str(e)}")
            return False

    def _pos_processar_ordens_estruturadas(self, log_callback=None):
        """Verifica arquivos gerados para Ordens Estruturadas"""
        config = self.obter_config("Ordens - Op. Estruturadas")
        pasta_trabalho_str = config.get('pasta_trabalho', '')

        if not pasta_trabalho_str:
            pasta_trabalho = self.path_manager.get_path(
                'base') / "Histórico Estruturadas"
        else:
            pasta_trabalho = Path(pasta_trabalho_str)

        if log_callback:
            log_callback(f"[ESTRUT-PÓS] Verificando arquivos gerados")

        try:
            if not pasta_trabalho.exists():
                if log_callback:
                    log_callback(
                        f"[ESTRUT-PÓS] ✗ Pasta não encontrada: {pasta_trabalho}")
                return False

            hoje = datetime.datetime.now().strftime('%Y-%m-%d')
            padrao_arquivo = config.get(
                'arquivo_padrao', 'Estruturadas_YYYY-MM-DD.xlsx')
            arquivo_hoje = padrao_arquivo.replace('YYYY-MM-DD', hoje)
            arquivo_excel = pasta_trabalho / arquivo_hoje

            if not arquivo_excel.exists():
                if log_callback:
                    log_callback(
                        f"[ESTRUT-PÓS] ⚠️ Arquivo Excel não encontrado: {arquivo_hoje}")
                    log_callback(
                        f"[ESTRUT-PÓS] Verifique se a automação gerou o arquivo corretamente")
                return False

            if log_callback:
                log_callback(
                    f"[ESTRUT-PÓS] ✓ Arquivo Excel encontrado: {arquivo_hoje}")

            if log_callback:
                log_callback(f"[ESTRUT-PÓS] ✓ Pós-processamento concluído")
                log_callback(
                    f"[ESTRUT-PÓS] 📁 Arquivo disponível em: {pasta_trabalho.name}")

            return True

        except Exception as e:
            if log_callback:
                log_callback(f"[ESTRUT-PÓS] Erro geral: {str(e)}")
            return False

    def _pos_processar_cetipados(self, log_callback=None):
        """Processa arquivos gerados e copia PNG para área de transferência - Cetipados"""
        config = self.obter_config("Processar Cetipados")
        pasta_trabalho_str = config.get('pasta_trabalho', '')

        if not pasta_trabalho_str:
            pasta_trabalho = self.path_manager.get_path('base') / "Cetipados"
        else:
            pasta_trabalho = Path(pasta_trabalho_str)

        if log_callback:
            log_callback(f"[CETIP-PÓS] Verificando arquivos gerados")

        try:
            if not pasta_trabalho.exists():
                if log_callback:
                    log_callback(
                        f"[CETIP-PÓS] ✗ Pasta não encontrada: {pasta_trabalho}")
                return False

            hoje = datetime.datetime.now().strftime('%Y-%m-%d')

            # Verificar arquivo Excel
            padrao_arquivo = config.get(
                'arquivo_padrao', 'Posicoes_Cetipados_YYYY-MM-DD.xlsx')
            arquivo_hoje = padrao_arquivo.replace('YYYY-MM-DD', hoje)
            arquivo_excel = pasta_trabalho / arquivo_hoje

            if not arquivo_excel.exists():
                if log_callback:
                    log_callback(
                        f"[CETIP-PÓS] ⚠️ Arquivo Excel não encontrado: {arquivo_hoje}")
                    log_callback(
                        f"[CETIP-PÓS] Verifique se a automação gerou o arquivo corretamente")
                return False

            if log_callback:
                log_callback(
                    f"[CETIP-PÓS] ✓ Arquivo Excel encontrado: {arquivo_hoje}")

            # Verificar e processar arquivo PNG se configurado
            if config.get('gera_png', True):
                padrao_png = config.get(
                    'arquivo_png', 'Desagios_Cetipados_YYYY-MM-DD.png')
                png_hoje = padrao_png.replace('YYYY-MM-DD', hoje)
                arquivo_png = pasta_trabalho / png_hoje

                if not arquivo_png.exists():
                    if log_callback:
                        log_callback(
                            f"[CETIP-PÓS] ⚠️ Arquivo PNG não encontrado: {png_hoje}")
                        log_callback(
                            f"[CETIP-PÓS] Verifique se a automação gerou o PNG corretamente")
                else:
                    if log_callback:
                        log_callback(
                            f"[CETIP-PÓS] ✓ Arquivo PNG encontrado: {png_hoje}")

                    # Copiar PNG para área de transferência se configurado
                    if config.get('copia_clipboard', True):
                        success = self._copiar_imagem_clipboard(
                            arquivo_png, log_callback)
                        if success:
                            if log_callback:
                                log_callback(
                                    f"[CETIP-PÓS] ✓ PNG copiado para área de transferência")
                        else:
                            if log_callback:
                                log_callback(
                                    f"[CETIP-PÓS] ✗ Falha ao copiar PNG para área de transferência")

            if log_callback:
                log_callback(f"[CETIP-PÓS] ✓ Pós-processamento concluído")
                log_callback(
                    f"[CETIP-PÓS] 📁 Arquivos disponíveis em: {pasta_trabalho.name}")

            return True

        except Exception as e:
            if log_callback:
                log_callback(f"[CETIP-PÓS] Erro geral: {str(e)}")
            return False

    def _copiar_imagem_clipboard(self, caminho_imagem, log_callback=None):
        """Copia uma imagem para a área de transferência"""
        try:
            if not Path(caminho_imagem).exists():
                if log_callback:
                    log_callback(
                        f"[CLIPBOARD] ✗ Arquivo não encontrado: {caminho_imagem}")
                return False

            # Tentar usar pillow e pywin32 para copiar imagem para clipboard
            try:
                from PIL import Image
                import win32clipboard

                if log_callback:
                    log_callback(
                        f"[CLIPBOARD] Copiando imagem para área de transferência...")

                # Abrir imagem com PIL
                imagem = Image.open(caminho_imagem)

                # Converter para formato compatível com clipboard do Windows
                output = BytesIO()
                imagem.convert('RGB').save(output, 'BMP')
                data = output.getvalue()[14:]  # Remover cabeçalho BMP
                output.close()

                # Copiar para clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()

                return True

            except ImportError:
                # Alternativa usando subprocess (apenas para Windows)
                if os.name == 'nt':  # Windows
                    try:
                        import subprocess

                        # Usar PowerShell para copiar imagem para clipboard
                        ps_script = f"""
                        Add-Type -Assembly System.Windows.Forms
                        Add-Type -Assembly System.Drawing
                        $img = [System.Drawing.Image]::FromFile('{caminho_imagem}')
                        [System.Windows.Forms.Clipboard]::SetImage($img)
                        """

                        # Executar PowerShell
                        result = subprocess.run(
                            ['powershell', '-Command', ps_script],
                            capture_output=True,
                            text=True
                        )

                        if result.returncode == 0:
                            return True
                        else:
                            if log_callback:
                                log_callback(
                                    f"[CLIPBOARD] ✗ Erro ao executar PowerShell: {result.stderr}")
                            return False

                    except Exception as e:
                        if log_callback:
                            log_callback(
                                f"[CLIPBOARD] ✗ Erro ao usar método alternativo: {str(e)}")
                        return False
                else:
                    if log_callback:
                        log_callback(
                            f"[CLIPBOARD] ✗ Sistema operacional não suportado: {os.name}")
                    return False

        except Exception as e:
            if log_callback:
                log_callback(f"[CLIPBOARD] ✗ Erro ao copiar imagem: {str(e)}")
            return False

    def abrir_pasta_automacao(self, nome_automacao, log_callback=None):
        """Abre a pasta específica de uma automação"""
        try:
            config = self.obter_config(nome_automacao)
            pasta_trabalho_str = config.get('pasta_trabalho', '')

            if not pasta_trabalho_str:
                # Definir pastas padrão baseadas no nome da automação
                pastas_padrao = {
                    "Contratos a Termo": "Contratos a Termo",
                    "Ordens - Op. Estruturadas": "Histórico Estruturadas",
                    "Processar Cetipados": "Cetipados",
                    "Renovar Token": "TOKEN",
                    "Minimo por Ordem": "Minimo por Ordem"
                }

                pasta_padrao = pastas_padrao.get(
                    nome_automacao, nome_automacao)
                pasta_trabalho = self.path_manager.get_path(
                    'base') / pasta_padrao
            else:
                pasta_trabalho = Path(pasta_trabalho_str)

            # Abrir pasta no explorer
            import os
            os.startfile(str(pasta_trabalho))

            if log_callback:
                log_callback(f"[PASTA] 📁 Aberta: {pasta_trabalho}")

            return True

        except Exception as e:
            if log_callback:
                log_callback(f"[PASTA] Erro ao abrir pasta.")
            return False

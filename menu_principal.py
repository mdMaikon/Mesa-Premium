import customtkinter as ctk
from tkinter import messagebox, font
import os
import sys
import subprocess
import threading
import datetime
import json
from pathlib import Path
import time

# Importar classes de módulos separados
from path_manager import PathManager
from automacao_config import AutomacaoConfig
from database import DatabaseManager
from automacao_manager import AutomacaoManager

# Configurações do CustomTkinter
ctk.set_appearance_mode("light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class MenuAutomacoes:
    def __init__(self):
        # Inicializar gerenciadores
        self.path_manager = PathManager()
        self.automacao_config = AutomacaoConfig(self.path_manager)
        self.db_manager = DatabaseManager()
        self.automacao_manager = AutomacaoManager(self.path_manager, self.db_manager)

        # Configurar janela principal
        self.root = ctk.CTk()
        self.root.title("Mesa Premium • Automações")
        
        
        # Configurar ícone se disponível
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass

        # Usar caminhos do PathManager
        self.automacoes_dir = self.path_manager.get_path('automacoes')
        self.logs_dir = self.path_manager.get_path('logs')
        self.config_file = self.path_manager.get_path('config')
        
        # Lista de automações (agora vem do AutomacaoManager)
        self.automacoes_disponiveis = []
        self.automacoes_cache = {}

        # Variáveis de controle
        self.processos_ativos = {}
        self.automacoes_encontradas = []
        self.automacoes_filtradas = []
        self.filtro_pesquisa = ""
        self.log_interno = []
        self.mensagens_usuario = []
        self.max_mensagens_usuario = 5
        self.automacao_selecionada_atual = None

        # Variáveis de animação
        self.animacao_ativa = False
        self.progresso_execucao = {}

        # Cores personalizadas (modo claro apenas)
        self.cores = {
            'primary': '#001d99',
            'primary_hover': '#002064',
            'accent': '#0092ff',
            'accent_hover': '#007ad8',
            'success': '#28a745',
            'success_hover': '#218838',
            'danger': '#dc3545',
            'danger_hover': '#c82333',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'executing': '#ff8c00',  # Laranja para execução
            'bg_primary': '#ffffff',
            'bg_secondary': '#f8f9fa',
            'text_primary': '#000000',
            'text_secondary': '#6c757d',
            'border': '#dee2e6'
        }
        
        self.criar_interface_moderna()
        self.carregar_automacoes()
        self.carregar_configuracoes()
        self.adicionar_atalhos_modernos()
        self.configurar_responsividade_moderna()

        # Bind para salvar logs ao fechar
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)


    def criar_interface_moderna(self):
        """Cria interface moderna com CustomTkinter"""
        
        # Container principal com padding
        self.container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.container.pack(fill='both', expand=True, padx=20, pady=20)

        # === HEADER ===
        self.criar_header_moderno()

        # === ÁREA PRINCIPAL (2 colunas) ===
        main_container = ctk.CTkFrame(self.container, fg_color="transparent")
        main_container.pack(fill='both', expand=True, pady=(20, 0))

        # Configurar grid
        main_container.grid_columnconfigure(0, weight=2)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        # Coluna esquerda - Lista de automações
        self.criar_lista_automacoes_moderna(main_container)

        # Coluna direita - Detalhes e status
        self.criar_painel_detalhes_moderno(main_container)

    def criar_header_moderno(self):
        """Cria header moderno com CustomTkinter"""
        header = ctk.CTkFrame(self.container, fg_color="transparent", height=140)
        header.pack(fill='x')
        header.pack_propagate(False)

        # === LINHA SUPERIOR ===
        top_row = ctk.CTkFrame(header, fg_color="transparent")
        top_row.pack(fill='x', pady=(0, 15))

        # Logo/Título à esquerda
        titulo_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        titulo_frame.pack(side='left', fill='y')

        titulo = ctk.CTkLabel(titulo_frame,
                             text="Mesa Premium",
                             font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
                             text_color=self.cores['primary'])
        titulo.pack(anchor='w')

        subtitulo = ctk.CTkLabel(titulo_frame,
                                text="Menu de Automações • Central de Processos",
                                font=ctk.CTkFont(family="Segoe UI", size=12),
                                text_color="gray50")
        subtitulo.pack(anchor='w')

        # Status e contador à direita
        right_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        right_frame.pack(side='right', fill='y')

        # Status geral
        self.status_geral = ctk.CTkLabel(right_frame,
                                        text="● Sistema Operacional",
                                        font=ctk.CTkFont(family="Segoe UI", size=12),
                                        text_color=self.cores['success'])
        self.status_geral.pack(anchor='e', pady=(10, 5))

        # Contador de automações
        self.contador_automacoes = ctk.CTkLabel(right_frame,
                                               text="0 automações disponíveis",
                                               font=ctk.CTkFont(family="Segoe UI", size=11),
                                               text_color="gray60")
        self.contador_automacoes.pack(anchor='e')

        # === LINHA INFERIOR - Ferramentas ===
        self.criar_toolbar_moderno(header)

    def criar_toolbar_moderno(self, parent):
        """Cria toolbar moderno com botões estilizados"""
        toolbar = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)

        # Container para botões à esquerda
        botoes_container = ctk.CTkFrame(toolbar, fg_color="transparent")
        botoes_container.pack(side='left', pady=5)

        # Botões de ferramentas
        self.btn_atualizar = ctk.CTkButton(botoes_container,
                                          text="🔄 Atualizar",
                                          command=self.carregar_automacoes,
                                          width=120,
                                          height=32,
                                          font=ctk.CTkFont(size=12),
                                          fg_color="gray85",
                                          hover_color="gray80",
                                          text_color="gray20",
                                          corner_radius=6)
        self.btn_atualizar.pack(side='left', padx=(0, 10))

        self.btn_logs = ctk.CTkButton(botoes_container,
                                     text="💾 Exportar Logs",
                                     command=self.exportar_logs_completos,
                                     width=140,
                                     height=32,
                                     font=ctk.CTkFont(size=12),
                                     fg_color="gray85",
                                     hover_color="gray80",
                                     text_color="gray20",
                                     corner_radius=6)
        self.btn_logs.pack(side='left', padx=(0, 10))

        self.btn_token = ctk.CTkButton(botoes_container,
                                      text="🔑 Renovar Token",
                                      command=self.executar_renovar_token,
                                      width=130,
                                      height=32,
                                      font=ctk.CTkFont(size=12),
                                      fg_color=self.cores['info'],
                                      hover_color="gray80",
                                      text_color="white",
                                      corner_radius=6)
        self.btn_token.pack(side='left')

        # Info de atalhos à direita (em container separado para melhor controle)
        atalhos_container = ctk.CTkFrame(toolbar, fg_color="transparent")
        atalhos_container.pack(side='right', fill='y')
        
        atalhos_label = ctk.CTkLabel(atalhos_container,
                                    text="Enter: Executar | Ctrl+T: Token | F5: Atualizar | Ctrl+F: Pesquisar",
                                    font=ctk.CTkFont(family="Segoe UI", size=11),
                                    text_color="gray40")
        atalhos_label.pack(expand=True)

    def criar_lista_automacoes_moderna(self, parent):
        """Cria lista moderna de automações"""
        # Frame principal da lista
        lista_frame = ctk.CTkFrame(parent, corner_radius=8)
        lista_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Título da seção
        titulo_lista = ctk.CTkLabel(lista_frame,
                                   text="Automações Disponíveis",
                                   font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                                   text_color=self.cores['primary'])
        titulo_lista.pack(pady=(20, 10), padx=20, anchor='w')
        
        # Campo de pesquisa simples
        pesquisa_frame = ctk.CTkFrame(lista_frame, fg_color="transparent")
        pesquisa_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        # Tentar diferentes configurações para o placeholder
        try:
            # Forçar modo claro e criar o campo
            ctk.set_appearance_mode("light")
            self.campo_pesquisa = ctk.CTkEntry(pesquisa_frame,
                                              placeholder_text="🔍 Pesquisar automações...",
                                              font=ctk.CTkFont(family="Segoe UI", size=12),
                                              height=32,
                                              corner_radius=6,
                                              border_width=1,
                                              border_color="gray60",
                                              fg_color="white",
                                              text_color="black",
                                              placeholder_text_color="gray50")
        except:
            # Fallback sem placeholder se houver erro
            self.campo_pesquisa = ctk.CTkEntry(pesquisa_frame,
                                              font=ctk.CTkFont(family="Segoe UI", size=12),
                                              height=32,
                                              corner_radius=6,
                                              border_width=1,
                                              border_color="gray60",
                                              fg_color="white",
                                              text_color="black")
        self.campo_pesquisa.pack(fill='x')
        self.campo_pesquisa.bind('<KeyRelease>', self.filtrar_automacoes)
        
        # Se não houver placeholder, adicionar hint ao lado
        if not hasattr(self.campo_pesquisa, 'placeholder_text') or not self.campo_pesquisa.cget('placeholder_text'):
            hint_label = ctk.CTkLabel(pesquisa_frame,
                                     text="Digite para pesquisar...",
                                     font=ctk.CTkFont(family="Segoe UI", size=10),
                                     text_color="gray50")
            hint_label.pack(anchor='w', pady=(2, 0))

        # Scrollable frame para as automações
        self.scroll_frame = ctk.CTkScrollableFrame(lista_frame, 
                                                  corner_radius=6,
                                                  scrollbar_button_color="gray70",
                                                  scrollbar_button_hover_color="gray60")
        self.scroll_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

    def criar_painel_detalhes_moderno(self, parent):
        """Cria painel de detalhes moderno"""
        # Frame principal do painel
        detalhes_frame = ctk.CTkFrame(parent, corner_radius=8)
        detalhes_frame.grid(row=0, column=1, sticky="nsew")

        # === SEÇÃO DE DETALHES ===
        detalhes_section = ctk.CTkFrame(detalhes_frame, corner_radius=6)
        detalhes_section.pack(fill='x', padx=20, pady=(20, 10))

        # Título
        titulo_detalhes = ctk.CTkLabel(detalhes_section,
                                      text="Detalhes da Execução",
                                      font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                                      text_color=self.cores['primary'])
        titulo_detalhes.pack(pady=(15, 10), padx=20, anchor='w')

        # Nome da automação selecionada
        self.automacao_selecionada_label = ctk.CTkLabel(detalhes_section,
                                                       text="Nenhuma automação selecionada",
                                                       font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                                                       text_color="gray60")
        self.automacao_selecionada_label.pack(pady=(0, 8), padx=20)

        # Última execução
        self.ultima_exec_label = ctk.CTkLabel(detalhes_section,
                                             text="",
                                             font=ctk.CTkFont(family="Segoe UI", size=12),
                                             text_color="gray50")
        self.ultima_exec_label.pack(pady=(0, 20), padx=20)

        # === BOTÕES DE AÇÃO ===
        botoes_frame = ctk.CTkFrame(detalhes_section, fg_color="transparent")
        botoes_frame.pack(pady=(0, 20))

        # Botão principal de execução
        self.btn_executar_principal = ctk.CTkButton(botoes_frame,
                                                   text="▶  Executar Automação",
                                                   command=self.executar_automacao,
                                                   width=250,
                                                   height=36,
                                                   font=ctk.CTkFont(size=12, weight="bold"),
                                                   fg_color=self.cores['accent'],
                                                   hover_color=self.cores['accent_hover'],
                                                   corner_radius=6,
                                                   state="disabled")
        self.btn_executar_principal.pack(pady=(0, 10))

        # Botão de abrir pasta
        self.btn_abrir_pasta_selecionada = ctk.CTkButton(botoes_frame,
                                                        text="📁  Abrir Pasta",
                                                        command=self.abrir_pasta_especifica,
                                                        width=250,
                                                        height=32,
                                                        font=ctk.CTkFont(size=12),
                                                        fg_color="gray60",
                                                        hover_color="gray50",
                                                        text_color="gray90",
                                                        border_width=0,
                                                        border_color="gray60",
                                                        corner_radius=6,
                                                        state="disabled")
        self.btn_abrir_pasta_selecionada.pack()

        # === SEÇÃO DE MENSAGENS ===
        mensagens_section = ctk.CTkFrame(detalhes_frame, corner_radius=6)
        mensagens_section.pack(fill='both', expand=True, padx=20, pady=(10, 20))

        # Título
        titulo_mensagens = ctk.CTkLabel(mensagens_section,
                                       text="Mensagens do Sistema",
                                       font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                                       text_color=self.cores['primary'])
        titulo_mensagens.pack(pady=(15, 10), padx=20, anchor='w')

        # Scrollable frame para mensagens
        self.mensagens_scroll = ctk.CTkScrollableFrame(mensagens_section,
                                                      corner_radius=6,
                                                      height=200)
        self.mensagens_scroll.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # Adicionar mensagem inicial
        self.adicionar_mensagem_usuario("Sistema iniciado e pronto para uso", tipo='info')

    def criar_card_automacao(self, nome, descricao="", status="Pronto"):
        """Cria um card moderno para automação"""
        # Frame principal do card com gradiente sutil
        card_frame = ctk.CTkFrame(self.scroll_frame, 
                                 corner_radius=8,
                                 fg_color="white",
                                 border_width=1,
                                 border_color="gray70")
        card_frame.pack(fill='x', pady=6, padx=8)

        # Container interno com padding maior
        content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        content_frame.pack(fill='both', expand=True, padx=16, pady=12)

        # Container horizontal principal
        main_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        main_container.pack(fill='x')

        # Container para nome e status (agora sem ícone)
        info_container = ctk.CTkFrame(main_container, fg_color="transparent")
        info_container.pack(side='left', fill='x', expand=True)

        # Nome da automação com fonte maior
        nome_label = ctk.CTkLabel(info_container,
                                 text=nome,
                                 font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                                 text_color="gray10",
                                 anchor='w')
        nome_label.pack(anchor='w', pady=(0, 2))

        # Status com melhor estilização
        status_label = ctk.CTkLabel(info_container,
                                   text=f"• {status}",
                                   font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
                                   text_color="gray50",
                                   anchor='w')
        status_label.pack(anchor='w')

        # Indicador visual do lado direito
        indicator = ctk.CTkFrame(main_container,
                                width=3,
                                height=30,
                                corner_radius=1,
                                fg_color=self.obter_cor_status(status))
        indicator.pack(side='right', padx=(8, 0))

        # Efeito hover e clique
        def on_click(event=None):
            self.selecionar_automacao(nome)

        # Bind de clique para todos os elementos
        for widget in [card_frame, content_frame, main_container, info_container, nome_label, status_label]:
            widget.bind("<Button-1>", on_click)
            widget.configure(cursor="hand2")

        # Efeito hover melhorado
        def on_enter(event):
            if self.automacao_selecionada_atual != nome:
                card_frame.configure(fg_color="gray95",
                                   border_color="gray60")

        def on_leave(event):
            if self.automacao_selecionada_atual != nome:
                card_frame.configure(fg_color="white",
                                   border_color="gray70")

        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)

        # Armazenar referências
        automacao_info = {
            'nome': nome,
            'descricao': descricao,
            'card_frame': card_frame,
            'status_label': status_label,
            'indicator': indicator,
            'status_original': status
        }
        
        self.automacoes_encontradas.append(automacao_info)
        self.automacoes_filtradas.append(automacao_info)
        return card_frame

    def adicionar_mensagem_usuario(self, mensagem, tipo='info'):
        """Adiciona mensagem ao painel de mensagens"""
        # Cores por tipo
        cores_tipo = {
            'info': "gray40",
            'success': self.cores['success'],
            'error': self.cores['danger'],
            'warning': self.cores['warning']
        }

        # Ícones por tipo
        icones_tipo = {
            'info': 'ℹ️',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️'
        }

        # Frame da mensagem
        msg_frame = ctk.CTkFrame(self.mensagens_scroll, 
                                corner_radius=8,
                                fg_color="gray90")
        msg_frame.pack(fill='x', pady=3, padx=5)

        # Container interno
        msg_content = ctk.CTkFrame(msg_frame, fg_color="transparent")
        msg_content.pack(fill='x', padx=10, pady=8)

        # Timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        # Label com ícone, timestamp e mensagem
        msg_text = f"{icones_tipo.get(tipo, '•')} {timestamp} - {mensagem}"
        msg_label = ctk.CTkLabel(msg_content,
                                text=msg_text,
                                font=ctk.CTkFont(family="Segoe UI", size=11),
                                text_color=cores_tipo.get(tipo, "gray40"),
                                anchor='w')
        msg_label.pack(fill='x')

        # Adicionar à lista
        self.mensagens_usuario.append(msg_frame)

        # Remover mensagens antigas
        if len(self.mensagens_usuario) > self.max_mensagens_usuario:
            old_msg = self.mensagens_usuario.pop(0)
            old_msg.destroy()

        # Auto-scroll para a mensagem mais recente
        self.mensagens_scroll._parent_canvas.yview_moveto(1.0)

    def selecionar_automacao(self, nome):
        """Seleciona uma automação"""
        if self.automacao_selecionada_atual == nome:
            return

        # Remover seleção anterior
        if self.automacao_selecionada_atual:
            for auto in self.automacoes_encontradas:
                if auto['nome'] == self.automacao_selecionada_atual:
                    auto['card_frame'].configure(fg_color="white",
                                               border_color="gray70",
                                               border_width=1)
                    # Restaurar cor original do indicador baseada no status
                    auto['indicator'].configure(fg_color=self.obter_cor_status(auto['status_original']))
                    break

        # Aplicar nova seleção
        for auto in self.automacoes_encontradas:
            if auto['nome'] == nome:
                auto['card_frame'].configure(fg_color="lightblue",
                                           border_color=self.cores['accent'],
                                           border_width=2)
                # Alterar cor do indicador para azul quando selecionado
                auto['indicator'].configure(fg_color=self.cores['accent'])
                break

        # Atualizar seleção atual
        self.automacao_selecionada_atual = nome

        # Atualizar detalhes
        self.automacao_selecionada_label.configure(
            text=nome,
            text_color="gray10"
        )

        # Buscar última execução
        ultima_exec = self.obter_ultima_execucao(nome)
        self.ultima_exec_label.configure(text=f"Última execução: {ultima_exec}")

        # Habilitar botões se não há processo ativo
        automacao = next((a for a in self.automacoes_encontradas if a['nome'] == nome), None)
        if automacao and automacao['nome'] not in self.processos_ativos:
            self.btn_executar_principal.configure(state='normal')
        else:
            self.btn_executar_principal.configure(state='disabled')

        self.btn_abrir_pasta_selecionada.configure(state='normal')

        # Feedback
        self.adicionar_mensagem_usuario(f"Automação '{nome}' selecionada", tipo='info')

    def obter_icone_status(self, status):
        """Retorna ícone baseado no status"""
        icones = {
            'Pronto': '🟢',  # Círculo verde
            'Executando': '🔄',  # Símbolo de atualização
            'Concluído': '✓',  # Check mark simples
            'Erro': '⚠',  # Triângulo de aviso
            'Atualizado': '✓',  # Check mark simples
            'Interrompido': '⏸'  # Pause
        }
        return icones.get(status, '🟢')

    def obter_cor_status(self, status):
        """Retorna cor baseada no status"""
        cores = {
            'Pronto': "gray60",
            'Executando': self.cores['executing'],
            'Concluído': self.cores['success'],
            'Erro': self.cores['danger'],
            'Atualizado': self.cores['success'],
            'Interrompido': "gray50"
        }
        return cores.get(status, "gray60")

    # === MÉTODOS FUNCIONAIS (mantidos do código original) ===
    
    def carregar_automacoes(self):
        """Carrega a lista de automações"""
        self.log_interno.append(f"[{datetime.datetime.now()}] Carregando automações...")

        # Limpar lista atual
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.automacoes_encontradas.clear()
        self.automacoes_filtradas.clear()
        self.automacao_selecionada_atual = None
        self.campo_pesquisa.delete(0, 'end')

        try:
            # Recarregar automações do manager
            self.automacao_manager.recarregar_automacoes()
            
            # Obter lista de automações disponíveis (filtrando tokens)
            self.automacoes_disponiveis = self.automacao_manager.listar_automacoes(filtrar_token=True)
            
            for automacao_meta in self.automacoes_disponiveis:
                nome = automacao_meta['nome']
                descricao = automacao_meta['descricao']
                self.criar_card_automacao(nome, descricao)

            total_automacoes = len(self.automacoes_disponiveis)
            self.contador_automacoes.configure(text=f"{total_automacoes} automações disponíveis")
            self.log_interno.append(f"[{datetime.datetime.now()}] Encontradas {total_automacoes} automações")
            self.adicionar_mensagem_usuario(f"{total_automacoes} automações carregadas", tipo='success')

        except Exception as e:
            self.log_interno.append(f"[{datetime.datetime.now()}] Erro ao carregar automações: {str(e)}")
            self.adicionar_mensagem_usuario("Erro ao carregar automações", tipo='error')

    def executar_automacao(self):
        """Executa a automação selecionada"""
        nome = self.automacao_selecionada_label.cget('text')
        if nome == "Nenhuma automação selecionada":
            return

        automacao = next((a for a in self.automacoes_encontradas if a['nome'] == nome), None)
        if not automacao:
            return

        # Verificar se automação existe no manager
        if not self.automacao_manager.obter_automacao(nome):
            self.adicionar_mensagem_usuario(f"Automação não encontrada: {nome}", tipo='error')
            messagebox.showerror("Erro", f"Automação não encontrada: {nome}")
            return

        self.btn_executar_principal.configure(state='disabled')
        thread = threading.Thread(target=self.executar_processo_modular, args=(nome,))
        thread.daemon = True
        thread.start()

    def executar_renovar_token(self):
        """Executa renovar token usando a versão simplificada"""
        try:
            self.adicionar_mensagem_usuario("🔑 Iniciando renovação de token...", tipo='info')
            thread = threading.Thread(target=self.executar_token_simplificado)
            thread.daemon = True
            thread.start()
                
        except Exception as e:
            self.log_interno.append(f"[{datetime.datetime.now()}] Erro ao executar Renovar Token: {str(e)}")
            self.adicionar_mensagem_usuario("❌ Erro ao executar Renovar Token", tipo='error')

    def executar_token_simplificado(self):
        """Executa renovar_token_simplified.py diretamente"""
        nome_automacao = "renovar_token_simplificado"
        execucao_id = None
        
        try:
            self.log_interno.append(f"[{datetime.datetime.now()}] Iniciando execução de token simplificado")
            
            # Registrar início da execução no banco
            execucao_id = self.db_manager.registrar_inicio_execucao(nome_automacao)
            
            # Importar e executar o módulo diretamente
            import importlib.util
            base_path = self.path_manager.get_path('base')
            if base_path is None:
                raise ValueError("Caminho base não encontrado")
            
            spec = importlib.util.spec_from_file_location(
                "renovar_token_simplified", 
                base_path / "renovar_token_simplified.py"
            )
            if spec is None or spec.loader is None:
                raise ValueError("Não foi possível carregar o módulo renovar_token_simplified")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Buscar a classe e executar
            extractor_class = getattr(module, 'HubXPTokenExtractorSimplified')
            extractor = extractor_class()
            
            # Executar
            resultado = extractor.run(headless=True)
            
            # Processar resultado
            if resultado and isinstance(resultado, dict) and resultado.get('success', False):
                mensagem_sucesso = resultado.get('message', 'Token renovado com sucesso')
                self.root.after(0, lambda msg=mensagem_sucesso: self.adicionar_mensagem_usuario(f"✅ {msg}", tipo='success'))
                
                # Registrar sucesso no banco
                if execucao_id:
                    self.db_manager.registrar_fim_execucao(
                        execucao_id, 'CONCLUIDO', dados_resultado=resultado
                    )
            else:
                mensagem_erro = resultado.get('message', 'Erro na renovação do token') if resultado else 'Falha na execução'
                self.root.after(0, lambda msg=mensagem_erro: self.adicionar_mensagem_usuario(f"❌ {msg}", tipo='error'))
                
                # Registrar erro no banco
                if execucao_id:
                    self.db_manager.registrar_fim_execucao(
                        execucao_id, 'ERRO', mensagem_erro=mensagem_erro
                    )
                
        except Exception as e:
            self.log_interno.append(f"[{datetime.datetime.now()}] Erro durante execução de token: {str(e)}")
            self.root.after(0, lambda: self.adicionar_mensagem_usuario(f"❌ Erro inesperado na renovação de token: {str(e)}", tipo='error'))
            
            # Registrar erro no banco
            if execucao_id:
                try:
                    self.db_manager.registrar_fim_execucao(
                        execucao_id, 'ERRO', mensagem_erro=str(e)
                    )
                except:
                    pass

    def executar_processo_modular(self, nome_automacao):
        """Executa processo usando AutomacaoManager"""
        try:
            self.log_interno.append(f"[{datetime.datetime.now()}] Iniciando execução modular: {nome_automacao}")
            self.root.after(0, lambda: self.adicionar_mensagem_usuario(f"Iniciando {nome_automacao}...", tipo='info'))
            self.root.after(0, lambda: self.atualizar_status_automacao(nome_automacao, "Executando", 'warning'))
            self.root.after(0, self.atualizar_contador_processos)

            self.processos_ativos[nome_automacao] = True
            
            # Executar via AutomacaoManager
            resultado = self.automacao_manager.executar_automacao(nome_automacao)
            
            if nome_automacao in self.processos_ativos:
                del self.processos_ativos[nome_automacao]
            
            # Verificar resultado
            if resultado and isinstance(resultado, dict) and resultado.get('success', False):
                mensagem_sucesso = resultado.get('message', f"{nome_automacao} concluído com sucesso")
                self.root.after(0, lambda msg=mensagem_sucesso: self.adicionar_mensagem_usuario(f"✅ {msg}", tipo='success'))
                self.root.after(0, lambda nome=nome_automacao: self.atualizar_status_automacao(nome, "Concluído", 'success'))
            elif resultado and isinstance(resultado, dict) and not resultado.get('success', True):
                mensagem_erro = resultado.get('message', 'Erro na execução')
                self.root.after(0, lambda msg=mensagem_erro: self.adicionar_mensagem_usuario(f"❌ {msg}", tipo='error'))
                self.root.after(0, lambda nome=nome_automacao: self.atualizar_status_automacao(nome, "Erro", 'error'))
            else:
                # Para automações que não retornam estrutura de sucesso/falha padrão
                self.root.after(0, lambda nome=nome_automacao: self.adicionar_mensagem_usuario(f"✅ {nome} executado", tipo='success'))
                self.root.after(0, lambda nome=nome_automacao: self.atualizar_status_automacao(nome, "Concluído", 'success'))

        except Exception as e:
            self.log_interno.append(f"[{datetime.datetime.now()}] Erro durante execução modular de {nome_automacao}: {str(e)}")
            self.root.after(0, lambda nome=nome_automacao: self.adicionar_mensagem_usuario(f"❌ Erro inesperado em {nome}", tipo='error'))
            self.root.after(0, lambda nome=nome_automacao: self.atualizar_status_automacao(nome, "Erro", 'error'))
            
            if nome_automacao in self.processos_ativos:
                del self.processos_ativos[nome_automacao]

        finally:
            nome_selecionado = self.automacao_selecionada_label.cget('text')
            if nome_automacao == nome_selecionado:
                self.root.after(0, lambda: self.btn_executar_principal.configure(state='normal'))
            self.root.after(0, self.atualizar_contador_processos)

    def abrir_pasta_especifica(self):
        """Abre a pasta específica da automação selecionada"""
        if self.automacao_selecionada_atual:
            self.automacao_config.abrir_pasta_automacao(
                self.automacao_selecionada_atual,
                log_callback=lambda msg: self.adicionar_mensagem_usuario(msg, tipo='info')
            )


    def atualizar_status_automacao(self, nome, status, tipo='info'):
        """Atualiza o status visual de uma automação"""
        automacao = next((a for a in self.automacoes_encontradas if a['nome'] == nome), None)
        if automacao:
            # Atualizar texto do status
            automacao['status_label'].configure(
                text=f"• {status}"
            )
            
            nova_cor = self.obter_cor_status(status)
            
            # Sempre atualizar indicador
            automacao['indicator'].configure(fg_color=nova_cor)
            
            # Mudar borda do card durante execução
            if status == 'Executando':
                automacao['card_frame'].configure(
                    border_color=self.cores['executing'],
                    border_width=2
                )
            elif self.automacao_selecionada_atual == nome:
                # Manter borda azul se selecionado
                automacao['card_frame'].configure(
                    border_color=self.cores['accent'],
                    border_width=2
                )
            else:
                # Restaurar borda normal
                automacao['card_frame'].configure(
                    border_color="gray70",
                    border_width=1
                )
            
            automacao['status_original'] = status

    def atualizar_contador_processos(self):
        """Atualiza o contador de processos ativos"""
        count = len(self.processos_ativos)
        
        if count > 0:
            self.status_geral.configure(
                text=f"● {count} processo{'s' if count != 1 else ''} em execução",
                text_color=self.cores['warning']
            )
        else:
            self.status_geral.configure(
                text="● Sistema Operacional",
                text_color=self.cores['success']
            )

    def exportar_logs_completos(self):
        """Exporta logs completos para arquivo"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.logs_dir / f"log_completo_{timestamp}.txt"

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("=== LOG COMPLETO DO SISTEMA ===\n\n")
                for linha in self.log_interno:
                    f.write(f"{linha}\n")

            self.adicionar_mensagem_usuario("Logs exportados com sucesso", tipo='success')
            messagebox.showinfo("Sucesso", f"Logs salvos em:\n{log_file}")

        except Exception as e:
            self.adicionar_mensagem_usuario("Erro ao exportar logs", tipo='error')

    def obter_ultima_execucao(self, nome_automacao):
        """Obtém a data da última execução"""
        try:
            # Primeiro tentar obter do banco de dados
            ultima_exec = self.automacao_manager.obter_ultima_execucao(nome_automacao)
            if ultima_exec:
                data_exec = ultima_exec['inicio']
                status = ultima_exec['status']
                return f"{data_exec.strftime('%d/%m/%Y %H:%M:%S')} ({status})"
            
            # Fallback para arquivo JSON (compatibilidade)
            if self.config_file is not None and self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    historico = config.get('historico_execucoes', {})
                    return historico.get(nome_automacao, {}).get('ultima_execucao', 'Nunca executado')
        except Exception as e:
            self.log_interno.append(f"[{datetime.datetime.now()}] Erro ao obter última execução: {str(e)}")
        return 'Nunca executado'

    def salvar_historico_execucao(self, nome_automacao, status, timestamp):
        """Salva o histórico de execução"""
        try:
            config = {}
            if self.config_file is not None and self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            if 'historico_execucoes' not in config:
                config['historico_execucoes'] = {}

            config['historico_execucoes'][nome_automacao] = {
                'ultima_execucao': timestamp,
                'status': status
            }

            if self.config_file is not None:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.log_interno.append(f"[{datetime.datetime.now()}] Erro ao salvar histórico: {str(e)}")

    def carregar_configuracoes(self):
        """Carrega configurações salvas"""
        try:
            if self.config_file is not None and self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.log_interno.append(f"[{datetime.datetime.now()}] Configurações carregadas")
        except Exception as e:
            self.log_interno.append(f"[{datetime.datetime.now()}] Erro ao carregar configurações: {str(e)}")

    def filtrar_automacoes(self, event=None):
        """Filtra as automações baseado no texto de pesquisa"""
        termo_pesquisa = self.campo_pesquisa.get().lower().strip()
        
        # Limpar cards atuais
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # Resetar lista filtrada
        self.automacoes_filtradas.clear()
        
        # Filtrar e recriar cards
        for automacao in self.automacoes_encontradas:
            nome_lower = automacao['nome'].lower()
            if not termo_pesquisa or termo_pesquisa in nome_lower:
                # Recriar o card
                self.recriar_card_automacao(automacao)
                self.automacoes_filtradas.append(automacao)
        
        # Atualizar contador
        total_encontradas = len(self.automacoes_encontradas)
        total_filtradas = len(self.automacoes_filtradas)
        
        if termo_pesquisa:
            self.contador_automacoes.configure(
                text=f"{total_filtradas} de {total_encontradas} automações"
            )
        else:
            self.contador_automacoes.configure(
                text=f"{total_encontradas} automações disponíveis"
            )
    
    def recriar_card_automacao(self, automacao_info):
        """Recria um card de automação baseado nas informações existentes"""
        nome = automacao_info['nome']
        status = automacao_info['status_original']
        
        # Frame principal do card
        card_frame = ctk.CTkFrame(self.scroll_frame, 
                                 corner_radius=8,
                                 fg_color="white",
                                 border_width=1,
                                 border_color="gray70")
        card_frame.pack(fill='x', pady=6, padx=8)

        # Container interno
        content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        content_frame.pack(fill='both', expand=True, padx=16, pady=12)

        # Container horizontal principal
        main_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        main_container.pack(fill='x')

        # Container para nome e status
        info_container = ctk.CTkFrame(main_container, fg_color="transparent")
        info_container.pack(side='left', fill='x', expand=True)

        # Nome da automação
        nome_label = ctk.CTkLabel(info_container,
                                 text=nome,
                                 font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                                 text_color="gray10",
                                 anchor='w')
        nome_label.pack(anchor='w', pady=(0, 2))

        # Status
        status_label = ctk.CTkLabel(info_container,
                                   text=f"• {status}",
                                   font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
                                   text_color="gray50",
                                   anchor='w')
        status_label.pack(anchor='w')

        # Indicador visual do lado direito
        indicator = ctk.CTkFrame(main_container,
                                width=3,
                                height=30,
                                corner_radius=1,
                                fg_color=self.obter_cor_status(status))
        indicator.pack(side='right', padx=(8, 0))

        # Efeito hover e clique
        def on_click(event=None):
            self.selecionar_automacao(nome)

        # Bind de clique para todos os elementos
        for widget in [card_frame, content_frame, main_container, info_container, nome_label, status_label]:
            widget.bind("<Button-1>", on_click)
            widget.configure(cursor="hand2")

        # Efeito hover melhorado
        def on_enter(event):
            if self.automacao_selecionada_atual != nome:
                card_frame.configure(fg_color="gray95",
                                   border_color="gray60")

        def on_leave(event):
            if self.automacao_selecionada_atual != nome:
                card_frame.configure(fg_color="white",
                                   border_color="gray70")

        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)

        # Atualizar referências
        automacao_info['card_frame'] = card_frame
        automacao_info['status_label'] = status_label
        automacao_info['indicator'] = indicator
        
        # Aplicar seleção se necessário
        if self.automacao_selecionada_atual == nome:
            card_frame.configure(fg_color="lightblue",
                               border_color=self.cores['accent'],
                               border_width=2)
            indicator.configure(fg_color=self.cores['accent'])

    def adicionar_atalhos_modernos(self):
        """Adiciona atalhos de teclado modernos"""
        self.root.bind('<Return>', lambda e: self.executar_automacao())
        self.root.bind('<Control-t>', lambda e: self.executar_renovar_token())
        self.root.bind('<F5>', lambda e: self.carregar_automacoes())
        self.root.bind('<Control-r>', lambda e: self.carregar_automacoes())
        self.root.bind('<Control-l>', lambda e: self.exportar_logs_completos())
        self.root.bind('<Control-o>', lambda e: self.abrir_pasta_especifica())
        self.root.bind('<Control-f>', lambda e: self.campo_pesquisa.focus())
        self.root.bind('<Escape>', lambda e: self.root.quit() if messagebox.askyesno("Sair", "Deseja sair do programa?") else None)

    def configurar_responsividade_moderna(self):
        """Configura responsividade da janela"""
        self.root.minsize(1000, 600)
        
        largura = 1200
        altura = 700
        
        x = (self.root.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.root.winfo_screenheight() // 2) - (altura // 2)
        
        self.root.geometry(f'{largura}x{altura}+{x}+{y}')

    def ao_fechar(self):
        """Salva logs e fecha a aplicação"""
        try:
            if self.log_interno:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = self.logs_dir / f"sessao_{timestamp}.log"

                with open(log_file, 'w', encoding='utf-8') as f:
                    for linha in self.log_interno:
                        f.write(f"{linha}\n")

        except Exception as e:
            print(f"Erro ao salvar log de sessão: {e}")

        finally:
            self.root.destroy()

    def executar(self):
        """Inicia a aplicação"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MenuAutomacoes()
    app.executar()
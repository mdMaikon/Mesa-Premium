"""
UI Manager
Gerencia criação e atualização da interface do usuário
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from ui_config import UIColors, UIConstants, UIConfig
from message_manager import MessageManager

class AutomationCard:
    """Representa um card de automação"""
    
    def __init__(self, name: str, description: str, status: str = "Pronto"):
        self.name = name
        self.description = description
        self.status = status
        self.status_original = status
        
        # Componentes UI
        self.card_frame: Optional[ctk.CTkFrame] = None
        self.status_label: Optional[ctk.CTkLabel] = None
        self.indicator: Optional[ctk.CTkFrame] = None

class UIManager:
    """Gerenciador da interface do usuário"""
    
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.setup_window()
        
        # Componentes principais
        self.container: Optional[ctk.CTkFrame] = None
        self.scroll_frame: Optional[ctk.CTkScrollableFrame] = None
        self.messages_scroll: Optional[ctk.CTkScrollableFrame] = None
        
        # Labels de informação
        self.automation_selected_label: Optional[ctk.CTkLabel] = None
        self.last_execution_label: Optional[ctk.CTkLabel] = None
        self.status_general: Optional[ctk.CTkLabel] = None
        self.automation_counter: Optional[ctk.CTkLabel] = None
        
        # Botões
        self.btn_execute_main: Optional[ctk.CTkButton] = None
        self.btn_open_folder: Optional[ctk.CTkButton] = None
        self.btn_update: Optional[ctk.CTkButton] = None
        self.btn_logs: Optional[ctk.CTkButton] = None
        self.btn_token: Optional[ctk.CTkButton] = None
        
        # Controle do spinner do token
        self.token_spinner_active: bool = False
        self.token_spinner_frame: int = 0
        self.token_original_text: str = "🔑 Renovar Token"
        
        # Gerenciamento de cards
        self.automation_cards: List[AutomationCard] = []
        self.filtered_cards: List[AutomationCard] = []
        self.selected_automation: Optional[str] = None
        
        # Message Manager
        self.message_manager: Optional[MessageManager] = None
        
        # Callbacks
        self.callbacks: Dict[str, Callable] = {}
    
    def setup_window(self):
        """Configura janela principal"""
        self.root.title(UIConstants.WINDOW_TITLE)
        self.root.minsize(UIConstants.MIN_WIDTH, UIConstants.MIN_HEIGHT)
        
        # Centralizar janela
        width = UIConstants.DEFAULT_WIDTH
        height = UIConstants.DEFAULT_HEIGHT
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Configurar ícone se disponível
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
    
    def create_interface(self):
        """Cria interface completa"""
        # Container principal
        self.container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.container.pack(fill='both', expand=True, padx=UIConstants.PADDING_MAIN, pady=UIConstants.PADDING_MAIN)
        
        # Header
        self._create_header()
        
        # Área principal (2 colunas)
        main_container = ctk.CTkFrame(self.container, fg_color="transparent")
        main_container.pack(fill='both', expand=True, pady=(UIConstants.PADDING_MAIN, 0))
        
        # Configurar grid
        main_container.grid_columnconfigure(0, weight=2)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        
        # Coluna esquerda - Lista de automações
        self._create_automation_list(main_container)
        
        # Coluna direita - Detalhes e status
        self._create_details_panel(main_container)
        
        # Configurar message manager
        if self.messages_scroll:
            self.message_manager = MessageManager(self.messages_scroll)
            self.message_manager.add_message("Sistema iniciado e pronto para uso", 'info')
    
    def _create_header(self):
        """Cria header moderno"""
        header = ctk.CTkFrame(self.container, fg_color="transparent", height=140)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Linha superior
        top_row = ctk.CTkFrame(header, fg_color="transparent")
        top_row.pack(fill='x', pady=(0, UIConstants.PADDING_SECTION))
        
        # Logo/Título à esquerda
        title_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        title_frame.pack(side='left', fill='y')
        
        title = ctk.CTkLabel(
            title_frame,
            text="Mesa Premium",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_TITLE, "bold"),
            text_color=UIColors.PRIMARY
        )
        title.pack(anchor='w')
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="Menu de Automações • Central de Processos",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_SUBTITLE),
            text_color="gray50"
        )
        subtitle.pack(anchor='w')
        
        # Status à direita
        right_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        right_frame.pack(side='right', fill='y')
        
        self.status_general = ctk.CTkLabel(
            right_frame,
            text="● Sistema Operacional",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_SUBTITLE),
            text_color=UIColors.SUCCESS
        )
        self.status_general.pack(anchor='e', pady=(10, 5))
        
        self.automation_counter = ctk.CTkLabel(
            right_frame,
            text="0 automações disponíveis",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_SMALL),
            text_color="gray60"
        )
        self.automation_counter.pack(anchor='e')
        
        # Toolbar
        self._create_toolbar(header)
    
    def _create_toolbar(self, parent):
        """Cria toolbar com botões"""
        toolbar = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        # Container para botões à esquerda
        buttons_container = ctk.CTkFrame(toolbar, fg_color="transparent")
        buttons_container.pack(side='left', pady=5)
        
        # Botão atualizar
        self.btn_update = ctk.CTkButton(
            buttons_container,
            text="🔄 Atualizar",
            width=120,
            **UIConfig.get_button_style("secondary")
        )
        self.btn_update.pack(side='left', padx=(0, 10))
        
        # Botão logs
        self.btn_logs = ctk.CTkButton(
            buttons_container,
            text="💾 Exportar Logs",
            width=140,
            **UIConfig.get_button_style("secondary")
        )
        self.btn_logs.pack(side='left', padx=(0, 10))
        
        # Botão token
        self.btn_token = ctk.CTkButton(
            buttons_container,
            text="🔑 Renovar Token",
            width=130,
            **UIConfig.get_button_style("info")
        )
        self.btn_token.pack(side='left')
        
        # Info de atalhos à direita
        shortcuts_container = ctk.CTkFrame(toolbar, fg_color="transparent")
        shortcuts_container.pack(side='right', fill='y')
        
        shortcuts_label = ctk.CTkLabel(
            shortcuts_container,
            text="Enter: Executar | Ctrl+T: Token | F5: Atualizar",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_SMALL),
            text_color="gray40"
        )
        shortcuts_label.pack(expand=True)
    
    def _create_automation_list(self, parent):
        """Cria lista de automações"""
        list_frame = ctk.CTkFrame(parent, **UIConfig.get_frame_style("card"))
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Título da seção
        title_list = ctk.CTkLabel(
            list_frame,
            text="Automações Disponíveis",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_SECTION, "bold"),
            text_color=UIColors.PRIMARY
        )
        title_list.pack(pady=(UIConstants.PADDING_MAIN, 10), padx=UIConstants.PADDING_MAIN, anchor='w')
        
        
        # Scrollable frame para as automações
        self.scroll_frame = ctk.CTkScrollableFrame(
            list_frame,
            corner_radius=UIConstants.CORNER_RADIUS_SMALL,
            scrollbar_button_color="gray70",
            scrollbar_button_hover_color="gray60"
        )
        self.scroll_frame.pack(fill='both', expand=True, padx=UIConstants.PADDING_MAIN, pady=(0, UIConstants.PADDING_MAIN))
    
    def _create_details_panel(self, parent):
        """Cria painel de detalhes"""
        details_frame = ctk.CTkFrame(parent, **UIConfig.get_frame_style("card"))
        details_frame.grid(row=0, column=1, sticky="nsew")
        
        # Seção de detalhes (altura fixa para consistência)
        details_section = ctk.CTkFrame(details_frame, **UIConfig.get_frame_style("section"))
        details_section.pack(fill='x', padx=UIConstants.PADDING_MAIN, pady=(UIConstants.PADDING_MAIN, 10))
        details_section.pack_propagate(False)  # Impede redimensionamento automático
        details_section.configure(height=UIConstants.DETAILS_SECTION_HEIGHT)  # Altura fixa
        
        # Título
        title_details = ctk.CTkLabel(
            details_section,
            text="Detalhes da Execução",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_NORMAL, "bold"),
            text_color=UIColors.PRIMARY
        )
        title_details.pack(pady=(UIConstants.PADDING_SECTION, 10), padx=UIConstants.PADDING_MAIN, anchor='w')
        
        # Nome da automação selecionada
        self.automation_selected_label = ctk.CTkLabel(
            details_section,
            text="Nenhuma automação selecionada",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_NORMAL, "bold"),
            text_color="gray60"
        )
        self.automation_selected_label.pack(pady=(0, 8), padx=UIConstants.PADDING_MAIN)
        
        # Última execução
        self.last_execution_label = ctk.CTkLabel(
            details_section,
            text="",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_SUBTITLE),
            text_color="gray50"
        )
        self.last_execution_label.pack(pady=(0, UIConstants.PADDING_MAIN), padx=UIConstants.PADDING_MAIN)
        
        # Botões de ação
        buttons_frame = ctk.CTkFrame(details_section, fg_color="transparent")
        buttons_frame.pack(pady=(0, UIConstants.PADDING_MAIN))
        
        # Botão principal de execução
        self.btn_execute_main = ctk.CTkButton(
            buttons_frame,
            text="▶  Executar Automação",
            width=250,
            state="disabled",
            **UIConfig.get_button_style("primary")
        )
        self.btn_execute_main.pack(pady=(0, 10))
        
        # Botão de abrir pasta
        self.btn_open_folder = ctk.CTkButton(
            buttons_frame,
            text="📁  Abrir Pasta",
            width=250,
            fg_color="gray60",
            hover_color="gray50",
            text_color="gray90",
            border_width=0,
            corner_radius=UIConstants.CORNER_RADIUS_BUTTON,
            height=UIConstants.BUTTON_HEIGHT_NORMAL,
            font=UIConfig.get_font(),
            state="disabled"
        )
        self.btn_open_folder.pack()
        
        # Seção de mensagens (preenche espaço restante)
        messages_section = ctk.CTkFrame(details_frame, **UIConfig.get_frame_style("section"))
        messages_section.pack(fill='both', expand=True, padx=UIConstants.PADDING_MAIN, pady=(10, UIConstants.PADDING_MAIN))
        
        # Título
        title_messages = ctk.CTkLabel(
            messages_section,
            text="Mensagens do Sistema",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_NORMAL, "bold"),
            text_color=UIColors.PRIMARY
        )
        title_messages.pack(pady=(UIConstants.PADDING_SECTION, 10), padx=UIConstants.PADDING_MAIN, anchor='w')
        
        # Scrollable frame para mensagens
        self.messages_scroll = ctk.CTkScrollableFrame(
            messages_section,
            corner_radius=UIConstants.CORNER_RADIUS_SMALL,
            height=200
        )
        self.messages_scroll.pack(fill='both', expand=True, padx=UIConstants.PADDING_MAIN, pady=(0, UIConstants.PADDING_MAIN))
    
    def create_automation_card(self, name: str, description: str = "", status: str = "Pronto") -> AutomationCard:
        """Cria um card de automação"""
        card = AutomationCard(name, description, status)
        
        # Frame principal do card
        card.card_frame = ctk.CTkFrame(
            self.scroll_frame,
            **UIConfig.get_frame_style("card")
        )
        card.card_frame.pack(fill='x', pady=6, padx=8)
        
        # Container interno
        content_frame = ctk.CTkFrame(card.card_frame, fg_color="transparent")
        content_frame.pack(fill='both', expand=True, padx=UIConstants.PADDING_CARD, pady=12)
        
        # Container horizontal principal
        main_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        main_container.pack(fill='x')
        
        # Container para nome e status
        info_container = ctk.CTkFrame(main_container, fg_color="transparent")
        info_container.pack(side='left', fill='x', expand=True)
        
        # Nome da automação
        name_label = ctk.CTkLabel(
            info_container,
            text=name,
            font=UIConfig.get_font(UIConstants.FONT_SIZE_NORMAL, "bold"),
            text_color="gray10",
            anchor='w'
        )
        name_label.pack(anchor='w', pady=(0, 2))
        
        # Status
        card.status_label = ctk.CTkLabel(
            info_container,
            text=f"• {status}",
            font=UIConfig.get_font(UIConstants.FONT_SIZE_SMALL),
            text_color="gray50",
            anchor='w'
        )
        card.status_label.pack(anchor='w')
        
        # Indicador visual
        card.indicator = ctk.CTkFrame(
            main_container,
            width=3,
            height=30,
            corner_radius=1,
            fg_color=UIColors.get_status_color(status)
        )
        card.indicator.pack(side='right', padx=(8, 0))
        
        # Eventos
        self._setup_card_events(card, name_label, card.status_label, content_frame, main_container, info_container)
        
        # Adicionar à lista
        self.automation_cards.append(card)
        self.filtered_cards.append(card)
        
        return card
    
    def _setup_card_events(self, card: AutomationCard, *widgets):
        """Configura eventos do card"""
        def on_click(event=None):
            if self.callbacks.get('select_automation'):
                self.callbacks['select_automation'](card.name)
        
        def on_enter(event):
            if self.selected_automation != card.name:
                card.card_frame.configure(fg_color="gray95", border_color="gray60")
        
        def on_leave(event):
            if self.selected_automation != card.name:
                card.card_frame.configure(fg_color="white", border_color="gray70")
        
        # Bind eventos para todos os widgets
        all_widgets = [card.card_frame] + list(widgets)
        for widget in all_widgets:
            widget.bind("<Button-1>", on_click)
            widget.configure(cursor="hand2")
        
        card.card_frame.bind("<Enter>", on_enter)
        card.card_frame.bind("<Leave>", on_leave)
    
    def set_callbacks(self, callbacks: Dict[str, Callable]):
        """Define callbacks para eventos da UI"""
        self.callbacks.update(callbacks)
        
        # Configurar callbacks dos botões
        if self.btn_execute_main and 'execute_automation' in callbacks:
            self.btn_execute_main.configure(command=callbacks['execute_automation'])
        
        if self.btn_token and 'execute_token' in callbacks:
            self.btn_token.configure(command=callbacks['execute_token'])
        
        if self.btn_update and 'update_automations' in callbacks:
            self.btn_update.configure(command=callbacks['update_automations'])
        
        if self.btn_logs and 'export_logs' in callbacks:
            self.btn_logs.configure(command=callbacks['export_logs'])
        
        if self.btn_open_folder and 'open_folder' in callbacks:
            self.btn_open_folder.configure(command=callbacks['open_folder'])
        
    
    def select_automation(self, name: str):
        """Seleciona uma automação"""
        if self.selected_automation == name:
            return
        
        # Remover seleção anterior
        if self.selected_automation:
            for card in self.automation_cards:
                if card.name == self.selected_automation:
                    card.card_frame.configure(fg_color="white", border_color="gray70", border_width=1)
                    card.indicator.configure(fg_color=UIColors.get_status_color(card.status_original))
                    break
        
        # Aplicar nova seleção
        for card in self.automation_cards:
            if card.name == name:
                card.card_frame.configure(fg_color="lightblue", border_color=UIColors.ACCENT, border_width=2)
                card.indicator.configure(fg_color=UIColors.ACCENT)
                break
        
        # Atualizar seleção atual
        self.selected_automation = name
        
        # Atualizar labels
        if self.automation_selected_label:
            self.automation_selected_label.configure(text=name, text_color="gray10")
        
        # Habilitar botões
        if self.btn_execute_main:
            self.btn_execute_main.configure(state='normal')
        if self.btn_open_folder:
            self.btn_open_folder.configure(state='normal')
    
    def update_automation_status(self, name: str, status: str):
        """Atualiza status de uma automação"""
        for card in self.automation_cards:
            if card.name == name:
                card.status = status
                card.status_original = status
                
                if card.status_label:
                    card.status_label.configure(text=f"• {status}")
                
                if card.indicator:
                    card.indicator.configure(fg_color=UIColors.get_status_color(status))
                
                # Atualizar borda do card
                if status == 'Executando':
                    card.card_frame.configure(border_color=UIColors.EXECUTING, border_width=2)
                elif self.selected_automation == name:
                    card.card_frame.configure(border_color=UIColors.ACCENT, border_width=2)
                else:
                    card.card_frame.configure(border_color="gray70", border_width=1)
                break
    
    def update_automation_counter(self, count: int):
        """Atualiza contador de automações"""
        if self.automation_counter:
            self.automation_counter.configure(text=f"{count} automações disponíveis")
    
    def update_process_counter(self, count: int):
        """Atualiza contador de processos"""
        if self.status_general:
            if count > 0:
                self.status_general.configure(
                    text=f"● {count} processo{'s' if count != 1 else ''} em execução",
                    text_color=UIColors.WARNING
                )
            else:
                self.status_general.configure(
                    text="● Sistema Operacional",
                    text_color=UIColors.SUCCESS
                )
    
    def update_last_execution(self, info: str):
        """Atualiza informação da última execução"""
        if self.last_execution_label:
            self.last_execution_label.configure(text=f"Última execução: {info}")
    
    def clear_automation_list(self):
        """Limpa lista de automações"""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.automation_cards.clear()
        self.filtered_cards.clear()
        self.selected_automation = None
        
    
    def get_message_manager(self) -> Optional[MessageManager]:
        """Retorna o message manager"""
        return self.message_manager
    
    def setup_keyboard_shortcuts(self, shortcuts: Dict[str, Callable]):
        """Configura atalhos de teclado"""
        for key, callback in shortcuts.items():
            self.root.bind(key, lambda e, cb=callback: cb())
    
    def show_error(self, title: str, message: str):
        """Mostra caixa de diálogo de erro"""
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str):
        """Mostra caixa de diálogo de informação"""
        messagebox.showinfo(title, message)
    
    def ask_yes_no(self, title: str, message: str) -> bool:
        """Mostra caixa de diálogo sim/não"""
        return messagebox.askyesno(title, message)
    
    def start_token_spinner(self) -> None:
        """Inicia animação do spinner no botão de token"""
        if not self.btn_token:
            return
            
        self.token_spinner_active = True
        self.token_spinner_frame = 0
        
        # Desabilitar botão durante execução
        self.btn_token.configure(state="disabled")
        
        # Iniciar animação
        self._animate_token_spinner()
    
    def stop_token_spinner(self) -> None:
        """Para animação do spinner no botão de token"""
        if not self.btn_token:
            return
            
        self.token_spinner_active = False
        
        # Restaurar texto original e reabilitar botão
        self.btn_token.configure(
            text=self.token_original_text,
            state="normal"
        )
    
    def _animate_token_spinner(self) -> None:
        """Anima o spinner do token"""
        if not self.token_spinner_active or not self.btn_token:
            return
        
        # Frames da animação usando caracteres Unicode
        spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
        # Atualizar texto do botão
        current_frame = spinner_frames[self.token_spinner_frame % len(spinner_frames)]
        self.btn_token.configure(text=f"{current_frame} Renovando Token...")
        
        # Próximo frame
        self.token_spinner_frame += 1
        
        # Continuar animação se ainda ativa
        if self.token_spinner_active:
            self.root.after(150, self._animate_token_spinner)
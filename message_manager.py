"""
Message Manager
Gerencia mensagens do sistema e logs internos
"""

import datetime
import customtkinter as ctk
from typing import List, Callable, Optional
from tkinter import TclError
from ui_config import UIColors, UIConstants, UIConfig

class MessageManager:
    """Gerenciador de mensagens do sistema"""
    
    def __init__(self, messages_container: ctk.CTkScrollableFrame):
        self.messages_container = messages_container
        self.messages_list: List[ctk.CTkFrame] = []
        self.log_interno: List[str] = []
        self.max_messages = UIConstants.MAX_MESSAGES
        
    def add_message(self, message: str, message_type: str = 'info') -> None:
        """Adiciona mensagem ao painel de mensagens"""
        # Cores por tipo
        type_colors = {
            'info': "gray40",
            'success': UIColors.SUCCESS,
            'error': UIColors.DANGER,
            'warning': UIColors.WARNING
        }
        
        # Frame da mensagem
        msg_frame = ctk.CTkFrame(
            self.messages_container,
            corner_radius=UIConstants.CORNER_RADIUS_CARD,
            fg_color="gray90"
        )
        msg_frame.pack(fill='x', pady=3, padx=5)
        
        # Container interno
        msg_content = ctk.CTkFrame(msg_frame, fg_color="transparent")
        msg_content.pack(fill='x', padx=10, pady=8)
        
        # Timestamp e ícone
        timestamp = datetime.datetime.now().strftime("%H:%M")
        icon = UIConstants.MESSAGE_ICONS.get(message_type, '•')
        
        # Label com ícone, timestamp e mensagem
        msg_text = f"{icon} {timestamp} - {message}"
        msg_label = ctk.CTkLabel(
            msg_content,
            text=msg_text,
            font=UIConfig.get_font(UIConstants.FONT_SIZE_SMALL),
            text_color=type_colors.get(message_type, "gray40"),
            anchor='w'
        )
        msg_label.pack(fill='x')
        
        # Adicionar à lista
        self.messages_list.append(msg_frame)
        
        # Adicionar ao log interno
        self.log_interno.append(f"[{datetime.datetime.now()}] {message_type.upper()}: {message}")
        
        # Remover mensagens antigas
        self._cleanup_old_messages()
        
        # Auto-scroll para a mensagem mais recente (com delay menor para fluidez)
        self._scroll_to_bottom()
    
    def _cleanup_old_messages(self) -> None:
        """Remove mensagens antigas mantendo apenas o máximo permitido"""
        while len(self.messages_list) > self.max_messages:
            old_msg = self.messages_list.pop(0)
            old_msg.destroy()
    
    def _scroll_to_bottom(self) -> None:
        """Faz scroll automático para a mensagem mais recente"""
        def do_scroll():
            try:
                # Método mais confiável para CTkScrollableFrame
                if hasattr(self.messages_container, '_parent_canvas'):
                    canvas = self.messages_container._parent_canvas
                    # Aguardar um frame para garantir que o conteúdo foi renderizado
                    self.messages_container.after(1, lambda: canvas.yview_moveto(1.0))
                elif hasattr(self.messages_container, '_scrollbar'):
                    # Alternativa usando scrollbar
                    scrollbar = self.messages_container._scrollbar
                    self.messages_container.after(1, lambda: scrollbar.set(1.0, 1.0))
            except (AttributeError, TclError):
                # Fallback se a estrutura interna mudar
                pass
        
        # Executar scroll após um pequeno delay para garantir renderização
        self.messages_container.after(10, do_scroll)
    
    def add_log_entry(self, message: str) -> None:
        """Adiciona entrada apenas no log interno"""
        self.log_interno.append(f"[{datetime.datetime.now()}] {message}")
    
    def get_log_history(self) -> List[str]:
        """Retorna histórico completo do log interno"""
        return self.log_interno.copy()
    
    def clear_messages(self) -> None:
        """Limpa todas as mensagens visíveis"""
        for msg_frame in self.messages_list:
            msg_frame.destroy()
        self.messages_list.clear()
    
    def force_scroll_update(self) -> None:
        """Força atualização do scroll - útil após múltiplas mensagens"""
        def update_scroll():
            try:
                # Atualizar o layout primeiro
                self.messages_container.update_idletasks()
                
                # Então fazer o scroll
                if hasattr(self.messages_container, '_parent_canvas'):
                    canvas = self.messages_container._parent_canvas
                    # Configurar scroll region
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    # Ir para o final
                    canvas.yview_moveto(1.0)
            except (AttributeError, TclError):
                pass
        
        # Executar após um delay maior para garantir que tudo foi renderizado
        self.messages_container.after(50, update_scroll)
    
    def export_logs(self, file_path: str) -> bool:
        """Exporta logs para arquivo"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=== LOG COMPLETO DO SISTEMA ===\\n\\n")
                for linha in self.log_interno:
                    f.write(f"{linha}\\n")
            return True
        except Exception as e:
            self.add_message(f"Erro ao exportar logs: {str(e)}", 'error')
            return False
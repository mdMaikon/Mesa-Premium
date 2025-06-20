"""
Configurações de Interface do Usuário
Cores, constantes e configurações visuais para o menu de automações
"""

import customtkinter as ctk
from typing import Dict, Any

# Configurações globais do CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class UIColors:
    """Paleta de cores da aplicação"""
    
    # Cores principais
    PRIMARY = '#001d99'
    PRIMARY_HOVER = '#002064'
    ACCENT = '#0092ff'
    ACCENT_HOVER = '#007ad8'
    
    # Cores de status
    SUCCESS = '#28a745'
    SUCCESS_HOVER = '#218838'
    DANGER = '#dc3545'
    DANGER_HOVER = '#c82333'
    WARNING = '#ffc107'
    INFO = '#17a2b8'
    EXECUTING = '#ff8c00'
    
    # Cores de fundo
    BG_PRIMARY = '#ffffff'
    BG_SECONDARY = '#f8f9fa'
    
    # Cores de texto
    TEXT_PRIMARY = '#000000'
    TEXT_SECONDARY = '#6c757d'
    
    # Cores de borda
    BORDER = '#dee2e6'
    BORDER_LIGHT = 'gray70'
    BORDER_ACTIVE = 'gray60'
    
    @classmethod
    def get_status_color(cls, status: str) -> str:
        """Retorna cor baseada no status"""
        colors = {
            'Pronto': 'gray60',
            'Executando': cls.EXECUTING,
            'Concluído': cls.SUCCESS,
            'Erro': cls.DANGER,
            'Atualizado': cls.SUCCESS,
            'Interrompido': 'gray50'
        }
        return colors.get(status, 'gray60')

class UIConstants:
    """Constantes da interface"""
    
    # Janela principal
    WINDOW_TITLE = "Mesa Premium • Automações"
    MIN_WIDTH = 1000
    MIN_HEIGHT = 600
    DEFAULT_WIDTH = 1200
    DEFAULT_HEIGHT = 700
    
    # Fontes
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_TITLE = 24
    FONT_SIZE_SUBTITLE = 12
    FONT_SIZE_SECTION = 14
    FONT_SIZE_NORMAL = 13
    FONT_SIZE_SMALL = 11
    FONT_SIZE_TINY = 10
    
    # Dimensões
    PADDING_MAIN = 20
    PADDING_SECTION = 15
    PADDING_CARD = 16
    CARD_HEIGHT = 60
    BUTTON_HEIGHT_NORMAL = 32
    BUTTON_HEIGHT_PRIMARY = 36
    
    # Raios
    CORNER_RADIUS_CARD = 8
    CORNER_RADIUS_BUTTON = 6
    CORNER_RADIUS_SMALL = 6
    
    # Mensagens
    MAX_MESSAGES = 5
    
    # Ícones de status
    STATUS_ICONS = {
        'Pronto': '🟢',
        'Executando': '🔄',
        'Concluído': '✓',
        'Erro': '⚠',
        'Atualizado': '✓',
        'Interrompido': '⏸'
    }
    
    # Ícones de tipo de mensagem
    MESSAGE_ICONS = {
        'info': 'ℹ️',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️'
    }

class UIConfig:
    """Configuração centralizada da UI"""
    
    @staticmethod
    def get_font(size: int = None, weight: str = "normal", family: str = None) -> ctk.CTkFont:
        """Cria fonte padronizada"""
        return ctk.CTkFont(
            family=family or UIConstants.FONT_FAMILY,
            size=size or UIConstants.FONT_SIZE_NORMAL,
            weight=weight
        )
    
    @staticmethod
    def get_button_style(style_type: str = "normal") -> Dict[str, Any]:
        """Retorna estilos pré-definidos para botões"""
        styles = {
            "primary": {
                "fg_color": UIColors.ACCENT,
                "hover_color": UIColors.ACCENT_HOVER,
                "text_color": "white",
                "corner_radius": UIConstants.CORNER_RADIUS_BUTTON,
                "height": UIConstants.BUTTON_HEIGHT_PRIMARY,
                "font": UIConfig.get_font(weight="bold")
            },
            "secondary": {
                "fg_color": "gray85",
                "hover_color": "gray80",
                "text_color": "gray20",
                "corner_radius": UIConstants.CORNER_RADIUS_BUTTON,
                "height": UIConstants.BUTTON_HEIGHT_NORMAL,
                "font": UIConfig.get_font()
            },
            "info": {
                "fg_color": UIColors.INFO,
                "hover_color": "gray80",
                "text_color": "white",
                "corner_radius": UIConstants.CORNER_RADIUS_BUTTON,
                "height": UIConstants.BUTTON_HEIGHT_NORMAL,
                "font": UIConfig.get_font()
            },
            "danger": {
                "fg_color": UIColors.DANGER,
                "hover_color": UIColors.DANGER_HOVER,
                "text_color": "white",
                "corner_radius": UIConstants.CORNER_RADIUS_BUTTON,
                "height": UIConstants.BUTTON_HEIGHT_NORMAL,
                "font": UIConfig.get_font()
            }
        }
        return styles.get(style_type, styles["secondary"])
    
    @staticmethod
    def get_frame_style(style_type: str = "normal") -> Dict[str, Any]:
        """Retorna estilos pré-definidos para frames"""
        styles = {
            "card": {
                "corner_radius": UIConstants.CORNER_RADIUS_CARD,
                "fg_color": UIColors.BG_PRIMARY,
                "border_width": 1,
                "border_color": UIColors.BORDER_LIGHT
            },
            "section": {
                "corner_radius": UIConstants.CORNER_RADIUS_SMALL,
                "fg_color": UIColors.BG_PRIMARY
            },
            "transparent": {
                "fg_color": "transparent"
            }
        }
        return styles.get(style_type, styles["transparent"])
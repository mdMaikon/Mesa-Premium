"""
Menu Principal Refatorado com DI Container
Versão modular usando injeção de dependência
"""

import customtkinter as ctk
import datetime
import json
from pathlib import Path

# Importar DI Container e configuração
from service_registry import get_configured_container
from di_container import DIContainer

# Importar managers para type hints
from path_manager import PathManager
from automacao_config import AutomacaoConfig
from database import DatabaseManager
from automacao_manager import AutomacaoManager
from ui_manager import UIManager
from execution_manager import ExecutionManager
from message_manager import MessageManager
from ui_config import UIConstants

class MenuAutomacoes:
    """Classe principal do menu de automações - versão refatorada"""
    
    def __init__(self, container: DIContainer = None):
        # Usar container configurado ou criar um novo
        self.container = container if container else get_configured_container()
        
        # Resolver dependências via DI Container
        self.path_manager = self.container.resolve(PathManager)
        self.automacao_config = self.container.resolve(AutomacaoConfig)
        self.db_manager = self.container.resolve(DatabaseManager)
        self.automacao_manager = self.container.resolve(AutomacaoManager)
        
        # Configurar janela principal
        self.root = ctk.CTk()
        
        # Inicializar UI Manager (ainda não migrado para DI)
        self.ui_manager = UIManager(self.root)
        self.ui_manager.create_interface()
        
        # Obter message manager da UI (ainda não migrado)
        self.message_manager = self.ui_manager.get_message_manager()
        
        # Resolver execution manager via DI Container
        # Sobrescrever o message_manager para usar o da UI
        self.execution_manager = self.container.resolve(ExecutionManager)
        self.execution_manager.message_manager = self.message_manager
        
        # Configurar callbacks da UI
        self._setup_ui_callbacks()
        
        # Configurar callbacks do execution manager
        self._setup_execution_callbacks()
        
        # Configurar atalhos de teclado
        self._setup_keyboard_shortcuts()
        
        # Carregar automações iniciais
        self.load_automations()
        
        # Configurar fechamento da aplicação
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _setup_ui_callbacks(self):
        """Configura callbacks da interface"""
        callbacks = {
            'select_automation': self.select_automation,
            'execute_automation': self.execute_automation,
            'execute_token': self.execute_token_renewal,
            'update_automations': self.load_automations,
            'export_logs': self.export_logs,
            'open_folder': self.open_specific_folder,
            'filter_automations': self.filter_automations
        }
        self.ui_manager.set_callbacks(callbacks)
    
    def _setup_execution_callbacks(self):
        """Configura callbacks do execution manager"""
        self.execution_manager.set_ui_callbacks(
            status_update=self.update_automation_status,
            process_counter=self.update_process_counter,
            button_state=self.update_button_state
        )
    
    def _setup_keyboard_shortcuts(self):
        """Configura atalhos de teclado"""
        shortcuts = {
            '<Return>': self.execute_automation,
            '<Control-t>': self.execute_token_renewal,
            '<F5>': self.load_automations,
            '<Control-r>': self.load_automations,
            '<Control-l>': self.export_logs,
            '<Control-o>': self.open_specific_folder,
            '<Control-f>': lambda: self.ui_manager.search_field.focus() if self.ui_manager.search_field else None,
            '<Escape>': self.try_quit
        }
        self.ui_manager.setup_keyboard_shortcuts(shortcuts)
    
    def load_automations(self):
        """Carrega lista de automações"""
        self.message_manager.add_log_entry("Carregando automações...")
        
        # Limpar lista atual
        self.ui_manager.clear_automation_list()
        
        try:
            # Recarregar automações do manager
            self.automacao_manager.recarregar_automacoes()
            
            # Obter lista de automações disponíveis (filtrando tokens)
            automacoes_disponiveis = self.automacao_manager.listar_automacoes(filtrar_token=True)
            
            # Criar cards para cada automação
            for automacao_meta in automacoes_disponiveis:
                nome = automacao_meta['nome']
                descricao = automacao_meta['descricao']
                self.ui_manager.create_automation_card(nome, descricao)
            
            # Atualizar contador
            total_automacoes = len(automacoes_disponiveis)
            self.ui_manager.update_automation_counter(total_automacoes)
            
            self.message_manager.add_log_entry(f"Encontradas {total_automacoes} automações")
            self.message_manager.add_message(f"{total_automacoes} automações carregadas", 'success')
            
        except Exception as e:
            self.message_manager.add_log_entry(f"Erro ao carregar automações: {str(e)}")
            self.message_manager.add_message("Erro ao carregar automações", 'error')
    
    def select_automation(self, name: str):
        """Seleciona uma automação"""
        self.ui_manager.select_automation(name)
        
        # Atualizar informações da última execução
        last_execution = self.execution_manager.get_last_execution(name)
        self.ui_manager.update_last_execution(last_execution)
        
        # Feedback
        self.message_manager.add_message(f"Automação '{name}' selecionada", 'info')
    
    def execute_automation(self):
        """Executa a automação selecionada"""
        if not self.ui_manager.selected_automation:
            return
        
        automation_name = self.ui_manager.selected_automation
        
        # Verificar se não está em execução
        if self.execution_manager.is_process_active(automation_name):
            self.message_manager.add_message(f"Automação '{automation_name}' já está em execução", 'warning')
            return
        
        # Executar via execution manager
        self.execution_manager.execute_automation(automation_name)
    
    def execute_token_renewal(self):
        """Executa renovação de token"""
        self.execution_manager.execute_token_renewal()
    
    def update_automation_status(self, name: str, status: str, status_type: str):
        """Atualiza status visual de uma automação"""
        self.ui_manager.update_automation_status(name, status)
    
    def update_process_counter(self):
        """Atualiza contador de processos ativos"""
        count = self.execution_manager.get_active_processes_count()
        self.ui_manager.update_process_counter(count)
    
    def update_button_state(self, automation_name: str, enabled: bool):
        """Atualiza estado dos botões após execução"""
        if automation_name == self.ui_manager.selected_automation:
            if self.ui_manager.btn_execute_main:
                state = 'normal' if enabled else 'disabled'
                self.ui_manager.btn_execute_main.configure(state=state)
    
    def open_specific_folder(self):
        """Abre pasta específica da automação selecionada"""
        if self.ui_manager.selected_automation:
            self.automacao_config.abrir_pasta_automacao(
                self.ui_manager.selected_automation,
                log_callback=lambda msg: self.message_manager.add_message(msg, 'info')
            )
    
    def export_logs(self):
        """Exporta logs completos"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            logs_dir = self.path_manager.get_path('logs')
            if logs_dir is None:
                raise ValueError("Diretório de logs não encontrado")
            
            log_file = logs_dir / f"log_completo_{timestamp}.txt"
            
            if self.message_manager.export_logs(str(log_file)):
                self.message_manager.add_message("Logs exportados com sucesso", 'success')
                self.ui_manager.show_info("Sucesso", f"Logs salvos em:\\n{log_file}")
            else:
                self.message_manager.add_message("Erro ao exportar logs", 'error')
                
        except Exception as e:
            self.message_manager.add_message(f"Erro ao exportar logs: {str(e)}", 'error')
    
    def filter_automations(self, event=None):
        """Filtra automações baseado no texto de pesquisa"""
        if not self.ui_manager.search_field:
            return
        
        search_term = self.ui_manager.search_field.get().lower().strip()
        
        # Limpar cards atuais
        for widget in self.ui_manager.scroll_frame.winfo_children():
            widget.destroy()
        
        # Resetar lista filtrada
        self.ui_manager.filtered_cards.clear()
        
        # Filtrar e recriar cards
        for card in self.ui_manager.automation_cards:
            if not search_term or search_term in card.name.lower():
                # Recriar o card
                new_card = self.ui_manager.create_automation_card(card.name, card.description, card.status)
                self.ui_manager.filtered_cards.append(new_card)
                
                # Aplicar seleção se necessário
                if self.ui_manager.selected_automation == card.name:
                    self.ui_manager.select_automation(card.name)
        
        # Atualizar contador
        total_found = len(self.ui_manager.automation_cards)
        total_filtered = len(self.ui_manager.filtered_cards)
        
        if search_term:
            self.ui_manager.automation_counter.configure(
                text=f"{total_filtered} de {total_found} automações"
            )
        else:
            self.ui_manager.automation_counter.configure(
                text=f"{total_found} automações disponíveis"
            )
    
    def try_quit(self):
        """Tenta sair da aplicação"""
        if self.ui_manager.ask_yes_no("Sair", "Deseja sair do programa?"):
            self.on_closing()
    
    def on_closing(self):
        """Manipula fechamento da aplicação"""
        try:
            # Salvar log de sessão
            if self.message_manager:
                log_history = self.message_manager.get_log_history()
                if log_history:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    logs_dir = self.path_manager.get_path('logs')
                    if logs_dir:
                        log_file = logs_dir / f"sessao_{timestamp}.log"
                        
                        with open(log_file, 'w', encoding='utf-8') as f:
                            for linha in log_history:
                                f.write(f"{linha}\\n")
        
        except Exception as e:
            print(f"Erro ao salvar log de sessão: {e}")
        
        finally:
            self.root.destroy()
    
    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()

def main():
    """Função principal"""
    app = MenuAutomacoes()
    app.run()

if __name__ == "__main__":
    main()
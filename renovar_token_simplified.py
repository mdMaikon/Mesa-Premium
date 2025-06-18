"""
Automação: Renovar Token Hub XP - Versão Simplificada
Extrai tokens de autenticação do Hub XP usando interface GUI e salva no banco MySQL
"""

from dotenv import load_dotenv
import mysql.connector
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from PIL import Image
from tkinter import messagebox
import customtkinter as ctk
import os
import json
import logging
import platform
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Adicionar diretório pai ao path
sys.path.append(str(Path(__file__).parent.parent))


__tags__ = ['autenticacao', 'hub-xp', 'token', 'mysql', 'gui', 'selenium']


class HubXPTokenExtractorSimplified:
    """Extrator de tokens do Hub XP - Versão Simplificada para arquitetura modular"""

    # Cores da interface
    AZUL_PRINCIPAL = "#071d5c"
    VERMELHO_PRINCIPAL = "#810b0b"
    AZUL_HOVER = "#0080ff"
    BRANCO = "#FFFFFF"
    CINZA_CLARO = "#f8f9fa"
    CINZA_TEXTO = "#495057"
    CINZA_BORDA = "#E9E9E9"

    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.base_folder = Path(__file__).parent
        self.log_path = self.base_folder / "logs" / "hub_token_simplified.log"
        self.icon_path = self.base_folder / "icone.png"
        self.user_config_path = self.base_folder / \
            "configs" / "user_config_simplified.json"

        # Criar diretórios se não existirem
        self.log_path.parent.mkdir(exist_ok=True, parents=True)
        self.user_config_path.parent.mkdir(exist_ok=True, parents=True)

        self.setup_logging()
        self.load_env()
        self.load_icon()
        self.driver: Optional[webdriver.Chrome] = None
        self.environment = self.detect_environment()

    def setup_logging(self):
        """Configura logging simples"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_env(self):
        """Carrega configurações do banco"""
        env_file = self.base_folder / '.env'
        load_dotenv(env_file)

        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME')
        }

        if not all([self.db_config['user'], self.db_config['password'], self.db_config['database']]):
            raise ValueError("Credenciais do banco não configuradas no .env")

    def detect_environment(self) -> str:
        """Detecta ambiente de execução"""
        try:
            if platform.system() == 'Windows':
                return 'windows'

            if platform.system() == 'Linux':
                # Verifica se é WSL
                try:
                    with open('/proc/version', 'r') as f:
                        if 'microsoft' in f.read().lower():
                            return 'wsl'
                except:
                    pass

                if os.environ.get('WSL_DISTRO_NAME'):
                    return 'wsl'

                return 'linux'

            return 'unknown'
        except Exception as e:
            self.logger.warning(f"Erro ao detectar ambiente: {e}")
            return 'unknown'

    def get_chrome_binary_path(self) -> Optional[str]:
        """Retorna caminho do Chrome baseado no ambiente"""
        if self.environment == 'windows':
            paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            for path in paths:
                if os.path.exists(path):
                    return path

        elif self.environment in ['wsl', 'linux']:
            paths = [
                '/usr/bin/chromium-browser',
                '/usr/bin/google-chrome-stable',
                '/usr/bin/google-chrome'
            ]
            for path in paths:
                if os.path.exists(path):
                    return path

        return None

    def get_chromedriver_path(self) -> Optional[str]:
        """Retorna caminho do ChromeDriver"""
        if self.environment == 'windows':
            paths = [
                str(self.base_folder / 'chromedriver.exe'),
                'chromedriver.exe'
            ]
            for path in paths:
                if os.path.exists(path) or path == 'chromedriver.exe':
                    return path

        elif self.environment in ['wsl', 'linux']:
            paths = [
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver'
            ]
            for path in paths:
                if os.path.exists(path):
                    return path

        return None

    def load_icon(self):
        """Carrega ícone se existir"""
        try:
            if self.icon_path.exists():
                self.icon = ctk.CTkImage(
                    Image.open(self.icon_path), size=(60, 60))
            else:
                self.icon = None
        except Exception:
            self.icon = None

    def load_user_config(self):
        """Carrega último login usado"""
        try:
            if self.user_config_path.exists():
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get('last_login', '')
        except:
            pass
        return ''

    def save_user_config(self, login):
        """Salva último login"""
        try:
            config = {'last_login': login,
                      'last_updated': datetime.now().isoformat()}
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Erro ao salvar config: {e}")

    def get_credentials(self) -> Dict[str, Any]:
        """Interface simples para credenciais"""
        result: Dict[str, Any] = {'cancelled': True}

        def submit():
            login = entry_login.get().strip()
            senha = entry_senha.get().strip()
            mfa = entry_mfa.get().strip()

            if not login or not senha:
                messagebox.showerror("Erro", "Login e senha são obrigatórios!")
                return

            if not mfa or len(mfa) != 6 or not mfa.isdigit():
                messagebox.showerror("Erro", "MFA deve ter 6 dígitos!")
                return

            result['login'] = login
            result['senha'] = senha
            result['mfa'] = mfa
            result['cancelled'] = False
            self.save_user_config(login)
            app.quit()

        def cancel():
            app.quit()

        # Janela principal
        app = ctk.CTk()
        app.title("Hub XP - Login (Simplificado)")
        app.geometry("400x430")
        app.resizable(False, False)

        # Centralizar
        x = (app.winfo_screenwidth() - 400) // 2
        y = (app.winfo_screenheight() - 430) // 2
        app.geometry(f"400x430+{x}+{y}")

        # Container principal
        frame = ctk.CTkFrame(app, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        title = ctk.CTkLabel(frame, text="Hub XP - Autenticação (Simplificado)",
                             font=ctk.CTkFont(size=18, weight="bold"),
                             text_color=self.AZUL_PRINCIPAL)
        title.pack(pady=(20, 30))

        # Campos de entrada
        ctk.CTkLabel(frame, text="Login:", font=ctk.CTkFont(
            weight="bold")).pack(anchor="w", padx=30)
        entry_login = ctk.CTkEntry(
            frame, placeholder_text="Digite seu login", height=35)
        entry_login.pack(fill="x", padx=30, pady=(5, 15))

        # Preenche último login
        last_login = self.load_user_config()
        if last_login:
            entry_login.insert(0, last_login)

        ctk.CTkLabel(frame, text="Senha:", font=ctk.CTkFont(
            weight="bold")).pack(anchor="w", padx=30)
        entry_senha = ctk.CTkEntry(
            frame, placeholder_text="Digite sua senha", show="*", height=35)
        entry_senha.pack(fill="x", padx=30, pady=(5, 15))

        ctk.CTkLabel(frame, text="MFA (6 dígitos):", font=ctk.CTkFont(
            weight="bold")).pack(anchor="w", padx=30)
        entry_mfa = ctk.CTkEntry(
            frame, placeholder_text="Digite o código MFA", height=35)
        entry_mfa.pack(fill="x", padx=30, pady=(5, 20))

        # Botões
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 20))

        ctk.CTkButton(btn_frame, text="Cancelar", command=cancel,
                      fg_color=self.VERMELHO_PRINCIPAL, width=120, height=40).pack(side="left")

        ctk.CTkButton(btn_frame, text="Entrar", command=submit,
                      fg_color=self.AZUL_PRINCIPAL, width=120, height=40).pack(side="right")

        # Bindings
        app.bind('<Return>', lambda e: submit())
        app.bind('<Escape>', lambda e: cancel())
        app.protocol("WM_DELETE_WINDOW", cancel)

        # Foco inicial
        app.after(100, lambda: entry_login.focus())

        app.mainloop()
        app.destroy()

        return result

    def setup_driver(self, headless: bool = True) -> bool:
        """Configuração do WebDriver baseada no ambiente"""
        try:
            options = Options()

            # Configurações comuns
            options.add_argument("--disable-gpu")
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            options.add_experimental_option(
                'excludeSwitches', ['enable-logging'])
            options.add_experimental_option('useAutomationExtension', False)

            # Configurações específicas para WSL/Linux
            if self.environment in ['wsl', 'linux']:
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-plugins")
                options.add_argument("--remote-debugging-port=9222")

                # Configura binário do browser
                binary_path = self.get_chrome_binary_path()
                if binary_path:
                    options.binary_location = binary_path
                    self.logger.info(f"Usando binário: {binary_path}")

            # Inicializa WebDriver
            chromedriver_path = self.get_chromedriver_path()
            if chromedriver_path and chromedriver_path != 'chromedriver.exe':
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(
                    service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)

            self.driver.implicitly_wait(10)
            self.logger.info(f"WebDriver configurado para {self.environment}")
            return True

        except WebDriverException as e:
            self.logger.error(f"Erro WebDriver: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def perform_login(self, credentials: Dict[str, Any]) -> bool:
        """Login no Hub XP"""
        if not self.driver:
            return False

        try:
            self.logger.info("Acessando Hub XP")
            self.driver.get("https://hub.xpi.com.br/")

            # Login
            login_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "account"))
            )
            login_field.send_keys(credentials['login'])

            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(credentials['senha'])

            submit_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[aria-label='Continuar']")
            submit_button.click()

            # MFA
            mfa_fields = WebDriverWait(self.driver, 30).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "input[pattern='[0-9]*']"))
            )

            for i, campo in enumerate(mfa_fields):
                campo.send_keys(credentials['mfa'][i])

            try:
                mfa_submit = self.driver.find_element(
                    By.CSS_SELECTOR, "button[aria-label='Confirmar e acessar conta']")
            except:
                mfa_submit = self.driver.find_element(
                    By.CSS_SELECTOR, "soma-button[type='submit']")

            mfa_submit.click()

            # Aguarda autenticação
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "header"))
            )

            self.logger.info("Login realizado com sucesso")
            return True

        except TimeoutException:
            self.logger.error("Timeout durante login")
            return False
        except Exception as e:
            self.logger.error(f"Erro durante login: {e}")
            return False

    def extract_token(self) -> Optional[Dict[str, Any]]:
        """Extrai token do localStorage"""
        if not self.driver:
            return None

        try:
            local_storage_keys = self.driver.execute_script(
                "return Object.keys(window.localStorage);")
            oidc_key = next(
                (k for k in local_storage_keys if k.startswith("oidc.user:")), None)

            if not oidc_key:
                self.logger.error("Chave OIDC não encontrada")
                return None

            oidc_data_raw = self.driver.execute_script(
                f"return window.localStorage.getItem('{oidc_key}');")
            oidc_data = json.loads(oidc_data_raw)

            token = oidc_data.get("access_token")
            expires_at = oidc_data.get("expires_at")

            if not token:
                self.logger.error("Token não encontrado")
                return None

            return {
                'token': token,
                'expires_at': datetime.fromtimestamp(expires_at) if expires_at else datetime.now() + timedelta(hours=8),
                'extracted_at': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Erro ao extrair token: {e}")
            return None

    def save_token_to_db(self, token_data: Dict[str, Any], user_login: str) -> bool:
        """Salva token no banco"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            # Cria tabela se não existir
            create_table_query = """
            CREATE TABLE IF NOT EXISTS hub_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_login VARCHAR(255) NOT NULL,
                token TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                extracted_at DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_login (user_login),
                INDEX idx_expires_at (expires_at)
            )
            """
            cursor.execute(create_table_query)

            # Remove tokens antigos do usuário
            cursor.execute(
                "DELETE FROM hub_tokens WHERE user_login = %s", (user_login,))

            # Insere novo token
            insert_query = """
            INSERT INTO hub_tokens (user_login, token, expires_at, extracted_at)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                user_login,
                token_data['token'],
                token_data['expires_at'],
                token_data['extracted_at']
            ))

            conn.commit()
            cursor.close()
            conn.close()

            self.logger.info(f"Token salvo para usuário: {user_login}")
            return True

        except mysql.connector.Error as e:
            self.logger.error(f"Erro no banco: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao salvar token: {e}")
            return False

    def cleanup(self):
        """Limpa recursos"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass

    def run(self, headless: bool = True, **kwargs) -> Dict[str, Any]:
        """Execução principal para integração modular"""
        try:
            self.logger.info(
                "Iniciando extração de token (versão simplificada)")

            # Obtém credenciais
            credentials = self.get_credentials()
            if credentials.get('cancelled', True):
                self.logger.info("Operação cancelada pelo usuário")
                return {
                    'success': False,
                    'message': 'Operação cancelada pelo usuário',
                    'token_extraido': False
                }

            # Configura WebDriver
            if not self.setup_driver(headless=headless):
                return {
                    'success': False,
                    'message': 'Falha na configuração do navegador',
                    'token_extraido': False
                }

            # Login
            if not self.perform_login(credentials):
                return {
                    'success': False,
                    'message': 'Falha no login - verifique suas credenciais',
                    'token_extraido': False
                }

            # Extrai token
            token_data = self.extract_token()
            if not token_data:
                return {
                    'success': False,
                    'message': 'Falha ao extrair token do localStorage',
                    'token_extraido': False
                }

            # Salva no banco
            if not self.save_token_to_db(token_data, credentials['login']):
                return {
                    'success': False,
                    'message': 'Falha ao salvar token no banco de dados',
                    'token_extraido': True,
                    'token_data': token_data
                }

            # Sucesso
            self.logger.info("Token extraído e salvo com sucesso")
            return {
                'success': True,
                'message': 'Token atualizado com sucesso!',
                'token_extraido': True,
                'user_login': credentials['login'],
                'expires_at': token_data['expires_at'].isoformat(),
                'extracted_at': token_data['extracted_at'].isoformat()
            }

        except Exception as e:
            self.logger.error(f"Erro geral: {e}")
            return {
                'success': False,
                'message': f'Erro inesperado: {str(e)}',
                'token_extraido': False
            }
        finally:
            self.cleanup()


# Função principal para uso na arquitetura modular
def renovar_token_simplificado(headless: bool = True, **kwargs):
    """
    Renova token do Hub XP usando interface GUI simplificada

    Args:
        headless: Executar navegador em modo headless (padrão: True)
        **kwargs: Parâmetros adicionais

    Returns:
        dict: Resultado da operação com detalhes do processo
    """
    try:
        extractor = HubXPTokenExtractorSimplified()
        return extractor.run(headless=headless, **kwargs)
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro na inicialização: {str(e)}',
            'token_extraido': False
        }


# Alias para compatibilidade
renovar_token_gui = renovar_token_simplificado


if __name__ == "__main__":
    # Execução standalone
    result = renovar_token_simplificado(headless=True)
    print(f"Resultado: {result}")

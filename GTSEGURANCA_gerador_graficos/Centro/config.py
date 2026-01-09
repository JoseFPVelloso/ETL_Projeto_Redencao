import os
import sys

# --- CONFIGURAÇÃO DE DIRETÓRIOS ---
# Define o diretório base (onde o script está rodando)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pastas de Saída e Configuração
OUTPUT_FOLDER = os.path.join(BASE_DIR, "Gráficos")
CONFIG_FOLDER = os.path.join(BASE_DIR, "Config")
CONFIG_FILE = os.path.join(CONFIG_FOLDER, 'config_ruas_preferidas.json')

# Constantes Padrão
DEFAULT_START_MONTHLY = "01/06/2025"
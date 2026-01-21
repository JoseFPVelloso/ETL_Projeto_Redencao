import os
from datetime import datetime, timedelta

# --- Caminhos ---
# Define a pasta onde o script está rodando
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'relatorios')

# Cria a pasta de relatórios se não existir
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# --- Configurações de Data Padrão ---
hoje = datetime.now()

# Padrão 1: Últimos 15 dias (para análise diária/ranking)
DATA_FIM_PADRAO = hoje
DATA_INICIO_DIARIA = hoje - timedelta(days=15)

# Padrão 2: Desde Junho (para análise mensal)
# Se estivermos antes de junho no ano, pega junho do ano anterior, senão junho deste ano
ano_corrente = hoje.year
mes_junho = 6
DATA_INICIO_MENSAL = datetime(ano_corrente, mes_junho, 1)

# --- Estilos da UI (Tkinter) ---
TITLE = "Analisador de Contagens - Okuhara & Centro"
GEOMETRY = "700x550"
BG_COLOR = "#f0f0f0"
ACCENT_COLOR = "#0078d7" # Azul estilo Windows
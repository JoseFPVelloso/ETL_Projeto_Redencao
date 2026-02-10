import os
from datetime import datetime, timedelta

# --- Caminhos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'relatorios')
ARQUIVO_REGIOES = os.path.join(BASE_DIR, 'regioes.xlsx') # Caminho do mapa de regiões

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# --- Configurações de Data ---
hoje = datetime.now()

# Padrão 1: Últimos 15 dias (Ranking Diário)
DATA_FIM_PADRAO = hoje
DATA_INICIO_DIARIA = hoje - timedelta(days=15)

# Padrão 2: Desde Junho (Evolução Mensal)
# Correção da lógica: Se estamos antes de Junho, pega Junho do ano passado.
# Se já passamos de Junho, pega Junho deste ano.
ano_mensal = hoje.year
if hoje.month < 6:
    ano_mensal -= 1

DATA_INICIO_MENSAL = datetime(ano_mensal, 6, 1)

# --- Configurações de Períodos ---
PERIODOS_DISPONIVEIS = [
    ("05h (Madrugada)", "05h"),
    ("10h (Manhã)", "10h"),
    ("15h (Tarde)", "15h"),
    ("20h (Noite)", "20h")
]

# --- Estilos da UI ---
TITLE = "Analisador Okuhara & Centro"
GEOMETRY = "900x750" # Aumentei um pouco para caber os checkboxes
BG_COLOR = "#f4f4f9"
ACCENT_COLOR = "#2980b9" # Azul mais sóbrio
ERROR_COLOR = "#c0392b"
SUCCESS_COLOR = "#27ae60"
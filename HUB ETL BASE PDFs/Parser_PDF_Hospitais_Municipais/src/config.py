"""
========================================================================
                      CONFIGURAÇÕES GLOBAIS
========================================================================
Este arquivo centraliza todas as constantes, nomes de colunas, 
mapeamentos e ordens do projeto de extração de leitos.
"""
from pathlib import Path


# --- Caminho Absoluto ---
BASE_DIR = Path(__file__).resolve().parent

# --- Configuração de Pastas ---
DIR_ENTRADA = BASE_DIR / 'PDF'
DIR_SAIDA = BASE_DIR / 'Tabelas'

# --- Configuração do PDF ---
PAGINA_PDF = 'all' # Lê todas as páginas

# --- Configuração das Colunas ---
NOMES_COLUNAS_LIMPOS = [
    'CNES', 'Estabelecimento', 'Leitos_Instalados', 
    'Quant_Involuntario', 'Quant_Voluntario', 'Quant_Compulsorios'
]
COLS_INTERNADOS = ['Quant_Involuntario', 'Quant_Voluntario', 'Quant_Compulsorios']

# --- Mapeamento de Nomes (Tradução) ---
MAPEAMENTO_NOMES = {
    # --- LIMPEZA DE NOMECLATURA ---
    'HM CAMPO LIMPO-FERNANDO MAURO P DA ROCHA': 'HM Fernando Mauro Pires da Rocha (Sub. Campo Limpo)',
    'HM CIDADE TIRADENTES CARMEN PRUDENTE': 'HM Carmen Prudente (Sub. Cidade Tiradentes)',
    'HM CIDADE TIRADENTES - CARMEN PRUDENTE': 'HM Carmen Prudente (Sub. Cidade Tiradentes)',
    'HM DR. ARTHUR RIBEIRO SABOYA- JABAQUARA': 'HM Jabaquara Artur Ribeiro de Saboya (Sub. Jabaquara)*',
    'HM DR. ARTHUR RIBEIRO SABOYA - JABAQUARA': 'HM Jabaquara Artur Ribeiro de Saboya (Sub. Jabaquara)*',
    'HM DR. ARTHUR RIBEIRO SABOΥΑ - JABAQUARA': 'HM Jabaquara Artur Ribeiro de Saboya (Sub. Jabaquara)*',
    'HM DR. BENEDITO MONTENEGRO - JARDIM IVA': 'HM Dr. Benedicto Montenegro (Sub. Aricanduva)',
    'HM DR. MOYSES DEUTSCH - M BOI MIRIM': "HM M'Boi Mirim (Sub. M'Boi Mirim)",
    'HM DR. MOYSES DEUTSCH - M BOΙ MIRIM': "HM M'Boi Mirim (Sub. M'Boi Mirim)",
    'HM JOSANIAS CASTANHA BRAGA - PARELHEIROS': 'Hospital Parelheiros - Josanias Castanha Braga (Sub. Parelheiros)',
    'HM PROF. DR. WALDOMIRO DE PAULA ITAQUERA/PLANALTO': 'HM Prof. Dr. Waldomiro de Paula (Sub. Itaquera)',
    'HM PROF. DR. WALDOMIRO DE PAULA - ITAQUERA/PLANALTO': 'HM Prof. Dr. Waldomiro de Paula (Sub. Itaquera)',
    'HM VILA MARIA - VEREADOR JOSÉ STOROPOILI': 'HM Ver. José Storopolli (Sub. Vila Maria)',
    'HOSPITAL CANTAREIRA': 'Hospital Cantareira (Sub. Santana Tucuruvi)'
}

# --- Ordem de Saída Personalizada ---
ORDEM_HOSPITAIS = [
    'Hospital Cantareira (Sub. Santana Tucuruvi)',
    'HM Jabaquara Artur Ribeiro de Saboya (Sub. Jabaquara)*',
    'HM Dr. Benedicto Montenegro (Sub. Aricanduva)',
    'HM Carmen Prudente (Sub. Cidade Tiradentes)',
    'HM Fernando Mauro Pires da Rocha (Sub. Campo Limpo)',
    "HM M'Boi Mirim (Sub. M'Boi Mirim)",
    'Hospital Parelheiros - Josanias Castanha Braga (Sub. Parelheiros)',
    'HM Prof. Dr. Waldomiro de Paula (Sub. Itaquera)',
    'HM Ver. José Storopolli (Sub. Vila Maria)'
]
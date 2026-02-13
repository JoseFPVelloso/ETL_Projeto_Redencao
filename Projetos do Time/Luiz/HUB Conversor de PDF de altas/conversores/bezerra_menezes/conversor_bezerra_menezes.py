import pdfplumber
import re
import os

def formatar_data_padrao(texto_data):
    """Converte datas de DD/MM/YY para DD/MM/YYYY."""
    if not texto_data:
        return None
    
    match = re.search(r"(\d{2})/(\d{2})/(\d{2,4})", texto_data)
    if match:
        dia, mes, ano = match.groups()
        if len(ano) == 2:
            ano = "19" + ano if int(ano) > 30 else "20" + ano
        return f"{dia}/{mes}/{ano}"
    return texto_data

def extrair_dados_bezerra(caminho_pdf):
    dados = {
        "Nome": None,
        "Data Nascimento": None,
        "Nome da Mãe": None,
        "Data Entrada": None,
        "Unidade": "BEZERRA", 
        "Tipo de Alta": None,
        "Data Alta": None,
        "Equipamento Social": None,
        "CAPS REFERENCIA": None  # Nova coluna adicionada
    }

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

            # Nome
            match_nome = re.search(r"Nome:\s*(.*)", full_text)
            if match_nome: dados["Nome"] = match_nome.group(1).strip()

            # Data de Entrada (Corrigida para aceitar com ou sem o "de")
            match_entrada = re.search(r"Data\s+(?:de\s+)?entrada:\s*(\d{2}/\d{2}/\d{2,4})", full_text, re.IGNORECASE)
            if match_entrada: dados["Data Entrada"] = formatar_data_padrao(match_entrada.group(1))

            # Outras Datas
            match_dn = re.search(r"Data de Nascimento:\s*(\d{2}/\d{2}/\d{2,4})", full_text)
            if match_dn: dados["Data Nascimento"] = formatar_data_padrao(match_dn.group(1))

            match_alta = re.search(r"Data de Alta:\s*(\d{2}/\d{2}/\d{2,4})", full_text)
            if match_alta: dados["Data Alta"] = formatar_data_padrao(match_alta.group(1))

            # Nome da Mãe
            match_mae = re.search(r"Nome da Genitora:\s*(.*)", full_text)
            if match_mae: dados["Nome da Mãe"] = match_mae.group(1).strip()

            # Tipo de Alta
            match_tipo = re.search(r"\(\s*[xX]\s*\)\s*(médica|pedida|administrativa)", full_text, re.IGNORECASE)
            if match_tipo:
                dados["Tipo de Alta"] = match_tipo.group(1).strip().capitalize()

            # Equipamento Social
            match_enc = re.search(r"Encaminhamento para:.*?\(\s*[xX]\s*\)\s*([^()\n]+)", full_text, re.DOTALL)
            if match_enc:
                dados["Equipamento Social"] = match_enc.group(1).strip()

            # CAPS de Referência (Nova Extração)
            # Procura por 'CAPS de referência:' e pega o texto até o fim da linha ou início da próxima seção
            match_caps = re.search(r"CAPS de referência:\s*(.*)", full_text, re.IGNORECASE)
            if match_caps:
                dados["CAPS REFERENCIA"] = match_caps.group(1).strip()

        return dados
    except Exception as e:
        print(f"Erro no arquivo {os.path.basename(caminho_pdf)}: {e}")
        return None
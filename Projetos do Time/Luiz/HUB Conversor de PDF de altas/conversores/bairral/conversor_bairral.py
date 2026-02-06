import pdfplumber
import re
import os

def extrair_dados_final_v2(caminho_pdf):
    dados = {
        "Nome": None,
        "Data Nascimento": None,
        "Nome da Mãe": None,
        "Data Entrada": None,
        "Unidade": "BAIRRAL",
        "Tipo de Alta": None,
        "Data Alta": None
    }

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            pagina_1 = pdf.pages[0]
            texto_bruto = pagina_1.extract_text()
            
            # Extração do Nome (Regex robusta)
            match_nome = re.search(r"Nome\s*\n?(.+?)(?=\s*(?:Nome Social|Data Nascto|Data Nascimento|Endereço))", texto_bruto, re.DOTALL | re.IGNORECASE)
            if match_nome:
                nome_limpo = match_nome.group(1).strip().replace('\n', ' ')
                dados["Nome"] = re.sub(r'\s+', ' ', nome_limpo)
            
            # Extração de Datas via Configuração de Tabela
            settings = {"vertical_strategy": "text", "horizontal_strategy": "text", "intersection_x_tolerance": 15}
            tabelas = pagina_1.extract_tables(table_settings=settings)

            for tabela in tabelas:
                for linha in tabela:
                    linha_str = [str(c).strip() if c else "" for c in linha]
                    for i, celula in enumerate(linha_str):
                        contexto = " ".join(linha_str[i:]) 
                        if "Data Nascto" in celula:
                            match = re.search(r"(\d{2}/\d{2}/\d{4})", contexto)
                            if match: dados["Data Nascimento"] = match.group(1)
                        if "Data Entrada" in celula:
                            match = re.search(r"(\d{2}/\d{2}/\d{4})", contexto)
                            if match: dados["Data Entrada"] = match.group(1)
                        if "Data Alta" in celula:
                            match = re.search(r"(\d{2}/\d{2}/\d{4})", contexto)
                            if match: dados["Data Alta"] = match.group(1)

            # Texto completo para campos de fluxo corrido
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

            # Nome da Mãe
            match_mae = re.search(r"Mãe:\s*(.*?)\s*Pai:", full_text)
            if match_mae: dados["Nome da Mãe"] = match_mae.group(1).strip()

            # Tipo de Alta
            match_tipo = re.search(r"Tipo da alta:(.*)", full_text)
            if match_tipo:
                opcoes = re.findall(r"\[[xX]\]\s*([^\[]+)", match_tipo.group(1))
                if opcoes: dados["Tipo de Alta"] = opcoes[0].strip()

            if not dados["Data Alta"]: 
                dados["Data Alta"] = "Em Aberto"

        return dados
    except Exception as e:
        print(f"Erro no arquivo {os.path.basename(caminho_pdf)}: {e}")
        return None
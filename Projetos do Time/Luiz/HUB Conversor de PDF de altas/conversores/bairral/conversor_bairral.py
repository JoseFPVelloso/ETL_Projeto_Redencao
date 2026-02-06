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
        "Data Alta": None,
        "Equipamento Social": None
    }

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            pagina_1 = pdf.pages[0]
            texto_bruto = pagina_1.extract_text()
            
            # Extração do Nome
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

            # Texto completo (paginas 1 e 2)
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

            # --- NOVO: Extração do Encaminhamento Social (Lógica Linha a Linha com STOP WORDS) ---
            # 1. Isola o bloco da Seção 4
            secao_encaminhamento = re.search(r"4\.\s*ENCAMINHAMENTOS PARA REDE.*?(?=\d{2}/\d{2}/\d{4}|Página)", full_text, re.DOTALL | re.IGNORECASE)
            
            if secao_encaminhamento:
                bloco_texto = secao_encaminhamento.group(0)
                linhas = bloco_texto.split('\n')
                
                texto_capturado = []
                capturando = False
                
                # Lista de frases que indicam que o texto do usuário ACABOU (Início de outra opção ou Rodapé)
                stop_phrases = [
                    "Santa Carlota", "CT Via HUB", "SCP", "Vaga Feminina", "Casa de Passagem", 
                    "CT-", "SIAT", "Casa Terapêutica", "Paciente orientado", "Seguirá", 
                    "Observação", "Obs:", "Ressalva", "CTA 15", "Espaço Prevenir"
                ]

                for linha in linhas:
                    linha_limpa = linha.strip()
                    
                    if not capturando:
                        # Procura a linha que tem o [x]
                        match = re.search(r"\[[xX]\]\s*(.*)", linha)
                        if match:
                            capturando = True
                            conteudo = match.group(1)
                            # Se houver outro '[' na mesma linha (ex: [x] Opção1 [ ] Opção2), corta antes
                            if "[" in conteudo:
                                conteudo = conteudo.split("[")[0]
                            texto_capturado.append(conteudo)
                    else:
                        # Se já estamos capturando (multilinha), verificamos se devemos PARAR
                        
                        # 1. Se encontrar um novo checkbox [ ] ou ( )
                        if "[" in linha_limpa or "(" in linha_limpa:
                            break
                        
                        # 2. Se a linha começar com palavras reservadas do formulário (Ex: Santa Carlota)
                        if any(linha_limpa.startswith(s) for s in stop_phrases):
                            break
                        
                        # 3. Proteção extra contra datas ou rodapés
                        if re.search(r"\d{2}/\d{2}/\d{4}", linha_limpa):
                            break
                        
                        # Se passou nos testes, é continuação do texto do usuário
                        texto_capturado.append(linha_limpa)
                
                # Processa o texto acumulado
                if texto_capturado:
                    texto_full = " ".join(texto_capturado).strip()
                    
                    # Limpeza do "Especificar"
                    if "especificar" in texto_full.lower():
                        partes = re.split(r"especificar[:\s]*", texto_full, flags=re.IGNORECASE)
                        if len(partes) > 1 and partes[1].strip():
                            dados["Equipamento Social"] = partes[1].strip()
                        else:
                            dados["Equipamento Social"] = texto_full
                    else:
                        dados["Equipamento Social"] = texto_full

            # Data Alta vazia vira None
            if not dados["Data Alta"]: 
                dados["Data Alta"] = None

        return dados
    except Exception as e:
        print(f"Erro no arquivo {os.path.basename(caminho_pdf)}: {e}")
        return None
# parsers/parser_Acolhimento_terapeutico.py
# Parser para o relatório "Acolhimento Terapêutico" (CTs HUB)
# Estratégia: pdfplumber extract_tables() — sem dependência de coordenadas fixas.

import pdfplumber
import pandas as pd


def _parse_numeric_string(s: str) -> dict:
    """
    Converte a string numérica concatenada pelo pdfplumber em colunas separadas.
    Formato: 'Vaga Operacionais Ocupadas Vazias Bloqueadas Ocupação% [Média Mediana]'
    Exemplo: '40 40 29 11 0 72,5% 76,5 49,0'
    """
    if not s or not str(s).strip():
        return {}
    tokens = str(s).split()
    if len(tokens) < 6:
        return {}
    return {
        "Leitos Instalados":    tokens[0],
        "Leitos Operacionais":  tokens[1],
        "Ocupados":             tokens[2],
        "Vazios":               tokens[3],
        "Ocupação (%)":         tokens[5].replace('%', '').replace(',', '.'),
    }


def processar_camas_acolhimento(caminho_pdf: str) -> pd.DataFrame:
    """
    Lê o PDF de Acolhimento Terapêutico e retorna um DataFrame filtrado
    apenas para linhas de tipo 'HUB', com colunas padronizadas.

    Colunas retornadas:
        Unidade | Leitos Instalados | Leitos Operacionais | Ocupados | Vazios | Ocupação (%)
    """
    print(f"Iniciando processamento (Camas Acolhimento): {caminho_pdf} (Página 1)")

    with pdfplumber.open(caminho_pdf) as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()

    if not tables:
        raise ValueError(f"Nenhuma tabela encontrada no PDF: {caminho_pdf}")

    raw = tables[0]

    # --- Encontrar a linha do cabeçalho de dados (contém 'DRS' e 'Unidade') ---
    header_idx = None
    for i, row in enumerate(raw):
        if row[0] and 'DRS' in str(row[0]) and row[2] and 'Unidade' in str(row[2]):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Cabeçalho de dados não encontrado no PDF de Acolhimento Terapêutico.")

    data_rows = raw[header_idx + 1:]

    # --- Montar DataFrame bruto ---
    registros = []
    for row in data_rows:
        col0 = str(row[0] or '')
        if col0.startswith('Fonte:'):
            break

        tipo    = str(row[3] or '').strip()
        numeric = str(row[4] or '').strip()
        unidade = str(row[2] or '').replace('\n', ' ').strip() if row[2] else None

        if not tipo or not numeric:
            continue

        parsed = _parse_numeric_string(numeric)
        if not parsed:
            continue

        registros.append({
            "Unidade":    unidade if unidade else None,
            "Tipo":       tipo,
            **parsed
        })

    df = pd.DataFrame(registros)
    if df.empty:
        print("AVISO: Nenhum dado extraído do PDF de Acolhimento Terapêutico.")
        return df

    # --- Propagar nome da Unidade (a linha HUB de uma CT vem após a linha Acolhimento) ---
    df["Unidade"] = df["Unidade"].replace('', None)
    df["Unidade"] = df["Unidade"].ffill()

    print("Filtrando dados para manter apenas 'Tipo' == 'HUB'...")
    df_hub = df[df["Tipo"] == "HUB"].copy()
    print(f"Filtragem concluída. {len(df_hub)} linhas 'HUB' encontradas.")

    colunas_finais = ["Unidade", "Leitos Instalados", "Leitos Operacionais",
                      "Ocupados", "Vazios", "Ocupação (%)"]
    df_hub = df_hub[colunas_finais].reset_index(drop=True)

    print("Processamento concluído com sucesso.")
    return df_hub
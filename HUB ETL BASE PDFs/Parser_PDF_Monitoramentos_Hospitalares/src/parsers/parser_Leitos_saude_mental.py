# parsers/parser_Leitos_saude_mental.py
# Parser para o relatório "Leitos Saúde Mental" (Hospitais HUB)
# Estratégia: pdfplumber extract_tables() — muito mais robusto que tabula por coordenadas.

import pdfplumber
import pandas as pd


def _parse_numeric_string(s: str) -> dict:
    """
    Converte a string numérica concatenada pelo pdfplumber em colunas separadas.
    Formato: 'LeitosInstalados LeitosOperacionais Ocupados Vazios Bloqueados Ocupação% [Média Mediana]'
    Exemplo: '142 74 62 12 68 83,8% 17,7 14,5'
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


def processar_leitos_saude_mental(caminho_pdf: str) -> pd.DataFrame:
    """
    Lê o PDF de Leitos Saúde Mental e retorna um DataFrame filtrado
    apenas para linhas de tipo 'HUB', com colunas padronizadas.

    Colunas retornadas:
        Unidade | Leitos Instalados | Leitos Operacionais | Ocupados | Vazios | Ocupação (%)
    """
    print(f"Iniciando processamento (Leitos Saúde Mental): {caminho_pdf} (Página 1)")

    with pdfplumber.open(caminho_pdf) as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()

    if not tables:
        raise ValueError(f"Nenhuma tabela encontrada no PDF: {caminho_pdf}")

    raw = tables[0]  # Sempre há uma única tabela neste relatório

    # --- Encontrar a linha do cabeçalho de dados (contém 'DRS' e 'Unidade') ---
    header_idx = None
    for i, row in enumerate(raw):
        if row[0] and 'DRS' in str(row[0]) and row[2] and 'Unidade' in str(row[2]):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Cabeçalho de dados não encontrado no PDF de Leitos Saúde Mental.")

    data_rows = raw[header_idx + 1:]

    # --- Montar DataFrame bruto ---
    registros = []
    for row in data_rows:
        # Linha de rodapé (Fonte:) — parar
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
            "Unidade": unidade if unidade else None,
            "Tipo Leito": tipo,
            **parsed
        })

    df = pd.DataFrame(registros)
    if df.empty:
        print("AVISO: Nenhum dado extraído do PDF de Leitos Saúde Mental.")
        return df

    # --- Propagar nome da Unidade para linhas 'OUTROS LEITOS' abaixo de cada unidade ---
    df["Unidade"] = df["Unidade"].replace('', None)
    df["Unidade"] = df["Unidade"].ffill()

    print("Filtrando dados para manter apenas 'Tipo Leito' == 'HUB'...")
    df_hub = df[df["Tipo Leito"] == "HUB"].copy()
    print(f"Filtragem concluída. {len(df_hub)} linhas 'HUB' encontradas.")

    colunas_finais = ["Unidade", "Leitos Instalados", "Leitos Operacionais",
                      "Ocupados", "Vazios", "Ocupação (%)"]
    df_hub = df_hub[colunas_finais].reset_index(drop=True)

    print("Processamento concluído com sucesso.")
    return df_hub
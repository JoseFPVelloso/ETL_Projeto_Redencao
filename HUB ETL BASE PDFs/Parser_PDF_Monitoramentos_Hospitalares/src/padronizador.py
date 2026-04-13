# /src/padronizador.py

import pandas as pd

# --- 1. Definições Iniciais ---
COLUNAS_FINAIS_ORDENADAS = [
    "Tipologia", "Equipamento", "Data", "Leitos Instalados",
    "Leitos Operacionais", "Ocupação atual", "Taxa de ocupação",
    "leitos Disponiveis"
]

# A CHAVE (esquerda) deve bater EXATAMENTE com o texto que sai do parser
# (já limpo de \n e espaços extras).
# O VALOR (direita) é o nome de exibição padronizado.
MAPA_NOMES_EQUIPAMENTOS = {
    # --- Parser Leitos Saúde Mental (Hospitais) ---
    "HOSP LACAN":
        "Lacan (Grande ABC)",
    "CAISM DR DAVID CAPISTRANO DA COSTA FILHO DA AGUA FUNDA SP":   # corrigido: "DA" (era "D")
        "CAISM Dr David Capistrano (São Paulo)",
    "CAISM PHILIPPE PINEL SAO PAULO":
        "CAISM Phillippe Pinel (São Paulo)",
    "UNIDADE RECOMECO HELVETIA":                                    # adicionado: estava faltando
        "Unidade Recomeço Helvétia (São Paulo)",
    "CAIS CENTRO ATENCAO INTEGRAL SAUDE SANTA RITA PASSA QUATRO":
        "CAIS Santa Rita (Santa Rita Passo Quatro)",
    "CAIS CANTIDIO DE MOURA CAMPOS BOTUCATU":                       # mantido: pode aparecer futuramente
        "CAIS Cantidio de Moura (Botucatu)",
    "INST AMERICO BAIRRAL DE PSIQUIATRIA":
        "Americo Bairral (Baixa Mogiana)",
    "INST BEZERRA DE MENEZES ESPIRITO SANTO DO PINHAL":
        "Bezerra de Menezes (Mantiqueira)",
    "CENTRO REAB CASA BRANCA":
        "Casa Branca (Rio Pardo)",

    # --- Parser Acolhimento Terapêutico (CTs HUB) ---
    "INSTITUICAO PADRE HAROLDO":
        "Instituição Padre Haroldo (Região Metropolitana de Campinas)",
    "COMUNIDADE TERAPEUTICA SANTA CARLOTA":
        "CT Santa Carlota (Baixa Mogiana)",

    # --- Parser SEDS (CTs FASE COMUNITARIA) ---
    "CT - ASSOCIACAO RENOVAR - CENTRO DE APOIO E RECUPERACAO":
        "CT Renovar (Franco da Rocha)",
    "CT - DESAFIO JOVEM DE SANTO ANDRE":
        "CT Desafio Jovem - SA (Grande ABC)",
    "CT - CRASA":
        "CT Crasa (Mananciais)",
    "CT - PRIMEIRO PASSO":
        "CT Primeiro Passo (Baixada Santista)",
    "CT - RECANTO VIDA":
        "CT Recanto Vida (Baixada Santista)",
    "CT - REPUBLICA DA VIDA - PREV E AUX COMUNITARIO AO TOXICOMA":
        "CT República da vida (Baixada Santista)",
    "CT - NOVA JORNADA":
        "CT Nova Jornada (Vale do Jurumirim)",
    "CT - PADRE HAROLDO RAHM FEM CT FEM":                          # corrigido: nome completo do PDF
        "CT Padre Haroldo Fem (Região Metropolitana de Campinas)",
    "CT - REENCONTRO":
        "CT Reencontro (Região Metropolitana de Campinas)",
    "CT - CASA RENASCER - PIRASSUNUNGA":                            # corrigido: nome completo do PDF
        "CT Casa Renascer (Araras)",
    "CT - PENIEL":
        "CT Peniel (Rio Claro)",
    "CT - ASSOCIACAO RESGATE A VIDA DE MOGI MIRIM":                 # corrigido: nome completo do PDF
        "CT Assoc. Resgate a Vida (Baixa Mogiana)",
    "CT - ABRAPI":
        "CT Abrapi (Alto Vale do Paraíba)",
    "CT - NOVA ESPERANCA I MAS":
        "CT Nova Esperança I MAS (Alto Vale do Paraíba)",
    "CT - NOVA ESPERANCA III":
        "CT Nova Esperança III (Alto Vale do Paraíba)",
    "CT - NOVA ESPERANCA IV":
        "CT Nova Esperança IV (Alto Vale do Paraíba)",
}


def _limpar_taxa(valor):
    """Função interna para limpar a coluna 'Taxa de ocupação'."""
    try:
        s = str(valor).replace(",", ".").replace("%", "").strip()
        num = pd.to_numeric(s)
        return int(round(num))
    except (ValueError, TypeError):
        return pd.NA


def _transformar_dataframe(df_original, tipologia_nome, data_str):
    """
    Converte um DataFrame bruto do parser para o formato final solicitado.
    """
    if df_original is None or df_original.empty:
        return pd.DataFrame(columns=COLUNAS_FINAIS_ORDENADAS)

    df_transformado = pd.DataFrame()

    df_transformado["Equipamento"] = df_original["Unidade"].replace(MAPA_NOMES_EQUIPAMENTOS)
    df_transformado["Leitos Instalados"] = pd.to_numeric(
        df_original["Leitos Instalados"], errors="coerce"
    )
    df_transformado["Leitos Operacionais"] = pd.to_numeric(
        df_original["Leitos Operacionais"], errors="coerce"
    )
    df_transformado["Ocupação atual"] = pd.to_numeric(
        df_original["Ocupados"], errors="coerce"
    )
    df_transformado["leitos Disponiveis"] = pd.to_numeric(
        df_original["Vazios"], errors="coerce"
    )
    df_transformado["Taxa de ocupação"] = df_original["Ocupação (%)"].apply(_limpar_taxa)

    df_transformado["Tipologia"] = tipologia_nome
    df_transformado["Data"] = data_str

    return df_transformado[COLUNAS_FINAIS_ORDENADAS]


def gerar_tabela_final(df_leitos, df_acolhimento, df_seds, data_selecionada_str):
    """
    Recebe os 3 DataFrames brutos dos parsers e a data selecionada,
    aplica transformações e retorna o DataFrame final combinado.
    """
    print(f"\nAplicando transformações e padronização para a data: {data_selecionada_str}...")

    df_leitos_final        = _transformar_dataframe(df_leitos,       "Hospitais",              data_selecionada_str)
    df_acolhimento_final   = _transformar_dataframe(df_acolhimento,  "Acolhimento Terapêutico", data_selecionada_str)
    df_seds_final          = _transformar_dataframe(df_seds,         "SEDS",                    data_selecionada_str)

    lista_dfs_validos = [
        df for df in [df_leitos_final, df_acolhimento_final, df_seds_final]
        if not df.empty
    ]

    if not lista_dfs_validos:
        raise Exception("Processamento falhou. Nenhum dado válido foi retornado dos parsers.")

    print(f"\nJuntando {len(lista_dfs_validos)} tabelas transformadas...")

    df_final_combinado = pd.concat(lista_dfs_validos, ignore_index=True, sort=False)
    return df_final_combinado
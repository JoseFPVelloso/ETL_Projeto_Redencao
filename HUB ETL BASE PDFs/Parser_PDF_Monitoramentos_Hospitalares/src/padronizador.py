# /src/transformer.py

import pandas as pd

# --- 1. Definições Iniciais ---
COLUNAS_FINAIS_ORDENADAS = [
    "Tipologia", "Equipamento", "Data", "Leitos Instalados", 
    "Leitos Operacionais", "Ocupação atual", "Taxa de ocupação", 
    "leitos Disponiveis"
]

# A CHAVE (esquerda) é o nome bruto do parser (conforme a imagem).
# O VALOR (direita) é o nome padronizado que você quer.
MAPA_NOMES_EQUIPAMENTOS = {
    # --- Parser Leitos (Hospitais) ---
    "HOSP LACAN": "Lacan (Grande ABC)",
    "CAISM PHILIPPE PINEL SAO PAULO": "CAISM Phillippe Pinel (São Paulo)",
    "CAIS CANTIDIO DE MOURA CAMPOS BOTUCATU": "CAIS Cantidio de Moura (Botucatu)",
    "CAIS CENTRO ATENCAO INTEGRAL SAUDE SANTA RITA PASSA QUATRO": "CAIS Santa Rita (Santa Rita Passo Quatro)",
    "INST AMERICO BAIRRAL DE PSIQUIATRIA": "Americo bairral (Baixa Mogiana)",
    "INST BEZERRA DE MENEZES ESPIRITO SANTO DO PINHAL": "Bezerra de menezes (Mantiqueira)",
    "CENTRO REAB CASA BRANCA": "Casa Branca (Rio Pardo)",
    "CAISM DR DAVID CAPISTRANO DA COSTA FILHO D AGUA FUNDA SP":"CAISM Dr David Capistrano (São Paulo)",
    
    # --- Parser Acolhimento (CTs) ---
    # Chaves baseadas no CSV e no parser_Acolhimento_terapeutico.py
    "INSTITUICAO PADRE HAROLDO": "Instituição Padre Haroldo (Região Metropolitana de Campinas)",
    "COMUNIDADE TERAPEUTICA SANTA CARLOTA": "CT Santa Carlota (Baixa Mogiana)",
    
    # --- Parser SEDS (CTs) ---
    # Chaves confirmadas pela imagem (image_12a949.png)
    "CT - ASSOCIACAO RENOVAR - CENTRO DE APOIO E RECUPERACAO": "CT Renovar (Franco da Rocha)",
    "CT - DESAFIO JOVEM DE SANTO ANDRE": "CT Desafio Jovem - SA (Grande ABC)",
    "CT - CRASA": "CT Crasa (Mananciais)",
    "CT - PRIMEIRO PASSO": "CT Primeiro Passo (Baixada Santista)",
    "CT - RECANTO VIDA": "CT Recanto Vida (Baixada Santista)",
    "CT - REPUBLICA DA VIDA - PREV E AUX COMUNITARIO AO TOXICOM": "CT República da vida (Baixada Santista)",
    "CT - NOVA JORNADA": "CT Nova Jornada (Vale do Jurumim)",
    "CT - PADRE HAROLDO FEM": "CT Padre Haroldo Fem (Região Metropolitana de Campinas)",
    "CT - REENCONTRO": "CT Reencontro (Região Metropolitana de Campinas)",
    "CT - CASA RENASCER": "CT Casa Renascer (Araras)",
    "CT - PENIEL": "CT Peniel (Rio Claro)",
    "CT - ASSOC RESGATE A VIDA": "CT Assoc. Resgate a Vida (Baixa Mogiana)",
    "CT - ABRAPI": "CT Abrapi (Alto Vale do Paraíba)",
    "CT - NOVA ESPERANCA I MAS": "CT Nova Esperança I MAS (Alto Vale do Paraíba)",
    "CT - NOVA ESPERANCA III": "CT Nova Esperança III (Alto Vale do Paraíba)",
    "CT - NOVA ESPERANCA IV": "CT Nova Esperança IV (Alto Vale do Paraíba)",
    
    # Adicione mais mapeamentos aqui se necessário
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
    (Versão Corrigida)
    """
    if df_original is None or df_original.empty:
        return pd.DataFrame(columns=COLUNAS_FINAIS_ORDENADAS) 

    df_transformado = pd.DataFrame()
    
    # --- CORREÇÃO (Passo 1: Adicionar dados originais PRIMEIRO) ---
    
    # --- MUDANÇA AQUI: Aplicar o mapeamento de nomes ---
    df_transformado["Equipamento"] = df_original["Unidade"].replace(MAPA_NOMES_EQUIPAMENTOS)
    
    df_transformado["Leitos Instalados"] = df_original["Leitos Instalados"]
    df_transformado["Leitos Operacionais"] = df_original["Leitos Operacionais"]
    df_transformado["Ocupação atual"] = df_original["Ocupados"]
    df_transformado["leitos Disponiveis"] = df_original["Vazios"]
    df_transformado["Taxa de ocupação"] = df_original["Ocupação (%)"].apply(_limpar_taxa)
    
    # --- CORREÇÃO (Passo 2: Adicionar colunas novas DEPOIS) ---
    df_transformado["Tipologia"] = tipologia_nome
    df_transformado["Data"] = data_str

    # Garante a ordem correta das colunas
    return df_transformado[COLUNAS_FINAIS_ORDENADAS]


def gerar_tabela_final(df_leitos, df_acolhimento, df_seds, data_selecionada_str):
    """
    Função principal: Recebe os 3 DataFrames brutos e a DATA SELECIONADA,
    aplica a transformação e retorna o DataFrame final combinado.
    """
    print(f"\nAplicando transformações e padronização para a data: {data_selecionada_str}...")

    # --- Aplicar Transformações (Nomes Corrigidos) ---
    df_leitos_final = _transformar_dataframe(df_leitos, "Hospitais", data_selecionada_str)
    df_acolhimento_final = _transformar_dataframe(df_acolhimento, "Acolhimento Terapêutico", data_selecionada_str)
    df_seds_final = _transformar_dataframe(df_seds, "SEDS", data_selecionada_str)

    # --- Juntar Tabelas FINAIS ---
    lista_dfs_finais = [df_leitos_final, df_acolhimento_final, df_seds_final]
    lista_dfs_validos = [df for df in lista_dfs_finais if not df.empty]
    
    if not lista_dfs_validos:
        raise Exception("Processamento falhou. Nenhum dado válido foi retornado dos parsers.")
    
    print(f"\nJuntando {len(lista_dfs_validos)} tabelas transformadas...")
    
    df_final_combinado = pd.concat(lista_dfs_validos, ignore_index=True, sort=False)
    
    return df_final_combinado


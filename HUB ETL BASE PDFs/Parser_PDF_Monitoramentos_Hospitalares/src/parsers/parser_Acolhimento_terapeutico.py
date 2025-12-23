# /src/parsers/parser_Acolhimento_terapeutico.py

import tabula
import pandas as pd
import sys

# --- 1. Definições Iniciais (Constantes) ---
PAGINA_ALVO = 1

# Áreas extraídas dos seus 8 arquivos .sh
LISTA_DE_AREAS_DADOS = [
    [192.081, 183.135, 440.471, 336.8],    # Area 1 (unidades.sh)
    [198.396, 339.958, 437.314, 388.373],  # Area 2 (Tipos.sh)
    [197.344, 385.215, 440.471, 435.735],  # Area 3 (Vaga.sh)
    [194.186, 438.592, 438.366, 488.059],  # Area 4 (Operacional.sh)
    [193.134, 490.164, 438.366, 541.737],  # Area 5 (ocupado.sh)
    [193.134, 541.737, 442.576, 594.362],  # Area 6 (Vazios.sh)
    [193.134, 594.362, 435.209, 642.777],  # Area 7 (Bloqueado.sh)
    [192.081, 645.934, 440.471, 695.402]   # Area 8 (ocupacao%.sh)
]

# Correções (mantendo a que sabemos ser necessária)
CORRECOES_UNIDADES = {
    "LAR SANTA TEREZINHA DO MENINO JESUS": "LAR NOSSA SENHORA DO CARMO"
}

# Nomes das colunas (PADRONIZADOS)
NOMES_COLUNAS = [
    "Unidade", "Tipo Leito", "Leitos Instalados", "Leitos Operacionais", "Ocupados", 
    "Vazios", "Bloqueado", "Ocupação (%)"
]

# --- 2. A Função Principal ---

def processar_camas_acolhimento(arquivo_pdf):
    """
    Processa o PDF de Camas Acolhimento, extrai todos os dados,
    corrige, preenche e filtra para 'HUB'.
    """
    print(f"Iniciando processamento (Camas Acolhimento): {arquivo_pdf} (Página {PAGINA_ALVO})")
    
    lista_tabelas_extraidas = []

    try:
        # --- 3. Extração (Lógica Unificada) ---
        print(f"Extraindo {len(LISTA_DE_AREAS_DADOS)} áreas da página (Modo Stream)...")
        for i, area in enumerate(LISTA_DE_AREAS_DADOS):
            df_pedaco = tabula.read_pdf(arquivo_pdf,
                                        pages=PAGINA_ALVO,
                                        area=area,
                                        stream=True,
                                        guess=False,
                                        pandas_options={'header': None})[0]
            lista_tabelas_extraidas.append(df_pedaco)

        # --- 4. Juntar e Limpar Inicial ---
        print("Juntando todas as colunas...")
        df_final = pd.concat(lista_tabelas_extraidas, axis=1)
        
        if len(df_final.columns) != len(NOMES_COLUNAS):
            print(f"--- ERRO ---")
            print(f"O número de colunas extraídas ({len(df_final.columns)}) não bate com o esperado ({len(NOMES_COLUNAS)}).")
            return pd.DataFrame()

        df_final.columns = NOMES_COLUNAS
        df_final = df_final.dropna(how='all').reset_index(drop=True)

        # --- 5. Lógica de Correção e Preenchimento ---

        # 5.1. Correção de Nomes Quebrados
        print("Iniciando correção de nomes quebrados...")
        if CORRECOES_UNIDADES: 
            for i, row in df_final.iterrows():
                nome_unidade_atual = str(row['Unidade']).strip()
                if nome_unidade_atual in CORRECOES_UNIDADES:
                    texto_acima = str(df_final.at[i-1, 'Unidade']).strip()
                    if texto_acima == CORRECOES_UNIDADES[nome_unidade_atual]:
                        nome_completo = texto_acima + " " + nome_unidade_atual
                        df_final.at[i-1, 'Unidade'] = nome_completo
                        df_final.at[i, 'Unidade'] = pd.NA
                        print(f"Correção aplicada: Juntou '{nome_unidade_atual}'.")
        else:
            print("Nenhuma correção de nome quebrado a ser aplicada.")

        # 5.2. Preencher nomes de Unidade (Lógica bfill + ffill)
        print("\nPreenchendo nomes de unidade (Lógica bfill + ffill)...")
        df_final['Unidade'] = df_final['Unidade'].bfill(limit=1)
        df_final['Unidade'] = df_final['Unidade'].ffill()
        print("Preenchimento concluído.")


        # --- 6. Filtrar por "HUB" ---
        print(f"\nFiltrando DataFrame para manter apenas 'Tipo Leito' == 'HUB'...")
        
        df_filtrado = df_final.dropna(subset=['Tipo Leito'])
        df_filtrado = df_filtrado[df_filtrado['Tipo Leito'].astype(str).str.strip() == 'HUB'].copy()
        
        print(f"Filtragem concluída. {len(df_filtrado)} linhas 'HUB' encontradas.")

        # --- 6.5. CORREÇÃO HARDCODED (NOVA SEÇÃO) ---
        print("Aplicando correção hardcoded para 'COMUNIDADE TERAPEUTICA SANTA CARLOTA'...")

        # Encontra a(s) linha(s) HUB que foram nomeadas erradamente e corrige
        # (regex=False garante que ele troque o texto exato)
        df_filtrado['Unidade'] = df_filtrado['Unidade'].str.replace(
            'LAR MARIA DE NAZARE', 
            'COMUNIDADE TERAPEUTICA SANTA CARLOTA', 
            regex=False
        )

        # --- 7. RETORNAR o DataFrame ---
        print("Processamento concluído com sucesso.")
        return df_filtrado

    except Exception as e:
        print(f"Ocorreu um erro inesperado em 'parser_Acolhimento_terapeutico': {e}", file=sys.stderr)
        return pd.DataFrame() 

# --- 3. Bloco de Teste ---
if __name__ == "__main__":
    print("--- MODO DE TESTE (parser_Acolhimento_terapeutico.py) ---")
    
    arquivo_teste = "../../PDFS/Camas_20251031.pdf" 
    
    try:
        df_resultado = processar_camas_acolhimento(arquivo_teste)
        
        if not df_resultado.empty:
            print("\nResultado da extração de teste:")
            print(df_resultado)
            df_resultado.to_excel("../../Tabelas/TESTE_camas_acolhimento.xlsx", index=False)
            print("\nArquivo de teste salvo em: /Tabelas/TESTE_camas_acolhimento.xlsx")
        else:
            print("Extração de teste falhou ou retornou vazio.")
            
    except FileNotFoundError:
        print(f"Erro no teste: Arquivo '{arquivo_teste}' não encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado no teste: {e}")
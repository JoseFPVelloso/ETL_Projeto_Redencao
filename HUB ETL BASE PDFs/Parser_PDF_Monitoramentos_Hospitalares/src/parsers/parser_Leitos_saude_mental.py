# /src/parsers/parser_Leitos_saude_mental.py

import tabula
import pandas as pd
import sys

# --- 1. Definições Iniciais (Constantes) ---
PAGINA_ALVO = 1

# Coordenadas extraídas do arquivo 'unidade.sh'
AREA_UNIDADE = [244.706, 131.212, 439.419, 290.139]

LISTA_DE_AREAS_DADOS = [
    # Área 2 (Tipo Leito) - extraído de 'Tipo Leito.sh'
    [240.496, 289.087, 434.156, 359.604],
    
    # Área 3 (Leitos Instalados) - extraído de 'Leitos Instalados.sh'
    [238.391, 342.764, 437.314, 397.494],
    
    # Área 4 (Leitos Operacionais) - extraído de 'Leitos operacionais.sh'
    [236.286, 398.547, 441.524, 451.172],
    
    # Área 5 (Ocupados) - extraído de 'Ocupados.sh'
    [239.444, 454.329, 437.314, 509.059],
    
    # Área 6 (Vazios) - extraído de 'Vazios.sh'
    [238.391, 517.479, 440.471, 573.262],
    
    # Área 7 (Bloqueado) - extraído de 'Bloqueados.sh'
    [238.391, 570.104, 437.314, 627.992],
    
    # Área 8 (Ocupação (%)) - extraído de 'Ocupação.sh'
    [238.391, 630.097, 438.366, 686.932]
]

# Lista de fragmentos que aparecem sozinhos na linha de baixo e devem subir
FRAGMENTOS_ORFAOS = [
    "RITA PASSA QUATRO",
    "PINHAL",
    "AGUA FUNDA SP"
]

# --- 2. A Função Principal ---

def processar_leitos_saude_mental(arquivo_pdf):
    """
    Processa o PDF de Leitos de Saúde Mental, extrai os dados
    e retorna um DataFrame limpo.
    """
    print(f"Iniciando processamento (Leitos Saúde Mental): {arquivo_pdf} (Página {PAGINA_ALVO})")

    try:
        # --- 3. EXTRAÇÃO DAS UNIDADES ---
        print("Processando Área 1 (Unidades) separadamente...")
        
        df_unidades = tabula.read_pdf(arquivo_pdf,
                                      pages=PAGINA_ALVO,
                                      area=AREA_UNIDADE,
                                      stream=True,
                                      guess=False,
                                      pandas_options={'header': None})[0]
        
        df_unidades.columns = ["Unidade"]
        df_unidades = df_unidades.dropna(how='all').reset_index(drop=True)

        # 3.2. Correção de nomes (Lógica Robustecida)
        # Verifica se a linha atual é um fragmento órfão e junta com a anterior
        print("Iniciando correção de nomes quebrados das Unidades...")
        
        # Iteramos pelo índice. Começamos do 1 para poder olhar para trás (i-1)
        for i in range(1, len(df_unidades)):
            # Converte para string e remove espaços extras
            nome_unidade_atual = str(df_unidades.at[i, 'Unidade']).strip()
            
            # Se encontrar um dos fragmentos conhecidos
            if nome_unidade_atual in FRAGMENTOS_ORFAOS:
                texto_acima = str(df_unidades.at[i-1, 'Unidade']).strip()
                
                # Junta com a linha de cima
                nome_completo = texto_acima + " " + nome_unidade_atual
                
                # Aplica a correção na linha de cima
                df_unidades.at[i-1, 'Unidade'] = nome_completo
                # Marca a linha atual como nula para ser removida depois
                df_unidades.at[i, 'Unidade'] = pd.NA
                
                print(f"Correção aplicada: '{texto_acima}' + '{nome_unidade_atual}'")

        # Remove as linhas que ficaram vazias após a fusão
        df_unidades_final = df_unidades.dropna(subset=['Unidade']).reset_index(drop=True)
        print(f"Limpeza concluída. {len(df_unidades_final)} Unidades encontradas.")

        # --- 4. EXTRAÇÃO DOS DADOS ---
        print(f"\nExtraindo {len(LISTA_DE_AREAS_DADOS)} áreas de dados (sem unidades)...")
        
        lista_tabelas_dados = []
        for i, area in enumerate(LISTA_DE_AREAS_DADOS):
            # print(f"Processando Área de Dados {i+2}...") # Comentado para não poluir o log
            df_pedaco = tabula.read_pdf(arquivo_pdf,
                                        pages=PAGINA_ALVO,
                                        area=area,
                                        stream=True,
                                        guess=False,
                                        pandas_options={'header': None})[0]
            lista_tabelas_dados.append(df_pedaco)

        df_dados_bruto = pd.concat(lista_tabelas_dados, axis=1)
        nomes_colunas_dados = [
            "Tipo Leito", "Leitos Instalados", "Leitos Operacionais", "Ocupados", 
            "Vazios", "Bloqueado", "Ocupação (%)"
        ]
        
        # Garante que o número de colunas bate antes de atribuir nomes
        if len(df_dados_bruto.columns) == len(nomes_colunas_dados):
            df_dados_bruto.columns = nomes_colunas_dados
        else:
            print(f"AVISO: Número de colunas extraídas ({len(df_dados_bruto.columns)}) diferente do esperado.")
            # Atribui nomes genéricos se der erro, para não quebrar o script
            df_dados_bruto.columns = [f"Col_{i}" for i in range(len(df_dados_bruto.columns))]
        
        # 4.2. Limpeza e FILTRO
        print("Filtrando dados para manter apenas 'Tipo Leito' == 'HUB'...")
        df_dados_bruto = df_dados_bruto.dropna(how='all')
        
        # Filtra onde a coluna 'Tipo Leito' (ou a primeira coluna) é 'HUB'
        coluna_filtro = df_dados_bruto.columns[0] # Assume que é a primeira
        df_dados_filtrado = df_dados_bruto[df_dados_bruto[coluna_filtro].astype(str).str.strip() == 'HUB'].copy()
        
        df_dados_filtrado = df_dados_filtrado.reset_index(drop=True)
        print(f"Filtragem concluída. {len(df_dados_filtrado)} linhas 'HUB' encontradas.")

        # --- 5. JUNÇÃO FINAL ---
        print("\n--- Verificando Alinhamento ---")
        print(f"Total Unidades limpas: {len(df_unidades_final)}")
        print(f"Total Linhas HUB:      {len(df_dados_filtrado)}")
        
        if len(df_unidades_final) == len(df_dados_filtrado):
            print("ALINHAMENTO PERFEITO. Juntando tabelas...")
            df_final = pd.concat([df_unidades_final, df_dados_filtrado], axis=1)

            # --- 6. RETORNAR o DataFrame ---
            print("Processamento concluído com sucesso.")
            return df_final

        else:
            print("\n--- ERRO CRÍTICO DE ALINHAMENTO ---")
            print("O número de Unidades extraídas NÃO BATE com o número de linhas 'HUB'.")
            print("Verifique se há alguma unidade nova ou nome quebrando de forma diferente.")
            return pd.DataFrame() # Retorna um DataFrame vazio em caso de erro

    except Exception as e:
        print(f"Ocorreu um erro inesperado em 'parser_Leitos_saude_mental': {e}", file=sys.stderr)
        return pd.DataFrame() # Retorna um DataFrame vazio em caso de erro


# --- 3. Bloco de Teste (só executa ao rodar este arquivo diretamente) ---
if __name__ == "__main__":
    print("--- MODO DE TESTE (parser_Leitos_saude_mental.py) ---")
    
    # Caminho ajustado para teste local, altere conforme sua estrutura de pastas real
    arquivo_teste = "../../PDFS/Leitos_20251201.pdf" 
    
    try:
        df_resultado = processar_leitos_saude_mental(arquivo_teste)
        
        if not df_resultado.empty:
            print("\nResultado da extração de teste (Primeiras 10 linhas):")
            print(df_resultado.head(10))
            
            # Opcional: Salvar para conferência
            # df_resultado.to_excel("teste_saida.xlsx", index=False)
        else:
            print("Extração de teste falhou ou retornou vazio.")
            
    except FileNotFoundError:
        print(f"Erro no teste: Arquivo '{arquivo_teste}' não encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado no teste: {e}")
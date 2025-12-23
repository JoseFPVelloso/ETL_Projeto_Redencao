# /src/parsers/parser_Secretaria_do_desenvolvimento_social.py

import tabula
import pandas as pd
import sys

# --- 1. Definições Iniciais (Constantes) ---
PAGINA_ALVO = 1

# Coordenadas dos SEUS 8 arquivos .sh
AREA_UNIDADE = [198.396, 202.832, 455.206, 410.174] # Unidade.sh

LISTA_DE_AREAS_DADOS = [
    [198.396, 116.527, 455.206, 202.832], # Região de Saude.sh
    [198.396, 416.489, 454.154, 511.214], # Fase.sh
    [193.134, 508.057, 452.049, 550.157], # Vaga.sh
    [195.239, 546.999, 454.154, 582.784], # Operacionais.sh
    [197.344, 582.784, 456.259, 620.674], # Ocupadas.sh
    [197.344, 622.779, 454.154, 655.407], # Vazias.sh
    [195.239, 690.139, 457.311, 731.187]  # ocupacao%.sh
]

# Nomes das 7 colunas de DADOS
NOMES_COLUNAS_DADOS = [
    "Região de Saúde", "Fase", "Vaga", "Operacionais", 
    "Ocupadas", "Vazias", "Ocupação (%)"
]

# Nomes FINAIS para padronização (8 colunas)
NOMES_COLUNAS_FINAL = [
    "Unidade", "Tipo Leito", "Leitos Instalados", "Leitos Operacionais", "Ocupados", 
    "Vazios", "Bloqueado", "Ocupação (%)"
]


# --- 2. A Função Principal ---

def processar_desenvolvimento_social(arquivo_pdf):
    """
    Processa o PDF do Desenvolvimento Social usando as 8 COORDENADAS
    fornecidas pelo usuário (stream=True).
    """
    print(f"Iniciando processamento (Desenvolvimento Social): {arquivo_pdf} (Página {PAGINA_ALVO})")

    try:
        # --- 3. EXTRAÇÃO DAS UNIDADES (Lógica 1) ---
        print("Processando Área 1 (Unidades) separadamente...")
        
        df_unidades = tabula.read_pdf(arquivo_pdf,
                                      pages=PAGINA_ALVO,
                                      area=AREA_UNIDADE,
                                      stream=True,
                                      guess=False,
                                      pandas_options={'header': None})[0]
        
        df_unidades.columns = ["Unidade"]
        
        # 3.1. Limpeza inicial
        df_unidades = df_unidades.dropna(how='all').reset_index(drop=True)

        # 3.2. Correção de nomes (bfill + ffill)
        print("Preenchendo nomes de unidade (Lógica bfill + ffill)...")
        df_unidades['Unidade'] = df_unidades['Unidade'].bfill(limit=1)
        df_unidades['Unidade'] = df_unidades['Unidade'].ffill()

        # 3.3. Limpeza final
        df_unidades_final = df_unidades.dropna(subset=['Unidade']).reset_index(drop=True)
        print(f"Limpeza concluída. {len(df_unidades_final)} Unidades candidatas encontradas.")


        # --- 4. EXTRAÇÃO DOS DADOS (Lógica 2) ---
        print(f"\nExtraindo {len(LISTA_DE_AREAS_DADOS)} áreas de dados (sem unidades)...")
        
        lista_tabelas_dados = []
        for i, area in enumerate(LISTA_DE_AREAS_DADOS):
            print(f"Processando Área de Dados {i+2}...")
            df_pedaco = tabula.read_pdf(arquivo_pdf,
                                        pages=PAGINA_ALVO,
                                        area=area,
                                        stream=True,
                                        guess=False,
                                        pandas_options={'header': None})[0]
            lista_tabelas_dados.append(df_pedaco)

        # 4.1. Juntar colunas de dados
        df_dados_bruto = pd.concat(lista_tabelas_dados, axis=1)
        df_dados_bruto.columns = NOMES_COLUNAS_DADOS
        
        # 4.2. Limpeza e FILTRO dos Dados
        print("Filtrando dados para manter apenas 'Fase' == 'FASE COMUNITARIA'...")
        
        df_dados_bruto = df_dados_bruto.dropna(how='all')
        
        df_dados_filtrado = df_dados_bruto[df_dados_bruto['Fase'].astype(str).str.strip() == 'FASE COMUNITARIA'].copy()
        df_dados_filtrado = df_dados_filtrado.reset_index(drop=True)
        
        print(f"Filtragem concluída. {len(df_dados_filtrado)} linhas 'FASE COMUNITARIA' encontradas.")


        # --- 5. JUNÇÃO FINAL ---
        print("\n--- Verificando Alinhamento ---")
        print(f"Total Unidades limpas (com preenchimento): {len(df_unidades_final)}")
        print(f"Total Linhas 'FASE COMUNITARIA':          {len(df_dados_filtrado)}")
        
        if len(df_unidades_final) == len(df_dados_filtrado):
            print("ALINHAMENTO PERFEITO. Juntando tabelas...")
            
            df_final = pd.concat([df_unidades_final, df_dados_filtrado], axis=1)

            # --- 6. Padronização de Colunas (CORRIGIDO) ---
            print("Padronizando nomes de colunas...")
            
            # 1. Adiciona a coluna 'Bloqueado' que falta
            df_final["Bloqueado"] = 0 
            
            # 2. Renomeia explicitamente todas as colunas necessárias
            df_final = df_final.rename(columns={
                "Fase": "Tipo Leito",
                "Vaga": "Leitos Instalados",
                "Operacionais": "Leitos Operacionais",
                "Ocupadas": "Ocupados",
                "Vazias": "Vazios" # Mesmo sendo igual, renomeia para garantir
                # Unidade e Ocupação (%) já estão corretos
            })
            
            # 3. Filtra e reordena para o padrão final
            # Esta linha agora tem 100% de certeza que 'Vazios' existe.
            df_final_padronizado = df_final[NOMES_COLUNAS_FINAL]

            print("Processamento concluído com sucesso.")
            return df_final_padronizado

        else:
            print("\n--- ERRO CRÍTICO DE ALINHAMENTO ---")
            print("O número de Unidades extraídas NÃO BATE com o número de linhas 'FASE COMUNITARIA'.")
            return pd.DataFrame() 

    except Exception as e:
        print(f"Ocorreu um erro inesperado em 'parser_Secretaria_do_desenvolvimento_social': {e}", file=sys.stderr)
        return pd.DataFrame() 


# --- 3. Bloco de Teste --- # 
# Essa seção serve para testar o código sem a ferramenta de UI 
if __name__ == "__main__":
    print("--- MODO DE TESTE (parser_Secretaria_do_desenvolvimento_social.py) ---") 
    
    arquivo_teste = "Camas - Desenvolvimento Social_20251031.pdf"  # Caminho para pdf de teste
    
    try:
        df_resultado = processar_desenvolvimento_social(arquivo_teste)
        
        if not df_resultado.empty:
            print("\nResultado da extração de teste:")
            print(df_resultado.head())
            df_resultado.to_excel("../../Tabelas/TESTE_desenvolvimento_social.xlsx", index=False)
            print("\nArquivo de teste salvo em: /Tabelas/TESTE_desenvolvimento_social.xlsx")
        else:
            print("Extração de teste falhou ou retornou vazio.")
            
    except FileNotFoundError:
        print(f"Erro no teste: Arquivo '{arquivo_teste}' não encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado no teste: {e}")
"""
========================================================================
                      MÓDULO DE ETL (CORE)
========================================================================
Este arquivo contém todas as funções de processamento de dados (ETL).
Extrai (Tabula), Transforma (Pandas) e Carrega (Excel).

ATUALIZAÇÃO (Fix de Colunas Aglutinadas):
Adicionada lógica para detectar quando o PDF mescla Nome+Leitos+Involuntário
em uma única coluna (o que resulta em 4 colunas em vez de 6).
"""

import tabula
import pandas as pd
import numpy as np
import os
import re
from typing import List, Optional

def ler_pdf(caminho_arquivo: str, pagina: str) -> Optional[List[pd.DataFrame]]:
    """Lê um PDF e retorna UMA LISTA de todas as tabelas encontradas."""
    print(f"\n▶️ Iniciando extração do arquivo: {caminho_arquivo}...")
    try:
        # Lattice=True força a leitura por linhas de grade.
        # Se o PDF perdeu linhas verticais, colunas podem vir grudadas.
        tabelas = tabula.read_pdf(
            caminho_arquivo, pages=pagina, output_format="dataframe",
            lattice=True, multiple_tables=True, stream=True
        )
        if not tabelas:
            print("❌ Nenhuma tabela encontrada no PDF.")
            return None
        print(f"✅ Tabelas/Pedaços de tabelas encontrados: {len(tabelas)}")
        return tabelas
    except Exception as e:
        print(f"❌ Erro during a extração do Tabula-py: {e}")
        return None

def corrigir_colunas_aglutinadas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Função de reparo para quando o PDF mescla:
    [Estabelecimento] + [Leitos] + [Involuntario]
    Resultando em apenas 4 colunas no total ao invés de 6.
    """
    # Se temos 4 colunas, há uma grande chance de ser o erro de layout
    if len(df.columns) == 4:
        print("⚠️ DETECÇÃO: Tabela com 4 colunas (Provável aglutinação de colunas). Tentando corrigir...")
        
        # Cria um novo DataFrame para reconstruir
        novos_dados = []
        
        for index, row in df.iterrows():
            # Coluna 0: CNES (Geralmente está ok)
            cnes = row[0]
            
            # Coluna 1: Onde está a bagunça "Nome\nLeitos\nInvoluntario"
            coluna_problematica = str(row[1])
            
            # Coluna 2: Voluntário (OK)
            voluntario = row[2]
            
            # Coluna 3: Compulsório (OK)
            compulsorio = row[3]
            
            # Tenta separar a coluna problemática.
            # O padrão observado no PDF é separação por quebra de linha (\r ou \n)
            # Normaliza para \n e divide
            partes = re.split(r'[\n\r]+', coluna_problematica)
            partes = [p.strip() for p in partes if p.strip()] # Remove vazios
            
            nome_estab = np.nan
            leitos = 0
            involuntario = 0
            
            if len(partes) >= 3:
                # Heurística: Os dois últimos são números (Leitos e Involuntário)
                # O resto (início) é o nome do hospital
                try:
                    involuntario = partes[-1]
                    leitos = partes[-2]
                    nome_estab = " ".join(partes[:-2]) # Junta o resto caso o nome tenha sido quebrado
                except:
                    nome_estab = coluna_problematica # Fallback
            elif len(partes) == 1:
                # Caso onde talvez só tenha o nome ou só numero (cabeçalho as vezes)
                nome_estab = partes[0]
            else:
                nome_estab = coluna_problematica

            novos_dados.append([cnes, nome_estab, leitos, involuntario, voluntario, compulsorio])
            
        # Retorna o DF reconstruído com 6 colunas
        return pd.DataFrame(novos_dados)
    
    return df

def normalizar_cabecalho(tabela_bruta: pd.DataFrame) -> pd.DataFrame:
    """Detecta e corrige o cabeçalho lido pelo Tabula."""
    primeiro_item_cabecalho = str(tabela_bruta.columns[0])
    # Verifica se o cabeçalho é um número (CNES), indicando que o header foi engolido como dado
    eh_numero = not pd.isna(pd.to_numeric(primeiro_item_cabecalho, errors='coerce'))
    
    if eh_numero:
        print("...DETECÇÃO: Tabula usou dados como cabeçalho. Resgatando...")
        primeira_linha_dados = list(tabela_bruta.columns)
        num_colunas = len(primeira_linha_dados)
        df_primeira_linha = pd.DataFrame([primeira_linha_dados], columns=range(num_colunas))
        df_resto = tabela_bruta.copy()
        df_resto.columns = range(num_colunas)
        return pd.concat([df_primeira_linha, df_resto], ignore_index=True)
    else:
        # Mesmo que não seja número, as vezes o cabeçalho bagunçado atrapalha.
        # Vamos padronizar para indices numéricos para facilitar a manipulação
        tabela_bruta.columns = range(len(tabela_bruta.columns))
        return tabela_bruta

def preparar_tabela(tabela_bruta: pd.DataFrame, nomes_colunas: list, 
                      mapeamento_nomes: dict, cols_internados: list) -> Optional[pd.DataFrame]:
    """
    Executa a limpeza completa de uma única tabela bruta.
    """
    print("...Processando um pedaço de tabela...")
    
    # 1. Traz o cabeçalho para dentro dos dados se necessário
    df_normalizada = normalizar_cabecalho(tabela_bruta)
    
    # 2. Tenta corrigir a aglutinação específica (Fix Novo)
    df_normalizada = corrigir_colunas_aglutinadas(df_normalizada)
    
    num_colunas_lidas = len(df_normalizada.columns)
    num_colunas_esperado = len(nomes_colunas)

    # 3. Ajusta colunas baseado na quantidade esperada
    if num_colunas_lidas == num_colunas_esperado:
        df_normalizada.columns = nomes_colunas
    elif num_colunas_lidas > num_colunas_esperado:
        print(f"⚠️ Aviso: Tabela lida com {num_colunas_lidas} colunas. Cortando para {num_colunas_esperado}.")
        df_normalizada = df_normalizada.iloc[:, :num_colunas_esperado]
        df_normalizada.columns = nomes_colunas
    elif num_colunas_lidas < num_colunas_esperado:
        # Esse era o ponto que causava o erro anterior (Preenchimento cego à esquerda)
        colunas_faltantes = num_colunas_esperado - num_colunas_lidas
        print(f"⚠️ Aviso Crítico: Tabela com {num_colunas_lidas} colunas (Esperado {num_colunas_esperado}). Tentando preencher...")
        
        # Tenta preencher à direita agora, assumindo que CNES (col 0) está certo
        # Mas mantemos a lógica original para não quebrar casos antigos que funcionavam assim,
        # pois o fix 'corrigir_colunas_aglutinadas' deve ter resolvido o caso principal.
        df_preenchimento = pd.DataFrame(np.nan, index=df_normalizada.index, columns=nomes_colunas[:colunas_faltantes])
        df_normalizada.columns = nomes_colunas[colunas_faltantes:]
        df_normalizada = pd.concat([df_preenchimento, df_normalizada], axis=1)
    else:
        return None
        
    # 4. Limpezas padrão
    df_normalizada['CNES'] = pd.to_numeric(df_normalizada['CNES'], errors='coerce')
    df_limpa = df_normalizada.dropna(subset=['CNES']).copy()
    
    print(f"...Linhas de lixo (Total, etc.) removidas. {len(df_limpa)} linhas de dados restantes.")
    
    if 'Estabelecimento' in df_limpa.columns:
        print("...Normalizando e traduzindo nomes de hospitais...")
        nomes_sujos = df_limpa['Estabelecimento'].astype(str)
        # Remove quebras de linha que possam ter sobrado dentro do nome
        nomes_limpos = nomes_sujos.str.replace(r'[\r\n]+', ' ', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
        df_limpa['Estabelecimento'] = nomes_limpos.map(mapeamento_nomes).fillna(nomes_limpos)
    else:
        print("⚠️ Aviso: Coluna 'Estabelecimento' não encontrada para tradução.")
    
    colunas_para_converter = ['Leitos_Instalados'] + cols_internados
    for col in colunas_para_converter:
        # Remove caracteres não numéricos antes de converter
        df_limpa[col] = df_limpa[col].astype(str).str.replace(r'[^\d]', '', regex=True)
        df_limpa[col] = pd.to_numeric(df_limpa[col], errors='coerce').fillna(0)
        
    df_limpa['CNES'] = df_limpa['CNES'].astype(int)
        
    return df_limpa

def agregar_dados(df_combinado: pd.DataFrame, cols_internados: list) -> pd.DataFrame:
    """Agrupa os dados por hospital e aplica a lógica de soma."""
    print("🔄 Agregando dados por hospital...")
    
    df_combinado = df_combinado.dropna(subset=['Estabelecimento'])
    df_combinado['Internados'] = df_combinado[cols_internados].sum(axis=1)
    
    regras_agg = {
        'Leitos_Instalados': 'first', # Pega o primeiro valor encontrado para leitos
        'Internados': 'sum'           # Soma os internados
    }
    
    df_agregado = df_combinado.groupby('Estabelecimento').agg(regras_agg).reset_index()
    
    print("✅ Dados agregados.")
    return df_agregado

def formatar_saida(df_agregado: pd.DataFrame, data_input: str) -> pd.DataFrame:
    """Adiciona colunas calculadas e formata a saída final."""
    print("🔄 Formatando a tabela de saída...")
    
    df_final = df_agregado.rename(columns={
        'Estabelecimento': 'Serviço',
        'Leitos_Instalados': 'Leitos'
    })
    
    df_final['Data'] = data_input
    
    df_final['Ocupação'] = np.where(
        df_final['Leitos'] > 0,
        df_final['Internados'] / df_final['Leitos'],
        np.nan
    )
    
    df_final['Ocupação'] = df_final['Ocupação'].apply(
        lambda x: f"{x:.0%}" if pd.notna(x) else "#DIV/0!"
    )

    ordem_final_colunas = ['Serviço', 'Data', 'Leitos', 'Internados', 'Ocupação']
    
    return df_final[ordem_final_colunas]

def salvar_excel(df: pd.DataFrame, caminho_saida: str) -> None:
    """
    Salva o DataFrame final em um arquivo Excel.
    """
    try:
        pasta_saida = os.path.dirname(caminho_saida)
        if pasta_saida and not os.path.exists(pasta_saida):
            os.makedirs(pasta_saida)
            print(f" pasta de saída '{pasta_saida}' criada.")

        df.to_excel(caminho_saida, index=False)
        print(f"\n✨ SUCESSO! Os dados foram salvos em: {caminho_saida}")
        print("A tabela está pronta para ser copiada.")
    except Exception as e:
        print(f"❌ Erro ao salvar o arquivo Excel: {e}")
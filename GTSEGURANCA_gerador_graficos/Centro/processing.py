import pandas as pd
import numpy as np
import os
import re
import json
from datetime import datetime, timedelta
from config import OUTPUT_FOLDER, CONFIG_FOLDER

def load_and_standardize_data(filepath):
    """
    Carrega o arquivo CSV/Excel, padroniza nomes de colunas, 
    converte datas, aplica correções de homônimos e normaliza os períodos.
    Retorna: (DataFrame processado, Lista de ruas únicas)
    """
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    # Padronização de colunas
    df.columns = [c.strip() for c in df.columns]
    
    # Validação
    required_cols = ['Data', 'Logradouro', 'Período', 'Qtd. pessoas']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes no arquivo: {', '.join(missing)}")

    # --- CORREÇÃO DE HOMÔNIMOS ---
    # Tenta carregar o JSON de correções da pasta Config
    try:
        json_path = os.path.join(CONFIG_FOLDER, 'correcoes_ruas.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                correcoes = json.load(f)
            # Aplica as correções na coluna Logradouro
            df['Logradouro'] = df['Logradouro'].replace(correcoes)
    except Exception as e:
        print(f"Aviso: Não foi possível carregar/aplicar correções de homônimos: {e}")

    # Tratamento de Data
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.dropna(subset=['Data'])

    # Tratamento Numérico (Garante que Qtd. pessoas seja número)
    df['Qtd. pessoas'] = pd.to_numeric(df['Qtd. pessoas'], errors='coerce').fillna(0)

    # Normalização de Períodos (Inteligente)
    def normalize_period_text(val):
        if pd.isna(val): return "Desconhecido"
        val_str = str(val).lower().strip()
        
        if 'madrugada' in val_str: return 'Madrugada'
        if 'manhã' in val_str or 'manha' in val_str: return 'Manhã'
        if 'tarde' in val_str: return 'Tarde'
        if 'noite' in val_str: return 'Noite'
        
        return str(val)

    df['Periodo_Norm'] = df['Período'].apply(normalize_period_text)

    # Lista de ruas
    all_streets = sorted(df['Logradouro'].astype(str).unique())
    
    return df, all_streets

def parse_date(date_str):
    """Converte string dd/mm/aaaa para datetime."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        return None

# Em processing.py

def generate_top15_excel(df_filtered, days_interval, end_date_str):
    """Gera o relatório Excel Top 15."""
    data_fim = parse_date(end_date_str)
    if not data_fim:
        raise ValueError("Data final do Top 15 inválida.")

    # Intervalo inclusivo (dias - 1)
    data_inicio = data_fim - timedelta(days=days_interval - 1)
    
    # Filtrar por data
    mask = (df_filtered['Data'] >= data_inicio) & (df_filtered['Data'] <= data_fim)
    df = df_filtered.loc[mask].copy()
    
    if df.empty:
        return False, "Sem dados no período selecionado."

    # --- Lógica de Agregação ---
    # Pivotar
    df_pivot = df.pivot_table(
        index=['Logradouro', 'Data'], 
        columns='Periodo_Norm', 
        values='Qtd. pessoas', 
        aggfunc='sum', 
        fill_value=0
    ).reset_index()

    # Garantir colunas e Forçar Ordem
    periodos_ordem = ['Madrugada', 'Manhã', 'Tarde', 'Noite']
    for p in periodos_ordem:
        if p not in df_pivot.columns: df_pivot[p] = 0

    # Médias (Agrupando por Logradouro -> Média dos dias)
    stats = df_pivot.groupby('Logradouro')[periodos_ordem].mean().reset_index()
    
    # ARREDONDAMENTO: Converte para inteiro
    stats[periodos_ordem] = stats[periodos_ordem].round(0).astype(int)
    
    # Calcular Média por Período
    stats['Média pessoas'] = stats[periodos_ordem].mean(axis=1).round(0).astype(int)
    
    # Soma total absoluta para ranking
    total_counts = df.groupby('Logradouro')['Qtd. pessoas'].sum().reset_index().rename(columns={'Qtd. pessoas': 'Soma pessoas'})
    stats = stats.merge(total_counts, on='Logradouro')

    # Top 15 - Ordenação
    top15 = stats.sort_values(by='Soma pessoas', ascending=False).head(15).reset_index(drop=True)
    top15.index = top15.index + 1

    # Reordenar colunas
    cols_base = ['Logradouro', 'Soma pessoas', 'Média pessoas']
    cols_final = cols_base + [p for p in periodos_ordem if p in top15.columns]
    top15 = top15[cols_final]

    # Aglomerações
    df_aglo = df[df['Qtd. pessoas'] > 10].copy()
    if not df_aglo.empty:
        aglo_stats = df_aglo.groupby(['Logradouro', 'Periodo_Norm']).size().unstack(fill_value=0)
        for p in periodos_ordem:
            if p not in aglo_stats.columns: aglo_stats[p] = 0
        
        aglo_stats = aglo_stats[periodos_ordem]
        
        aglo_stats['Total Aglomerações'] = aglo_stats.sum(axis=1)
        aglo_stats = aglo_stats.reset_index()
        top15_aglo = top15[['Logradouro']].merge(aglo_stats, on='Logradouro', how='left').fillna(0)
    else:
        top15_aglo = top15[['Logradouro']].copy()
        top15_aglo['Total Aglomerações'] = 0
        for c in periodos_ordem: top15_aglo[c] = 0

    # Converter colunas de aglomeração para int
    cols_num_aglo = ['Total Aglomerações'] + periodos_ordem
    top15_aglo[cols_num_aglo] = top15_aglo[cols_num_aglo].astype(int)

    # Renomear para visualização final
    rename_map_media = {
        'Madrugada': 'Média Madrugada', 'Manhã': 'Média Manhã', 
        'Tarde': 'Média Tarde', 'Noite': 'Média Noite'
    }
    top15 = top15.rename(columns=rename_map_media)
    
    rename_map_aglo = {
        'Madrugada': 'Qtd Madrugada', 'Manhã': 'Qtd Manhã', 
        'Tarde': 'Qtd Tarde', 'Noite': 'Qtd Noite'
    }
    top15_aglo = top15_aglo.rename(columns=rename_map_aglo)

    # --- Salvar Arquivo ---
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # 1. NOME ATUALIZADO (DIÁRIO)
    nome_arquivo = f"Ranking_Diario_{datetime.now().strftime('%Y%m%d')}_Centro.xlsx"
    filepath = os.path.join(OUTPUT_FOLDER, nome_arquivo)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        top15.to_excel(writer, sheet_name='Top 15 Média', index_label='#')
        top15_aglo.to_excel(writer, sheet_name='Top 15 Qtd Aglo', index_label='#')
        
        for idx, row in top15.iterrows():
            rua = row['Logradouro']
            df_rua = df[df['Logradouro'] == rua].copy()
            
            # Pivot para abas individuais
            df_rua_pivot = df_rua.pivot_table(index='Data', columns='Periodo_Norm', values='Qtd. pessoas', aggfunc='sum').fillna(0)
            
            # Garante colunas e ordem
            for p in periodos_ordem:
                if p not in df_rua_pivot.columns: df_rua_pivot[p] = 0
            
            # Ordena e Converte para Int
            df_rua_pivot = df_rua_pivot[periodos_ordem].astype(int)

            # --- AQUI ESTÁ A MUDANÇA ---
            # Reset index para transformar Data em coluna
            df_rua_pivot = df_rua_pivot.reset_index()

            # FORMATAÇÃO OBRIGATÓRIA: Transforma em string "DD/MM/AAAA"
            if 'Data' in df_rua_pivot.columns:
                df_rua_pivot['Data'] = df_rua_pivot['Data'].dt.strftime('%d/%m/%Y')
            
            # Insere o Nome da Rua como primeira coluna
            df_rua_pivot.insert(0, 'Logradouro', rua)
            # ---------------------------
            
            sheet_name = f"{idx}_{rua[:20]}"
            clean_sheet_name = re.sub(r'[\\/*?:\[\]]', '', sheet_name)[:31]
            df_rua_pivot.to_excel(writer, sheet_name=clean_sheet_name, index=False)
            
    return True, filepath

def generate_monthly_excel(df_filtered, start_date_str, end_date_str):
    """Gera o relatório Excel Mensal."""
    data_inicio = parse_date(start_date_str)
    data_fim = parse_date(end_date_str)
    
    if not data_inicio or not data_fim:
        raise ValueError("Datas do relatório mensal inválidas.")

    mask = (df_filtered['Data'] >= data_inicio) & (df_filtered['Data'] <= data_fim)
    df = df_filtered.loc[mask].copy()

    if df.empty:
        return False, "Sem dados no período mensal selecionado."

    # Preparação
    meses_pt = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho',
               7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
    df['Mes_Num'] = df['Data'].dt.month
    df['Mês'] = df['Mes_Num'].map(meses_pt)
    df['Ano'] = df['Data'].dt.year

    # Função interna auxiliar
    def get_stats(dataframe, periodo_nome=None):
        df_p = dataframe[dataframe['Periodo_Norm'] == periodo_nome].copy() if periodo_nome else dataframe.copy()
        if df_p.empty: return pd.DataFrame()

        grouped = df_p.groupby(['Ano', 'Mes_Num', 'Mês'])
        stats = grouped.agg(Qtd_Dias=('Data', 'nunique'), Soma_Pessoas=('Qtd. pessoas', 'sum')).reset_index()
        
        # ARREDONDAMENTO
        stats['Média Pessoas'] = (stats['Soma_Pessoas'] / stats['Qtd_Dias']).round(0).astype(int)
        
        df_aglo = df_p[df_p['Qtd. pessoas'] > 10]
        if not df_aglo.empty:
            aglo_grouped = df_aglo.groupby(['Ano', 'Mes_Num', 'Mês']).agg(
                Qtd_Aglomeracoes=('Qtd. pessoas', 'count'), Soma_Pessoas_Aglo=('Qtd. pessoas', 'sum')
            ).reset_index()
            final = stats.merge(aglo_grouped, on=['Ano', 'Mes_Num', 'Mês'], how='left').fillna(0)
            
            # ARREDONDAMENTO
            final['Média Pessoas Aglomerações'] = (final['Soma_Pessoas_Aglo'] / final['Qtd_Aglomeracoes']).fillna(0).round(0).astype(int)
            
            # Garante inteiros
            final['Qtd_Aglomeracoes'] = final['Qtd_Aglomeracoes'].astype(int)
            final['Soma_Pessoas_Aglo'] = final['Soma_Pessoas_Aglo'].astype(int)
        else:
            final = stats.copy()
            for c in ['Qtd_Aglomeracoes','Soma_Pessoas_Aglo','Média Pessoas Aglomerações']: final[c] = 0

        final = final.drop(columns=['Ano', 'Mes_Num'])
        cols_map = {
            'Qtd_Dias': 'Qtd. Dias', 'Soma_Pessoas': 'Soma Pessoas', 'Média Pessoas': 'Média Pessoas',
            'Qtd_Aglomeracoes': 'Qtd. Aglomerações', 'Soma_Pessoas_Aglo': 'Soma Pessoas Aglomerações',
            'Média Pessoas Aglomerações': 'Média Pessoas Aglomerações'
        }
        return final.rename(columns=cols_map)

    # --- Salvar Arquivo ---
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # 2. NOME ATUALIZADO (MENSAL)
    # Inclui o período no nome para evitar confusão sobre quais meses estão no relatório
    nome_arquivo = f"Ranking_Mensal_{data_inicio.strftime('%Y%m%d')}_a_{data_fim.strftime('%Y%m%d')}_Centro.xlsx"
    filepath = os.path.join(OUTPUT_FOLDER, nome_arquivo)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        get_stats(df).to_excel(writer, sheet_name='Geral', index=False)
        
        # Ordem cronológica correta
        periodos = ['Madrugada', 'Manhã', 'Tarde', 'Noite']
        prefixes = {'Madrugada': '05h - ', 'Manhã': '10h - ', 'Tarde': '15h - ', 'Noite': '20h - '}
        media_por_periodo_dict = {}

        for p in periodos:
            df_p = get_stats(df, p)
            if not df_p.empty:
                sheet_title = f"{prefixes.get(p, '')}{p}"
                df_p.to_excel(writer, sheet_name=sheet_title, index=False)
                media_por_periodo_dict[p] = df_p.set_index('Mês')['Média Pessoas']

        if media_por_periodo_dict:
            df_grafico = pd.DataFrame(media_por_periodo_dict)
            ordem_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            df_grafico = df_grafico.reindex(ordem_meses).dropna(how='all')
            # Garante ordem das colunas no gráfico
            cols_grafico = [c for c in periodos if c in df_grafico.columns]
            df_grafico = df_grafico[cols_grafico]
            df_grafico.to_excel(writer, sheet_name='Para Gráfico', index_label='Mês')
            
    return True, filepath
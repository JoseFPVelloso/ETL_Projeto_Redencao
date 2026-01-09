import pandas as pd
import numpy as np
import os
import re
from datetime import datetime, timedelta
from config import OUTPUT_FOLDER

def load_and_standardize_data(filepath):
    """
    Carrega o arquivo CSV/Excel, padroniza nomes de colunas, 
    converte datas e normaliza os períodos.
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

    # Tratamento de Data
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.dropna(subset=['Data'])

    # Normalização de Períodos
    periodo_map = {
        '05h - Madrugada': 'Madrugada', '10h - Manhã': 'Manhã',
        '15h - Tarde': 'Tarde', '20h - Noite': 'Noite'
    }
    df['Periodo_Norm'] = df['Período'].map(periodo_map).fillna(df['Período'])

    # Lista de ruas
    all_streets = sorted(df['Logradouro'].astype(str).unique())
    
    return df, all_streets

def parse_date(date_str):
    """Converte string dd/mm/aaaa para datetime."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        return None

def generate_top15_excel(df_filtered, days_interval, end_date_str):
    """Gera o relatório Excel Top 15."""
    data_fim = parse_date(end_date_str)
    if not data_fim:
        raise ValueError("Data final do Top 15 inválida.")

    # CORREÇÃO: Subtraímos (dias - 1) para pegar o intervalo exato inclusivo.
    # Ex: Se são 15 dias terminando dia 06, queremos do dia 23 ao 06 (15 dias).
    # Antes (dias=15) resultava dia 22 (16 dias totais).
    data_inicio = data_fim - timedelta(days=days_interval - 1)
    
    # Filtrar por data
    mask = (df_filtered['Data'] >= data_inicio) & (df_filtered['Data'] <= data_fim)
    df = df_filtered.loc[mask].copy()
    
    if df.empty:
        return False, "Sem dados no período selecionado."

    # --- Lógica de Agregação ---
    # Pivotar
    df_pivot = df.pivot_table(
        index=['Logradouro', 'Data'], columns='Periodo_Norm', values='Qtd. pessoas', aggfunc='sum', fill_value=0
    ).reset_index()

    # Garantir colunas
    for p in ['Madrugada', 'Manhã', 'Tarde', 'Noite']:
        if p not in df_pivot.columns: df_pivot[p] = 0

    # Médias
    stats = df_pivot.groupby('Logradouro').agg({
        'Madrugada': 'mean', 'Manhã': 'mean', 'Tarde': 'mean', 'Noite': 'mean'
    }).reset_index()
    
    stats['Média pessoas'] = stats['Madrugada'] + stats['Manhã'] + stats['Tarde'] + stats['Noite']
    
    # Soma total para ranking
    total_counts = df.groupby('Logradouro')['Qtd. pessoas'].sum().reset_index().rename(columns={'Qtd. pessoas': 'Soma pessoas'})
    stats = stats.merge(total_counts, on='Logradouro')

    # Top 15
    top15 = stats.sort_values(by='Soma pessoas', ascending=False).head(15).reset_index(drop=True)
    top15.index = top15.index + 1

    # Aglomerações
    df_aglo = df[df['Qtd. pessoas'] > 10].copy()
    if not df_aglo.empty:
        aglo_stats = df_aglo.groupby(['Logradouro', 'Periodo_Norm']).size().unstack(fill_value=0)
        for p in ['Madrugada', 'Manhã', 'Tarde', 'Noite']:
            if p not in aglo_stats.columns: aglo_stats[p] = 0
        aglo_stats['Total Aglomerações'] = aglo_stats.sum(axis=1)
        aglo_stats = aglo_stats.reset_index()
        top15_aglo = top15[['Logradouro']].merge(aglo_stats, on='Logradouro', how='left').fillna(0)
    else:
        top15_aglo = top15[['Logradouro']].copy()
        for c in ['Total Aglomerações','Madrugada','Manhã','Tarde','Noite']: top15_aglo[c] = 0

    # Renomear
    top15 = top15.rename(columns={'Madrugada': 'Média Madrugada', 'Manhã': 'Média Manhã', 'Tarde': 'Média Tarde', 'Noite': 'Média Noite'})
    cols_aglo = {'Madrugada': 'Qtd Madrugada', 'Manhã': 'Qtd Manhã', 'Tarde': 'Qtd Tarde', 'Noite': 'Qtd Noite'}
    top15_aglo = top15_aglo.rename(columns=cols_aglo)

    # --- Salvar Arquivo ---
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    nome_arquivo = f"top15_media_diaria_pessoas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    filepath = os.path.join(OUTPUT_FOLDER, nome_arquivo)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        top15.to_excel(writer, sheet_name='Top 15 Média', index_label='#')
        top15_aglo.to_excel(writer, sheet_name='Top 15 Qtd Aglo', index_label='#')
        
        for idx, row in top15.iterrows():
            rua = row['Logradouro']
            df_rua = df[df['Logradouro'] == rua].copy()
            df_rua_pivot = df_rua.pivot_table(index='Data', columns='Periodo_Norm', values='Qtd. pessoas', aggfunc='sum').fillna(0)
            sheet_name = f"{idx}_{rua[:20]}"
            clean_sheet_name = re.sub(r'[\\/*?:\[\]]', '', sheet_name)[:31]
            df_rua_pivot.to_excel(writer, sheet_name=clean_sheet_name)
            
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
        stats['Média Pessoas'] = round(stats['Soma_Pessoas'] / stats['Qtd_Dias'], 2)
        
        df_aglo = df_p[df_p['Qtd. pessoas'] > 10]
        if not df_aglo.empty:
            aglo_grouped = df_aglo.groupby(['Ano', 'Mes_Num', 'Mês']).agg(
                Qtd_Aglomeracoes=('Qtd. pessoas', 'count'), Soma_Pessoas_Aglo=('Qtd. pessoas', 'sum')
            ).reset_index()
            final = stats.merge(aglo_grouped, on=['Ano', 'Mes_Num', 'Mês'], how='left').fillna(0)
            final['Média Pessoas Aglomerações'] = round(final['Soma_Pessoas_Aglo'] / final['Qtd_Aglomeracoes'], 2).fillna(0)
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
    nome_arquivo = f"media_pessoas_aglomeracoes_{data_inicio.strftime('%Y%m%d')}_a_{data_fim.strftime('%Y%m%d')}_{datetime.now().strftime('%H%M%S')}.xlsx"
    filepath = os.path.join(OUTPUT_FOLDER, nome_arquivo)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        get_stats(df).to_excel(writer, sheet_name='Geral', index=False)
        
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
            df_grafico.to_excel(writer, sheet_name='Para Gráfico', index_label='Mês')
            
    return True, filepath
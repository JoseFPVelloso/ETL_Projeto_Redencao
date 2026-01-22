import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
import config

class AnalisadorDados:
    def __init__(self):
        self.df = None
        self.caminho_arquivo = ""
        self.mapa_regioes = {}
        self.regioes_disponiveis = []

    def carregar_mapa_regioes(self):
        """Carrega o arquivo regioes.xlsx"""
        if not os.path.exists(config.ARQUIVO_REGIOES):
            return False, "Arquivo 'regioes.xlsx' não encontrado."
        
        try:
            df_map = pd.read_excel(config.ARQUIVO_REGIOES)
            col_log = next((c for c in df_map.columns if 'Padrão' in c or 'Logradouro' in c), None)
            col_reg = next((c for c in df_map.columns if 'Região' in c or 'Regiao' in c), None)
            
            if not col_log or not col_reg:
                return False, "Colunas 'Padrão' e 'Região' necessárias no arquivo de mapa."

            df_map[col_log] = df_map[col_log].astype(str).str.strip()
            df_map[col_reg] = df_map[col_reg].astype(str).str.strip()
            
            self.mapa_regioes = dict(zip(df_map[col_log], df_map[col_reg]))
            return True, f"Mapa carregado: {len(self.mapa_regioes)} locais."
            
        except Exception as e:
            return False, f"Erro no mapa: {str(e)}"

    def carregar_dados(self, caminho):
        try:
            self.df = pd.read_excel(caminho)
            self.caminho_arquivo = caminho

            # Padronização
            self.df.columns = self.df.columns.str.strip()
            mapa_cols = {'Região': 'Regiao_Original', 'Regiao': 'Regiao_Original',
                         'Período': 'Periodo', 'Logradouro': 'Logradouro', 
                         'Quantidade': 'Quantidade', 'Data': 'Data'}
            self.df.rename(columns=mapa_cols, inplace=True)
            
            if 'Logradouro' in self.df.columns:
                self.df['Logradouro'] = self.df['Logradouro'].astype(str).str.strip()

            # Aplicação do Mapa
            if self.mapa_regioes:
                self.df['Regiao'] = self.df['Logradouro'].map(self.mapa_regioes).fillna('Outros')
            else:
                if 'Regiao_Original' in self.df.columns: self.df['Regiao'] = self.df['Regiao_Original']
                elif 'Logradouro' in self.df.columns: self.df['Regiao'] = self.df['Logradouro'].str.split(' - ', n=1).str[0].str.strip()
                else: self.df['Regiao'] = 'Desconhecido'

            # Tratamentos Finais
            self.df['Quantidade'] = pd.to_numeric(self.df['Quantidade'], errors='coerce').fillna(0)
            self.df['Data'] = pd.to_datetime(self.df['Data'], errors='coerce')
            self.df = self.df.dropna(subset=['Data'])
            if 'Periodo' in self.df.columns: self.df['Periodo'] = self.df['Periodo'].astype(str).str.strip()

            # Lista Única para UI (Ordenada, com Outros no fim)
            self.regioes_disponiveis = sorted(self.df['Regiao'].unique().tolist())
            if "Outros" in self.regioes_disponiveis:
                self.regioes_disponiveis.remove("Outros")
                self.regioes_disponiveis.append("Outros")

            return True, f"Base carregada: {len(self.df)} registros."
        except Exception as e:
            return False, str(e)

    def obter_logradouros_da_regiao(self, regiao):
        """Retorna lista de logradouros presentes na base para uma região específica"""
        if self.df is None or regiao not in self.df['Regiao'].unique():
            return []
        
        # Filtra e pega valores únicos, ordenados
        logs = self.df[self.df['Regiao'] == regiao]['Logradouro'].unique()
        return sorted(logs)

    def _sanitizar_nome_aba(self, nome, nomes_existentes):
        nome_limpo = str(nome).replace('/', '-').replace('\\', '-').replace(':', '')
        nome_limpo = re.sub(r'[?*\[\]]', '', nome_limpo)[:31]
        if not nome_limpo: nome_limpo = "Sheet"
        
        nome_final = nome_limpo
        c = 1
        while nome_final.lower() in [n.lower() for n in nomes_existentes]:
            sufixo = f"_{c}"
            nome_final = f"{nome_limpo[:31-len(sufixo)]}{sufixo}"
            c += 1
        nomes_existentes.append(nome_final)
        return nome_final

    def gerar_todos_relatorios(self, params_diario, params_mensal, regioes_selecionadas):
        msgs = []
        if not regioes_selecionadas: return False, "Nenhuma região selecionada."
            
        df_filter = self.df[self.df['Regiao'].isin(regioes_selecionadas)].copy()
        if df_filter.empty: return False, "Sem dados para as regiões selecionadas."

        # 1. DIÁRIO
        try:
            df_d = df_filter[(df_filter['Data'] >= params_diario['inicio']) & (df_filter['Data'] <= params_diario['fim'])].copy()
            if not df_d.empty:
                path = os.path.join(config.OUTPUT_FOLDER, f"1_Ranking_Diario_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")
                self._processar_ranking_excel(df_d, path, params_diario['inicio'], params_diario['fim'])
                msgs.append("✓ Ranking Diário OK")
            else: msgs.append("⚠️ Diário vazio")
        except Exception as e: msgs.append(f"❌ Erro Diário: {e}")

        # 2. MENSAL
        try:
            df_m = df_filter[(df_filter['Data'] >= params_mensal['inicio']) & (df_filter['Data'] <= params_mensal['fim'])].copy()
            if not df_m.empty:
                path = os.path.join(config.OUTPUT_FOLDER, f"2_Evolucao_Mensal_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")
                self._processar_mensal_excel(df_m, path)
                msgs.append("✓ Evolução Mensal OK")
            else: msgs.append("⚠️ Mensal vazio")
        except Exception as e: msgs.append(f"❌ Erro Mensal: {e}")

        return True, "\n".join(msgs)

    def _processar_ranking_excel(self, df, caminho, d_ini, d_fim):
        # Lógica idêntica ao anterior (Ranking + Abas Pivot)
        dias = (d_fim - d_ini).days + 1
        total_p = dias * 2
        abas = []
        with pd.ExcelWriter(caminho, engine='openpyxl') as writer:
            for reg in df.groupby('Regiao')['Quantidade'].sum().sort_values(ascending=False).index:
                df_reg = df[df['Regiao'] == reg]
                
                # Resumo
                df_rank = df_reg.groupby('Logradouro').agg({'Quantidade':'sum'}).reset_index()
                df_rank['Média'] = df_rank['Quantidade'] / total_p
                # Turnos
                detalhes = []
                for l in df_rank['Logradouro']:
                    dl = df_reg[df_reg['Logradouro']==l]
                    sm = dl[dl['Periodo'].str.contains('Manhã|10h',case=False,na=False)]['Quantidade'].sum()
                    st = dl[dl['Periodo'].str.contains('Tarde|15h',case=False,na=False)]['Quantidade'].sum()
                    detalhes.append({'Manhã':sm/dias, 'Tarde':st/dias})
                
                df_rank = pd.concat([df_rank, pd.DataFrame(detalhes)], axis=1).sort_values('Média', ascending=False)
                df_rank.to_excel(writer, sheet_name=self._sanitizar_nome_aba(f"Rank {reg}", abas), index=False)
                
                # Pivots
                for l in df_rank['Logradouro']:
                    dd = df_reg[df_reg['Logradouro']==l].copy()
                    dd['P_Norm'] = dd['Periodo'].apply(lambda x: 'Manhã' if 'Manhã' in x or '10h' in x else 'Tarde')
                    piv = dd.pivot_table(index='Data', columns='P_Norm', values='Quantidade', aggfunc='sum', fill_value=0)
                    piv = piv.reindex(pd.date_range(d_ini, d_fim, freq='D'), fill_value=0).reset_index().rename(columns={'index':'Data'})
                    piv['Data'] = piv['Data'].dt.strftime('%d/%m/%Y')
                    piv.to_excel(writer, sheet_name=self._sanitizar_nome_aba(l, abas), index=False)

    def _processar_mensal_excel(self, df, caminho):
        # Lógica idêntica ao anterior (Mensal + Gráfico + Totais)
        df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')
        map_mes = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
        abas = []
        with pd.ExcelWriter(caminho, engine='openpyxl') as writer:
            for reg in df.groupby('Regiao')['Quantidade'].sum().sort_values(ascending=False).index:
                df_reg = df[df['Regiao'] == reg]
                l_princ, l_graf = [], []
                
                for m_str in sorted(df_reg['Mes_Ano'].unique()):
                    df_m = df_reg[df_reg['Mes_Ano'] == m_str]
                    m_nome = map_mes.get(int(m_str.split('-')[1]), m_str)
                    
                    t_soma, t_dias, t_m, t_t = 0, 0, 0, 0
                    for log in sorted(df_m['Logradouro'].unique()):
                        dl = df_m[df_m['Logradouro']==log]
                        dm = dl[dl['Periodo'].str.contains('Manhã|10h',case=False,na=False)]['Data'].nunique()
                        dt = dl[dl['Periodo'].str.contains('Tarde|15h',case=False,na=False)]['Data'].nunique()
                        du = max(dm, dt) or 1
                        
                        sm = dl[dl['Periodo'].str.contains('Manhã|10h',case=False,na=False)]['Quantidade'].sum()
                        st = dl[dl['Periodo'].str.contains('Tarde|15h',case=False,na=False)]['Quantidade'].sum()
                        
                        l_princ.append({'Mês': m_nome, 'Logradouro': log, 'Soma': sm+st, 'Dias': du, 
                                      'Média': round((sm+st)/(du*2),2), 'Manhã': round(sm/du,2), 'Tarde': round(st/du,2)})
                        t_soma+=sm+st; t_dias+=du; t_m+=sm; t_t+=st
                    
                    l_princ.append({'Mês': m_nome.upper(), 'Logradouro': 'TOTAL', 'Soma': t_soma, 'Dias': t_dias,
                                  'Média': round(t_soma/(t_dias*2),2) if t_dias else 0,
                                  'Manhã': round(t_m/t_dias,2) if t_dias else 0, 'Tarde': round(t_t/t_dias,2) if t_dias else 0})
                    l_graf.append({'Mês': m_nome, 'Manhã': round(t_m/t_dias,2) if t_dias else 0, 'Tarde': round(t_t/t_dias,2) if t_dias else 0})
                
                pd.DataFrame(l_princ).to_excel(writer, sheet_name=self._sanitizar_nome_aba(reg, abas), index=False)
                pd.DataFrame(l_graf).to_excel(writer, sheet_name=self._sanitizar_nome_aba(f"{reg} - Graf", abas), index=False)
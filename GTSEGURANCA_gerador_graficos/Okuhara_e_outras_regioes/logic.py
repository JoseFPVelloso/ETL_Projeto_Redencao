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
        self.mapa_regioes = {}      # Mapeia: Nome Oficial -> Região
        self.mapa_correcao = {}     # Mapeia: Nome Torto -> Nome Oficial
        self.regioes_disponiveis = []

    def carregar_mapa_regioes(self):
        """
        Carrega o arquivo regioes.xlsx.
        Agora suporta 3 colunas para UNIFICAR logradouros:
        Col 1: Nome Original (na planilha de dados)
        Col 2: Nome Oficial (Unificado)
        Col 3: Região
        """
        if not os.path.exists(config.ARQUIVO_REGIOES):
            return False, "Arquivo 'regioes.xlsx' não encontrado."
        
        try:
            df_map = pd.read_excel(config.ARQUIVO_REGIOES)
            
            # Limpeza dos nomes das colunas (remove espaços)
            df_map.columns = df_map.columns.str.strip()
            cols = df_map.columns
            
            # Lógica Inteligente de Colunas
            if len(cols) >= 3:
                # Estrutura NOVA: [Original, Oficial, Regiao]
                col_orig = cols[0]
                col_oficial = cols[1]
                col_reg = cols[2]
                
                # Limpa dados
                df_map[col_orig] = df_map[col_orig].astype(str).str.strip()
                df_map[col_oficial] = df_map[col_oficial].astype(str).str.strip()
                df_map[col_reg] = df_map[col_reg].astype(str).str.strip()
                
                # Cria os dicionários
                self.mapa_correcao = dict(zip(df_map[col_orig], df_map[col_oficial]))
                self.mapa_regioes = dict(zip(df_map[col_oficial], df_map[col_reg]))
                
                msg = f"Mapa carregado: {len(self.mapa_correcao)} correções e {len(self.mapa_regioes)} locais oficiais."

            elif len(cols) == 2:
                # Estrutura ANTIGA: [Original, Regiao] (Sem correção de nome)
                col_orig = cols[0]
                col_reg = cols[1]
                
                df_map[col_orig] = df_map[col_orig].astype(str).str.strip()
                df_map[col_reg] = df_map[col_reg].astype(str).str.strip()
                
                self.mapa_correcao = {} # Sem correção
                self.mapa_regioes = dict(zip(df_map[col_orig], df_map[col_reg]))
                
                msg = f"Mapa simples carregado (sem unificação): {len(self.mapa_regioes)} locais."
            else:
                return False, "O arquivo regioes.xlsx precisa ter 2 ou 3 colunas."
            
            return True, msg
            
        except Exception as e:
            return False, f"Erro ao ler regioes.xlsx: {str(e)}"

    def carregar_dados(self, caminho):
        try:
            self.df = pd.read_excel(caminho)
            self.caminho_arquivo = caminho

            # 1. Padronização de Colunas
            self.df.columns = self.df.columns.str.strip()
            mapa_cols = {
                'Região': 'Regiao_Original', 'Regiao': 'Regiao_Original',
                'Período': 'Periodo', 'Logradouro': 'Logradouro', 
                'Quantidade': 'Quantidade', 'Data': 'Data'
            }
            self.df.rename(columns=mapa_cols, inplace=True)
            
            if 'Logradouro' in self.df.columns:
                self.df['Logradouro'] = self.df['Logradouro'].astype(str).str.strip()

            # 2. APLICAÇÃO DA CORREÇÃO DE NOMES (FUSÃO)
            if self.mapa_correcao:
                # Se o logradouro estiver no mapa de correção, substitui pelo oficial
                # Se não estiver, mantém o original
                self.df['Logradouro'] = self.df['Logradouro'].map(self.mapa_correcao).fillna(self.df['Logradouro'])

            # 3. APLICAÇÃO DA REGIÃO
            if self.mapa_regioes:
                # Agora mapeamos a região baseada no nome JÁ CORRIGIDO
                self.df['Regiao'] = self.df['Logradouro'].map(self.mapa_regioes).fillna('Outros')
            else:
                # Fallback antigo
                if 'Regiao_Original' in self.df.columns: self.df['Regiao'] = self.df['Regiao_Original']
                else: self.df['Regiao'] = 'Desconhecido'

            # 4. Tratamentos Numéricos e Data
            self.df['Quantidade'] = pd.to_numeric(self.df['Quantidade'], errors='coerce').fillna(0)
            self.df['Data'] = pd.to_datetime(self.df['Data'], errors='coerce')
            self.df = self.df.dropna(subset=['Data'])
            if 'Periodo' in self.df.columns: self.df['Periodo'] = self.df['Periodo'].astype(str).str.strip()

            # Atualiza lista para UI
            self.regioes_disponiveis = sorted(self.df['Regiao'].unique().tolist())
            if "Outros" in self.regioes_disponiveis:
                self.regioes_disponiveis.remove("Outros")
                self.regioes_disponiveis.append("Outros")

            return True, f"Base processada: {len(self.df)} registros (Nomes unificados)."
        except Exception as e:
            return False, str(e)

    def obter_logradouros_da_regiao(self, regiao):
        if self.df is None or regiao not in self.df['Regiao'].unique(): return []
        return sorted(self.df[self.df['Regiao'] == regiao]['Logradouro'].unique())

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

        # === NOVO: Configuração do Nome do Arquivo ===
        # 1. Junta os nomes das regiões selecionadas
        # Ex: "Complexo Okuhara Koei", "CnR Lapa" -> "Complexo_Okuhara_Koei_CnR_Lapa"
        nomes_regioes = [str(r).replace(" ", "_").replace("/", "-").replace("\\", "") for r in regioes_selecionadas]
        sufixo_regioes = "_".join(nomes_regioes)
        
        # Trava de segurança para nome de arquivo muito longo (max ~100 chars é seguro)
        if len(sufixo_regioes) > 100:
            sufixo_regioes = sufixo_regioes[:100] + "..."
            
        # 2. Define a DATA atual para o nome (Ex: 28-01-2026)
        data_str = datetime.now().strftime('%d-%m-%Y')

        # 1. DIÁRIO
        try:
            df_d = df_filter[(df_filter['Data'] >= params_diario['inicio']) & (df_filter['Data'] <= params_diario['fim'])].copy()
            if not df_d.empty:
                # Mudança solicitada: Ranking_Diario_DATA_Regioes.xlsx
                nome_arq = f"Ranking_Diario_{data_str}_{sufixo_regioes}.xlsx"
                path = os.path.join(config.OUTPUT_FOLDER, nome_arq)
                
                self._processar_ranking_excel(df_d, path, params_diario['inicio'], params_diario['fim'])
                msgs.append(f"✓ Ranking Diário OK: {nome_arq}")
            else: msgs.append("⚠️ Diário vazio")
        except Exception as e: msgs.append(f"❌ Erro Diário: {e}")

        # 2. MENSAL
        try:
            df_m = df_filter[(df_filter['Data'] >= params_mensal['inicio']) & (df_filter['Data'] <= params_mensal['fim'])].copy()
            if not df_m.empty:
                # Mudança solicitada: Ranking_Mensal_DATA_Regioes.xlsx (Antes era Evolucao_Mensal)
                nome_arq = f"Ranking_Mensal_{data_str}_{sufixo_regioes}.xlsx"
                path = os.path.join(config.OUTPUT_FOLDER, nome_arq)
                
                self._processar_mensal_excel(df_m, path)
                msgs.append(f"✓ Ranking Mensal OK: {nome_arq}")
            else: msgs.append("⚠️ Mensal vazio")
        except Exception as e: msgs.append(f"❌ Erro Mensal: {e}")

        return True, "\n".join(msgs)

    def _processar_ranking_excel(self, df, caminho, d_ini, d_fim):
        dias = (d_fim - d_ini).days + 1
        total_p = dias * 2
        abas = []
        with pd.ExcelWriter(caminho, engine='openpyxl') as writer:
            for reg in df.groupby('Regiao')['Quantidade'].sum().sort_values(ascending=False).index:
                df_reg = df[df['Regiao'] == reg]
                
                df_rank = df_reg.groupby('Logradouro').agg({'Quantidade':'sum'}).reset_index()
                df_rank['Média'] = df_rank['Quantidade'] / total_p
                
                detalhes = []
                for l in df_rank['Logradouro']:
                    dl = df_reg[df_reg['Logradouro']==l]
                    sm = dl[dl['Periodo'].str.contains('Manhã|10h',case=False,na=False)]['Quantidade'].sum()
                    st = dl[dl['Periodo'].str.contains('Tarde|15h',case=False,na=False)]['Quantidade'].sum()
                    detalhes.append({'Manhã':sm/dias, 'Tarde':st/dias})
                
                df_rank = pd.concat([df_rank, pd.DataFrame(detalhes)], axis=1).sort_values('Média', ascending=False)
                df_rank.to_excel(writer, sheet_name=self._sanitizar_nome_aba(f"Rank {reg}", abas), index=False)
                
                for l in df_rank['Logradouro']:
                    dd = df_reg[df_reg['Logradouro']==l].copy()
                    dd['P_Norm'] = dd['Periodo'].apply(lambda x: 'Manhã' if 'Manhã' in x or '10h' in x else 'Tarde')
                    piv = dd.pivot_table(index='Data', columns='P_Norm', values='Quantidade', aggfunc='sum', fill_value=0)
                    piv = piv.reindex(pd.date_range(d_ini, d_fim, freq='D'), fill_value=0).reset_index().rename(columns={'index':'Data'})
                    piv['Data'] = piv['Data'].dt.strftime('%d/%m/%Y')
                    
                    # === NOVA COLUNA DE IDENTIFICAÇÃO ===
                    # Insere o Logradouro na segunda coluna (índice 1), ao lado da Data
                    piv.insert(1, 'Logradouro', l)
                    
                    piv.to_excel(writer, sheet_name=self._sanitizar_nome_aba(l, abas), index=False)

    def _processar_mensal_excel(self, df, caminho):
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
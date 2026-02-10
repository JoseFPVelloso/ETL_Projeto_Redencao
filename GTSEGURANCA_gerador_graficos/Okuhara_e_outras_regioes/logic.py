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
        self.mapa_correcao = {}     
        self.regioes_disponiveis = []

    def carregar_mapa_regioes(self):
        if not os.path.exists(config.ARQUIVO_REGIOES):
            return False, "Arquivo 'regioes.xlsx' não encontrado."
        try:
            df_map = pd.read_excel(config.ARQUIVO_REGIOES)
            df_map.columns = df_map.columns.str.strip()
            cols = df_map.columns
            if len(cols) >= 3:
                col_orig, col_oficial, col_reg = cols[0], cols[1], cols[2]
                df_map[col_orig] = df_map[col_orig].astype(str).str.strip()
                df_map[col_oficial] = df_map[col_oficial].astype(str).str.strip()
                df_map[col_reg] = df_map[col_reg].astype(str).str.strip()
                self.mapa_correcao = dict(zip(df_map[col_orig], df_map[col_oficial]))
                self.mapa_regioes = dict(zip(df_map[col_oficial], df_map[col_reg]))
                msg = f"Mapa carregado: {len(self.mapa_correcao)} correções."
            elif len(cols) == 2:
                col_orig, col_reg = cols[0], cols[1]
                df_map[col_orig] = df_map[col_orig].astype(str).str.strip()
                df_map[col_reg] = df_map[col_reg].astype(str).str.strip()
                self.mapa_correcao = {}
                self.mapa_regioes = dict(zip(df_map[col_orig], df_map[col_reg]))
                msg = f"Mapa simples carregado: {len(self.mapa_regioes)} locais."
            else:
                return False, "O arquivo regioes.xlsx precisa ter 2 ou 3 colunas."
            return True, msg
        except Exception as e:
            return False, f"Erro ao ler regioes.xlsx: {str(e)}"

    def carregar_dados(self, caminho):
        try:
            self.df = pd.read_excel(caminho)
            self.caminho_arquivo = caminho
            self.df.columns = self.df.columns.str.strip()
            mapa_cols = {
                'Região': 'Regiao_Original', 'Regiao': 'Regiao_Original',
                'Período': 'Periodo', 'Logradouro': 'Logradouro', 
                'Quantidade': 'Quantidade', 'Data': 'Data'
            }
            self.df.rename(columns=mapa_cols, inplace=True)
            if 'Logradouro' in self.df.columns:
                self.df['Logradouro'] = self.df['Logradouro'].astype(str).str.strip()
            if self.mapa_correcao:
                self.df['Logradouro'] = self.df['Logradouro'].map(self.mapa_correcao).fillna(self.df['Logradouro'])
            if self.mapa_regioes:
                self.df['Regiao'] = self.df['Logradouro'].map(self.mapa_regioes).fillna('Outros')
            else:
                if 'Regiao_Original' in self.df.columns: self.df['Regiao'] = self.df['Regiao_Original']
                else: self.df['Regiao'] = 'Desconhecido'
            
            self.df['Quantidade'] = pd.to_numeric(self.df['Quantidade'], errors='coerce').fillna(0)
            self.df['Data'] = pd.to_datetime(self.df['Data'], errors='coerce')
            self.df = self.df.dropna(subset=['Data'])
            if 'Periodo' in self.df.columns: self.df['Periodo'] = self.df['Periodo'].astype(str).str.strip()

            self.regioes_disponiveis = sorted(self.df['Regiao'].unique().tolist())
            if "Outros" in self.regioes_disponiveis:
                self.regioes_disponiveis.remove("Outros")
                self.regioes_disponiveis.append("Outros")

            return True, f"Base processada: {len(self.df)} registros."
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

    # --- ATUALIZADO: Recebe periodos_ativos ---
    def gerar_todos_relatorios(self, params_diario, params_mensal, regioes_selecionadas, periodos_ativos):
        msgs = []
        if not regioes_selecionadas: return False, "Nenhuma região selecionada."
            
        df_filter = self.df[self.df['Regiao'].isin(regioes_selecionadas)].copy()
        if df_filter.empty: return False, "Sem dados para as regiões selecionadas."

        nomes_regioes = [str(r).replace(" ", "_").replace("/", "-") for r in regioes_selecionadas]
        sufixo_regioes = "_".join(nomes_regioes)
        if len(sufixo_regioes) > 80: sufixo_regioes = sufixo_regioes[:80] + "..."
        data_str = datetime.now().strftime('%d-%m-%Y')

        # 1. DIÁRIO
        try:
            df_d = df_filter[(df_filter['Data'] >= params_diario['inicio']) & (df_filter['Data'] <= params_diario['fim'])].copy()
            if not df_d.empty:
                nome_arq = f"Ranking_Diario_{data_str}_{sufixo_regioes}.xlsx"
                path = os.path.join(config.OUTPUT_FOLDER, nome_arq)
                self._processar_ranking_excel(df_d, path, params_diario['inicio'], params_diario['fim'], periodos_ativos)
                msgs.append(f"✓ Ranking Diário OK: {nome_arq}")
            else: msgs.append("⚠️ Diário vazio")
        except Exception as e: msgs.append(f"❌ Erro Diário: {e}")

        # 2. MENSAL
        try:
            df_m = df_filter[(df_filter['Data'] >= params_mensal['inicio']) & (df_filter['Data'] <= params_mensal['fim'])].copy()
            if not df_m.empty:
                nome_arq = f"Ranking_Mensal_{data_str}_{sufixo_regioes}.xlsx"
                path = os.path.join(config.OUTPUT_FOLDER, nome_arq)
                self._processar_mensal_excel(df_m, path, periodos_ativos)
                msgs.append(f"✓ Ranking Mensal OK: {nome_arq}")
            else: msgs.append("⚠️ Mensal vazio")
        except Exception as e: msgs.append(f"❌ Erro Mensal: {e}")

        return True, "\n".join(msgs)

    # --- LÓGICA DO DIÁRIO ATUALIZADA ---
    def _processar_ranking_excel(self, df, caminho, d_ini, d_fim, periodos_ativos):
        dias = (d_fim - d_ini).days + 1
        total_p = dias * len(periodos_ativos) # Média considera o número de períodos selecionados
        abas = []
        
        with pd.ExcelWriter(caminho, engine='openpyxl') as writer:
            # Ordena regiões por volume total
            for reg in df.groupby('Regiao')['Quantidade'].sum().sort_values(ascending=False).index:
                df_reg = df[df['Regiao'] == reg]
                
                # --- ABA 1: RESUMO (Rank Região) ---
                df_rank = df_reg.groupby('Logradouro').agg({'Quantidade':'sum'}).reset_index()
                # Calcula média baseada no nº de dias e nº de períodos
                df_rank['Média'] = df_rank['Quantidade'] / total_p if total_p > 0 else 0
                
                detalhes = []
                for l in df_rank['Logradouro']:
                    dl = df_reg[df_reg['Logradouro']==l]
                    stats = {}
                    # Loop Dinâmico pelos períodos escolhidos
                    for p in periodos_ativos:
                        soma_p = dl[dl['Periodo'].str.contains(p, case=False, na=False)]['Quantidade'].sum()
                        stats[p] = soma_p / dias if dias > 0 else 0
                    detalhes.append(stats)
                
                df_rank = pd.concat([df_rank, pd.DataFrame(detalhes)], axis=1).sort_values('Média', ascending=False)
                df_rank.to_excel(writer, sheet_name=self._sanitizar_nome_aba(f"Rank {reg}", abas), index=False)
                
                # --- ABAS 2...N: DETALHE POR LOGRADOURO ---
                # Função auxiliar para classificar a linha em um dos períodos selecionados
                def classificar_periodo(texto_periodo):
                    for p in periodos_ativos:
                        if p in str(texto_periodo):
                            return p
                    return 'Outros'

                for l in df_rank['Logradouro']:
                    dd = df_reg[df_reg['Logradouro']==l].copy()
                    
                    # Cria coluna normalizada apenas com os períodos selecionados
                    dd['P_Norm'] = dd['Periodo'].apply(classificar_periodo)
                    # Filtra fora o que não foi selecionado (opcional, mas limpa o dado)
                    dd = dd[dd['P_Norm'].isin(periodos_ativos)]

                    piv = dd.pivot_table(index='Data', columns='P_Norm', values='Quantidade', aggfunc='sum', fill_value=0)
                    
                    # Garante que todas as datas apareçam
                    piv = piv.reindex(pd.date_range(d_ini, d_fim, freq='D'), fill_value=0).reset_index().rename(columns={'index':'Data'})
                    piv['Data'] = piv['Data'].dt.strftime('%d/%m/%Y')
                    
                    # === MUDANÇA SOLICITADA: ORDEM DAS COLUNAS ===
                    # 1. Adiciona a coluna Logradouro
                    piv['Logradouro'] = l
                    
                    # 2. Define a ordem: Logradouro | Data | [Períodos Ativos que existem nos dados]
                    cols_periodos = [c for c in periodos_ativos if c in piv.columns]
                    # Se por acaso algum período não tiver dados, ele não aparece no pivot, então usamos intersecção
                    nova_ordem = ['Logradouro', 'Data'] + cols_periodos
                    
                    # Caso haja colunas extras (bugs ou Outros), adicionamos ao fim
                    extras = [c for c in piv.columns if c not in nova_ordem]
                    nova_ordem += extras
                    
                    piv = piv[nova_ordem] # Reordena efetivamente
                    
                    piv.to_excel(writer, sheet_name=self._sanitizar_nome_aba(l, abas), index=False)

    # --- LÓGICA DO MENSAL ATUALIZADA ---
    def _processar_mensal_excel(self, df, caminho, periodos_ativos):
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
                    
                    # Acumuladores Totais do Mês
                    total_soma = 0
                    total_dias_unicos = 0
                    stats_totais_periodos = {p: 0 for p in periodos_ativos} # { '05h': 0, '10h': 0... }

                    for log in sorted(df_m['Logradouro'].unique()):
                        dl = df_m[df_m['Logradouro']==log]
                        
                        # Calcula dias únicos considerando qualquer um dos períodos ativos
                        # Ex: se tem registro 05h no dia 1 e 10h no dia 1, conta como 1 dia.
                        mask_periodos = dl['Periodo'].str.contains('|'.join(periodos_ativos), case=False, na=False)
                        dias_unicos_log = dl[mask_periodos]['Data'].nunique() or 1
                        
                        soma_log = 0
                        row_data = {'Mês': m_nome, 'Logradouro': log}
                        
                        # Loop para preencher colunas dinâmicas (05h, 10h...)
                        for p in periodos_ativos:
                            s_p = dl[dl['Periodo'].str.contains(p, case=False, na=False)]['Quantidade'].sum()
                            row_data[p] = round(s_p / dias_unicos_log, 2)
                            
                            # Soma para totais
                            soma_log += s_p
                            stats_totais_periodos[p] += s_p

                        row_data['Soma'] = soma_log
                        row_data['Dias'] = dias_unicos_log
                        # Média Geral do Logradouro
                        row_data['Média'] = round(soma_log / (dias_unicos_log * len(periodos_ativos)), 2)
                        
                        l_princ.append(row_data)
                        
                        total_soma += soma_log
                        total_dias_unicos += dias_unicos_log # Soma simples de dias dos logradouros para média ponderada

                    # Linha TOTAL DO MÊS
                    row_total = {'Mês': m_nome.upper(), 'Logradouro': 'TOTAL', 'Soma': total_soma, 'Dias': total_dias_unicos}
                    div_media = total_dias_unicos if total_dias_unicos > 0 else 1
                    
                    row_total['Média'] = round(total_soma / (div_media * len(periodos_ativos)), 2)
                    
                    # Médias por período no TOTAL
                    graf_data = {'Mês': m_nome}
                    for p in periodos_ativos:
                        val_media = round(stats_totais_periodos[p] / div_media, 2)
                        row_total[p] = val_media
                        graf_data[p] = val_media
                    
                    l_princ.append(row_total)
                    l_graf.append(graf_data)
                
                pd.DataFrame(l_princ).to_excel(writer, sheet_name=self._sanitizar_nome_aba(reg, abas), index=False)
                pd.DataFrame(l_graf).to_excel(writer, sheet_name=self._sanitizar_nome_aba(f"{reg} - Graf", abas), index=False)
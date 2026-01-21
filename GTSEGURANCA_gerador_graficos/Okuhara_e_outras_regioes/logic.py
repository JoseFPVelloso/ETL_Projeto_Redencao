import pandas as pd
import numpy as np
import os
import re
from datetime import datetime, timedelta
from config import OUTPUT_FOLDER

class AnalisadorDados:
    def __init__(self):
        self.df = None
        self.caminho_arquivo = ""

    def carregar_dados(self, caminho):
        try:
            self.df = pd.read_excel(caminho)
            self.caminho_arquivo = caminho

            # 1. Padronizar nomes das colunas e remover espaços
            self.df.columns = self.df.columns.str.strip()
            
            # Renomeações para garantir compatibilidade
            mapa_correcao = {
                'Região': 'Regiao', 'Período': 'Periodo', 
                'Equipe': 'Equipe', 'Logradouro': 'Logradouro', 
                'Quantidade': 'Quantidade', 'Data': 'Data'
            }
            self.df.rename(columns=mapa_correcao, inplace=True)

            # 2. Tratamento Numérico e Data
            self.df['Quantidade'] = pd.to_numeric(self.df['Quantidade'], errors='coerce').fillna(0)
            self.df['Data'] = pd.to_datetime(self.df['Data'], errors='coerce')
            self.df = self.df.dropna(subset=['Data'])

            # 3. Lógica de Região (se não existir, cria)
            if 'Regiao' not in self.df.columns and 'Logradouro' in self.df.columns:
                 self.df['Regiao'] = self.df['Logradouro'].astype(str).str.split(' - ', n=1).str[0].str.strip()

            # 4. Limpeza de strings
            for col in ['Regiao', 'Logradouro', 'Periodo']:
                if col in self.df.columns:
                    self.df[col] = self.df[col].astype(str).str.strip()

            if 'Regiao' not in self.df.columns:
                return False, "Erro: Coluna 'Regiao' não encontrada."

            return True, f"Carregado: {len(self.df)} registros."
        
        except Exception as e:
            return False, f"Erro ao ler arquivo: {str(e)}"

    def _sanitizar_nome_aba(self, nome, nomes_existentes):
        """Limpa nomes para abas do Excel (max 31 chars, sem caracteres proibidos)"""
        nome_limpo = str(nome).replace('/', '-').replace('\\', '-').replace(':', '')
        nome_limpo = re.sub(r'[?*\[\]]', '', nome_limpo)
        
        # Tenta encurtar nomes longos pegando a parte mais específica (depois do hífen se houver)
        if len(nome_limpo) > 31 and ' - ' in nome_limpo:
             parts = nome_limpo.split(' - ')
             if len(parts) > 1:
                 nome_limpo = parts[1]

        nome_limpo = nome_limpo[:31]
        if not nome_limpo: nome_limpo = "Sheet"

        # Garante unicidade
        nome_final = nome_limpo
        contador = 1
        while nome_final.lower() in [n.lower() for n in nomes_existentes]:
            sufixo = f"_{contador}"
            nome_final = f"{nome_limpo[:31-len(sufixo)]}{sufixo}"
            contador += 1
            
        nomes_existentes.append(nome_final)
        return nome_final

    def _filtrar_periodo(self, data_inicio, data_fim):
        return self.df[(self.df['Data'] >= data_inicio) & (self.df['Data'] <= data_fim)].copy()

    def gerar_ranking_raw(self, data_inicio, data_fim):
        """
        REPLICA NOTEBOOK 03:
        - Aba 1: Ranking Geral da Região (divisão pelo calendário total)
        - Abas Seguintes: Detalhe dia a dia de cada logradouro (Pivot Table com zeros preenchidos)
        """
        df_filtrado = self._filtrar_periodo(data_inicio, data_fim)
        if df_filtrado.empty: return False, "Sem dados no período."

        # Cálculos globais do Notebook 03
        dias_no_periodo = (data_fim - data_inicio).days + 1
        total_periodos = dias_no_periodo * 2

        # Define ordem das regiões (maior volume primeiro)
        soma_regiao = df_filtrado.groupby('Regiao')['Quantidade'].sum().sort_values(ascending=False)
        regioes_ordenadas = soma_regiao.index.tolist()

        nome_arquivo = f"Ranking_Diario_RAW_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        caminho_saida = os.path.join(OUTPUT_FOLDER, nome_arquivo)
        nomes_abas_usados = []

        try:
            with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
                for regiao in regioes_ordenadas:
                    # 1. Preparar Aba de Ranking (Resumo)
                    df_reg = df_filtrado[df_filtrado['Regiao'] == regiao]
                    
                    df_rank = df_reg.groupby('Logradouro').agg({'Quantidade': 'sum'}).reset_index()
                    df_rank['Soma pessoas'] = df_rank['Quantidade']
                    df_rank['Média pessoas'] = df_rank['Soma pessoas'] / total_periodos
                    
                    # Médias por turno (Manhã/Tarde)
                    detalhes = []
                    for log in df_rank['Logradouro']:
                        d_log = df_reg[df_reg['Logradouro'] == log]
                        # Busca flexível por Manhã/10h e Tarde/15h
                        s_manha = d_log[d_log['Periodo'].str.contains('Manhã|10h', case=False, na=False)]['Quantidade'].sum()
                        s_tarde = d_log[d_log['Periodo'].str.contains('Tarde|15h', case=False, na=False)]['Quantidade'].sum()
                        detalhes.append({'Manhã': s_manha / dias_no_periodo, 'Tarde': s_tarde / dias_no_periodo})
                    
                    df_rank = pd.concat([df_rank, pd.DataFrame(detalhes)], axis=1)
                    df_rank = df_rank[['Logradouro', 'Soma pessoas', 'Média pessoas', 'Manhã', 'Tarde']]
                    df_rank = df_rank.sort_values('Média pessoas', ascending=False)

                    # Salva Aba Ranking
                    nome_aba_rank = self._sanitizar_nome_aba(f"Rank {regiao}", nomes_abas_usados)
                    df_rank.to_excel(writer, sheet_name=nome_aba_rank, index=False)

                    # 2. Criar Abas Individuais (Estilo Notebook 03)
                    # Itera na ordem do ranking
                    for logradouro in df_rank['Logradouro']:
                        df_detalhe = df_reg[df_reg['Logradouro'] == logradouro]
                        
                        # Pivot Table: Data nas linhas, Período nas colunas
                        # Padroniza nomes dos períodos para colunas ficarem bonitas
                        df_detalhe['Periodo_Norm'] = df_detalhe['Periodo'].apply(
                            lambda x: 'Manhã' if 'Manhã' in x or '10h' in x else ('Tarde' if 'Tarde' in x or '15h' in x else x)
                        )
                        
                        pivot = df_detalhe.pivot_table(
                            index='Data', columns='Periodo_Norm', values='Quantidade', aggfunc='sum', fill_value=0
                        )
                        
                        # Preencher datas faltantes (O segredo do Notebook 03)
                        idx_datas = pd.date_range(start=data_inicio, end=data_fim, freq='D')
                        pivot = pivot.reindex(idx_datas, fill_value=0)
                        pivot.index.name = 'Data'
                        pivot = pivot.reset_index()
                        
                        # Formatar data
                        pivot['Data'] = pivot['Data'].dt.strftime('%d/%m/%Y')
                        
                        # Garante colunas Manhã/Tarde
                        for col in ['Manhã', 'Tarde']:
                            if col not in pivot.columns: pivot[col] = 0
                            
                        # Salva Aba Logradouro
                        nome_aba_log = self._sanitizar_nome_aba(logradouro, nomes_abas_usados)
                        pivot[['Data', 'Manhã', 'Tarde']].to_excel(writer, sheet_name=nome_aba_log, index=False)

            return True, f"Relatório Ranking IDÊNTICO ao Notebook 3 gerado em:\n{caminho_saida}"
        except Exception as e:
            return False, f"Erro: {str(e)}"

    def gerar_evolucao_mensal(self, data_inicio, data_fim):
        """
        REPLICA NOTEBOOK 04:
        - Agrupamento mensal
        - Cálculo baseado em 'Dias Únicos Trabalhados'
        - Linha 'TOTAL DO MÊS' somando tudo
        - Aba '[Regiao] - Gráfico' separada
        """
        df_filtrado = self._filtrar_periodo(data_inicio, data_fim)
        if df_filtrado.empty: return False, "Sem dados."

        df_filtrado['Mes_Ano'] = df_filtrado['Data'].dt.strftime('%Y-%m')
        df_filtrado['Mes_Num'] = df_filtrado['Data'].dt.month
        
        # Mapeamento de meses para nomes (igual ao notebook)
        nomes_meses = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho',
                       7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}

        # Ordenar regiões por total
        soma_regiao = df_filtrado.groupby('Regiao')['Quantidade'].sum().sort_values(ascending=False)
        regioes_ordenadas = soma_regiao.index.tolist()

        nome_arquivo = f"Evolucao_Mensal_RAW_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        caminho_saida = os.path.join(OUTPUT_FOLDER, nome_arquivo)
        nomes_abas_usados = []

        try:
            with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
                for regiao in regioes_ordenadas:
                    df_reg = df_filtrado[df_filtrado['Regiao'] == regiao]
                    
                    linhas_principal = []
                    linhas_grafico = []
                    
                    meses_unicos = sorted(df_reg['Mes_Ano'].unique())
                    
                    for mes_str in meses_unicos:
                        df_mes = df_reg[df_reg['Mes_Ano'] == mes_str]
                        mes_nome = nomes_meses.get(int(mes_str.split('-')[1]), mes_str)
                        
                        # Variáveis para o TOTAL DO MÊS
                        total_soma_mes = 0
                        total_dias_mes = 0 # Soma dos dias únicos de cada logradouro
                        total_manha_mes = 0
                        total_tarde_mes = 0
                        
                        # Processa Logradouros
                        logradouros = sorted(df_mes['Logradouro'].unique())
                        for log in logradouros:
                            d_log = df_mes[df_mes['Logradouro'] == log]
                            
                            # Lógica do Notebook 4: Max(dias_manha, dias_tarde)
                            # Para replicar exato, precisamos contar quantos dias únicos apareceram como manha e tarde
                            dias_manha = d_log[d_log['Periodo'].str.contains('Manhã|10h', case=False, na=False)]['Data'].nunique()
                            dias_tarde = d_log[d_log['Periodo'].str.contains('Tarde|15h', case=False, na=False)]['Data'].nunique()
                            dias_unicos = max(dias_manha, dias_tarde)
                            if dias_unicos == 0: dias_unicos = 1 # Evitar div/0
                            
                            soma_manha = d_log[d_log['Periodo'].str.contains('Manhã|10h', case=False, na=False)]['Quantidade'].sum()
                            soma_tarde = d_log[d_log['Periodo'].str.contains('Tarde|15h', case=False, na=False)]['Quantidade'].sum()
                            soma_total = soma_manha + soma_tarde
                            
                            media_total = soma_total / (dias_unicos * 2)
                            
                            linhas_principal.append({
                                'Mês': mes_nome,
                                'Logradouro': log,
                                'Soma Pessoas': soma_total,
                                'Qtd. Dias': dias_unicos,
                                'Média Pessoas': round(media_total, 2),
                                'Média Manhã': round(soma_manha / dias_unicos, 2),
                                'Média Tarde': round(soma_tarde / dias_unicos, 2)
                            })
                            
                            # Acumula para o Total
                            total_soma_mes += soma_total
                            total_dias_mes += dias_unicos
                            total_manha_mes += soma_manha
                            total_tarde_mes += soma_tarde

                        # LINHA TOTAL DO MÊS (Essencial para Notebook 4)
                        media_total_mes_consol = total_soma_mes / (total_dias_mes * 2) if total_dias_mes > 0 else 0
                        media_manha_mes_consol = total_manha_mes / total_dias_mes if total_dias_mes > 0 else 0
                        media_tarde_mes_consol = total_tarde_mes / total_dias_mes if total_dias_mes > 0 else 0
                        
                        linhas_principal.append({
                            'Mês': mes_nome.upper(),
                            'Logradouro': 'TOTAL DO MÊS',
                            'Soma Pessoas': total_soma_mes,
                            'Qtd. Dias': total_dias_mes,
                            'Média Pessoas': round(media_total_mes_consol, 2),
                            'Média Manhã': round(media_manha_mes_consol, 2),
                            'Média Tarde': round(media_tarde_mes_consol, 2)
                        })
                        
                        # Dados para Aba Gráfico
                        linhas_grafico.append({
                            'Mês': mes_nome,
                            'Média Manhã': round(media_manha_mes_consol, 2),
                            'Média Tarde': round(media_tarde_mes_consol, 2)
                        })

                    # Salvar Aba Principal
                    df_main = pd.DataFrame(linhas_principal)
                    nome_aba_main = self._sanitizar_nome_aba(regiao, nomes_abas_usados)
                    df_main.to_excel(writer, sheet_name=nome_aba_main, index=False)
                    
                    # Salvar Aba Gráfico
                    df_graph = pd.DataFrame(linhas_grafico)
                    nome_aba_graph = self._sanitizar_nome_aba(f"{regiao} - Gráfico", nomes_abas_usados)
                    df_graph.to_excel(writer, sheet_name=nome_aba_graph, index=False)

            return True, f"Relatório Mensal IDÊNTICO ao Notebook 4 gerado em:\n{caminho_saida}"
        except Exception as e:
            return False, f"Erro: {str(e)}"
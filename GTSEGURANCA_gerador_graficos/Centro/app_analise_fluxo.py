import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import os
import sys
import json
import re
from datetime import datetime, timedelta
import threading

# --- CORREÇÃO DE DIRETÓRIOS ---
# Garante que o BASE_DIR seja a pasta onde este arquivo .py está salvo
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configurações de Pastas e Arquivos (Caminhos Absolutos)
OUTPUT_FOLDER = os.path.join(BASE_DIR, "Gráficos")
CONFIG_FOLDER = os.path.join(BASE_DIR, "Config")
CONFIG_FILE = os.path.join(CONFIG_FOLDER, 'config_ruas_preferidas.json')
DEFAULT_START_MONTHLY = "01/06/2025"

class PedestrianAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador de Fluxo de Pessoas e Aglomerações")
        self.root.geometry("1000x800")
        
        # Variáveis de Estado
        self.df_raw = None
        self.filepath = tk.StringVar()
        self.all_streets = []
        self.selected_streets_set = set() # Usando Set para performance e facilidade
        
        # Variáveis de Data
        yesterday = datetime.now() - timedelta(days=1)
        self.yesterday_str = yesterday.strftime("%d/%m/%Y")
        
        self.top15_days_var = tk.IntVar(value=15)
        self.top15_end_date_var = tk.StringVar(value=self.yesterday_str)
        
        self.monthly_start_var = tk.StringVar(value=DEFAULT_START_MONTHLY)
        self.monthly_end_date_var = tk.StringVar(value=self.yesterday_str)

        # Estilo
        style = ttk.Style()
        style.configure("Bold.TLabel", font=("Segoe UI", 10, "bold"))
        
        self.create_widgets()
        self.load_preferences()

    def create_widgets(self):
        # --- Frame Principal ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Seleção de Arquivo
        file_frame = ttk.LabelFrame(main_frame, text="1. Importação de Dados", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="Arquivo Padronizado (.csv ou .xlsx):").pack(side=tk.LEFT)
        ttk.Entry(file_frame, textvariable=self.filepath, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Buscar Arquivo", command=self.browse_file).pack(side=tk.LEFT)
        ttk.Button(file_frame, text="Carregar Dados", command=self.load_data).pack(side=tk.LEFT, padx=5)

        # 2. Configuração de Datas
        date_frame = ttk.LabelFrame(main_frame, text="2. Configuração de Períodos", padding="10")
        date_frame.pack(fill=tk.X, pady=5)
        
        # Grid para alinhar melhor
        date_grid = ttk.Frame(date_frame)
        date_grid.pack(fill=tk.X)

        # -- Top 15 --
        ttk.Label(date_grid, text="Relatório Top 15", style="Bold.TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        f_top15 = ttk.Frame(date_grid)
        f_top15.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(f_top15, text="Intervalo de").pack(side=tk.LEFT)
        ttk.Spinbox(f_top15, from_=1, to=365, textvariable=self.top15_days_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(f_top15, text="dias até a data:").pack(side=tk.LEFT, padx=2)
        ttk.Entry(f_top15, textvariable=self.top15_end_date_var, width=12).pack(side=tk.LEFT, padx=2)
        
        # -- Mensal --
        ttk.Label(date_grid, text="Relatório Mensal", style="Bold.TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        f_mensal = ttk.Frame(date_grid)
        f_mensal.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(f_mensal, text="De:").pack(side=tk.LEFT)
        ttk.Entry(f_mensal, textvariable=self.monthly_start_var, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Label(f_mensal, text="Até:").pack(side=tk.LEFT, padx=2)
        ttk.Entry(f_mensal, textvariable=self.monthly_end_date_var, width=12).pack(side=tk.LEFT, padx=2)

        # Botão Auxiliar
        ttk.Button(date_grid, text="Resetar Datas Finais para 'Ontem'", command=self.set_dates_to_yesterday).grid(row=0, column=2, rowspan=2, padx=20)

        # 3. Seleção de Ruas (OTIMIZADO)
        street_frame = ttk.LabelFrame(main_frame, text="3. Seleção de Ruas (Logradouros)", padding="10")
        street_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Controles de Filtro
        filter_frame = ttk.Frame(street_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(filter_frame, text="Marcar Filtradas", command=self.select_visible).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Desmarcar Filtradas", command=self.deselect_visible).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(filter_frame, text="|  Pesquisar:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_list)
        ttk.Entry(filter_frame, textvariable=self.search_var, width=40).pack(side=tk.LEFT)
        
        # Label de contador
        self.count_label = ttk.Label(filter_frame, text="0 selecionadas")
        self.count_label.pack(side=tk.RIGHT, padx=10)

        # Listbox Customizada (Substitui Checkbuttons)
        list_container = ttk.Frame(street_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.street_listbox = tk.Listbox(list_container, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set, font=("Consolas", 10))
        self.street_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.street_listbox.yview)
        
        # Evento de clique para alternar seleção
        self.street_listbox.bind('<ButtonRelease-1>', self.toggle_street_selection)

        # 4. Ações
        action_frame = ttk.Frame(main_frame, padding="10")
        action_frame.pack(fill=tk.X, pady=5)
        
        self.btn_process = ttk.Button(action_frame, text="PROCESSAR E GERAR RELATÓRIOS", command=self.start_processing, state="disabled")
        self.btn_process.pack(fill=tk.X, ipady=10)
        
        self.status_var = tk.StringVar(value="Aguardando dados...")
        ttk.Label(action_frame, textvariable=self.status_var, foreground="blue").pack(pady=5)
        
        ttk.Label(main_frame, text=f"Salvando arquivos em: {BASE_DIR}", font=("Arial", 8), foreground="gray").pack(side=tk.BOTTOM, pady=2)

    def set_dates_to_yesterday(self):
        yesterday = datetime.now() - timedelta(days=1)
        yst_str = yesterday.strftime("%d/%m/%Y")
        self.top15_end_date_var.set(yst_str)
        self.monthly_end_date_var.set(yst_str)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel/CSV Files", "*.xlsx *.xls *.csv")])
        if filename:
            self.filepath.set(filename)

    def load_data(self):
        path = self.filepath.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Erro", "Arquivo inválido ou não encontrado.")
            return

        try:
            self.status_var.set("Carregando arquivo...")
            self.root.update()

            if path.endswith('.csv'):
                self.df_raw = pd.read_csv(path)
            else:
                self.df_raw = pd.read_excel(path)

            self.df_raw.columns = [c.strip() for c in self.df_raw.columns]
            
            # Validação
            required_cols = ['Data', 'Logradouro', 'Período', 'Qtd. pessoas']
            if not all(col in self.df_raw.columns for col in required_cols):
                messagebox.showerror("Erro", f"O arquivo deve conter as colunas: {', '.join(required_cols)}")
                return

            self.df_raw['Data'] = pd.to_datetime(self.df_raw['Data'], errors='coerce')
            self.df_raw = self.df_raw.dropna(subset=['Data'])

            # Parser Interno
            periodo_map = {
                '05h - Madrugada': 'Madrugada', '10h - Manhã': 'Manhã',
                '15h - Tarde': 'Tarde', '20h - Noite': 'Noite'
            }
            self.df_raw['Periodo_Norm'] = self.df_raw['Período'].map(periodo_map).fillna(self.df_raw['Período'])

            # Lista única de ruas
            self.all_streets = sorted(self.df_raw['Logradouro'].astype(str).unique())
            
            # Recuperar preferências
            saved_prefs = self.load_preferences_from_disk()
            if saved_prefs:
                # Validar se as ruas salvas ainda existem no arquivo novo
                self.selected_streets_set = set(s for s in saved_prefs if s in self.all_streets)
            else:
                self.selected_streets_set = set(self.all_streets) # Padrão: todas selecionadas

            self.refresh_listbox()
            self.btn_process.config(state="normal")
            self.status_var.set(f"Dados carregados! {len(self.df_raw)} registros, {len(self.all_streets)} logradouros.")

        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao carregar dados: {str(e)}")
            self.status_var.set("Erro no carregamento.")

    # --- Lógica da Listbox Otimizada ---
    def refresh_listbox(self):
        self.street_listbox.delete(0, tk.END)
        search = self.search_var.get().lower()
        
        # Filtra ruas baseado na pesquisa
        visible_streets = [s for s in self.all_streets if search in s.lower()]
        
        for street in visible_streets:
            prefix = "[X] " if street in self.selected_streets_set else "[ ] "
            self.street_listbox.insert(tk.END, f"{prefix}{street}")
            
            # Opcional: Colorir fundo se selecionado
            if street in self.selected_streets_set:
                self.street_listbox.itemconfig(tk.END, {'bg': '#e6f3ff'})

        self.update_count_label()

    def filter_list(self, *args):
        self.refresh_listbox()

    def toggle_street_selection(self, event):
        # Pega o item clicado
        selection = self.street_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        text = self.street_listbox.get(index)
        
        # Extrai o nome da rua (remove o prefixo "[X] " ou "[ ] ")
        street_name = text[4:]
        
        if street_name in self.selected_streets_set:
            self.selected_streets_set.remove(street_name)
        else:
            self.selected_streets_set.add(street_name)
            
        # Atualiza visualmente apenas essa linha (mais rápido que refresh total)
        # Mas como temos filtro, o indice da lista pode não bater com a lista total
        # Recarregar lista filtrada é seguro e rápido o suficiente para interações humanas
        self.refresh_listbox()
        
        # Mantém a seleção visual (foco) onde estava
        self.street_listbox.selection_set(index)
        self.street_listbox.see(index)

    def select_visible(self):
        search = self.search_var.get().lower()
        visible_streets = [s for s in self.all_streets if search in s.lower()]
        self.selected_streets_set.update(visible_streets)
        self.refresh_listbox()

    def deselect_visible(self):
        search = self.search_var.get().lower()
        visible_streets = [s for s in self.all_streets if search in s.lower()]
        self.selected_streets_set.difference_update(visible_streets)
        self.refresh_listbox()
        
    def update_count_label(self):
        count = len(self.selected_streets_set)
        total = len(self.all_streets)
        self.count_label.config(text=f"{count}/{total} selecionadas")

    # --- Persistência ---
    def load_preferences_from_disk(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None
        
    def load_preferences(self):
        pass

    def save_preferences_to_disk(self):
        try:
            os.makedirs(CONFIG_FOLDER, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                # Converte set para list para serializar JSON
                json.dump(list(self.selected_streets_set), f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar preferências: {e}")

    # --- Processamento ---
    def start_processing(self):
        self.save_preferences_to_disk()
        
        if not self.selected_streets_set:
            messagebox.showwarning("Aviso", "Selecione pelo menos um logradouro.")
            return

        threading.Thread(target=self.run_analysis).start()

    def run_analysis(self):
        try:
            self.root.after(0, lambda: self.status_var.set("Processando..."))
            self.btn_process.config(state="disabled")

            selected_list = list(self.selected_streets_set)
            df = self.df_raw[self.df_raw['Logradouro'].isin(selected_list)].copy()

            os.makedirs(OUTPUT_FOLDER, exist_ok=True)

            self.generate_top15_report(df)
            self.generate_monthly_report(df)

            self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"Relatórios salvos em:\n{OUTPUT_FOLDER}"))
            self.root.after(0, lambda: self.status_var.set("Concluído."))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Erro."))
        finally:
            self.root.after(0, lambda: self.btn_process.config(state="normal"))

    # =========================================================================
    # LÓGICA DE NEGÓCIO
    # =========================================================================

    def parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            return None

    def generate_top15_report(self, df_full):
        # Lógica Atualizada: Data Final Definida - Dias
        data_fim_str = self.top15_end_date_var.get()
        dias = self.top15_days_var.get()
        
        data_fim = self.parse_date(data_fim_str)
        if not data_fim:
            print("Erro: Data final Top 15 inválida.")
            return

        data_inicio = data_fim - timedelta(days=dias)
        
        mask = (df_full['Data'] >= data_inicio) & (df_full['Data'] <= data_fim)
        df = df_full.loc[mask].copy()
        
        if df.empty:
            print("Aviso: Sem dados Top 15 no período.")
            return

        # Agregação
        df_pivot = df.pivot_table(
            index=['Logradouro', 'Data'], columns='Periodo_Norm', values='Qtd. pessoas', aggfunc='sum', fill_value=0
        ).reset_index()

        for p in ['Madrugada', 'Manhã', 'Tarde', 'Noite']:
            if p not in df_pivot.columns: df_pivot[p] = 0

        stats = df_pivot.groupby('Logradouro').agg({
            'Madrugada': 'mean', 'Manhã': 'mean', 'Tarde': 'mean', 'Noite': 'mean'
        }).reset_index()
        
        stats['Média pessoas'] = stats['Madrugada'] + stats['Manhã'] + stats['Tarde'] + stats['Noite']
        
        total_counts = df.groupby('Logradouro')['Qtd. pessoas'].sum().reset_index().rename(columns={'Qtd. pessoas': 'Soma pessoas'})
        stats = stats.merge(total_counts, on='Logradouro')

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
        
        # Mapeamento de colunas de aglomeração pode variar dependendo do pivot acima
        # Se aglo_stats tiver colunas diretas 'Madrugada', etc.
        cols_aglo = {'Madrugada': 'Qtd Madrugada', 'Manhã': 'Qtd Manhã', 'Tarde': 'Qtd Tarde', 'Noite': 'Qtd Noite'}
        top15_aglo = top15_aglo.rename(columns=cols_aglo)

        # Excel
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

    def generate_monthly_report(self, df_full):
        data_inicio_str = self.monthly_start_var.get()
        data_fim_str = self.monthly_end_date_var.get()
        
        data_inicio = self.parse_date(data_inicio_str)
        data_fim = self.parse_date(data_fim_str)
        
        if not data_inicio or not data_fim:
            print("Erro: Datas Mensais inválidas.")
            return

        mask = (df_full['Data'] >= data_inicio) & (df_full['Data'] <= data_fim)
        df = df_full.loc[mask].copy()

        if df.empty:
            print("Aviso: Sem dados para o relatório mensal.")
            return

        meses_pt = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho',
                   7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
        df['Mes_Num'] = df['Data'].dt.month
        df['Mês'] = df['Mes_Num'].map(meses_pt)
        df['Ano'] = df['Data'].dt.year

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

if __name__ == "__main__":
    root = tk.Tk()
    app = PedestrianAnalyzerApp(root)
    root.mainloop()
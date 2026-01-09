import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
from datetime import datetime, timedelta

# Importando nossos módulos separados
from config import BASE_DIR, CONFIG_FOLDER, CONFIG_FILE, DEFAULT_START_MONTHLY, OUTPUT_FOLDER
import processing

class PedestrianAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador de Fluxo de Pessoas e Aglomerações")
        self.root.geometry("1000x800")
        
        # Variáveis de Estado
        self.df_raw = None
        self.filepath = tk.StringVar()
        self.all_streets = []
        self.selected_streets_set = set()
        
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

        ttk.Button(date_grid, text="Resetar Datas Finais para 'Ontem'", command=self.set_dates_to_yesterday).grid(row=0, column=2, rowspan=2, padx=20)

        # 3. Seleção de Ruas
        street_frame = ttk.LabelFrame(main_frame, text="3. Seleção de Ruas (Logradouros)", padding="10")
        street_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        filter_frame = ttk.Frame(street_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(filter_frame, text="Marcar Filtradas", command=self.select_visible).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Desmarcar Filtradas", command=self.deselect_visible).pack(side=tk.LEFT, padx=2)
        ttk.Label(filter_frame, text="|  Pesquisar:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_list)
        ttk.Entry(filter_frame, textvariable=self.search_var, width=40).pack(side=tk.LEFT)
        self.count_label = ttk.Label(filter_frame, text="0 selecionadas")
        self.count_label.pack(side=tk.RIGHT, padx=10)

        list_container = ttk.Frame(street_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.street_listbox = tk.Listbox(list_container, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set, font=("Consolas", 10))
        self.street_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.street_listbox.yview)
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

            # Chama função do processing.py
            self.df_raw, self.all_streets = processing.load_and_standardize_data(path)
            
            # Recuperar preferências
            saved_prefs = self.load_preferences_from_disk()
            if saved_prefs:
                self.selected_streets_set = set(s for s in saved_prefs if s in self.all_streets)
            else:
                self.selected_streets_set = set(self.all_streets)

            self.refresh_listbox()
            self.btn_process.config(state="normal")
            self.status_var.set(f"Dados carregados! {len(self.df_raw)} registros, {len(self.all_streets)} logradouros.")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao processar dados: {str(e)}")
            self.status_var.set("Erro no carregamento.")

    # --- Lógica da Listbox ---
    def refresh_listbox(self):
        self.street_listbox.delete(0, tk.END)
        search = self.search_var.get().lower()
        visible_streets = [s for s in self.all_streets if search in s.lower()]
        
        for street in visible_streets:
            prefix = "[X] " if street in self.selected_streets_set else "[ ] "
            self.street_listbox.insert(tk.END, f"{prefix}{street}")
            if street in self.selected_streets_set:
                self.street_listbox.itemconfig(tk.END, {'bg': '#e6f3ff'})
        self.update_count_label()

    def filter_list(self, *args):
        self.refresh_listbox()

    def toggle_street_selection(self, event):
        selection = self.street_listbox.curselection()
        if not selection: return
        index = selection[0]
        text = self.street_listbox.get(index)
        street_name = text[4:]
        
        if street_name in self.selected_streets_set:
            self.selected_streets_set.remove(street_name)
        else:
            self.selected_streets_set.add(street_name)
            
        self.refresh_listbox()
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

    # --- Persistência (UI State) ---
    def load_preferences_from_disk(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return None
        return None
    
    def load_preferences(self): pass

    def save_preferences_to_disk(self):
        try:
            os.makedirs(CONFIG_FOLDER, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self.selected_streets_set), f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar preferências: {e}")

    # --- Execução ---
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

            # Filtra o DataFrame antes de passar para o backend
            selected_list = list(self.selected_streets_set)
            df_filtered = self.df_raw[self.df_raw['Logradouro'].isin(selected_list)].copy()

            # Coleta parâmetros da UI
            top15_days = self.top15_days_var.get()
            top15_end = self.top15_end_date_var.get()
            
            monthly_start = self.monthly_start_var.get()
            monthly_end = self.monthly_end_date_var.get()

            # Chama o backend (processing.py)
            res_top15, msg_top15 = processing.generate_top15_excel(df_filtered, top15_days, top15_end)
            res_monthly, msg_monthly = processing.generate_monthly_excel(df_filtered, monthly_start, monthly_end)
            
            if not res_top15: print(f"Top 15: {msg_top15}")
            if not res_monthly: print(f"Mensal: {msg_monthly}")

            self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"Processamento concluído!\nArquivos salvos em:\n{OUTPUT_FOLDER}"))
            self.root.after(0, lambda: self.status_var.set("Concluído."))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro crítico: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Erro."))
        finally:
            self.root.after(0, lambda: self.btn_process.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = PedestrianAnalyzerApp(root)
    root.mainloop()
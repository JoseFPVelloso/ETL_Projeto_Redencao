import tkinter as tk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry
import pandas as pd
import threading
import os
import config
from logic import AnalisadorDados

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(config.TITLE)
        self.geometry(config.GEOMETRY)
        self.configure(bg=config.BG_COLOR)
        
        self.logic = AnalisadorDados()
        self.check_vars_regioes = {} 
        self.check_vars_periodos = {} # Nova variável para os períodos
        
        # Mapa
        ok_mapa, msg_mapa = self.logic.carregar_mapa_regioes()
        self.msg_inicial = msg_mapa if ok_mapa else "⚠️ regioes.xlsx não encontrado"
        
        self._setup_ui()
        
    def _setup_ui(self):
        bg = config.BG_COLOR
        font_head = ("Segoe UI", 11, "bold")
        
        # === CONTAINER PRINCIPAL ===
        main = tk.Frame(self, bg=bg)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 1. ARQUIVO
        frm_top = tk.Frame(main, bg=bg)
        frm_top.pack(fill=tk.X, pady=(0, 10))
        tk.Label(frm_top, text="1. Fonte de Dados", bg=bg, font=font_head).pack(anchor="w")
        
        btn_file = tk.Button(frm_top, text="📂 Selecionar Planilha", command=self.selecionar_arquivo, bg="#e0e0e0")
        btn_file.pack(side=tk.RIGHT)
        self.lbl_arquivo = tk.Label(frm_top, text=self.msg_inicial, bg=bg, fg="gray", font=("Segoe UI", 9))
        self.lbl_arquivo.pack(side=tk.LEFT, padx=(0, 10))

        # 2. ÁREA CENTRAL (SPLIT VIEW)
        tk.Label(main, text="2. Seleção de Regiões", bg=bg, font=font_head).pack(anchor="w")
        
        paned = tk.PanedWindow(main, orient=tk.HORIZONTAL, bg="#ccc", sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # --- LADO ESQUERDO: LISTA DE REGIÕES ---
        frm_left = tk.Frame(paned, bg="white")
        paned.add(frm_left, minsize=300)
        
        tk.Label(frm_left, text="Regiões Disponíveis", bg="#eee", pady=5).pack(fill=tk.X)
        
        self.canvas = tk.Canvas(frm_left, bg="white", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(frm_left, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="white")
        
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # --- LADO DIREITO: LISTA DE DETALHES ---
        frm_right = tk.Frame(paned, bg="#f8f9fa")
        paned.add(frm_right, minsize=300)
        
        self.lbl_detalhe_titulo = tk.Label(frm_right, text="Detalhes da Região", bg="#ddd", pady=5, font=("Segoe UI", 9, "bold"))
        self.lbl_detalhe_titulo.pack(fill=tk.X)
        
        self.lst_logradouros = tk.Listbox(frm_right, bg="#f8f9fa", bd=0, highlightthickness=0, font=("Segoe UI", 9))
        self.lst_logradouros.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.lst_logradouros.insert(0, "Passe o mouse sobre uma região")

        # 3. NOVO: SELEÇÃO DE PERÍODOS
        frm_periodos = tk.Frame(main, bg=bg)
        frm_periodos.pack(fill=tk.X, pady=(10, 0))
        tk.Label(frm_periodos, text="3. Períodos para Análise", bg=bg, font=font_head).pack(anchor="w")
        
        frm_chk_p = tk.Frame(frm_periodos, bg=bg)
        frm_chk_p.pack(fill=tk.X, pady=5)
        
        # Gera checkboxes dinamicamente baseado no config
        for nome_ui, termo_busca in config.PERIODOS_DISPONIVEIS:
            var = tk.BooleanVar(value=True) # Começa marcado por padrão
            self.check_vars_periodos[termo_busca] = var
            cb = tk.Checkbutton(frm_chk_p, text=nome_ui, variable=var, bg=bg, font=("Segoe UI", 9))
            cb.pack(side=tk.LEFT, padx=(0, 15))

        # 4. DATAS E BOTÃO
        frm_bottom = tk.Frame(main, bg=bg)
        frm_bottom.pack(fill=tk.X, pady=(15, 0))
        
        # Datas Lado a Lado
        frm_d = tk.LabelFrame(frm_bottom, text="Ranking Diário (15d)", bg=bg, padx=5, pady=2)
        frm_d.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.dt_ini_d = DateEntry(frm_d, width=10, date_pattern='dd/mm/yyyy'); self.dt_ini_d.pack(side=tk.LEFT)
        tk.Label(frm_d, text="a", bg=bg).pack(side=tk.LEFT)
        self.dt_fim_d = DateEntry(frm_d, width=10, date_pattern='dd/mm/yyyy'); self.dt_fim_d.pack(side=tk.LEFT)
        self.dt_ini_d.set_date(config.DATA_INICIO_DIARIA)
        self.dt_fim_d.set_date(config.DATA_FIM_PADRAO)

        frm_m = tk.LabelFrame(frm_bottom, text="Evolução Mensal", bg=bg, padx=5, pady=2)
        frm_m.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.dt_ini_m = DateEntry(frm_m, width=10, date_pattern='dd/mm/yyyy'); self.dt_ini_m.pack(side=tk.LEFT)
        tk.Label(frm_m, text="a", bg=bg).pack(side=tk.LEFT)
        self.dt_fim_m = DateEntry(frm_m, width=10, date_pattern='dd/mm/yyyy'); self.dt_fim_m.pack(side=tk.LEFT)
        self.dt_ini_m.set_date(config.DATA_INICIO_MENSAL)
        self.dt_fim_m.set_date(config.DATA_FIM_PADRAO)

        # Botão
        self.btn_run = tk.Button(main, text="GERAR RELATÓRIOS", command=self.executar,
                                 bg=config.ACCENT_COLOR, fg="white", font=("Segoe UI", 10, "bold"), pady=8)
        self.btn_run.pack(fill=tk.X, pady=(15, 5))
        
        self.txt_log = tk.Text(main, height=4, bg="#eef", font=("Consolas", 8), state='disabled')
        self.txt_log.pack(fill=tk.BOTH)

    def selecionar_arquivo(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx;*.xls")])
        if path:
            ok, msg = self.logic.carregar_dados(path)
            self.lbl_arquivo.config(text=f"{os.path.basename(path)}", fg="green" if ok else "red")
            self.log(msg)
            if ok: self.criar_lista_regioes()

    def criar_lista_regioes(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        self.check_vars_regioes.clear()
        
        frm_botoes = tk.Frame(self.scroll_frame, bg="white")
        frm_botoes.pack(fill=tk.X, pady=2)
        tk.Button(frm_botoes, text="Todos", command=lambda: self.toggle_all(True), font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=2)
        tk.Button(frm_botoes, text="Nenhum", command=lambda: self.toggle_all(False), font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=2)

        for reg in self.logic.regioes_disponiveis:
            var = tk.BooleanVar(value=True)
            self.check_vars_regioes[reg] = var
            chk = tk.Checkbutton(self.scroll_frame, text=reg, variable=var, bg="white", anchor="w")
            chk.pack(fill="x", padx=5, pady=1)
            chk.bind("<Enter>", lambda e, r=reg: self.mostrar_detalhes(r))

    def toggle_all(self, state):
        for var in self.check_vars_regioes.values(): var.set(state)

    def mostrar_detalhes(self, regiao):
        self.lbl_detalhe_titulo.config(text=f"Logradouros: {regiao}")
        self.lst_logradouros.delete(0, tk.END)
        logs = self.logic.obter_logradouros_da_regiao(regiao)
        if logs:
            for l in logs: self.lst_logradouros.insert(tk.END, f"• {l}")
        else: self.lst_logradouros.insert(tk.END, "(Nenhum logradouro encontrado)")

    def log(self, msg):
        self.txt_log.config(state='normal')
        self.txt_log.insert(tk.END, f"> {msg}\n")
        self.txt_log.see(tk.END); self.txt_log.config(state='disabled')

    def executar(self):
        if self.logic.df is None: return messagebox.showwarning("Ops", "Selecione o arquivo primeiro")
        
        sel_regioes = [r for r, v in self.check_vars_regioes.items() if v.get()]
        if not sel_regioes: return messagebox.showwarning("Ops", "Selecione ao menos uma região")

        sel_periodos = [p for p, v in self.check_vars_periodos.items() if v.get()]
        if not sel_periodos: return messagebox.showwarning("Ops", "Selecione ao menos um período (05h, 10h...)")
        
        self.btn_run.config(state="disabled", text="Processando...")
        # Passamos também os periodos selecionados para a thread
        threading.Thread(target=self._run_thread, args=(sel_regioes, sel_periodos), daemon=True).start()

    def _run_thread(self, sel_regioes, sel_periodos):
        try:
            pd_d = {'inicio': pd.to_datetime(self.dt_ini_d.get_date()), 'fim': pd.to_datetime(self.dt_fim_d.get_date())}
            pd_m = {'inicio': pd.to_datetime(self.dt_ini_m.get_date()), 'fim': pd.to_datetime(self.dt_fim_m.get_date())}
            
            # Chama a lógica passando os períodos
            ok, msg = self.logic.gerar_todos_relatorios(pd_d, pd_m, sel_regioes, sel_periodos)
            self.after(0, lambda: self._end(ok, msg))
        except Exception as e:
            self.after(0, lambda: self._end(False, str(e)))

    def _end(self, ok, msg):
        self.log(msg)
        if ok: messagebox.showinfo("Sucesso", "Relatórios Gerados!")
        else: messagebox.showerror("Erro", msg)
        self.btn_run.config(state="normal", text="GERAR RELATÓRIOS")

if __name__ == "__main__":
    app = App()
    app.mainloop()
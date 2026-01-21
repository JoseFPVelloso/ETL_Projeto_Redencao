import tkinter as tk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry  # Requer pip install tkcalendar
import pandas as pd  # <--- CORREÇÃO: Import necessário para pd.to_datetime
import threading
from datetime import datetime

# Importando seus módulos locais
import config
from logic import AnalisadorDados

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(config.TITLE)
        self.geometry(config.GEOMETRY)
        self.configure(bg=config.BG_COLOR)
        
        # Inicializa a lógica
        self.logic = AnalisadorDados()
        
        # Constrói a interface
        self._setup_ui()
        
    def _setup_ui(self):
        # --- Configurações de Estilo Comuns ---
        lbl_style = {"bg": config.BG_COLOR, "fg": "#333333", "font": ("Segoe UI", 10)}
        header_style = {"bg": config.BG_COLOR, "fg": "#000000", "font": ("Segoe UI", 12, "bold")}
        btn_style = {"bg": "#e1e1e1", "fg": "black", "font": ("Segoe UI", 9), "relief": "groove", "bd": 1}

        # Container Principal (Padding simulado com pack padx/pady)
        main_frame = tk.Frame(self, bg=config.BG_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # --- Seção 1: Seleção de Arquivo ---
        tk.Label(main_frame, text="1. Seleção de Dados", **header_style).pack(anchor="w", pady=(0, 10))
        
        file_frame = tk.Frame(main_frame, bg=config.BG_COLOR)
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Botão selecionar
        btn_file = tk.Button(file_frame, text="📂 Selecionar Planilha (.xlsx)", 
                             command=self.selecionar_arquivo, **btn_style)
        btn_file.pack(side=tk.RIGHT)

        # Label do arquivo (fica à esquerda do botão)
        self.lbl_arquivo = tk.Label(file_frame, text="Nenhum arquivo selecionado", 
                                    bg=config.BG_COLOR, fg="gray", font=("Segoe UI", 9, "italic"))
        self.lbl_arquivo.pack(side=tk.LEFT, padx=(0, 10))
        
        # --- Seção 2: Datas ---
        tk.Label(main_frame, text="2. Período de Análise", **header_style).pack(anchor="w", pady=(0, 10))
        
        date_frame = tk.Frame(main_frame, bg=config.BG_COLOR)
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Data Início
        tk.Label(date_frame, text="Início:", **lbl_style).pack(side=tk.LEFT)
        self.dt_inicio = DateEntry(date_frame, width=12, background='darkblue',
                                   foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.dt_inicio.pack(side=tk.LEFT, padx=5)
        
        # Data Fim
        tk.Label(date_frame, text="Fim:", **lbl_style).pack(side=tk.LEFT, padx=(15, 0))
        self.dt_fim = DateEntry(date_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.dt_fim.set_date(config.DATA_FIM_PADRAO)
        self.dt_fim.pack(side=tk.LEFT, padx=5)

        # Botões de Atalho de Data
        btn_frame = tk.Frame(main_frame, bg=config.BG_COLOR)
        btn_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Button(btn_frame, text="Últimos 15 Dias (Padrão)", 
                  command=self.set_data_diaria, **btn_style).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(btn_frame, text="Desde Junho (Mensal)", 
                  command=self.set_data_mensal, **btn_style).pack(side=tk.LEFT)

        # --- Seção 3: Tipo de Relatório ---
        tk.Label(main_frame, text="3. Gerar Relatório", **header_style).pack(anchor="w", pady=(0, 10))
        
        action_frame = tk.Frame(main_frame, bg=config.BG_COLOR)
        action_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.var_tipo = tk.StringVar(value="ranking")
        
        # Radiobuttons nativos (selectcolor conserta o fundo do quadradinho)
        rb1 = tk.Radiobutton(action_frame, text="Ranking Diário (Divisão por Calendário)", 
                             variable=self.var_tipo, value="ranking",
                             bg=config.BG_COLOR, activebackground=config.BG_COLOR, 
                             selectcolor=config.BG_COLOR, font=("Segoe UI", 10))
        rb1.pack(anchor="w")
        
        rb2 = tk.Radiobutton(action_frame, text="Evolução Mensal (Divisão por Dias Trabalhados)", 
                             variable=self.var_tipo, value="mensal",
                             bg=config.BG_COLOR, activebackground=config.BG_COLOR, 
                             selectcolor=config.BG_COLOR, font=("Segoe UI", 10))
        rb2.pack(anchor="w", pady=(5, 0))

        # Botão Executar (Estilizado para destaque)
        self.btn_run = tk.Button(main_frame, text="GERAR RELATÓRIO", 
                                 bg=config.ACCENT_COLOR, fg="white", 
                                 font=("Segoe UI", 11, "bold"),
                                 relief="flat", pady=10, cursor="hand2",
                                 command=self.executar_analise)
        self.btn_run.pack(fill=tk.X, pady=20)

        # Log
        self.txt_log = tk.Text(main_frame, height=8, font=("Consolas", 9), 
                               bg="#e0e0e0", state='disabled', relief="sunken", bd=1)
        self.txt_log.pack(fill=tk.BOTH, expand=True)
        
        # Configurar estado inicial
        self.set_data_diaria()

    def log(self, mensagem):
        self.txt_log.config(state='normal')
        self.txt_log.insert(tk.END, f"> {mensagem}\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state='disabled')

    def set_data_diaria(self):
        self.dt_inicio.set_date(config.DATA_INICIO_DIARIA)
        self.dt_fim.set_date(config.DATA_FIM_PADRAO)
        self.var_tipo.set("ranking")
        self.log("Definido para Ranking Diário (15 dias).")

    def set_data_mensal(self):
        self.dt_inicio.set_date(config.DATA_INICIO_MENSAL)
        self.dt_fim.set_date(config.DATA_FIM_PADRAO)
        self.var_tipo.set("mensal")
        self.log("Definido para Evolução Mensal (desde Junho).")

    def selecionar_arquivo(self):
        # Garante que filtra por Excel
        caminho = filedialog.askopenfilename(
            title="Selecione a Planilha",
            filetypes=[("Arquivos Excel", "*.xlsx *.xls")]
        )
        if caminho:
            sucesso, msg = self.logic.carregar_dados(caminho)
            if sucesso:
                self.lbl_arquivo.config(text=caminho, fg="green")
                self.log(msg)
            else:
                self.lbl_arquivo.config(text="Erro ao carregar", fg="red")
                messagebox.showerror("Erro", msg)

    def executar_analise(self):
        if self.logic.df is None:
            messagebox.showwarning("Atenção", "Selecione um arquivo primeiro!")
            return

        self.btn_run.config(state='disabled', text="Processando...", bg="#cccccc")
        
        # Thread para processamento pesado
        threading.Thread(target=self._processar_backend, daemon=True).start()

    def _processar_backend(self):
        tipo = self.var_tipo.get()
        # Aqui estava o erro do "pd undefined": agora com 'import pandas as pd' vai funcionar
        try:
            d_inicio = pd.to_datetime(self.dt_inicio.get_date())
            d_fim = pd.to_datetime(self.dt_fim.get_date())

            if tipo == "ranking":
                sucesso, msg = self.logic.gerar_ranking_raw(d_inicio, d_fim)
            else:
                sucesso, msg = self.logic.gerar_evolucao_mensal(d_inicio, d_fim)
            
            # Atualiza UI na thread principal (Tkinter não gosta de updates de outras threads)
            self.after(0, lambda: self._finalizar_processo(sucesso, msg))

        except Exception as e:
            self.after(0, lambda: self._finalizar_processo(False, str(e)))

    def _finalizar_processo(self, sucesso, msg):
        if sucesso:
            self.log("SUCESSO!")
            self.log(msg)
            messagebox.showinfo("Sucesso", "Relatório gerado com sucesso!")
        else:
            self.log(f"Erro: {msg}")
            messagebox.showerror("Erro", msg)
            
        self.btn_run.config(state='normal', text="GERAR RELATÓRIO", bg=config.ACCENT_COLOR)

if __name__ == "__main__":
    app = App()
    app.mainloop()
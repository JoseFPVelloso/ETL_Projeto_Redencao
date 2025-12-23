# main_app.py
# VERSÃO COM ROTINA DE QUADRAS ADICIONADA

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime, timedelta
import threading
import queue
import os
import subprocess
import sys
from pathlib import Path

# Importa as funções de lógica
try:
    import logic_parser
    import logic_report
    import quadras_report # NOVO IMPORT
except ImportError as e:
    messagebox.showerror("Erro de Importação", 
                         f"Erro ao importar módulos.\nDetalhe: {e}\n"
                         "Certifique-se de que logic_parser.py, logic_report.py e quadras_report.py estão na mesma pasta.")
    sys.exit()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automatizador de Relatórios SEPE")
        self.geometry("850x850") # Aumentei um pouco a altura

        self.style = ttk.Style(self)
        
        # --- Caminhos ---
        self.project_root = Path(__file__).resolve().parent
        self.docs_path = self.project_root / "docs"
        self.readme_path = self.project_root / "README.md"
        self.requirements_path = self.project_root / "requirements.txt"
        
        self.docs_path.mkdir(exist_ok=True)

        # Variáveis
        self.raw_file_path = tk.StringVar()
        self.processed_file_path = tk.StringVar()
        self.start_date_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        
        self.final_excel_path = None # Relatório Diário
        self.final_txt_path = None   # Análise Diária
        self.final_quadras_path = None # Relatório Quadras (NOVO)

        self.msg_queue = queue.Queue()

        self.create_widgets()
        self.set_default_dates()
        self.check_queue()

    def set_default_dates(self):
        hoje = datetime.now()
        data_fim = hoje
        data_inicio = hoje - timedelta(days=3)
        self.start_date_var.set(data_inicio.strftime("%d/%m/%Y"))
        self.end_date_var.set(data_fim.strftime("%d/%m/%Y"))

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # --- Utilitários ---
        util_frame = ttk.LabelFrame(main_frame, text="Utilitários e Ajuda", padding="10")
        util_frame.pack(fill="x", pady=5)
        
        self.btn_install_reqs = ttk.Button(util_frame, text="Instalar Dependências", command=self.install_requirements)
        self.btn_install_reqs.pack(side="left", padx=5, pady=5)

        self.btn_open_docs = ttk.Button(util_frame, text="Abrir Pasta Docs", command=self.open_docs_folder)
        self.btn_open_docs.pack(side="left", padx=5, pady=5)

        self.btn_open_readme = ttk.Button(util_frame, text="Ajuda (README)", command=self.open_readme)
        self.btn_open_readme.pack(side="left", padx=5, pady=5)
        
        if not self.requirements_path.exists():
            self.btn_install_reqs.config(state="disabled")

        # --- Passo 1 ---
        parser_frame = ttk.LabelFrame(main_frame, text="Passo 1: Processar Planilha 'Raw'", padding="10")
        parser_frame.pack(fill="x", pady=5)
        parser_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(parser_frame, text="Arquivo Raw:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_raw_file = ttk.Entry(parser_frame, textvariable=self.raw_file_path, state="disabled")
        self.entry_raw_file.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.btn_select_raw = ttk.Button(parser_frame, text="Selecionar...", command=self.select_raw_file)
        self.btn_select_raw.grid(row=0, column=2, padx=5, pady=5)

        self.btn_run_parser = ttk.Button(parser_frame, text="Executar Parser", state="disabled", command=self.run_parser)
        self.btn_run_parser.grid(row=1, column=2, padx=5, pady=5, sticky="e")

        # --- Passo 2 ---
        report_frame = ttk.LabelFrame(main_frame, text="Passo 2: Gerar Relatório Diário", padding="10")
        report_frame.pack(fill="x", pady=5)
        report_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(report_frame, text="Arq. Processado:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_processed_file = ttk.Entry(report_frame, textvariable=self.processed_file_path, state="disabled")
        self.entry_processed_file.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        ttk.Label(report_frame, text="Data Início:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_start_date = ttk.Entry(report_frame, textvariable=self.start_date_var)
        self.entry_start_date.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(report_frame, text="Data Fim:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.entry_end_date = ttk.Entry(report_frame, textvariable=self.end_date_var)
        self.entry_end_date.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        self.btn_run_report = ttk.Button(report_frame, text="Gerar Relatório", state="disabled", command=self.run_report_generator)
        self.btn_run_report.grid(row=2, column=3, padx=5, pady=5, sticky="e")

        # --- Passo 3: Quadras (NOVO) ---
        quadras_frame = ttk.LabelFrame(main_frame, text="Passo 3: Relatório de Quadras", padding="10")
        quadras_frame.pack(fill="x", pady=5)
        
        ttk.Label(quadras_frame, text="Este passo usa o relatório gerado no Passo 2 e aplica o mapeamento de quadras.").pack(anchor="w", padx=5)
        
        self.btn_run_quadras = ttk.Button(quadras_frame, text="Gerar Relatório por Quadras", state="disabled", command=self.run_quadras_generator)
        self.btn_run_quadras.pack(side="right", padx=5, pady=5)

        # --- Log ---
        log_frame = ttk.LabelFrame(main_frame, text="Log de Processamento", padding="10")
        log_frame.pack(fill="both", expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state="disabled", wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)

        # --- Passo 4 (Botões Finais) ---
        results_frame = ttk.LabelFrame(main_frame, text="Passo 4: Abrir Arquivos Gerados", padding="10")
        results_frame.pack(fill="x", pady=5)

        self.btn_open_excel = ttk.Button(results_frame, text="Abrir Diário (.xlsx)", state="disabled", command=lambda: self.open_path(self.final_excel_path))
        self.btn_open_excel.pack(side="left", padx=5, pady=5)

        self.btn_open_txt = ttk.Button(results_frame, text="Abrir Análise (.txt)", state="disabled", command=lambda: self.open_path(self.final_txt_path))
        self.btn_open_txt.pack(side="left", padx=5, pady=5)

        # Botão novo para Quadras
        self.btn_open_quadras = ttk.Button(results_frame, text="Abrir Quadras (.xlsx)", state="disabled", command=lambda: self.open_path(self.final_quadras_path))
        self.btn_open_quadras.pack(side="left", padx=5, pady=5)

    # --- Funções Auxiliares ---
    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END)

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")

    def select_raw_file(self):
        filetype = [("Arquivos Excel", "*.xlsx")]
        filepath = filedialog.askopenfilename(title="Selecione a planilha 'Raw'", filetypes=filetype)
        if filepath:
            self.raw_file_path.set(filepath)
            self.btn_run_parser.config(state="normal")
            
            # Reset steps posteriores
            self.processed_file_path.set("")
            self.btn_run_report.config(state="disabled")
            self.btn_run_quadras.config(state="disabled")
            self.btn_open_excel.config(state="disabled")
            self.btn_open_txt.config(state="disabled")
            self.btn_open_quadras.config(state="disabled")

    def set_ui_state(self, state):
        entry_state = "normal" if state == "normal" else "readonly"
        self.btn_select_raw.config(state=state)
        # Lógica condicional para botões intermediários
        self.btn_run_parser.config(state=state if self.raw_file_path.get() else "disabled")
        self.btn_run_report.config(state=state if self.processed_file_path.get() else "disabled")
        self.btn_run_quadras.config(state=state if self.final_excel_path else "disabled")
        
        self.entry_start_date.config(state=entry_state)
        self.entry_end_date.config(state=entry_state)
        self.btn_install_reqs.config(state=state if self.requirements_path.exists() else "disabled")
        self.btn_open_docs.config(state=state)
        self.btn_open_readme.config(state=state)

    def open_path(self, path):
        if not path or not os.path.exists(str(path)):
            messagebox.showwarning("Aviso", f"Caminho não encontrado ou ainda não gerado.")
            return
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            self.log(f"✓ Abrindo: {path}")
        except Exception as e:
            self.log(f"❌ Erro ao abrir: {e}")
            messagebox.showerror("Erro", f"Não foi possível abrir {path}.\nErro: {e}")

    def open_docs_folder(self):
        self.open_path(self.docs_path)
        
    def open_readme(self):
        if not self.readme_path.exists():
            messagebox.showwarning("Aviso", "README.md não encontrado.")
            return
        self.open_path(self.readme_path)

    def install_requirements(self):
        self.clear_log()
        self.log("INICIANDO INSTALAÇÃO DE DEPENDÊNCIAS...")
        self.log(f"Executando: pip install -r {self.requirements_path.name}")
        self.set_ui_state("disabled")
        threading.Thread(target=self.install_requirements_thread, daemon=True).start()

    def install_requirements_thread(self):
        try:
            command = [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_path)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                       text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            for line in iter(process.stdout.readline, ''):
                self.msg_queue.put(line.strip())
            process.stdout.close()
            if process.wait() == 0:
                self.msg_queue.put(("DONE_INSTALL", "✓ Sucesso!"))
            else:
                self.msg_queue.put(("ERROR", "❌ Erro na instalação."))
        except Exception as e:
            self.msg_queue.put(("ERROR", f"❌ Falha: {e}"))

    # --- PARSER ---
    def run_parser(self):
        self.clear_log()
        self.set_ui_state("disabled")
        self.btn_open_excel.config(state="disabled")
        self.btn_open_txt.config(state="disabled")
        self.btn_open_quadras.config(state="disabled")
        filepath = self.raw_file_path.get()
        threading.Thread(target=self.run_parser_thread, args=(filepath,), daemon=True).start()

    def run_parser_thread(self, filepath):
        def log_callback(message): self.msg_queue.put(message)
        try:
            processed_path, _ = logic_parser.execute_parser(filepath, log_callback)
            if processed_path: self.msg_queue.put(("DONE_PARSER", processed_path))
            else: raise Exception("Falha no parser.")
        except Exception as e: self.msg_queue.put(("ERROR", f"Erro no Parser: {e}"))

    # --- RELATÓRIO DIÁRIO ---
    def run_report_generator(self):
        self.clear_log()
        self.set_ui_state("disabled")
        self.btn_open_excel.config(state="disabled")
        self.btn_open_txt.config(state="disabled")
        self.btn_open_quadras.config(state="disabled")
        self.btn_run_quadras.config(state="disabled")

        filepath = self.processed_file_path.get()
        try:
            start_date = datetime.strptime(self.start_date_var.get(), "%d/%m/%Y")
            end_date = datetime.strptime(self.end_date_var.get(), "%d/%m/%Y")
            if end_date < start_date: raise ValueError("Data fim < Data início")
        except ValueError as e:
            messagebox.showerror("Erro", "Data inválida.")
            self.set_ui_state("normal")
            return
        threading.Thread(target=self.run_report_thread, args=(filepath, start_date, end_date), daemon=True).start()

    def run_report_thread(self, filepath, start_date, end_date):
        def log_callback(message): self.msg_queue.put(message)
        try:
            excel_path, txt_path = logic_report.execute_report_generator(filepath, start_date, end_date, log_callback)
            if excel_path and txt_path: self.msg_queue.put(("DONE_REPORT", excel_path, txt_path))
            else: raise Exception("Falha no gerador.")
        except Exception as e: self.msg_queue.put(("ERROR", f"Erro no Report: {e}"))

    # --- RELATÓRIO QUADRAS (NOVO) ---
    def run_quadras_generator(self):
        # Não limpa o log inteiro, apenas separa
        self.log("-" * 30)
        self.set_ui_state("disabled")
        self.btn_open_quadras.config(state="disabled")
        
        # O input é o resultado do passo anterior
        input_excel = self.final_excel_path
        
        if not input_excel or not os.path.exists(input_excel):
             messagebox.showerror("Erro", "Arquivo do Relatório Diário não encontrado. Rode o Passo 2 primeiro.")
             self.set_ui_state("normal")
             return

        threading.Thread(target=self.run_quadras_thread, args=(input_excel,), daemon=True).start()

    def run_quadras_thread(self, input_file):
        def log_callback(message): self.msg_queue.put(message)
        try:
            output_path = quadras_report.gerar_relatorio_quadras(input_file, log_callback)
            if output_path:
                self.msg_queue.put(("DONE_QUADRAS", output_path))
            else:
                raise Exception("Falha na geração do relatório de Quadras.")
        except Exception as e:
            self.msg_queue.put(("ERROR", f"Erro Quadras: {e}"))


    # --- QUEUE HANDLER ---
    def check_queue(self):
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if isinstance(msg, tuple):
                    type_, payload = msg[0], msg[1]
                    
                    if type_ == "DONE_PARSER":
                        self.log("✓ Parser concluído.")
                        self.processed_file_path.set(payload)
                        self.set_ui_state("normal")
                    
                    elif type_ == "DONE_REPORT":
                        self.log("✓ Relatório Diário concluído.")
                        self.final_excel_path, self.final_txt_path = payload, msg[2]
                        # Habilita botões do diário e o botão de rodar Quadras
                        self.btn_open_excel.config(state="normal")
                        self.btn_open_txt.config(state="normal")
                        self.btn_run_quadras.config(state="normal") # Agora pode rodar o próximo
                        self.set_ui_state("normal")
                        messagebox.showinfo("Sucesso", "Passo 2 Concluído! Você já pode abrir os arquivos ou prosseguir para o Passo 3 (Quadras).")
                    
                    elif type_ == "DONE_QUADRAS":
                        self.log("✓ Relatório Quadras concluído.")
                        self.final_quadras_path = payload
                        self.btn_open_quadras.config(state="normal")
                        self.set_ui_state("normal")
                        # Garante que o botão de rodar quadras continue ativo
                        self.btn_run_quadras.config(state="normal")
                        messagebox.showinfo("Sucesso", "Relatório de Quadras gerado com sucesso!")

                    elif type_ == "DONE_INSTALL":
                        self.log(payload)
                        self.set_ui_state("normal")
                        messagebox.showinfo("Sucesso", "Instalação concluída!")
                    
                    elif type_ == "ERROR":
                        self.log(f"❌ {payload}")
                        messagebox.showerror("Erro", payload)
                        self.set_ui_state("normal")
                        # Reabilita botão de quadras se falhar, mas tínhamos o path anterior
                        if self.final_excel_path:
                            self.btn_run_quadras.config(state="normal")
                else:
                    self.log(str(msg))
        except queue.Empty: pass
        self.after(100, self.check_queue)

if __name__ == "__main__":
    app = App()
    app.mainloop()
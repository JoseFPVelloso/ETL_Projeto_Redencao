# /src/app.py

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
import sys
import pandas as pd
import threading
import queue
from datetime import datetime 

# --- NOVA IMPORTAÇÃO ---
try:
    from tkcalendar import DateEntry
except ImportError:
    messagebox.showerror("Erro de Dependência", 
                         "A biblioteca 'tkcalendar' não foi encontrada.\n\n"
                         "Por favor, instale-a executando:\n"
                         "pip install tkcalendar")
    sys.exit(1)

# --- IMPORTAÇÃO DOS PARSERS E TRANSFORMER ---
try:
    from parsers.parser_Leitos_saude_mental import processar_leitos_saude_mental
    from parsers.parser_Acolhimento_terapeutico import processar_camas_acolhimento
    from parsers.parser_Secretaria_do_desenvolvimento_social import processar_desenvolvimento_social
    
    from padronizador import gerar_tabela_final

except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro Fatal de Importação", 
                             f"Não foi possível importar um parser: {e}\n\n"
                             "Verifique os nomes dos arquivos em 'src/parsers/' ou 'src/transformer.py' "
                             "e os nomes das funções ('def ...') dentro deles.")
    except:
        pass
    sys.exit(1)


# --- CAMINHOS PADRÃO ---
PASTA_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_PADRAO_PDFS = os.path.join(PASTA_RAIZ_PROJETO, "PDFS")
PASTA_PADRAO_TABELAS = os.path.join(PASTA_RAIZ_PROJETO, "Tabelas")


class App:
    """
    Classe principal da aplicação Tkinter (v2.3)
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Extrator de Monitoramentos (v2.3)")
        self.root.geometry("700x650") 

        # --- Variáveis de controle ---
        self.arquivos_carregados = {
            "leitos_sm": "",
            "acolhimento": "",
            "desenvolvimento_social": "" 
        }
        self.labels_arquivos = {} 
        self.date_entry = None 

        self.log_queue = queue.Queue()
        self.create_widgets()
        self.root.after(100, self.check_log_queue)

        os.makedirs(PASTA_PADRAO_PDFS, exist_ok=True)
        os.makedirs(PASTA_PADRAO_TABELAS, exist_ok=True)
        self.log(f"🔎 Monitorando pasta de entrada: {PASTA_PADRAO_PDFS}\n")
        self.log(f"✅ Pasta de saída pronta: {PASTA_PADRAO_TABELAS}\n")
        self.log("----------------------------------------------------\n")
        self.log("Por favor, carregue os 3 arquivos PDF e selecione a data.\n")

    def create_widgets(self):
        """Cria todos os componentes visuais da janela."""
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Seção 1: Carregamento ---
        config_frame = ttk.LabelFrame(main_frame, text="1. Seleção de Arquivos", padding="10")
        config_frame.pack(fill=tk.X, expand=False, pady=5)
        config_frame.grid_columnconfigure(1, weight=1)

        # (Botões de carregar arquivos)
        ttk.Label(config_frame, text="Leitos Saúde Mental:").grid(row=0, column=0, padx=5, pady=8, sticky=tk.W)
        btn1 = ttk.Button(config_frame, text="Carregar...", 
                          command=lambda: self.carregar_arquivo("leitos_sm"))
        btn1.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.labels_arquivos["leitos_sm"] = ttk.Label(config_frame, text="Nenhum arquivo", foreground="grey")
        self.labels_arquivos["leitos_sm"].grid(row=0, column=2, padx=5, pady=5, sticky=tk.E, ipadx=10)

        ttk.Label(config_frame, text="Acolhimento Terapêutico:").grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
        btn2 = ttk.Button(config_frame, text="Carregar...", 
                          command=lambda: self.carregar_arquivo("acolhimento"))
        btn2.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        self.labels_arquivos["acolhimento"] = ttk.Label(config_frame, text="Nenhum arquivo", foreground="grey")
        self.labels_arquivos["acolhimento"].grid(row=1, column=2, padx=5, pady=5, sticky=tk.E, ipadx=10)

        ttk.Label(config_frame, text="Desenvolvimento Social:").grid(row=2, column=0, padx=5, pady=8, sticky=tk.W)
        btn3 = ttk.Button(config_frame, text="Carregar...", 
                          command=lambda: self.carregar_arquivo("desenvolvimento_social"))
        btn3.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        self.labels_arquivos["desenvolvimento_social"] = ttk.Label(config_frame, text="Nenhum arquivo", foreground="grey")
        self.labels_arquivos["desenvolvimento_social"].grid(row=2, column=2, padx=5, pady=5, sticky=tk.E, ipadx=10)


        # --- Seção 2: Seletor de Data (FORMATO CORRIGIDO) ---
        date_frame = ttk.LabelFrame(main_frame, text="2. Seleção de Data", padding="10")
        date_frame.pack(fill=tk.X, expand=False, pady=10)
        
        ttk.Label(date_frame, text="Data do Relatório:").pack(side=tk.LEFT, padx=5)
        
        self.date_entry = DateEntry(
            date_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='dd/MM/yyyy', # <-- MUDANÇA: Formato DD/MM/YYYY
            locale='pt_BR', 
            maxdate=datetime.now()
        )
        self.date_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # --- Seção 3: Ação ---
        action_frame = ttk.Frame(main_frame, padding="0 10 0 10")
        action_frame.pack(fill=tk.X, expand=False)
        self.run_button = ttk.Button(action_frame, text="Processar e Juntar (3 Arquivos)", 
                                     command=self.start_processing)
        self.run_button.pack(fill=tk.X, expand=True, ipady=10)

        # --- Seção 4: Log (Terminal) ---
        log_frame = ttk.LabelFrame(main_frame, text="3. Log de Processamento", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15, state="disabled")
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def log(self, message: str):
        """Adiciona uma mensagem à caixa de log de forma segura."""
        self.log_area.configure(state="normal")
        self.log_area.insert(tk.END, message)
        self.log_area.see(tk.END) # Auto-scroll
        self.log_area.configure(state="disabled")

    def carregar_arquivo(self, tipo_pdf):
        """Pede ao usuário para selecionar um arquivo e guarda o caminho."""
        filepath = filedialog.askopenfilename(
            title=f"Selecione o PDF - {tipo_pdf.replace('_', ' ').title()}",
            filetypes=[("Arquivos PDF", "*.pdf")],
            initialdir=PASTA_PADRAO_PDFS
        )
        if filepath:
            self.arquivos_carregados[tipo_pdf] = filepath
            nome_arquivo = os.path.basename(filepath)
            self.labels_arquivos[tipo_pdf].config(text=nome_arquivo, foreground="green")
            self.log(f"✅ Arquivo '{tipo_pdf}' carregado: {nome_arquivo}\n")

    def start_processing(self):
        """
        Valida os campos e inicia a thread de ETL.
        """
        # 1. Validação dos arquivos
        if not all(self.arquivos_carregados.values()):
            messagebox.showwarning("Atenção", "Por favor, carregue OS 3 tipos de PDF antes de processar.")
            return
            
        # 2. Obter a data (AGORA EM DOIS FORMATOS)
        try:
            data_obj = self.date_entry.get_date()
            # Formato para a coluna no Excel (DD/MM/YYYY)
            data_para_coluna = data_obj.strftime("%d/%m/%Y")
            # Formato para o nome do arquivo (YYYY-MM-DD), que é seguro
            data_para_arquivo = data_obj.strftime("%Y-%m-%d")
            
            self.log(f"📅 Data selecionada para o relatório: {data_para_coluna}\n")
        except Exception as e:
            messagebox.showerror("Erro na Data", f"Formato de data inválido: {e}")
            return

        # 3. Limpa o log e desabilita o botão
        self.log_area.configure(state="normal")
        self.log_area.delete(1.0, tk.END) 
        self.log("----------------------------------------------------\n")
        self.log("🚀 INICIANDO PROCESSAMENTO (3 ARQUIVOS)...\n")
        self.log("----------------------------------------------------\n")
        self.log_area.configure(state="disabled")
        
        self.run_button.config(text="Processando...", state="disabled")
        
        stdout_writer = QueueWriter(self.log_queue)
        sys.stdout = stdout_writer
        sys.stderr = stdout_writer

        # 4. Inicia a thread de processamento (passando as duas datas)
        threading.Thread(
            target=self.processing_thread,
            args=(data_para_coluna, data_para_arquivo,), # Passa as duas strings
            daemon=True
        ).start()

    def processing_thread(self, data_para_coluna, data_para_arquivo): # Recebe as duas
        """
        Esta é a função que roda em segundo plano.
        """
        try:
            # --- 1. Chamar Parsers (Extração) ---
            print("Processando Leitos Saúde Mental (Hospitais)...")
            df_leitos = processar_leitos_saude_mental(self.arquivos_carregados["leitos_sm"])
            
            print("\nProcessando Acolhimento Terapêutico...")
            df_acolhimento = processar_camas_acolhimento(self.arquivos_carregados["acolhimento"])
            
            print("\nProcessando Desenvolvimento Social (SEDS)...")
            df_desenvolvimento_social = processar_desenvolvimento_social(self.arquivos_carregados['desenvolvimento_social'])

            
            # --- 2. Aplicar Transformações (usando o transformer) ---
            df_final_combinado = gerar_tabela_final(
                df_leitos,
                df_acolhimento,
                df_desenvolvimento_social,
                data_para_coluna # Passa a data formatada (DD/MM/YYYY)
            )
            
            # --- 3. LÓGICA DE SALVAR (com novo nome) ---
            # Usa a data segura (YYYY-MM-DD) para o nome do arquivo
            nome_arquivo_saida = f"Tabela_Combinada_Monitoramento_{data_para_arquivo}.xlsx"
            caminho_salvar = os.path.join(PASTA_PADRAO_TABELAS, nome_arquivo_saida)
            
            print(f"\nSalvando arquivo em: {caminho_salvar}...")
            df_final_combinado.to_excel(caminho_salvar, index=False)
            
            print("\n----------------------------------------------------")
            print("✨ PROCESSO CONCLUÍDO COM SUCESSO! ✨")
            print(f"Arquivo final gerado: {nome_arquivo_saida}")
            print("----------------------------------------------------")
            
            self.log_queue.put( ("SUCCESS", caminho_salvar) )

        except Exception as e:
            print("\n----------------------------------------------------")
            print(f"❌ ERRO FATAL DURANTE O PROCESSAMENTO: {e}")
            import traceback
            print(traceback.format_exc()) 
            print("----------------------------------------------------")
            self.log_queue.put( ("ERROR", str(e)) )
            
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            self.log_queue.put( ("DONE",) )

    def check_log_queue(self):
        """Verifica a fila de logs por novas mensagens e atualiza a GUI."""
        try:
            while True:
                message_item = self.log_queue.get_nowait()
                
                if isinstance(message_item, str):
                    self.log(message_item)
                
                elif isinstance(message_item, tuple):
                    command = message_item[0]
                    if command == "SUCCESS":
                        messagebox.showinfo("Sucesso", f"Arquivo combinado salvo com sucesso em:\n{message_item[1]}")
                    elif command == "WARNING":
                        messagebox.showwarning("Atenção", message_item[1])
                    elif command == "ERROR":
                        messagebox.showerror("Erro no Processamento", f"Ocorreu um erro:\n{message_item[1]}")
                    elif command == "DONE":
                        self.run_button.config(text="Processar e Juntar (3 Arquivos)", state="normal")
                        
        except queue.Empty:
            self.root.after(100, self.check_log_queue)


class QueueWriter:
    """ Objeto para redirecionar o stdout para a fila da GUI. """
    def __init__(self, queue):
        self.queue = queue
    def write(self, message):
        self.queue.put(message)
    def flush(self):
        pass

# --- Ponto de Entrada Principal ---
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()


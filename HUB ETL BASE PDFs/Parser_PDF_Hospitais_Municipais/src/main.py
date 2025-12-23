"""
========================================================================
                      SCRIPT DA INTERFACE GRÁFICA (GUI)
========================================================================
Este arquivo cria a interface gráfica (GUI) com Tkinter para
orquestrar o processo de ETL.

Para executar, rode: python gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import sys
import pandas as pd
from datetime import datetime
from typing import Optional
import threading
import queue

# Importa os módulos do seu projeto
import config
import etl_core

class App:
    """
    Classe principal da aplicação Tkinter.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Leitos Hospitalares")
        self.root.geometry("700x600")

        # --- Variáveis de controle ---
        self.pdf_files = []
        self.selected_pdf = tk.StringVar()
        self.output_name = tk.StringVar()
        self.selected_date = tk.StringVar()

        # Fila para comunicação entre a thread de ETL e a GUI
        self.log_queue = queue.Queue()

        # Configura o layout
        self.create_widgets()
        
        # Popula a lista de PDFs inicial
        self.populate_pdf_list()

        # Inicia o monitoramento da fila de logs
        self.root.after(100, self.check_log_queue)

    def create_widgets(self):
        """Cria todos os componentes visuais da janela."""
        
        # --- Frame Principal ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Seção de Configuração ---
        config_frame = ttk.LabelFrame(main_frame, text="1. Configuração", padding="10")
        config_frame.pack(fill=tk.X, expand=False, pady=5)
        config_frame.grid_columnconfigure(1, weight=1) # Faz a coluna 1 (widgets) expandir

        # 1. Seleção de PDF
        ttk.Label(config_frame, text="Arquivo PDF de Entrada:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.pdf_combo = ttk.Combobox(config_frame, textvariable=self.selected_pdf, state="readonly")
        self.pdf_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Botão para atualizar a lista de PDFs
        self.refresh_button = ttk.Button(config_frame, text="Atualizar Lista", command=self.populate_pdf_list)
        self.refresh_button.grid(row=0, column=2, padx=5, pady=5)
        
        # A seleção de um PDF atualiza o nome de saída
        self.pdf_combo.bind("<<ComboboxSelected>>", self.on_pdf_select)

        # 2. Nome de Saída
        ttk.Label(config_frame, text="Nome do Arquivo de Saída:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.output_entry = ttk.Entry(config_frame, textvariable=self.output_name)
        self.output_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)

        # 3. Data
        ttk.Label(config_frame, text="Data (DD/MM/AAAA):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.date_entry = ttk.Entry(config_frame, textvariable=self.selected_date)
        self.date_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        # Define a data de hoje como padrão
        self.selected_date.set(datetime.now().strftime('%d/%m/%Y'))

        # --- Seção de Ação ---
        action_frame = ttk.Frame(main_frame, padding="10")
        action_frame.pack(fill=tk.X, expand=False)

        # 4. Botão de Processar
        self.run_button = ttk.Button(action_frame, text="Processar Arquivo", command=self.start_processing)
        self.run_button.pack(fill=tk.X, expand=True, ipady=10) # Botão grande

        # --- Seção de Log (Terminal) ---
        log_frame = ttk.LabelFrame(main_frame, text="2. Log de Processamento", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 5. Caixa de Texto de Log
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15, state="disabled")
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def log(self, message: str):
        """Adiciona uma mensagem à caixa de log de forma segura."""
        self.log_area.configure(state="normal")
        self.log_area.insert(tk.END, message)
        self.log_area.see(tk.END) # Auto-scroll
        self.log_area.configure(state="disabled")

    def populate_pdf_list(self):
        """Varre a pasta de entrada (definida no config.py) e atualiza o dropdown."""
        self.log("🔎 Mapeando arquivos PDF...\n")
        try:
            # Garante que a pasta de entrada exista
            if not os.path.exists(config.DIR_ENTRADA):
                os.makedirs(config.DIR_ENTRADA)
                self.log(f" pasta '{config.DIR_ENTRADA}' criada. Por favor, adicione seus PDFs.\n")
                self.pdf_files = []
            else:
                self.pdf_files = [f for f in os.listdir(config.DIR_ENTRADA) if f.lower().endswith('.pdf')]
            
            if not self.pdf_files:
                self.log("❌ Nenhum PDF encontrado na pasta de entrada.\n")
                self.pdf_combo['values'] = []
                self.selected_pdf.set("")
                self.output_name.set("")
            else:
                self.pdf_combo['values'] = self.pdf_files
                self.selected_pdf.set(self.pdf_files[0]) # Seleciona o primeiro por padrão
                self.on_pdf_select() # Dispara a atualização do nome de saída
                self.log(f"✅ {len(self.pdf_files)} PDF(s) encontrados.\n")
                
        except Exception as e:
            self.log(f"❌ ERRO ao ler a pasta de entrada: {e}\n")
            messagebox.showerror("Erro de Leitura", f"Não foi possível ler a pasta de PDFs: {e}")

    def on_pdf_select(self, event=None):
        """Chamado quando um PDF é selecionado. Atualiza o nome de saída padrão."""
        pdf_name = self.selected_pdf.get()
        if pdf_name:
            nome_base = os.path.splitext(pdf_name)[0]
            nome_saida_padrao = f"{nome_base}-EXCEL.xlsx"
            self.output_name.set(nome_saida_padrao)

    def start_processing(self):
        """
        Função principal do botão "Processar".
        Valida os campos e inicia a thread de ETL.
        """
        pdf_name = self.selected_pdf.get()
        output_name = self.output_name.get()
        date_str = self.selected_date.get()

        # --- Validações ---
        if not pdf_name:
            messagebox.showerror("Erro", "Por favor, selecione um arquivo PDF.")
            return
        if not output_name:
            messagebox.showerror("Erro", "Por favor, defina um nome para o arquivo de saída.")
            return
        if not output_name.lower().endswith('.xlsx'):
            output_name += ".xlsx"
            self.output_name.set(output_name)
        try:
            # Valida o formato da data
            datetime.strptime(date_str, '%d/%m/%Y')
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido. Use DD/MM/AAAA.")
            return

        # Caminhos completos
        caminho_pdf_completo = os.path.join(config.DIR_ENTRADA, pdf_name)
        caminho_saida_completo = os.path.join(config.DIR_SAIDA, output_name)

        # --- Limpa o log e desabilita o botão ---
        self.log_area.configure(state="normal")
        self.log_area.delete(1.0, tk.END) # Limpa o log
        self.log_area.configure(state="disabled")
        
        self.run_button.config(text="Processando...", state="disabled")
        self.refresh_button.config(state="disabled")
        self.pdf_combo.config(state="disabled")

        # --- Redireciona o stdout para a nossa fila de log ---
        # Isso captura todos os 'print()' do etl_core.py
        stdout_writer = QueueWriter(self.log_queue)
        sys.stdout = stdout_writer
        sys.stderr = stdout_writer

        # --- Inicia a thread de processamento ---
        # Isso impede que a GUI congele
        threading.Thread(
            target=self.processing_thread,
            args=(caminho_pdf_completo, caminho_saida_completo, date_str),
            daemon=True
        ).start()

    def processing_thread(self, caminho_pdf, caminho_saida, data_selecionada):
        """
        Esta é a função que roda em segundo plano.
        Contém a lógica principal do seu main.py
        """
        try:
            # 1. EXTRACT
            # (etl_core.ler_pdf já imprime seu status)
            lista_tabelas_brutas = etl_core.ler_pdf(caminho_pdf, config.PAGINA_PDF)
            if lista_tabelas_brutas is None:
                raise Exception("Nenhuma tabela encontrada ou erro na leitura do PDF.")

            # 2. TRANSFORM
            tabelas_limpas = []
            for tabela_bruta in lista_tabelas_brutas:
                tabela_preparada = etl_core.preparar_tabela(
                    tabela_bruta, 
                    config.NOMES_COLUNAS_LIMPOS,
                    config.MAPEAMENTO_NOMES,
                    config.COLS_INTERNADOS
                )
                if tabela_preparada is not None and not tabela_preparada.empty:
                    tabelas_limpas.append(tabela_preparada)

            if not tabelas_limpas:
                raise Exception("Nenhuma linha de dados válida pôde ser processada.")
                
            df_combinado = pd.concat(tabelas_limpas, ignore_index=True)
            
            df_agregado = etl_core.agregar_dados(df_combinado, config.COLS_INTERNADOS) 
            df_formatado = etl_core.formatar_saida(df_agregado, data_selecionada)
            
            print("\n🔄 Aplicando ordem de hospitais personalizada...")
            df_formatado['Serviço'] = pd.Categorical(
                df_formatado['Serviço'], 
                categories=config.ORDEM_HOSPITAIS,
                ordered=True
            )
            df_final = df_formatado.sort_values('Serviço').reset_index(drop=True)
            print("✅ Ordem personalizada aplicada.")
            
            print("\n✅ Estrutura Final da Tabela (Pronta para salvar):")
            # Envia o DataFrame como string para o log
            print(df_final.to_string())

            # 3. LOAD
            etl_core.salvar_excel(df_final, caminho_saida)
            
            print("\n----------------------------------------------------")
            print("✨ PROCESSO CONCLUÍDO COM SUCESSO! ✨")
            print("----------------------------------------------------")
            
            # Envia um comando especial para a fila para mostrar o pop-up
            self.log_queue.put( ("SUCCESS", caminho_saida) )

        except Exception as e:
            # Em caso de erro, imprime o erro no log
            print("\n----------------------------------------------------")
            print(f"❌ ERRO FATAL DURANTE O PROCESSAMENTO: {e}")
            print("----------------------------------------------------")
            self.log_queue.put( ("ERROR", str(e)) )
            
        finally:
            # Restaura o stdout e reabilita os botões
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            self.log_queue.put( ("DONE",) ) # Sinaliza que a thread terminou

    def check_log_queue(self):
        """Verifica a fila de logs por novas mensagens e atualiza a GUI."""
        try:
            while True:
                message_item = self.log_queue.get_nowait()
                
                if isinstance(message_item, str):
                    # Mensagem de log padrão (vinda do QueueWriter)
                    self.log(message_item)
                
                elif isinstance(message_item, tuple):
                    # Comandos especiais
                    command = message_item[0]
                    if command == "SUCCESS":
                        messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso em:\n{message_item[1]}")
                    elif command == "ERROR":
                        messagebox.showerror("Erro no Processamento", f"Ocorreu um erro:\n{message_item[1]}")
                    elif command == "DONE":
                        # Reabilita os botões
                        self.run_button.config(text="Processar Arquivo", state="normal")
                        self.refresh_button.config(state="normal")
                        self.pdf_combo.config(state="readonly")
                        
        except queue.Empty:
            # A fila está vazia, verifica novamente em 100ms
            self.root.after(100, self.check_log_queue)


class QueueWriter:
    """
    Um objeto 'tipo arquivo' que escreve mensagens em uma fila (Queue).
    Usado para redirecionar o sys.stdout.
    """
    def __init__(self, queue):
        self.queue = queue

    def write(self, message):
        """Coloca a mensagem na fila."""
        self.queue.put(message)

    def flush(self):
        """Necessário para a interface 'tipo arquivo'."""
        pass

# --- Ponto de Entrada Principal ---
if __name__ == "__main__":
    # Garante que as pastas de configuração existam
    # (O etl_core.salvar_excel e populate_pdf_list já fazem isso, 
    # mas é uma boa prática garantir)
    os.makedirs(config.DIR_ENTRADA, exist_ok=True)
    os.makedirs(config.DIR_SAIDA, exist_ok=True)

    # Inicia a aplicação Tkinter
    root = tk.Tk()
    app = App(root)
    root.mainloop()
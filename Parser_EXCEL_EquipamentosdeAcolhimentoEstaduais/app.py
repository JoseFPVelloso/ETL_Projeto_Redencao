import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

# --- IMPORTA O "MOTOR" ---
# Do arquivo parser_equipamentosEstaduais.py, importa a nossa função
from parser_equipamentosEstaduais import processar_arquivo_excel

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Processador de Tabelas Estaduais")
        self.root.geometry("500x250")

        # Variáveis
        self.caminho_arquivo_entrada = tk.StringVar()
        self.nome_arquivo_saida = tk.StringVar(value="Resumo_Estadual_COED.xlsx")
        self.status_var = tk.StringVar(value="Pronto para começar.")

        # --- Layout ---
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        # --- 1. Seleção de Arquivo ---
        frame_input = ttk.Frame(main_frame)
        frame_input.pack(fill="x", pady=5)
        
        ttk.Label(frame_input, text="Arquivo de Entrada:").pack(side="left", padx=5)
        
        self.entry_input = ttk.Entry(frame_input, textvariable=self.caminho_arquivo_entrada, state="readonly", width=40)
        self.entry_input.pack(side="left", fill="x", expand=True)
        
        self.btn_selecionar = ttk.Button(frame_input, text="Selecionar...", command=self.selecionar_arquivo)
        self.btn_selecionar.pack(side="left", padx=5)

        # --- 2. Nome do Arquivo de Saída ---
        frame_output = ttk.Frame(main_frame)
        frame_output.pack(fill="x", pady=10)
        
        ttk.Label(frame_output, text="Nome da Saída:").pack(side="left", padx=5)
        
        self.entry_output = ttk.Entry(frame_output, textvariable=self.nome_arquivo_saida, width=50)
        self.entry_output.pack(side="left", fill="x", expand=True, padx=5)

        # --- 3. Botão de Processar ---
        self.btn_processar = ttk.Button(main_frame, text="Processar Arquivo", command=self.iniciar_processamento)
        self.btn_processar.pack(pady=20, fill="x", ipady=10)
        
        # --- 4. Status ---
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief="sunken", anchor="w", padding=5)
        status_label.pack(fill="x", side="bottom")

    def selecionar_arquivo(self):
        # Abre a caixa de diálogo para selecionar o arquivo
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo Excel",
            filetypes=(("Arquivos Excel", "*.xlsx"), ("Todos os arquivos", "*.*"))
        )
        if caminho:
            self.caminho_arquivo_entrada.set(caminho)
            self.status_var.set(f"Arquivo selecionado: {os.path.basename(caminho)}")

    def iniciar_processamento(self):
        # Pega os caminhos
        arquivo_entrada = self.caminho_arquivo_entrada.get()
        nome_saida = self.nome_arquivo_saida.get()
        
        # Validação
        if not arquivo_entrada:
            messagebox.showerror("Erro", "Por favor, selecione um arquivo de entrada primeiro.")
            return
        if not nome_saida:
            messagebox.showerror("Erro", "Por favor, defina um nome para o arquivo de saída.")
            return
        if not nome_saida.endswith(".xlsx"):
            nome_saida += ".xlsx"
            self.nome_arquivo_saida.set(nome_saida)
            
        # Define a pasta de saída
        pasta_saida = "Tabelas Tratadas"
        # Cria a pasta se ela não existir
        os.makedirs(pasta_saida, exist_ok=True)
        
        # Monta o caminho completo de saída
        caminho_completo_saida = os.path.join(pasta_saida, nome_saida)
        
        # Atualiza o status e desabilita o botão
        self.status_var.set("Processando... Aguarde.")
        self.btn_processar.config(state="disabled")
        self.root.update_idletasks() # Força a atualização da tela

        # --- CHAMA O MOTOR ---
        try:
            # Chama a função que importamos do outro arquivo
            sucesso, erro_msg = processar_arquivo_excel(arquivo_entrada, caminho_completo_saida)
            
            if sucesso:
                messagebox.showinfo("Sucesso", f"Arquivo processado e salvo com sucesso em:\n{caminho_completo_saida}")
                self.status_var.set("Pronto.")
            else:
                # Mostra o erro que o motor retornou
                messagebox.showerror("Erro no Processamento", f"Ocorreu um erro ao processar o arquivo:\n\n{erro_msg}")
                self.status_var.set("Erro. Tente novamente.")
                
        except Exception as e:
            # Este é um erro inesperado, como falha ao importar
            messagebox.showerror("Erro Inesperado", f"Um erro crítico ocorreu:\n\n{e}")
            self.status_var.set("Erro crítico.")

        # Reabilita o botão
        self.btn_processar.config(state="normal")


# --- Inicia a Aplicação ---
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
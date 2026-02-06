import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pandas as pd
from datetime import datetime
import uuid
from conversor_bairral import extrair_dados_final_v2

class ConversorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extrator de Altas Bairral")
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        
        self.arquivos_selecionados = []

        # Estilização básica
        tk.Label(root, text="Consolidador de PDFs - BAIRRAL", font=("Arial", 14, "bold")).pack(pady=15)
        
        self.btn_selecionar = tk.Button(root, text="1. Selecionar Arquivos PDF", 
                                        command=self.selecionar_arquivos, width=30, height=2)
        self.btn_selecionar.pack(pady=5)

        self.lbl_status = tk.Label(root, text="Nenhum arquivo na fila", fg="red")
        self.lbl_status.pack(pady=10)

        self.btn_processar = tk.Button(root, text="2. Gerar Planilha Excel", command=self.processar, 
                                      bg="#2E7D32", fg="white", font=("Arial", 10, "bold"),
                                      width=30, height=2, state="disabled")
        self.btn_processar.pack(pady=10)

    def selecionar_arquivos(self):
        self.arquivos_selecionados = filedialog.askopenfilenames(
            title="Selecione os PDFs do Bairral",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if self.arquivos_selecionados:
            qtd = len(self.arquivos_selecionados)
            self.lbl_status.config(text=f"{qtd} arquivo(s) selecionado(s)", fg="blue")
            self.btn_processar.config(state="normal")

    def processar(self):
        # 1. Preparar pasta de saída
        pasta_saida = "Relatorios_Extraidos"
        if not os.path.exists(pasta_saida):
            os.makedirs(pasta_saida)

        dados_acumulados = []
        
        # 2. Extração
        for caminho in self.arquivos_selecionados:
            resultado = extrair_dados_final_v2(caminho)
            if resultado:
                # Mapeamento para a ordem e nomes de colunas desejados
                linha = {
                    "Nome do paciente": resultado["Nome"],
                    "DN": resultado["Data Nascimento"],
                    "Nome da mãe": resultado["Nome da Mãe"],
                    "Data admissão": resultado["Data Entrada"],
                    "Unidade": resultado["Unidade"],
                    "Tipo de alta": resultado["Tipo de Alta"],
                    "Data da alta": resultado["Data Alta"],
                    "Equipamento Social de passagem": resultado["Equipamento Social"]
                }
                dados_acumulados.append(linha)

        if not dados_acumulados:
            messagebox.showwarning("Atenção", "Nenhum dado pôde ser extraído dos arquivos.")
            return

        # 3. Gerar Excel usando Pandas
        try:
            df = pd.DataFrame(dados_acumulados)
            
            # Garantir a ordem exata das colunas solicitada
            colunas_ordem = [
                             "Nome do paciente", 
                             "DN", 
                             "Nome da mãe", 
                             "Data admissão", 
                             "Unidade", 
                             "Tipo de alta", 
                             "Data da alta",
                             "Equipamento Social de passagem"
                             ]
            df = df[colunas_ordem]

            data_id = datetime.now().strftime("%d%m%y")
            random_id = uuid.uuid4().hex[:4] # Gera 4 caracteres aleatórios (ex: a1b2)
            nome_arquivo = f"consolidado_bairral_{data_id}_{random_id}.xlsx"
            caminho_final = os.path.join(pasta_saida, nome_arquivo)
            
            # Salvando o arquivo
            df.to_excel(caminho_final, index=False, engine='openpyxl')
            
            messagebox.showinfo("Sucesso", f"Planilha gerada com sucesso em:\n{caminho_final}")
            
            # Abre a pasta para o usuário
            os.startfile(os.path.abspath(pasta_saida))
            
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Feche o arquivo Excel se ele estiver aberto!\nErro: {e}")
        
        self.btn_processar.config(state="disabled")
        self.lbl_status.config(text="Processamento finalizado!", fg="green")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConversorApp(root)
    root.mainloop()
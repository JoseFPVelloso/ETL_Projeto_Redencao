import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pandas as pd
from datetime import datetime
import uuid
from conversor_bezerra_menezes import extrair_dados_bezerra

class BezerraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extrator IBM - Bezerra de Menezes")
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        
        self.arquivos_selecionados = []
        tk.Label(root, text="Consolidador de PDFs - IBM", font=("Arial", 14, "bold")).pack(pady=15)
        
        self.btn_selecionar = tk.Button(root, text="1. Selecionar PDFs Bezerra", 
                                        command=self.selecionar_arquivos, width=30, height=2)
        self.btn_selecionar.pack(pady=5)

        self.lbl_status = tk.Label(root, text="Nenhum arquivo na fila", fg="red")
        self.lbl_status.pack(pady=10)

        self.btn_processar = tk.Button(root, text="2. Gerar Planilha Excel", command=self.processar, 
                                      bg="#00796B", fg="white", font=("Arial", 10, "bold"),
                                      width=30, height=2, state="disabled")
        self.btn_processar.pack(pady=10)

    def selecionar_arquivos(self):
        self.arquivos_selecionados = filedialog.askopenfilenames(
            title="Selecione os PDFs do Bezerra",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if self.arquivos_selecionados:
            self.lbl_status.config(text=f"{len(self.arquivos_selecionados)} arquivo(s) selecionado(s)", fg="blue")
            self.btn_processar.config(state="normal")

    def processar(self):
            pasta_saida = "Relatorios_Extraidos"
            if not os.path.exists(pasta_saida):
                os.makedirs(pasta_saida)

            dados_acumulados = []
            for caminho in self.arquivos_selecionados:
                res = extrair_dados_bezerra(caminho)
                if res:
                    dados_acumulados.append({
                        "Nome do paciente": res["Nome"],
                        "DN": res["Data Nascimento"],
                        "Nome da mãe": res["Nome da Mãe"],
                        "Data admissão": res["Data Entrada"],
                        "Unidade": res["Unidade"],
                        "Tipo de alta": res["Tipo de Alta"],
                        "Data da alta": res["Data Alta"],
                        "Equipamento Social de passagem": res["Equipamento Social"],
                        "CAPS REFERENCIA": res["CAPS REFERENCIA"] # <-- NOVA LINHA ADICIONADA AQUI
                    })

            if not dados_acumulados:
                messagebox.showwarning("Erro", "Nenhum dado extraído.")
                return

            try:
                df = pd.DataFrame(dados_acumulados)
                # <-- NOVA COLUNA ADICIONADA NA LISTA ABAIXO
                colunas = ["Nome do paciente", "DN", "Nome da mãe", "Data admissão", 
                        "Unidade", "Tipo de alta", "Data da alta", "Equipamento Social de passagem", "CAPS REFERENCIA"] 
                df = df[colunas]

                data_id = datetime.now().strftime("%d%m%y")
                random_id = uuid.uuid4().hex[:4]
                nome_arquivo = f"Instituto_Bezerra_de_menezes_{data_id}_{random_id}.xlsx"
                caminho_final = os.path.join(pasta_saida, nome_arquivo)
                
                df.to_excel(caminho_final, index=False)
                messagebox.showinfo("Sucesso", f"Gerado: {nome_arquivo}")
                os.startfile(os.path.abspath(pasta_saida))
            except Exception as e:
                messagebox.showerror("Erro", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = BezerraApp(root)
    root.mainloop()
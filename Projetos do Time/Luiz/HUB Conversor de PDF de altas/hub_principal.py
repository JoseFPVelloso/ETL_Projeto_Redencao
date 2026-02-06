import tkinter as tk
from tkinter import messagebox
import subprocess
import os

class HubConversores:
    def __init__(self, root):
        self.root = root
        self.root.title("Hub de Conversores - Projeto Redenção")
        self.root.geometry("400x500")
        
        # Título
        tk.Label(root, text="Painel de Automação", font=("Arial", 16, "bold")).pack(pady=20)

        # Botão: Tutorial
        self.btn_tutorial = tk.Button(root, text="📖 Tutorial de Uso", command=self.abrir_tutorial, 
                                      width=30, height=2, bg="#FFF176")
        self.btn_tutorial.pack(pady=5)

        # Botão: Instalar Requisitos
        self.btn_reqs = tk.Button(root, text="⚙️ Instalar Requerimentos", command=self.instalar_requisitos, 
                                   width=30, height=2, bg="#E0E0E0")
        self.btn_reqs.pack(pady=5)

        tk.Label(root, text="Selecione o Conversor:", font=("Arial", 10, "italic")).pack(pady=15)

        # Botão: Conversor Bairral
        self.btn_bairral = tk.Button(root, text="PDF Bairral", command=lambda: self.abrir_conversor("bairral"), 
                                      width=30, height=2, bg="#4FC3F7")
        self.btn_bairral.pack(pady=5)

        # Botão: Conversor Y (Exemplo)
        self.btn_y = tk.Button(root, text="Conversor Y", command=lambda: self.abrir_conversor("conversor_y"), 
                                width=30, height=2, bg="#4DB6AC")
        self.btn_y.pack(pady=5)

    def abrir_tutorial(self):
        # Você pode abrir um arquivo de texto ou uma messagebox
        texto_tutorial = (
            "1. Clique em 'Instalar Requerimentos' na primeira vez.\n"
            "2. Escolha o conversor desejado.\n"
            "3. Selecione os arquivos PDF e clique em Gerar Planilha.\n"
            "4. O resultado estará na pasta 'Relatorios_Extraidos'."
        )
        messagebox.showinfo("Tutorial", texto_tutorial)

    def instalar_requisitos(self):
        try:
            messagebox.showinfo("Aguarde", "Instalando bibliotecas... Isso pode levar alguns segundos.")
            subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
            messagebox.showinfo("Sucesso", "Requisitos instalados com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao instalar: {e}")

    def abrir_conversor(self, nome_pasta):
        # Define o caminho para o script da interface dentro da subpasta
        caminho_script = os.path.join("conversores", nome_pasta, f"interface_{nome_pasta}.py")
        
        if os.path.exists(caminho_script):
            # Abre o processo sem travar o Hub
            subprocess.Popen(["python", caminho_script])
        else:
            messagebox.showerror("Erro", f"Script não encontrado:\n{caminho_script}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HubConversores(root)
    root.mainloop()
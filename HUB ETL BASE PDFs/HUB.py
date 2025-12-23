import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys


# --- Determina o diretório base da aplicação (onde o script/exe está) ---
# Isso é crucial para que o PyInstaller funcione corretamente
if getattr(sys, 'frozen', False):
    # Se estiver rodando como um .exe (congelado pelo PyInstaller)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Se estiver rodando como um script .py normal
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print(f"Diretório Base da Aplicação (BASE_DIR): {BASE_DIR}")

# --- Constantes de Caminhos ---
# Todos os caminhos agora são absolutos, baseados no BASE_DIR
# e usam os.path.join() para compatibilidade (sem barras \ ou /)

# Projeto 0: O Próprio Hub (está no BASE_DIR)
HUB_README = os.path.join(BASE_DIR, "README.md")
HUB_REQUIREMENTS = os.path.join(BASE_DIR, "requirements.txt") 

# Projeto 1: Monitoramentos
MONITOR_DIR = os.path.join(BASE_DIR, "Parser_PDF_Monitoramentos_Hospitalares")
# Diretório onde o app.py está e de onde deve ser executado (cwd)
MONITOR_SCRIPT_DIR = os.path.join(MONITOR_DIR, "src")
MONITOR_SCRIPT_NAME = "app.py" # Apenas o nome do script
# Caminhos para os botões "Abrir Pasta" (baseado nos seus screenshots)
MONITOR_README = os.path.join(MONITOR_DIR, "README.md")
MONITOR_PDF_DIR = os.path.join(MONITOR_DIR, "PDFs")
MONITOR_RELATORIO_DIR = os.path.join(MONITOR_DIR, "Tabelas")

# Projeto 2: Hospitais Municipais
HOSPITAL_DIR = os.path.join(BASE_DIR, "Parser_PDF_Hospitais_Municipais")
# Diretório onde o main.py está e de onde deve ser executado (cwd)
HOSPITAL_SCRIPT_DIR = os.path.join(HOSPITAL_DIR, "src")
HOSPITAL_SCRIPT_NAME = "main.py" # Apenas o nome do script
# Caminhos para os botões "Abrir Pasta" (são dentro do 'src' deste projeto)
HOSPITAL_README = os.path.join(HOSPITAL_SCRIPT_DIR, "README.md")
HOSPITAL_PDF_DIR = os.path.join(HOSPITAL_SCRIPT_DIR, "PDF")
HOSPITAL_RELATORIO_DIR = os.path.join(HOSPITAL_SCRIPT_DIR, "Tabelas")

# --- Funções Principais ---

def launch_app(script_name, working_dir):
    """
    Função genérica para lançar um script Python.
    'script_name' é apenas o nome do arquivo (ex: "app.py")
    'working_dir' é o caminho absoluto para o diretório que contém o script.
    """
    print(f"Tentando iniciar {script_name} em {working_dir}...")
    
    # Verifica se o diretório de trabalho existe
    if not os.path.isdir(working_dir):
        print(f"Erro: Diretório de trabalho não encontrado: {working_dir}")
        messagebox.showerror("Erro de Caminho", f"O diretório de trabalho não foi encontrado:\n{working_dir}")
        return
        
    # Verifica se o script existe dentro do diretório de trabalho
    script_path_check = os.path.join(working_dir, script_name)
    if not os.path.isfile(script_path_check):
        print(f"Erro: Script não encontrado em: {script_path_check}")
        messagebox.showerror("Erro de Caminho", f"O script não foi encontrado:\n{script_path_check}")
        return

    try:
        # sys.executable é o caminho para o interpretador Python
        # 'script_name' é o arquivo a ser executado
        # 'cwd=working_dir' diz ao subprocesso para "entrar" nesse diretório antes de rodar
        # Isso garante que qualquer caminho relativo DENTRO do app.py/main.py funcione
        subprocess.Popen([sys.executable, script_name], cwd=working_dir)
    except Exception as e:
        print(f"Erro ao iniciar {script_name}: {e}")
        messagebox.showerror("Erro ao Executar", f"Não foi possível iniciar o script:\n{e}")

def open_path(path):
    """
    Abre um arquivo ou pasta no explorador de arquivos padrão.
    'path' JÁ DEVE SER um caminho absoluto.
    """
    try:
        # O 'path' que recebemos já é absoluto, construído com BASE_DIR
        print(f"Tentando abrir: {path}")
        
        if not os.path.exists(path):
            print("Erro: Caminho não existe.")
            messagebox.showwarning("Caminho não Encontrado", 
                                   f"Não foi possível encontrar o item:\n{path}")
            return
            
        # 'os.path.realpath' garante que o caminho é resolvido
        abs_path = os.path.realpath(path)
        
        # 'start' é um comando do CMD, funciona bem no Windows
        # A string vazia "" é um "título" para a janela 'start'
        os.system(f'start "" "{abs_path}"')
        
    except Exception as e:
        print(f"Erro ao abrir {path}: {e}")
        messagebox.showerror("Erro ao Abrir", f"Não foi possível abrir o caminho:\n{e}")

def install_requirements():
    """
    Abre um novo terminal (CMD) e executa o pip install -r requirements.txt.
    """
    print(f"Tentando instalar os requisitos de: {HUB_REQUIREMENTS}")
    
    # Verifica se o arquivo requirements.txt existe
    if not os.path.exists(HUB_REQUIREMENTS):
        print(f"Erro: {HUB_REQUIREMENTS} não encontrado.")
        messagebox.showwarning("Arquivo não Encontrado", 
                               f"Não foi possível encontrar o arquivo:\n{HUB_REQUIREMENTS}")
        return

    try:
        # sys.executable é o caminho exato para o python.exe que está rodando o script
        # 'start cmd /k' abre um novo terminal e o MANTÉM ABERTO (/k)
        # Usamos HUB_REQUIREMENTS, que agora é um caminho absoluto (e entre aspas)
        command = f'start cmd /k "{sys.executable} -m pip install -r \"{HUB_REQUIREMENTS}\""'
        print(f"Executando: {command}")
        os.system(command)
    except Exception as e:
        print(f"Erro ao tentar abrir o CMD para instalação: {e}")
        messagebox.showerror("Erro ao Instalar",
                             f"Não foi possível iniciar o processo de instalação:\n{e}")

# --- Configuração da Interface Gráfica (GUI) ---

root = tk.Tk()
root.title("Hub de Aplicativos ETL")
root.geometry("450x420") # Um pouco mais alto para os novos botões

# --- Estilos ---
style = ttk.Style()
style.configure("TLabelFrame.Label", font=("Arial", 14, "bold"))
style.configure("TButton", font=("Arial", 11, "bold"), padding=10)
style.configure("Small.TButton", font=("Arial", 9), padding=5)

# Frame principal com padding
main_frame = ttk.Frame(root, padding=15)
main_frame.pack(expand=True, fill=tk.BOTH)

# --- NOVA SEÇÃO: Ferramentas do Hub ---
hub_tools_frame = ttk.Frame(main_frame)
hub_tools_frame.pack(fill="x", pady=(0, 5))

btn_readme_hub = ttk.Button(hub_tools_frame, 
                            text="Abrir README do Hub", 
                            command=lambda: open_path(HUB_README),
                            style="Small.TButton")
btn_readme_hub.pack(side="left", fill="x", expand=True, padx=2)

btn_install_req = ttk.Button(hub_tools_frame, 
                             text="Instalar Requisitos", 
                             command=install_requirements,
                             style="Small.TButton")
btn_install_req.pack(side="left", fill="x", expand=True, padx=2)

# --- Linha Separadora ---
separator = ttk.Separator(main_frame, orient='horizontal')
separator.pack(fill='x', pady=10)


# --- Seção 1: Parser de Monitoramentos ---
monitor_frame = ttk.LabelFrame(main_frame, text="Parser de Monitoramentos")
monitor_frame.pack(fill="x", expand=True, pady=(5, 10))

btn_run_monitor = ttk.Button(monitor_frame, 
                             text="EXECUTAR APLICAÇÃO", 
                             # ATUALIZADO AQUI: Passa o NOME e o DIRETÓRIO CWD
                             command=lambda: launch_app(MONITOR_SCRIPT_NAME, MONITOR_SCRIPT_DIR),
                             style="TButton")
btn_run_monitor.pack(fill="x", expand=True, pady=10, padx=10)

links_monitor_frame = ttk.Frame(monitor_frame)
links_monitor_frame.pack(fill="x", expand=True, pady=(0, 10), padx=10)

btn_readme_m = ttk.Button(links_monitor_frame, 
                          text="Abrir README", 
                          command=lambda: open_path(MONITOR_README),
                          style="Small.TButton")
btn_readme_m.pack(side="left", fill="x", expand=True, padx=2)

btn_pdf_m = ttk.Button(links_monitor_frame, 
                       text="Pasta PDFs", 
                       command=lambda: open_path(MONITOR_PDF_DIR),
                       style="Small.TButton")
btn_pdf_m.pack(side="left", fill="x", expand=True, padx=2)

btn_tabela_m = ttk.Button(links_monitor_frame, 
                          text="Pasta Relatórios", 
                          command=lambda: open_path(MONITOR_RELATORIO_DIR),
                          style="Small.TButton")
btn_tabela_m.pack(side="left", fill="x", expand=True, padx=2)


# --- Seção 2: Parser de Hospitais Municipais ---
hospital_frame = ttk.LabelFrame(main_frame, text="Parser de Hospitais Municipais")
hospital_frame.pack(fill="x", expand=True, pady=10)

btn_run_hospital = ttk.Button(hospital_frame, 
                              text="EXECUTAR APLICAÇÃO", 
                              # ATUALIZADO AQUI: Passa o NOME e o DIRETÓRIO CWD
                              command=lambda: launch_app(HOSPITAL_SCRIPT_NAME, HOSPITAL_SCRIPT_DIR),
                              style="TButton")
btn_run_hospital.pack(fill="x", expand=True, pady=10, padx=10)

links_hospital_frame = ttk.Frame(hospital_frame)
links_hospital_frame.pack(fill="x", expand=True, pady=(0, 10), padx=10)

btn_readme_h = ttk.Button(links_hospital_frame, 
                          text="Abrir README", 
                          command=lambda: open_path(HOSPITAL_README),
                          style="Small.TButton")
btn_readme_h.pack(side="left", fill="x", expand=True, padx=2)

btn_pdf_h = ttk.Button(links_hospital_frame, 
                       text="Pasta PDF", 
                       command=lambda: open_path(HOSPITAL_PDF_DIR),
                       style="Small.TButton")
btn_pdf_h.pack(side="left", fill="x", expand=True, padx=2)

btn_tabela_h = ttk.Button(links_hospital_frame, 
                          text="Pasta Relatórios", 
                          command=lambda: open_path(HOSPITAL_RELATORIO_DIR),
                          style="Small.TButton")
btn_tabela_h.pack(side="left", fill="x", expand=True, padx=2)


# --- Inicia a aplicação ---
root.mainloop()

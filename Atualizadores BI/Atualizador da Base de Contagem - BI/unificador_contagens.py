import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from datetime import datetime

def processar_contagens():
    # Caminhos dos arquivos selecionados na interface
    path_cnr = entry_cnr.get()
    path_sms = entry_sms.get()
    path_dic = entry_dic.get()

    if not all([path_cnr, path_sms, path_dic]):
        messagebox.showwarning("Atenção", "Selecione todos os três arquivos.")
        return

    try:
        # 1. Carregamento dos dados (Assumindo XLSX conforme regra de uso)
        df_cnr = pd.read_excel(path_cnr)
        df_sms = pd.read_excel(path_sms)
        df_dic = pd.read_excel(path_dic)

        # Padronização de colunas para união
        # CNR: Data, Equipe, Logradouro, Período, Quantidade
        df_cnr['Referencia'] = 'CNR'
        df_cnr = df_cnr.rename(columns={'Quantidade': 'Contagem'})

        # SMS: Equipe, Data, Logradouro, Período, Qtd. pessoas
        df_sms['Referencia'] = 'SMS'
        df_sms = df_sms.rename(columns={'Qtd. pessoas': 'Contagem'})

        # 2. União das contagens
        colunas_finais = ['Equipe', 'Data', 'Logradouro', 'Período', 'Contagem', 'Referencia']
        df_unido = pd.concat([df_cnr[colunas_finais], df_sms[colunas_finais]], ignore_index=True)

        # 3. Verificação de Logradouros Novos
        logradouros_nas_contagens = set(df_unido['Logradouro'].unique())
        logradouros_no_dicionario = set(df_dic['Original'].unique())
        novos_logradouros = list(logradouros_nas_contagens - logradouros_no_dicionario)

        # Atualização do dicionário se houver novidades
        qtd_antiga = len(df_dic)
        if novos_logradouros:
            df_novos = pd.DataFrame({'Original': novos_logradouros})
            # Criamos as outras colunas vazias para preenchimento manual posterior
            for col in [c for c in df_dic.columns if c != 'Original']:
                df_novos[col] = ""
            
            df_dic_atualizado = pd.concat([df_dic, df_novos], ignore_index=True)
        else:
            df_dic_atualizado = df_dic

        # 4. Criação da estrutura de pastas e salvamento
        now = datetime.now()
        timestamp_pasta = now.strftime("%d_%m_%y_%Hh%M")
        timestamp_arquivo = now.strftime("%d_%m_%Y")
        
        diretorio_script = os.path.dirname(os.path.abspath(__file__))
        nome_pasta = f"arquivos_contagens_{timestamp_pasta}"
        caminho_saida = os.path.join(diretorio_script, nome_pasta)
        
        if not os.path.exists(caminho_saida):
            os.makedirs(caminho_saida)

        # Salvando arquivos (Sempre XLSX)
        path_out_contagem = os.path.join(caminho_saida, f"Contagem_{timestamp_arquivo}.xlsx")
        path_out_dic = os.path.join(caminho_saida, f"dicionario_{timestamp_arquivo}.xlsx")

        df_unido.to_excel(path_out_contagem, index=False)
        df_dic_atualizado.to_excel(path_out_dic, index=False)

        # 5. Saída no Terminal/Log do Tkinter
        txt_log.delete(1.0, tk.END)
        txt_log.insert(tk.END, f"Processamento concluído!\n")
        txt_log.insert(tk.END, f"Pasta: {nome_pasta}\n")
        txt_log.insert(tk.END, f"---------------------------\n")
        txt_log.insert(tk.END, f"Quantidade anterior no dicionário: {qtd_antiga}\n")
        txt_log.insert(tk.END, f"Novos logradouros encontrados: {len(novos_logradouros)}\n\n")
        
        if novos_logradouros:
            txt_log.insert(tk.END, "Lista de novos logradouros:\n")
            for log in novos_logradouros:
                txt_log.insert(tk.END, f"- {log}\n")
        
        messagebox.showinfo("Sucesso", f"Arquivos gerados na pasta {nome_pasta}")

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")

# --- Interface Gráfica Tkinter ---
root = tk.Tk()
root.title("Consolidador de Contagens - Redenção")
root.geometry("600x500")

def selecionar_arquivo(entry_field):
    filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    entry_field.delete(0, tk.END)
    entry_field.insert(0, filename)

# Layout
tk.Label(root, text="Arquivo CNR (XLSX):").pack(pady=(10,0))
entry_cnr = tk.Entry(root, width=70)
entry_cnr.pack()
tk.Button(root, text="Procurar", command=lambda: selecionar_arquivo(entry_cnr)).pack()

tk.Label(root, text="Arquivo SMS (XLSX):").pack(pady=(10,0))
entry_sms = tk.Entry(root, width=70)
entry_sms.pack()
tk.Button(root, text="Procurar", command=lambda: selecionar_arquivo(entry_sms)).pack()

tk.Label(root, text="Dicionário de Logradouros (XLSX):").pack(pady=(10,0))
entry_dic = tk.Entry(root, width=70)
entry_dic.pack()
tk.Button(root, text="Procurar", command=lambda: selecionar_arquivo(entry_dic)).pack()

tk.Button(root, text="PROCESSAR ARQUIVOS", command=processar_contagens, bg="green", fg="white", font=('Helvetica', 10, 'bold')).pack(pady=20)

tk.Label(root, text="Log de Processamento:").pack()
txt_log = tk.Text(root, height=10, width=70)
txt_log.pack(pady=5)

root.mainloop()
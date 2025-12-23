"""
Script para identificar os nomes das colunas do arquivo e exportar informações
"""

import pandas as pd
import os

# Configuração dos caminhos
pasta_entrada = r'C:\Users\x504693\Documents\projetos\projeto_etl_dados\data\raw'
pasta_saida = r'C:\Users\x504693\Documents\projetos\projeto_etl_dados\docs'

print("Carregando lista de arquivos...")
arquivos = [f for f in os.listdir(pasta_entrada) if os.path.isfile(os.path.join(pasta_entrada, f))]

if not arquivos:
    print("Nenhum arquivo encontrado na pasta especificada.")
    exit()

print("\nArquivos disponíveis:")
for i, arquivo in enumerate(arquivos, 1):
    print(f"{i:2d}. {arquivo}")

while True:
    try:
        selecao = int(input("\nDigite o número do arquivo que deseja analisar: "))
        if 1 <= selecao <= len(arquivos):
            arquivo_selecionado = arquivos[selecao - 1]
            break
        else:
            print("Número inválido. Tente novamente.")
    except ValueError:
        print("Por favor, digite apenas números.")

# Construindo caminhos completos
caminho_arquivo = os.path.join(pasta_entrada, arquivo_selecionado)
nome_saida = os.path.splitext(arquivo_selecionado)[0] + '_analise.txt'
caminho_saida = os.path.join(pasta_saida, nome_saida)

print(f"\nCarregando arquivo selecionado: {arquivo_selecionado}")
try:
    df = pd.read_excel(caminho_arquivo)
except Exception as e:
    print(f"Erro ao ler o arquivo: {e}")
    exit()

# Cria e escreve no arquivo de texto
with open(caminho_saida, 'w', encoding='utf-8') as f:
    f.write("="*100 + "\n")
    f.write(f"ANÁLISE DO ARQUIVO: {arquivo_selecionado}\n")
    f.write("="*100 + "\n\n")

    f.write("COLUNAS DISPONÍVEIS NO ARQUIVO\n")
    f.write("-"*50 + "\n")
    
    for i, col in enumerate(df.columns, 1):
        f.write(f"{i:2d}. {col}\n")

    f.write("\n" + "="*100 + "\n")
    f.write(f"Total: {len(df.columns)} colunas\n")
    f.write(f"Total de registros: {len(df)}\n")
    f.write("="*100 + "\n\n")

    f.write("="*100 + "\n")
    f.write("AMOSTRA DOS DADOS (20 primeiras linhas)\n")
    f.write("="*100 + "\n")
    f.write(df.head(20).to_string())

print(f"\nArquivo de análise exportado em: {caminho_saida}")

# Mantém as impressões no console também
print("\n" + "="*100)
print(f"ANÁLISE DO ARQUIVO: {arquivo_selecionado}")
print("="*100)

print("\nCOLUNAS DISPONÍVEIS NO ARQUIVO")
print("-"*50)

for i, col in enumerate(df.columns, 1):
    print(f"{i:2d}. {col}")

print("\n" + "="*100)
print(f"Total: {len(df.columns)} colunas")
print(f"Total de registros: {len(df)}")
print("="*100)

print("\n" + "="*100)
print("AMOSTRA DOS DADOS (20 primeiras linhas)")
print("="*100)
print(df.head(20))
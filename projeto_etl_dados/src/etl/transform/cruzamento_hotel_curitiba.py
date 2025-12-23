"""
Script para cruzar dados entre duas planilhas e exportar resultados
"""

import pandas as pd
import os
from datetime import datetime

# Configuração dos caminhos
pasta_raw = r'C:\Users\x504693\Documents\projetos\projeto_etl_dados\data\raw'
pasta_processed = r'C:\Users\x504693\Documents\projetos\projeto_etl_dados\data\processed'

def selecionar_arquivo(pasta, mensagem):
    """Função para selecionar arquivo interativamente"""
    print(f"\n{mensagem}")
    arquivos = [f for f in os.listdir(pasta) if f.endswith(('.xlsx', '.xls'))]
    
    if not arquivos:
        print("Nenhum arquivo Excel encontrado na pasta especificada.")
        return None
    
    print("\nArquivos disponíveis:")
    for i, arquivo in enumerate(arquivos, 1):
        print(f"{i:2d}. {arquivo}")
    
    while True:
        try:
            selecao = int(input("\nDigite o número do arquivo: "))
            if 1 <= selecao <= len(arquivos):
                return arquivos[selecao - 1]
            else:
                print("Número inválido. Tente novamente.")
        except ValueError:
            print("Por favor, digite apenas números.")

# Selecionar os arquivos
arquivo_cidadaos = selecionar_arquivo(pasta_raw, "Selecione o arquivo de Cidadãos Vinculados:")
if not arquivo_cidadaos:
    exit()

arquivo_beneficios = selecionar_arquivo(pasta_raw, "Selecione o arquivo de Cidadãos x Benefícios:")
if not arquivo_beneficios:
    exit()

# Construir caminhos completos
caminho_cidadaos = os.path.join(pasta_raw, arquivo_cidadaos)
caminho_beneficios = os.path.join(pasta_raw, arquivo_beneficios)

print(f"\nCarregando arquivos...")
print(f"Arquivo de cidadãos: {arquivo_cidadaos}")
print(f"Arquivo de benefícios: {arquivo_beneficios}")

try:
    # Carregar os dados
    df_cidadaos = pd.read_excel(caminho_cidadaos)
    df_beneficios = pd.read_excel(caminho_beneficios)
    
    print(f"\nDimensões dos arquivos:")
    print(f"Cidadãos: {df_cidadaos.shape[0]} linhas x {df_cidadaos.shape[1]} colunas")
    print(f"Benefícios: {df_beneficios.shape[0]} linhas x {df_beneficios.shape[1]} colunas")
    
except Exception as e:
    print(f"Erro ao ler os arquivos: {e}")
    exit()

# Pré-processamento dos dados
print("\nPré-processando dados...")

# Converter datas para formato consistente
df_cidadaos['Data de Nascimento'] = pd.to_datetime(df_cidadaos['Data de Nascimento'], format='%d/%m/%Y', errors='coerce')
df_beneficios['dataNascimento'] = pd.to_datetime(df_beneficios['dataNascimento'], errors='coerce')

# Limpar e padronizar nomes
df_cidadaos['Nome_limpo'] = df_cidadaos['Nome do Cidadão'].str.upper().str.strip()
df_beneficios['Nome_limpo'] = df_beneficios['Nome_do_Cidadao'].str.upper().str.strip()

# Realizar o cruzamento
print("Realizando cruzamento dos dados...")

# Fazer o merge usando nome e data de nascimento
df_cruzado = df_beneficios.merge(
    df_cidadaos[['Nome_limpo', 'Data de Nascimento', 'Dias de Permanência']],
    left_on=['Nome_limpo', 'dataNascimento'],
    right_on=['Nome_limpo', 'Data de Nascimento'],
    how='left',
    suffixes=('', '_cidadaos')
)

# Remover colunas auxiliares
df_cruzado = df_cruzado.drop(['Nome_limpo', 'Data de Nascimento'], axis=1, errors='ignore')

# Reorganizar colunas - colocar Dias de Permanência em uma posição mais visível
colunas = list(df_cruzado.columns)
if 'Dias de Permanência' in colunas:
    colunas.remove('Dias de Permanência')
    # Inserir após Dias_de_Permanencia se existir, senão após Nome_do_Cidadao
    if 'Dias_de_Permanencia' in colunas:
        posicao = colunas.index('Dias_de_Permanencia') + 1
    else:
        posicao = colunas.index('Nome_do_Cidadao') + 1
    colunas.insert(posicao, 'Dias de Permanência')
    df_cruzado = df_cruzado[colunas]

# Estatísticas do cruzamento
total_registros = len(df_cruzado)
registros_com_dias = df_cruzado['Dias de Permanência'].notna().sum()
percentual_match = (registros_com_dias / total_registros) * 100

print(f"\nResultado do cruzamento:")
print(f"Total de registros: {total_registros}")
print(f"Registros com Dias de Permanência encontrados: {registros_com_dias}")
print(f"Percentual de match: {percentual_match:.2f}%")

# Salvar o arquivo cruzado
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
nome_arquivo_saida = f"dados_cruzados_{timestamp}.xlsx"
caminho_saida = os.path.join(pasta_processed, nome_arquivo_saida)

try:
    # Salvar como Excel
    df_cruzado.to_excel(caminho_saida, index=False)
    
    # Salvar também um resumo em TXT
    nome_resumo = f"resumo_cruzamento_{timestamp}.txt"
    caminho_resumo = os.path.join(pasta_processed, nome_resumo)
    
    with open(caminho_resumo, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("RESUMO DO CRUZAMENTO DE DADOS\n")
        f.write("="*80 + "\n\n")
        f.write(f"Data do processamento: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Arquivo de cidadãos: {arquivo_cidadaos}\n")
        f.write(f"Arquivo de benefícios: {arquivo_beneficios}\n")
        f.write(f"Arquivo de saída: {nome_arquivo_saida}\n\n")
        f.write("ESTATÍSTICAS:\n")
        f.write(f"Total de registros: {total_registros}\n")
        f.write(f"Registros com Dias de Permanência encontrados: {registros_com_dias}\n")
        f.write(f"Percentual de match: {percentual_match:.2f}%\n\n")
        f.write("PRIMEIRAS LINHAS DO RESULTADO:\n")
        f.write("="*80 + "\n")
        
        # Mostrar apenas algumas colunas importantes no resumo
        colunas_resumo = ['Nome_do_Cidadao', 'dataNascimento', 'Dias_de_Permanencia', 'Dias de Permanência', 'NomeBeneficio']
        colunas_disponiveis = [col for col in colunas_resumo if col in df_cruzado.columns]
        
        if colunas_disponiveis:
            f.write(df_cruzado[colunas_disponiveis].head(10).to_string())
        else:
            f.write(df_cruzado.head(10).to_string())
    
    print(f"\nArquivos salvos com sucesso!")
    print(f"Dados cruzados: {caminho_saida}")
    print(f"Resumo do processamento: {caminho_resumo}")
    
    # Mostrar preview no console
    print(f"\nPreview dos dados cruzados (primeiras 5 linhas):")
    print("="*80)
    colunas_preview = ['Nome_do_Cidadao', 'dataNascimento', 'Dias de Permanência', 'NomeBeneficio']
    colunas_preview_disponiveis = [col for col in colunas_preview if col in df_cruzado.columns]
    
    if colunas_preview_disponiveis:
        print(df_cruzado[colunas_preview_disponiveis].head().to_string())
    else:
        print(df_cruzado.head().to_string())
        
except Exception as e:
    print(f"Erro ao salvar os arquivos: {e}")

print(f"\nProcessamento concluído!")
# src/etl/cruzamento_okuhara.py
import pandas as pd
import os
import unicodedata
import re

def normalizar_texto(texto):
    """
    Normaliza o texto removendo acentos, convertendo para maiúsculas, 
    removendo espaços extras e tratando caracteres especiais como Ç
    """
    if pd.isna(texto):
        return texto
    
    # Converte para string se não for
    texto = str(texto)
    
    # Remove acentos e caracteres especiais
    texto = unicodedata.normalize('NFKD', texto)
    
    # Substitui caracteres especiais manualmente
    substituicoes = {
        'Ç': 'C',
        'ç': 'C',
    }
    
    for char, substituicao in substituicoes.items():
        texto = texto.replace(char, substituicao)
    
    # Remove todos os diacríticos (acentos)
    texto = ''.join([c for c in texto if not unicodedata.combining(c)])
    
    # Converte para maiúsculas e remove espaços extras
    texto = texto.upper().strip()
    
    # Remove múltiplos espaços
    texto = re.sub(r'\s+', ' ', texto)
    
    return texto

def cruzar_planilhas_okuhara():
    # Define os caminhos dos arquivos
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    raw_dir = os.path.join(base_dir, 'data', 'raw')
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    
    # Cria a pasta processed se não existir
    os.makedirs(processed_dir, exist_ok=True)
    
    # Caminhos completos dos arquivos
    arquivo_abordados = os.path.join(raw_dir, 'nomes_Abordados.xlsx')
    arquivo_okuhara = os.path.join(raw_dir, 'Base Okuhara Kohei.xlsx')
    
    print(f"Procurando arquivos em:")
    print(f"Abordados: {arquivo_abordados}")
    print(f"Okuhara: {arquivo_okuhara}")
    
    # Verifica se os arquivos existem
    if not os.path.exists(arquivo_abordados):
        print(f"ERRO: Arquivo não encontrado: {arquivo_abordados}")
        return
    if not os.path.exists(arquivo_okuhara):
        print(f"ERRO: Arquivo não encontrado: {arquivo_okuhara}")
        return
    
    # Carrega as planilhas
    try:
        df_abordados = pd.read_excel(arquivo_abordados)
        df_okuhara = pd.read_excel(arquivo_okuhara)
        
        print(f"Planilha abordados carregada: {len(df_abordados)} registros")
        print(f"Planilha Okuhara carregada: {len(df_okuhara)} registros")
        
    except Exception as e:
        print(f"Erro ao carregar planilhas: {e}")
        return
    
    # Verifica se as colunas existem
    if 'Nomes' not in df_abordados.columns:
        print(f"ERRO: Coluna 'Nomes' não encontrada em nomes_Abordados.xlsx")
        print(f"Colunas disponíveis: {list(df_abordados.columns)}")
        return
        
    if 'NOME COMPLETO' not in df_okuhara.columns:
        print(f"ERRO: Coluna 'NOME COMPLETO' não encontrada em Base Okuhara Kohei.xlsx")
        print(f"Colunas disponíveis: {list(df_okuhara.columns)}")
        return
    
    # Cria colunas normalizadas para comparação
    print("Normalizando nomes para comparação...")
    df_abordados['Nomes_Normalizados'] = df_abordados['Nomes'].apply(normalizar_texto)
    df_okuhara['NOME_COMPLETO_Normalizado'] = df_okuhara['NOME COMPLETO'].apply(normalizar_texto)
    
    # Mostra alguns exemplos de nomes normalizados
    print("\nExemplos de nomes normalizados da planilha de abordados:")
    for nome in df_abordados['Nomes_Normalizados'].head(10):
        print(f"  - {nome}")
    
    print("\nExemplos de nomes normalizados da base Okuhara:")
    for nome in df_okuhara['NOME_COMPLETO_Normalizado'].head(10):
        print(f"  - {nome}")
    
    # Realiza o cruzamento pelos nomes normalizados
    df_cruzado = df_okuhara[df_okuhara['NOME_COMPLETO_Normalizado'].isin(df_abordados['Nomes_Normalizados'])]
    
    # Remove as colunas normalizadas do resultado final
    df_cruzado = df_cruzado.drop(columns=['NOME_COMPLETO_Normalizado'])
    
    # Salva o resultado
    output_path = os.path.join(processed_dir, 'cruzamento_nomes_base_okuhara.xlsx')
    df_cruzado.to_excel(output_path, index=False)
    
    print(f"\nPlanilha cruzada salva em: {output_path}")
    print(f"Total de registros encontrados: {len(df_cruzado)}")
    
    # Mostra alguns exemplos dos nomes cruzados
    if len(df_cruzado) > 0:
        print("\nPrimeiros 10 nomes cruzados:")
        for nome in df_cruzado['NOME COMPLETO'].head(10):
            print(f"  - {nome}")
        
        # Mostra também os nomes correspondentes da planilha de abordados
        nomes_cruzados_normalizados = df_cruzado['NOME COMPLETO'].apply(normalizar_texto).unique()
        nomes_abordados_correspondentes = df_abordados[df_abordados['Nomes_Normalizados'].isin(nomes_cruzados_normalizados)]['Nomes']
        
        print("\nNomes correspondentes na planilha de abordados:")
        for nome in nomes_abordados_correspondentes.head(10):
            print(f"  - {nome}")
    else:
        print("\nNenhum registro encontrado mesmo após normalização.")
        print("Vamos tentar uma abordagem mais flexível com correspondência parcial...")
        
        # Tentativa com correspondência parcial
        encontrar_correspondencias_parciais_okuhara(df_abordados, df_okuhara)

def encontrar_correspondencias_parciais_okuhara(df_abordados, df_okuhara):
    """
    Tenta encontrar correspondências parciais quando a correspondência exata falha
    """
    print("\n--- TENTATIVA COM CORRESPONDÊNCIA PARCIAL ---")
    
    # Coleta todos os nomes normalizados
    nomes_abordados = set(df_abordados['Nomes_Normalizados'].dropna())
    nomes_okuhara = set(df_okuhara['NOME_COMPLETO_Normalizado'].dropna())
    
    correspondencias = []
    
    for nome_abordado in nomes_abordados:
        for nome_okuhara in nomes_okuhara:
            # Verifica se um nome contém o outro (correspondência parcial)
            if nome_abordado in nome_okuhara or nome_okuhara in nome_abordado:
                # Encontra o nome original nas planilhas
                nome_abordado_original = df_abordados[df_abordados['Nomes_Normalizados'] == nome_abordado]['Nomes'].iloc[0]
                nome_okuhara_original = df_okuhara[df_okuhara['NOME_COMPLETO_Normalizado'] == nome_okuhara]['NOME COMPLETO'].iloc[0]
                
                correspondencias.append({
                    'Nome_Abordado': nome_abordado_original,
                    'Nome_Okuhara': nome_okuhara_original,
                    'Normalizado_Abordado': nome_abordado,
                    'Normalizado_Okuhara': nome_okuhara
                })
    
    if correspondencias:
        print(f"\nEncontradas {len(correspondencias)} correspondências parciais:")
        for i, corresp in enumerate(correspondencias[:20]):  # Mostra no máximo 20
            print(f"  {i+1}. '{corresp['Nome_Abordado']}' -> '{corresp['Nome_Okuhara']}'")
        
        if len(correspondencias) > 20:
            print(f"  ... e mais {len(correspondencias) - 20} correspondências")
            
        # Pergunta se quer salvar essas correspondências
        salvar = input("\nDeseja salvar essas correspondências em um arquivo? (s/n): ")
        if salvar.lower() == 's':
            df_correspondencias = pd.DataFrame(correspondencias)
            output_corresp_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data', 'processed', 'correspondencias_parciais_okuhara.xlsx'
            )
            df_correspondencias.to_excel(output_corresp_path, index=False)
            print(f"Arquivo salvo em: {output_corresp_path}")
    else:
        print("Nenhuma correspondência parcial encontrada.")

if __name__ == "__main__":
    cruzar_planilhas_okuhara()
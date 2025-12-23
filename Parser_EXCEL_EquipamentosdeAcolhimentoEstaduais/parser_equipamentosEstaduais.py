import pandas as pd
from openpyxl.utils import get_column_letter

def processar_arquivo_excel(caminho_entrada, caminho_saida_completo):
    """
    Função "motor" que lê um arquivo Excel, o processa conforme as regras,
    e o salva em um novo local.
    
    Retorna (True, None) em caso de sucesso.
    Retorna (False, str(e)) em caso de erro.
    """
    try:
        # --- 2. Leitura e Limpeza Inicial ---
        # sheet_name=1 lê a SEGUNDA ABA do arquivo
        df = pd.read_excel(caminho_entrada, sheet_name=1) 
        
        df = df.dropna(how='all')
        df_limpo = df[df['TIPOLOGIA'] != 'TOTAL GERAL'].copy()
        
        # Preenche a data antes de remover a primeira linha
        df_limpo['DATA'] = df_limpo['DATA'].ffill()
        
        # Remove a primeira e a última linha de dados
        df_limpo = df_limpo.dropna(subset=['TIPOLOGIA'])
        df_limpo = df_limpo.iloc[1:-1].copy()
        
        # --- 3. Criação da Nova Estrutura de Dados ---
        df_novo = pd.DataFrame()
        
        # Formata a Tipologia (ex: "Casas de passagem")
        df_novo['Tipologia'] = df_limpo['TIPOLOGIA'].str.capitalize()
        df_novo['Equipamento'] = 'COED' 
        
        # Formata a Data como DD/MM/YYYY
        df_novo['Data'] = pd.to_datetime(df_limpo['DATA']).dt.strftime('%d/%m/%Y')
        
        df_novo['Leitos Instalados'] = pd.to_numeric(df_limpo['VAGAS INFORMADAS'], errors='coerce')
        df_novo['Leitos Operacionais'] = pd.to_numeric(df_limpo['VAGAS INFORMADAS'], errors='coerce')
        df_novo['Ocupação Atual'] = pd.to_numeric(df_limpo['OCUPAÇÃO ATUAL'], errors='coerce')

        # --- 4. Cálculos ---
        df_novo['Leitos Disponiveis'] = df_novo['Leitos Operacionais'] - df_novo['Ocupação Atual']
        
        # Arredonda a Taxa de Ocupação para 0 casas decimais
        df_novo['Taxa de ocupação'] = ((df_novo['Ocupação Atual'] / df_novo['Leitos Operacionais']).fillna(0) * 100).round(0)

        # --- 5. Reordenar Colunas ---
        ordem_colunas = [
            'Tipologia', 
            'Equipamento', 
            'Data', 
            'Leitos Instalados', 
            'Leitos Operacionais', 
            'Ocupação Atual',
            'Taxa de ocupação',  # Posição trocada
            'Leitos Disponiveis' # Posição trocada
        ]
        df_novo = df_novo[ordem_colunas]

        # --- 6. Salvamento ---
        with pd.ExcelWriter(caminho_saida_completo, engine='openpyxl') as writer:
            df_novo.to_excel(writer, sheet_name='Resumo_COED', index=False)
            
            # Formata a coluna "Taxa de ocupação" como número inteiro
            workbook = writer.book
            worksheet = writer.sheets['Resumo_COED']
            
            col_idx = df_novo.columns.get_loc('Taxa de ocupação') + 1
            col_letter = get_column_letter(col_idx)
            
            for cell in worksheet[col_letter][1:]: 
                cell.number_format = '0' # Formato '0' (sem decimais)
        
        # Se tudo deu certo, retorna True e nenhuma mensagem de erro
        return True, None 
        
    except Exception as e:
        # Se der erro, retorna False e a mensagem de erro
        return False, str(e)
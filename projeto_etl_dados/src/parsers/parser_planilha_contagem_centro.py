# Parser Completo - Logradouros e Períodos
# Baseado na análise exploratória de: Contagem_diaria_centro - Padronizada.xlsx
#
# Autor: Análise automatizada
# Data: 31/10/2025

# %% [markdown]
# # 1. Configuração Inicial

# %%
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

print("=" * 80)
print("PARSER COMPLETO - LOGRADOUROS E PERÍODOS")
print("=" * 80)
print(f"✓ Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

# %% [markdown]
# # 2. Definir Tipos de Logradouro

# %%
# Tipos identificados na análise (ordenados por frequência)
TIPOS_LOGRADOURO = [
    'Rua', 'Avenida', 'Alameda', 'Praça', 'Viaduto', 
    'Terminal', 'Largo', 'Parque', 'Passarela',
    # Tipos adicionais que podem aparecer
    'Travessa', 'Viela', 'Galeria', 'Escadaria',
    'Jardim', 'Quadra', 'Rodovia', 'Estrada',
    'Ladeira', 'Beco', 'Vila', 'Conjunto',
    'Ponte', 'Túnel', 'Elevado', 'Corredor', 'Pátio', 'Complexo'
]

PATTERN_TIPOS = '|'.join(TIPOS_LOGRADOURO)

# %% [markdown]
# # 3. Função de Parser de Logradouro

# %%
def parse_logradouro(logradouro_original):
    """
    Parse logradouro otimizado com extração de número mesmo sem vírgula
    
    PADRÕES SUPORTADOS:
    - "Tipo Nome, Número" (com vírgula)
    - "Tipo Nome Número" (sem vírgula - será corrigido)
    - "Tipo Nome, Número - Complemento"
    - "Tipo Nome Número - Complemento"
    - "Tipo Nome" (sem número)
    
    CORREÇÕES APLICADAS:
    - Extrai número mesmo quando não há vírgula
    - Padroniza formato: "Tipo Nome, Número" ou "Tipo Nome, Número - Complemento"
    
    Args:
        logradouro_original (str): Logradouro completo
        
    Returns:
        dict: {
            'tipo_logradouro': str,
            'nome_logradouro': str,
            'numero_logradouro': str,
            'complemento_logradouro': str,
            'logradouro_padronizado': str (formato correto)
        }
    """
    
    resultado = {
        'tipo_logradouro': '',
        'nome_logradouro': '',
        'numero_logradouro': '',
        'complemento_logradouro': '',
        'logradouro_padronizado': ''
    }
    
    # Validação
    if pd.isna(logradouro_original) or str(logradouro_original).strip() == '':
        return resultado
    
    logradouro = str(logradouro_original).strip()
    
    # ========================================
    # PASSO 1: Separar COMPLEMENTO (por " - ")
    # ========================================
    if ' - ' in logradouro:
        partes = logradouro.split(' - ', 1)
        parte_principal = partes[0].strip()
        resultado['complemento_logradouro'] = partes[1].strip()
    else:
        parte_principal = logradouro
    
    # ========================================
    # PASSO 2: Separar NÚMERO
    # ========================================
    tipo_nome = parte_principal
    numero = ''
    
    # Caso 1: Tem vírgula (padrão correto)
    if ',' in parte_principal:
        partes = parte_principal.split(',', 1)
        tipo_nome = partes[0].strip()
        numero = partes[1].strip()
    else:
        # Caso 2: Sem vírgula - tentar extrair número do final
        # Padrões: "Avenida Duque de Caxias 784" ou "Rua Aurora 123A"
        match = re.search(r'\s+(\d+[A-Za-z]?)$', parte_principal)
        if match:
            numero = match.group(1).strip()
            tipo_nome = parte_principal[:match.start()].strip()
    
    resultado['numero_logradouro'] = numero
    
    # ========================================
    # PASSO 3: Separar TIPO e NOME
    # ========================================
    tipo_match = re.match(rf'^({PATTERN_TIPOS})\b', tipo_nome, re.IGNORECASE)
    
    if tipo_match:
        resultado['tipo_logradouro'] = tipo_match.group(1).title()
        resultado['nome_logradouro'] = tipo_nome[tipo_match.end():].strip()
    else:
        # Fallback: primeira palavra como tipo
        partes = tipo_nome.split(maxsplit=1)
        if len(partes) >= 2:
            resultado['tipo_logradouro'] = partes[0].title()
            resultado['nome_logradouro'] = partes[1]
        elif len(partes) == 1:
            resultado['nome_logradouro'] = partes[0]
    
    # ========================================
    # PASSO 4: Limpeza final
    # ========================================
    for key in resultado:
        if resultado[key] and key != 'logradouro_padronizado':
            resultado[key] = ' '.join(resultado[key].split())
    
    # ========================================
    # PASSO 5: Montar logradouro padronizado
    # ========================================
    # Formato: "Tipo Nome, Número" ou "Tipo Nome, Número - Complemento"
    logr_padrao = resultado['tipo_logradouro']
    
    if resultado['nome_logradouro']:
        logr_padrao += ' ' + resultado['nome_logradouro']
    
    if resultado['numero_logradouro']:
        logr_padrao += ', ' + resultado['numero_logradouro']
    
    if resultado['complemento_logradouro']:
        logr_padrao += ' - ' + resultado['complemento_logradouro']
    
    resultado['logradouro_padronizado'] = logr_padrao.strip()
    
    return resultado

print("✓ Função parse_logradouro() criada")

# %% [markdown]
# # 4. Função de Parser de Período

# %%
def parse_periodo(periodo_original):
    """
    Parse período otimizado para os padrões identificados
    
    PADRÕES IDENTIFICADOS:
    - "05h - Madrugada" (padrão correto - 99.4%)
    - "Madrugada - 05h" (ordem invertida - 0.6%)
    - "10h - Manhã " (com espaço extra - 0.04%)
    
    CORREÇÕES APLICADAS:
    - Remove espaços extras
    - Inverte ordem quando necessário
    - Padroniza para "HHh - Descrição"
    
    Args:
        periodo_original (str): Período original
        
    Returns:
        str: Período padronizado no formato "HHh - Descrição"
    """
    
    # Validação
    if pd.isna(periodo_original) or str(periodo_original).strip() == '':
        return ''
    
    # Limpar espaços extras (corrige "10h - Manhã ")
    periodo = str(periodo_original).strip()
    
    # Mapeamento direto dos valores corretos (99.4% dos casos)
    mapeamento_direto = {
        '05h - Madrugada': '05h - Madrugada',
        '10h - Manhã': '10h - Manhã',
        '15h - Tarde': '15h - Tarde',
        '20h - Noite': '20h - Noite',
    }
    
    if periodo in mapeamento_direto:
        return mapeamento_direto[periodo]
    
    # ========================================
    # CORREÇÃO: Ordem invertida (0.6% dos casos)
    # ========================================
    # Padrões: "Madrugada - 05h", "Manhã - 10h", etc.
    mapeamento_invertido = {
        'Madrugada - 05h': '05h - Madrugada',
        'Manhã - 10h': '10h - Manhã',
        'Tarde - 15h': '15h - Tarde',
        'Noite - 20h': '20h - Noite',
    }
    
    if periodo in mapeamento_invertido:
        return mapeamento_invertido[periodo]
    
    # ========================================
    # EXTRAÇÃO: Padrão genérico (fallback)
    # ========================================
    # Para casos não mapeados, tentar extrair
    
    # Tentar padrão: "HHh - Descrição"
    match = re.match(r'^(\d{1,2})h\s*-\s*(\w+)', periodo)
    if match:
        hora_num = match.group(1).zfill(2)
        descricao = match.group(2).strip().title()
        return f"{hora_num}h - {descricao}"
    
    # Tentar padrão invertido: "Descrição - HHh"
    match = re.match(r'^(\w+)\s*-\s*(\d{1,2})h', periodo)
    if match:
        descricao = match.group(1).strip().title()
        hora_num = match.group(2).zfill(2)
        return f"{hora_num}h - {descricao}"
    
    # Se nada funcionou, retorna o original
    return periodo

print("✓ Função parse_periodo() criada")

# %% [markdown]
# # 5. Localizar e Selecionar Planilha

# %%
print("\n" + "=" * 80)
print("LOCALIZAR PLANILHA RAW")
print("=" * 80)

# Detectar raiz do projeto
script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
if script_dir.name == 'parsers':
    project_root = script_dir.parent.parent
elif script_dir.name == 'notebooks':
    project_root = script_dir.parent
else:
    project_root = script_dir

pasta_raw = project_root / 'data' / 'raw'
print(f"\n📂 Pasta raw: {pasta_raw}")

if not pasta_raw.exists():
    print(f"❌ Pasta não encontrada!")
    raise FileNotFoundError(f"Pasta raw não encontrada em {pasta_raw}")

# Listar arquivos Excel
arquivos_disponiveis = sorted(
    list(pasta_raw.glob('*.xlsx')), 
    key=lambda x: x.stat().st_mtime, 
    reverse=True
)

if not arquivos_disponiveis:
    print(f"❌ Nenhum arquivo .xlsx encontrado!")
    raise FileNotFoundError(f"Nenhuma planilha em {pasta_raw}")

print(f"\n📁 Arquivos disponíveis (mais recentes primeiro):\n")
for i, arq in enumerate(arquivos_disponiveis, 1):
    modificado = datetime.fromtimestamp(arq.stat().st_mtime).strftime('%d/%m/%Y %H:%M')
    tamanho_kb = arq.stat().st_size / 1024
    print(f"  {i}. {arq.name}")
    print(f"     Modificado: {modificado} | Tamanho: {tamanho_kb:.1f} KB\n")

print("=" * 80)
selecao = int(input("Digite o número do arquivo para processar: "))
arquivo_selecionado = arquivos_disponiveis[selecao - 1]
print(f"✓ Selecionado: {arquivo_selecionado.name}")
print("=" * 80)

# %% [markdown]
# # 6. Carregar Planilha

# %%
print("\n" + "=" * 80)
print("CARREGANDO PLANILHA")
print("=" * 80)

df = pd.read_excel(arquivo_selecionado)

print(f"\n✓ Arquivo carregado: {arquivo_selecionado.name}")
print(f"✓ Total de registros: {len(df):,}")
print(f"\n📋 Colunas disponíveis:")
for col in df.columns:
    print(f"  • {col}")

# Verificar colunas necessárias
tem_logradouro = 'Logradouro' in df.columns
tem_periodo = 'Período' in df.columns

if not tem_logradouro and not tem_periodo:
    print(f"\n❌ ERRO: Colunas 'Logradouro' e 'Período' não encontradas!")
    raise KeyError("Colunas necessárias não encontradas")

print(f"\n✓ Validação:")
print(f"  • Campo 'Logradouro': {'✓ Encontrado' if tem_logradouro else '✗ Não encontrado'}")
print(f"  • Campo 'Período': {'✓ Encontrado' if tem_periodo else '✗ Não encontrado'}")

# %% [markdown]
# # 7. Aplicar Parsers

# %%
print("\n" + "=" * 80)
print("APLICANDO PARSERS")
print("=" * 80)

# PARSER DE LOGRADOURO
if tem_logradouro:
    print(f"\n🔄 Processando campo 'Logradouro'...")
    print(f"   Aguarde, processando {len(df):,} registros...\n")
    
    # Aplicar parser
    logradouros_parseados = df['Logradouro'].apply(parse_logradouro)
    
    # Substituir coluna Logradouro original com versão padronizada
    df['Logradouro'] = logradouros_parseados.apply(lambda x: x['logradouro_padronizado'])
    
    # Criar novas colunas
    df['tipo_logradouro'] = logradouros_parseados.apply(lambda x: x['tipo_logradouro'])
    df['nome_logradouro'] = logradouros_parseados.apply(lambda x: x['nome_logradouro'])
    df['numero_logradouro'] = logradouros_parseados.apply(lambda x: x['numero_logradouro'])
    df['complemento_logradouro'] = logradouros_parseados.apply(lambda x: x['complemento_logradouro'])
    
    print(f"✓ Campo 'Logradouro' parseado e padronizado com sucesso!")
    print(f"  → Coluna 'Logradouro' atualizada com formato padronizado")
    print(f"  → Novas colunas: tipo_logradouro, nome_logradouro, numero_logradouro, complemento_logradouro")

# PARSER DE PERÍODO
if tem_periodo:
    print(f"\n🔄 Processando campo 'Período'...")
    
    # Aplicar parser e substituir a coluna original
    df['Período'] = df['Período'].apply(parse_periodo)
    
    print(f"✓ Campo 'Período' padronizado com sucesso!")
    print(f"  → Coluna 'Período' atualizada com valores padronizados")

print(f"\n✓ Parsing concluído!")
print(f"  • Colunas padronizadas: 2 (Logradouro, Período)")
print(f"  • Colunas adicionadas: 4 (tipo_logradouro, nome_logradouro, numero_logradouro, complemento_logradouro)")
print(f"  • Total de colunas finais: {len(df.columns)}")

# %% [markdown]
# # 8. Análise de Qualidade

# %%
print("\n" + "=" * 80)
print("ANÁLISE DE QUALIDADE DO PARSING")
print("=" * 80)

total = len(df)

# Qualidade do Logradouro
if tem_logradouro:
    print(f"\n📊 LOGRADOURO:")
    com_tipo = (df['tipo_logradouro'] != '').sum()
    com_nome = (df['nome_logradouro'] != '').sum()
    com_numero = (df['numero_logradouro'] != '').sum()
    com_complemento = (df['complemento_logradouro'] != '').sum()
    
    print(f"  • Total de registros: {total:,}")
    print(f"  • Com tipo identificado: {com_tipo:,} ({(com_tipo/total*100):.1f}%)")
    print(f"  • Com nome extraído: {com_nome:,} ({(com_nome/total*100):.1f}%)")
    print(f"  • Com número extraído: {com_numero:,} ({(com_numero/total*100):.1f}%)")
    print(f"  • Com complemento: {com_complemento:,} ({(com_complemento/total*100):.1f}%)")
    
    print(f"\n  🏷️ Top 10 tipos identificados:")
    tipos_contagem = df[df['tipo_logradouro'] != '']['tipo_logradouro'].value_counts()
    for i, (tipo, qtd) in enumerate(tipos_contagem.head(10).items(), 1):
        pct = (qtd/total*100)
        print(f"    {i:2d}. {tipo:<15} {qtd:>8,} ({pct:>5.1f}%)")

# Qualidade do Período
if tem_periodo:
    print(f"\n📊 PERÍODO:")
    
    # Contar valores padronizados
    valores_unicos = df['Período'].nunique()
    periodos_validos = df['Período'].notna().sum()
    
    print(f"  • Total de registros: {total:,}")
    print(f"  • Valores padronizados: {periodos_validos:,} ({(periodos_validos/total*100):.1f}%)")
    print(f"  • Valores únicos após padronização: {valores_unicos}")
    
    print(f"\n  🕐 Distribuição de períodos:")
    periodos_contagem = df['Período'].value_counts()
    for periodo, qtd in periodos_contagem.items():
        pct = (qtd/total*100)
        print(f"    • {periodo:<20} {qtd:>8,} ({pct:>5.1f}%)")

# %% [markdown]
# # 9. Amostras de Resultados

# %%
print("\n" + "=" * 80)
print("AMOSTRA DE RESULTADOS")
print("=" * 80)

# Mostrar 5 exemplos
amostra = df.sample(min(5, len(df)))

print(f"\n🔍 {len(amostra)} exemplos aleatórios de registros parseados:\n")

for idx, (i, row) in enumerate(amostra.iterrows(), 1):
    print(f"{'=' * 80}")
    print(f"EXEMPLO {idx}:")
    print(f"{'-' * 80}")
    
    if tem_logradouro:
        print(f"LOGRADOURO PADRONIZADO: {row['Logradouro']}")
        print(f"  → Tipo........: {row['tipo_logradouro']}")
        print(f"  → Nome........: {row['nome_logradouro']}")
        print(f"  → Número......: {row['numero_logradouro']}")
        print(f"  → Complemento.: {row['complemento_logradouro']}")
    
    if tem_periodo:
        print(f"\nPERÍODO PADRONIZADO: {row['Período']}")
    
    print()

# %% [markdown]
# # 10. Exportar Planilha Processada

# %%
print("\n" + "=" * 80)
print("EXPORTANDO PLANILHA PROCESSADA")
print("=" * 80)

# Criar pasta processed
pasta_processed = project_root / 'data' / 'processed'
pasta_processed.mkdir(parents=True, exist_ok=True)

# Nome do arquivo
nome_base = arquivo_selecionado.stem
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
nome_saida = f"{nome_base}_processada_{timestamp}.xlsx"
arquivo_saida = pasta_processed / nome_saida

# Reordenar colunas na ordem especificada
colunas_ordenadas = [
    'Equipe',
    'Data', 
    'Logradouro',
    'Período',
    'Qtd. pessoas',
    'tipo_logradouro',
    'nome_logradouro',
    'numero_logradouro',
    'complemento_logradouro'
]

# Filtrar apenas colunas que existem no DataFrame
colunas_finais = [col for col in colunas_ordenadas if col in df.columns]

# Adicionar qualquer coluna que não está na lista (por segurança)
for col in df.columns:
    if col not in colunas_finais:
        colunas_finais.append(col)

df_exportar = df[colunas_finais]

# Exportar
print(f"\n💾 Salvando arquivo processado...")
print(f"   Destino: {arquivo_saida}\n")

df_exportar.to_excel(arquivo_saida, index=False, engine='openpyxl')

print(f"✓ Arquivo exportado com sucesso!")
print(f"  📁 Local: {arquivo_saida}")
print(f"  📊 Registros: {len(df_exportar):,}")
print(f"  📋 Colunas: {len(df_exportar.columns)}")
print(f"  💾 Tamanho: {arquivo_saida.stat().st_size / 1024:.1f} KB")

# %% [markdown]
# # 11. Gerar Relatório

# %%
print("\n" + "=" * 80)
print("GERANDO RELATÓRIO")
print("=" * 80)

pasta_docs = project_root / 'docs'
pasta_docs.mkdir(parents=True, exist_ok=True)

arquivo_relatorio = pasta_docs / f'relatorio_parser_{timestamp}.txt'

with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("RELATÓRIO DE PROCESSAMENTO - PARSER COMPLETO\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    f.write(f"Arquivo de entrada: {arquivo_selecionado.name}\n")
    f.write(f"Arquivo de saída: {nome_saida}\n")
    f.write(f"Registros processados: {total:,}\n\n")
    
    if tem_logradouro:
        f.write("-" * 80 + "\n")
        f.write("LOGRADOURO\n")
        f.write("-" * 80 + "\n")
        f.write(f"Com tipo identificado: {com_tipo:,} ({(com_tipo/total*100):.1f}%)\n")
        f.write(f"Com nome extraído: {com_nome:,} ({(com_nome/total*100):.1f}%)\n")
        f.write(f"Com número extraído: {com_numero:,} ({(com_numero/total*100):.1f}%)\n")
        f.write(f"Com complemento: {com_complemento:,} ({(com_complemento/total*100):.1f}%)\n\n")
        
        f.write("Top 10 tipos:\n")
        for i, (tipo, qtd) in enumerate(tipos_contagem.head(10).items(), 1):
            pct = (qtd/total*100)
            f.write(f"  {i:2d}. {tipo:<15} {qtd:>8,} ({pct:>5.1f}%)\n")
        f.write("\n")
    
    if tem_periodo:
        f.write("-" * 80 + "\n")
        f.write("PERÍODO\n")
        f.write("-" * 80 + "\n")
        f.write(f"Valores padronizados: {periodos_validos:,} ({(periodos_validos/total*100):.1f}%)\n")
        f.write(f"Valores únicos: {valores_unicos}\n\n")
        
        f.write("Distribuição:\n")
        for periodo, qtd in periodos_contagem.items():
            pct = (qtd/total*100)
            f.write(f"  • {periodo:<20} {qtd:>8,} ({pct:>5.1f}%)\n")
        f.write("\n")
    
    f.write("-" * 80 + "\n")
    f.write("COLUNAS DO ARQUIVO PROCESSADO\n")
    f.write("-" * 80 + "\n")
    for col in df_exportar.columns:
        f.write(f"  • {col}\n")

print(f"✓ Relatório exportado: {arquivo_relatorio}")

# %% [markdown]
# # 12. Resumo Executivo

# %%
print("\n" + "=" * 80)
print("RESUMO EXECUTIVO")
print("=" * 80)

resumo_log = ""
if tem_logradouro:
    resumo_log = f"""
LOGRADOURO:
• {com_tipo:,} com tipo identificado ({(com_tipo/total*100):.1f}%)
• {com_nome:,} com nome extraído ({(com_nome/total*100):.1f}%)
• {com_numero:,} com número extraído ({(com_numero/total*100):.1f}%)
• Top 3: {', '.join(tipos_contagem.head(3).index.tolist())}
"""

resumo_per = ""
if tem_periodo:
    resumo_per = f"""
PERÍODO:
• {periodos_validos:,} valores padronizados ({(periodos_validos/total*100):.1f}%)
• {valores_unicos} valores únicos
• Períodos: {', '.join(periodos_contagem.head(4).index.tolist())}
"""

print(f"""
PROCESSAMENTO CONCLUÍDO COM SUCESSO!

ARQUIVO DE ENTRADA:
• {arquivo_selecionado.name}
• {total:,} registros

PROCESSAMENTO:
• Parser de Logradouro: {'✓ Aplicado' if tem_logradouro else '✗ Não aplicado'}
• Parser de Período: {'✓ Aplicado' if tem_periodo else '✗ Não aplicado'}
{resumo_log}
{resumo_per}

ARQUIVOS GERADOS:
✓ Planilha processada: {arquivo_saida.name}
✓ Relatório: {arquivo_relatorio.name}

LOCALIZAÇÃO:
• Planilha: {pasta_processed}
• Relatório: {pasta_docs}

PRÓXIMOS PASSOS:
1. Revisar planilha processada em data/processed/
2. Validar qualidade do parsing
3. Usar planilha processada nas análises
""")

print("=" * 80)
print("✓ PARSER COMPLETO EXECUTADO COM SUCESSO!")
print(f"✓ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("=" * 80)
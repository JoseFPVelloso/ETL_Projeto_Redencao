# Análise Exploratória de Planilha RAW
# Objetivo: Identificar padrões em Logradouro e Período para criar parser otimizado
# Output: Relatório detalhado com análises e exemplos

# %% [markdown]
# # 1. Configuração Inicial

# %%
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

print("=" * 80)
print("ANÁLISE EXPLORATÓRIA - PLANILHA RAW")
print("=" * 80)
print(f"✓ Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

# %% [markdown]
# # 2. Localizar e Selecionar Planilha

# %%
print("=" * 80)
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
selecao = int(input("Digite o número do arquivo para análise: "))
arquivo_selecionado = arquivos_disponiveis[selecao - 1]
print(f"✓ Selecionado: {arquivo_selecionado.name}")
print("=" * 80)

# %% [markdown]
# # 3. Carregar Planilha

# %%
print("\n" + "=" * 80)
print("CARREGANDO PLANILHA")
print("=" * 80)

df = pd.read_excel(arquivo_selecionado)

print(f"\n✓ Arquivo carregado: {arquivo_selecionado.name}")
print(f"✓ Total de registros: {len(df):,}")
print(f"\n📋 Colunas disponíveis:")
for i, col in enumerate(df.columns, 1):
    tipo = df[col].dtype
    nulos = df[col].isna().sum()
    print(f"  {i}. {col:<20} (tipo: {tipo}, nulos: {nulos:,})")

# %% [markdown]
# # 4. Análise Geral

# %%
print("\n" + "=" * 80)
print("ANÁLISE GERAL DOS DADOS")
print("=" * 80)

print(f"\n📊 RESUMO:")
print(f"  • Total de registros: {len(df):,}")
print(f"  • Total de colunas: {len(df.columns)}")
print(f"  • Memória utilizada: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

# Verificar duplicatas
duplicatas = df.duplicated().sum()
print(f"  • Registros duplicados: {duplicatas:,}")

# Registros por coluna com valor
print(f"\n📈 PREENCHIMENTO DAS COLUNAS:")
for col in df.columns:
    preenchidos = df[col].notna().sum()
    pct = (preenchidos / len(df)) * 100
    print(f"  • {col:<20}: {preenchidos:>8,} ({pct:>6.2f}%)")

# %% [markdown]
# # 5. Análise Detalhada - LOGRADOURO

# %%
if 'Logradouro' in df.columns:
    print("\n" + "=" * 80)
    print("ANÁLISE DETALHADA - CAMPO 'LOGRADOURO'")
    print("=" * 80)
    
    # Estatísticas básicas
    logradouros = df['Logradouro'].dropna()
    total_log = len(logradouros)
    unicos = logradouros.nunique()
    
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"  • Total de registros: {total_log:,}")
    print(f"  • Logradouros únicos: {unicos:,}")
    print(f"  • Taxa de variação: {(unicos/total_log*100):.2f}%")
    
    # Análise de comprimento
    comprimentos = logradouros.str.len()
    print(f"\n📏 COMPRIMENTO DOS LOGRADOUROS:")
    print(f"  • Mínimo: {comprimentos.min()} caracteres")
    print(f"  • Máximo: {comprimentos.max()} caracteres")
    print(f"  • Média: {comprimentos.mean():.1f} caracteres")
    print(f"  • Mediana: {comprimentos.median():.1f} caracteres")
    
    # Análise de padrões estruturais
    print(f"\n🔍 PADRÕES ESTRUTURAIS:")
    
    # Conta ocorrências de separadores
    com_virgula = logradouros.str.contains(',', na=False).sum()
    com_hifen = logradouros.str.contains(' - ', na=False).sum()
    com_parenteses = logradouros.str.contains(r'\(.*\)', na=False).sum()
    com_numero = logradouros.str.contains(r'\d', na=False).sum()
    com_sn = logradouros.str.contains(r'[Ss]/[NnºoO]', na=False).sum()
    
    print(f"  • Com vírgula (,): {com_virgula:,} ({(com_virgula/total_log*100):.1f}%)")
    print(f"  • Com hífen ( - ): {com_hifen:,} ({(com_hifen/total_log*100):.1f}%)")
    print(f"  • Com parênteses (): {com_parenteses:,} ({(com_parenteses/total_log*100):.1f}%)")
    print(f"  • Com número: {com_numero:,} ({(com_numero/total_log*100):.1f}%)")
    print(f"  • Com S/N: {com_sn:,} ({(com_sn/total_log*100):.1f}%)")
    
    # Identificar possíveis tipos de logradouro
    print(f"\n🏷️ POSSÍVEIS TIPOS DE LOGRADOURO (primeiras palavras):")
    primeiras_palavras = logradouros.str.split(n=1).str[0].value_counts().head(20)
    for i, (palavra, qtd) in enumerate(primeiras_palavras.items(), 1):
        pct = (qtd/total_log*100)
        print(f"  {i:2d}. {palavra:<20} {qtd:>8,} ({pct:>6.2f}%)")
    
    # Análise de separadores " - " (complemento)
    print(f"\n📍 ANÁLISE DE COMPLEMENTOS (após ' - '):")
    logradouros_com_complemento = logradouros[logradouros.str.contains(' - ', na=False)]
    if len(logradouros_com_complemento) > 0:
        complementos = logradouros_com_complemento.str.split(' - ', n=1).str[1]
        print(f"  • Total com complemento: {len(complementos):,} ({(len(complementos)/total_log*100):.1f}%)")
        print(f"  • Complementos únicos: {complementos.nunique():,}")
        print(f"\n  Top 15 complementos mais comuns:")
        for i, (compl, qtd) in enumerate(complementos.value_counts().head(15).items(), 1):
            print(f"    {i:2d}. {compl[:50]:<50} {qtd:>6,}")
    
    # Análise de números
    print(f"\n🔢 ANÁLISE DE NÚMEROS:")
    logradouros_com_numero = logradouros[logradouros.str.contains(r'\d', na=False)]
    if len(logradouros_com_numero) > 0:
        # Extrair padrões de números
        numeros_extraidos = logradouros_com_numero.str.extract(r',?\s*(\d+[A-Za-z]?|[Ss]/[NnºoO])', expand=False).dropna()
        print(f"  • Total com número: {len(logradouros_com_numero):,} ({(len(logradouros_com_numero)/total_log*100):.1f}%)")
        print(f"  • Padrões de número únicos: {numeros_extraidos.nunique():,}")
        print(f"\n  Top 20 padrões de número:")
        for i, (num, qtd) in enumerate(numeros_extraidos.value_counts().head(20).items(), 1):
            print(f"    {i:2d}. '{num}' ({qtd:,} vezes)")
    
    # Exemplos representativos
    print(f"\n📋 EXEMPLOS REPRESENTATIVOS (20 aleatórios):")
    amostra_log = logradouros.sample(min(20, len(logradouros)))
    for i, log in enumerate(amostra_log, 1):
        print(f"  {i:2d}. {log}")
    
    # Casos especiais/problemáticos
    print(f"\n⚠️ CASOS ESPECIAIS/PROBLEMÁTICOS:")
    
    # Muito curtos
    muito_curtos = logradouros[logradouros.str.len() < 10]
    if len(muito_curtos) > 0:
        print(f"\n  • Logradouros muito curtos (<10 caracteres): {len(muito_curtos):,}")
        for i, log in enumerate(muito_curtos.head(10), 1):
            print(f"    {i}. '{log}'")
    
    # Muito longos
    muito_longos = logradouros[logradouros.str.len() > 80]
    if len(muito_longos) > 0:
        print(f"\n  • Logradouros muito longos (>80 caracteres): {len(muito_longos):,}")
        for i, log in enumerate(muito_longos.head(10), 1):
            print(f"    {i}. {log[:80]}...")
    
    # Caracteres especiais
    com_especiais = logradouros[logradouros.str.contains(r'[:\[\]\*\?\\\/]', na=False)]
    if len(com_especiais) > 0:
        print(f"\n  • Com caracteres especiais (: [ ] * ? \\ /): {len(com_especiais):,}")
        for i, log in enumerate(com_especiais.head(10), 1):
            print(f"    {i}. {log}")

else:
    print("\n⚠️ Coluna 'Logradouro' não encontrada!")

# %% [markdown]
# # 6. Análise Detalhada - PERÍODO

# %%
if 'Período' in df.columns:
    print("\n" + "=" * 80)
    print("ANÁLISE DETALHADA - CAMPO 'PERÍODO'")
    print("=" * 80)
    
    # Estatísticas básicas
    periodos = df['Período'].dropna()
    total_per = len(periodos)
    unicos_per = periodos.nunique()
    
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"  • Total de registros: {total_per:,}")
    print(f"  • Períodos únicos: {unicos_per:,}")
    
    # Análise de comprimento
    comprimentos_per = periodos.astype(str).str.len()
    print(f"\n📏 COMPRIMENTO DOS PERÍODOS:")
    print(f"  • Mínimo: {comprimentos_per.min()} caracteres")
    print(f"  • Máximo: {comprimentos_per.max()} caracteres")
    print(f"  • Média: {comprimentos_per.mean():.1f} caracteres")
    
    # Valores únicos
    print(f"\n🕐 VALORES ÚNICOS DE PERÍODO:")
    valores_periodo = periodos.value_counts().sort_index()
    for i, (per, qtd) in enumerate(valores_periodo.items(), 1):
        pct = (qtd/total_per*100)
        print(f"  {i:2d}. '{per}' {qtd:>10,} ({pct:>6.2f}%)")
    
    # Padrões identificados
    print(f"\n🔍 PADRÕES IDENTIFICADOS:")
    
    # Verifica se tem hora (formato ##h)
    com_hora = periodos.astype(str).str.contains(r'\d{1,2}h', na=False).sum()
    print(f"  • Com formato de hora (##h): {com_hora:,} ({(com_hora/total_per*100):.1f}%)")
    
    # Verifica se tem descrição textual
    com_texto = periodos.astype(str).str.contains(r'[A-Za-z]{3,}', na=False).sum()
    print(f"  • Com descrição textual: {com_texto:,} ({(com_texto/total_per*100):.1f}%)")
    
    # Verifica se tem hífen
    com_hifen_per = periodos.astype(str).str.contains('-', na=False).sum()
    print(f"  • Com hífen (-): {com_hifen_per:,} ({(com_hifen_per/total_per*100):.1f}%)")
    
    # Extrair horas
    print(f"\n⏰ HORAS IDENTIFICADAS:")
    horas_extraidas = periodos.astype(str).str.extract(r'(\d{1,2})h?', expand=False).dropna()
    if len(horas_extraidas) > 0:
        horas_unicas = horas_extraidas.value_counts().sort_index()
        for hora, qtd in horas_unicas.items():
            pct = (qtd/total_per*100)
            print(f"  • {hora}h: {qtd:>10,} ({pct:>6.2f}%)")
    
    # Exemplos
    print(f"\n📋 TODOS OS VALORES ÚNICOS:")
    for i, per in enumerate(periodos.unique(), 1):
        print(f"  {i:2d}. '{per}'")

else:
    print("\n⚠️ Coluna 'Período' não encontrada!")

# %% [markdown]
# # 7. Análise de Outros Campos Relevantes

# %%
print("\n" + "=" * 80)
print("ANÁLISE DE OUTROS CAMPOS")
print("=" * 80)

# Data
if 'Data' in df.columns:
    print(f"\n📅 CAMPO 'DATA':")
    datas = pd.to_datetime(df['Data'], errors='coerce')
    datas_validas = datas.dropna()
    print(f"  • Total de registros: {len(df['Data']):,}")
    print(f"  • Datas válidas: {len(datas_validas):,}")
    print(f"  • Data mínima: {datas_validas.min()}")
    print(f"  • Data máxima: {datas_validas.max()}")
    print(f"  • Período: {(datas_validas.max() - datas_validas.min()).days} dias")

# Quantidade
if 'Quantidade' in df.columns:
    print(f"\n🔢 CAMPO 'QUANTIDADE':")
    qtd = pd.to_numeric(df['Quantidade'], errors='coerce').dropna()
    print(f"  • Total de registros: {len(df['Quantidade']):,}")
    print(f"  • Valores válidos: {len(qtd):,}")
    print(f"  • Mínimo: {qtd.min():.0f}")
    print(f"  • Máximo: {qtd.max():.0f}")
    print(f"  • Média: {qtd.mean():.2f}")
    print(f"  • Mediana: {qtd.median():.0f}")
    
    # Distribuição
    print(f"\n  Distribuição:")
    print(f"    • 0-10 pessoas: {(qtd <= 10).sum():,} ({((qtd <= 10).sum()/len(qtd)*100):.1f}%)")
    print(f"    • 11-20 pessoas: {((qtd > 10) & (qtd <= 20)).sum():,} ({(((qtd > 10) & (qtd <= 20)).sum()/len(qtd)*100):.1f}%)")
    print(f"    • 21-50 pessoas: {((qtd > 20) & (qtd <= 50)).sum():,} ({(((qtd > 20) & (qtd <= 50)).sum()/len(qtd)*100):.1f}%)")
    print(f"    • >50 pessoas: {(qtd > 50).sum():,} ({((qtd > 50).sum()/len(qtd)*100):.1f}%)")

# Equipe
if 'Equipe' in df.columns:
    print(f"\n👥 CAMPO 'EQUIPE':")
    equipes = df['Equipe'].dropna()
    print(f"  • Total de registros: {len(df['Equipe']):,}")
    print(f"  • Valores únicos: {equipes.nunique()}")
    if equipes.nunique() <= 20:
        print(f"\n  Valores:")
        for i, (eq, qtd) in enumerate(equipes.value_counts().items(), 1):
            pct = (qtd/len(equipes)*100)
            print(f"    {i:2d}. {eq}: {qtd:,} ({pct:.1f}%)")

# %% [markdown]
# # 8. Exportar Relatório Completo

# %%
print("\n" + "=" * 80)
print("EXPORTANDO RELATÓRIO")
print("=" * 80)

# Criar pasta docs
pasta_docs = project_root / 'docs'
pasta_docs.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
arquivo_relatorio = pasta_docs / f'analise_exploratoria_{timestamp}.txt'

# Gerar relatório em arquivo
with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("ANÁLISE EXPLORATÓRIA - PLANILHA RAW\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    f.write(f"Arquivo: {arquivo_selecionado.name}\n")
    f.write(f"Total de registros: {len(df):,}\n\n")
    
    # Resumo das colunas
    f.write("-" * 80 + "\n")
    f.write("COLUNAS DISPONÍVEIS\n")
    f.write("-" * 80 + "\n")
    for col in df.columns:
        f.write(f"  • {col}\n")
    f.write("\n")
    
    # Logradouro
    if 'Logradouro' in df.columns:
        f.write("-" * 80 + "\n")
        f.write("ANÁLISE - LOGRADOURO\n")
        f.write("-" * 80 + "\n")
        logradouros = df['Logradouro'].dropna()
        f.write(f"Total: {len(logradouros):,}\n")
        f.write(f"Únicos: {logradouros.nunique():,}\n\n")
        
        f.write("Padrões estruturais:\n")
        f.write(f"  • Com vírgula: {logradouros.str.contains(',', na=False).sum():,}\n")
        f.write(f"  • Com hífen: {logradouros.str.contains(' - ', na=False).sum():,}\n")
        f.write(f"  • Com número: {logradouros.str.contains(r'\d', na=False).sum():,}\n")
        f.write(f"  • Com S/N: {logradouros.str.contains(r'[Ss]/[NnºoO]', na=False).sum():,}\n\n")
        
        f.write("Top 20 tipos (primeira palavra):\n")
        for i, (palavra, qtd) in enumerate(logradouros.str.split(n=1).str[0].value_counts().head(20).items(), 1):
            f.write(f"  {i:2d}. {palavra:<20} {qtd:>8,}\n")
        f.write("\n")
        
        f.write("30 Exemplos aleatórios:\n")
        for i, log in enumerate(logradouros.sample(min(30, len(logradouros))), 1):
            f.write(f"  {i:2d}. {log}\n")
        f.write("\n")
    
    # Período
    if 'Período' in df.columns:
        f.write("-" * 80 + "\n")
        f.write("ANÁLISE - PERÍODO\n")
        f.write("-" * 80 + "\n")
        periodos = df['Período'].dropna()
        f.write(f"Total: {len(periodos):,}\n")
        f.write(f"Únicos: {periodos.nunique()}\n\n")
        
        f.write("Todos os valores únicos:\n")
        for i, (per, qtd) in enumerate(periodos.value_counts().sort_index().items(), 1):
            pct = (qtd/len(periodos)*100)
            f.write(f"  {i:2d}. '{per}' {qtd:>10,} ({pct:>6.2f}%)\n")
        f.write("\n")

print(f"✓ Relatório exportado: {arquivo_relatorio}")
print(f"  📄 {arquivo_relatorio}")

# %% [markdown]
# # 9. Resumo Executivo

# %%
print("\n" + "=" * 80)
print("RESUMO EXECUTIVO")
print("=" * 80)

resumo_logradouro = ""
if 'Logradouro' in df.columns:
    logradouros = df['Logradouro'].dropna()
    com_virgula = logradouros.str.contains(',', na=False).sum()
    com_hifen = logradouros.str.contains(' - ', na=False).sum()
    resumo_logradouro = f"""
LOGRADOURO:
• {len(logradouros):,} registros
• {logradouros.nunique():,} únicos
• {com_virgula:,} com vírgula ({(com_virgula/len(logradouros)*100):.1f}%)
• {com_hifen:,} com hífen/complemento ({(com_hifen/len(logradouros)*100):.1f}%)
"""

resumo_periodo = ""
if 'Período' in df.columns:
    periodos = df['Período'].dropna()
    resumo_periodo = f"""
PERÍODO:
• {len(periodos):,} registros
• {periodos.nunique()} valores únicos
• Valores: {', '.join([str(p) for p in periodos.unique()])}
"""

print(f"""
ANÁLISE EXPLORATÓRIA CONCLUÍDA!

ARQUIVO ANALISADO:
• {arquivo_selecionado.name}
• {len(df):,} registros
• {len(df.columns)} colunas

{resumo_logradouro}
{resumo_periodo}

ARQUIVO GERADO:
✓ {arquivo_relatorio}

PRÓXIMOS PASSOS:
1. Revisar o relatório completo em {arquivo_relatorio.name}
2. Compartilhar os resultados desta análise
3. Criar parser otimizado baseado nos padrões identificados
4. Aplicar parser na planilha completa
""")

print("=" * 80)
print("✓ ANÁLISE CONCLUÍDA!")
print(f"✓ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("=" * 80)
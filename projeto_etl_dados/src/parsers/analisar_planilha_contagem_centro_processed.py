# Validação de Qualidade do Parsing
# Objetivo: Analisar arquivo processado e validar qualidade do parsing
# Compara resultados com logradouros esperados e identifica problemas

# %% [markdown]
# # 1. Configuração Inicial

# %%
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter
import warnings

warnings.filterwarnings('ignore')

print("=" * 80)
print("VALIDAÇÃO DE QUALIDADE DO PARSING")
print("=" * 80)
print(f"✓ Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

# %% [markdown]
# # 2. Definir Logradouros Esperados

# %%
print("=" * 80)
print("CARREGANDO LOGRADOUROS ESPERADOS")
print("=" * 80)

# Lista de logradouros esperados (baseada na imagem fornecida)
LOGRADOUROS_ESPERADOS = {
    'Praça': [
        'Antônio Cândido de Camargo',
        'da Luz',
        'Marechal Deodoro',
        'Princesa Isabel'
    ],
    'Rua': [
        'Apa',
        'Aurora',
        'Barão de Campinas',
        'Conselheiro Nébias',
        'das Margaridas',
        'do Triunfo',
        'dos Andradas',
        'dos Gusmões',
        'dos Protestantes',
        'General Couto de Magalhães',
        'General Osório',
        'Guaianases',
        'Helvétia',
        'Mauá',
        'Santa Ifigênia',
        'Vitória'
    ],
    'Alameda': [
        'Barão de Limeira',
        'Barão de Piracicaba',
        'Cleveland',
        'Dino Bueno',
        'Glete',
        'Nothmann'
    ],
    'Avenida': [
        'Cásper Líbero',
        'Duque de Caxias',
        'General Olímpio da Silveira',
        'Prestes Maia',
        'Rio Branco',
        'São João',
        'Senador Queirós',
        'Tiradentes'
    ],
    'Largo': [
        'Coração de Jesus',
        'General Osório'
    ],
    'Viaduto': [
        'Engenheiro Orlando Murgel'
    ],
    'Marquise': [
        'Estação da Luz'
    ],
    'Terminal': [
        'Princesa Isabel'
    ],
    'Parque': [
        'Jardim da Luz'
    ],
    'Passarela': [
        'Rua das Noivas'
    ]
}

# Criar lista plana de todos os logradouros esperados
total_esperados = sum(len(nomes) for nomes in LOGRADOUROS_ESPERADOS.values())

print(f"\n✓ Logradouros esperados carregados: {total_esperados}")
print(f"\n📋 Distribuição por tipo:")
for tipo, nomes in LOGRADOUROS_ESPERADOS.items():
    print(f"  • {tipo:<15} {len(nomes):>3} logradouros")

# %% [markdown]
# # 3. Localizar e Selecionar Arquivo Processado

# %%
print("\n" + "=" * 80)
print("LOCALIZAR ARQUIVO PROCESSADO")
print("=" * 80)

# Detectar raiz do projeto
script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
if script_dir.name == 'notebooks':
    project_root = script_dir.parent
elif script_dir.name == 'parsers':
    project_root = script_dir.parent.parent
else:
    project_root = script_dir

pasta_processed = project_root / 'data' / 'processed'
print(f"\n📂 Pasta processed: {pasta_processed}")

if not pasta_processed.exists():
    print(f"❌ Pasta não encontrada!")
    raise FileNotFoundError(f"Pasta processed não encontrada em {pasta_processed}")

# Listar arquivos Excel
arquivos_disponiveis = sorted(
    list(pasta_processed.glob('*.xlsx')), 
    key=lambda x: x.stat().st_mtime, 
    reverse=True
)

if not arquivos_disponiveis:
    print(f"❌ Nenhum arquivo .xlsx encontrado!")
    raise FileNotFoundError(f"Nenhuma planilha em {pasta_processed}")

print(f"\n📁 Arquivos disponíveis (mais recentes primeiro):\n")
for i, arq in enumerate(arquivos_disponiveis, 1):
    modificado = datetime.fromtimestamp(arq.stat().st_mtime).strftime('%d/%m/%Y %H:%M')
    tamanho_kb = arq.stat().st_size / 1024
    print(f"  {i}. {arq.name}")
    print(f"     Modificado: {modificado} | Tamanho: {tamanho_kb:.1f} KB\n")

print("=" * 80)
selecao = int(input("Digite o número do arquivo para validar: "))
arquivo_selecionado = arquivos_disponiveis[selecao - 1]
print(f"✓ Selecionado: {arquivo_selecionado.name}")
print("=" * 80)

# %% [markdown]
# # 4. Carregar Arquivo Processado

# %%
print("\n" + "=" * 80)
print("CARREGANDO ARQUIVO PROCESSADO")
print("=" * 80)

df = pd.read_excel(arquivo_selecionado)

print(f"\n✓ Arquivo carregado: {arquivo_selecionado.name}")
print(f"✓ Total de registros: {len(df):,}")
print(f"\n📋 Colunas disponíveis:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i:2d}. {col}")

# Verificar colunas esperadas
colunas_esperadas = [
    'Equipe', 'Data', 'Logradouro', 'Período', 'Qtd. pessoas',
    'tipo_logradouro', 'nome_logradouro', 'numero_logradouro', 'complemento_logradouro'
]

colunas_faltando = [c for c in colunas_esperadas if c not in df.columns]
if colunas_faltando:
    print(f"\n⚠️ ATENÇÃO: Colunas faltando: {', '.join(colunas_faltando)}")
else:
    print(f"\n✓ Todas as colunas esperadas presentes!")

# %% [markdown]
# # 5. Análise Geral de Qualidade

# %%
print("\n" + "=" * 80)
print("ANÁLISE GERAL DE QUALIDADE")
print("=" * 80)

total = len(df)

# Estatísticas de preenchimento
print(f"\n📊 PREENCHIMENTO DAS COLUNAS PARSEADAS:")
if 'tipo_logradouro' in df.columns:
    com_tipo = (df['tipo_logradouro'].notna() & (df['tipo_logradouro'] != '')).sum()
    print(f"  • tipo_logradouro: {com_tipo:,} ({(com_tipo/total*100):.1f}%)")

if 'nome_logradouro' in df.columns:
    com_nome = (df['nome_logradouro'].notna() & (df['nome_logradouro'] != '')).sum()
    print(f"  • nome_logradouro: {com_nome:,} ({(com_nome/total*100):.1f}%)")

if 'numero_logradouro' in df.columns:
    com_numero = (df['numero_logradouro'].notna() & (df['numero_logradouro'] != '')).sum()
    print(f"  • numero_logradouro: {com_numero:,} ({(com_numero/total*100):.1f}%)")

if 'complemento_logradouro' in df.columns:
    com_complemento = (df['complemento_logradouro'].notna() & (df['complemento_logradouro'] != '')).sum()
    print(f"  • complemento_logradouro: {com_complemento:,} ({(com_complemento/total*100):.1f}%)")

# Verificar padronização do Logradouro
print(f"\n🔍 VALIDAÇÃO DE PADRONIZAÇÃO:")
if 'Logradouro' in df.columns:
    # Verificar se tem vírgula quando tem número
    if 'numero_logradouro' in df.columns:
        df_com_numero = df[df['numero_logradouro'].notna() & (df['numero_logradouro'] != '')]
        com_virgula = df_com_numero['Logradouro'].str.contains(',', na=False).sum()
        total_com_numero = len(df_com_numero)
        print(f"  • Logradouros com número: {total_com_numero:,}")
        print(f"  • Com vírgula antes do número: {com_virgula:,} ({(com_virgula/total_com_numero*100):.1f}%)")
        
        if com_virgula < total_com_numero:
            sem_virgula = total_com_numero - com_virgula
            print(f"  ⚠️ Sem vírgula (problema): {sem_virgula:,}")

# Verificar padronização do Período
if 'Período' in df.columns:
    periodos_unicos = df['Período'].unique()
    print(f"\n  • Períodos únicos: {len(periodos_unicos)}")
    print(f"  • Valores:")
    for periodo in sorted(periodos_unicos):
        qtd = (df['Período'] == periodo).sum()
        print(f"    - '{periodo}': {qtd:,}")

# %% [markdown]
# # 6. Comparação com Logradouros Esperados

# %%
print("\n" + "=" * 80)
print("COMPARAÇÃO COM LOGRADOUROS ESPERADOS")
print("=" * 80)

if 'tipo_logradouro' in df.columns and 'nome_logradouro' in df.columns:
    
    # Obter combinações únicas de tipo + nome
    logradouros_encontrados = df[['tipo_logradouro', 'nome_logradouro']].drop_duplicates()
    logradouros_encontrados = logradouros_encontrados[
        (logradouros_encontrados['tipo_logradouro'].notna()) & 
        (logradouros_encontrados['nome_logradouro'].notna()) &
        (logradouros_encontrados['tipo_logradouro'] != '') &
        (logradouros_encontrados['nome_logradouro'] != '')
    ]
    
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"  • Logradouros esperados: {total_esperados}")
    print(f"  • Logradouros únicos encontrados: {len(logradouros_encontrados)}")
    
    # Verificar cada tipo
    print(f"\n🔍 VALIDAÇÃO POR TIPO:")
    
    resultados_validacao = []
    
    for tipo, nomes_esperados in LOGRADOUROS_ESPERADOS.items():
        # Filtrar logradouros deste tipo
        logs_tipo = logradouros_encontrados[
            logradouros_encontrados['tipo_logradouro'] == tipo
        ]['nome_logradouro'].tolist()
        
        print(f"\n  {tipo}:")
        print(f"    • Esperados: {len(nomes_esperados)}")
        print(f"    • Encontrados: {len(logs_tipo)}")
        
        # Verificar quais foram encontrados
        encontrados_corretos = []
        nao_encontrados = []
        
        for nome_esperado in nomes_esperados:
            # Busca flexível (ignora case e espaços extras)
            encontrado = False
            for nome_encontrado in logs_tipo:
                if nome_esperado.lower().strip() == nome_encontrado.lower().strip():
                    encontrado = True
                    encontrados_corretos.append(nome_esperado)
                    break
            
            if not encontrado:
                nao_encontrados.append(nome_esperado)
        
        # Encontrar logradouros extras (não esperados)
        extras = []
        for nome_encontrado in logs_tipo:
            eh_esperado = False
            for nome_esperado in nomes_esperados:
                if nome_esperado.lower().strip() == nome_encontrado.lower().strip():
                    eh_esperado = True
                    break
            if not eh_esperado:
                extras.append(nome_encontrado)
        
        taxa_acerto = (len(encontrados_corretos) / len(nomes_esperados) * 100) if nomes_esperados else 0
        
        print(f"    • ✓ Corretos: {len(encontrados_corretos)} ({taxa_acerto:.1f}%)")
        
        if nao_encontrados:
            print(f"    • ✗ Não encontrados: {len(nao_encontrados)}")
            for nome in nao_encontrados[:5]:  # Mostrar até 5
                print(f"      - {nome}")
            if len(nao_encontrados) > 5:
                print(f"      ... e mais {len(nao_encontrados) - 5}")
        
        if extras:
            print(f"    • ⚠️ Extras (não esperados): {len(extras)}")
            for nome in extras[:5]:  # Mostrar até 5
                print(f"      - {nome}")
            if len(extras) > 5:
                print(f"      ... e mais {len(extras) - 5}")
        
        resultados_validacao.append({
            'tipo': tipo,
            'esperados': len(nomes_esperados),
            'encontrados_corretos': len(encontrados_corretos),
            'nao_encontrados': nao_encontrados,
            'extras': extras,
            'taxa_acerto': taxa_acerto
        })
    
    # Resumo geral
    total_corretos = sum(r['encontrados_corretos'] for r in resultados_validacao)
    taxa_geral = (total_corretos / total_esperados * 100)
    
    print(f"\n{'=' * 80}")
    print(f"TAXA DE ACERTO GERAL: {taxa_geral:.1f}% ({total_corretos}/{total_esperados})")
    print(f"{'=' * 80}")

else:
    print("\n⚠️ Colunas 'tipo_logradouro' ou 'nome_logradouro' não encontradas!")

# %% [markdown]
# # 7. Análise de Problemas Comuns

# %%
print("\n" + "=" * 80)
print("ANÁLISE DE PROBLEMAS COMUNS")
print("=" * 80)

problemas = []

# Problema 1: Nome de logradouro com artigos/preposições no início
if 'nome_logradouro' in df.columns:
    print(f"\n🔍 VERIFICANDO: Nomes com artigos/preposições no início")
    
    artigos = ['da', 'das', 'do', 'dos', 'de', 'a', 'o']
    nomes_com_artigo = df[
        df['nome_logradouro'].str.lower().str.split().str[0].isin(artigos)
    ]['nome_logradouro'].unique()
    
    if len(nomes_com_artigo) > 0:
        print(f"  ⚠️ Encontrados: {len(nomes_com_artigo)}")
        for nome in list(nomes_com_artigo)[:10]:
            print(f"    • {nome}")
        problemas.append(f"Nomes com artigos no início: {len(nomes_com_artigo)}")
    else:
        print(f"  ✓ Nenhum problema encontrado")

# Problema 2: Tipos não reconhecidos
if 'tipo_logradouro' in df.columns:
    print(f"\n🔍 VERIFICANDO: Tipos de logradouro")
    
    tipos_esperados = list(LOGRADOUROS_ESPERADOS.keys())
    tipos_encontrados = df['tipo_logradouro'].unique()
    tipos_nao_esperados = [t for t in tipos_encontrados if t not in tipos_esperados and pd.notna(t) and t != '']
    
    if tipos_nao_esperados:
        print(f"  ⚠️ Tipos não esperados: {len(tipos_nao_esperados)}")
        for tipo in tipos_nao_esperados:
            qtd = (df['tipo_logradouro'] == tipo).sum()
            print(f"    • '{tipo}': {qtd:,} registros")
        problemas.append(f"Tipos não esperados: {len(tipos_nao_esperados)}")
    else:
        print(f"  ✓ Todos os tipos são esperados")

# Problema 3: Números faltando quando deveriam existir
if 'numero_logradouro' in df.columns and 'Logradouro' in df.columns:
    print(f"\n🔍 VERIFICANDO: Números faltando")
    
    # Logradouros que têm número no original mas não no parseado
    sem_numero = df[
        (df['numero_logradouro'].isna() | (df['numero_logradouro'] == '')) &
        (df['Logradouro'].str.contains(r'\d', na=False))
    ]
    
    if len(sem_numero) > 0:
        print(f"  ⚠️ Registros com número não extraído: {len(sem_numero):,}")
        print(f"  Exemplos:")
        for idx, row in sem_numero.head(5).iterrows():
            print(f"    • {row['Logradouro']}")
        problemas.append(f"Números não extraídos: {len(sem_numero):,}")
    else:
        print(f"  ✓ Todos os números foram extraídos")

# Problema 4: Complementos não capturados
if 'complemento_logradouro' in df.columns and 'Logradouro' in df.columns:
    print(f"\n🔍 VERIFICANDO: Complementos")
    
    # Logradouros que têm " - " no original mas não têm complemento
    sem_complemento = df[
        (df['complemento_logradouro'].isna() | (df['complemento_logradouro'] == '')) &
        (df['Logradouro'].str.contains(' - ', na=False))
    ]
    
    if len(sem_complemento) > 0:
        print(f"  ⚠️ Registros com complemento não extraído: {len(sem_complemento):,}")
        print(f"  Exemplos:")
        for idx, row in sem_complemento.head(5).iterrows():
            print(f"    • {row['Logradouro']}")
        problemas.append(f"Complementos não extraídos: {len(sem_complemento):,}")
    else:
        print(f"  ✓ Todos os complementos foram extraídos")

# Resumo de problemas
if problemas:
    print(f"\n{'=' * 80}")
    print(f"RESUMO DE PROBLEMAS ENCONTRADOS:")
    print(f"{'=' * 80}")
    for i, problema in enumerate(problemas, 1):
        print(f"  {i}. {problema}")
else:
    print(f"\n{'=' * 80}")
    print(f"✓ NENHUM PROBLEMA CRÍTICO ENCONTRADO!")
    print(f"{'=' * 80}")

# %% [markdown]
# # 8. Top 20 Logradouros por Frequência

# %%
print("\n" + "=" * 80)
print("TOP 20 LOGRADOUROS MAIS FREQUENTES")
print("=" * 80)

if 'tipo_logradouro' in df.columns and 'nome_logradouro' in df.columns:
    # Criar coluna temporária com tipo + nome
    df_temp = df.copy()
    df_temp['logradouro_completo'] = df_temp['tipo_logradouro'] + ' ' + df_temp['nome_logradouro']
    
    top20 = df_temp['logradouro_completo'].value_counts().head(20)
    
    print(f"\n📊 Top 20 logradouros:")
    for i, (logr, qtd) in enumerate(top20.items(), 1):
        pct = (qtd / total * 100)
        print(f"  {i:2d}. {logr:<40} {qtd:>6,} ({pct:>5.1f}%)")

# %% [markdown]
# # 9. Amostras para Revisão Manual

# %%
print("\n" + "=" * 80)
print("AMOSTRAS PARA REVISÃO MANUAL")
print("=" * 80)

# Amostra 1: Logradouros com problemas potenciais
print(f"\n🔍 AMOSTRA 1: Logradouros com artigos no início")
if 'nome_logradouro' in df.columns:
    artigos = ['da', 'das', 'do', 'dos', 'de']
    df_artigos = df[df['nome_logradouro'].str.lower().str.split().str[0].isin(artigos)]
    
    if len(df_artigos) > 0:
        amostra1 = df_artigos[['Logradouro', 'tipo_logradouro', 'nome_logradouro', 'numero_logradouro']].drop_duplicates().head(10)
        print(f"\nExemplos ({len(amostra1)}):")
        for idx, row in amostra1.iterrows():
            print(f"  • {row['tipo_logradouro']} {row['nome_logradouro']}, {row['numero_logradouro']}")
            print(f"    Original: {row['Logradouro']}")
    else:
        print(f"  ✓ Nenhum encontrado")

# Amostra 2: Logradouros sem número
print(f"\n🔍 AMOSTRA 2: Logradouros sem número")
if 'numero_logradouro' in df.columns:
    df_sem_numero = df[df['numero_logradouro'].isna() | (df['numero_logradouro'] == '')]
    
    if len(df_sem_numero) > 0:
        amostra2 = df_sem_numero[['Logradouro', 'tipo_logradouro', 'nome_logradouro']].drop_duplicates().head(10)
        print(f"\nExemplos ({len(amostra2)}):")
        for idx, row in amostra2.iterrows():
            print(f"  • {row['tipo_logradouro']} {row['nome_logradouro']}")
            print(f"    Original: {row['Logradouro']}")
    else:
        print(f"  ✓ Todos têm número")

# Amostra 3: Logradouros com complemento
print(f"\n🔍 AMOSTRA 3: Logradouros com complemento")
if 'complemento_logradouro' in df.columns:
    df_com_complemento = df[df['complemento_logradouro'].notna() & (df['complemento_logradouro'] != '')]
    
    if len(df_com_complemento) > 0:
        amostra3 = df_com_complemento[['Logradouro', 'tipo_logradouro', 'nome_logradouro', 'numero_logradouro', 'complemento_logradouro']].drop_duplicates().head(10)
        print(f"\nExemplos ({len(amostra3)}):")
        for idx, row in amostra3.iterrows():
            print(f"  • {row['tipo_logradouro']} {row['nome_logradouro']}, {row['numero_logradouro']} - {row['complemento_logradouro']}")
            print(f"    Original: {row['Logradouro']}")
    else:
        print(f"  ✓ Nenhum com complemento")

# %% [markdown]
# # 10. Exportar Relatório de Validação

# %%
print("\n" + "=" * 80)
print("EXPORTANDO RELATÓRIO DE VALIDAÇÃO")
print("=" * 80)

pasta_docs = project_root / 'docs'
pasta_docs.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
arquivo_relatorio = pasta_docs / f'validacao_parsing_{timestamp}.txt'

with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("RELATÓRIO DE VALIDAÇÃO DO PARSING\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    f.write(f"Arquivo analisado: {arquivo_selecionado.name}\n")
    f.write(f"Total de registros: {total:,}\n\n")
    
    f.write("-" * 80 + "\n")
    f.write("QUALIDADE GERAL\n")
    f.write("-" * 80 + "\n")
    if 'tipo_logradouro' in df.columns:
        f.write(f"tipo_logradouro preenchido: {com_tipo:,} ({(com_tipo/total*100):.1f}%)\n")
    if 'nome_logradouro' in df.columns:
        f.write(f"nome_logradouro preenchido: {com_nome:,} ({(com_nome/total*100):.1f}%)\n")
    if 'numero_logradouro' in df.columns:
        f.write(f"numero_logradouro preenchido: {com_numero:,} ({(com_numero/total*100):.1f}%)\n")
    if 'complemento_logradouro' in df.columns:
        f.write(f"complemento_logradouro preenchido: {com_complemento:,} ({(com_complemento/total*100):.1f}%)\n")
    f.write("\n")
    
    if 'tipo_logradouro' in df.columns and 'nome_logradouro' in df.columns:
        f.write("-" * 80 + "\n")
        f.write("COMPARAÇÃO COM LOGRADOUROS ESPERADOS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Taxa de acerto geral: {taxa_geral:.1f}% ({total_corretos}/{total_esperados})\n\n")
        
        for resultado in resultados_validacao:
            f.write(f"\n{resultado['tipo']}:\n")
            f.write(f"  Esperados: {resultado['esperados']}\n")
            f.write(f"  Encontrados corretos: {resultado['encontrados_corretos']} ({resultado['taxa_acerto']:.1f}%)\n")
            
            if resultado['nao_encontrados']:
                f.write(f"  Não encontrados ({len(resultado['nao_encontrados'])}):\n")
                for nome in resultado['nao_encontrados']:
                    f.write(f"    - {nome}\n")
            
            if resultado['extras']:
                f.write(f"  Extras não esperados ({len(resultado['extras'])}):\n")
                for nome in resultado['extras'][:10]:
                    f.write(f"    - {nome}\n")
                if len(resultado['extras']) > 10:
                    f.write(f"    ... e mais {len(resultado['extras']) - 10}\n")
    
    if problemas:
        f.write("\n" + "-" * 80 + "\n")
        f.write("PROBLEMAS ENCONTRADOS\n")
        f.write("-" * 80 + "\n")
        for problema in problemas:
            f.write(f"  • {problema}\n")

print(f"✓ Relatório exportado: {arquivo_relatorio}")

# %% [markdown]
# # 11. Sugestões de Melhorias

# %%
print("\n" + "=" * 80)
print("SUGESTÕES DE MELHORIAS PARA O PARSER")
print("=" * 80)

sugestoes = []

# Analisar problemas e gerar sugestões
if 'nome_logradouro' in df.columns:
    artigos = ['da', 'das', 'do', 'dos', 'de']
    nomes_com_artigo = df[
        df['nome_logradouro'].str.lower().str.split().str[0].isin(artigos)
    ]['nome_logradouro'].unique()
    
    if len(nomes_com_artigo) > 0:
        sugestoes.append({
            'problema': 'Nomes de logradouro com artigos no início',
            'quantidade': len(nomes_com_artigo),
            'sugestao': 'Adicionar regra para manter artigos como parte do nome',
            'exemplos': list(nomes_com_artigo)[:5]
        })

if resultados_validacao:
    for resultado in resultados_validacao:
        if resultado['nao_encontrados']:
            sugestoes.append({
                'problema': f"Logradouros não encontrados - {resultado['tipo']}",
                'quantidade': len(resultado['nao_encontrados']),
                'sugestao': 'Verificar se esses logradouros existem com grafia diferente nos dados',
                'exemplos': resultado['nao_encontrados'][:5]
            })

if sugestoes:
    print(f"\n📝 SUGESTÕES IDENTIFICADAS: {len(sugestoes)}\n")
    for i, sug in enumerate(sugestoes, 1):
        print(f"{i}. {sug['problema']}")
        print(f"   Quantidade: {sug['quantidade']}")
        print(f"   Sugestão: {sug['sugestao']}")
        if sug['exemplos']:
            print(f"   Exemplos:")
            for ex in sug['exemplos']:
                print(f"     • {ex}")
        print()
else:
    print(f"\n✓ Nenhuma sugestão de melhoria identificada!")
    print(f"  O parser está funcionando muito bem! 🎉")

# %% [markdown]
# # 12. Resumo Executivo

# %%
print("\n" + "=" * 80)
print("RESUMO EXECUTIVO")
print("=" * 80)

resumo_qualidade = ""
if 'tipo_logradouro' in df.columns:
    resumo_qualidade = f"""
QUALIDADE DO PARSING:
• tipo_logradouro: {(com_tipo/total*100):.1f}% preenchido
• nome_logradouro: {(com_nome/total*100):.1f}% preenchido
• numero_logradouro: {(com_numero/total*100):.1f}% preenchido
• complemento_logradouro: {(com_complemento/total*100):.1f}% preenchido
"""

resumo_comparacao = ""
if 'tipo_logradouro' in df.columns and 'nome_logradouro' in df.columns:
    resumo_comparacao = f"""
COMPARAÇÃO COM ESPERADOS:
• Taxa de acerto: {taxa_geral:.1f}% ({total_corretos}/{total_esperados})
• Logradouros únicos encontrados: {len(logradouros_encontrados)}
"""

resumo_problemas = ""
if problemas:
    resumo_problemas = f"""
PROBLEMAS ENCONTRADOS: {len(problemas)}
"""
    for problema in problemas:
        resumo_problemas += f"• {problema}\n"
else:
    resumo_problemas = "\n✓ NENHUM PROBLEMA CRÍTICO ENCONTRADO!"

print(f"""
VALIDAÇÃO DE PARSING CONCLUÍDA!

ARQUIVO ANALISADO:
• {arquivo_selecionado.name}
• {total:,} registros
{resumo_qualidade}
{resumo_comparacao}
{resumo_problemas}

ARQUIVOS GERADOS:
✓ Relatório: {arquivo_relatorio.name}

LOCALIZAÇÃO:
• {pasta_docs}

PRÓXIMOS PASSOS:
1. Revisar problemas identificados
2. Ajustar parser se necessário
3. Re-processar planilha
4. Validar novamente
""")

print("=" * 80)
print("✓ VALIDAÇÃO CONCLUÍDA!")
print(f"✓ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("=" * 80)
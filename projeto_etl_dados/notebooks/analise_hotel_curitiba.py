"""
Análise Hotel Curitiba - Programa Redenção
Objetivo: Realocar pessoas do hotel para outros serviços

IMPORTANTE: Cada linha representa um benefício/atendimento.
A mesma pessoa pode aparecer em múltiplas linhas.
Deduplilcamos por CPF e agregamos os benefícios.

Análises:
- Sexo
- Idade
- Origem
- Benefícios (agregados por pessoa)
- Usuários de outros serviços

Autor: Pedro - SEPE
Data: 2025-11-05
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys

def imprimir_secao(texto, arquivo=None):
    """Imprime uma seção formatada no console e no arquivo"""
    separador = "=" * 100
    conteudo = f"\n{separador}\n{texto.center(100)}\n{separador}\n"
    print(conteudo)
    if arquivo:
        arquivo.write(conteudo)

def imprimir_linha(texto, arquivo=None):
    """Imprime uma linha no console e no arquivo"""
    print(texto)
    if arquivo:
        arquivo.write(texto + "\n")

def carregar_dados(caminho_arquivo):
    """Carrega os dados do arquivo Excel"""
    try:
        print(f"📂 Carregando arquivo: {caminho_arquivo}")
        df = pd.read_excel(caminho_arquivo)
        print(f"✅ Arquivo carregado com sucesso!")
        print(f"   Total de registros (linhas): {len(df)}")
        print(f"   Total de colunas: {len(df.columns)}")
        return df
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        sys.exit(1)

def filtrar_hotel_curitiba(df):
    """Filtra apenas os registros do Hotel Curitiba"""
    print("\n🔍 Filtrando dados do Hotel Curitiba...")
    
    # Verificar coluna 'Centro de Acolhida'
    if 'Centro de Acolhida' in df.columns:
        mask = df['Centro de Acolhida'].astype(str).str.contains('Hotel|Curitiba', case=False, na=False, regex=True)
        df_hotel = df[mask].copy()
        
        if len(df_hotel) > 0:
            print(f"✅ Encontrados {len(df_hotel)} registros (linhas) do Hotel Curitiba")
            return df_hotel
    
    # Se não encontrar, tentar pela coluna 'Estabelecimento Executante'
    if 'Estabelecimento Executante' in df.columns:
        mask = df['Estabelecimento Executante'].astype(str).str.contains('Hotel|Curitiba', case=False, na=False, regex=True)
        df_hotel = df[mask].copy()
        
        if len(df_hotel) > 0:
            print(f"✅ Encontrados {len(df_hotel)} registros (linhas) do Hotel Curitiba")
            return df_hotel
    
    print("⚠️ Nenhum registro do Hotel Curitiba encontrado.")
    print("   Usando todos os registros para análise...")
    return df.copy()

def deduplicar_pessoas(df_hotel, arquivo):
    """
    Deduplica o dataset por pessoa (Nome + Data de Nascimento) e agrega informações de benefícios
    """
    imprimir_secao("DEDUPLICAÇÃO E CONSOLIDAÇÃO POR PESSOA", arquivo)
    
    # Criar identificador único combinando Nome + Data de Nascimento
    imprimir_linha("\n🔑 Criando identificador único: Nome_do_Cidadao + dataNascimento", arquivo)
    
    df_hotel['ID_UNICO'] = (
        df_hotel['Nome_do_Cidadao'].astype(str).str.strip().str.upper() + 
        '|' + 
        pd.to_datetime(df_hotel['dataNascimento'], errors='coerce').astype(str)
    )
    
    id_col = 'ID_UNICO'
    
    total_linhas = len(df_hotel)
    pessoas_unicas = df_hotel[id_col].nunique()
    
    imprimir_linha(f"\nTotal de linhas no dataset: {total_linhas}", arquivo)
    imprimir_linha(f"Total de pessoas únicas identificadas: {pessoas_unicas}", arquivo)
    imprimir_linha(f"Média de linhas por pessoa: {total_linhas/pessoas_unicas:.1f}", arquivo)
    
    # Criar dataset de pessoas únicas com dados demográficos
    # Pegamos a primeira ocorrência de cada pessoa
    colunas_demograficas = [
        'Nome_do_Cidadao', 'Nome_Social', 'Sexo', 'Dias_de_Permanencia',
        'cpf', 'nomeCompleto', 'nomeSocial', 'dataNascimento', 'genero', 
        'sexo', 'raca', 'estadoCivil', 'nomeMae'
    ]
    
    colunas_existentes = [col for col in colunas_demograficas if col in df_hotel.columns]
    colunas_existentes.insert(0, id_col)
    
    df_pessoas = df_hotel[colunas_existentes].drop_duplicates(subset=[id_col], keep='first').copy()
    
    imprimir_linha(f"\n✅ Dataset de pessoas únicas criado: {len(df_pessoas)} pessoas", arquivo)
    
    # Agregar benefícios por pessoa
    beneficios_por_pessoa = df_hotel.groupby(id_col).agg({
        'NomeBeneficio': lambda x: list(x.dropna().unique()) if 'NomeBeneficio' in df_hotel.columns else [],
        'valorPagto': 'sum' if 'valorPagto' in df_hotel.columns else lambda x: 0,
        'qtPagto': 'sum' if 'qtPagto' in df_hotel.columns else lambda x: 0
    }).reset_index()
    
    # Adicionar informações agregadas ao dataset de pessoas
    df_pessoas = df_pessoas.merge(beneficios_por_pessoa, on=id_col, how='left')
    
    # Criar flag de tem benefício
    df_pessoas['TEM_BENEFICIO'] = df_pessoas['NomeBeneficio'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)
    df_pessoas['QTD_BENEFICIOS'] = df_pessoas['NomeBeneficio'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    
    # Agregar atendimentos por pessoa
    if 'Estabelecimento Executante' in df_hotel.columns:
        atendimentos = df_hotel.groupby(id_col)['Estabelecimento Executante'].apply(
            lambda x: list(x.dropna().unique())
        ).reset_index()
        atendimentos.columns = [id_col, 'ESTABELECIMENTOS']
        df_pessoas = df_pessoas.merge(atendimentos, on=id_col, how='left')
        df_pessoas['QTD_ESTABELECIMENTOS'] = df_pessoas['ESTABELECIMENTOS'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )
    
    # Agregar procedimentos por pessoa
    if 'Procedimento' in df_hotel.columns:
        procedimentos = df_hotel.groupby(id_col)['Procedimento'].apply(
            lambda x: list(x.dropna().unique())
        ).reset_index()
        procedimentos.columns = [id_col, 'PROCEDIMENTOS']
        df_pessoas = df_pessoas.merge(procedimentos, on=id_col, how='left')
        df_pessoas['QTD_PROCEDIMENTOS'] = df_pessoas['PROCEDIMENTOS'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )
    
    imprimir_linha(f"\n📊 Estatísticas de agregação:", arquivo)
    imprimir_linha(f"   Pessoas com benefícios: {df_pessoas['TEM_BENEFICIO'].sum()} ({(df_pessoas['TEM_BENEFICIO'].sum()/len(df_pessoas)*100):.1f}%)", arquivo)
    imprimir_linha(f"   Média de benefícios por pessoa: {df_pessoas['QTD_BENEFICIOS'].mean():.2f}", arquivo)
    
    if 'QTD_ESTABELECIMENTOS' in df_pessoas.columns:
        imprimir_linha(f"   Média de estabelecimentos por pessoa: {df_pessoas['QTD_ESTABELECIMENTOS'].mean():.2f}", arquivo)
    
    if 'QTD_PROCEDIMENTOS' in df_pessoas.columns:
        imprimir_linha(f"   Média de procedimentos por pessoa: {df_pessoas['QTD_PROCEDIMENTOS'].mean():.2f}", arquivo)
    
    return df_pessoas, df_hotel

def analisar_sexo(df_pessoas, arquivo):
    """Análise da distribuição por sexo"""
    imprimir_secao("ANÁLISE POR SEXO", arquivo)
    
    col_sexo = 'Sexo' if 'Sexo' in df_pessoas.columns else 'sexo'
    
    sexo_count = df_pessoas[col_sexo].value_counts()
    total = len(df_pessoas)
    
    # Mapear M/F para Masculino/Feminino
    mapa_sexo = {'M': 'Masculino', 'F': 'Feminino'}
    
    imprimir_linha("\nDistribuição por sexo:", arquivo)
    for sexo, qtd in sexo_count.items():
        percentual = (qtd / total) * 100
        sexo_nome = mapa_sexo.get(sexo, sexo)
        barra = '█' * int(percentual / 2)
        imprimir_linha(f"  {sexo_nome:10s}: {qtd:3d} ({percentual:5.1f}%) {barra}", arquivo)
    
    imprimir_linha(f"\nTotal: {total} pessoas", arquivo)
    
    return sexo_count

def analisar_idade(df_pessoas, arquivo):
    """Análise da distribuição por idade"""
    imprimir_secao("ANÁLISE POR IDADE", arquivo)
    
    col_data_nasc = 'dataNascimento'
    
    if col_data_nasc not in df_pessoas.columns:
        imprimir_linha("⚠️ Coluna de data de nascimento não encontrada", arquivo)
        return df_pessoas
    
    # Calcular idade
    try:
        df_pessoas['IDADE'] = (pd.to_datetime('today') - pd.to_datetime(df_pessoas[col_data_nasc])).dt.days // 365
        
        # Remover idades inválidas
        df_pessoas = df_pessoas[(df_pessoas['IDADE'] >= 0) & (df_pessoas['IDADE'] <= 120)]
        
        # Estatísticas
        imprimir_linha("\nEstatísticas de idade:", arquivo)
        imprimir_linha(f"  Idade média: {df_pessoas['IDADE'].mean():.1f} anos", arquivo)
        imprimir_linha(f"  Idade mediana: {df_pessoas['IDADE'].median():.1f} anos", arquivo)
        imprimir_linha(f"  Idade mínima: {df_pessoas['IDADE'].min():.0f} anos", arquivo)
        imprimir_linha(f"  Idade máxima: {df_pessoas['IDADE'].max():.0f} anos", arquivo)
        imprimir_linha(f"  Desvio padrão: {df_pessoas['IDADE'].std():.1f} anos", arquivo)
        
        # Faixas etárias
        bins = [0, 18, 30, 40, 50, 60, 120]
        labels = ['0-17', '18-29', '30-39', '40-49', '50-59', '60+']
        df_pessoas['FAIXA_ETARIA'] = pd.cut(df_pessoas['IDADE'], bins=bins, labels=labels)
        
        faixa_count = df_pessoas['FAIXA_ETARIA'].value_counts().sort_index()
        total = len(df_pessoas)
        
        imprimir_linha("\nDistribuição por faixa etária:", arquivo)
        for faixa, qtd in faixa_count.items():
            percentual = (qtd / total) * 100
            barra = '█' * int(percentual / 2)
            imprimir_linha(f"  {faixa} anos: {qtd:3d} ({percentual:5.1f}%) {barra}", arquivo)
        
    except Exception as e:
        imprimir_linha(f"⚠️ Erro ao calcular idade: {e}", arquivo)
    
    return df_pessoas

def analisar_origem(df_pessoas, arquivo):
    """Análise da origem dos usuários (raça e estado civil)"""
    imprimir_secao("ANÁLISE DEMOGRÁFICA", arquivo)
    
    # Raça/Cor
    if 'raca' in df_pessoas.columns:
        imprimir_linha("\nDistribuição por raça/cor:", arquivo)
        raca_count = df_pessoas['raca'].value_counts()
        total = len(df_pessoas)
        for raca, qtd in raca_count.items():
            if pd.notna(raca):
                percentual = (qtd / total) * 100
                barra = '█' * int(percentual / 2)
                imprimir_linha(f"  {raca:20s}: {qtd:3d} ({percentual:5.1f}%) {barra}", arquivo)
    
    # Estado Civil
    if 'estadoCivil' in df_pessoas.columns:
        imprimir_linha("\nDistribuição por estado civil:", arquivo)
        estado_count = df_pessoas['estadoCivil'].value_counts()
        total = len(df_pessoas)
        for estado, qtd in estado_count.items():
            if pd.notna(estado):
                percentual = (qtd / total) * 100
                barra = '█' * int(percentual / 2)
                imprimir_linha(f"  {estado:20s}: {qtd:3d} ({percentual:5.1f}%) {barra}", arquivo)

def analisar_permanencia(df_pessoas, arquivo):
    """Análise dos dias de permanência"""
    imprimir_secao("ANÁLISE DE PERMANÊNCIA", arquivo)
    
    if 'Dias_de_Permanencia' not in df_pessoas.columns:
        imprimir_linha("⚠️ Coluna de dias de permanência não encontrada", arquivo)
        return
    
    # Converter para numérico
    df_pessoas['Dias_Permanencia_Num'] = pd.to_numeric(df_pessoas['Dias_de_Permanencia'], errors='coerce')
    
    # Remover valores nulos
    dados_validos = df_pessoas['Dias_Permanencia_Num'].dropna()
    
    if len(dados_validos) > 0:
        imprimir_linha("\nEstatísticas de permanência:", arquivo)
        imprimir_linha(f"  Média: {dados_validos.mean():.1f} dias", arquivo)
        imprimir_linha(f"  Mediana: {dados_validos.median():.1f} dias", arquivo)
        imprimir_linha(f"  Mínimo: {dados_validos.min():.0f} dias", arquivo)
        imprimir_linha(f"  Máximo: {dados_validos.max():.0f} dias", arquivo)
        
        # Categorias de permanência
        bins = [0, 30, 90, 180, 365, float('inf')]
        labels = ['0-30 dias', '31-90 dias', '91-180 dias', '181-365 dias', 'Mais de 1 ano']
        df_pessoas['CATEGORIA_PERMANENCIA'] = pd.cut(df_pessoas['Dias_Permanencia_Num'], bins=bins, labels=labels)
        
        cat_count = df_pessoas['CATEGORIA_PERMANENCIA'].value_counts().sort_index()
        total = len(df_pessoas)
        
        imprimir_linha("\nDistribuição por tempo de permanência:", arquivo)
        for cat, qtd in cat_count.items():
            percentual = (qtd / total) * 100
            barra = '█' * int(percentual / 2)
            imprimir_linha(f"  {cat:20s}: {qtd:3d} ({percentual:5.1f}%) {barra}", arquivo)

def analisar_beneficios(df_pessoas, df_hotel, arquivo):
    """Análise de benefícios agregados por pessoa"""
    imprimir_secao("ANÁLISE DE BENEFÍCIOS", arquivo)
    
    # Estatísticas gerais
    com_beneficio = df_pessoas['TEM_BENEFICIO'].sum()
    sem_beneficio = len(df_pessoas) - com_beneficio
    total = len(df_pessoas)
    
    imprimir_linha("\nAcesso a benefícios:", arquivo)
    imprimir_linha(f"  COM benefício: {com_beneficio} ({(com_beneficio/total*100):.1f}%)", arquivo)
    imprimir_linha(f"  SEM benefício: {sem_beneficio} ({(sem_beneficio/total*100):.1f}%)", arquivo)
    
    # Quantidade de benefícios por pessoa
    imprimir_linha("\nQuantidade de benefícios por pessoa:", arquivo)
    qtd_benef_count = df_pessoas['QTD_BENEFICIOS'].value_counts().sort_index()
    for qtd, pessoas in qtd_benef_count.items():
        percentual = (pessoas / total) * 100
        imprimir_linha(f"  {qtd} benefício(s): {pessoas} pessoas ({percentual:.1f}%)", arquivo)
    
    # Tipos de benefícios (do dataset original)
    if 'NomeBeneficio' in df_hotel.columns:
        imprimir_linha("\nTipos de benefícios registrados (todas as ocorrências):", arquivo)
        beneficios_count = df_hotel['NomeBeneficio'].value_counts()
        for beneficio, qtd in beneficios_count.items():
            if pd.notna(beneficio):
                # Contar quantas pessoas únicas têm esse benefício
                pessoas_com_beneficio = df_hotel[df_hotel['NomeBeneficio'] == beneficio]['ID_UNICO'].nunique()
                imprimir_linha(f"  {beneficio}: {pessoas_com_beneficio} pessoas ({qtd} registros)", arquivo)
    
    # Análise de valores
    if 'valorPagto' in df_pessoas.columns:
        valores_validos = df_pessoas[df_pessoas['valorPagto'] > 0]['valorPagto']
        if len(valores_validos) > 0:
            imprimir_linha("\nValores de benefícios (agregado por pessoa):", arquivo)
            imprimir_linha(f"  Pessoas com valor > 0: {len(valores_validos)}", arquivo)
            imprimir_linha(f"  Valor médio por pessoa: R$ {valores_validos.mean():.2f}", arquivo)
            imprimir_linha(f"  Valor mediano: R$ {valores_validos.median():.2f}", arquivo)
            imprimir_linha(f"  Valor total: R$ {valores_validos.sum():.2f}", arquivo)
            imprimir_linha(f"  Valor máximo: R$ {valores_validos.max():.2f}", arquivo)

def analisar_outros_servicos(df_pessoas, df_hotel, arquivo):
    """Análise de uso de outros serviços"""
    imprimir_secao("ANÁLISE DE OUTROS SERVIÇOS", arquivo)
    
    # Estatísticas de estabelecimentos por pessoa
    if 'QTD_ESTABELECIMENTOS' in df_pessoas.columns:
        imprimir_linha("\nQuantidade de estabelecimentos por pessoa:", arquivo)
        qtd_estab = df_pessoas['QTD_ESTABELECIMENTOS'].value_counts().sort_index()
        for qtd, pessoas in qtd_estab.items():
            percentual = (pessoas / len(df_pessoas)) * 100
            imprimir_linha(f"  {qtd} estabelecimento(s): {pessoas} pessoas ({percentual:.1f}%)", arquivo)
    
    # Top estabelecimentos
    if 'Estabelecimento Executante' in df_hotel.columns:
        estabelecimentos = df_hotel['Estabelecimento Executante'].dropna()
        if len(estabelecimentos) > 0:
            imprimir_linha("\nTop 10 estabelecimentos executantes (por atendimentos):", arquivo)
            estab_count = estabelecimentos.value_counts().head(10)
            for i, (estab, qtd) in enumerate(estab_count.items(), 1):
                # Contar pessoas únicas
                pessoas = df_hotel[df_hotel['Estabelecimento Executante'] == estab]['ID_UNICO'].nunique()
                imprimir_linha(f"  {i:2d}. {estab}: {pessoas} pessoas ({qtd} atendimentos)", arquivo)
    
    # Estatísticas de procedimentos por pessoa
    if 'QTD_PROCEDIMENTOS' in df_pessoas.columns:
        imprimir_linha("\nQuantidade de procedimentos por pessoa:", arquivo)
        qtd_proc = df_pessoas['QTD_PROCEDIMENTOS'].value_counts().sort_index().head(10)
        for qtd, pessoas in qtd_proc.items():
            percentual = (pessoas / len(df_pessoas)) * 100
            imprimir_linha(f"  {qtd} procedimento(s): {pessoas} pessoas ({percentual:.1f}%)", arquivo)
    
    # Especialidades
    if 'Especialidade' in df_hotel.columns:
        especialidades = df_hotel['Especialidade'].dropna()
        if len(especialidades) > 0:
            imprimir_linha("\nTop 10 especialidades dos atendimentos:", arquivo)
            esp_count = especialidades.value_counts().head(10)
            for i, (esp, qtd) in enumerate(esp_count.items(), 1):
                pessoas = df_hotel[df_hotel['Especialidade'] == esp]['ID_UNICO'].nunique()
                imprimir_linha(f"  {i:2d}. {esp}: {pessoas} pessoas ({qtd} atendimentos)", arquivo)

def gerar_perfil_realocacao(df_pessoas, arquivo):
    """Gera perfil para realocação"""
    imprimir_secao("PERFIL PARA REALOCAÇÃO", arquivo)
    
    # Perfil demográfico
    if 'FAIXA_ETARIA' in df_pessoas.columns and 'Sexo' in df_pessoas.columns:
        col_sexo = 'Sexo' if 'Sexo' in df_pessoas.columns else 'sexo'
        mapa_sexo = {'M': 'Masculino', 'F': 'Feminino'}
        
        imprimir_linha("\nDistribuição: Sexo x Faixa Etária", arquivo)
        imprimir_linha("-" * 100, arquivo)
        
        perfil = df_pessoas.groupby([col_sexo, 'FAIXA_ETARIA']).size().reset_index(name='Quantidade')
        perfil = perfil.sort_values('Quantidade', ascending=False)
        
        for _, row in perfil.iterrows():
            sexo_nome = mapa_sexo.get(row[col_sexo], row[col_sexo])
            imprimir_linha(f"  {sexo_nome:10s} | {row['FAIXA_ETARIA']:10s} : {row['Quantidade']:3d} pessoas", arquivo)
    
    # Critérios de priorização
    imprimir_linha("\n" + "-" * 100, arquivo)
    imprimir_linha("\nCritérios sugeridos para priorização na realocação:", arquivo)
    imprimir_linha("-" * 100, arquivo)
    
    if 'TEM_BENEFICIO' in df_pessoas.columns and 'IDADE' in df_pessoas.columns:
        # 1. Pessoas com benefícios E idade produtiva
        alta_prioridade = (
            (df_pessoas['TEM_BENEFICIO'] == True) &
            (df_pessoas['IDADE'].between(18, 59))
        ).sum()
        
        # 2. Pessoas sem benefícios (precisam de mais suporte)
        sem_beneficio = (df_pessoas['TEM_BENEFICIO'] == False).sum()
        
        # 3. Idosos (60+)
        idosos = (df_pessoas['IDADE'] >= 60).sum()
        
        # 4. Jovens (<18)
        jovens = (df_pessoas['IDADE'] < 18).sum()
        
        # 5. Permanência longa
        if 'Dias_Permanencia_Num' in df_pessoas.columns:
            permanencia_longa = (df_pessoas['Dias_Permanencia_Num'] > 180).sum()
            imprimir_linha(f"\n  🔴 PERMANÊNCIA PROLONGADA (>180 dias): {permanencia_longa} pessoas", arquivo)
            imprimir_linha(f"     → Necessitam de atenção especial para realocação", arquivo)
        
        # 6. Pessoas com múltiplos benefícios
        if 'QTD_BENEFICIOS' in df_pessoas.columns:
            multiplos_beneficios = (df_pessoas['QTD_BENEFICIOS'] >= 2).sum()
            imprimir_linha(f"\n  🟣 MÚLTIPLOS BENEFÍCIOS (2+): {multiplos_beneficios} pessoas", arquivo)
            imprimir_linha(f"     → Já inseridas em múltiplos programas", arquivo)
        
        imprimir_linha(f"\n  🟢 ALTA PRIORIDADE (com benefícios, 18-59 anos): {alta_prioridade} pessoas", arquivo)
        imprimir_linha(f"     → Maior autonomia potencial, já inseridos em programas", arquivo)
        
        imprimir_linha(f"\n  🟡 ATENÇÃO ESPECIAL (sem benefícios): {sem_beneficio} pessoas", arquivo)
        imprimir_linha(f"     → Precisam de encaminhamento para programas sociais", arquivo)
        
        imprimir_linha(f"\n  🟠 GRUPO IDOSOS (60+ anos): {idosos} pessoas", arquivo)
        imprimir_linha(f"     → Necessitam de serviços especializados para idosos", arquivo)
        
        imprimir_linha(f"\n  🔵 GRUPO JOVENS (< 18 anos): {jovens} pessoas", arquivo)
        imprimir_linha(f"     → Necessitam de proteção especial e serviços para crianças/adolescentes", arquivo)

def gerar_resumo_executivo(df_pessoas, arquivo):
    """Gera resumo executivo da análise"""
    imprimir_secao("RESUMO EXECUTIVO", arquivo)
    
    imprimir_linha(f"\n📊 DADOS GERAIS", arquivo)
    imprimir_linha(f"   Total de pessoas únicas: {len(df_pessoas)}", arquivo)
    
    if 'IDADE' in df_pessoas.columns:
        imprimir_linha(f"   Idade média: {df_pessoas['IDADE'].mean():.1f} anos", arquivo)
        imprimir_linha(f"   Idade mediana: {df_pessoas['IDADE'].median():.1f} anos", arquivo)
    
    col_sexo = 'Sexo' if 'Sexo' in df_pessoas.columns else 'sexo'
    if col_sexo in df_pessoas.columns:
        imprimir_linha(f"\n👥 DISTRIBUIÇÃO POR SEXO", arquivo)
        sexo_count = df_pessoas[col_sexo].value_counts()
        mapa_sexo = {'M': 'Masculino', 'F': 'Feminino'}
        for sexo, qtd in sexo_count.items():
            sexo_nome = mapa_sexo.get(sexo, sexo)
            imprimir_linha(f"   {sexo_nome}: {qtd} ({(qtd/len(df_pessoas)*100):.1f}%)", arquivo)
    
    if 'TEM_BENEFICIO' in df_pessoas.columns:
        com_beneficio = df_pessoas['TEM_BENEFICIO'].sum()
        imprimir_linha(f"\n💰 BENEFÍCIOS", arquivo)
        imprimir_linha(f"   Com benefício: {com_beneficio} ({(com_beneficio/len(df_pessoas)*100):.1f}%)", arquivo)
        imprimir_linha(f"   Sem benefício: {len(df_pessoas)-com_beneficio} ({((len(df_pessoas)-com_beneficio)/len(df_pessoas)*100):.1f}%)", arquivo)
        
        if 'QTD_BENEFICIOS' in df_pessoas.columns:
            media_beneficios = df_pessoas[df_pessoas['TEM_BENEFICIO']]['QTD_BENEFICIOS'].mean()
            imprimir_linha(f"   Média de benefícios (quem tem): {media_beneficios:.2f}", arquivo)
    
    if 'Dias_Permanencia_Num' in df_pessoas.columns:
        dados_validos = df_pessoas['Dias_Permanencia_Num'].dropna()
        if len(dados_validos) > 0:
            imprimir_linha(f"\n⏱️  PERMANÊNCIA", arquivo)
            imprimir_linha(f"   Média: {dados_validos.mean():.0f} dias", arquivo)
            imprimir_linha(f"   Mediana: {dados_validos.median():.0f} dias", arquivo)
            imprimir_linha(f"   Máxima: {dados_validos.max():.0f} dias", arquivo)
    
    if 'valorPagto' in df_pessoas.columns:
        valores_validos = df_pessoas[df_pessoas['valorPagto'] > 0]['valorPagto']
        if len(valores_validos) > 0:
            imprimir_linha(f"\n💵 VALORES PAGOS", arquivo)
            imprimir_linha(f"   Total pago: R$ {valores_validos.sum():,.2f}", arquivo)
            imprimir_linha(f"   Média por pessoa beneficiária: R$ {valores_validos.mean():,.2f}", arquivo)

def exportar_dados_csv(df_pessoas, df_hotel, timestamp):
    """Exporta dados completos para CSV"""
    try:
        # CSV de pessoas únicas
        arquivo_pessoas = f'hotel_curitiba_pessoas_{timestamp}.csv'
        df_pessoas.to_csv(arquivo_pessoas, index=False, encoding='utf-8-sig', sep=';')
        print(f"\n✅ Dados de pessoas exportados: {arquivo_pessoas}")
        
        # CSV com todos os registros originais
        arquivo_completo = f'hotel_curitiba_completo_{timestamp}.csv'
        df_hotel.to_csv(arquivo_completo, index=False, encoding='utf-8-sig', sep=';')
        print(f"✅ Dados completos exportados: {arquivo_completo}")
        
        return arquivo_pessoas, arquivo_completo
    except Exception as e:
        print(f"\n⚠️ Erro ao exportar CSV: {e}")
        return None, None

def main():
    """Função principal"""
    print("\n" + "="*100)
    print("ANÁLISE HOTEL CURITIBA - PROGRAMA REDENÇÃO".center(100))
    print("SEPE - Secretaria Executiva de Projetos Estratégicos".center(100))
    print("="*100 + "\n")
    
    # Caminho do arquivo - AJUSTE AQUI SE NECESSÁRIO
    caminho_arquivo = r'C:\Users\x504693\Downloads\CidadaosVinculadosXBeneficios.xlsx'
    
    # Carregar dados
    df = carregar_dados(caminho_arquivo)
    
    # Filtrar Hotel Curitiba
    df_hotel = filtrar_hotel_curitiba(df)
    
    # Criar arquivo de relatório
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_relatorio = f'relatorio_hotel_curitiba_{timestamp}.txt'
    
    print(f"\n📝 Gerando relatório: {nome_relatorio}\n")
    
    with open(nome_relatorio, 'w', encoding='utf-8') as arquivo:
        # Cabeçalho do relatório
        arquivo.write("="*100 + "\n")
        arquivo.write("RELATÓRIO DE ANÁLISE - HOTEL CURITIBA\n".center(100))
        arquivo.write("Programa Redenção - SEPE\n".center(100))
        arquivo.write(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n".center(100))
        arquivo.write("="*100 + "\n")
        
        # Deduplicar e consolidar
        df_pessoas, df_hotel = deduplicar_pessoas(df_hotel, arquivo)
        
        # Executar análises
        analisar_sexo(df_pessoas, arquivo)
        df_pessoas = analisar_idade(df_pessoas, arquivo)
        analisar_origem(df_pessoas, arquivo)
        analisar_permanencia(df_pessoas, arquivo)
        analisar_beneficios(df_pessoas, df_hotel, arquivo)
        analisar_outros_servicos(df_pessoas, df_hotel, arquivo)
        gerar_perfil_realocacao(df_pessoas, arquivo)
        gerar_resumo_executivo(df_pessoas, arquivo)
        
        # Rodapé
        arquivo.write("\n" + "="*100 + "\n")
        arquivo.write("FIM DO RELATÓRIO\n".center(100))
        arquivo.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n".center(100))
        arquivo.write("="*100 + "\n")
    
    print(f"\n{'='*100}")
    print(f"✅ RELATÓRIO GERADO COM SUCESSO!".center(100))
    print(f"{'='*100}")
    print(f"\n📄 Arquivo TXT: {nome_relatorio}")
    
    # Exportar dados para CSV
    arq_pessoas, arq_completo = exportar_dados_csv(df_pessoas, df_hotel, timestamp)
    if arq_pessoas:
        print(f"📊 Pessoas únicas: {arq_pessoas}")
        print(f"📊 Dados completos: {arq_completo}")
    
    print(f"\n✨ Análise concluída! Os arquivos estão na mesma pasta do script.")

if __name__ == "__main__":
    main()
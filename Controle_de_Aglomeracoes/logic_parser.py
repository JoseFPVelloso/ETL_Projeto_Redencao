# logic_parser.py

import pandas as pd
import re
from pathlib import Path
from datetime import datetime
import warnings
import traceback

warnings.filterwarnings('ignore')

TIPOS_LOGRADOURO = [
    'Rua', 'Avenida', 'Alameda', 'Praça', 'Viaduto',
    'Terminal', 'Largo', 'Parque', 'Passarela',
    'Travessa', 'Viela', 'Galeria', 'Escadaria',
    'Jardim', 'Quadra', 'Rodovia', 'Estrada',
    'Ladeira', 'Beco', 'Vila', 'Conjunto',
    'Ponte', 'Túnel', 'Elevado', 'Corredor', 'Pátio', 'Complexo'
]

PATTERN_TIPOS = '|'.join(TIPOS_LOGRADOURO)

# Palavras que indicam que o que segue NÃO é o número principal do logradouro
# (evita capturar 'apto 2', 'bloco 3', 'sala 5' como número do endereço)
_SUFIXOS_NAO_NUMERO = re.compile(
    r'\s+(apto|ap|bloco|bl|sala|andar|and|loja|lj|cj|conjunto|galpao|galpão|fund|fundo|lote)\b',
    re.IGNORECASE
)


def parse_logradouro(logradouro_original):
    """
    Parse logradouro com extração robusta de número.
    Correções:
      - Número com letra separada por espaço (ex: '10 A') é tratado como '10A'.
      - Sufixos não-numéricos (apto, bloco, sala…) não são confundidos com número.
      - Garante que o número extraído é sempre o do logradouro, não de complementos.
    """
    resultado = {
        'tipo_logradouro': '',
        'nome_logradouro': '',
        'numero_logradouro': '',
        'complemento_logradouro': '',
        'logradouro_padronizado': ''
    }

    if pd.isna(logradouro_original) or str(logradouro_original).strip() == '':
        return resultado

    logradouro = str(logradouro_original).strip()

    # PASSO 1: Separar COMPLEMENTO (delimitado por ' - ')
    if ' - ' in logradouro:
        partes = logradouro.split(' - ', 1)
        parte_principal = partes[0].strip()
        resultado['complemento_logradouro'] = partes[1].strip()
    else:
        parte_principal = logradouro

    # PASSO 2: Separar NÚMERO
    tipo_nome = parte_principal
    numero = ''

    if ',' in parte_principal:
        # Formato canônico: 'Rua das Flores, 10'
        partes = parte_principal.split(',', 1)
        tipo_nome = partes[0].strip()
        numero = partes[1].strip()
    else:
        # FIX: truncar na primeira ocorrência de sufixo não-numérico antes de buscar número
        parte_sem_sufixo = _SUFIXOS_NAO_NUMERO.split(parte_principal)[0].strip()

        # FIX: aceitar número seguido de letra opcionalmente separada por espaço
        # ex: '10 A' -> '10A', '10A' -> '10A', '10' -> '10'
        match = re.search(r'\s+(\d+)\s*([A-Za-z]?)$', parte_sem_sufixo)
        if match:
            numero = match.group(1) + match.group(2).upper()
            tipo_nome = parte_sem_sufixo[:match.start()].strip()

    resultado['numero_logradouro'] = numero.strip()

    # PASSO 3: Separar TIPO e NOME
    tipo_match = re.match(rf'^({PATTERN_TIPOS})\b', tipo_nome, re.IGNORECASE)

    if tipo_match:
        resultado['tipo_logradouro'] = tipo_match.group(1).title()
        resultado['nome_logradouro'] = tipo_nome[tipo_match.end():].strip()
    else:
        partes = tipo_nome.split(maxsplit=1)
        if len(partes) >= 2:
            resultado['tipo_logradouro'] = partes[0].title()
            resultado['nome_logradouro'] = partes[1]
        elif len(partes) == 1:
            resultado['nome_logradouro'] = partes[0]

    # PASSO 4: Limpeza final
    for key in resultado:
        if resultado[key] and key != 'logradouro_padronizado':
            resultado[key] = ' '.join(resultado[key].split())

    # PASSO 5: Montar logradouro padronizado
    logr_padrao = resultado['tipo_logradouro']
    if resultado['nome_logradouro']:
        logr_padrao += ' ' + resultado['nome_logradouro']
    if resultado['numero_logradouro']:
        logr_padrao += ', ' + resultado['numero_logradouro']
    if resultado['complemento_logradouro']:
        logr_padrao += ' - ' + resultado['complemento_logradouro']

    resultado['logradouro_padronizado'] = logr_padrao.strip()

    return resultado


def parse_periodo(periodo_original):
    """
    Parse e padronização do campo Período.
    FIX: inclui normalização de acentos no fallback regex para evitar
    que 'Manhã' sem acento passe como valor não reconhecido.
    """
    if pd.isna(periodo_original) or str(periodo_original).strip() == '':
        return ''

    periodo = str(periodo_original).strip()

    mapeamento_direto = {
        '05h - Madrugada': '05h - Madrugada',
        '10h - Manhã': '10h - Manhã',
        '15h - Tarde': '15h - Tarde',
        '20h - Noite': '20h - Noite',
    }
    if periodo in mapeamento_direto:
        return mapeamento_direto[periodo]

    mapeamento_invertido = {
        'Madrugada - 05h': '05h - Madrugada',
        'Manhã - 10h': '10h - Manhã',
        'Tarde - 15h': '15h - Tarde',
        'Noite - 20h': '20h - Noite',
    }
    if periodo in mapeamento_invertido:
        return mapeamento_invertido[periodo]

    # FIX: normalização adicional para variações sem acento ou com ordem diferente
    periodo_lower = periodo.lower()
    if 'madrug' in periodo_lower:
        hora = re.search(r'\d{1,2}', periodo_lower)
        return f"{hora.group().zfill(2)}h - Madrugada" if hora else '05h - Madrugada'
    if 'manh' in periodo_lower:
        hora = re.search(r'\d{1,2}', periodo_lower)
        return f"{hora.group().zfill(2)}h - Manhã" if hora else '10h - Manhã'
    if 'tarde' in periodo_lower:
        hora = re.search(r'\d{1,2}', periodo_lower)
        return f"{hora.group().zfill(2)}h - Tarde" if hora else '15h - Tarde'
    if 'noite' in periodo_lower:
        hora = re.search(r'\d{1,2}', periodo_lower)
        return f"{hora.group().zfill(2)}h - Noite" if hora else '20h - Noite'

    # Fallback genérico para formatos desconhecidos
    match = re.match(r'^(\d{1,2})h\s*-\s*(\w+)', periodo)
    if match:
        hora_num = match.group(1).zfill(2)
        descricao = match.group(2).strip().title()
        return f"{hora_num}h - {descricao}"

    match = re.match(r'^(\w+)\s*-\s*(\d{1,2})h', periodo)
    if match:
        descricao = match.group(1).strip().title()
        hora_num = match.group(2).zfill(2)
        return f"{hora_num}h - {descricao}"

    return periodo


def execute_parser(arquivo_selecionado_path, log_callback):
    """
    Função principal que executa toda a lógica de parsing.
    """
    try:
        log_callback("=" * 80)
        log_callback("INICIANDO PARSER COMPLETO")
        log_callback("=" * 80)

        arquivo_selecionado = Path(arquivo_selecionado_path)

        script_dir = Path(__file__).parent
        project_root = script_dir

        if not (project_root / 'data').exists():
            project_root = script_dir.parent
            if not (project_root / 'data').exists():
                log_callback(f"❌ Estrutura de pastas 'data' não encontrada a partir de {script_dir}")
                raise FileNotFoundError("Não foi possível localizar a pasta 'data'")

        pasta_processed = project_root / 'data' / 'processed'
        pasta_processed.mkdir(parents=True, exist_ok=True)
        log_callback(f"✓ Pasta de saída: {pasta_processed}")

        pasta_docs = project_root / 'docs'
        pasta_docs.mkdir(parents=True, exist_ok=True)
        log_callback(f"✓ Pasta de relatórios: {pasta_docs}")

        log_callback("\n" + "=" * 80)
        log_callback("CARREGANDO PLANILHA")
        log_callback("=" * 80)

        df = pd.read_excel(arquivo_selecionado)
        log_callback(f"\n✓ Arquivo carregado: {arquivo_selecionado.name}")
        log_callback(f"✓ Total de registros: {len(df):,}")

        tem_logradouro = 'Logradouro' in df.columns
        tem_periodo = 'Período' in df.columns

        if not tem_logradouro and not tem_periodo:
            log_callback(f"\n❌ ERRO: Colunas 'Logradouro' e 'Período' não encontradas!")
            raise KeyError("Colunas necessárias não encontradas")

        log_callback("\n" + "=" * 80)
        log_callback("APLICANDO PARSERS")
        log_callback("=" * 80)

        if tem_logradouro:
            log_callback(f"\n🔄 Processando campo 'Logradouro'...")
            logradouros_parseados = df['Logradouro'].apply(parse_logradouro)
            df['Logradouro'] = logradouros_parseados.apply(lambda x: x['logradouro_padronizado'])
            df['tipo_logradouro'] = logradouros_parseados.apply(lambda x: x['tipo_logradouro'])
            df['nome_logradouro'] = logradouros_parseados.apply(lambda x: x['nome_logradouro'])
            df['numero_logradouro'] = logradouros_parseados.apply(lambda x: x['numero_logradouro'])
            df['complemento_logradouro'] = logradouros_parseados.apply(lambda x: x['complemento_logradouro'])
            log_callback(f"✓ Campo 'Logradouro' parseado com sucesso!")

        if tem_periodo:
            log_callback(f"\n🔄 Processando campo 'Período'...")
            df['Período'] = df['Período'].apply(parse_periodo)
            log_callback(f"✓ Campo 'Período' padronizado com sucesso!")

        log_callback(f"\n✓ Parsing concluído!")

        log_callback("\n" + "=" * 80)
        log_callback("ANÁLISE DE QUALIDADE DO PARSING")
        log_callback("=" * 80)
        total = len(df)

        com_tipo = 0
        com_nome = 0
        com_numero = 0
        com_complemento = 0
        tipos_contagem = pd.Series(dtype='int64')
        periodos_validos = 0
        valores_unicos = 0
        periodos_contagem = pd.Series(dtype='int64')

        if tem_logradouro:
            com_tipo = (df['tipo_logradouro'] != '').sum()
            com_nome = (df['nome_logradouro'] != '').sum()
            com_numero = (df['numero_logradouro'] != '').sum()
            com_complemento = (df['complemento_logradouro'] != '').sum()
            tipos_contagem = df[df['tipo_logradouro'] != '']['tipo_logradouro'].value_counts()
            log_callback(f"\n📊 LOGRADOURO:")
            log_callback(f"  • Com tipo: {com_tipo:,} ({(com_tipo/total*100):.1f}%)")
            log_callback(f"  • Com nome: {com_nome:,} ({(com_nome/total*100):.1f}%)")
            log_callback(f"  • Com número: {com_numero:,} ({(com_numero/total*100):.1f}%)")
            log_callback(f"  • Com complemento: {com_complemento:,} ({(com_complemento/total*100):.1f}%)")

        if tem_periodo:
            valores_unicos = df['Período'].nunique()
            periodos_validos = df['Período'].notna().sum()
            periodos_contagem = df['Período'].value_counts()
            log_callback(f"\n📊 PERÍODO:")
            log_callback(f"  • Padronizados: {periodos_validos:,} ({(periodos_validos/total*100):.1f}%)")
            log_callback(f"  • Valores únicos: {valores_unicos}")

        log_callback("\n" + "=" * 80)
        log_callback("EXPORTANDO PLANILHA PROCESSADA")
        log_callback("=" * 80)

        nome_base = arquivo_selecionado.stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_saida = f"{nome_base}_processada_{timestamp}.xlsx"
        arquivo_saida = pasta_processed / nome_saida

        colunas_ordenadas = [
            'Equipe', 'Data', 'Logradouro', 'Período', 'Qtd. pessoas',
            'tipo_logradouro', 'nome_logradouro', 'numero_logradouro', 'complemento_logradouro'
        ]
        colunas_finais = [col for col in colunas_ordenadas if col in df.columns]
        for col in df.columns:
            if col not in colunas_finais:
                colunas_finais.append(col)
        df_exportar = df[colunas_finais]

        df_exportar.to_excel(arquivo_saida, index=False, engine='openpyxl')
        log_callback(f"\n💾 Salvando arquivo processado...")
        log_callback(f"✓ Arquivo exportado com sucesso!")
        log_callback(f"  📁 Local: {arquivo_saida}")
        log_callback(f"  📊 Registros: {len(df_exportar):,}")

        log_callback("\n" + "=" * 80)
        log_callback("GERANDO RELATÓRIO TXT")
        log_callback("=" * 80)

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
                f.write(f"Com tipo: {com_tipo:,} ({(com_tipo/total*100):.1f}%)\n")
                f.write(f"Com nome: {com_nome:,} ({(com_nome/total*100):.1f}%)\n")
                f.write(f"Com número: {com_numero:,} ({(com_numero/total*100):.1f}%)\n")
                f.write(f"Com complemento: {com_complemento:,} ({(com_complemento/total*100):.1f}%)\n\n")
                f.write("Top 10 tipos:\n")
                for i, (tipo, qtd) in enumerate(tipos_contagem.head(10).items(), 1):
                    pct = (qtd / total * 100)
                    f.write(f"  {i:2d}. {tipo:<15} {qtd:>8,} ({pct:>5.1f}%)\n")
                f.write("\n")

            if tem_periodo:
                f.write("-" * 80 + "\n")
                f.write("PERÍODO\n")
                f.write(f"Padronizados: {periodos_validos:,} ({(periodos_validos/total*100):.1f}%)\n")
                f.write(f"Valores únicos: {valores_unicos}\n\n")
                f.write("Distribuição:\n")
                for periodo, qtd in periodos_contagem.items():
                    pct = (qtd / total * 100)
                    f.write(f"  • {periodo:<20} {qtd:>8,} ({pct:>5.1f}%)\n")
                f.write("\n")

        log_callback(f"✓ Relatório TXT exportado: {arquivo_relatorio}")
        log_callback("\n" + "=" * 80)
        log_callback("✓ PARSER COMPLETO EXECUTADO COM SUCESSO!")
        log_callback("=" * 80)

        return str(arquivo_saida), str(arquivo_relatorio)

    except Exception as e:
        log_callback(f"\n❌ ERRO GERAL NO PARSER ❌")
        log_callback(traceback.format_exc())
        return None, None
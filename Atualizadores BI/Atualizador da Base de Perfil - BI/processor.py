"""
processor.py — Motor de processamento da Base Unificada (Versão Corrigida 2026)
=============================================================================
Suporta:
  1. Relatório de Abordagem (Registro Diário) → Novo formato com 39 colunas
  2. Base Unificada BI (Destino) → 66 colunas padrão PowerBI
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from collections import Counter
import logging
import os

def configurar_log(caminho_saida):
    # O log terá o mesmo nome do seu arquivo de saída, mas com extensão .log
    log_path = caminho_saida.replace('.xlsx', '.log')
    
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S',
        encoding='utf-8'
    )
    # Adiciona um handler para também mostrar o log no terminal enquanto roda
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)
    
    logging.info("=== INICIANDO PROCESSAMENTO DA BASE UNIFICADA ===")

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTES E MAPEAMENTOS
# ──────────────────────────────────────────────────────────────────────────────

DATAS_PLACEHOLDER = {'01/01/1970', '1/1/1970'}

VALORES_VAZIOS = {
    '', 'nan', 'none', 'sem informação', 'sem informações', 'sem informacoes',
    'não informado', 'nao informado', 's.inf', 'sinf', 'não inf', 'nao inf',
    'sem info', 'null', 'sem informação ', 'não informado ', 'nao informando',
    'sem informações ', 'não infromado', 'não informao', 'não infoemado',
    'não inf.', 'sen informações', 'sem informacões', 'sem informa',
    'não i', 'n~so', 'n', 'sem informação', 'sem informação', '-'
}

RENOMEAR_FONTES = {
    'DATA':                                             'Data de Inclusão',
    'Equipe':                                           'Equipe/Líder',
    'Pessoa Idosa':                                     'Idoso',
    'Serviços que compartilham o cuidado':              'Quais serviços compartilham o cuidado?',
    'Quanto tempo faz uso de drogas em situação de rua?':
        'Quanto tempo na cena aberta de uso? E onde frequentava antes de chegar nesta cena?',
    # Trailing-space variants — seguras após .str.strip() nas colunas
    'Encaminhamento ':                                  'Encaminhamento',
    'Motivo da recusa ':                                'Motivo da recusa',
    # NOVO: Território vai direto para Unnamed: 0, sem tratamento
    'Território':                                       'Unnamed: 0',
}

CAMPOS_ENRIQUECIMENTO = [
    'Gênero', 'Sexo de Nascimento', 'Data de Nascimento', 'Nome da Mãe',
    'CNS', 'Nome Social', 'Pop Rua', 'Usuário', 'Criança/Adolescente',
    'Gestante', 'Idoso', 'IST', 'TB', 'PcD',
    'Faz uso de quais substâncias?',
    'Origem (País - Estado - Município - Região)',
    'O usuário é acompanhado desde quando?',
    'Unnamed: 0',
    'Qual local foi realizada a abordagem?',
    'Quanto tempo na cena aberta de uso? E onde frequentava antes de chegar nesta cena?',
    'Motivo referido pelo qual frequenta a cena aberta de uso?',
    'Está portando carroças, carrinho e etc.?',
    'Tem animais de estimação?',
    'Teve internações anteriores? (Sim/Não)',
    'Local de internação',
    'Quais serviços compartilham o cuidado?',
    'Encaminhamento',
    'Estratégia de Abordagem',
]

CAMPOS_DATA = {'Data de Nascimento', 'O usuário é acompanhado desde quando?'}

TERRITORIO_CANONICO = {
    r'parque\s+dom\s+pedro|pq\.?\s*dom\s*pedro|parque\s+d\.?\s*pedro': 'Parque Dom Pedro',
    r'glicério|glicerio':                                                'Glicério',
    r'okuhara|okurara|okuhura':                                          'Complexo Okuhara Koei',
    r'outr[ao]s?':                                                       'Outras',
}

CORRECOES_TERRITORIO = {
    'Praça Dom Pedro':      'Parque Dom Pedro',
    'Parque Dom Pedr':      'Parque Dom Pedro',
    'Parque Dom Pedro II':  'Parque Dom Pedro',
    'Praça Da Sé':          'Glicério',
    'Outro':                'Outras',
}

MAPA_NUMEROS = {
    'um': '1', 'uma': '1', 'dois': '2', 'duas': '2', 'três': '3', 'tres': '3',
    'quatro': '4', 'cinco': '5', 'seis': '6', 'sete': '7', 'oito': '8',
    'nove': '9', 'dez': '10', 'onze': '11', 'doze': '12'
}

# Ordem canônica de colunas da BASEBI (66 colunas para compatibilidade PowerBI)
COLUNAS_BASEBI = [
    'Data de Inclusão', 'Equipe/Líder', 'ID', 'Nome Completo',
    'Quantas vezes foi abordado no dia?', 'Encaminhamento',
    'Estratégia de Abordagem', 'Outras Informações Relevantes',
    'Quantas ofertas de acolhimento foram realizadas no dia?',
    'Aceite para a oferta de acolhimento? (Sim/Não)', 'Motivo da recusa',
    'Aceite para internação? (Sim/Não)', 'Motivo da recusa para internação',
    'Nome Social', 'CNS', 'Gênero', 'Sexo de Nascimento', 'Data de Nascimento',
    'Nome da Mãe', 'Pop Rua', 'Usuário', 'Criança/Adolescente', 'Gestante',
    'Idoso', 'IST', 'TB', 'PcD', 'Faz uso de quais substâncias?',
    'Qual local foi realizada a abordagem?',
    'Origem (País - Estado - Município - Região)',
    'Quanto tempo na cena aberta de uso? E onde frequentava antes de chegar nesta cena?',
    'Motivo referido pelo qual frequenta a cena aberta de uso?',
    'Está portando carroças, carrinho e etc.?', 'Tem animais de estimação?',
    'Teve internações anteriores? (Sim/Não)', 'Local de internação',
    'Quais serviços compartilham o cuidado?', 'O usuário é acompanhado desde quando?',
    'Tempo na Cena', 'Onde Frequentava', 'Anos de cena', 'Meses de cena',
    'Usa_Alcool', 'Usa_Crack', 'Usa_Maconha', 'Usa_Cocaina', 'Usa_Tabaco',
    'Num_Substancias', 'Pontuacao MV', 'MV',
    'Encaminhado_CAPS', 'Encaminhado_SIAT', 'Encaminhado_Acolhimento',
    'Encaminhado_Saude_Basica', 'Encaminhado_Hospital_PS', 'Encaminhado_SAE',
    'Tratamento_TB', 'Tratamento_HIV_IST', 'Acao_Medicacao_Curativo',
    'Acao_Exames', 'Acao_Documentacao', 'Acao_Contato_Familiar',
    'Status_Privado_Liberdade', 'Status_Nao_Localizado', 'Status_Recusa_Abandono',
    'Unnamed: 0',
]

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS DE VALIDAÇÃO
# ──────────────────────────────────────────────────────────────────────────────

def e_vazio(v, campo=''):
    if v is None or (isinstance(v, float) and np.isnan(v)): return True
    s = str(v).strip()
    if s.lower() in VALORES_VAZIOS: return True
    if campo in CAMPOS_DATA and s in DATAS_PLACEHOLDER: return True
    return False

def e_sim(v):
    return str(v).strip().lower() in {'sim', 's', 'sim ', 'slm', 'sin', 'aim', '`sim', 'acolhida'}

def e_nao(v):
    t = str(v).strip().lower()
    return bool(re.fullmatch(r'n[ãa]o\.?|n[ãa]o\s*|nao\.?|nao\s*|nâo|nÃo|não|naõ|naão|ñao|náo|n\b|nã', t))

def normalizar_str(v):
    if not isinstance(v, str): return ''
    return re.sub(r'\s+', ' ', v.strip().lower())

# ──────────────────────────────────────────────────────────────────────────────
# PADRONIZAÇÃO DE PERFIL (SEXO, GÊNERO, CLÍNICO)
# ──────────────────────────────────────────────────────────────────────────────

def padronizar_sexo(v):
    t = normalizar_str(v)
    if re.search(r'^masculin|^mascul|^marcul|^maculi|^masscul|^masucu', t): return 'MASCULINO'
    if re.search(r'^feminin|^femina|^femin|^fenimin|^femenin', t): return 'FEMININO'
    if t in {'mulher trans', '~mulher trans'}: return 'MASCULINO'
    return 'NÃO INFORMADO'

def classificar_genero_sexo(genero_raw, sexo_raw):
    g = normalizar_str(genero_raw)
    s = normalizar_str(sexo_raw)
    is_trans = bool(re.search(r'\btrans\b|travesti|transexual|transgênero|transgenero', g)) or s in {'mulher trans', '~mulher trans'}

    if is_trans:
        genero_pad = 'TRANS'
        if re.search(r'mulher|feminino|f\b', g) or s in {'mulher trans', '~mulher trans'}:
            sexo_pad = 'MASCULINO'
        elif re.search(r'homem|masculino|m\b', g):
            sexo_pad = 'FEMININO'
        else:
            sexo_pad = padronizar_sexo(sexo_raw)
        return genero_pad, sexo_pad

    is_cis = bool(re.search(r'\bcis\b|cisgen|cisgên|cisger|cisgeb|cigener', g)) or g in {'masculino', 'feminino', 'cis'}
    if is_cis:
        genero_pad = 'CIS'
        sexo_pad = padronizar_sexo(sexo_raw)
        if sexo_pad == 'NÃO INFORMADO':
            if re.search(r'feminino|mulher', g): sexo_pad = 'FEMININO'
            elif re.search(r'masculino|homem', g): sexo_pad = 'MASCULINO'
        return genero_pad, sexo_pad

    return 'NÃO INFORMADO', padronizar_sexo(sexo_raw)

def padronizar_ist_tb_pcd(v, campo=''):
    if e_vazio(v): return 'NÃO INFORMADO'
    raw = str(v).strip()
    t = raw.lower()
    if e_sim(raw): return 'SIM'
    if e_nao(raw): return 'NÃO'
    if campo == 'PcD' and re.search(r'cadeirante|locomoção|deficiên|amput|cego|surdo', raw, re.I): return 'SIM'
    return 'NÃO INFORMADO'

def padronizar_sim_nao(v):
    if e_vazio(v): return 'NÃO INFORMADO'
    if e_sim(v): return 'SIM'
    if e_nao(v): return 'NÃO'
    return 'NÃO INFORMADO'

# ──────────────────────────────────────────────────────────────────────────────
# PADRONIZAÇÃO BIOGRÁFICA
# ──────────────────────────────────────────────────────────────────────────────

def padronizar_idoso(row, hoje):
    dob = row.get('Data de Nascimento')
    if pd.notnull(dob) and not e_vazio(dob, 'Data de Nascimento'):
        try:
            dob_ts = pd.to_datetime(str(dob), errors='coerce', dayfirst=True)
            if pd.notnull(dob_ts) and 1900 < dob_ts.year <= hoje.year:
                return 'SIM' if (hoje - dob_ts).days / 365 >= 60 else 'NÃO'
        except: pass
    atual = str(row.get('Idoso', '')).strip().upper()
    return 'SIM' if atual == 'SIM' else 'NÃO'

def padronizar_crianca(row, hoje):
    dob = row.get('Data de Nascimento')
    if pd.notnull(dob) and not e_vazio(dob, 'Data de Nascimento'):
        try:
            dob_ts = pd.to_datetime(str(dob), errors='coerce', dayfirst=True)
            if pd.notnull(dob_ts) and 1900 < dob_ts.year <= hoje.year:
                return 'SIM' if (hoje - dob_ts).days / 365 < 18 else 'NÃO'
        except: pass
    atual = str(row.get('Criança/Adolescente', '')).strip().upper()
    return 'SIM' if atual == 'SIM' else 'NÃO'

def padronizar_gestante(row):
    if str(row.get('Sexo de Nascimento', '')).strip() == 'MASCULINO': return 'NÃO'
    return padronizar_sim_nao(row.get('Gestante'))

def normalizar_territorio(v):
    """Retorna o valor original, já que a planilha agora é padronizada na fonte."""
    if pd.isna(v) or str(v).strip() == '': 
        return 'NÃO INFORMADO'
    return str(v).strip() # Retorna o nome exatamente como foi escrito

# ──────────────────────────────────────────────────────────────────────────────
# TEMPO NA CENA E SUBSTÂNCIAS
# ──────────────────────────────────────────────────────────────────────────────

def separar_tempo_local(texto):
    if not isinstance(texto, str) or not texto.strip():
        return pd.Series({'Tempo na Cena': 'Não informado', 'Onde Frequentava': 'Não informado'})
    t_lower = texto.lower()

    if re.search(r'6\s+anos?\s+ou\s+mais', t_lower):
        return pd.Series({'Tempo na Cena': '6 anos', 'Onde Frequentava': 'Não informado'})

    for word, digit in MAPA_NUMEROS.items():
        t_lower = re.sub(rf'\b{word}\b', digit, t_lower)

    padrao = r'(\d+)\s*(ano|anos|mês|mes|meses|semana|semanas|dia|dias)\b'
    matches = re.findall(padrao, t_lower)
    tempo, onde = 'Não identificado', texto
    if matches:
        val, unit = matches[-1]
        unit_map = {'mes': 'meses', 'ano': 'anos', 'dia': 'dias', 'semana': 'semanas'}
        unit = unit_map.get(unit, unit + 's' if not unit.endswith('s') else unit)
        if val == '1' and unit.endswith('s'): unit = unit[:-1]
        tempo = f'{val} {unit}'
        onde = re.sub(r'(?i)(?:h[aá]|aproximadamente|uns|mais de|cerca de)\s+\b\d+\s*(?:ano|mes|dia|semana)s?\b', '', texto)

    onde = re.sub(r'(?i)(?:tem permanecido|na cena de uso|em situação de rua)', '', onde)
    onde = re.sub(r'^\W+|\W+$', '', onde).strip()
    return pd.Series({'Tempo na Cena': tempo, 'Onde Frequentava': onde or 'Não informado'})

def extrair_anos_meses(texto):
    texto = str(texto).lower().strip()
    if '6 anos' in texto: return pd.Series({'Anos de cena': 6, 'Meses de cena': 0})
    anos = meses = pd.NA
    m = re.search(r'(\d+)', texto)
    if m:
        v = int(m.group(1))
        if 'ano' in texto: anos, meses = v, 0
        elif any(t in texto for t in ['mês', 'mes', 'mê']): anos, meses = 0, v
        elif 'dia' in texto or 'semana' in texto: anos, meses = 0, 0
    return pd.Series({'Anos de cena': anos, 'Meses de cena': meses})

def processar_substancias(v):
    texto = str(v).lower()
    alc = bool(re.search(r'álcool|alcool|cachaça|pinga|cerveja|vinho', texto))
    cra = bool(re.search(r'crack|cracl|pedra|zika', texto))
    mac = bool(re.search(r'maconha|baseado|mato|erva|skunk', texto))
    coc = bool(re.search(r'cocaína|cocaina|pó\b|faria|pino', texto))
    tab = bool(re.search(r'tabaco|cigarro|fumo', texto))
    if re.search(r'\bspa\b', texto): cra = coc = True
    if re.search(r'múltiplas?\s+substâncias?', texto): alc = cra = coc = True
    return pd.Series({
        'Usa_Alcool': 'SIM' if alc else 'NÃO',
        'Usa_Crack': 'SIM' if cra else 'NÃO',
        'Usa_Maconha': 'SIM' if mac else 'NÃO',
        'Usa_Cocaina': 'SIM' if coc else 'NÃO',
        'Usa_Tabaco': 'SIM' if tab else 'NÃO',
        'Num_Substancias': sum([alc, cra, mac, coc, tab])
    })

def mapear_encaminhamentos(texto):
    cats = {k: 'NÃO' for k in [
        'Encaminhado_CAPS', 'Encaminhado_SIAT', 'Encaminhado_Acolhimento',
        'Encaminhado_Saude_Basica', 'Encaminhado_Hospital_PS', 'Encaminhado_SAE',
        'Tratamento_TB', 'Tratamento_HIV_IST', 'Acao_Medicacao_Curativo',
        'Acao_Exames', 'Acao_Documentacao', 'Acao_Contato_Familiar',
        'Status_Privado_Liberdade', 'Status_Nao_Localizado', 'Status_Recusa_Abandono'
    ]}
    if pd.isna(texto) or not str(texto).strip(): return pd.Series(cats)
    t = str(texto).lower()
    if re.search(r'\bcaps\b|\bprosam\b|\brue\b', t): cats['Encaminhado_CAPS'] = 'SIM'
    if re.search(r'\bsiat\b', t): cats['Encaminhado_SIAT'] = 'SIM'
    if re.search(r'hotel\s+social|\babrigo\b|\balbergue\b|\bcta\b|\bcaei\b|pernoite|\b156\b', t): cats['Encaminhado_Acolhimento'] = 'SIM'
    if re.search(r'\bubs\b|\bama\b|\bupa\b|\bcer\b|consulta\s+m[eé]dic', t): cats['Encaminhado_Saude_Basica'] = 'SIM'
    if re.search(r'\bhc\b|\bhospital\b|pronto[\s-]?socorro|santa\s+casa|\bps\b', t): cats['Encaminhado_Hospital_PS'] = 'SIM'
    if re.search(r'\bsae\b', t): cats['Encaminhado_SAE'] = 'SIM'
    if re.search(r'\btdo\b|\btuberculose\b', t): cats['Tratamento_TB'] = 'SIM'
    if re.search(r'\btarv\b|\bhiv\b|\bist\b', t): cats['Tratamento_HIV_IST'] = 'SIM'
    if re.search(r'medica[çc][aã]o|rem[eé]dio|curativo|les[aã]o', t): cats['Acao_Medicacao_Curativo'] = 'SIM'
    if re.search(r'exame', t): cats['Acao_Exames'] = 'SIM'
    if re.search(r'documento|\brg\b|poupatempo', t): cats['Acao_Documentacao'] = 'SIM'
    if re.search(r'fam[ií]lia|m[aã]e\b', t): cats['Acao_Contato_Familiar'] = 'SIM'
    if re.search(r'privad[ao]\s+de\s+liberdade|reclus[ao]|pres[ao]', t): cats['Status_Privado_Liberdade'] = 'SIM'
    if re.search(r'n[aã]o\s+localizado|fora\s+do\s+territ[oó]rio|desaparecid', t): cats['Status_Nao_Localizado'] = 'SIM'
    if re.search(r'recus[ao]|negou|abandono', t): cats['Status_Recusa_Abandono'] = 'SIM'
    return pd.Series(cats)

# ──────────────────────────────────────────────────────────────────────────────
# ENRIQUECIMENTO INTRA-DIA
# ──────────────────────────────────────────────────────────────────────────────

def enriquecer_intra_dia(df, callback=None):
    campos = [c for c in CAMPOS_ENRIQUECIMENTO if c in df.columns]
    grupos = {}
    for idx, row in df.iterrows():
        id_ = row.get('ID')
        data = row.get('Data de Inclusão')
        if pd.isna(id_) or pd.isna(data): continue
        chave = (str(id_).strip(), str(data).strip())
        grupos.setdefault(chave, []).append(idx)

    preenchidos = 0
    total = len(df)
    for i, idx in enumerate(df.index):
        if callback and i % 500 == 0:
            callback(int(i / total * 100), f'Enriquecendo {i}/{total}...')
        id_ = df.at[idx, 'ID']
        data = df.at[idx, 'Data de Inclusão']
        chave = (str(id_).strip(), str(data).strip()) if pd.notna(id_) and pd.notna(data) else None
        idxs_grupo = grupos.get(chave, [idx]) if chave else [idx]
        for campo in campos:
            if not e_vazio(df.at[idx, campo], campo): continue
            vals = [df.at[j, campo] for j in idxs_grupo if j != idx and not e_vazio(df.at[j, campo], campo)]
            if vals:
                df.at[idx, campo] = Counter([str(v).strip() for v in vals]).most_common(1)[0][0]
                preenchidos += 1
            else:
                df.at[idx, campo] = 'NÃO INFORMADO'
    return df, preenchidos

# ──────────────────────────────────────────────────────────────────────────────
# CÁLCULO DE MV
# ──────────────────────────────────────────────────────────────────────────────

def calcular_mv(df, callback=None):
    hoje = pd.Timestamp.now()
    ids_validos = df.dropna(subset=['ID'])['ID'].unique()
    total = len(ids_validos)
    mv_map = {}
    for i, id_ in enumerate(ids_validos):
        if callback and i % 100 == 0:
            callback(int(i / total * 100), f'Calculando MV {i}/{total}...')
        rows = df[df['ID'] == id_]
        pts = 0

        dob = None
        for v in rows['Data de Nascimento'].dropna():
            if not e_vazio(v, 'Data de Nascimento'):
                dob = pd.to_datetime(v, errors='coerce', dayfirst=True)
                if pd.notna(dob): break

        if dob and pd.notna(dob):
            idade = (hoje - dob).days / 365
            if idade < 18 or idade >= 60: pts += 5
        elif 'Idoso' in rows.columns and (rows['Idoso'] == 'SIM').any():
            pts += 5
        elif 'Criança/Adolescente' in rows.columns and (rows['Criança/Adolescente'] == 'SIM').any():
            pts += 5

        for c in ['Gestante', 'PcD', 'IST', 'TB']:
            if c in rows.columns and (rows[c] == 'SIM').any(): pts += 5

        if 'Sexo de Nascimento' in rows.columns and (rows['Sexo de Nascimento'] == 'FEMININO').any(): pts += 1
        if 'Gênero' in rows.columns and (rows['Gênero'] == 'TRANS').any(): pts += 1

        anos_max = 0
        if 'Tempo na Cena' in rows.columns:
            for t in rows['Tempo na Cena'].dropna():
                nums = re.findall(r'\d+', str(t))
                if nums and 'ano' in str(t).lower():
                    anos_max = max(anos_max, int(nums[0]))
        if anos_max >= 6: pts += 5
        elif anos_max >= 2: pts += 3

        mv_map[id_] = (pts, 'SIM' if pts > 0 else 'NÃO')

    df['Pontuacao MV'] = df['ID'].map(lambda x: mv_map.get(x, (0, 'NÃO'))[0] if pd.notna(x) else 0)
    df['MV'] = df['ID'].map(lambda x: mv_map.get(x, (0, 'NÃO'))[1] if pd.notna(x) else 'NÃO')
    return df

# ──────────────────────────────────────────────────────────────────────────────
# LEITURA DO RELATÓRIO DIÁRIO
# ──────────────────────────────────────────────────────────────────────────────

def _carregar_semanal(path):

    if str(path).lower().endswith('.csv'):
        return pd.read_csv(path, encoding='utf-8-sig')
    try:
        return pd.read_excel(path, sheet_name='Registro Semanal')
    except Exception:
        return pd.read_excel(path)

# ──────────────────────────────────────────────────────────────────────────────
# PROCESSAMENTO DO RELATÓRIO (padronização de uma nova entrada)
# ──────────────────────────────────────────────────────────────────────────────

def processar_diario(df):
    hoje = pd.Timestamp.now()

    res_gs = df.apply(
        lambda r: pd.Series(
            classificar_genero_sexo(r.get('Gênero'), r.get('Sexo de Nascimento')),
            index=['Gênero', 'Sexo de Nascimento']
        ), axis=1
    )
    df['Gênero'] = res_gs['Gênero']
    df['Sexo de Nascimento'] = res_gs['Sexo de Nascimento']

    for c in ['IST', 'TB', 'PcD']:
        df[c] = df[c].apply(lambda v, campo=c: padronizar_ist_tb_pcd(v, campo)) if c in df.columns else 'NÃO INFORMADO'

    for c in ['Pop Rua', 'Usuário', 'Gestante']:
        if c not in df.columns:
            df[c] = 'NÃO INFORMADO'

    for c in ['Pop Rua', 'Usuário']:
        df[c] = df[c].apply(padronizar_sim_nao)

    df['Idoso'] = df.apply(padronizar_idoso, axis=1, args=(hoje,))
    df['Criança/Adolescente'] = df.apply(padronizar_crianca, axis=1, args=(hoje,))
    df['Gestante'] = df.apply(padronizar_gestante, axis=1)

    col_tempo = 'Quanto tempo na cena aberta de uso? E onde frequentava antes de chegar nesta cena?'
    if col_tempo in df.columns:
        res_t = df[col_tempo].apply(separar_tempo_local)
        df['Tempo na Cena'] = res_t['Tempo na Cena']
        df['Onde Frequentava'] = res_t['Onde Frequentava']
        res_am = df['Tempo na Cena'].apply(extrair_anos_meses)
        df['Anos de cena'] = res_am['Anos de cena']
        df['Meses de cena'] = res_am['Meses de cena']

    if 'Faz uso de quais substâncias?' in df.columns:
        df = pd.concat([df, df['Faz uso de quais substâncias?'].apply(processar_substancias)], axis=1)

    if 'Encaminhamento' in df.columns:
        df = pd.concat([df, df['Encaminhamento'].apply(mapear_encaminhamentos)], axis=1)

    return df

# ──────────────────────────────────────────────────────────────────────────────
# RELATÓRIO DE NOVOS REGISTROS COM CONFIABILIDADE
# ──────────────────────────────────────────────────────────────────────────────

def _normalizar_campo(v):
    if pd.isna(v) or e_vazio(v): return ''
    return str(v).strip().lower()

def calcular_confiabilidade(row_novo, df_base):
    """
    Calcula a confiabilidade de que uma nova entrada é REALMENTE nova
    (não apenas com ID diferente de alguém já cadastrado).

    Compara Nome Completo, CNS e Nome da Mãe contra TODA a base.
    - 0 campos coincidentes em qualquer registro da base → ALTA (claramente novo)
    - 1 campo coincidente em algum registro              → MÉDIA
    - 2+ campos coincidentes em algum registro           → BAIXA (possível duplicata)
    """
    campos_check = {
        'Nome Completo': _normalizar_campo(row_novo.get('Nome Completo')),
        'CNS':           _normalizar_campo(row_novo.get('CNS')),
        'Nome da Mãe':   _normalizar_campo(row_novo.get('Nome da Mãe')),
    }

    max_coincidencias = 0
    for _, row_base in df_base.iterrows():
        coincidencias = 0
        for campo, val_novo in campos_check.items():
            if not val_novo: continue
            val_base = _normalizar_campo(row_base.get(campo))
            if val_base and val_novo == val_base:
                coincidencias += 1
        if coincidencias > max_coincidencias:
            max_coincidencias = coincidencias
        if max_coincidencias >= 2:
            break

    if max_coincidencias == 0: return 'ALTA'
    if max_coincidencias == 1: return 'MÉDIA'
    return 'BAIXA'

# ──────────────────────────────────────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────

def atualizar_base(path_base, path_diario, path_saida, callback=None):
    """
    Pipeline completo:
      1. Lê BASEBI e Registro Diário (aba correta)
      2. Renomeia colunas (Território → Unnamed: 0, sem normalização)
      3. Identifica novos IDs e calcula confiabilidade
      4. Padroniza o relatório novo (gênero, clínico, substâncias, encaminhamentos)
      5. Alinha colunas com a BASEBI
      6. Concatena e remove duplicatas exatas
      7. Enriquece intra-dia
      8. Recalcula MV para todos os IDs
      9. Salva BASEBI atualizada + relatório de novos
    """

    configurar_log(path_saida)
    try:
        # ── 1. Leitura ────────────────────────────────────────────────────────
        logging.info(f"Arquivos de entrada: Base[{os.path.basename(path_base)}] | Diário[{os.path.basename(path_diario)}]")
        if callback: callback(5, 'Lendo arquivos...')

        logging.info(f"Lendo base: {path_base}")
        df_base = pd.read_excel(path_base)

        df_base.columns = df_base.columns.str.strip()

        logging.info(f"Lendo relatório diário: {path_diario}")        
        df_novo = _carregar_semanal(path_diario)
        df_novo.columns = df_novo.columns.str.strip()

        # ── 2. Renomear colunas do relatório novo ─────────────────────────────
        if callback: callback(15, 'Mapeando colunas...')
        df_novo = df_novo.rename(columns=RENOMEAR_FONTES)
        # Neste ponto, 'Território' já se chama 'Unnamed: 0' (bruto, sem normalizar)

        # ── 3. Identificar novos IDs e guardar dados para o relatório ─────────
        if callback: callback(25, 'Identificando novos registros...')
        ids_na_base = set(df_base['ID'].dropna().astype(str).unique())
        mask_novos = ~df_novo['ID'].astype(str).isin(ids_na_base)
        df_candidatos = df_novo[mask_novos].drop_duplicates(subset=['ID'])

        # Guarda apenas nome, id, data e confiabilidade — MV será adicionado
        # depois da etapa 8, quando o cálculo já tiver sido feito no df_final
        confiabilidades = {}
        for _, row in df_candidatos.iterrows():
            id_str = str(row.get('ID', ''))
            confiabilidades[id_str] = {
                'NOME':             row.get('Nome Completo', ''),
                'ID':               row.get('ID', ''),
                'DATA_DE_INCLUSAO': row.get('Data de Inclusão', ''),
                'CONFIABILIDADE':   calcular_confiabilidade(row, df_base),
            }

        # ── 4. Padronizar o relatório novo ────────────────────────────────────
        if callback: callback(40, 'Padronizando dados do relatório...')
        df_novo = processar_diario(df_novo)

        # ── 5. Alinhar colunas ao esquema da BASEBI ───────────────────────────
        if callback: callback(55, 'Alinhando colunas...')
        # Garante que df_novo tenha todas as colunas da BASEBI (NaN para ausentes)
        for col in COLUNAS_BASEBI:
            if col not in df_novo.columns:
                df_novo[col] = np.nan
        # Mantém apenas as colunas reconhecidas + extras da BASEBI (não perde colunas extras)
        colunas_extras_base = [c for c in df_base.columns if c not in COLUNAS_BASEBI]
        ordem_final = COLUNAS_BASEBI + colunas_extras_base
        df_novo = df_novo.reindex(columns=ordem_final)

        # ── 6. Concatenar e remover duplicatas ────────────────────────────────
        if callback: callback(65, 'Concatenando e removendo duplicatas...')
        df_final = pd.concat([df_base, df_novo], ignore_index=True)
        # Remove duplicatas exatas (todas as colunas iguais)
        df_final = df_final.drop_duplicates()
        # Remove duplicatas por ID + Data de Inclusão (mantém a linha mais completa)
        df_final = df_final.sort_values(
            by=['ID', 'Data de Inclusão'],
            na_position='last'
        ).reset_index(drop=True)

        # ── 7. Enriquecimento intra-dia ───────────────────────────────────────
        if callback: callback(75, 'Enriquecendo campos vazios...')
        df_final, n_preenchidos = enriquecer_intra_dia(
            df_final,
            callback=lambda p, m: callback(75 + int(p * 0.1), m) if callback else None
        )

        # ── 8. Recalcular MV ──────────────────────────────────────────────────
        if callback: callback(87, 'Recalculando MV...')
        df_final = calcular_mv(
            df_final,
            callback=lambda p, m: callback(87 + int(p * 0.08), m) if callback else None
        )

        # ── 9. Salvar arquivos ────────────────────────────────────────────────
        if callback: callback(96, 'Salvando arquivos...')

        # Monta o relatório de novos agora que o MV já foi calculado
        mv_por_id = (
            df_final.drop_duplicates(subset=['ID'])
            .set_index(df_final.drop_duplicates(subset=['ID'])['ID'].astype(str))['MV']
            .to_dict()
        )
        registros_novos = []
        for id_str, dados in confiabilidades.items():
            registros_novos.append({
                **dados,
                'MV': mv_por_id.get(id_str, ''),
            })
        df_relatorio_novos = pd.DataFrame(registros_novos)

        # Garante ordem canônica das colunas na saída
        cols_saida = [c for c in COLUNAS_BASEBI if c in df_final.columns]
        cols_extras = [c for c in df_final.columns if c not in COLUNAS_BASEBI]
        df_final[cols_saida + cols_extras].to_excel(path_saida, index=False)

        path_novos = path_saida.replace('.xlsx', '_NOVOS_REGISTROS.xlsx')
        df_relatorio_novos.to_excel(path_novos, index=False)

        n_novos = len(df_relatorio_novos)
        n_alta  = (df_relatorio_novos['CONFIABILIDADE'] == 'ALTA').sum()
        n_media = (df_relatorio_novos['CONFIABILIDADE'] == 'MÉDIA').sum()
        n_baixa = (df_relatorio_novos['CONFIABILIDADE'] == 'BAIXA').sum()

        resumo = (
            f"✅ Atualização concluída!\n\n"
            f"• Registros processados: {len(df_novo)}\n"
            f"• Campos enriquecidos intra-dia: {n_preenchidos}\n"
            f"• Novos IDs identificados: {n_novos}\n"
            f"  ↳ Confiabilidade ALTA:  {n_alta}\n"
            f"  ↳ Confiabilidade MÉDIA: {n_media}\n"
            f"  ↳ Confiabilidade BAIXA: {n_baixa} (verificar possíveis duplicatas)\n"
            f"• Relatório de novos salvo em: {path_novos.split('/')[-1]}"
        )
        logging.info(f"Processamento concluído. {len(df_novo)} registros processados.")
        return True, resumo

    except Exception as e:
        import traceback
        logging.error("Erro crítico no processamento:", exc_info=True)
        return False, f"Erro crítico: {str(e)}\n\n{traceback.format_exc()}"
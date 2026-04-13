"""
atualizar_base_relatorio.py
===========================
Atualiza a Base Unificada BI incorporando os dados do relatório de abordagem.

Diferenças tratadas automaticamente em relação ao fluxo antigo:
  - Coluna 'Pessoa Idosa'  →  'Idoso'
  - Coluna 'Equipe'        →  'Equipe/Líder'
  - Coluna 'Serviços que compartilham o cuidado'  →  'Quais serviços compartilham o cuidado?'
  - Coluna 'Quanto tempo faz uso de drogas em situação de rua?'
           →  'Quanto tempo na cena aberta de uso? E onde frequentava...'
  - Territórios de bairros adjacentes (Campos Elíseos, Santa Cecília etc.) → 'Outras'
  - '6 anos ou mais' no campo de tempo de uso → '6 anos' para pontuação MV correta

Uso:
    python atualizar_base_relatorio.py
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from collections import Counter

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════

DATAS_PLACEHOLDER = {'01/01/1970', '1/1/1970'}

VALORES_VAZIOS = {
    '', 'nan', 'none', 'sem informação', 'sem informações', 'sem informacoes',
    'não informado', 'nao informado', 's.inf', 'sinf', 'não inf', 'nao inf',
    'sem info', 'null', 'sem informação ', 'não informado ', 'nao informando',
    'sem informações ', 'não infromado', 'não informao', 'não infoemado',
    'não inf.', 'sen informações', 'sem informacões', 'sem informa',
    'não i', 'n~so', 'n', 'sem informação'
}

# Renomeações do relatorio_abordagem → formato BASEBI
RENOMEAR_RELATORIO = {
    'DATA':                                                        'Data de Inclusão',
    'Equipe':                                                      'Equipe/Líder',
    'Pessoa Idosa':                                                'Idoso',
    'Serviços que compartilham o cuidado':                         'Quais serviços compartilham o cuidado?',
    'Quanto tempo faz uso de drogas em situação de rua?':
        'Quanto tempo na cena aberta de uso? E onde frequentava antes de chegar nesta cena?',
}

# Renomeações históricas da BASEBI (mantidas por compatibilidade)
RENOMEAR_BASE = {
    'Serviços que compartilham o cuidado':  'Quais serviços compartilham o cuidado?',
    'Encaminhamento ':                      'Encaminhamento',
    'Motivo da recusa ':                    'Motivo da recusa',
}

TERRITORIO_CANONICO = {
    r'parque\s+dom\s+pedro|pq\.?\s*dom\s*pedro|parque\s+d\.?\s*pedro': 'Parque Dom Pedro',
    r'glicério|glicerio':                                               'Glicério',
    r'okuhara|okurara|okuhura':                                         'Complexo Okuhara Koei',
    r'outr[ao]s?':                                                      'Outras',
}

CORRECOES_TERRITORIO = {
    'Praça Dom Pedro':      'Parque Dom Pedro',
    'Parque Dom Pedr':      'Parque Dom Pedro',
    'Parque Dom Pedro II':  'Parque Dom Pedro',
    'Praça Da Sé':          'Glicério',
    'Outro':                'Outras',
}

# Bairros adjacentes às cenas principais → "Outras"
BAIRROS_OUTRAS = {
    'campos elíseos', 'campos eliseos', 'santa cecília', 'santa cecilia',
    'santa ifigênia', 'santa ifigenia', 'república', 'republica',
    'bom retiro', 'brás', 'bras', 'pari', 'mooca', 'luz',
}

CAMPOS_ENRIQUECIMENTO = [
    'Gênero', 'Sexo de Nascimento', 'Data de Nascimento', 'Nome da Mãe',
    'CNS', 'Nome Social', 'Pop Rua', 'Usuário', 'Criança/Adolescente',
    'Gestante', 'Idoso', 'IST', 'TB', 'PcD',
    'Faz uso de quais substâncias?',
    'Origem (País - Estado - Município - Região)',
    'O usuário é acompanhado desde quando?',
    'Território',
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

MAPA_NUMEROS = {
    'um': '1', 'uma': '1', 'dois': '2', 'duas': '2', 'três': '3', 'tres': '3',
    'quatro': '4', 'cinco': '5', 'seis': '6', 'sete': '7', 'oito': '8',
    'nove': '9', 'dez': '10', 'onze': '11', 'doze': '12'
}

ORDEM_COLUNAS_BASEBI = [
    'Data de Inclusão', 'Equipe/Líder', 'ID', 'Nome Completo',
    'Quantas vezes foi abordado no dia?', 'Encaminhamento',
    'Estratégia de Abordagem', 'Outras Informações Relevantes',
    'Quantas ofertas de acolhimento foram realizadas no dia?',
    'Aceite para a oferta de acolhimento? (Sim/Não)', 'Motivo da recusa',
    'Aceite para internação? (Sim/Não)', 'Motivo da recusa para internação',
    'Nome Social', 'CNS', 'Gênero', 'Sexo de Nascimento', 'Data de Nascimento',
    'Nome da Mãe', 'Pop Rua', 'Usuário', 'Criança/Adolescente', 'Gestante', 'Idoso',
    'IST', 'TB', 'PcD', 'Faz uso de quais substâncias?',
    'Qual local foi realizada a abordagem?',
    'Origem (País - Estado - Município - Região)',
    'Quanto tempo na cena aberta de uso? E onde frequentava antes de chegar nesta cena?',
    'Motivo referido pelo qual frequenta a cena aberta de uso?',
    'Está portando carroças, carrinho e etc.?', 'Tem animais de estimação?',
    'Teve internações anteriores? (Sim/Não)', 'Local de internação',
    'Quais serviços compartilham o cuidado?', 'O usuário é acompanhado desde quando?',
    'Território',
    'Tempo na Cena', 'Onde Frequentava', 'Anos de cena', 'Meses de cena',
    'Usa_Alcool', 'Usa_Crack', 'Usa_Maconha', 'Usa_Cocaina', 'Usa_Tabaco',
    'Num_Substancias', 'Pontuacao MV', 'MV',
    'Encaminhado_CAPS', 'Encaminhado_SIAT', 'Encaminhado_Acolhimento',
    'Encaminhado_Saude_Basica', 'Encaminhado_Hospital_PS', 'Encaminhado_SAE',
    'Tratamento_TB', 'Tratamento_HIV_IST', 'Acao_Medicacao_Curativo',
    'Acao_Exames', 'Acao_Documentacao', 'Acao_Contato_Familiar',
    'Status_Privado_Liberdade', 'Status_Nao_Localizado', 'Status_Recusa_Abandono',
]

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

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
    return bool(re.fullmatch(
        r'n[ãa]o\.?|n[ãa]o\s*|nao\.?|nao\s*|nâo|nÃo|não|naõ|naão|ñao|náo|n\b|nã', t
    ))

def normalizar_str(v):
    if not isinstance(v, str): return ''
    return re.sub(r'\s+', ' ', v.strip().lower())

def _log(step, total, msg):
    barra = '█' * step + '░' * (total - step)
    print(f"  [{barra}] {msg}", flush=True)

# ══════════════════════════════════════════════════════════════════════════════
# PADRONIZAÇÃO — GÊNERO E SEXO
# ══════════════════════════════════════════════════════════════════════════════

def padronizar_sexo(v):
    t = normalizar_str(v)
    if re.search(r'^masculin|^mascul|^marcul|^maculi|^masscul|^masucu', t): return 'MASCULINO'
    if re.search(r'^feminin|^femina|^femin|^fenimin|^femenin', t): return 'FEMININO'
    if t in {'mulher trans', '~mulher trans'}: return 'MASCULINO'
    return 'NÃO INFORMADO'

def classificar_genero_sexo(genero_raw, sexo_raw):
    g = normalizar_str(genero_raw)
    s = normalizar_str(sexo_raw)
    is_trans = bool(re.search(
        r'\btrans\b|travesti|transexual|transgênero|transgenero|trangenero|trasgenero', g
    )) or s in {'mulher trans', '~mulher trans'}

    if is_trans:
        genero_pad = 'TRANS'
        if re.search(r'mulher|feminino|f\b', g) or s in {'mulher trans', '~mulher trans'}:
            sexo_pad = 'MASCULINO'
        elif re.search(r'homem|masculino|m\b', g):
            sexo_pad = 'FEMININO'
        else:
            sexo_pad = padronizar_sexo(sexo_raw)
        return genero_pad, sexo_pad

    is_cis = bool(re.search(
        r'\bcis\b|cisgen|cisgên|cisger|cisgeb|cigener|cosgen|cigenero', g
    )) or g in {'masculino', 'feminino', 'cis'}

    if is_cis:
        genero_pad = 'CIS'
        sexo_pad = padronizar_sexo(sexo_raw)
        if sexo_pad == 'NÃO INFORMADO':
            if re.search(r'feminino|mulher', g): sexo_pad = 'FEMININO'
            elif re.search(r'masculino|homem', g): sexo_pad = 'MASCULINO'
        return genero_pad, sexo_pad

    return 'NÃO INFORMADO', padronizar_sexo(sexo_raw)

# ══════════════════════════════════════════════════════════════════════════════
# PADRONIZAÇÃO — CAMPOS CLÍNICOS
# ══════════════════════════════════════════════════════════════════════════════

PCD_POSITIVO = re.compile(
    r'cadeirante|locomoção|locomocao|fratura|cirurgi|deficiên|deficien|'
    r'amput|cego|cega|surdo|surda|paralisi|paralis', re.IGNORECASE
)

def padronizar_ist_tb_pcd(v, campo=''):
    if pd.isna(v): return 'NÃO INFORMADO'
    raw = str(v).strip()
    t = raw.lower()
    if re.fullmatch(r'sim\.?|sim\s*|s\.?|sim\s+\(.*\)', t): return 'SIM'
    if e_nao(t): return 'NÃO'
    if campo == 'PcD' and PCD_POSITIVO.search(raw): return 'SIM'
    return 'NÃO INFORMADO'

def padronizar_sim_nao(v):
    if pd.isna(v): return 'NÃO INFORMADO'
    if e_sim(v): return 'SIM'
    if e_nao(v): return 'NÃO'
    return 'NÃO INFORMADO'

# ══════════════════════════════════════════════════════════════════════════════
# PADRONIZAÇÃO — CAMPOS BIOGRÁFICOS
# ══════════════════════════════════════════════════════════════════════════════

def padronizar_idoso(row, hoje):
    dob = row.get('Data de Nascimento')
    if pd.notnull(dob):
        try:
            dob_ts = pd.to_datetime(str(dob), errors='coerce', dayfirst=True)
            if pd.notnull(dob_ts) and 1900 < dob_ts.year <= hoje.year:
                return 'SIM' if (hoje - dob_ts).days / 365 >= 60 else 'NÃO'
        except: pass
    atual = str(row.get('Idoso', '')).strip().upper()
    return 'SIM' if atual == 'SIM' else 'NÃO'

def padronizar_crianca(row, hoje):
    dob = row.get('Data de Nascimento')
    if pd.notnull(dob):
        try:
            dob_ts = pd.to_datetime(str(dob), errors='coerce', dayfirst=True)
            if pd.notnull(dob_ts) and 1900 < dob_ts.year <= hoje.year:
                return 'SIM' if (hoje - dob_ts).days / 365 < 18 else 'NÃO'
        except: pass
    atual = str(row.get('Criança/Adolescente', '')).strip().upper()
    return 'SIM' if atual == 'SIM' else 'NÃO'

def padronizar_gestante(row):
    if str(row.get('Sexo de Nascimento', '')).strip() == 'MASCULINO':
        return 'NÃO'
    return padronizar_sim_nao(row.get('Gestante'))

# ══════════════════════════════════════════════════════════════════════════════
# PADRONIZAÇÃO — TERRITÓRIO
# ══════════════════════════════════════════════════════════════════════════════

def normalizar_territorio(v):
    if pd.isna(v): return 'NÃO INFORMADO'
    s = str(v).strip()
    if s in CORRECOES_TERRITORIO:
        return CORRECOES_TERRITORIO[s]
    t = s.lower()
    for padrao, canonico in TERRITORIO_CANONICO.items():
        if re.search(padrao, t):
            return canonico
    if t in BAIRROS_OUTRAS:
        return 'Outras'
    # Qualquer território não reconhecido → Outras
    # (mantém valor original se já for um dos 4 canônicos)
    canonicos = {'Parque Dom Pedro', 'Glicério', 'Complexo Okuhara Koei', 'Outras'}
    return s if s in canonicos else 'Outras'

# ══════════════════════════════════════════════════════════════════════════════
# PADRONIZAÇÃO — TEMPO NA CENA
# ══════════════════════════════════════════════════════════════════════════════

def separar_tempo_local(texto):
    if not isinstance(texto, str) or not texto.strip():
        return pd.Series({'Tempo na Cena': 'Não informado', 'Onde Frequentava': 'Não informado'})
    t_lower = texto.lower()

    # Tratar variante específica do relatorio_abordagem
    if re.search(r'6\s+anos?\s+ou\s+mais', t_lower):
        return pd.Series({'Tempo na Cena': '6 anos', 'Onde Frequentava': 'Não informado'})

    for word, digit in MAPA_NUMEROS.items():
        t_lower = re.sub(rf'\b{word}\b', digit, t_lower)

    padrao = r'(\d+)\s*(ano|anos|mês|mes|meses|semana|semanas|dia|dias)\b'
    matches = re.findall(padrao, t_lower)
    tempo = "Não identificado"
    onde = texto

    if matches:
        val, unit = matches[-1]
        unit_map = {'mes': 'meses', 'ano': 'anos', 'dia': 'dias', 'semana': 'semanas'}
        unit = unit_map.get(unit, unit + 's' if not unit.endswith('s') else unit)
        if val == '1' and unit.endswith('s'): unit = unit[:-1]
        tempo = f"{val} {unit}"
        onde = re.sub(
            r'(?i)(?:h[aá]\s+(?:cerca\s+de\s+|mais\s+de\s+)?|aproximadamente\s+|uns\s+|mais\s+de\s+)?'
            r'\b(?:um|uma|dois|duas|três|tres|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|\d+)'
            r'\s*(?:ano|anos|mês|mes|meses|semana|semanas|dia|dias)\b', '', texto)
    elif re.search(r'sem\s+infor', t_lower):
        tempo = "Sem informação"
    elif re.search(r'não\s+(sabe|lembra)', t_lower):
        tempo = "Não sabe"
    elif re.search(r'desde\s+a\s+infância', t_lower):
        tempo = "Desde a infância"

    onde = re.sub(r'(?i)(?:tem\s+permanecido\s+no\s+territ[oó]rio|na\s+cena\s+de\s+uso|'
                  r'em\s+situaç[aã]o\s+de\s+rua)', '', onde)
    onde = re.sub(r'^\W+|\W+$', '', onde)
    onde = re.sub(r'\s+', ' ', onde).strip()
    return pd.Series({'Tempo na Cena': tempo, 'Onde Frequentava': onde or 'Não informado'})

def extrair_anos_meses(texto):
    texto = str(texto).lower().strip()
    if re.search(r'6\s+anos?\s+ou\s+mais', texto):
        return pd.Series({'Anos de cena': 6, 'Meses de cena': 0})
    anos = meses = pd.NA
    m = re.search(r'(\d+)', texto)
    if m:
        v = int(m.group(1))
        if 'ano' in texto:   anos, meses = v, 0
        elif any(t in texto for t in ['mês', 'mes', 'mê']): anos, meses = 0, v
        elif 'dia' in texto or 'semana' in texto: anos, meses = 0, 0
    return pd.Series({'Anos de cena': anos, 'Meses de cena': meses})

# ══════════════════════════════════════════════════════════════════════════════
# PADRONIZAÇÃO — SUBSTÂNCIAS
# ══════════════════════════════════════════════════════════════════════════════

def processar_substancias(v):
    texto = str(v).lower()
    alc = bool(re.search(r'álcool|alcool|cachaça|pinga|cerveja|vinho|àlcool', texto))
    cra = bool(re.search(r'crack|cracl|pedra|zika', texto))
    mac = bool(re.search(r'maconha|baseado|mato|erva|skunk', texto))
    coc = bool(re.search(r'cocaína|cocaina|pó\b|faria|pino', texto))
    tab = bool(re.search(r'tabaco|cigarro|fumo', texto))
    if re.search(r'\bspa\b', texto): cra = coc = True
    if re.search(r'múltiplas?\s+(?:drogas?|substâncias?)|multiplas?\s+(?:drogas?|substancias?)', texto):
        alc = cra = coc = True
    return pd.Series({
        'Usa_Alcool':     'SIM' if alc else 'NÃO',
        'Usa_Crack':      'SIM' if cra else 'NÃO',
        'Usa_Maconha':    'SIM' if mac else 'NÃO',
        'Usa_Cocaina':    'SIM' if coc else 'NÃO',
        'Usa_Tabaco':     'SIM' if tab else 'NÃO',
        'Num_Substancias': sum([alc, cra, mac, coc, tab]),
    })

# ══════════════════════════════════════════════════════════════════════════════
# MAPEAMENTO DE ENCAMINHAMENTOS
# ══════════════════════════════════════════════════════════════════════════════

def mapear_encaminhamentos(texto):
    cats = {
        'Encaminhado_CAPS': 'NÃO', 'Encaminhado_SIAT': 'NÃO',
        'Encaminhado_Acolhimento': 'NÃO', 'Encaminhado_Saude_Basica': 'NÃO',
        'Encaminhado_Hospital_PS': 'NÃO', 'Encaminhado_SAE': 'NÃO',
        'Tratamento_TB': 'NÃO', 'Tratamento_HIV_IST': 'NÃO',
        'Acao_Medicacao_Curativo': 'NÃO', 'Acao_Exames': 'NÃO',
        'Acao_Documentacao': 'NÃO', 'Acao_Contato_Familiar': 'NÃO',
        'Status_Privado_Liberdade': 'NÃO', 'Status_Nao_Localizado': 'NÃO',
        'Status_Recusa_Abandono': 'NÃO',
    }
    if pd.isna(texto) or not str(texto).strip():
        return pd.Series(cats)
    t = str(texto).lower()
    if re.search(r'\bcaps\b|\bprosam\b|\brue\b', t):            cats['Encaminhado_CAPS'] = 'SIM'
    if re.search(r'\bsiat\b', t):                               cats['Encaminhado_SIAT'] = 'SIM'
    if re.search(r'\bcta\b|\bcaei\b|hotel social|\babrigo\b|\balbergue\b|pernoite|\b156\b', t):
                                                                 cats['Encaminhado_Acolhimento'] = 'SIM'
    if re.search(r'\bubs\b|\bama\b|\bupa\b|\bcer\b|consulta m[eé]d|médico|medico', t):
                                                                 cats['Encaminhado_Saude_Basica'] = 'SIM'
    if re.search(r'\bhc\b|\bhospital\b|\bsanta casa\b|pronto[\s-]?socorro|\bps\b', t):
                                                                 cats['Encaminhado_Hospital_PS'] = 'SIM'
    if re.search(r'\bsae\b|\bseas\b', t):                       cats['Encaminhado_SAE'] = 'SIM'
    if re.search(r'\btdo\b|\btb\b|\btuberculose\b', t):         cats['Tratamento_TB'] = 'SIM'
    if re.search(r'\btarv\b|\bhiv\b|\bist\b', t):               cats['Tratamento_HIV_IST'] = 'SIM'
    if re.search(r'medica[çc][aã]o|rem[eé]dio|sintom[aá]ticos|curativo|les[aã]o', t):
                                                                 cats['Acao_Medicacao_Curativo'] = 'SIM'
    if re.search(r'exame|endoscopia|mamografia|citologia', t):   cats['Acao_Exames'] = 'SIM'
    if re.search(r'documento|documenta[çc][aã]o|certid[aã]o|\brg\b|poupatempo', t):
                                                                 cats['Acao_Documentacao'] = 'SIM'
    if re.search(r'familiar|fam[ií]lia|retorno para casa|m[aã]e\b|\bpai\b', t):
                                                                 cats['Acao_Contato_Familiar'] = 'SIM'
    if re.search(r'privad[ao]\s+de\s+liberdade|reclus[ao]|pres[ao]', t):
                                                                 cats['Status_Privado_Liberdade'] = 'SIM'
    if re.search(r'fora do territ[oó]rio|n[aã]o\s+localizado|desaparecido', t):
                                                                 cats['Status_Nao_Localizado'] = 'SIM'
    if re.search(r'recus[ao]|recusou|neg[ao]|negou|abandono|abandonou', t):
                                                                 cats['Status_Recusa_Abandono'] = 'SIM'
    return pd.Series(cats)

# ══════════════════════════════════════════════════════════════════════════════
# CORREÇÃO DE DATAS
# ══════════════════════════════════════════════════════════════════════════════

def corrigir_ano_digitado(texto_data):
    if not isinstance(texto_data, str): return texto_data
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{1,4})$', texto_data.strip())
    if m:
        dia, mes, ano_str = m.groups()
        if len(ano_str) == 4 and ano_str.startswith('0') and int(ano_str) < 1000:
            candidato = ano_str[1:] + ano_str[0]
            if 2000 <= int(candidato) <= datetime.now().year:
                return f"{dia}/{mes}/{candidato}"
        elif len(ano_str) == 3:
            candidato = '2' + ano_str
            if 2000 <= int(candidato) <= datetime.now().year:
                return f"{dia}/{mes}/{candidato}"
    return texto_data

def _corrigir_datas(df):
    cols_data = [c for c in df.columns if any(p in c.lower() for p in ['data', 'editado', 'quando'])]
    hoje = pd.Timestamp.now()
    for col in cols_data:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).apply(corrigir_ano_digitado)
        conv = pd.to_datetime(df[col], errors='coerce', dayfirst=True, format='mixed')
        mask = (conv > hoje) | (conv.dt.year < 1900)
        conv[mask] = pd.NaT
        df[col] = conv
    return df

def _formatar_datas_str(df):
    """Converte todas as colunas de data para string DD/MM/AAAA (para deduplicação e salvamento)."""
    cols_data = [c for c in df.columns if any(p in c.lower() for p in ['data', 'editado', 'quando'])]
    for col in cols_data:
        conv = pd.to_datetime(df[col], errors='coerce', dayfirst=True, format='mixed')
        df[col] = conv.dt.strftime('%d/%m/%Y')
    return df

# ══════════════════════════════════════════════════════════════════════════════
# PROCESSAMENTO DO RELATORIO_ABORDAGEM
# ══════════════════════════════════════════════════════════════════════════════

def processar_relatorio(path_relatorio):
    """
    Carrega o relatorio_abordagem e aplica todas as regras de padronização,
    retornando um DataFrame no formato BASEBI pronto para concatenação.
    """
    print("  Carregando relatorio_abordagem...")
    df = pd.read_excel(path_relatorio)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.startswith('Unnamed')]

    print("  Renomeando colunas para o formato BASEBI...")
    df = df.rename(columns=RENOMEAR_RELATORIO)

    print("  Corrigindo datas...")
    df = _corrigir_datas(df)
    hoje = pd.Timestamp.now()

    print("  Padronizando Gênero e Sexo de Nascimento...")
    res = df.apply(
        lambda r: pd.Series(
            classificar_genero_sexo(r.get('Gênero'), r.get('Sexo de Nascimento')),
            index=['Gênero', 'Sexo de Nascimento']
        ), axis=1
    )
    df['Gênero'] = res['Gênero']
    df['Sexo de Nascimento'] = res['Sexo de Nascimento']

    print("  Padronizando IST, TB, PcD...")
    for campo in ['IST', 'TB', 'PcD']:
        if campo in df.columns:
            df[campo] = df[campo].apply(lambda v: padronizar_ist_tb_pcd(v, campo))

    print("  Padronizando Pop Rua e Usuário...")
    for campo in ['Pop Rua', 'Usuário']:
        if campo in df.columns:
            df[campo] = df[campo].apply(padronizar_sim_nao)

    print("  Padronizando Idoso, Criança/Adolescente e Gestante...")
    df['Idoso'] = df.apply(padronizar_idoso, axis=1, args=(hoje,))
    df['Criança/Adolescente'] = df.apply(padronizar_crianca, axis=1, args=(hoje,))
    df['Gestante'] = df.apply(padronizar_gestante, axis=1)

    print("  Padronizando Território...")
    if 'Território' in df.columns:
        df['Território'] = df['Território'].apply(normalizar_territorio)

    col_cena = 'Quanto tempo na cena aberta de uso? E onde frequentava antes de chegar nesta cena?'
    if col_cena in df.columns:
        print("  Processando Tempo na Cena...")
        df[['Tempo na Cena', 'Onde Frequentava']] = df[col_cena].apply(separar_tempo_local)
        anos_meses = df['Tempo na Cena'].apply(extrair_anos_meses)
        df['Anos de cena'] = anos_meses['Anos de cena'].astype('Int64')
        df['Meses de cena'] = anos_meses['Meses de cena'].astype('Int64')

    if 'Faz uso de quais substâncias?' in df.columns:
        print("  Processando substâncias...")
        df = pd.concat([df, df['Faz uso de quais substâncias?'].apply(processar_substancias)], axis=1)

    if 'Encaminhamento' in df.columns:
        print("  Mapeando encaminhamentos...")
        df = pd.concat([df, df['Encaminhamento'].apply(mapear_encaminhamentos)], axis=1)

    return df

# ══════════════════════════════════════════════════════════════════════════════
# ENRIQUECIMENTO INTRA-DIA
# ══════════════════════════════════════════════════════════════════════════════

def enriquecer_intra_dia(df):
    campos = [c for c in CAMPOS_ENRIQUECIMENTO if c in df.columns]
    grupos = {}
    for idx, row in df.iterrows():
        id_ = row.get('ID')
        data = row.get('Data de Inclusão')
        if pd.isna(id_) or pd.isna(data): continue
        chave = (str(id_).strip(), str(data).strip())
        grupos.setdefault(chave, []).append(idx)

    preenchidos = nao_info = 0
    total = len(df)
    for i, idx in enumerate(df.index):
        if i % 1000 == 0:
            print(f"    Enriquecendo linha {i}/{total}...", end='\r')
        id_   = df.at[idx, 'ID'] if 'ID' in df.columns else None
        data  = df.at[idx, 'Data de Inclusão'] if 'Data de Inclusão' in df.columns else None
        chave = (str(id_).strip(), str(data).strip()) if pd.notna(id_) and pd.notna(data) else None
        idxs_grupo = grupos.get(chave, [idx]) if chave else [idx]

        for campo in campos:
            if not e_vazio(df.at[idx, campo], campo): continue
            vals = [df.at[j, campo] for j in idxs_grupo
                    if j != idx and not e_vazio(df.at[j, campo], campo)]
            if vals:
                melhor = Counter([str(v).strip() for v in vals]).most_common(1)[0][0]
                df.at[idx, campo] = melhor
                preenchidos += 1
            else:
                df.at[idx, campo] = 'NÃO INFORMADO'
                nao_info += 1
    print()
    return df, preenchidos, nao_info

# ══════════════════════════════════════════════════════════════════════════════
# CÁLCULO DE MV
# ══════════════════════════════════════════════════════════════════════════════

def _data_mais_frequente(rows, hoje):
    vals = []
    for v in rows['Data de Nascimento'].dropna():
        s = str(v).strip()
        if s.lower() in VALORES_VAZIOS or s in DATAS_PLACEHOLDER: continue
        try:
            d = pd.to_datetime(s, errors='coerce', dayfirst=True, format='mixed')
            if pd.notna(d) and 1900 < d.year <= hoje.year:
                vals.append(d)
        except: pass
    return Counter(vals).most_common(1)[0][0] if vals else None

def _tempo_cena_id(rows):
    col = 'Tempo na Cena' if 'Tempo na Cena' in rows.columns else None
    if not col: return None
    vals = [str(v).strip().lower() for v in rows[col].dropna()
            if re.search(r'\d', str(v)) and 'não' not in str(v).lower()]
    if not vals: return None
    candidatos_anos = [(int(re.findall(r'\d+', v)[0]), v)
                       for v in vals if re.findall(r'\d+', v) and 'ano' in v]
    if candidatos_anos:
        return max(candidatos_anos, key=lambda x: x[0])[1]
    return Counter(vals).most_common(1)[0][0]

def _campo_clinico(rows, campo):
    if campo not in rows.columns: return 'NÃO'
    vals = rows[campo].dropna().astype(str).str.strip().str.upper()
    return 'SIM' if (vals == 'SIM').any() else 'NÃO'

def _mais_frequente(rows, campo):
    if campo not in rows.columns: return None
    vals = [str(v).strip() for v in rows[campo].dropna()
            if not e_vazio(v) and str(v).strip().upper() != 'NÃO INFORMADO']
    return Counter(vals).most_common(1)[0][0] if vals else None

def _calcular_pontuacao_perfil(perfil, hoje):
    pontos = 0
    dob = perfil.get('dob')
    if dob:
        idade = (hoje - dob).days / 365
        if idade < 18 or idade >= 60: pontos += 5
    else:
        if perfil.get('idoso') == 'SIM':  pontos += 5
        elif perfil.get('crianca') == 'SIM': pontos += 5
    for campo, peso in [('gestante', 5), ('pcd', 5), ('ist', 5), ('tb', 5)]:
        if perfil.get(campo) == 'SIM': pontos += peso
    if perfil.get('sexo') == 'FEMININO': pontos += 1
    if perfil.get('genero') == 'TRANS':  pontos += 1
    tempo = perfil.get('tempo_cena') or ''
    nums = re.findall(r'\d+', tempo)
    if nums and 'ano' in tempo:
        anos = int(nums[0])
        if anos >= 6:   pontos += 5
        elif anos >= 2: pontos += 3
    return pontos

def _calc_mv_linha(row, hoje):
    pontos = 0
    dob = row.get('Data de Nascimento')
    if pd.notna(dob) and str(dob).strip().lower() not in VALORES_VAZIOS \
            and str(dob).strip() not in DATAS_PLACEHOLDER:
        try:
            d = pd.to_datetime(str(dob), errors='coerce', dayfirst=True, format='mixed')
            if pd.notna(d) and 1900 < d.year <= hoje.year:
                idade = (hoje - d).days / 365
                if idade < 18 or idade >= 60: pontos += 5
        except: pass
    else:
        if str(row.get('Idoso', '')).strip() == 'SIM': pontos += 5
        elif str(row.get('Criança/Adolescente', '')).strip() == 'SIM': pontos += 5
    for campo, peso in [('Gestante', 5), ('PcD', 5), ('IST', 5), ('TB', 5)]:
        if str(row.get(campo, '')).strip() == 'SIM': pontos += peso
    if str(row.get('Sexo de Nascimento', '')).strip() == 'FEMININO': pontos += 1
    if str(row.get('Gênero', '')).strip() == 'TRANS': pontos += 1
    tempo = str(row.get('Tempo na Cena', '')).lower()
    nums = re.findall(r'\d+', tempo)
    if nums and 'ano' in tempo:
        anos = int(nums[0])
        if anos >= 6:   pontos += 5
        elif anos >= 2: pontos += 3
    return pontos

def calcular_mv(df):
    hoje = pd.Timestamp.now()
    mv_por_id = {}
    ids_validos = df.dropna(subset=['ID'])['ID'].unique()
    total = len(ids_validos)
    for i, id_ in enumerate(ids_validos):
        if i % 200 == 0:
            print(f"    MV: {i}/{total} IDs processados...", end='\r')
        rows = df[df['ID'] == id_]
        perfil = {
            'dob':        _data_mais_frequente(rows, hoje),
            'idoso':      _mais_frequente(rows, 'Idoso'),
            'crianca':    _mais_frequente(rows, 'Criança/Adolescente'),
            'gestante':   _campo_clinico(rows, 'Gestante'),
            'pcd':        _campo_clinico(rows, 'PcD'),
            'ist':        _campo_clinico(rows, 'IST'),
            'tb':         _campo_clinico(rows, 'TB'),
            'sexo':       _mais_frequente(rows, 'Sexo de Nascimento'),
            'genero':     _mais_frequente(rows, 'Gênero'),
            'tempo_cena': _tempo_cena_id(rows),
        }
        pontuacao = _calcular_pontuacao_perfil(perfil, hoje)
        mv_por_id[id_] = {'pontuacao': pontuacao, 'mv': 'SIM' if pontuacao > 0 else 'NÃO'}

    df['Pontuacao MV'] = df['ID'].map(
        lambda id_: mv_por_id.get(id_, {}).get('pontuacao', 0) if pd.notna(id_) else None
    )
    df['MV'] = df['ID'].map(
        lambda id_: mv_por_id.get(id_, {}).get('mv', 'NÃO') if pd.notna(id_) else None
    )
    mask_sem_id = df['ID'].isna()
    for idx in df[mask_sem_id].index:
        p = _calc_mv_linha(df.loc[idx], hoje)
        df.at[idx, 'Pontuacao MV'] = p
        df.at[idx, 'MV'] = 'SIM' if p > 0 else 'NÃO'
    print()
    return df

# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL DE ATUALIZAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def atualizar_base(path_base, path_relatorio, path_saida):
    """
    Pipeline completo:
      1. Carrega a BASEBI existente
      2. Carrega e processa o relatorio_abordagem (novo formato)
      3. Concatena as duas bases
      4. Remove duplicatas exatas
      5. Enriquece campos vazios intra-dia (ID + Data)
      6. Recalcula MV para todos os IDs da base combinada
      7. Reordena colunas no formato BASEBI
      8. Salva
    """
    separador = '─' * 60

    # ── 1. CARREGAR BASEBI ─────────────────────────────────────────────────
    print(f"\n{separador}")
    print("PASSO 1 — Carregando Base Unificada BI...")
    print(separador)
    df_base = pd.read_excel(path_base)
    df_base.columns = df_base.columns.str.strip()
    df_base = df_base.loc[:, ~df_base.columns.str.startswith('Unnamed')]

    # Normalizar renomeações históricas da BASEBI
    for col_errada, col_certa in RENOMEAR_BASE.items():
        if col_errada in df_base.columns and col_certa in df_base.columns:
            df_base[col_certa] = df_base[col_certa].combine_first(df_base[col_errada])
            df_base = df_base.drop(columns=[col_errada])
        elif col_errada in df_base.columns:
            df_base = df_base.rename(columns={col_errada: col_certa})

    n_base = len(df_base)
    ids_base = df_base['ID'].dropna().nunique() if 'ID' in df_base.columns else 0
    print(f"  ✓ {n_base:,} linhas carregadas | {ids_base:,} IDs únicos na base atual")

    # ── 2. PROCESSAR RELATORIO ─────────────────────────────────────────────
    print(f"\n{separador}")
    print("PASSO 2 — Processando relatorio_abordagem...")
    print(separador)
    df_novo = processar_relatorio(path_relatorio)
    n_novo = len(df_novo)
    ids_novos = df_novo['ID'].dropna().nunique() if 'ID' in df_novo.columns else 0
    print(f"  ✓ {n_novo:,} linhas processadas | {ids_novos:,} IDs únicos no relatório")

    # ── 3. CONCATENAR ─────────────────────────────────────────────────────
    print(f"\n{separador}")
    print("PASSO 3 — Unindo bases...")
    print(separador)
    df_final = pd.concat([df_base, df_novo], ignore_index=True)
    print(f"  Total antes da deduplicação: {len(df_final):,} linhas")

    # ── 4. FORMATAR DATAS E REMOVER DUPLICATAS ─────────────────────────────
    print(f"\n{separador}")
    print("PASSO 4 — Normalizando datas e removendo duplicatas exatas...")
    print(separador)
    df_final = _formatar_datas_str(df_final)
    n_antes = len(df_final)
    df_final = df_final.drop_duplicates()
    n_removidas = n_antes - len(df_final)

    # Identificar registros genuinamente novos (IDs do relatório não presentes na base)
    if 'ID' in df_base.columns and 'ID' in df_novo.columns:
        ids_existentes = set(df_base['ID'].dropna().astype(str).str.strip())
        ids_do_relatorio = set(df_novo['ID'].dropna().astype(str).str.strip())
        ids_realmente_novos = ids_do_relatorio - ids_existentes
    else:
        ids_realmente_novos = set()

    print(f"  Duplicatas exatas removidas  : {n_removidas:,}")
    print(f"  IDs novos (não estavam na base): {len(ids_realmente_novos):,}")
    print(f"  Total após deduplicação      : {len(df_final):,} linhas")

    # ── 5. ENRIQUECER INTRA-DIA ────────────────────────────────────────────
    print(f"\n{separador}")
    print("PASSO 5 — Enriquecimento intra-dia (ID + Data)...")
    print(separador)
    df_final, preenchidos, nao_info = enriquecer_intra_dia(df_final)
    print(f"  Campos preenchidos por par ID+Data : {preenchidos:,}")
    print(f"  Campos preenchidos com NÃO INFORMADO: {nao_info:,}")

    # ── 6. RECALCULAR MV ───────────────────────────────────────────────────
    print(f"\n{separador}")
    print("PASSO 6 — Recalculando MV para todos os IDs da base combinada...")
    print(separador)
    df_final = calcular_mv(df_final)
    mv_sim = (df_final['MV'] == 'SIM').sum()
    mv_nao = (df_final['MV'] == 'NÃO').sum()
    ids_unicos_final = df_final['ID'].dropna().nunique() if 'ID' in df_final.columns else 0
    print(f"  MV = SIM : {mv_sim:,} linhas")
    print(f"  MV = NÃO : {mv_nao:,} linhas")

    # ── 7. REORDENAR COLUNAS ───────────────────────────────────────────────
    colunas_presentes = [c for c in ORDEM_COLUNAS_BASEBI if c in df_final.columns]
    colunas_extras = [c for c in df_final.columns if c not in ORDEM_COLUNAS_BASEBI]
    df_final = df_final[colunas_presentes + colunas_extras]

    # ── 8. SALVAR ──────────────────────────────────────────────────────────
    print(f"\n{separador}")
    print("PASSO 7 — Salvando arquivo final...")
    print(separador)
    df_final.to_excel(path_saida, index=False)

    # ── RESUMO FINAL ───────────────────────────────────────────────────────
    print(f"""
{'═' * 60}
  ✅  BASE ATUALIZADA COM SUCESSO
{'═' * 60}

  Base anterior
    Linhas              : {n_base:,}
    IDs únicos          : {ids_base:,}

  Relatório incorporado
    Linhas              : {n_novo:,}
    IDs únicos          : {ids_novos:,}
    IDs genuinamente novos: {len(ids_realmente_novos):,}

  Base final
    Linhas              : {len(df_final):,}
    IDs únicos          : {ids_unicos_final:,}
    Duplicatas removidas: {n_removidas:,}
    MV = SIM            : {mv_sim:,}
    MV = NÃO            : {mv_nao:,}

  Arquivo salvo em:
    {path_saida}
{'═' * 60}
""")
    return df_final


# ══════════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    hoje_str = datetime.now().strftime('%d_%m_%Y')

    PATH_BASE      = '/mnt/user-data/uploads/BASEBI_30_03_2026__Perfil_ComplexoOkuharaKoei_PqDomPedro_Glicerio_.xlsx'
    PATH_RELATORIO = '/mnt/user-data/uploads/relatorio_abordagem.xlsx'
    PATH_SAIDA     = f'/mnt/user-data/outputs/BASEBI_{hoje_str}_(Perfil_ComplexoOkuharaKoei_PqDomPedro_Glicerio).xlsx'

    atualizar_base(PATH_BASE, PATH_RELATORIO, PATH_SAIDA)

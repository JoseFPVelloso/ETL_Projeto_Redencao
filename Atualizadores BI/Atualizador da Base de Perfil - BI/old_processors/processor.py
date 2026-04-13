"""
processor.py — Motor de processamento da Base Unificada (Versão Unificada 2026)
=============================================================================
Suporta: 
  1. Base de Perfil (Antiga)
  2. Relatório de Abordagem (Nova)
  3. Base Unificada BI (Destino)
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from collections import Counter

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTES E MAPEAMENTOS (UNIFICADOS)
# ──────────────────────────────────────────────────────────────────────────────

DATAS_PLACEHOLDER = {'01/01/1970', '1/1/1970'}

VALORES_VAZIOS = {
    '', 'nan', 'none', 'sem informação', 'sem informações', 'sem informacoes',
    'não informado', 'nao informado', 's.inf', 'sinf', 'não inf', 'nao inf',
    'sem info', 'null', 'sem informação ', 'não informado ', 'nao informando',
    'sem informações ', 'não infromado', 'não informao', 'não infoemado',
    'não inf.', 'sen informações', 'sem informacões', 'sem informa',
    'não i', 'n~so', 'n', 'sem informação'
}

# Tradução de colunas: Novo Relatório -> Padrão BASEBI
RENOMEAR_FONTES = {
    'DATA': 'Data de Inclusão',
    'Equipe': 'Equipe/Líder',
    'Pessoa Idosa': 'Idoso',
    'Serviços que compartilham o cuidado': 'Quais serviços compartilham o cuidado?',
    'Quanto tempo faz uso de drogas em situação de rua?': 
        'Quanto tempo na cena aberta de uso? E onde frequentava antes de chegar nesta cena?',
    'Encaminhamento ': 'Encaminhamento',
    'Motivo da recusa ': 'Motivo da recusa',
}

TERRITORIO_CANONICO = {
    r'parque\s+dom\s+pedro|pq\.?\s*dom\s*pedro|parque\s+d\.?\s*pedro': 'Parque Dom Pedro',
    r'glicério|glicerio': 'Glicério',
    r'okuhara|okurara|okuhura': 'Complexo Okuhara Koei',
    r'outr[ao]s?': 'Outras',
}

CORRECOES_TERRITORIO = {
    'Praça Dom Pedro': 'Parque Dom Pedro',
    'Parque Dom Pedr': 'Parque Dom Pedro',
    'Parque Dom Pedro II': 'Parque Dom Pedro',
    'Praça Da Sé':     'Glicério',
    'Outro':           'Outras',
}

# Bairros que compõem a região central expandida
BAIRROS_CENTRO = {
    'campos elíseos', 'campos eliseos', 'santa cecília', 'santa cecilia',
    'santa ifigênia', 'santa ifigenia', 'república', 'republica',
    'bom retiro', 'luz', 'sé', 'liberdade', 'anhangabaú'
}

# Bairros que são realmente fora do centro (opcional, para controle)
BAIRROS_OUTRAS = {
    'brás', 'bras', 'pari', 'mooca', 'belém', 'tatuapé'
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
        if re.search(r'mulher|feminino|f\b', g) or s in {'mulher trans', '~mulher trans'}: sexo_pad = 'MASCULINO'
        elif re.search(r'homem|masculino|m\b', g): sexo_pad = 'FEMININO'
        else: sexo_pad = padronizar_sexo(sexo_raw)
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
    if pd.isna(v): return 'NÃO INFORMADO'
    raw = str(v).strip()
    t = raw.lower()
    if re.fullmatch(r'sim\.?|sim\s*|s\.?|sim\s+\(.*\)', t): return 'SIM'
    if e_nao(t): return 'NÃO'
    if campo == 'PcD' and re.search(r'cadeirante|locomoção|deficiên|amput|cego|surdo', raw, re.I): return 'SIM'
    return 'NÃO INFORMADO'

def padronizar_sim_nao(v):
    if pd.isna(v): return 'NÃO INFORMADO'
    if e_sim(v): return 'SIM'
    if e_nao(v): return 'NÃO'
    return 'NÃO INFORMADO'

# ──────────────────────────────────────────────────────────────────────────────
# PADRONIZAÇÃO BIOGRÁFICA E TERRITORIAL
# ──────────────────────────────────────────────────────────────────────────────

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
    if str(row.get('Sexo de Nascimento', '')).strip() == 'MASCULINO': return 'NÃO'
    return padronizar_sim_nao(row.get('Gestante'))

def normalizar_territorio(v):
    if pd.isna(v): return 'NÃO INFORMADO'
    s = str(v).strip()
    
    # 1. Correções diretas e pontuais
    if s in CORRECOES_TERRITORIO:
        return CORRECOES_TERRITORIO[s]
    
    t = s.lower()
    
    # 2. Verificação das Cenas Principais (Regex)
    for padrao, canonico in TERRITORIO_CANONICO.items():
        if re.search(padrao, t) and canonico != 'Outras':
            return canonico
            
    # 3. Agrupamento "Centro" (Nova Inteligência)
    if t in BAIRROS_CENTRO:
        return 'Centro'
        
    # 4. Agrupamento "Outras" (Bairros adjacentes de outras regiões)
    if t in BAIRROS_OUTRAS:
        return 'Outras'
    
    # 5. Trava de segurança: Se já for um dos nomes oficiais, mantém. 
    # Se for desconhecido, vira 'Outras' para não sujar o BI.
    canonicos_finais = {'Parque Dom Pedro', 'Glicério', 'Complexo Okuhara Koei', 'Centro', 'Outras'}
    return s if s in canonicos_finais else 'Outras'

def separar_tempo_local(texto):
    if not isinstance(texto, str) or not texto.strip():
        return pd.Series({'Tempo na Cena': 'Não informado', 'Onde Frequentava': 'Não informado'})
    t_lower = texto.lower()
    
    # Tratamento "6 anos ou mais"
    if re.search(r'6\s+anos?\s+ou\s+mais', t_lower):
        return pd.Series({'Tempo na Cena': '6 anos', 'Onde Frequentava': 'Não informado'})

    for word, digit in MAPA_NUMEROS.items():
        t_lower = re.sub(rf'\b{word}\b', digit, t_lower)

    padrao = r'(\d+)\s*(ano|anos|mês|mes|meses|semana|semanas|dia|dias)\b'
    matches = re.findall(padrao, t_lower)
    tempo, onde = "Não identificado", texto
    if matches:
        val, unit = matches[-1]
        unit_map = {'mes': 'meses', 'ano': 'anos', 'dia': 'dias', 'semana': 'semanas'}
        unit = unit_map.get(unit, unit + 's' if not unit.endswith('s') else unit)
        if val == '1' and unit.endswith('s'): unit = unit[:-1]
        tempo = f"{val} {unit}"
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

# ──────────────────────────────────────────────────────────────────────────────
# SUBSTÂNCIAS E ENCAMINHAMENTOS
# ──────────────────────────────────────────────────────────────────────────────

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
        'Usa_Alcool': 'SIM' if alc else 'NÃO', 'Usa_Crack': 'SIM' if cra else 'NÃO',
        'Usa_Maconha': 'SIM' if mac else 'NÃO', 'Usa_Cocaina': 'SIM' if coc else 'NÃO',
        'Usa_Tabaco': 'SIM' if tab else 'NÃO', 'Num_Substancias': sum([alc, cra, mac, coc, tab])
    })

def mapear_encaminhamentos(texto):
    cats = {k: 'NÃO' for k in ['Encaminhado_CAPS', 'Encaminhado_SIAT', 'Encaminhado_Acolhimento', 
                               'Encaminhado_Saude_Basica', 'Encaminhado_Hospital_PS', 'Encaminhado_SAE', 
                               'Tratamento_TB', 'Tratamento_HIV_IST', 'Acao_Medicacao_Curativo', 
                               'Acao_Exames', 'Acao_Documentacao', 'Acao_Contato_Familiar', 
                               'Status_Privado_Liberdade', 'Status_Nao_Localizado', 'Status_Recusa_Abandono']}
    if pd.isna(texto) or not str(texto).strip(): return pd.Series(cats)
    t = str(texto).lower()
    if re.search(r'\bcaps\b|\bprosam\b', t): cats['Encaminhado_CAPS'] = 'SIM'
    if re.search(r'\bsiat\b', t): cats['Encaminhado_SIAT'] = 'SIM'
    if re.search(r'hotel social|\babrigo\b|\balbergue\b', t): cats['Encaminhado_Acolhimento'] = 'SIM'
    if re.search(r'\bubs\b|\bama\b|\bupa\b', t): cats['Encaminhado_Saude_Basica'] = 'SIM'
    if re.search(r'\bhospital\b|pronto[\s-]?socorro|\bps\b', t): cats['Encaminhado_Hospital_PS'] = 'SIM'
    if re.search(r'\bsae\b', t): cats['Encaminhado_SAE'] = 'SIM'
    if re.search(r'\btb\b|\btuberculose\b', t): cats['Tratamento_TB'] = 'SIM'
    if re.search(r'\bhiv\b|\bist\b', t): cats['Tratamento_HIV_IST'] = 'SIM'
    if re.search(r'medica[çc][aã]o|rem[eé]dio|curativo', t): cats['Acao_Medicacao_Curativo'] = 'SIM'
    if re.search(r'exame', t): cats['Acao_Exames'] = 'SIM'
    if re.search(r'documento|\brg\b', t): cats['Acao_Documentacao'] = 'SIM'
    if re.search(r'fam[ií]lia|m[aã]e\b', t): cats['Acao_Contato_Familiar'] = 'SIM'
    if re.search(r'reclus[ao]|pres[ao]', t): cats['Status_Privado_Liberdade'] = 'SIM'
    if re.search(r'n[aã]o\s+localizado', t): cats['Status_Nao_Localizado'] = 'SIM'
    if re.search(r'recus[ao]|abandono', t): cats['Status_Recusa_Abandono'] = 'SIM'
    return pd.Series(cats)

# ──────────────────────────────────────────────────────────────────────────────
# ENRIQUECIMENTO E MV
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
        if callback and i % 500 == 0: callback(int(i/total*100), f'Enriquecendo {i}/{total}...')
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
            else: df.at[idx, campo] = 'NÃO INFORMADO'
    return df, preenchidos, 0

def calcular_mv(df, callback=None):
    hoje = pd.Timestamp.now()
    ids_validos = df.dropna(subset=['ID'])['ID'].unique()
    total = len(ids_validos)
    mv_map = {}
    for i, id_ in enumerate(ids_validos):
        if callback and i % 100 == 0: callback(int(i/total*100), f'Calculando MV {i}/{total}...')
        rows = df[df['ID'] == id_]
        
        # Consolidação de perfil por ID
        dob = None
        for v in rows['Data de Nascimento'].dropna():
            if not e_vazio(v, 'Data de Nascimento'):
                dob = pd.to_datetime(v, errors='coerce', dayfirst=True)
                break
        
        pts = 0
        if dob and pd.notna(dob):
            idade = (hoje - dob).days / 365
            if idade < 18 or idade >= 60: pts += 5
        elif (rows['Idoso'] == 'SIM').any() or (rows['Criança/Adolescente'] == 'SIM').any(): pts += 5
        
        for c in ['Gestante', 'PcD', 'IST', 'TB']:
            if (rows[c] == 'SIM').any(): pts += 5
        if (rows['Sexo de Nascimento'] == 'FEMININO').any(): pts += 1
        if (rows['Gênero'] == 'TRANS').any(): pts += 1
        
        # Tempo na cena (Pega o maior tempo registrado)
        anos_max = 0
        for t in rows['Tempo na Cena'].dropna():
            nums = re.findall(r'\d+', str(t))
            if nums and 'ano' in str(t).lower(): anos_max = max(anos_max, int(nums[0]))
        if anos_max >= 6: pts += 5
        elif anos_max >= 2: pts += 3
        
        mv_map[id_] = (pts, 'SIM' if pts > 0 else 'NÃO')

    df['Pontuacao MV'] = df['ID'].map(lambda x: mv_map.get(x, (0, 'NÃO'))[0] if pd.notna(x) else 0)
    df['MV'] = df['ID'].map(lambda x: mv_map.get(x, (0, 'NÃO'))[1] if pd.notna(x) else 'NÃO')
    return df

# ──────────────────────────────────────────────────────────────────────────────
# PIPELINE PRINCIPAL (ATUALIZAR BASE)
# ──────────────────────────────────────────────────────────────────────────────

def atualizar_base(path_base, path_diario, path_saida, callback=None):
    try:
        if callback: callback(2, 'Carregando base unificada...')
        df_base = pd.read_excel(path_base).rename(columns=lambda x: str(x).strip())
        
        if callback: callback(10, 'Processando novas entradas...')
        df_novo = processar_diario(path_diario, callback=lambda p, m: callback(10 + int(p * 0.4), m))

        if callback: callback(55, 'Unindo e deduplicando...')
        df_final = pd.concat([df_base, df_novo], ignore_index=True)
        
        # Normalização de datas para string (Garante deduplicação precisa)
        cols_data = [c for c in df_final.columns if any(p in c.lower() for p in ['data', 'editado', 'quando'])]
        for col in cols_data:
            conv = pd.to_datetime(df_final[col], errors='coerce', dayfirst=True)
            df_final[col] = conv.dt.strftime('%d/%m/%Y')

        n_antes = len(df_final)
        df_final = df_final.drop_duplicates()
        
        if callback: callback(70, 'Enriquecendo e calculando MV...')
        df_final, pre, _ = enriquecer_intra_dia(df_final)
        df_final = calcular_mv(df_final)

        if callback: callback(95, 'Salvando arquivo...')
        df_final.to_excel(path_saida, index=False)
        
        resumo = f"✅ Sucesso!\n• Novas linhas: {len(df_novo)}\n• IDs únicos: {df_final['ID'].nunique()}"
        return True, resumo
    except Exception as e:
        return False, f"Erro: {str(e)}"

def processar_diario(path, callback=None):
    df = pd.read_excel(path) if str(path).endswith('.xlsx') else pd.read_csv(path)
    df.columns = df.columns.str.strip()
    
    # TRADUÇÃO: Mapeia colunas do Relatório de Abordagem
    df = df.rename(columns=RENOMEAR_FONTES)
    
    hoje = pd.Timestamp.now()
    total = len(df)
    
    # Processamento de Perfil
    res_gs = df.apply(lambda r: pd.Series(classificar_genero_sexo(r.get('Gênero'), r.get('Sexo de Nascimento')), index=['Gênero', 'Sexo de Nascimento']), axis=1)
    df['Gênero'], df['Sexo de Nascimento'] = res_gs['Gênero'], res_gs['Sexo de Nascimento']
    
    for c in ['IST', 'TB', 'PcD']: df[c] = df[c].apply(lambda v: padronizar_ist_tb_pcd(v, c))
    for c in ['Pop Rua', 'Usuário']: df[c] = df[c].apply(padronizar_sim_nao)
    
    df['Idoso'] = df.apply(padronizar_idoso, axis=1, args=(hoje,))
    df['Criança/Adolescente'] = df.apply(padronizar_crianca, axis=1, args=(hoje,))
    df['Gestante'] = df.apply(padronizar_gestante, axis=1)
    df['Território'] = df['Território'].apply(normalizar_territorio)
    
    # Tempo na Cena
    col_tempo = 'Quanto tempo na cena aberta de uso? E onde frequentava antes de chegar nesta cena?'
    if col_tempo in df.columns:
        res_t = df[col_tempo].apply(separar_tempo_local)
        df['Tempo na Cena'], df['Onde Frequentava'] = res_t['Tempo na Cena'], res_t['Onde Frequentava']
        res_am = df['Tempo na Cena'].apply(extrair_anos_meses)
        df['Anos de cena'], df['Meses de cena'] = res_am['Anos de cena'], res_am['Meses de cena']

    if 'Faz uso de quais substâncias?' in df.columns:
        df = pd.concat([df, df['Faz uso de quais substâncias?'].apply(processar_substancias)], axis=1)
    if 'Encaminhamento' in df.columns:
        df = pd.concat([df, df['Encaminhamento'].apply(mapear_encaminhamentos)], axis=1)
        
    return df
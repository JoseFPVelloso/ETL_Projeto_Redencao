# logic_text_generator.py
# MÓDULO RESPONSÁVEL POR GERAR O TEXTO DE ANÁLISE CONSOLIDADO
from datetime import datetime

def _format_top_5(top_5_list):
    """
    Formata a lista dos 5 logradouros com maior frequência.
    Usa ';' como separador e 'e' para o último item.
    """
    if not top_5_list:
        return "Nenhum logradouro encontrado."
    
    nomes = [log for log, _ in top_5_list]
    
    if len(nomes) == 1:
        return nomes[0]
    if len(nomes) == 2:
        return f"{nomes[0]} e {nomes[1]}"
    
    # Formato esperado: "Rua A; Rua B; Rua C e Rua D"
    return "; ".join(nomes[:-1]) + f" e {nomes[-1]}"

def _format_extreme_variations(variations_list):
    """
    Formata a seção de variações de volume (>= 10 pessoas).
    Recebe a lista já ordenada (Aumentos primeiro, depois Reduções).
    """
    if not variations_list:
        return "Nenhuma variação relevante (>= 10 pessoas) detectada no período."
    
    linhas = []
    for var in variations_list:
        # Define o emoji e o termo com base no sinal da variação
        seta = "🔺" if var['dif_bruta'] > 0 else "🔻"
        tipo = "aumento" if var['dif_bruta'] > 0 else "diminuição"
        
        texto = (
            f"{seta} {var['logradouro']}: passou de {int(var['v1'])} para {int(var['v2'])} pessoas "
            f"({var['periodo'].capitalize()} de {var['d1']} para {var['d2']}). "
            f"Uma {tipo} de {abs(var['pct']):.1f}% em 24h."
        )
        linhas.append(texto)
    
    return "\n".join(linhas)

def generate_analysis_text(data: dict):
    """
    Gera o conteúdo completo do arquivo .txt com base nos dados calculados no logic_report.py.
    """
    
    # Extração de variáveis do dicionário para facilitar a manutenção
    hoje = data['hoje']
    data_inicio = data['data_inicio']
    data_fim = data['data_fim']
    data_inicio_anterior = data['data_inicio_anterior']
    data_fim_anterior = data['data_fim_anterior']
    
    ultimo_dia_val = data['ultimo_dia_val']
    ultimo_dia_noite = data['ultimo_dia_noite']
    
    madr = data['madr']
    manha = data['manha']
    tarde = data['tarde']
    noite = data['noite']
    
    top_5_texto = _format_top_5(data['top_5_logradouros'])
    variacoes_extremas_texto = _format_extreme_variations(data.get('variacoes_extremas', []))
    
    media_atual = data['media_atual']
    media_anterior = data['media_anterior']
    variacao = data['variacao']
    
    # Define o termo de comparação global
    tipo_variacao = "um aumento" if variacao > 0 else ("uma diminuição" if variacao < 0 else "estabilidade")
    ref_texto = data['ref_texto']

    # --- 1. Construção do Parágrafo de Análise Principal ---
    texto_analise = (
        f"Na região de Santa Cecília, Campos Elíseos e Santa Ifigênia, em {ultimo_dia_val.strftime('%d/%m/%Y')} "
        f"foram localizadas {int(madr['total'])} pessoas de madrugada (05h), {int(manha['total'])} de manhã (10h), "
        f"{int(tarde['total'])} à tarde (15h) e {int(noite['total'])} à noite (20h) do dia {ultimo_dia_noite.strftime('%d')}. "
        f"Os 5 logradouros com maior frequência nos últimos 3 dias são: {top_5_texto}. "
        f"Com mais de 10 pessoas, foram {int(madr['enderecos'])} endereços de madrugada, {int(manha['enderecos'])} de manhã, "
        f"{int(tarde['enderecos'])} à tarde e {int(noite['enderecos'])} à noite, "
        f"somando respectivamente {int(madr['soma_aglom'])}, {int(manha['soma_aglom'])}, {int(tarde['soma_aglom'])} e {int(noite['soma_aglom'])}. "
        f"A média atual é de {int(media_atual)} pessoas por dia — {tipo_variacao} de {abs(variacao)}% "
        f"em relação à contagem enviada {ref_texto}."
    )

    # --- 2. Montagem da Estrutura Visual do Arquivo TXT ---
    conteudo_txt = f"""================================================================================
TEXTO DE ANÁLISE - RELATÓRIO DIÁRIO
================================================================================

Período do Relatório: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}
Gerado em: {hoje.strftime('%d/%m/%Y às %H:%M:%S')}

================================================================================
ANÁLISE RESUMIDA
================================================================================

{texto_analise}

================================================================================
VARIAÇÕES RELEVANTES (TOP AUMENTOS E REDUÇÕES)
================================================================================

{variacoes_extremas_texto}

================================================================================
ESTATÍSTICAS GERAIS
================================================================================

Média Atual:    {int(media_atual)} pessoas/dia (intervalo {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')})
Média Anterior: {int(media_anterior)} pessoas/dia (intervalo {data_inicio_anterior.strftime('%d/%m/%Y')} a {data_fim_anterior.strftime('%d/%m/%Y')})
Variação Global: {variacao:+.1f}%

================================================================================
DETALHAMENTO ÚLTIMO DIA - {ultimo_dia_val.strftime('%d/%m/%Y')}
================================================================================

Madrugada (05h):
  • Total de pessoas: {int(madr['total'])}
  • Endereços com >10 pessoas: {int(madr['enderecos'])}
  • Soma nas aglomerações: {int(madr['soma_aglom'])}

Manhã (10h):
  • Total de pessoas: {int(manha['total'])}
  • Endereços com >10 pessoas: {int(manha['enderecos'])}
  • Soma nas aglomerações: {int(manha['soma_aglom'])}

Tarde (15h):
  • Total de pessoas: {int(tarde['total'])}
  • Endereços com >10 pessoas: {int(tarde['enderecos'])}
  • Soma nas aglomerações: {int(tarde['soma_aglom'])}

Noite (20h) do dia {ultimo_dia_noite.strftime('%d/%m/%Y')}:
  • Total de pessoas: {int(noite['total'])}
  • Endereços com >10 pessoas: {int(noite['enderecos'])}
  • Soma nas aglomerações: {int(noite['soma_aglom'])}

================================================================================
"""
    
    return conteudo_txt
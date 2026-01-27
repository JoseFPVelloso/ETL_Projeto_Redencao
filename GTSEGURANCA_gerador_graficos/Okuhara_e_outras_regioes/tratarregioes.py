import pandas as pd

# 1. Carrega o seu arquivo original
try:
    df = pd.read_excel('regioes.xlsx')
except:
    # Caso esteja em CSV como no upload
    df = pd.read_csv('regioes.xlsx - Plan1.csv') # Ajuste o nome se necessário

# Garante que as colunas têm o nome certo (remove espaços extras)
df.columns = df.columns.str.strip()

# 2. Dicionário de Correções (De -> Para)
correcoes = {
    # --- Complexo Okuhara Koei (Limpeza) ---
    'Complexo Okuhara Koei - Paredão': 'Paredão',
    'Paredao': 'Paredão',
    'Paredão': 'Paredão',
    'Complexo Okuhara Koei - Viaduto Okuhara: Fitinha (lateral baixo viaduto)': 'Complexo Okuhara Koei - Viaduto Okuhara',
    'Complexo Okuhara Koei - Avenida Rebouças (Rampa)': 'Complexo Okuhara Koei - Avenida Rebouças',
    'Complexo Okuhara Koei - Praça Dr. Clemente Ferreira (Subida da Rebouças p/ Dr Arnaldo)': 'Complexo Okuhara Koei - Praça Dr. Clemente Ferreira',
    'Complexo Okuhara Koei - Rua Vinicius de Moraes (Pensão do Gerson)': 'Complexo Okuhara Koei - Rua Vinicius de Moraes',
    'Complexo Okuhara Koei - Avenida Pacaembu - Tunel Noite Ilustrada': 'Complexo Okuhara Koei - Avenida Pacaembu',
    'Rua Minas Gerais (Antena Grill)': 'Rua Minas Gerais',

    # --- Glicério (Unificação) ---
    # Av. Prefeito Passos 200
    'Glicério - Avenida Prefeito Passos, 200': 'Glicério - Av. Prefeito Passos, 200',
    'Glicério - Avenida Prefeito Passos, 200 ao lado do SIAT Glicério,lateral do muro do SIAT': 'Glicério - Av. Prefeito Passos, 200',
    'Glicério - Avenida Prefeito Passos, 200 ao lado do SIAT Glicério, lateral do muro do SIAT': 'Glicério - Av. Prefeito Passos, 200',
    
    # Av. Prefeito Passos 46 (Praça Sá Cordeiro)
    'Glicerio - Avenida Prefeito Passos, 46- Praça Miinistro Sá Cordeiro- Baixada do Glicério': 'Glicério - Av. Prefeito Passos, 46 (Pça Sá Cordeiro)',
    'Glicerio - Avenida Prefeito Passos, 46 - Praça Miinistro Sá Cordeiro - Baixada do Glicério': 'Glicério - Av. Prefeito Passos, 46 (Pça Sá Cordeiro)',
    'Glicerio - Avenida Prefeito Passos, 46 - Praça Ministro Sá Cordeiro - Baixada do Glicério': 'Glicério - Av. Prefeito Passos, 46 (Pça Sá Cordeiro)',

    # Rua Antônio de Sá
    'Glicério - Rua Antônio de Sá - bosque urbano bem-te-vi (eco ponto)': 'Glicério - Rua Antônio de Sá',
    'Glicério - Rua Antônio de Sá - bosque urbano bem-te-vi (eco ponto), proximo ao numeral 116- Esquina com a avenida do Estado': 'Glicério - Rua Antônio de Sá',

    # Igreja Deus é Amor
    'Glicério - Lateral da Igreja Deus é amor': 'Glicério - Igreja Deus é Amor',
    'Glicério- Lateral da Igreja Deus é amor': 'Glicério - Igreja Deus é Amor',
    'Glicério -  Baixada do Glicério,  Rua Teixeira Leite, 140 /Lateral da Igreja Deus é amor': 'Glicério - Igreja Deus é Amor',
    'Glicério - Baixada do Glicério, Rua Teixeira Leite, 140 /Lateral da Igreja Deus é amor': 'Glicério - Igreja Deus é Amor',

    # Travessa Rua dos Estudantes
    'Glicério - Travessa Rua dos Estudantes': 'Glicério - Travessa Rua dos Estudantes',
    'Glicério- Travessa Rua dos Estudantes': 'Glicério - Travessa Rua dos Estudantes',
    'Glicério - Travessa Rua dos Estudantes, 382 fundos com a Rua. Dr. Lund': 'Glicério - Travessa Rua dos Estudantes',

    # --- Parque Dom Pedro II ---
    'Parque Dom Pedro II - Viaduto Antônio Nakashima (embaixo do viaduto/quadrado)': 'Parque Dom Pedro II - Viaduto Antônio Nakashima',
    'Parque Dom Pedro II - Viaduto Antônio Nakashima (embaixo do viaduto/quadrado)-Parque Dom Pedro, 1000': 'Parque Dom Pedro II - Viaduto Antônio Nakashima',

    # --- Praça Fernando Costa ---
    'Praça Fernando Costa': 'Praça Fernando Costa',
    'Praça Fernando Costa /Gramado- extensão da Praça do Banheiro n. 14': 'Praça Fernando Costa',
    'Praça Fernando Costa, 14 - Em frente ao Banheiro Publico': 'Praça Fernando Costa',
}

# 3. Aplica a correção
# Se estiver no dicionário, usa o novo nome. Se não, mantém o original.
coluna_original = 'Padrão' # Nome da coluna no seu CSV
if coluna_original not in df.columns:
    coluna_original = df.columns[0] # Tenta pegar a primeira se o nome for diferente

df['Oficial'] = df[coluna_original].map(correcoes).fillna(df[coluna_original])

# 4. Organiza e Salva
# Cria o DataFrame final com as 3 colunas que o nosso sistema precisa
df_final = pd.DataFrame({
    'Original': df[coluna_original],
    'Oficial': df['Oficial'],
    'Regiao': df['Região']
})

print("Gerando arquivo tratado...")
df_final.to_excel('regioes_tratado.xlsx', index=False)
print("✓ Sucesso! Arquivo 'regioes_tratado.xlsx' criado.")
print("Agora renomeie ele para 'regioes.xlsx' e use no seu sistema.")
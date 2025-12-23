# Projeto ETL - Organização de Dados

## Setup do Ambiente (Windows)

1. Clone o repositório
2. Crie o ambiente virtual: `python -m venv .venv`
3. Ative o ambiente: `.\.venv\Scripts\Activate.ps1`
4. Instale dependências: `pip install -r requirements.txt`
5. Configure o arquivo `.env` com suas credenciais
6. Execute o teste: `python test_setup.py`

## Estrutura do Projeto

projeto_etl_dados/
├── config/              # Configurações
├── notebooks/           # Análises exploratórias
├── src/                 # Código-fonte
│   ├── parsers/         # Funções de parsing
│   ├── validators/      # Validações
│   ├── database/        # Conexão e modelos
│   └── etl/            # Pipeline ETL
├── data/               # Dados
│   ├── raw/            # Planilhas originais
│   ├── processed/      # Planilhas tratadas
│   └── logs/           # Logs de execução
├── sql/                # Scripts SQL
├── tests/              # Testes unitários
└── docs/               # Documentação

## Uso

(A ser documentado)
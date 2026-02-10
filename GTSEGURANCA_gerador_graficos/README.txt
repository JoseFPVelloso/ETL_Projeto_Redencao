# 📊 Suíte de Análise de Dados e Fluxo de Pessoas

Este repositório contém duas ferramentas distintas desenvolvidas em Python para automação de relatórios, análise de fluxo pessoas em CAU.

Ambos os projetos utilizam interface gráfica (GUI) para facilitar o uso, sem necessidade de alterar código para operações diárias.

---

## 🛠️ Instalação e Requisitos

Para começar, você só precisa instalar as dependências listadas no arquivo requirements.txt.

Certifique-se de ter o Python instalado.

Abra seu terminal ou prompt de comando na pasta do projeto.

Execute o comando abaixo:

pip install -r requirements.txt

ou escreva 

pip install pandas openpyxl tkcalendar numpy

Isso instalará automaticamente todas as bibliotecas necessárias (pandas, openpyxl, tkcalendar, etc.) nas versões corretas.

```

---

## 📁 Projeto 1: Analisador do Centro (`app.py`)

Focado na análise geral de logradouros, permitindo filtrar uma lista massiva de ruas e gerar relatórios de "Top 15 Dias" e "Evolução Mensal".

### ✨ Funcionalidades

* **Importação Flexível:** Aceita arquivos `.csv` ou `.xlsx`.
* **Filtro de Ruas:** Interface com busca e seleção múltipla para escolher quais logradouros analisar.
* **Memória de Preferências:** O sistema salva automaticamente as últimas ruas selecionadas para agilizar o próximo uso.
* **Configuração de Datas:** Permite definir janelas de tempo personalizadas para os relatórios.

### 🚀 Como Usar

1. Execute o arquivo: `python app.py`
2. **Importação:** Clique em "Buscar Arquivo" e selecione sua base de dados. Clique em "Carregar Dados".
3. **Configuração:** Defina o intervalo de dias para o relatório Top 15 e o intervalo mensal.
4. **Seleção:** Na lista de ruas, use a barra de pesquisa para encontrar e marcar as ruas desejadas.
5. **Processar:** Clique em "PROCESSAR E GERAR RELATÓRIOS".
6. Os arquivos Excel serão salvos na pasta `Gráficos`.

---

## 🏙️ Projeto 2: Analisador Okuhara & Outras Regiões (`app.py`)

Uma ferramenta especializada para análise regionalizada (ex: Glicério, Complexo Okuhara), com foco em turnos específicos e detalhamento profundo por região.

### ✨ Funcionalidades

* **Mapeamento Inteligente:** Utiliza um arquivo `regioes.xlsx` para corrigir nomes de ruas (ex: padronizar "Paredao" para "Paredão") e agrupá-las em macro-regiões.
* **Seleção de Turnos:** Permite escolher quais períodos contabilizar (05h, 10h, 15h, 20h). O sistema calcula médias e volumes apenas para os horários marcados.
* **Detalhamento Visual:** Ao passar o mouse sobre uma região, o sistema lista quais ruas compõem aquele local.
* **Relatórios Completos:** Gera Ranking Diário (com abas por região) e Evolução Mensal (com contagem de dias únicos e médias ponderadas).

### ⚠️ Observação Importante (Recomendação de Uso)

> **Para o Complexo Okuhara e Geração de Gráficos:**
> Embora o sistema permita selecionar todas as regiões de uma vez, **recomenda-se rodar a ferramenta selecionando UMA região por vez** (ex: marque apenas "Complexo Okuhara", gere o relatório, e depois repita para "Glicério").
> Isso garante que o Excel gerado seja focado, com as abas de gráficos e detalhes organizadas especificamente para aquela área, facilitando a leitura e a impressão dos dados.

### 🚀 Como Usar

1. **Pré-requisito:** Certifique-se de que o arquivo `regioes.xlsx` esteja na mesma pasta (use o script `tratarregioes.py` se precisar gerar um novo a partir de dados brutos).
2. Execute o arquivo: `python app.py`
3. **Fonte de Dados:** Selecione a planilha de atendimentos/contagens.
4. **Regiões:** Marque a caixa de seleção da região desejada (Recomendado: uma por vez).
5. **Períodos:** Marque quais turnos você deseja incluir na análise (ex: Manhã e Tarde, ou Todos).
6. **Datas:** Defina os períodos para o Ranking Diário (15 dias) e Evolução Mensal.
7. Clique em **GERAR RELATÓRIOS**.

---

## 🔧 Ferramenta Auxiliar: `tratarregioes.py`

Este script não possui interface gráfica. Ele serve para criar a "memória" do Projeto 2.

* **Função:** Lê uma planilha bruta de regiões, aplica um dicionário de correções (corrige erros de digitação conhecidos) e gera o arquivo `regioes_tratado.xlsx`.
* **Como usar:**
1. Coloque sua planilha de regiões original na pasta.
2. Edite o script se houver novas correções de nomes a fazer.
3. Rode `python tratarregioes.py`.
4. Renomeie o arquivo gerado para `regioes.xlsx` para que o *Analisador Okuhara* possa lê-lo.



---

## 📂 Estrutura de Pastas

O sistema organizará os arquivos da seguinte forma:

```text
/
├── app.py                # Executável do Projeto 1
├── app2.py               # Executável do Projeto 2 (Okuhara)
├── config.py             # Configurações globais (Cores, Pastas)
├── processing.py         # Lógica do Projeto 1
├── logic.py              # Lógica do Projeto 2
├── tratarregioes.py      # Script utilitário
├── regioes.xlsx          # Base de conhecimento de locais
└── Gráficos/             # Onde os relatórios Excel serão salvos (Criada automaticamente)

```